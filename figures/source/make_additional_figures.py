"""Additional manuscript figures based on the recorded patient-level scores."""
import csv
import sys
from pathlib import Path

import matplotlib as mpl
mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
from matplotlib.lines import Line2D
from matplotlib.patches import Patch


WIDTH_MM = 175
MM_PER_INCH = 25.4
INK = "#202830"
GRAY = "#4D5963"
SPINE = "#A9B2B8"
GRID = "#E5E9EC"
WHITE = "#FFFFFF"
METHOD_COLOR = {"A": "#14658D", "B": "#A9441B"}
METHOD_STYLE = {"A": "-", "B": (0, (4.5, 2.4))}
METHODS = ("A", "B")
PANELS = (
    ("A", "internal_holdout", "BUS-BRA internal test"),
    ("B", "external_test", "BrEaST external test"),
)
CUTS = ("0.50", "0.70", "0.80")

arial = Path("C:/Windows/Fonts/arial.ttf")
if arial.is_file():
    font_manager.fontManager.addfont(str(arial))
mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "DejaVu Sans"],
    "font.size": 9.0,
    "text.color": INK,
    "axes.labelcolor": INK,
    "axes.linewidth": 0.8,
    "xtick.color": INK,
    "ytick.color": INK,
    "pdf.fonttype": 42,
    "svg.fonttype": "none",
    "figure.facecolor": WHITE,
    "savefig.facecolor": WHITE,
})


def heading(ax, label, title, detail, x=0.13):
    ax.text(0, 1.135, label, transform=ax.transAxes, ha="left", va="bottom",
            fontsize=12, fontweight="bold")
    ax.text(x, 1.135, title, transform=ax.transAxes, ha="left", va="bottom",
            fontsize=10.2, fontweight="bold")
    ax.text(x, 1.043, detail, transform=ax.transAxes, ha="left", va="bottom",
            fontsize=8.5, color=GRAY)


def plot_pair(height_mm, bottom):
    fig, axes = plt.subplots(1, 2, sharey=True, figsize=(WIDTH_MM / MM_PER_INCH,
                                                         height_mm / MM_PER_INCH))
    fig.subplots_adjust(left=0.13, right=0.973, bottom=bottom, top=0.78, wspace=0.23)
    for ax in axes:
        ax.set_ylim(0, 105)
        ax.set_yticks(np.arange(0, 101, 20))
        ax.set_axisbelow(True)
        ax.grid(axis="y", color=GRID, linewidth=0.7)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        for name in ("left", "bottom"):
            ax.spines[name].set_color(SPINE)
        ax.tick_params(length=3, width=0.7, pad=4, labelsize=8.8)
    axes[0].set_ylabel("Low-quality masks detected (%)", labelpad=8)
    return fig, axes


def line_key(method, marker=None):
    return Line2D([0], [0], color=METHOD_COLOR[method], linestyle=METHOD_STYLE[method],
                  lw=1.45, marker=marker, markersize=5,
                  markerfacecolor=METHOD_COLOR[method] if method == "A" else "none",
                  label=f"Method {method}")


def rank_curve(rows, method):
    ranked = sorted(rows, key=lambda row: (-float(row[f"risk_{method}"]), row["patient_id"]))
    low = np.array([int(row["low_quality"]) for row in ranked], dtype=int)
    captured = np.r_[0, low.cumsum()]
    return np.arange(len(low) + 1), captured


