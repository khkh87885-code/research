#!/usr/bin/env python3
"""Reformat the approved BMT v8 main manuscript without scientific revision.

The clean single-column review style is an editorial choice. It does not claim
to reproduce Word styles from the unavailable publisher research DOCX binary.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from zipfile import ZipFile

from lxml import etree

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Mm, Pt, RGBColor
from docx.text.paragraph import Paragraph

BASE = Path('/workspace/bmt_v9')
SOURCE = Path('/workspace/research_source/submission/bmt_v8_final/BMT_main_manuscript_v8.docx')
OUTPUT = BASE / 'outputs/BMT_main_manuscript_v9.docx'
EVIDENCE = BASE / 'evidence/manuscript_layout_changes.json'
CAPTIONS = BASE / 'evidence/final_caption_updates.json'
FONT = 'Times New Roman'
RUNNING_TITLE = 'Threshold transfer and review budgets'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def set_font(run, size=12, bold=None):
    run.font.name = FONT
    run.font.size = Pt(size)
    run.font.color.rgb = RGBColor(0, 0, 0)
    rpr = run._r.get_or_add_rPr()
    rf = rpr.find(qn('w:rFonts'))
    if rf is None:
        rf = OxmlElement('w:rFonts')
        rpr.insert(0, rf)
    for k in ('ascii', 'hAnsi', 'eastAsia', 'cs'):
        rf.set(qn('w:' + k), FONT)
    if bold is not None:
        run.bold = bold


def style_font(style, size, bold=False):
    style.font.name = FONT
    style.font.size = Pt(size)
    style.font.bold = bold
    style.font.color.rgb = RGBColor(0, 0, 0)
    rpr = style.element.get_or_add_rPr()
    rf = rpr.find(qn('w:rFonts'))
    if rf is None:
        rf = OxmlElement('w:rFonts')
        rpr.insert(0, rf)
    for k in ('ascii', 'hAnsi', 'eastAsia', 'cs'):
        rf.set(qn('w:' + k), FONT)


def paragraph_format(p, size=12, line=1.5, before=0, after=6,
                     keep_next=False, keep_lines=False, page_before=False,
                     bold=None, style='Normal'):
    # Start from a clean pPr to remove inherited v8 direct-layout remnants.
    old = p._p.find(qn('w:pPr'))
    if old is not None:
        p._p.remove(old)
    p.style = style
    pf = p.paragraph_format
    pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
    pf.left_indent = Pt(0)
    pf.right_indent = Pt(0)
    pf.first_line_indent = Pt(0)
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    pf.line_spacing = line
    pf.keep_with_next = keep_next
    pf.keep_together = keep_lines
    pf.page_break_before = page_before
    pf.widow_control = True
    for run in p.runs:
        set_font(run, size, bold)
    return p


def bold_prefix(p, prefix):
    """Apply a bold run label while preserving every character of the paragraph."""
    text = p.text
    assert text.startswith(prefix), (prefix, text)
    p.clear()
    a = p.add_run(text[:len(prefix)])
    set_font(a, 12, True)
    b = p.add_run(text[len(prefix):])
    set_font(b, 12, False)
    assert p.text == text


def add_field(p, field):
    r = p.add_run()
    begin = OxmlElement('w:fldChar')
    begin.set(qn('w:fldCharType'), 'begin')
    instr = OxmlElement('w:instrText')
    instr.set(qn('xml:space'), 'preserve')
    instr.text = f' {field} '
    separate = OxmlElement('w:fldChar')
    separate.set(qn('w:fldCharType'), 'separate')
    value = OxmlElement('w:t')
    value.text = '1'
    end = OxmlElement('w:fldChar')
    end.set(qn('w:fldCharType'), 'end')
    for element in (begin, instr, separate, value, end):
        r._r.append(element)
    set_font(r, 10)


def table_snapshot(doc):
    return [[[c.text for c in row.cells] for row in table.rows]
            for table in doc.tables]


def remove_orphan_images(doc):
    """Remove only image relationships unused by their owning XML part."""
    rel_ns = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
    removed = []
    for part in list(doc.part.package.parts):
        image_rels = [(rid, rel) for rid, rel in part.rels.items()
                      if rel.reltype.endswith('/image')]
        if not image_rels:
            continue
        root = etree.fromstring(part.blob)
        used = {v for e in root.iter() for k, v in e.attrib.items()
                if k.startswith(rel_ns)}
        for rid, rel in image_rels:
            if rid not in used:
                removed.append({'part': str(part.partname), 'relationship_id': rid,
                                'target': rel.target_ref})
                part.drop_rel(rid)
                assert rid not in part.rels
    return removed


def package_image_audit(path, expected_paths=()):
    """Validate XML relationship references and exact embedded media bytes."""
    d = Document(path)
    rel_ns = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
    for part in d.part.package.parts:
        if 'xml' not in part.content_type:
            continue
        root = etree.fromstring(part.blob)
        for e in root.iter():
            for key, rid in e.attrib.items():
                if key.startswith(rel_ns):
                    assert rid in part.rels, (str(part.partname), rid, 'unresolved XML relationship')
    with ZipFile(path) as z:
        media = [n for n in z.namelist() if n.startswith('word/media/')]
        hashes = sorted(hashlib.sha256(z.read(n)).hexdigest() for n in media)
    expected_hashes = sorted(digest(p) for p in expected_paths)
    assert hashes == expected_hashes, 'Embedded media differ from the expected final new images'
    return {'media_file_count': len(media), 'media_files': media,
            'embedded_media_sha256': hashes, 'all_explicit_xml_relationships_resolve': True,
            'embedded_media_exactly_match_expected_final_figures': True}


def format_table(table, table_index):
    table.alignment = WD_TABLE_ALIGNMENT.LEFT
    table.autofit = False
    widths = [
        [1.77, 0.80, 0.77, 0.86, 2.07],
        [1.22, 0.45, 1.68, 1.35, 0.57, 0.80],
        [1.14, 3.04, 0.94, 1.15],
    ][table_index]
    # All grid widths sum to the A4 text width (~6.27 in); no vertical rules.
    for col, width in zip(table.columns, widths):
        col.width = Inches(width)
    pr = table._tbl.tblPr
    borders = pr.find(qn('w:tblBorders'))
    if borders is not None:
        pr.remove(borders)
    borders = OxmlElement('w:tblBorders')
    for name in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        b = OxmlElement('w:' + name)
        b.set(qn('w:val'), 'single' if name in ('top', 'bottom') else 'nil')
        b.set(qn('w:sz'), '8')
        b.set(qn('w:color'), '000000')
        borders.append(b)
    pr.append(borders)
    margins = pr.find(qn('w:tblCellMar'))
    if margins is not None:
        pr.remove(margins)
    margins = OxmlElement('w:tblCellMar')
    for name, val in [('top', 95), ('bottom', 95), ('left', 70), ('right', 70)]:
        v = OxmlElement('w:' + name)
        v.set(qn('w:w'), str(val))
        v.set(qn('w:type'), 'dxa')
        margins.append(v)
    pr.append(margins)
    for ri, row in enumerate(table.rows):
        trpr = row._tr.get_or_add_trPr()
        cant = OxmlElement('w:cantSplit')
        trpr.append(cant)
        if ri == 0:
            repeat = OxmlElement('w:tblHeader')
            trpr.append(repeat)
        for ci, (cell, width) in enumerate(zip(row.cells, widths)):
            cell.width = Inches(width)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            tcpr = cell._tc.get_or_add_tcPr()
            for name in ('shd', 'tcBorders'):
                for e in list(tcpr.findall(qn('w:' + name))):
                    tcpr.remove(e)
            if ri == 0:
                cb = OxmlElement('w:tcBorders')
                bottom = OxmlElement('w:bottom')
                bottom.set(qn('w:val'), 'single')
                bottom.set(qn('w:sz'), '6')
                bottom.set(qn('w:color'), '000000')
                cb.append(bottom)
                tcpr.append(cb)
            for p in cell.paragraphs:
                paragraph_format(p, size=10.5, line=1.12, after=0,
                                 keep_lines=True, bold=(ri == 0))
                # Label columns are left aligned; all numerical columns right aligned.
                numeric = ci > 0 if table_index == 0 else (ci >= 2)
                if table_index == 1 and ci == 1:
                    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
                elif numeric:
                    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.RIGHT


def illustrated_copy(main_path, legend_texts):
    """Optional reading copy; formal submission manuscript still has no inline figures."""
    from PIL import Image
    figures = [BASE / f'outputs/Figures/Figure_{n}.png' for n in range(1, 6)]
    missing = [str(p) for p in figures if not p.exists()]
    if missing:
        raise FileNotFoundError('All five new main figures are required: ' + ', '.join(missing))
    reading = Document(main_path)
    for n, (image_path, caption) in enumerate(zip(figures, legend_texts), 1):
        title = reading.add_paragraph(f'Figure {n}', style='Heading 1')
        paragraph_format(title, size=14, line=1.0, after=8, keep_next=True,
                         keep_lines=True, page_before=True, bold=True, style='Heading 1')
        p = reading.add_paragraph()
        paragraph_format(p, line=1.0, after=8, keep_next=True, keep_lines=True)
        p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        w, h = Image.open(image_path).size
        # Figure 5 is 8.425 in high at its 6.89 in source width. A 6.35 in
        # displayed height keeps its source minimum 8 pt labels above 6 pt.
        width = min(6.2677, 6.35 * w / h)
        p.add_run().add_picture(str(image_path), width=Inches(width))
        cp = reading.add_paragraph(caption, style='Figure legend')
        paragraph_format(cp, size=10.5, line=1.1, after=0,
                         keep_lines=True, style='Figure legend')
        # Caption is exactly the approved/new formal legend; only this reading
        # copy uses a compact caption size to keep each plate and legend together.
        prefix = caption.split('.', 1)[0] + '.'
        text = cp.text
        cp.clear()
        set_font(cp.add_run(text[:len(prefix)]), 10.5, True)
        set_font(cp.add_run(text[len(prefix):]), 10.5, False)
    output = main_path.with_name(main_path.stem + '_illustrated.docx')
    reading.save(output)
    return {'path': str(output), 'sha256': digest(output),
            'purpose': 'Optional reading copy with five new main figures and repeated exact legends at the end',
            'formal_submission_file': str(main_path),
            'added_figure_plates': [str(p) for p in figures],
            'plate_caption_style': '10.5 pt, 1.1 lines; chosen compact reading-copy style',
            'image_package_audit': package_image_audit(output, figures)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, default=SOURCE)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    parser.add_argument('--illustrated', action='store_true',
                        help='Also create reading copy with all five final main PNG figures')
    args = parser.parse_args()
    source = Document(args.source)
    original_paragraphs = [p.text for p in source.paragraphs]
    original_tables = table_snapshot(source)
    doc = Document(args.source)
    ps = list(doc.paragraphs)
    source_style = {id(p._p): p.style.name for p in ps}
    style_font(doc.styles['Normal'], 12)
    for name, size, bold in [('Title', 16, True), ('Heading 1', 14, True),
                              ('Heading 2', 12, True), ('Title metadata', 12, False),
                              ('Caption', 12, True), ('Figure legend', 12, False),
                              ('Reference entry', 12, False), ('Manuscript note', 10.5, False)]:
        if name in doc.styles:
            style_font(doc.styles[name], size, bold)
    normal = doc.styles['Normal'].paragraph_format
    normal.alignment = WD_ALIGN_PARAGRAPH.LEFT
    normal.line_spacing = 1.5
    normal.space_before = Pt(0)
    normal.space_after = Pt(6)
    normal.first_line_indent = Pt(0)

    for section in doc.sections:
        section.page_width = Mm(210)
        section.page_height = Mm(297)
        section.top_margin = section.bottom_margin = Mm(25.4)
        section.left_margin = section.right_margin = Mm(25.4)
        section.header_distance = section.footer_distance = Mm(12.7)
        cols = section._sectPr.find(qn('w:cols'))
        if cols is None:
            cols = OxmlElement('w:cols')
            section._sectPr.append(cols)
        cols.set(qn('w:num'), '1')
        section.different_first_page_header_footer = False
        for container in (section.header, section.footer):
            for p in container.paragraphs:
                p._element.getparent().remove(p._element)
        h = section.header.add_paragraph(RUNNING_TITLE)
        paragraph_format(h, size=9, line=1.0, after=0)
        f = section.footer.add_paragraph()
        paragraph_format(f, size=10, line=1.0, after=0)
        f.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        add_field(f, 'PAGE')

    # Keep all original body strings. Front-matter labels and shared affiliation
    # superscripts alone are re-presented to give a conventional title page.
    title_mapping = {
        1: 'Running title: ' + RUNNING_TITLE,
        2: 'Haoze Lan*, Ziyuan Zhu',
        3: original_paragraphs[3].removeprefix('¹ '),
        4: 'Corresponding author: Haoze Lan; Email: 478283902@qq.com',
        5: original_paragraphs[5].replace('Institutional mailing address  ', 'Mailing address: ', 1),
        6: 'Ziyuan Zhu; Email: zzy2630816871@gmail.com',
        7: 'ORCID: Haoze Lan: https://orcid.org/0009-0008-5089-5902',
    }
    for i, text in title_mapping.items():
        ps[i].text = text
    # Running title follows the contact block rather than interrupting the byline.
    ps[7]._p.addnext(ps[1]._p)

    caption_updates = {}
    if CAPTIONS.exists():
        raw = json.loads(CAPTIONS.read_text())
        caption_updates = raw.get('main', {})
        for p in ps:
            match = re.match(r'^Figure (\d+)\.', p.text)
            if match and match.group(1) in caption_updates:
                new = caption_updates[match.group(1)]
                p.text = new if new.startswith('Figure ') else f'Figure {match.group(1)}.  {new}'

    # Explicit Conclusions is supported by the transcribed research template.
    conclusion = ps[83].insert_paragraph_before('Conclusions', style='Heading 1')

    # Match the official declarations-template order and labels. Only these two
    # inline labels change; each declaration's substantive sentences stay exact.
    declaration_order = [86, 90, 87, 85, 89, 88, 91]
    declaration_labels = {
        85: 'Use of Large Language Models, AI and Machine Learning Tools',
        91: 'Data availability',
    }
    declaration_mapping = {}
    for i in declaration_order:
        old_label, substantive = original_paragraphs[i].split('. ', 1)
        new_label = declaration_labels.get(i, old_label)
        new_text = new_label + '. ' + substantive
        ps[i].text = new_text
        declaration_mapping[i] = {
            'source_paragraph_index': i, 'before_label': old_label,
            'after_label': new_label, 'substantive_text': substantive,
            'before': original_paragraphs[i], 'after': new_text,
        }
        ps[92]._p.addprevious(ps[i]._p)
    # This heading had no separate non-AI acknowledgment content.
    ps[84]._p.getparent().remove(ps[84]._p)

    for i, p in enumerate(ps):
        if i == 84:
            continue
        old_style = source_style[id(p._p)]
        paragraph_format(p)
        if i == 0:
            paragraph_format(p, size=16, line=1.15, after=18, bold=True,
                             keep_next=True, style='Title')
        elif i < 8:
            paragraph_format(p, size=12, line=1.15, after=10, keep_next=True,
                             bold=(i == 2), style='Title metadata')
            if i in (1, 4, 5, 7):
                prefix = p.text.split(':', 1)[0] + ':'
                bold_prefix(p, prefix)
            if i == 3:
                p.paragraph_format.space_after = Pt(18)
        elif old_style == 'Heading 1':
            paragraph_format(p, size=14, line=1.15, before=14, after=8,
                             keep_next=True, keep_lines=True, bold=True,
                             page_before=i in (8, 14, 108, 115), style='Heading 1')
        elif old_style == 'Heading 2':
            paragraph_format(p, size=12, line=1.15, before=12, after=6,
                             keep_next=True, keep_lines=True, bold=True,
                             style='Heading 2')
        elif old_style == 'Reference entry':
            paragraph_format(p, size=12, line=1.15, after=6, keep_lines=True,
                             style='Reference entry')
            p.paragraph_format.left_indent = Inches(0.25)
            p.paragraph_format.first_line_indent = Inches(-0.25)
        elif old_style == 'Caption':
            paragraph_format(p, size=12, line=1.15, before=6, after=8,
                             keep_next=True, keep_lines=True, bold=True,
                             page_before=i in (111, 113), style='Caption')
        elif old_style == 'Figure legend':
            paragraph_format(p, size=12, line=1.5, after=10,
                             keep_lines=True, style='Figure legend')
            bold_prefix(p, p.text.split('.', 1)[0] + '.')
        elif old_style == 'Manuscript note':
            paragraph_format(p, size=10.5, line=1.15, after=8,
                             keep_lines=True, style='Manuscript note')
        if i in range(9, 14):
            bold_prefix(p, original_paragraphs[i].split('  ', 1)[0])
        if i in range(85, 92):
            bold_prefix(p, p.text.split('.', 1)[0] + '.')
    paragraph_format(conclusion, size=14, line=1.15, before=14, after=8,
                     keep_next=True, keep_lines=True, bold=True, style='Heading 1')

    for ti, table in enumerate(doc.tables):
        format_table(table, ti)
    removed_orphan_images = remove_orphan_images(doc)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    doc.save(args.output)
    check = Document(args.output)
    final_paragraphs = [p.text for p in check.paragraphs]
    assert table_snapshot(check) == original_tables, 'Table-cell text changed'
    # Scientific body, references and table notes stay exact. Declarations are
    # explicitly mapped to the official order and labels above.
    expected_unchanged = original_paragraphs[8:84] + original_paragraphs[92:116]
    assert all(t in final_paragraphs for t in expected_unchanged), 'Approved scientific text changed'
    abstract_start = final_paragraphs.index('Abstract')
    legends_start = final_paragraphs.index('Figure legends')
    preserved_sequence = [t for t in final_paragraphs[abstract_start:legends_start+1]
                          if t != 'Conclusions']
    expected_sequence = (original_paragraphs[8:84]
                         + [declaration_mapping[i]['after'] for i in declaration_order]
                         + original_paragraphs[92:116])
    assert preserved_sequence == expected_sequence, 'Unexpected scientific or declaration paragraph order'
    original_statistical_text = '\n'.join(original_paragraphs[8:84])
    final_statistical_text = '\n'.join(preserved_sequence[:76])
    assert original_statistical_text == final_statistical_text
    numeric_pattern = r'(?<!\w)[+−-]?\d+(?:[.,]\d+)*(?:[eE][+−-]?\d+)?'
    original_numeric_tokens = re.findall(numeric_pattern, original_statistical_text)
    final_numeric_tokens = re.findall(numeric_pattern, final_statistical_text)
    assert original_numeric_tokens == final_numeric_tokens, 'Statistical numeric token changed'
    assert original_statistical_text.count('\u202f%') == final_statistical_text.count('\u202f%')
    for i, item in declaration_mapping.items():
        assert item['after'] in final_paragraphs
        assert item['after'].split('. ', 1)[1] == item['substantive_text']
        assert re.findall(numeric_pattern, item['before']) == re.findall(numeric_pattern, item['after'])
    # Reconstruct source-order labels only for an inspectable exact preservation
    # audit. Actual final presentation intentionally uses the official order.
    canonical_statistical_text = '\n'.join(
        preserved_sequence[:76] + [original_paragraphs[84]]
        + [declaration_mapping[i]['before_label'] + '. '
           + declaration_mapping[i]['after'].split('. ', 1)[1] for i in range(85, 92)])
    original_with_declarations = '\n'.join(original_paragraphs[8:92])
    assert canonical_statistical_text == original_with_declarations
    canonical_numeric_tokens = re.findall(numeric_pattern, canonical_statistical_text)
    expected_refs = original_paragraphs[93:108]
    final_refs = [p.text for p in check.paragraphs if p.style.name == 'Reference entry']
    assert final_refs == expected_refs and len(final_refs) == 15, 'Reference text changed'
    expected_legends = []
    for n, original in enumerate(original_paragraphs[116:121], 1):
        new = caption_updates.get(str(n), original)
        expected_legends.append(new if new.startswith('Figure ') else f'Figure {n}.  {new}')
    final_legends = [p.text for p in check.paragraphs if p.style.name == 'Figure legend']
    assert final_legends == expected_legends and len(final_legends) == 5, 'Figure legend mismatch'
    approval = 'All authors have accepted responsibility for the entire content of this manuscript and approved its submission.'
    assert any(approval in p for p in final_paragraphs)
    assert len(check.tables) == 3
    source_urls = re.findall(r'https?://\S+', '\n'.join(original_paragraphs[:116]))
    final_urls = re.findall(r'https?://\S+', '\n'.join(final_paragraphs[:-5]))
    assert all(url in final_urls for url in source_urls), 'A DOI/URL string changed'
    hyperlinks_before = [e.xml for e in source.element.xpath('//w:hyperlink')]
    hyperlinks_after = [e.xml for e in check.element.xpath('//w:hyperlink')]
    assert hyperlinks_before == hyperlinks_after, 'Hyperlink XML changed'
    report = {
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'source': str(args.source), 'source_sha256': digest(args.source),
        'output': str(args.output), 'output_sha256': digest(args.output),
        'source_status': 'Approved v8 final manuscript; no older review used as source',
        'official_source': 'official_format_requirements.json, checked 2026-11-06',
        'official_mandatory_implemented': [
            'First-page full names, corresponding-author asterisk, shared affiliation, complete approved mailing address, emails, ORCID, short title',
            'Structured abstract: Objectives, Methods, Results, Conclusions; keywords retained',
            'Unnumbered sentence-case headings and consistent hierarchy',
            'Statements between main text and References follow the official template order and labels; substantive approved wording retained',
            '15 Vancouver references with exact original DOI/URL strings',
            'Editable Tables 1–3, separate titles, notes, approximate placement markers; figure legends after references',
        ],
        'chosen_style_not_official_mandate': {
            'page': 'A4 portrait, 25.4 mm margins, single column',
            'body': 'Times New Roman 12 pt; 1.5 lines; left aligned; no first-line indent; 6 pt after',
            'title': '16 pt bold; 1.15 lines',
            'heading_1': '14 pt bold; 1.15 lines',
            'heading_2': '12 pt bold; 1.15 lines',
            'front_matter': 'Dedicated title page; Abstract on page 2; Introduction starts a new page; metadata 12 pt, 1.15 lines',
            'running_furniture': '9 pt short-title header, 10 pt continuous Arabic page field in footer',
            'references': '12 pt, 1.15 lines, 6 pt after, uniform 0.25 in hanging indent',
            'tables': 'One table per page; 10.5 pt; 1.12 lines; right-aligned numerical columns; horizontal outer/header rules; no vertical rules; no row splitting',
            'notes': '10.5 pt, 1.15 lines immediately after each table',
            'conclusions': 'Separate H1 before the original final summary paragraph; template-supported structural choice',
        },
        'template_limitation': 'Original Research Article DOCX binary not obtained; these are chosen review styles, not verified exact publisher Word styles.',
        'font_rendering_note': 'DOCX specifies Times New Roman. The local PDF renderer may substitute Liberation Serif where Times New Roman is unavailable; font substitution does not change the editable DOCX style.',
        'metadata_presentation_map': [
            {'source_index': i, 'before': original_paragraphs[i], 'after': text}
            for i, text in title_mapping.items()
        ],
        'content_verification': {
            'scientific_body_paragraphs_8_through_83_exactly_preserved': True,
            'scientific_body_paragraph_sequence_preserved': True,
            'references_tables_notes_exactly_preserved': True,
            'original_conclusion_paragraph_exactly_preserved': True,
            'author_responsibility_and_submission_approval_sentence_exactly_preserved': True,
            'references_exactly_preserved_count': 15,
            'reference_doi_characters_exact': True,
            'hyperlink_elements_before': len(hyperlinks_before),
            'hyperlink_elements_after': len(hyperlinks_after),
            'hyperlink_xml_unchanged': True,
            'editable_tables_count': 3,
            'table_cell_strings_identical': True,
            'table_cell_string_count': sum(len(r) for t in original_tables for r in t),
            'figure_legend_paragraph_count': len(final_legends),
            'figure_legend_strings_match_original_or_authorized_updates': True,
            'new_pending_approval_text_added': False,
            'statistical_text_sha256_before': hashlib.sha256(original_statistical_text.encode()).hexdigest(),
            'statistical_text_sha256_after': hashlib.sha256(final_statistical_text.encode()).hexdigest(),
            'statistical_numeric_token_count': len(original_numeric_tokens),
            'statistical_numeric_token_sequence_exact': True,
            'statistical_text_narrow_nbsp_percent_count': original_statistical_text.count('\u202f%'),
            'statistical_text_narrow_nbsp_percent_unchanged': True,
            'declaration_substantive_text_exact_each_paragraph': True,
            'declaration_numeric_tokens_exact_within_each_paragraph': True,
            'scientific_and_declaration_canonical_numeric_token_count': len(canonical_numeric_tokens),
            'canonical_source_order_numeric_token_sequence_exact': True,
            'canonical_source_order_text_sha256_before': hashlib.sha256(original_with_declarations.encode()).hexdigest(),
            'canonical_source_order_text_sha256_after': hashlib.sha256(canonical_statistical_text.encode()).hexdigest(),
            'canonical_audit_note': 'Canonical audit restores original declaration order/labels and the removed empty Acknowledgments heading solely to verify exact source content. Final presentation follows official order/labels; no substantive declaration sentences are changed.',
        },
        'declarations': {
            'final_order': [declaration_mapping[i]['after_label'] for i in declaration_order],
            'source_to_final_mapping': [declaration_mapping[i] for i in declaration_order],
            'removed_empty_heading': 'Acknowledgments',
            'authorization': 'Root integration task explicitly authorized declaration order and label normalization on 2026-11-06',
        },
        'caption_updates_file': str(CAPTIONS) if CAPTIONS.exists() else None,
        'final_caption_updates_applied': sorted(caption_updates),
        'caption_status': 'final update applied' if caption_updates else 'Original v8 captions retained pending root-provided final caption updates',
        'removed_orphan_image_relationships': removed_orphan_images,
        'formal_image_package_audit': package_image_audit(args.output),
        'no_actual_submission_performed': True,
        'pdf_review': {'status': 'awaiting separate PDF export and visual inspection'},
    }
    if args.illustrated:
        report['illustrated_reading_copy'] = illustrated_copy(args.output, final_legends)
    EVIDENCE.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'output':str(args.output),'table_cells_exact':True,
                      'references_exact':15,'caption_updates_applied':sorted(caption_updates)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
