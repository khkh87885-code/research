# BMT v13 WPS公式显示修订

[正式主稿 Word](BMT_main_manuscript_v13.docx) · [正式主稿 PDF](BMT_main_manuscript_v13_preview.pdf) · [含图阅读版 PDF](BMT_main_manuscript_v13_illustrated_preview.pdf) · [全部图件 PDF](BMT_v13_all_figures.pdf) · [上传清单](UPLOAD_FILE_MAP.md)

本轮处理用户WPS截图中的具体显示异常：Eq.(3)圆括号出现H/I样字形。针对该公式对象及同类结构，移除数学对象中的自动伸缩分隔符，改用原生数学文本中的普通ASCII圆括号；分式、求和和上下标仍为可编辑数学结构。五个公式布局表全部移除，改为普通公式段落，使用标准制表位居中公式并在右侧显示编号。

主稿仍仅保留Dice、风险A和风险B三式(1)–(3)，补充仍为Kitagawa的C和W两式(S1)–(S2)。本轮直接以v12为源，仅修公式对象和承载布局；方法文字、结果、讨论、15条参考文献、作者声明实质与12幅科研图保留。主稿有3张数据表66个单元格，补充有19个数据表面板878个单元格；文档不再含公式布局表。

本云端未实际运行WPS或Microsoft Word。当前核验覆盖DOCX原生结构、自动分隔符清除、普通括号字符、编号及本环境PDF呈现，未声称新版已经在WPS中实测通过。公式仍可编辑，PDF用于对照文档内容与版式。

原H1–H3结果与区间、H2/H3及补充比较的名义区间性质，以及预算/bootstrap/诊断构成分析的事后性质均保持。主稿仍是5图+3表共8项、174词摘要。Kitagawa两式仍用于描述性分账；未运行新推理、重采样或新增实验。

正式补充材料仍分两件，各小于10MB：

- [补充材料Word](BMT_supplementary_material_v9.docx)，或[PDF预览](BMT_supplementary_material_v9_preview.pdf)。含两式、原数据表和图S1–S5、S6图注及文件指引。
- [六例逐页图S6 PDF](BMT_supplementary_Figure_S6_v9.pdf)。与v12的S6逐字节相同，仅文件名及主补充文档中的指向升级；S6A为A–C，S6B为D–F。

正式Word用于Main manuscript，五主图逐幅另传。含图阅读版、图册及BMT_formula_layout_proof_v13.pdf（如提供）仅供复检，不作为投稿文件。现有作者、机构及投稿事实声明沿用，尚未执行期刊系统上传或最终提交。

完整v12目录和历史记录保持；本版仅附v12的文件清单、说明与上传索引，不递归复制旧审计树。新构建和检查脚本位于Analysis/wps_compatibility_v13，结构修正、当前文档hash和独立检查在Audit/wps_compatibility_v13；必要BMT/NIST/Microsoft官方来源复用于Audit/reference_sources。Reproducibility、CSV、图件与此前分析脚本沿用。Audit、构建脚本、历史索引和阅读预览不作为公开补充材料整包上传。
