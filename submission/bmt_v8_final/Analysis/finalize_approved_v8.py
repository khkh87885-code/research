"""Apply the user's explicit final-version approval; preserve scientific content."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil,re
from docx import Document
from docx.shared import Pt,Inches
from docx.oxml.ns import qn

ROOT=Path('/workspace/bmt_v8_final');OUT=ROOT/'outputs';SOURCE=Path('/workspace/research_source/submission/bmt_v8')
EXACT_CONFIRMATION='批准，审稿人没有利益冲突，原创没有在其他地方投稿'
MANDATORY='All authors have accepted responsibility for the entire content of this manuscript and approved its submission.'
OLD_RESPONSIBILITY='All authors have accepted responsibility for the entire content of this manuscript.'
DATE='6 November 2026'
TITLE=Document(SOURCE/'BMT_main_manuscript_v8.docx').paragraphs[0].text
REVIEWERS=['Carole Sudre','Veronika Cheplygina','Geert Litjens','Yuyin Zhou','Lena Maier-Hein','Bo Wang']
assert not OUT.exists(),'Use a new final output directory'
shutil.copytree(SOURCE,OUT,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
(ROOT/'qa').mkdir(parents=True,exist_ok=True)
history=OUT/'Audit/prior_v8_review';history.mkdir(exist_ok=True)
for name in ['BMT_pre_submission_review_zh.md','BMT_revision_report_v8_zh.docx','BMT_revision_report_v8_zh.md','BMT_revision_report_v8_zh_preview.pdf']:
 if(OUT/name).exists():shutil.move(OUT/name,history/name)
for name in ['version_status.json','revision_metrics.json','independent_review.json','independent_review.md','pre_submission_independent_check.json','pre_submission_independent_check.md','structural_extraction.json','structural_check_stdout.json','final_layout_review.json']:
 if(OUT/'Audit'/name).exists():shutil.move(OUT/'Audit'/name,history/name)
if(OUT/'FILE_MANIFEST.json').exists():shutil.move(OUT/'FILE_MANIFEST.json',history/'previous_review_FILE_MANIFEST.json')

def paragraphs(doc):
 yield from doc.paragraphs
 for table in doc.tables:
  for row in table.rows:
   for cell in row.cells:yield from cell.paragraphs
def remove(p):p._p.getparent().remove(p._p)
def properties(doc):
 doc.core_properties.title=TITLE
 doc.core_properties.author='Haoze Lan; Ziyuan Zhu'
 doc.core_properties.comments=''
 doc.core_properties.subject='Biomedical Engineering / Biomedizinische Technik submission'
 doc.core_properties.keywords=''
 doc.core_properties.category=''
 doc.core_properties.content_status=''
 doc.core_properties.last_modified_by='BMT document preparation workflow'
 for sec in doc.sections:
  for part in [sec.header,sec.footer]:
   for p in part.paragraphs:
    for run in p.runs:
     if 'Author review draft' in run.text:run.text=run.text.replace('Author review draft','Haoze Lan; Ziyuan Zhu')
def save(doc,path):properties(doc);doc.save(path)

main=Document(OUT/'BMT_main_manuscript_v8.docx')
target=next(p for p in main.paragraphs if p.text.startswith('Author contributions.'))
assert OLD_RESPONSIBILITY in target.text and MANDATORY not in target.text
target.text=target.text.replace(OLD_RESPONSIBILITY,MANDATORY)
contributions=target.text[len('Author contributions. '):]
save(main,OUT/'BMT_main_manuscript_v8.docx')

supp=Document(OUT/'BMT_supplementary_material_v4.docx')
assert 'v8 author-review revision'in supp.paragraphs[2].text
supp.paragraphs[2].text='Haoze Lan; Ziyuan Zhu'
save(supp,OUT/'BMT_supplementary_material_v4.docx')

decl_old=OUT/'BMT_Ethical_and_Legal_Declarations_v8_review.docx';decl=Document(decl_old)
decl.paragraphs[0].text='Ethical and legal declarations; Haoze Lan; Ziyuan Zhu'
assert OLD_RESPONSIBILITY in decl.tables[0].rows[4].cells[1].text
decl.tables[0].rows[4].cells[1].text=contributions
for p in list(decl.paragraphs):
 if p.text.startswith('Version status: this form accompanies the revised v8 author-review manuscript.'):remove(p)
save(decl,OUT/'BMT_Ethical_and_Legal_Declarations_v8.docx');decl_old.unlink()

cover_old=OUT/'BMT_cover_letter_v8_review.docx';cover=Document(cover_old)
cover.paragraphs[0].text='Cover letter';cover.paragraphs[1].text=DATE
p=cover.paragraphs[9]
assert 'This letter remains a draft accompanying the revised author-review edition.' in p.text
p.text=(p.text.replace('This letter remains a draft accompanying the revised author-review edition.','')+
        ' Both authors have approved the final manuscript, supplementary materials and figures for submission to Biomedical Engineering / Biomedizinische Technik and accept responsibility for the entire content. '+
        'The work is original and is not under consideration by another journal. Earlier manuscript drafts and supporting research materials are publicly available in our GitHub repository: https://github.com/khkh87885-code/research.').strip()
save(cover,OUT/'BMT_cover_letter_v8.docx');cover_old.unlink()

reviewers=Document(OUT/'BMT_reviewer_candidates.docx');count=0
for p in reviewers.paragraphs:
 text=p.text
 if text.startswith('[AUTHOR CONFIRMATION REQUIRED]'):
  p.text='The authors have confirmed that none of the six proposed reviewers has a disqualifying personal, institutional or collaborative conflict of interest with them.';count+=1
 elif text.startswith('Conflict check: [AUTHOR CONFIRMATION REQUIRED]'):
  p.text='Conflict check: the authors confirm no disqualifying conflict of interest for this candidate.';count+=1
 elif 'This list does not certify willingness to review or absence of personal, institutional or collaborative conflicts.'in text:
  p.text=text.replace('This list does not certify willingness to review or absence of personal, institutional or collaborative conflicts.','The authors have confirmed no disqualifying reviewer conflicts. Availability and willingness to review have not been tested.')
 elif 'Several candidates collaborate in broad image-validation initiatives;'in text:
  p.text='Affiliations and public email publication were checked through official institutional pages or the original publisher article. Email deliverability, availability and willingness were not tested. The authors have confirmed the personal, institutional and collaborative conflict checks for all six candidates.'
 elif 'the authors must complete institutional, collaboration and personal conflict checks before nomination.'in text:
  p.text=text.replace('the authors must complete institutional, collaboration and personal conflict checks before nomination.','the authors have confirmed no disqualifying conflicts for the supplied six-person list.')
assert count==7
save(reviewers,OUT/'BMT_reviewer_candidates.docx')

availability=Document(OUT/'BMT_data_and_code_availability_v8.docx');save(availability,OUT/'BMT_data_and_code_availability_v8.docx')
check=Document(OUT/'BMT_submission_checklist_v8.docx')
check.paragraphs[0].text='v8 作者批准与提交文件检查'
check.paragraphs[2].text='主稿v8、补充材料v4及新版图表已获作者最终批准；声明和投稿信已同步。材料已整理为提交文件，尚未执行期刊系统投稿。'
check.paragraphs[10].text='作者已确认最终版本批准、推荐审稿人无利益冲突、论文原创且无其他期刊投稿。主稿与官方声明均含BMT完整责任及批准提交句；投稿信披露已有GitHub公开稿。既有免审、无经费与研究无利益冲突声明沿用。'
check.paragraphs[11].text='上传文件'
check.paragraphs[12].text='按UPLOAD_FILE_MAP.md选择正式主稿、主图1–5、声明、投稿信及补充材料和具名CSV。推荐审稿人按系统字段录入。Audit/Analysis及历史审阅记录用于归档，不作为公开补充材料整包上传。'
save(check,OUT/'BMT_submission_checklist_v8.docx')

record={'recorded_utc':datetime.now(timezone.utc).isoformat(),'source':'Explicit user reply to the three-item pre-submission check','exact_user_reply':EXACT_CONFIRMATION,'scope':'Current main manuscript v8, supplementary material v4, new analyses and figures','both_authors_final_v8_submission_approved':True,'both_authors_responsibility_confirmed':True,'proposed_reviewer_conflicts_confirmed_absent':True,'confirmed_reviewer_names':REVIEWERS,'original_work_confirmed':True,'no_other_journal_submission_confirmed':True,'public_GitHub_manuscript_disclosure_retained':True,'journal_submission_executed':False,'review_basis_commit':'d75261433a11a814ebfd55c1bc9cb7ca4a962379','approved_input_main_sha256':hashlib.sha256((SOURCE/'BMT_main_manuscript_v8.docx').read_bytes()).hexdigest(),'approved_input_supp_sha256':hashlib.sha256((SOURCE/'BMT_supplementary_material_v4.docx').read_bytes()).hexdigest(),'scientific_tables_scores_and_figures_changed':False}
(OUT/'Audit/final_author_confirmation.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
(OUT/'Audit/version_status.json').write_text(json.dumps({'manuscript':'v8','supplement':'v4','status':'author-approved submission files','final_v8_submission_approval_confirmed':True,'reviewer_conflicts_confirmed_absent':True,'originality_and_no_other_submission_confirmed':True,'author_confirmed_correspondence_postcode':'400016','scientific_results_unchanged':True,'journal_submission_executed':False},indent=2)+'\n')
metrics=json.loads((history/'revision_metrics.json').read_text());metrics['final_version_author_submission_approval_claimed']=True;metrics['final_version_author_submission_approval_evidence']='final_author_confirmation.json';(OUT/'Audit/revision_metrics.json').write_text(json.dumps(metrics,indent=2)+'\n')
(OUT/'BMT_pre_submission_final_status_zh.md').write_text('''# v8提交前事项：已完成作者确认

作者明确回复：“批准，审稿人没有利益冲突，原创没有在其他地方投稿”。已记录原话及适用版本。

- 主稿v8、补充v4及新增图表的最终批准已记录；主稿和官方声明填入完整责任及批准提交句。
- 六位推荐审稿人的关系已由作者确认无利益冲突；7处待确认标记已替换为明确的作者确认记录，未声称候选人已被联系或同意审稿。
- 投稿信写入原创及无其他期刊审理声明，并披露已有GitHub公开稿。
- 正式文档中的作者侧Draft/author-review文字及旧版本状态说明已清理；官方模板自带说明保留。
- S7引用的Additional_quality_control_metrics.csv已在包内；S13完整对照CSV仍可取得。
- 科学正文、原表数字、全部图件保持，新增变化限于批准/投稿事实与文档状态。

已整理提交文件，尚未执行期刊投稿。以前检查中的未决状态保存在Audit/prior_v8_review，当前状态见Audit/version_status.json和final_author_confirmation.json。
''')
(OUT/'UPLOAD_FILE_MAP.md').write_text('''# 正式上传文件清单

| 投稿系统类别 | 文件 |
| --- | --- |
| Main manuscript | BMT_main_manuscript_v8.docx |
| Main figures | Figures/Figure_1.png至Figure_5.png；逐图上传 |
| Ethical and legal declarations | BMT_Ethical_and_Legal_Declarations_v8.docx |
| Cover letter | BMT_cover_letter_v8.docx |
| Supplementary material | BMT_supplementary_material_v4.docx或其PDF，依系统要求选择 |
| Supplementary data | Additional_quality_control_metrics.csv；Analysis/table_data/S13_all_48_comparisons_unrounded.csv |
| Data availability, if requested separately | BMT_data_and_code_availability_v8.docx |
| Reviewer nominations | 按BMT_reviewer_candidates.docx中的六人信息录入系统；至少五人 |

预览PDF供排版核对。补充图已嵌入补充材料，若系统另需图件，可使用Figures/Figure_S*。Audit、Analysis中的构建/审计代码、历史修订报告及作者确认记录不作为论文公开补充材料整包上传。

作者已批准并确认三类投稿事实；期刊系统填写、上传及最终提交尚未执行。
''')
(OUT/'README_zh.md').write_text('''# BMT v8 作者批准提交材料

[主稿Word](BMT_main_manuscript_v8.docx) · [主稿PDF](BMT_main_manuscript_v8_preview.pdf) · [补充Word](BMT_supplementary_material_v4.docx) · [补充PDF](BMT_supplementary_material_v4_preview.pdf) · [上传清单](UPLOAD_FILE_MAP.md)

两位作者最终批准、六位候选审稿人无利益冲突、论文原创且无其他期刊投稿均已按用户明确回复记录。主稿、官方声明和投稿信已同步，7处审稿人待确认标记已处理。正式文件中作者侧草稿标记已清除，期刊原始模板说明保留。

科学结果、H1–H3、全部表格和图像未改。原v8审阅版保留在仓库submission/bmt_v8；当前批准版位于submission/bmt_v8_final。现有400016邮编、作者信息、免审、无经费及研究无冲突声明保留。

完整包用于归档；实际上传请遵循UPLOAD_FILE_MAP.md。当前尚未执行期刊投稿。以前审阅和检查状态位于Audit/prior_v8_review，当前以Audit/version_status.json和final_author_confirmation.json为准。
''')
(OUT/'Analysis/finalize_approved_v8.py').write_bytes(Path(__file__).read_bytes())
print(json.dumps({'status':'prepared author-approved v8 documents','reviewer_placeholders_replaced':count,'approval_record':'Audit/final_author_confirmation.json','journal_submission_executed':False},ensure_ascii=False))