def detection_by_review(study, rows_by_split):
    fig, axes = plot_pair(98, bottom=0.255)
    equal = study.supp["external_equal_review"]
    for ax, (letter, split, title) in zip(axes, PANELS):
        record = study.main["cohorts"][split]
        n, f = record["N"], record["F"]
        ax.set_xlim(0, 100)
        ax.set_xticks(np.arange(0, 101, 20))
        heading(ax, letter, title, f"{n:,} patients  ·  {f} low-quality masks")
        for method in METHODS:
            reviewed, captured = rank_curve(rows_by_split[split], method)
            if len(reviewed) != n + 1 or captured[-1] != f:
                raise ValueError("Rank curve totals differ from the scored cohort")
            ax.step(100 * reviewed / n, 100 * captured / f, where="post",
                    color=METHOD_COLOR[method], linestyle=METHOD_STYLE[method], lw=1.45)
            fixed = record["methods"][method]
            if captured[fixed["R"]] != fixed["TP"]:
                raise ValueError("The locked operating point is off the ranked curve")
            ax.plot(100 * fixed["R"] / n, 100 * fixed["TP"] / f, linestyle="none",
                    marker="o", markersize=6.0, markerfacecolor=METHOD_COLOR[method],
                    markeredgecolor=WHITE, markeredgewidth=0.9, zorder=5)
            if split == "external_test":
                chosen = equal["methods"][method]
                if captured[chosen["R"]] != chosen["TP"]:
                    raise ValueError("The equal-review point is off the ranked curve")
                ax.plot(100 * chosen["R"] / n, 100 * chosen["TP"] / f, linestyle="none",
                        marker="D", markersize=5.2, markerfacecolor=WHITE,
                        markeredgecolor=METHOD_COLOR[method], markeredgewidth=1.15, zorder=6)
    fig.supxlabel("Patients selected for simulated review (%)", x=0.55, y=0.146, fontsize=9.5)
    locked = Line2D([0], [0], color=GRAY, linestyle="none", marker="o", markersize=5.3,
                    label="Locked threshold")
    matched = Line2D([0], [0], color=GRAY, linestyle="none", marker="D", markersize=5.3,
                     markerfacecolor=WHITE, label="Equal review")
    fig.legend(handles=[line_key("A"), line_key("B"), locked, matched], loc="lower center",
               ncol=4, bbox_to_anchor=(0.53, 0.030), fontsize=8.6, frameon=False,
               columnspacing=1.65, handletextpad=0.54)
    return fig


def dice_cutoff_sensitivity(study):
    fig, axes = plot_pair(97, bottom=0.29)
    sensitivities = study.supp["fixed_threshold_dice_sensitivity"]
    cut_values = [float(c) for c in CUTS]
    for ax, (letter, split, title) in zip(axes, PANELS):
        records = [
            study.main["cohorts"][split] if c == "0.70" else sensitivities[c]["cohorts"][split]
            for c in CUTS
        ]
        heading(ax, letter, title, f"{records[0]['N']:,} scored patients")
        ax.set_xlim(0.46, 0.84)
        ax.set_xticks(cut_values, [f"{c}\n{r['F']} masks" for c, r in zip(CUTS, records)])
        for method in METHODS:
            y = [100 * r["methods"][method]["TP"] / r["F"] for r in records]
            ax.plot(cut_values, y, color=METHOD_COLOR[method], linestyle=METHOD_STYLE[method],
                    lw=1.45, marker="o" if method == "A" else "s",
                    markersize=4.8 if method == "A" else 6.6,
                    markerfacecolor=METHOD_COLOR[method] if method == "A" else "none",
                    markeredgewidth=1.15, zorder=3)
    fig.supxlabel("Reference Dice cutoff and number of low-quality masks", x=0.55, y=0.132,
                  fontsize=9.4)
    fig.legend(handles=[line_key("A", "o"), line_key("B", "s")], loc="lower center",
               ncol=2, bbox_to_anchor=(0.53, 0.026), fontsize=8.8, frameon=False,
               columnspacing=2.1, handletextpad=0.56)
    return fig


