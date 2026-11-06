# Independent narrative review for BMT v8

Only this review and its companion JSON are created; the main DOCX is unchanged. Source facts were checked against v7 and the completed budget, bootstrap, Kitagawa and six-case CPU replay reports.

## Recommendation

Use the operating policy as the organizing question. A service can preserve a numerical cutoff and allow its review count to vary, or preserve its review capacity and select a fixed number of cases. The evidence shows why these require separate evaluations. The contribution is not a new uncertainty algorithm, and the complete grid does not support a general winner.

Recommended title: **Fixed-threshold transfer and equal-review ranking in breast ultrasound segmentation quality control**

Alternative: **Fixed thresholds and review budgets in breast ultrasound segmentation quality control**

Running title: **Threshold transfer and review budgets**

## Proposed structured abstract (170 words; below the confirmed 200-word limit)

**Objectives** To distinguish transfer of fixed numerical review thresholds from ranking at a fixed review count for breast ultrasound segmentation quality control.

**Methods** Frozen SAM predictions used reference-derived, known-location boxes. Confidence and prompt-disagreement thresholds targeting 20% review in 213 development patients were transferred to 851 internal and 252 external patients. Low quality was reference Dice <0.70. Equal-review ranking and a post hoc eight-budget analysis assessed policy dependence.

**Results** Confidence-based detection was 71/93 internally and 10/16 externally: −13.84 percentage points (95% confidence interval −38.85 to 7.45). Review fractions were 20.45% and 13.89%, respectively. Externally, disagreement detected 13/16 low-quality masks at its transferred cutoff versus 10/16 for confidence; at 50 reviews per method, the corresponding counts were 13/16 and 14/16. Across targets from 5% to 50%, neither score consistently detected more low-quality masks.

**Conclusions** Fixed-threshold transfer and equal-review ranking answer different deployment questions. Their method comparisons depend on the policy and budget, while external detection remains imprecise with 16 low-quality masks. Reporting detection, review fraction and misses together makes this distinction explicit.

The abstract deliberately omits the Kitagawa and replay details: they support interpretation and inspectability, while the full budget result directly determines the central claim. Bootstrap can remain in the main Results without turning the abstract into an experiment catalogue.

## Introduction: replace final paragraph

We therefore evaluated two deployment questions for segmentation quality control: what happens when a development-calibrated numerical cutoff is transferred unchanged, and how the same scores compare when a fixed number of cases can be reviewed. Using confidence and prompt-disagreement scores on identical predictions from a frozen SAM, we calibrated cutoffs to a 20% development review target in BUS-BRA and applied them to internal BUS-BRA and external BrEaST patients. The prespecified analyses examined detection of low-quality masks, review fraction and paired external detection at the locked cutoffs; equal-review ranking addressed the capacity-constrained question separately. Exploratory analyses then examined how the comparison varied across review budgets and under development and test-sample resampling. The contribution is an empirical evaluation of these distinct operating policies, rather than a new uncertainty algorithm.

## Discussion: proposed first paragraph

The choice between preserving a numerical cutoff and preserving a review count changes the question asked of a quality-control score. At the transferred cutoffs calibrated to 20% development review, prompt disagreement detected 13 of 16 low-quality external masks and confidence detected 10; when both received 50 reviews, the corresponding counts were 13 and 14. The complete eight-budget analysis showed no uniformly better score. The 20% result therefore illustrates dependence on the operating policy and budget, rather than a general advantage of either score. A ranking comparison alone does not establish how a fixed cutoff will transfer, and a transferred-cutoff comparison does not isolate performance at equal review capacity.

## Proposed conclusion

In this known-location breast ultrasound evaluation, transferring development-calibrated numerical cutoffs changed the fraction of cases flagged for review. Method comparisons depended on the operating policy and review budget, with no uniform winner across the complete budget grid. External detection remained imprecise because only 16 masks met the low-quality definition. Joint reporting of detection, review fraction and missed cases, with an explicit statement of whether the cutoff or review count is fixed, provides the practical interpretation of these results.

## Compact Results passages

### budget

