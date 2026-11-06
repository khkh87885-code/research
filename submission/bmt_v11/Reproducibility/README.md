# Reproduction package for fixed review thresholds in breast ultrasound segmentation

本包提供两条复现路线。路线一用留档的逐例评分重算结果，适合快速核查。路线二用原始超声影像和权重重新生成评分，再与留档数据逐例比较。解压后先运行下方的 Route 1，查看 `verification.json`。两条路线使用相同的病例清单、分割质量定义和锁定阈值。

## Route 1. Recompute results from archived case scores

Use Python 3.12.14 and its standard library. Run the following from the extracted `breast_ultrasound_reproduction` directory.

```sh
python -B reproduce.py analyze --output replay_records
```

Use a new output directory whose parent already exists. The analysis checks the input files against the SHA-256 values in `study_lock.json` and confirms the case IDs and cohort membership. It writes:

| Output | Contents |
| --- | --- |
| `calibration.json` | Recalculated development cutoffs, review counts and detections compared with the locked values |
| `primary.json` | Fixed-threshold results, counts and confidence intervals for the two test cohorts and the H1–H3 contrasts |
| `supplementary.json` | Dice cutoffs of 0.50 and 0.80 and an equal-review-count external comparison at 50 of 252 cases per method |
| `review_curve_counts.csv` | Count-level data for review-versus-detection curves in both test cohorts |
| `verification.json` | Comparisons with the archived calibration, primary and supplementary results |

For the review curve, the horizontal coordinate is `reviewed / scored_patients` and the vertical coordinate is `low_quality_detected / low_quality_patients`. Sort each cohort and method by descending risk score and use the string form of the case ID to break ties. The curve lists all review counts, including zero. The fixed-threshold comparison handles cutoff ties as a group.

## Route 2. Generate new scores from the original images

