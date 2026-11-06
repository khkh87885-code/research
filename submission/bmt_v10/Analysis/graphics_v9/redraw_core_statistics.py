#!/usr/bin/env python3
"""Redraw four publication figures from locked study results and patient records.

No statistical result is re-estimated. Rank curves and paired counts are checked
against the archived patient records; every displayed interval is read verbatim
from the approved reference JSON files.
"""
from pathlib import Path
import csv
import hashlib
import json
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.text import Text
import numpy as np

ROOT = Path("/workspace/bmt_v9")
SOURCE = Path("/workspace/research_source/reproducibility")
OUT = ROOT / "outputs/Figures"
EVIDENCE = ROOT / "evidence/core_statistics_figures.json"
STYLE_PATH = ROOT / "evidence/figure_style_spec.json"
STYLE = json.loads(STYLE_PATH.read_text())
PRIMARY_PATH = SOURCE / "reference/primary.json"
SUPP_PATH = SOURCE / "reference/supplementary.json"
CURVE_PATH = SOURCE / "review_curve_counts.csv"
RECORDS_PATH = SOURCE / "records/validation_cases.csv"
MAIN = json.loads(PRIMARY_PATH.read_text())
SUPP = json.loads(SUPP_PATH.read_text())
COLORS = STYLE["colors"]
W = STYLE["full_width_inches"]
INK = "#202020"
GRAY = "#666666"
WHITE = "#FFFFFF"

plt.rcParams.update({
    "font.family": STYLE["font_family"], "font.size": 9,
    "axes.labelsize": 9, "axes.titlesize": 9.5, "xtick.labelsize": 8,
    "ytick.labelsize": 8.5, "legend.fontsize": 8,
    "axes.linewidth": 0.7, "lines.linewidth": 1.2,
    "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none",
    "figure.facecolor": WHITE, "axes.facecolor": WHITE,
    "savefig.facecolor": WHITE, "text.color": INK,
    "axes.labelcolor": INK, "axes.edgecolor": INK,
    "xtick.color": INK, "ytick.color": INK,
    "savefig.bbox": None, "svg.hashsalt": "bmt-v9-core-statistics",
})


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def signed(value):
    return f"{value:+.2f}".replace("-", "−")


def value_text(item):
    lo, hi = item["ci95_pp"]
    return f"{signed(item['difference_pp'])} [{signed(lo)}, {signed(hi)}]"


