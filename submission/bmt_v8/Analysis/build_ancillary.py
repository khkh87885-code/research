from pathlib import Path
import json,re,shutil,sys
from docx import Document
from docx.shared import Pt,Inches
from docx.oxml.ns import qn
sys.path.insert(0,'/workspace/bmt_v8/scripts')
from build_v8 import R,O,E,BASE,TITLE,RUNNING,SOURCE,REPO,normalize,review_props

def body(d):
 yield from d.paragraphs
 for t in d.tables:
  for row in t.rows:
   for c in row.cells:yield from c.paragraphs
def style(d,chinese=False):
 for sec in d.sections:sec.top_margin=sec.bottom_margin=Inches(.7);sec.left_margin=sec.right_margin=Inches(.8)
 for key in ['Normal','Title','Heading 1','Heading 2']:
  st=d.styles[key];st.font.name='Noto Sans CJK SC'if chinese else'Times New Roman';st.font.size=Pt(10.5 if key=='Normal' else 14)
  if chinese:st._element.rPr.rFonts.set(qn('w:eastAsia'),'Noto Sans CJK SC')
  st.paragraph_format.space_after=Pt(6)
 review_props(d,'Ancillary v8 author-review document');normalize(d)
def standalone(s):
 return s.replace(' [14]',' (https://doi.org/10.48550/arXiv.2609.00065)').replace(' [15]',' ('+REPO+'/tree/'+SOURCE+')').replace(' [8, 10]','')

m=Document(O/'BMT_main_manuscript_v8.docx');statements={}
for p in m.paragraphs:
 for prefix in ['AI use and acknowledgments.','Research ethics.','Author contributions.','Research funding.','Conflict of interest.','Informed consent.','Data and code availability.']:
  if p.text.startswith(prefix):statements[prefix]=p.text[len(prefix):].strip()
d=Document(BASE/'BMT_Ethical_and_Legal_Declarations_v7.docx')
d.paragraphs[0].text='Ethical and legal declarations — v8 author-review copy; Haoze Lan; Ziyuan Zhu'
values=[statements['AI use and acknowledgments.'],statements['Research ethics.'],statements['Informed consent.'],statements['Author contributions.'],statements['AI use and acknowledgments.'],statements['Conflict of interest.'],statements['Research funding.'],statements['Data and code availability.']]
for row,value in zip(d.tables[0].rows[1:9],values):row.cells[1].text=standalone(value)
d.add_paragraph('Version status: this form accompanies the revised v8 author-review manuscript. Final approval to submit this revised version is not inferred from the recorded approval of v7.')
review_props(d,'Original official declaration template populated for v8 author review');normalize(d);d.save(O/'BMT_Ethical_and_Legal_Declarations_v8_review.docx')

d=Document(BASE/'BMT_cover_letter.docx');p=list(d.paragraphs);p[0].text='Draft cover letter — v8 author-review edition';p[3].text='Re: Research Article — '+TITLE
p[5].text='We request consideration of this manuscript as a Research Article. It examines two operating questions in breast ultrasound segmentation quality control: transferring a development-calibrated numerical review threshold and selecting a fixed number of cases by risk ranking.'
p[6].text='A frozen SAM ViT-B generated shared initial masks for confidence and prompt-disagreement scores in a reference-informed, known-location setting. Each score targeted 20% review in 213 BUS-BRA development patients; the cutoffs were transferred to 851 internal and 252 BrEaST external patients. Detection, actual review fractions and missed low-quality masks were evaluated jointly.'
p[7].text='The confidence threshold selected 20.45% of internal patients and 13.89% externally. Relative detection counts changed between transferred cutoffs and equal review at the 20% target; a complete eight-budget analysis showed no uniformly better score. The revised manuscript uses this distinction to explain how an operating rule changes the interpretation of score comparisons. Three bootstrap routes and descriptive diagnostic-stratum accounting characterize its sampling and case-mix context without changing the prespecified H1–H3 analyses.'
p[8].text='Actual prediction contours are supplied for all six audited external misses. A targeted CPU replay used checkpoint bytes identical to the original and preserved every review and quality label, with numerical differences disclosed. The reference-derived prompts define a known-location evaluation, and review flags are simulated counts rather than measured reader time.'
p[9].text='The authors report no research funding or conflicts of interest. OpenAI Codex assistance is disclosed in the manuscript and original Ethical and Legal Declarations form. The authors previously confirmed statutory ethics-review exemption under Article 32 of the Chinese Measures (2023). This letter remains a draft accompanying the revised author-review edition.'
style(d);d.save(O/'BMT_cover_letter_v8_review.docx')

