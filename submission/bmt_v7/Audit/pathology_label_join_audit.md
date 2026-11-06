# Pathology-label source and join audit

Source commit: `9fc8f54a91216b80aba909ba6028078f7642e4a9`. All 1,316 study cases were audited read-only. No SAM inference was performed.

## Official labels and keys

- BUS-BRA labels come from `data/raw/BUS-BRA/BUSBRA/bus_data.csv`, column **Pathology**. The table has 1,875 unique image IDs and 1,064 unique patient `Case` values. Each selected `image_id` was joined to `ID`, and its integer `patient_id` was checked against `Case`. No patient has contradictory labels between image views.
- BrEaST labels come from `data/raw/BrEaST/BrEaST-Lesions-USG-clinical-data-Dec-15-2023.xlsx`, first sheet `BrEaST-Lesions-USG clinical dat`, column **Classification**. The actual identifier header is **CaseID** (the dictionary calls it `Case_ID`). The integer patient ID was joined to `CaseID`, with exact filename checks against `Image_filename` and `Mask_tumor_filename`.
- Keys retain the dataset identity. Numeric IDs coincide across datasets in 252 cases; joining on patient number alone would incorrectly mix different people.

## Coverage and diagnostics

| Cohort | Cases | Benign | Malignant | Missing/nonbinary labels | Label conflicts | Unmatched score/manifest rows |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| development | 213 | 145 | 68 | 0 | 0 | 0 |
| internal_holdout | 851 | 577 | 274 | 0 | 0 | 0 |
| external_test | 252 | 154 | 98 | 0 | 0 | 0 |

There are no duplicate full keys in the score or manifest files, no duplicate patients within a cohort, no missing official-source matches, no score–manifest label conflicts, and no manifest–official label conflicts. BUS-BRA development and internal testing share **0 patients**, and together cover all 1,064 official BUS-BRA patients.

BrEaST cases **45, 61, 209 and 213** are labelled normal and have no main tumour mask; they are the only four such official cases and are excluded. The selected external IDs exactly equal the 252 eligible benign/malignant cases with a main mask.

The experiment copies, release copies and current v6 submission copies were compared byte-for-byte: all 10 checked score/manifest copy pairs agree.

## Wording implication

Use **dataset-reported benign/malignant classification**. Among the 252 external cases, the official workbook reports **197 confirmed by biopsy** and **55 confirmed by follow-up care**. Therefore, describing every external label as histopathologically confirmed would be inaccurate. The labels define exploratory strata only; the positive outcome remains low-quality segmentation (reference Dice < 0.70), not malignancy.

This validates label propagation against the official files available in the repository; it does not independently reassess clinical diagnoses or obtain new patient records. No source data were changed.
