"""Independent v11 content proof: row-aligned native equations vs audited math."""
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile
import hashlib,json,re,subprocess
from lxml import etree
from docx import Document
import fitz
B=Path('/workspace/bmt_v11');OLD=Path('/workspace/bmt_v10/outputs');NS={'m':'http://schemas.openxmlformats.org/officeDocument/2006/math','w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def upright(tex):
    # Preserve already grouped literal labels, then make each named count and
    # hypothesis label one text token even inside a fraction's braces.
    tex=re.sub(r'\\mathrm\{([A-Za-z0-9]+)\}',lambda m:r'\text{'+m.group(1)+'}',tex)
    protected=[]
    def save(m):
        protected.append(m.group());return '@@LITERAL'+str(len(protected)-1)+'@@'
    tex=re.sub(r'\\text\{[^{}]*\}',save,tex)
    tex=re.sub(r'(?<![A-Za-z])(TP|FP|TN|FN|H[123])(?![A-Za-z])',lambda m:r'\text{'+m.group(1)+'}',tex)
    for i,value in enumerate(protected):tex=tex.replace('@@LITERAL'+str(i)+'@@',value)
    return re.sub(r'\\quad\s*\\text\{or\}\\quad\s*',lambda m:r'\lor ',tex)

def split_rows(tex):
    tex=upright(tex).strip()
    if not tex.startswith(r'\begin{aligned}'):return [[tex]]
    assert tex.endswith(r'\end{aligned}')
    content=tex[len(r'\begin{aligned}'):-len(r'\end{aligned}')]
    rr=[]
    for row in re.split(r'\\\\',content):
        assert row.count('&')==1,row
        lhs,rhs=row.split('&');rr.append([lhs.strip(),rhs.strip()])
    return rr

def semantic(e):
    tag=etree.QName(e).localname;namespace=etree.QName(e).namespace
    if tag=='r'and namespace==NS['m']:
        return ('TEXT',''.join(e.xpath('.//m:t/text()',namespaces=NS)))
    # Font, plain/italic/normal-text flags, matrix appearance and limit placement
    # are authorized presentation changes; arithmetic scope remains structural.
    children=[x for x in e if etree.QName(x).localname not in ['rPr','ctrlPr','limLoc']]
    if tag in ['dPr','mcPr']:children=sorted(children,key=lambda x:x.tag)
    cc=[]
    for c in children:
        z=semantic(c)
        if cc and cc[-1][0]=='TEXT'and z[0]=='TEXT':cc[-1]=('TEXT',cc[-1][1]+z[1])
        else:cc.append(z)
    return (e.tag,tuple(sorted(e.attrib.items())),e.text or '',tuple(cc))

def read_root(path):
    with ZipFile(path)as z:return etree.fromstring(z.read('word/document.xml'))

def actual_groups(root):
    groups=[];current=[]
    for p in root.findall('./w:body/w:p',NS):
        math=p.findall('./m:oMath',NS)
        wt=''.join(p.xpath('.//w:t/text()',namespaces=NS)).strip()
        label=re.fullmatch(r'\((S?\d+)\)',wt)
        if math and (not wt or label):
            current.append(math)
            if label:groups.append((label.group(1),current));current=[]
        else:assert not current,('unterminated math group',wt)
    assert not current
    return groups

def expected_math(fragments):
    with TemporaryDirectory(prefix='bmt_v11_independent_')as td:
        p=Path(td)/'expected.md';q=p.with_suffix('.docx')
        p.write_text('\n\n'.join('$$'+x+'$$'for x in fragments))
        r=subprocess.run(['pandoc',str(p),'-o',str(q)],capture_output=True,text=True)
        assert r.returncode==0 and not r.stderr.strip(),r.stderr
        return read_root(q).findall('.//m:oMath',NS)

def snapshot(d):return [[[c.text for c in row.cells]for row in t.rows]for t in d.tables]

def run():
    checks=[];documents={};records=[]
    def ck(name,ok,detail=''):
        checks.append({'name':name,'pass':bool(ok),'detail':detail});assert ok,(name,detail)
    configs=[('main','effective_main_equation_plan.json','BMT_main_manuscript_v11.docx','BMT_main_manuscript_v10.docx',14),('supplement','effective_supplement_equation_plan.json','BMT_supplementary_material_v7.docx','BMT_supplementary_material_v6.docx',12)]
    for group,planfile,new,old,count in configs:
        plan=json.loads((B/'evidence'/planfile).read_text());prior=json.loads((Path('/workspace/bmt_v10/evidence')/planfile).read_text())
        allblocks=lambda p:[b for r in p['replacements']for b in r['blocks']]if 'replacements'in p else p['blocks']
        blocks=allblocks(plan);ck(group+' audited v10 plan definitions exact',blocks==allblocks(prior))
        eq=[b for b in blocks if b['type']=='equation'];root=read_root(B/'outputs'/new);groups=actual_groups(root)
        ck(group+' numbered group labels',[n for n,rr in groups]==[b['label']for b in eq])
        ck(group+' display group count',len(groups)==count)
        expectedrows=[split_rows(b['latex'])for b in eq]
        fragments=[x for rr in expectedrows for row in rr for x in row];expected=iter(expected_math(fragments))
        for b,(label,actual),wanted in zip(eq,groups,expectedrows):
            ck(group+' '+label+' row count',len(actual)==len(wanted))
            for j,(row,frags)in enumerate(zip(actual,wanted),1):
                ck(group+' '+label+' row'+str(j)+' native fragment count',len(row)==len(frags))
                for k,(node,tex)in enumerate(zip(row,frags),1):
                    exp=next(expected)
                    ck(group+' '+label+f' row{j} part{k} arithmetic structure exact',semantic(node)==semantic(exp))
            records.append({'document':group,'label':label,'rows':len(actual),'native_fragments':sum(len(x)for x in actual),'pass':True,'latex_definition':b['latex']})
        # Compare inline mathematical objects as well. Side versus under/over
        # sum-limit placement is a typography change, not an index change.
        paragraphs=[]
        for block in blocks:
            if block['type']=='paragraph':
                text=block['text'].replace(r'$s\in\{\mathrm{benign},\mathrm{malignant}\}$',r'$s$ (benign or malignant)')
                text=re.sub(r'\$([^$]+)\$',lambda m:'$'+upright(m.group(1))+'$',text)
                paragraphs.append(text)
        with TemporaryDirectory(prefix='bmt_v11_inline_')as td:
            pp=Path(td)/'prose.md';dx=pp.with_suffix('.docx');pp.write_text('\n\n'.join(paragraphs))
            result=subprocess.run(['pandoc',str(pp),'-o',str(dx)],capture_output=True,text=True)
            assert not result.returncode and not result.stderr.strip(),result.stderr
            expected_inline=read_root(dx).findall('.//m:oMath',NS)
        actual_inline=[]
        for p in root.findall('./w:body/w:p',NS):
            ms=p.findall('./m:oMath',NS);wt=''.join(p.xpath('.//w:t/text()',namespaces=NS)).strip()
            if ms and wt and not re.fullmatch(r'\((S?\d+)\)',wt):actual_inline.extend(ms)
        ck(group+' inline math object count unchanged',len(actual_inline)==len(expected_inline),f'actual={len(actual_inline)}, expected={len(expected_inline)}')
        ck(group+' all inline arithmetic structures exact',len(actual_inline)==len(expected_inline)and all(semantic(x)==semantic(y)for x,y in zip(actual_inline,expected_inline)))
        d=Document(B/'outputs'/new);a=Document(OLD/old)
        ck(group+' all table cells exact',snapshot(d)==snapshot(a))
        ck(group+' table count unchanged',len(d.tables)==len(a.tables))
        if group=='main':
            aa=[p.text for p in a.paragraphs];bb=[p.text for p in d.paragraphs]
            ck('main abstract unchanged',aa[8:14]==bb[8:14])
            ck('main Results through captions unchanged',aa[aa.index('Results'):]==bb[bb.index('Results'):])
        else:
            # Original scientific supplement, after the newly added math, is untouched.
            aa=[p.text for p in a.paragraphs];bb=[p.text for p in d.paragraphs]
            start=next(i for i,t in enumerate(aa)if t.startswith('Table S1.'))
            j=next(i for i,t in enumerate(bb)if t.startswith('Table S1.'))
            expected_tail=[t.replace('BMT_supplementary_Figure_S6_v6.pdf','BMT_supplementary_Figure_S6_v7.pdf')for t in aa[start:]]
            ck('supplement TableS1 through end unchanged except file pointer',expected_tail==bb[j:])
        docsraw=ZipFile(B/'outputs'/new)
        ck(group+' formula images absent and old figure embeds unchanged',len([x for x in docsraw.namelist()if x.startswith('word/media/')])==(0 if group=='main' else 5))
        documents[new]={'sha256':sha(B/'outputs'/new),'bytes':(B/'outputs'/new).stat().st_size,'display_equation_groups':len(groups)}
    for n in ['BMT_main_manuscript_v11_preview.pdf','BMT_main_manuscript_v11_illustrated_preview.pdf','BMT_supplementary_material_v7_preview.pdf','BMT_supplementary_Figure_S6_v7.pdf']:
        f=B/'outputs'/n;pdf=fitz.open(f);text='\n'.join(x.get_text()for x in pdf)
        ck(n+' no math parser error glyph',not any(c in text for c in ['¿','\ufffd']))
        ck(n+' no red parser text',not any(s['color']==0xff0000 for p in pdf for b in p.get_text('dict')['blocks']if'lines'in b for l in b['lines']for s in l['spans']))
        documents[n]={'sha256':sha(f),'bytes':f.stat().st_size,'pages':len(pdf)}
    ck('S6 image publication PDF unchanged',sha(B/'outputs/BMT_supplementary_Figure_S6_v7.pdf')==sha(OLD/'BMT_supplementary_Figure_S6_v6.pdf'))
    return {'checks':checks,'documents':documents,'equation_group_checks':records}
if __name__=='__main__':
    d=run();(B/'evidence/native_content_check_result.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');print(len(d['checks']),'content checks pass,',len(d['equation_group_checks']),'groups')
