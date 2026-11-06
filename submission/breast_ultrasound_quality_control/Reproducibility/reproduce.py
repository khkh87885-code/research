"""Reproduce the breast ultrasound study from archived scores or original images."""
import argparse
from collections import defaultdict
import csv
from fractions import Fraction
import json
from pathlib import Path
import sys

from study_statistics import (
    METHODS, describe_cohort, file_hash, main_results, require, supplementary_results,
)


ROOT = Path(__file__).resolve().parent
TEST_SPLITS = ("internal_holdout", "external_test")
SCORE_FIELDS = ("dice_vs_reference", "sam_predicted_iou", "risk_A", "risk_B",
                "dice_shift_left", "dice_shift_right", "dice_shift_up", "dice_shift_down")
FLAG_FIELDS = ("low_quality", "alert_A", "alert_B", "initial_mask_empty", "distinct_perturbed_boxes")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def write_json(path, data):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(data, stream, indent=2, allow_nan=False)
        stream.write("\n")


def identity(row):
    return int(row["patient_id"]), row["image_id"], row["pathology"]


def verified_inputs():
    lock_path = ROOT / "study_lock.json"
    lock = read_json(lock_path)
    require(lock["version"] == 1, "Unsupported release version")
    for name, digest in lock["files_sha256"].items():
        path = (ROOT / name).resolve(strict=True)
        require(ROOT in path.parents and file_hash(path) == digest,
                f"Release record missing or changed: {name}")
    manifests = {}
    for split, entry in lock["cohorts"].items():
        rows = read_rows(ROOT / entry["manifest"])
        require(len(rows) == entry["count"] == len({int(r["patient_id"]) for r in rows})
                and all(r["dataset"] == entry["dataset"] and r["split"] == split for r in rows),
                f"Invalid case manifest for {split}")
        manifests[split] = sorted(rows, key=lambda row: int(row["patient_id"]))
    dev_ids = {int(row["patient_id"]) for row in manifests["development"]}
    require(dev_ids.isdisjoint(int(row["patient_id"]) for row in manifests["internal_holdout"]),
            "Development and internal testing share patients")
    return lock, manifests, file_hash(lock_path)


def verify_rows(groups, manifests):
    require(set(groups) == set(manifests), "Expected the three fixed cohorts")
    for split, cases in groups.items():
        manifest = manifests[split]
        require(len(cases) == len(manifest)
                and sorted(map(identity, cases)) == sorted(map(identity, manifest))
                and all(row["split"] == split and row["dataset"] == manifest[0]["dataset"]
                        for row in cases), f"Scores differ from the case manifest for {split}")
        cases.sort(key=lambda row: int(row["patient_id"]))


def archived_scores(config, manifests):
    grouped = defaultdict(list)
    for row in read_rows(ROOT / config["cohorts"]["development"]["archived_scores"]):
        row.update(dataset="BUS-BRA", split="development")
        for method in METHODS:
            row[f"alert_{method}"] = row[f"candidate_alert_{method}"]
        grouped["development"].append(row)
    for row in read_rows(ROOT / config["cohorts"]["internal_holdout"]["archived_scores"]):
        grouped[row["split"]].append(row)
    verify_rows(grouped, manifests)
    return grouped


def fresh_scores(run, config, manifests, lock_sha):
    receipt = read_json(run / "run_receipt.json")
    model = config["threshold_lock"]["model"]
    source = run / "scores.csv"
    require(receipt["version"] == 1 and receipt["study_lock_sha256"] == lock_sha
            and receipt["scores_sha256"] == file_hash(source)
            and receipt["sam_commit"] == model["source_commit"]
            and receipt["checkpoint_sha256"] == model["weight_sha256"]
            and receipt["archive_sha256"] == {
                name: data["archive_sha256"] for name, data in config["datasets"].items()
            }, "Run receipt, inputs or score checksum differ from this release")
    grouped = defaultdict(list)
    for row in read_rows(source):
        require(row["sam_commit"] == receipt["sam_commit"]
                and row["checkpoint_sha256"] == receipt["checkpoint_sha256"],
                "A score row reports a different model")
        grouped[row["split"]].append(row)
    verify_rows(grouped, manifests)
    for split, rows in grouped.items():
        require(receipt["cohorts"][split] == {
            "scheduled": len(rows), "scored": sum(row["status"] == "scored" for row in rows),
        }, f"Run counts differ for {split}")
    return grouped, receipt


def calibration(rows, locked, thresholds):
    quality = locked["quality_reference"]["cutoff"]
    cohort = describe_cohort(rows, quality, thresholds)
    scored = [row for row in rows if row["status"] == "scored"]
    require(scored, "No scored development cases")
    target = Fraction(str(locked["calibration"]["review_target_fraction"]))
    report = {}
    for method in METHODS:
        grouped = defaultdict(list)
        for row in scored:
            grouped[float(row[f"risk_{method}"])].append(int(row["low_quality"]))
        # None represents a cutoff above the maximum score and flags zero cases.
        points = [(None, 0, 0)]
        reviewed = detected = 0
        for score, labels in sorted(grouped.items(), reverse=True):
            reviewed += len(labels)
            detected += sum(labels)
            points.append((score, reviewed, detected))
        cutoff, reviewed, detected = min(points, key=lambda point: (
            abs(target.denominator * point[1] - target.numerator * len(scored)), point[1],
        ))
        expected = locked["methods"][method]
        fixed = cohort["methods"][method]
        report[method] = {
            "recomputed_threshold": cutoff, "recomputed_reviews": reviewed,
            "recomputed_detections": detected, "locked_reviews": fixed["R"],
            "locked_detections": fixed["TP"],
            "matches_original": (
                cutoff == expected["threshold"] and reviewed == fixed["R"] == expected["development_review_count"]
                and detected == fixed["TP"] == expected["development_low_quality_detected"]
            ),
        }
    return {"N": cohort["N"], "F": cohort["F"], "methods": report}


