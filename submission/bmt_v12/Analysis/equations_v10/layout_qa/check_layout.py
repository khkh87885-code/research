"""Independent read-only validation of editable math and final layout exports."""
from pathlib import Path
from datetime import datetime,timezone
from zipfile import ZipFile
from lxml import etree
from docx import Document
import fitz,hashlib,json,re

B=Path('/workspace/bmt_v10');O=B/'outputs';S=Path('/workspace/research_source/submission/bmt_v9')
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','m':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
checks=[];docs={}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def check(name,result,detail=None):
    checks.append({'name':name,'pass':bool(result),'detail':detail})
def cells(d):return [[[c.text for c in r.cells]for r in t.rows]for t in d.tables]
def rawtext(p):return ''.join(p._p.xpath('.//w:t/text() | .//m:t/text()'))
def media(path):
    with ZipFile(path)as z:return sorted(hashlib.sha256(z.read(n)).hexdigest()for n in z.namelist()if n.startswith('word/media/'))
def mathmeta(path,labels):
    with ZipFile(path)as z:xml=etree.fromstring(z.read('word/document.xml'))
    equations=[];kept=[];mathtexts=[]
    for p in xml.findall('./w:body/w:p',NS):
        text=''.join(p.xpath('.//w:t/text()',namespaces=NS))
        m=re.fullmatch(r'\((S?\d+)\)',text)
        if m and p.find('m:oMath',NS)is not None:
            equations.append(m[1]);kept.append(p.find('w:pPr/w:keepLines',NS)is not None)
            mathtexts.append(''.join(p.xpath('.//m:t/text()',namespaces=NS)))
    check(path.name+' display numbering',equations==labels,equations)
    check(path.name+' native editable math',len(xml.findall('.//m:oMath',NS))>=len(labels))
    check(path.name+' equation paragraphs cannot split',all(kept))
    wt=''.join(xml.xpath('.//w:t/text()',namespaces=NS))
    check(path.name+' no raw TeX commands',not re.search(r'\\(?:frac|begin|sum|operatorname|mathbf|widehat)',wt))
    for dp in xml.findall('.//m:dPr',NS):
        names=[etree.QName(c).localname for c in dp]
        if 'sepChr'in names and'endChr'in names:assert names.index('sepChr')<names.index('endChr')
    return {'equation_labels':equations,'math_texts':mathtexts,'office_math_objects':len(xml.findall('.//m:oMath',NS))}

main=Document(O/'BMT_main_manuscript_v10.docx');old=Document(S/'BMT_main_manuscript_v9.docx')
supp=Document(O/'BMT_supplementary_material_v6.docx');olds=Document(S/'BMT_supplementary_material_v5.docx')
check('Main 3 editable tables /66 cells exact',len(main.tables)==3 and cells(main)==cells(old) and sum(len(r.cells)for t in main.tables for r in t.rows)==66)
check('Supplement 19 panels /878 cells exact',len(supp.tables)==19 and cells(supp)==cells(olds) and sum(len(r.cells)for t in supp.tables for r in t.rows)==878)
def tail(d,label):
    p=[p.text for p in d.paragraphs];return p[p.index(label):]
check('Results, discussion, declarations, references, table/figure legends exact',tail(main,'Results')==tail(old,'Results'))
check('Title page author and correspondence exact',[p.text for p in main.paragraphs[:8]]==[p.text for p in old.paragraphs[:8]])
def abstract(d):
    ps=d.paragraphs;a=next(i for i,p in enumerate(ps)if p.text=='Abstract');z=next(i for i,p in enumerate(ps)if p.text=='Introduction')
    return [p.text for p in ps[a:z]]
check('Abstract and keywords exact',abstract(main)==abstract(old))
ab=abstract(main);awc=sum(len(t.split())for t in ab[1:5]);check('Abstract <=200 words',awc<=200,awc)
ps=main.paragraphs;i=next(i for i,p in enumerate(ps)if p.text=='Introduction');e=next(i for i,p in enumerate(ps)if p.text.startswith('Research ethics.'))
bwc=len(' '.join(rawtext(p)for p in ps[i:e]).split());check('Main text <=6000 words including math text',bwc<6000,bwc)
refs=[p.text for p in ps if re.match(r'^\d+\.  ',p.text)];check('15 references unchanged',len(refs)==15 and refs==[p.text for p in old.paragraphs if re.match(r'^\d+\.  ',p.text)])
before_refs=' '.join(p.text for p in ps[:next(i for i,p in enumerate(ps)if p.text=='References')]);seen=[]
for chunk in re.findall(r'\[([\d, –-]+)\]',before_refs):
    for token in chunk.split(','):
        token=token.strip();rg=re.fullmatch(r'(\d+)\s*[–-]\s*(\d+)',token)
        nums=range(int(rg[1]),int(rg[2])+1)if rg else [int(token)]
        for n in nums:
            if n not in seen:seen.append(n)
