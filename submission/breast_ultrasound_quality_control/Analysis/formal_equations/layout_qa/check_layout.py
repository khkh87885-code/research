"""Independent v12 layout audit against journal math rules and the pruned scope."""
from pathlib import Path
from datetime import datetime,timezone
from zipfile import ZipFile
import hashlib,json,re,sys
from lxml import etree
from docx import Document
from docx.oxml.ns import qn
import fitz

B=Path('/workspace/bmt_v12');O=B/'outputs';LATEST=Path('/workspace/research_source/submission/bmt_v11');V9=Path('/workspace/research_source/submission/bmt_v9')
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','m':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
checks=[];docs={}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def check(name,result,detail=None):checks.append({'name':name,'pass':bool(result),'detail':detail})
def eqtable(t):
 c=t._tbl.tblPr.find(qn('w:tblCaption'));return c is not None and c.get(qn('w:val'),'').startswith('Equation layout (')
def data(t):return not eqtable(t)
def cells(d):return [[[c.text for c in r.cells]for r in t.rows]for t in d.tables if data(t)]
def media(p):
 with ZipFile(p)as z:return sorted(hashlib.sha256(z.read(n)).hexdigest()for n in z.namelist()if n.startswith('word/media/'))
def tail(d,label):
 p=[x.text for x in d.paragraphs];return p[p.index(label):]
def abstract(d):
 p=[x.text for x in d.paragraphs];return p[p.index('Abstract'):p.index('Introduction')]
def textmath(p):return ''.join(p._p.xpath('.//w:t/text() | .//m:t/text()'))
main=Document(O/'BMT_main_manuscript_v12.docx');supp=Document(O/'BMT_supplementary_material_v8.docx')
oldmain=Document(LATEST/'BMT_main_manuscript_v11.docx');oldsupp=Document(LATEST/'BMT_supplementary_material_v7.docx')
check('Main3data tables66cells exact',len([t for t in main.tables if data(t)])==3 and cells(main)==cells(oldmain) and sum(len(r.cells)for t in main.tables if data(t)for r in t.rows)==66)
check('Supplement19data panels878cells exact',len([t for t in supp.tables if data(t)])==19 and cells(supp)==cells(oldsupp) and sum(len(r.cells)for t in supp.tables if data(t)for r in t.rows)==878)
check('Results discussion declarations refs legends exact',tail(main,'Results')==tail(oldmain,'Results'))
check('Titlepage author info exact',[p.text for p in main.paragraphs[:8]]==[p.text for p in oldmain.paragraphs[:8]])
check('Abstract keywords exact',abstract(main)==abstract(oldmain))
awc=sum(len(x.split())for x in abstract(main)[1:5]);check('Abstract<=200words',awc<=200,awc)
ps=main.paragraphs;i=next(i for i,p in enumerate(ps)if p.text=='Introduction');z=next(i for i,p in enumerate(ps)if p.text.startswith('Research ethics.'))
bwc=len(' '.join(textmath(p)for p in ps[i:z]).split());check('Maintext<=6000words',bwc<=6000,bwc)
refs=[p.text for p in ps if re.match(r'^\d+\.  ',p.text)];check('15references exact',len(refs)==15 and refs==[p.text for p in oldmain.paragraphs if re.match(r'^\d+\.  ',p.text)])
check('No redundant mathematical appendix',[p.text for p in supp.paragraphs].count('Supplementary mathematical methods')==0)
all_equation_refs=set()
for document in [main,supp]:
 for p in document.paragraphs:
  for ref in re.finditer(r'\bEqs?\.\s*\(S?\d+\)(?:\s*(?:and|,)\s*\(S?\d+\))*',p.text):all_equation_refs.update(re.findall(r'\((S?\d+)\)',ref.group()))
