#!/usr/bin/env python3
"""Audit six archived external misses; optionally capture exact-model reruns.

Audit mode does not require torch. Rerun mode only accepts the locked SAM source
commit and checkpoint SHA-256; it never substitutes another model or changes the
archived results. Prediction displays are made only from actual captured masks.
"""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
from time import perf_counter

import numpy as np
from PIL import Image, __version__ as PILLOW_VERSION

FIELDS = ("dice_vs_reference", "sam_predicted_iou", "risk_A", "risk_B",
          "dice_shift_left", "dice_shift_right", "dice_shift_up", "dice_shift_down")
DIRECTIONS = ("left", "right", "up", "down")


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def rows(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False,
                                    allow_nan=False) + "\n")


def write_csv(path, records):
    with Path(path).open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(records[0]))
        w.writeheader()
        w.writerows(records)


def dice(a, b):
    den = int(a.sum()) + int(b.sum())
    return 2.0 * np.count_nonzero(a & b) / den if den else 1.0


def prompt_boxes(reference):
    # Same float32 geometry and iteration order as original score_images.py.
    height, width = reference.shape
    ys, xs = np.nonzero(reference)
    left, top, right, bottom = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    pad_x, pad_y = .1 * (right - left), .1 * (bottom - top)
    limits = np.array([width, height, width, height], dtype=np.float32)
    base = np.clip(np.array([left-pad_x, top-pad_y, right+pad_x, bottom+pad_y],
                            dtype=np.float32), 0, limits)
    dx, dy = .05 * float(base[2]-base[0]), .05 * float(base[3]-base[1])
    shifts = ((-dx, 0, -dx, 0), (dx, 0, dx, 0),
              (0, -dy, 0, -dy), (0, dy, 0, dy))
    return np.stack([base] + [np.clip(base + np.asarray(s, dtype=np.float32),
                                     0, limits) for s in shifts])


def load_pair(source, manifest):
    raw = source / "data/raw/BrEaST"
    image_path, reference_path = raw / manifest["image_path"], raw / manifest["mask_path"]
    assert digest(image_path) == manifest["image_sha256"], "Image hash mismatch"
    assert digest(reference_path) == manifest["mask_sha256"], "Reference hash mismatch"
    with Image.open(image_path) as image:
        before = image.convert("RGB")
        rgba = image.convert("RGBA")
        black = Image.new("RGBA", rgba.size, (0, 0, 0, 255))
        rgb = Image.alpha_composite(black, rgba).convert("RGB")
        changed = rgb.tobytes() != before.tobytes()
        array = np.array(rgb, dtype=np.uint8)
    with Image.open(reference_path) as mask:
        reference = np.array(mask.convert("1"), dtype=bool)
    assert array.shape == (int(manifest["height"]), int(manifest["width"]), 3)
    assert reference.shape == array.shape[:2] and reference.any()
    return array, reference, changed