check('Citations first appear sequentially 1..15',seen==list(range(1,16)),seen)
oldtext=[p.text.replace('BMT_supplementary_Figure_S6_v5.pdf','BMT_supplementary_Figure_S6_v6.pdf')for p in olds.paragraphs]
actual=[p.text for p in supp.paragraphs if p.text in set(oldtext)]
check('Original supplement prose exact apart from S6 filename',actual==oldtext)
check('Formal main contains no image media',media(O/'BMT_main_manuscript_v10.docx')==[])
check('Supplement retains exactly original 5 image media',media(O/'BMT_supplementary_material_v6.docx')==media(S/'BMT_supplementary_material_v5.docx') and len(media(O/'BMT_supplementary_material_v6.docx'))==5)
expected_media=sorted(sha(O/'Figures'/f'Figure_{n}.png')for n in range(1,6))
check('Illustrated copy contains only unchanged five main figures',media(O/'BMT_main_manuscript_v10_illustrated.docx')==expected_media)
check('Five figures plus three tables =8',len(expected_media)+len(main.tables)==8)
check('Separate S6 unchanged from v9',sha(O/'BMT_supplementary_Figure_S6_v6.pdf')==sha(S/'BMT_supplementary_Figure_S6_v5.pdf'))
for filename in ['BMT_main_manuscript_v10.docx','BMT_main_manuscript_v10_illustrated.docx','BMT_supplementary_material_v6.docx']:
    docs[filename]={'sha256':sha(O/filename),'bytes':(O/filename).stat().st_size}
docs['BMT_main_manuscript_v10.docx'].update(mathmeta(O/'BMT_main_manuscript_v10.docx',[str(i)for i in range(1,15)]))
docs['BMT_supplementary_material_v6.docx'].update(mathmeta(O/'BMT_supplementary_material_v6.docx',[f'S{i}'for i in range(1,13)]))
for document,expected,label in [(main,{str(i)for i in range(1,15)},'Main'),(supp,{f'S{i}'for i in range(1,13)},'Supplement')]:
    mentioned=set()
    for p in document.paragraphs:
        for ref in re.finditer(r'\bEqs?\.\s*\(S?\d+\)(?:\s*(?:and|,)\s*\(S?\d+\))*',p.text):
            mentioned.update(re.findall(r'\((S?\d+)\)',ref.group()))
    check(label+' all display equations cited and no undefined equation references',mentioned==expected,sorted(mentioned))
pdfs=['BMT_main_manuscript_v10_preview.pdf','BMT_main_manuscript_v10_illustrated_preview.pdf','BMT_supplementary_material_v6_preview.pdf','BMT_supplementary_Figure_S6_v6.pdf']
for filename in pdfs:
    d=fitz.open(O/filename);bounds=[];placeholder=[];red=[];empty=[];nums=[];eqpages={};eq_number_bounds=[]
    for i,p in enumerate(d):
        t=p.get_text()
        if len(t.strip())<10:empty.append(i+1)
        labels=re.findall(r'^\((S?\d+)\)$',t,re.M);nums+=labels
        for label in labels:eqpages[label]=i+1
        for block in p.get_text('dict')['blocks']:
            for l in block.get('lines',[]):
                for sp in l['spans']:
                    r=fitz.Rect(sp['bbox'])
                    if r.x0<2 or r.y0<2 or r.x1>p.rect.width-2 or r.y1>p.rect.height-2:bounds.append({'page':i+1,'text':sp['text'],'bbox':list(r)})
                    if '¿'in sp['text'] or '\ufffd'in sp['text']:placeholder.append({'page':i+1,'text':sp['text']})
                    if sp['color']==0x800000:red.append({'page':i+1,'text':sp['text']})
                    if re.fullmatch(r'\(S?\d+\)',sp['text']):eq_number_bounds.append({'label':sp['text'],'page':i+1,'bbox':list(r)})
    check(filename+' no clipped text',not bounds,bounds)
    check(filename+' no empty pages',not empty,empty)
    check(filename+' no missing-math placeholders',not placeholder and not red,{'placeholder':placeholder,'red':red})
    if 'main_manuscript'in filename:check(filename+' equation labels14 sequential',nums==[str(i)for i in range(1,15)],nums)
    if 'material_v6'in filename:check(filename+' equation labelsS1..S12 sequential',nums==[f'S{i}'for i in range(1,13)],nums)
    if filename.startswith('BMT_supplementary'):check(filename+' <10MB',(O/filename).stat().st_size<10_000_000)
    docs[filename]={'sha256':sha(O/filename),'bytes':(O/filename).stat().st_size,'pages':len(d),'equation_pages':eqpages,'equation_number_bounds':eq_number_bounds,'out_of_page_text':bounds,'empty_pages':empty}
check('Supplement DOCX <10MB',(O/'BMT_supplementary_material_v6.docx').stat().st_size<10_000_000)
report={'checked_utc':datetime.now(timezone.utc).isoformat(),'scope':'Independent editable-equation layout and source-preservation QA','checks':checks,'documents':docs,'abstract_words':awc,'body_words_including_math_text':bwc,'final_documents_pending':True,'visual_review_pending':True}
(B/'evidence/independent_layout_qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'checks':len(checks),'passed':sum(c['pass']for c in checks),'failed':[c['name']for c in checks if not c['pass']]},indent=2))
