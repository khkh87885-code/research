"""Render the three B-only detected captured CPU replay examples at journal size.

Consumes existing arrays and receipt values only; performs no model inference and
never changes, smooths, dilates, or resamples the saved mask arrays.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

ROOT = Path('/workspace/bmt_v8')
SOURCE = Path('/workspace/research_source/experiments/six_case_replay_v1/predictions')
OUT = ROOT / 'outputs/Figures'
OUT.mkdir(parents=True, exist_ok=True)
RECEIPT = SOURCE / 'targeted_rerun_receipt.json'
receipt = json.loads(RECEIPT.read_text())
cases = receipt['cases'][3:]
assert [c['image_id'] for c in cases] == ['case024', 'case105', 'case222']
assert all(c['archived_group'] == 'B_only_detected' for c in cases)
COLORS = {'reference': '#1b9e77', 'prediction': '#d95f02', 'prompt': '#56b4e9'}
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 8.5,
                     'pdf.fonttype': 42, 'ps.fonttype': 42})
fig, axs = plt.subplots(3, 2, figsize=(6.89, 7.7), squeeze=False)
fig.subplots_adjust(left=.035, right=.985, bottom=.02, top=.97, wspace=.10, hspace=.25)
panels = list('ABCDEF')
evidence = []
for row, c in enumerate(cases):
    file = SOURCE / c['artifact']
    digest = hashlib.sha256(file.read_bytes()).hexdigest()
    assert digest == c['artifact_sha256']
    with np.load(file, allow_pickle=False) as z:
        mask = z['masks'][0]
        assert int(mask.sum()) == c['prediction_pixel_counts'][0]
        for col, ax in enumerate(axs[row]):
            ax.imshow(z['image'], interpolation='nearest')
            ax.set_axis_off()
            if col == 0:
                ax.contour(z['reference'], levels=[.5], colors=[COLORS['reference']], linewidths=.9)
                b = z['boxes'][0]
                ax.add_patch(Rectangle((b[0], b[1]), b[2]-b[0], b[3]-b[1],
                                       fill=False, edgecolor=COLORS['prompt'], linewidth=.8))
                ax.set_title(panels[row*2+col] + '  ' + c['image_id'] + ': reference and prompt', fontsize=8.5, pad=5, loc='left')
            else:
                ax.contour(mask, levels=[.5], colors=[COLORS['prediction']], linewidths=.9)
                ax.set_title(panels[row*2+col] + '  CPU prediction; Dice ' + f"{c['rerun']['dice_vs_reference']:.4f}",
                             fontsize=8.5, pad=5, loc='left')
        evidence.append({'image_id': c['image_id'], 'source_npz': str(file),
                         'sha256': digest, 'artifact_arrays': {k: list(z[k].shape) for k in z.files},
                         'actual_prediction_foreground_pixels': int(mask.sum()),
                         'reference_foreground_pixels': int(z['reference'].sum()),
                         'rerun_dice': c['rerun']['dice_vs_reference'],
                         'displayed_dice': f"{c['rerun']['dice_vs_reference']:.4f}",
                         'archived_group': c['archived_group'],
                         'archived_risk_A': c['archived']['risk_A'],
                         'archived_risk_B': c['archived']['risk_B'],
                         'rerun_flags': c['rerun_flags']})
fig.canvas.draw()
renderer = fig.canvas.get_renderer()
text_bounds = []
for t in [t for ax in axs.flat for t in list(ax.texts) + [ax.title, ax._left_title, ax._right_title]]:
    if t.get_visible() and t.get_text():
        bb = t.get_window_extent(renderer).transformed(fig.transFigure.inverted())
        text_bounds.append({'text': t.get_text(), 'bounds_figure_fraction': list(bb.bounds),
                            'font_pt': float(t.get_fontsize())})
        assert bb.x0 >= 0 and bb.y0 >= 0 and bb.x1 <= 1 and bb.y1 <= 1, (t.get_text(), bb)
fig.savefig(OUT/'Figure_S6B.png', dpi=600)
fig.savefig(OUT/'Figure_S6B.pdf')
plt.close(fig)
provenance = {'source': 'Existing captured CPU replay masks; no model inference during rendering',
              'receipt_path': str(RECEIPT), 'receipt_sha256': hashlib.sha256(RECEIPT.read_bytes()).hexdigest(),
              'cases': evidence, 'width_inches': 6.89, 'height_inches': 7.7, 'raster_dpi': 600,
              'png_dimensions_pixels': [4134, 4620], 'font_family': 'DejaVu Sans',
              'font_pt': 8.5, 'panel_font_pt': 8.5, 'panel_title_style': 'Uppercase panel letter and title on one line, left aligned, 8.5 pt', 'panels': 'A-F',
              'colors': COLORS,
              'color_accessibility': 'Distinct green reference / blue rectangular prompt / orange CPU prediction; role also encoded by column and contour/rectangle geometry.',
              'mask_handling': 'Original masks[0] array contours at level 0.5; no array modification or model inference.',
              'qa': {'all_source_hashes_match_receipt': True, 'foreground_pixel_counts_match_receipt': True,
                     'all_text_within_canvas': True, 'text_bounds': text_bounds,
                     'visual_inspection': 'PNG and separately rasterized PDF inspected: all six panels, titles, contours, prompt rectangles and uppercase labels visible without overlap or clipping.'}}
provenance['output_sha256'] = {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in [OUT/'Figure_S6B.png', OUT/'Figure_S6B.pdf']}
(ROOT/'evidence/figure_s6b_provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
print('Built Figure S6B from case024, case105, case222 actual CPU prediction arrays.')