Use Python 3.8.20, PyTorch `2.4.1+cu118`, torchvision `0.19.1+cu118`, NumPy `1.24.4`, Pillow `10.4.0`, Git on the command path and a CUDA-enabled NVIDIA GPU. The verified run used Windows and a GeForce RTX 3060 Laptop GPU. For the CUDA 11.8 wheel setup, see the [official PyTorch 2.4.1 instructions](https://pytorch.org/get-started/previous-versions/#v241).

Obtain the archives and checkpoint from their official sources. The input directory in the example can be any location. Keep the archives intact so that their SHA-256 hashes match `study_lock.json`.

| Input | Official source |
| --- | --- |
| `BUSBRA.zip`, BUS-BRA version 1.0 | [Zenodo dataset record](https://zenodo.org/records/8231412) |
| `BrEaST-Lesions_USG-images_and_masks-Dec-15-2023.zip`, BrEaST version 1 | [TCIA collection](https://www.cancerimagingarchive.net/collection/breast-lesions-usg/) |
| SAM source at commit `dca509fe793f601edb92606367a655c15ac00fdf` | [Official SAM checkout](https://github.com/facebookresearch/segment-anything/tree/dca509fe793f601edb92606367a655c15ac00fdf) |
| `sam_vit_b_01ec64.pth` | [Official SAM ViT-B checkpoint](https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth) |

Use a clean Git checkout of SAM at the specified commit. The scoring script imports it from the supplied directory. Example commands for preparing the checkout and running the two stages follow.

```sh
git clone https://github.com/facebookresearch/segment-anything.git ./inputs/segment-anything
git -C ./inputs/segment-anything checkout dca509fe793f601edb92606367a655c15ac00fdf
```

Run the scoring command with the Python 3.8.20 inference environment active.

```sh
python -E -B reproduce.py score --busbra-archive ./inputs/BUSBRA.zip --breast-archive ./inputs/BrEaST-Lesions_USG-images_and_masks-Dec-15-2023.zip --sam-source ./inputs/segment-anything --checkpoint ./inputs/sam_vit_b_01ec64.pth --output rerun_images
```

Run the following with the Python 3.12.14 analysis environment active.

```sh
python -B reproduce.py analyze --run rerun_images --output replay_images
```

Scoring validates the archive and checkpoint digests, SAM commit, PNG pairs and recorded dimensions. It writes a fresh `scores.csv` and a `run_receipt.json` with the runtime, input checksums and cohort counts. Analysis validates the receipt and records the maximum absolute per-field differences and the number of cases with changed scores, flags or statuses. `inference_ms` is measured anew on each run and is outside the equality checks. An analysis exit code of 2 means that calibration, primary results or supplementary results differ from the reference. See the verification file for the per-case comparison.

## Study population and calculations

The three manifests fix one image and its manual reference mask per patient. BUS-BRA contributes 213 development and 851 internal holdout patients with disjoint IDs. The recorded split and per-patient image-selection seeds are 20261105 and 20261106, respectively. BrEaST contributes 252 patients with a main lesion mask. Four normal cases lack that reference, and 14 additional mask files are outside the primary reference definition. The BrEaST manifest pairs each selected `Case_ID` with the original image and main tumor mask. These scripts start from the locked manifests.

SAM uses the manual reference mask to construct a localization box for the retrospective simulation. The mask bounding box is expanded by 10% of its width or height on each side and clipped to the image. The four perturbed boxes shift left, right, up and down by 5% of the initial box width or height, followed by clipping. Each case uses one image encoding and five single-mask predictions. Images are RGB, with BrEaST transparency composited over black. `study_lock.json` lists the eight BrEaST cases whose RGB bytes change with that operation.

Method A is one minus SAM's raw predicted IoU for the initial mask. Method B is one minus the average of the four Dice scores between the initial and perturbed masks. Dice between two empty predicted masks is defined as 1 for that consistency calculation. A case is low quality when the initial mask has Dice below 0.70 against the manual mask. Each method flags a case when its risk score meets or exceeds its locked threshold.

| Method | Locked risk threshold | Reviewed during development |
| --- | ---: | ---: |
| A | 0.13705134391784668 | 43 / 213 |
| B | 0.06972856653991777 | 43 / 213 |

For each method, the calibration selects the achievable review count closest to 20% of the development cohort. All cases at a cutoff are handled together. If two counts are equally close, use the smaller one. Both test cohorts apply the saved cutoffs. The external equal-review comparison uses a fixed top 50 per method and is reported separately.

Detection is `TP / F`, where `F` is the number of low-quality cases. Review is `R / N`, where `R` is the number of flagged cases and `N` is the number of scored cases. Misses per 100 patients is `100 * (F - TP) / N`. H1 and H2 compare method A between independent cohorts. H3 compares methods B and A on the same external cases. Single proportions use Wilson intervals and contrasts use the corresponding Newcombe score intervals. H1 is the primary contrast. [Independent differences](https://pubmed.ncbi.nlm.nih.gov/9595617/) · [Paired differences](https://pubmed.ncbi.nlm.nih.gov/9839354/)

## Files and provenance

| File or directory | Role |
| --- | --- |
| `manifests/` | Locked case IDs, image and mask member names, image dimensions and BrEaST PNG SHA-256 digests |
| `records/` | Original development and validation case scores with Dice, raw IoU, both risk scores, four perturbation scores, alerts, status and timing |
| `reference/` | Archived numerical outputs with workstation-specific provenance fields omitted |
| `study_lock.json` | Dataset and model identifiers, archive and record checksums, threshold settings, case counts and runtime |
| `reproduce.py`, `score_images.py`, `study_statistics.py` | Entrypoint, original-image scoring and statistical routines |
| `review_curve_counts.csv` | Archived-score replay output underlying the review curves |
| `verification.json` | Verification records for both routes |
| `SHA256SUMS.txt` | Package file checksums |

The two image archives and the model weights are obtained separately from the linked sources. This package is prepared for local author review. The distribution method and licence for the study-derived files are pending author confirmation.

## Source citations

- Gómez-Flores W, Gregorio-Calas MJ, Pereira WCA. BUS-BRA breast ultrasound dataset, version 1.0. Zenodo, 2023. The original record identifies the rights holder and asks users to cite the associated Medical Physics paper. [Dataset DOI](https://doi.org/10.5281/zenodo.8231412) · [Medical Physics article](https://doi.org/10.1002/mp.16812)
- Pawłowska A et al. BrEaST breast ultrasound benchmark dataset, version 1. The Cancer Imaging Archive, 2024. The source reports a CC BY 4.0 licence. [Dataset DOI](https://doi.org/10.7937/9WKK-Q141) · [Scientific Data article](https://doi.org/10.1038/s41597-024-02984-z)
- Kirillov A et al. Segment Anything. ICCV, 2023. [Paper](https://arxiv.org/abs/2304.02643) · [Official SAM repository](https://github.com/facebookresearch/segment-anything)

