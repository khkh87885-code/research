# v8 提交前独立只读检查

v8稿包仍为作者审阅版本。真正未决项为v8最终批准、审稿人关系、原创性/无同时投稿事实确认；批准后清理作者侧草稿字样。没有发现隐藏批注、修订、内容控件、隐藏文字或正文空占位。

未修改投稿源文件。位置P编号按OOXML指定部件内所有w:p顺序计数，含表格段落。

## AUTH-01 v8最终批准与模板强制批准句尚未完成

已确认批准记录明确针对v7；v8新增预算、bootstrap、诊断分解及CPU轮廓。当前正文与表格仅保留承担责任句；原始官方模板P50要求mandatory default statement，P51完整句包含and approved its submission。

需做：先由两位作者审阅并明确批准主稿v8、补充v4和新版图表；随后在主稿与伦理表同步使用完整句：All authors have accepted responsibility for the entire content of this manuscript and approved its submission. 不得凭v7批准自动补写。

位置：
- BMT_main_manuscript_v8.docx / word/document.xml / P88；Author contributions. All authors have accepted responsibility for the entire content of this manuscript.
- BMT_Ethical_and_Legal_Declarations_v8_review.docx / word/document.xml / P17（表1第5行第2格）；All authors have accepted responsibility for the entire content of this manuscript.
- BMT_Ethical_and_Legal_Declarations_v8_review.docx / word/document.xml / P80；Final approval to submit this revised version is not inferred from the recorded approval of v7.

## AUTH-02 审稿人独立性仍有显式待确认项

总说明及Carole Sudre、Veronika Cheplygina、Geert Litjens、Yuyin Zhou、Lena Maier-Hein、Bo Wang逐人均保留[AUTHOR CONFIRMATION REQUIRED] / Not yet confirmed by both authors。

需做：由两位作者核对近期共同作者、共同基金、师生/指导、私人关系、同单位等期刊冲突；从确认独立的人选中提交至少5名。不能从公开单位与国别推定没有个人/合作冲突。

位置：
- BMT_reviewer_candidates.docx / word/document.xml / P4
- BMT_reviewer_candidates.docx / word/document.xml / P12
- BMT_reviewer_candidates.docx / word/document.xml / P20
- BMT_reviewer_candidates.docx / word/document.xml / P29
- BMT_reviewer_candidates.docx / word/document.xml / P37
- BMT_reviewer_candidates.docx / word/document.xml / P48
- BMT_reviewer_candidates.docx / word/document.xml / P58

## AUTH-03 原创、未重复发表和无同时投稿仍需真实事实确认

本轮检查的提交正文、投稿信、声明及既有作者确认记录未记录双方对这些投稿事实的明确确认；当前投稿信没有代为声称已确认。

需做：正式投稿及填系统声明前由作者确认原创性、既往发表/预印本/相关稿披露及无同时投稿。是否在投稿信加入该句依期刊或系统要求；不是要求凭空补一个未经确认的句子。

位置：
- BMT_submission_checklist_v8.docx / word/document.xml / P13；核对原创性、未重复/同时投稿及推荐审稿人关系

## EDIT-01 将正式上传副本中的作者审阅/草稿标记清理

这些是作者侧新增状态文本，非官方模板原文；补充材料可按原样发布。

需做：批准完成后，制作正式上传副本，清理上述状态字样并更新必要日期；审稿人文档若仅用于系统录入则无需整份上传。内部修订报告和submission checklist可保留审阅状态，无需作为论文文件上传。

位置：
- BMT_cover_letter_v8_review.docx / word/document.xml / P1；Draft cover letter — v8 author-review edition
- BMT_cover_letter_v8_review.docx / word/document.xml / P10；This letter remains a draft accompanying the revised author-review edition.
- BMT_cover_letter_v8_review.docx / word/footer1.xml / P1；Author review draft
- BMT_Ethical_and_Legal_Declarations_v8_review.docx / word/document.xml / P1；Ethical and legal declarations — v8 author-review copy
- BMT_Ethical_and_Legal_Declarations_v8_review.docx / word/document.xml / P80；Version status: this form accompanies the revised v8 author-review manuscript.
- BMT_supplementary_material_v4.docx / word/document.xml / P3；Haoze Lan; Ziyuan Zhu; v8 author-review revision, 6 November 2026
- BMT_reviewer_candidates.docx / word/footer1.xml / P1；Author review draft

## 已排除的误报

- **官方伦理模板的[TEMPLATE]、[INSTRUCTIONS]和默认示例不是漏填**：已与Audit/official_declarations_template_original.docx逐段对照；这些提示与示例来自期刊原始模板，8个实际必填值均已填写。P51的批准句是官方说明示例，不代表作者已作出该声明。 位置：document.xml P2–6及P33–79；表1第10–11行是原模板空可选行；BMT_Ethical_and_Legal_Declarations_v8_review.docx 保留官方模板结构；勿全局删除方括号或把说明页当成作者声明。
- **主稿的表格放置提示是正常排版标记**：实际Table 1–3均在文后editable tables出现；不是空数据或未完成表格。 位置：document.xml P24 [Place Table 1 near here]；P51 [Place Tables 2 and 3 near here]；BMT_main_manuscript_v8.docx
- **不重复索要历史已确认信息**：作者顺序、单位/邮箱/ORCID、400016通讯邮编、贡献、无经费、无利益冲突及法定免审依据已有作者确认。主稿与伦理表一致；没有编造IRB批准机关、编号或新的知情同意。 位置：主稿P3–8、P87–91；伦理表1第3–8行
- **未找到隐藏编辑遗留**：comments、w:ins/w:del、moveFrom/moveTo、w:sdt、w:vanish/webHidden及trackRevisions均为0；页面字段是正常PAGE域。 位置：8个顶层DOCX的document、tables、headers、footers和全部XML parts
- **Codex模型ID缺失已作事实披露**：明确写明精确底层模型ID不在归档记录中，未留下TBD或伪造型号。若作者确有原始记录可补充；无记录时不编造。 位置：主稿P30、P86；伦理表1第2及第6行

检查了8个顶层DOCX；各文件散列与详细XML计数见independent_check.json。Audit/Analysis内历史占位未计入投稿正文缺陷。
