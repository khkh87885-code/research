"""Draw the three manuscript figures from the verified study records."""
import sys
from pathlib import Path

import matplotlib as mpl
mpl.use("Agg")

import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from display_data import load_study


INK = "#1E2935"
BLUE = "#164C68"
MUTED = "#495C69"
EDGE = "#9DAEB8"
PAPER = "#F2F6F8"
ACCENT = "#E6F0F4"
WHITE = "#FFFFFF"
WIDTH_MM = 175
MM_PER_INCH = 25.4

arial = Path("C:/Windows/Fonts/arial.ttf")
if arial.is_file():
    font_manager.fontManager.addfont(str(arial))
mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "DejaVu Sans"],
    "font.size": 9,
    "text.color": INK,
    "axes.labelcolor": INK,
    "xtick.color": INK,
    "axes.linewidth": 0.8,
    "pdf.fonttype": 42,
    "svg.fonttype": "none",
    "figure.facecolor": WHITE,
    "savefig.facecolor": WHITE,
})


def canvas(height_mm):
    fig = plt.figure(figsize=(WIDTH_MM / MM_PER_INCH, height_mm / MM_PER_INCH))
    ax = fig.add_axes([0.0, 0.0, 1.0, 1.0], xlim=(0, 100), ylim=(0, 100))
    ax.set_axis_off()
    return fig, ax


def box(ax, x, y, w, h, title, details, accent=False):
    rect = FancyBboxPatch(
        (x - w / 2, y - h / 2), w, h,
        boxstyle="round,pad=0,rounding_size=1.05",
        facecolor=ACCENT if accent else PAPER,
        edgecolor=BLUE if accent else EDGE, linewidth=0.9, zorder=2,
    )
    ax.add_patch(rect)
    ax.text(x, y + (4.5 if len(details) == 1 else 7.0), title,
            ha="center", va="center", fontsize=10.4, fontweight="bold", zorder=3)
    offsets = [-4.5] if len(details) == 1 else [-0.5, -8.0]
    for detail, offset in zip(details, offsets):
        ax.text(x, y + offset, detail, ha="center", va="center", fontsize=9.15, zorder=3)


def connector(ax, points, arrow=False):
    xx, yy = zip(*points)
    if arrow:
        ax.add_patch(FancyArrowPatch(points[0], points[1], arrowstyle="-|>",
                                    color=MUTED, lw=0.9, mutation_scale=8.3,
                                    shrinkA=0, shrinkB=0, zorder=1))
    else:
        ax.plot(xx, yy, color=MUTED, linewidth=0.9, zorder=1)


def cohort_flow(study):
    internal = study.main["cohorts"]["internal_holdout"]
    external = study.main["cohorts"]["external_test"]
    n_dev = study.dev["scored_patients"]
    excluded = len(study.external["eligibility"]["excluded_normal_case_ids_without_main_mask"])
    fig, ax = canvas(78)
    box(ax, 25, 81, 42, 24, "BUS-BRA", [f"{n_dev + internal['N']:,} patients"], accent=True)
    box(ax, 75, 81, 42, 24, "BrEaST", [f"{external['N'] + excluded:,} patients"], accent=True)
    for center, left, right in [(25, 13, 37), (75, 63, 87)]:
        connector(ax, [(center, 69), (center, 58)])
        connector(ax, [(left, 58), (right, 58)])
        connector(ax, [(left, 58), (left, 47)], arrow=True)
        connector(ax, [(right, 58), (right, 47)], arrow=True)
    box(ax, 13, 31, 22, 32, "Development",
        [f"{n_dev:,} patients", "Threshold selection"])
    box(ax, 37, 31, 22, 32, "Internal testing",
        [f"{internal['N']:,} patients", f"{internal['F']} low-quality masks"], accent=True)
    box(ax, 63, 31, 22, 32, "External testing",
        [f"{external['N']:,} patients", f"{external['F']} low-quality masks"], accent=True)
    box(ax, 87, 31, 22, 32, "Excluded",
        [f"{excluded} normal cases", "No main lesion mask"])
    ax.text(50, 6.5, "Low-quality counts use Dice < 0.70 against the manual reference",
            ha="center", va="center", fontsize=8.5, color=MUTED)
    return fig


