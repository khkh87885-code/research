#!/usr/bin/env python3
"""Package the user-requested editable-equation revision after final math/layout QA.

The default action is a read-only plan. Execution requires the hash of root's
final combined QA report. No Git branch or journal action is performed here.
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
from lxml import etree

BASE = Path('/workspace/bmt_v10')
OUT = BASE / 'outputs'
SOURCE = Path('/workspace/research_source/submission/bmt_v9')
DEST = Path('/workspace/research_source/submission/bmt_v10')
ZIP_PATH = DEST.parent / 'BMT_v10_submission_files.zip'
MATH_QA = BASE / 'evidence/independent_mathematics_qa.json'
LAYOUT_QA = BASE / 'evidence/independent_layout_qa.json'
FINAL_QA = BASE / 'evidence/final_revision_qa.json'
SAFE_BLOB_BYTES = 12_300_000
SUPPLEMENT_BYTES = 10_000_000
MAIN = 'BMT_main_manuscript_v10.docx'
SUPP = 'BMT_supplementary_material_v6.docx'
S6 = 'BMT_supplementary_Figure_S6_v6.pdf'
OUTPUT_FILES = [
    MAIN, 'BMT_main_manuscript_v10_preview.pdf',
    'BMT_main_manuscript_v10_illustrated_preview.pdf',
    SUPP, 'BMT_supplementary_material_v6_preview.pdf', S6,
]
ANCILLARY = {
    'BMT_Ethical_and_Legal_Declarations_v9.docx': 'BMT_Ethical_and_Legal_Declarations_v10.docx',
    'BMT_cover_letter_v9.docx': 'BMT_cover_letter_v10.docx',
    'BMT_data_and_code_availability_v9.docx': 'BMT_data_and_code_availability_v10.docx',
    'BMT_reviewer_candidates.docx': 'BMT_reviewer_candidates.docx',
}
FIGURE_NAMES = [f'Figure_{x}' for x in range(1, 6)] + [f'Figure_S{x}' for x in range(1, 6)] + ['Figure_S6A', 'Figure_S6B']
UPLOAD_FILES = [
    MAIN, *[f'Figures/Figure_{x}.png' for x in range(1, 6)],
    'BMT_Ethical_and_Legal_Declarations_v10.docx', 'BMT_cover_letter_v10.docx',
    SUPP, S6, 'BMT_data_and_code_availability_v10.docx',
    'BMT_reviewer_candidates.docx', 'Additional_quality_control_metrics.csv',
    'Analysis/table_data/S13_all_48_comparisons_unrounded.csv', 'UPLOAD_FILE_MAP.md',
]

README = '''# BMT v10 可编辑数学公式修订

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
'''

UPLOAD_MAP = '''# BMT v10 正式上传文件清单

| 投稿系统类别 | 文件 |
| --- | --- |
| Main manuscript | BMT_main_manuscript_v10.docx，含14组可编辑编号公式 |
| Main figures | Figures/Figure_1.png至Figure_5.png，分别上传 |
| Ethical and legal declarations | BMT_Ethical_and_Legal_Declarations_v10.docx |
| Cover letter | BMT_cover_letter_v10.docx |
| Supplementary material 1 | BMT_supplementary_material_v6.docx：含12组补充公式、19个可编辑表格面板及图S1–S5；系统要求PDF时以对应PDF替代，不重复上传相同内容 |
| Supplementary material 2 | BMT_supplementary_Figure_S6_v6.pdf：六例逐页图S6，须与补充材料1一并上传 |
| Supplementary data | Additional_quality_control_metrics.csv；Analysis/table_data/S13_all_48_comparisons_unrounded.csv |
| Data availability, if requested separately | BMT_data_and_code_availability_v10.docx |
| Reviewer nominations | 按BMT_reviewer_candidates.docx六人信息录入，至少五名 |

两个补充文件各小于10MB；S6A为A–C，S6B为D–F。正式主稿含原生Office Math，公式可在Word中编辑。五幅主图仍单独提供600dpi PNG；图内数据与v9相同。

主稿PDF用于检查Word；illustrated阅读副本和BMT_v10_all_figures.pdf用于阅读，不与正式Word同时作为Main Document上传。提交ZIP包含上述15件上传文件，不含预览PDF、Audit、Analysis构建脚本或历史确认记录。既有作者与投稿事实声明实质不变；本轮公式修订已按用户请求完成，尚未执行期刊系统上传或最终提交。
'''

CHANGE_NOTE = '''# v10 数学表达修改说明

主稿新增14组编号公式，补充方法新增12组编号公式，全部为可编辑Office Math。方法说明对应调整12段，以统一符号并明确提示框几何、风险分数、低质量定义、阈值校准和等复核排序、效能指标、H1–H3、区间、bootstrap、Kitagawa及CPU误差的计算。补充数学方法说明零分母、关联修正、缺失层率、截止阈值与排序并列等边界，公式与既有源代码逐项核对。

结果和讨论、15条参考文献、作者声明实质、全部图件与表格数值保持。主稿三表66个单元格、补充19个表格面板878个单元格逐字相同；S6 PDF仅文件名变化、内容字节不变。没有进行新推理、重采样、数据收集或新的科学实验。

H1–H3保持原比较方向与区间；H2/H3及补充区间保持未经多重调整的名义性质。预算、bootstrap和诊断构成分解仍属事后分析，经验频率不等同于p值、后验或总体概率，Kitagawa分解保持描述性解释。公式不会把重采样次数变为新增患者，也不将CPU数值接近表述为未留存CUDA掩膜逐像素相同。

本轮按用户请求完成公式修订。既有作者声明与确认链沿用，历史记录保留原范围；未新增一次明确作者批准事实，未执行期刊投稿。正式上传文件见UPLOAD_FILE_MAP.md，原v9归档完整保留。
'''


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copy_file(src: Path, dst: Path) -> None:
    assert src.is_file(), src
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    assert digest(src) == digest(dst), (src, dst)


def lock_final_report(expected: str) -> tuple[dict, dict, dict]:
    assert FINAL_QA.is_file() and digest(FINAL_QA) == expected, 'Inspect combined final QA hash before packaging'
    report = json.loads(FINAL_QA.read_text())
    assert report.get('final_documents_pending') is False, f'Document QA is pending: {FINAL_QA}'
    assert report.get('status') == 'PASS', 'Combined final QA has not passed'
    children = []
    for name, expected_path in [('mathematics', MATH_QA), ('layout', LAYOUT_QA)]:
        item = report['reports'][name]
        path = Path(item['path'])
        if not path.is_absolute():
            path = BASE / path
        assert path.resolve() == expected_path.resolve(), f'Unexpected {name} QA location'
        assert digest(path) == item['sha256'], f'{name} QA changed after final review'
        children.append(json.loads(path.read_text()))
    return report, children[0], children[1]


def table_cells(doc: Document) -> list[str]:
    return [cell.text for table in doc.tables for row in table.rows for cell in row.cells]


def native_math_count(path: Path) -> int:
    with zipfile.ZipFile(path) as z:
        tree = etree.fromstring(z.read('word/document.xml'))
    return len(tree.findall('.//{http://schemas.openxmlformats.org/officeDocument/2006/math}oMath'))


def validate(qa_hash: str) -> tuple[dict, dict, dict, dict]:
    final, math, layout = lock_final_report(qa_hash)
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
        (MAIN, 'BMT_main_manuscript_v9.docx', 66, 3),
        (SUPP, 'BMT_supplementary_material_v5.docx', 878, 19),
    ]:
        doc, src = Document(OUT / filename), Document(SOURCE / old)
        assert len(doc.tables) == tables and len(table_cells(doc)) == count
        assert table_cells(doc) == table_cells(src), f'Table content changed: {filename}'
        assert native_math_count(OUT / filename) > 0, f'No editable math: {filename}'
    assert digest(OUT / S6) == digest(SOURCE / 'BMT_supplementary_Figure_S6_v5.pdf')
    for name in FIGURE_NAMES:
        for suffix in ('.png', '.pdf'):
            assert digest(OUT / 'Figures' / (name + suffix)) == digest(SOURCE / 'Figures' / (name + suffix))
    return final, math, layout, build


def write_checklist(path: Path) -> None:
    doc = Document(SOURCE / 'BMT_submission_checklist_v9.docx')
    changes = {
        0: 'v10 数学公式与投稿文件检查',
        2: '本轮按用户要求为主稿及补充方法增加可编辑公式。原v9归档保留，作者声明实质和既有确认记录范围不变；未执行期刊投稿。',
        6: '主稿14组、补充12组编号公式均为原生Office Math，已核对既有代码。结果、讨论、表格、参考文献、声明实质与全部12幅科研图不变；没有新推理、重采样或新增患者。',
        8: '主稿5图+3表共8项，摘要174词、15条参考文献。主表66个单元格及补充19表878个单元格逐字保留。PDF分页、公式边界和文件hash见Audit/equations_v10。',
        10: '既有全文责任与批准提交句、推荐审稿人无利益冲突、论文原创、无其他期刊投稿，以及免审、无经费和研究无利益冲突声明保留。未新增一次明确作者批准记录。',
        12: '按UPLOAD_FILE_MAP.md分别上传正式主稿、五主图、声明、投稿信、补充v6 Word和S6_v6 PDF，以及具名CSV。阅读副本、图册、Audit和构建脚本不作为公开补充材料整包上传。',
    }
    assert len(doc.paragraphs) > max(changes)
    for index, text in changes.items():
        doc.paragraphs[index].text = text
    doc.core_properties.title = 'BMT v10 submission file checklist'
    doc.core_properties.content_status = ''
    doc.core_properties.comments = ''
    doc.save(path)


def package(qa_hash: str) -> None:
    final, math, layout, build = validate(qa_hash)
    assert not DEST.exists() and not ZIP_PATH.exists(), 'Inspect existing v10 output rather than overwriting it'
    DEST.mkdir(parents=True)
    for filename in OUTPUT_FILES:
        copy_file(OUT / filename, DEST / filename)
    copy_file(SOURCE / 'BMT_v9_all_figures.pdf', DEST / 'BMT_v10_all_figures.pdf')
    for old, new in ANCILLARY.items():
        copy_file(SOURCE / old, DEST / new)
    copy_file(SOURCE / 'Additional_quality_control_metrics.csv', DEST / 'Additional_quality_control_metrics.csv')
    shutil.copytree(SOURCE / 'Analysis', DEST / 'Analysis', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    shutil.copytree(SOURCE / 'Reproducibility', DEST / 'Reproducibility', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    for name in FIGURE_NAMES:
        for suffix in ('.png', '.pdf'):
            copy_file(SOURCE / 'Figures' / (name + suffix), DEST / 'Figures' / (name + suffix))
    # Text-only prior audit chain; template and document binaries remain in v9.
    for p in (SOURCE / 'Audit').rglob('*'):
        if p.is_file() and p.suffix in ('.json', '.md', '.txt'):
            copy_file(p, DEST / 'Audit/prior_v9' / p.relative_to(SOURCE / 'Audit'))
    copy_file(SOURCE / 'FILE_MANIFEST.json', DEST / 'Audit/prior_v9/FILE_MANIFEST_v9.json')
    copy_file(SOURCE / 'README_zh.md', DEST / 'Audit/prior_v9/README_v9_zh.md')
    copy_file(SOURCE / 'UPLOAD_FILE_MAP.md', DEST / 'Audit/prior_v9/UPLOAD_FILE_MAP_v9.md')
    for p in (BASE / 'evidence').iterdir():
        if p.is_file() and p.suffix in ('.json', '.md', '.txt'):
            copy_file(p, DEST / 'Audit/equations_v10' / p.name)
        elif p.is_file() and p.suffix == '.py':
            copy_file(p, DEST / 'Analysis/equations_v10' / p.name)
    for subdir in ('scripts', 'qa'):
        for p in (BASE / subdir).rglob('*.py'):
            if '__pycache__' not in p.parts:
                copy_file(p, DEST / 'Analysis/equations_v10' / p.relative_to(BASE / subdir))
    (DEST / 'README_zh.md').write_text(README)
    (DEST / 'UPLOAD_FILE_MAP.md').write_text(UPLOAD_MAP)
    (DEST / 'BMT_revision_note_v10_zh.md').write_text(CHANGE_NOTE)
    (DEST / 'Analysis/equations_v10/README.md').write_text('''# Editable-equation build archive

The v10 scripts preserve the cloud execution paths /workspace/bmt_v10 and /workspace/research_source. They replace only audited method-paragraph anchors and add the mathematical-methods supplement, generating native Office Math from audited TeX through Pandoc. They do not rerun inference or resampling. Effective plans, current build hashes and final mathematical/layout checks are under ../../Audit/equations_v10. Existing figure-build scripts and portable numerical-analysis Reproducibility content are preserved from v9. Historical source/approval evidence is retained as text/JSON under Audit/prior_v9 without changing its scope.
''')
    write_checklist(DEST / 'BMT_submission_checklist_v10.docx')
    status = {
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'revision': 'v10 editable mathematical methods',
        'source': 'submission/bmt_v9',
        'user_requested_formula_revision_completed': True,
        'main_numbered_equation_groups': 14,
        'supplement_numbered_equation_groups': 12,
        'native_editable_office_math': True,
        'results_tables_figures_references_declaration_substance_changed': False,
        'main_tables_and_cells': [3, 66],
        'supplement_tables_and_cells': [19, 878],
        'post_hoc_and_nominal_interval_boundaries_retained': True,
        'new_explicit_author_approval_record_created': False,
        'prior_author_confirmation_scope_preserved': True,
        'journal_submission_executed': False,
        'final_documents_pending': False,
        'final_revision_qa_sha256': qa_hash,
        'mathematics_qa_sha256': final['reports']['mathematics']['sha256'],
        'layout_qa_sha256': final['reports']['layout']['sha256'],
        'mathematics_checks_passed': len(math.get('checks', [])),
        'layout_checks_passed': len(layout.get('checks', [])),
        'upload_files': UPLOAD_FILES,
    }
    (DEST / 'Audit/equations_v10/version_status.json').write_text(json.dumps(status, ensure_ascii=False, indent=2) + '\n')
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
