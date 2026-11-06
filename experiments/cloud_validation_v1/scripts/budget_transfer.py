#!/usr/bin/env python3
"""Post hoc development-calibrated budget sweep; archived scores only.

Example:
  python scripts/budget_transfer.py --source-root /workspace/research_source \
      --output-root /workspace/bmt_cloud_validation

Uses the source release's verified Wilson/Newcombe implementation, preserving
the original H1--H3 results. No model inference, stochastic sampling or p-values.
"""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

# Keep all source directories read-only, including Python's bytecode cache.
sys.dont_write_bytecode = True
os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

METHODS = ("A", "B")
SPLITS = ("internal_holdout", "external_test")
MODE_FIXED = "development_calibrated_threshold"
MODE_EQUAL = "test_cohort_equal_review"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def read_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")


def write_csv(path, rows):
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with Path(path).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def load_inputs(source, plan):
    commit = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
    require(commit == plan["source_commit"], "Source commit differs from fixed protocol.")
    release = source / "reproducibility"
    lock_path = release / "study_lock.json"
    lock = read_json(lock_path)
    hashes = {"reproducibility/study_lock.json": sha256(lock_path)}
    for rel, expected in lock["files_sha256"].items():
        path = (release / rel).resolve()
        require(release.resolve() in path.parents, "Input escapes release directory.")
        actual = sha256(path)
        require(actual == expected, "Locked source checksum differs: " + rel)
        hashes["reproducibility/" + rel] = actual
    for rel in ("reproducibility/study_statistics.py", "reproducibility/reproduce.py"):
        hashes[rel] = sha256(source / rel)
        # Verify these unlocked Python helpers against the specified Git tree too.
        blob = subprocess.check_output(["git", "-C", str(source), "show", commit + ":" + rel])
        require(hashlib.sha256(blob).hexdigest() == hashes[rel], "Helper differs from source commit: " + rel)
    grouped = defaultdict(list)
    for row in read_csv(release / lock["cohorts"]["development"]["archived_scores"]):
        row.update(dataset="BUS-BRA", split="development")
        for m in METHODS:
            row["alert_" + m] = row["candidate_alert_" + m]
        grouped["development"].append(row)
    for row in read_csv(release / lock["cohorts"]["internal_holdout"]["archived_scores"]):
        grouped[row["split"]].append(row)
    quality = lock["threshold_lock"]["quality_reference"]["cutoff"]
    for split, entry in lock["cohorts"].items():
        rows = grouped[split]
        manifest = read_csv(release / entry["manifest"])
        ident = lambda r: (int(r["patient_id"]), r["image_id"], r["pathology"])
        require(len(rows) == entry["count"] and sorted(map(ident, rows)) == sorted(map(ident, manifest)),
                "Scores do not match manifest: " + split)
        require(len({int(r["patient_id"]) for r in rows}) == len(rows), "Duplicate patients: " + split)
        for row in rows:
            require(row["status"] == "scored", "Unexpected technical failure.")
            dice = float(row["dice_vs_reference"])
            require(math.isfinite(dice) and 0 <= dice <= 1, "Invalid Dice.")
            require(int(row["low_quality"]) == int(dice < quality), "Incorrect low-quality flag.")
            require(all(math.isfinite(float(row["risk_" + m])) for m in METHODS), "Nonfinite risk.")
        rows.sort(key=lambda r: int(r["patient_id"]))
    require({int(r["patient_id"]) for r in grouped["development"]}.isdisjoint(
        int(r["patient_id"]) for r in grouped["internal_holdout"]), "Development/test leakage.")
    require([len(grouped[s]) for s in ("development", *SPLITS)] == [213, 851, 252], "Cohort sizes differ.")
    require([sum(int(r["low_quality"]) for r in grouped[s]) for s in ("development", *SPLITS)] == [24, 93, 16],
            "Low-quality denominators differ.")
    spec = importlib.util.spec_from_file_location("budget_source_statistics", release / "study_statistics.py")
    stats = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(stats)
    return grouped, lock, stats, hashes, commit