for name,doc,labels,base in [('BMT_main_manuscript_v12.docx',main,['1','2','3'],12),('BMT_supplementary_material_v8.docx',supp,['S1','S2'],11)]:
 with ZipFile(O/name)as zipf:
  xml=etree.fromstring(zipf.read('word/document.xml'));settings=etree.fromstring(zipf.read('word/settings.xml'))
 containers=[t for t in doc.tables if eqtable(t)]
 check(name+'exact reduced display count',len(containers)==len(labels))
 check(name+'all display groups true editable oMathPara',len(xml.findall('.//m:oMathPara',NS))==len(labels))
 check(name+'no equation matrices or multiline arrays',not xml.findall('.//m:m',NS) and not xml.findall('.//m:eqArr',NS))
 eq_labels=[];nodes=[]
 for t in containers:
  eq_labels.append(t.cell(0,2).text)
  border=t._tbl.tblPr.find(qn('w:tblBorders'))
  check(name+' '+eq_labels[-1]+'borderless equation-only container',len(t.rows)==1 and len(t.columns)==3 and border is not None and all(x.get(qn('w:val'))in['nil','none']for x in border))
  widths=[c.width for c in t.rows[0].cells]
  check(name+' '+eq_labels[-1]+'symmetric number gutters',widths[0]==widths[2] and abs(widths[0]/914400-.6)<.01,[w/914400 for w in widths])
  check(name+' '+eq_labels[-1]+'native display stays in one cell',len(t.cell(0,1)._tc.findall('.//m:oMathPara',NS))==1 and not t.cell(0,1)._tc.findall('.//w:drawing',NS))
  check(name+' '+eq_labels[-1]+'single display line',not t.cell(0,1)._tc.findall('.//m:brk',NS) and not t.cell(0,1)._tc.findall('.//w:br',NS))
  check(name+' '+eq_labels[-1]+'row cannot split',t.rows[0]._tr.find('w:trPr/w:cantSplit',NS)is not None)
  nodes+=t.cell(0,1)._tc.findall('.//m:oMath',NS)
 check(name+'labels sequential',eq_labels==['('+x+')'for x in labels],eq_labels)
 font=settings.find('.//m:mathFont',NS);check(name+'standardCambriaMath default',font is not None and font.get(qn('m:val'))=='Cambria Math')
 # NIST-style ordinary variables remain math; descriptive A/B/E/I are roman labels.
 marker=[]
 for m in nodes:
  for run in m.findall('.//m:r',NS):
   txt=''.join(run.xpath('./m:t/text()',namespaces=NS))
   if txt in {'A','B','E','I'}:marker.append({'label':txt,'normal':run.find('m:rPr/m:nor',NS)is not None})
 inline_bad=[]
 for run in xml.findall('.//m:r',NS):
  txt=''.join(run.xpath('./m:t/text()',namespaces=NS))
  if txt in {'E','I'}and run.find('m:rPr/m:nor',NS)is None:inline_bad.append(txt)
 check(name+'descriptive inline E/I also upright or ordinary prose',not inline_bad,inline_bad)
 check(name+'descriptive method/cohort indices upright',bool(marker)and all(v['normal']for v in marker),marker)
 variable_runs=[]
 for m in nodes:
  for run in m.findall('.//m:r',NS):
   txt=''.join(run.xpath('./m:t/text()',namespaces=NS))
   if txt in {'U','V','P','q','r','C','W','p','w','s','j','D'}:variable_runs.append({'variable':txt,'not_normal_text':run.find('m:rPr/m:nor',NS)is None})
 check(name+'NIST variables and running indices stay mathematical italic',bool(variable_runs)and all(x['not_normal_text']for x in variable_runs),variable_runs)
 check(name+'short generic mask notation no patienti',not any('i'in ''.join(m.xpath('.//m:sub//m:t/text()',namespaces=NS))for m in nodes))
 plain=' '.join(p.text for p in doc.paragraphs)
 found=set()
 for match in re.finditer(r'\bEqs?\.\s*\(S?\d+\)(?:\s*(?:and|,)\s*\(S?\d+\))*',plain):found.update(re.findall(r'\((S?\d+)\)',match.group()))
 check(name+'no stale equation references',found<=set(labels)|{'S1','S2'},sorted(found))
 check(name+'all display equations cited across main/supplement',set(labels)<=all_equation_refs,sorted(all_equation_refs))
 check(name+'no rawTeX',not re.search(r'\\(?:frac|sum|begin|operatorname|mathrm)',plain))
 docs[name]={'sha256':sha(O/name),'bytes':(O/name).stat().st_size,'equation_labels':labels,'total_layout_plus_data_tables':len(doc.tables),'scientific_data_tables':len([t for t in doc.tables if data(t)])}
