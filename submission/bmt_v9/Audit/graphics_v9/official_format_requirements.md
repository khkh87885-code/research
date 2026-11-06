# BMT Research Article 官方格式复核

复核日期：2026-11-06。复核对象为 Biomedical Engineering / Biomedizinische Technik 的投稿稿件，而非出版后的排版样张。未改主稿，未进行投稿。

## 核心结论

当前官网仍链接同一套 Instructions for Authors、Research Articles Word 模板和 LaTeX 模板。通过 Firecrawl 对官网、Instructions PDF 和 ResearchArticle DOCX 请求实时重新抓取（`maxAge: 0`），均返回 HTTP 200；已保留响应内容与元数据。

官方 Instructions 没有规定正文必须采用某一种字体、字号、行距、页边距、纸型或单双栏。它要求清晰的层级和可编辑源稿，并明确说图表确切位置要到稿件 typeset 后才能确定。因而，已发表论文的双栏外观不能当作投稿 manuscript 必须双栏的证据。

**原始 ResearchArticle DOCX 二进制没有取得。** Firecrawl 返回的是内容转录及去样式后的 HTML，不包含 Word 的 styles.xml、页面 section、栏数、边距或字体间距等信息。此前文本转录不能称为“已按原始模板样式排版”。当前云环境只允许包管理器/GitHub 等网络域，出版商下载域不在允许名单；没有修改代理/CA，也没有绕过限制。针对原文件名及 GitHub 合法镜像的两次搜索没有找到匹配的原件。资源目录已明确记录这一限制。

当前 live PDF 解析器遗漏首页页眉的修订日期；“December 2024”来自此前独立提取的官方 PDF 第1页 `/workspace/bmt_v7/evidence/official_pdf_pages_1_4_10.txt`，不能说是本次 live Markdown 重新读到了日期。

## 官方明确要求

| 项目 | 已核实要求 | 证据 |
|---|---|---|
| 提交格式 | Microsoft Word 或 LaTeX；LaTeX 需提供完整 PDF 作为 Main Document | Instructions p.7 |
| 第一页 | 作者姓名、主标题、短标题及单位信息；至少一个名字及姓氏写全；通讯作者姓后 `*` | p.7 |
| 短标题 | 含空格不超过75字符；最终版本作为 running head | p.7 |
| 主标题 | Sentence case；冒号后小写 | p.7 |
| 通讯作者信息 | 邮箱、department、institution、street、city、postal code、country | p.7 |
| 其他作者单位 | department、institution、city、postal code、country | p.7 |
| ORCID | Highly recommended；不得编造 | p.7 |
| 正文总量 | Research Article：6000词、≤35篇参考文献、图和表合计≤8 | p.8；表格未说明各部分计词排除口径 |
| 摘要 | ≤200词；Objectives / Methods / Results / Conclusions 四个标题；摘要独立解释缩写；避免引用 | p.8 |
| 关键词 | 3–6个，字母序、小写、分号分隔；避免缩写和标题词重复 | p.8 |
| 小标题 | 不编号，sentence case，无句末句点，最多4级；同一级细分至少2个小标题 | p.9 |
| 参考文献 | Vancouver；文内方括号；按首次出现依次编号（包括图表）；列表数字不带方括号；>6位作者列前6位后 et al.；双向匹配 | p.9、11 |
| 图 | 每幅单独提交 jpg/eps/png/tiff；目标尺寸像素/半色调≥300dpi、混合像素及线图≥600dpi；图字≥6pt，优先Arial/Helvetica；分图大写字母；所有图文内引用；图注不在图像内部 | p.9 |
| 表 | 可编辑 Word/LaTeX，不能图片或Excel；阿拉伯数字连续编号；标题和列头；表注小写字母；解释缩写和粗体意义；正文标近似位置 | p.9 |
| 声明文件 | 定制的 Ethical and Legal Declarations 必须另交Word；文中信息与模板一致；冲突时以模板为准 | 当前官网 Submit、p.8 |
| 声明位置与顺序 | 最终 typeset 稿位于正文与参考文献之间；顺序见下 | p.8、已存原始声明模板 |

