from pathlib import Path
import csv,difflib,hashlib,json,re
from docx import Document
from docx.shared import Inches,Pt
from docx.oxml.ns import qn

R=Path('/workspace/bmt_v8');O=R/'outputs';BASE=Path('/workspace/research_source/submission/bmt_v7')
d=Document(O/'BMT_main_manuscript_v8.docx');s=Document(O/'BMT_supplementary_material_v4.docx');old=Document(BASE/'BMT_main_manuscript_v7.docx')
ps=[p.text for p in d.paragraphs];op=[p.text for p in old.paragraphs]
lex=lambda x:len(re.findall(r"[\w]+(?:[’'−–-][\w]+)*",x))
a=' '.join(p for p in ps if p.startswith(('Objectives  ','Methods  ','Results  ','Conclusions  ')))
body=' '.join(ps[ps.index('Introduction'):ps.index('Acknowledgments')])
cells=lambda x:[[[c.text for c in row.cells]for row in t.rows]for t in x.tables]
assert cells(d)==cells(old)
assert cells(s)[:9]==cells(Document(BASE/'BMT_supplementary_material_v3.docx'))
assert lex(a)<=200 and lex(body)<=6000
assert len(d.tables)==3 and len([p for p in ps if re.match(r'^Figure \d+\.',p)])==5
assert (O/'BMT_supplementary_material_v4.docx').stat().st_size<10000000
stats={'abstract_whitespace_words':len(a.split()),'abstract_lexical_words':lex(a),'main_body_lexical_words_including_headings':lex(body),'main_tables':3,'main_figures':5,'main_combined_display_items':8,'references':15,'supplement_logical_tables':13,'supplement_physical_tables':len(s.tables),'supplement_figures':6,'original_main_table_cells_unchanged':True,'original_S1_S9_table_cells_unchanged':True,'supplement_docx_bytes':(O/'BMT_supplementary_material_v4.docx').stat().st_size,'final_version_author_submission_approval_claimed':False}
(O/'Audit/revision_metrics.json').write_text(json.dumps(stats,indent=2)+'\n')
text=f'''# BMT v8 修订与核验报告

已完成主稿v8和补充材料v4，整合全部预算扫描、三路线bootstrap、诊断构成分解及六例真实预测轮廓。新版围绕“固定阈值迁移与等复核量排序回答不同的部署问题”组织论证。

## 主线与文字

标题、结构式摘要、引言结尾、讨论开头和结论已重写。讨论明确说明数值阈值可逐病例应用，而等复核量排序在指定队列或批次中固定选择数量。通过完整8预算结果界定20%示例的适用范围，避免把单点方向反转写成方法普遍优越。

摘要{len(a.split())}个空格计数词（词法计数{lex(a)}），正文约{lex(body)}词，均低于BMT的200/6000词限制。主文5图与3表共8项，新增Kitagawa原始文献后共15条参考文献。方法中的空掩膜句已改为条件定义，不再容易误读成发生过两张空掩膜。

## 新证据的整合

1. **预算依赖**：Table S10和Figure S3报告5%至50%的全部8预算及两种规则。等复核量的复核率差按设计恒为0，C/E面板不再呈现可能被误读为政策不确定性的非零区间。原计算归档保留，检测差区间不变。
2. **校准与抽样稳定性**：Table S11和Figure S4包括3路线各10,000次重采样。全部重采样的原方向严格反转频率为30.94%，零差占28.08%；表述为经验频率，并说明固定阈值bootstrap中缺少A-only病例的支持约束。原H1–H3 Newcombe区间保留。
3. **病例构成分账**：Table S12和Figure S5报告对称Kitagawa分解及共同权重标准化。A复核率差−6.56个百分点由构成相关+0.64与层内率−7.20组成；不作因果或“解释比例”判断。检测分解4,999/5,000次有效，零分母保持缺失。
4. **真实预测轮廓**：Figure 5突出三例共同漏检，Figure S6展示全部六例；Table S13及CSV公开逐例原值与CPU重放值。精确权重和源码下保存30张真实掩膜，全部复核和质量标签相同；初始参考Dice最大绝对差9.61×10⁻⁵。所有48项中最大差为0.00143543，不将新CPU数组说成未保存的原CUDA数组。

## 保留的科学记录与作者信息

三张主表与原补表S1–S9逐单元格相同。原始逐例评分、阈值与预设H1–H3没有覆盖；原同环境全1,316例零差异复跑和新增跨CPU环境六例重放分开报告。

作者顺序、单位、ORCID、邮箱及已确认的400016通讯邮编保留。已确认的法定免审依据、无经费和无冲突事实沿用；没有新增伦理机构决定或编号。本版为新的作者审阅稿，v7的批准记录作为历史证据保留，没有自动声称两位作者已重新批准v8，未执行期刊投稿。

## 核验与交付

新增表已从全精度归档、逐次抽样和真实NPZ独立核对；主表及S1–S9逐格保护。新图按6.4–6.89英寸出版宽重排，PNG为600dpi，最小字标7.2pt；PDF向量文字与轮廓可检查。摘要、篇幅、15条参考、图表引用顺序和专业地址均作结构检查，PDF另作排版目检。详细结果见Audit目录。

补充材料Word约{(O/'BMT_supplementary_material_v4.docx').stat().st_size/1000000:.2f}MB，低于单文件10MB。交付包含主稿/补充Word与PDF预览、分开的生产图、更新的声明及投稿信审阅稿、推荐审稿人、数据代码说明、供给审稿报告的回应、新表CSV和核验记录。
'''
(O/'BMT_revision_report_v8_zh.md').write_text(text)
report=Document();sec=report.sections[0];sec.top_margin=sec.bottom_margin=Inches(.65);sec.left_margin=sec.right_margin=Inches(.75)
for name in ['Normal','Title','Heading 1','Heading 2']:
 st=report.styles[name];st.font.name='Noto Sans CJK SC';st._element.rPr.rFonts.set(qn('w:eastAsia'),'Noto Sans CJK SC');st.font.size=Pt(10 if name=='Normal' else 14);st.paragraph_format.space_after=Pt(5)
for line in text.splitlines():
 clean=line.replace('**','')
 if clean.startswith('# '):report.add_heading(clean[2:],0)
 elif clean.startswith('## '):report.add_heading(clean[3:],1)
 elif clean:report.add_paragraph(clean)
report.core_properties.author='Haoze Lan; Ziyuan Zhu';report.core_properties.title='BMT v8 revision report'
report.save(O/'BMT_revision_report_v8_zh.docx')
diff='\n'.join(difflib.unified_diff(op,ps,fromfile='v7 main manuscript paragraphs',tofile='v8 main manuscript paragraphs',lineterm=''))+'\n'
(O/'Audit/main_manuscript_v7_to_v8.diff').write_text(diff)
print(json.dumps(stats,indent=2))
