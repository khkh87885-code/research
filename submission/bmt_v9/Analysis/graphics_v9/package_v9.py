#!/usr/bin/env python3
"""Archive the completed BMT graphics/layout revision after final integration QA.

This script is deliberately inert unless --execute and the SHA256 of the final
QA report are provided. It preserves the author-approved v8 source directory.
It does not submit a journal manuscript or change any Git branch.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

from docx import Document

BASE = Path('/workspace/bmt_v9')
SOURCE = Path('/workspace/research_source/submission/bmt_v8_final')
DEST = Path('/workspace/research_source/submission/bmt_v9')
OUTPUTS = BASE / 'outputs'
ZIP_PATH = DEST.parent / 'BMT_v9_submission_files.zip'
QA_PATH = BASE / 'evidence/independent_integration_qa.json'
SAFE_BLOB_BYTES = 12_300_000
SUPPLEMENT_BYTES = 10_000_000

OUTPUT_FILES = [
    'BMT_main_manuscript_v9.docx',
    'BMT_main_manuscript_v9_preview.pdf',
    'BMT_main_manuscript_v9_illustrated_preview.pdf',
    'BMT_v9_all_figures.pdf',
    'BMT_supplementary_material_v5.docx',
    'BMT_supplementary_material_v5_preview.pdf',
    'BMT_supplementary_Figure_S6_v5.pdf',
]
ANCILLARY = {
    'BMT_Ethical_and_Legal_Declarations_v8.docx': 'BMT_Ethical_and_Legal_Declarations_v9.docx',
    'BMT_cover_letter_v8.docx': 'BMT_cover_letter_v9.docx',
    'BMT_data_and_code_availability_v8.docx': 'BMT_data_and_code_availability_v9.docx',
    'BMT_reviewer_candidates.docx': 'BMT_reviewer_candidates.docx',
}
FIGURE_NAMES = [f'Figure_{x}' for x in range(1, 6)] + [f'Figure_S{x}' for x in range(1, 6)] + ['Figure_S6A', 'Figure_S6B']
UPLOAD_FILES = [
    'BMT_main_manuscript_v9.docx',
    *[f'Figures/Figure_{x}.png' for x in range(1, 6)],
    'BMT_Ethical_and_Legal_Declarations_v9.docx',
    'BMT_cover_letter_v9.docx',
    'BMT_supplementary_material_v5.docx',
    'BMT_supplementary_Figure_S6_v5.pdf',
    'BMT_data_and_code_availability_v9.docx',
    'BMT_reviewer_candidates.docx',
    'Additional_quality_control_metrics.csv',
    'Analysis/table_data/S13_all_48_comparisons_unrounded.csv',
    'UPLOAD_FILE_MAP.md',
]

README = '''# BMT v9 科研图与投稿排版修订

[正式主稿 Word](BMT_main_manuscript_v9.docx) · [正式主稿 PDF 预览](BMT_main_manuscript_v9_preview.pdf) · [含图阅读版 PDF](BMT_main_manuscript_v9_illustrated_preview.pdf) · [全部新图 PDF](BMT_v9_all_figures.pdf) · [上传清单](UPLOAD_FILE_MAP.md)

本版依据用户要求重新设计全部主图及补图，并参照2026-11-06核验的BMT官方作者指南重排。科学正文、原统计结果、三张主表、19个补表面板及作者声明实质内容保留；只更新图形呈现、图注和排版。输入是已批准的v8提交材料，原目录submission/bmt_v8_final完整保留。此前作者确认记录按原适用范围保存在Audit中，没有记录一次新的v9批准。尚未执行期刊投稿。

主稿保留5幅主图和3张表，合计8项；摘要174词，参考文献15条。正式Word包含可编辑表格及末尾图注，主图应逐幅另传。含图阅读版增加五张新图板，仅用于核对和阅读，避免与正式主稿同时作为两个Main Document上传。

补充材料分两件，均小于10MB：

- [补充文字、19个可编辑表格及图S1–S5 Word](BMT_supplementary_material_v5.docx)，以及[PDF预览](BMT_supplementary_material_v5_preview.pdf)。内含S6总图注和独立文件指引。
- [补充图S6：六例逐页PDF](BMT_supplementary_Figure_S6_v5.pdf)。S6A对应A–C，S6B对应D–F；不是新增六名患者。

统计图直接读取归档CSV/JSON，采用白底、清楚的坐标和单位、真实置信区间及统一分图标注。研究流程由常规矢量图元绘制。超声图像、参考掩膜及预测轮廓来自已发布影像和保存的SAM输出，保留全视野、宽高比及原始像素，未使用生成式图像制作病例图。图5与S6采用既有六例精确检查点CPU重放，明确区别于未保存的原始CUDA掩膜；未运行新模型推理、重采样或新增实验。

BMT指南明确规定标题页、四段式摘要、未编号标题、参考文献和图表规范；未强制某种正文字体、行距、纸型或单双栏。本次选择A4单栏、25.4mm页边距、Times New Roman 12pt及1.5倍正文行距以便审阅，不能称为官方强制样式。原始Research Article Word模板二进制未取得；已核验其官方链接和内容转录，未声称复刻其Word样式。官方来源及限制见Audit/graphics_v9/official_format_requirements.md。

Figures保存12幅图的600dpi PNG及矢量PDF。可生成PNG/PDF/SVG的绘图脚本和输入hash记录保存在Analysis/graphics_v9与Audit/graphics_v9；脚本保留当前云端执行路径。Reproducibility沿用已批准分析复现入口。Audit、构建脚本、历史批准记录和阅读预览不作为公开补充材料整包上传。
'''

UPLOAD_MAP = '''# BMT v9 正式上传文件清单

| 投稿系统类别 | 文件 |
| --- | --- |
| Main manuscript | BMT_main_manuscript_v9.docx |
| Main figures | Figures/Figure_1.png至Figure_5.png，五幅分别上传 |
| Ethical and legal declarations | BMT_Ethical_and_Legal_Declarations_v9.docx |
| Cover letter | BMT_cover_letter_v9.docx |
| Supplementary material 1 | BMT_supplementary_material_v5.docx（文字、表格及图S1–S5；若系统要求PDF，可用其PDF版替代，不重复上传相同内容） |
| Supplementary material 2 | BMT_supplementary_Figure_S6_v5.pdf（六例逐页图S6；须与补充材料1一并上传） |
| Supplementary data | Additional_quality_control_metrics.csv；Analysis/table_data/S13_all_48_comparisons_unrounded.csv |
| Data availability, if requested separately | BMT_data_and_code_availability_v9.docx |
| Reviewer nominations | 按BMT_reviewer_candidates.docx中的六人信息录入；至少五名 |

两个补充材料文件分别小于10MB。图S6按病例分为六页以保持轮廓与标注可读；S6A为A–C，S6B为D–F，正文逻辑图号不变。

BMT_main_manuscript_v9_preview.pdf用于核对正式Word；illustrated阅读副本和BMT_v9_all_figures.pdf用于阅读与检查，不与正式Word同时作为Main Document上传。主图另交600dpi PNG；Figures内的PDF为矢量留档。若系统另外索要补充图文件，可从Figures中取对应图，但应避免与已嵌入补充材料的内容重复刊出。

提交ZIP仅含本表所列Word、五主图、两个CSV和本清单，不含Audit、构建脚本、作者历史确认记录或预览PDF。作者、机构、伦理、经费、利益冲突、原创及无其他期刊投稿等既有确认内容沿用；本轮修改是用户要求的科研图和排版修订。期刊系统上传与最终提交尚未执行。
'''

CHANGE_NOTE = '''# v9 图形和排版修改说明

本轮完成全部主图1–5及补图S1–S6重绘。统计点、曲线、成对结果、预算扫描、bootstrap和诊断构成分解均读取既有归档结果；无数据改写、无新的推理或重采样。病例图显示原始超声像素、参考轮廓及真实CPU预测，使用统一图例、全视野和宽高比，图S6同时呈现全部30张非空预测掩膜。

已按BMT官方指南核对标题页、作者与通讯信息、摘要、关键词、章节层次、声明顺序、Vancouver参考文献、图注和可编辑表格。正式主稿采用清晰的单栏投稿布局；字体、行距和页边距属于本次排版选择，不能称为指南强制规定。没有添加虚构DOI、出版商标识、卷期页码或收稿日期。原始Word模板二进制的获取限制已保留，官方PDF要求和模板转录可以独立核查。

主文5图+3表共8项，摘要174词、15条文献。补充材料保留13个逻辑表号、19个实际表格面板；S6拆为独立六页PDF，与主补充Word共同作为两个补充文件上传，均小于10MB。

科学正文、表格数字、原H1–H3、CPU重放误差及作者声明事实保留。主稿声明仅调整标签和顺序以匹配官方模板。原作者批准记录按其原适用范围保存，本轮不新增批准事实，未执行期刊投稿。
'''


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copy_file(src: Path, dst: Path) -> None:
    assert src.is_file(), src
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    assert digest(src) == digest(dst), (src, dst)


def check_qa(expected: str) -> dict:
    assert digest(QA_PATH) == expected, 'Final QA hash differs; inspect report before packaging'
    qa = json.loads(QA_PATH.read_text())
    assert qa.get('final_documents_pending') is False, 'Final document QA remains pending'
    assert qa.get('checks') and all(c.get('pass') is True for c in qa['checks']), 'A QA check has not passed'
    docs = qa.get('documents', {})
    # The QA report must record current main Word and all final PDF hashes.
    assert docs.get('main', {}).get('docx_sha256') == digest(OUTPUTS / OUTPUT_FILES[0]), 'Main Word changed after QA'
    for filename in OUTPUT_FILES:
        p = OUTPUTS / filename
        assert p.is_file(), p
        if filename.endswith('.pdf') and filename != 'BMT_v9_all_figures.pdf':
            item = docs.get(filename)
            assert item and item.get('sha256') == digest(p), f'Final PDF not hash-verified: {filename}'
    # Supplement's own equality report and final QA must both be current.
    se = json.loads((BASE / 'evidence/supplement_layout_changes.json').read_text())
    assert se.get('tables_equal') is True and se.get('physical_tables') == 19
    assert se.get('final_docx_sha256') == digest(OUTPUTS / 'BMT_supplementary_material_v5.docx')
    assert se.get('s6', {}).get('sha256') == digest(OUTPUTS / 'BMT_supplementary_Figure_S6_v5.pdf')
    for p in OUTPUTS.glob('BMT_supplementary*'):
        if p.suffix in ('.docx', '.pdf'):
            assert p.stat().st_size < SUPPLEMENT_BYTES, f'Supplement exceeds 10MB: {p}'
    return qa


def write_checklist(dest: Path) -> None:
    d = Document(SOURCE / 'BMT_submission_checklist_v8.docx')
    replacements = {
        0: 'v9 科研图与投稿排版检查',
        2: '本轮按用户要求重新设计科研图并重排主稿。输入为已批准v8材料；作者事实及批准责任句沿用，原批准记录按其原范围保存。本版未执行期刊投稿。',
        6: '科学正文、原H1–H3、三张主表和19个补表面板的数值均保留。图直接读取已有归档评分、区间和真实CPU掩膜；本轮未运行新推理、重采样或新增实验。',
        8: '摘要174词、主文约3927词；主图5+表3共8项；补表S1–S13共19个实际表格面板、补图S1–S6；15条文献。最终分页、字数及文件hash见Audit/graphics_v9核验记录。',
        10: '原作者确认的推荐审稿人无利益冲突、论文原创、无其他期刊投稿及全文责任声明均保留。声明标签和顺序按官方模板调整，实质文字不变；免审、无经费及研究无利益冲突内容沿用。',
        12: '按UPLOAD_FILE_MAP.md分别上传正式主稿、五幅主图、声明、投稿信、两个补充文件及具名CSV。含图阅读副本、图册、Audit和构建脚本不作为公开补充材料整包上传。',
    }
    assert len(d.paragraphs) > max(replacements), 'Checklist source structure changed'
    for i, text in replacements.items():
        d.paragraphs[i].text = text
    d.core_properties.content_status = ''
    d.core_properties.comments = ''
    d.core_properties.title = 'BMT v9 submission file checklist'
    d.save(dest)


def package(expected_qa: str) -> None:
    qa = check_qa(expected_qa)
    assert not DEST.exists(), f'{DEST} already exists; inspect rather than overwrite'
    assert not ZIP_PATH.exists(), f'{ZIP_PATH} already exists; inspect rather than overwrite'
    DEST.mkdir(parents=True)
    for filename in OUTPUT_FILES:
        copy_file(OUTPUTS / filename, DEST / filename)
    for old, new in ANCILLARY.items():
        copy_file(SOURCE / old, DEST / new)
    copy_file(SOURCE / 'Additional_quality_control_metrics.csv', DEST / 'Additional_quality_control_metrics.csv')
    shutil.copytree(SOURCE / 'Analysis/table_data', DEST / 'Analysis/table_data')
    shutil.copytree(SOURCE / 'Reproducibility', DEST / 'Reproducibility', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    for name in FIGURE_NAMES:
        for ext in ('.png', '.pdf'):
            copy_file(OUTPUTS / 'Figures' / (name + ext), DEST / 'Figures' / (name + ext))
    for p in (BASE / 'scripts').glob('*.py'):
        copy_file(p, DEST / 'Analysis/graphics_v9' / p.name)
    copy_file(BASE / 'qa/independent_check.py', DEST / 'Analysis/graphics_v9/independent_check.py')
    for p in (BASE / 'evidence').iterdir():
        if p.suffix in ('.json', '.md'):
            copy_file(p, DEST / 'Audit/graphics_v9' / p.name)
    for filename in ('official_declarations_template_original.docx', 'research_article_template_binary_unavailable.txt'):
        copy_file(BASE / 'resources' / filename, DEST / 'Audit/resources' / filename)
    for filename in ('final_author_confirmation.json', 'version_status.json'):
        copy_file(SOURCE / 'Audit' / filename, DEST / 'Audit/prior_v8_author_confirmation' / filename)
    # Include case asset source index, not another 10MB of duplicate medical panels.
    copy_file(BASE / 'layout_assets/layout_asset_index.json', DEST / 'Audit/graphics_v9/layout_asset_index.json')
    (DEST / 'README_zh.md').write_text(README)
    (DEST / 'UPLOAD_FILE_MAP.md').write_text(UPLOAD_MAP)
    (DEST / 'BMT_revision_note_v9_zh.md').write_text(CHANGE_NOTE)
    (DEST / 'Analysis/graphics_v9/README.md').write_text('''# Graphics/layout build archive

These scripts are the exact cloud build scripts used for the v9 presentation revision. They retain /workspace/bmt_v9 and /workspace/research_source execution paths and are not advertised as a path-independent installer. Figure generation reads the already archived JSON/CSV and captured NPZ inputs; it does not rerun inference or resampling. The scripts export PNG, PDF and SVG; this delivery stores PNG and PDF, while SVG can be regenerated. Input/output hashes, current official-format evidence and independent checks are under ../../Audit/graphics_v9. The separate Reproducibility directory retains the approved portable numerical-analysis entry point.
''')
    write_checklist(DEST / 'BMT_submission_checklist_v9.docx')
    status = {
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'revision': 'v9 scientific graphics and submission layout',
        'source': 'submission/bmt_v8_final',
        'user_requested_layout_and_figure_revision': True,
        'scientific_results_changed': False,
        'author_statement_substance_changed': False,
        'prior_author_confirmation_scope_preserved': True,
        'new_explicit_v9_author_approval_claimed': False,
        'journal_submission_executed': False,
        'integration_qa_sha256': expected_qa,
        'independent_checks_passed': len(qa['checks']),
        'upload_files': UPLOAD_FILES,
    }
    (DEST / 'Audit/graphics_v9/version_status.json').write_text(json.dumps(status, ensure_ascii=False, indent=2) + '\n')
    manifest = []
    for p in sorted(DEST.rglob('*')):
        if p.is_file():
            manifest.append({'path': p.relative_to(DEST).as_posix(), 'bytes': p.stat().st_size, 'sha256': digest(p)})
    (DEST / 'FILE_MANIFEST.json').write_text(json.dumps({'files': manifest}, ensure_ascii=False, indent=2) + '\n')
    with zipfile.ZipFile(ZIP_PATH, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for rel in UPLOAD_FILES:
            z.write(DEST / rel, rel)
    assert ZIP_PATH.stat().st_size < SAFE_BLOB_BYTES, 'Upload ZIP exceeds safe tool blob size; split before GitHub upload'
    receipt = {'destination': str(DEST), 'files': len(manifest) + 1, 'zip': str(ZIP_PATH), 'zip_bytes': ZIP_PATH.stat().st_size, 'zip_sha256': digest(ZIP_PATH), 'integration_qa_sha256': expected_qa}
    (BASE / 'packaging_receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--execute', action='store_true', help='Actually package; otherwise show a plan only')
    ap.add_argument('--qa-sha256', help='SHA256 of independently reviewed final QA report')
    args = ap.parse_args()
    if not args.execute:
        print(json.dumps({'destination': str(DEST), 'output_files': OUTPUT_FILES, 'upload_files': UPLOAD_FILES, 'execute_after_final_qa': True}, indent=2))
        return
    assert args.qa_sha256 and len(args.qa_sha256) == 64, '--qa-sha256 is required for execution'
    package(args.qa_sha256)


if __name__ == '__main__':
    main()