d=Document();d.add_heading('Data and code availability',0);d.add_paragraph(TITLE);d.add_paragraph(standalone(statements['Data and code availability.']))
d.add_heading('Fixed evidence archives',1)
for line in ['Original study: '+REPO+'/tree/592566b4c5f39e261c676eb034139a974e9cdfd5','Budget/calibration/diagnostic accounting: '+REPO+'/tree/'+SOURCE+'/experiments/cloud_validation_v1','Six-case CPU replay and actual masks: '+REPO+'/tree/'+SOURCE+'/experiments/six_case_replay_v1','SAM source: https://github.com/facebookresearch/segment-anything/tree/dca509fe793f601edb92606367a655c15ac00fdf','Checksum-identical public checkpoint asset: https://github.com/ultralytics/assets/releases/download/v8.3.0/sam_b.pt','Checkpoint SHA-256: ec2df62732614e57411cdcf32a23ffdf28910380d03139ee0f4fcbe91eb8c912']:
 d.add_paragraph(line)
style(d);d.save(O/'BMT_data_and_code_availability_v8.docx')

d=Document(BASE/'BMT_reviewer_candidates.docx')
for p in body(d):
 if 'Transfer of fixed review thresholds for breast ultrasound segmentation quality control'in p.text:p.text=p.text.replace('Transfer of fixed review thresholds for breast ultrasound segmentation quality control',TITLE)
style(d);d.save(O/'BMT_reviewer_candidates.docx')

d=Document();d.add_heading('v8 修订与投稿检查',0)
checks=[('版本','主稿v8、补充材料v4；本轮为作者审阅稿，未执行期刊投稿。v7既有作者确认作为历史记录保留，不将其写成已对新v8重新批准。'),('作者与联系','Haoze Lan第一兼通讯，Ziyuan Zhu第二；同重庆医科大学人工智能医学学院；通讯邮编400016，ORCID和邮箱沿用已确认信息。'),('科学核验','原H1–H3和主表、原S1–S9数字保持。新增8预算、3路线bootstrap、诊断构成分解及六例CPU真实轮廓；均标注事后性质。'),('格式','摘要≤200词、主文≤6000词；主图5+表3共8项；补表S1–S13、补图S1–S6；15条文献。最终字数、分页、文件大小与引用顺序见Audit核验记录。'),('作者责任及声明','已确认的免审依据、无经费、无利益冲突等事实沿用。BMT要求最终稿由所有作者批准后加入其完整批准提交句；本轮不自动认证新版已获两位作者批准。'),('实际投稿前','按最终版本完成两位作者审阅；核对原创性、未重复/同时投稿及推荐审稿人关系。此处为投递检查事项，不代表已经核实或提交。')]
for title,text in checks:d.add_heading(title,1);d.add_paragraph(text)
style(d,True);d.save(O/'BMT_submission_checklist_v8.docx')