正文结构官方列为：Title page → Abstract → Keywords → 非标准缩写表（可选）→ Introduction → Materials and methods → Results → Discussion → Acknowledgments → References → Table and Figure legends。ResearchArticle 模板另外示范了 Discussion 后独立 Conclusions；可以保留，但不能说一般结构表强制要求独立 Conclusions。

声明模板的顺序为：Acknowledgments → Research ethics → Informed consent → Author contributions → Use of Large Language Models, AI and Machine Learning Tools → Conflict of interest → Research funding → Data availability。无适用内容的 Acknowledgments 可移除。使用已确认的作者事实，不重新询问或更改通讯地址、邮编、伦理事实、作者批准及全文责任。

## 提交版具体排版建议：自主选择，不冒称官方强制

| 元素 | 建议的本次实现 |
|---|---|
| 页面 | A4纵向、单栏、四边25.4mm |
| 正文 | Times New Roman或稳定衬线字体12pt，1.5倍行距，左对齐，段后6pt，无首行缩进 |
| 主标题 | 16pt粗体，左对齐，sentence case |
| 小标题 | 一级13pt粗体，二级12pt粗体；不编号；标题与下段同页 |
| 第1页 | 清晰title page：主标题、作者、单位、通讯地址/邮箱、已有ORCID、short title |
| 摘要及正文 | 摘要/关键词从第2页开始；正文在其后另起页；这些分页是易读布局选择 |
| 页眉页脚 | 简洁短标题及连续页码可用于审稿；官方实际明确要求的是第一页有短标题，以及最终版本有running head |
| 声明 | 与单独声明Word使用同名标题和相同内容，置于References前 |
| 图表 | 正文保留近似位置标记；References后给完整Table and Figure legends，再给可编辑表和高质量figure plates，并保留每幅单独图文件 |
| 图内字体 | 统一Arial/Helvetica等无衬线；目标尺寸以8–10pt为宜，绝不低于官方6pt；轴、单位、置信区间和panel清晰 |
| 不加入的出版元素 | 不添加De Gruyter标识、虚构DOI、卷期页码、received/accepted日期或出版商masthead |

模板中的“Insert figure here”和内嵌表格是近似定位示范；图表位置最终由出版流程决定。General structure 把 legends 列在References之后，因此本次推荐正文标记、末尾集中 legends/图表，避免把发表版的精确双栏浮动位置当作投稿要求。若选择正文内嵌供审稿阅读，也必须保留独立图源文件；不能声称该选择来自未取得的Word样式。

模板转录还包含 `www.chemsuschem.org` 等显然不属于本文的遗留页眉内容，不能复制到稿件。转录明确提醒：表不放textbox/frame，figure和legend不要捆在textbox/frame里。

## 可审计材料

- [机器可读要求](official_format_requirements.json)
- [本次官方Instructions全文转录及元数据](official_live_instructions_firecrawl.json)
- [本次ResearchArticle模板内容转录及元数据](official_live_article_template_firecrawl.json)
- [本次官网Submit及模板链接摘录](official_live_journal_submit_excerpt.json)
- [已有官方声明模板原件](../resources/official_declarations_template_original.docx)，SHA256：`8facc5b46d8dc245e1814a9f749e2ddc4d84e2189b20ea9f511886c38d9ef230`
- [原始ResearchArticle模板缺失说明](../resources/research_article_template_binary_unavailable.txt)

官方源：

- https://www.degruyterbrill.com/journal/key/bmte/html
- https://www.degruyterbrill.com/publication/journal_key/BMTE/downloadAsset/BMTE_Instructions%20for%20Authors.pdf
- https://www.degruyterbrill.com/publication/journal_key/BMTE/downloadAsset/BMTE_Template%20for%20Research%20Articles.docx
- https://www.degruyterbrill.com/publication/journal_key/BMTE/downloadAsset/BMTE_Template%20for%20Ethical%20and%20Legal%20Declarations.docx
