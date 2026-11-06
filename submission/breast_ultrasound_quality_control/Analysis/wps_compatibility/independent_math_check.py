"""Read-only v13 scientific-content and native-math compatibility QA."""
from pathlib import Path
from zipfile import ZipFile
from datetime import datetime,timezone
import json,hashlib,re
from lxml import etree
from docx import Document
import fitz
B=Path('/workspace/bmt_v13');SRC=Path('/workspace/research_source/submission/bmt_v12')
NS={'m':'http://schemas.openxmlformats.org/officeDocument/2006/math','w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def xml(p):
 with ZipFile(p)as z:return etree.fromstring(z.read('word/document.xml'))
def chars(e):return ''.join(e.xpath('.//m:t/text()',namespaces=NS))
def merge(items):
 out=[]
 for x in items:
  if out and out[-1][0]=='text'and x[0]=='text':out[-1]=('text',out[-1][1]+x[1])
  else:out.append(x)
 return tuple(out)
def seq(e):return merge([x for child in e for x in signature(child)])
def signature(e):
 """Preserve fraction/script scopes; make fence rendering and sum-body binding explicit.

 Legacy nary/e boundaries are ignored in this comparison only; separate checks
 below require every final summand to be complete inside nary/e.
 """
 tag=etree.QName(e).localname
 if tag.endswith('Pr')or tag in ['argPr']:return []
 if tag=='r':return [('text',chars(e))]
 if tag=='d':
  p=e.find('m:dPr',NS)
  def attr(name,default):
   x=p.find('m:'+name,NS)if p is not None else None
   return x.get('{'+NS['m']+'}val',default)if x is not None else default
  out=[('text',attr('begChr','('))];sep=attr('sepChr','|')
  for i,arg in enumerate(e.findall('m:e',NS)):
   if i:out.append(('text',sep))
   out.extend(seq(arg))
  out.append(('text',attr('endChr',')')));return list(merge(out))
 if tag=='f':return [('fraction',seq(e.find('m:num',NS)),seq(e.find('m:den',NS)))]
 if tag in ['sSub','sSup','sSubSup']:
  return[(tag,seq(e.find('m:e',NS)),*(seq(e.find('m:'+n,NS))for n in ['sub','sup']if e.find('m:'+n,NS)is not None))]
 if tag=='acc':
  pr=e.find('m:accPr/m:chr',NS);a=pr.get('{'+NS['m']+'}val','')if pr is not None else''
  return[('accent',a,seq(e.find('m:e',NS)))]
 if tag=='nary':
  c=e.find('m:naryPr/m:chr',NS);c=c.get('{'+NS['m']+'}val','Σ')if c is not None else'Σ'
  return[('nary',c,seq(e.find('m:sub',NS)),seq(e.find('m:sup',NS)))]+list(seq(e.find('m:e',NS)))
 return list(seq(e))
def equation_label(p):
 if not p._p.xpath('.//m:oMath'):return None
 t=p.text.strip();m=re.fullmatch(r'\((S?\d+)\)',t)
 return m.group(1)if m else None
def old_data_tables(d):
 out=[]
 for t in d.tables:
  c=t._tbl.tblPr.find('w:tblCaption',NS)
  if c is None or not c.get('{'+NS['w']+'}val','').startswith('Equation layout ('):out.append(t)
 return out
def snapshot(tt):return[[[c.text for c in row.cells]for row in t.rows]for t in tt]

def run():
 checks=[];docs={};eqrecords=[]
 def ck(name,ok,detail=''):
  checks.append({'name':name,'pass':bool(ok),'detail':detail});assert ok,(name,detail)
 configs=[('main','BMT_main_manuscript_v12.docx','BMT_main_manuscript_v13.docx',['1','2','3'],3,66),('supplement','BMT_supplementary_material_v8.docx','BMT_supplementary_material_v9.docx',['S1','S2'],19,878)]
 for group,old,new,labels,nt,nc in configs:
  a=Document(SRC/old);b=Document(B/'outputs'/new);ra=xml(SRC/old);rb=xml(B/'outputs'/new)
  ck(group+' scientific table count',len(b.tables)==nt)
  ck(group+' all scientific table cells exact',snapshot(b.tables)==snapshot(old_data_tables(a)))
  ck(group+' scientific cell count',sum(len(row.cells)for t in b.tables for row in t.rows)==nc)
  ck(group+' no formula layout table',not any(c.get('{'+NS['w']+'}val','').startswith('Equation layout (')for c in rb.findall('.//w:tblCaption',NS)))
  eqs=[p for p in b.paragraphs if equation_label(p)is not None]
  ck(group+' formula labels/order unchanged',[equation_label(p)for p in eqs]==labels)
  ck(group+' all formulas are ordinary single paragraphs',all(len(p._p.findall('./m:oMath',NS))==1 for p in eqs))
  ck(group+' no automatic delimiter objects',not rb.findall('.//m:d',NS))
  ck(group+' no math paragraph wrappers',not rb.findall('.//m:oMathPara',NS))
  oldp=[p.text for p in a.paragraphs];newp=[p.text for p in b.paragraphs if equation_label(p)is None]
  if group=='supplement':oldp=[s.replace('BMT_supplementary_Figure_S6_v8.pdf','BMT_supplementary_Figure_S6_v9.pdf')for s in oldp]
  ck(group+' all ordinary prose exact apart from S6 filename',oldp==newp)
  ma=ra.findall('.//m:oMath',NS);mb=rb.findall('.//m:oMath',NS)
  ck(group+' native math object count unchanged',len(ma)==len(mb))
  for i,(x,y)in enumerate(zip(ma,mb),1):ck(group+' native arithmetic fraction/script/accent signature '+str(i),seq(x)==seq(y))
  for tag in ['f','nary','sSub','sSup','sSubSup','acc']:
   ck(group+' native '+tag+' object count unchanged',len(ra.findall('.//m:'+tag,NS))==len(rb.findall('.//m:'+tag,NS)))
  # Every new parenthesis is ASCII normal math text in a standard text font.
  parentheses=[r for r in rb.findall('.//m:r',NS)if chars(r)in ['(',')']]
  ck(group+' all literal parentheses normal text',bool(parentheses)and all(r.find('m:rPr/m:nor',NS)is not None for r in parentheses))
  ck(group+' all literal parentheses Times New Roman',all(r.find('w:rPr/w:rFonts',NS)is not None and r.find('w:rPr/w:rFonts',NS).get('{'+NS['w']+'}ascii')=='Times New Roman'for r in parentheses))
  ck(group+' literal opening/closing parenthesis counts balanced',sum(chars(r)=='('for r in parentheses)==sum(chars(r)==')'for r in parentheses))
  oldeq={}
  for t in a.tables:
   c=t._tbl.tblPr.find('w:tblCaption',NS)
   if c is not None:
    m=re.fullmatch(r'Equation layout \((S?\d+)\)',c.get('{'+NS['w']+'}val',''))
    if m:oldeq[m.group(1)]=t._tbl.find('.//m:oMath',NS)
  for p in eqs:
   label=equation_label(p);m=p._p.find('./m:oMath',NS)
   ck(group+' equation '+label+' source arithmetic equivalent',seq(oldeq[label])==seq(m))
   if label in ['3','S1','S2']:
    nary=m.find('.//m:nary',NS);body=nary.find('m:e',NS);parent=nary.getparent();tail=list(parent)[parent.index(nary)+1:]
    ck(group+' '+label+' no operand remains outside summation',all(etree.QName(x).localname=='r'and chars(x)in ['.',',']for x in tail))
    if label=='3':
     ck('riskB full Dice function is within summand',chars(body)=='D(P0,Pj)',chars(body))
     ck('riskB complete P subscripts inside summand',len(body.findall('.//m:sSub',NS))==2)
     ck('riskB sum bounds still1..4',chars(nary.find('m:sub',NS))=='j=1'and chars(nary.find('m:sup',NS))=='4')
     ck('riskB summand has no H/I substitution','H'not in chars(body)and'I'not in chars(body))
    else:
     f=body.find('m:f',NS)
     ck(group+' '+label+' mean fraction lies inside summand',f is not None)
     ck(group+' '+label+' denominator remains2',chars(f.find('m:den',NS))=='2')
     expected='pE,s+pI,s'if label=='S1'else'wE,s+wI,s'
     ck(group+' '+label+' mean numerator correct',chars(f.find('m:num',NS))==expected)
     ck(group+' '+label+' body has literal factor parentheses',chars(body).startswith('(')and')'in chars(body))
   eqrecords.append({'document':group,'label':label,'pass':True,'math_text':chars(m),'source_signature_equivalent':True,'native_math_sha256':hashlib.sha256(etree.tostring(m)).hexdigest()})
  if group=='main':
   aa=[p.text for p in a.paragraphs];bb=newp
   ck('main title author metadata and abstract unchanged',aa[:14]==bb[:14])
   ck('main Results declarations references captions unchanged',aa[aa.index('Results'):]==bb[bb.index('Results'):])
  with ZipFile(SRC/old)as za,ZipFile(B/'outputs'/new)as zb:
   pa={n:hashlib.sha256(za.read(n)).hexdigest()for n in za.namelist()if n.startswith('word/media/')};pb={n:hashlib.sha256(zb.read(n)).hexdigest()for n in zb.namelist()if n.startswith('word/media/')}
   ck(group+' all embedded images unchanged',pa==pb)
  docs[new]={'sha256':sha(B/'outputs'/new),'bytes':(B/'outputs'/new).stat().st_size,'data_tables':nt,'scientific_cells':nc,'formula_paragraphs':len(eqs)}
 # Reading copy must contain the same complete main mathematical content.
 im=B/'outputs/BMT_main_manuscript_v13_illustrated.docx';mm=xml(im);main=xml(B/'outputs/BMT_main_manuscript_v13.docx')
 ck('reading copy native math identical',[seq(x)for x in mm.findall('.//m:oMath',NS)]==[seq(x)for x in main.findall('.//m:oMath',NS)])
 ck('reading copy no delimiters or formula tables',not mm.findall('.//m:d',NS)and len(Document(im).tables)==3)
 docs[im.name]={'sha256':sha(im),'bytes':im.stat().st_size}
 ck('S6 bytes unchanged',sha(B/'outputs/BMT_supplementary_Figure_S6_v9.pdf')==sha(SRC/'BMT_supplementary_Figure_S6_v8.pdf'))
 for p in (B/'outputs').glob('*.pdf'):
  pdf=fitz.open(p);text='\n'.join(x.get_text()for x in pdf)
  ck(p.name+' no replacement or parser glyph',not any(x in text for x in ['¿','\ufffd']))
  ck(p.name+' no red formula error text',not any(s['color']==0xff0000 for pg in pdf for bl in pg.get_text('dict')['blocks']if'lines'in bl for line in bl['lines']for s in line['spans']))
  docs[p.name]={'sha256':sha(p),'bytes':p.stat().st_size,'pages':len(pdf)}
 repair=json.loads((B/'evidence/repair_report.json').read_text())
 for x in repair['documents']:ck('repair hash matches '+Path(x['output']).name,sha(x['output'])==x['sha256'])
 return {'checked_utc':datetime.now(timezone.utc).isoformat(),'status':'PASS','checks':checks,'checks_passed':len(checks),'equations_verified':5,'equation_checks':eqrecords,'documents':docs,'source_repair_report_sha256':sha(B/'evidence/repair_report.json'),'source_v12_main_sha256':sha(SRC/'BMT_main_manuscript_v12.docx'),'source_v12_supplement_sha256':sha(SRC/'BMT_supplementary_material_v8.docx'),'unresolved_findings':0,'final_documents_pending':False,'direct_wps_tested':False,'notes':['All scientific definitions and ordinary prose are unchanged from v12, except the S6v9 filename. The3main and2supplement equations remain native editable OfficeMath.','The arithmetic signature preserves fraction/script/accent structure and every source token while allowing dynamic-delimiter containers to become literal parentheses and legacy nary-body boundaries to expand. Separate checks require complete final summands, so this equivalence proof does not accept an incorrectly truncated summation operand.','RiskB contains the complete D(P0,Pj) function inside nary/e, with both P subscripts and bounds j=1..4. Kitagawa C/W both contain their full mean-rate/mean-weight fraction inside nary/e; only terminal punctuation stays outside.','All automatic m:d delimiter objects and all5 formula-layout tables are absent. Literal parentheses are ASCII normal-math text explicitly using Times New Roman.','All66main/878supplement scientific tablecells, author metadata/abstract, Results/declarations/references/captions and embedded image bytes are preserved. S6PDF bytes are unchanged.','No inference, resampling or statistical experiment was run. This is structural/content verification and this environment PDF checking, not a direct WPS or MicrosoftWord runtime test. Full visual review is separately documented.']}
if __name__=='__main__':
 report=run();p=B/'qa/independent_math_qa.json';p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 md=['# v13 independent scientific-content and native-math QA','','Status: PASS. '+str(report['checks_passed'])+' checks;5 native formula paragraphs; no scientific data or text change.','','| Document | Equation | Verdict |','|---|---|---|']
 for x in report['equation_checks']:md.append(f"| {x['document']} | ({x['label']}) | PASS |")
 md+=['',*report['notes']];(B/'qa/independent_math_qa.md').write_text('\n'.join(md)+'\n')
 print(report['checks_passed'],'checks PASS;5formulas;reportSHA',sha(p))
