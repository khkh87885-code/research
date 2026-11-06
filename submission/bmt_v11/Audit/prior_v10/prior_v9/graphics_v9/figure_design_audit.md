# v8 图件来源与科研设计审计

审计日期：2026-11-06。范围：12个PNG、11个逻辑图。仅审计，不改正式图、稿件、数据或mask。

## 核心结论

现有可核查图件并非一组生成式医学插图：Figure 1为带真实病例数的流程示意；Figure 3–4与S1–S5为真实归档统计图；Figure 2为方法示意加真实超声及捕获的SAM预测；Figure 5/S6为真实超声及实际CPU重放分割结果。可以改进其形式感和一致性，但不能把“不像传统科研图”推断成“由image_gen生成”。

已在图件、实验、v8分析/审计及bmt_v8脚本证据目录的文本中搜索image_gen/imagegen/DALL·E/gpt-image/Midjourney/Stable Diffusion；未发现服务调用证据。该结论限于可查记录，不能证明历史上从未调用过外部服务。

已看过[12图contact sheet](/workspace/bmt_v9/qa/current_figures_contact_sheet.png)，另单独查看了Figure 2和S4高分辨率文件。原Figure 1–4/S1–S2与原figures目录对应PNG逐字节相同；11条新图数据/数组源hash与v8 provenance完全一致；六例npz的hash、30个mask前景像素数与原始Dice独立重算均通过。Figure 5与S6A逐像素完全相同。

## 统一重设计规格

以下是设计建议，不能代替另行核实的BMT当前官方图件规范：白底、细线、方角流程框；取消阴影/渐变/装饰性token图标；统一无衬线字体，最终尺寸目标8–9 pt数据标签；A蓝/B橙并配合线型/marker冗余编码。所有曲线、点估计、区间和病例数保持原值。照片采用真实数组及原比例，同病例比较面板使用完全相同裁剪；轮廓直接来自mask 0.5边界，不平滑、不修饰、不生成替代超声或mask，不虚构比例尺。

统计图保留可编辑源、矢量PDF/SVG及按正式尺寸导出的高分辨率提交文件。重新输出后须复核数值、原数组hash/前景计数/Dice、文字大小、裁剪一致性、黑白可读性及caption。

## 逐图审计

### Figure 1

**任务与来源类型**：Show development, internal test, external test and exclusion flow.  类型：schematic with recorded cohort counts。

**当前可读性/风格观察**：

- Scientifically legible existing flowchart; no evidence of generated image content. Rounded blue-grey cards give a presentation-template appearance.
- The external exclusion branch has the same prominence as the two analysis cohorts; box widths, body text and note compete.

**正式科研图重设计规格**：

- Redraw in vector as a restrained rectangular cohort flowchart, white fill, 0.6–0.8 pt black/grey lines; no decorative colored cards.
- Use two source columns and a consistent vertical flow. Show BrEaST 256 → excluded 4 → eligible 252 unambiguously, and BUS-BRA 1064 → development 213 / internal 851.
- Put patient n on a separate consistent text line. Put low-quality n in internal/external test boxes only.

**caption不可丢失的含义**：

- BUS-BRA 1064 patients; development 213 and internal test 851; BrEaST 256 total, four normal cases without a main lesion mask excluded, external test 252.
- One image per patient; low quality is initial-mask/reference Dice <0.70; internal F=93 and external F=16.

**可核来源**：

- `/workspace/research_source/figures/source/make_figures.py`
- `/workspace/research_source/figures/Figure_1_cohort_flow.svg`
- `/workspace/research_source/experiments/development_213/development_summary.json`
- `/workspace/research_source/experiments/replication/archived_replay/primary.json`
- `/workspace/research_source/reproducibility/manifests/breast_external.csv`

### Figure 2

**任务与来源类型**：Explain reference-informed box prompts, shared frozen SAM inference and A/B risk calculation.  类型：hybrid schematic + real BrEaST ultrasound/reference + captured SAM output masks。

