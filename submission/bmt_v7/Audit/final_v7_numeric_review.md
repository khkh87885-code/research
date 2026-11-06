# Final independent v7 numerical review

**PASS within the numerical and cross-reference scope.** The review did not modify either manuscript. The author-confirmed campus, statutory ethics exemption and completed human review, together with officially sourced address details, have been incorporated. Both authors explicitly approved submission of the final v7 manuscript and accepted full-content responsibility; no actual journal submission has been performed.

## Checked copies

- Main manuscript SHA-256: `279dd1b3692754054d1798f2f2b20715e1500f7e1415b52dc27e800c15726d3f`
- Supplementary manuscript SHA-256: `a47cbc92341784c03060ed554dfbc48c8f10f79160389c0af60d4809aae2b97d`

## Numerical findings

- Main Tables 1 and 3 and Supplementary Tables S1–S7 preserve every numerical token from the previously validated v6 copies. Percentage spacing and table styles do not alter values.
- Main Table 2: all four event fractions, review fractions, misses and misses per 100 match the audit. Newly added detection Wilson intervals were independently recalculated: internal A [66.77,83.83]%, internal B [63.32,81.08]%, external A [38.64,81.52]%, external B [56.99,93.41]%.
- Table S7: all 24 copied proportions and their Wilson intervals were also independently recalculated from confusion counts and agree.
- Table S8: all 48 cells in the eight data rows match the independently audited diagnostic-stratum records. Detection and review intervals were independently recalculated. Every stratum-specific N/F/R/TP/FP/TN/FN sum returns exactly to the original overall count.
- Table S9: all six rows and their eight copied cells match the original external scores, label, threshold flags and mean consistency. The selected set is complete for external Dice<0.70 and A flag=0: shared misses 089/175/238; B-only detections 024/105/222. The accompanying six-case CSV reproduces every original score field exactly.
- Main numerical prose, including cohort sizes, 197 biopsy/55 follow-up labels, primary estimates, subgroup counts and shared-miss Dice/consistency values, agrees with the checked tables and source evidence.

## Interpretation and cross-references

- Abstract: 178 whitespace-delimited words including Objectives/Methods/Results/Conclusions headings; below 200.
- Supplementary Tables S1–S9 first appear in increasing order in the main manuscript. Main references 1–14 first appear in increasing order and match the numbered reference list.
- Methods explicitly call the strata post hoc/exploratory, retain locked cutoffs and say no recalibration, hypothesis test or interaction test was performed. The positive condition remains low-quality segmentation, not malignancy.
- BrEaST biopsy and follow-up confirmation are distinguished. Supplementary wording explicitly says the labels are not uniformly histopathologically confirmed.
- S9 states that six predicted masks were not retained, the visual aid shows only released images/manual references, and exact-checkpoint availability is required before targeted replay. Read-only image inspection confirms there is no claimed predicted contour in that aid. Case001 is correctly described as flagged by A and B and is not substituted for a target case.
- No author-confirmation placeholders remain. The explicit author approval is recorded, and the mandatory BMT full-content responsibility/submission-approval sentence is present. The prior pending approval state is superseded by the recorded author confirmation.

## Updated author confirmations and source provenance

- `author_confirmation_record.json` records the author-confirmed Jinyun campus, applicability of the statutory Article 32 ethics-review exemption and completion of human review of code, data, figures and text. These study-specific confirmations come from the user; they are not presented as independently issued institutional approvals.
- `confirmed_address_ethics_sources.json` preserves the university campus-specific 401331 source and the college footer 400016 source. The current title page follows the latest explicit author confirmation of correspondence postcode 400016 at Building 6, Lanyuan, No. 61 Daxuecheng Middle Road. Official source facts were not overwritten; the current author-selected address matches the confirmation record.
- The official National Health Commission source establishes the text and scope of Article 32. Applicability to this particular secondary study is author-confirmed. The manuscript does not invent an IRB reference number or transfer the original BrEaST approval to the present study.
- Informed consent reports the factual process: no new recruitment/contact and no additional consent obtained. It does not convert an ethics-review exemption into an invented IRB waiver of consent.
- Methods and acknowledgments now state the completed human review. They candidly state that a precise underlying Codex model identifier was unavailable in archived study records; this is an archival limitation, not a remaining request to invent a version.
- Final version approval: Both authors explicitly approved submission of the final v7 manuscript and accepted full-content responsibility; no actual journal submission has been performed. The approval record retains the user statement and is distinct from an actual submission action.
- This audit read and checked the two provenance JSON records and their agreement with the manuscript. It did not itself perform a new external retrieval of those official pages or issue a legal or institutional ethics determination.

## Limits

No model inference was performed in this review. The original unchanged main/supplementary numerical analyses were not rerun. Their final table copies were checked against the previously validated baseline; new copied CIs, diagnostic strata and six-case records were checked against their existing independent audits and direct source scores. This review finds no numerical discrepancy requiring a manuscript edit.