response='''# Response to the supplied v7 review report (internal author-review revision)\n\nThis response addresses the supplied report dated 6 November 2026. It is not represented as correspondence from a journal.\n\n1. **Make the operating-policy contribution explicit.** The title, abstract, final Introduction paragraph, Discussion opening and conclusion now distinguish a transferred numerical cutoff from equal-review ranking. The complete eight-budget grid shows that the relative detection yield depends on the policy and budget, with no uniformly better score. Original H1–H3 remain unchanged.\n2. **Add real prediction contours.** The original-checkpoint bytes were recovered from a public GitHub release and verified against the frozen SHA-256. Six targeted CPU replays saved 30 actual masks. Figure 5 shows the three shared misses; Figure S6 includes all six. Table S13 discloses the cross-environment numerical differences and unchanged decisions.\n3. **Characterize the small external sample and stability.** Three patient-bootstrap routes, each with 10,000 replicates, separate calibration and test-sampling sensitivity (Table S11). The original strict pattern occurs in 30.94% of full resamples. This is an empirical frequency; the original Newcombe intervals remain. No new independent patients or population-level superiority are claimed.\n4. **Describe diagnostic composition without causal attribution.** Direct standardization and symmetric Kitagawa accounting quantify composition-associated and within-stratum terms (Table S12). A review-fraction difference of −6.56 points comprises +0.64 and −7.20 points. Acquisition and annotation differences have not been causally separated.\n5. **Keep submission statements factual.** Confirmed professional details, ethics basis, funding and conflicts are retained. The revised package is for author review; originality/exclusive-consideration, reviewer relationships and final-version submission approval are not inferred from the older report.\n'''
(O/'Response_to_supplied_v7_review.md').write_text(response)
(O/'README_zh.md').write_text('# BMT v8 作者审阅版\n\n主稿：BMT_main_manuscript_v8.docx；补充材料：BMT_supplementary_material_v4.docx。PDF为排版预览。\n\n本版整合完整预算扫描、三路线患者bootstrap、诊断构成标准化/分解和六例真实CPU预测轮廓。原预设H1–H3、三张主表与原S1–S9数值保持不变。新增内容为事后验证。主文5图+3表共8项；补表S1–S13和补图S1–S6。\n\n主文第5图和补图S6来自已捕获的CPU数组。精确权重字节/源码及提示规则相同，但存在已披露的数值差异；原六例CUDA数组未保存，未声称逐像素恢复。\n\n作者单位通讯地址及400016邮编、第一作者ORCID和邮箱均沿用已确认信息。已确认的法定免审、无经费及无冲突事实保留。v7原作者确认记录存于Audit/prior_author_confirmations；本次v8是修订审阅稿，不将旧批准表述为已经对新版重新批准，未执行期刊投稿。\n\n完整逐例科学证据在固定提交 '+SOURCE+'；本包Analysis与Audit提供新表、源哈希、代码、数值与排版核验及对应永久链接。来源中早期“缺权重/未执行”的记录保留其历史日期，当前状态以六例重放回执为准。\n')

for folder in ['Audit','Analysis','Audit/prior_author_confirmations']:(O/folder).mkdir(parents=True,exist_ok=True)
# The S7 note names this companion explicitly; retain it in every rebuilt package.
shutil.copy2(BASE/'Additional_quality_control_metrics.csv',O/'Additional_quality_control_metrics.csv')
for name in ['author_confirmation_record.json','postal_confirmation_20261106.json','confirmed_address_ethics_sources.json','confirmed_address_ethics_sources.md']:
 if(BASE/'Audit'/name).exists():shutil.copy2(BASE/'Audit'/name,O/'Audit/prior_author_confirmations'/name)
for name in ['requirements.json','official_requirements.md','official_declarations_template_original.docx']:
 if(BASE/'Audit'/name).exists():shutil.copy2(BASE/'Audit'/name,O/'Audit'/name)
for name in ['figure5_provenance.json','new_tables.json','new_tables_numeric_verification.json','new_tables_verification.md','narrative_review.json','narrative_review.md']:
 if(E/name).exists():shutil.copy2(E/name,O/'Audit'/name)
shutil.copytree(E/'table_data',O/'Analysis/table_data',dirs_exist_ok=True)
for name in ['build_v8.py','build_figure5.py','build_ancillary.py']:shutil.copy2(R/'scripts'/name,O/'Analysis'/name)
for name in ['checkpoint_acquisition_receipt.json','replay_protocol.json','runtime_resource.json']:
 shutil.copy2(Path('/workspace/research_source/experiments/six_case_replay_v1')/name,O/'Audit'/('six_case_'+name))
for name in ['postrun_review.json','postrun_review.md']:
 shutil.copy2(Path('/workspace/research_source/experiments/six_case_replay_v1/qa')/name,O/'Audit'/('six_case_'+name))
print('Built v8 cover draft, original-form declarations, availability, reviewers and author-review checklist.')
