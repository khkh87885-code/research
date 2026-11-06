"""Convert TeX math to editable Office Math via Pandoc; retain Word source styles."""
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.text.paragraph import Paragraph
from lxml import etree

NS = {'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
      'm':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
MATH_FONT = 'Latin Modern Math'

@lru_cache(maxsize=512)
def pandoc_paragraph(markdown):
    with TemporaryDirectory(prefix='bmt_v10_math_') as tmp:
        md=Path(tmp)/'fragment.md';dx=Path(tmp)/'fragment.docx'
        md.write_text(markdown)
        r=subprocess.run(['pandoc','--from=markdown+tex_math_dollars',str(md),'-o',str(dx)],capture_output=True,text=True)
        if r.returncode or r.stderr.strip():
            raise RuntimeError(f'Pandoc math conversion failed/warned: {r.stderr}\n{markdown}')
        with ZipFile(dx) as z:
            xml=etree.fromstring(z.read('word/document.xml'))
        ps=xml.findall('./w:body/w:p',NS)
        if len(ps)!=1:
            raise ValueError(f'Expected one paragraph, got {len(ps)}: {markdown}')
        return etree.tostring(ps[0])

def math_font_tree(element, size=12):
    # Pandoc 3.1.11 emits endChr before sepChr. Put delimiter properties in
    # schema order so LibreOffice retains the actual right bracket/bar.
    for dp in element.findall('.//m:dPr',NS):
        children=list(dp)
        order={'begChr':0,'sepChr':1,'endChr':2,'grow':3,'shp':4,'ctrlPr':5}
        for child in children:dp.remove(child)
        for child in sorted(children,key=lambda x:order.get(etree.QName(x).localname,99)):
            dp.append(child)
    for r in element.findall('.//m:r',NS):
        pr=r.find('w:rPr',NS)
        if pr is None:
            pr=OxmlElement('w:rPr')
            mpr=r.find('m:rPr',NS)
            r.insert(1 if mpr is not None else 0,pr)
        rf=pr.find(qn('w:rFonts'))
        if rf is None:
            rf=OxmlElement('w:rFonts');pr.insert(0,rf)
        for k in ['ascii','hAnsi','cs','eastAsia']:rf.set(qn('w:'+k),MATH_FONT)
        for name in ['sz','szCs']:
            for old in list(pr.findall(qn('w:'+name))):pr.remove(old)
            e=OxmlElement('w:'+name);e.set(qn('w:val'),str(int(size*2)));pr.append(e)

def set_doc_math_font(doc):
    settings=doc.settings.element
    mp=settings.find(qn('m:mathPr'))
    if mp is None:mp=OxmlElement('m:mathPr');settings.append(mp)
    mf=mp.find(qn('m:mathFont'))
    if mf is None:mf=OxmlElement('m:mathFont');mp.insert(0,mf)
    mf.set(qn('m:val'),MATH_FONT)

def fill_prose(p, text, *, size=12, line=1.5, keep_next=False):
    # Inline TeX becomes Office Math; normal text retains the source manuscript font.
    p.clear();src=etree.fromstring(pandoc_paragraph(text))
    for child in src:
        if child.tag!=qn('w:pPr'):p._p.append(deepcopy(child))
    p.style='Normal'
    pf=p.paragraph_format
    pf.alignment=WD_ALIGN_PARAGRAPH.LEFT;pf.line_spacing=line
    pf.space_before=Pt(0);pf.space_after=Pt(6);pf.keep_with_next=keep_next
    pf.keep_together=False;pf.widow_control=True
    for r in p.runs:
        r.font.name='Times New Roman';r.font.size=Pt(size)
    math_font_tree(p._p,size)
    return p

def fill_equation(p, latex, label, *, width=6.2677, size=12, keep_next=True):
    src=etree.fromstring(pandoc_paragraph('$$'+latex+'$$'))
    maths=src.findall('.//m:oMath',NS)
    if len(maths)!=1:raise ValueError((label,len(maths),latex))
    p.clear();p.style='Normal';pf=p.paragraph_format
    pf.alignment=WD_ALIGN_PARAGRAPH.LEFT;pf.line_spacing=1.15
    pf.space_before=Pt(4);pf.space_after=Pt(8)
    pf.keep_together=True;pf.keep_with_next=keep_next;pf.widow_control=True
    # Center math and align equation number to the text area's right edge.
    pf.tab_stops.clear_all()
    pf.tab_stops.add_tab_stop(Inches(width/2),WD_TAB_ALIGNMENT.CENTER)
    pf.tab_stops.add_tab_stop(Inches(width),WD_TAB_ALIGNMENT.RIGHT)
    p.add_run('\t')
    math=deepcopy(maths[0]);math_font_tree(math,size);p._p.append(math)
    p.add_run('\t')
    r=p.add_run(f'({label})');r.font.name='Times New Roman';r.font.size=Pt(size)
    return p

def insert_after(anchor):
    el=OxmlElement('w:p');anchor._p.addnext(el)
    return Paragraph(el,anchor._parent)

def text_with_math(p):
    return ''.join(p._p.xpath('.//w:t/text() | .//m:t/text()'))
