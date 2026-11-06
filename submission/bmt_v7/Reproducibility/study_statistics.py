"""Core computations preserved from the formal and supplementary study analyses."""
from collections import Counter
from fractions import Fraction
import hashlib
import math
from statistics import NormalDist


INDEPENDENT_SOURCE = "https://pubmed.ncbi.nlm.nih.gov/9595617/"
PAIRED_SOURCE = "https://www.site.uottawa.ca/~nat/Courses/csi5388/Newcombe.1998.pdf#page=5"
Z95 = NormalDist().inv_cdf(0.975)
METHODS = ("A", "B")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def file_hash(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def ratio(numerator, denominator):
    return numerator / denominator if denominator else None


def wilson(successes, total):
    """Wilson score limits without continuity correction."""
    p = successes / total
    z2 = Z95 ** 2
    scale = 1.0 + z2 / total
    center = (p + z2 / (2 * total)) / scale
    half_width = Z95 * math.sqrt(p * (1 - p) / total + z2 / (4 * total ** 2)) / scale
    return max(0.0, center - half_width), min(1.0, center + half_width)


def paired_phi(both, first_only, second_only, neither):
    """Newcombe's paired method 10 adjusts positive association only."""
    total = both + first_only + second_only + neither
    margin_product = (
        (both + first_only) * (second_only + neither)
        * (both + second_only) * (first_only + neither)
    )
    if margin_product == 0:
        return 0.0
    numerator = both * neither - first_only * second_only
    if numerator > 0:
        numerator = max(numerator - total / 2, 0.0)
    return numerator / math.sqrt(margin_product)


def newcombe_difference(x_first, n_first, x_second, n_second, phi=0.0):
    """First minus second, using the independent or paired method 10."""
    require(0 <= x_first <= n_first and 0 <= x_second <= n_second, "Invalid proportions.")
    if not n_first or not n_second:
        return None, None

    first, second = x_first / n_first, x_second / n_second
    lower_first, upper_first = wilson(x_first, n_first)
    lower_second, upper_second = wilson(x_second, n_second)
    estimate = first - second

    def radius(left, right):
        variance = left ** 2 + right ** 2 - 2 * phi * left * right
        return math.sqrt(max(variance, 0.0))

    lower = estimate - radius(first - lower_first, upper_second - second)
    upper = estimate + radius(upper_first - first, second - lower_second)
    return estimate, (lower, upper)


def describe_cohort(rows, cutoff, thresholds):
    valid = []
    failed = []
    for row in rows:
        if row["status"] == "failed":
            failed.append(row["image_id"])
            continue
        require(row["status"] == "scored", f"Unrecognized status for {row['image_id']}.")
        dice = float(row["dice_vs_reference"])
        risks = [float(row[f"risk_{method}"]) for method in ("A", "B")]
        require(0 <= dice <= 1 and all(math.isfinite(value) for value in risks), f"Invalid score for {row['image_id']}.")
        quality_flag = int(dice < cutoff)
        alerts = tuple(int(risk >= thresholds[method]) for method, risk in zip(("A", "B"), risks))
        require(
            int(row["low_quality"]) == quality_flag and tuple(int(row[f"alert_{method}"]) for method in ("A", "B")) == alerts,
            f"Saved flags differ from the locked rules for {row['image_id']}.",
        )
        valid.append((quality_flag, *alerts))

    n, f = len(valid), sum(entry[0] for entry in valid)
    methods = {}
    for index, method in enumerate(("A", "B"), 1):
        reviewed = sum(entry[index] for entry in valid)
        detected = sum(entry[index] for entry in valid if entry[0])
        missed = f - detected
        methods[method] = {
            "R": reviewed, "TP": detected, "FN": missed,
            "low_quality_detection_fraction": ratio(detected, f),
            "review_fraction": ratio(reviewed, n),
            "missed_low_quality_per_100": ratio(100 * missed, n),
            "acceptable_cases_alerted": reviewed - detected,
            "acceptable_cases": n - f,
            "review_fraction_among_acceptable": ratio(reviewed - detected, n - f),
        }
    pairs = Counter((a, b) for low, a, b in valid if low)
    return {
        "scheduled_patients": len(rows),
        "technical_failures": failed,
        "N": n,
        "F": f,
        "low_quality_fraction": ratio(f, n),
        "methods": methods,
        "paired_low_quality": {
            "both": pairs[1, 1], "A_only": pairs[1, 0],
            "B_only": pairs[0, 1], "neither": pairs[0, 0],
        },
    }


def contrast(label, role, first, second, source, phi=0.0):
    estimate, interval = newcombe_difference(*first, *second, phi=phi)
    return {
        "contrast": label,
        "role": role,
        "method": "Newcombe method 10",
        "reference": source,
        "first": {"events": first[0], "denominator": first[1]},
        "second": {"events": second[0], "denominator": second[1]},
        "difference_pp": None if estimate is None else 100 * estimate,
        "ci95_pp": None if interval is None else [100 * bound for bound in interval],
        "interval_excludes_zero": None if interval is None else interval[0] > 0 or interval[1] < 0,
    }


def main_results(groups, quality, thresholds, dev_budget):
    cohorts = {split: describe_cohort(rows, quality["cutoff"], thresholds)
               for split, rows in groups.items()}
    internal, external = cohorts["internal_holdout"], cohorts["external_test"]
    internal_a, external_a = internal["methods"]["A"], external["methods"]["A"]
    external_b = external["methods"]["B"]
    matched_budget = dev_budget["A"] == dev_budget["B"]

    h1 = contrast(
        "A low-quality detection, BrEaST minus BUS-BRA holdout", "primary",
        (external_a["TP"], external["F"]), (internal_a["TP"], internal["F"]), INDEPENDENT_SOURCE,
    )
    h2 = contrast(
        "A simulated review, BrEaST minus BUS-BRA holdout", "secondary_nominal",
        (external_a["R"], external["N"]), (internal_a["R"], internal["N"]), INDEPENDENT_SOURCE,
    )
    pair = external["paired_low_quality"]
    phi = paired_phi(pair["both"], pair["B_only"], pair["A_only"], pair["neither"])
    h3 = contrast(
        "Low-quality detection in BrEaST, B minus A",
        "secondary_nominal" if matched_budget else "descriptive_unmatched_development_budget",
        (external_b["TP"], external["F"]), (external_a["TP"], external["F"]), PAIRED_SOURCE, phi=phi,
    )
    h3.update(
        paired_low_quality=pair,
        phi_with_positive_association_continuity_correction=phi,
        development_review_counts=dev_budget,
        development_review_budget_matched=matched_budget,
        external_review_difference_B_minus_A_pp=ratio(100 * (external_b["R"] - external_a["R"]), external["N"]),
    )

    return {
        "status": "planned_h1_h3_analysis_complete",
        "unit": "patient",
        "scored_patients": internal["N"] + external["N"],
        "confidence_level": 0.95,
        "secondary_intervals": "nominal, without multiplicity adjustment",
        "low_quality_reference": quality,
        "alert_operator": ">=",
        "thresholds": thresholds,
        "cohorts": cohorts,
        "contrasts": {"H1": h1, "H2": h2, "H3": h3},
    }


def detection_record(detected, failures, total):
    return {
        "TP": detected,
        "FN": failures - detected,
        "low_quality_detection_fraction": ratio(detected, failures),
        "low_quality_detection_ci95": wilson(detected, failures) if failures else None,
        "missed_low_quality_per_100": ratio(100 * (failures - detected), total),
    }


def paired_detection(methods, failures, pairs, label, role):
    phi = paired_phi(pairs["both"], pairs["B_only"], pairs["A_only"], pairs["neither"])
    return contrast(
        label, role, (methods["B"]["TP"], failures), (methods["A"]["TP"], failures),
        PAIRED_SOURCE, phi=phi,
    )


def dice_sensitivity(groups, primary, cutoff):
    cohorts = {}
    for split, rows in groups.items():
        recoded = [
            dict(row, low_quality=int(float(row["dice_vs_reference"]) < cutoff))
            if row["status"] == "scored" else row
            for row in rows
        ]
        cohort = describe_cohort(recoded, cutoff, primary["thresholds"])
        previous = primary["cohorts"][split]
        require(cohort["N"] == previous["N"], f"Scored denominator changed in {split}.")
        for method in METHODS:
            counts = cohort["methods"][method]
            require(counts["R"] == previous["methods"][method]["R"], f"Alert count changed in {split}, {method}.")
            counts.update(detection_record(counts["TP"], cohort["F"], cohort["N"]))
        cohorts[split] = cohort

    internal, external = cohorts["internal_holdout"], cohorts["external_test"]
    a_across_cohorts = contrast(
        "A low-quality detection, BrEaST minus BUS-BRA holdout",
        "supplementary_nominal",
        (external["methods"]["A"]["TP"], external["F"]),
        (internal["methods"]["A"]["TP"], internal["F"]),
        INDEPENDENT_SOURCE,
    )
    b_minus_a = paired_detection(
        external["methods"], external["F"], external["paired_low_quality"],
        "BrEaST low-quality detection, B minus A", "supplementary_nominal",
    )
    return {
        "low_quality_dice_cutoff": cutoff,
        "cohorts": cohorts,
        "A_detection_external_minus_internal": a_across_cohorts,
        "external_detection_B_minus_A": b_minus_a,
    }


def equal_review(rows, cutoff, target):
    scored = [row for row in rows if row["status"] == "scored"]
    n = len(scored)
    budget = min(range(n + 1), key=lambda count: (abs(count - n * target), count))
    require(0 < budget <= n, "Equal-review budget cannot be evaluated.")
    failures = {row["patient_id"] for row in scored if float(row["dice_vs_reference"]) < cutoff}
    methods = {}
    selected_ids = {}
    for method in METHODS:
        score_column = f"risk_{method}"
        ordered = sorted(scored, key=lambda row: (-float(row[score_column]), row["patient_id"]))
        selected = ordered[:budget]
        selected_ids[method] = {row["patient_id"] for row in selected}
        require(len(selected_ids[method]) == budget, f"Repeated patient in ranking for {method}.")
        boundary = float(selected[-1][score_column])
        methods[method] = {
            "R": budget,
            "review_fraction": budget / n,
            **detection_record(len(selected_ids[method] & failures), len(failures), n),
            "last_selected_score": boundary,
            "patients_at_last_selected_score": sum(float(row[score_column]) == boundary for row in scored),
            "selected_at_last_selected_score": sum(float(row[score_column]) == boundary for row in selected),
            "selected_case_ids_in_rank_order": [row["patient_id"] for row in selected],
        }
    pairs = Counter((patient in selected_ids["A"], patient in selected_ids["B"]) for patient in failures)
    paired = {
        "both": pairs[True, True], "A_only": pairs[True, False],
        "B_only": pairs[False, True], "neither": pairs[False, False],
    }
    return {
        "dataset": "BrEaST",
        "N": n,
        "F": len(failures),
        "low_quality_dice_cutoff": cutoff,
        "target_review_fraction": float(target),
        "review_count_per_method": budget,
        "ranking_rule": "Descending risk score, then lexicographic official CaseID as stored in patient_id.",
        "methods": methods,
        "paired_low_quality": paired,
        "detection_B_minus_A": paired_detection(
            methods, len(failures), paired, "BrEaST equal-review detection, B minus A",
            "supplementary_descriptive_nominal",
        ),
        "interval_scope": "The nominal paired interval uses the observed ranking selections. It does not account for re-ranking in another sample.",
    }


def supplementary_results(groups, primary, target):
    return {
        "status": "prespecified_supplementary_analysis_complete",
        "scored_patients": primary["scored_patients"],
        "confidence_level": primary["confidence_level"],
        "intervals": "Nominal two-sided 95 percent. No multiplicity adjustment.",
        "fixed_thresholds": primary["thresholds"],
        "fixed_threshold_dice_sensitivity": {
            f"{cutoff:.2f}": dice_sensitivity(groups, primary, cutoff) for cutoff in (0.50, 0.80)
        },
        "external_equal_review": equal_review(
            groups["external_test"], primary["low_quality_reference"]["cutoff"], Fraction(str(target)),
        ),
    }

