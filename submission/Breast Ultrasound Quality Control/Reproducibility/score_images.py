"""Score the locked cohorts from the original image archives."""
import csv
from datetime import datetime, timezone
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path
import subprocess
import sys
from time import perf_counter
from zipfile import ZipFile

import numpy as np
from PIL import Image, __version__ as PILLOW_VERSION
import torch
import torchvision

from study_statistics import METHODS, file_hash, require


BORDER_FRACTION = 0.10
SHIFT_FRACTION = 0.05
LOW_QUALITY_DICE = 0.70
RESULT_FIELDS = (
    "dataset", "split", "patient_id", "image_id", "pathology", "sam_commit",
    "checkpoint_sha256", "status", "retries", "error", "dice_vs_reference",
    "low_quality", "sam_predicted_iou", "risk_A", "risk_B", "alert_A", "alert_B",
    "dice_shift_left", "dice_shift_right", "dice_shift_up", "dice_shift_down",
    "initial_mask_empty", "distinct_perturbed_boxes", "inference_ms",
)


def dice(first, second):
    total = int(first.sum()) + int(second.sum())
    if total == 0:
        return 1.0
    return 2.0 * np.count_nonzero(first & second) / total


def prompt_boxes(reference):
    height, width = reference.shape
    rows, columns = np.nonzero(reference)
    left, top = columns.min(), rows.min()
    right, bottom = columns.max() + 1, rows.max() + 1
    pad_x = BORDER_FRACTION * (right - left)
    pad_y = BORDER_FRACTION * (bottom - top)
    limits = np.array([width, height, width, height], dtype=np.float32)
    base = np.clip(
        np.array([left - pad_x, top - pad_y, right + pad_x, bottom + pad_y], dtype=np.float32),
        0,
        limits,
    )
    shift_x = SHIFT_FRACTION * float(base[2] - base[0])
    shift_y = SHIFT_FRACTION * float(base[3] - base[1])
    shifts = {
        "left": [-shift_x, 0, -shift_x, 0],
        "right": [shift_x, 0, shift_x, 0],
        "up": [0, -shift_y, 0, -shift_y],
        "down": [0, shift_y, 0, shift_y],
    }
    shifted = {
        name: np.clip(base + np.asarray(offset, dtype=np.float32), 0, limits)
        for name, offset in shifts.items()
    }
    return base, shifted


def png_bytes(archive, row, kind):
    data = archive.read(row[f"{kind}_path"])
    digest = row.get(f"{kind}_sha256")
    if digest is not None:
        require(hashlib.sha256(data).hexdigest() == digest,
                f"Unexpected {kind} bytes for {row['image_id']}")
    return data


def measure_case(row, predictor, device, archive, alpha_changed):
    with Image.open(BytesIO(png_bytes(archive, row, "image"))) as image:
        require(image.format == "PNG", f"Expected a PNG for {row['image_id']}")
        original = image.convert("RGB")
        if row["dataset"] == "BrEaST":
            rgba = image.convert("RGBA")
            black = Image.new("RGBA", rgba.size, (0, 0, 0, 255))
            composite = Image.alpha_composite(black, rgba).convert("RGB")
            require((composite.tobytes() != original.tobytes()) ==
                    (int(row["patient_id"]) in alpha_changed),
                    f"Unexpected transparency decoding for {row['image_id']}")
            original = composite
        rgb = np.array(original, dtype=np.uint8)
    with Image.open(BytesIO(png_bytes(archive, row, "mask"))) as mask:
        require(mask.format == "PNG", f"Expected a PNG mask for {row['image_id']}")
        reference = np.array(mask.convert("1"), dtype=bool)

    width, height = int(row["width"]), int(row["height"])
    if rgb.shape != (height, width, 3) or reference.shape != (height, width) or not reference.any():
        raise ValueError(f"Invalid image and reference pair for {row['image_id']}.")
    base, shifted = prompt_boxes(reference)
    start = perf_counter()
    predictor.set_image(rgb)
    masks, scores, _ = predictor.predict(box=base, multimask_output=False)
    if masks.shape != (1, height, width) or scores.shape != (1,):
        raise RuntimeError(f"Unexpected SAM output shape for {row['image_id']}.")
    prediction = masks[0].astype(bool)
    predicted_iou = float(scores[0])
    consistency = {}
    for direction, box in shifted.items():
        masks, _, _ = predictor.predict(box=box, multimask_output=False)
        if masks.shape != (1, height, width):
            raise RuntimeError(f"Unexpected perturbed mask shape for {row['image_id']}.")
        consistency[f"dice_shift_{direction}"] = dice(prediction, masks[0].astype(bool))
    torch.cuda.synchronize(device)
    elapsed_ms = 1000 * (perf_counter() - start)
    predictor.reset_image()

    reference_dice = dice(prediction, reference)
    risk_a = 1.0 - predicted_iou
    risk_b = 1.0 - sum(consistency.values()) / len(consistency)
    if not np.isfinite([reference_dice, risk_a, risk_b]).all():
        raise RuntimeError(f"A metric is non-finite for {row['image_id']}.")
    return {
        "patient_id": int(row["patient_id"]),
        "image_id": row["image_id"],
        "pathology": row["pathology"],
        "dice_vs_reference": reference_dice,
        "low_quality": int(reference_dice < LOW_QUALITY_DICE),
        "sam_predicted_iou": predicted_iou,
        "risk_A": risk_a,
        "risk_B": risk_b,
        **consistency,
        "initial_mask_empty": int(not prediction.any()),
        "distinct_perturbed_boxes": len({tuple(box) for box in shifted.values()}),
        "inference_ms": elapsed_ms,
    }