def paired_external_outcomes(study):
    fixed = study.main["cohorts"]["external_test"]
    matched = study.supp["external_equal_review"]
    fig, axes = plt.subplots(1, 2, figsize=(WIDTH_MM / MM_PER_INCH, 101 / MM_PER_INCH))
    fig.subplots_adjust(left=0.10, right=0.90, bottom=0.18, top=0.80, wspace=0.13)
    colors = ["#314653", METHOD_COLOR["A"], METHOD_COLOR["B"], "#D6DCDE"]
    keys = ["both", "A_only", "B_only", "neither"]
    labels = ["Both flagged", "A only", "B only", "Neither flagged"]
    titles = ["Locked risk thresholds", "Equal external review"]
    details = [
        f"A {fixed['methods']['A']['R']}/{fixed['N']}  ·  B {fixed['methods']['B']['R']}/{fixed['N']} flagged",
        f"{matched['review_count_per_method']}/{matched['N']} selected per method",
    ]
    for ax, letter, rec, title, detail in zip(axes, ("A", "B"), (fixed, matched), titles, details):
        vals = [rec["paired_low_quality"][k] for k in keys]
        total = rec["F"]
        if sum(vals) != total:
            raise ValueError("Donut categories do not cover the paired cohort")

        def count_label(percent):
            count = round(percent * total / 100)
            return str(count) if count else ""

        _, _, numbers = ax.pie(
            vals, colors=colors, radius=0.96, counterclock=False, startangle=90,
            wedgeprops={"width": 0.34, "edgecolor": WHITE, "linewidth": 1.4},
            autopct=count_label, pctdistance=0.82, textprops={"fontsize": 9.4},
        )
        for i, label in enumerate(numbers):
            label.set_color(INK if i == 3 else WHITE)
            label.set_fontweight("bold")
        ax.set_xlim(-1.09, 1.09)
        ax.set_ylim(-1.09, 1.09)
        ax.text(0, 0.085, str(total), ha="center", va="center",
                fontsize=20, fontweight="bold")
        ax.text(0, -0.20, "low-quality masks", ha="center", va="center",
                fontsize=8.7, color=GRAY)
        heading(ax, letter, title, detail, x=0.14)
    keys_legend = [Patch(facecolor=c, edgecolor="none", label=l) for c, l in zip(colors, labels)]
    fig.legend(handles=keys_legend, loc="lower center", ncol=4,
               bbox_to_anchor=(0.50, 0.048), fontsize=8.8, frameon=False,
               columnspacing=1.65, handletextpad=0.56)
    return fig


def export(fig, name, output, qa):
    fig.canvas.draw()
    report = require_matplotlib_panel_alignment(
        fig, panel_ids=["A", "B"], json_out=qa / f"{name}.alignment.json",
        tolerance_pt=1.5, gutter_tolerance_pt=1.5, strict=True,
    )
    anchors = []
    for ax, letter in zip(fig.axes, ("A", "B")):
        label = next(text for text in ax.texts if text.get_text() == letter)
        display = label.get_transform().transform(label.get_position())
        anchors.append((display - np.array([ax.bbox.x0, ax.bbox.y1])) * 72 / fig.dpi)
    if max(abs(anchors[0] - anchors[1])) > 1.5:
        raise ValueError("Uppercase panel labels are not aligned")
    if len(report["layout"]["panels"]) != 2:
        raise ValueError("Two panels must be measured in every figure")
    fig.savefig(output / f"{name}.png", dpi=600)
    fig.savefig(qa / f"{name}.pdf")
    fig.savefig(qa / f"{name}.svg")
    plt.close(fig)
    print(f"Exported {name} with aligned panels")


if __name__ == "__main__":
    project, output, qa, source_work, skill_scripts = map(Path, sys.argv[1:6])
    sys.path[:0] = [str(source_work), str(skill_scripts)]
    from display_data import load_study
    from audit_panel_alignment import require_matplotlib_panel_alignment

    study = load_study(project)
    with (project / "formal_validation/validation_cases.csv").open(
        encoding="utf-8-sig", newline=""
    ) as source:
        rows = list(csv.DictReader(source))
    groups = {split: [row for row in rows if row["split"] == split] for _, split, _ in PANELS}
    for label, figure in (
        ("Figure_4_detection_by_review", detection_by_review(study, groups)),
        ("Figure_S1_dice_cutoff_sensitivity", dice_cutoff_sensitivity(study)),
        ("Figure_S2_paired_external_outcomes", paired_external_outcomes(study)),
    ):
        export(figure, label, output, qa)

