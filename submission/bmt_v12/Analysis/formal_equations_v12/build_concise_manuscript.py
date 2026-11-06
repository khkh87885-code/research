"""Restore readable methods prose and retain only five essential display equations."""
from copy import deepcopy
from datetime import datetime,timezone
from functools import lru_cache
import hashlib,importlib.util,json,re,shutil,subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile
from lxml import etree
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt,RGBColor
from docx.text.paragraph import Paragraph
from docx.enum.text import WD_ALIGN_PARAGRAPH
from formal_equations import NS,display_equation,normalize_display,set_math_font,profile

BASE=Path('/workspace/bmt_v12');OUT=BASE/'outputs'
SOURCE=Path('/workspace/research_source/submission/bmt_v9')
LATEST=Path('/workspace/research_source/submission/bmt_v11')

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def is_layout(table):
    cap=table._tbl.tblPr.find(qn('w:tblCaption'))
    return cap is not None and cap.get(qn('w:val'),'').startswith('Equation layout (')
def scientific_tables(doc):return [t for t in doc.tables if not is_layout(t)]
def cells(doc):return [[[c.text for c in r.cells]for r in t.rows]for t in scientific_tables(doc)]

@lru_cache(maxsize=64)
def prose_xml(text):
    with TemporaryDirectory(prefix='bmt_v12_prose_')as td:
        p=Path(td)/'fragment.md';out=p.with_suffix('.docx');p.write_text(text)
        r=subprocess.run(['pandoc',str(p),'-o',str(out)],capture_output=True,text=True)
        assert r.returncode==0 and not r.stderr.strip(),r.stderr
        with ZipFile(out)as z:root=etree.fromstring(z.read('word/document.xml'))
        ps=root.findall('./w:body/w:p',NS);assert len(ps)==1
        return etree.tostring(ps[0])

def fill_prose(p,text,size,line=1.5,keep=False):
    text=re.sub(r'(?<=\d)[ \u00a0\u202f]*%', '\u202f%',text)
    src=etree.fromstring(prose_xml(text));p.clear();p.style='Normal'
    for child in src:
        if child.tag!=qn('w:pPr'):p._p.append(deepcopy(child))
    pf=p.paragraph_format;pf.line_spacing=line;pf.space_after=Pt(6)
    pf.space_before=Pt(0);pf.keep_with_next=keep;pf.keep_together=False
    pf.widow_control=True;pf.alignment=WD_ALIGN_PARAGRAPH.LEFT
    for r in p.runs:r.font.name='Times New Roman';r.font.size=Pt(size);r.font.color.rgb=RGBColor(0,0,0)
    for math in list(p._p.findall('m:oMath',NS)):
        temp=OxmlElement('m:oMathPara');temp.append(deepcopy(math));normalize_display(temp,size)
        math.getparent().replace(math,temp.find('m:oMath',NS))

def canonical_latex(tex):
    # Descriptive cohort/method labels are upright; running index s is italic.
    for cohort in ['E','I']:tex=tex.replace('_{'+cohort+',s}',r'_{\mathrm{'+cohort+'},s}')
    return tex

def apply_replacements(doc,replacements,size,width):
    line=1.5 if size==12 else 1.15
    for rep in replacements:
        hits=[p for p in doc.paragraphs if p.text==rep['anchor_exact']];assert len(hits)==1,rep['source_paragraph_index']
        anchor=hits[0];cursor=None
        for i,block in enumerate(rep['blocks']):
            next_is_equation=i+1<len(rep['blocks'])and rep['blocks'][i+1]['type']=='equation'
            if block['type']=='paragraph':
                if cursor is None:p=anchor
                else:
                    e=OxmlElement('w:p');cursor.addnext(e);p=Paragraph(e,doc._body)
                fill_prose(p,block['text'],size,line,keep=next_is_equation);cursor=p._p
            else:
                assert cursor is not None
                table=display_equation(doc,canonical_latex(block['latex']),block['label'],width,size)
                cursor.addnext(table._tbl);cursor=table._tbl
                # Keep the complete equation and its contextual definition together.
                for cell in table.rows[0].cells:
                    for p in cell.paragraphs:p.paragraph_format.keep_with_next=True

