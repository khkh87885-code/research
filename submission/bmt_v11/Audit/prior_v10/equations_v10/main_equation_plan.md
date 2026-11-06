# Main-manuscript equation plan for v10

This plan formalizes existing computations; it introduces no new model, experiment, inferential claim or statistical result. It replaces only 12 exact method-paragraph anchors in the approved v9 layout source. All other prose, all result paragraphs, tables, figures, captions, references and author statements are outside its edit scope.

| Equations | Scope |
| --- | --- |
| (1)–(2) | Reference box expansion, clipping and four deterministic translations |
| (3) | Dice, including the empty–empty convention |
| (4)–(5) | Raw SAM quality-head risk A and four-mask consistency risk B |
| (6) | Strict reference-Dice low-quality label |
| (7)–(8) | Review flag and nearest-budget development calibration |
| (9) | Detection, simulated review and misses per 100 patients |
| (10) | Prespecified H1–H3 percentage-point contrasts |
| (11) | Nearest-integer equal-review count and rank-based flags |
| (12) | Specificity, PPV and NPV; sensitivity is detection in (9) |
| (13)–(14) | Symmetric Kitagawa accounting and common-weight standardization |

The source paragraphs selected for replacement contain 1,166 whitespace words. The replacement prose has approximately 1,211 tokens including inline-LaTeX notation; display equations are additional. Final Word/body counts must be measured after native-OMML rendering. This keeps prose compact while supplying the missing mathematical definitions.

## Details that must survive rendering and review

- SAM predicted IoU is the raw quality-head output; it is not empirical reference IoU and must not silently be clipped to [0,1].
- Box coordinates use the actual upper edge max foreground index + 1; clipping is separately to [0,image width] and [0,image height].
- All four perturbations count toward the mean even if clipping gives identical boxes.
- Calibration keeps cutoff ties together, includes zero reviews, and resolves target-distance ties toward fewer reviews. The ordered-pair argmin is defined lexicographically in adjacent prose.
- Equal K uses the minimum among closest integer minimizers, implementing a half-integer tie toward fewer cases. Ranking is descending risk, then the original patient-ID string.
- Quality uses strict Dice < tau; review uses risk >= cutoff.
- Detection-standardization weights are diagnostic shares among low-quality cases; review-standardization weights are diagnostic shares among all scored patients. Undefined layer rates propagate to dependent components even with a zero weight.
- Full Wilson/Newcombe equations, corrected paired association, bootstrap percentile and sign-frequency equations, empirical-support caveats, and replay absolute error are supplied by Supplementary mathematical methods. Main reference calls [11], [12] and [13] remain in their original first-appearance positions.
- Native equation blocks use fixed delimiters (no left/right) and aligned rows suitable for the 6.27-inch text width. The JSON was checked for Python escape-control corruption and for sequential labels 1–14.

## Rendering schema

`replacements[].anchor_exact` selects one existing paragraph. Replace it with its `blocks` in order. Paragraph blocks contain `$inline$` notation for native conversion; equation blocks contain un-delimited LaTeX with a separate numeric `label`. Read-only source/source-code references are included in JSON.

Final domain clarification: the weighted representation P=sum(w*p) and Kitagawa identity require all stratum rates to be defined. Overall cohort rates use aggregate numerators/denominators and can remain defined when a stratum rate is undefined. This is the only final QA amendment.