def calibrate(rows, method, target):
    """Whole tied groups under >=, plus a cutoff above max representing zero."""
    grouped = Counter(float(r["risk_" + method]) for r in rows)
    points = [(None, 0)]
    count = 0
    for score, size in sorted(grouped.items(), reverse=True):
        count += size
        points.append((score, count))
    chosen = min(points, key=lambda p: (abs(target.denominator * p[1] - target.numerator * len(rows)), p[1]))
    # Independent brute-force count check, including zero, against cumulative grouping.
    risks = np.array([float(r["risk_" + method]) for r in rows])
    independent = [(None, 0)] + [(float(x), int(np.sum(risks >= x))) for x in np.unique(risks)]
    brute = min(independent, key=lambda p: (abs(Fraction(p[1], len(rows)) - target), p[1]))
    require(chosen == brute, "Independent calibration mismatch.")
    return chosen[0], chosen[1], len(points)


def nearest_count(n, target):
    # Exact rational arithmetic avoids binary-float and Python bankers-rounding ties.
    return min(range(n + 1), key=lambda k: (abs(target.denominator * k - target.numerator * n), k))


def boundary_checks():
    expected = {851: [43,85,128,170,213,255,340,425],
                252: [13,25,38,50,63,76,101,126]}
    targets = [Fraction(x,100) for x in (5,10,15,20,25,30,40,50)]
    for n, values in expected.items():
        require([nearest_count(n,t) for t in targets] == values, "Top-K grid rounding differs.")
    require(nearest_count(851,Fraction(1,2)) == 425, "425.5 must choose 425.")
    require(nearest_count(3,Fraction(1,2)) == 1, "Exact half tie must choose fewer.")
    tied = [{"risk_A":str(x)} for x in (.9,.8,.8,.7)]
    require(calibrate(tied,"A",Fraction(1,2))[:2] == (.9,1), "Whole-tie nearest counts must choose fewer.")
    zero = [{"risk_A":"1"} for _ in range(4)]
    require(calibrate(zero,"A",Fraction(1,20))[:2] == (None,0), "Zero-review candidate missing.")
    tied_ids = [{"patient_id":"2","risk_A":".5"}, {"patient_id":"10","risk_A":".5"},
                {"patient_id":"1","risk_A":".6"}]
    flags = select(tied_ids,"A",count=2)
    require([r["patient_id"] for r,f in zip(tied_ids,flags) if f] == ["10","1"],
            "Tie-breaking must use original patient_id string, not integers/image IDs.")
    return {"internal_K_by_budget":expected[851],"external_K_by_budget":expected[252],
            "half_tie_851_times_0_5":425,"half_tie_3_times_0_5":1,
            "whole_score_tie_nearest_fewer_pass":True,"zero_review_option_pass":True,
            "unmodified_patient_id_string_tie_pass":True}


def select(rows, method, threshold=None, count=None):
    if count is None:
        return np.array([threshold is not None and float(r["risk_" + method]) >= threshold for r in rows], dtype=bool)
    ordered = sorted(range(len(rows)), key=lambda i: (-float(rows[i]["risk_" + method]), rows[i]["patient_id"]))
    # String CaseID is deliberately not converted to integer for tie-breaking.
    risks = np.array([float(r["risk_" + method]) for r in rows])
    ids = np.array([r["patient_id"] for r in rows])
    alternate = np.lexsort((ids, -risks)).tolist()
    require(ordered == alternate, "Independent ranking mismatch.")
    flags = np.zeros(len(rows), dtype=bool)
    flags[ordered[:count]] = True
    return flags


def performance(rows, flags, stats):
    low = np.array([bool(int(r["low_quality"])) for r in rows])
    n, f = len(rows), int(low.sum())
    r, tp = int(flags.sum()), int((low & flags).sum())
    ci = stats.wilson(tp, f) if f else (None, None)
    return {"N": n, "F": f, "R": r, "TP": tp, "misses": f - tp,
            "review_fraction": r / n, "detection_fraction": tp / f if f else None,
            "detection_ci95_low": ci[0], "detection_ci95_high": ci[1],
            "missed_low_quality_per_100": 100 * (f - tp) / n,
            "acceptable_cases_reviewed": r - tp}


def paired_contrast(first, second, stats):
    both = int(np.sum(first & second))
    first_only = int(np.sum(first & ~second))
    second_only = int(np.sum(~first & second))
    neither = int(np.sum(~first & ~second))
    n = len(first)
    phi = stats.paired_phi(both, first_only, second_only, neither)
    point, ci = stats.newcombe_difference(int(first.sum()), n, int(second.sum()), n, phi=phi)
    return {"difference_pp": 100 * point if point is not None else None,
            "ci95_low_pp": 100 * ci[0] if ci else None,
            "ci95_high_pp": 100 * ci[1] if ci else None,
            "phi_positive_association_corrected": phi,
            "both": both, "B_only": first_only, "A_only": second_only, "neither": neither, "denominator": n}