Across development targets of 5%, 10%, 15%, 20%, 25%, 30%, 40% and 50%, the external B-minus-A detection difference under transferred cutoffs was positive at the first four targets, negative at 25%, 30% and 50%, and zero at 40%. Under equal-review ranking, it was positive at 5%, 10% and 15%, negative at 20%, and zero at the remaining targets. Thus, neither score consistently detected more low-quality masks, and the direction change between policies at 20% was budget-dependent.

### bootstrap

Three patient-bootstrap routes, each with 10,000 replicates, separately examined test-sample variation at fixed cutoffs, development-calibration variation with the test cohorts unchanged, and both sources together. Under joint development-and-test resampling, the original strict direction pattern, external B-minus-A detection >0 at transferred cutoffs and <0 at 50 reviews, occurred in 3,094/10,000 jointly valid replicates (30.94%); at least one contrast was zero in 28.08%. These are empirical resampling frequencies, not p-values or probabilities that either direction holds in the population. The original Newcombe intervals were retained.

### case_mix

At the locked cutoffs, the external-minus-internal difference in A's review fraction was −6.56 percentage points. Symmetric Kitagawa accounting across dataset-reported benign/malignant strata gave a +0.64-point composition-associated term and a −7.20-point within-stratum-rate term. The latter also equalled the difference after direct standardization to common diagnostic weights. These terms describe the observed mixture of rates and stratum shares; they do not attribute the difference causally to diagnostic classification.

### replay

Targeted CPU replay of the six external low-quality cases missed by A generated 30 prediction masks using the byte-identical SAM checkpoint and archived prompt rules. All quality labels and A/B review flags matched the archived records. The maximum absolute difference in initial reference Dice was 9.61 × 10−5. The replay contours provide spatial context for these six cases; all cohort analyses continue to use the original archived scores.

## One empirical-support note, next to bootstrap

At the original fixed cutoffs, the external low-quality sample contained 10 detections by both scores, zero by A alone, three by B alone and three by neither. An empirical bootstrap at those fixed cutoffs cannot generate an unobserved A-only outcome, constraining its B-minus-A contrast to be nonnegative. Its percentile interval of [0.00, 40.00] percentage points therefore does not exclude an A advantage in the population. The original paired Newcombe interval [−4.28, 40.04] percentage points remains the interval for H3.

This is specifically the fixed-cutoff test-resampling route. It must not be generalized into a claim that recalibration cannot change discordant detections. Calibration-only route 2 leaves the equal-top50 contrast at −6.25 pp by design; its 90.40% frequency conditions on the original test sample. These two qualifications belong together in one supplement note.

## Supplement wording and caption details

**bootstrap methods.** Resample patients independently within development, internal and external cohorts while keeping A, B and quality labels paired; retain repeated draws and rerank the external resample to select exactly 50 draw records when that policy is evaluated. Route 1 fixes the original cutoffs and resamples the test cohorts; route 2 resamples development and recalibrates while retaining the original test cohorts and top-50 rankings; route 3 combines both. Report 10,000 iterations per route, joint-valid denominators and zero contrasts separately.

**case mix methods.** For detection, diagnostic weights are F_s/F, the benign/malignant shares among low-quality masks; for review fraction they are N_s/N among all patients. Report the symmetric Kitagawa identity D=C+R and the direct-standardization identity. The separate decomposition bootstrap has 5,000 repetitions, not 10,000; detection components have 4,999 valid draws because one external benign low-quality stratum denominator was zero, while overall detection contrasts have 5,000.

**replay caption.** Targeted CPU replay of all six external low-quality cases missed by A. Green contours show the released reference and orange contours the newly generated initial prediction; boxes are reference-derived. The first three cases were missed by both scores and the other three were detected by B. All quality and review flags matched the archived results. The original CUDA masks were not archived, so cross-environment pixel identity could not be checked; the maximum absolute initial-reference-Dice difference was 9.61 × 10−5.

**replay precision.** The 9.61 × 10−5 figure concerns initial reference Dice only. Across all 48 numerical comparisons, the maximum absolute difference was 0.0014354348103 (case105, left-shift consistency Dice). Do not describe every score as agreeing to 10−4 or exactly reproducing. Thirty nonempty newly generated masks were saved; these are six existing patients, not 30 patients or newly independent observations.

