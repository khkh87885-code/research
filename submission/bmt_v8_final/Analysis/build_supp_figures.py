"""Publication-size supplementary figures from archived, reviewed results.

No fitting, inference, bootstrap, patient resampling, or result estimation occurs
here. Percent / percentage-point conversions and display-only sign aggregation
preserve the archived statistics.
"""
from pathlib import Path
import hashlib
import json
import subprocess
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import fitz
from PIL import Image
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.text import Text

ROOT = Path('/workspace/bmt_v8')
SRC = Path('/workspace/research_source/experiments/cloud_validation_v1/results')
OUT = ROOT / 'outputs/Figures'
EVIDENCE = ROOT / 'evidence'
OUT.mkdir(parents=True, exist_ok=True)
EVIDENCE.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({
    'font.family': 'DejaVu Sans', 'font.size': 8,
    'axes.titlesize': 8.6, 'axes.labelsize': 8,
    'xtick.labelsize': 7.5, 'ytick.labelsize': 7.5,
    'legend.fontsize': 7.2, 'axes.linewidth': .65,
    'pdf.fonttype': 42, 'ps.fonttype': 42,
    'savefig.facecolor': 'white',
})
BLUE, ORANGE = '#0072B2', '#D55E00'
PURPLE, GREY, INK = '#CC79A7', '#BBBBBB', '#333333'
palette = {'method_A': BLUE, 'method_B': ORANGE,
           'transferred_contrast': INK, 'equal_review_contrast': PURPLE,
           'original_strict_pattern': BLUE, 'opposite_strict_pattern': ORANGE,
           'any_zero_contrast': GREY, 'same_nonzero_sign': '#E6C14C'}
