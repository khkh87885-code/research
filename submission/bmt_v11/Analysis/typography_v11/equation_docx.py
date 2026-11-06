"""Editable Word equations with literal labels and renderer-stable relation rows."""
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
import hashlib,json,re,subprocess
from tempfile import TemporaryDirectory
from zipfile import ZipFile
from lxml import etree
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches,Pt,Mm
from docx.enum.text import WD_ALIGN_PARAGRAPH,WD_TAB_ALIGNMENT
from docx.text.paragraph import Paragraph
from normalizer_recommendation import normalize_math,write_lo_profile

NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'm':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
BASE=Path('/workspace/bmt_v11')
WIDTHS={}
MATH_FONT='Cambria Math'

def format_tex(tex):
    tex=re.sub(r'_\{(H[123])\}',r'_{\\text{\1}}',tex)
    tex=re.sub(r'\\mathrm\{([A-Za-z0-9]+)\}',r'\\text{\1}',tex)
    # Count names are literal identifiers, including inside fraction braces.
    previous=tex
    tex=re.sub(r'(?<![A-Za-z\\])(TP|FP|TN|FN)(?![A-Za-z])',
               lambda m:m.group() if previous[:m.start()].endswith(r'\text{') else r'\text{'+m.group()+'}',previous)
    tex=re.sub(r'\\quad\s*\\text\{or\}\\quad\s*',r'\\text{ or }',tex)
    # A logical symbol remains legible when a renderer trims math-text spaces.
    tex=tex.replace(r'\text{ or }',r'\lor')
    return tex

@lru_cache(maxsize=1024)
def pandoc_paragraph(markdown):
    with TemporaryDirectory(prefix='bmt_v11_math_')as td:
        p=Path(td)/'fragment.md';out=p.with_suffix('.docx');p.write_text(markdown)
        r=subprocess.run(['pandoc','--from=markdown+tex_math_dollars',str(p),'-o',str(out)],capture_output=True,text=True)
        if r.returncode or r.stderr.strip():raise RuntimeError(r.stderr+'\n'+markdown)
        with ZipFile(out)as z:root=etree.fromstring(z.read('word/document.xml'))
        ps=root.findall('./w:body/w:p',NS)
        assert len(ps)==1,(len(ps),markdown)
        return etree.tostring(ps[0])

def style_math(math,size=12,inline=False):
    normalize_math(math)
    for r in math.findall('.//m:r',NS):
        mrp=r.find('m:rPr',NS);normal=mrp is not None and mrp.find('m:nor',NS)is not None
        wp=r.find('w:rPr',NS)
        if wp is None:
            wp=OxmlElement('w:rPr');r.insert(1 if mrp is not None else 0,wp)
        rf=wp.find(qn('w:rFonts'))
        if rf is None:rf=OxmlElement('w:rFonts');wp.insert(0,rf)
        for name in ['ascii','hAnsi','cs','eastAsia']:rf.set(qn('w:'+name),'Times New Roman'if normal else MATH_FONT)
        if normal:
            it=OxmlElement('w:i');it.set(qn('w:val'),'0');wp.append(it)
        for name in ['sz','szCs']:
            for old in list(wp.findall(qn('w:'+name))):wp.remove(old)
            e=OxmlElement('w:'+name);e.set(qn('w:val'),str(int(size*2)));wp.append(e)
    if inline:
        for lim in math.findall('.//m:naryPr/m:limLoc',NS):lim.set(qn('m:val'),'subSup')
    return math

def native_math(tex,size=12):
    p=etree.fromstring(pandoc_paragraph('$$'+format_tex(tex)+'$$'))
    ms=p.findall('.//m:oMath',NS);assert len(ms)==1,tex
    return style_math(deepcopy(ms[0]),size)

def set_doc_math_font(doc):
    mp=doc.settings.element.find(qn('m:mathPr'))
    if mp is None:mp=OxmlElement('m:mathPr');doc.settings.element.append(mp)
    mf=mp.find(qn('m:mathFont'))
    if mf is None:mf=OxmlElement('m:mathFont');mp.insert(0,mf)
    mf.set(qn('m:val'),MATH_FONT)

def fill_prose(p,text,*,size=12,line=1.5,keep_next=False):
    text=text.replace(r'$s\in\{\mathrm{benign},\mathrm{malignant}\}$',r'$s$ (benign or malignant)')
    text=re.sub(r'\$([^$]+)\$',lambda m:'$'+format_tex(m.group(1))+'$',text)
    src=etree.fromstring(pandoc_paragraph(text));p.clear();p.style='Normal'
    for e in src:
        if e.tag!=qn('w:pPr'):p._p.append(deepcopy(e))
    pf=p.paragraph_format;pf.alignment=WD_ALIGN_PARAGRAPH.LEFT
    pf.line_spacing=line;pf.space_before=Pt(0);pf.space_after=Pt(6)
    pf.keep_with_next=keep_next;pf.keep_together=False;pf.widow_control=True
    for r in p.runs:r.font.name='Times New Roman';r.font.size=Pt(size)
    for m in p._p.findall('.//m:oMath',NS):style_math(m,size,inline=True)
    return p

