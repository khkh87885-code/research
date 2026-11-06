# Scientific and numerical audit

Source: `khkh87885-code/research`, commit `592566b4c5f39e261c676eb034139a974e9cdfd5`. Audit date: 6 November 2026. Original repository files were read without modification. This audit establishes internal consistency and computational reproduction of the archived evidence; it does not establish the authenticity of patient acquisition or independent model replication.

## Verdict

**Numerically consistent within the checked scope; manuscript interpretation must retain the known-location design and external uncertainty.** No numerical correction to the existing primary or supplementary results is needed. Descriptive quality-control utility metrics have been added separately. The empty-prediction concern did not affect the archived cases.

## Independently recalculated evidence

`../scripts/independent_scientific_audit.py` is a separate implementation that imports none of the study's calculation helpers. It checks cohort identities, individual risk definitions and flags, reselects the development cutoffs, recomputes confusion matrices, Wilson intervals and Newcombe differences, and compares 78 reported result fields to the frozen numerical outputs. All compared fields agree within floating-point tolerance (absolute tolerance 1e-11).

The development set contains 213 unique patients. The internal set contains 851 unique patients and is disjoint from development by BUS-BRA patient ID. The external set contains 252 unique patients. Each selected case matches its frozen manifest. Every archived case has `status=scored`. The risk scores equal their stated definitions, and each saved review flag agrees with risk >= the complete-precision locked threshold. The primary reference condition is Dice < 0.70.

Recalibration selected exactly the original thresholds: A=0.13705134391784668; B=0.06972856653991777. Both flag 43/213 development cases. No threshold was retuned on test results. The documented lock timestamp (5 November 2026, 19:16:27 +08:00) precedes the formal-scoring start timestamp (19:51:56 +08:00). This checks the recorded chronology, rather than establishing a separately registered protocol.

| Contrast | Difference, percentage points | 95% interval, percentage points |
| --- | ---: | --- |
| H1: external minus internal sensitivity, A | -13.844086 | [-38.849065, +7.448184] |
| H2: external minus internal review fraction, A | -6.557645 | [-11.245572, -1.098304] |
| H3: external sensitivity, B minus A | +18.750000 | [-4.283596, +40.038898] |
| Equal review: external sensitivity, B minus A | -6.250000 | [-31.609404, +19.567264] |

H3 uses 10 cases detected by both, 3 detected by B alone, 0 detected by A alone, and 3 missed by both. The pairing is retained rather than treating A and B as independent samples. At equal review counts, both methods select 50/252 cases using descending risk and the string-valued patient ID to break ties; A detects 14/16 and B 13/16. The selected IDs exactly match the supplementary archive.

The paired interval implementation was independently checked against six published Table III examples in Newcombe, *Statistics in Medicine* 1998;17:2635-2650. Its method 10 applies the positive-association correction max(eh-fg-n/2,0) to the correlation numerator when eh>fg, with no correction to the Wilson marginal limits. All six examples agree at published four-decimal precision. A readable source copy and URL are in `Newcombe_1998_paired_source.md`.

H2, H3 and supplementary intervals are nominal 95% intervals without multiplicity adjustment. The equal-review interval conditions on the observed selections and does not include variability from re-ranking a new sample.

At fixed thresholds and Dice < 0.50, internal failures=53 and external failures=7; A detects 52/53 and 5/7; B detects 43/53 and 5/7. At Dice < 0.80, internal failures=183 and external failures=50; A detects 109/183 and 21/50; B detects 95/183 and 21/50. Counts, differences and intervals match the original supplementary outputs. Review counts remain unchanged when only the reference quality definition changes.

## Additional quality-control utility

`utility_metrics.csv` contains 18 rows: both methods in all three cohorts at reference Dice cutoffs 0.50, 0.70 and 0.80. It includes TP/FP/TN/FN, sensitivity, specificity, positive predictive value, negative predictive value, review fraction, misses per 100, explicit numerators/denominators, and Wilson 95% intervals. `utility_table_for_supplement.md` supplies the six main-definition rows in editable text.

Here a positive condition means low-quality segmentation; a positive test means a review flag. These are not breast-cancer diagnostic metrics. Specificity, PPV and NPV added during this revision are **post hoc descriptive** summaries, not new prespecified hypotheses. Development estimates are in-sample threshold-selection estimates.

