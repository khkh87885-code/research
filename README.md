# Fixed-threshold transfer and equal-review ranking in breast ultrasound segmentation quality control

作者：兰昊泽（Haoze Lan，第一作者兼通讯作者）、Ziyuan Zhu（第二作者）；两位作者均署名重庆医科大学人工智能医学学院。第一作者 ORCID：[0009-0008-5089-5902](https://orcid.org/0009-0008-5089-5902)。研究比较两种基于 Segment Anything Model（SAM）的复核评分，并考察在 BUS-BRA 开发集锁定的阈值在内部留出集和 BrEaST 外部队列上的表现。

| 队列 | 纳入患者 | 初始分割 Dice < 0.70 |
| --- | ---: | ---: |
| BUS-BRA 开发 | 213 | 24 |
| BUS-BRA 内部留出 | 851 | 93 |
| BrEaST 外部测试 | 252 | 16 |

每位纳入患者固定使用一张图及对应参考掩膜。正式验证共 1,103 例。40 例预实验来自开发集。评分和复核均在回顾性模拟中进行。

## 当前版本：v9 科研图件与投稿排版修订

[正式主稿 Word](submission/bmt_v9/BMT_main_manuscript_v9.docx) · [正式主稿 PDF](submission/bmt_v9/BMT_main_manuscript_v9_preview.pdf) · [含图阅读 PDF](submission/bmt_v9/BMT_main_manuscript_v9_illustrated_preview.pdf) · [全部新图 PDF](submission/bmt_v9/BMT_v9_all_figures.pdf) · [补充 Word](submission/bmt_v9/BMT_supplementary_material_v5.docx) · [六例 S6 图版 PDF](submission/bmt_v9/BMT_supplementary_Figure_S6_v5.pdf) · [提交文件 ZIP](submission/BMT_v9_submission_files.zip) · [上传清单](submission/bmt_v9/UPLOAD_FILE_MAP.md)

按用户要求，v9以已批准v8为基础重绘全部5张主图和补图S1–S6，并根据BMT当前官方作者指南整理投稿排版。统计图读取归档数据；超声图、参考掩膜与已捕获的SAM预测保持真实来源和几何，不使用生成式插画。生产图提供600dpi PNG及矢量PDF；六例补图另以6页PDF逐例展示，保持可读字体和完整视野。

正式主稿为可编辑单栏Word，包含独立标题页、结构式摘要、规范标题层级、官方顺序的七项声明、参考文献、三张可编辑表和独立图注。A4、12pt正文及1.5倍行距是本次易读排版选择，官方指南未将字体、行距或单双栏规定为强制样式；未声称读取了未取得的Research Article模板Word样式。指南、模板内容转录及来源限制保存在新版Audit中。

科学正文、全部数值和研究结论保持；三张主表66个单元格、19个补表面板878个单元格及15条文献逐字保留。作者信息、伦理适用性、责任与批准提交声明沿用已确认内容；本轮新增授权是图件和排版修订，不另造作者确认记录。主图5+表3仍共8项；补充材料按每文件低于10MB分为主补充文档和S6图版两个文件。正式版、阅读副本和实际上传选择见清单。尚未执行期刊投稿。

## 历史版本：v8 作者批准提交材料

[主稿 Word](submission/bmt_v8_final/BMT_main_manuscript_v8.docx) · [主稿 PDF](submission/bmt_v8_final/BMT_main_manuscript_v8_preview.pdf) · [补充 Word](submission/bmt_v8_final/BMT_supplementary_material_v4.docx) · [官方声明](submission/bmt_v8_final/BMT_Ethical_and_Legal_Declarations_v8.docx) · [投稿信](submission/bmt_v8_final/BMT_cover_letter_v8.docx) · [提交文件 ZIP](submission/BMT_v8_submission_files.zip) · [上传清单](submission/bmt_v8_final/UPLOAD_FILE_MAP.md)

作者明确确认最终v8批准、推荐审稿人无利益冲突及论文原创、无其他期刊投稿。主稿和官方声明已填入完整批准提交句，投稿信披露GitHub公开稿，7处审稿人待确认标记及正式文件的草稿状态已清理。27项独立检查通过；科学正文、所有数值、19个图件及11个嵌入媒体均保持。期刊投稿尚未执行。

提交ZIP仅包括论文上传所需文稿、主图及具名CSV，不含内部Audit/历史记录；完整溯源见bmt_v8_final目录。此前各审阅版本保留，下方旧版“待确认”描述属于批准前历史，当前以本节和[最终状态](submission/bmt_v8_final/BMT_pre_submission_final_status_zh.md)为准。

## v8 作者审阅记录（批准前）

[主稿 Word](submission/bmt_v8/BMT_main_manuscript_v8.docx) · [主稿 PDF](submission/bmt_v8/BMT_main_manuscript_v8_preview.pdf) · [补充材料 Word](submission/bmt_v8/BMT_supplementary_material_v4.docx) · [补充 PDF](submission/bmt_v8/BMT_supplementary_material_v4_preview.pdf) · [文稿及分析 ZIP](submission/BMT_documents_and_analysis_v8.zip) · [生产图 ZIP](submission/BMT_production_figures_v8.zip) · [修订说明](submission/bmt_v8/BMT_revision_report_v8_zh.md)

v8围绕固定阈值迁移与等复核量排序的部署含义重写标题、摘要、引言和讨论，整合全部8预算扫描、三路线bootstrap、诊断构成标准化/分解及六例真实CPU预测轮廓。原H1–H3、三张主表与原S1–S9数字不变。主文5图+3表共8项；补表S1–S13、补图S1–S6；新增内容明确为事后分析。摘要174词，正文约3927词，15条文献。

新增表139项数值核验与独立稿件审查通过；图按出版宽重排为600dpi、文字至少7.2pt。等复核量的复核差按设计为0，不将归档条件二元标志区间当作政策差区间。作者地址邮编400016沿用确认信息。本版是新的作者审阅稿，保留v7既有批准记录，不将其表述为已重新批准v8，未执行期刊投稿。

批准前检查已补齐S7引用的CSV附件，并记录当时的三类作者事项；作者随后已明确确认，当前状态见上方批准版。

## 六例真实预测轮廓：已完成

[两页A4轮廓图](experiments/six_case_replay_v1/reports/six_case_contours_A4.pdf) · [中文核验报告](experiments/six_case_replay_v1/reports/six_case_replay_report_zh.pdf) · [逐例对照与复现](experiments/six_case_replay_v1/README.md) · [完整结果包](experiments/BMT_six_case_replay_v1.zip)

2026-11-06已取得与原SAM ViT-B检查点SHA-256完全一致的375,042,383字节权重，并实际完成六例CPU重放，保存6个NPZ内的30张预测掩膜。12个A/B复核决定与6个低质量标签全部匹配；初始参考Dice最大绝对差0.0000961064。总墙钟59.419秒，峰值RSS约3.15GiB。真实预测轮廓与独立核验均已交付，原研究评分和H1–H3保持不变；本轮CPU数组按新运行标注，不能声称为原CUDA数组的逐像素恢复。

## 历史修订：v7 作者批准归档版

[主稿 Word](submission/bmt_v7/BMT_main_manuscript_v7.docx) · [主稿 PDF 预览](submission/bmt_v7/BMT_main_manuscript_v7_preview.pdf) · [完整包 ZIP](submission/BMT_revision_review_package_v7.zip) · [补充材料](submission/bmt_v7/BMT_supplementary_material_v3.docx) · [修订与核验报告](submission/bmt_v7/BMT_revision_report.md)

v7增加事后良恶性诊断分层（S8）、全部六例外部漏检记录（S9），把检出率Wilson区间放入主表，统一百分号/补表样式，并纠正官方指南日期及至少5名审稿人的审计记录。作者页采用缙云校区地址与作者最新确认的通讯邮编400016（官方401331来源记录保留）；法定免审与人工核验由作者确认，原始官方声明表单已填入。两位作者已明确批准本版并承担全文责任，主稿无作者确认占位。

v7制作时提供了六例病例表、原图/参考辅助图和精确复跑脚本。随后已取得精确权重并完成CPU重放，真实预测图及数值对照见上述“六例真实预测轮廓”目录。原始评分、锁定阈值与预设主要比较保持不变。期刊投稿尚未执行，v7原归档文件保留制作时的审计状态。

## 云端补充验证：2026-11-06

[中文执行报告 PDF](experiments/cloud_validation_v1/reports/BMT_cloud_validation_report_zh.pdf) · [Word](experiments/cloud_validation_v1/reports/BMT_cloud_validation_report_zh.docx) · [方案、代码与完整结果](experiments/cloud_validation_v1/README.md) · [完整包 ZIP](experiments/BMT_cloud_validation_v1.zip)

已在2核CPU配额、8GiB内存的当前主机执行完整8预算扫描、3路线各10,000次患者bootstrap，以及5,000次诊断构成分解。原预设H1–H3与评分保持不变；本轮为事后探索性分析。方法比较随规则和预算变化；全开发/测试重采样下原方向严格反转出现30.94%，这是经验频率，不是总体概率或p值。诊断分解为描述性分账。未运行新模型推理、未新增独立患者。详细条件、输入哈希和固定源提交复现方法见目录README。

## 历史修订：v6 作者审阅版

[主稿 Word](submission/bmt_v6/BMT_main_manuscript_v6.docx) · [主稿 PDF 预览](submission/bmt_v6/BMT_main_manuscript_v6_preview.pdf) · [完整修订包 ZIP](submission/BMT_revision_review_package_v6.zip) · [修订文件目录](submission/bmt_v6) · [核验与修改报告](submission/bmt_v6/BMT_revision_report.md)

本次将最新 v6 修订材料归档至 `main`，包含两位作者、第一作者 ORCID、补充材料、声明审阅稿、投稿信、潜在审稿人和数值核验记录。该版本尚未提交期刊；伦理与同意适用性、最终作者批准及 AI 相关事项仍待确认。原始数据与锁定分析保持不变。

包内“本轮没有推送 GitHub”等文字记录材料制作时的历史状态；本次仓库归档以本节为准。旧稿和原始实验记录保留在原目录。

## 文件索引

| 内容 | 位置 |
| --- | --- |
| 研究问题、假设、统计计划 | [冻结时的实验方案](planning/formal_experiment_protocol.md) · [阈值锁定记录](planning/formal_validation_threshold_lock.json) · [论文结构](planning/manuscript_plan.md) |
| 原始公开影像、掩膜、标注和数据来源 | [数据说明与使用条款](data/README.md) · [BUS-BRA](data/raw/BUS-BRA) · [BrEaST](data/raw/BrEaST) · [原始病例清单](data/manifests) |
| 原始试验记录、逐例评分和统计结果 | [单例检查](experiments/results) · [40 例预实验](experiments/pilot_40) · [213 例开发](experiments/development_213) · [1,103 例验证](experiments/formal_validation) · [主要统计](experiments/formal_validation_statistics.json) · [补充统计](experiments/supplementary_validation_statistics.json) |
| 两条复现路线及复跑记录 | [可运行复现包](reproducibility/README.md) · [复现核对结果](reproducibility/verification.json) · [留档复跑记录](experiments/replication) |
| 英文论文和图表 | [v4 公开审阅稿](manuscript/BMT_manuscript_v4_public.docx) · [补充材料](manuscript/BMT_supplementary_material_v1.docx) · [声明草稿](manuscript/BMT_declarations_draft.md) · [图件与审查记录](figures) · [早期稿件](manuscript/archive) |

## 复现

从仓库根目录进入复现包，使用 Python 3.12.14 及其标准库重新计算归档评分。

~~~sh
cd reproducibility
python -B reproduce.py analyze --output replay_records
~~~

[复现说明](reproducibility/README.md)同时记录了从官方压缩包和 SAM 权重重新运行推理的方法、环境及输入校验。此前的图像复跑在 1,316 例上完成，归档核对记录列出逐例一致性。单次运行耗时单独记录。

[数据目录](data/README.md)保存了原包内的原始文件及精确下载版本。图像评分入口按原包字节计算校验值，需使用来源提供的完整压缩包。experiments/ 和 figures/source/ 中的历史脚本保留了运行时路径和依赖设置，便于核查原流程。独立复现入口在 reproducibility/。

v4 为公开审阅副本，作者姓名与单位保留，联系邮箱隐去。声明中的待确认项目仍属草稿。冻结方案中的“待计算”记录当时的状态。完成后的结果在统计和复现目录。
