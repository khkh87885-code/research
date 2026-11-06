# BMT revision and compliance report

## Decision and source

This is an author-review revision package, not a certified submission-ready manuscript. It has not been submitted, and no reviewer has been contacted. The scientific and format checks below passed, but institutional ethics/consent applicability, final author approval and substantive AI/human-review questions remain unresolved.

The uploaded attachment contained instructions only, not the binary BMT_manuscript_v4(1).docx named in those instructions. The revision therefore uses manuscript/BMT_manuscript_v4_public.docx and the archived supplementary DOCX from https://github.com/khkh87885-code/research at commit 592566b4c5f39e261c676eb034139a974e9cdfd5. Both original DOCX files were preserved separately with their SHA-256 values. No changes were pushed to the remote repository during this revision.

## Confirmed author information

First author and corresponding author: Haoze Lan; 478283902@qq.com. Second author: Ziyuan Zhu; zzy2630816871@gmail.com. Both: College of Artificial Intelligence Medicine, Chongqing Medical University, Chongqing, China. Street address and postal code remain to be confirmed; no address or ORCID was invented.

Contributions supplied by the user: Haoze Lan — research conceptualization and principal study design. Ziyuan Zhu — code review, GitHub repository uploads and manuscript revision. The user confirmed no research funding and no conflicts of interest. These confirmations do not constitute both authors’ final approval or proof of full human verification.

## Scientific and editorial changes

The Methods now explicitly identify reference-derived boxes as an oracle-localization/known-location setting. No autonomous clinical workflow or clinical validation is claimed. The Discussion preserves the external sample-size limitation and the dependence of the A/B ordering on the review rule.

The empty-mask audit was added. All 1,316 saved initial-empty flags were zero. All 5,264 initial-to-shifted consistency Dice values were positive, establishing that the shifted masks were also nonempty. The empty-empty Dice convention affected zero recorded cases, so an affected-case sensitivity analysis was unnecessary. The potential future failure mode is still described; the locked rule was not changed.

Post hoc descriptive classification counts and screening measures were added as Tables S6 and S7: TP/FP/TN/FN, sensitivity, specificity, PPV, NPV and Wilson 95% intervals. The machine-readable CSV also includes all three Dice cutoffs and misses per 100. These are segmentation-quality screening metrics, not breast-cancer diagnostic metrics.

The verified Loke et al. SAM/MedSAM comparison was added as reference 5; all subsequent original citations were renumbered. The two verified Newcombe DOIs were added. The 1999 correction concerns independent method 11 and does not change the method 10 results used here. The public study repository is cited at a fixed commit. No pending workshop DOI or page range was fabricated.

AI assistance is described in Methods, Acknowledgments and the separate declarations draft. The description includes study-design discussion, research/statistical code, plotting scripts and substantive text drafting. It is not reduced to simple language correction. Exact AI version and the extent of human review remain explicit confirmation items.

## Formatting and submission files

The revised abstract has 194 words including its four heading labels. Introduction through the end of acknowledgments/declarations has 2983 words, conservatively including confirmation placeholders; both are below the 200/6,000 limits. There are 5 lowercase alphabetical keywords, a 44-character running title, 14 references, 3 main tables and 4 main figures (7 combined).

Main tables remain editable Word tables. The main figures are supplied separately as unchanged approximately 600 dpi PNG files, with separate captions and consecutive main-text citations. The manuscript omits embedded figure previews; the supplementary DOCX retains its two figures and includes all Tables S1–S7. Each supplementary file is below 10 MB.

The independent ethical/legal declaration file reconstructs the eight fields of the verified current official BMT template. It is clearly marked as a review copy; the original publisher binary template was not downloaded. Confirmed text should be transferred to the current original template before submission. A cover letter, data/code statement, six-person reviewer shortlist and final checklist are included. Reviewer emails were read from official public professional pages, not inferred. All candidates are outside the supplied author institution; personal/collaboration conflicts still require author screening.

## What was preserved

All original patient identities, split manifests, released image/reference files, scoring records, risk formulas, exact locked cutoffs, Dice definitions and prespecified contrasts were preserved. The original 3 main tables and 5 supplementary tables have identical normalized cell contents. No unfavorable result was removed and no numerical result was made more positive.

