# BMT v11 数学公式排版修订

[正式主稿 Word](BMT_main_manuscript_v11.docx) · [正式主稿 PDF](BMT_main_manuscript_v11_preview.pdf) · [公式页快速预览](BMT_formula_layout_proof_v11.pdf) · [含图阅读版 PDF](BMT_main_manuscript_v11_illustrated_preview.pdf) · [全部图件 PDF](BMT_v11_all_figures.pdf) · [上传清单](UPLOAD_FILE_MAP.md)

本轮针对公式排列散乱、文字标签失去正体和实际字号不一致的问题重排。TP/FP/FN/TN等计数缩写、dev/std/fixed/CPU等文字标签以及min/max/argmin/clip/rank等运算符采用紧凑正体；数学变量保留其数学格式。长公式拆为各自完整的数学行，按实测宽度设置制表位，对齐关系号与右侧编号，并减少不必要的多行列间空白。

主稿仍有14组编号公式(1)–(14)，补充方法仍为12组(S1)–(S12)。一组可包含多行，公式行数及OMML对象数不等于组数；可见组号连续且不重复。公式仍为原生Office Math，可在文档中编辑，未转成截图。当前PDF导出按主稿数学基准12pt、补充11pt配置并核验，实际字号、分页和对齐检查见Audit/typography_v11。

本轮保留既有数学定义与统计方法，未增加公式组或新的推断。结果与讨论、三主表66个单元格、19个补表面板878个单元格、15条参考文献、作者声明实质及全部12幅科研图保持。主稿仍为5图+3表共8项、174词摘要。H1–H3原区间、H2/H3及补充比较的名义区间性质、预算/bootstrap/诊断构成分析的事后性质均保留；未运行新推理、重采样或新增实验。

正式补充材料仍为两件，均小于10MB：

- [补充方法、表格及图S1–S5 Word](BMT_supplementary_material_v7.docx)，或[PDF预览](BMT_supplementary_material_v7_preview.pdf)。内含S6总图注和文件指引。
- [六例逐页图S6 PDF](BMT_supplementary_Figure_S6_v7.pdf)。该文件与v10的S6内容逐字节相同，仅文件名及主补充文档中的指向升级；S6A为A–C，S6B为D–F。

正式Word用于Main manuscript，五主图逐幅另传；含图阅读版和图册用于核对。[9页公式预览](BMT_formula_layout_proof_v11.pdf)从主稿及补充PDF抽取有编号公式的页面，仅供快速复检，不作为投稿文件。当前环境检查覆盖DOCX原生数学结构及LibreOffice导出的PDF；未在Microsoft Word或WPS中实际运行文档，因此没有声称已验证所有跨软件排版兼容性。可结合正式PDF核对提交Word的呈现。

原v10归档完整保留。现有作者、机构及投稿事实声明沿用；尚未执行期刊系统上传或投稿。新构建与核验脚本在Analysis/typography_v11，诊断、有效公式计划、构建hash及独立检查在Audit/typography_v11。v10及此前官方证据和确认链的文本/JSON副本位于Audit/prior_v10，原始二进制资料仍在既有归档。Reproducibility、表格CSV和绘图脚本沿用。Audit、构建脚本、历史确认记录和预览不作为公开补充材料整包上传。
