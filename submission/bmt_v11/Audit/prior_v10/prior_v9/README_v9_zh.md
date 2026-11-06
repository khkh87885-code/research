# BMT v9 科研图与投稿排版修订

[正式主稿 Word](BMT_main_manuscript_v9.docx) · [正式主稿 PDF 预览](BMT_main_manuscript_v9_preview.pdf) · [含图阅读版 PDF](BMT_main_manuscript_v9_illustrated_preview.pdf) · [全部新图 PDF](BMT_v9_all_figures.pdf) · [上传清单](UPLOAD_FILE_MAP.md)

本版依据用户要求重新设计全部主图及补图，并参照2026-11-06核验的BMT官方作者指南重排。科学正文、原统计结果、三张主表、19个补表面板及作者声明实质内容保留；只更新图形呈现、图注和排版。输入是已批准的v8提交材料，原目录submission/bmt_v8_final完整保留。此前作者确认记录按原适用范围保存在Audit中，没有记录一次新的v9批准。尚未执行期刊投稿。

主稿保留5幅主图和3张表，合计8项；摘要174词，参考文献15条。正式Word包含可编辑表格及末尾图注，主图应逐幅另传。含图阅读版增加五张新图板，仅用于核对和阅读，避免与正式主稿同时作为两个Main Document上传。

补充材料分两件，均小于10MB：

- [补充文字、19个可编辑表格及图S1–S5 Word](BMT_supplementary_material_v5.docx)，以及[PDF预览](BMT_supplementary_material_v5_preview.pdf)。内含S6总图注和独立文件指引。
- [补充图S6：六例逐页PDF](BMT_supplementary_Figure_S6_v5.pdf)。S6A对应A–C，S6B对应D–F；不是新增六名患者。

统计图直接读取归档CSV/JSON，采用白底、清楚的坐标和单位、真实置信区间及统一分图标注。研究流程由常规矢量图元绘制。超声图像、参考掩膜及预测轮廓来自已发布影像和保存的SAM输出，保留全视野、宽高比及原始像素，未使用生成式图像制作病例图。图5与S6采用既有六例精确检查点CPU重放，明确区别于未保存的原始CUDA掩膜；未运行新模型推理、重采样或新增实验。

BMT指南明确规定标题页、四段式摘要、未编号标题、参考文献和图表规范；未强制某种正文字体、行距、纸型或单双栏。本次选择A4单栏、25.4mm页边距、Times New Roman 12pt及1.5倍正文行距以便审阅，不能称为官方强制样式。原始Research Article Word模板二进制未取得；已核验其官方链接和内容转录，未声称复刻其Word样式。官方来源及限制见Audit/graphics_v9/official_format_requirements.md。

Figures保存12幅图的600dpi PNG及矢量PDF。可生成PNG/PDF/SVG的绘图脚本和输入hash记录保存在Analysis/graphics_v9与Audit/graphics_v9；脚本保留当前云端执行路径。Reproducibility沿用已批准分析复现入口。Audit、构建脚本、历史批准记录和阅读预览不作为公开补充材料整包上传。
