#!/usr/bin/env python3
"""Read-only preflight comparison; does not import torch or run SAM inference."""
import ast
import csv
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import platform

import numpy as np
from PIL import Image, __version__ as pillow_version

SOURCE = Path('/workspace/research_source')
OUT = Path('/workspace/bmt_six_case_replay/qa')
AUDIT = SOURCE / 'submission/bmt_v7/Analysis/external_case_audit.py'
ORIGINAL = SOURCE / 'reproducibility/score_images.py'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


spec = importlib.util.spec_from_file_location('reviewed_external_case_audit', AUDIT)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

# Extract only the frozen pure NumPy functions, avoiding the original script's
# torch import and forced-CUDA inference entry point.
tree = ast.parse(ORIGINAL.read_text())
pure = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in ('dice', 'prompt_boxes')]
ns = {'np': np, 'BORDER_FRACTION': 0.10, 'SHIFT_FRACTION': 0.05}
exec(compile(ast.Module(body=pure, type_ignores=[]), str(ORIGINAL), 'exec'), ns)
lock, manifests, selected = audit.audited_records(SOURCE)
assert {r['image_id'] for r in selected} == {'case024', 'case089', 'case105', 'case175', 'case222', 'case238'}

cases = []
for row in selected:
    manifest = manifests[row['image_id']]
    image, reference, changed = audit.load_pair(SOURCE, manifest)
    path = SOURCE / 'data/raw/BrEaST' / manifest['image_path']
    maskpath = SOURCE / 'data/raw/BrEaST' / manifest['mask_path']
    with Image.open(path) as source_image:
        image_mode, image_format = source_image.mode, source_image.format
        uncomposited = np.asarray(source_image.convert('RGB'), dtype=np.uint8)
        rgba = source_image.convert('RGBA')
        alpha = np.asarray(rgba.getchannel('A'))
        # The frozen measure_case uses these exact PIL calls for BrEaST.
        original_rgb = np.asarray(Image.alpha_composite(
            Image.new('RGBA', rgba.size, (0, 0, 0, 255)), rgba
        ).convert('RGB'), dtype=np.uint8)
    with Image.open(maskpath) as source_mask:
        mask_mode, mask_format = source_mask.mode, source_mask.format
        original_reference = np.asarray(source_mask.convert('1'), dtype=bool)
    assert np.array_equal(image, original_rgb)
    assert np.array_equal(reference, original_reference)
    assert not changed
    base, shifted = ns['prompt_boxes'](original_reference)
    original_boxes = np.stack([base, *shifted.values()])
    replay_boxes = audit.prompt_boxes(reference)
    assert replay_boxes.dtype == np.float32
    assert original_boxes.dtype == np.float32
    assert original_boxes.tobytes() == replay_boxes.tobytes()
    assert list(shifted) == list(audit.DIRECTIONS)
    consistency = [float(row['dice_shift_' + direction]) for direction in audit.DIRECTIONS]
    thresholds = {m: lock['threshold_lock']['methods'][m]['threshold'] for m in ('A', 'B')}
    risks = {'A': 1.0 - float(row['sam_predicted_iou']), 'B': 1.0 - sum(consistency) / 4}
    assert all(risks[m] == float(row['risk_' + m]) for m in risks)
    flags = {'alert_' + m: int(risks[m] >= thresholds[m]) for m in risks}
    assert all(flags['alert_' + m] == int(row['alert_' + m]) for m in risks)
    assert int(float(row['dice_vs_reference']) < 0.70) == int(row['low_quality'])
    cases.append({
        'image_id': row['image_id'], 'group': row['group'],
        'width': image.shape[1], 'height': image.shape[0],
        'image_format': image_format, 'image_mode': image_mode,
        'mask_format': mask_format, 'mask_mode': mask_mode,
        'image_sha256': sha(path), 'reference_sha256': sha(maskpath),
        'input_rgb_array_sha256': hashlib.sha256(image.tobytes()).hexdigest(),
        'input_reference_array_sha256': hashlib.sha256(reference.tobytes()).hexdigest(),
        'input_loading_matches_frozen': True,
        'alpha_min': int(alpha.min()), 'alpha_max': int(alpha.max()),
        'alpha_compositing_changes_pixels': changed,
        'rgb_pixels_changed_by_alpha': int(np.count_nonzero(np.any(image != uncomposited, axis=2))),
        'reference_foreground_pixels': int(reference.sum()),
        'box_order': ['initial', *audit.DIRECTIONS], 'boxes_float32': replay_boxes.tolist(),
        'boxes_sha256': hashlib.sha256(replay_boxes.tobytes()).hexdigest(),
        'boxes_match_frozen_byte_exact': True,
        'distinct_shifted_boxes': len({tuple(box) for box in replay_boxes[1:]}),
        'archived_metrics': {k: float(row[k]) for k in audit.FIELDS},
        'risk_formulas_match_archived_exact': True,
        'thresholds': thresholds, 'flags_recomputed_from_archived': flags,
        'flag_formulas_match_archived': True,
        'low_quality_recomputed_from_archived': float(row['dice_vs_reference']) < 0.70,
        'risk_minus_threshold': {m: risks[m] - thresholds[m] for m in risks},
        'dice_minus_low_quality_cutoff': float(row['dice_vs_reference']) - 0.70,
    })

