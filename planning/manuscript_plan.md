# 论文结构与证据索引

题名为 **Transfer of fixed review thresholds for breast ultrasound segmentation quality control**。本页整理当前英文稿的论证结构和对应证据。假设、统计顺序和阈值以冻结的[实验方案](formal_experiment_protocol.md)和[阈值记录](formal_validation_threshold_lock.json)为准。

| 部分 | 内容 | 对应证据 |
| --- | --- | --- |
| 摘要与引言 | 说明超声分割复核的用途，提出固定阈值在数据集之间能否维持低质量病例检出和复核量的问题 | [研究问题和假设](formal_experiment_protocol.md) |
| 方法 | 交代患者级划分、单图选择、SAM 提示框、两种风险分、Dice 参照标准、开发集阈值与配对统计 | [病例清单](../reproducibility/manifests) · [锁定参数](formal_validation_threshold_lock.json) · [图 1](../figures/Figure_1_cohort_flow.png) · [图 2](../figures/Figure_2_SAM_architecture_preview.png) |
| 结果 | 依次呈现开发集阈值、内部和外部复核比例及检出、H1–H3 对比和敏感性分析 | [主要结果](../experiments/formal_validation_statistics.json) · [补充分析](../experiments/supplementary_validation_statistics.json) · [图 3](../figures/Figure_3_planned_contrasts.png) · [图 4](../figures/Figure_4_review_curves.png) |
| 讨论 | 解释固定阈值迁移的实际表现，讨论外部低质量病例较少和人工轮廓生成提示框的回顾性限制 | [v4 公开审阅稿](../manuscript/BMT_manuscript_v4_public.docx) · [补充材料](../manuscript/BMT_supplementary_material_v1.docx) |
| 声明与可复现性 | 汇总数据出处、脚本、锁定输入、两种复现路径及待作者确认的声明 | [数据来源](../data/README.md) · [复现说明](../reproducibility/README.md) · [声明草稿](../manuscript/BMT_declarations_draft.md) |