def rows(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


RECORDS = rows(RECORDS_PATH)
CURVES = rows(CURVE_PATH)


def plain_axis(ax, left=True):
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines["left"].set_visible(left)
    ax.tick_params(width=0.7, length=3, pad=3)
    ax.grid(False)


def panel_header(fig, letter, title, y, x=0.065):
    fig.text(x - 0.042, y, letter, fontsize=10, weight="bold", va="baseline")
    fig.text(x, y, title, fontsize=9.5, weight="bold", va="baseline")


def interval(ax, item, y, color=INK, marker="o", open_marker=False):
    x = item["difference_pp"]
    lo, hi = item["ci95_pp"]
    ax.errorbar(x, y, xerr=[[x - lo], [hi - x]], fmt=marker,
                color=color, ecolor=color, ms=4.0, mew=0.9,
                mfc=WHITE if open_marker else color,
                elinewidth=1, capsize=2.4, capthick=0.8, zorder=3)


QA = {}
PRIMITIVES = {}
CAPTIONS = {}


def export(fig, name):
    """Keep a fixed physical canvas and audit all visible text before export."""
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    fw, fh = fig.bbox.width, fig.bbox.height
    outside, fonts, text_entries = [], [], []
    for t in fig.findobj(Text):
        if not t.get_visible() or not t.get_text().strip():
            continue
        bb = t.get_window_extent(renderer)
        # Text outside the artist's clipping rectangle is not permitted.
        if bb.x0 < -0.5 or bb.y0 < -0.5 or bb.x1 > fw + 0.5 or bb.y1 > fh + 0.5:
            outside.append(t.get_text())
        fonts.append(t.get_fontsize())
        text_entries.append({"text": t.get_text(), "font_pt": t.get_fontsize(),
                             "bbox_figure_fraction": [bb.x0/fw, bb.y0/fh, bb.x1/fw, bb.y1/fh]})
    if outside:
        raise AssertionError(f"{name}: clipped text: {outside}")
    if min(fonts) < STYLE["minimum_pt"]:
        raise AssertionError(f"{name}: type below minimum")
    collisions = []
    width_in, height_in = fig.get_size_inches()
    for index, a in enumerate(text_entries):
        ab = a["bbox_figure_fraction"]
        for b in text_entries[index+1:]:
            bb = b["bbox_figure_fraction"]
            dx = min(ab[2], bb[2]) - max(ab[0], bb[0])
            dy = min(ab[3], bb[3]) - max(ab[1], bb[1])
            if dx > 0 and dy > 0 and dx*width_in*72*dy*height_in*72 > 1:
                collisions.append([a["text"], b["text"]])
    if collisions:
        raise AssertionError(f"{name}: overlapping text: {collisions}")
    OUT.mkdir(parents=True, exist_ok=True)
    for ext in STYLE["exports"]:
        kwargs = {"dpi": STYLE["png_dpi"]} if ext == "png" else {}
        fig.savefig(OUT / f"{name}.{ext}", **kwargs)
    # Small previews are QA only; submission PNG remains 600 dpi.
    preview = ROOT / "evidence" / f"{name}_preview.png"
    fig.savefig(preview, dpi=150)
    QA[name] = {
        "size_inches": list(fig.get_size_inches()), "dpi_png": STYLE["png_dpi"],
        "minimum_text_pt": min(fonts), "font_family": STYLE["font_family"],
        "out_of_canvas_text": outside, "text_bbox_overlaps_above_1_square_pt": collisions,
        "all_text": text_entries,
        "exports": {ext: {"path": str(OUT/f"{name}.{ext}"),
                            "sha256": sha(OUT/f"{name}.{ext}")}
                    for ext in STYLE["exports"]},
        "preview": str(preview), "visual_review": "pending",
    }
    plt.close(fig)


def forest_scaffold(fig, bottom, height, ylim, xlim, xticks):
    # Three aligned columns: contrast/denominator, interval, exact estimate.
    lab = fig.add_axes([0.065, bottom, 0.285, height])
    ax = fig.add_axes([0.370, bottom, 0.345, height])
    val = fig.add_axes([0.750, bottom, 0.235, height])
    for side in (lab, val):
        side.set(xlim=(0, 1), ylim=ylim)
        side.set_axis_off()
    plain_axis(ax, left=False)
    ax.set(xlim=xlim, ylim=ylim, xticks=xticks, yticks=[])
    ax.axvline(0, color=GRAY, lw=0.8, ls=(0, (3, 2)), zorder=0)
    ax.set_xlabel("Difference (percentage points)", labelpad=7)
    return lab, ax, val


def figure3():
    fig = plt.figure(figsize=(W, 3.55))
    panel_header(fig, "", "Prespecified contrasts", 0.927)
    lab, ax, val = forest_scaffold(fig, .22, .60, (-.60, 2.65), (-45, 45), [-40, -20, 0, 20, 40])
    lab.text(0, 2.52, "Contrast / observed events", fontsize=8, weight="bold")
    val.text(0, 2.52, "Estimate [95% CI]", fontsize=8, weight="bold")
    descriptions = [
        ("H1", "A detection: external − internal", "10/16 vs 71/93", COLORS["A"]),
        ("H2", "A review: external − internal", "35/252 vs 174/851", INK),
        ("H3", "External detection: B − A", "13/16 vs 10/16 (paired)", COLORS["B"]),
    ]
    primitive = []
    for y, (key, desc, denom, color) in zip([2, 1, 0], descriptions):
        item = MAIN["contrasts"][key]
        lab.text(0, y + .13, f"{key}  {desc}", fontsize=8.3, weight="bold", va="center")
        lab.text(0, y - .17, denom, fontsize=8, color=GRAY, va="center")
        interval(ax, item, y, color)
        val.text(0, y, value_text(item), fontsize=8.2, va="center")
        primitive.append({"id": key, "label": desc, "observed_events": denom, **item})
    fig.text(.065, .055, "Newcombe method 10; H2 and H3 intervals are nominal.", fontsize=8, color=GRAY)
    PRIMITIVES["Figure_3"] = primitive
    CAPTIONS["Figure_3"] = {
        "mapping": "Rows H1, H2, H3 correspond exactly to primary.json contrasts.",
        "caption": "Prespecified patient-level contrasts. Points show differences in percentage points; horizontal bars show original two-sided 95% Newcombe method 10 confidence intervals. H1 compares Method A low-quality detection in the BrEaST external test cohort with the BUS-BRA internal holdout. H2 compares Method A simulated review fractions between those cohorts. H3 compares low-quality detection for Method B minus Method A among the same 16 external low-quality patients and uses the original paired interval. H2 and H3 intervals are nominal without multiplicity adjustment. Low quality is Dice <0.70. Numerators and denominators are shown for each contrast.",
    }
    export(fig, "Figure_3")


def curves_verified(split, method):
    observed = sorted([r for r in CURVES if r["split"] == split and r["method"] == method],
                      key=lambda r: int(r["reviewed"]))
    ranked = sorted([r for r in RECORDS if r["split"] == split and r["status"] == "scored"],
                    key=lambda r: (-float(r[f"risk_{method}"]), r["patient_id"]))
    x = np.array([int(r["reviewed"]) for r in observed])
    y = np.array([int(r["low_quality_detected"]) for r in observed])
    expected = np.r_[0, np.cumsum([int(r["low_quality"]) for r in ranked])]
    assert np.array_equal(x, np.arange(len(ranked) + 1))
    assert np.array_equal(y, expected), (split, method)
    return x, y


def operating_marker(ax, x, y, method, policy):
    # Redundant shape encoding: squares = locked; circles = top 50.
    ax.plot(x, y, marker="s" if policy == "locked" else "o", ls="none",
            ms=4.8 if policy == "locked" else 5.5,
            mfc=COLORS[method] if policy == "locked" else WHITE,
            mec=COLORS[method], mew=1.0, zorder=5)


def figure4():
    fig = plt.figure(figsize=(W, 5.65))
    axs = [fig.add_axes([.095, .535, .39, .345]),
           fig.add_axes([.590, .535, .39, .345])]
    line_styles = {"A": "-", "B": (0, (4, 2))}
    primitive = {"rank_curves": [], "policy_markers": [], "paired_contrasts": []}
    for ax, split, letter, title in zip(axs, ["internal_holdout", "external_test"],
                                       ["A", "B"], ["Internal holdout", "External test"]):
        c = MAIN["cohorts"][split]
        n, f = c["N"], c["F"]
        plain_axis(ax)
        ax.set(xlim=(0, n), ylim=(0, 104), yticks=[0, 25, 50, 75, 100])
        ax.set_xticks([0, 200, 400, 600, 800] if split == "internal_holdout" else [0, 50, 100, 150, 200, 250])
        ax.set_xlabel("Patients selected for review (count)", labelpad=6, fontsize=8.5)
        if split == "internal_holdout":
            ax.set_ylabel("Low-quality patients detected (%)", labelpad=6, fontsize=8.5)
        fig.text(ax.get_position().x0 - .065, .935, letter, fontsize=10, weight="bold")
        fig.text(ax.get_position().x0, .935, title, fontsize=9.5, weight="bold")
        fig.text(ax.get_position().x0, .901, f"N = {n}; low quality n = {f}", fontsize=8.5, color=GRAY)
        for method in ["A", "B"]:
            x, y = curves_verified(split, method)
            ax.step(x, 100*y/f, where="post", color=COLORS[method], ls=line_styles[method], lw=1.2)
            m = c["methods"][method]
            assert int(y[m["R"]]) == m["TP"]
            operating_marker(ax, m["R"], 100*m["TP"]/f, method, "locked")
            primitive["rank_curves"].append({"split": split, "method": method, "N": n, "F": f,
                "x_review_count": x.tolist(), "y_detected_count": y.tolist(), "drawstyle": "steps-post"})
            primitive["policy_markers"].append({"split": split, "method": method, "policy": "locked", "R": m["R"], "TP": m["TP"], "F": f, "marker": "square"})
            if split == "external_test":
                e = SUPP["external_equal_review"]["methods"][method]
                assert int(y[e["R"]]) == e["TP"]
                operating_marker(ax, e["R"], 100*e["TP"]/f, method, "top50")
                primitive["policy_markers"].append({"split": split, "method": method, "policy": "top50", "R": e["R"], "TP": e["TP"], "F": f, "marker": "open circle"})
        if split == "internal_holdout":
            ax.text(.42, .29, "Locked cutoffs", transform=ax.transAxes, fontsize=8, weight="bold")
            ax.text(.42, .19, "A: 71/93; R = 174", color=COLORS["A"], transform=ax.transAxes, fontsize=8)
            ax.text(.42, .09, "B: 68/93; R = 150", color=COLORS["B"], transform=ax.transAxes, fontsize=8)
    handles = [Line2D([0], [0], color=COLORS[m], ls=line_styles[m], lw=1.2, label=f"Method {m}") for m in ["A", "B"]]
    handles += [Line2D([0], [0], marker="s", ms=4.5, ls="none", color=GRAY, label="Locked cutoff"),
                Line2D([0], [0], marker="o", ms=5, ls="none", mfc=WHITE, mec=GRAY, label="Top 50 per method")]
    fig.legend(handles=handles, loc="center", bbox_to_anchor=(.53, .438), ncol=4,
               frameon=False, columnspacing=1.5, handlelength=2.2, handletextpad=.55)
    panel_header(fig, "C", "External paired detection contrast", .362, x=.095)
    lab, ax, val = forest_scaffold(fig, .120, .185, (-.55, 1.55), (-40, 50), [-40, -20, 0, 20, 40])
    ax.set_xlabel("B − A (percentage points)", fontsize=8.5, labelpad=6)
    val.text(0, 1.5, "Estimate [95% CI]", fontsize=8, weight="bold")
    policies = [
        ("Locked cutoffs", "A: 10/16, R = 35; B: 13/16, R = 33", MAIN["contrasts"]["H3"], "s"),
        ("Top 50 per method", "A: 14/16; B: 13/16; R = 50 each", SUPP["external_equal_review"]["detection_B_minus_A"], "o"),
    ]
    for y, (label, denom, item, marker) in zip([1, 0], policies):
        lab.text(0, y+.14, label, va="center", fontsize=8.5, weight="bold")
        lab.text(0, y-.19, denom, va="center", fontsize=7.5, color=GRAY)
        interval(ax, item, y, INK, marker, open_marker=(marker == "o"))
        val.text(0, y, value_text(item), va="center", fontsize=8)
        primitive["paired_contrasts"].append({"policy": label, "denominators": denom, **item})
    fig.text(.065, .020, "Original paired Newcombe 95% CIs; nominal. Top-50 interval conditions on the observed ranking.", fontsize=7.5, color=GRAY)
    PRIMITIVES["Figure_4"] = primitive
    CAPTIONS["Figure_4"] = {
        "mapping": "A=BUS-BRA internal holdout; B=BrEaST external test; C=primary H3 and supplementary external_equal_review.detection_B_minus_A.",
        "caption": "Risk-ranked review curves and external paired contrasts. Panels A and B show empirical step curves of the fraction of low-quality patients detected versus the actual number selected for simulated review, ranked by descending risk with official CaseID as the lexicographic tie-breaker. The cohorts contain 93/851 and 16/252 low-quality patients, respectively (Dice <0.70). Blue solid and orange dashed curves represent Methods A and B. Filled squares mark the development-locked cutoffs (internal A: 71/93 detected at 174 reviews; B: 68/93 at 150; external A: 10/16 at 35; B: 13/16 at 33). Open circles mark 50 external reviews per method (A: 14/16; B: 13/16). Panel C shows B minus A detection differences with the original paired nominal 95% Newcombe method 10 intervals: +18.75 [−4.28, +40.04] percentage points at locked cutoffs and −6.25 [−31.61, +19.57] at top 50. The latter interval conditions on the observed ranking and does not account for re-ranking in another sample.",
    }
    export(fig, "Figure_4")


def figure_s1():
    fig = plt.figure(figsize=(W, 5.8))
    primitive = []
    for panel, bottom, top, title, key in [
        ("A", .61, .94, "Method A detection: external − internal", "A_detection_external_minus_internal"),
        ("B", .15, .48, "External detection: B − A", "external_detection_B_minus_A"),
    ]:
        panel_header(fig, panel, title, top)
        lab, ax, val = forest_scaffold(fig, bottom, .265, (-.65, 2.65), (-70, 50), [-60, -40, -20, 0, 20, 40])
        lab.text(0, 2.53, "Low-quality definition / n", fontsize=8, weight="bold")
        val.text(0, 2.53, "Estimate [95% CI]", fontsize=8, weight="bold")
        for y, cutoff in zip([2, 1, 0], ["0.50", "0.70", "0.80"]):
            if cutoff == "0.70":
                cohorts = MAIN["cohorts"]
                item = MAIN["contrasts"]["H1" if panel == "A" else "H3"]
            else:
                scenario = SUPP["fixed_threshold_dice_sensitivity"][cutoff]
                cohorts, item = scenario["cohorts"], scenario[key]
            ni = cohorts["internal_holdout"]["F"]
            ne = cohorts["external_test"]["F"]
            denom = f"External {ne}; internal {ni}" if panel == "A" else f"Same {ne} external patients (paired)"
            lab.text(0, y+.13, f"Dice < {cutoff}", fontsize=8.5, weight="bold", va="center")
            lab.text(0, y-.19, denom, fontsize=7.8, color=GRAY, va="center")
            interval(ax, item, y, COLORS["A"] if panel == "A" else COLORS["B"])
            val.text(0, y, value_text(item), fontsize=8, va="center")
            primitive.append({"panel": panel, "dice_cutoff": float(cutoff), "n_internal": ni,
                              "n_external": ne, "denominators": denom, **item})
    fig.text(.065, .025, "Locked risk cutoffs retained throughout; original nominal 95% Newcombe method 10 intervals.", fontsize=8, color=GRAY)
    PRIMITIVES["Figure_S1"] = primitive
    CAPTIONS["Figure_S1"] = {
        "mapping": "A=external-minus-internal Method A detection; B=external B-minus-A paired detection. Each panel uses Dice cutoffs 0.50, 0.70, 0.80, with 0.70 from primary.json and other cutoffs from supplementary.json.",
        "caption": "Sensitivity to the Dice definition of low quality with development-locked risk cutoffs unchanged. Panel A shows Method A detection in the BrEaST external test minus BUS-BRA internal holdout. Panel B shows paired Method B minus Method A detection in BrEaST. Low-quality denominators for Dice <0.50, <0.70, and <0.80 are 53, 93, and 183 internally and 7, 16, and 50 externally. Points show the original differences in percentage points and bars the original nominal two-sided 95% Newcombe method 10 confidence intervals. No interval was replaced by a bootstrap interval.",
    }
    export(fig, "Figure_S1")


def paired_membership(policy):
    ext = [r for r in RECORDS if r["split"] == "external_test" and r["status"] == "scored"]
    selected = {}
    for method in ["A", "B"]:
        if policy == "locked":
            selected[method] = {r["patient_id"] for r in ext if int(r[f"alert_{method}"])}
        else:
            selected[method] = {r["patient_id"] for r in sorted(ext, key=lambda r: (-float(r[f"risk_{method}"]), r["patient_id"]))[:50]}
    membership = {k: [] for k in ["both", "A_only", "B_only", "neither"]}
    for r in ext:
        if not int(r["low_quality"]):
            continue
        pid = r["patient_id"]
        a, b = pid in selected["A"], pid in selected["B"]
        key = "both" if a and b else "A_only" if a else "B_only" if b else "neither"
        membership[key].append(pid)
    for v in membership.values():
        v.sort(key=int)
    expected = (MAIN["cohorts"]["external_test"] if policy == "locked" else SUPP["external_equal_review"])["paired_low_quality"]
    assert {k: len(v) for k, v in membership.items()} == expected
    return membership


def figure_s2():
    fig = plt.figure(figsize=(W, 3.35))
    left = fig.add_axes([.195, .21, .33, .56])
    right = fig.add_axes([.635, .21, .33, .56], sharex=left, sharey=left)
    primitive = []
    cats = ["both", "A_only", "B_only", "neither"]
    labels = ["Both detected", "A only", "B only", "Neither detected"]
    colors = ["#555555", COLORS["A"], COLORS["B"], WHITE]
    for ax, policy, letter, title, detail in [
        (left, "locked", "A", "Locked cutoffs", "A: R = 35; B: R = 33"),
        (right, "top50", "B", "Top 50 per method", "A: R = 50; B: R = 50"),
    ]:
        plain_axis(ax)
        membership = paired_membership(policy)
        values = [len(membership[k]) for k in cats]
        ax.set(xlim=(0, 16.8), ylim=(-.6, 3.6), xticks=[0, 4, 8, 12, 16], yticks=[3, 2, 1, 0])
        ax.barh([3, 2, 1, 0], values, height=.48, color=colors,
                edgecolor=["#555555", COLORS["A"], COLORS["B"], GRAY], linewidth=.8)
        ax.set_yticklabels(labels)
        ax.tick_params(axis="y", length=0, pad=7)
        ax.set_xlabel("Patients (of 16)", labelpad=7)
        if ax is right:
            ax.tick_params(labelleft=False)
        fig.text(ax.get_position().x0 - .052, .914, letter, fontsize=10, weight="bold")
        fig.text(ax.get_position().x0, .914, title, fontsize=9.5, weight="bold")
        fig.text(ax.get_position().x0, .843, detail, fontsize=8.5, color=GRAY)
        for y, n in zip([3, 2, 1, 0], values):
            ax.text(n + .3, y, str(n), va="center", fontsize=9, weight="bold")
        primitive.append({"policy": policy, "N_external": 252, "F_low_quality": 16,
                          "review_counts": {"A": 35 if policy == "locked" else 50, "B": 33 if policy == "locked" else 50},
                          "counts": dict(zip(cats, values)), "real_patient_id_membership": membership})
    fig.text(.195, .047, "Same 16 external low-quality patients (Dice < 0.70) in both panels.", fontsize=8.5, color=GRAY)
    PRIMITIVES["Figure_S2"] = primitive
    CAPTIONS["Figure_S2"] = {
        "mapping": "A=primary.cohorts.external_test.paired_low_quality; B=supplementary.external_equal_review.paired_low_quality. Bar counts independently derived from actual validation records.",
        "caption": "Paired detection outcomes for the same 16 BrEaST external low-quality patients (Dice <0.70), under two review policies. Panel A uses development-locked cutoffs: both methods detect 10 patients, Method A only 0, Method B only 3, and neither 3; the corresponding review counts are 35/252 for A and 33/252 for B. Panel B uses the top 50 ranked patients per method: both detect 12, A only 2, B only 1, and neither 1. The four mutually exclusive outcome categories sum to 16 under each policy. Counts were derived from the archived patient-level flags and deterministic ranking, not read from a previous graphic. The locked-cutoff A-only cell has zero observed support.",
    }
    export(fig, "Figure_S2")


def main():
    figure3()
    figure4()
    figure_s1()
    figure_s2()
    evidence = {
        "scope": "Publication redraw only; approved scientific results retained without re-estimation.",
        "sources": [{"path": str(p), "sha256": sha(p)} for p in
                    [STYLE_PATH, PRIMARY_PATH, SUPP_PATH, CURVE_PATH, RECORDS_PATH, Path(__file__)]],
        "style": STYLE, "caption_mapping": CAPTIONS,
        "figure_primitive_values": PRIMITIVES, "qa": QA,
        "verified_invariants": {
            "all_2210_rank_curve_points_match_patient_records": True,
            "rank_tie_break": "Descending risk then lexicographic patient_id (official CaseID)",
            "original_newcombe_intervals_unchanged": True,
            "external_paired_counts_match_records_and_references": True,
            "no_invented_patient_ids_or_statistical_results": True,
            "no_image_synthesis": True,
            "locked_cutoff_A_only_zero_support_retained": True,
        },
    }
    EVIDENCE.write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote 12 figure exports and evidence to {EVIDENCE}")


if __name__ == "__main__":
    main()
