# Exploratory stratification by dataset-reported benign/malignant classification

Source commit: `9fc8f54a91216b80aba909ba6028078f7642e4a9`. The archived score tables, locked thresholds and primary Dice < 0.70 definition were preserved. No SAM inference, threshold recalibration, hypothesis test or interaction test was performed.

## Label and join audit

All 1,316 score records matched their frozen manifests and original dataset metadata. The full score-to-manifest key was `(dataset, canonical integer patient_id, image_id)`; dataset namespaces were kept separate. BUS-BRA labels came from official `bus_data.csv:Pathology`, joined by `image_id=ID` and checked against `patient_id=Case`. BrEaST labels came from the first official workbook worksheet, using `Classification`, joined by `patient_id=CaseID` with image and main-mask filename checks. Missing labels, conflicting labels, repeated patient rows and unmatched records were all zero. BUS-BRA development and internal patients were disjoint. Their strata contain 145/68 and 577/274 benign/malignant cases; BrEaST contains 154/98.

BrEaST verification was biopsy in 197 cases and follow-up care in 55 (all in the benign group). Therefore, this is stratification by dataset-reported benign/malignant classification, not a statement that every case had histopathological confirmation. The four normal cases without a main lesion mask (45, 61, 209, 213) remain excluded. Independent label-audit details are in `pathology_label_join_audit.json` and `.md`.

## Supplementary Table S8 — primary proposed display

| Cohort | Diagnostic stratum | Method | N | Low quality | Reviewed, n/N (%) | Low-quality detected, TP/F (%) | Wilson 95% CI (%) | FP | TN | FN | Misses/100 |
| --- | --- | --- | ---: | ---: | --- | --- | --- | ---: | ---: | ---: | ---: |
| BUS-BRA internal | benign | A | 577 | 53 | 102/577 (17.68) | 51/53 (96.23) | 87.25–98.96 | 51 | 473 | 2 | 0.35 |
| BUS-BRA internal | benign | B | 577 | 53 | 80/577 (13.86) | 41/53 (77.36) | 64.47–86.55 | 39 | 485 | 12 | 2.08 |
| BUS-BRA internal | malignant | A | 274 | 40 | 72/274 (26.28) | 20/40 (50.00) | 35.20–64.80 | 52 | 182 | 20 | 7.30 |
| BUS-BRA internal | malignant | B | 274 | 40 | 70/274 (25.55) | 27/40 (67.50) | 52.02–79.92 | 43 | 191 | 13 | 4.74 |
| BrEaST external | benign | A | 154 | 8 | 15/154 (9.74) | 5/8 (62.50) | 30.57–86.32 | 10 | 136 | 3 | 1.95 |
| BrEaST external | benign | B | 154 | 8 | 13/154 (8.44) | 7/8 (87.50) | 52.91–97.76 | 6 | 140 | 1 | 0.65 |
| BrEaST external | malignant | A | 98 | 8 | 20/98 (20.41) | 5/8 (62.50) | 30.57–86.32 | 15 | 75 | 3 | 3.06 |
| BrEaST external | malignant | B | 98 | 8 | 20/98 (20.41) | 6/8 (75.00) | 40.93–92.85 | 14 | 76 | 2 | 2.04 |

Table footnote: Exploratory post hoc analysis. Low-quality segmentation is defined as reference Dice < 0.70. A positive review flag indicates risk >= the original development-selected method-specific threshold (A 0.13705134391784668; B 0.06972856653991777). F denotes the low-quality count within the diagnostic stratum; detection uses TP/F, review uses R/N, and misses per 100 uses 100*FN/N for that stratum. TP/FP/TN/FN concern segmentation quality, not malignancy classification. Wilson intervals are unadjusted descriptive 95% intervals; no subgroup comparison or interaction test was performed. The two strata recombine exactly to the original overall counts. Development rows are retained in the machine-readable audit and are in-sample threshold-selection results.

## Main Table 2 — detection intervals for migration into main text

| Cohort | Method | Detection | Wilson 95% CI (%) |
| --- | --- | --- | --- |
| BUS-BRA internal | A | 71/93 (76.34%) | 66.77–83.83 |
| BUS-BRA internal | B | 68/93 (73.12%) | 63.32–81.08 |
| BrEaST external | A | 10/16 (62.50%) | 38.64–81.52 |
| BrEaST external | B | 13/16 (81.25%) | 56.99–93.41 |

## Checks against supplied reviewer values

All eight supplied low-quality detection counts agree with the independent calculation. Internal A benign sensitivity is 51/53=96.226415%, with Wilson interval [87.245713%,98.958971%], which rounds to [87.25%,98.96%]. Internal A malignant sensitivity is 20/40=50.000000%, with interval [35.199527%,64.800473%], which rounds to [35.20%,64.80%]. All class-specific N/F/R/TP/FP/TN/FN totals sum exactly to their pre-existing cohort totals.

## What this analysis supports

The observed internal sensitivity of A was 96.23% in benign-labelled low-quality cases and 50.00% in malignant-labelled low-quality cases. These are descriptive conditional results. For external testing, A detected 5/8 low-quality cases in each stratum; B detected 7/8 and 6/8. Each external denominator is only eight. The analysis does not establish that diagnostic class causes screening performance, does not explain a cross-dataset effect causally, and does not show that either method is generally superior. The original overall primary endpoint and all previous statistical results remain unchanged.

## Reproduction

Run `python scripts/pathology_stratification.py --repo /path/to/research --output /path/to/new/evidence` with Python and openpyxl. The script verifies official-label joins, locked rules, saved flags and recombination checks before writing `pathology_audit.json` and `pathology_stratified_metrics.csv`. Source input SHA-256 values are included in the JSON. The independent label-audit script is `scripts/pathology_label_join_check.py`.