dice_checks = []
for name, first, second in (
    ('both_empty', np.zeros((2, 3), bool), np.zeros((2, 3), bool)),
    ('one_empty', np.zeros((2, 3), bool), np.ones((2, 3), bool)),
    ('identical', np.eye(3, dtype=bool), np.eye(3, dtype=bool)),
    ('partial_overlap', np.array([[True, True, False]]), np.array([[False, True, True]])),
):
    archived_value, rerun_value = ns['dice'](first, second), audit.dice(first, second)
    assert archived_value == rerun_value
    dice_checks.append({'case': name, 'frozen': archived_value, 'rerun': rerun_value, 'exact_match': True})

report = {
    'reviewed_at_utc': datetime.now(timezone.utc).isoformat(),
    'review_scope': 'Independent preflight only: no torch import, SAM model load, or model inference was performed.',
    'status': 'passed_preflight',
    'source_files': {str(AUDIT): sha(AUDIT), str(ORIGINAL): sha(ORIGINAL),
                     str(SOURCE / 'reproducibility/study_lock.json'): sha(SOURCE / 'reproducibility/study_lock.json')},
    'review_environment': {'python': platform.python_version(), 'numpy': np.__version__, 'pillow': pillow_version},
    'model_required': lock['threshold_lock']['model'],
    'frozen_inference_environment': lock['environment'],
    'logic_findings': {
        'selection': 'Exactly the six frozen external Dice<0.70 cases with alert_A=0; partition uses archived alert_B.',
        'input': 'PNG hashes are checked against locked manifest; RGB uint8 uses RGBA compositing on opaque black; reference is PIL convert(1) to bool.',
        'geometry': '10% expansion per side of inclusive foreground bounding rectangle with right/bottom +1; clip to [0,width/height]; shift each direction by 5% of clipped base width/height; float32 coordinates.',
        'inference': 'Same exact clean SAM ViT-B source and checkpoint are required; strict state load; eval; first weight dtype float32; torch.inference_mode; predictor.set_image then five predict(box=...,multimask_output=False) calls; no autocast or point/mask prompt.',
        'sam_mask_conversion': 'Exact SAM predict defaults return_logits=False and thresholds postprocessed masks at model.mask_threshold=0.0; output is original-size boolean single mask.',
        'metrics': 'Reference Dice and each initial-vs-shifted Dice use identical integer-count formula and both-empty convention=1; A=1-initial raw predicted IoU; B=1-ordered four-shift mean Dice.',
        'thresholds': 'Alerts use risk>=locked cutoff with no tolerance; low quality uses reference Dice<0.70. No recalibration or risk clipping.',
        'capture': 'Each new NPZ stores actual image/reference, all five model masks, five boxes and five raw predicted IoUs; each artifact SHA256 is recorded.',
        'plot': 'Each row loads image/reference/initial prediction from that row\'s actual captured NPZ. Left is actual input+prompt, middle reference contour green, right actual initial prediction contour orange. Labels explicitly say targeted rerun and preserve archived group.',
    },
    'blocking_bugs_found': [],
    'nonblocking_execution_notes': [
        'CPU/Python/NumPy runtime differs from frozen Windows/RTX/CUDA environment: model identity and functional logic match, but exact numerical inference equivalence must be measured after capture.',
        'Run without python -O, because integrity and shape guards are implemented with assert.',
        'Original run_patient retries once on selected exceptions; targeted rerun stops on failure. A stopped or partial rerun is not complete evidence.',
        'Receipt status=complete is written before plot_captured; independently check that both PNG and PDF exist, open successfully, and show six distinct rows.',
        'Plot titles contain rerun Dice and risks but no rerun flags. If any flag or low-quality label changes, call out the discrepancy explicitly because row groups are archived groups.',
        'Current script checks the first model parameter dtype only. In the fresh default-float32 process this matches the original guard; final environment verification may also inspect all floating parameters/buffers.',
        'Do not compare current CPU elapsed seconds with archived RTX inference_ms as a reproduction of the original speed.',
    ],
    'post_run_acceptance_checks': [
        'Exactly six expected cases; five bool masks per NPZ in initial,left,right,up,down order; masks shape (5,H,W), boxes float32 shape (5,4), RGB uint8 shape(H,W,3), bool reference shape(H,W).',
        'Verify checkpoint SHA256, clean exact SAM git source, imported segment_anything path, environment versions, recorded source-script SHA256 and each NPZ artifact SHA256.',
        'Recompute all eight metric fields directly from captured arrays and raw_predicted_ious; recompute risk_A/risk_B, flags and low-quality labels against locked cutoffs without rounding.',
        'Compare all 48 numerical fields to archive and report exact matches plus absolute deltas; separately report flags and low-quality label agreement.',
        'Verify pixel counts and nonempty status from all 30 masks. Archive says all six initial masks are nonempty; positive archived consistency Dice also rules out empty shifted masks.',
        'Visually inspect actual six-row PNG/PDF for correct case linkage, contour orientation, prompt rectangle, readable titles and no truncation.',
        'Treat these outputs as verified targeted rerun predictions; do not describe them as saved original archived prediction arrays.',
    ],
    'dice_pure_function_checks': dice_checks,
    'cases': cases,
}
OUT.mkdir(parents=True, exist_ok=True)
(OUT / 'preflight_review.json').write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + '\n')
lines = [
    '# Six-case SAM replay independent preflight review', '',
    'Passed the read-only preflight. No blocking functional mismatch was found between the targeted rerun and frozen inference logic. No model inference was performed in this review.', '',
    f'Reviewed runner SHA256: `{sha(AUDIT)}`.',
    f'Frozen scorer SHA256: `{sha(ORIGINAL)}`.', '',
    'All six raw image/reference hashes pass the locked manifest. Loaded RGB/reference arrays and all 30 float32 prompt boxes match the frozen preprocessing and prompt functions exactly. Alpha compositing changes no RGB pixel in any of these six cases. The original single-mask/float32 protocol, metric formulas, ordered consistency average and strict comparison operators agree.', '',
    '| Case | Archived group | Base box [x0,y0,x1,y1] | Reference pixels | A flag | B flag |',
    '|---|---|---|---:|---:|---:|',
]
for c in cases:
    box = ', '.join(f'{v:.7g}' for v in c['boxes_float32'][0])
    lines.append(f"| {c['image_id']} | {c['group']} | [{box}] | {c['reference_foreground_pixels']} | {c['flags_recomputed_from_archived']['alert_A']} | {c['flags_recomputed_from_archived']['alert_B']} |")
lines += ['', 'Thresholds are frozen at A=0.13705134391784668 and B=0.06972856653991777; alert when risk >= threshold. Low quality is reference Dice <0.70. Prompt order is initial, left, right, up, down.', '',
          'The figure implementation reads actual captured initial masks from the six new NPZ artifacts, draws the released reference and prediction in separate correctly labelled columns, and preserves the archived group. No source reference is substituted for a SAM output.', '',
          '## Execution notes', '']
lines.extend('- ' + item for item in report['nonblocking_execution_notes'])
lines += ['', '## Final acceptance checks', '']
lines.extend('- ' + item for item in report['post_run_acceptance_checks'])
lines += ['', f"Preflight used Python {platform.python_version()}, NumPy {np.__version__}, Pillow {pillow_version}. This is a preprocessing/logic check, not a claim that this is the inference environment. The final replay receipt must record its actual dependency versions.", '']
(OUT / 'preflight_review.md').write_text('\n'.join(lines))
print(json.dumps({'status': report['status'], 'case_count': len(cases), 'all_30_boxes_byte_exact': True, 'output': str(OUT)}, indent=2))
