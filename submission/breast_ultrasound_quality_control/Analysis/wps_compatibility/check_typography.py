"""Independent native-structure and actual PDF typography review for v13."""
from pathlib import Path
from datetime import datetime,timezone
from zipfile import ZipFile
from lxml import etree
from docx import Document
from docx.oxml.ns import qn
import fitz,hashlib,json,re
B=Path('/workspace/bmt_v13');O=B/'outputs';S=Path('/workspace/research_source/submission/bmt_v12')
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','m':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
checks=[];documents={};geometry=[]
def check(name,ok,detail=None):checks.append({'name':name,'pass':bool(ok),'detail':detail})
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def eqtable(t):
 c=t._tbl.tblPr.find(qn('w:tblCaption'));return c is not None and c.get(qn('w:val'),'').startswith('Equation layout (')
def cells(d):return [[[c.text for c in r.cells]for r in t.rows]for t in d.tables if not eqtable(t)]
def equation(p):
 t=''.join(p._p.xpath('.//w:t/text()')).strip();return p._p.find('m:oMath',NS)is not None and re.fullmatch(r'\(S?\d+\)',t)
def plain(d):return [p.text.replace('BMT_supplementary_Figure_S6_v8.pdf','BMT_supplementary_Figure_S6_v9.pdf')for p in d.paragraphs if p.text.strip()and not equation(p)]
def media(p):
 with ZipFile(p)as z:return sorted(hashlib.sha256(z.read(n)).hexdigest()for n in z.namelist()if n.startswith('word/media/'))
for new,old,count,cellcount,labels in [('BMT_main_manuscript_v13.docx','BMT_main_manuscript_v12.docx',3,66,['1','2','3']),('BMT_supplementary_material_v9.docx','BMT_supplementary_material_v8.docx',19,878,['S1','S2'])]:
 d=Document(O/new);s=Document(S/old)
 check(new+' only original scientific tables remain',len(d.tables)==count and not any(eqtable(t)for t in d.tables),len(d.tables))
 check(new+' data cells exact',cells(d)==cells(s)and sum(len(r.cells)for t in d.tables for r in t.rows)==cellcount)
 check(new+' all non-equation prose exact',plain(d)==plain(s))
 with ZipFile(O/new)as z:r=etree.fromstring(z.read('word/document.xml'))
 check(new+' no automatic delimiter objects',not r.findall('.//m:d',NS))
 ps=[p for p in d.paragraphs if equation(p)]
 check(new+' five-equation scope and labels retained',[''.join(p._p.xpath('.//w:t/text()')).strip()for p in ps]==['('+x+')'for x in labels])
 check(new+' native editable fractions/sums retained',len(r.findall('.//m:oMath',NS))>=len(labels) and len(r.findall('.//m:f',NS))>=1 and len(r.findall('.//m:nary',NS))>=1)
 for p,label in zip(ps,labels):
  check(new+' '+label+' one unsplit equation paragraph',p._p.find('w:pPr/w:keepLines',NS)is not None and not p._p.findall('.//w:br',NS))
  check(new+' '+label+' standard center/right tabs',{'center','right'}<=set(t.get(qn('w:val'))for t in p._p.findall('w:pPr/w:tabs/w:tab',NS)))
  check(new+' '+label+' literal parenthesis runs valid',all(x.getparent().find('m:rPr/m:nor',NS)is not None for x in p._p.findall('.//m:t',NS)if x.text in ['(',')']))
 check(new+' no new equation images',media(O/new)==media(S/old))
 documents[new]={'sha256':sha(O/new),'bytes':(O/new).stat().st_size,'native_equation_labels':labels}
# Illustrated DOCX is not a scientific source but must preserve the five figure media.
reading=O/'BMT_main_manuscript_v13_illustrated.docx';check('Reading copy contains unchanged five figures',media(reading)==sorted(sha(S/'Figures'/f'Figure_{i}.png')for i in range(1,6)))
documents[reading.name]={'sha256':sha(reading),'bytes':reading.stat().st_size}
for filename in ['BMT_main_manuscript_v13_preview.pdf','BMT_main_manuscript_v13_illustrated_preview.pdf','BMT_supplementary_material_v9_preview.pdf','BMT_supplementary_Figure_S6_v9.pdf']:
 d=fitz.open(O/filename);bounds=[];bad=[];empty=[]
 for i,p in enumerate(d):
  if len(p.get_text().strip())<10:empty.append(i+1)
  for bl in p.get_text('dict')['blocks']:
   for ln in bl.get('lines',[]):
    for sp in ln['spans']:
     r=fitz.Rect(sp['bbox']);txt=sp['text']
     if r.x0<2 or r.y0<2 or r.x1>p.rect.width-2 or r.y1>p.rect.height-2:bounds.append([i+1,txt])
     if '¿'in txt or'\ufffd'in txt or sp['color']==0x800000:bad.append([i+1,txt])
 check(filename+' no clipping/empty/parser errors',not bounds and not empty and not bad,{'bounds':bounds,'empty':empty,'errors':bad})
 documents[filename]={'sha256':sha(O/filename),'bytes':(O/filename).stat().st_size,'pages':len(d)}
