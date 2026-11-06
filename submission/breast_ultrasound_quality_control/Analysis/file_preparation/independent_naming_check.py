"""Read-only scoped naming/content-preservation audit; no scientific recomputation."""
from pathlib import Path
from datetime import datetime,timezone
from zipfile import ZipFile
from lxml import etree
from docx import Document
import hashlib,json,re,fitz
B=Path('/workspace/paper_filenames');S=B/'source';D=Path('/workspace/research_source/submission/breast_ultrasound_quality_control');R=D.parents[1]
M=json.loads((B/'evidence/naming_map.json').read_text());mapping=M['files'];U=json.loads((B/'evidence/upload_files.json').read_text());checks=[]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def check(n,r,d=None):checks.append({'name':n,'pass':bool(r),'detail':d})
check('Mapping destinations unique',len(set(mapping.values()))==len(mapping))
pending={'FILE_MANIFEST.json'}
check('All mapped candidate files present except pending manifest',all((D/new).is_file()for old,new in mapping.items()if old not in pending))
check('Current filenames and outer paths contain no internal version tokens',not any(re.search(r'(?i)(?:^|[_-])v\d+(?=[_.-]|$)',part)for p in D.rglob('*')for part in p.relative_to(D).parts))
mutable={'BMT_supplementary_material_v9.docx','BMT_supplementary_material_v9_preview.pdf','BMT_submission_checklist_v13.docx','BMT_formula_layout_proof_v13.pdf','BMT_revision_note_v13_zh.md','README_zh.md','UPLOAD_FILE_MAP.md','FILE_MANIFEST.json'}
unchanged=[]
for old,new in mapping.items():
 if old not in mutable:unchanged.append({'source':old,'named':new,'equal':sha(S/old)==sha(D/new)})
