# v10公式排版严格复检

**结论：需要重排。** 用户反馈有可见依据；此前只核对数学语义、编号和页面边界，不能证明公式排版已经合格。

本次直接查看仓库最终版主稿第5、6、7、8、10页和补充材料第2–4页的1.8倍图，并检查PDF实际字体和DOCX XML。未修改文稿或代码。

## 已确认问题

### T01 · high · Operators and descriptive mathematical labels are italic or visibly expanded into separate letters in final PDF

位置：main p6 Eq7 dev and Eq8 argmin/lex；main p8 Eq11 min/argmin/rank and Eq12 Specificity；main p10 Eq14 std；supp p2 S2 max, S4 corr/min, S5 CI/boot；supp p3 S6-S7 fixed/equal/same/or；supp p4 S11 std and S12 CPU/archive/all/max

PDF page images show operator/label typography as italic letter sequences. Actual OOXML Specificity/argmin has m:sty=p, yet final PDF is italic, so the present style survives XML but not this renderer.

修复建议：Use explicit upright identifiers and function-name/normal-text nodes, validate actual rendering. Test m:nor plus explicit w:i=false for textual runs; do not rely on font name or m:sty=p alone.

### T02 · high · TP, FP, FN, TN are typeset as spaced italic mathematical letters rather than compact count abbreviations

位置：main p7 count-definition paragraph and Eq9；main p8 Eq12；main p10 stratum definitions；supp p4 stratum definitions

Rendered TP reads T P, and all count labels are italic; source TeX also uses plain TP/FP/FN/TN as multiple mathematical variables.

修复建议：Encode all four count identifiers as upright whole tokens, e.g. \mathrm{TP}, while retaining the same counts and formulas.

### T03 · medium · Supplementary formula base size does not match declared engine size and its surrounding prose/number

位置：supp mathematical methods pp2-4

PDF body prose is 11pt and equation numbers 11pt, while ordinary equation/inline-math letters are mostly 12pt. Scripts are mostly7.2pt and nested symbols down to about5.13pt. This is a readability/style mismatch, not a claimed BMT minimum-font violation.

修复建议：Choose and validate a consistent 11pt or12pt math base in the exported PDF; use legible script proportions and avoid unnecessary nested scripts.

### T04 · high · Long prose labels placed in math objects disrupt normal text and cause letter spacing

位置：supp p4 first paragraph: s in {benign,malignant}；supp p2/p3 descriptive superscripts boot/fixed/equal；supp p4 CPU/archive in replay definition

benign and malignant appear as large italic letter sequences in a set inside prose; similar descriptive labels become spread-out superscripts/subscripts.

修复建议：Keep long verbal definitions in ordinary prose; use short mathematical indices and compact upright labels where genuinely needed.

### T05 · medium · Dedicated math font setting is not reflected in final PDF fonts

位置：all eight audited mathematical pages

Despite DOCX mathFont and run fonts being Latin Modern Math, inspected PDF spans/fonts are LiberationSerif, OpenSymbol and NimbusRoman; no Latin Modern Math is embedded on these pages.

修复建议：For DOCX use a conventional Word math font such as Cambria Math and verify compatibility, then configure/verify a suitable available rendering font for PDF. Font fallback alone is not always wrong, but it cannot be treated as proof that desired math typography was preserved.

### T06 · medium · All displayed equations are inline oMath plus tab stops; no oMathPara is present

位置：main DOCX68 oMath and0 oMathPara；supp DOCX56 oMath and0 oMathPara

Inspected word/document.xml. The14/12 numbered groups use the same inline object type as prose, between tab runs. This is valid OOXML, but lacks a dedicated display-math container and is a compatibility/style risk.

修复建议：Prototype proper display OMML, or a robust dedicated equation layout, keeping equation numbers at the right margin. Check native Word and exported PDF rather than only object count.

### T07 · medium · Intended aligned-column justification may be lost during import due property ordering

位置：main Eq1/2/7/9/10/12/13/14 and supplementary aligned groups

Pandoc m:mcPr writes mcJc before count. Standard examples put count before mcJc. Current multiline equations show uneven left-column placement and excessive gaps, particularly Eq14/S11. This is a testable root-cause hypothesis, not established causation.

修复建议：Prototype schema-order normalization count then mcJc and confirm right/left column alignment in rendered output; alternatively use equation-array alignment at the relation sign.

