# v12 independent concise-equation layout QA

Status: PASS. **91/91 checks passed**; final_documents_pending=false.

This review applies the journal's explicit mathematics rules: equations should be well aligned and not crowded, avoid complicated subscripts/superscripts, be editable rather than images, and be numbered consecutively when cited. NIST guidance supplies the italic-variable/upright-descriptive-label convention; Microsoft guidance supports professional editable equation objects. Sources are archived in the same evidence directory. Font size, symmetric layout containers and exact margins are implementation choices, not claimed publisher mandates.

The revised scope is independently confirmed: only three main display formulas remain (Dice, confidence riskA and prompt-disagreement riskB), plus two contextual Kitagawa components with TableS12. The long mathematical appendix and obsolete display groups/references are removed. All five formulas use true native m:oMathPara, each on one line, with generic per-image notation and no patient-index hierarchy. Mainp5 and supplementp19 were individually inspected at1.8x; the two-page proof matches those current final PDF pages exactly.

Actual PDF geometry supports the visual assessment. All five equations are centered to within0.33pt of the page center; all main numbers share right edge523.44pt and supplemental numbers545.87pt. Main base and number size is12pt; supplemental is11pt. Variables and running indices remain italic, while A/B and E/Iare upright. No formulas, brackets, signs or labels collide. The qhat punctuation line break was corrected, E/I prose labels are ordinary roman text, and fraction-rate formulas are distinguished from the percentage-point presentation in TableS12.

Three main and19supplementary scientific data tables retain all66+878cell strings. Administrative borderless equation layout containers are explicitly tagged and excluded from those scientific-table counts: Word contains6/21total table structures, of which3/2are equation layouts. They do not create new scientific data tables. Results, discussion, author/contact information, declarations,15references, figure legends and all image media remain unchanged. Non-replaced prose was independently checked against the v9 baseline. Main21pages, reading26pages, supplement25pages and S6six pages have no clipped text, empty pages or math parser placeholders; supplemental files remain below10MB. Abstract remains174words.

Scope limit: the final PDFs and Word XML were inspected. Microsoft Word and WPS were not directly run in this environment. Native editable equations and standard math-font settings are verified, without claiming direct testing of those applications.

Visual record: qa/layout_qa/visual_review.json. Reproducible independent checks: qa/layout_qa/check_layout.py. Exact final8document hashes, rule references and display measurements are in the JSON report.
