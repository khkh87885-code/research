# Minimal native display equations for v12

The prototype keeps only three main equations (Dice, risk A, risk B) and two supplementary decomposition equations (C and W). All five are single-line, editable `m:oMathPara` display objects. There are no aligned matrices, multi-row continuation formulas, formula screenshots or tab runs.

## Implemented layout

- Use standard Cambria Math for mathematical variables and Times New Roman for explicitly normal text and reference numbers. Nominal method labels A/B and cohort labels E/I are upright; patient/stratum indices remain mathematical variables.
- Center the formula in a 1-row, 3-cell, borderless layout container. The left and right columns are equally wide at 0.60 inch, so the center of the equation remains the center of the full text area. The right cell contains only the reference number, right aligned and marked `noWrap`.
- Use automatic row height, vertical centering and `cantSplit`. The central paragraph contains an actual `m:oMathPara`; it is not an inline object with tabs used to imitate display math.
- Each container is explicitly tagged with `w:tblCaption="Equation layout (n)"` and a description stating that it is not a scientific data table. Scientific-table checks must filter these containers. The main paper still has three captioned data tables, alongside its five main figures; these three formula layouts do not introduce three more scientific results tables.
- The helper itself does not require an empty paragraph before or after the container. The extra empty paragraphs in the visual prototype only separate example blocks; in the manuscript, use existing prose before/after the equation with modest paragraph spacing.

## Reusable code

`formal_equations.py` exports:

```python
set_math_font(doc)
table = display_equation(doc, latex, label, width=6.268, size=12)
# To place it after an existing paragraph:
anchor._p.addnext(table._tbl)
```

The input `doc` is a python-docx document. The helper appends a layout container and returns it; its XML can then be moved to a precise paragraph anchor. It uses Pandoc to convert a single TeX equation to native Office Math and normalizes delimiter-property order and explicit roman text.

For PDF conversion, `profile(path, size)` creates only a task-local LibreOffice Math profile. It sets BaseSize to 12 for the main paper or 11 for the supplement, with IndexSize and LimitsSize at 70 percent. This avoids the previously observed LibreOffice default of 12-point math regardless of the requested supplementary run size.

## Directly checked artifacts

- `main_formal_display.docx` and `.pdf`: three genuine display equations, no formula images, zero tab runs. All three equations fit on one demonstration page.
- `supplement_formal_display.docx` and `.pdf`: two genuine display equations, no formula images, zero tab runs. Both fit on one demonstration page.
- `main_formal_1.png` and `supplement_formal_1.png`: actual 1.8x PDF page renders, visually inspected.
- `render_validation.json`: native-object counts, document hashes, reference-number positions, font sizes, boundary checks and stated review scope.

Measured math sizes are approximately 12.0/8.4 points for main variables/scripts and 11.03/7.69 points for supplementary variables/scripts. Number cells have the matching 12/11-point text. All reference-number right edges agree within 0.5 point, no reference number wraps, and no formula/parser error glyph or out-of-page text was found.

The current environment directly tested the DOCX-to-PDF path through LibreOffice. Microsoft Word and WPS were not available for direct runtime testing. The source uses their standard native display-OMML structure and common math font, but the prototype evidence must not be described as an actual Word/WPS rendering test.
