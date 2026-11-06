# v8提交前检查：作者事项与可直接修正的项目

检查对象为主稿v8、补充材料v4、官方声明填写件、投稿信、数据代码说明、推荐审稿人及投稿清单。本轮没有进行期刊提交，也没有替两位作者认证尚未确认的事实。

## 已直接修正

补充材料S7说明引用的`Additional_quality_control_metrics.csv`此前漏装在v8包内。本轮从已核验的v7归档补齐原文件，7,130字节，SHA-256为`b1778d9b785773a9c44b59ccd9c06e607f5c4f950171d6e3e1903d5c1eb9146e`。未重算或改变其数值，主稿和补充Word/PDF均未改变。另一个具名附件`S13_all_48_comparisons_unrounded.csv`已位于Analysis/table_data内。

## 三类作者事实尚未完成

| 项目 | 当前证据及位置 | 提交前处理 |
| --- | --- | --- |
| 最终v8批准 | 主稿Author contributions、官方声明表Author contributions行只有承担全文责任的句子；已有明确批准记录针对v7 | 两位作者对最终主稿v8、补充v4和新增图表作批准后，同步写入BMT完整批准提交句 |
| 推荐审稿人关系 | 推荐人文档有7处`AUTHOR CONFIRMATION REQUIRED`：总说明1处，6位候选人各1处 | 两位作者核对个人、师生、近期共同作者/基金及机构关系，最终提供至少5名符合要求的人选，再替换对应待确认项 |
| 原创及投稿状态 | 当前记录没有明确确认是否已有期刊发表或正在另一刊审理 | 作者确认既往期刊发表、相关稿件及无同时投稿事实；投稿系统和投稿信按真实情况填写，并披露已在GitHub公开的稿件版本 |

BMT官方原始声明模板要求的完整句为：

> All authors have accepted responsibility for the entire content of this manuscript and approved its submission.

以上句子已准备好，未在尚缺v8批准事实时写入作者填写栏。原模板说明页出现同一句，只是出版社给出的默认示例，不代表作者已作出声明。

若作者确认相应事实，可采用的投稿状态措辞为：

> The manuscript has not been published in a peer-reviewed journal and is not under consideration by another journal. Earlier manuscript drafts and supporting research materials are publicly available in our GitHub repository.

其中GitHub公开稿件是已知事实；前半句有关期刊发表和同时投稿状态仍须据实确认，不应把已有公开稿写成从未公开。

## 正式上传副本需清理的状态标记

- 投稿信：标题的Draft/author-review、正文末的draft句及页脚Author review draft。
- 官方声明填写件：标题的author-review copy，以及文后关于v7与v8批准状态的内部说明。
- 补充材料：作者行的v8 author-review revision。
- 推荐审稿人：核对完成后清理7处待确认项；系统若仅需逐人录入，不必上传整份内部候选人审查文档。
- 正式上传的Word文档属性：清理关于author review/未认证v8批准的内部comments描述。内部Audit、修订报告及清单可保留历史记录。

这些清理项目应与最终批准后的提交副本一致。当前审阅稿中的状态描述是准确记录，不应靠删除状态文字来替代事实确认。

## 不属于待填项

- 作者名单、贡献、单位、邮箱、第一作者ORCID、400016通讯邮编、无经费、研究无利益冲突及作者确认的法定免审依据已经有记录；本轮不重复索取。
- 主稿及补充材料没有TBD/TODO或空数据占位；三张主表与原S1–S9仍完整。
- 官方模板的`TEMPLATE`、`INSTRUCTIONS`、条件示例、双盲作者名提示和可选空行来自出版社原模板，不能按未完成作者内容处理。
- 两个`Place Table … near here`是排版提示，表1–3已存在，不是缺表。
- 8个顶层DOCX未发现隐藏批注、增删修订、隐藏文字或占位内容控件。
- 精确Codex模型ID未保留在原始记录中的情况已经据实披露；不是待猜填型号。
- 机构邮箱及第二作者ORCID属于官方强烈建议项，现有指南未将其列为绝对要求；有真实信息时可补充。

## 上传文件与内部审阅资料的区别

按投稿系统分别提供最终主稿、主图1–5、正式声明、投稿信和补充材料。补充材料内的图已嵌入；是否同时提供独立图件按系统要求选择。两个具名CSV可作为数据补充附件提交或按期刊要求关联。

完整ZIP用于作者审阅与归档，包含内部Audit、Analysis、作者确认记录和修订报告，不应不加选择地整包作为期刊公开补充材料上传。保留官方模板说明的要求与内部审阅文件的选择是两回事。

独立只读检查详见同目录`independent_check.md/json`。本次补齐附件的字节证明见`attachment_fix_receipt.json`。
