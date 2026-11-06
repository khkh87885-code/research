#!/usr/bin/env python3
"""Repair v12 Office Math delimiters and remove equation-layout tables.

Scientific content, data tables, pictures and approved declarations are retained.
WPS is the reported failing viewer; this script does not claim to run WPS.
"""
from copy import deepcopy
from pathlib import Path
import hashlib
import importlib.util
import json
import shutil
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, Twips
from docx.text.paragraph import Paragraph

BASE = Path('/workspace/bmt_v13')
SRC = Path('/workspace/research_source/submission/bmt_v12')
OUT = BASE/'outputs'
OUT.mkdir(parents=True, exist_ok=True)
NS = {'m':'http://schemas.openxmlformats.org/officeDocument/2006/math',
      'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
spec = importlib.util.spec_from_file_location('fences', Path(__file__).parent/'native_fence_helpers.py')
fences = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fences)

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def bind_complete_summand(math, label):
    if label == '(3)':
        assert fences.bind_eq3_summand(math), 'Eq3 summand not bound'
    elif label in ('(S1)', '(S2)'):
        nary = math.find('.//m:nary', NS)
        assert nary is not None
        body = nary.find('m:e', NS)
        parent = nary.getparent()
        trailing = list(parent)[parent.index(nary)+1:]
        # The terminal period belongs to the sentence, not the summand.
        assert ''.join(trailing[-1].xpath('.//m:t/text()',namespaces=NS)) in ('.', ',')
        for item in trailing[:-1]:
            parent.remove(item)
            body.append(item)
        assert body.find('.//m:f', NS) is not None

def equation_paragraph(doc, table, size):
    label = table.cell(0,2).text.strip()
    math = deepcopy(table._tbl.find('.//m:oMath', NS))
    assert math is not None
    bind_complete_summand(math, label)
    e = OxmlElement('w:p')
    table._tbl.addprevious(e)
    p = Paragraph(e, doc._body)
    p.style = doc.styles['Normal']
    pf = p.paragraph_format
    pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
    pf.left_indent = pf.right_indent = Pt(0)
    pf.first_line_indent = Pt(0)
    pf.space_before = Pt(8)
    pf.space_after = Pt(8)
    pf.line_spacing = 1.15
    pf.keep_together = True
    pf.keep_with_next = False
    sec = doc.sections[0]
    width_twips = round((sec.page_width-sec.left_margin-sec.right_margin)/635)
    pf.tab_stops.add_tab_stop(Twips(round(width_twips/2)), WD_TAB_ALIGNMENT.CENTER)
    pf.tab_stops.add_tab_stop(Twips(width_twips), WD_TAB_ALIGNMENT.RIGHT)
    # Ordinary paragraph tabs avoid the WPS table editing grid.  Native inline
    # Office Math retains built-up fractions, limits, accents and subscripts.
    p.add_run('\t')
    p._p.append(math)
    p.add_run('\t'+label)
    for r in p.runs:
        r.font.name = 'Times New Roman'
        r.font.size = Pt(size)
    table._tbl.getparent().remove(table._tbl)
    return label

def repair(src, dst, size, expected):
    doc = Document(src)
    flattened = fences.flatten_fences(doc.element, size)
    tables = []
    for t in doc.tables:
        cap = t._tbl.tblPr.find(qn('w:tblCaption'))
        if cap is not None and cap.get(qn('w:val'), '').startswith('Equation layout '):
            tables.append(t)
    labels = [equation_paragraph(doc,t,size) for t in tables]
    assert labels == expected, labels
    for p in doc.paragraphs:
        for r in p.runs:
            if 'BMT_supplementary_Figure_S6_v8.pdf' in r.text:
                r.text = r.text.replace('BMT_supplementary_Figure_S6_v8.pdf','BMT_supplementary_Figure_S6_v9.pdf')
    assert not doc.element.findall('.//m:d',NS)
    assert not doc.element.findall('.//m:oMathPara',NS)
    doc.save(dst)
    return {'source':str(src),'output':str(dst),'sha256':digest(dst),
            'flattened_delimiters':flattened,'equation_labels':labels,
            'scientific_tables':len(doc.tables),'editable_math':True,
            'automatic_delimiter_objects':0,'layout_tables':0}

def profile(path,size):
    (path/'user').mkdir(parents=True,exist_ok=True)
    (path/'user/registrymodifications.xcu').write_text('''<?xml version="1.0" encoding="UTF-8"?><oor:items xmlns:oor="http://openoffice.org/2001/registry"><item oor:path="/org.openoffice.Office.Math/StandardFormat"><prop oor:name="BaseSize" oor:op="fuse"><value>'''+str(size)+'''</value></prop><prop oor:name="IndexSize" oor:op="fuse"><value>70</value></prop><prop oor:name="LimitsSize" oor:op="fuse"><value>70</value></prop></item></oor:items>''')

if __name__ == '__main__':
    reports = [
        repair(SRC/'BMT_main_manuscript_v12.docx', OUT/'BMT_main_manuscript_v13.docx',12,['(1)','(2)','(3)']),
        repair(SRC/'BMT_supplementary_material_v8.docx', OUT/'BMT_supplementary_material_v9.docx',11,['(S1)','(S2)']),
    ]
    # Rebuild the reading copy with the unchanged five main figure plates.
    old = Path('/workspace/bmt_v12/outputs/BMT_main_manuscript_v12_illustrated.docx')
    if old.exists():
        reports.append(repair(old, OUT/'BMT_main_manuscript_v13_illustrated.docx',12,['(1)','(2)','(3)']))
    else:
        raise FileNotFoundError('v12 illustrated DOCX required for exact repair')
    shutil.copy2(SRC/'BMT_supplementary_Figure_S6_v8.pdf',OUT/'BMT_supplementary_Figure_S6_v9.pdf')
    for kind,size in [('main',12),('supplement',11),('illustrated',12)]:
        profile(BASE/('lo_'+kind),size)
    report={'revision':'v13','known_failing_viewer':'WPS','direct_wps_tested':False,
            'fix':'Literal native-math parentheses; complete summands; ordinary paragraphs with center/right tabs; no layout tables',
            'documents':reports}
    (BASE/'evidence/repair_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
