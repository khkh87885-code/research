#!/usr/bin/env python3
"""Format the approved supplement; retain exact tables and scientific prose.

Figure S6 is a separate publication-ready PDF so every supplemental file remains
below BMT's 10 MB limit without resampling clinical image pixels or mask arrays.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from zipfile import ZipFile

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Mm, Pt, RGBColor
from docx.table import Table
from docx.text.paragraph import Paragraph
import fitz

BASE = Path('/workspace/bmt_v9')
SOURCE = Path('/workspace/research_source/submission/bmt_v8_final/BMT_supplementary_material_v4.docx')
OUT = BASE / 'outputs'
FONT = 'Times New Roman'
CAP = json.loads((BASE / 'evidence/final_caption_updates.json').read_text())['supplement']
WIDTH = 6.89
DOCX = OUT / 'BMT_supplementary_material_v5.docx'
S6PDF = OUT / 'BMT_supplementary_Figure_S6_v5.pdf'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def font(run, size=11, bold=None):
    run.font.name = FONT
    run.font.size = Pt(size)
    run.font.color.rgb = RGBColor(0, 0, 0)
    if bold is not None:
        run.bold = bold
    r = run._r.get_or_add_rPr()
    rf = r.find(qn('w:rFonts'))
    if rf is None:
        rf = OxmlElement('w:rFonts')
        r.insert(0, rf)
    for v in ['ascii', 'hAnsi', 'cs', 'eastAsia']:
        rf.set(qn('w:' + v), FONT)


def fmt(p, size=11, bold=None, after=6, line=1.15, keep=False, page=False):
    old = p._p.find(qn('w:pPr'))
    if old is not None:
        p._p.remove(old)
    p.style = 'Normal'
    f = p.paragraph_format
    f.space_before = Pt(0)
    f.space_after = Pt(after)
    f.line_spacing = line
    f.keep_with_next = keep
    f.keep_together = True
    f.widow_control = True
    f.page_break_before = page
    f.alignment = WD_ALIGN_PARAGRAPH.LEFT
    for r in p.runs:
        font(r, size, bold)


def snapshot(d):
    return [[[c.text for c in row.cells] for row in t.rows] for t in d.tables]


def table_format(table, index):
    # Widths sum to 6.89 in; column widths reflect data precision and label length.
    widths = {
        0: [1.70, 5.19],
        1: [.55, 1.18, .50, 1.17, 1.17, .62, 1.70],
        2: [.75, 3.08, 1.20, 1.86],
        3: [.65, 1.55, 1.55, .82, 2.32],
        4: [1.25, 1.25, 1.38, 1.50, 1.51],
        5: [1.65, .60, 1.16, 1.16, 1.16, 1.16],
        6: [1.15, .45, 1.32, 1.32, 1.32, 1.33],
        7: [1.18, .86, .75, .45, 1.82, 1.83],
        8: [1.04, .85, .85, .80, .48, .80, .48, 1.59],
        9: [.67, 1.00, 1.00, 1.37, 1.42, 1.43],
        10: [.48, 1.03, 1.03, 1.03, 1.03, 1.14, 1.15],
        11: [.48, 1.03, 1.03, 1.03, 1.03, 1.14, 1.15],
        12: [.48, 1.03, 1.03, 1.03, 1.03, 1.14, 1.15],
        13: [.48, 1.03, 1.03, 1.03, 1.03, 1.14, 1.15],
        14: [.45, 2.25, .83, 1.02, 1.50, .84],
        15: [.50, 1.25, 1.71, 1.71, 1.72],
        16: [1.15, 1.26, 1.26, 1.26, .98, .98],
        17: [.72, .90, .90, 1.47, 1.60, 1.30],
        18: [.70, 1.28, 1.28, 1.10, 1.10, 1.43],
    }[index]
    assert abs(sum(widths)-WIDTH) < .001, (index, sum(widths))
    table.alignment = WD_TABLE_ALIGNMENT.LEFT
    table.autofit = False
    for c, w in zip(table.columns, widths):
        c.width = Inches(w)
    pr = table._tbl.tblPr
    for name in ('tblBorders', 'tblCellMar', 'tblInd'):
        for e in list(pr.findall(qn('w:' + name))):
            pr.remove(e)
    ind = OxmlElement('w:tblInd')
    ind.set(qn('w:w'), '0')
    ind.set(qn('w:type'), 'dxa')
    pr.append(ind)
    borders = OxmlElement('w:tblBorders')
    for name in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        b = OxmlElement('w:' + name)
        b.set(qn('w:val'), 'single' if name in ['top', 'bottom'] else 'nil')
        b.set(qn('w:sz'), '8')
        b.set(qn('w:color'), '000000')
        borders.append(b)
    pr.append(borders)
    margins = OxmlElement('w:tblCellMar')
    for name, val in [('top', 70), ('bottom', 70), ('left', 55), ('right', 55)]:
        e = OxmlElement('w:' + name)
        e.set(qn('w:w'), str(val))
        e.set(qn('w:type'), 'dxa')
        margins.append(e)
    pr.append(margins)
    for ri, row in enumerate(table.rows):
        tr = row._tr.get_or_add_trPr()
        for tag in ('cantSplit', 'tblHeader', 'trHeight'):
            for e in list(tr.findall(qn('w:' + tag))):
                tr.remove(e)
        tr.append(OxmlElement('w:cantSplit'))
        if ri == 0:
            tr.append(OxmlElement('w:tblHeader'))
        for ci, (cell, w) in enumerate(zip(row.cells, widths)):
            cell.width = Inches(w)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            cp = cell._tc.get_or_add_tcPr()
            for tag in ('shd', 'tcBorders', 'textDirection'):
                for e in list(cp.findall(qn('w:' + tag))):
                    cp.remove(e)
            if ri == 0:
                cb = OxmlElement('w:tcBorders')
                b = OxmlElement('w:bottom')
                b.set(qn('w:val'), 'single')
                b.set(qn('w:sz'), '6')
                cb.append(b)
                cp.append(cb)
            for p in cell.paragraphs:
                fmt(p, 9.5 if index in [8, 10, 11, 12, 13, 16, 18] else 10,
                    bold=ri == 0, after=1.5, line=1.08)
                if ri > 0 and index != 0 and ci > (1 if index in [1, 2, 5, 6, 7, 14, 15] else 0):
                    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.RIGHT


def add_picture(d, name, page=True):
    p = d.add_paragraph()
    fmt(p, after=8, keep=True, page=page)
    p.add_run().add_picture(str(BASE / f'outputs/Figures/Figure_{name}.png'), width=Inches(WIDTH))
    p = d.add_paragraph(f'Figure {name}. {CAP[name]}')
    fmt(p, size=10.5, after=8, line=1.12)


def build_docx():
    src = Document(SOURCE)
    d = Document()
    sec = d.sections[0]
    sec.page_width, sec.page_height = Mm(210), Mm(297)
    sec.left_margin = sec.right_margin = Mm(17.5)
    sec.top_margin = sec.bottom_margin = Mm(20)
    sec.header_distance = sec.footer_distance = Mm(9)
    for st in ['Normal', 'Heading 1', 'Caption']:
        d.styles[st].font.name = FONT
        d.styles[st].font.size = Pt(11)
        d.styles[st].font.color.rgb = RGBColor(0, 0, 0)
    # New package: no source relationships or unused legacy image parts are copied.
    p_index = {id(p._p): i for i, p in enumerate(src.paragraphs)}
    p_ids = {p._p: i for i, p in enumerate(src.paragraphs)}
    table_i = 0
    image_at = {11: 'S1', 17: 'S2', 96: 'S3', 99: 'S4', 102: 'S5'}
    skip = {12, 18, 97, 100, 103}
    # Scientific prose through paragraph 94 is copied character for character.
    # Only figure-specific closing blocks are replaced, because S6 is now external.
    section_starts = {5, 8, 13, 19, 25, 32, 38, 42, 46, 51, 56, 61,
                      66, 73, 78, 85, 91, 95, 98, 101}
    for el in src.element.body:
        if el.tag == qn('w:tbl'):
            new_el = deepcopy(el)
            d.element.body.insert(len(d.element.body)-1, new_el)
            table_format(Table(new_el, d._body), table_i)
            table_i += 1
            continue
        if el.tag != qn('w:p'):
            continue
        i = p_ids[el]
        if i >= 104:
            continue
        if i in image_at:
            add_picture(d, image_at[i], page=i in [11, 17])
            continue
        if i in skip:
            continue
        source_p = Paragraph(el, src._body)
        if not source_p.text.strip():
            continue
        new_el = deepcopy(el)
        d.element.body.insert(len(d.element.body)-1, new_el)
        p = Paragraph(new_el, d._body)
        text = p.text
        if i == 0:
            fmt(p, 16, True, after=8, keep=True)
        elif i == 1:
            fmt(p, 12, True, after=8, keep=True)
        elif i == 2:
            fmt(p, 11, after=14, keep=True)
        elif source_p.style.name.startswith('Heading'):
            fmt(p, 12 if source_p.style.name == 'Heading 1' else 11, True,
                after=8, keep=True, page=i in section_starts)
        elif text.startswith('Table S'):
            fmt(p, 11, True, after=5, keep=True, page=i == 29)
        else:
            fmt(p, 10.5 if source_p.style.name == 'Manuscript note' else 11,
                after=6, line=1.12)
    p = d.add_paragraph('Targeted CPU replay: all six cases')
    fmt(p, 12, True, after=10, keep=True, page=True)
    p = d.add_paragraph('Figure S6. ' + CAP['S6'])
    fmt(p, 10.5, after=10, line=1.15)
    p = d.add_paragraph('Figure S6 is supplied in the separate publication-ready file '
                        'BMT_supplementary_Figure_S6_v5.pdf. Panels A–C show the shared misses '
                        '(S6A); panels D–F show B-only detections (S6B), with one complete case per page.')
    fmt(p, 11)
    footer = sec.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = footer.add_run('Supplementary material • ')
    font(r, 9)
    r = footer.add_run()
    begin, instr, end = OxmlElement('w:fldChar'), OxmlElement('w:instrText'), OxmlElement('w:fldChar')
    begin.set(qn('w:fldCharType'), 'begin')
    instr.text = ' PAGE '
    end.set(qn('w:fldCharType'), 'end')
    for e in (begin, instr, end):
        r._r.append(e)
    font(r, 9)
    d.core_properties.title = 'Supplementary material — breast ultrasound segmentation quality control'
    d.core_properties.author = 'Haoze Lan; Ziyuan Zhu'
    d.core_properties.subject = 'Publication supplement: Tables S1–S13 and Figures S1–S6'
    d.save(DOCX)
    final = Document(DOCX)
    assert snapshot(src) == snapshot(final), 'A source table string changed'
    original_body = [p.text for i,p in enumerate(src.paragraphs)
                     if i < 95 and p.text.strip() and i not in skip and i not in image_at]
    final_texts = [p.text for p in final.paragraphs]
    assert all(t in final_texts for t in original_body), 'A scientific prose paragraph changed'
    with ZipFile(DOCX) as z:
        media = [n for n in z.namelist() if n.startswith('word/media/')]
    assert len(final.inline_shapes) == 5 and len(media) == 5
    assert DOCX.stat().st_size < 10_000_000
    return {'tables_equal': True, 'physical_tables': len(final.tables),
            'exact_table_cells': sum(len(row.cells) for t in final.tables for row in t.rows),
            'preserved_nonfigure_paragraphs': len(original_body), 'new_images': len(media),
            'orphaned_legacy_images': 0, 'source_sha256': sha(SOURCE),
            'final_docx_sha256': sha(DOCX), 'docx_bytes': DOCX.stat().st_size}


def build_s6_pdf():
    # Native PDFs are placed as PDF Form XObjects: image arrays and contour paths
    # are reused rather than screen-captured, resampled, or redrawn here.
    pdf = fitz.open()
    w, h = 210/25.4*72, 297/25.4*72
    margin = 17.5/25.4*72
    cases = [('A','089'), ('B','175'), ('C','238'), ('D','024'), ('E','105'), ('F','222')]
    asset_records = []
    for n, (letter, case) in enumerate(cases):
        path = BASE / f'layout_assets/Figure_S6_case_{letter}_case{case}.pdf'
        asset = fitz.open(path)
        page = pdf.new_page(width=w, height=h)
        page.insert_text((margin, 43), f'Supplementary Figure S6 — panel {letter} (case{case})',
                         fontname='hebo', fontsize=12)
        if n == 0:
            caption = 'Figure S6. ' + CAP['S6']
            rect = fitz.Rect(margin, 58, w-margin, 257)
            spare = page.insert_textbox(rect, caption, fontname='helv', fontsize=10.5, lineheight=1.18)
            assert spare >= 0, ('S6 caption did not fit', spare)
            top = 272
        else:
            descriptor = 'Shared screening miss' if n < 3 else 'Detected by method B only'
            page.insert_text((margin, 64), descriptor + '. Display and metric definitions follow panel A.',
                             fontname='helv', fontsize=10.5)
            top = 87
        rect = fitz.Rect(margin, top, w-margin, top + asset[0].rect.height)
        assert rect.y1 < h-45
        page.show_pdf_page(rect, asset, 0, keep_proportion=True)
        page.insert_text((margin, h-25), f'Supplementary Figure S6 • {n+1}/6',
                         fontname='helv', fontsize=9)
        asset_records.append({'case': 'case'+case, 'panel': letter, 'path': str(path),
                              'sha256': sha(path), 'embedded_width_in': rect.width/72,
                              'scale': rect.width/asset[0].rect.width})
        asset.close()
    pdf.set_metadata({'title': 'Supplementary Figure S6 — six-case targeted CPU replay',
                      'author': 'Haoze Lan; Ziyuan Zhu'})
    pdf.save(S6PDF, garbage=4, deflate=True, clean=True)
    pdf.close()
    assert S6PDF.stat().st_size < 10_000_000
    return {'file': str(S6PDF), 'bytes': S6PDF.stat().st_size, 'sha256': sha(S6PDF),
            'pages': 6, 'assets': asset_records,
            'native_pdf_placement': True, 'image_resampling': False}


def pdf_qa(path):
    d = fitz.open(path)
    outliers = []
    page_info = []
    for i, p in enumerate(d):
        text = p.get_text()
        blocks = p.get_text('dict')['blocks']
        spans = [s for b in blocks if 'lines' in b for l in b['lines'] for s in l['spans']]
        for s in spans:
            r = fitz.Rect(s['bbox'])
            if r.x0 < 4 or r.y0 < 4 or r.x1 > p.rect.width-4 or r.y1 > p.rect.height-4:
                outliers.append({'page': i+1, 'text': s['text'], 'bbox': list(r)})
        page_info.append({'page': i+1, 'chars': len(text), 'min_font_pt': min((s['size'] for s in spans), default=None),
                          'tables': [x for x in re.findall(r'Table S\d+(?: \(continued\))?', text)]})
    assert not outliers, outliers
    assert all(x['chars'] > 20 for x in page_info), 'Empty page'
    return {'pages': len(d), 'out_of_page_text': outliers, 'page_info': page_info}


if __name__ == '__main__':
    result = build_docx()
    if '--docx-only' in sys.argv:
        # Do not touch the already finalized standalone S6 PDF for a table typo.
        result['s6'] = json.loads((BASE/'evidence/supplement_layout_changes.json').read_text())['s6']
        assert sha(S6PDF) == result['s6']['sha256']
    else:
        result['s6'] = build_s6_pdf()
    subprocess.run(['soffice', '-env:UserInstallation=file:///tmp/bmt_supp_v9_layout_lo', '--headless',
                    '--convert-to', 'pdf', '--outdir', str(BASE/'qa'), str(DOCX)], check=True,
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    raw = BASE/'qa'/DOCX.with_suffix('.pdf').name
    preview = OUT/'BMT_supplementary_material_v5_preview.pdf'
    preview.write_bytes(raw.read_bytes())
    result['preview'] = {'path': str(preview), 'sha256': sha(preview), 'bytes': preview.stat().st_size,
                         **pdf_qa(preview)}
    result['s6']['qa'] = pdf_qa(S6PDF)
    (BASE/'evidence/supplement_layout_changes.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['s6','preview']}, ensure_ascii=False))
    print('Supplement main PDF pages:', result['preview']['pages'], '; separate S6 PDF pages:', result['s6']['pages'])