**当前可读性/风格观察**：

- The ultrasound and all five masks are data-backed; the embedding stacks and model blocks are conceptual schematic symbols.
- Many nested rounded cards, tinted areas, embedding icons and small repeated labels produce an infographic appearance.
- The source minimum label is 6.45 pt at 175 mm; Figure 2 production note explicitly warns against single-column scaling.
- The original mask silhouettes are irregular because they are actual predictions. Their visual irregularity is not evidence of image generation.

**正式科研图重设计规格**：

- Use a clean three-stage engineering diagram on white, with simple rectangular model boxes and only essential arrows; no stacked embedding icons or decorative tokens.
- Keep the real case001 image and exact reference/prompt overlay. Show actual initial and four shifted mask arrays as monochrome or method-colored measured outputs at identical crop and aspect.
- Place exact score formulas in the final branch; keep evaluation/reference definition in a compact separate line. Use readable ≥8 pt labels at intended final width.
- Keep image attribution and CC BY 4.0 in the legend; distinguish schematic model modules from actual measured image/mask tiles.

**caption不可丢失的含义**：

- Initial prompt derives from manual contour: 10% margin per side then clip; four shifts are 5% of the clipped width/height.
- Frozen SAM ViT-B: one image embedding, five single-mask decodes, no fine tuning implied.
- A=1−initial predicted IoU; B=1−mean Dice(initial vs each shifted mask); flag score ≥ locked cutoff.
- Low quality is initial/reference Dice <0.70. Shared display crop is case001; no generative replacement or mask smoothing.

**可核来源**：

- `/workspace/research_source/figures/source/draw_sam_architecture.py`
- `/workspace/research_source/figures/Figure_2_SAM_architecture_preview.svg`
- `/workspace/research_source/figures/source/example_case.npz`
- `/workspace/research_source/figures/source/example_case.json`
- `/workspace/research_source/figures/source/capture_figure_case.py`

### Figure 3

**任务与来源类型**：Show planned H1–H3 proportion differences and original 95% intervals.  类型：statistical result plot from archived patient scores。

**当前可读性/风格观察**：

- Already a conventional forest plot; no generative illustration content.
- No numerical estimate/CI column is present; substantial left label area and dark-blue heading weights make the balance uneven.
- Primary/secondary encoding by filled/open marker is subtle and not stated inside the figure.

**正式科研图重设计规格**：

- Use a compact forest plot with a left outcome/contrast column, central intervals and right numerical estimate [95% CI] column.
- Maintain one shared percentage-point axis, a thin zero reference and H1 filled versus H2/H3 open markers; add a clear marker key or explicit role labels.
- Use restrained monochrome or a single method color, equal row spacing and consistent typography.

**caption不可丢失的含义**：

- H1 A detection: −13.844086 pp, 95% CI [−38.849065,+7.448184]; H2 A review: −6.557645 pp [−11.245572,−1.098304].
- H3 external B−A detection: +18.75 pp [−4.283596,+40.038898]; original Newcombe intervals remain unchanged.
- H1/H2 external−internal; H3 paired same 16 external low-quality cases; H2/H3 intervals nominal.

**可核来源**：

- `/workspace/research_source/figures/source/make_figures.py`
- `/workspace/research_source/figures/Figure_3_planned_contrasts.svg`
- `/workspace/research_source/experiments/replication/archived_replay/primary.json`

### Figure 4

**任务与来源类型**：Compare detection versus review volume and show the policy-dependent 20% operating example.  类型：statistical rank/review curves from recorded patient-level scores。

**当前可读性/风格观察**：

- Already a faithful step-curve plot, not a generated image.
- Panel C dominates the vertical space; large bold count annotations and four-part legend compete with the two top curves.
- Method and operating-rule encodings need to be carried consistently to the supplementary figures.

**正式科研图重设计规格**：