def audited_records(source):
    package = source / "reproducibility"
    lock = json.loads((package / "study_lock.json").read_text(encoding="utf-8-sig"))
    table = package / "records/validation_cases.csv"
    manifest_path = package / "manifests/breast_external.csv"
    assert digest(table) == lock["files_sha256"]["records/validation_cases.csv"]
    assert digest(manifest_path) == lock["files_sha256"]["manifests/breast_external.csv"]
    external = [r for r in rows(table) if r["split"] == "external_test"]
    failures = [r for r in external if float(r["dice_vs_reference"]) < .7]
    selected = [r for r in failures if int(r["alert_A"]) == 0]
    assert len(external) == 252 and len(failures) == 16 and len(selected) == 6
    manifests = {r["image_id"]: r for r in rows(manifest_path)}
    thresholds = {m: lock["threshold_lock"]["methods"][m]["threshold"] for m in ("A", "B")}
    out = []
    for r in sorted(selected, key=lambda r: (int(r["alert_B"]), int(r["patient_id"]))):
        m = manifests[r["image_id"]]
        assert all(r[k] == m[k] for k in ("patient_id", "image_id", "pathology", "split"))
        assert abs((1-float(r["sam_predicted_iou"]))-float(r["risk_A"])) < 1e-15
        consistency = [float(r["dice_shift_"+d]) for d in DIRECTIONS]
        assert abs((1-sum(consistency)/4)-float(r["risk_B"])) < 1e-15
        assert all(int(r["alert_"+k]) == int(float(r["risk_"+k]) >= t)
                   for k, t in thresholds.items())
        image, reference, changed = load_pair(source, m)
        assert changed == (int(r["patient_id"]) in lock["external_alpha_changed_ids"])
        out.append({"group": "both_missed" if int(r["alert_B"]) == 0 else "B_only_detected",
                    **r, "threshold_A": thresholds["A"], "threshold_B": thresholds["B"],
                    "risk_A_minus_threshold": float(r["risk_A"])-thresholds["A"],
                    "risk_B_minus_threshold": float(r["risk_B"])-thresholds["B"],
                    "mean_prompt_consistency_dice": sum(consistency)/4,
                    "image_path": m["image_path"], "reference_path": m["mask_path"],
                    "image_sha256": m["image_sha256"], "reference_sha256": m["mask_sha256"],
                    "width": image.shape[1], "height": image.shape[0],
                    "reference_foreground_pixels": int(reference.sum()),
                    "alpha_compositing_changes_pixels": changed,
                    "archived_initial_prediction_nonempty": int(r["initial_mask_empty"]) == 0,
                    "all_shifted_predictions_nonempty_proven_by_positive_dice": min(consistency)>0,
                    "saved_prediction_available_before_v7": False})
    assert sum(r["group"] == "both_missed" for r in out) == 3
    return lock, manifests, out


