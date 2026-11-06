"""Draw the SAM quality-screening workflow with a verified BrEaST example."""
from hashlib import sha256
from itertools import combinations
import json
import re
from pathlib import Path
import sys

import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgb
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Rectangle
import numpy as np

sys.path.insert(0, str(Path(sys.argv[1]) / "scripts"))
from audit_panel_alignment import require_matplotlib_panel_alignment


WORK = Path(__file__).resolve().parent
PREFIX = WORK / "Figure_2_SAM_architecture_preview"
WIDTH_MM = 175.0
W, H = WIDTH_MM, 108.0
INK = "#142C3D"
SUB = "#465F70"
LINE = "#5D7789"
HAIR = "#C8D6DF"
PANEL = "#F4F8FA"
WHITE = "#FFFFFF"
BLUE, ORANGE = "#14658D", "#A9441B"
A_PALE, B_PALE = "#EAF4F9", "#FCF0E9"
BLUE_LIGHT, ORANGE_LIGHT = "#81CEE5", "#F5A980"
PHOTO_BOX = "#5FD4EC"
PHOTO_REF = "#FFFDF7"
MASK_BG = "#1C2D3B"

mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "svg.fonttype": "none",
    "image.composite_image": False,
    "pdf.fonttype": 42,
    "savefig.facecolor": WHITE,
    "font.size": 7.1,
    "axes.unicode_minus": False,
})


def round_box(ax, x, y, w, h, face, edge=HAIR, radius=1.25, lw=0.65, gid=None):
    patch = FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={radius}",
                           facecolor=face, edgecolor=edge, linewidth=lw, zorder=1)
    patch.set_gid(gid)
    ax.add_patch(patch)
    return patch


def draw_line(ax, points, *, color=LINE, width=0.95, style="-", z=4):
    x, y = zip(*points)
    return ax.plot(x, y, color=color, lw=width, ls=style,
                   solid_capstyle="round", zorder=z)[0]


def arrow(ax, points, *, color=LINE, width=1.05, gid=None):
    if len(points) > 2:
        draw_line(ax, points[:-1], color=color, width=width, z=4)
    tip = FancyArrowPatch(points[-2], points[-1], arrowstyle="-|>", mutation_scale=8.5,
                          shrinkA=0, shrinkB=0, linewidth=width, color=color,
                          joinstyle="round", capstyle="round", zorder=4)
    tip.set_gid(gid)
    ax.add_patch(tip)


def label(ax, x, y, value, *, size=7.1, color=INK, weight="normal", ha="left", gid=None):
    t = ax.text(x, y, value, ha=ha, va="center", fontweight=weight,
                fontsize=size, color=color, zorder=6)
    t.set_gid(gid)
    return t


def picture(ax, rgb, x, y, w, h, gid):
    art = ax.imshow(rgb, extent=(x, x + w, y + h, y), origin="upper",
                    interpolation="nearest", zorder=2, aspect="auto")
    art.set_gid(gid)


def silhouette(mask, tint):
    rgb = np.zeros((*mask.shape, 3), dtype=np.uint8)
    rgb[:] = np.rint(255 * np.array(to_rgb(MASK_BG))).astype(np.uint8)
    rgb[mask] = np.rint(255 * np.array(to_rgb(tint))).astype(np.uint8)
    return rgb


def shape_box(ax, coords, map_x, map_y, *, color, width, style="-", gid=None):
    x0, y0, x1, y1 = coords
    patch = Rectangle((map_x(x0), map_y(y0)), map_x(x1) - map_x(x0),
                      map_y(y1) - map_y(y0), facecolor="none", edgecolor=color,
                      linewidth=width, linestyle=style, zorder=4)
    patch.set_gid(gid)
    ax.add_patch(patch)


