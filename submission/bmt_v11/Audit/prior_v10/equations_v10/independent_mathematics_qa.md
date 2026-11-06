# v10 independent mathematics and native-equation QA

Status: PASS. 83/83 checks and all26 displayed equation groups pass. Final documents are complete.

The audit first verified every mathematical definition against archived code, then independently converted the effective audited TeX and compared its semantic OfficeMath XML with the actual Word equation at each number. Font formatting and delimiter-property serialization order were excluded; operators, fractions, cases, indices, matrices and all other mathematical structure were retained.

Two issues were resolved during preparation: the Kitagawa weighted-sum identity is explicitly limited to defined stratum rates while overall rates use aggregate counts; equation2 was rewritten with equivalent delta helpers after its initial multiline-set PDF rendering failed. Both were rechecked against the final documents.

| Document | Equation | Source | Verdict |
|---|---|---|---|
| main | (1) | score_images.py:41 | PASS |
| main | (2) | score_images.py:54 | PASS |
| main | (3) | score_images.py:34 | PASS |
| main | (4) | score_images.py:116 | PASS |
| main | (5) | score_images.py:107 | PASS |
| main | (6) | score_images.py:125 | PASS |
| main | (7) | study_statistics.py:88 | PASS |
| main | (8) | budget_transfer.py:129 | PASS |
| main | (9) | study_statistics.py:94 | PASS |
| main | (10) | study_statistics.py:149 | PASS |
| main | (11) | budget_transfer.py:146 | PASS |
| main | (12) | independent_scientific_audit.py:112 | PASS |
| main | (13) | case_mix_decomposition.py:170 | PASS |
| main | (14) | case_mix_decomposition.py:180 | PASS |
| supplement | (S1) | study_statistics.py:32 | PASS |
| supplement | (S2) | study_statistics.py:57 | PASS |
| supplement | (S3) | study_statistics.py:42 | PASS |
| supplement | (S4) | study_statistics.py:49 | PASS |
| supplement | (S5) | bootstrap_stability.py:173 | PASS |
| supplement | (S6) | bootstrap_stability.py:139 | PASS |
| supplement | (S7) | bootstrap_stability.py:195 | PASS |
| supplement | (S8) | case_mix_decomposition.py:170 | PASS |
| supplement | (S9) | case_mix_decomposition.py:186 | PASS |
| supplement | (S10) | case_mix_decomposition.py:180 | PASS |
| supplement | (S11) | case_mix_decomposition.py:180 | PASS |
| supplement | (S12) | external_case_audit.py:313 | PASS |

Final native Word/PDF hashes are locked in independent_mathematics_qa.json and current_document_hashes.json. Main23 pages, illustrated28, supplement29 and S6six. All5 main mathematical pages and3 supplementary mathematical pages were inspected; equation2 contains all4 directions, and no red parser or replacement glyph remains.

No model inference, cohort resampling, or new scientific experiment was performed. Scalar algebra checks only verify the written formulas against existing source functions.
One initial issue was identified and corrected by the plan author: main Kitagawa Pc=sum(w*p) now explicitly requires all stratum rates to be defined, while aggregate overall rates are computed from summed counts.
R1 empirical-support constraint and all nominal/post-hoc/noncausal interpretation limits remain explicit in the supplement plan.
Percentile quantile braces denote the indexed collection of valid replicate statistics; repeated records and repeated statistic values are retained, as in the source implementation.
Final native Word contains 14 main and 12 supplementary display equation groups, plus inline Office Math. All26 match the effective audited TeX as semantic XML, with mathematical properties retained.
Independently viewed all5 main mathematical pages and all3 supplementary mathematical pages. Final equation2 shows all4 shift tuples; fractions, inequalities, cases, paired-correlation correction, logical-or and all Kitagawa/replay terms render without missing operators or red parser errors.
Unchanged-data checks confirm main abstract, all paragraphs from Results to document end (including declarations/references/captions), all66 main tablecells, all878 supplement tablecells, and all old supplementary prose apart from the v6 standalone-S6 file pointer.
Final PDF pages: formal main23, illustrated28, supplement29, S6six. No inference or resampling was run.