def audit(source, output):
    output.mkdir(parents=True, exist_ok=True)
    lock, manifests, selected = audited_records(source)
    write_csv(output / "external_six_cases.csv", selected)
    # Inventory the only archived external prediction-array artifact.
    example = source / "figures/source/example_case.npz"
    meta = json.loads((example.with_suffix(".json")).read_text())
    assert digest(example) == meta["artifact_sha256"]
    case1 = next(r for r in rows(source / "reproducibility/records/validation_cases.csv")
                 if r["split"] == "external_test" and r["image_id"] == "case001")
    with np.load(example, allow_pickle=False) as z:
        assert float(case1["dice_vs_reference"]) == dice(z["masks"][0], z["reference"])
        risk_b = 1-sum(dice(z["masks"][0], x) for x in z["masks"][1:])/4
        assert risk_b == float(case1["risk_B"])
        example_info = {"path": str(example), "image_id": meta["case"],
                        "sha256": digest(example), "keys": list(z.files),
                        "initial_prediction_pixels": int(z["masks"][0].sum()),
                        "dice_vs_reference": float(case1["dice_vs_reference"]),
                        "risk_A": float(case1["risk_A"]), "risk_B": risk_b,
                        "alert_A": int(case1["alert_A"]), "alert_B": int(case1["alert_B"]),
                        "belongs_to_target_six": False,
                        "finding": "Both methods flag case001; it cannot illustrate a target miss."}
    inventory = [str(p.relative_to(source)) for p in source.rglob("*.npz")]
    evidence = {"audit_date_utc": datetime.now(timezone.utc).isoformat(),
                "source_repository": "https://github.com/khkh87885-code/research",
                "archived_study_commit": "592566b4c5f39e261c676eb034139a974e9cdfd5",
                "source_root": str(source),
                "score_table_sha256": digest(source / "reproducibility/records/validation_cases.csv"),
                "study_lock_sha256": digest(source / "reproducibility/study_lock.json"),
                "selection": "All external Dice<0.70 cases unflagged by A, partitioned by B flag; no visual cherry-picking",
                "external_case_count": 252, "external_low_quality_count": 16,
                "thresholds": {m: lock["threshold_lock"]["methods"][m]["threshold"] for m in ("A", "B")},
                "cases": selected, "npz_inventory": inventory,
                "archived_external_example": example_info,
                "target_predictions_available_before_v7": 0,
                "model_rerun_performed": False,
                "interpretation": "Saved scores establish high confidence and prompt stability in shared misses, not the spatial error mechanism. Dice/risk do not identify empty masks.",
                "missing_for_complete_target_prediction_figure": "Actual initial masks for all six targets; rerun requires exact checkpoint/source and documented environment."}
    write_json(output / "external_case_audit.json", evidence)
    lines = ["# External missed-case audit", "", "This is a post hoc descriptive audit of all six external low-quality cases missed by method A, not a new confirmatory comparison.", "",
             f"Locked thresholds (review if risk >= cutoff): A={evidence['thresholds']['A']}; B={evidence['thresholds']['B']}. Low quality is reference Dice <0.70.", "",
             "| Group | Case | Archived pathology | Reference Dice | Risk A | A flag | Risk B | B flag |",
             "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |"]
    for r in selected:
        lines.append(f"| {r['group']} | {r['image_id']} | {r['pathology']} | {float(r['dice_vs_reference']):.6f} | {float(r['risk_A']):.6f} | {r['alert_A']} | {float(r['risk_B']):.6f} | {r['alert_B']} |")
    lines += ["", "## What the archived scores establish", "",
              "Both methods miss case089, case175 and case238. Their mean initial-to-shifted Dice values are 0.958959, 0.979941 and 0.994234, respectively: stable predictions can still have low agreement with the released reference. Case175 has reference Dice 0.029287 despite a predicted IoU of 0.885056. This is a confidence/stability screening miss, not evidence of an empty mask.", "",
              "B additionally flags case024, case105 and case222, whose A risks stay below the locked cutoff. In case105 the left shift has Dice 0.246456 while the other three comparisons are approximately 0.90–0.91. The scores describe perturbation sensitivity; without captured predictions they do not establish a particular anatomical or contour-error cause.", "",
              "The archived initial-empty flags are zero for all six. Every shifted-versus-initial Dice value is positive, which independently excludes an empty shifted prediction when the initial mask is nonempty. No empty mask is inferred from low reference Dice or low risk.", "",
              "## Available image and prediction evidence", "",
              "All six original PNG images and primary tumor references exist and match their frozen manifest SHA-256 values. Pathology is the original binary archived category, not a new clinical diagnosis. The stored reference is never presented as a SAM prediction.", "",
              "Only figures/source/example_case.npz contains archived external predicted masks; it is case001. Its actual Dice/risk values reproduce the archive, and both A and B flag it. It cannot replace any of the requested six missed cases. No saved target predicted masks were located in the source repository.", "",
              "A complete original-image/reference/initial-prediction illustration therefore needs a verified exact-model rerun. The companion rerun command captures all five actual outputs, records their arrays and environment, and compares eight numerical fields and decisions to the original scores. Until that is executed, no target prediction panel is claimed as complete.", "",
              "## Commands", "", "```bash", "python external_case_audit.py audit --source /path/to/research --output /path/to/new/evidence", "python external_case_audit.py rerun --source /path/to/research --output /path/to/new/rerun --sam-source /path/to/clean/segment-anything --checkpoint /path/to/sam_vit_b_01ec64.pth --device cpu", "```", "",
              "The rerun refuses a mismatched source commit or checkpoint digest. CPU use is a new environment, not the original RTX run. Exact matches are measured, not assumed. No original data or archived scores are overwritten."]
    (output / "external_case_audit.md").write_text("\n".join(lines)+"\n")
    print(json.dumps({"case_count": len(selected), "groups": {g: [r["image_id"] for r in selected if r["group"]==g] for g in ("both_missed", "B_only_detected")}, "output": str(output)}, indent=2))


