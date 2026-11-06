# BMT v7 revision and verification report

Transfer of fixed review thresholds for breast ultrasound segmentation quality control

## Revision outcome

v7 includes the unchanged prespecified results, new post hoc diagnostic-stratum and missed-case audits, corrected official requirements, and the populated original publisher declaration form. The user confirmed statutory ethics exemption and completed human review; verified Jinyun-campus correspondence details have been filled. Main-manuscript author-confirmation placeholders remaining: 0. Both authors confirmed acceptance of responsibility and approval of the exact final manuscript for submission.

## Authors

Haoze Lan is first and corresponding author; Ziyuan Zhu is second author. Haoze Lan ORCID is https://orcid.org/0009-0008-5089-5902. Both authors use: College of Artificial Intelligence Medicine, Chongqing Medical University, Jinyun Campus, Building 6, Lanyuan, No. 61 Daxuecheng Middle Road, Shapingba District, Chongqing 401331, China The postcode 401331 is explicitly assigned to Jinyun Campus on the university admissions website; the department supplies Building 6, Lanyuan. The authors confirmed completed review of code, data, figures and text, no funding and no conflicts of interest.

## Exploratory diagnostic strata

Table S8 reports dataset-provided benign/malignant diagnostic strata with unchanged risk cutoffs and Dice < 0.70. Internal A detection is 51/53 (96.23 %; Wilson 95 % CI 87.25–98.96 %) in benign-labelled low-quality masks and 20/40 (50.00 %; 35.20–64.80 %) in malignant-labelled masks. B detects 41/53 and 27/40. Externally, A detects 5/8 in each stratum and B detects 7/8 and 6/8. All counts recombine exactly to the original totals. There are no missing/conflicting/duplicated/unmatched labels. BrEaST contains 197 biopsy-confirmed and 55 follow-up-confirmed diagnoses, so the strata are not all labelled histopathologically confirmed. No new significance or interaction test was conducted and no causal claim was added.

## Precision in the main results

Main Table 2 now includes Wilson 95 % intervals for all four detection proportions. External A is 62.50 % [38.64,81.52] and B is 81.25 % [56.99,93.41]. The external detection denominator remains 16. H1 is still −13.84 pp [−38.85,+7.45]; H2 −6.56 pp [−11.25,−1.10]; H3 +18.75 pp [−4.28,+40.04], and the equal-review contrast −6.25 pp [−31.61,+19.57]. H2/H3 intervals remain nominal. No primary endpoint, risk threshold, quality definition or unfavorable result was changed.

## Six external missed cases

Table S9 includes all A-missed low-quality external cases: 089,175,238 are missed by both scores; 024,105,222 are detected by B. Scores, flags, four prompt-consistency values, source-image/reference hashes and code-defined prompts were checked from records. Shared misses retain high mean consistency (0.9590,0.9799,0.9942) despite reference Dice (0.3191,0.0293,0.6813), providing a concrete stability-versus-agreement observation. These are outcome-defined descriptive cases, not a new estimate of population performance.

## Case-image resource limit

The accessible archive contains original images and manual references for these six cases, but not their initial predicted masks. The saved case001 prediction is detected by both methods and was not substituted. No checksum-matching checkpoint was available in this execution environment, so SAM inference was not rerun. A source/reference visual aid and targeted replay script are included under Analysis; neither claims to display missing SAM predictions. To complete the requested predicted-contour illustrations, provide the saved six-case prediction arrays or run the script with the exact checkpoint. No alternate model or synthesized predicted contour was used.

## Scientific narrative and parameters

The abstract, final introduction paragraph and conclusion now lead with fixed numerical operating-point transport and distinguish it from external equal-review ranking. The known-location setting and uncertain comparisons remain explicit. The 10 % context margin, 5 % deterministic relative shifts, 20 % review-budget scenario and operational Dice cutoff are explained. Method B adds four decodes to a reused image embedding. Existing combined timings cannot establish an A/B time ratio; no fivefold cost claim was added.

## Formatting

Revised Word prose/tables consistently use U+202F before %. S6/S7 and new S8/S9 now share the light-header, grey-grid, white-body styling of S1–S5, with consistent typography, numerical alignment and note spacing. Scientific PNG bytes are unchanged; Figure 2 is explicitly retained at approximately 175 mm full width so its minimum source label remains approximately 6.45 pt. The original clinical images were not enhanced.

## Official audit corrections

Official PDF page 1 verifies December 2024, page 4 requires at least five potential reviewers, and page 10 specifies the narrow non-breaking space. The earlier contrary audit statements were erroneous and have been corrected in current requirements, reviewer and checklist documents. Six reviewer candidates satisfy the count; author conflict checks remain. The original official declaration DOCX is 27,927 bytes, SHA-256 8facc5b46d8dc245e1814a9f749e2ddc4d84e2189b20ea9f511886c38d9ef230, and its eight fields are populated directly. It is no longer described as a reconstructed template.

## Verification scope

The revised abstract has 188 lexical words including headings (178 by whitespace tokenization). Main text through the declarations has 3468 words. There are 14 references, 3 main tables and 4 main figures; Tables S1–S9 and two supplementary figures are present. Original score-file hashes remain unchanged. This revision did not rerun SAM, acquire independent localization boxes or recruit participants.

## Before submission

The authors confirmed that the project meets Article 32 statutory-exemption conditions; this is not presented as an IRB-issued approval or waiver and no approval number was invented. Consent is reported factually: no new recruitment/contact and no additional consent obtained for public-anonymized secondary analysis. Human review is confirmed. The exact underlying Codex identifier was unavailable in retained records and is disclosed as such, with no invented version. Both authors confirmed acceptance of responsibility and approval of the exact final manuscript for submission. Before actual journal submission the corresponding author should confirm the cover letter’s originality/exclusive-consideration certification and the reviewer nominations. Missing saved predictions limit the six-case illustration, not the reproduced locked-threshold statistics. The publisher’s specific interpretation of AI-assisted plotting is not certified by this package.
