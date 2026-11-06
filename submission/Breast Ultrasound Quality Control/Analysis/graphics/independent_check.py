#!/usr/bin/env python3
"""Independent read-only checks of final v9 deliverables and their data."""
import csv, hashlib, json, re, math
from collections import Counter
from pathlib import Path
import fitz
import numpy as np
from PIL import Image
from docx import Document

B=Path('/workspace/bmt_v9')
R=Path('/workspace/research_source')
E=B/'evidence'
checks=[]
def check(name, ok, detail=None):
    checks.append({'name':name,'pass':bool(ok),'detail':detail})
def load(p):return json.loads(Path(p).read_text())
def rows(p):
    with Path(p).open(encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def same(a,b):return math.isclose(float(a),float(b),rel_tol=0,abs_tol=1e-11)

core=load(E/'core_statistics_figures.json')['figure_primitive_values']
primary=load(R/'reproducibility/reference/primary.json')
supp=load(R/'reproducibility/reference/supplementary.json')
records=rows(R/'reproducibility/records/validation_cases.csv')
development=rows(R/'reproducibility/records/development_cases.csv')
check('Figure1 cohort counts from patient records',len(development)==213 and sum(int(r['low_quality']) for r in development)==24 and all(sum(r['split']==s for r in records)==n and sum(int(r['low_quality']) for r in records if r['split']==s)==f for s,n,f in [('internal_holdout',851,93),('external_test',252,16)]))
example=np.load(R/'figures/source/example_case.npz')
exdice=2*np.count_nonzero(example['masks'][0]&example['reference'])/(np.count_nonzero(example['masks'][0])+np.count_nonzero(example['reference']))
exrisk=1-np.mean([2*np.count_nonzero(example['masks'][0]&a)/(np.count_nonzero(example['masks'][0])+np.count_nonzero(a)) for a in example['masks'][1:]])
exrow=[r for r in records if r['image_id']=='case001'][0]
check('Figure2 actual archived case001 mask Dice and consistency match original records',same(exdice,exrow['dice_vs_reference']) and same(exrisk,exrow['risk_B']))
points=0
for curve in core['Figure_4']['rank_curves']:
    rs=[r for r in records if r['split']==curve['split']]
    rs.sort(key=lambda r:(-float(r['risk_'+curve['method']]),r['patient_id']))
    counts=[0]
    for r in rs: counts.append(counts[-1]+int(r['low_quality']))
    check(f"{curve['split']} {curve['method']} complete patient-ranked curve",counts==curve['y_detected_count'] and list(range(len(rs)+1))==curve['x_review_count'])
    points+=len(counts)
for entry in core['Figure_3']:
    orig=primary['contrasts'][entry['id']]
    check(entry['id']+' exact original point/CI',same(entry['difference_pp'],orig['difference_pp']) and entry['ci95_pp']==orig['ci95_pp'])
for marker in core['Figure_4']['policy_markers']:
    rs=[r for r in records if r['split']==marker['split']]
    if marker['policy']=='top50':
        rs=sorted(rs,key=lambda r:(-float(r['risk_'+marker['method']]),r['patient_id']))[:50]
    else:rs=[r for r in rs if int(r['alert_'+marker['method']])]
    check('policy marker '+str(marker),len(rs)==marker['R'] and sum(int(r['low_quality']) for r in rs)==marker['TP'])
ext=[r for r in records if r['split']=='external_test']
for table in core['Figure_S2']:
    if table['policy']=='top50':
        selected={m:{r['patient_id'] for r in sorted(ext,key=lambda r:(-float(r['risk_'+m]),r['patient_id']))[:50]} for m in ['A','B']}
    else:selected={m:{r['patient_id'] for r in ext if int(r['alert_'+m])} for m in ['A','B']}
    groups={k:[] for k in ['both','A_only','B_only','neither']}
    for r in ext:
        if not int(r['low_quality']):continue
        a=r['patient_id'] in selected['A'];b=r['patient_id'] in selected['B']
        key='both' if a and b else 'A_only' if a else 'B_only' if b else 'neither'
        groups[key].append(r['patient_id'])
    check('paired outcome table '+table['policy'],all(set(groups[k])==set(table['real_patient_id_membership'][k]) and len(groups[k])==table['counts'][k] for k in groups))

extended=load(E/'extended_statistics_figures.json')['figures']
source=R/'experiments/cloud_validation_v1/results'
perf=rows(source/'budget_transfer/performance.csv')
contrasts=rows(source/'budget_transfer/paired_contrasts.csv')
for series in extended['Figure_S3']['plot_series']:
    selected=[r for r in perf if r['split']==series['split'] and r['method']==series['method'] and r['mode']==series.get('mode','development_calibrated_threshold')]
    selected.sort(key=lambda r:float(r['target_budget']))
    check('budget plot '+str({k:v for k,v in series.items() if k not in ['budget_percent','values_percent']}),all(same(float(r['target_budget'])*100,x) and same(float(r[series['source_column']])*100,y) for r,x,y in zip(selected,series['budget_percent'],series['values_percent'])) and len(selected)==len(series['values_percent']))
for interval in extended['Figure_S3']['paired_intervals']:
    found=[r for r in contrasts if r['split']=='external_test' and r['mode']==interval['mode'] and same(100*float(r['target_budget']),interval['budget_percent'])]
    check('budget paired CI '+str(interval['budget_percent'])+' '+interval['mode'],len(found)==1 and all(same(found[0][k],interval[v]) for k,v in [('detection_difference_pp','estimate_pp'),('detection_ci95_low_pp','ci95_low_pp'),('detection_ci95_high_pp','ci95_high_pp')]))
bs=load(source/'bootstrap_stability/summary.json')
routes=dict(zip(['R1','R2','R3'],bs['routes']))
for interval in extended['Figure_S4']['bootstrap_intervals']:
    o=bs['routes'][routes[interval['route']]]['endpoints_pp'][interval['endpoint']]
    check('bootstrap interval '+interval['route']+' '+interval['endpoint'],same(interval['median_pp'],o['median']) and interval['percentile95_pp']==o['percentile_95'] and interval['valid_replicates']==o['valid_replicates'])
for freq in extended['Figure_S4']['joint_frequencies']:
    p=bs['routes'][routes[freq['route']]]['joint_direction_patterns']
    if freq['category']=='Original strict':count=p['original_direction_reversal']['count']
    elif freq['category']=='Opposite strict':count=p['opposite_direction_reversal']['count']
    elif freq['category']=='Any zero':count=p['any_difference_tie']['count']
    else:count=p['sign_matrix']['positive']['positive']['count']+p['sign_matrix']['negative']['negative']['count']
    check('bootstrap sign frequency '+freq['route']+' '+freq['category'],count==freq['count'] and same(100*count/p['valid_replicates'],freq['frequency_percent']))
mix=load(source/'case_mix_decomposition.json')
for term in extended['Figure_S5']['term_intervals']:
    o=mix['results'][term['method']+'.'+term['outcome']]['statistics'][term['term']]
    check('case mix '+term['method']+' '+term['outcome']+' '+term['term'],same(100*o['estimate'],term['estimate_pp']) and all(same(100*a,b) for a,b in zip(o['percentile_ci95'],term['percentile95_pp'])) and o['valid_replicates']==term['valid_replicates'])

figmeta={}
for p in sorted((B/'outputs/Figures').glob('*.png')):
    im=Image.open(p);dpi=im.info.get('dpi',(0,0))
    d=fitz.open(p.with_suffix('.pdf'));page=d[0]
    spans=[s for block in page.get_text('dict')['blocks'] if 'lines' in block for line in block['lines'] for s in line['spans'] if s['text'].strip()]
    minimum=min(s['size'] for s in spans)
    inside=all(s['bbox'][0]>=-.1 and s['bbox'][1]>=-.1 and s['bbox'][2]<=page.rect.width+.1 and s['bbox'][3]<=page.rect.height+.1 for s in spans)
    figmeta[p.stem]={'pixels':list(im.size),'dpi':list(dpi),'minimum_font_pt':minimum,'page_inches':[page.rect.width/72,page.rect.height/72],'text_inside_canvas':inside,'png_sha256':sha(p),'pdf_sha256':sha(p.with_suffix('.pdf'))}
    check(p.stem+' 600 dpi at intended size',min(dpi)>599 and same(im.size[0]/600,6.89))
    check(p.stem+' legible font and text bounds',minimum>=6 and inside)

case_report=load(E/'case_figures.json')
source_images={}
for item in case_report['case_audit']:
    a=np.load(item['artifact'])
    source_images[item['case_id']]=a['image']
    hashes={k:hashlib.sha256(a[k].tobytes()).hexdigest() for k in ['image','reference','masks','boxes','raw_predicted_ious']}
    check(item['case_id']+' original arrays exact hashes',all(hashes[k]==item['arrays'][k]['sha256_raw_C_order_bytes'] for k in hashes))
    ms=a['masks'];ref=a['reference']
    dice=lambda x,y:2*np.count_nonzero(x&y)/(np.count_nonzero(x)+np.count_nonzero(y))
    observed={'dice_vs_reference':dice(ms[0],ref),'risk_A':1-float(a['raw_predicted_ious'][0]),'risk_B':1-np.mean([dice(ms[0],m) for m in ms[1:]])}
    check(item['case_id']+' CPU metrics recomputed',all(same(v,item['recomputed_CPU_values'][k]) for k,v in observed.items()))
    check(item['case_id']+' all five masks nonempty',all(np.count_nonzero(m)>0 for m in ms))
for fig,cases in [('Figure_5',['case089','case175','case238']),('Figure_S6A',['case089','case175','case238']),('Figure_S6B',['case024','case105','case222'])]:
    pdf=fitz.open(B/'outputs/Figures'/f'{fig}.pdf');decoded=[]
    for info in pdf[0].get_image_info(xrefs=True):
        pix=fitz.Pixmap(pdf,info['xref'])
        if pix.n==3:
            a=np.frombuffer(pix.samples,np.uint8).reshape(pix.height,pix.width,3)
            # Matplotlib stores image rows bottom-up and applies negative y scale.
            if info['transform'][3]<0:a=np.flipud(a)
            if info['transform'][0]<0:a=np.fliplr(a)
            decoded.append(a)
    for cid in cases:
        check(fig+' '+cid+' native RGB pixels unaltered',any(a.shape==source_images[cid].shape and np.array_equal(a,source_images[cid]) for a in decoded))

docs={}
old=Document(R/'submission/bmt_v8_final/BMT_main_manuscript_v8.docx')
new=Document(B/'outputs/BMT_main_manuscript_v9.docx')
oldp=[p.text for p in old.paragraphs];newp=[p.text for p in new.paragraphs]
table=lambda d:[[[c.text for c in row.cells] for row in t.rows] for t in d.tables]
check('main all editable table cell strings exactly preserved',table(old)==table(new) and len(new.tables)==3)
decl_prefixes=['AI use and acknowledgments.','Research ethics.','Author contributions.','Research funding.','Conflict of interest.','Informed consent.','Data and code availability.','Data availability.','Use of Large Language Models, AI and Machine Learning Tools.']
declold=[p for p in oldp if any(p.startswith(z) for z in decl_prefixes)]
declnew=[p for p in newp if any(p.startswith(z) for z in decl_prefixes)]
body_old=oldp[oldp.index('Introduction'):oldp.index('Acknowledgments')]
body_new=[p for p in newp[newp.index('Introduction'):min(newp.index(p) for p in declnew)] if p not in ['Conclusions','Acknowledgments']]
check('main exact original scientific body paragraphs',body_old==body_new)
check('main exact original references',oldp[oldp.index('References'):oldp.index('Tables and table legends')]==newp[newp.index('References'):newp.index('Tables and table legends')])
decl_value=lambda p:p.split('.',1)[1]
check('all approved declaration facts exactly preserved',Counter(map(decl_value,declold))==Counter(map(decl_value,declnew)) and len(declnew)==7)
check('declarations in official template order and terms',[p.split('.',1)[0] for p in declnew]==['Research ethics','Informed consent','Author contributions','Use of Large Language Models, AI and Machine Learning Tools','Conflict of interest','Research funding','Data availability'])
captions=load(E/'final_caption_updates.json')['main']
for number,caption in captions.items():
    found=[p.text for p in new.paragraphs if re.match(r'^Figure '+number+r'\.',p.text)]
    expected='Figure '+number+'.  '+caption
    check('final main figure caption '+number,len(found)==1 and found[0]==expected)
approval='All authors have accepted responsibility for the entire content of this manuscript and approved its submission.'
check('final author approval sentence retained',approval in '\n'.join(newp))
abstract=[p for p in newp[newp.index('Abstract')+1:newp.index('Introduction')] if not p.startswith('Keywords')]
abstract_count=len(re.findall(r"\S+",' '.join(abstract)))
check('four-part abstract <=200 words',abstract_count<=200 and [p.split()[0] for p in abstract]==['Objectives','Methods','Results','Conclusions'],abstract_count)
keywords=[p for p in newp if p.startswith('Keywords')][0].split('Keywords',1)[1].strip().split('; ')
check('keywords3–6 alphabetical lowercase',3<=len(keywords)<=6 and sorted(keywords)==keywords and all(k==k.lower() for k in keywords))
refs=newp[newp.index('References')+1:newp.index('Tables and table legends')]
refs=[p for p in refs if p.strip()]
check('15 Vancouver reference labels <=35',len(refs)==15 and all(re.match(r'^'+str(i)+r'\.\s',p) for i,p in enumerate(refs,1)))
body=' '.join(newp[newp.index('Introduction'):newp.index('References')])
citations=[]
for group in re.findall(r'\[([\d, –-]+)\]',body):
    for field in re.split(r',\s*',group):
        nums=re.split('[–-]',field)
        values=range(int(nums[0]),int(nums[-1])+1)
        for v in values:
            if v not in citations:citations.append(v)
check('references sequentially first cited and all cited',citations==list(range(1,16)),citations)
check('main5 figures+3tables meets8 combined limit',len(captions)+len(new.tables)==8)
check('main no figure embeds required as separate files',len(new.inline_shapes)==0)
check('no author draft placeholders in main',not any(x in '\n'.join(newp).lower() for x in ['[author approval','[to be confirmed','待确认','tbd','insert here']))
docs['main']={'docx_sha256':sha(B/'outputs/BMT_main_manuscript_v9.docx'),'abstract_whitespace_words':abstract_count,'reference_count':len(refs),'table_cell_count':sum(len(r.cells) for t in new.tables for r in t.rows),'total_paragraph_plus_cell_whitespace_words':sum(len(p.text.split()) for p in new.paragraphs)+sum(len(c.text.split()) for t in new.tables for r in t.rows for c in r.cells),'declaration_order':[p.split('.',1)[0] for p in declnew]}
illustrated=Document(B/'outputs/BMT_main_manuscript_v9_illustrated.docx')
scales=[]
for number,shape in enumerate(illustrated.inline_shapes,1):
    scaled=shape.width/914400/6.89*figmeta['Figure_'+str(number)]['minimum_font_pt']
    scales.append(scaled)
check('all illustrated main labels >=6pt at actual document display size',len(scales)==5 and min(scales)>=6,scales)

supp_path=B/'outputs/BMT_supplementary_material_v5.docx'
if supp_path.exists():
    osup=Document(R/'submission/bmt_v8_final/BMT_supplementary_material_v4.docx');nsup=Document(supp_path)
    check('supplement19tables all878cell strings exactly preserved',len(nsup.tables)==19 and table(osup)==table(nsup))
    old_before=[p.text for p in osup.paragraphs[:104] if p.text.strip() and not p.text.startswith('Figure S')]
    new_before=[p.text for p in nsup.paragraphs if p.text.strip() and not p.text.startswith('Figure S')]
    check('supplement pre-S6 scientific prose exactly preserved',new_before[:len(old_before)]==old_before)
    supcaps=load(E/'final_caption_updates.json')['supplement']
    for number,cap in supcaps.items():
        found=[p.text for p in nsup.paragraphs if p.text.startswith('Figure '+number+'.')]
        check('final supplement caption '+number,len(found)==1 and found[0]=='Figure '+number+'. '+cap)
    check('supplement docx <10MB',supp_path.stat().st_size<10_000_000,supp_path.stat().st_size)
    s6pdf=B/'outputs/BMT_supplementary_Figure_S6_v5.pdf'
    check('S6 publication file <10MB',s6pdf.stat().st_size<10_000_000,s6pdf.stat().st_size)
    s6doc=fitz.open(s6pdf)
    check('S6 one case per page at readable font',len(s6doc)==6 and all(min(s['size'] for block in page.get_text('dict')['blocks'] if 'lines' in block for line in block['lines'] for s in line['spans'] if s['text'].strip())>=6 for page in s6doc))
    for page,cid in zip(s6doc,['case089','case175','case238','case024','case105','case222']):
        decoded=[]
        for info in page.get_image_info(xrefs=True):
            pix=fitz.Pixmap(s6doc,info['xref'])
            if pix.n==3:
                a=np.frombuffer(pix.samples,np.uint8).reshape(pix.height,pix.width,3)
                if info['transform'][3]<0:a=np.flipud(a)
                if info['transform'][0]<0:a=np.fliplr(a)
                decoded.append(a)
        check('final S6 PDF '+cid+' native original RGB retained',len(decoded)==5 and all(a.shape==source_images[cid].shape and np.array_equal(a,source_images[cid]) for a in decoded))
    sup_scales=[s.width/914400/6.89*figmeta['Figure_S'+str(i)]['minimum_font_pt'] for i,s in enumerate(nsup.inline_shapes,1)]
    check('all supplement embedded figure labels >=6pt at actual display size',len(sup_scales)==5 and min(sup_scales)>=6,sup_scales)
    docs['supplement']={'docx_sha256':sha(supp_path),'table_count':len(nsup.tables),'cell_count':sum(len(r.cells) for t in nsup.tables for r in t.rows),'embedded_figures':len(nsup.inline_shapes),'label_sizes_pt':sup_scales,'S6_pdf_sha256':sha(s6pdf)}
pdf_paths=[B/'outputs/BMT_main_manuscript_v9_preview.pdf',B/'outputs/BMT_main_manuscript_v9_illustrated_preview.pdf',B/'outputs/BMT_supplementary_material_v5_preview.pdf',B/'outputs/BMT_supplementary_Figure_S6_v5.pdf']
for path in pdf_paths:
    if not path.exists():continue
    d=fitz.open(path);outside=[];empty=[]
    for pi,page in enumerate(d):
        spans=[s for b in page.get_text('dict')['blocks'] if 'lines'in b for l in b['lines'] for s in l['spans'] if s['text'].strip()]
        if not spans and not page.get_images():empty.append(pi+1)
        for s in spans:
            x0,y0,x1,y1=s['bbox']
            if x0<-.1 or y0<-.1 or x1>page.rect.width+.1 or y1>page.rect.height+.1:outside.append({'page':pi+1,'text':s['text'],'bbox':s['bbox']})
    check(path.name+' no clipped text or empty pages',not outside and not empty,{'pages':len(d),'outside':outside,'empty_pages':empty})
    docs[path.name]={'sha256':sha(path),'pages':len(d),'empty_pages':empty,'outside_text':outside}

visual_report=B/'qa/visual_qa_report.json'
out={'scope':'Independent integration QA; source CSV/JSON/NPZ and final export inspection, no inference or resampling','checks':checks,'figure_metadata':figmeta,'documents':docs,'curve_points_checked':points,'source_data_unchanged':'All checks are read-only; source audit SHA matches recorded source arrays.','visual_review':{'report':str(visual_report),'sha256':sha(visual_report),'status':'All12production figures,20formalmainpages,5illustratedplates,25supplementpagesand6S6pages visually reviewed; no material issues.'},'limits':['Publisher template binary was unavailable: this review verifies current official guide content and explicit requirements, not exact template Word styles.','PNG manuscript embeds are display rasters; native RGB array equality was independently verified in Figure5/S6 production PDFs and all30 final S6 PDF image views. Figure2 source arrays and computed metrics were verified; display resizing is conventional figure rendering.','No original unarchived CUDA masks are claimed to have been recovered; displayed six-case masks are correctly identified as CPU replay outputs.'],'final_documents_pending':False}
(E/'independent_integration_qa.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'checks':len(checks),'failed':[q for q in checks if not q['pass']],'curves':points},ensure_ascii=False))