def plot_captured(records, destination):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})
    fig, axes = plt.subplots(len(records), 3, figsize=(10, 3*len(records)), squeeze=False)
    for row, record in enumerate(records):
        with np.load(destination / record["artifact"], allow_pickle=False) as z:
            image, reference, prediction, box = z["image"], z["reference"], z["masks"][0], z["boxes"][0]
            for col, ax in enumerate(axes[row]):
                ax.imshow(image, interpolation="nearest")
                ax.set_axis_off()
                if col == 1:
                    ax.contour(reference, levels=[.5], colors=["#28c76f"], linewidths=1)
                if col == 2 and prediction.any():
                    ax.contour(prediction, levels=[.5], colors=["#ff7f00"], linewidths=1)
                if col == 0:
                    ax.add_patch(Rectangle((box[0], box[1]), box[2]-box[0], box[3]-box[1], fill=False, edgecolor="#59c8ff", linewidth=1))
            label = record["image_id"] + " | " + record["archived_group"]
            axes[row, 0].set_title(label + "\nOriginal + reference-derived prompt", fontsize=9)
            axes[row, 1].set_title("Released primary reference (green)", fontsize=9)
            axes[row, 2].set_title("Actual targeted rerun prediction (orange)\n" +
                                   f"Dice {record['rerun']['dice_vs_reference']:.4f}; " +
                                   f"A {record['rerun']['risk_A']:.4f}; B {record['rerun']['risk_B']:.4f}", fontsize=9)
    fig.tight_layout(pad=1.2)
    fig.savefig(destination / "external_six_case_predictions.png", dpi=300)
    fig.savefig(destination / "external_six_case_predictions.pdf")
    plt.close(fig)