def module(ax, x, y, width, height, title, detail, gid):
    round_box(ax, x, y, width, height, WHITE, edge="#9BB1C0", gid=gid)
    label(ax, x + width / 2, y + 5.55, title, size=8.0, weight="bold", ha="center",
          gid=f"{gid}-title")
    label(ax, x + width / 2, y + 11.0, detail, size=6.8, color=SUB, ha="center")


def image_embedding(ax, x, y):
    """A visual token symbol, without a claim about tensor dimensions."""
    for offset in (1.9, 0.95, 0):
        round_box(ax, x + offset, y - offset, 7.6, 8.0, "#E5EEF3",
                  edge="#88A2B2", radius=0.48, lw=0.55)
    for fraction in (1 / 3, 2 / 3):
        draw_line(ax, [(x + 7.6 * fraction, y), (x + 7.6 * fraction, y + 8.0)],
                  color="#ADC0CB", width=0.48)
        draw_line(ax, [(x, y + 8.0 * fraction), (x + 7.6, y + 8.0 * fraction)],
                  color="#ADC0CB", width=0.48)


def prompt_embeddings(ax, x, y):
    for i in range(5):
        round_box(ax, x, y + 1.65 * i, 8.6, 1.15, "#D5E3EB" if i == 0 else WHITE,
                  edge="#8DA8B9", radius=0.35, lw=0.55)


def make_panel(fig, left, right, letter, title):
    axis = fig.add_axes([left / W, (H - 90.0) / H, (right - left) / W, 86.0 / H],
                        label=letter, zorder=1)
    axis.set_xlim(left, right)
    axis.set_ylim(90.0, 4.0)
    axis.axis("off")
    label(axis, left, 7.5, letter, size=10.3, weight="bold", gid=f"panel-{letter}")
    label(axis, left + 5.6, 7.5, title, size=9.0, weight="bold")
    draw_line(axis, [(left, 11.15), (right, 11.15)], color=HAIR, width=0.78, z=1)
    return axis


def inputs(ax, image, reference, boxes, crop):
    """Show a single true image and the exact prompt coordinates used in inference."""
    x0, y0, x1, y1 = crop
    scene = image[y0:y1, x0:x1]
    ref = reference[y0:y1, x0:x1]
    x, y, w = 5.4, 18.1, 40.15
    h = w * (y1 - y0) / (x1 - x0)
    label(ax, x, 15.65, "BrEaST case 001", size=7.25, weight="bold")
    picture(ax, scene, x, y, w, h, "br-east-case-001-image")
    ax.add_patch(Rectangle((x, y), w, h, fc="none", ec="#425565", lw=0.65, zorder=3))
    map_x = lambda value: x + (value - x0) * w / (x1 - x0)
    map_y = lambda value: y + (value - y0) * h / (y1 - y0)
    contour_x = map_x(np.arange(x0, x1) + 0.5)
    contour_y = map_y(np.arange(y0, y1) + 0.5)
    ax.contour(contour_x, contour_y, ref, levels=[0.5], colors=["#223340"],
               linewidths=1.55, zorder=4)
    ax.contour(contour_x, contour_y, ref, levels=[0.5], colors=[PHOTO_REF],
               linewidths=0.8, linestyles="dashed", zorder=5)
    shape_box(ax, boxes[0], map_x, map_y, color=PHOTO_BOX, width=1.0,
              gid="initial-prompt-on-image")
    draw_line(ax, [(5.5, 51.1), (8.4, 51.1)], color="#35849D", width=1.05)
    label(ax, 9.6, 51.1, "Initial box", size=6.8)
    draw_line(ax, [(22.5, 51.1), (25.4, 51.1)], color=LINE, width=0.87, style="--")
    label(ax, 26.55, 51.1, "Manual contour", size=6.8)
    label(ax, 5.4, 57.2, "10% margin per side, then clipped", size=7.0)
    round_box(ax, 3.5, 62.1, 44.0, 27.9, PANEL, gid="shifted-prompt-container")
    label(ax, 5.6, 66.55, "Initial box and four shifts", size=8.0, weight="bold")
    label(ax, 5.6, 71.3, "5% of clipped box width or height", size=6.85, color=SUB)

    scale = 6.7 / (x1 - x0)
    prompt_h = scale * (y1 - y0)
    for i, direction in enumerate(("Left", "Right", "Up", "Down")):
        tile_x = 5.5 + i * 10.55
        round_box(ax, tile_x, 75.1, 8.55, 7.3, WHITE, edge="#CDD9E0", radius=0.5, lw=0.55)
        pic_x = tile_x + (8.55 - 6.7) / 2
        pic_y = 75.1 + (7.3 - prompt_h) / 2
        tx = lambda value: pic_x + (value - x0) * scale
        ty = lambda value: pic_y + (value - y0) * scale
        shape_box(ax, boxes[0], tx, ty, color="#A5B6C0", width=0.58, style="--")
        shape_box(ax, boxes[i + 1], tx, ty, color="#375C72", width=0.78,
                  gid=f"prompt-{direction.lower()}")
        label(ax, tile_x + 4.275, 86.1, direction, size=6.7, ha="center")