def scoring_workflow():
    fig, ax = canvas(111)
    box(ax, 50, 89, 72, 17, "Image and lesion box",
        ["Ultrasound image and a box derived from the manual contour"])
    connector(ax, [(50, 80.5), (50, 73.5)], arrow=True)
    box(ax, 50, 65, 72, 17, "Frozen SAM ViT-B",
        ["One image encoding, one initial mask and its predicted IoU"], accent=True)
    connector(ax, [(50, 56.5), (50, 54)])
    connector(ax, [(27, 54), (73, 54)])
    connector(ax, [(27, 54), (27, 50)], arrow=True)
    connector(ax, [(73, 54), (73, 50)], arrow=True)
    box(ax, 27, 39, 42, 22, "Method A", ["1 − predicted IoU", "Initial-mask quality score"])
    box(ax, 73, 39, 42, 22, "Method B", ["1 − mean Dice", "Four shifted-box masks vs initial mask"])
    for x, method in [(27, "A"), (73, "B")]:
        connector(ax, [(x, 28), (x, 24.5)], arrow=True)
        box(ax, x, 16, 42, 17, f"Method {method} review flag",
            [f"{method} score ≥ locked {method} threshold"], accent=True)
    ax.text(50, 3.5, "Evaluation label uses Dice < 0.70 between the initial mask and manual contour",
            ha="center", va="center", fontsize=8.5, color=MUTED)
    return fig


def planned_contrasts(study):
    fig = plt.figure(figsize=(WIDTH_MM / MM_PER_INCH, 70 / MM_PER_INCH))
    ax = fig.add_axes([0.41, 0.27, 0.55, 0.64])
    ax.set_ylim(0.5, 3.5)
    ax.set_xlim(-46, 46)
    ax.set_yticks([])
    ax.set_xticks([-40, -20, 0, 20, 40])
    ax.set_xlabel("Difference in proportions (percentage points)", labelpad=7)
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color(EDGE)
    ax.tick_params(axis="x", length=3, pad=4, labelsize=9)
    ax.axvline(0, color=EDGE, linewidth=0.9, linestyle=(0, (3, 3)), zorder=1)
    labels = (
        ("H1", "Method A detection", "Primary · external minus internal"),
        ("H2", "Method A simulated review", "Secondary · external minus internal"),
        ("H3", "External detection", "Secondary · Method B minus A"),
    )
    for y, (code, title, subtitle) in zip((3, 2, 1), labels):
        record = study.main["contrasts"][code]
        x = record["difference_pp"]
        lo, hi = record["ci95_pp"]
        primary = code == "H1"
        color = BLUE if primary else MUTED
        ax.errorbar(x, y, xerr=[[x - lo], [hi - x]], fmt="o", capsize=3.0,
                    markersize=6.1 if primary else 5.7, color=color,
                    markerfacecolor=color if primary else WHITE, markeredgewidth=1.2,
                    elinewidth=1.6 if primary else 1.25, zorder=3)
        ax.text(-0.69, y + 0.14, f"{code}  {title}",
                transform=ax.get_yaxis_transform(), va="center", ha="left",
                fontsize=10, fontweight="bold", clip_on=False)
        ax.text(-0.69, y - 0.17, subtitle, transform=ax.get_yaxis_transform(),
                va="center", ha="left", fontsize=8.55, color=MUTED, clip_on=False)
    return fig


def export(fig, name, output, qa):
    fig.canvas.draw()
    require_matplotlib_panel_alignment(fig, json_out=qa / f"{name}.alignment.json",
          tolerance_pt=1.5, gutter_tolerance_pt=1.5, strict=True)
    fig.savefig(output / f"{name}.png", dpi=600)
    fig.savefig(qa / f"{name}.pdf")
    fig.savefig(qa / f"{name}.svg")
    plt.close(fig)


if __name__ == "__main__":
    project, output, qa, audit_module = map(Path, sys.argv[1:5])
    sys.path.insert(0, str(audit_module))
    from audit_panel_alignment import require_matplotlib_panel_alignment
    study = load_study(project)
    for name, figure in (
        ("Figure_1_cohort_flow", cohort_flow(study)),
        ("Figure_2_scoring_workflow", scoring_workflow()),
        ("Figure_3_planned_contrasts", planned_contrasts(study)),
    ):
        export(figure, name, output, qa)

