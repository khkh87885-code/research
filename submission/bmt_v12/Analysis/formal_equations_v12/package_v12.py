#!/usr/bin/env python3
"""Package the concise formal-equation revision after final independent QA.

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

BASE = Path('/workspace/bmt_v12')
OUT = BASE / 'outputs'
SOURCE = Path('/workspace/research_source/submission/bmt_v11')
DEST = Path('/workspace/research_source/submission/bmt_v12')
ZIP_PATH = DEST.parent / 'BMT_v12_submission_files.zip'
FINAL_QA = BASE / 'evidence/final_revision_qa.json'
SAFE_BLOB_BYTES = 12_300_000
SUPPLEMENT_BYTES = 10_000_000
MAIN = 'BMT_main_manuscript_v12.docx'
SUPP = 'BMT_supplementary_material_v8.docx'
S6 = 'BMT_supplementary_Figure_S6_v8.pdf'
OUTPUT_FILES = [
    MAIN, 'BMT_main_manuscript_v12_preview.pdf',
    'BMT_main_manuscript_v12_illustrated_preview.pdf',
    SUPP, 'BMT_supplementary_material_v8_preview.pdf', S6,
]
OPTIONAL_REVIEW_FILES = ['BMT_formula_layout_proof_v12.pdf']
ANCILLARY = {
    'BMT_Ethical_and_Legal_Declarations_v11.docx': 'BMT_Ethical_and_Legal_Declarations_v12.docx',
    'BMT_cover_letter_v11.docx': 'BMT_cover_letter_v12.docx',
    'BMT_data_and_code_availability_v11.docx': 'BMT_data_and_code_availability_v12.docx',
    'BMT_reviewer_candidates.docx': 'BMT_reviewer_candidates.docx',
}
FIGURE_NAMES = [f'Figure_{x}' for x in range(1, 6)] + [f'Figure_S{x}' for x in range(1, 6)] + ['Figure_S6A', 'Figure_S6B']
UPLOAD_FILES = [
    MAIN, *[f'Figures/Figure_{x}.png' for x in range(1, 6)],
    'BMT_Ethical_and_Legal_Declarations_v12.docx', 'BMT_cover_letter_v12.docx',
    SUPP, S6, 'BMT_data_and_code_availability_v12.docx',
    'BMT_reviewer_candidates.docx', 'Additional_quality_control_metrics.csv',
    'Analysis/table_data/S13_all_48_comparisons_unrounded.csv', 'UPLOAD_FILE_MAP.md',
]

README = '''# BMT v12 精简正式公式稿

[正式主稿 Word](BMT_main_manuscript_v12.docx) · [正式主稿 PDF](BMT_main_manuscript_v12_preview.pdf) · [含图阅读版 PDF](BMT_main_manuscript_v12_illustrated_preview.pdf) · [全部图件 PDF](BMT_v12_all_figures.pdf) · [上传清单](UPLOAD_FILE_MAP.md)

本轮将显示公式从26组精简为5组：主稿仅保留Dice、风险A与风险B三式(1)–(3)；补充材料仅保留Kitagawa的构成项C和层内率项W两式(S1)–(S2)。恢复以文字解释为主的方法骨架，其余21组显示公式改为精确文字定义、已引用的标准方法和可核查代码说明。没有在补充材料中另行堆放被删公式。

五式采用原生Office Math的独立公式结构，保留分式、求和和上下标，可在文档中编辑。公式居中、组号位于右侧；无边框公式排版容器与科学数据表分开识别。论文仍是三张主数据表、19个补充数据表面板，不把公式容器新增编号为Table4–6。

本轮参考BMT作者指南、NIST科学符号字体说明和Microsoft Word公式帮助，变量与描述标签使用恰当字体，并检查实际PDF呈现。官方来源内容保存在Audit/formal_equations_v12；主稿三式、补充两式的数量，以及本版居中、右侧编号和具体字号，均是此次编辑选择，没有表述为BMT的强制规定。

结果与讨论、三主表66个单元格、19个补表面板878个单元格、15条参考文献、作者声明实质及全部12幅科研图保持。主稿仍有5图+3表共8项、174词摘要。原H1–H3比较与区间、H2/H3及补充比较的名义区间性质、预算/bootstrap/诊断构成分析的事后性质均保留。Kitagawa两式用于描述性分账，未引入因果归因；未运行新推理、重采样或新增实验。

正式补充材料仍为两件，各小于10MB：

- [补充材料Word](BMT_supplementary_material_v8.docx)，或[PDF预览](BMT_supplementary_material_v8_preview.pdf)。内含两式、原表格和图S1–S5，以及S6总图注和文件指引。
- [六例逐页图S6 PDF](BMT_supplementary_Figure_S6_v8.pdf)。与v11的S6内容逐字节相同，仅文件名及主补充文档中的指向升级；S6A为A–C，S6B为D–F。

正式Word用于Main manuscript，五主图逐幅另传。含图阅读版、图册及另附的BMT_formula_layout_proof_v12.pdf（如提供）仅供快速复检，不是投稿文件。当前检查覆盖DOCX结构及本环境导出的PDF；未实际运行Microsoft Word或WPS，因此未声称已验证所有跨软件排版兼容性。

现有作者、机构及投稿事实声明沿用，原v11归档完整保留；尚未执行期刊系统上传或投稿。构建与检查脚本位于Analysis/formal_equations_v12，取舍方案、官方来源、有效数学结构与最终独立检查在Audit/formal_equations_v12。旧官方证据和确认链的文本/JSON副本位于Audit/prior_v11，原始二进制资料仍在历史归档。Reproducibility、表格CSV和科研图源沿用。Audit、构建脚本、历史记录和阅读预览不作为公开补充材料整包上传。
'''

UPLOAD_MAP = '''# BMT v12 正式上传文件清单

| 投稿系统类别 | 文件 |
| --- | --- |
| Main manuscript | BMT_main_manuscript_v12.docx：仅三式核心数学定义，原生可编辑独立公式 |
| Main figures | Figures/Figure_1.png至Figure_5.png，分别上传 |
| Ethical and legal declarations | BMT_Ethical_and_Legal_Declarations_v12.docx |
| Cover letter | BMT_cover_letter_v12.docx |
| Supplementary material 1 | BMT_supplementary_material_v8.docx：两式Kitagawa定义、19个可编辑数据表面板及图S1–S5；系统要求PDF时用对应PDF替代，不重复上传相同内容 |
| Supplementary material 2 | BMT_supplementary_Figure_S6_v8.pdf：六例逐页图S6，须与补充材料1一并上传 |
| Supplementary data | Additional_quality_control_metrics.csv；Analysis/table_data/S13_all_48_comparisons_unrounded.csv |
| Data availability, if requested separately | BMT_data_and_code_availability_v12.docx |
| Reviewer nominations | 按BMT_reviewer_candidates.docx六人信息录入，至少五名 |

两个补充文件各小于10MB。显示公式仅3+2组，原生可编辑；Word内部的无边框公式排版容器不计入论文数据表。数据表仍为主稿3张、补充19个面板；五主图为600dpi PNG，与此前图件相同。

正式PDF用于核对当前环境导出的Word呈现；Word/WPS未在本环境实际运行，未声称跨软件排版均已验证。公式页快速预览BMT_formula_layout_proof_v12.pdf（如提供）、illustrated阅读副本及图册均仅供复检，不作为投稿文件，不与正式Word同时作为Main Document上传。ZIP仍包含上述15件上传文件，不含公式预览、其他预览PDF、Audit、构建脚本或历史记录。现有作者与投稿事实声明实质不变，尚未执行期刊系统上传或最终提交。
'''

CHANGE_NOTE = '''# v12 公式精简与正式排版说明

显示公式由原26组减为5组：主稿保留Dice、风险A和风险B三式，补充仅保留Kitagawa构成项与层内率项两式。其余公式改回精确文字、已引用的标准区间方法和可核查代码说明，恢复易读的方法骨架，没有转移到补充材料继续增加显示公式。

五式使用原生Office Math独立公式结构，包含可编辑的分式、求和和上下标。公式居中、编号右置，文字标签和变量的字体分工清楚。BMT、NIST与Microsoft官方来源及适用范围已归档；3+2的取舍、居中、编号位置及具体字号属于本次编辑选择，未声称是BMT强制要求。当前核验覆盖文档结构和本环境PDF，未实际运行Word/WPS。

公式的无边框排版容器不属于科学数据表，不新增Table4–6。主稿三数据表66个单元格、补充19个数据表面板878个单元格逐字保留；结果、讨论、15条参考文献、作者声明实质和12幅图均保持。S6 PDF只改文件名，内容字节不变；主补充文档指向同步到v8。

原H1–H3比较、区间及名义/事后分析边界保持；Kitagawa分解仍为描述性解释。没有新推理、重采样、数据收集或新的科学实验。现有声明事实沿用，原v11和历史记录保留，尚未执行期刊投稿。正式上传内容见UPLOAD_FILE_MAP.md。
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


def check_equation_layouts(path: Path, expected_labels: list[str]) -> dict:
    doc = Document(path)
    layouts = [table for table in doc.tables if equation_layout_label(table) is not None]
    labels = [equation_layout_label(table) for table in layouts]
    assert labels == expected_labels, f'Display group sequence differs: {path}'
    for table, label in zip(layouts, expected_labels):
        assert len(table.rows) == 1 and len(table.columns) == 3, f'Equation container structure: {label}'
        assert table.rows[0].cells[2].text.strip() == '(' + label + ')', f'Visible equation number: {label}'
        center = table.rows[0].cells[1]._tc
        displays = center.findall('.//{' + M_NS + '}oMathPara')
        assert len(displays) == 1, f'Expected a true native display equation: {label}'
        assert displays[0].find('{' + M_NS + '}oMath') is not None, f'Display has no native editable math: {label}'
    with zipfile.ZipFile(path) as z:
        root = etree.fromstring(z.read('word/document.xml'))
    assert len(root.findall('.//{' + M_NS + '}oMathPara')) == len(expected_labels), 'Extra unnumbered displays remain'
    return {'labels': labels, 'layout_containers': len(layouts), 'true_display_math': len(expected_labels)}


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
        (MAIN, 'BMT_main_manuscript_v11.docx', 66, 3),
        (SUPP, 'BMT_supplementary_material_v7.docx', 878, 19),
    ]:
        doc, src = Document(OUT / filename), Document(SOURCE / old)
        data = scientific_tables(doc)
        old_data = scientific_tables(src)
        assert len(data) == tables and len(table_cells(data)) == count
        assert table_cells(data) == table_cells(old_data), f'Scientific table content changed: {filename}'
        assert native_math_count(OUT / filename) > 0, f'No editable math: {filename}'
        expected_labels = ['1', '2', '3'] if filename == MAIN else ['S1', 'S2']
        validated_layouts[filename] = check_equation_layouts(OUT / filename, expected_labels)
    main, old_main = Document(OUT / MAIN), Document(SOURCE / 'BMT_main_manuscript_v11.docx')
    references = lambda doc: [p.text for p in doc.paragraphs if re.match(r'^\d+\.  ', p.text)]
    assert len(references(main)) == 15 and references(main) == references(old_main), 'References changed'
    def result_and_declaration_text(doc):
        paragraphs = [p.text for p in doc.paragraphs]
        return paragraphs[paragraphs.index('Results'):paragraphs.index('References')]
    assert result_and_declaration_text(main) == result_and_declaration_text(old_main), 'Results/discussion/declarations changed'
    assert digest(OUT / S6) == digest(SOURCE / 'BMT_supplementary_Figure_S6_v7.pdf')
    for name in FIGURE_NAMES:
        for suffix in ('.png', '.pdf'):
            assert digest(OUT / 'Figures' / (name + suffix)) == digest(SOURCE / 'Figures' / (name + suffix))
    return final, children, files, validated_layouts


def write_checklist(path: Path) -> None:
    doc = Document(SOURCE / 'BMT_submission_checklist_v11.docx')
    changes = {
        0: 'v12 精简正式公式与投稿文件检查',
        2: '本轮按用户要求将26组显示公式精简为主稿3式、补充2式，并以原生独立公式排版。原v11归档保留，现有作者声明实质不变；未执行期刊投稿。',
        6: '五式均为原生Office Math独立公式，组号为1–3及S1–S2。其余数学说明改回精确文字及已有引用。结果、讨论、数据表、参考文献、声明实质与12幅图保持；没有新推理、重采样或新增患者。',
        8: '主稿5图+3张科学数据表共8项，摘要174词、15条参考文献。主数据表66个单元格及补充19个数据表面板878个单元格逐字保留。无边框公式容器不计入科学数据表。PDF及文件hash见Audit/formal_equations_v12。',
        10: '现有作者与机构、推荐审稿人无利益冲突、论文原创、无其他期刊投稿，以及免审、无经费和研究无利益冲突声明保留。公式检查覆盖本环境DOCX结构及PDF导出，未实际运行Word/WPS。',
        12: '按UPLOAD_FILE_MAP.md分别上传正式主稿、五主图、声明、投稿信、补充v8 Word和S6_v8 PDF，以及具名CSV。公式预览、阅读副本、图册、Audit和构建脚本不作为公开补充材料整包上传。',
    }
    assert len(doc.paragraphs) > max(changes)
    for index, text in changes.items():
        doc.paragraphs[index].text = text
    doc.core_properties.title = 'BMT v12 submission file checklist'
    doc.core_properties.content_status = ''
    doc.core_properties.comments = ''
    doc.save(path)


def package(qa_hash: str) -> None:
    final, children, outputs, validated_layouts = validate(qa_hash)
    assert not DEST.exists() and not ZIP_PATH.exists(), 'Inspect existing v12 output rather than overwriting it'
    DEST.mkdir(parents=True)
    for filename in outputs:
        copy_file(OUT / filename, DEST / filename)
    copy_file(SOURCE / 'BMT_v11_all_figures.pdf', DEST / 'BMT_v12_all_figures.pdf')
    for old, new in ANCILLARY.items():
        copy_file(SOURCE / old, DEST / new)
    copy_file(SOURCE / 'Additional_quality_control_metrics.csv', DEST / 'Additional_quality_control_metrics.csv')
    shutil.copytree(SOURCE / 'Analysis', DEST / 'Analysis', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    shutil.copytree(SOURCE / 'Reproducibility', DEST / 'Reproducibility', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    for name in FIGURE_NAMES:
        for suffix in ('.png', '.pdf'):
            copy_file(SOURCE / 'Figures' / (name + suffix), DEST / 'Figures' / (name + suffix))
    # Text-only prior audit chain; template and document binaries remain in v11.
    for p in (SOURCE / 'Audit').rglob('*'):
        if p.is_file() and p.suffix in ('.json', '.md', '.txt'):
            copy_file(p, DEST / 'Audit/prior_v11' / p.relative_to(SOURCE / 'Audit'))
    copy_file(SOURCE / 'FILE_MANIFEST.json', DEST / 'Audit/prior_v11/FILE_MANIFEST_v11.json')
    copy_file(SOURCE / 'README_zh.md', DEST / 'Audit/prior_v11/README_v11_zh.md')
    copy_file(SOURCE / 'UPLOAD_FILE_MAP.md', DEST / 'Audit/prior_v11/UPLOAD_FILE_MAP_v11.md')
    for p in (BASE / 'evidence').iterdir():
        if p.is_file() and p.suffix in ('.json', '.md', '.txt'):
            copy_file(p, DEST / 'Audit/formal_equations_v12' / p.name)
        elif p.is_file() and p.suffix == '.py':
            copy_file(p, DEST / 'Analysis/formal_equations_v12' / p.name)
    for filename in ('engine_findings.json', 'engine_findings.md', 'render_validation.json', 'engine_recommendation.md'):
        p = BASE / 'experiments/engine_agent' / filename
        if p.is_file():
            copy_file(p, DEST / 'Audit/formal_equations_v12/engine' / filename)
    for subdir in ('scripts', 'qa'):
        for p in (BASE / subdir).rglob('*.py'):
            if '__pycache__' not in p.parts:
                copy_file(p, DEST / 'Analysis/formal_equations_v12' / p.relative_to(BASE / subdir))
    (DEST / 'README_zh.md').write_text(README)
    (DEST / 'UPLOAD_FILE_MAP.md').write_text(UPLOAD_MAP)
    (DEST / 'BMT_revision_note_v12_zh.md').write_text(CHANGE_NOTE)
    (DEST / 'Analysis/formal_equations_v12/README.md').write_text('''# Concise formal-equation build archive

The v12 scripts preserve /workspace/bmt_v12 and /workspace/research_source execution paths. Three main definitions (Dice and risks A/B) plus two supplementary Kitagawa component definitions replace the previous26 display groups. Remaining methods use precise prose, existing references and archived implementation details. Each retained group uses native Office Math display structure in a borderless equation-layout container identified by tblCaption; these containers are excluded from scientific data-table counts. Visible labels are1–3 andS1–S2. Native Microsoft Word and WPS were not executed here. BMT instructions, NIST symbol-typeface guidance and Microsoft equation-help source material, their scope, final hashes and independent checks are under ../../Audit/formal_equations_v12. The five-group scope and chosen layout are editorial decisions, not a claimed BMT mandate. No inference or resampling is rerun; figure sources and numerical-analysis Reproducibility content are preserved from v11. Historical evidence remains as text/JSON under Audit/prior_v11 with its original scope.
''')
    write_checklist(DEST / 'BMT_submission_checklist_v12.docx')
    status = {
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'revision': 'v12 concise formal equations',
        'source': 'submission/bmt_v11',
        'user_requested_formula_simplification_and_formal_layout_completed': True,
        'main_numbered_equation_groups': 3,
        'supplement_numbered_equation_groups': 2,
        'native_editable_office_math': True,
        'previous_display_groups': 26,
        'retained_display_groups': 5,
        'true_native_display_math': True,
        'equation_layout_containers_are_not_scientific_data_tables': True,
        'validated_equation_layouts': validated_layouts,
        'native_word_or_wps_executed': False,
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
    (DEST / 'Audit/formal_equations_v12/version_status.json').write_text(json.dumps(status, ensure_ascii=False, indent=2) + '\n')
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