def model(ax):
    round_box(ax, 52.5, 13.6, 65.0, 76.4, PANEL, gid="frozen-sam-vit-b-container")
    module(ax, 56.7, 24.2, 25.2, 16.6, "Image encoder", "1 pass per image",
           "image-encoder")
    module(ax, 56.7, 64.2, 25.2, 16.6, "Prompt encoder", "Initial + 4 shifts",
           "prompt-encoder")
    image_embedding(ax, 89.0, 28.4)
    prompt_embeddings(ax, 89.0, 68.7)
    label(ax, 93.7, 41.0, "Image embedding", size=6.65, ha="center", color=SUB)
    label(ax, 93.7, 81.1, "Prompt embeddings", size=6.65, ha="center", color=SUB)
    round_box(ax, 98.5, 44.1, 17.5, 17.0, INK, edge=INK, gid="shared-mask-decoder")
    label(ax, 107.25, 49.8, "Mask", color=WHITE, weight="bold", size=8.35, ha="center")
    label(ax, 107.25, 55.2, "decoder", color=WHITE, weight="bold", size=8.35, ha="center")
    label(ax, 56.7, 86.3, "One shared image embedding", size=6.7, color=SUB)
    label(ax, 114.7, 86.3, "5 single-mask decodes", size=6.7, color=SUB, ha="right")

    arrow(ax, [(45.55, 32.5), (56.7, 32.5)], gid="scan-to-image-encoder")
    arrow(ax, [(47.5, 72.5), (56.7, 72.5)], gid="boxes-to-prompt-encoder")
    arrow(ax, [(81.9, 32.5), (89.0, 32.5)], gid="image-to-embedding")
    arrow(ax, [(81.9, 72.5), (89.0, 72.5)], gid="boxes-to-embeddings")
    arrow(ax, [(98.5, 32.5), (107.25, 32.5), (107.25, 44.1)],
          gid="image-embedding-to-decoder")
    arrow(ax, [(97.6, 72.5), (107.25, 72.5), (107.25, 61.1)],
          gid="prompt-embeddings-to-decoder")
    draw_line(ax, [(116, 52.6), (119.85, 52.6)], width=1.15)
    ax.add_patch(Circle((119.85, 52.6), 0.53, facecolor=INK, edgecolor="none", zorder=6))
    arrow(ax, [(119.85, 52.6), (119.85, 27.1), (122.5, 27.1)], color=BLUE,
          gid="decoder-to-method-a")
    arrow(ax, [(119.85, 52.6), (119.85, 68.3), (122.5, 68.3)], color=ORANGE,
          gid="decoder-to-method-b")


