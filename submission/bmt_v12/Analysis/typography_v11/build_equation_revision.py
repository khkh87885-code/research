"""Add explicit, editable mathematical definitions to the archived v9 submission."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
from zipfile import ZipFile

from docx import Document
from docx.shared import Pt
from docx.shared import RGBColor
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph
from lxml import etree

from equation_docx import NS, fill_equation, fill_prose, insert_after, set_doc_math_font, text_with_math, prepare_equation_layout
from normalizer_recommendation import write_lo_profile

BASE=Path('/workspace/bmt_v11')
SOURCE=Path('/workspace/research_source/submission/bmt_v9')
OUT=BASE/'outputs'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def tables(d):return [[[c.text for c in r.cells]for r in t.rows]for t in d.tables]
def numspace(s):return re.sub(r'(?<=\d)[ \u00a0\u202f]*%', '\u202f%', s)

def effective_plan(plan):
    """Add explicit introductions for equation labels not otherwise cited in prose."""
    plan=deepcopy(plan)
    blocks=[b for r in plan.get('replacements',[]) for b in r['blocks']] if 'replacements'in plan else plan['blocks']
    if 'replacements'in plan:
        # An open set spanning aligned rows triggers a LibreOffice parser
        # placeholder. Equivalent named displacements keep each row complete.
        eq2=next(b for b in blocks if b['type']=='equation'and b['label']=='2')
        eq2['latex']=r'\begin{aligned}B_{j,i}&=\operatorname{clip}_{\Omega_i}\{B_{0,i}+(u_{j,i},v_{j,i},u_{j,i},v_{j,i})\},\\(u_{j,i},v_{j,i})&\in\{(-\delta_{x,i},0),(\delta_{x,i},0),(0,-\delta_{y,i}),(0,\delta_{y,i})\},\\\delta_{x,i}&=0.05w_{0,i},\qquad\delta_{y,i}=0.05h_{0,i}.\end{aligned}'
        eq2['rendering_note']='Equivalent explicit displacement variables avoid an open delimiter across aligned rows.'
    else:
        for block in blocks:
            if block.get('key')=='bootstrap_tie_same':
                block['latex']=block['latex'].replace(r'\ \mathrm{or}\ ',r'\quad\mathrm{or}\quad ')
    ref_pattern=r'\bEqs?\.\s*\(S?\d+\)(?:\s*(?:and|,)\s*\(S?\d+\))*'
    referenced=set()
    for b in blocks:
        if b['type']=='paragraph':
            for match in re.finditer(ref_pattern,b['text']):
                referenced.update(re.findall(r'\((S?\d+)\)',match.group()))
    introductions={}
    for i,b in enumerate(blocks):
        if b['type']!='equation':continue
        label=b['label']
        if label not in referenced:
            j=i-1
            while j>=0 and blocks[j]['type']!='paragraph':j-=1
            if j>=0:introductions.setdefault(j,[]).append(label)
    for j,labels in introductions.items():
        t=blocks[j]['text'].rstrip()
        ref=('Eq. 'if len(labels)==1 else'Eqs. ')+ ' and '.join('('+s+')'for s in labels)
        if t.endswith(':'):t=t[:-1]+f' ({ref}):'
        elif t.endswith('.'):t=t[:-1]+f' ({ref}).'
        elif t.endswith(' uses'):t+=' '+ref+':'
        elif t.endswith(' as'):t=t[:-3]+' using '+ref+':'
        elif t.endswith('Then'):t=t[:-4]+'The rates and weights are defined in '+ref+':'
        else:t+=' given by '+ref+':'
        blocks[j]['text']=t
    return plan

def replace_block(doc,p,blocks,size=12,line=1.5,width=6.2677):
    cursor=p
    for i,b in enumerate(blocks):
        if i:cursor=insert_after(cursor)
        next_eq=i+1<len(blocks) and blocks[i+1]['type']=='equation'
        if b['type']=='paragraph':
            fill_prose(cursor,numspace(b['text']),size=size,line=line,keep_next=next_eq)
            if size==11:cursor.paragraph_format.space_after=Pt(4)
        elif b['type']=='equation':
            cursor=fill_equation(cursor,b['latex'],b['label'],width=width,size=size)
            if size==11:cursor.paragraph_format.space_after=Pt(6)
        elif b['type']=='heading':
            cursor.text=b['text'];cursor.style='Heading '+str(b.get('level',2))
            pf=cursor.paragraph_format;pf.keep_with_next=True;pf.keep_together=True
            pf.space_before=Pt(12);pf.space_after=Pt(6);pf.line_spacing=1.15
            for r in cursor.runs:
                r.font.name='Times New Roman';r.font.size=Pt(12);r.bold=True
                r.font.color.rgb=RGBColor(0,0,0)
        else:raise ValueError(b['type'])
    return cursor

def package_math(path,expected_labels):
    with ZipFile(path)as z:
        root=etree.fromstring(z.read('word/document.xml'))
        media=[n for n in z.namelist()if n.startswith('word/media/')]
    display=[]
    for p in root.findall('./w:body/w:p',NS):
        if p.find('m:oMath',NS)is not None:
            label=''.join(p.findall('w:r/w:t',NS)[-1].itertext()) if p.findall('w:r/w:t',NS)else''
            if re.fullmatch(r'\(S?\d+\)',label):display.append(label[1:-1])
    assert display==expected_labels,(display,expected_labels)
    return {'numbered_display_equations':display,'office_math_objects':len(root.findall('.//m:oMath',NS)),
            'image_media_count':len(media),'editable_native_math':True}

def build_main(plan):
    src=SOURCE/'BMT_main_manuscript_v9.docx';assert sha(src)==plan['source_sha256']
    before=Document(src);doc=Document(src);set_doc_math_font(doc)
    excluded={r['anchor_exact']for r in plan['replacements']}
    untouched=[p.text for p in before.paragraphs if p.text not in excluded]
    for rep in plan['replacements']:
        matches=[p for p in doc.paragraphs if p.text==rep['anchor_exact']]
        assert len(matches)==1,(rep['source_paragraph_index'],len(matches))
        replace_block(doc,matches[0],rep['blocks'])
    assert tables(doc)==tables(before)
    # Unchanged scientific sections, authors, all references, tables and captions.
    after_untouched=[p.text for p in doc.paragraphs if p.text in set(untouched)]
    assert after_untouched==untouched
    path=OUT/'BMT_main_manuscript_v11.docx';doc.save(path)
    audit=package_math(path,[str(i)for i in range(1,15)])
    assert audit['image_media_count']==0
    # Reuse only the plate-layout helper, with the unchanged v9 figure files.
    spec=importlib.util.spec_from_file_location('v9layout',SOURCE/'Analysis/graphics_v9/reformat_manuscript.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    mod.BASE=BASE
    legends=[p.text for p in doc.paragraphs if re.match(r'^Figure [1-5]\. ',p.text)]
    assert len(legends)==5
    illustrated=mod.illustrated_copy(path,legends)
    # Count prose and mathematical text separately; equations are not raster art.
    ps=doc.paragraphs
    intro=next(i for i,p in enumerate(ps)if p.text=='Introduction')
    ethics=next(i for i,p in enumerate(ps)if p.text.startswith('Research ethics.'))
    body=' '.join(text_with_math(p)for p in ps[intro:ethics])
    refs=[p.text for p in ps if re.match(r'^\d+\.  ',p.text)]
    assert len(refs)==15
    return {'source':str(src),'source_sha256':sha(src),'output':str(path),'sha256':sha(path),
            'replaced_method_paragraphs':len(plan['replacements']),'all_other_paragraphs_exact':True,
            'table_cells_exact':True,'table_cell_count':sum(len(r.cells)for t in doc.tables for r in t.rows),
            'references_exact_count':len(refs),'body_words_including_math_text':len(body.split()),
            'abstract_unchanged':True,'results_discussion_declarations_exact':True,
            **audit,'illustrated':illustrated}

def build_supplement(plan):
    src=SOURCE/'BMT_supplementary_material_v5.docx';before=Document(src);doc=Document(src)
    set_doc_math_font(doc)
    anchor=next(p for p in doc.paragraphs if p.text.startswith('Table S1.'))
    title=anchor.insert_paragraph_before('Supplementary mathematical methods','Heading 1')
    title.paragraph_format.page_break_before=True;title.paragraph_format.keep_with_next=True
    title.paragraph_format.space_after=Pt(8)
    for r in title.runs:r.font.name='Times New Roman';r.font.size=Pt(14);r.bold=True
    cursor=insert_after(title)
    blocks=[]
    for b in plan['blocks']:
        blocks.append(b)
        if b['type']=='equation' and b.get('note'):
            blocks.append({'type':'paragraph','text':b['note']})
    replace_block(doc,cursor,blocks,size=11,line=1.15,width=6.89)
    old_file='BMT_supplementary_Figure_S6_v5.pdf';new_file='BMT_supplementary_Figure_S6_v7.pdf'
    for p in doc.paragraphs:
        if old_file in p.text:
            for r in p.runs:r.text=r.text.replace(old_file,new_file)
    assert tables(doc)==tables(before)
    oldtexts=[p.text for p in before.paragraphs]
    oldtexts=[x.replace(old_file,new_file)for x in oldtexts]
    # Insertion preserves all existing supplemental scientific text in order.
    actual=[p.text for p in doc.paragraphs if p.text in set(oldtexts)]
    assert actual==oldtexts
    path=OUT/'BMT_supplementary_material_v7.docx';doc.save(path)
    audit=package_math(path,[f'S{i}'for i in range(1,13)])
    assert audit['image_media_count']==5
    shutil.copy2(SOURCE/old_file,OUT/new_file)
    return {'source':str(src),'source_sha256':sha(src),'output':str(path),'sha256':sha(path),
            'all_prior_scientific_paragraphs_exact':True,'table_cells_exact':True,
            'table_cell_count':sum(len(r.cells)for t in doc.tables for r in t.rows),
            'separate_S6_filename_only_updated':True,'S6_bytes_unchanged':sha(SOURCE/old_file)==sha(OUT/new_file),**audit}

def render(path):
    name=path.stem
    uri=write_lo_profile(BASE/'qa'/('lo_profile_'+name),11 if 'supplementary_material' in name else 12,5)
    cmd=['soffice','-env:UserInstallation='+uri,'--headless',
         '--convert-to','pdf','--outdir',str(BASE/'qa'),str(path)]
    r=subprocess.run(cmd,capture_output=True,text=True,check=True)
    raw=BASE/'qa'/path.with_suffix('.pdf').name
    assert raw.is_file(),r.stdout+r.stderr
    dest=OUT/(name+'_preview.pdf');shutil.copy2(raw,dest)
    return dest

def main():
    OUT.mkdir(exist_ok=True)
    if not(OUT/'Figures').exists():shutil.copytree(SOURCE/'Figures',OUT/'Figures')
    mp=effective_plan(json.loads((BASE/'evidence/main_equation_plan.json').read_text()))
    sp=effective_plan(json.loads((BASE/'evidence/supplement_equation_plan.json').read_text()))
    (BASE/'evidence/effective_main_equation_plan.json').write_text(json.dumps(mp,ensure_ascii=False,indent=2)+'\n')
    (BASE/'evidence/effective_supplement_equation_plan.json').write_text(json.dumps(sp,ensure_ascii=False,indent=2)+'\n')
    prepare_equation_layout([mp,sp])
    a=build_main(mp);s=build_supplement(sp)
    report={'created_utc':datetime.now(timezone.utc).isoformat(),'scope':'Explicit equations for existing analyses; no experiment or numerical-result change',
            'main':a,'supplement':s,'pandoc_version':subprocess.check_output(['pandoc','--version'],text=True).splitlines()[0],
            'equation_format':'Native editable Office Math, generated from audited TeX; no formula images',
            'rendering_fix':'Literal upright labels, normal-text operators, normalized delimiter/column properties, measured tab-aligned complete equation rows; PDF math profile12pt main/11pt supplement',
            'figures_unchanged':True,'final_documents_pending':True}
    for name in ['BMT_main_manuscript_v11.docx','BMT_main_manuscript_v11_illustrated.docx','BMT_supplementary_material_v7.docx']:
        path=render(OUT/name);report.setdefault('previews',[]).append({'path':str(path),'sha256':sha(path)})
    (BASE/'evidence/equation_build_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'main':a['body_words_including_math_text'],'main_eqs':14,'supp_eqs':12,'main_docx':a['output'],'supp_docx':s['output']},indent=2))

if __name__=='__main__':main()
