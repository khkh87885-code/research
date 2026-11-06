# Fixed design for the case-mix decomposition module

Written before executing the new decomposition. This module implements the existing `protocol/analysis_plan.json`, decomposition section, without modifying it. Source repository: `/workspace/research_source`, main commit `f9cfdc49b6e6a9e037443f6ce077006bc9377960`.

Use the 851 BUS-BRA internal and 252 BrEaST external patient records, the original locked A/B risk cutoffs, reference Dice <0.70, and dataset-reported benign/malignant classification. Rejoin scores to manifests and official metadata and check all stratum counts against `submission/bmt_v7/Audit/pathology_audit.json`. The legacy field name `pathology` does not imply that all labels are histopathologically confirmed.

For detection, each stratum numerator is flagged low-quality masks, its denominator is low-quality masks, and w is that stratum's share among all low-quality masks. For review fraction, numerator is flagged patients, denominator is all patients in that stratum, and w is the stratum's share among all patients. Compute both methods independently from the same patients.

For E-minus-I, report:

- composition-associated component C = sum_s[(w_Es-w_Is)(p_Es+p_Is)/2];
- within-stratum-rate component R = sum_s[(p_Es-p_Is)(w_Es+w_Is)/2];
- overall difference D = sum_s(w_Es*p_Es) - sum_s(w_Is*p_Is), with C+R=D;
- common weights w* = (w_E+w_I)/2, directly standardized rates sum_s(w*_s*p_Is) and sum_s(w*_s*p_Es), with their difference equal to R;
- both stratum-specific terms and numeric identity residuals.

Patient bootstrap: 5000 repetitions, NumPy PCG64 seed 20261107. For each repetition independently sample 851 internal patient indices with replacement and 252 external patient indices with replacement. Use the same sampled indices for A, B, quality, diagnosis and all outcomes. Recompute stratum denominators, weights and rates in every draw. Do not resample development or recalibrate the locked thresholds in this module. Original CSV patient order is retained and the RNG draws internal indices before external indices in each repetition.

If any stratum denominator is zero, its rate and dependent components/standardized rates are NA, even if its weight is zero. Overall cohort rates remain available if their own total denominator is positive. Do not fill undefined rates. Give the valid replicate count and percentile 2.5th–97.5th limits (NumPy linear quantiles) separately for each statistic; record missing-denominator counts. Preserve unrounded raw replicate values in CSV.

Outputs: portable Python script; JSON, summary CSV, stratum CSV and bootstrap CSV; standalone PNG/PDF plot; concise Markdown report; input SHA-256 hashes, protocol/source commit, actual computation and end-to-end runtime. Use one numerical thread on the available 2-CPU/8-GiB cloud host; no model loading, training or inference.

Interpretation: post hoc descriptive accounting, without causal attribution or percent-explained measures. Diagnostic composition and within-stratum terms cannot remove acquisition/device/annotation or other confounding. Percentile intervals describe resampling variability and do not replace the original H1–H3 Newcombe intervals or establish equivalence.
