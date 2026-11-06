# External missed-case audit

This is a post hoc descriptive audit of all six external low-quality cases missed by method A, not a new confirmatory comparison.

Locked thresholds (review if risk >= cutoff): A=0.13705134391784668; B=0.06972856653991777. Low quality is reference Dice <0.70.

| Group | Case | Archived pathology | Reference Dice | Risk A | A flag | Risk B | B flag |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| both_missed | case089 | malignant | 0.319057 | 0.104072 | 0 | 0.041041 | 0 |
| both_missed | case175 | benign | 0.029287 | 0.114944 | 0 | 0.020059 | 0 |
| both_missed | case238 | malignant | 0.681270 | 0.038909 | 0 | 0.005766 | 0 |
| B_only_detected | case024 | benign | 0.685173 | 0.054510 | 0 | 0.109995 | 1 |
| B_only_detected | case105 | malignant | 0.654572 | 0.102471 | 0 | 0.259671 | 1 |
| B_only_detected | case222 | benign | 0.578368 | 0.126987 | 0 | 0.201743 | 1 |

## What the archived scores establish

Both methods miss case089, case175 and case238. Their mean initial-to-shifted Dice values are 0.958959, 0.979941 and 0.994234, respectively: stable predictions can still have low agreement with the released reference. Case175 has reference Dice 0.029287 despite a predicted IoU of 0.885056. This is a confidence/stability screening miss, not evidence of an empty mask.

B additionally flags case024, case105 and case222, whose A risks stay below the locked cutoff. In case105 the left shift has Dice 0.246456 while the other three comparisons are approximately 0.90–0.91. The scores describe perturbation sensitivity; without captured predictions they do not establish a particular anatomical or contour-error cause.

The archived initial-empty flags are zero for all six. Every shifted-versus-initial Dice value is positive, which independently excludes an empty shifted prediction when the initial mask is nonempty. No empty mask is inferred from low reference Dice or low risk.

## Available image and prediction evidence

All six original PNG images and primary tumor references exist and match their frozen manifest SHA-256 values. Pathology is the original binary archived category, not a new clinical diagnosis. The stored reference is never presented as a SAM prediction.

Only figures/source/example_case.npz contains archived external predicted masks; it is case001. Its actual Dice/risk values reproduce the archive, and both A and B flag it. It cannot replace any of the requested six missed cases. No saved target predicted masks were located in the source repository.

A complete original-image/reference/initial-prediction illustration therefore needs a verified exact-model rerun. The companion rerun command captures all five actual outputs, records their arrays and environment, and compares eight numerical fields and decisions to the original scores. Until that is executed, no target prediction panel is claimed as complete.

## Commands

```bash
python external_case_audit.py audit --source /path/to/research --output /path/to/new/evidence
python external_case_audit.py rerun --source /path/to/research --output /path/to/new/rerun --sam-source /path/to/clean/segment-anything --checkpoint /path/to/sam_vit_b_01ec64.pth --device cpu
```

The rerun refuses a mismatched source commit or checkpoint digest. CPU use is a new environment, not the original RTX run. Exact matches are measured, not assumed. No original data or archived scores are overwritten.

## Resource check and final status

The readable workspace/user caches contained no checkpoint. The exact clean SAM source was obtained at resources/segment-anything. Two explicitly published GitHub checkpoint candidates returned HTTP 404; the bounded additional searches did not locate another permitted live original-PTH release asset. This is not a claim that no mirror exists anywhere. Current resources are Python 3.12.14, 2 CPU quota, 8 GiB RAM, no installed torch and no available GPU evidence. No dependencies were installed and no inference was run. See model_resource_availability.json for sources, timestamps and search limits.

A separate official-page browser API assessment found no native large-download artifact or shared-local-path transfer mechanism. Passing a 375 MB model through text/base64 output was not attempted, and no network-policy bypass was used.

The available figure, ../figures/external_six_case_source_pairs.png (also PDF), is an explicitly labelled original-image/reference-only inspection sheet. It was visually inspected. It has no model prediction panels and is not a completed original/reference/prediction comparison.

The outstanding input is the exact sam_vit_b_01ec64.pth checkpoint with SHA-256 ec2df62732614e57411cdcf32a23ffdf28910380d03139ee0f4fcbe91eb8c912. Once supplied through an allowed route, the ready script can capture the six actual predictions in a separately documented CPU environment. Six-case/30-box geometry already matches the original function exactly. Detailed commands and limitations are in ../scripts/CASE_RERUN_README.md.
