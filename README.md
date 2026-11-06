# Transfer of fixed review thresholds for breast ultrasound segmentation quality control

作者：兰昊泽（Haoze Lan，第一作者兼通讯作者）、Ziyuan Zhu（第二作者）；两位作者均署名重庆医科大学人工智能医学学院。第一作者 ORCID：[0009-0008-5089-5902](https://orcid.org/0009-0008-5089-5902)。研究比较两种基于 Segment Anything Model（SAM）的复核评分，并考察在 BUS-BRA 开发集锁定的阈值在内部留出集和 BrEaST 外部队列上的表现。

| 队列 | 纳入患者 | 初始分割 Dice < 0.70 |
| --- | ---: | ---: |
| BUS-BRA 开发 | 213 | 24 |
| BUS-BRA 内部留出 | 851 | 93 |
| BrEaST 外部测试 | 252 | 16 |

每位纳入患者固定使用一张图及对应参考掩膜。正式验证共 1,103 例。40 例预实验来自开发集。评分和复核均在回顾性模拟中进行。

## 最新修订：v6 作者审阅版

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