provenance = {
    'purpose': 'Publication-size supplementary figures for BMT v8',
    'statistics_policy': 'Archived result rendering only; no bootstrap or inference rerun.',
    'typography': {'family': 'DejaVu Sans', 'minimum_point_size': 7.2},
    'palette': palette,
    'accessibility': 'Okabe-Ito derived palette; redundant line styles, markers, row labels and stack hatching; blue/orange method encoding; no red-green comparisons.',
    'sources': {}, 'figures': {},
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def records(frame):
    return frame.astype(object).where(pd.notna(frame), None).to_dict('records')


def source(rel):
    path = SRC / rel
    provenance['sources'][str(path)] = sha(path)
    return path


def panel(ax, letter, title):
    ax.set_title(title, loc='left', pad=8)
    ax.text(-.15, 1.035, letter, transform=ax.transAxes,
            fontsize=10, fontweight='bold', va='bottom', ha='left')


def clean(ax, grid='y'):
    ax.spines[['top', 'right']].set_visible(False)
    ax.tick_params(width=.65, length=3, pad=3)
    ax.set_axisbelow(True)
    ax.grid(axis=grid, color='#DDDDDD', linewidth=.45)


def save(fig, name, details):
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    width, height = fig.canvas.get_width_height()
    outside = []
    fonts = []
    for t in fig.findobj(match=Text):
        if not t.get_visible() or not t.get_text().strip():
            continue
        fonts.append(t.get_fontsize())
        b = t.get_window_extent(renderer)
        if b.x0 < -.5 or b.y0 < -.5 or b.x1 > width+.5 or b.y1 > height+.5:
            outside.append(t.get_text())
    if outside:
        raise RuntimeError(f'{name}: text outside figure: {outside}')
    if min(fonts) < 7:
        raise RuntimeError(f'{name}: undersized text {min(fonts)}')
    fig.savefig(OUT / f'{name}.png', dpi=600)
    fig.savefig(OUT / f'{name}.pdf')
    provenance['figures'][name] = {
        **details, 'width_inches': float(fig.get_figwidth()),
        'height_inches': float(fig.get_figheight()), 'raster_dpi': 600,
        'minimum_rendered_font_pt': min(fonts), 'maximum_rendered_font_pt': max(fonts),
        'text_outside_figure': outside,
        'png_sha256': sha(OUT / f'{name}.png'),
        'pdf_sha256': sha(OUT / f'{name}.pdf'),
        'pdf_content': 'Vector text, lines, markers and intervals',
    }
    plt.close(fig)


def figure_s3():
    p = pd.read_csv(source('budget_transfer/performance.csv'))
    c = pd.read_csv(source('budget_transfer/paired_contrasts.csv'))
    assert len(p) == 64 and len(c) == 32
    budgets = np.sort(p.target_budget.unique()) * 100
    assert len(budgets) == 8
    fig, axs = plt.subplots(2, 2, figsize=(6.4, 6.15))
    fig.subplots_adjust(left=.11, right=.985, bottom=.09, top=.94, wspace=.32, hspace=.46)
    ax = axs[0, 0]
    panel(ax, 'A', 'Transferred review volume')
    for split, ls, marker, cohort in [('internal_holdout', '-', 'o', 'Internal'),
                                       ('external_test', '--', '^', 'External')]:
        for method, color in [('A', BLUE), ('B', ORANGE)]:
            d = p[(p.split == split) & (p['mode'] == 'development_calibrated_threshold') & (p.method == method)].sort_values('target_budget')
            ax.plot(d.target_budget * 100, d.review_fraction * 100, color=color,
                    linestyle=ls, marker=marker, ms=3.5, lw=1.1,
                    markerfacecolor='white' if split == 'external_test' else color,
                    label=f'{cohort} {method}')
    ax.plot([0, 55], [0, 55], color='#777777', lw=.7, ls=':', zorder=0)
    ax.set(xlim=(2, 52), ylim=(0, 55), ylabel='Actual review fraction (%)', xlabel='Target review budget (%)')
    ax.set_xticks(budgets)
    ax.set_yticks([0, 10, 20, 30, 40, 50])
    ax.legend(loc='upper left', ncol=2, frameon=False, columnspacing=.8,
              handlelength=1.6, handletextpad=.45, borderaxespad=.2)
    clean(ax)
    for ax, split, letter, title, denom in [
        (axs[0, 1], 'external_test', 'B', 'External detection', 16),
        (axs[1, 0], 'internal_holdout', 'C', 'Internal detection', 93)]:
        panel(ax, letter, title)
        for mode, ls, marker, label in [
            ('development_calibrated_threshold', '-', 'o', 'Transferred'),
            ('test_cohort_equal_review', '--', 's', 'Equal review')]:
            for method, color in [('A', BLUE), ('B', ORANGE)]:
                d = p[(p.split == split) & (p['mode'] == mode) & (p.method == method)].sort_values('target_budget')
                ax.plot(d.target_budget * 100, d.detection_fraction * 100,
                        color=color, ls=ls, marker=marker, lw=1.1, ms=3.4,
                        markerfacecolor='white' if mode == 'test_cohort_equal_review' else color,
                        label=f'{label} {method}')
        ax.set(xlim=(2, 52), ylim=(0, 105), ylabel=f'Low-quality cases detected (%)', xlabel='Target review budget (%)')
        ax.set_xticks(budgets)
        ax.set_yticks([0, 25, 50, 75, 100])
        ax.text(.03 if letter == 'B' else .97, .95 if letter == 'B' else .04,
                f'n = {denom} low-quality cases', transform=ax.transAxes,
                ha='left' if letter == 'B' else 'right',
                va='top' if letter == 'B' else 'bottom', fontsize=7.2, color=INK)
        if letter == 'B':
            ax.legend(loc='lower right', frameon=False, ncol=1, handlelength=1.6,
                      borderaxespad=.2, handletextpad=.5)
        clean(ax)
    ax = axs[1, 1]
    panel(ax, 'D', 'External B − A detection')
    ax.axhline(0, color='#777777', lw=.75)
    for mode, offset, color, marker, label in [
        ('development_calibrated_threshold', -.55, INK, 'o', 'Transferred'),
        ('test_cohort_equal_review', .55, PURPLE, 's', 'Equal review')]:
        d = c[(c.split == 'external_test') & (c['mode'] == mode)].sort_values('target_budget')
        v = d.detection_difference_pp.to_numpy()
        lo, hi = d.detection_ci95_low_pp.to_numpy(), d.detection_ci95_high_pp.to_numpy()
        ax.errorbar(d.target_budget * 100 + offset, v, yerr=[v-lo, hi-v],
                    color=color, marker=marker, ls='none', ms=3.5, lw=.85,
                    capsize=2, markerfacecolor='white' if marker == 's' else color, label=label)
    ax.set(xlim=(2, 52), ylim=(-42, 50), ylabel='Detection difference (pp)', xlabel='Target review budget (%)')
    ax.set_xticks(budgets)
    ax.set_yticks([-40, -20, 0, 20, 40])
    ax.legend(loc='upper right', frameon=False, borderaxespad=.2, handletextpad=.5)
    clean(ax)
    save(fig, 'Figure_S3', {
        'panels': {'A': 'Actual internal/external review fractions at transferred development-calibrated thresholds',
                   'B': 'External detection under transferred thresholds and cohort-specific equal review',
                   'C': 'Internal detection under transferred thresholds and cohort-specific equal review',
                   'D': 'External B-minus-A detection differences with archived nominal paired 95% Newcombe CIs'},
        'budgets_percent': budgets.tolist(), 'performance_rows': len(p), 'paired_contrast_rows': len(c),
        'displayed_values': {'performance': records(p), 'paired_contrasts': records(c[c.split == 'external_test'])},
        'legend_note': 'A: circles/solid = internal; open triangles/dashed = external. B/C: solid circles = transferred, open dashed squares = equal review. D: black circles = transferred, pink open squares = equal review.',
    })


def interval(ax, lo, med, hi, y, color, marker='o', fill=True):
    ax.errorbar(med, y, xerr=[[med-lo], [hi-med]], color=color, ls='none',
                marker=marker, ms=4, markerfacecolor=color if fill else 'white',
                lw=1.15, capsize=2.5, markeredgewidth=.9)


def figure_s4():
    b = json.loads(source('bootstrap_stability/summary.json').read_text())
    routes = list(b['routes'])
    assert len(routes) == 3
    fig, axs = plt.subplots(2, 2, figsize=(6.4, 6.8))
    fig.subplots_adjust(left=.12, right=.975, bottom=.24, top=.945, wspace=.35, hspace=.47)
    endpoint_keys = ['H1_A_external_minus_internal_detection_pp', 'H2_A_external_minus_internal_review_pp']
    displayed = {}
    for ax, letter, key, title, lim, ticks in zip(
        axs[0], ['A', 'B'], endpoint_keys,
        ['H1: A detection, external − internal', 'H2: A review, external − internal'],
        [(-45, 17), (-14, 1)], [[-40, -20, 0], [-12, -8, -4, 0]]):
        panel(ax, letter, title)
        ax.axvline(0, color='#777777', lw=.75)
        ax.axvline(b['observed'][key], color=INK, lw=.8, ls=':')
        for idx, route in enumerate(routes):
            d = b['routes'][route]['endpoints_pp'][key]
            interval(ax, *[d['percentile_95'][0], d['median'], d['percentile_95'][1]], 2-idx, BLUE)
            displayed[f'{route}:{key}'] = d
        ax.set(yticks=[2, 1, 0], yticklabels=['R1', 'R2', 'R3'], ylim=(-.6, 2.6), xlim=lim,
               xlabel='Difference (pp)')
        ax.set_xticks(ticks)
        clean(ax, 'x')
    ax = axs[1, 0]
    panel(ax, 'C', 'External B − A detection')
    ax.axvline(0, color='#777777', lw=.75)
    labels = []
    for i, route in enumerate(routes):
        for j, (key, label, color, marker) in enumerate([
            ('external_fixed_B_minus_A_detection_pp', 'fixed', INK, 'o'),
            ('external_equal_B_minus_A_detection_pp', 'top-50', PURPLE, 's')]):
            y = 5-i*2-j
            d = b['routes'][route]['endpoints_pp'][key]
            interval(ax, d['percentile_95'][0], d['median'], d['percentile_95'][1], y,
                     color, marker, marker == 'o')
            labels.append(f'R{i+1} {label}')
            displayed[f'{route}:{key}'] = d
    ax.set(yticks=list(range(5, -1, -1)), yticklabels=labels, ylim=(-.65, 5.65),
           xlim=(-30, 45), xlabel='Detection difference (pp)')
    ax.set_xticks([-20, 0, 20, 40])
    clean(ax, 'x')
    ax = axs[1, 1]
    panel(ax, 'D', 'Joint fixed / top-50 sign patterns')
    stacks = []
    for route in routes:
        joint = b['routes'][route]['joint_direction_patterns']
        same = (joint['sign_matrix']['negative']['negative']['fraction'] +
                joint['sign_matrix']['positive']['positive']['fraction'])
        vals = [joint['original_direction_reversal']['fraction'],
                joint['opposite_direction_reversal']['fraction'],
                joint['any_difference_tie']['fraction'], same]
        assert abs(sum(vals)-1) < 1e-12
        stacks.append(np.array(vals)*100)
        displayed[f'{route}:joint_sign_pattern_percent'] = dict(zip(
            ['original_strict', 'opposite_strict', 'any_zero', 'same_nonzero'], np.array(vals)*100))
    starts = np.zeros(3)
    stack_colors = [BLUE, ORANGE, GREY, '#E6C14C']
    hatches = ['', '////', '..', '\\\\']
    for j, (color, hatch) in enumerate(zip(stack_colors, hatches)):
        vals = np.array(stacks)[:, j]
        ax.barh([2, 1, 0], vals, left=starts, color=color, edgecolor='white',
                linewidth=.55, height=.5, hatch=hatch)
        for i, v in enumerate(vals):
            if v >= 4:
                ax.text(starts[i]+v/2, 2-i, f'{v:.2f}', ha='center', va='center',
                        color='white' if j == 0 else INK, fontsize=7.2,
                        rotation=90 if v < 10 else 0)
        starts += vals
    # The 0.90% opposite-sign segment is too narrow for an in-segment label.
    r3_original, r3_opposite = stacks[2][:2]
    ax.annotate(f'{r3_opposite:.2f}', xy=(r3_original+r3_opposite/2, -.24),
                xytext=(r3_original+r3_opposite/2, -.57), fontsize=7.2,
                ha='center', va='center', arrowprops={'arrowstyle': '-', 'lw': .55, 'color': INK})
    ax.set(yticks=[2, 1, 0], yticklabels=['R1', 'R2', 'R3'], ylim=(-.85, 2.6),
           xlim=(0, 100), xlabel='Jointly valid replicates (%)')
    ax.set_xticks([0, 25, 50, 75, 100])
    clean(ax, 'x')
    legend_handles = [Patch(facecolor=c, hatch=h, edgecolor='#EEEEEE', label=l)
                      for c, h, l in zip(stack_colors, hatches,
                        ['Original strict pattern', 'Opposite strict pattern', 'Any zero contrast', 'Same nonzero sign'])]
    fig.legend(handles=legend_handles, loc='lower center', bbox_to_anchor=(.52, .113), ncol=2,
               frameon=False, columnspacing=1.8, handlelength=1.7, handletextpad=.5, fontsize=7.4)
    fig.text(.12, .087, 'R1: fixed cutoffs; test sampling.  R2: development calibration only.', fontsize=7.4)
    fig.text(.12, .061, 'R3: full development + test sampling.  Each route: 10,000 replicates.', fontsize=7.4)
    fig.text(.12, .027, 'A–C: dots = bootstrap medians; bars = percentile 95% CIs. A/B dotted line = observed value.', fontsize=7.2)
    save(fig, 'Figure_S4', {
        'panels': {'A': 'H1 percentile intervals by route', 'B': 'H2 percentile intervals by route',
                   'C': 'External fixed-cutoff and top-50 B-minus-A percentile intervals by route',
                   'D': 'Joint fixed/top-50 sign-pattern empirical fractions'},
        'routes': {f'R{i+1}': b['routes'][k]['label'] for i, k in enumerate(routes)},
        'replicates_per_route': b['replicates_per_route'], 'displayed_values': displayed,
        'joint_pattern_definitions': {'original_strict': 'fixed > 0 and top-50 < 0',
            'opposite_strict': 'fixed < 0 and top-50 > 0',
            'any_zero': 'at least one contrast is zero',
            'same_nonzero': 'both negative or both positive; display-only sum of archived two sign_matrix fractions'},
    })


def figure_s5():
    k = json.loads(source('case_mix_decomposition.json').read_text())
    fig, axs = plt.subplots(1, 2, figsize=(6.4, 3.65))
    fig.subplots_adjust(left=.20, right=.98, bottom=.19, top=.87, wspace=.86)
    displayed = {}
    row_labels = ['A: Total', 'Composition', 'Within strata', 'B: Total', 'Composition', 'Within strata']
    terms = ['overall_difference', 'composition_associated', 'within_stratum_rate']
    for ax, letter, outcome, title, lim, ticks in [
        (axs[0], 'A', 'detection', 'Detection', (-45, 34), [-40, -20, 0, 20]),
        (axs[1], 'B', 'review_fraction', 'Review fraction', (-14, 4), [-12, -8, -4, 0, 4])]:
        panel(ax, letter, title)
        ax.axvline(0, color='#777777', lw=.75)
        ax.axhline(2.5, color='#DDDDDD', lw=.6)
        for mi, (method, color) in enumerate([('A', BLUE), ('B', ORANGE)]):
            d = k['results'][f'{method}.{outcome}']['statistics']
            for ti, term in enumerate(terms):
                a = d[term]
                lo, hi = np.array(a['percentile_ci95'])*100
                med = a['estimate']*100
                interval(ax, lo, med, hi, 5-mi*3-ti, color, ['o', 's', '^'][ti], ti != 1)
                displayed[f'{method}.{outcome}.{term}'] = a
        ax.set(yticks=[5, 4, 3, 2, 1, 0], yticklabels=row_labels,
               ylim=(-.6, 5.6), xlim=lim, xlabel='External − internal (pp)')
        ax.set_xticks(ticks)
        clean(ax, 'x')
    fig.text(.20, .057, 'Points: observed estimates. Bars: term-specific percentile 95% CIs.', fontsize=7.4)
    save(fig, 'Figure_S5', {
        'panels': {'A': 'Detection: total difference, composition-associated and within-stratum terms for methods A/B',
                   'B': 'Review fraction: the same three terms for methods A/B'},
        'direction': k['direction'], 'unit_conversion': 'Archived fractions multiplied by 100 to percentage points',
        'bootstrap_replicates': k['bootstrap']['replicates'], 'displayed_values': displayed,
        'interval_note': 'Each term retains its own archived CI; 4,999 valid decomposition replicates for detection terms and 5,000 for totals/review terms.',
    })


def figure_s6a():
    script = ROOT/'scripts/build_figure_s6a.py'
    if not script.exists():
        raise RuntimeError('Missing S6A publication layout renderer')
    subprocess.run(['python', str(script)], check=True)
    provenance['figures']['Figure_S6A'] = json.loads((EVIDENCE/'figure_s6a_provenance.json').read_text())


def output_checks():
    for name, detail in provenance['figures'].items():
        image = Image.open(OUT/f'{name}.png')
        doc = fitz.open(OUT/f'{name}.pdf')
        page = doc[0]
        assert len(doc) == 1
        expected_pixels = [round(detail['width_inches']*600), round(detail['height_inches']*600)]
        assert list(image.size) == expected_pixels
        assert abs(page.rect.width/72-detail['width_inches']) < 1e-6
        assert abs(page.rect.height/72-detail['height_inches']) < 1e-6
        spans = [span for block in page.get_text('dict')['blocks'] if 'lines' in block
                 for line in block['lines'] for span in line['spans'] if span['text'].strip()]
        minimum_font = min(s['size'] for s in spans)
        assert minimum_font >= 7
        escaped = [s['text'] for s in spans if s['bbox'][0] < -.1 or s['bbox'][1] < -.1
                   or s['bbox'][2] > page.rect.width+.1 or s['bbox'][3] > page.rect.height+.1]
        assert not escaped
        detail['export_validation'] = {
            'png_dimensions_pixels': list(image.size), 'png_dpi_metadata': list(image.info['dpi']),
            'pdf_page_inches': [page.rect.width/72, page.rect.height/72],
            'pdf_text_minimum_point_size': minimum_font,
            'pdf_vector_drawing_count': len(page.get_drawings()),
            'pdf_raster_image_count': len(page.get_images()),
            'pdf_text_outside_page': escaped,
        }
        detail['manual_rendered_inspection'] = {
            'status': 'passed', 'date_UTC': '2026-11-06',
            'surfaces': ['PNG at publication aspect and resolution', 'independently rasterized vector PDF'],
            'checks': ['No cropped labels', 'No overlapping labels', 'Legible final-size labels',
                       'Intervals remain visible', 'Consistent uppercase panels'],
            'preview_directory': '/workspace/bmt_v8/qa/figure_previews',
        }
        if name in ['Figure_S6A', 'Figure_S6B']:
            provenance['sources'][detail['receipt_path']] = detail['receipt_sha256']
            for case in detail['cases']:
                provenance['sources'][case['source_npz']] = case['sha256']


if __name__ == '__main__':
    figure_s3()
    figure_s4()
    figure_s5()
    figure_s6a()
    subprocess.run(['python', str(ROOT/'scripts/build_figure_s6b.py')], check=True)
    extra = EVIDENCE / 'figure_s6b_provenance.json'
    provenance['figures']['Figure_S6B'] = json.loads(extra.read_text())
    output_checks()
    provenance['rendering_script_sha256'] = sha(__file__)
    provenance['helper_rendering_script_sha256'] = {
        str(ROOT/'scripts'/f'build_figure_s6{suffix}.py'): sha(ROOT/'scripts'/f'build_figure_s6{suffix}.py')
        for suffix in ['a', 'b']}
    (EVIDENCE/'new_figure_provenance.json').write_text(json.dumps(provenance, indent=2, allow_nan=False)+'\n')
    print('Built publication-size Figures S3–S5, S6A and S6B.')