def run_patient(row, predictor, device, archive, alpha_changed):
    errors = []
    for attempt in range(2):
        try:
            result = measure_case(row, predictor, device, archive, alpha_changed)
        except (OSError, ValueError, RuntimeError) as error:
            errors.append(f"{type(error).__name__}: {error}")
            predictor.reset_image()
            if isinstance(error, torch.cuda.OutOfMemoryError):
                torch.cuda.empty_cache()
        else:
            result.update(status="scored", retries=attempt, error=" | ".join(errors))
            return result
    return {
        "patient_id": int(row["patient_id"]),
        "image_id": row["image_id"],
        "pathology": row["pathology"],
        "status": "failed",
        "retries": 1,
        "error": " | ".join(errors),
    }


def run_score(args, config, manifests, lock_sha):
    locked = config["threshold_lock"]
    model_info = locked["model"]
    require(model_info["prompt_box_expansion_per_side"] == BORDER_FRACTION
            and model_info["prompt_box_shift_fraction"] == SHIFT_FRACTION
            and locked["quality_reference"]["cutoff"] == LOW_QUALITY_DICE
            and model_info["multimask_output"] is False,
            "Model geometry differs from the locked experiment")
    actual = {
        "python": sys.version.split()[0], "torch": torch.__version__,
        "torchvision": torchvision.__version__, "pillow": PILLOW_VERSION,
        "numpy": np.__version__,
    }
    for key, value in actual.items():
        require(value == config["environment"][key],
                f"Wrong {key} version: {value}. Expected {config['environment'][key]}.")
    require(torch.cuda.is_available(), "CUDA is required for the verified inference environment")
    device = torch.device("cuda:0")
    actual.update(gpu=torch.cuda.get_device_name(0), cuda=torch.version.cuda)

    sources = {"BUS-BRA": args.busbra_archive, "BrEaST": args.breast_archive}
    archive_hashes = {name: file_hash(path) for name, path in sources.items()}
    require(all(digest == config["datasets"][name]["archive_sha256"]
                for name, digest in archive_hashes.items()),
            "An archive differs from the version used for the study")
    checkpoint_hash = file_hash(args.checkpoint)
    require(checkpoint_hash == model_info["weight_sha256"], "SAM checkpoint SHA-256 mismatch")
    source = args.sam_source.resolve(strict=True)
    git = ["git", "--no-optional-locks", "-C", str(source)]
    commit = subprocess.check_output(git + ["rev-parse", "--verify", "HEAD"], text=True).strip()
    changed = subprocess.check_output(git + ["status", "--porcelain"], text=True).strip()
    require(commit == model_info["source_commit"] and not changed,
            "SAM source must be a clean checkout of the recorded commit")
    sys.path.insert(0, str(source))
    import segment_anything
    require(source in Path(segment_anything.__file__).resolve().parents,
            "The imported SAM code did not come from the checked checkout")
    print(f"Verified image archives, SAM source, checkpoint, and {actual['gpu']}.", flush=True)
    started = datetime.now(timezone.utc).isoformat()

    output = args.output.resolve()
    output.mkdir()
    model = segment_anything.sam_model_registry["vit_b"]()
    state = torch.load(args.checkpoint, map_location="cpu", weights_only=True)
    model.load_state_dict(state, strict=True)
    del state
    model.to(device).eval()
    require(next(model.parameters()).dtype == torch.float32, "SAM weights must be float32")
    predictor = segment_anything.SamPredictor(model)
    alpha_changed = set(config["external_alpha_changed_ids"])
    thresholds = {method: locked["methods"][method]["threshold"] for method in METHODS}
    results = []
    counts = {}
    with ZipFile(sources["BUS-BRA"]) as bus, ZipFile(sources["BrEaST"]) as breast:
        archives = {"BUS-BRA": bus, "BrEaST": breast}
        for split, cohort in manifests.items():
            archive = archives[config["cohorts"][split]["dataset"]]
            members = archive.namelist()
            require(len(members) == len(set(members)), "The image archive contains duplicate paths")
            names = set(members)
            require(all(row[field] in names for row in cohort for field in ("image_path", "mask_path")),
                    f"Image archive members are missing for {split}")
        with torch.inference_mode():
            for split, cohort in manifests.items():
                archive = archives[config["cohorts"][split]["dataset"]]
                scored = 0
                for i, row in enumerate(cohort, 1):
                    result = run_patient(row, predictor, device, archive, alpha_changed)
                    result.update(dataset=row["dataset"], split=split, sam_commit=commit,
                                  checkpoint_sha256=checkpoint_hash)
                    if result["status"] == "scored":
                        scored += 1
                        for method in METHODS:
                            result[f"alert_{method}"] = int(result[f"risk_{method}"] >= thresholds[method])
                    results.append(result)
                    if i % 50 == 0 or i == len(cohort):
                        print(f"{split}: {i}/{len(cohort)} processed, {scored} scored", flush=True)
                counts[split] = {"scheduled": len(cohort), "scored": scored}

    path = output / "scores.csv"
    with path.open("x", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=RESULT_FIELDS)
        writer.writeheader()
        writer.writerows(results)
    receipt = {
        "version": 1,
        "study_lock_sha256": lock_sha,
        "scores_sha256": file_hash(path),
        "archive_sha256": archive_hashes,
        "sam_commit": commit,
        "checkpoint_sha256": checkpoint_hash,
        "runtime": actual,
        "cohorts": counts,
        "started_at_utc": started,
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    with (output / "run_receipt.json").open("x", encoding="utf-8") as stream:
        json.dump(receipt, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(f"Scored {sum(group['scored'] for group in counts.values())}/{len(results)} patients.", flush=True)