# Preserved non-formula prose is checked independently against the v9 baseline.
plan=json.loads((B/'evidence/formula_scope_plan.json').read_text())
for doc,filename,key in [(main,'BMT_main_manuscript_v9.docx','main_replacements'),(supp,'BMT_supplementary_material_v5.docx','supplement_replacements')]:
 before=Document(V9/filename);excluded={r['anchor_exact']for r in plan[key]}
 expected=[p.text.replace('BMT_supplementary_Figure_S6_v5.pdf','BMT_supplementary_Figure_S6_v8.pdf')for p in before.paragraphs if p.text not in excluded]
 actual=[p.text for p in doc.paragraphs if p.text in set(expected)]
 check(filename+'non-replaced v9 prose exactly restored',actual==expected)
check('Formalmain no images',media(O/'BMT_main_manuscript_v12.docx')==[])
check('Supplement5images unchanged',media(O/'BMT_supplementary_material_v8.docx')==media(LATEST/'BMT_supplementary_material_v7.docx') and len(media(O/'BMT_supplementary_material_v8.docx'))==5)
expectedimages=sorted(sha(O/'Figures'/f'Figure_{i}.png')for i in range(1,6))
check('Readingcopy5images unchanged',media(O/'BMT_main_manuscript_v12_illustrated.docx')==expectedimages)
check('Main scientific figures+tables remains8',len(expectedimages)+len([t for t in main.tables if data(t)])==8)
check('S6 byte-identical',sha(O/'BMT_supplementary_Figure_S6_v8.pdf')==sha(LATEST/'BMT_supplementary_Figure_S6_v7.pdf'))
for name in ['BMT_main_manuscript_v12_illustrated.docx']:
 docs[name]={'sha256':sha(O/name),'bytes':(O/name).stat().st_size}
proof=next(O.glob('*proof*v12*.pdf'),None)
pdfs=['BMT_main_manuscript_v12_preview.pdf','BMT_main_manuscript_v12_illustrated_preview.pdf','BMT_supplementary_material_v8_preview.pdf','BMT_supplementary_Figure_S6_v8.pdf']+([proof.name]if proof else[])
for name in pdfs:
 d=fitz.open(O/name);bounds=[];bad=[];empty=[];number=[];equation_pages={};styles=[]
 for i,p in enumerate(d):
  if len(p.get_text().strip())<10:empty.append(i+1)
  for b in p.get_text('dict')['blocks']:
   for ln in b.get('lines',[]):
    for sp in ln['spans']:
     box=fitz.Rect(sp['bbox']);txt=sp['text'].strip()
     if box.x0<2 or box.y0<2 or box.x1>p.rect.width-2 or box.y1>p.rect.height-2:bounds.append([i+1,txt,list(box)])
     if '¿'in txt or'\ufffd'in txt or sp['color']==0x800000:bad.append([i+1,txt])
     if re.fullmatch(r'\(S?\d+\)',txt):number.append(txt[1:-1]);equation_pages[txt[1:-1]]=i+1
     if txt in {'A','B','E','I'}:styles.append({'text':txt,'font':sp['font'],'size':sp['size'],'page':i+1,'upright':not any(v in sp['font'].lower()for v in ['italic','oblique'])})
 check(name+'no clip/empty/parser errors',not bounds and not empty and not bad,{'bounds':bounds,'empty':empty,'errors':bad})
 if'main_manuscript'in name:check(name+'exact3display labels',number==['1','2','3'],number)
 if'material_v8'in name:check(name+'exact2display labels',number==['S1','S2'],number)
 if name.startswith('BMT_supplementary'):check(name+'under10MB',(O/name).stat().st_size<10_000_000)
 docs[name]={'sha256':sha(O/name),'bytes':(O/name).stat().st_size,'pages':len(d),'equation_pages':equation_pages,'label_font_samples':styles,'out_of_page_text':bounds,'empty_pages':empty}