## Integrate experiments as evidence, not a work log

| Location | Editorial action |
|---|---|
| Title / Introduction / Discussion opening / Conclusion | Organize around two operating policies; use the 20% point as a concrete example and the complete grid as its scope check. |
| Results: replace or expand Sensitivity and equal-review comparisons | Keep the locked H1–H3 estimates first, then place the complete grid after the original top-50 result. Do not create eight budget-specific claims or choose a best budget. |
| Results: one short stability paragraph; full routes in supplement | Use full resampling as the headline sensitivity result, then distinguish route 1 and route 2 in the supplement. Retain original Newcombe intervals in the primary tables. |
| Discussion: existing review-fraction / case-mix paragraph | Replace the qualitative benign/malignant account with the −6.56=+0.64−7.20 pp identity; do not create a new causal explanation section. |
| External missed-case audit + Figure 5 + Figure S3 | Use Figure 5 for the three jointly missed cases and Figure S3 for all six. Distinguish the CPU replay from the previous same-environment full-cohort reproducibility check. |
| Supplementary reproducibility details | Keep hashes, software versions, CPU runtime, seeds, tied-score sorting, valid counts, 48-field discrepancies and output paths here. These support auditability, not the scientific Results narrative. |

Use a single Methods sentence to identify all new score analyses as post hoc exploratory sensitivity, stability and descriptive-accounting analyses. Retain the original H1–H3 order and estimates. In the main text, each added analysis should answer one scientific question: does policy dependence extend beyond one budget; how sensitive is the observed pattern to calibration and sampling; how does the observed diagnostic mixture account for review-fraction differences; and what do actual missed-mask contours look like. Omit download history, environment troubleshooting and completion dates from the scientific narrative.

The approved plan uses three main tables and five main figures, reaching the combined limit of eight. Keep Figure 4 for ranking, use main Figure 5 to show the three jointly missed masks, and put all six cases in Figure S3. Place the complete budget, bootstrap and Kitagawa figures in S4–S6, respectively, with concise main-text summaries. The main shared-miss figure makes the failure mode inspectable without promoting the six selected cases to a population result. Keep full numerical grids and sign matrices in supplementary tables. Avoid adding a separate main-text subsection for every computation.

## Place qualifications once where they are needed

| Qualification | Placement |
|---|---|
| 16 external low-quality masks | State the denominator in Results, precision implication in one Limitations sentence, and briefly in abstract/conclusion. Avoid restating it after each supplemental result. |
| Fixed-cutoff empirical-support boundary | Explain once beside the bootstrap method/result or in a clearly referenced supplement note. Do not repeat it in abstract, case-mix discussion or conclusion. |
| Post hoc exploratory status | One Methods umbrella statement and clear table/figure labels cover all supplemental analyses; avoid starting every Results paragraph with defensive disclaimers. |
| Known-location reference-derived prompts | Keep explicit in Methods, abstract and Limitations; contour caption names the reference-derived boxes. Do not introduce a clinical deployment claim. |

## Suggested reviewer-response language

These are response templates for use after the corresponding manuscript edits have been applied.

**Contribution too implicit.** We have made the operating policy the organizing question of the manuscript. Transferring a development-calibrated numerical cutoff evaluates operating-point transfer; selecting the same number of high-risk cases evaluates ranking at fixed review capacity. We now report all eight target budgets, which show no uniformly better score and prevent the 20% direction change from being presented as a general method advantage. The study's contribution is this empirical distinction, not a new uncertainty algorithm.

**Stability of the 20% direction change.** We added three patient-bootstrap routes, with 10,000 replicates each, to separate development-calibration variation from test-sample variation. The original strict direction pattern occurred in 30.94% of jointly valid full-resampling replicates. We describe this as an empirical stability frequency and preserve the original Newcombe intervals; it is not a p-value or a population probability. The fixed-cutoff bootstrap's empirical-support boundary is explained alongside its results.