In particular, H1 remains −13.84 percentage points (95% CI −38.85 to +7.45), H2 −6.56 (nominal CI −11.25 to −1.10), H3 +18.75 (nominal CI −4.28 to +40.04), and the equal-review B-minus-A contrast −6.25 (nominal CI −31.61 to +19.57). The 16 external low-quality cases remain the detection denominator.

The archived reproducibility folder is an unmodified provenance snapshot with its original checksums. Its historical README predates the public GitHub archive and contains an old distribution-pending sentence; README_CURRENT_ACCESS.md clarifies the present verified access route without modifying the checksum-locked source files.

## What was verified in this revision

An independently written calculation checked 78 existing result fields against original case-level records, with no differences. Locked-cutoff calibration, review fractions, H1/H2 independent Newcombe intervals, H3 paired intervals, equal-review comparisons and Dice 0.50/0.80 sensitivity results were reproduced. The paired formula was also checked against six published numerical examples.

Statistics were actually replayed twice: from archived original scores and from the previously saved raw-image rerun scores. Both passed. This revision did not rerun SAM model inference. The original study’s same-environment 1,316-image rerun remains documented prior evidence; computational reproducibility is not independent replication.

All 1,316 selected image/reference pairs were decoded, matched in size and confirmed to have nonempty references. All 504 external PNG hashes and the eight alpha-compositing cases matched the locked provenance. Source-package CRC and listed checksums passed. The checkpoint digest and original archive digests were verified as recorded identifiers, not by newly downloading checkpoint/archive binaries, which are not in the repository.

The six PNGs were matched to the original embedded figure bytes. Corresponding PDFs use Arial/Arial-Bold at minimum sizes 6.45–8.55 pt. The Figure 2 example image and reference mask match the original source pixels and its scores match saved case-level records. Reviewed scripts show conventional Matplotlib rendering and no image-generation service calls. This evidence does not establish all possible historical AI use or resolve the publisher’s interpretation of AI-assisted plotting code.

## Ethics basis and unresolved requirements

The official Chinese Measures for Ethical Review of Life Science and Medical Research Involving Human Participants (国卫科教发〔2023〕4号), Article 32, permit ethics-review exemption for qualifying legally obtained public data or anonymized-information research subject to its stated conditions. The Article 32 conditions include no harm, no sensitive personal information and no commercial interests. No funding or conflict of interest is not itself proof of every condition.

The Personal Information Protection Law distinguishes anonymization (not identifiable and not reversible) from de-identification. The source datasets’ publication descriptions do not by themselves prove the complete statutory assessment for this reuse. Exemption from ethics review is distinct from exemption from consent or from written consent. No institutional approval, exemption number, date or consent waiver was invented.

The current accessible Chongqing Medical University research-office pages provide an application route, but their general process page is dated 2017 and no dedicated public-data exemption form was found. The authors need the institution’s applicable current determination/record, and must not backdate approval. See Audit/china_ethics_basis.md for exact official links and quoted provisions.

Other requirements: complete institutional street/postcode; both authors’ final approval, accountability and publication-history/exclusive-submission confirmation; exact AI model/version and other tools; substantive human verification of the AI-assisted work; resolution of the publisher AI-policy interpretation; and conflict checks for nominated reviewers. The first author’s ORCID is confirmed as https://orcid.org/0009-0008-5089-5902. Institutional emails and the second author’s ORCID are recommended if available; missing identifiers are not invented.

## Remaining policy and scientific limits

The September 2026 publisher AI policy explicitly prohibits generative-AI creation, alteration, manipulation or enhancement of research data, figures or experimental images, and requires disclosure of substantive AI contributions. It gives no express exception for AI-authored plotting scripts later executed conventionally. The package describes the observed workflow accurately; it does not certify policy acceptance. The authors should review the actual extent of AI contribution and obtain editorial clarification where needed. No figures were regenerated or enhanced in this revision.

Scientific scope remains one frozen model, two public datasets, reference-derived localization, and only 16 external low-quality cases. There is no demonstrated reader-time saving, prospective clinical utility, equivalence or robust clinical generalization. These limitations do not invalidate the reproduced calculations, but they limit the conclusions and cannot be removed by editing.

Submission-readiness decision: NOT YET READY. Numerical consistency and the prepared formatting checks pass. Resolve the critical institutional ethics/consent, final authorship approval and AI-review/policy matters, transfer the confirmed declarations to the original official form, and then repeat the checklist before actual submission.