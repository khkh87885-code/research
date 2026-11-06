#!/usr/bin/env python3
"""Name current submission artifacts for the paper and retain original evidence."""
from pathlib import Path
from zipfile import ZipFile
from copy import deepcopy
import hashlib,json,re,shutil
from docx import Document

TASK=Path('/workspace/paper_filenames')
ROOT=Path('/workspace/research_source')
SOURCE=TASK/'source'
DEST=ROOT/'submission/breast_ultrasound_quality_control'
PREFIX='Breast_Ultrasound_Quality_Control'
TITLE='Fixed-threshold transfer and equal-review ranking in breast ultrasound segmentation quality control'
ZIP=ROOT/'submission'/(PREFIX+'_Submission_Files.zip')
ROOT_NAMES={
 'BMT_main_manuscript_v13.docx':PREFIX+'_Manuscript.docx',
 'BMT_main_manuscript_v13_preview.pdf':PREFIX+'_Manuscript.pdf',
 'BMT_main_manuscript_v13_illustrated_preview.pdf':PREFIX+'_Illustrated_Manuscript.pdf',
 'BMT_supplementary_material_v9.docx':PREFIX+'_Supplementary_Material.docx',
 'BMT_supplementary_material_v9_preview.pdf':PREFIX+'_Supplementary_Material.pdf',
 'BMT_supplementary_Figure_S6_v9.pdf':PREFIX+'_Supplementary_Figure_S6.pdf',
 'BMT_Ethical_and_Legal_Declarations_v13.docx':PREFIX+'_Ethical_and_Legal_Declarations.docx',
 'BMT_cover_letter_v13.docx':PREFIX+'_Cover_Letter.docx',
 'BMT_data_and_code_availability_v13.docx':PREFIX+'_Data_and_Code_Availability.docx',
 'BMT_reviewer_candidates.docx':PREFIX+'_Reviewer_Candidates.docx',
 'BMT_submission_checklist_v13.docx':PREFIX+'_Submission_Checklist.docx',
 'BMT_formula_layout_proof_v13.pdf':PREFIX+'_Formula_Proof.pdf',
 'BMT_v13_all_figures.pdf':PREFIX+'_Figures.pdf',
 'BMT_revision_note_v13_zh.md':PREFIX+'_Preparation_Notes_zh.md',
 'Additional_quality_control_metrics.csv':PREFIX+'_Additional_Quality_Control_Metrics.csv',
 'UPLOAD_FILE_MAP.md':PREFIX+'_Submission_Guide.md',
 'FILE_MANIFEST.json':PREFIX+'_File_Manifest.json',
}
POINTERS={
 'Additional_quality_control_metrics.csv':PREFIX+'_Additional_Quality_Control_Metrics.csv',
 'S13_all_48_comparisons_unrounded.csv':PREFIX+'_Table_S13_Unrounded_Comparisons.csv',
 'BMT_supplementary_Figure_S6_v9.pdf':PREFIX+'_Supplementary_Figure_S6.pdf',
}

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def newpath(relative):
    if relative in ROOT_NAMES:return ROOT_NAMES[relative]
    p=Path(relative)
    if p.parts[0]=='Figures':return 'Figures/'+PREFIX+'_'+p.name
    if p.parts[:2]==('Analysis','table_data'):
        name=POINTERS.get(p.name,PREFIX+'_'+p.name)
        return 'Analysis/table_data/'+name
    # Archived build/evidence names are neutral; their original contents and
    # hashes remain unchanged. Their historical scope is stated in the README.
    return '/'.join(re.sub(r'_v\d+(?=\b|_)','',part)for part in p.parts)

def rewrite_docx(path, replacements):
    with ZipFile(path) as z:
        parts=[(item,z.read(item.filename))for item in z.infolist()]
    changed={}
    for i,(item,content)in enumerate(parts):
        if item.filename=='word/document.xml':
            for old,new in replacements.items():
                assert content.count(old.encode())==1,(old,content.count(old.encode()))
                content=content.replace(old.encode(),new.encode())
            changed[item.filename]=content
    with ZipFile(path,'w')as z:
        for item,content in parts:z.writestr(item,changed.get(item.filename,content))

