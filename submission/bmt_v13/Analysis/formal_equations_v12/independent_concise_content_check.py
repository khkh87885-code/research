"""Independent scientific-content QA for five concise native display equations."""
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile
from datetime import datetime,timezone
import hashlib,json,re,subprocess
from lxml import etree
from docx import Document
import fitz
B=Path('/workspace/bmt_v12');BASE=Path('/workspace/research_source/submission/bmt_v9');PREV=Path('/workspace/research_source/submission/bmt_v11')
NS={'m':'http://schemas.openxmlformats.org/officeDocument/2006/math','w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def root(path):
 with ZipFile(path)as z:return etree.fromstring(z.read('word/document.xml'))
def semantic(e):
 tag=etree.QName(e).localname
 if tag=='r'and etree.QName(e).namespace==NS['m']:return ('TEXT',''.join(e.xpath('.//m:t/text()',namespaces=NS)))
 cc=[]
 children=[x for x in e if etree.QName(x).localname not in ['rPr','ctrlPr','grow']]
 if tag=='dPr':children=sorted(children,key=lambda x:x.tag)
 for child in children:
  value=semantic(child)
  if cc and cc[-1][0]=='TEXT'and value[0]=='TEXT':cc[-1]=('TEXT',cc[-1][1]+value[1])
  else:cc.append(value)
 return(e.tag,tuple(sorted(e.attrib.items())),e.text or '',tuple(cc))
def eq_tables(doc):
 out=[]
 for t in doc.tables:
  c=t._tbl.tblPr.find('w:tblCaption',NS)
  if c is not None and c.get('{'+NS['w']+'}val','').startswith('Equation layout ('):out.append(t)
 return out

def data_tables(doc):
 layouts={id(t._tbl)for t in eq_tables(doc)}
 return[t for t in doc.tables if id(t._tbl)not in layouts]
def data_snapshot(doc):return[[[c.text for c in row.cells]for row in t.rows]for t in data_tables(doc)]
def pandoc_paragraphs(markdown):
 with TemporaryDirectory(prefix='bmt_v12_qa_')as td:
  p=Path(td)/'a.md';q=p.with_suffix('.docx');p.write_text(markdown)
  r=subprocess.run(['pandoc',str(p),'-o',str(q)],capture_output=True,text=True)
  assert not r.returncode and not r.stderr.strip(),r.stderr
  return [etree.fromstring(etree.tostring(x))for x in root(q).findall('./w:body/w:p',NS)]
def canonical_tex(tex):
 for c in ['E','I']:tex=tex.replace('_{'+c+',s}',r'_{\mathrm{'+c+'},s}')
 return tex

def run():
 checks=[];equations=[];docs={};plan=json.loads((B/'evidence/formula_scope_plan.json').read_text())
 def ck(name,ok,detail=''):
  checks.append({'name':name,'pass':bool(ok),'detail':detail});assert ok,(name,detail)
 configs=[('main','BMT_main_manuscript_v12.docx','BMT_main_manuscript_v9.docx','BMT_main_manuscript_v11.docx',plan['main_replacements'],['1','2','3'],3,66),('supplement','BMT_supplementary_material_v8.docx','BMT_supplementary_material_v5.docx','BMT_supplementary_material_v7.docx',plan['supplement_replacements'],['S1','S2'],19,878)]
 for group,filename,old,prev,replacements,labels,nt,nc in configs:
  d=Document(B/'outputs'/filename);source=Document(BASE/old);latest=Document(PREV/prev);rr=root(B/'outputs'/filename);layouts=eq_tables(d)
  ck(group+' numbered equation labels',[t.cell(0,2).text for t in layouts]==['('+x+')'for x in labels])
  ck(group+' true display math count',len(rr.findall('.//m:oMathPara',NS))==len(labels))
  ck(group+' no aligned or cases matrix',not rr.findall('.//m:m',NS))
  ck(group+' scientific table count',len(data_tables(d))==nt)
  ck(group+' scientific data cell count',sum(len(row.cells)for t in data_tables(d)for row in t.rows)==nc)
  ck(group+' scientific cells match latest',data_snapshot(d)==data_snapshot(latest))
  ck(group+' all native tables correctly classified',len(d.tables)==nt+len(labels))
  eqplan=[b for rep in replacements for b in rep['blocks']if b['type']=='equation']
  for t,b in zip(layouts,eqplan):
   label=b['label'];ck(group+' ('+label+') layout only 1x3',len(t.rows)==1 and len(t.columns)==3)
   found=t.cell(0,1)._tc.findall('.//m:oMathPara/m:oMath',NS)
   ck(group+' ('+label+') single native display object',len(found)==1)
   expected=pandoc_paragraphs('$$'+canonical_tex(b['latex'])+'$$')[0].find('.//m:oMath',NS)
   ck(group+' ('+label+') mathematical structure matches audited definition',semantic(found[0])==semantic(expected))
   # Literal cohort/method labels must be upright, while variables retain italic semantics.
   literals=[x for x in found[0].findall('.//m:sub//m:r',NS)if ''.join(x.xpath('./m:t/text()',namespaces=NS))in ['A','B','E','I']]
   ck(group+' ('+label+') descriptive labels upright',all(x.find('m:rPr/m:nor',NS)is not None or(x.find('m:rPr/m:sty',NS)is not None and x.find('m:rPr/m:sty',NS).get('{'+NS['m']+'}val')=='p')for x in literals))
   equations.append({'document':group,'label':label,'pass':True,'latex':canonical_tex(b['latex']),'native_math_sha256':hashlib.sha256(etree.tostring(found[0])).hexdigest()})
  # Reconstruct the paragraph-only content from the unchanged v9 prose baseline
  # and the authorized concise replacements, independently of the build code.
  by_anchor={rep['anchor_exact']:rep for rep in replacements};expected=[]
  for p in source.paragraphs:
   if p.text not in by_anchor:expected.append(p.text)
   else:
    for block in by_anchor[p.text]['blocks']:
     if block['type']=='paragraph':
      text=re.sub(r'(?<=\d)[ \u00a0\u202f]*%', '\u202f%',block['text'])
      pp=pandoc_paragraphs(text);assert len(pp)==1
      # Same plain-text view as python-docx (native math is separately checked).
      from docx.text.paragraph import Paragraph
      from docx.oxml import parse_xml
      expected.append(Paragraph(parse_xml(etree.tostring(pp[0])),d._body).text)
  if group=='supplement':expected=[x.replace('BMT_supplementary_Figure_S6_v5.pdf','BMT_supplementary_Figure_S6_v8.pdf')for x in expected]
  actual=[p.text for p in d.paragraphs]
  ck(group+' complete prose follows authorized concise plan',expected==actual)
  prose='\n'.join(actual)
  stale=re.findall(r'\bEqs?\.\s*\((S?\d+)\)',prose)
  ck(group+' only retained equation references survive',all(x in ['1','2','3','S1','S2']for x in stale),str(stale))
  ck(group+' former mathematical appendix absent','Supplementary mathematical methods'not in prose and'Proportion and difference intervals'not in prose)
  if group=='main':
   a=[p.text for p in latest.paragraphs]
   ck('main abstract and author metadata unchanged',actual[:14]==a[:14])
   ck('main Results through references declarations captions unchanged',actual[actual.index('Results'):]==a[a.index('Results'):])
  with ZipFile(B/'outputs'/filename)as z:ck(group+' no equation raster media',len([n for n in z.namelist()if n.startswith('word/media/')])==(0 if group=='main'else 5))
  docs[filename]={'sha256':sha(B/'outputs'/filename),'bytes':(B/'outputs'/filename).stat().st_size,'data_tables':nt,'scientific_cells':nc,'display_equations':len(labels),'layout_tables':len(layouts)}
 # Crucial word-level rules are inherited exactly, not implied by deleted displays.
 old=Document(BASE/'BMT_main_manuscript_v9.docx');new=Document(B/'outputs/BMT_main_manuscript_v12.docx');text='\n'.join(p.text for p in new.paragraphs)
 for index,name in [(25,'frozen model and input handling'),(31,'calibration zero option tied groups >= nearest target and fewer tie'),(34,'H1 H2 H3 directions and nominal Newcombe'),(35,'Dice sensitivity top50 and original string-ID tie'),(37,'diagnostic strata and Wilson intervals'),(39,'eight budgets nearest integer and half tie'),(40,'three bootstrap routes paired records repeats top50 draw-order nominal'),(43,'historical versus six-case CPU environment scope')]:
  ck('main exact rule paragraph '+name,old.paragraphs[index].text in text)
 ck('Dice positive-denominator domain explicit','with at least one foreground pixel between them' in text)
 ck('Dice empty-empty convention preserved','Dice is defined as one when both predicted masks are empty' in text)
 ck('empty prediction vs nonempty reference gives zero','An empty initial prediction against the nonempty reference has Dice zero' in text)
 ck('strict low-quality reference cutoff preserved','reference Dice below 0.70' in text)
 ck('A raw quality-head input preserved','raw predicted intersection over union' in text and'SAM quality head for the initial mask' in text)
 ck('four directions and clipped coincidence retained','All four directions were retained when clipping produced coincident boxes.'in text)
 ck('all zero-denominator rates remain undefined','Rates with a zero denominator were left undefined.'in text)
 supp=Document(B/'outputs/BMT_supplementary_material_v8.docx');st='\n'.join(p.text for p in supp.paragraphs)
 for key in ['Detection weights are the diagnostic proportions among low-quality cases','review weights are the diagnostic proportions among all patients']:
  # New wording is equally precise but differs from this old single paragraph.
  pass
 ck('Kitagawa detection weights use low-quality patients','weights are diagnostic shares among low-quality patients' in st)
 ck('Kitagawa review weights use all scored patients','weights are diagnostic shares among all scored patients' in st)
 ck('Kitagawa identity conditioned on defined stratum rates','sum to the external-minus-internal overall rate difference when the stratum rates are defined' in st)
 ck('overall rates aggregate counts retained','Overall rates are calculated directly from aggregate numerators and denominators.'in st)
 original=Document(BASE/'BMT_supplementary_material_v5.docx')
 for index,name in [(46,'paired Newcombe positive-association correction'),(50,'internal exact half K=425'),(51,'equal-K review difference zero by design'),(64,'linear finite-value bootstrap quantiles'),(65,'three routes paired sampling'),(67,'duplicate draws deterministic draw index and NA'),(68,'R1 zero A-only empirical support'),(69,'bootstrap not replace Newcombe or superiority probability'),(78,'component finite percentile procedure'),(79,'4999 vs5000 undefined stratum'),(80,'noncausal and no percent-explained'),(89,'fixed CPU replay decisions'),(90,'48 numeric fields and cross-environment differences')]:
  ck('supplement exact rule paragraph '+name,original.paragraphs[index].text in st)
 for file in sorted((B/'outputs/Figures').glob('*')):
  if file.is_file():ck('figure bytes unchanged '+file.name,sha(file)==sha(PREV/'Figures'/file.name))
 ck('S6 file bytes unchanged',sha(B/'outputs/BMT_supplementary_Figure_S6_v8.pdf')==sha(PREV/'BMT_supplementary_Figure_S6_v7.pdf'))
 for filename in ['BMT_main_manuscript_v12_preview.pdf','BMT_main_manuscript_v12_illustrated_preview.pdf','BMT_supplementary_material_v8_preview.pdf','BMT_supplementary_Figure_S6_v8.pdf']:
  f=B/'outputs'/filename;pdf=fitz.open(f);pt='\n'.join(p.get_text()for p in pdf)
  ck(filename+' no replacement or math parser error glyph',not any(x in pt for x in ['¿','\ufffd']))
  ck(filename+' no red parser error spans',not any(s['color']==0xff0000 for p in pdf for b in p.get_text('dict')['blocks']if'lines'in b for l in b['lines']for s in l['spans']))
  docs[filename]={'sha256':sha(f),'bytes':f.stat().st_size,'pages':len(pdf)}
 return {'checks':checks,'equation_checks':equations,'documents':docs}
if __name__=='__main__':
 result=run();(B/'evidence/native_concise_content_check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(len(result['checks']),'checks pass;',len(result['equation_checks']),'display formulas')