def outputs(ax, masks, crop):
    x0, y0, x1, y1 = crop
    actual = masks[:, y0:y1, x0:x1]
    aspect = (y1 - y0) / (x1 - x0)
    round_box(ax, 122.5, 13.6, 49.0, 27.0, A_PALE, edge="#B7D6E5",
              gid="method-a-review-card")
    round_box(ax, 122.5, 44.1, 49.0, 45.9, B_PALE, edge="#E5C7B8",
              gid="method-b-review-card")
    label(ax, 125.2, 18.55, "Method A", color=BLUE, weight="bold", size=8.4)
    label(ax, 141.05, 18.55, "Model confidence", weight="bold", size=7.45)
    picture(ax, silhouette(actual[0], BLUE_LIGHT), 125.2, 23.7, 12.55,
            12.55 * aspect, "initial-predicted-mask")
    label(ax, 131.475, 36.5, "Initial mask", size=6.55, ha="center")
    label(ax, 141.05, 25.8, "1 − predicted IoU", size=8.25, weight="bold", color=BLUE)
    round_box(ax, 140.6, 31.0, 28.35, 6.15, WHITE, edge="#BDD7E4", radius=0.86, lw=0.55)
    label(ax, 154.775, 34.1, "Flag if score ≥ cutoff A", size=6.6, ha="center", color=BLUE)

    label(ax, 125.2, 49.1, "Method B", color=ORANGE, weight="bold", size=8.4)
    label(ax, 141.05, 49.1, "Prompt disagreement", weight="bold", size=7.45)
    label(ax, 125.2, 54.15, "Four shifted masks", size=7.1, color=SUB)
    for i, direction in enumerate(("Left", "Right", "Up", "Down")):
        x = 125.2 + i * 11.15
        picture(ax, silhouette(actual[i + 1], ORANGE_LIGHT), x, 57.5, 9.6,
                9.6 * aspect, f"predicted-mask-{direction.lower()}")
        label(ax, x + 4.8, 67.2, direction, size=6.55, ha="center")
    label(ax, 125.2, 72.6, "1 − mean Dice", size=8.25, weight="bold", color=ORANGE)
    label(ax, 125.2, 77.1, "Initial mask vs four shifted masks", size=7.0)
    round_box(ax, 124.75, 81.0, 28.35, 6.2, WHITE, edge="#E0C2B3", radius=0.86, lw=0.55)
    label(ax, 138.925, 84.15, "Flag if score ≥ cutoff B", size=6.6, ha="center", color=ORANGE)


def verify_text_layout(fig):
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    entries = [(t, t.get_window_extent(renderer)) for axis in fig.axes for t in axis.texts]
    for text, bounds in entries:
        if text.get_fontsize() < 6 or not (
            bounds.x0 >= 0 and bounds.y0 >= 0
            and bounds.x1 <= fig.bbox.width and bounds.y1 <= fig.bbox.height
        ):
            raise ValueError(f"Text is too small or outside the canvas: {text.get_text()}")
    for (one, first), (two, second) in combinations(entries, 2):
        overlap_x = min(first.x1, second.x1) - max(first.x0, second.x0)
        overlap_y = min(first.y1, second.y1) - max(first.y0, second.y0)
        if min(overlap_x, overlap_y) > 0.65:
            raise ValueError(f"Overlapping labels: {one.get_text()} | {two.get_text()}")
    print(f"Measured {len(entries)} non-overlapping labels at {W:g} mm width.")