**Missing prediction contours.** We generated and saved actual prediction masks in a targeted CPU replay of the six audited cases using the byte-identical checkpoint and original prompt rules. All quality labels and A/B flags matched. Initial reference Dice differed by at most 9.61 × 10−5. We now provide the contours with the environment and numerical differences disclosed, retain the original scores for all cohort analyses, and do not claim pixel identity with unarchived CUDA masks.

**Case-mix interpretation.** We added descriptive two-stratum standardization and symmetric Kitagawa accounting using dataset-reported benign/malignant classifications. For A's review fraction, the observed −6.56-point difference comprises +0.64 composition-associated and −7.20 within-stratum-rate points. We describe these as algebraic accounting terms, without attributing causation or claiming that acquisition and annotation differences have been controlled.

## Claims to prevent during revision

- Do not write: B is superior at fixed thresholds; A is the better ranking method. Use observed counts and policy/budget dependence.
- Do not call 30.94% a p-value, posterior probability, replication probability, or probability of a population reversal.
- Do not call route 2's 90.40% frequency stronger general evidence; the original test patients and rankings are unchanged.
- Do not substitute bootstrap percentile intervals for the original prespecified Newcombe intervals.
- Do not report a percent explained by diagnosis or say that adjustment removed case mix/confounding.
- Do not say exact six-case numerical reproduction or bitwise/pixel-identical predictions; all flags match despite small numerical differences.
- Do not merge the older all-1,316 same-environment zero-difference rerun with the new six-case cross-environment CPU replay.
- Do not infer clinical review-time savings, inference speed ratios, new patients, independent validation, or independent human-prompt validation.

## Source-status warning

The cloud validation overview and independent resource review predate the completed CPU replay and still describe missing weights or unexecuted replay. Use the later six_case_replay report for current replay status; preserve the earlier reports as historical provenance.

## Sources reviewed

- /workspace/bmt_v8/evidence/BMT_main_manuscript_v7.txt
- /workspace/research_source/experiments/cloud_validation_v1/protocol/reviewer_report_20261106.md
- /workspace/research_source/experiments/cloud_validation_v1/reports/budget_transfer.md
- /workspace/research_source/experiments/cloud_validation_v1/reports/bootstrap_stability.md
- /workspace/research_source/experiments/cloud_validation_v1/reports/case_mix_decomposition.md
- /workspace/research_source/experiments/cloud_validation_v1/reports/independent_design_review.md
- /workspace/research_source/experiments/cloud_validation_v1/reports/BMT_cloud_validation_report_zh.md
- /workspace/research_source/experiments/six_case_replay_v1/reports/six_case_replay_report_zh.md


## Confirmed journal and figure limits

The parent verified an abstract limit of 200 words, main text limit of 6,000 words and combined main figure/table limit of eight. The proposed abstract has 170 words, including its four labels. The agreed layout is three main tables plus five main figures; Figure 5 shows the three jointly missed cases, Figure S3 all six replay cases, and S4–S6 the budget, bootstrap and Kitagawa analyses.

Suggested Figure 5 caption: Three external low-quality masks missed by both review scores. Green contours show the released reference, orange contours show the initial prediction generated in the targeted CPU replay, and blue boxes show the reference-derived initial prompts. Panel values are the archived scores used for cohort analyses. The newly generated masks provide spatial context; their quality labels and review flags matched the archive. Six-case numerical comparisons and complete replay contours are reported in the supplement.

## Verified Kitagawa reference

Kitagawa EM. Components of a difference between two rates. J Am Stat Assoc 1955;50:1168–1194. https://doi.org/10.1080/01621459.1955.10501299

The Taylor & Francis publisher page confirms the author, volume 50, issue 272, December 1955, pages 1168–1194 and this DOI in its metadata: https://www.tandfonline.com/doi/abs/10.1080/01621459.1955.10501299 . APA PsycNet corroborates the bibliographic details and instead lists the JSTOR DOI 10.2307/2281213: https://psycnet.apa.org/record/1956-06545-001 . Use the publisher DOI. Only bibliographic metadata was verified, not the full original article.
