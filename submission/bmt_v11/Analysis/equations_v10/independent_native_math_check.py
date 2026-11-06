"""Independent document integrity and audited-TeX-to-OMML matching for v10."""
from pathlib import Path
from copy import deepcopy
from tempfile import TemporaryDirectory
from zipfile import ZipFile
import json,re,hashlib,subprocess
from docx import Document
from lxml import etree
import fitz
B=Path('/workspace/bmt_v10');R=Path('/workspace/research_source/submission/bmt_v9')
NS={'m':'http://schemas.openxmlformats.org/officeDocument/2006/math','w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def math_semantics(e):
    # Ignore Word font/run formatting; mathematical operators and structural
    # properties remain. Delimiter property sequence is normalized for comparison.
    children=[x for x in e if not (etree.QName(x).namespace==NS['w'] and etree.QName(x).localname=='rPr')]
    if etree.QName(e).localname=='dPr':children=sorted(children,key=lambda x:x.tag)
    return (e.tag,tuple(sorted(e.attrib.items())),e.text or '',tuple(math_semantics(c)for c in children))

def table_snapshot(d):return [[[c.text for c in row.cells]for row in t.rows]for t in d.tables]

def native_checks():
    checks=[];docs={};eqrecords=[]
    def ck(name,ok,detail=''):
        checks.append({'name':name,'pass':bool(ok),'detail':detail});assert ok,(name,detail)
    groups=[('main','effective_main_equation_plan.json','BMT_main_manuscript_v10.docx','BMT_main_manuscript_v9.docx'),('supplement','effective_supplement_equation_plan.json','BMT_supplementary_material_v6.docx','BMT_supplementary_material_v5.docx')]
    for group,pname,new,old in groups:
        plan=json.loads((B/'evidence'/pname).read_text())
        blocks=[b for r in plan['replacements'] for b in r['blocks']]if group=='main'else plan['blocks']
        equations=[b for b in blocks if b['type']=='equation']
        d=Document(B/'outputs'/new);src=Document(R/old)
        ck(group+' tables exact',table_snapshot(d)==table_snapshot(src))
        ck(group+' editable table count',len(d.tables)==(3 if group=='main'else 19))
        with ZipFile(B/'outputs'/new) as z:
            root=etree.fromstring(z.read('word/document.xml'))
            ck(group+' no equation images',len([n for n in z.namelist()if n.startswith('word/media/')])==(0 if group=='main'else 5))
        numbered=[]
        for p in root.findall('./w:body/w:p',NS):
            wtext=''.join(p.findall('.//w:t',NS)[i].text or ''for i in range(len(p.findall('.//w:t',NS))))
            label=re.search(r'\((S?\d+)\)\s*$',wtext)
            maths=p.findall('.//m:oMath',NS)
            if label and maths:numbered.append((label.group(1),maths))
        ck(group+' numbered formula count',len(numbered)==len(equations))
        ck(group+' sequential formula labels',[n for n,ms in numbered]==[b['label']for b in equations])
        with TemporaryDirectory(prefix='bmt_independent_omml_')as tmp:
            md=Path(tmp)/'audited.md';dx=Path(tmp)/'audited.docx'
            md.write_text('\n\n'.join('$$'+b['latex']+'$$'for b in equations))
            r=subprocess.run(['pandoc',str(md),'-o',str(dx)],capture_output=True,text=True)
            ck(group+' audited equations independently convert',r.returncode==0 and not r.stderr.strip(),r.stderr)
            with ZipFile(dx)as z:rr=etree.fromstring(z.read('word/document.xml'))
            expected=rr.findall('.//m:oMath',NS)
            ck(group+' expected math node count',len(expected)==len(equations))
            for b,(label,actual),exp in zip(equations,numbered,expected):
                ck(group+' equation '+label+' semantic XML equals audited TeX',len(actual)==1 and math_semantics(actual[0])==math_semantics(exp))
                eqrecords.append({'document':group,'label':label,'actual_office_math_sha256':hashlib.sha256(etree.tostring(actual[0])).hexdigest(),'audited_latex':b['latex'],'pass':True})
        if group=='main':
            aa=[p.text for p in src.paragraphs];bb=[p.text for p in d.paragraphs]
            ck('main abstract exact',aa[8:14]==bb[8:14])
            ck('main all paragraphs Results through end exact',aa[aa.index('Results'):]==bb[bb.index('Results'):])
        else:
            ap=[p.text.replace('BMT_supplementary_Figure_S6_v5.pdf','BMT_supplementary_Figure_S6_v6.pdf')for p in src.paragraphs if p.text]
            bp=[p.text for p in d.paragraphs if p.text];pos=0;missing=[]
            for text in ap:
                try:pos=bp.index(text,pos)+1
                except ValueError:missing.append(text)
            ck('all original supplement prose ordered and exact apart from v6 file pointer',not missing,str(missing))
        ck(group+' no raw TeX in plain Word text',not re.search(r'\\(?:frac|sum|begin|hat|mathbf|operatorname)', '\n'.join(p.text for p in d.paragraphs)))
        docs[new]={'sha256':sha(B/'outputs'/new),'tables':len(d.tables),'display_formulas':len(equations)}
    for name in ['BMT_main_manuscript_v10_preview.pdf','BMT_main_manuscript_v10_illustrated_preview.pdf','BMT_supplementary_material_v6_preview.pdf','BMT_supplementary_Figure_S6_v6.pdf']:
        p=B/'outputs'/name;d=fitz.open(p);text='\n'.join(x.get_text()for x in d)
        ck(name+' no replacement/math-error glyph',not any(x in text for x in ['\ufffd','¿']))
        ck(name+' no red formula parser errors',not any(s['color']==0xff0000 for p in d for b in p.get_text('dict')['blocks']if'lines'in b for l in b['lines']for s in l['spans']))
        docs[name]={'sha256':sha(p),'pages':len(d),'bytes':p.stat().st_size}
    return checks,docs,eqrecords

if __name__=='__main__':
    checks,docs,eq=native_checks()
    (B/'evidence/native_math_check_result.json').write_text(json.dumps({'checks':checks,'documents':docs,'equation_native_checks':eq},ensure_ascii=False,indent=2)+'\n')
    print(len(checks),'native checks PASS;',len(eq),'equation semantic matches')