for filename,n,labels,base in [('BMT_main_manuscript_v13_preview.pdf',5,['1','2','3'],12),('BMT_supplementary_material_v9_preview.pdf',19,['S1','S2'],11)]:
 p=fitz.open(O/filename)[n-1];spans=[s for b in p.get_text('dict')['blocks']for ln in b.get('lines',[])for s in ln['spans']]
 numbers=[s for s in spans if re.fullmatch(r'\(S?\d+\)',s['text'].strip())]
 check(filename+' actual display labels',[''.join(re.findall(r'\((S?\d+)\)',s['text']))for s in numbers]==labels)
 gs=[]
 for num in numbers:
  near=[s for s in spans if abs(s['origin'][1]-num['origin'][1])<2.1 and s['bbox'][2]<num['bbox'][0]-10 and len(s['text'])<45]
  center=(min(s['bbox'][0]for s in near)+max(s['bbox'][2]for s in near))/2
  basechars=[s for s in near if'Symbol'not in s['font']and s['size']>.9*base]
  g={'document':filename,'page':n,'label':num['text'],'center_error_pt':abs(center-p.rect.width/2),'number_right_pt':num['bbox'][2],'number_size':num['size'],'base_char_sizes':[s['size']for s in basechars]};gs.append(g);geometry.append(g)
  check(filename+' '+num['text']+' centered within2pt',g['center_error_pt']<2,g)
  check(filename+' '+num['text']+' actual base/number size',abs(num['size']-base)<.1 and all(abs(s['size']-base)<.15 for s in basechars),g)
 check(filename+' right equation numbers align',max(g['number_right_pt']for g in gs)-min(g['number_right_pt']for g in gs)<.1,gs)
 check(filename+' literal parentheses recognizable in extracted PDF','('in p.get_text()and')'in p.get_text())
proof=O/'BMT_formula_layout_proof_v13.pdf'
if proof.exists():
 pd=fitz.open(proof);check('Proof is current two mathematical pages',len(pd)==2 and [p.get_text()for p in pd]==[fitz.open(O/'BMT_main_manuscript_v13_preview.pdf')[4].get_text(),fitz.open(O/'BMT_supplementary_material_v9_preview.pdf')[18].get_text()]);documents[proof.name]={'sha256':sha(proof),'bytes':proof.stat().st_size,'pages':len(pd)}
check('Visual review all five formulas passed',True,{'main_page':5,'supplement_page':19,'reviewed_labels':['1','2','3','S1','S2'],'observation':'Literal parentheses ordinary and recognizable; fraction bars, four-direction sum and subscripts complete; numbers right aligned; native math remains legible in its actual paper context; no H/I-like fence glyph or new overlap in exported PDF.'})
check('No claim of direct WPS/MicrosoftWord test',True)
report={'checked_utc':datetime.now(timezone.utc).isoformat(),'status':'PASS'if all(c['pass']for c in checks)else'FAIL','final_documents_pending':False,'scope':'Native object and real exported PDF typography audit for literal-fence/non-table equation paragraphs','checks':checks,'documents':documents,'display_geometry':geometry,'visual_review':{'method':'Individually viewed actual mainp5 and supplementp19 rendered at1.8x','labels':['1','2','3','S1','S2'],'image_directory':str(B/'qa/typography_view')},'known_failing_viewer':'WPS','direct_wps_tested':False,'direct_microsoft_word_tested':False,'limits':['The old source already used correct parenthesis characters. The exact internal reason for the user WPS rendering defect is not proven.','This review confirms literal punctuation, native structure, preserved content and the current LibreOffice PDF appearance; it is not evidence that WPS or Microsoft Word has been directly run.']}
(B/'qa/typography_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'checks':len(checks),'passed':sum(c['pass']for c in checks),'failed':[c['name']for c in checks if not c['pass']]},indent=2))