- Keep exact step curves, full 0–100% axes and equal A/B panel dimensions. Do not smooth or interpolate the observed ranking steps.
- Use A blue solid and B orange dashed consistently, with filled circle=locked threshold and open diamond=equal review.
- Make C a compact paired-policy dot/line panel with counts and percentages aligned outside points; keep same 16-case denominator explicit.

**caption不可丢失的含义**：

- Internal N851/F93 and external N252/F16; risk descending with patient-ID tie breaking.
- External locked A reviews35/252, detects10/16; B reviews33/252, detects13/16.
- Equal-review 50/252 per score: A detects14/16 and B13/16; policies are different operating rules, not a general ranking of scores.

**可核来源**：

- `/workspace/research_source/figures/source/redraw_figures.py`
- `/workspace/research_source/figures/source/make_additional_figures.py`
- `/workspace/research_source/figures/Figure_4_review_curves.svg`
- `/workspace/research_source/experiments/formal_validation/validation_cases.csv`
- `/workspace/research_source/experiments/replication/archived_replay/review_curve_counts.csv`
- `/workspace/research_source/experiments/replication/archived_replay/primary.json`
- `/workspace/research_source/experiments/replication/archived_replay/supplementary.json`

### Figure 5

**任务与来源类型**：Illustrate the three external shared screening misses.  类型：real ultrasound/reference + actual targeted CPU SAM replay mask contours。

**当前可读性/风格观察**：

- These are genuine source ultrasound images and measured model masks, not generative medical imagery.
- Case aspect ratios make the image widths, title starts and visible anatomy areas uneven across rows.
- No figure-internal contour/box legend; the reader must consult the caption to decode green/blue/orange.
- Figure5 and FigureS6A PNGs are pixel-identical, creating visual duplication.

**正式科研图重设计规格**：

- Use a standardized clinical image plate with clear column headings, aligned case/row labels, discrete panel letters and a single contour/box key.
- Keep paired panels at exactly the same crop/zoom within each case; retain source aspect ratio and full pixel data. Use native arrays, no smoothing, retouching or invented scale bar.
- For the main figure, emphasize shared-miss interpretation with a compact data strip for CPU Dice and original A/B below-cutoff flags, using existing receipt values only.
- Distinguish main-figure focus from supplementary complete replay display while retaining all three cases and provenance.

**caption不可丢失的含义**：

- Rows case089/case175/case238; left released reference+initial reference-derived box, right actual initial CPU prediction.
- Both A/B missed these low-quality masks at original locked thresholds. CPU Dice 0.3190999051,0.0292870500,0.6812697985 (display 4 decimals).
- Original checksum-matched SAM weights/source/prompt rules; CPU arrays are new replay captures, original study scores remain Table S9.
- All six replay cases/TableS13; maximum six-case initial Dice difference9.61e−5. Do not claim original CUDA pixel identity.

**可核来源**：

- `/workspace/research_source/submission/bmt_v8_final/Analysis/build_figure5.py`
- `/workspace/research_source/submission/bmt_v8_final/Audit/figure5_provenance.json`
- `/workspace/research_source/experiments/six_case_replay_v1/predictions/targeted_rerun_receipt.json`
- `/workspace/research_source/experiments/six_case_replay_v1/predictions/case089_targeted_rerun.npz`
- `/workspace/research_source/experiments/six_case_replay_v1/predictions/case175_targeted_rerun.npz`
- `/workspace/research_source/experiments/six_case_replay_v1/predictions/case238_targeted_rerun.npz`

### Figure S1

**任务与来源类型**：Show sensitivity of the detection contrasts to low-quality Dice definition.  类型：statistical sensitivity contrasts from archived patient scores。

**当前可读性/风格观察**：

- Conventional forest plot with data-backed intervals; no generative illustration.
- A large left label gutter, per-row numerical values under intervals, and pale primary-row bands give the two panels uneven visual density.
- The x-axis uses a detection-difference wording different from Figure3 despite the same unit.

**正式科研图重设计规格**：

