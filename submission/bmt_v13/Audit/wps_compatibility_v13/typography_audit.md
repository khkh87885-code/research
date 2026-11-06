# v13 exported-PDF typography audit

PASS:53/53checks; final_documents_pending=false. The final eight document hashes are recorded in typography_audit.json.

All five equations were individually viewed on the actual exported mainpage5 and supplementarypage19 at1.8×. Ordinary literal parentheses are recognizable in all function/group calls, including the complete D(P0,Pj) summand of Eq.(3). No H/I-like fence glyph, missing argument, red parser placeholder or overlap is visible. Fractions, sum limits and native subscripts remain legible. The five equations are centered within0.43pt of the page center; all main numbers share right edge523.39pt and supplemental numbers545.82pt, at12pt and11pt respectively. Context and pagination remain natural.

The DOCX files contain no automatic m:d delimiter objects and no equation-layout tables. They retain exactly3main and19supplementary data tables with66and878unchanged cells. All non-equation prose is exact against v12 apart from the S6version filename; image media are unchanged. Native equation labels remain(1)–(3) and(S1)–(S2), with unsplit paragraph layout and standard center/right tabs. The two-page proof matches the currently finalized main/supplement equation pages.

The known failing viewer is WPS, as identified by the user. This environment did not directly run WPS or Microsoft Word. The original source already contained correct parenthesis characters; the internal reason for that viewer's rendering anomaly is not proven. This audit verifies the simplified literal-punctuation structure and actual current LibreOffice PDF appearance, rather than claiming direct cross-viewer acceptance.

Reproducible checks:qa/check_typography.py. Final high-resolution observations:qa/typography_view/main_final.png and supp_final.png.
