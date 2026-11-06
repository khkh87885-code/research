# BMT v10 可编辑数学公式修订

[正式主稿 Word](BMT_main_manuscript_v10.docx) · [正式主稿 PDF](BMT_main_manuscript_v10_preview.pdf) · [含图阅读版 PDF](BMT_main_manuscript_v10_illustrated_preview.pdf) · [全部图件 PDF](BMT_v10_all_figures.pdf) · [上传清单](UPLOAD_FILE_MAP.md)

本轮按用户要求把已有方法计算正式写成可编辑数学公式：主稿14组编号公式(1)–(14)，补充方法12组编号公式(S1)–(S12)，均为原生Office Math（OMML），不是公式截图。主稿相应改写12处方法说明，补充材料新增数学方法段落，保留原结果、表格、参考文献、作者声明和科研图。未运行新模型推理、重采样或新增实验。

主文公式覆盖提示框扩展/裁切/平移、Dice、A/B风险、低质量标签、开发阈值与等复核量排序、评价指标、预设H1–H3及Kitagawa分解/标准化。补充公式给出Wilson与独立/配对Newcombe区间、关联修正、bootstrap区间和四类经验频率、诊断分层计算与CPU重放误差，并说明零分母、未定义层率和按原患者ID字符串排序等边界。

原预设比较及其Newcombe区间保持；H2/H3与补充比较的区间仍为未经多重调整的名义区间。预算、bootstrap与诊断构成分析仍属事后描述性分析；bootstrap经验频率不表述为p值或总体概率，R1的经验支持限制保留。公式只是明确原计算，没有新增效应、患者或因果结论。

主稿保留5图+3表共8项、174词摘要和15条参考文献；三主表66个单元格和19个补表面板878个单元格逐字保留。全部12幅科研图沿用v9的600dpi PNG与矢量PDF；病例图保留真实超声像素、参考轮廓和已有CPU预测，全视野及几何关系不变。

正式补充材料仍为两件，均小于10MB：

- [补充方法、表格及图S1–S5 Word](BMT_supplementary_material_v6.docx)，或[PDF预览](BMT_supplementary_material_v6_preview.pdf)。内含S6总图注与文件指引。
- [六例逐页图S6 PDF](BMT_supplementary_Figure_S6_v6.pdf)。该PDF与v9的S6逐字节相同，仅文件名升级；S6A为A–C，S6B为D–F，六例不是新增独立患者。

正式Word用于Main manuscript，主图逐幅另传；含图阅读版与图册用于核对。原BMT格式核验、单栏布局、作者及机构事实、免审、无经费/无利益冲突、原创与无其他期刊投稿声明沿用。输入v9与此前作者确认链完整保留，历史确认记录维持其原适用范围；本轮未生成新的明确作者批准记录，也未执行期刊系统上传或投稿。

公式构建与检查脚本在Analysis/equations_v10，方案、数学和排版独立检查在Audit/equations_v10。旧官方格式证据和批准记录的文本/JSON副本在Audit/prior_v9；官方模板原始二进制及完整旧归档仍在submission/bmt_v9。Reproducibility、表格CSV和绘图脚本沿用。Audit、构建脚本、作者历史确认记录与阅读预览不作为公开补充材料整包上传。
