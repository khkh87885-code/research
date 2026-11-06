# Case-mix standardization and symmetric Kitagawa accounting

Post hoc descriptive analysis of the fixed locked thresholds. Source main: `f9cfdc49b6e6a9e037443f6ce077006bc9377960`. No SAM model was loaded or run.

## Inputs and denominators

Score/manifest/official-metadata labels, patient uniqueness within each dataset namespace, quality labels, locked decisions and all v7 stratum counts matched exactly.
Dataset-reported benign/malignant classification; BrEaST includes follow-up-confirmed cases, so not all diagnoses are histopathologically confirmed.
Internal: 851 patients, 93 low-quality masks (53 benign / 40 malignant). External: 252 patients, 16 low-quality masks (8 / 8). Detection weights are diagnostic shares among low-quality cases; review weights are shares among all cases. Identifiers are dataset-local.

Detection common benign/malignant weights: 0.53494624, 0.46505376.
Review common benign/malignant weights: 0.64456848, 0.35543152.

## Original records with bootstrap intervals

Values in the next table are percentage points [percentile 95% interval]. Direction is external minus internal.

| Method | Outcome | Overall difference | Composition-associated | Within-stratum-rate / standardized difference | Valid draws: overall / components |
|---|---|---:|---:|---:|---:|
| A | detection | -13.84 [-40.85, 11.40] | -1.62 [-10.89, 5.73] | -12.23 [-39.94, 14.30] | 5000 / 4999 |
| A | review_fraction | -6.56 [-11.54, -1.31] | 0.64 [-0.01, 1.54] | -7.20 [-12.15, -2.08] | 5000 / 5000 |
| B | detection | 8.13 [-15.09, 28.18] | -0.78 [-6.43, 3.62] | 8.91 [-14.32, 28.70] | 5000 / 4999 |
| B | review_fraction | -4.53 [-9.31, 0.41] | 0.79 [-0.01, 1.80] | -5.32 [-10.03, -0.56] | 5000 / 5000 |

Rates below are percent [percentile 95% interval], using the same recomputed common diagnostic weights in each draw.

| Method | Outcome | Observed internal | Observed external | Standardized internal | Standardized external |
|---|---|---:|---:|---:|---:|
| A | detection | 76.34 [67.44, 84.62] | 62.50 [36.36, 86.67] | 74.73 [63.91, 84.21] | 62.50 [36.51, 86.43] |
| A | review_fraction | 20.45 [17.74, 23.15] | 13.89 [9.92, 18.25] | 20.73 [18.02, 23.50] | 13.53 [9.45, 17.90] |
| B | detection | 73.12 [63.74, 82.02] | 81.25 [60.00, 100.00] | 72.77 [63.27, 81.85] | 81.69 [60.49, 100.00] |
| B | review_fraction | 17.63 [15.04, 20.21] | 13.10 [8.73, 17.46] | 18.02 [15.43, 20.68] | 12.69 [8.66, 16.98] |

## Accounting identities and resampling

For every method/outcome: C = Σ(wE−wI)(pE+pI)/2; R = Σ(pE−pI)(wE+wI)/2; D = external−internal = C+R. Common weights w*=(wE+wI)/2 give standardized external−internal = R. These are algebraic identities, not causal models.

5000 patient-bootstrap repetitions; PCG64 seed 20261107. Cohorts were independently resampled, with the same sampled patient indices retaining A/B, quality and diagnosis. Stratum weights and rates were recalculated in every repetition. Development calibration was not resampled in this module. Intervals use finite repetitions and unadjusted percentile limits. No missing denominator was filled.

Zero stratum-denominator draws: `{"detection": {"internal_holdout": {"benign": 0, "malignant": 0}, "external_test": {"benign": 1, "malignant": 0}}, "review_fraction": {"internal_holdout": {"benign": 0, "malignant": 0}, "external_test": {"benign": 0, "malignant": 0}}}`. Overall rates can remain estimable when a stratum-specific decomposition is undefined. Each statistic's valid and invalid counts are in JSON and summary CSV.

Maximum absolute bootstrap identity residuals: 2.498001805406602e-16 (raw fractions); standardized-difference identity: 2.220446049250313e-16.

## Interpretation

For detection, composition-associated terms refer specifically to the benign/malignant label composition of the low-quality subset, not the diagnostic composition of the full cohorts. A has negative composition-associated and within-stratum-rate terms; their sum is the observed negative overall detection difference. B has a negative composition-associated term and positive within-stratum-rate term. For review fractions, composition refers to the full-cohort diagnostic shares; both methods have a positive composition-associated term and a negative within-stratum-rate term. These signed accounting terms describe the observed two-stratum mixtures and do not identify causes.

Diagnostic standardization does not eliminate device/acquisition, reference-annotation or other confounding. External detection relies on 16 low-quality masks. Bootstrap intervals do not supply new patients or replace the original prespecified Newcombe intervals; zero-crossing does not establish equivalence.

## Runtime, resources and files

Actual 5000-draw bootstrap time: 1.107427 seconds. Actual process elapsed time through data verification, CSV exports and PNG/PDF rendering: 2.829753 seconds. The final JSON/Markdown write is excluded from that endpoint.
Numerical thread settings: all 1. cgroup CPU quota: `200000 100000`; memory limit: `8589934592` bytes. Observed threadpools and package versions are in JSON.

Portable entry point: `scripts/case_mix_decomposition.py`; results: `results/case_mix_decomposition.json`, `.csv`, `_strata.csv`, `_bootstrap.csv`; figures: `figures/case_mix_decomposition.png` and `.pdf`. Input hashes, script hash and protocol hash are in JSON.

The v7 stratum audit was created at an earlier source commit; its relevant input hashes and counts match the current source exactly. Source manuscripts and the fixed protocol were not edited.

## SHA-256 inputs

| Input | SHA-256 |
|---|---|
| `reproducibility/records/validation_cases.csv` | `6ac44d3d3557caceba1e47dab4f87bc3b180568195c0d0ecb6506fbb04d07961` |
| `reproducibility/manifests/busbra_internal_holdout.csv` | `2727d11d0db4f41ddd70a915576e5273a9d0ecbd735f151ae2ae710d0963a026` |
| `reproducibility/manifests/breast_external.csv` | `33db74c60e8ce242f82f5efcd1007c08151e6faf359a6204f68a251791dbda22` |
| `reproducibility/study_lock.json` | `91189487ed1fa5328f33e5db4094f846f5619d73924329577f6a0d9e05ffc7d0` |
| `submission/bmt_v7/Audit/pathology_audit.json` | `ce1a085b1306c8267f5aec737ae41fbcfbfd529b14cc5694f75b68ac22e5b7a5` |
| `data/raw/BUS-BRA/BUSBRA/bus_data.csv` | `f218d0f10b0aeeb14ff4b2cfed8631b2f4a7cf608e564548b35bddd55f3aafb3` |
| `data/raw/BrEaST/BrEaST-Lesions-USG-clinical-data-Dec-15-2023.xlsx` | `89a8874496a6f1f93960390b963f7369b90f7e72ee08a738f2d17e37f5eff8bf` |
| protocol | `c34718732b856ab31d0d8ae19c88bbbf0f43a9614ea14433d8f62210cc1409c7` |
| executable script | `818487d97e5ec9e34c594b724199b64f24d0590f2fed25c7c047dd5e9dc311ac` |

