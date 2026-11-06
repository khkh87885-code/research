"""Redraw the study curves, sensitivity contrasts, and paired counts."""
import csv
import sys
from pathlib import Path

import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D


PROJECT, OUTPUT, QA, VALIDATION, PREVIOUS, AUDIT = map(Path, sys.argv[1:7])
sys.path[:0] = [str(VALIDATION), str(PREVIOUS), str(AUDIT)]
from display_data import interval, load_study, signed
from make_additional_figures import (
    GRAY, GRID, INK, METHOD_COLOR, METHOD_STYLE, METHODS, MM_PER_INCH,
    PANELS, SPINE, WHITE, WIDTH_MM, heading, line_key, rank_curve,
)
from audit_panel_alignment import require_matplotlib_panel_alignment


mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "DejaVu Sans"],
    "pdf.fonttype": 42,
    "svg.fonttype": "none",
})

SHADE = "#EDF3F5"
PRIMARY_BLUE = METHOD_COLOR["A"]
PAIRED_ORANGE = METHOD_COLOR["B"]


def canvas(height_mm):
    return plt.figure(figsize=(WIDTH_MM / MM_PER_INCH, height_mm / MM_PER_INCH))


def style_axis(ax, grid=False):
    for edge in ("top", "right"):
        ax.spines[edge].set_visible(False)
    for edge in ("bottom", "left"):
        ax.spines[edge].set_color(SPINE)
    ax.tick_params(labelsize=8.6, width=0.7, length=3, pad=4)
    ax.set_axisbelow(True)
    if grid:
        ax.grid(axis="y", color=GRID, linewidth=0.65)


def operating_marker(ax, x, y, method, matched=False, size=5.4):
    color = METHOD_COLOR[method]
    ax.plot(x, y, linestyle="none", marker="D" if matched else "o", markersize=size,
            markerfacecolor=WHITE if matched else color,
            markeredgecolor=color if matched else WHITE, markeredgewidth=1.12 if matched else 0.8,
            zorder=5)


def review_curves(study, by_cohort):
    fig = canvas(143)
    grid = fig.add_gridspec(2, 2, left=0.13, right=0.972, bottom=0.19, top=0.883,
                            hspace=0.62, wspace=0.23, height_ratios=(1.04, 0.94))
    axes = [fig.add_subplot(grid[0, 0])]
    axes.append(fig.add_subplot(grid[0, 1], sharex=axes[0], sharey=axes[0]))
    equal = study.supp["external_equal_review"]
    external = study.main["cohorts"]["external_test"]
    for ax, (letter, split, title) in zip(axes, PANELS):
        record = study.main["cohorts"][split]
        n, f = record["N"], record["F"]
        style_axis(ax, grid=True)
        ax.set(xlim=(0, 100), ylim=(0, 105), xticks=[0, 20, 40, 60, 80, 100],
               yticks=[0, 25, 50, 75, 100])
        heading(ax, letter, title, f"{n:,} patients  ·  {f} low-quality masks")
        for method in METHODS:
            reviewed, detected = rank_curve(by_cohort[split], method)
            if len(reviewed) != n + 1 or detected[-1] != f:
                raise ValueError("Curve endpoint differs from the verified cohort total")
            ax.step(100 * reviewed / n, 100 * detected / f, where="post",
                    color=METHOD_COLOR[method], linestyle=METHOD_STYLE[method], linewidth=1.35)
            item = record["methods"][method]
            if detected[item["R"]] != item["TP"]:
                raise ValueError("Locked threshold does not match the ranking")
            operating_marker(ax, 100 * item["R"] / n, 100 * item["TP"] / f, method, size=5.2)
            if split == "external_test":
                target = equal["methods"][method]
                if detected[target["R"]] != target["TP"]:
                    raise ValueError("Equal review does not match the ranking")
                operating_marker(ax, 100 * target["R"] / n, 100 * target["TP"] / f,
                                 method, matched=True, size=4.9)
    axes[0].set_ylabel("Detected (%)", labelpad=7)
    axes[1].tick_params(labelleft=False)
    fig.text(0.552, axes[0].get_position().y0 - 0.062,
             "Patients selected for simulated review (%)",
             ha="center", va="top", fontsize=9.1)

    ax = fig.add_subplot(grid[1, :])
    style_axis(ax, grid=True)
    heading(ax, "C", "BrEaST at the two review settings",
            f"Same {external['F']} low-quality masks", x=0.069)
    ax.set_xlim(-0.62, 1.62)
    ax.set_ylim(50, 100)
    ax.set_yticks([50, 60, 70, 80, 90, 100])
    ax.set_ylabel("Detected (%)", labelpad=7)
    n, f = external["N"], external["F"]
    fixed_a = external["methods"]["A"]["R"]
    fixed_b = external["methods"]["B"]["R"]
    budget = equal["review_count_per_method"]
    ax.set_xticks(
        [0, 1],
        [f"Locked thresholds\nA {fixed_a}/{n}, B {fixed_b}/{n} flagged",
         f"Equal review\n{budget}/{n} selected per method"],
    )
    ax.tick_params(axis="x", length=0, pad=6)
    for method in METHODS:
        counts = (external["methods"][method]["TP"], equal["methods"][method]["TP"])
        y = [100 * value / f for value in counts]
        ax.plot([0, 1], y, color=METHOD_COLOR[method], linestyle=METHOD_STYLE[method], lw=1.25)
        for x, n_detected, value in zip((0, 1), counts, y):
            operating_marker(ax, x, value, method, matched=(x == 1), size=5.8)
            side = -8 if x == 0 else 8
            ax.annotate(f"{n_detected}/{f} ({value:.2f}%)", xy=(x, value),
                        xytext=(side, 0), textcoords="offset points",
                        ha="right" if x == 0 else "left", va="center",
                        fontsize=8.8, fontweight="bold", color=INK)

    locked = Line2D([0], [0], color=GRAY, linestyle="none", marker="o", markersize=5.3,
                    label="Locked threshold")
    matched = Line2D([0], [0], color=GRAY, linestyle="none", marker="D", markersize=5.3,
                     markerfacecolor=WHITE, label="Equal review")
    fig.legend(handles=[line_key("A"), line_key("B"), locked, matched], ncol=4,
               loc="lower center", bbox_to_anchor=(0.54, 0.035), fontsize=8.6,
               frameon=False, columnspacing=1.6, handletextpad=0.57)
    return fig