def plot_sources(source, output):
    """Inspection sheet only: never substitute references for predictions."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    _, manifests, selected = audited_records(source)
    output.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(6, 2, figsize=(8, 17), squeeze=False)
    for index, record in enumerate(selected):
        image, reference, _ = load_pair(source, manifests[record["image_id"]])
        for col, ax in enumerate(axes[index]):
            ax.imshow(image, interpolation="nearest")
            ax.set_axis_off()
            if col == 1:
                ax.contour(reference, levels=[.5], colors=["#28c76f"], linewidths=1)
        axes[index, 0].set_title(record["image_id"]+" | "+record["group"]+"\nOriginal released image", fontsize=9)
        axes[index, 1].set_title("Released reference (green)\nNo SAM prediction is shown", fontsize=9)
    fig.suptitle("Source-pair audit only: target prediction arrays are not available", fontsize=12)
    fig.tight_layout(pad=1.3, rect=(0, 0, 1, .98))
    fig.savefig(output / "external_six_case_source_pairs.png", dpi=180)
    fig.savefig(output / "external_six_case_source_pairs.pdf")
    plt.close(fig)


def rerun(args):
    import torch
    import torchvision
    source, output = args.source.resolve(), args.output.resolve()
    assert not output.exists(), "Use a new output directory; never overwrite a prior rerun"
    lock, manifests, selected = audited_records(source)
    model_info = lock["threshold_lock"]["model"]
    assert digest(args.checkpoint) == model_info["weight_sha256"], "Checkpoint SHA-256 mismatch"
    sam_source = args.sam_source.resolve()
    git = ["git", "--no-optional-locks", "-C", str(sam_source)]
    commit = subprocess.check_output(git+["rev-parse", "HEAD"], text=True).strip()
    dirty = subprocess.check_output(git+["status", "--porcelain"], text=True).strip()
    assert commit == model_info["source_commit"] and not dirty, "SAM source must be clean and exact"
    sys.path.insert(0, str(sam_source))
    import segment_anything
    assert sam_source in Path(segment_anything.__file__).resolve().parents
    torch.set_num_threads(args.threads)
    device = torch.device(args.device)
    assert device.type != "cuda" or torch.cuda.is_available()
    model = segment_anything.sam_model_registry["vit_b"]()
    state = torch.load(args.checkpoint, map_location="cpu", weights_only=True)
    model.load_state_dict(state, strict=True)
    del state
    model.to(device).eval()
    assert next(model.parameters()).dtype == torch.float32
    predictor = segment_anything.SamPredictor(model)
    output.mkdir(parents=True)
    environment = {"python": platform.python_version(), "platform": platform.platform(),
                   "torch": torch.__version__, "torchvision": torchvision.__version__,
                   "numpy": np.__version__, "pillow": PILLOW_VERSION,
                   "device": str(device), "threads": torch.get_num_threads(),
                   "gpu_name": torch.cuda.get_device_name(0) if device.type=="cuda" else None,
                   "cuda_runtime": torch.version.cuda,
                   "weight_dtype": str(next(model.parameters()).dtype),
                   "original_environment": lock["environment"],
                   "same_environment_as_original": False}
    receipt = {"status": "running", "started_at_utc": datetime.now(timezone.utc).isoformat(),
               "scope": "Only the six archived external A-missed cases; not a full-cohort rerun",
               "checkpoint_sha256": digest(args.checkpoint), "sam_source_commit": commit,
               "environment": environment, "cases": []}
    write_json(output / "targeted_rerun_receipt.json", receipt)
    with torch.inference_mode():
        for r in selected:
            image, reference, _ = load_pair(source, manifests[r["image_id"]])
            boxes = prompt_boxes(reference)
            start = perf_counter()
            predictor.set_image(image)
            masks, raw_scores = [], []
            for box in boxes:
                m, s, _ = predictor.predict(box=box, multimask_output=False)
                assert m.shape == (1, *reference.shape) and s.shape == (1,)
                masks.append(m[0].astype(bool)); raw_scores.append(float(s[0]))
            if device.type == "cuda":
                torch.cuda.synchronize(device)
            seconds = perf_counter()-start
            predictor.reset_image()
            consistency = [dice(masks[0], x) for x in masks[1:]]
            values = {"dice_vs_reference": dice(masks[0], reference),
                      "sam_predicted_iou": raw_scores[0], "risk_A": 1-raw_scores[0],
                      "risk_B": 1-sum(consistency)/4,
                      **{"dice_shift_"+d: v for d,v in zip(DIRECTIONS, consistency)}}
            artifact = r["image_id"]+"_targeted_rerun.npz"
            np.savez_compressed(output / artifact, image=image, reference=reference,
                                masks=np.stack(masks), boxes=boxes,
                                raw_predicted_ious=np.asarray(raw_scores))
            flags = {"alert_"+m: int(values["risk_"+m] >= r["threshold_"+m]) for m in ("A", "B")}
            comparison = {k: {"archived": float(r[k]), "rerun": values[k],
                              "difference": values[k]-float(r[k]),
                              "exact_match": values[k]==float(r[k])} for k in FIELDS}
            entry = {"image_id": r["image_id"], "patient_id": r["patient_id"],
                     "archived_group": r["group"], "pathology": r["pathology"],
                     "archived": {k: float(r[k]) for k in FIELDS}, "rerun": values,
                     "comparison": comparison, "rerun_flags": flags,
                     "archived_flags": {"alert_"+m: int(r["alert_"+m]) for m in ("A", "B")},
                     "flags_match": all(flags["alert_"+m]==int(r["alert_"+m]) for m in ("A", "B")),
                     "rerun_low_quality": values["dice_vs_reference"]<.7,
                     "low_quality_label_match": int(values["dice_vs_reference"]<.7)==int(r["low_quality"]),
                     "prediction_pixel_counts": [int(m.sum()) for m in masks],
                     "elapsed_seconds_current_environment": seconds,
                     "artifact": artifact, "artifact_sha256": digest(output / artifact)}
            receipt["cases"].append(entry)
            write_json(output / "targeted_rerun_receipt.json", receipt)
            print(json.dumps({"image_id": r["image_id"], "seconds": seconds,
                              "max_abs_difference": max(abs(x["difference"]) for x in comparison.values()),
                              "flags_match": entry["flags_match"]}), flush=True)
    receipt.update(status="complete", completed_at_utc=datetime.now(timezone.utc).isoformat(),
                   all_flags_match=all(x["flags_match"] for x in receipt["cases"]),
                   all_fields_exact=all(v["exact_match"] for x in receipt["cases"] for v in x["comparison"].values()),
                   max_absolute_difference=max(abs(v["difference"]) for x in receipt["cases"] for v in x["comparison"].values()))
    write_json(output / "targeted_rerun_receipt.json", receipt)
    plot_captured(receipt["cases"], output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("audit", "sources", "rerun"))
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sam-source", type=Path)
    parser.add_argument("--checkpoint", type=Path)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--threads", type=int, default=2)
    args = parser.parse_args()
    if args.command == "audit":
        audit(args.source.resolve(), args.output.resolve())
    elif args.command == "sources":
        plot_sources(args.source.resolve(), args.output.resolve())
    else:
        assert args.sam_source and args.checkpoint, "Rerun requires exact source and checkpoint"
        rerun(args)


if __name__ == "__main__":
    main()
