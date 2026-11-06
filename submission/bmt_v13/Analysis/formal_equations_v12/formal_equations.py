"""Native single-line Word display equations in symmetric layout containers.

The 1x3 borderless containers are tagged as equation layouts, not scientific
data tables. The formula itself is an editable m:oMathPara, never an image.
"""
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile
import json,re,subprocess

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT,WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches,Pt,Mm,RGBColor
from lxml import etree

NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'm':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
MATH_FONT='Cambria Math'

@lru_cache(maxsize=64)
def math_xml(latex):
    with TemporaryDirectory(prefix='bmt_v12_display_')as td:
        src=Path(td)/'math.md';out=src.with_suffix('.docx');src.write_text('$$'+latex+'$$')
        p=subprocess.run(['pandoc',str(src),'-o',str(out)],capture_output=True,text=True)
        if p.returncode or p.stderr.strip():raise RuntimeError(p.stderr)
        with ZipFile(out)as z:root=etree.fromstring(z.read('word/document.xml'))
        para=root.find('./w:body/w:p/m:oMathPara',NS)
        assert para is not None,'Expected native display math'
        return etree.tostring(para)

def normalize_display(para,size):
    for pr in para.findall('.//m:dPr',NS):
        order={'begChr':0,'sepChr':1,'endChr':2,'grow':3,'shp':4,'ctrlPr':5}
        cs=list(pr)
        for c in cs:pr.remove(c)
        for c in sorted(cs,key=lambda x:order.get(etree.QName(x).localname,99)):pr.append(c)
        # These five equations use fixed-size fences; no multi-line cases.
        g=pr.find('m:grow',NS)
        if g is not None:g.set(qn('m:val'),'0')
    for run in para.findall('.//m:r',NS):
        pr=run.find('m:rPr',NS);t=run.find('m:t',NS)
        if pr is not None and pr.find('m:scr',NS)is None:
            sty=pr.find('m:sty',NS)
            if sty is not None and sty.get(qn('m:val'))=='p'and t is not None and t.text and t.text.isalnum():
                pr.remove(sty)
                if pr.find('m:nor',NS)is None:pr.append(OxmlElement('m:nor'))
        normal=pr is not None and pr.find('m:nor',NS)is not None
        wp=run.find('w:rPr',NS)
        if wp is None:
            wp=OxmlElement('w:rPr');run.insert(1 if pr is not None else 0,wp)
        fonts=OxmlElement('w:rFonts')
        for k in ['ascii','hAnsi','cs','eastAsia']:fonts.set(qn('w:'+k),'Times New Roman'if normal else MATH_FONT)
        wp.insert(0,fonts)
        sz=OxmlElement('w:sz');sz.set(qn('w:val'),str(round(size*2)));wp.append(sz)
        if normal:
            i=OxmlElement('w:i');i.set(qn('w:val'),'0');wp.append(i)
    pr=para.find('m:oMathParaPr',NS)
    if pr is None:pr=OxmlElement('m:oMathParaPr');para.insert(0,pr)
    jc=pr.find('m:jc',NS)
    if jc is None:jc=OxmlElement('m:jc');pr.append(jc)
    jc.set(qn('m:val'),'center')
    return para

def set_math_font(doc):
    mp=doc.settings.element.find(qn('m:mathPr'))
    if mp is None:mp=OxmlElement('m:mathPr');doc.settings.element.append(mp)
    mf=mp.find(qn('m:mathFont'))
    if mf is None:mf=OxmlElement('m:mathFont');mp.insert(0,mf)
    mf.set(qn('m:val'),MATH_FONT)

def display_equation(doc,latex,label,width=6.268,size=12,number_width=.60):
    assert width>2*number_width
    table=doc.add_table(rows=1,cols=3)
    table.style='Normal Table'
    table.alignment=WD_TABLE_ALIGNMENT.CENTER;table.autofit=False
    widths=[number_width,width-2*number_width,number_width]
    for c,w in zip(table.columns,widths):c.width=Inches(w)
    pr=table._tbl.tblPr
    for tag in ['tblBorders','tblCellMar','tblW','tblInd']:
        for old in list(pr.findall(qn('w:'+tag))):pr.remove(old)
    tw=OxmlElement('w:tblW');tw.set(qn('w:w'),str(round(width*1440)));tw.set(qn('w:type'),'dxa');pr.insert(0,tw)
    borders=OxmlElement('w:tblBorders')
    for side in ['top','left','bottom','right','insideH','insideV']:
        e=OxmlElement('w:'+side);e.set(qn('w:val'),'nil');borders.append(e)
    pr.append(borders)
    margins=OxmlElement('w:tblCellMar')
    for name,val in [('top',80),('bottom',80),('left',0),('right',0)]:
        e=OxmlElement('w:'+name);e.set(qn('w:w'),str(val));e.set(qn('w:type'),'dxa');margins.append(e)
    pr.append(margins)
    cap=OxmlElement('w:tblCaption');cap.set(qn('w:val'),'Equation layout ('+label+')');pr.append(cap)
    desc=OxmlElement('w:tblDescription');desc.set(qn('w:val'),'Native display equation layout; not a scientific data table.');pr.append(desc)
    row=table.rows[0];trpr=row._tr.get_or_add_trPr();trpr.append(OxmlElement('w:cantSplit'))
    for cell,w in zip(row.cells,widths):
        cell.width=Inches(w);cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
        nowrap=OxmlElement('w:noWrap');cell._tc.get_or_add_tcPr().append(nowrap)
        p=cell.paragraphs[0];p.paragraph_format.space_before=Pt(0);p.paragraph_format.space_after=Pt(0)
        p.paragraph_format.line_spacing=1.0;p.paragraph_format.keep_together=True
    p=row.cells[1].paragraphs[0];p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    native=etree.fromstring(math_xml(latex));p._p.append(normalize_display(native,size))
    p=row.cells[2].paragraphs[0];p.alignment=WD_ALIGN_PARAGRAPH.RIGHT
    r=p.add_run('('+label+')');r.font.name='Times New Roman';r.font.size=Pt(size)
    return table

