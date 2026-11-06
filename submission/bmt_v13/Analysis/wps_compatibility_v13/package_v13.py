#!/usr/bin/env python3
"""Package the user-reported WPS equation-compatibility repair after final QA.

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

BASE = Path('/workspace/bmt_v13')
OUT = BASE / 'outputs'
SOURCE = Path('/workspace/research_source/submission/bmt_v12')
DEST = Path('/workspace/research_source/submission/bmt_v13')
ZIP_PATH = DEST.parent / 'BMT_v13_submission_files.zip'
FINAL_QA = BASE / 'evidence/final_revision_qa.json'
SAFE_BLOB_BYTES = 12_300_000
SUPPLEMENT_BYTES = 10_000_000
MAIN = 'BMT_main_manuscript_v13.docx'
SUPP = 'BMT_supplementary_material_v9.docx'
S6 = 'BMT_supplementary_Figure_S6_v9.pdf'
OUTPUT_FILES = [
    MAIN, 'BMT_main_manuscript_v13_preview.pdf',
    'BMT_main_manuscript_v13_illustrated_preview.pdf',
    SUPP, 'BMT_supplementary_material_v9_preview.pdf', S6,
]
OPTIONAL_REVIEW_FILES = ['BMT_formula_layout_proof_v13.pdf']
ANCILLARY = {
    'BMT_Ethical_and_Legal_Declarations_v12.docx': 'BMT_Ethical_and_Legal_Declarations_v13.docx',
    'BMT_cover_letter_v12.docx': 'BMT_cover_letter_v13.docx',
    'BMT_data_and_code_availability_v12.docx': 'BMT_data_and_code_availability_v13.docx',
    'BMT_reviewer_candidates.docx': 'BMT_reviewer_candidates.docx',
}
FIGURE_NAMES = [f'Figure_{x}' for x in range(1, 6)] + [f'Figure_S{x}' for x in range(1, 6)] + ['Figure_S6A', 'Figure_S6B']
UPLOAD_FILES = [
    MAIN, *[f'Figures/Figure_{x}.png' for x in range(1, 6)],
    'BMT_Ethical_and_Legal_Declarations_v13.docx', 'BMT_cover_letter_v13.docx',
    SUPP, S6, 'BMT_data_and_code_availability_v13.docx',
    'BMT_reviewer_candidates.docx', 'Additional_quality_control_metrics.csv',
    'Analysis/table_data/S13_all_48_comparisons_unrounded.csv', 'UPLOAD_FILE_MAP.md',
]

README = '''# BMT v13 WPS公式显示修订

[正式主稿 Word](BMT_main_manuscript_v13.docx) · [正式主稿 PDF](BMT_main_manuscript_v13_preview.pdf) · [含图阅读版 PDF](BMT_main_manuscript_v13_illustrated_preview.pdf) · [全部图件 PDF](BMT_v13_all_figures.pdf) · [上传清单](UPLOAD_FILE_MAP.md)

本轮处理用户WPS截图中的具体显示异常：Eq.(3)圆括号出现H/I样字形。针对该公式对象及同类结构，移除数学对象中的自动伸缩分隔符，改用原生数学文本中的普通ASCII圆括号；分式、求和和上下标仍为可编辑数学结构。五个公式布局表全部移除，改为普通公式段落，使用标准制表位居中公式并在右侧显示编号。

主稿仍仅保留Dice、风险A和风险B三式(1)–(3)，补充仍为Kitagawa的C和W两式(S1)–(S2)。本轮直接以v12为源，仅修公式对象和承载布局；方法文字、结果、讨论、15条参考文献、作者声明实质与12幅科研图保留。主稿有3张数据表66个单元格，补充有19个数据表面板878个单元格；文档不再含公式布局表。

本云端未实际运行WPS或Microsoft Word。当前核验覆盖DOCX原生结构、自动分隔符清除、普通括号字符、编号及本环境PDF呈现，未声称新版已经在WPS中实测通过。公式仍可编辑，PDF用于对照文档内容与版式。

原H1–H3结果与区间、H2/H3及补充比较的名义区间性质，以及预算/bootstrap/诊断构成分析的事后性质均保持。主稿仍是5图+3表共8项、174词摘要。Kitagawa两式仍用于描述性分账；未运行新推理、重采样或新增实验。

正式补充材料仍分两件，各小于10MB：

- [补充材料Word](BMT_supplementary_material_v9.docx)，或[PDF预览](BMT_supplementary_material_v9_preview.pdf)。含两式、原数据表和图S1–S5、S6图注及文件指引。
- [六例逐页图S6 PDF](BMT_supplementary_Figure_S6_v9.pdf)。与v12的S6逐字节相同，仅文件名及主补充文档中的指向升级；S6A为A–C，S6B为D–F。

正式Word用于Main manuscript，五主图逐幅另传。含图阅读版、图册及BMT_formula_layout_proof_v13.pdf（如提供）仅供复检，不作为投稿文件。现有作者、机构及投稿事实声明沿用，尚未执行期刊系统上传或最终提交。

完整v12目录和历史记录保持；本版仅附v12的文件清单、说明与上传索引，不递归复制旧审计树。新构建和检查脚本位于Analysis/wps_compatibility_v13，结构修正、当前文档hash和独立检查在Audit/wps_compatibility_v13；必要BMT/NIST/Microsoft官方来源复用于Audit/reference_sources。Reproducibility、CSV、图件与此前分析脚本沿用。Audit、构建脚本、历史索引和阅读预览不作为公开补充材料整包上传。
'''

UPLOAD_MAP = '''# BMT v13 正式上传文件清单

| 投稿系统类别 | 文件 |
| --- | --- |
| Main manuscript | BMT_main_manuscript_v13.docx：三式核心数学定义，普通段落承载原生可编辑公式 |
| Main figures | Figures/Figure_1.png至Figure_5.png，分别上传 |
| Ethical and legal declarations | BMT_Ethical_and_Legal_Declarations_v13.docx |
| Cover letter | BMT_cover_letter_v13.docx |
| Supplementary material 1 | BMT_supplementary_material_v9.docx：两式Kitagawa定义、19个可编辑数据表面板及图S1–S5；系统要求PDF时以对应PDF替代，不重复上传相同内容 |
| Supplementary material 2 | BMT_supplementary_Figure_S6_v9.pdf：六例逐页图S6，须与补充材料1一并上传 |
| Supplementary data | Additional_quality_control_metrics.csv；Analysis/table_data/S13_all_48_comparisons_unrounded.csv |
| Data availability, if requested separately | BMT_data_and_code_availability_v13.docx |
| Reviewer nominations | 按BMT_reviewer_candidates.docx六人信息录入，至少五名 |

两个补充文件各小于10MB。公式仍为3+2组，本版清除自动伸缩括号与公式布局表，保留可编辑分式、求和和上下标；主稿和补充的Word表格总数分别为3和19。五主图为600dpi PNG，与此前相同。

当前云端未实际运行WPS或Word；结构核验及PDF对照不等同于WPS运行验证。公式快速预览BMT_formula_layout_proof_v13.pdf（如提供）、其他预览PDF、illustrated阅读副本及图册仅供复检，不作为投稿文件，不与正式Word同时作为Main Document上传。ZIP仍为上述15件上传文件，不含Audit、构建脚本或历史索引。现有作者与投稿事实声明实质不变，尚未执行期刊系统上传或最终提交。
'''

CHANGE_NOTE = '''# v13 WPS公式结构修正说明

针对WPS截图中Eq.(3)括号呈现H/I样字形的异常，移除所有自动伸缩数学分隔符，改用原生数学文本的普通ASCII圆括号。五个公式布局表改为普通公式段落，用标准制表位居中公式、右置编号；保留可编辑分式、求和和上下标。

主稿三式与补充两式的数学内容保持，直接由v12修订，没有重写方法骨架。普通文字、结果、讨论、15条参考文献、作者声明实质与全部12幅科研图保持；主稿3表66个单元格、补充19表878个单元格逐字相同，文档不再包含公式布局表。S6 PDF仅改文件名，内容字节不变，主补充材料的文件指向同步到v9。

本环境未实际运行WPS或Microsoft Word，核验范围为原生DOCX结构与当前PDF，未声称WPS实测通过。原科学比较、区间、名义/事后分析边界均不变；没有新推理、重采样或新增实验。现有声明事实沿用，完整v12归档保留，尚未执行期刊投稿。
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


W_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
M_NS = 'http://schemas.openxmlformats.org/officeDocument/2006/math'


def equation_layout_label(table) -> str | None:
    caption = table._tbl.find('./{' + W_NS + '}tblPr/{' + W_NS + '}tblCaption')
    value = caption.get('{' + W_NS + '}val', '') if caption is not None else ''
    match = re.fullmatch(r'Equation layout \((S?\d+)\)', value)
    return match.group(1) if match else None


def scientific_tables(doc: Document) -> list:
    return [table for table in doc.tables if equation_layout_label(table) is None]


def table_cells(tables) -> list[str]:
    return [cell.text for table in tables for row in table.rows for cell in row.cells]


def native_math_count(path: Path) -> int:
    with zipfile.ZipFile(path) as z:
        tree = etree.fromstring(z.read('word/document.xml'))
    return len(tree.findall('.//{http://schemas.openxmlformats.org/officeDocument/2006/math}oMath'))


def equation_paragraph_label(p) -> str | None:
    if p.find('.//{' + M_NS + '}oMath') is None:
        return None
    texts = p.findall('{' + W_NS + '}r/{' + W_NS + '}t')
    value = (texts[-1].text or '').strip() if texts else ''
    match = re.fullmatch(r'\((S?\d+)\)', value)
    return match.group(1) if match else None


def check_equation_paragraphs(path: Path, expected_labels: list[str]) -> dict:
    with zipfile.ZipFile(path) as z:
        root = etree.fromstring(z.read('word/document.xml'))
    assert not root.findall('.//{' + M_NS + '}d'), f'Automatic delimiters remain: {path}'
    ps = root.findall('./{' + W_NS + '}body/{' + W_NS + '}p')
    equations = [p for p in ps if equation_paragraph_label(p) is not None]
    labels = [equation_paragraph_label(p) for p in equations]
    assert labels == expected_labels, f'Equation paragraph numbering differs: {path}'
    for p, label in zip(equations, labels):
        tabs = p.find('./{' + W_NS + '}pPr/{' + W_NS + '}tabs')
        values = [t.get('{' + W_NS + '}val') for t in tabs] if tabs is not None else []
        assert 'center' in values and 'right' in values, f'Center/right number stops missing: {label}'
    assert all(equation_layout_label(t) is None for t in Document(path).tables), 'Formula-layout table remains'
    return {'labels': labels, 'numbered_native_equation_paragraphs': len(labels),
            'automatic_delimiter_objects': 0, 'formula_layout_tables': 0}


def arithmetic_structure_counts(path: Path) -> dict:
    with zipfile.ZipFile(path) as z:
        root = etree.fromstring(z.read('word/document.xml'))
    return {name: len(root.findall('.//{' + M_NS + '}' + name))
            for name in ('f', 'nary', 'sSub', 'sSup', 'sSubSup')}


def ordinary_prose(doc: Document) -> list[str]:
    return [p.text for p in doc.paragraphs if p.text.strip() and equation_paragraph_label(p._p) is None]


def validate(qa_hash: str) -> tuple[dict, dict[str, dict], list[str], dict]:
    final, children = lock_final_report(qa_hash)
    # Root's combined review locks document bytes and child-report hashes. This
    # avoids imposing one historical schema or check count on independent QA.
    files = OUTPUT_FILES + [name for name in OPTIONAL_REVIEW_FILES if (OUT / name).is_file() or name in final['documents']]
    for filename in files:
        p = OUT / filename
        assert p.is_file(), p
        record = final['documents'][filename]
        assert record['sha256'] == digest(p), f'Final document hash mismatch: {filename}'
        assert record['bytes'] == p.stat().st_size, f'Final document length mismatch: {filename}'
        if filename.startswith('BMT_supplementary'):
            assert p.stat().st_size < SUPPLEMENT_BYTES, f'Supplement exceeds 10MB: {p}'
    validated_layouts = {}
    for filename, old, count, tables in [
        (MAIN, 'BMT_main_manuscript_v12.docx', 66, 3),
        (SUPP, 'BMT_supplementary_material_v8.docx', 878, 19),
    ]:
        doc, src = Document(OUT / filename), Document(SOURCE / old)
        assert len(doc.tables) == tables, f'Unexpected non-data table remains: {filename}'
        data = scientific_tables(doc)
        old_data = scientific_tables(src)
        assert len(data) == tables and len(table_cells(data)) == count
        assert table_cells(data) == table_cells(old_data), f'Scientific table content changed: {filename}'
        assert native_math_count(OUT / filename) > 0, f'No editable math: {filename}'
        expected_labels = ['1', '2', '3'] if filename == MAIN else ['S1', 'S2']
        validated_layouts[filename] = check_equation_paragraphs(OUT / filename, expected_labels)
        assert arithmetic_structure_counts(OUT / filename) == arithmetic_structure_counts(SOURCE / old), 'Fraction/sum/script structures changed'
        old_prose = ordinary_prose(src)
        if filename == SUPP:
            old_prose = [text.replace('BMT_supplementary_Figure_S6_v8.pdf', S6) for text in old_prose]
        assert ordinary_prose(doc) == old_prose, f'Ordinary source prose changed: {filename}'
    main, old_main = Document(OUT / MAIN), Document(SOURCE / 'BMT_main_manuscript_v12.docx')
    references = lambda doc: [p.text for p in doc.paragraphs if re.match(r'^\d+\.  ', p.text)]
    assert len(references(main)) == 15 and references(main) == references(old_main), 'References changed'
    def result_and_declaration_text(doc):
        paragraphs = [p.text for p in doc.paragraphs]
        return paragraphs[paragraphs.index('Results'):paragraphs.index('References')]
    assert result_and_declaration_text(main) == result_and_declaration_text(old_main), 'Results/discussion/declarations changed'
    assert digest(OUT / S6) == digest(SOURCE / 'BMT_supplementary_Figure_S6_v8.pdf')
    source_manifest = json.loads((SOURCE / 'FILE_MANIFEST.json').read_text())
    source_hashes = {item['path']: item['sha256'] for item in source_manifest['files']}
    for name in FIGURE_NAMES:
        for suffix in ('.png', '.pdf'):
            relative = 'Figures/' + name + suffix
            original_hash = digest(SOURCE / relative)
            assert original_hash == source_hashes[relative], f'Source figure differs from v12 manifest: {relative}'
            if (OUT / relative).is_file():
                assert digest(OUT / relative) == original_hash, f'Output figure changed: {relative}'
    return final, children, files, validated_layouts


def write_checklist(path: Path) -> None:
    doc = Document(SOURCE / 'BMT_submission_checklist_v12.docx')
    changes = {
        0: 'v13 WPS公式显示与投稿文件检查',
        2: '本轮针对WPS截图的括号异常修正公式对象，清除自动伸缩分隔符和公式布局表。直接以v12为源，原目录保留，现有作者声明实质不变；未执行期刊投稿。',
        6: '主稿3式、补充2式仍为原生可编辑数学。普通公式段落以标准制表位居中公式、右置编号。普通文字、结果、讨论、数据表、参考文献、声明实质和12幅图保持；没有新推理或新增实验。',
        8: '主稿5图+3表共8项，摘要174词、15条参考文献。Word表格总数恢复为主稿3、补充19，分别66/878个单元格逐字保留。结构核验与文件hash见Audit/wps_compatibility_v13。',
        10: '现有作者与机构、推荐审稿人无利益冲突、论文原创、无其他期刊投稿，以及免审、无经费和研究无利益冲突声明保留。公式检查覆盖本环境DOCX结构及PDF导出，未实际运行Word/WPS。',
        12: '按UPLOAD_FILE_MAP.md分别上传正式主稿、五主图、声明、投稿信、补充v9 Word和S6_v9 PDF，以及具名CSV。公式预览、阅读副本、图册、Audit和构建脚本不作为公开补充材料整包上传。',
    }
    assert len(doc.paragraphs) > max(changes)
    for index, text in changes.items():
        doc.paragraphs[index].text = text
    doc.core_properties.title = 'BMT v13 submission file checklist'
    doc.core_properties.content_status = ''
    doc.core_properties.comments = ''
    doc.save(path)


def package(qa_hash: str) -> None:
    final, children, outputs, validated_layouts = validate(qa_hash)
    assert not DEST.exists() and not ZIP_PATH.exists(), 'Inspect existing v13 output rather than overwriting it'
    DEST.mkdir(parents=True)
    for filename in outputs:
        copy_file(OUT / filename, DEST / filename)
    copy_file(SOURCE / 'BMT_v12_all_figures.pdf', DEST / 'BMT_v13_all_figures.pdf')
    for old, new in ANCILLARY.items():
        copy_file(SOURCE / old, DEST / new)
    copy_file(SOURCE / 'Additional_quality_control_metrics.csv', DEST / 'Additional_quality_control_metrics.csv')
    shutil.copytree(SOURCE / 'Analysis', DEST / 'Analysis', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    shutil.copytree(SOURCE / 'Reproducibility', DEST / 'Reproducibility', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    for name in FIGURE_NAMES:
        for suffix in ('.png', '.pdf'):
            copy_file(SOURCE / 'Figures' / (name + suffix), DEST / 'Figures' / (name + suffix))
    # Do not recursively duplicate the historical audit tree. The complete v12
    # archive remains in its original folder; retain only its small index here.
    copy_file(SOURCE / 'FILE_MANIFEST.json', DEST / 'Audit/prior_v12/FILE_MANIFEST_v12.json')
    copy_file(SOURCE / 'README_zh.md', DEST / 'Audit/prior_v12/README_v12_zh.md')
    copy_file(SOURCE / 'UPLOAD_FILE_MAP.md', DEST / 'Audit/prior_v12/UPLOAD_FILE_MAP_v12.md')
    for filename in ('bmt_official_mathematics_source.md', 'nist_official_mathematics_source.md',
                     'microsoft_official_equation_source.md', 'formal_equation_requirements.json'):
        copy_file(SOURCE / 'Audit/formal_equations_v12' / filename, DEST / 'Audit/reference_sources' / filename)
    for p in (BASE / 'evidence').iterdir():
        if p.is_file() and p.suffix in ('.json', '.md', '.txt'):
            copy_file(p, DEST / 'Audit/wps_compatibility_v13' / p.name)
        elif p.is_file() and p.suffix == '.py':
            copy_file(p, DEST / 'Analysis/wps_compatibility_v13' / p.name)
    for filename in ('engine_findings.json', 'engine_findings.md', 'render_validation.json', 'engine_recommendation.md'):
        p = BASE / 'experiments/engine_agent' / filename
        if p.is_file():
            copy_file(p, DEST / 'Audit/wps_compatibility_v13/engine' / filename)
    for subdir in ('scripts', 'qa'):
        for p in (BASE / subdir).rglob('*.py'):
            if '__pycache__' not in p.parts:
                copy_file(p, DEST / 'Analysis/wps_compatibility_v13' / p.relative_to(BASE / subdir))
    (DEST / 'README_zh.md').write_text(README)
    (DEST / 'UPLOAD_FILE_MAP.md').write_text(UPLOAD_MAP)
    (DEST / 'BMT_revision_note_v13_zh.md').write_text(CHANGE_NOTE)
    (DEST / 'Analysis/wps_compatibility_v13/README.md').write_text('''# Targeted WPS equation-compatibility build archive

The v13 scripts preserve /workspace/bmt_v13 and /workspace/research_source paths. They directly repair the v12 equation objects in response to the user's WPS screenshot: all automatic delimiter objects are removed in favor of ordinary native-math ASCII parentheses, and five formula-layout tables become standard equation paragraphs with center/right tab stops. Fractions, summations, scripts, group labels1–3/S1–S2 and all ordinary prose remain. Word/WPS were not executed here; structural checks and this environment's PDF are not represented as a WPS runtime test. New output hashes and independent checks are under ../../Audit/wps_compatibility_v13. Necessary official guidance is reused under Audit/reference_sources. The complete prior audit remains in bmt_v12; only a small source index is duplicated in Audit/prior_v12. No inference or resampling is rerun. Figure sources and numerical Reproducibility content are unchanged.
''')
    write_checklist(DEST / 'BMT_submission_checklist_v13.docx')
    status = {
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'revision': 'v13 targeted WPS equation compatibility repair',
        'source': 'submission/bmt_v12',
        'user_requested_wps_equation_repair_completed': True,
        'main_numbered_equation_groups': 3,
        'supplement_numbered_equation_groups': 2,
        'native_editable_office_math': True,
        'retained_display_groups': 5,
        'native_equation_paragraphs': True,
        'automatic_math_delimiters_removed': True,
        'formula_layout_tables_removed': True,
        'validated_equation_paragraphs': validated_layouts,
        'native_word_or_wps_executed': False,
        'user_reported_software': 'WPS',
        'results_tables_figures_references_declaration_substance_changed': False,
        'main_scientific_tables_and_cells': [3, 66],
        'supplement_scientific_tables_and_cells': [19, 878],
        'post_hoc_and_nominal_interval_boundaries_retained': True,
        'prior_author_confirmation_scope_preserved': True,
        'journal_submission_executed': False,
        'final_documents_pending': False,
        'final_revision_qa_sha256': qa_hash,
        'locked_independent_reports': final['reports'],
        'independent_check_counts': {name: len(child.get('checks', [])) for name, child in children.items()},
        'upload_files': UPLOAD_FILES,
    }
    (DEST / 'Audit/wps_compatibility_v13/version_status.json').write_text(json.dumps(status, ensure_ascii=False, indent=2) + '\n')
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
        print(json.dumps({'destination': str(DEST), 'outputs': OUTPUT_FILES, 'optional_review_files': OPTIONAL_REVIEW_FILES, 'upload_files': UPLOAD_FILES, 'required_final_qa': str(FINAL_QA)}, indent=2))
        return
    assert args.qa_sha256 and len(args.qa_sha256) == 64
    package(args.qa_sha256)


if __name__ == '__main__':
    main()