- Use the Figure3 forest style, aligned cutoff/denominator rows across two contrast columns, with explicit numerical estimate/CI columns.
- Keep one common x range and thin zero lines. Mark primary H1 at Dice<0.70 with a filled marker; avoid large tinted bands.
- Use consistent pp units, fonts, panel letters and confidence-interval line weight.

**caption不可丢失的含义**：

- Risk thresholds remain locked; vary only reference Dice cutoff0.50/0.70/0.80.
- Internal/external low-quality denominators53/7,93/16,183/50; A shows A external−internal; B external B−A.
- Only H1 at0.70 is the primary interval; remaining95% intervals nominal.

**可核来源**：

- `/workspace/research_source/figures/source/redraw_figures.py`
- `/workspace/research_source/figures/Figure_S1_dice_cutoff_contrasts.svg`
- `/workspace/research_source/experiments/replication/archived_replay/primary.json`
- `/workspace/research_source/experiments/replication/archived_replay/supplementary.json`

### Figure S2

**任务与来源类型**：Show overlap of A/B detection for the same 16 external low-quality masks under two review rules.  类型：paired empirical count plot from archived patient scores。

**当前可读性/风格观察**：

- Current dot table is a measured count display; not a generated illustration.
- The dot rows and separate right-count rules consume space; very pale neither dots have low contrast.
- Dots do not encode case identity or trajectories between panels, so readers should not infer dot-by-dot patient pairing.

**正式科研图重设计规格**：

- Use two aligned standard 2×2 A-flag/B-flag contingency tables, or retain dot tables with clearer black borders and all counts explicit.
- Use exactly the same category order/scale across policies; label denominator16 once per panel and total reviewed counts in headings.
- Do not invent transitions or patient identities from anonymous count dots.

**caption不可丢失的含义**：

- Locked thresholds both10/A-only0/B-only3/neither3; A35/252 and B33/252 flagged.
- Equal review top50/252 each: both12/A-only2/B-only1/neither1; same16 low-quality cases.

**可核来源**：

- `/workspace/research_source/figures/source/redraw_figures.py`
- `/workspace/research_source/figures/Figure_S2_external_paired_counts.svg`
- `/workspace/research_source/experiments/replication/archived_replay/primary.json`
- `/workspace/research_source/experiments/replication/archived_replay/supplementary.json`

### Figure S3

**任务与来源类型**：Show all eight budgets under transferred thresholds and equal-review ranking.  类型：post hoc archived quantitative budget-scan plot。

**当前可读性/风格观察**：

- A conventional data plot; no generative illustration content.
- Four series per panel and legends inside small axes increase cognitive load; D has overlapping paired error bars.
- This figure uses a different blue/orange palette and smaller typography than main Figures3/4.

**正式科研图重设计规格**：

- Use a consistent 2×2 statistical panel grid: actual review, external detection, internal detection, external B−A contrast.
- Carry score colors consistently and use solid/filled=transferred versus dashed/open=equal review; use independent cohort marker shapes where needed.
- Retain actual numerical x positions5,10,15,20,25,30,40,50; offset paired error bars only for legibility, never change endpoints.
- Use a compact shared legend and readable≥8pt labels; a thin20% reference may identify the original example without visually selecting a favorable budget.

**caption不可丢失的含义**：

- All8 budgets and both rules evaluated; no favorable-budget selection; external F16/internal F93.
- D preserves archived nominal paired Newcombe95% CIs conditional on observed calibration/rankings; no recalibration or reranking uncertainty.
- Post hoc sensitivity, TableS10. No rerun or new inference is needed to redraw.

**可核来源**：

- `/workspace/research_source/submission/bmt_v8_final/Analysis/build_supp_figures.py`
- `/workspace/research_source/experiments/cloud_validation_v1/results/budget_transfer/performance.csv`
- `/workspace/research_source/experiments/cloud_validation_v1/results/budget_transfer/paired_contrasts.csv`
- `/workspace/research_source/submission/bmt_v8_final/Analysis/table_data/S10_performance_unrounded.csv`
- `/workspace/research_source/submission/bmt_v8_final/Analysis/table_data/S10_paired_contrasts_unrounded.csv`

