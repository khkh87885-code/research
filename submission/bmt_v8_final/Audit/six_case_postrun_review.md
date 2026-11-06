# Six-case SAM replay independent post-run review

All numerical and file-integrity checks passed. This review reads saved prediction arrays; no inference was repeated.

Six NPZ artifacts contain all 30 actual nonempty masks. All 48 metric values were independently recomputed from arrays and raw predicted IoUs and match the replay receipt exactly. All 12 alert decisions and all six low-quality labels agree with the frozen archive. 6/48 numerical fields match the archive exactly; 42/48 differ in the CPU replay.

The largest absolute archived-to-replay difference is 0.0014354348103, in case105 dice_shift_left. The largest reference-Dice difference is 9.61064306665e-05, in case222.

| Case | Archived Dice | CPU replay Dice | Dice difference | A | B | Initial pixels |
|---|---:|---:|---:|---:|---:|---:|
| case089 | 0.319056655 | 0.319099905 | +0.000043250 | 0 | 0 | 1365 |
| case175 | 0.029287050 | 0.029287050 | +0.000000000 | 0 | 0 | 3861 |
| case238 | 0.681269798 | 0.681269798 | +0.000000000 | 0 | 0 | 5054 |
| case024 | 0.685173122 | 0.685138791 | -0.000034331 | 0 | 1 | 12316 |
| case105 | 0.654572458 | 0.654579028 | +0.000006571 | 0 | 1 | 271052 |
| case222 | 0.578368500 | 0.578464606 | +0.000096106 | 0 | 1 | 42115 |

Exact frozen SAM source and checkpoint identities pass verification. All NPZ hashes match the replay receipt; image, reference and box arrays match preflight fingerprints. The original research worktree is clean and all locked primary/score/manifest hashes remain unchanged.

PNG decoding and one-page PDF rendering both succeed. The PDF contains all six case identifiers and all 18 expected panel labels. Visual review passed: six distinct correctly linked rows; prompt/reference/prediction columns and colors are clear; titles are readable and not truncated. Case175 has a true top-border narrow-band prediction with 3861 pixels, confirmed in a full-resolution crop; it is not an empty mask.

These are captured targeted CPU replay predictions. They must not be described as original saved CUDA predictions or as a bit-identical reproduction. The frozen primary scores remain the study record.
