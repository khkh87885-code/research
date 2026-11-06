# Six-case SAM replay independent preflight review

Passed the read-only preflight. No blocking functional mismatch was found between the targeted rerun and frozen inference logic. No model inference was performed in this review.

Reviewed runner SHA256: `2fa13777d6b4fae4a9711577c5dad4efa6550b2253c5aba1131372270b044acc`.
Frozen scorer SHA256: `00086ee2db464e8e3080c2a2a02fc9d0a5e670ac03f9716e5ea1eb666d4bcbf8`.

All six raw image/reference hashes pass the locked manifest. Loaded RGB/reference arrays and all 30 float32 prompt boxes match the frozen preprocessing and prompt functions exactly. Alpha compositing changes no RGB pixel in any of these six cases. The original single-mask/float32 protocol, metric formulas, ordered consistency average and strict comparison operators agree.

| Case | Archived group | Base box [x0,y0,x1,y1] | Reference pixels | A flag | B flag |
|---|---|---|---:|---:|---:|
| case089 | both_missed | [157.9, 110.7, 267.1, 222.3] | 6012 | 0 | 0 |
| case175 | both_missed | [188.8, 0, 647.2, 159.1] | 34108 | 0 | 0 |
| case238 | both_missed | [108.6, 146.5, 281.4, 284.5] | 9783 | 0 | 0 |
| case024 | B_only_detected | [130.3, 36.8, 294.7, 159.2] | 7642 | 0 | 1 |
| case105 | B_only_detected | [53.6, 41, 742.4, 497] | 132942 | 0 | 1 |
| case222 | B_only_detected | [18.8, 15.7, 405.2, 187.3] | 18065 | 0 | 1 |

Thresholds are frozen at A=0.13705134391784668 and B=0.06972856653991777; alert when risk >= threshold. Low quality is reference Dice <0.70. Prompt order is initial, left, right, up, down.

The figure implementation reads actual captured initial masks from the six new NPZ artifacts, draws the released reference and prediction in separate correctly labelled columns, and preserves the archived group. No source reference is substituted for a SAM output.

## Execution notes

- CPU/Python/NumPy runtime differs from frozen Windows/RTX/CUDA environment: model identity and functional logic match, but exact numerical inference equivalence must be measured after capture.
- Run without python -O, because integrity and shape guards are implemented with assert.
- Original run_patient retries once on selected exceptions; targeted rerun stops on failure. A stopped or partial rerun is not complete evidence.
- Receipt status=complete is written before plot_captured; independently check that both PNG and PDF exist, open successfully, and show six distinct rows.
- Plot titles contain rerun Dice and risks but no rerun flags. If any flag or low-quality label changes, call out the discrepancy explicitly because row groups are archived groups.
- Current script checks the first model parameter dtype only. In the fresh default-float32 process this matches the original guard; final environment verification may also inspect all floating parameters/buffers.
- Do not compare current CPU elapsed seconds with archived RTX inference_ms as a reproduction of the original speed.

## Final acceptance checks

- Exactly six expected cases; five bool masks per NPZ in initial,left,right,up,down order; masks shape (5,H,W), boxes float32 shape (5,4), RGB uint8 shape(H,W,3), bool reference shape(H,W).
- Verify checkpoint SHA256, clean exact SAM git source, imported segment_anything path, environment versions, recorded source-script SHA256 and each NPZ artifact SHA256.
- Recompute all eight metric fields directly from captured arrays and raw_predicted_ious; recompute risk_A/risk_B, flags and low-quality labels against locked cutoffs without rounding.
- Compare all 48 numerical fields to archive and report exact matches plus absolute deltas; separately report flags and low-quality label agreement.
- Verify pixel counts and nonempty status from all 30 masks. Archive says all six initial masks are nonempty; positive archived consistency Dice also rules out empty shifted masks.
- Visually inspect actual six-row PNG/PDF for correct case linkage, contour orientation, prompt rectangle, readable titles and no truncation.
- Treat these outputs as verified targeted rerun predictions; do not describe them as saved original archived prediction arrays.

Preflight used Python 3.12.14, NumPy 1.26.4, Pillow 10.4.0. This is a preprocessing/logic check, not a claim that this is the inference environment. The final replay receipt must record its actual dependency versions.