def write_guides():
    guide=PREFIX+'_Submission_Guide.md'
    (DEST/'README_zh.md').write_text(f'''# {TITLE}

本目录是论文的当前投稿文件，文件名统一采用主题前缀 `{PREFIX}`，不使用内部版本标记。目标期刊为 Biomedical Engineering / Biomedizinische Technik，文章类型为 Research Article，按常规新稿投稿。

[正式主稿 Word]({PREFIX}_Manuscript.docx) · [主稿 PDF]({PREFIX}_Manuscript.pdf) · [补充材料 Word]({PREFIX}_Supplementary_Material.docx) · [补充材料 PDF]({PREFIX}_Supplementary_Material.pdf) · [六例图 S6]({PREFIX}_Supplementary_Figure_S6.pdf) · [投稿上传清单]({guide}) · [完整投稿包](../{ZIP.name})

主稿保留三式，补充材料保留两式，均为原生可编辑数学。主稿有五图、三张数据表；补充材料有十九个数据表面板。科研正文、数据、模型、图件与既有作者声明保持。补充正文中的两处CSV和一处S6文件名已与实际文件同步。

正式上传文件及类别见上传清单。主稿PDF、含图阅读稿、图册和公式快速预览供检查阅读；投稿包包含十五件正式上传文件。两个补充文件各小于10MB，需一同上传。

当前命名与内容保持核验位于 Audit/file_naming。Audit和Analysis中的既有构建及检查材料保留其原始内容、原路径和原检查范围；它们属于命名前的历史证据，不能用旧报告里的文件名或hash替代当前文件清单。旧脚本也可能含原工作目录，可从[原始归档](https://github.com/khkh87885-code/research/tree/f7f61104b5d7039dd8537c6c9963200627d07dd1/submission/bmt_v13)获取。Reproducibility中的科学计算资料保持。数据集、软件和外部权重的真实版本信息保留。

当前环境核验DOCX结构和实际导出的PDF；未直接运行WPS或Microsoft Word。尚未向期刊系统上传或提交。
''')
    rows=[
      ('Main Document',PREFIX+'_Manuscript.docx'),
      ('Figures',f'Figures/{PREFIX}_Figure_1.png 至 {PREFIX}_Figure_5.png，分别上传'),
      ('Cover Letter',PREFIX+'_Cover_Letter.docx'),
      ('Ethical and Legal Declarations',PREFIX+'_Ethical_and_Legal_Declarations.docx'),
      ('Supplementary Material 1',PREFIX+'_Supplementary_Material.docx'),
      ('Supplementary Material 2',PREFIX+'_Supplementary_Figure_S6.pdf'),
      ('Supplementary Data',PREFIX+'_Additional_Quality_Control_Metrics.csv；Analysis/table_data/'+POINTERS['S13_all_48_comparisons_unrounded.csv']),
      ('Data Availability（另行要求时）',PREFIX+'_Data_and_Code_Availability.docx'),
      ('Reviewer nominations','按 '+PREFIX+'_Reviewer_Candidates.docx 录入至少五名候选人'),
    ]
    text=f'# {TITLE} — 投稿上传清单\n\n官方投稿入口：https://mc.manuscriptcentral.com/bmt\n\n文章类型：Research Article；常规新稿。\n\n| 系统类别 | 文件 |\n| --- | --- |\n'
    text+='\n'.join('| '+a+' | '+b+' |'for a,b in rows)
    text+='\n\n两个补充文件各小于10MB，必须同时上传。若系统要求补充PDF，使用同主题名的补充PDF替代Word，不重复上传相同内容。主稿PDF、含图阅读稿、公式预览、图册、检查清单、Audit和构建脚本仅供复检。投稿ZIP用于下载后解压，按类别逐件上传。尚未执行期刊提交。\n'
    (DEST/guide).write_text(text)
    (DEST/(PREFIX+'_Preparation_Notes_zh.md')).write_text(f'''# 论文文件说明

论文：{TITLE}

投稿文件采用论文主题前缀，不包含内部版本标记。主稿、科研图件、S6、声明和科学数据保持原内容；补充材料中的三处文件名与实际文件同步，补充PDF随之导出。公式仍可编辑，保留主稿三式、补充两式及普通段落布局。现有作者确认及投稿事实声明沿用，尚未执行期刊投稿。

当前清单与命名核验见 Audit/file_naming；历史构建和检查证据保留原始内容及原检查范围。正式上传选择见 {guide}。
''')

def write_checklist():
    p=DEST/(PREFIX+'_Submission_Checklist.docx');d=Document(p)
    changes={0:'乳腺超声分割质量控制论文：投稿文件检查',1:'文件说明',
      2:'投稿文件采用论文主题名称；公式使用普通原生数学括号及段落排版，保留可编辑结构。现有作者声明实质保持，尚未执行期刊投稿。',
      8:'主稿5图+3表共8项，摘要174词、15条参考文献。主稿3张数据表、补充19个面板，分别66/878个单元格；当前文件核验见Audit/file_naming。',
      12:'按'+PREFIX+'_Submission_Guide.md分别上传正式主稿、五主图、声明、投稿信、补充Word、图S6 PDF和具名CSV。公式预览、阅读稿、图册、Audit和构建脚本供复检。'}
    for i,t in changes.items():d.paragraphs[i].text=t
    d.core_properties.title=TITLE+' — Submission checklist'
    d.save(p)

if __name__=='__main__':
    assert not DEST.exists()and not ZIP.exists()
    mapping={p.relative_to(SOURCE).as_posix():newpath(p.relative_to(SOURCE).as_posix())for p in SOURCE.rglob('*')if p.is_file()}
    assert len(set(mapping.values()))==len(mapping)
    assert not any(re.search(r'(^|[_/])v\d+(?=[_./]|$)',p,re.I)for p in mapping.values())
    for old,new in mapping.items():
        if old=='FILE_MANIFEST.json':continue
        target=DEST/new;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(SOURCE/old,target)
    rewrite_docx(DEST/ROOT_NAMES['BMT_supplementary_material_v9.docx'],POINTERS)
    write_guides();write_checklist()
    record={'paper_title':TITLE,'topic_prefix':PREFIX,'source_commit':'f7f61104b5d7039dd8537c6c9963200627d07dd1',
            'directory':'submission/breast_ultrasound_quality_control','zip':ZIP.name,'files':mapping,
            'supplement_filename_replacements':POINTERS,
            'scientific_content_changed':False}
    (TASK/'evidence/naming_map.json').write_text(json.dumps(record,indent=2)+'\n')
    profile=TASK/'lo_supplement';(profile/'user').mkdir(parents=True,exist_ok=True)
    (profile/'user/registrymodifications.xcu').write_text('''<?xml version="1.0" encoding="UTF-8"?><oor:items xmlns:oor="http://openoffice.org/2001/registry"><item oor:path="/org.openoffice.Office.Math/StandardFormat"><prop oor:name="BaseSize" oor:op="fuse"><value>11</value></prop><prop oor:name="IndexSize" oor:op="fuse"><value>70</value></prop><prop oor:name="LimitsSize" oor:op="fuse"><value>70</value></prop></item></oor:items>''')
    print(json.dumps({'directory':str(DEST),'renamed_paths':len(mapping),'prefix':PREFIX},indent=2))
