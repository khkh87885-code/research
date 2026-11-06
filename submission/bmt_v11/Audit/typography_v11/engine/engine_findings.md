# Native-math engine findings

No final manuscript was modified. Actual LibreOffice prototypes establish that styling and alignment import behavior, not just formula semantics or missing fonts, caused visible problems.

1. Use native normal-text math for named counts and labels. `\text{TP}` remains a single upright label; plain unmarked `TP` is two variables. `m:nor` plus alphabetic-run coalescing fixes `clip`, `argmin`, `dev`, `corr` and related words that LibreOffice italicized or spaced despite `m:sty=p`.
2. Cambria Math is a sensible DOCX portability default, but changing font names alone did not fix the LibreOffice PDF. Word and WPS were not available and are not claimed as tested.
3. LibreOffice drops matrix column alignment/gap properties, even when the OOXML `mcPr` order is normalized. Equation arrays remove the matrix gap but center rows independently. Root's proposed complete single-line math rows anchored by paragraph tabs avoids both limitations while retaining editable native expressions.
4. LibreOffice ignores 11pt math-run size and paragraph-marker size in this import route. A task-local Math StandardFormat `BaseSize=11` profile produces exactly11pt roots in PDF; `BaseSize=12` does the same for the main document. Profile example is in `lo_profile11/user/registrymodifications.xcu` and reusable writer in `normalizer_recommendation.py`.
5. ODT intermediate is possible, but modifying `BaseFontHeight` alone is insufficient because frame sizes retain the old scale. Scaling corresponding math frames by11/12 also produces10.99pt roots; the direct profile method is simpler.

Compare `roman_plain_sty.png` / `roman_nor.png` / `roman_text.png` and `old_1.png` / `roman_matrix_1.png` / `roman_eqarr_1.png`. All source DOCX files contain editable OMML, not formula images. Complete machine-readable evidence is in `engine_findings.json`.