### T08 · medium · Automatic stretchy delimiters are visually oversized and thin in many short inline expressions

位置：main p5 inline box coordinates and clipping ranges；main p6 a(t), indicators and Eq8 tuple；main p7/8 short argument parentheses；supp p2 Wilson-bound notation and p3 sign tuples

Short expressions show tall thin fences whose style differs from normal parentheses in surrounding text. They amplify the baseline/spacing mismatch.

修复建议：Use fixed ordinary parentheses/brackets for short inline expressions; keep stretching for genuinely tall fractions/cases only.

### T09 · medium · Long inline count formulas and multi-definition rows are too dense for smooth reading

位置：main p7 TP/FP/FN/TN definition paragraph；main Eq14 and supp S11 first row

The count paragraph contains four long math fragments with changing inline height; Eq14/S11 puts two definitions on a row then a much longer lhs on the next row.

修复建议：Use a compact separate aligned count definition or plain prose for the counts; put common weight, standardized rate and difference on three relation-aligned rows within the same equation group.

### T10 · low · Number alignment is generally sound and formulas are not currently clipped

位置：all26 numbered groups

All numbers are at the right margin; no red parser placeholders or missing perturbation direction was seen in current archived v10. Formula content is semantically intact on the reviewed pages.

修复建议：Preserve number positions and mathematical content while rebuilding typography. Do not reintroduce the already-fixed Eq2 red-placeholder issue.

## 逐式记录

|文档|公式|观察|
|---|---|---|
|main|1|Needs upright clip and consistent compact delimiter style.|
|main|2|All four directions are present, but long coordinate row/brackets are crowded; preserve full geometry.|
|main|3|Dice cases is largely readable; avoid unnecessarily tall function parentheses.|
|main|4|Simple risk equation is readable; keep method label consistently upright.|
|main|5|Risk-B expression is readable; harmonize script size and function parentheses.|
|main|6|Indicator remains plain-looking1 and fences are tall; use a consistent indicator style.|
|main|7|dev is letter-spaced/italic and a(t) fences distract.|
|main|8|argmin/lex italic rather than compact upright operator/label.|
|main|9|TP/FP/FN/TN look like multiplied separate variables; count paragraph is dense.|
|main|10|Main contrast definitions are largely readable; hypothesis labels can be standardized.|
|main|11|min,argmin,rank appear italic; nested index is tiny.|
|main|12|Specificity and abbreviations are italic and count tokens split.|
|main|13|Definitions are mathematically intact; harmonize alignment and math text spacing.|
|main|14|std is separated italic letters; row layout is uneven and crowded.|
|supplement|S1|Wilson expression readable; math base12pt differs from prose/number11pt.|
|supplement|S2|max is italic; radius function loses intended script appearance; relation alignment needs polish.|
|supplement|S3|Paired-table definitions readable; compact spacing can improve.|
|supplement|S4|corr and min appear as italic letter sequences.|
|supplement|S5|CI and boot split/italic; overly small nested labels and tall brackets.|
|supplement|S6|fixed/equal labels split/italic; many nested superscripts/subscripts are visually busy.|
|supplement|S7|or is almost concatenated to adjacent zero/contrast; same label split/italic.|
|supplement|S8|Formula readable but preceding benign/malignant math text disruptive.|
|supplement|S9|Short identity is readable.|
|supplement|S10|Components readable; normalize alignment and delimiters.|
|supplement|S11|std split/italic; separate definitions into relation-aligned rows.|
|supplement|S12|CPU/archive/all split/italic; max operator should be upright.|

## 新版验收

- Actual rendered operators min,max,argmin,rank,clip and textual labels are upright and compact.
- TP/FP/FN/TN are whole upright count identifiers.
- Main and supplementary math base sizes match the chosen document styles; scripts remain readable.
- Short inline math aligns with surrounding text and does not contain expanded word labels.
- Multiline groups align at relation signs without arbitrary column gaps.
- Equation numbers remain at the right edge, without overlap or loss of content.
- No red/error/tofu glyphs, and all brackets, signs and perturbation directions are present.
- Inspect the final DOCX with a word processor and final PDF; do not infer appearance from OMML counts alone.

## 核查限度

- This audit directly observed the final PDFs and DOCX XML; it did not observe the user’s exact Microsoft Word/WPS environment.
- The mcPr property-order explanation is a hypothesis for the rendering engine to test.
- No scientific content, data, DOCX or build scripts were edited.