def rows(tex):
    tex=format_tex(tex).strip()
    if tex.startswith(r'\begin{aligned}')and tex.endswith(r'\end{aligned}'):
        body=tex[len(r'\begin{aligned}'):-len(r'\end{aligned}')]
        answer=[]
        for row in body.split(r'\\'):
            parts=row.split('&',1);assert len(parts)==2 and parts[0].strip(),row
            answer.append((parts[0].strip(),parts[1].strip()))
        return answer
    return [(None,tex)]

def prepare_equation_layout(plans):
    """Measure native renderer widths once; avoid heuristic spacing in final rows."""
    fragments=[]
    for plan in plans:
        bs=[b for r in plan.get('replacements',[])for b in r['blocks']]if'replacements'in plan else plan['blocks']
        for b in bs:
            if b['type']=='equation':
                for l,r in rows(b['latex']):
                    fragments.extend(([l]if l is not None else[])+[r])
    fragments=list(dict.fromkeys(fragments));d=Document();s=d.sections[0]
    s.page_width=Mm(600);s.page_height=Mm(600);s.left_margin=s.right_margin=Mm(20)
    d.styles['Normal'].font.name='Times New Roman';d.styles['Normal'].font.size=Pt(12);set_doc_math_font(d)
    for i,tex in enumerate(fragments):
        p=d.add_paragraph();p.paragraph_format.space_after=Pt(5)
        rr=p.add_run(f'A{i:03d}Z');rr.font.size=Pt(8)
        p._p.append(native_math(tex))
        rr=p.add_run(f'B{i:03d}Z');rr.font.size=Pt(8)
    p=BASE/'qa/native_width_probe.docx';d.save(p)
    uri=write_lo_profile(BASE/'qa/lo_profile_widths',12,5)
    subprocess.run(['soffice','-env:UserInstallation='+uri,'--headless','--convert-to','pdf','--outdir',str(BASE/'qa'),str(p)],check=True,capture_output=True)
    import fitz
    pdf=fitz.open(p.with_suffix('.pdf'));allsp=[]
    for pg in pdf:
        allsp.extend(s for b in pg.get_text('dict')['blocks']for l in b.get('lines',[])for s in l['spans'])
    for i,tex in enumerate(fragments):
        a=next(s for s in allsp if s['text'].strip()==f'A{i:03d}Z');b=next(s for s in allsp if s['text'].strip()==f'B{i:03d}Z')
        WIDTHS[tex]=b['bbox'][0]-a['bbox'][2]
        assert WIDTHS[tex]>0,(tex,WIDTHS[tex])
    (BASE/'evidence/native_equation_widths.json').write_text(json.dumps(WIDTHS,ensure_ascii=False,indent=2)+'\n')

def insert_after(anchor):
    el=OxmlElement('w:p');anchor._p.addnext(el);return Paragraph(el,anchor._parent)

def fill_equation(p,latex,label,*,width=6.2677,size=12,keep_next=True):
    rr=rows(latex);scaled=lambda t:WIDTHS[t]*size/12
    if len(rr)>1:
        left=max(scaled(l)for l,r in rr);right=max(scaled(r)for l,r in rr);gap=5
        total=left+gap+right;start=(width*72-total)/2
        # Leave a clear number gutter at the right, keeping the formula centered when possible.
        start=min(start,width*72-36-total);assert start>=0,(label,total,width)
        relation=start+left+gap
    cursor=p
    for j,(lhs,rhs)in enumerate(rr):
        if j:cursor=insert_after(cursor)
        cursor.clear();cursor.style='Normal';pf=cursor.paragraph_format
        pf.alignment=WD_ALIGN_PARAGRAPH.LEFT;pf.line_spacing=1.1
        pf.space_before=Pt(5 if j==0 else 0);pf.space_after=Pt(7 if j==len(rr)-1 else 2)
        pf.keep_together=True;pf.keep_with_next=True;pf.widow_control=True
        pf.tab_stops.clear_all()
        if lhs is not None:
            pf.tab_stops.add_tab_stop(Pt(relation-gap),WD_TAB_ALIGNMENT.RIGHT)
            pf.tab_stops.add_tab_stop(Pt(relation),WD_TAB_ALIGNMENT.LEFT)
            cursor.add_run('\t');cursor._p.append(native_math(lhs,size))
            cursor.add_run('\t');cursor._p.append(native_math(rhs,size))
        else:
            measured=scaled(rhs);center=min(width*72/2,width*72-36-measured/2)
            assert center-measured/2>=0,(label,measured,width)
            pf.tab_stops.add_tab_stop(Pt(center),WD_TAB_ALIGNMENT.CENTER)
            cursor.add_run('\t');cursor._p.append(native_math(rhs,size))
        pf.tab_stops.add_tab_stop(Inches(width),WD_TAB_ALIGNMENT.RIGHT)
        if j==len(rr)-1:
            run=cursor.add_run('\t('+label+')');run.font.name='Times New Roman';run.font.size=Pt(size)
        # Word's paragraph marker carries the intended math size as well.
        pr=cursor._p.get_or_add_pPr();rp=OxmlElement('w:rPr');sz=OxmlElement('w:sz');sz.set(qn('w:val'),str(int(size*2)));rp.append(sz);pr.append(rp)
    return cursor

def text_with_math(p):return ''.join(p._p.xpath('.//w:t/text() | .//m:t/text()'))