### Figure S4

**任务与来源类型**：Separate calibration/test-sampling sensitivity and summarize joint contrast sign patterns.  类型：post hoc archived patient-bootstrap summaries。

**当前可读性/风格观察**：

- Quantitative bootstrap results, not an image-generation artifact.
- R1/R2/R3 labels require bottom footnote decoding; multi-meaning color choices differ from method palette.
- Tiny sign-frequency segments have rotated labels; the 0.90% segment needs a leader; 7.2pt text is small at162.56mm width.
- Three dense footnote lines and a separate legend force the reader away from the data.

**正式科研图重设计规格**：

- Use explicit route names in aligned rows and compact forest panels for the four endpoints; preserve median/percentile-CI versus observed-estimate distinction.
- Replace D with a 3-route×4-pattern annotated frequency matrix or grouped table, showing all percentages including zeros at identical readable size.
- Use a simple semantic key: transferred vs equal-review markers, original observed points distinct from resampling medians. Avoid reusing method colors for unrelated categories.
- Keep a short caption caveat with full support constraint and TableS11 reference; label all results post hoc descriptive resampling.

**caption不可丢失的含义**：

- 10,000 patient-bootstrap replicates per route: test-only fixed cutoff, development-only calibration, full development+test.
- A/B show A external−internal detection/review; C external B−A transferred/equal-top50 detection; points medians and bars percentile95% intervals with original estimates separate.
- Original strict pattern fixed>0/equal<0:39.61%,90.40%,30.94%; full ties28.08%. Sign frequencies are not p-values or population probabilities.
- Fixed-test bootstrap cannot create absent A-only low-quality detection; nonnegative support does not exclude a population A advantage; retain originalH3 interval.

**可核来源**：

- `/workspace/research_source/submission/bmt_v8_final/Analysis/build_supp_figures.py`
- `/workspace/research_source/experiments/cloud_validation_v1/results/bootstrap_stability/summary.json`
- `/workspace/research_source/experiments/cloud_validation_v1/results/bootstrap_stability/iterations.csv.gz`
- `/workspace/research_source/submission/bmt_v8_final/Analysis/table_data/S11_endpoints_unrounded.csv`
- `/workspace/research_source/submission/bmt_v8_final/Analysis/table_data/S11_direction_matrix_unrounded.csv`

### Figure S5

**任务与来源类型**：Decompose external−internal differences using symmetric Kitagawa accounting.  类型：post hoc archived diagnostic-stratum accounting with patient-bootstrap CIs。

**当前可读性/风格观察**：

- Conventional empirical interval plot; no generated illustration.
- Panel A/B letters and score A/B row labels may be confused; abbreviated Composition/Within strata labels require caption.
- Panel-specific ranges are valid but should be explicit; no numerical estimate column.

**正式科研图重设计规格**：

- Use two forest panels labelled Low-quality detection and Simulated review, with score labels separated from panel letters.
- Group each score as Overall / Composition-associated / Within-stratum-rate, with exact estimate[CI] values aligned in a right column.
- Keep term-specific intervals and zero references; do not force CI components to add or imply causal attribution.

**caption不可丢失的含义**：

- Original locked cutoffs, external−internal direction; overall=compositional+within-stratum point terms.
- Nominal percentile95% intervals from5000 patient bootstrap draws; detection components4999 valid, totals/review5000.
- Detection weighting uses diagnosis shares among low-quality cases; review weighting uses all patients; within-stratum equals common-weight standardized difference.
- Descriptive accounting, not causal effects; TableS12.

**可核来源**：

- `/workspace/research_source/submission/bmt_v8_final/Analysis/build_supp_figures.py`
- `/workspace/research_source/experiments/cloud_validation_v1/results/case_mix_decomposition.json`
- `/workspace/research_source/experiments/cloud_validation_v1/results/case_mix_decomposition.csv`
- `/workspace/research_source/experiments/cloud_validation_v1/results/case_mix_decomposition_bootstrap.csv.gz`
- `/workspace/research_source/submission/bmt_v8_final/Analysis/table_data/S12_decomposition_unrounded.csv`