For external A, TP=10, FP=25, TN=211, FN=6; specificity=89.41%, PPV=28.57%, NPV=97.24%. For external B, TP=13, FP=20, TN=216, FN=3; specificity=91.53%, PPV=39.39%, NPV=98.63%. High NPV occurs in a sample with 16/252 low-quality cases and cannot by itself establish a safe clinical workflow. No comparative superiority is established by these point estimates.

## Empty-prediction handling

The archived initial-empty indicator is present for all 1,316 cases and is 0 for every case. Every one of the 5,264 initial-versus-perturbed Dice scores is strictly positive. Given a nonempty initial mask, a positive Dice requires a nonempty perturbed mask with nonzero intersection. Therefore, all 5,264 perturbed predictions are also nonempty in the archived evidence. No empty-empty comparison occurs; the convention Dice(empty,empty)=1 affects zero cases. An empty-mask sensitivity analysis would reproduce identical results and is unnecessary.

This conclusion uses direct initial flags plus logically sufficient positive consistency values; it does not pretend that perturbation pixel areas were saved. The pipeline does not save those areas or all predicted masks. Development case `bus_0905-l` has Dice=0 against the reference but an explicitly nonempty initial prediction, illustrating why Dice=0 must not be interpreted as an empty mask. Details are in `empty_mask_audit.json` and `.md`.

## Image and reference audit

All 1,316 selected original image/reference pairs were read in this audit. Every pair matches its manifest dimensions and has a nonempty manual reference. All 504 BrEaST image and reference file hashes match the frozen manifest hashes. The eight cases whose visible RGB pixels change when transparency is composited over black are exactly 5, 11, 77, 101, 112, 144, 215 and 216, matching the lock. Digests of every selected image/reference file are in `selected_raw_file_sha256.json`.

These checks validate the locally available selected files and frozen memberships. They are not a fresh verification against original remote archive bytes, which are not stored in the repository. The original archive digests are recorded in `study_lock.json` and the historical inference receipt.

## Reproduction package and runtime audit

The supplied ZIP passes its CRC test. All 15 ZIP members match their corresponding uncompressed package files, and all 14 entries in SHA256SUMS.txt match. The seven files locked by `study_lock.json` match their expected digests. Package evidence is in `reproduction_package_integrity.json`.

Two computations were executed in this audit:

1. `python -B reproduce.py analyze --output [new audit directory]` recalculates the original archived scores. Calibration, primary and supplementary outputs all exactly match the archived outputs.
2. `python -B reproduce.py analyze --run [existing image_rerun directory] --output [new audit directory]` validates the existing inference receipt and recomputes statistics from the **previously generated** image-rerun scores. Calibration, primary and supplementary outputs all match. All 1,316 cases have zero numerical and flag differences against the archived case scores. The review-curve data agree.

The second operation is a fresh analysis of an existing image rerun; **SAM inference was not rerun during this revision**. Output folders deliberately use `prior_rerun_score_replay` to avoid confusing these events. The original receipt records Windows, Python 3.8.20, torch 2.4.1+cu118, torchvision 0.19.1+cu118, NumPy 1.24.4, Pillow 10.4.0 and an RTX 3060 Laptop GPU. The recorded SAM commit is dca509fe793f601edb92606367a655c15ac00fdf. The checkpoint digest is ec2df62732614e57411cdcf32a23ffdf28910380d03139ee0f4fcbe91eb8c912. Those identifiers agree across the lock, receipt and per-case records. Checkpoint bytes are not present and were not independently rehashed in this audit.

This is computational reproducibility, with a documented earlier same-environment image rerun. It must not be labelled independent replication by another research group or validation in an independent clinical workflow.

## Required interpretation and remaining limits

- Reference-derived localization boxes create a known-location/oracle-prompt experiment. The method does not demonstrate fully automated lesion detection or prospective clinical quality control.
- Only 16 external cases are low quality under the main definition. H1 and H3 intervals span zero and permit materially different effects in both directions. Absence of a detected difference does not show equivalence.
- Fixed-threshold and equal-review comparisons answer different questions. The ranking of the point estimates changes and must be retained.
- Two public datasets, one frozen model and one initial prompt rule cannot establish robust generalization across hospitals or devices. No clinical reader study or actual time-saving assessment was performed.
- Human author review of code, numerical results, figures, text, authorship and declarations must be confirmed by the authors; this automated audit cannot attest that they have personally completed it.
- Ethics/exemption, consent applicability and disclosure statements cannot be inferred from numerical consistency.

No extra experiments or statistical significance were invented. No unfavorable or uncertain result was removed. The archived data and prespecified results remain unchanged.
