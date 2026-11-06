# Final independent delivery QA

Reviewed 6 November 2026. **No remaining scientific-result or figure-readability blocker identified.** This is QA of the three score-based supplemental experiments, not a claim that the manuscript is ready for journal submission. The reviewer changed neither the scientific scripts nor the original figures.

## Results and interpretation

- **Budget transfer:** all eight frozen targets, 5/10/15/20/25/30/40/50%, are present for both methods and both test policies. The report presents the full grid and warns against selecting a favorable post hoc point. The 20% cutoffs and original H1–H3 remain preserved. “Equal review” means the same patient count in a test cohort; it is distinguished from transferring development-calibrated numerical cutoffs and from equal computation time. The internal 50% ranking budget is correctly 425 patients.
- **Bootstrap:** 10,000 draws per route, 30,000 exported records, with patient occurrences retained and A/B/quality paired. The full-resampling A detection interval is [−39.03, +11.71] pp and review interval [−12.70, −1.55] pp. The observed-direction reversal fraction is 3094/10000 (30.94%), explicitly described as an empirical resampling frequency, not a p-value or population probability. No new patients, model inference or training are claimed. The report and figure explicitly identify the zero-observed-A-only support constraint: fixed-cutoff empirical resampling cannot create that absent discordant outcome. Its [0, +40] pp interval does not replace the original paired Newcombe [−4.28, +40.04] pp interval or establish superiority/noninferiority/equivalence. The calibration-only equal-top50 contrast correctly stays −6.25 pp.
- **Diagnostic composition:** the report uses dataset-reported benign/malignant classification, detection weights among low-quality cases and review weights among all cases. Composition plus within-stratum terms equal the observed E-minus-I difference; the standardized difference equals the within-stratum term. For A detection, −1.62 and −12.23 pp sum to −13.84 pp after rounding. The description is explicitly accounting rather than causal attribution or removal of device/annotation confounding. One zero external benign low-quality stratum gives 4999 valid component draws while the overall contrast retains 5000; this distinction is reported.

Independent numerical checks already recorded in `reports/independent_design_review.json` cover all cutoffs, budget counts/paired intervals, decomposition points/percentiles and all 30,000 bootstrap count-derived endpoint records. Final result metadata hashes match the actual three scripts, and all module protocol hashes match the frozen plan.

## Visual QA

Created `qa/three_figures_contact_sheet.png` (1080×820 pixels), using small previews rendered from the actual PDFs. Each PDF was also rendered separately at 1600 pixels and visually inspected. The three PDFs are one-page vector documents with selectable text; titles, axes, legends, units, interval descriptions and the bootstrap empirical-support caveat are readable. No visible clipped labels, overlapping panels or missing plots were found.

| PDF | Minimum font size | Visual result |
| --- | ---: | --- |
| budget_transfer.pdf | 8 pt | Four panels, full budget grid and nominal paired-interval scope readable. |
| bootstrap_stability.pdf | 9 pt | Route/contrast labels, legends and non-p-value/support-constraint footnote readable. |
| case_mix_decomposition.pdf | 9 pt | Signed components, zero lines and descriptive/noncausal caption readable. |

The decomposition title's font-metric bounding box extends slightly above the page rectangle, but the rendered glyphs begin four pixels below the top edge and show no visible clipping. Its top margin is tight; this is a cosmetic observation, not a lost-content finding. The contact sheet is only an overview, not a substitute for the full-size figures. No original scientific image was edited.

## Reproduction interface and new-clone notes

All three `--help` commands exit successfully in the current environment. All support explicit source/output/protocol paths. Bootstrap uses `--repo`, `--output`, `--plan`; budget and composition use `--source-root`, `--output-root`, `--protocol`.

The following usability conditions should be included in the delivery README:

1. **Pin the source snapshot.** All three scripts require the input Git checkout HEAD to be `f9cfdc49b6e6a9e037443f6ce077006bc9377960`. A fresh clone of a later main branch will intentionally fail that check. Create a separate detached worktree/checkout of that commit for source inputs, and run the delivered experiment scripts against it.
2. **Pass paths explicitly.** `budget_transfer.py` still defaults `--source-root` to `/workspace/research_source`; that default is environment-specific. It also looks for `protocol/analysis_plan.json` below the selected output directory unless `--protocol` is passed. A new empty output directory therefore needs an explicit protocol path. These are avoidable CLI defaults, not an immutable absolute-path dependency.
3. **Keep the protocol beside the bundle or pass it.** Bootstrap's default plan path is relative to its script's parent directory and is portable when the bundle layout is retained. Composition requires all three paths explicitly. Absolute paths inside historical provenance identify this execution and do not require editing the frozen protocol for a new source path.
4. **Dependencies and inputs.** Install the documented Python/NumPy/Matplotlib dependencies before invoking scripts; composition additionally needs openpyxl and the original clinical metadata/label-audit files. The source snapshot must retain its Git metadata and frozen relative file layout. No torch or checkpoint is needed for these three score experiments.

Example interfaces after choosing the actual pinned source, bundle and fresh output paths:

```bash
python /path/to/bundle/scripts/budget_transfer.py --source-root /path/to/pinned-source --protocol /path/to/bundle/protocol/analysis_plan.json --output-root /path/to/new-output
python /path/to/bundle/scripts/bootstrap_stability.py --repo /path/to/pinned-source --plan /path/to/bundle/protocol/analysis_plan.json --output /path/to/new-output
python /path/to/bundle/scripts/case_mix_decomposition.py --source-root /path/to/pinned-source --protocol /path/to/bundle/protocol/analysis_plan.json --output-root /path/to/new-output
```

A fresh clone/reinstallation was not executed by this QA; this is interface/source inspection plus successful local `--help` checks. The portability conditions above have been sent to the parent agent for its delivery instructions. No script changes were made.

## Integrated Chinese report

Also reviewed reports/BMT_cloud_validation_report_zh.md, .docx and .pdf after the pagination correction. The PDF has exactly six pages and no blank text page (page text lengths 878, 757, 983, 774, 895 and 1221). Key bootstrap counts/percentages/intervals, source commit, required checkpoint hash and the author-confirmed 400016 versus historical 401331 distinction are consistent across all three formats. The complete external budget table and the decomposition summary agree with the already independently checked outputs.

The integrated conclusions preserve exploratory status, the empirical-support constraint, conditional calibration-only scope, non-p-value/non-population-probability wording, the 16 independent external low-quality cases, noncausal composition accounting and the absence of new model inference. No substantive correction was identified. The report's archive/gzip description is subject to the parent's final packaging/manifest check rather than assumed verified by this content QA.