def main():
    case_path = WORK / "example_case.npz"
    record = json.loads((WORK / "example_case.json").read_text(encoding="utf-8"))
    assert sha256(case_path.read_bytes()).hexdigest() == record["artifact_sha256"]
    assert record["case"] == "case001" and record["archived_values_match"]
    with np.load(case_path, allow_pickle=False) as data:
        image, reference, masks, boxes = (data[k] for k in ("image", "reference", "masks", "boxes"))
    crop = (97, 0, 485, 282)
    x0, y0, x1, y1 = crop
    foreground = reference | np.any(masks, axis=0)
    assert int(foreground.sum()) == int(foreground[y0:y1, x0:x1].sum())
    assert (boxes[:, 0] >= x0).all() and (boxes[:, 1] >= y0).all()
    assert (boxes[:, 2] <= x1).all() and (boxes[:, 3] <= y1).all()

    fig = plt.figure(figsize=(W / 25.4, H / 25.4), dpi=600, facecolor=WHITE)
    panel_axes = [
        make_panel(fig, 3.5, 47.5, "A", "Image and prompts"),
        make_panel(fig, 52.5, 117.5, "B", "Frozen SAM ViT-B"),
        make_panel(fig, 122.5, 171.5, "C", "Review scores"),
    ]
    canvas = fig.add_axes([0, 0, 1, 1], label="diagram", zorder=2)
    canvas.patch.set_visible(False)
    canvas.set_xlim(0, W)
    canvas.set_ylim(H, 0)
    canvas.set_autoscale_on(False)
    canvas.axis("off")

    inputs(canvas, image, reference, boxes, crop)
    model(canvas)
    outputs(canvas, masks, crop)
    round_box(canvas, 3.5, 93.2, 168, 6.55, "#F1F5F7", edge="none",
              radius=0.86, gid="evaluation-reference-band")
    label(canvas, 5.7, 96.45, "Evaluation reference", size=7.25, weight="bold")
    label(canvas, 36.1, 96.45,
          "Dice between the initial mask and manual contour < 0.70 defines low quality.", size=7.25)
    label(canvas, 3.5, 104.35,
          "Pawłowska et al. (2024)  ·  BrEaST v1 case 001  ·  doi 10.7937/9WKK-Q141  ·  CC BY 4.0  ·  Display crop", size=6.45, color=SUB)

    verify_text_layout(fig)
    require_matplotlib_panel_alignment(
        fig, axes=panel_axes, panel_ids=["A", "B", "C"],
        row_groups=[{"id": "diagram-stages", "panels": ["A", "B", "C"]}],
        exemptions=[{"panels": ["A", "B", "C"], "checks": ["panel-width"],
                     "reason": "The shared SAM model uses a wider center column than the image and score panels."}],
        json_out=str(PREFIX) + ".alignment.json",
        tolerance_pt=1.5, gutter_tolerance_pt=1.5, strict=True,
    )
    title = "Prompted segmentation and review scores in breast ultrasound"
    desc = ("Illustration from the locked BrEaST case 001, selected by case number. "
            "The same SAM ViT-B image embedding is used for five box prompts. "
            "The initial predicted IoU and four-mask consistency define the two review scores. "
            "An identical crop is used in each image and mask tile. "
            "Source image and reference mask: Pawłowska et al. (2024), BrEaST v1, https://doi.org/10.7937/9WKK-Q141, "
            "CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/).")
    fig.savefig(str(PREFIX) + ".png", dpi=600, metadata={"Title": title, "Description": desc})
    svg_path = PREFIX.with_suffix(".svg")
    fig.savefig(svg_path, dpi=600, metadata={"Title": title, "Description": desc})
    svg, count = re.subn(r"<!DOCTYPE svg PUBLIC[^>]*>\s*", "", svg_path.read_text(encoding="utf-8"), count=1)
    assert count == 1, "Expected only the renderer SVG declaration"
    svg, font_count = re.subn(
        r'<text(?=[^>]*\bfont: [^";]*?\b([\d.]+)px\b)', r'<text font-size="\1"', svg
    )
    assert font_count == 44, "Every live label must declare its size"
    svg = re.sub(r' transform="rotate\(-0 [^"]+\)"', "", svg)
    svg_path.write_text(svg, encoding="utf-8")
    fig.savefig(str(PREFIX) + ".pdf", dpi=600, metadata={"Title": title, "Subject": desc})
    plt.close(fig)
    print("Exported PNG, SVG and PDF.")


if __name__ == "__main__":
    main()
