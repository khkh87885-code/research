# Independent decomposition input check

All checks passed. Source branch `main`, commit `f9cfdc49b6e6a9e037443f6ce077006bc9377960`. All seven score, manifest and raw diagnostic-metadata hashes match the v7 pathology audit. The prior audit carries an older commit ID, but its input files are byte-identical to current main.

- 1,316 score rows correspond to 1,316 unique dataset-qualified patients.
- Development and internal BUS-BRA patient overlap: 0.
- Internal/external exact image-SHA256 overlap: 0.
- Score/manifest/official metadata diagnosis mismatches: 0.
- Risk-threshold versus archived flag mismatches: 0.
- Reference Dice versus archived low-quality labels mismatches: 0.

Dataset-local numeric patient IDs cannot establish absence of the same person across datasets; this check establishes namespace uniqueness and absence of exact image overlap. BrEaST labels are dataset-reported Classification, comprising biopsy and follow-up confirmation; they are not all histopathologically confirmed.

| Cohort | Diagnosis | N | Low-quality | A detected | A reviewed | B detected | B reviewed |
|---|---|---:|---:|---:|---:|---:|---:|
| development | benign | 145 | 10 | 10 | 21 | 8 | 21 |
| development | malignant | 68 | 14 | 9 | 22 | 9 | 22 |
| internal_holdout | benign | 577 | 53 | 51 | 102 | 41 | 80 |
| internal_holdout | malignant | 274 | 40 | 20 | 72 | 27 | 70 |
| external_test | benign | 154 | 8 | 5 | 15 | 7 | 13 |
| external_test | malignant | 98 | 8 | 5 | 20 | 6 | 20 |

Actual elapsed validation time: 0.294349 seconds. No model inference was performed.