### Figure S6

**任务与来源类型**：Document all six external low-quality cases missed by A: three shared misses and three B-only detections.  类型：real ultrasound/reference + 30 actual targeted CPU SAM replay mask arrays across six cases。

**当前可读性/风格观察**：

- Real measured model segmentations include highly irregular/fragmented masks (especially case105). These failure patterns must be preserved.
- S6A is pixel-identical to main Figure5; title baselines and ultrasound widths vary with patient aspect ratio.
- S6B uses the same two-column layout, but visually large case105 oversegmentation lacks a nearby explanation of the B-only status.
- No internal role legend or compact risk/flag metadata strip.

**正式科研图重设计规格**：

- Keep two parts/pages if needed, with a common clinical plate layout and shared legend. Group shared misses then B-only detections explicitly.
- Use rows for patients with aligned column headings and native full image/ref+prompt/prediction; optional additional actual shifted-mask panels can document B without inventing imagery.
- Keep per-case paired crop/zoom identical, aspect ratio preserved, exact contours at0.5, no smoothing/dilation/retouching or synthetic replacement.
- Display CPU Dice and original A/B flag status from receipt; label arrays CPU replay and keep original CUDA limitation in caption.
- Use distinct supplementary views or extra measured mask information to avoid simple duplication while retaining all6 cases and the original scientific message.

**caption不可丢失的含义**：

- S6A case089/175/238 shared A/B misses; S6B case024/105/222 A-missed B-detected.
- All30 captured masks nonempty; low-quality labels and A/B review flags agree with archive.
- Same checksum-matched checkpoint/source, float32 and frozen prompt geometry; newCPU arrays, originalCUDA arrays not saved so pixel identity unverified.
- Max initialDice difference9.61e−5, max48field difference0.00143543(case105 left-shift consistency); no new independent patients; TableS13 and unroundedCSV.

**可核来源**：

- `/workspace/research_source/submission/bmt_v8_final/Analysis/build_figure_s6a.py`
- `/workspace/research_source/submission/bmt_v8_final/Analysis/build_figure_s6b.py`
- `/workspace/research_source/submission/bmt_v8_final/Audit/new_figure_provenance.json`
- `/workspace/research_source/experiments/six_case_replay_v1/predictions/targeted_rerun_receipt.json`
- `/workspace/research_source/experiments/six_case_replay_v1/predictions/case089_targeted_rerun.npz`
- `/workspace/research_source/experiments/six_case_replay_v1/predictions/case175_targeted_rerun.npz`
- `/workspace/research_source/experiments/six_case_replay_v1/predictions/case238_targeted_rerun.npz`
- `/workspace/research_source/experiments/six_case_replay_v1/predictions/case024_targeted_rerun.npz`
- `/workspace/research_source/experiments/six_case_replay_v1/predictions/case105_targeted_rerun.npz`
- `/workspace/research_source/experiments/six_case_replay_v1/predictions/case222_targeted_rerun.npz`

## 源证据及实施注意

- 详细源hash、12个PNG尺寸/元数据、实际病例数组shape/像素数/Dice、原v8 caption全文均存于配套JSON。
- 原make_figures.py/redraw_figures.py所导入的display_data.py在当前源树中未找到。重新实现时可直接读取archived_replay/primary.json、supplementary.json与patient CSV，保持分析结果不变；不要因为脚本依赖缺失而重跑或重估科学结果。
- case001源脚本要求原CUDA环境、同源提交与同checkpoint，并记录8个数值字段与归档精确相等；6例后续CPU重放来源不同，不能将其表述成原CUDA逐像素恢复。
- 本审计不改变旧v8已获批准的科学结论、作者声明或事实；不提出重复作者确认。