def score_comparison(observed, archived):
    result = {}
    for split, rows in observed.items():
        maxima = {key: 0.0 for key in SCORE_FIELDS}
        changed_scores = changed_flags = changed_status = compared = 0
        for row, original in zip(rows, archived[split]):
            if row["status"] != original["status"]:
                changed_status += 1
            if row["status"] != "scored" or original["status"] != "scored":
                continue
            compared += 1
            diffs = {key: abs(float(row[key]) - float(original[key])) for key in SCORE_FIELDS}
            changed_scores += any(diffs.values())
            changed_flags += any(row[key] != original[key] for key in FLAG_FIELDS)
            for key, value in diffs.items():
                maxima[key] = max(maxima[key], value)
        result[split] = {
            "rows": len(rows), "scored_rows_compared": compared,
            "rows_with_numeric_difference": changed_scores,
            "rows_with_flag_difference": changed_flags,
            "rows_with_status_difference": changed_status,
            "maximum_absolute_difference": maxima if compared else None,
        }
    return result


def curve_data(path, groups):
    with path.open("x", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(("dataset", "split", "method", "reviewed", "scored_patients",
                         "low_quality_detected", "low_quality_patients"))
        for split, rows in groups.items():
            cases = [row for row in rows if row["status"] == "scored"]
            low = sum(int(row["low_quality"]) for row in cases)
            for method in METHODS:
                ranked = sorted(cases, key=lambda row: (-float(row[f"risk_{method}"]), row["patient_id"]))
                detected = 0
                writer.writerow((rows[0]["dataset"], split, method, 0, len(cases), 0, low))
                for k, case in enumerate(ranked, 1):
                    detected += int(case["low_quality"])
                    writer.writerow((rows[0]["dataset"], split, method, k, len(cases), detected, low))


def analyze(args, lock, manifests, lock_sha):
    reference = archived_scores(lock, manifests)
    observed, receipt = fresh_scores(args.run, lock, manifests, lock_sha) if args.run else (reference, None)
    settings = lock["threshold_lock"]
    require(settings["alert_operator"] == ">="
            and settings["quality_reference"]["low_quality_operator"] == "<", "Unexpected locked decision rule")
    thresholds = {method: settings["methods"][method]["threshold"] for method in METHODS}
    replay = calibration(observed["development"], settings, thresholds)
    groups = {split: observed[split] for split in TEST_SPLITS}
    dev_budget = {m: replay["methods"][m]["locked_reviews"] for m in METHODS}
    primary = main_results(groups, settings["quality_reference"], thresholds, dev_budget)
    supp = supplementary_results(groups, primary, settings["calibration"]["review_target_fraction"])
    matches = {
        "calibration_matches_archive": all(r["matches_original"] for r in replay["methods"].values())
            and (replay["N"], replay["F"]) == (settings["calibration"]["patients"],
                                               settings["calibration"]["low_quality_count"]),
        "primary_matches_archive": primary == read_json(ROOT / "reference/primary.json"),
        "supplementary_matches_archive": json.loads(json.dumps(supp, allow_nan=False))
            == read_json(ROOT / "reference/supplementary.json"),
    }
    report = {
        "route": "original_image_rerun" if receipt else "archived_scores",
        "study_lock_sha256": lock_sha,
        "analysis_python": sys.version.split()[0],
        "matches": matches,
        "scored_rows": primary["scored_patients"],
        "development_rows": replay["N"],
    }
    if receipt:
        report["inference_receipt"] = receipt
        report["score_comparison"] = score_comparison(observed, reference)
    output = args.output.resolve()
    output.mkdir()
    write_json(output / "calibration.json", replay)
    write_json(output / "primary.json", primary)
    write_json(output / "supplementary.json", supp)
    write_json(output / "verification.json", report)
    curve_data(output / "review_curve_counts.csv", groups)
    print(json.dumps({"route": report["route"], **matches,
                      "scored_test_rows": report["scored_rows"]}, allow_nan=False))
    return 0 if all(matches.values()) else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    stats = sub.add_parser("analyze", help="Recompute locked statistics and curve counts")
    stats.add_argument("--run", type=Path, help="Use a completed image scoring directory")
    stats.add_argument("--output", required=True, type=Path, help="New output directory")
    score = sub.add_parser("score", help="Score the original images using the locked SAM setup")
    for flag in ("busbra-archive", "breast-archive", "sam-source", "checkpoint", "output"):
        score.add_argument("--" + flag, required=True, type=Path)
    args = parser.parse_args()
    lock, manifests, lock_sha = verified_inputs()
    require(not args.output.exists(), "Choose a new output directory")
    if args.command == "analyze":
        return analyze(args, lock, manifests, lock_sha)
    from score_images import run_score
    run_score(args, lock, manifests, lock_sha)
    return 0


if __name__ == "__main__":
    sys.exit(main())
