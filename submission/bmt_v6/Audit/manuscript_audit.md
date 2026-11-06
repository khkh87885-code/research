Author metadata update, 6 November 2026: Haoze Lan's ORCID is https://orcid.org/0009-0008-5089-5902. The user confirmed that both authors have the same affiliation: College of Artificial Intelligence Medicine, Chongqing Medical University, Chongqing, China. This ORCID is not assigned to Ziyuan Zhu. Any earlier general ORCID confirmation item below is historical; only the second author's optional ORCID remains unprovided. Scientific data and results were not changed by this update. Final signatures are in FILE_MANIFEST.json.

# Manuscript, references and figure provenance audit

Audit date: 6 November 2026. Source: `research_source/manuscript/BMT_manuscript_v4_public.docx` at repository commit `592566b4c5f39e261c676eb034139a974e9cdfd5`. The uploaded material in this chat is a requirements text, not the named `BMT_manuscript_v4(1).docx`; equivalence to that local file cannot be established. The source repository and source DOCX were not modified.

## Entire-document inventory

- Main document: 94 paragraphs (including blank figure anchors), three editable Word tables, four inline PNG figures, 12 numbered references. No tracked insertions/deletions, hidden runs, comments, or embedded OLE objects were found in the DOCX package.
- Main text from Introduction through Discussion: approximately 2,295 regex-delimited words including subheadings. Abstract: 190 words without the four labels, 194 with them. The running title contains 44 characters. These are deterministic audit counts, not a claim to Word's exact tokenization.
- Abstract contains Objectives, Methods, Results and Conclusions. Five keywords are lowercase, semicolon separated and already alphabetical: domain shift; external testing; prompt perturbation; selective prediction; vision foundation models.
- First appearances of citations are exactly 1–12 in ascending order; all 12 original references are cited and no unresolved numeric citation was found. The dataset references are separate objects from their associated data-descriptor articles, not duplicate bibliography items. Main figure captions cite the correct BrEaST dataset reference.
- Main has three tables and four figures, seven combined items. All Figures 1–4 and Tables 1–3 are cited in the body. Existing placement markers for all three tables are present. Supplementary document contains all Tables S1–S5 and Figures S1–S2 referenced by the body, with five editable tables and two inline PNGs.
- Separate figure files are all present. The unchanged main and supplementary DOCX sizes and each separate figure size are below 10 MB. The reproducibility source is a directory, not an uploaded supplementary item; any final ZIP must be checked against the actual journal's selected file route and size limit.

## Title page and declarations requiring revision

The source public copy has one author with `[Confirm any additional authors]`, withheld email, and an unfilled mailing address. The user has now supplied the second author, Ziyuan Zhu, and the same institutional affiliation, and has supplied both contact emails in chat. Those confirmed details should replace placeholders. Haoze Lan remains first/corresponding author under earlier instructions; Ziyuan Zhu should not be made a corresponding author merely because an email was supplied.

The user has subsequently confirmed: Haoze Lan undertook the principal innovative design; Ziyuan Zhu undertook code review, GitHub pushing, and content revisions; no funding and no competing interests. Do not broaden this into unconfirmed data acquisition, independent execution of calculations, final approval by both authors, or institutional ethics determination. Postal code/street address, any institutional email, ORCIDs, author accountability/final approval and the institutional ethics determination remain separate confirmations.

All four declarations paragraphs in source remain incomplete. Repository access is now verifiable, so the derived-data/code statement should cite the actual repository, preferably a fixed commit. Source materials are publicly visible, but that does not establish a new license for all derived code or a DOI that does not exist. Correct the broad AI disclosure into specific methodological/code/drafting/figure-script roles, and do not assert human independent verification beyond user-confirmed facts.

## Targeted scientific wording review

- P24 and P56 explicitly explain that the reference contour supplies the initial box. This accurately limits the study to a known-location/oracle-prompt setting. Preserve and, if desired, use the explicit phrase “reference-derived (oracle) box”; do not add a fully automated clinical-workflow claim.
- P39, P50, P53 and P56 correctly preserve the uncertainty caused by only 16 low-quality BrEaST masks. They do not claim equivalence, superior external generalization, or a robust advantage of B. Fixed-threshold B detects more, while equal-review A has the higher point estimate; preserve both findings.
- P34/P47 call the archived reruns computational reproducibility in the same computing environment. This is accurate as a description of existing records, but is not independent replication. During this revision, distinguish newly recomputed statistics from the archived raw-image rerun rather than implying new GPU inference occurred.
- P25 explicitly documents Dice(empty,empty)=1. The scientific auditor is checking the original empty-mask fields and consequences. Do not delete the convention silently or change the primary locked analysis. Add the audit findings/limitations or a separately labeled sensitivity analysis only if supported by those records.
- P30 currently defines detection, review fraction and misses/100. If the requested audit adds specificity, PPV and NPV, add their denominators and explain that a positive flag predicts low reference-mask agreement, not malignancy.
- Reference 4 supports prior prompt-response consistency and fusion. A highly relevant direct comparison by Loke et al. was absent from v4 and has now been verified from the official MICCAI page and full 11-page PDF. Add it to Introduction and/or Discussion as prior comparison of SAM/MedSAM perturbation uncertainty with predicted IoU. Do not imply this study invents prompt perturbation. Cite the official workshop open-access version; official DOI and pagination remain pending.

