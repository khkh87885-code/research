# Delimiter compatibility diagnosis and prototype

The v12 Equation (3) source contains the correct opening U+0028 and closing U+0029 parentheses. There are no H/I letters substituted for those delimiters in the DOCX XML. The screenshot therefore demonstrates a rendering/import incompatibility or glyph issue, not a literal H/I typo in the scientific expression. The user has now identified WPS as the screenshot renderer. The exact WPS defect remains unproven.

The source has a native OMML `m:d` delimiter object with `begChr="("`, empty `sepChr`, `endChr=")"`, and `grow="0"`. These properties were used by the v12 generation helper. Nothing in this inspection proves the property order invalid under OOXML. A consumer-specific treatment of the custom fences, the empty separator, the no-growth flag, or inherited fonts is possible; the evidence does not distinguish them. Instead of adding further compatibility flags, the prototype removes this unnecessary abstraction for these short single-line function calls.

`literal_fence_prototype.py` replaces every `m:d` in the main manuscript, including inline math, by literal U+0028/U+0029 native math runs with explicit upright Times New Roman punctuation. Fraction, summation, and subscript objects are preserved. Main has 3 delimiter objects originally, 0 after conversion. The supplement has 2 originally and 0 after conversion. All 5 displayed equations retain native editable mathematical structures.

The optional `bind_eq3_summand()` helper also moves the full `D(P0,Pj)` function call into the summation body; the original Pandoc structure only had `D` in the summation body and kept its arguments immediately outside. This changes no mathematical definition but gives a complete structural summand.

The minimal diagnostic document `eq3_literal_no_table.docx` contains 0 layout tables, 0 delimiter objects, 1 native fraction, 1 native summation, and 3 native subscript structures. Its LibreOffice-rendered PDF and PNG show ordinary parentheses and the intended equation. No direct Microsoft Word or WPS test has been performed, and the LibreOffice result is not evidence of compatibility with those renderers.

Do not copy the minimal diagnostic prose into the manuscript. The parent is responsible for removing the manuscript equation layout tables and applying final paragraph alignment/numbering. No final manuscript files have been edited by this independent prototype.
