#!/usr/bin/env python3
"""Redraw supplementary Figs S3–S5 from immutable, verified result files.

This script performs no model inference, resampling, interval estimation, or
recalibration. It changes presentation only; percentages/percentage points are
unit conversions of archived values. Run with Python 3 from any directory.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.text import Text
import numpy as np
import pandas as pd
from PIL import Image
import fitz


ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path("/workspace/research_source/experiments/cloud_validation_v1/results")
OUT = ROOT / "outputs/Figures"
QA = ROOT / "qa"
STYLE_PATH = ROOT / "evidence/figure_style_spec.json"
STYLE = json.loads(STYLE_PATH.read_text())
WIDTH = float(STYLE["full_width_inches"])
COLORS = STYLE["colors"]
FONT = STYLE["font_family"]
MIN_FONT = float(STYLE["minimum_pt"])

plt.rcParams.update({
    "font.family": FONT,
    "font.size": 9,
    "axes.labelsize": 9,
    "axes.titlesize": 9,
    "axes.titleweight": "normal",
    "axes.linewidth": 0.7,
    "axes.edgecolor": "black",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.unicode_minus": True,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8.5,
    "xtick.major.width": 0.7,
    "ytick.major.width": 0.7,
    "xtick.major.size": 3,
    "ytick.major.size": 3,
    "legend.fontsize": 8,
    "legend.frameon": False,
    "legend.handlelength": 1.6,
    "legend.handletextpad": 0.5,
    "legend.columnspacing": 1.2,
    "lines.linewidth": 1.2,
    "lines.markersize": 4,
    "lines.markeredgewidth": 0.9,
    "savefig.facecolor": "white",
    "figure.facecolor": "white",
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "svg.fonttype": "none",
    "svg.hashsalt": "bmt-v9-extended-statistics",
})

SOURCE_PATHS = {
    "performance": SOURCE / "budget_transfer/performance.csv",
    "paired_contrasts": SOURCE / "budget_transfer/paired_contrasts.csv",
    "bootstrap_summary": SOURCE / "bootstrap_stability/summary.json",
    "case_mix": SOURCE / "case_mix_decomposition.json",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


HASHES_BEFORE = {k: sha256(v) for k, v in SOURCE_PATHS.items()}
perf = pd.read_csv(SOURCE_PATHS["performance"])
contrasts = pd.read_csv(SOURCE_PATHS["paired_contrasts"])
boot = json.loads(SOURCE_PATHS["bootstrap_summary"].read_text())
mix = json.loads(SOURCE_PATHS["case_mix"].read_text())
BUDGETS = np.array([5, 10, 15, 20, 25, 30, 40, 50], dtype=float)
assert len(perf) == 64 and len(contrasts) == 32
assert np.allclose(sorted(perf.target_budget.unique()) * np.ones(8), BUDGETS / 100)
assert boot["replicates_per_route"] == 10000
assert mix["bootstrap"]["replicates"] == 5000

evidence = {
    "script": str(Path(__file__).resolve()),
    "source_root": str(SOURCE),
    "source_sha256_before": HASHES_BEFORE,
    "style_source": str(STYLE_PATH),
    "changes": "Presentation only; no bootstrap rerun, model inference, recalibration, or new statistical estimation.",
    "font": FONT,
    "width_inches": WIDTH,
    "figures": {},
}


def panel(ax, letter: str, title: str, letter_x: float = -0.15):
    ax.text(letter_x, 1.045, letter, transform=ax.transAxes,
            ha="left", va="bottom", fontsize=10, fontweight="bold")
    ax.set_title(title, loc="left", pad=10)


def legend_line(color, marker="o", ls="-", filled=True, label=None):
    return Line2D([0], [0], color=color, marker=marker, linestyle=ls,
                  markerfacecolor=color if filled else "white", label=label)


def error_point(ax, x, y, lo, hi, *, color, marker="o", filled=True):
    ax.errorbar(x, y, xerr=[[x - lo], [hi - x]], fmt=marker,
                color=color, markerfacecolor=color if filled else "white",
                markeredgecolor=color, elinewidth=1, capsize=2.2,
                capthick=0.85, markersize=4.4, zorder=3)


def save(fig, name, content):
    # Journal style: numeric percentages use a narrow no-break space.
    # Axes labeled (%) and numeric ticks without % remain unchanged.
    percent_pattern = r"(?<=\d)[ \u00a0\u202f]*%"
    for text in fig.findobj(Text):
        text.set_text(re.sub(percent_pattern, "\u202f%", text.get_text()))
    content["caption"] = re.sub(percent_pattern, "\u202f%", content["caption"])
    fig.canvas.draw()
    texts = [x for x in fig.findobj(Text) if x.get_visible() and x.get_text().strip()]
    minimum_font = min(x.get_fontsize() for x in texts)
    assert minimum_font >= MIN_FONT, (name, minimum_font)
    renderer = fig.canvas.get_renderer()
    frame = fig.bbox
    clipping = []
    for item in texts:
        bb = item.get_window_extent(renderer)
        if bb.x0 < -0.1 or bb.y0 < -0.1 or bb.x1 > frame.x1 + .1 or bb.y1 > frame.y1 + .1:
            clipping.append(item.get_text())
    assert not clipping, (name, clipping)
    files = {}
    for ext in ("png", "pdf", "svg"):
        target = OUT / f"{name}.{ext}"
        fig.savefig(target, dpi=600, metadata={"Creator": "BMT v9; Matplotlib; verified archived values"})
        files[ext] = {"path": str(target), "sha256": sha256(target), "bytes": target.stat().st_size}
    with Image.open(OUT / f"{name}.png") as im:
        files["png"]["pixels"] = list(im.size)
        files["png"]["dpi"] = list(im.info.get("dpi", ()))
        assert im.width == round(WIDTH * 600)
        preview = im.copy()
        preview.thumbnail((1400, 1400))
        preview.convert("RGB").save(QA / f"{name}_preview.png")
        preview.convert("L").save(QA / f"{name}_grayscale_preview.png")
    svg = ET.parse(OUT / f"{name}.svg").getroot()
    ns = {"s": "http://www.w3.org/2000/svg"}
    vector_paths = len(svg.findall(".//s:path", ns))
    embedded_images = len(svg.findall(".//s:image", ns))
    vector_texts = len(svg.findall(".//s:text", ns))
    assert embedded_images == 0 and vector_paths > 10 and vector_texts > 5
    with fitz.open(OUT / f"{name}.pdf") as pdf:
        page = pdf[0]
        assert len(pdf) == 1
        assert abs(page.rect.width / 72 - WIDTH) < .001
        assert len(page.get_images()) == 0
        assert len(page.get_drawings()) > 10
        page.get_pixmap(matrix=fitz.Matrix(2, 2)).save(QA / f"{name}_pdf_preview.png")
        pdf_spans = [s for b in page.get_text("dict")["blocks"] if "lines" in b
                     for line in b["lines"] for s in line["spans"] if s["text"].strip()]
        pdf_min_font = min(s["size"] for s in pdf_spans)
        assert pdf_min_font >= MIN_FONT - .001
        files["pdf"].update({"page_size_pt": list(page.rect[2:]),
                              "raster_images": len(page.get_images()),
                              "vector_drawings": len(page.get_drawings()),
                              "minimum_font_pt": pdf_min_font,
                              "fonts": [list(x) for x in page.get_fonts()]})
    content.update({
        "numeric_percent_spacing": "U+202F narrow no-break space before %; axes (%) unchanged",
        "files": files,
        "minimum_visible_font_pt": minimum_font,
        "visible_text_elements": len(texts),
        "all_text_inside_canvas": True,
        "vector_validation": {"svg_paths": vector_paths, "svg_text_elements": vector_texts,
                              "svg_embedded_images": embedded_images, "pdf_raster_images": 0},
        "preview": str(QA / f"{name}_preview.png"),
        "pdf_render_preview": str(QA / f"{name}_pdf_preview.png"),
        "grayscale_preview": str(QA / f"{name}_grayscale_preview.png"),
    })
    evidence["figures"][name] = content
    plt.close(fig)


def budget_axes(ax):
    ax.set_xlim(3, 52)
    ax.set_xticks(BUDGETS)
    ax.set_xlabel("Target review budget (%)")


def draw_s3():
    fig, axes = plt.subplots(2, 2, figsize=(WIDTH, 5.1))
    fig.subplots_adjust(left=.092, right=.982, bottom=.105, top=.89, wspace=.29, hspace=.49)
    axa, axb, axc, axd = axes.flat
    fig.legend(handles=[legend_line(COLORS[m], label=f"Method {m}", marker="o" if m == "A" else "D") for m in ["A", "B"]],
               loc="upper center", bbox_to_anchor=(.52, .995), ncol=2)
    series = []
    # A: threshold-transfer review fraction, both cohorts; all eight budgets.
    for split, ls, filled in [("internal_holdout", "-", True), ("external_test", "--", False)]:
        for method in ["A", "B"]:
            marker = "o" if method == "A" else "D"
            d = perf[(perf.split == split) & (perf.method == method) &
                     (perf["mode"] == "development_calibrated_threshold")].sort_values("target_budget")
            x, y = d.target_budget.to_numpy() * 100, d.review_fraction.to_numpy() * 100
            assert np.allclose(x, BUDGETS)
            axa.plot(x, y, color=COLORS[method], marker=marker, linestyle=ls,
                     markerfacecolor=COLORS[method] if filled else "white", zorder=3)
            series.append({"panel": "A", "split": split, "method": method,
                           "source_column": "review_fraction", "budget_percent": x.tolist(), "values_percent": y.tolist()})
    axa.plot([3, 52], [3, 52], color="#999999", linestyle=":", linewidth=.8, zorder=1)
    axa.set_ylim(0, 56)
    axa.set_yticks([0, 20, 40])
    axa.set_ylabel("Cases reviewed (%)")
    axa.legend(handles=[legend_line("#444444", "None", "-", True, "Internal"),
                        legend_line("#444444", "None", "--", False, "External")],
               loc="upper left", borderaxespad=.2)
    panel(axa, "A", "Transferred review volume")
    modes = [("development_calibrated_threshold", "-", True),
             ("test_cohort_equal_review", "--", False)]
    for ax, split, letter, title, n in [(axb, "external_test", "B", "External detection", 16),
                                        (axc, "internal_holdout", "C", "Internal detection", 93)]:
        for mode, ls, filled in modes:
            for method in ["A", "B"]:
                marker = "o" if method == "A" else "D"
                d = perf[(perf.split == split) & (perf.method == method) & (perf["mode"] == mode)].sort_values("target_budget")
                x, y = d.target_budget.to_numpy() * 100, d.detection_fraction.to_numpy() * 100
                assert np.allclose(x, BUDGETS)
                ax.plot(x, y, color=COLORS[method], marker=marker, linestyle=ls,
                        markerfacecolor=COLORS[method] if filled else "white", zorder=3)
                series.append({"panel": letter, "split": split, "method": method, "mode": mode,
                               "source_column": "detection_fraction", "budget_percent": x.tolist(), "values_percent": y.tolist()})
        ax.set_ylim(0, 103)
        ax.set_yticks([0, 25, 50, 75, 100])
        ax.set_ylabel("Low-quality cases detected (%)")
        ax.text(.98, .04, f"{n} low-quality cases", transform=ax.transAxes,
                fontsize=7.5, ha="right", va="bottom", color="#555555")
        panel(ax, letter, title)
    axb.legend(handles=[legend_line("#444444", "None", "-", True, "Transferred"),
                        legend_line("#444444", "None", "--", False, "Equal review")],
               loc="lower left", borderaxespad=.2)
    interval_rows = []
    for mode, color, marker, offset, filled in [
        ("development_calibrated_threshold", COLORS["fixed"], "o", -.55, True),
        ("test_cohort_equal_review", COLORS["equal"], "s", .55, False),
    ]:
        d = contrasts[(contrasts.split == "external_test") & (contrasts["mode"] == mode)].sort_values("target_budget")
        x = d.target_budget.to_numpy() * 100
        y = d.detection_difference_pp.to_numpy()
        lo, hi = d.detection_ci95_low_pp.to_numpy(), d.detection_ci95_high_pp.to_numpy()
        assert np.allclose(x, BUDGETS)
        axd.errorbar(x + offset, y, yerr=np.vstack((y - lo, hi - y)), fmt=marker,
                     color=color, markerfacecolor=color if filled else "white", markersize=4,
                     elinewidth=.9, capsize=1.8, capthick=.8, zorder=3)
        for b, est, lower, upper in zip(x, y, lo, hi):
            interval_rows.append({"budget_percent": b, "mode": mode, "estimate_pp": est,
                                  "ci95_low_pp": lower, "ci95_high_pp": upper})
    axd.axhline(0, color="#888888", linewidth=.8, zorder=1)
    axd.set_ylim(-39, 48)
    axd.set_yticks([-20, 0, 20, 40])
    axd.set_ylabel("B − A detection (pp)")
    panel(axd, "D", "External paired contrast")
    axd.legend(handles=[legend_line(COLORS["fixed"], "o", "None", True, "Transferred"),
                        legend_line(COLORS["equal"], "s", "None", False, "Equal review")],
               loc="upper right", fontsize=7.5, borderaxespad=.2)
    for ax in axes.flat:
        budget_axes(ax)
    caption = (
        "Figure S3. Review-budget transfer and detection across all eight evaluated budgets (5%, 10%, 15%, 20%, 25%, 30%, 40%, and 50%). "
        "(A) Observed review fractions after transferring development-calibrated thresholds to the internal holdout (filled markers, solid lines; n=851) "
        "and external cohort (open markers, dashed lines; n=252); the dotted diagonal marks equality with the target budget. "
        "(B,C) Observed low-quality detection on the external (16 low-quality cases) and internal (93 low-quality cases) cohorts. "
        "Filled markers/solid lines denote transferred thresholds, and open markers/dashed lines denote cohort-specific equal-review ranking. "
        "Method A uses blue circles and method B uses orange diamonds in A–C; shapes retain method identity in grayscale. "
        "(D) External paired B-minus-A detection differences (percentage points); points are observed contrasts, and vertical bars are the archived paired "
        "Newcombe 95% confidence intervals. Dark circles denote transferred thresholds and blue open squares denote equal review; horizontal offsets are for legibility only. "
        "The equal-review count is cohort-specific and rounded as archived; at the 20% budget, 50 of 252 external cases are reviewed per method. "
        "Lines in A–C connect observed budget settings and do not imply additional evaluations. Source: budget_transfer/performance.csv (64 rows) "
        "and budget_transfer/paired_contrasts.csv (32 rows); all values and original intervals are unchanged."
    )
    save(fig, "Figure_S3", {"caption": caption, "panels": ["A: transferred review fraction", "B: external detection", "C: internal detection", "D: paired Newcombe contrast"],
                             "plot_series": series, "paired_intervals": interval_rows, "input_rows": {"performance": 64, "paired_contrasts": 32},
                             "data_marks": {"A": 32, "B": 32, "C": 32, "D": 16}})


ROUTES = [("R1", "fixed_cutoffs_test_sampling"), ("R2", "development_calibration_only"), ("R3", "full_resampling")]


def draw_s4():
    fig = plt.figure(figsize=(WIDTH, 4.55))
    gs = fig.add_gridspec(2, 2, left=.095, right=.98, bottom=.065, top=.85,
                          wspace=.25, hspace=.60, height_ratios=[1.5, 1.0])
    axa, axb, axc = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1]), fig.add_subplot(gs[1, :])
    records = []
    groups = [(5, "R1"), (3, "R2"), (1, "R3")]
    endpoints_a = [("H1_A_external_minus_internal_detection_pp", "H1: detection", "o", True, .23),
                   ("H2_A_external_minus_internal_review_pp", "H2: review", "s", False, -.23)]
    endpoints_b = [("external_fixed_B_minus_A_detection_pp", "Fixed cutoff", "o", True, .23, COLORS["fixed"]),
                   ("external_equal_B_minus_A_detection_pp", "Equal top 50", "s", False, -.23, COLORS["equal"])]
    for (route_name, key), (center, _) in zip(ROUTES, groups):
        route = boot["routes"][key]
        for endpoint, label, marker, filled, offset in endpoints_a:
            st = route["endpoints_pp"][endpoint]
            lo, hi = st["percentile_95"]
            error_point(axa, st["median"], center + offset, lo, hi, color=COLORS["A"], marker=marker, filled=filled)
            records.append({"panel": "A", "route": route_name, "endpoint": endpoint, "median_pp": st["median"], "percentile95_pp": [lo, hi], "valid_replicates": st["valid_replicates"]})
        for endpoint, label, marker, filled, offset, color in endpoints_b:
            st = route["endpoints_pp"][endpoint]
            lo, hi = st["percentile_95"]
            error_point(axb, st["median"], center + offset, lo, hi, color=color, marker=marker, filled=filled)
            records.append({"panel": "B", "route": route_name, "endpoint": endpoint, "median_pp": st["median"], "percentile95_pp": [lo, hi], "valid_replicates": st["valid_replicates"]})
    for ax in [axa, axb]:
        ax.set_yticks([5, 3, 1], ["R1", "R2", "R3"])
        ax.set_ylim(.25, 5.85)
        ax.tick_params(axis="y", length=0, pad=7)
        ax.spines["left"].set_visible(False)
        ax.axvline(0, color="#999999", linewidth=.8, zorder=1)
        ax.set_xlabel("Difference (pp)")
    axa.set_xlim(-44, 16)
    axa.set_xticks([-40, -20, 0])
    axb.set_xlim(-29, 44)
    axb.set_xticks([-20, 0, 20, 40])
    panel(axa, "A", "Method A: external − internal")
    panel(axb, "B", "External B − A detection")
    # Each legend sits above its panel. No full statistical notes are embedded.
    axa.legend(handles=[legend_line(COLORS["A"], "o", "None", True, "H1: detection"),
                        legend_line(COLORS["A"], "s", "None", False, "H2: review")],
               loc="lower left", bbox_to_anchor=(-.02, 1.20), ncol=2, borderaxespad=0, fontsize=7.5)
    axb.legend(handles=[legend_line(COLORS["fixed"], "o", "None", True, "Fixed cutoff"),
                        legend_line(COLORS["equal"], "s", "None", False, "Equal top 50")],
               loc="lower left", bbox_to_anchor=(-.02, 1.20), ncol=2, borderaxespad=0, fontsize=7.5)
    # Exact-value dot table replaces tiny, unreadable stacked segments.
    axc.axis("off")
    axc.set_xticks([])
    axc.set_yticks([])
    panel(axc, "C", "Joint fixed / top-50 sign frequencies", letter_x=-.07)
    axc.set_xlim(0, 5.05)
    axc.set_ylim(-.15, 3.45)
    categories = [("Original strict", "original_direction_reversal", "o"),
                  ("Opposite strict", "opposite_direction_reversal", "s"),
                  ("Any zero", "any_difference_tie", "D"),
                  ("Same nonzero", "same_nonzero", "^")]
    centers = [1.05, 2.25, 3.45, 4.65]
    for cx, (label, _, marker) in zip(centers, categories):
        axc.text(cx, 3.1, label, fontsize=8.5, ha="center", va="center")
    axc.hlines(2.75, .05, 5.05, color="#555555", linewidth=.65)
    frequency_rows = []
    for i, (route_name, key) in enumerate(ROUTES):
        joint = boot["routes"][key]["joint_direction_patterns"]
        y = 2.2 - .86 * i
        axc.text(.02, y, route_name, ha="left", va="center", fontsize=9)
        vals = []
        for cx, (label, field, marker) in zip(centers, categories):
            if field == "same_nonzero":
                count = sum(joint["sign_matrix"][s][s]["count"] for s in ["negative", "positive"])
                fraction = count / joint["valid_replicates"]
            else:
                count = joint[field]["count"]
                fraction = joint[field]["fraction"]
            vals.append(fraction)
            axc.plot(cx - .33, y, marker=marker, color="#444444", markerfacecolor="white", markersize=4, linestyle="None")
            axc.text(cx + .04, y, f"{fraction * 100:.2f}%", fontsize=9, ha="center", va="center")
            frequency_rows.append({"route": route_name, "category": label, "count": count,
                                   "valid_replicates": joint["valid_replicates"], "frequency_percent": fraction * 100})
        assert abs(sum(vals) - 1) < 1e-10
    observed_values = [39.61, 0, 25.19, 35.20, 90.40, 0, 4.35, 5.25, 30.94, .90, 28.08, 40.08]
    assert np.allclose([r["frequency_percent"] for r in frequency_rows], observed_values)
    caption = (
        "Figure S4. Exploratory bootstrap stability under three sources of variation. "
        "R1 resamples test patients at fixed development cutoffs; R2 resamples development patients for cutoff calibration while holding the test cohorts fixed; "
        "R3 resamples development and test patients. Each route has 10,000 archived patient-bootstrap replicates with method A, method B, and quality labels kept paired. "
        "(A) Method-A external-minus-internal contrasts for H1, low-quality detection (filled circles), and H2, review fraction (open squares). "
        "(B) External B-minus-A detection contrasts for the fixed-cutoff policy (dark circles) and equal top-50 review policy (blue open squares). "
        "In A and B, points are bootstrap medians and horizontal bars are unadjusted 2.5th–97.5th percentile intervals from the archived valid replicates; "
        "a collapsed interval is shown by its point, including the necessarily constant R2 equal-top-50 endpoint. "
        "(C) Exact empirical frequencies among jointly valid replicates, with marker shapes identifying four mutually exclusive sign categories. "
        "Original strict means fixed B−A >0 and top-50 B−A <0; opposite strict reverses both inequalities; any zero includes either contrast equal to zero; "
        "same nonzero means both contrasts share a nonzero sign. Frequencies are not p-values, posterior probabilities, or population probabilities. "
        "The observed external fixed-cutoff A-only detection cell is zero: R1 cannot resample an A-only detection and its fixed B−A distribution is therefore structurally nonnegative. "
        "Its [0,40] pp percentile interval does not exclude a population A advantage and does not replace the original paired Newcombe interval [−4.28,40.04] pp. "
        "Only 16 external low-quality patients inform detection; bootstrap replicates are not new patients. "
        "Source: bootstrap_stability/summary.json; no bootstrap was rerun, and original H1–H3 Newcombe intervals are unchanged."
    )
    save(fig, "Figure_S4", {"caption": caption, "panels": ["A: H1/H2 three-route bootstrap medians", "B: external policy three-route bootstrap medians", "C: exact four-category empirical frequencies"],
                             "bootstrap_intervals": records, "joint_frequencies": frequency_rows,
                             "data_marks": {"A": 6, "B": 6, "C": 12},
                             "frequencies_are_p_values": False,
                             "support_constraint": boot["fixed_cutoff_empirical_support_constraint"]})


def draw_s5():
    fig, axes = plt.subplots(1, 2, figsize=(WIDTH, 2.9), sharey=True)
    fig.subplots_adjust(left=.165, right=.98, bottom=.205, top=.82, wspace=.24)
    fig.legend(handles=[legend_line(COLORS["A"], "o", "None", True, "Method A"),
                        legend_line(COLORS["B"], "s", "None", False, "Method B")],
               loc="upper center", bbox_to_anchor=(.57, .995), ncol=2)
    rows = []
    terms = [("overall_difference", "Total", 2),
             ("composition_associated", "Composition", 1),
             ("within_stratum_rate", "Within strata", 0)]
    for ax, outcome, letter, title in [(axes[0], "detection", "A", "Low-quality detection"),
                                       (axes[1], "review_fraction", "B", "Review fraction")]:
        for method, marker, offset, filled in [("A", "o", .13, True), ("B", "s", -.13, False)]:
            stats = mix["results"][f"{method}.{outcome}"]["statistics"]
            for term, label, center in terms:
                st = stats[term]
                est = st["estimate"] * 100
                lo, hi = [v * 100 for v in st["percentile_ci95"]]
                expected_n = 4999 if outcome == "detection" and term != "overall_difference" else 5000
                assert st["valid_replicates"] == expected_n
                error_point(ax, est, center + offset, lo, hi, color=COLORS[method], marker=marker, filled=filled)
                rows.append({"panel": letter, "method": method, "outcome": outcome, "term": term,
                             "estimate_pp": est, "percentile95_pp": [lo, hi],
                             "valid_replicates": st["valid_replicates"], "invalid_replicates": st["invalid_replicates"]})
        ax.axvline(0, color="#999999", linewidth=.8, zorder=1)
        ax.set_yticks([2, 1, 0], ["Total", "Composition", "Within strata"])
        ax.tick_params(axis="y", length=0, pad=8)
        ax.spines["left"].set_visible(False)
        ax.set_ylim(-.48, 2.48)
        ax.set_xlabel("External − internal (pp)")
        panel(ax, letter, title, letter_x=-.21 if letter == "A" else -.10)
    axes[0].set_xlim(-45, 32)
    axes[0].set_xticks([-40, -20, 0, 20])
    axes[1].set_xlim(-13.5, 3.0)
    axes[1].set_xticks([-12, -8, -4, 0])
    caption = (
        "Figure S5. Descriptive symmetric Kitagawa decomposition of external-minus-internal differences at the locked development-calibrated cutoffs. "
        "(A) Low-quality detection. (B) Review fraction. For each outcome, the total observed difference is separated into a diagnostic-composition-associated term "
        "and a within-stratum-rate term using dataset-reported benign and malignant strata. "
        "Blue filled circles denote method A, and orange open squares denote method B; points are observed estimates, and horizontal bars are each term's own "
        "unadjusted bootstrap percentile 95% interval. The symmetric formula averages internal and external stratum rates for the composition term and "
        "averages internal and external stratum weights for the within-stratum term. Detection weights use low-quality denominators; review weights use all-patient denominators. "
        "The two panels use separately labeled horizontal scales. There were 5,000 archived patient-bootstrap draws; detection components have 4,999 valid draws "
        "because one draw had an undefined external benign low-quality rate, while detection totals and all review terms have 5,000 valid draws. "
        "Observed terms add to their total; percentile-interval endpoints do not have to add. "
        "This is post hoc descriptive accounting, not causal attribution or a percent-explained analysis; two diagnostic strata do not remove other confounding. "
        "Only 16 external low-quality cases inform detection, and bootstrap draws are not independent new patients. "
        "Source: case_mix_decomposition.json; archived estimates and component-specific intervals are unchanged, and no resampling was rerun."
    )
    save(fig, "Figure_S5", {"caption": caption, "panels": ["A: detection", "B: review fraction"],
                             "term_intervals": rows, "data_marks": {"A": 6, "B": 6},
                             "interpretation": "Post hoc descriptive accounting; not causal attribution.",
                             "interval_counts": "Detection components: 4999; detection totals and every review term: 5000."})


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    QA.mkdir(parents=True, exist_ok=True)
    target = ROOT / "evidence/extended_statistics_figures.json"
    previous = json.loads(target.read_text()) if target.exists() else {}
    draw_s3()
    draw_s4()
    draw_s5()
    after = {k: sha256(v) for k, v in SOURCE_PATHS.items()}
    assert HASHES_BEFORE == after
    evidence["source_sha256_after"] = after
    evidence["source_files_unchanged"] = True
    evidence["script_sha256"] = sha256(Path(__file__).resolve())
    review_hashes = {name: record["files"]["png"]["sha256"] for name, record in evidence["figures"].items()}
    prior_review = previous.get("visual_inspection", {})
    if prior_review.get("reviewed_png_sha256") == review_hashes:
        evidence["visual_inspection"] = prior_review
    else:
        evidence["visual_inspection"] = {"status": "pending", "previews": [str(QA / f"Figure_S{i}_preview.png") for i in [3, 4, 5]]}
    target.write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"evidence": str(target), "files": [f"Figure_S{i}.{ext}" for i in [3, 4, 5] for ext in ["png", "pdf", "svg"]],
                      "source_unchanged": True}, indent=2))


if __name__ == "__main__":
    main()
