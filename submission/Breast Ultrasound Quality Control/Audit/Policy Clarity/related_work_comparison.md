# Related-work evidence and safe positioning

The paper can retain references4 and5 with no invented DOI, publication pages or novelty claim. Reference4 provides important prior fixed-fraction rejection evidence; its full methods/S1 remain unavailable. Reference5 was inspected in its complete official main and supplement.

| Dimension | Kinalioglu[4] | Loke etal.[5] | Present study |
| --- | --- | --- | --- |
| Scores and model setting | SPRC-CB combines structural prompt-response probes with confidence through a balanced rank rule; main SAM, supporting MedSAM check reported in abstract. Exact checkpoint and all probe details not accessible. | PPU uses mean pairwise IoU disagreement across perturbed predictions; compares entropy, predicted IoU and dihedral TTA; SAM ViT-B, SAM ViT-L and MedSAM. | Frozen SAM ViT-B; confidence complement versus mean initial-to-four-shift Dice complement on shared initial masks. |
| Data and domain scope | Four polyp sites: Kvasir-SEG, CVC-ClinicDB, CVC-ColonDB and ETIS-Larib; preview states 150 nonempty images/site, 600 total. Publisher highlights also mention cross-modality MRI support, whose detailed design was not accessible. | Kvasir-SEG N=200, ISIC-2018 validation N=100, MSD Hippocampus N=100 representative slices; ten model/dataset/prompt cells. | Patient-level BUS-BRA development213/internal851 and BrEaST external252; one image/patient. |
| Development source and locked numerical threshold transfer | Kvasir-SEG builds rank references; pooled four-site performance and a source held-out split are reported. Transport of one development-calibrated numerical review cutoff is unknown from accessible preview; do not assert absent. | No development-calibrated review cutoff transfer is reported in retrieved complete main/supplement. Its threshold sweep changes the Dice definition of failure, which differs from a review-score cutoff. | A20% development review target selects one cutoff per score; numerical cutoffs are locked and applied unchanged internally and externally. |
| Fixed-budget selection and workload | Explicit highest-risk10% rejection with failure recovery73% vs51% for confidence; this is prior fixed-fraction budget reporting. Exact tie/count handling is unknown without full methods/S1. | Case-level evaluation reports failure AUROC and Spearman correlation. No same-patient-count referral comparison or deployment review-fraction transport is reported in retrieved main/supplement. Pixel-level precision@k and ensemble K are different quantities. | Reports detection, actual review counts/fractions and misses at transferred cutoffs, original Top50 and added descriptive equal counts33/35/50. |
| Paired comparison and uncertainty | Paired bootstrap, AUPRC differences and confidence intervals/p-values are reported in preview; cutoff recalibration/resampling procedure unknown. | Paired DeLong and per-case score-exchange permutation tests; Holm correction within metric family;2000-resample descriptive bootstrap CIs; five seed redraws assess PPU Monte Carlo noise. No development review-cutoff recalibration route reported. | Original independent/paired Newcombe contrasts remain; three10000-replicate routes separate development calibration, test sampling and both; added33/35 points descriptive without new significance tests. |
| Prompt realism and clinical validation | Abstract reports noisy-box and detector-derived-prompt checks and supporting MedSAM. Detailed construction and reader involvement unknown. | Oracle prompts plus synthetic off-centroid/loose-box regimes; paper explicitly says realistic regime is a model, not a user study. | Reference-derived known-location boxes; no independently supplied clinician or detector prompts and no measured reader-time/correction endpoint. |

## Suggested Introduction replacement

Case-level quality estimation without a new manual mask has been studied with reverse classification accuracy [3]. For promptable models, Kinalioglu fused structural responses to prompt perturbations with confidence and reported failure recovery after rejecting the highest-risk tenth of masks [4]. Loke et al. compared prompt-perturbation uncertainty with predicted IoU, entropy and test-time augmentation across SAM/MedSAM settings using paired tests and multiplicity control [5]. These studies establish relevant scoring and ranking comparisons. Here, the contribution is an operating-policy evaluation in breast ultrasound: development-calibrated numerical cutoffs are transferred unchanged to internal and external patients, then interpreted alongside rankings at the same actual review count. Joint reporting of detection, review fraction and misses distinguishes transfer of a cutoff from allocation of a specified review capacity.

## Suggested Discussion paragraph

Prior work already includes budget-constrained failure screening: Kinalioglu reported failure recovery in the highest-risk 10% [4], while Loke et al. evaluated case-level discrimination and error correlation across datasets and prompt regimes [5]. Our analysis links a development review target to the numerical cutoff deployed on another dataset and compares that operating point with the same-count ranking curves. The transferred cutoff leaves workload as an outcome; the ranking rule fixes how many patients are selected. The additional development-, test- and combined-resampling routes describe uncertainty in calibration and test sampling for this operating example. This scope supports a policy- and budget-specific interpretation of the observed detections.

## Access and locators

Reference4: https://www.sciencedirect.com/science/article/pii/S0167865526003016

Publisher article preview: abstract, highlights, introduction and truncated section snippets. Full main text and S1 were not obtained in this session. A focused open-access search did not locate a lawful complete copy; this is not an exhaustive availability claim.


Reference5: https://papers.miccai.org/miccai-2026-sat/UNSURE2026_002.html

Complete official11-page main paper and8-page supplement retrieved as text. The parser did not retain physical page delimiters; section/table locations are supplied instead of guessed page numbers.


## Interpretation boundaries

The specific breast-ultrasound workflow coupling a development-calibrated review-score cutoff, unchanged cross-dataset transfer, joint detection/workload/miss reporting, and same-actual-count rankings, with calibration/test resampling separated.

Reference4 already reports failure recovery at a fixed rejection fraction. Reference5 already directly compares perturbation uncertainty with model confidence across models/datasets and includes synthetic non-oracle prompt checks.

Avoid:

- First prompt-perturbation failure score
- First fixed-budget segmentation failure screening
- Prior work never reports workload or budgeted selection
- Reference4 lacks locked-cutoff transport or calibration uncertainty: unknown from available preview
- Our known-location setting validates independent clinician/detector prompts
- An ordering change under two operating configurations isolates the causal effect of policy alone

prior_source_0/1/2.md are local temporary publisher/full-paper retrievals and must not be copied wholesale into public GitHub or submission files. This concise report may be archived.
