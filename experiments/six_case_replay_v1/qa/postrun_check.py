#!/usr/bin/env python3
"""Independently validate saved predictions; no torch/SAM inference."""
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess

import fitz
import numpy as np
from PIL import Image, __version__ as pillow_version

ROOT = Path('/workspace/bmt_six_case_replay')
SOURCE = Path('/workspace/research_source')
PRED = ROOT / 'predictions'
QA = ROOT / 'qa'
FIELDS = ('dice_vs_reference', 'sam_predicted_iou', 'risk_A', 'risk_B',
          'dice_shift_left', 'dice_shift_right', 'dice_shift_up', 'dice_shift_down')
DIRECTIONS = ('left', 'right', 'up', 'down')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def read_csv(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def independent_dice(first, second):
    # Count bool membership, independently from the runner's sum-based helper.
    denominator = int(np.count_nonzero(first)) + int(np.count_nonzero(second))
    return 2 * int(np.count_nonzero(np.logical_and(first, second))) / denominator if denominator else 1.0


receipt_path = PRED / 'targeted_rerun_receipt.json'
receipt = json.loads(receipt_path.read_text())
protocol = json.loads((ROOT / 'replay_protocol.json').read_text())
preflight = json.loads((QA / 'preflight_review.json').read_text())
lock = json.loads((SOURCE / 'reproducibility/study_lock.json').read_text())
assert receipt['status'] == 'complete'
assert len(receipt['cases']) == 6
expected_ids = set(protocol['six_cases'])
assert {r['image_id'] for r in receipt['cases']} == expected_ids
assert {p.stem.replace('_targeted_rerun', '') for p in PRED.glob('*.npz')} == expected_ids
records = {r['image_id']: r for r in read_csv(SOURCE / 'reproducibility/records/validation_cases.csv') if r['split'] == 'external_test'}
manifest = {r['image_id']: r for r in read_csv(SOURCE / 'reproducibility/manifests/breast_external.csv')}
preflight_cases = {r['image_id']: r for r in preflight['cases']}
thresholds = {m: lock['threshold_lock']['methods'][m]['threshold'] for m in ('A', 'B')}

unchanged = []
for relative, expected_hash in lock['files_sha256'].items():
    actual = sha(SOURCE / 'reproducibility' / relative)
    assert actual == expected_hash, relative
    unchanged.append({'path': str(SOURCE / 'reproducibility' / relative), 'sha256': actual, 'unchanged': True})
for path, expected_hash in preflight['source_files'].items():
    assert sha(path) == expected_hash, path
assert sha(ROOT / 'scripts/external_case_audit.py') == protocol['script_sha256']
assert protocol['script_sha256'] == sha(SOURCE / protocol['script_source_path'])
research_status = subprocess.check_output(['git', '-C', str(SOURCE), 'status', '--porcelain'], text=True).strip()
assert not research_status
sam_path = Path('/workspace/bmt_v7/resources/segment-anything')
sam_commit = subprocess.check_output(['git', '-C', str(sam_path), 'rev-parse', 'HEAD'], text=True).strip()
sam_status = subprocess.check_output(['git', '-C', str(sam_path), 'status', '--porcelain'], text=True).strip()
assert sam_commit == lock['threshold_lock']['model']['source_commit'] == receipt['sam_source_commit']
assert not sam_status
checkpoint_hash = sha(ROOT / 'resources/sam_vit_b_01ec64.pth')
assert checkpoint_hash == receipt['checkpoint_sha256'] == lock['threshold_lock']['model']['weight_sha256']

case_reviews = []
all_comparisons = []
for entry in receipt['cases']:
    case = entry['image_id']
    archived = records[case]
    m = manifest[case]
    artifact = PRED / entry['artifact']
    artifact_hash = sha(artifact)
    assert artifact_hash == entry['artifact_sha256']
    with np.load(artifact, allow_pickle=False) as z:
        assert set(z.files) == {'image', 'reference', 'masks', 'boxes', 'raw_predicted_ious'}
        arrays = {k: z[k] for k in z.files}
    image, ref, masks, boxes, scores = [arrays[k] for k in ('image', 'reference', 'masks', 'boxes', 'raw_predicted_ious')]
    h, w = int(m['height']), int(m['width'])
    assert image.dtype == np.uint8 and image.shape == (h, w, 3)
    assert ref.dtype == bool and ref.shape == (h, w)
    assert masks.dtype == bool and masks.shape == (5, h, w)
    assert boxes.dtype == np.float32 and boxes.shape == (5, 4)
    assert scores.shape == (5,) and np.isfinite(scores).all()
    assert np.array_equal(scores.astype(np.float32).astype(scores.dtype), scores)
    assert hashlib.sha256(image.tobytes()).hexdigest() == preflight_cases[case]['input_rgb_array_sha256']
    assert hashlib.sha256(ref.tobytes()).hexdigest() == preflight_cases[case]['input_reference_array_sha256']
    assert hashlib.sha256(boxes.tobytes()).hexdigest() == preflight_cases[case]['boxes_sha256']
    assert int(np.count_nonzero(ref)) == preflight_cases[case]['reference_foreground_pixels']
    consistency = [independent_dice(masks[0], mask) for mask in masks[1:]]
    values = {'dice_vs_reference': independent_dice(masks[0], ref), 'sam_predicted_iou': float(scores[0]),
              'risk_A': 1.0 - float(scores[0]), 'risk_B': 1.0 - sum(consistency) / 4,
              **{'dice_shift_' + direction: v for direction, v in zip(DIRECTIONS, consistency)}}
    assert np.isfinite(list(values.values())).all()
    comparison = {}
    for field in FIELDS:
        value = values[field]
        original = float(archived[field])
        delta = value - original
        assert entry['rerun'][field] == value
        assert entry['archived'][field] == original
        assert entry['comparison'][field]['archived'] == original
        assert entry['comparison'][field]['rerun'] == value
        assert entry['comparison'][field]['difference'] == delta
        assert entry['comparison'][field]['exact_match'] == (value == original)
        comparison[field] = {'archived': original, 'independently_recomputed_rerun': value,
                             'difference': delta, 'absolute_difference': abs(delta), 'exact_match': value == original}
        all_comparisons.append({'image_id': case, 'field': field, **comparison[field]})
    flags = {'alert_' + method: int(values['risk_' + method] >= threshold) for method, threshold in thresholds.items()}
    archived_flags = {'alert_' + method: int(archived['alert_' + method]) for method in thresholds}
    assert flags == archived_flags == entry['rerun_flags'] == entry['archived_flags']
    low_quality = values['dice_vs_reference'] < lock['threshold_lock']['quality_reference']['cutoff']
    assert low_quality == bool(int(archived['low_quality'])) == entry['rerun_low_quality']
    assert entry['flags_match'] and entry['low_quality_label_match']
    counts = [int(np.count_nonzero(mask)) for mask in masks]
    assert counts == entry['prediction_pixel_counts']
    assert all(value > 0 for value in counts)
    tp = int(np.count_nonzero(masks[0] & ref))
    fp = int(np.count_nonzero(masks[0] & ~ref))
    fn = int(np.count_nonzero(~masks[0] & ref))
    case_reviews.append({
        'image_id': case, 'archived_group': entry['archived_group'],
        'artifact': str(artifact), 'artifact_sha256': artifact_hash, 'artifact_hash_matches_receipt': True,
        'array_shapes': {k: list(v.shape) for k, v in arrays.items()},
        'array_dtypes': {k: str(v.dtype) for k, v in arrays.items()},
        'rgb_reference_boxes_match_preflight_exact': True,
        'mask_order': ['initial', *DIRECTIONS], 'prediction_foreground_pixel_counts': counts,
        'all_five_masks_nonempty': True, 'initial_prediction_is_not_reference': not np.array_equal(masks[0], ref),
        'initial_reference_overlap_pixels': {'TP': tp, 'FP': fp, 'FN': fn},
        'raw_predicted_ious': scores.tolist(), 'comparison': comparison,
        'metrics_match_receipt_exactly': True, 'flags': flags, 'flags_match_archive': True,
        'low_quality': low_quality, 'low_quality_matches_archive': True,
        'risk_minus_locked_threshold': {method: values['risk_' + method] - threshold for method, threshold in thresholds.items()},
    })

maximum = max(all_comparisons, key=lambda x: x['absolute_difference'])
max_dice = max((x for x in all_comparisons if x['field'] == 'dice_vs_reference'), key=lambda x: x['absolute_difference'])
field_summary = {field: {'exact_match_count': sum(x['exact_match'] for x in all_comparisons if x['field'] == field),
                         'max_absolute_difference': max(x['absolute_difference'] for x in all_comparisons if x['field'] == field)}
                 for field in FIELDS}
exact_count = sum(x['exact_match'] for x in all_comparisons)
assert receipt['all_flags_match']
assert receipt['all_fields_exact'] == (exact_count == 48)
assert receipt['max_absolute_difference'] == maximum['absolute_difference']

png = PRED / 'external_six_case_predictions.png'
pdf = PRED / 'external_six_case_predictions.pdf'
assert png.stat().st_size and pdf.stat().st_size
with Image.open(png) as image:
    image.load()
    png_dimensions = list(image.size)
    assert image.size == (3000, 5400)
    assert image.getbbox() is not None
    image.thumbnail((1200, 2160))
    image.convert('RGB').save(QA / 'prediction_sheet_visual_preview.jpg', quality=94)
with fitz.open(pdf) as doc:
    assert len(doc) == 1
    page = doc[0]
    text = page.get_text()
    assert all(text.count(case) == 1 for case in expected_ids)
    assert text.count('Actual targeted rerun prediction (orange)') == 6
    assert text.count('Released primary reference (green)') == 6
    assert text.count('Original + reference-derived prompt') == 6
    page_dimensions = [page.rect.width, page.rect.height]
    embedded_images = len(page.get_images())
    assert embedded_images >= 6
    page.get_pixmap(matrix=fitz.Matrix(1.3, 1.3)).save(QA / 'prediction_pdf_render.png')
    (QA / 'prediction_pdf_text.txt').write_text(text)

visual_evidence_path = QA / 'postrun_visual_review.json'
visual_evidence = json.loads(visual_evidence_path.read_text()) if visual_evidence_path.exists() else None
visual_passed = bool(visual_evidence and visual_evidence.get('status') == 'passed'
                     and visual_evidence.get('png_sha256') == sha(png)
                     and visual_evidence.get('pdf_sha256') == sha(pdf))
report = {
    'reviewed_at_utc': datetime.now(timezone.utc).isoformat(),
    'status': 'passed' if visual_passed else 'passed_numerical_and_file_integrity_checks_pending_visual_review',
    'scope': 'Independent recomputation from six saved NPZ artifacts, without importing torch or rerunning SAM.',
    'review_environment': {'python': platform.python_version(), 'numpy': np.__version__, 'pillow': pillow_version, 'pymupdf': fitz.VersionBind},
    'receipt_status': receipt['status'], 'receipt_sha256': sha(receipt_path),
    'runner_sha256': protocol['script_sha256'], 'runner_identical_to_frozen_source': True,
    'model_checkpoint_sha256': checkpoint_hash, 'sam_source_commit': sam_commit,
    'sam_source_clean': True, 'original_research_worktree_clean': True,
    'locked_primary_and_score_input_hashes_unchanged': unchanged,
    'case_count': len(case_reviews), 'captured_mask_count': 30, 'empty_captured_masks': 0,
    'numerical_field_count': 48, 'exact_matches_to_archive': exact_count,
    'nonexact_fields_to_archive': 48 - exact_count,
    'all_48_metric_values_match_independent_array_recomputation_exactly': True,
    'all_12_alert_decisions_match_archive': True, 'all_6_low_quality_labels_match_archive': True,
    'maximum_absolute_difference_to_archive': maximum,
    'maximum_reference_dice_difference_to_archive': max_dice,
    'field_summary': field_summary, 'thresholds': thresholds,
    'cases': case_reviews,
    'figure_file_checks': {
        'png': {'path': str(png), 'sha256': sha(png), 'bytes': png.stat().st_size, 'pixels': png_dimensions, 'decoded_successfully': True},
        'pdf': {'path': str(pdf), 'sha256': sha(pdf), 'bytes': pdf.stat().st_size, 'pages': 1, 'page_points': page_dimensions,
                'embedded_image_placements': embedded_images, 'all_six_case_labels_present_once': True, 'all_18_panel_labels_present': True, 'rendered_successfully': True},
    },
    'visual_review': visual_evidence if visual_passed else {'status': 'pending', 'png_preview': str(QA / 'prediction_sheet_visual_preview.jpg'), 'pdf_render': str(QA / 'prediction_pdf_render.png')},
    'interpretation': 'Exact model and matching preprocessing produce real captured predictions. CPU replay is not numerically bit-identical to the archived CUDA run; all review decisions and low-quality labels are preserved. The primary archived scores were not replaced.',
    'blocking_findings': [],
}
(QA / 'postrun_review.json').write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + '\n')
lines = ['# Six-case SAM replay independent post-run review', '',
         'All numerical and file-integrity checks passed. This review reads saved prediction arrays; no inference was repeated.', '',
         f"Six NPZ artifacts contain all 30 actual nonempty masks. All 48 metric values were independently recomputed from arrays and raw predicted IoUs and match the replay receipt exactly. All 12 alert decisions and all six low-quality labels agree with the frozen archive. {exact_count}/48 numerical fields match the archive exactly; {48-exact_count}/48 differ in the CPU replay.", '',
         f"The largest absolute archived-to-replay difference is {maximum['absolute_difference']:.12g}, in {maximum['image_id']} {maximum['field']}. The largest reference-Dice difference is {max_dice['absolute_difference']:.12g}, in {max_dice['image_id']}.", '',
         '| Case | Archived Dice | CPU replay Dice | Dice difference | A | B | Initial pixels |',
         '|---|---:|---:|---:|---:|---:|---:|']