def plot_results(records, contrasts, path):
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                         "pdf.fonttype": 42, "ps.fonttype": 42})
    fig, axes = plt.subplots(2, 2, figsize=(13.0, 9.2), constrained_layout=True)
    colors = {"A": "#0072B2", "B": "#D55E00"}
    targets = sorted(set(r["target_budget"] for r in records))
    for split, style, marker in (("internal_holdout", "--", "o"), ("external_test", "-", "s")):
        for m in METHODS:
            rows = [r for r in records if r["split"] == split and r["mode"] == MODE_FIXED and r["method"] == m]
            axes[0, 0].plot([100*r["target_budget"] for r in rows], [100*r["review_fraction"] for r in rows],
                            color=colors[m], linestyle=style, marker=marker, label=("Internal " if split == "internal_holdout" else "External ") + m)
    axes[0, 0].plot([5, 50], [5, 50], color="0.5", linestyle=":", label="Target (reference)")
    axes[0, 0].set(title="A  Review fraction after threshold transfer", ylabel="Test patients reviewed (%)", ylim=(0,55))
    for ax, split, panel in ((axes[0, 1], "external_test", "B"), (axes[1, 0], "internal_holdout", "C")):
        for mode, style, marker, label in ((MODE_FIXED, "-", "o", "Transferred cutoff"), (MODE_EQUAL, "--", "s", "Equal-review top K")):
            for m in METHODS:
                rows = [r for r in records if r["split"] == split and r["mode"] == mode and r["method"] == m]
                ax.plot([100*r["target_budget"] for r in rows], [100*r["detection_fraction"] for r in rows],
                        color=colors[m], linestyle=style, marker=marker, label=label + " " + m)
        ax.set(title=panel + ("  External detection (16 low-quality cases)" if split == "external_test" else "  Internal detection (93 low-quality cases)"),
               ylabel="Low-quality masks detected (%)", ylim=(-2, 102))
    ax = axes[1, 1]
    for mode, color, offset, label in ((MODE_FIXED, "#009E73", -0.45, "Transferred cutoff"),
                                       (MODE_EQUAL, "#CC79A7", 0.45, "Equal-review top K")):
        rows = [r for r in contrasts if r["split"] == "external_test" and r["mode"] == mode]
        y = np.array([r["detection_difference_pp"] for r in rows])
        lo = np.array([r["detection_ci95_low_pp"] for r in rows])
        hi = np.array([r["detection_ci95_high_pp"] for r in rows])
        ax.errorbar([100*r["target_budget"] + offset for r in rows], y, yerr=np.array([y-lo, hi-y]),
                    color=color, fmt="o-", capsize=3, label=label)
    ax.axhline(0, color="0.4", linewidth=1)
    ax.set(title="D  External B minus A detection", ylabel="Difference (percentage points)")
    for ax in axes.flat:
        ax.set_xlabel("Development calibration / top-K target budget (%)")
        ax.set_xticks([100*t for t in targets])
        ax.grid(alpha=0.22)
        ax.legend(fontsize=8, loc="best")
    fig.suptitle("Post hoc budget sweep: development-calibrated threshold transfer versus equal review\n"
                 "Panel D: nominal 95% paired Wilson-Newcombe intervals; calibration/re-ranking uncertainty excluded", fontsize=11)
    fig.savefig(str(path) + ".png", dpi=200)
    fig.savefig(str(path) + ".pdf")
    plt.close(fig)