# Quantitative check of real rendered display centers and actual base fonts.
for filename,base in [('BMT_main_manuscript_v12_preview.pdf',12),('BMT_supplementary_material_v8_preview.pdf',11)]:
 geometry=[]
 for page in fitz.open(O/filename):
  spans=[sp for block in page.get_text('dict')['blocks']for line in block.get('lines',[])for sp in line['spans']]
  numbers=[sp for sp in spans if re.fullmatch(r'\(S?\d+\)',sp['text'].strip())]
  for number in numbers:
   near=[sp for sp in spans if abs(sp['origin'][1]-number['origin'][1])<2.1 and sp['bbox'][2]<number['bbox'][0]-10 and len(sp['text'])<45]
   assert near,number
   x0=min(sp['bbox'][0]for sp in near);x1=max(sp['bbox'][2]for sp in near);center=(x0+x1)/2
   basechars=[sp for sp in near if'Symbol'not in sp['font']and sp['size']>.9*base]
   geometry.append({'label':number['text'],'page':page.number+1,'ink_center_pt':center,'page_center_pt':page.rect.width/2,'center_error_pt':abs(center-page.rect.width/2),'number_right_pt':number['bbox'][2],'number_size':number['size'],'minimum_ink_number_gap_pt':number['bbox'][0]-x1,'base_char_sizes':[sp['size']for sp in basechars]})
   check(filename+' '+number['text']+'visually centered within2pt',abs(center-page.rect.width/2)<2,geometry[-1])
   check(filename+' '+number['text']+'base and number actual font size',abs(number['size']-base)<.1 and bool(basechars)and all(abs(sp['size']-base)<.15 for sp in basechars),geometry[-1])
 check(filename+'right equation numbers aligned',max(g['number_right_pt']for g in geometry)-min(g['number_right_pt']for g in geometry)<.1,geometry)
 docs[filename]['display_geometry']=geometry
if proof:
 original=[]
 for f in ['BMT_main_manuscript_v12_preview.pdf','BMT_supplementary_material_v8_preview.pdf']:
  for page in fitz.open(O/f):
   if re.search(r'^\(S?\d+\)$',page.get_text(),re.M):original.append(page.get_text())
 pr=fitz.open(proof)
 check('Two-page proof equals current final mathematical pages',len(pr)==2 and [p.get_text()for p in pr]==original)

check('SupplementDOCX under10MB',(O/'BMT_supplementary_material_v8.docx').stat().st_size<10_000_000)
report={'checked_utc':datetime.now(timezone.utc).isoformat(),'scope':'v12 pruned formal equations verified against BMT mathematics rules and NIST typography, with independent visual review','status':'PROGRAMMATIC_PASS_VISUAL_PENDING'if all(c['pass']for c in checks)else'FAIL','checks':checks,'documents':docs,'abstract_words':awc,'body_words_including_inline_math':bwc,'final_documents_pending':True,'visual_review_pending':True,'external_rules':{'BMT':{'source':str(B/'evidence/bmt_official_mathematics_source.md'),'rules':['Equations well aligned and not crowded','Avoid complicated superscripts/subscripts','Editable Word equations rather than images','Displayed equations numbered consecutively when cited']},'NIST':{'source':str(B/'evidence/nist_official_mathematics_source.md'),'rules':['Quantity and variable symbols italic','Descriptive labels upright']},'Microsoft':{'source':str(B/'evidence/microsoft_official_equation_source.md'),'rules':['Professional editable equation objects']}}}
if '--final'in sys.argv:
 vpath=B/'qa/layout_qa/visual_review.json';v=json.loads(vpath.read_text());h=json.loads((B/'evidence/current_document_hashes.json').read_text())
 for name,val in h.items():assert sha(O/name)==val['sha256']and docs[name]['sha256']==val['sha256'],name
 assert v['documents']==h and v['status']=='PASS'and not v['findings']
 check('All5display equations individually visually inspected',set(v['display_labels'])=={'1','2','3','S1','S2'})
 check('BMT/NIST visual rules individually passed',v['external_rule_visual_pass'])
 report.update(status='PASS'if all(c['pass']for c in checks)else'FAIL',final_documents_pending=False,visual_review_pending=False,visual_review={'path':str(vpath),'sha256':sha(vpath),'summary':v['summary']},limits=['Final PDF and native Word XML were inspected. Microsoft Word and WPS were not directly run.','Equation layout containers are administrative layout structures, not scientific data tables; they are explicitly tagged and excluded from the3main/19supplement scientific-table counts.'])
 assert report['status']=='PASS',[c for c in checks if not c['pass']]
(B/'evidence/independent_layout_qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'checks':len(checks),'passed':sum(c['pass']for c in checks),'failed':[c['name']for c in checks if not c['pass']]},indent=2))