def prose(doc,text,size=12):
    p=doc.add_paragraph(text);p.paragraph_format.line_spacing=1.35
    p.paragraph_format.space_after=Pt(6)
    for r in p.runs:r.font.name='Times New Roman';r.font.size=Pt(size);r.font.color.rgb=RGBColor(0,0,0)
    return p

def profile(path,size):
    user=Path(path)/'user';user.mkdir(parents=True,exist_ok=True)
    (user/'registrymodifications.xcu').write_text(f'''<?xml version="1.0" encoding="UTF-8"?>
<oor:items xmlns:oor="http://openoffice.org/2001/registry">
 <item oor:path="/org.openoffice.Office.Math/StandardFormat"><prop oor:name="BaseSize" oor:op="fuse"><value>{size}</value></prop><prop oor:name="IndexSize" oor:op="fuse"><value>70</value></prop><prop oor:name="LimitsSize" oor:op="fuse"><value>70</value></prop></item>
</oor:items>''')
    return Path(path).as_uri()

def prototype(outdir):
    outdir=Path(outdir);outdir.mkdir(parents=True,exist_ok=True)
    definitions=[
      ('1',r'D(U,V)=\frac{2\lvert U\cap V\rvert}{\lvert U\rvert+\lvert V\rvert}.','Dice agreement is evaluated for two binary masks. The empty-empty convention and quality cutoff are stated in prose.'),
      ('2',r'r_{\text{A},i}=1-\widehat q_i.','Method A uses the raw quality-head output of SAM for the initial prediction.'),
      ('3',r'r_{\text{B},i}=1-\frac{1}{4}\sum_{j=1}^{4}D(P_{0,i},P_{j,i}).','Method B measures disagreement under four fixed prompt shifts. The exact box rules remain in the methods text.'),
    ]
    supplemental=[
      ('S1',r'C=\sum_s(w_{\text{E},s}-w_{\text{I},s})\frac{p_{\text{E},s}+p_{\text{I},s}}{2}.','For diagnostic strata s, the composition-associated contribution is'),
      ('S2',r'W=\sum_s(p_{\text{E},s}-p_{\text{I},s})\frac{w_{\text{E},s}+w_{\text{I},s}}{2}.','The within-stratum-rate contribution is'),
    ]
    results={}
    for name,size,defs,width in [('main',12,definitions,6.268),('supplement',11,supplemental,6.89)]:
        d=Document();sec=d.sections[0];sec.page_width=Mm(210);sec.page_height=Mm(297)
        margin=(210-width*25.4)/2;sec.left_margin=sec.right_margin=Mm(margin);sec.top_margin=sec.bottom_margin=Mm(25.4)
        d.styles['Normal'].font.name='Times New Roman';d.styles['Normal'].font.size=Pt(size);set_math_font(d)
        title=d.add_heading('Essential mathematical definitions'if name=='main'else'Diagnostic-stratum decomposition',level=1)
        for r in title.runs:r.font.name='Times New Roman';r.font.size=Pt(14);r.font.color.rgb=RGBColor(0,0,0)
        for label,latex,intro in defs:
            prose(d,intro,size);display_equation(d,latex,label,width,size)
            p=d.add_paragraph();p.paragraph_format.space_after=Pt(6)
        if name=='supplement':prose(d,'The two contributions add to the external-minus-internal difference. Weights use low-quality patients for detection and all scored patients for review. Common-weight standardization and undefined-denominator handling are described in prose.',size)
        p=outdir/(name+'_formal_display.docx');d.save(p)
        uri=profile(outdir/('lo_profile_'+name),size)
        run=subprocess.run(['soffice','-env:UserInstallation='+uri,'--headless','--convert-to','pdf','--outdir',str(outdir),str(p)],check=True,capture_output=True,text=True)
        results[name]={'docx':str(p),'pdf':str(p.with_suffix('.pdf')),'display_count':len(defs),'data_table_count':0,'layout_table_count':len(d.tables),'body_pt':size,'number_column_inches':.6}
    (outdir/'prototype_metadata.json').write_text(json.dumps(results,indent=2)+'\n')
    return results

if __name__=='__main__':
    print(json.dumps(prototype(Path(__file__).parent),indent=2))