def mathematical_audit(path,labels):
    d=Document(path);eqs=[t for t in d.tables if is_layout(t)]
    actual=[t.cell(0,2).text for t in eqs]
    assert actual==['('+s+')'for s in labels],actual
    with ZipFile(path)as z:
        root=etree.fromstring(z.read('word/document.xml'))
        images=[n for n in z.namelist()if n.startswith('word/media/')]
    assert len(root.findall('.//m:oMathPara',NS))==len(labels)
    assert not root.findall('.//m:m',NS),'No aligned/cases matrices retained'
    return {'display_equation_labels':labels,'native_display_count':len(eqs),
            'scientific_data_table_count':len(scientific_tables(d)),'equation_layout_count':len(eqs),
            'scientific_cell_count':sum(len(r.cells)for t in scientific_tables(d)for r in t.rows),
            'total_native_math_objects':len(root.findall('.//m:oMath',NS)),
            'image_media_count':len(images),'equation_images':0,'true_display_office_math':True}

def render(p,size):
    uri=profile(BASE/'qa'/('lo_'+p.stem),size)
    r=subprocess.run(['soffice','-env:UserInstallation='+uri,'--headless','--convert-to','pdf','--outdir',str(BASE/'qa'),str(p)],capture_output=True,text=True,check=True)
    raw=BASE/'qa'/p.with_suffix('.pdf').name;assert raw.exists(),r.stdout+r.stderr
    dest=OUT/(p.stem+'_preview.pdf');shutil.copy2(raw,dest);return dest

def build():
    plan=json.loads((BASE/'evidence/formula_scope_plan.json').read_text())
    OUT.mkdir(exist_ok=True)
    if not(OUT/'Figures').exists():shutil.copytree(LATEST/'Figures',OUT/'Figures')
    src=Path(plan['main_source']);assert sha(src)==plan['source_sha256']['main']
    main=Document(src);set_math_font(main)
    apply_replacements(main,plan['main_replacements'],12,6.2677)
    assert cells(main)==cells(Document(LATEST/'BMT_main_manuscript_v11.docx'))
    # Results through declarations/references/captions are unchanged from the latest revision.
    expected=Document(LATEST/'BMT_main_manuscript_v11.docx')
    def tail(d):
        ps=d.paragraphs;n=next(i for i,p in enumerate(ps)if p.text=='Results');return [p.text for p in ps[n:]]
    assert tail(main)==tail(expected)
    mainpath=OUT/'BMT_main_manuscript_v12.docx';main.save(mainpath)
    ma=mathematical_audit(mainpath,['1','2','3']);assert ma['scientific_data_table_count']==3 and ma['image_media_count']==0
    spec=importlib.util.spec_from_file_location('plate_layout',SOURCE/'Analysis/graphics_v9/reformat_manuscript.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);mod.BASE=BASE
    captions=[p.text for p in main.paragraphs if re.match(r'^Figure [1-5]\. ',p.text)]
    illustrated=mod.illustrated_copy(mainpath,captions)
    src=Path(plan['supplement_source']);assert sha(src)==plan['source_sha256']['supplement']
    supp=Document(src);set_math_font(supp)
    apply_replacements(supp,plan['supplement_replacements'],11,6.89)
    old='BMT_supplementary_Figure_S6_v5.pdf';new='BMT_supplementary_Figure_S6_v8.pdf'
    for p in supp.paragraphs:
        if old in p.text:
            for r in p.runs:r.text=r.text.replace(old,new)
    assert cells(supp)==cells(Document(LATEST/'BMT_supplementary_material_v7.docx'))
    supppath=OUT/'BMT_supplementary_material_v8.docx';supp.save(supppath)
    sa=mathematical_audit(supppath,['S1','S2']);assert sa['scientific_data_table_count']==19 and sa['image_media_count']==5
    shutil.copy2(LATEST/'BMT_supplementary_Figure_S6_v7.pdf',OUT/new)
    result={'created_utc':datetime.now(timezone.utc).isoformat(),'source_latest':'submission/bmt_v11',
       'prose_baseline':'submission/bmt_v9','scope':'User-authorized pruning and formal display-equation layout',
       'main':{'output':str(mainpath),'sha256':sha(mainpath),**ma},
       'supplement':{'output':str(supppath),'sha256':sha(supppath),**sa},
       'prior_display_equation_count':26,'current_display_equation_count':5,
       'results_declarations_references_figures_scientific_cells_unchanged':True,
       'no_new_analysis_or_experiments':True,'final_documents_pending':True,
       'illustrated':illustrated,'previews':[]}
    for p,size in [(mainpath,12),(OUT/'BMT_main_manuscript_v12_illustrated.docx',12),(supppath,11)]:
        pdf=render(p,size);result['previews'].append({'path':str(pdf),'sha256':sha(pdf)})
    (BASE/'evidence/concise_equation_build_report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'main':ma,'supplement':sa},indent=2))

if __name__=='__main__':build()