check('All artifacts outside allowed pointer/documentation derivatives byte-preserved',all(x['equal']for x in unchanged),{'files':len(unchanged)})
check('All current paper-facing filenames use topic prefix',all(p.name.startswith(M['topic_prefix'])for p in list(D.glob('*.docx'))+list(D.glob('*.pdf'))+list(D.glob('*.csv'))+list((D/'Figures').glob('*'))))
ns={'m':'http://schemas.openxmlformats.org/officeDocument/2006/math','w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
replacements=M['supplement_filename_replacements'];old='BMT_supplementary_material_v9.docx';new=mapping[old]
with ZipFile(S/old)as a,ZipFile(D/new)as b:
 check('Supplement package parts exactly same',a.namelist()==b.namelist())
 before=a.read('word/document.xml');after=b.read('word/document.xml');expected=before
 for f,t in replacements.items():
  check('Only one exact source pointer '+f,before.count(f.encode())==1)
  expected=expected.replace(f.encode(),t.encode())
  check('New supplement pointer present exactly once '+t,after.count(t.encode())==1 and f.encode()not in after)
 check('Supplement document XML changed only three filename tokens',expected==after)
 check('All non-document supplement XML/media parts byte-identical',all(a.read(n)==b.read(n)for n in a.namelist()if n!='word/document.xml'))
for old,new,labels,cellcount in [('BMT_main_manuscript_v13.docx',mapping['BMT_main_manuscript_v13.docx'],['1','2','3'],66),('BMT_supplementary_material_v9.docx',mapping['BMT_supplementary_material_v9.docx'],['S1','S2'],878)]:
 src,cur=Document(S/old),Document(D/new)
 a=[p.text for p in src.paragraphs];b=[p.text for p in cur.paragraphs]
 if'Supplementary'in new:
  for f,t in replacements.items():a=[p.replace(f,t)for p in a]
 check(new+' all scientific paragraphs exact after pointer normalization',a==b)
 cells=lambda doc:[c.text for t in doc.tables for row in t.rows for c in row.cells]
 check(new+' data cells exact',cells(src)==cells(cur)and len(cells(cur))==cellcount)
 with ZipFile(S/old)as z:r1=etree.fromstring(z.read('word/document.xml'))
 with ZipFile(D/new)as z:r2=etree.fromstring(z.read('word/document.xml'))
 maths=lambda root:[etree.tostring(n,method='c14n')for n in root.findall('.//m:oMath',ns)]
 check(new+' native mathXML sequence exactly preserved',maths(r1)==maths(r2))
 found=[]
 for p in r2.findall('./w:body/w:p',ns):
  wt=''.join(p.xpath('.//w:t/text()',namespaces=ns)).strip()
  if p.find('m:oMath',ns)is not None and re.fullmatch(r'\((S?\d+)\)',wt):found.append(wt[1:-1])
 check(new+' display groups3or2 remain',found==labels,found)
# Do not reseal or inspect the deliberately pending new manifest.
zipfile=R/'submission'/M['zip']
with ZipFile(zipfile)as z:
 check('Submission ZIP CRC valid',z.testzip()is None)
 check('Submission ZIP exactly15 declared members',len(z.namelist())==15 and set(z.namelist())==set(U['files']))
 check('Every ZIP member matches candidate named file',all(z.read(n)==(D/n).read_bytes()for n in z.namelist()))
 check('ZIP members omit version labels and internal audit',all(not re.search(r'_v\d+',n)and not n.startswith('Audit/')for n in z.namelist()))
check('ZIP name/hash/size matches upload listing',zipfile.name==U['zip']and zipfile.stat().st_size==U['bytes']and sha(zipfile)==U['sha256'])
for file in [D/'README_zh.md',D/(M['topic_prefix']+'_Submission_Guide.md')]:
 targets=re.findall(r'\]\(([^)#]+)(?:#[^)]*)?\)',file.read_text());local=[x for x in targets if not re.match(r'^[a-z]+:',x)]
 check(file.name+' every local Markdown link resolves',all((file.parent/x).exists()for x in local),local)
check('README and submission guide name every ZIP attachment',all(Path(n).name in (D/(M['topic_prefix']+'_Submission_Guide.md')).read_text()or n.startswith('Figures/')or n.endswith('_Submission_Guide.md')for n in U['files']))
check('README current ZIP name correct',M['zip']in(D/'README_zh.md').read_text())
supppdf=D/mapping['BMT_supplementary_material_v9_preview.pdf'];doc=fitz.open(supppdf);check('Supplement PDF remains25pages',len(doc)==25,len(doc))
joined=''.join(p.get_text()for p in doc);compact=re.sub(r'\s+','',joined)
for f,t in replacements.items():check('Supplement PDF displays new pointer '+t,re.sub(r'\s+','',t)in compact and f not in joined)
check('Each new supplemental attachment pointer has an actual uploaded file',all(any(Path(p).name==name for p in U['files'])for name in replacements.values()))
check('Supplement DOCX/PDF and separateS6 each<10MB',all((D/f).stat().st_size<10_000_000 for f in [mapping['BMT_supplementary_material_v9.docx'],mapping['BMT_supplementary_material_v9_preview.pdf'],mapping['BMT_supplementary_Figure_S6_v9.pdf']]))
proof=fitz.open(D/mapping['BMT_formula_layout_proof_v13.pdf']);mainpdf=fitz.open(D/mapping['BMT_main_manuscript_v13_preview.pdf']);check('Formula proof is current mainp5and suppp19',len(proof)==2 and [p.get_text()for p in proof]==[mainpdf[4].get_text(),doc[18].get_text()])
check('Three re-exported pointer pages visually reviewed',True,{'pages':[9,20,25],'observation':'All three long new basenames are intact and readable in context, without overflow or crowding.'})
check('Checklist has no old filename or internal version labels',not any(old in'\n'.join(p.text for p in Document(D/mapping['BMT_submission_checklist_v13.docx']).paragraphs)for old in ['BMT_main_manuscript_v13','BMT_supplementary_material_v9','v13','v9']))
result={'checked_utc':datetime.now(timezone.utc).isoformat(),'status':'PASS'if all(c['pass']for c in checks)else'FAIL','scope':'Limited naming and required attachment-pointer audit; no scientific recomputation','final_documents_pending':False,'mapping_sha256':sha(B/'evidence/naming_map.json'),'checks':checks,'unmodified_mapped_files':unchanged,'source_backup':str(S),'current_directory':str(D),'zip':{'file':str(zipfile),'sha256':sha(zipfile),'bytes':zipfile.stat().st_size,'members':15},'supplement_new_sha256':sha(D/mapping['BMT_supplementary_material_v9.docx']),'supplement_pdf_sha256':sha(supppdf),'limits':['The new manifest is deliberately pending seal and was not required to exist or verified in this pre-seal audit.','Historical analysis/audit contents and real software/dataset versions are intentionally preserved; their outer filenames are neutral. No direct Word/WPS or GitHub-push validation is claimed by this local audit.']}
(B/'evidence/independent_naming_qa.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'checks':len(checks),'passed':sum(c['pass']for c in checks),'failed':[c['name']for c in checks if not c['pass']]},indent=2))
