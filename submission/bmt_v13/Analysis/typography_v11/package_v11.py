#!/usr/bin/env python3
"""Package the user-requested mathematical-typography revision after final QA.

The default action is a read-only plan. Execution requires the hash of root's
final combined QA report. No Git branch or journal action is performed here.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import zipfile

from docx import Document
from lxml import etree

BASE = Path('/workspace/bmt_v11')
OUT = BASE / 'outputs'
SOURCE = Path('/workspace/research_source/submission/bmt_v10')
DEST = Path('/workspace/research_source/submission/bmt_v11')
ZIP_PATH = DEST.parent / 'BMT_v11_submission_files.zip'
FINAL_QA = BASE / 'evidence/final_revision_qa.json'
SAFE_BLOB_BYTES = 12_300_000
SUPPLEMENT_BYTES = 10_000_000
MAIN = 'BMT_main_manuscript_v11.docx'
SUPP = 'BMT_supplementary_material_v7.docx'
S6 = 'BMT_supplementary_Figure_S6_v7.pdf'
OUTPUT_FILES = [
    MAIN, 'BMT_main_manuscript_v11_preview.pdf',
    'BMT_main_manuscript_v11_illustrated_preview.pdf',
    SUPP, 'BMT_supplementary_material_v7_preview.pdf', S6,
    'BMT_formula_layout_proof_v11.pdf',
]
ANCILLARY = {
    'BMT_Ethical_and_Legal_Declarations_v10.docx': 'BMT_Ethical_and_Legal_Declarations_v11.docx',
    'BMT_cover_letter_v10.docx': 'BMT_cover_letter_v11.docx',
    'BMT_data_and_code_availability_v10.docx': 'BMT_data_and_code_availability_v11.docx',
    'BMT_reviewer_candidates.docx': 'BMT_reviewer_candidates.docx',
}
FIGURE_NAMES = [f'Figure_{x}' for x in range(1, 6)] + [f'Figure_S{x}' for x in range(1, 6)] + ['Figure_S6A', 'Figure_S6B']
UPLOAD_FILES = [
    MAIN, *[f'Figures/Figure_{x}.png' for x in range(1, 6)],
    'BMT_Ethical_and_Legal_Declarations_v11.docx', 'BMT_cover_letter_v11.docx',
    SUPP, S6, 'BMT_data_and_code_availability_v11.docx',
    'BMT_reviewer_candidates.docx', 'Additional_quality_control_metrics.csv',
    'Analysis/table_data/S13_all_48_comparisons_unrounded.csv', 'UPLOAD_FILE_MAP.md',
]

README = '''# BMT v11 数学公式排版修订

[正式主稿 Word](BMT_main_manuscript_v11.docx) · [正式主稿 PDF](BMT_main_manuscript_v11_preview.pdf) · [公式页快速预览](BMT_formula_layout_proof_v11.pdf) · [含图阅读版 PDF](BMT_main_manuscript_v11_illustrated_preview.pdf) · [全部图件 PDF](BMT_v11_all_figures.pdf) · [上传清单](UPLOAD_FILE_MAP.md)

本轮针对公式排列散乱、文字标签失去正体和实际字号不一致的问题重排。TP/FP/FN/TN等计数缩写、dev/std/fixed/CPU等文字标签以及min/max/argmin/clip/rank等运算符采用紧凑正体；数学变量保留其数学格式。长公式拆为各自完整的数学行，按实测宽度设置制表位，对齐关系号与右侧编号，并减少不必要的多行列间空白。

主稿仍有14组编号公式(1)–(14)，补充方法仍为12组(S1)–(S12)。一组可包含多行，公式行数及OMML对象数不等于组数；可见组号连续且不重复。公式仍为原生Office Math，可在文档中编辑，未转成截图。当前PDF导出按主稿数学基准12pt、补充11pt配置并核验，实际字号、分页和对齐检查见Audit/typography_v11。

本轮保留既有数学定义与统计方法，未增加公式组或新的推断。结果与讨论、三主表66个单元格、19个补表面板878个单元格、15条参考文献、作者声明实质及全部12幅科研图保持。主稿仍为5图+3表共8项、174词摘要。H1–H3原区间、H2/H3及补充比较的名义区间性质、预算/bootstrap/诊断构成分析的事后性质均保留；未运行新推理、重采样或新增实验。

正式补充材料仍为两件，均小于10MB：

- [补充方法、表格及图S1–S5 Word](BMT_supplementary_material_v7.docx)，或[PDF预览](BMT_supplementary_material_v7_preview.pdf)。内含S6总图注和文件指引。
- [六例逐页图S6 PDF](BMT_supplementary_Figure_S6_v7.pdf)。该文件与v10的S6内容逐字节相同，仅文件名及主补充文档中的指向升级；S6A为A–C，S6B为D–F。

正式Word用于Main manuscript，五主图逐幅另传；含图阅读版和图册用于核对。[9页公式预览](BMT_formula_layout_proof_v11.pdf)从主稿及补充PDF抽取有编号公式的页面，仅供快速复检，不作为投稿文件。当前环境检查覆盖DOCX原生数学结构及LibreOffice导出的PDF；未在Microsoft Word或WPS中实际运行文档，因此没有声称已验证所有跨软件排版兼容性。可结合正式PDF核对提交Word的呈现。

原v10归档完整保留。现有作者、机构及投稿事实声明沿用；尚未执行期刊系统上传或投稿。新构建与核验脚本在Analysis/typography_v11，诊断、有效公式计划、构建hash及独立检查在Audit/typography_v11。v10及此前官方证据和确认链的文本/JSON副本位于Audit/prior_v10，原始二进制资料仍在既有归档。Reproducibility、表格CSV和绘图脚本沿用。Audit、构建脚本、历史确认记录和预览不作为公开补充材料整包上传。
'''

UPLOAD_MAP = '''# BMT v11 正式上传文件清单

| 投稿系统类别 | 文件 |
| --- | --- |
| Main manuscript | BMT_main_manuscript_v11.docx，14组可编辑编号公式已重排 |
| Main figures | Figures/Figure_1.png至Figure_5.png，分别上传 |
| Ethical and legal declarations | BMT_Ethical_and_Legal_Declarations_v11.docx |
| Cover letter | BMT_cover_letter_v11.docx |
| Supplementary material 1 | BMT_supplementary_material_v7.docx：12组补充公式、19个可编辑表格面板及图S1–S5；系统要求PDF时以对应PDF替代，不重复上传相同内容 |
| Supplementary material 2 | BMT_supplementary_Figure_S6_v7.pdf：六例逐页图S6，须与补充材料1一并上传 |
| Supplementary data | Additional_quality_control_metrics.csv；Analysis/table_data/S13_all_48_comparisons_unrounded.csv |
| Data availability, if requested separately | BMT_data_and_code_availability_v11.docx |
| Reviewer nominations | 按BMT_reviewer_candidates.docx六人信息录入，至少五名 |

两个补充文件各小于10MB；S6A为A–C，S6B为D–F。主稿及主补充Word包含原生Office Math，公式可编辑；一组公式可有多行，编号仍14/12组。五主图为600dpi PNG，图件数据与v10相同。

正式PDF用于核对当前环境导出的Word呈现；Word/WPS未在本环境实际运行，未声称跨软件排版均已验证。BMT_formula_layout_proof_v11.pdf为9页公式快速预览，仅供复检，不作为投稿文件；illustrated阅读副本和BMT_v11_all_figures.pdf用于阅读，不与正式Word同时作为Main Document上传。提交ZIP包含上述15件上传文件，不含公式预览、其他预览PDF、Audit、构建脚本或历史记录。现有作者及投稿事实声明实质不变，尚未执行期刊系统上传或最终提交。
'''

CHANGE_NOTE = '''# v11 数学公式排版修改说明

本轮修正公式的呈现：多字母计数与描述标签改为紧凑正体，运算符以正体清楚显示；拆分长行和多定义行，每个数学行自身完整，通过实测宽度控制关系号及右侧组号对齐。改善列间距、行间距和段落衔接；当前PDF导出数学基准为主稿12pt、补充11pt，实际字号和页面结果纳入最终核验。

14组主公式及12组补充公式的可见编号保持连续唯一，实际数学行数可增加。全部公式仍为原生Office Math，并未替换成图片。当前检查覆盖DOCX结构及本环境LibreOffice PDF；没有实际启动Microsoft Word或WPS，不声称已完成两者或所有跨软件兼容性验证。

既有数学定义、统计方法、结果、讨论、15条参考文献、作者声明实质及全部科研图保留；三主表66个单元格和19个补表面板878个单元格逐字相同。S6 PDF仅改文件名，内容字节不变，主补充材料对应文件指向同步到v7。没有新模型推理、重采样、数据收集或新的科学实验。

原H1–H3比较与区间保持，H2/H3和补充区间仍为未经多重调整的名义区间；预算、bootstrap和诊断构成分解仍属事后分析。经验频率不变成p值、后验或总体概率，诊断分解保持描述性解释。

本轮按用户要求完成排版修订，原v10及历史确认记录保留，现有声明事实沿用。尚未执行期刊投稿；正式上传内容见UPLOAD_FILE_MAP.md。
'''


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copy_file(src: Path, dst: Path) -> None:
    assert src.is_file(), src
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    assert digest(src) == digest(dst), (src, dst)


def lock_final_report(expected: str) -> tuple[dict, dict[str, dict]]:
    assert FINAL_QA.is_file() and digest(FINAL_QA) == expected, 'Inspect combined final QA hash before packaging'
    report = json.loads(FINAL_QA.read_text())
    assert report.get('final_documents_pending') is False, f'Document QA is pending: {FINAL_QA}'
    assert report.get('status') == 'PASS', 'Combined final QA has not passed'
    children = {}
    assert len(report['reports']) >= 2, 'Final report must lock mathematical and layout checks'
    for name, item in report['reports'].items():
        path = Path(item['path'])
        if not path.is_absolute():
            path = BASE / path
        assert path.resolve().is_relative_to(BASE.resolve()), f'Unexpected {name} QA location'
        assert digest(path) == item['sha256'], f'{name} QA changed after final review'
        children[name] = json.loads(path.read_text())
    return report, children


def table_cells(doc: Document) -> list[str]:
    return [cell.text for table in doc.tables for row in table.rows for cell in row.cells]


def native_math_count(path: Path) -> int:
    with zipfile.ZipFile(path) as z:
        tree = etree.fromstring(z.read('word/document.xml'))
    return len(tree.findall('.//{http://schemas.openxmlformats.org/officeDocument/2006/math}oMath'))


def visible_group_labels(path: Path) -> list[str]:
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
          'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math'}
    with zipfile.ZipFile(path) as z:
        root = etree.fromstring(z.read('word/document.xml'))
    labels = []
    for p in root.findall('./w:body/w:p', ns):
        if p.find('m:oMath', ns) is None:
            continue
        texts = p.findall('w:r/w:t', ns)
        if texts and re.fullmatch(r'\(S?\d+\)', texts[-1].text or ''):
            labels.append(texts[-1].text[1:-1])
    return labels


def validate(qa_hash: str) -> tuple[dict, dict[str, dict], dict]:
    final, children = lock_final_report(qa_hash)
    # Root's combined review locks document bytes and child-report hashes. This
    # avoids imposing one historical schema or check count on independent QA.
    for filename in OUTPUT_FILES:
        p = OUT / filename
        assert p.is_file(), p
        record = final['documents'][filename]
        assert record['sha256'] == digest(p), f'Final document hash mismatch: {filename}'
        assert record['bytes'] == p.stat().st_size, f'Final document length mismatch: {filename}'
        if filename.startswith('BMT_supplementary'):
            assert p.stat().st_size < SUPPLEMENT_BYTES, f'Supplement exceeds 10MB: {p}'
    build = json.loads((BASE / 'evidence/equation_build_report.json').read_text())
    assert build['main']['sha256'] == digest(OUT / MAIN)
    assert build['supplement']['sha256'] == digest(OUT / SUPP)
    assert build['main']['numbered_display_equations'] == [str(x) for x in range(1, 15)]
    assert build['supplement']['numbered_display_equations'] == [f'S{x}' for x in range(1, 13)]
    assert build['main']['table_cells_exact'] and build['main']['results_discussion_declarations_exact']
    assert build['main']['references_exact_count'] == 15 and build['main']['abstract_unchanged']
    assert build['supplement']['table_cells_exact'] and build['supplement']['S6_bytes_unchanged']
    for filename, old, count, tables in [
        (MAIN, 'BMT_main_manuscript_v10.docx', 66, 3),
        (SUPP, 'BMT_supplementary_material_v6.docx', 878, 19),
    ]:
        doc, src = Document(OUT / filename), Document(SOURCE / old)
        assert len(doc.tables) == tables and len(table_cells(doc)) == count
        assert table_cells(doc) == table_cells(src), f'Table content changed: {filename}'
        assert native_math_count(OUT / filename) > 0, f'No editable math: {filename}'
        expected_labels = [str(i) for i in range(1, 15)] if filename == MAIN else [f'S{i}' for i in range(1, 13)]
        assert visible_group_labels(OUT / filename) == expected_labels, f'Equation groups not uniquely numbered: {filename}'
    assert digest(OUT / S6) == digest(SOURCE / 'BMT_supplementary_Figure_S6_v6.pdf')
    for name in FIGURE_NAMES:
        for suffix in ('.png', '.pdf'):
            assert digest(OUT / 'Figures' / (name + suffix)) == digest(SOURCE / 'Figures' / (name + suffix))
    return final, children, build


def write_checklist(path: Path) -> None:
    doc = Document(SOURCE / 'BMT_submission_checklist_v10.docx')
    changes = {
        0: 'v11 数学公式排版与投稿文件检查',
        2: '本轮按用户要求修正公式正体标签、长行、关系号对齐和实际字号。原v10归档保留，现有作者声明实质不变；未执行期刊投稿。',
        6: '主稿14组、补充12组编号公式仍为原生Office Math，组号连续唯一，每组可有多行。结果、讨论、表格、参考文献、声明实质与全部12幅科研图不变；没有新推理、重采样或新增患者。',
        8: '主稿5图+3表共8项，摘要174词、15条参考文献。主表66个单元格及补充19表878个单元格逐字保留。PDF分页、公式边界和文件hash见Audit/typography_v11。',
        10: '现有作者与机构、推荐审稿人无利益冲突、论文原创、无其他期刊投稿，以及免审、无经费和研究无利益冲突声明保留。公式检查覆盖本环境DOCX结构及PDF导出，未实际运行Word/WPS。',
        12: '按UPLOAD_FILE_MAP.md分别上传正式主稿、五主图、声明、投稿信、补充v7 Word和S6_v7 PDF，以及具名CSV。阅读副本、图册、Audit和构建脚本不作为公开补充材料整包上传。',
    }
    assert len(doc.paragraphs) > max(changes)
    for index, text in changes.items():
        doc.paragraphs[index].text = text
    doc.core_properties.title = 'BMT v11 submission file checklist'
    doc.core_properties.content_status = ''
    doc.core_properties.comments = ''
    doc.save(path)


def package(qa_hash: str) -> None:
    final, children, build = validate(qa_hash)
    assert not DEST.exists() and not ZIP_PATH.exists(), 'Inspect existing v11 output rather than overwriting it'
    DEST.mkdir(parents=True)
    for filename in OUTPUT_FILES:
        copy_file(OUT / filename, DEST / filename)
    copy_file(SOURCE / 'BMT_v10_all_figures.pdf', DEST / 'BMT_v11_all_figures.pdf')
    for old, new in ANCILLARY.items():
        copy_file(SOURCE / old, DEST / new)
    copy_file(SOURCE / 'Additional_quality_control_metrics.csv', DEST / 'Additional_quality_control_metrics.csv')
    shutil.copytree(SOURCE / 'Analysis', DEST / 'Analysis', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    shutil.copytree(SOURCE / 'Reproducibility', DEST / 'Reproducibility', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    for name in FIGURE_NAMES:
        for suffix in ('.png', '.pdf'):
            copy_file(SOURCE / 'Figures' / (name + suffix), DEST / 'Figures' / (name + suffix))
    # Text-only prior audit chain; template and document binaries remain in v10.
    for p in (SOURCE / 'Audit').rglob('*'):
        if p.is_file() and p.suffix in ('.json', '.md', '.txt'):
            copy_file(p, DEST / 'Audit/prior_v10' / p.relative_to(SOURCE / 'Audit'))
    copy_file(SOURCE / 'FILE_MANIFEST.json', DEST / 'Audit/prior_v10/FILE_MANIFEST_v10.json')
    copy_file(SOURCE / 'README_zh.md', DEST / 'Audit/prior_v10/README_v10_zh.md')
    copy_file(SOURCE / 'UPLOAD_FILE_MAP.md', DEST / 'Audit/prior_v10/UPLOAD_FILE_MAP_v10.md')
    for p in (BASE / 'evidence').iterdir():
        if p.is_file() and p.suffix in ('.json', '.md', '.txt'):
            copy_file(p, DEST / 'Audit/typography_v11' / p.name)
        elif p.is_file() and p.suffix == '.py':
            copy_file(p, DEST / 'Analysis/typography_v11' / p.name)
    for filename in ('engine_findings.json', 'engine_findings.md'):
        p = BASE / 'experiments/engine_agent' / filename
        if p.is_file():
            copy_file(p, DEST / 'Audit/typography_v11/engine' / filename)
    for subdir in ('scripts', 'qa'):
        for p in (BASE / subdir).rglob('*.py'):
            if '__pycache__' not in p.parts:
                copy_file(p, DEST / 'Analysis/typography_v11' / p.relative_to(BASE / subdir))
    (DEST / 'README_zh.md').write_text(README)
    (DEST / 'UPLOAD_FILE_MAP.md').write_text(UPLOAD_MAP)
    (DEST / 'BMT_revision_note_v11_zh.md').write_text(CHANGE_NOTE)
    (DEST / 'Analysis/typography_v11/README.md').write_text('''# Mathematical-typography build archive

The v11 scripts preserve the cloud execution paths /workspace/bmt_v11 and /workspace/research_source. They render the existing audited mathematics as editable Office Math with compact upright text labels/operators and measured complete-row relation alignment. Mathematical rows may outnumber the14/12 visibly numbered groups. A temporary LibreOffice profile controls PDF math base size; actual output is checked at12pt main/11pt supplement. Native Microsoft Word and WPS were not executed in this environment. No inference or resampling is rerun. Effective plans, typography diagnosis, current output hashes and final independent checks are under ../../Audit/typography_v11. Existing figure-build scripts and numerical-analysis Reproducibility content are preserved from v10. Historical evidence is retained as text/JSON under Audit/prior_v10 without changing its scope.
''')
    write_checklist(DEST / 'BMT_submission_checklist_v11.docx')
    status = {
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'revision': 'v11 mathematical typography',
        'source': 'submission/bmt_v10',
        'user_requested_formula_typography_revision_completed': True,
        'main_numbered_equation_groups': 14,
        'supplement_numbered_equation_groups': 12,
        'native_editable_office_math': True,
        'equation_rows_may_outnumber_numbered_groups': True,
        'native_word_or_wps_executed': False,
        'results_tables_figures_references_declaration_substance_changed': False,
        'main_tables_and_cells': [3, 66],
        'supplement_tables_and_cells': [19, 878],
        'post_hoc_and_nominal_interval_boundaries_retained': True,
        'prior_author_confirmation_scope_preserved': True,
        'journal_submission_executed': False,
        'final_documents_pending': False,
        'final_revision_qa_sha256': qa_hash,
        'locked_independent_reports': final['reports'],
        'independent_check_counts': {name: len(child.get('checks', [])) for name, child in children.items()},
        'upload_files': UPLOAD_FILES,
    }
    (DEST / 'Audit/typography_v11/version_status.json').write_text(json.dumps(status, ensure_ascii=False, indent=2) + '\n')
    files = [{'path': p.relative_to(DEST).as_posix(), 'bytes': p.stat().st_size, 'sha256': digest(p)} for p in sorted(DEST.rglob('*')) if p.is_file()]
    (DEST / 'FILE_MANIFEST.json').write_text(json.dumps({'files': files}, ensure_ascii=False, indent=2) + '\n')
    with zipfile.ZipFile(ZIP_PATH, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for rel in UPLOAD_FILES:
            z.write(DEST / rel, rel)
    assert ZIP_PATH.stat().st_size < SAFE_BLOB_BYTES, 'Split an oversized upload archive before uploading to GitHub'
    receipt = {'destination': str(DEST), 'files': len(files) + 1, 'zip': str(ZIP_PATH), 'zip_bytes': ZIP_PATH.stat().st_size, 'zip_sha256': digest(ZIP_PATH), 'final_revision_qa_sha256': qa_hash}
    (BASE / 'packaging_receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--execute', action='store_true')
    ap.add_argument('--qa-sha256')
    args = ap.parse_args()
    if not args.execute:
        print(json.dumps({'destination': str(DEST), 'outputs': OUTPUT_FILES, 'upload_files': UPLOAD_FILES, 'required_final_qa': str(FINAL_QA)}, indent=2))
        return
    assert args.qa_sha256 and len(args.qa_sha256) == 64
    package(args.qa_sha256)


if __name__ == '__main__':
    main()