def main():
    started = time.perf_counter()
    created = datetime.now(timezone.utc).isoformat()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=Path("/workspace/research_source"))
    parser.add_argument("--output-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--protocol", type=Path, default=None)
    args = parser.parse_args()
    root = args.output_root.resolve()
    protocol = args.protocol or root / "protocol/analysis_plan.json"
    plan = read_json(protocol)
    targets = [Fraction(str(t)) for t in plan["budget_targets"]]
    require(targets == [Fraction(x, 100) for x in (5, 10, 15, 20, 25, 30, 40, 50)], "Protocol budget grid changed.")
    edge_checks = boundary_checks()
    groups, lock, stats, hashes, commit = load_inputs(args.source_root.resolve(), plan)
    out = root / "results/budget_transfer"
    out.mkdir(parents=True, exist_ok=True)
    (root / "figures").mkdir(exist_ok=True)
    (root / "reports").mkdir(exist_ok=True)
    calibration, records, contrasts, selections = [], [], [], []
    for target in targets:
        chosen = {}
        for m in METHODS:
            cutoff, count, points = calibrate(groups["development"], m, target)
            chosen[m] = cutoff
            perf = performance(groups["development"], select(groups["development"], m, cutoff), stats)
            require(perf["R"] == count, "Calibration review count changed.")
            calibration.append({"target_budget": float(target), "method": m, "threshold": cutoff,
                                "threshold_zero_option": cutoff is None, "candidate_points": points,
                                **perf, "deviation_from_target_pp": 100 * (perf["review_fraction"] - float(target))})
        if target == Fraction(1, 5):
            for m in METHODS:
                row = next(r for r in calibration if r["target_budget"] == 0.2 and r["method"] == m)
                expected = lock["threshold_lock"]["methods"][m]
                require(chosen[m] == expected["threshold"] and row["R"] == 43
                        and row["TP"] == expected["development_low_quality_detected"], "20% locked calibration not reproduced.")
        for split in SPLITS:
            rows = groups[split]
            low = np.array([bool(int(r["low_quality"])) for r in rows])
            k = nearest_count(len(rows), target)
            for mode in (MODE_FIXED, MODE_EQUAL):
                flags = {}
                for m in METHODS:
                    flags[m] = select(rows, m, threshold=chosen[m]) if mode == MODE_FIXED else select(rows, m, count=k)
                    perf = performance(rows, flags[m], stats)
                    dev = next(r for r in calibration if r["target_budget"] == float(target) and r["method"] == m)
                    records.append({"target_budget": float(target), "split": split, "dataset": rows[0]["dataset"],
                                    "mode": mode, "method": m, "development_threshold": chosen[m],
                                    "development_R": dev["R"], "development_N": dev["N"],
                                    "development_review_fraction": dev["review_fraction"],
                                    "top_k": k if mode == MODE_EQUAL else None, **perf,
                                    "review_minus_target_pp": 100 * (perf["review_fraction"] - float(target)),
                                    "review_minus_development_pp": 100 * (perf["review_fraction"] - dev["review_fraction"])})
                    selections.append({"target_budget": float(target), "split": split, "mode": mode, "method": m,
                                       "selected_case_ids": [r["patient_id"] for r, selected in zip(rows, flags[m]) if selected]})
                detection = paired_contrast(flags["B"][low], flags["A"][low], stats)
                review = paired_contrast(flags["B"], flags["A"], stats)
                contrasts.append({"target_budget": float(target), "split": split, "mode": mode,
                                  **{"detection_"+k:v for k,v in detection.items()},
                                  **{"review_"+k:v for k,v in review.items()}})
    # Preserve the original H1--H3 analysis and prove exact agreement with its archive.
    thresholds = {m: lock["threshold_lock"]["methods"][m]["threshold"] for m in METHODS}
    original = stats.main_results({s:groups[s] for s in SPLITS}, lock["threshold_lock"]["quality_reference"], thresholds, {m:43 for m in METHODS})
    require(original == read_json(args.source_root / "reproducibility/reference/primary.json"), "Original H1--H3 changed.")
    for split in SPLITS:
        for m in METHODS:
            observed = next(r for r in records if r["target_budget"] == .2 and r["split"] == split and r["method"] == m and r["mode"] == MODE_FIXED)
            expected = original["cohorts"][split]["methods"][m]
            require((observed["R"], observed["TP"], observed["misses"]) == (expected["R"], expected["TP"], expected["FN"]), "20% test results changed.")
    # External threshold-transfer drift relative to the actual internal review fraction.
    for row in records:
        internal = next(r for r in records if r["target_budget"] == row["target_budget"] and r["method"] == row["method"] and r["mode"] == row["mode"] and r["split"] == "internal_holdout")
        row["review_minus_internal_pp"] = 100 * (row["review_fraction"] - internal["review_fraction"])
    write_csv(out / "calibration.csv", calibration)
    write_csv(out / "performance.csv", records)
    write_csv(out / "paired_contrasts.csv", contrasts)
    write_json(out / "selected_case_ids.json", selections)
    plot_results(records, contrasts, root / "figures/budget_transfer")
    verification = {"all_source_lock_checksums_match": True, "independent_calibration_checks": 16,
                    "independent_top_k_ranking_checks": 32, "twenty_percent_cutoffs_exactly_reproduced": True,
                    "twenty_percent_development_counts": {"A":43,"B":43}, "original_H1_H3_exact_json_match": True,
                    "development_N_F": [213,24], "internal_N_F": [851,93], "external_N_F": [252,16],
                    "grid_complete": len(calibration) == 16 and len(records) == 64 and len(contrasts) == 32,
                    "boundary_cases":edge_checks}
    write_json(out / "verification.json", verification)
    metadata = {"classification": plan["classification"], "created_utc": created,
                "source_commit": commit, "protocol_sha256": sha256(protocol), "source_sha256": hashes,
                "script_sha256": sha256(__file__), "python": platform.python_version(), "numpy": np.__version__,
                "matplotlib": matplotlib.__version__, "seed": None,
                "seed_note": "Deterministic exact-count/rank analysis; no resampling or randomness used.",
                "ranking_tie_key": "Exact unmodified archived row['patient_id'] string, as in source study_statistics.py equal_review; risk descending, then lexicographic string (e.g. '1','10','100'). No integer conversion or image_id/zero-padding for ranking.",
                "rounding": "Exact rational nearest integer; equal distances select fewer. Internal N=851 and target 0.50 selects K=425, never 426.",
                "host_cpu_count": os.cpu_count(),
                "cgroup_cpu_max": Path('/sys/fs/cgroup/cpu.max').read_text().strip() if Path('/sys/fs/cgroup/cpu.max').exists() else None,
                "cgroup_memory_max": Path('/sys/fs/cgroup/memory.max').read_text().strip() if Path('/sys/fs/cgroup/memory.max').exists() else None,
                "statistics_reuse": "Unmodified verified source reproducibility/study_statistics.py: wilson, paired_phi, newcombe_difference; method 10 with corrected positive association. Source hash recorded.",
                "interval_scope": "Nominal two-sided 95%; conditional on observed calibration/selection. No calibration uncertainty, re-ranking bootstrap or multiplicity correction; no new significance tests.",
                "analysis_seconds": time.perf_counter() - started}
    write_json(out / "results.json", {"metadata":metadata,"calibration":calibration,"performance":records,"paired_contrasts":contrasts,"verification":verification})
    write_json(out / "run_receipt.json", {**metadata,"verification":verification})
    external_fixed = [r for r in contrasts if r["split"] == "external_test" and r["mode"] == MODE_FIXED]
    external_equal = [r for r in contrasts if r["split"] == "external_test" and r["mode"] == MODE_EQUAL]
    def direction_budgets(rows, sign):
        return ", ".join(f"{100*r['target_budget']:.0f}%" for r in rows
                         if (r["detection_difference_pp"] > 0 if sign == "positive" else
                             r["detection_difference_pp"] < 0 if sign == "negative" else
                             r["detection_difference_pp"] == 0))
    direction_text = (
        "Across the complete grid, external B-minus-A detection is positive at targets "
        + direction_budgets(external_fixed,"positive") + "; negative at "
        + direction_budgets(external_fixed,"negative") + "; and zero at "
        + direction_budgets(external_fixed,"zero") + " under transferred cutoffs. Under equal-review top K, it is positive at "
        + direction_budgets(external_equal,"positive") + "; negative at "
        + direction_budgets(external_equal,"negative") + "; and zero at "
        + direction_budgets(external_equal,"zero") + ". Thus the 20% point-estimate reversal is budget-dependent rather than a uniform ranking advantage."
    )
    lines = ["# Post hoc development-calibrated budget transfer", "", "Ready within the specified deterministic score-analysis scope. All eight target budgets are reported; the original H1–H3 results are preserved.", "",
             direction_text, "",
             "Development calibration uses only the 213 development risk scores and review counts, with whole tied groups under risk >= threshold and a zero-review option; labels do not select cutoffs. Each cutoff is transferred unchanged to the 851 internal and 252 external patients. Equal-review top K is a separate policy, with nearest-integer K (exact half ties choose fewer) and descending risk followed by the exact archived patient_id string, e.g. '1', '10', '100'; not integer or image-filename order. Internal N=851 at 50% selects K=425. Actual K is in performance.csv.", "",
             "Low quality means reference Dice < 0.70. Low-quality denominators are 24 development, 93 internal and 16 external patients. Percentages below are descriptive. Intervals reuse the release's verified paired Wilson–Newcombe method 10 implementation; they are nominal 95% and do not include development-calibration or re-ranking uncertainty. There are no new significance tests or claims of equivalence.", "",
             "## Development calibration (new budget sweep)", "", "| Target | A cutoff | B cutoff | A reviews | B reviews | A TP/24 | B TP/24 |", "|---:|---:|---:|---:|---:|---:|---:|"]
    for target in targets:
        a,b = [next(r for r in calibration if r["target_budget"] == float(target) and r["method"] == m) for m in METHODS]
        lines.append(f"| {100*float(target):.0f}% | {a['threshold']:.17g} | {b['threshold']:.17g} | {a['R']}/213 | {b['R']}/213 | {a['TP']} | {b['TP']} |")
    for split, name in (("internal_holdout","Internal BUS-BRA (N=851, F=93)"),("external_test","External BrEaST (N=252, F=16)")):
        lines += ["", "## " + name, "", "| Target | Policy | A R/N | B R/N | A TP/F (misses) | B TP/F (misses) | B−A detection pp (95% CI) |", "|---:|---|---:|---:|---:|---:|---:|"]
        for target in targets:
            for mode in (MODE_FIXED,MODE_EQUAL):
                a,b = [next(r for r in records if r["target_budget"]==float(target) and r["split"]==split and r["mode"]==mode and r["method"]==m) for m in METHODS]
                c = next(r for r in contrasts if r["target_budget"]==float(target) and r["split"]==split and r["mode"]==mode)
                label = "Transferred cutoff" if mode==MODE_FIXED else "Equal-review top K"
                lines.append(f"| {100*float(target):.0f}% | {label} | {a['R']}/{a['N']} | {b['R']}/{b['N']} | {a['TP']}/{a['F']} ({a['misses']}) | {b['TP']}/{b['F']} ({b['misses']}) | {c['detection_difference_pp']:.2f} ({c['detection_ci95_low_pp']:.2f}, {c['detection_ci95_high_pp']:.2f}) |")
    lines += ["", "## External budget drift after threshold transfer", "", "The full CSV also gives external-minus-development and external-minus-internal achieved review fractions. Drift below is relative to the nominal target, not a fitted correction.", "", "| Target | A actual review | B actual review | A minus target pp | B minus target pp |", "|---:|---:|---:|---:|---:|"]
    for target in targets:
        a,b = [next(r for r in records if r["target_budget"]==float(target) and r["split"]=="external_test" and r["mode"]==MODE_FIXED and r["method"]==m) for m in METHODS]
        lines.append(f"| {100*float(target):.0f}% | {100*a['review_fraction']:.2f}% | {100*b['review_fraction']:.2f}% | {a['review_minus_target_pp']:+.2f} | {b['review_minus_target_pp']:+.2f} |")
    lines += ["", "## Preservation and reproducibility", "", "At 20%, A = 0.13705134391784668 and B = 0.06972856653991777, each selecting 43/213 development cases. All original H1–H3 result JSON fields match the locked archive exactly. This is a new development-calibrated grid of transferred numerical cutoffs, rather than a redraw of the original test-cohort ranking curve.", "", "The external sample contains only 16 low-quality masks; individual detections change its fraction by 6.25 percentage points. The all-budget grid must not be used to select a favorable budget or promote a post hoc contrast to a primary result.", "", f"Actual deterministic analysis and rendering time: {metadata['analysis_seconds']:.3f} seconds. Seed: not applicable (no random operations). Source commit: `{commit}`. The recorded cgroup quota is `{metadata['cgroup_cpu_max']}` CPU and `{metadata['cgroup_memory_max']}` bytes memory.", "", "Source/protocol/script hashes, exact full-precision values, intervals and verification results are in `results/budget_transfer/results.json`. Full tables are `calibration.csv`, `performance.csv` and `paired_contrasts.csv`; per-policy selected string CaseIDs are preserved in `selected_case_ids.json`. Figures are `figures/budget_transfer.png` and `.pdf`.", "", "![Post hoc budget sweep](../figures/budget_transfer.png)"]
    (root / "reports/budget_transfer.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({"output":str(out),"analysis_seconds":metadata["analysis_seconds"],"verification":verification}))


if __name__ == "__main__":
    main()