def dice_contrasts(study):
    fig = canvas(101)
    grid = fig.add_gridspec(1, 2, left=0.255, right=0.975, top=0.77, bottom=0.21, wspace=0.18)
    left = fig.add_subplot(grid[0, 0])
    right = fig.add_subplot(grid[0, 1], sharex=left, sharey=left)
    headings = [
        ("A", "Method A detection", "External minus internal"),
        ("B", "BrEaST detection", "Method B minus Method A"),
    ]
    for ax, (letter, title, subtitle) in zip((left, right), headings):
        heading(ax, letter, title, subtitle, x=0.14)
        style_axis(ax)
        ax.spines["left"].set_visible(False)
        ax.set(xlim=(-67, 46), ylim=(-0.54, 2.63),
               xticks=[-60, -40, -20, 0, 20, 40], yticks=[])
        ax.axhspan(0.54, 1.49, color=SHADE, zorder=0)
        ax.axvline(0, color=SPINE, linestyle=(0, (3, 2)), lw=0.9, zorder=1)
    for y, cutoff in zip((2, 1, 0), ("0.50", "0.70", "0.80")):
        if cutoff == "0.70":
            cohort = study.main["cohorts"]
            contrasts = [study.main["contrasts"]["H1"], study.main["contrasts"]["H3"]]
        else:
            scenario = study.supp["fixed_threshold_dice_sensitivity"][cutoff]
            cohort = scenario["cohorts"]
            contrasts = [scenario["A_detection_external_minus_internal"],
                         scenario["external_detection_B_minus_A"]]
        n_internal = cohort["internal_holdout"]["F"]
        n_external = cohort["external_test"]["F"]
        left.text(-0.675, y + 0.14, f"Dice < {cutoff}",
                  transform=left.get_yaxis_transform(), ha="left", va="center",
                  fontsize=9.3, fontweight="bold")
        left.text(-0.675, y - 0.21, f"{n_internal} internal  ·  {n_external} external",
                  transform=left.get_yaxis_transform(), ha="left", va="center",
                  fontsize=8.15, color=GRAY)
        for ax, record, color in zip((left, right), contrasts, (PRIMARY_BLUE, PAIRED_ORANGE)):
            x = record["difference_pp"]
            lo, hi = record["ci95_pp"]
            primary = ax is left and cutoff == "0.70"
            ax.errorbar(x, y + 0.16, xerr=[[x - lo], [hi - x]], fmt="o", capsize=2.8,
                        lw=1.45, color=color, markersize=5.8 if primary else 5.2,
                        markerfacecolor=color if primary else WHITE, markeredgewidth=1.15,
                        zorder=3)
            ax.text(-2.9, y - 0.22, f"{signed(x)} {interval(record)}",
                    ha="right", va="center", fontsize=8.05,
                    fontweight="bold" if primary else "normal")
    fig.text(0.62, 0.103, "Detection rate difference (percentage points), 95% CI",
             ha="center", va="center", fontsize=9.2)
    return fig