for case in case_reviews:
    d = case['comparison']['dice_vs_reference']
    lines.append(f"| {case['image_id']} | {d['archived']:.9f} | {d['independently_recomputed_rerun']:.9f} | {d['difference']:+.9f} | {case['flags']['alert_A']} | {case['flags']['alert_B']} | {case['prediction_foreground_pixel_counts'][0]} |")
lines += ['', 'Exact frozen SAM source and checkpoint identities pass verification. All NPZ hashes match the replay receipt; image, reference and box arrays match preflight fingerprints. The original research worktree is clean and all locked primary/score/manifest hashes remain unchanged.', '',
          ('PNG decoding and one-page PDF rendering both succeed. The PDF contains all six case identifiers and all 18 expected panel labels. Visual review passed: six distinct correctly linked rows; prompt/reference/prediction columns and colors are clear; titles are readable and not truncated. Case175 has a true top-border narrow-band prediction with 3861 pixels, confirmed in a full-resolution crop; it is not an empty mask.' if visual_passed else 'PNG decoding and one-page PDF rendering both succeed. The PDF contains all six case identifiers and all 18 expected panel labels. Visual review is pending inspection of the generated previews.'), '',
          'These are captured targeted CPU replay predictions. They must not be described as original saved CUDA predictions or as a bit-identical reproduction. The frozen primary scores remain the study record.', '']
(QA / 'postrun_review.md').write_text('\n'.join(lines))
print(json.dumps({'case_count': 6, 'mask_count': 30, 'exact_fields': exact_count,
                  'max_absolute_difference': maximum, 'max_dice_difference': max_dice,
                  'all_flags_match': True, 'all_low_quality_match': True, 'output': str(QA)}, indent=2))