Suggested addition: “Loke et al. directly compared prompt-perturbation uncertainty with predicted IoU in SAM and MedSAM; most case-level differences remained unresolved after paired testing and multiplicity correction [new reference].” Suggested distinction: “Our contribution is the transfer of fixed numerical review thresholds between breast ultrasound datasets and the joint reporting of detection, review volume and misses.”

## Reference verification

All 12 original entries were checked against publisher/official archive/PubMed metadata. See `references_verified.json` and saved source excerpts for exact coverage and verified fields. No nonexistent source was identified. Corrections recommended:

1. Add the verified DOI to Newcombe's independent-proportions paper: `10.1002/(SICI)1097-0258(19980430)17:8<873::AID-SIM779>3.0.CO;2-I`.
2. Add the verified DOI to Newcombe's paired-proportions paper: `10.1002/(SICI)1097-0258(19981130)17:22<2635::AID-SIM954>3.0.CO;2-C`.
3. If normalizing author surnames, the BUS-BRA publisher recommended citation renders the third author “Coelho de Albuquerque Pereira W”; the source uses “Pereira WCA”. Both refer to the same verified person. Keep dataset creator identity consistent.
4. Do not change SAM's IEEE pagination, 3992–4003, to the separate CVF pagination 4015–4026 while retaining the IEEE DOI. Both archival records exist.
5. Scientific Agent Skills is a verified arXiv preprint; its use as workflow provenance does not establish efficacy or independent verification of this study. Retain only as relevant to the accurate disclosure, not as supporting validation.
6. Add Loke et al. using the official conference URL, with no invented DOI, month or page range. Re-number every subsequent citation and the BrEaST caption citation consistently.

Access limits are explicit: reference 3's full PubMed page could not be scraped, but canonical DOI metadata, author preprint and PubMed indexed volume/pages were checked. Reference 4's publisher preview/metadata was read, not the paywalled full article. Newcombe's paired PubMed page failed, but the publisher full page was read.

The original one-page 1999 Newcombe correction was also read from the publisher PDF. It corrects an ambiguity in independent-proportions **method 11**, not the chosen method 10. It expressly notes that paired methods 8–10 have no such ambiguity. See `newcombe_1999_correction.md` for the formulas and source. No numerical change is justified merely by the existence of that correction; the separate independent numerical audit checks the actual implementation and archive.

## Figures: measured properties and provenance

All six separate figure PNGs carry approximately 600 dpi metadata (599.9988), with width 4,133 pixels, corresponding to 175 mm. Actual text extracted from all matching PDFs uses ArialMT/Arial-BoldMT. Minimum text sizes: Figure 1, 8.50 pt; Figure 2, 6.45 pt; Figure 3, 8.55 pt; Figure 4, 8.50 pt; Figure S1, 8.05 pt; Figure S2, 8.25 pt. Uppercase panel labels and standalone captions are present. Figure titles and explanatory labels inside the graphics are not copies of the external full captions.

All four main-document embedded PNGs and both supplementary embedded PNGs have exactly the same SHA-256 as their corresponding independent figure files. Thus the separate submission files match the figures actually inspected in the source manuscript.

For Figure 2, the NPZ artifact hash matches its receipt. Its input image is exactly equal, pixel by pixel, to the official archived case001 PNG decoded and alpha-composited over black; its reference array is exactly equal to the archived tumor PNG converted to binary. The original image and reference-file hashes match the receipt. Recomputing the displayed case's Dice (0.3952017732577091) and B score (0.33613448737215834) from the stored five masks reproduces the original CSV. The source script applies a common display crop, nearest-neighbor display and deterministic mask coloring, and checks that the crop retains all reference/prediction foreground. A view of the exported Figure 2 showed readable labels and matching visible content.

The repository contains conventional matplotlib/numpy plotting and figure-capture scripts. No generative-image service call was found in those scripts. These positive checks establish data provenance for the stored illustration inputs, embedded/standalone file identity, and a conventional script rendering route. They cannot establish that no historical generative editing ever occurred outside the repository; nor do they by themselves determine whether the publisher regards AI-authored plotting scripts as prohibited AI figure generation. Describe the actual workflow and leave that policy interpretation explicit for author/editor confirmation. Do not give blanket policy-clearance language.

Machine-readable evidence: `figure_audit.json`, `embedded_figures_verified.json`, `figure2_input_provenance.json`, `docx_structure_audit.json`, `manuscript_extracted.json`, `supplement_extracted.json`, and `references_verified.json`.