def paired_counts(study):
    fig = canvas(83)
    grid = fig.add_gridspec(1, 2, left=0.244, right=0.975, top=0.72, bottom=0.16, wspace=0.20)
    left = fig.add_subplot(grid[0, 0])
    right = fig.add_subplot(grid[0, 1], sharex=left, sharey=left)
    fixed = study.main["cohorts"]["external_test"]
    equal = study.supp["external_equal_review"]
    f, n = fixed["F"], fixed["N"]
    a_review, b_review = (fixed["methods"][m]["R"] for m in METHODS)
    settings = (
        ("A", "Locked thresholds", f"A {a_review}/{n}, B {b_review}/{n} flagged", fixed),
        ("B", "Equal review", f"{equal['review_count_per_method']}/{n} selected per method", equal),
    )
    categories = (
        ("both", "Both flagged", "#344955"),
        ("A_only", "A only", PRIMARY_BLUE),
        ("B_only", "B only", PAIRED_ORANGE),
        ("neither", "Neither flagged", "#D6DDE0"),
    )
    for ax, (letter, title, detail, record) in zip((left, right), settings):
        if sum(record["paired_low_quality"].values()) != f:
            raise ValueError("Outcome categories do not add up to the paired cohort size")
        ax.set(xlim=(0.15, 15.25), ylim=(-0.49, 3.64), xticks=[], yticks=[])
        ax.set_axis_off()
        heading(ax, letter, title, detail, x=0.14)
        ax.text(14.35, 3.59, "Count", ha="center", va="center", fontsize=8.25, color=GRAY)
        ax.plot([13.05, 13.05], [-0.30, 3.45], color=GRID, lw=0.8)
        for separator in (0.5, 1.5, 2.5):
            ax.axhline(separator, color=GRID, lw=0.65)
        for y, (key, label, color) in zip((3, 2, 1, 0), categories):
            value = record["paired_low_quality"][key]
            if ax is left:
                left.text(-0.635, y, label, transform=left.get_yaxis_transform(),
                          ha="left", va="center", fontsize=9.2, color=INK)
            ax.scatter(np.arange(1, value + 1), np.full(value, y), s=30,
                       color=color, edgecolor=SPINE if key == "neither" else color,
                       linewidth=0.62, zorder=2)
            ax.text(14.35, y, str(value), ha="center", va="center",
                    fontsize=10.2, fontweight="bold", color=INK)
    fig.text(0.5, 0.059,
             f"Each dot represents one case. Both panels show the same {f} BrEaST masks with Dice < 0.70.",
             ha="center", va="center", fontsize=8.75, color=GRAY)
    return fig


def export(fig, name, panel_ids):
    fig.canvas.draw()
    require_matplotlib_panel_alignment(
        fig, panel_ids=panel_ids, json_out=QA / f"{name}.alignment.json",
        tolerance_pt=1.5, gutter_tolerance_pt=1.5, strict=True,
    )
    anchors = []
    for ax, letter in zip(fig.axes[:2], panel_ids[:2]):
        marker = next(label for label in ax.texts if label.get_text() == letter)
        anchor = marker.get_transform().transform(marker.get_position())
        anchors.append((anchor - np.array([ax.bbox.x0, ax.bbox.y1])) * 72 / fig.dpi)
    if max(abs(anchors[0] - anchors[1])) > 1.5:
        raise ValueError("Comparable panel letters are misaligned")
    fig.savefig(OUTPUT / f"{name}.png", dpi=600)
    fig.savefig(QA / f"{name}.pdf")
    fig.savefig(QA / f"{name}.svg")
    plt.close(fig)
    print(f"Rendered {name} with measured panel alignment")


def main():
    study = load_study(PROJECT)
    with (PROJECT / "formal_validation/validation_cases.csv").open(
        encoding="utf-8-sig", newline=""
    ) as file:
        rows = list(csv.DictReader(file))
    by_cohort = {split: [row for row in rows if row["split"] == split]
                 for _, split, _ in PANELS}
    export(review_curves(study, by_cohort), "Figure_4_review_curves", ["A", "B", "C"])
    export(dice_contrasts(study), "Figure_S1_dice_cutoff_contrasts", ["A", "B"])
    export(paired_counts(study), "Figure_S2_external_paired_counts", ["A", "B"])


if __name__ == "__main__":
    main()

