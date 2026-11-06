"""Draw cohort flow and the observed SAM workflow using data and vector primitives."""
from pathlib import Path
import csv,hashlib,json,re
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,FancyArrowPatch

ROOT=Path('/workspace/bmt_v9');REPO=Path('/workspace/research_source');OUT=ROOT/'outputs/Figures';OUT.mkdir(parents=True,exist_ok=True)
SPEC=json.loads((ROOT/'evidence/figure_style_spec.json').read_text())
plt.rcParams.update({'font.family':'Liberation Sans','font.size':9,'pdf.fonttype':42,'svg.fonttype':'none','axes.linewidth':.7,'figure.facecolor':'white'})
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return list(csv.DictReader(p.open(encoding='utf-8-sig',newline='')))
def save(fig,stem):
 for text in fig.findobj(matplotlib.text.Text):
  text.set_text(re.sub(r'(?<=\d)[ \u00a0\u202f]*%', '\u202f%', text.get_text()))
 for ext in ['png','pdf','svg']:fig.savefig(OUT/(stem+'.'+ext),dpi=600,facecolor='white')
 plt.close(fig)
def box(ax,x,y,w,h,lines,size=9,bold_first=True,edge='#303030',fill='white',dash='solid'):
 ax.add_patch(Rectangle((x,y),w,h,facecolor=fill,edgecolor=edge,lw=.8,linestyle=dash))
 if isinstance(lines,str):lines=lines.split('\n')
 for i,text in enumerate(lines):
  yy=y+h-(i+.65)*h/len(lines)
  ax.text(x+w/2,yy,text,ha='center',va='center',fontsize=size,fontweight='bold'if i==0 and bold_first else'normal')
def arrow(ax,start,end,style='-|>',**kw):
 ax.add_patch(FancyArrowPatch(start,end,arrowstyle=style,mutation_scale=9,lw=.8,color='#303030',shrinkA=1,shrinkB=1,**kw))
def path_arrow(ax,points):
 for p,q in zip(points[:-2],points[1:-1]):ax.plot([p[0],q[0]],[p[1],q[1]],color='#303030',lw=.8)
 arrow(ax,points[-2],points[-1])

lockfile=REPO/'reproducibility/study_lock.json';lock=json.loads(lockfile.read_text());devfile=REPO/'reproducibility/records/development_cases.csv';valfile=REPO/'reproducibility/records/validation_cases.csv'
dev=read(devfile);val=read(valfile);intr=[r for r in val if r['split']=='internal_holdout'];ext=[r for r in val if r['split']=='external_test']
counts={key:{'N':len(rows),'F':sum(float(r['dice_vs_reference'])<.7 for r in rows)}for key,rows in [('development',dev),('internal',intr),('external',ext)]}
assert counts=={'development':{'N':213,'F':24},'internal':{'N':851,'F':93},'external':{'N':252,'F':16}}
assert len(lock['external_eligibility']['excluded_normal_case_ids_without_main_mask'])==4
assert len({r['patient_id']for r in dev+intr})==1064
rawmeta=REPO/'data/raw/BUS-BRA/BUSBRA/bus_data.csv';assert len(read(rawmeta))==1875
fig=plt.figure(figsize=(6.89,5.6));ax=fig.add_axes([0,0,1,1]);ax.set(xlim=(0,1),ylim=(0,1));ax.set_axis_off()
ax.text(.035,.965,'A  BUS-BRA',weight='bold',fontsize=10)
ax.text(.545,.965,'B  BrEaST',weight='bold',fontsize=10)
box(ax,.035,.80,.43,.13,['Source dataset','1,064 patients; 1,875 images'])
box(ax,.545,.80,.42,.13,['Source dataset','256 patients; 256 scans'])
ax.plot([.25,.25],[.80,.755],color='#303030',lw=.8)
path_arrow(ax,[(.25,.755),(.135,.755),(.135,.72)])
path_arrow(ax,[(.25,.755),(.365,.755),(.365,.72)])
ax.text(.25,.775,'Patient-level split',fontsize=8,ha='center',bbox={'facecolor':'white','edgecolor':'none','pad':.5})
box(ax,.035,.55,.20,.17,['Development','213 patients','24 low-quality masks'],size=8.5)
box(ax,.265,.55,.20,.17,['Internal test','851 patients','93 low-quality masks'],size=8.5)
path_arrow(ax,[(.755,.80),(.755,.755),(.655,.755),(.655,.72)])
path_arrow(ax,[(.755,.755),(.88,.755),(.88,.72)])
box(ax,.545,.55,.22,.17,['External test','252 patients','16 low-quality masks'],size=8.5)
box(ax,.795,.58,.17,.14,['Excluded: 4','Normal cases','No primary mask'],size=8,dash='dashed')
arrow(ax,(.135,.55),(.135,.43))
box(ax,.035,.26,.20,.17,['Threshold selection','20% review target','43/213 per score'],size=8.5)
box(ax,.31,.26,.455,.17,['Fixed-threshold evaluation','Apply development cutoffs unchanged','1,103 internal and external test patients'],size=9)
arrow(ax,(.235,.345),(.31,.345))
arrow(ax,(.365,.55),(.365,.43))
arrow(ax,(.655,.55),(.655,.43))
ax.text(.035,.14,'One image per patient in every analysis cohort.',fontsize=9)
ax.text(.035,.09,'Low quality: initial-prediction Dice against the reference < 0.70.',fontsize=9)
save(fig,'Figure_1')

capture=REPO/'figures/source/example_case.npz';meta=json.loads((capture.with_suffix('.json')).read_text());assert sha(capture)==meta['artifact_sha256']
z=np.load(capture,allow_pickle=False);image=z['image'];ref=z['reference'];masks=z['masks'];boxes=z['boxes'];assert image.dtype==np.uint8 and masks.shape==(5,*ref.shape)
case=next(r for r in ext if r['image_id']=='case001')
dice=lambda a,b:2*np.count_nonzero(a&b)/(int(a.sum())+int(b.sum()))
quality=dice(masks[0],ref);riskb=1-np.mean([dice(masks[0],m)for m in masks[1:]])
assert quality==float(case['dice_vs_reference']) and abs(riskb-float(case['risk_B']))<1e-15
fig=plt.figure(figsize=(6.89,6.1))
fig.text(.035,.965,'A  Image, reference-informed prompt and observed masks',fontsize=10,weight='bold')
labels=['Image + prompt','Initial','Left','Right','Up','Down']
for i,label in enumerate(labels):
 ax=fig.add_axes([.035+i*.157,.665,.147,.25]);ax.set_axis_off()
 if i==0:
  ax.imshow(image,interpolation='nearest');ax.contour(ref,levels=[.5],colors=['#0072B2'],linewidths=.8)
  b=boxes[0];ax.add_patch(Rectangle((b[0],b[1]),b[2]-b[0],b[3]-b[1],fill=False,edgecolor='#D55E00',lw=.8))
 else:ax.imshow(masks[i-1],cmap='gray',vmin=0,vmax=1,interpolation='nearest')
 ax.set_title(label,fontsize=8.5,pad=5)
fig.text(.035,.615,'BrEaST case001   |   Blue: released reference   |   Orange: initial box   |   White: mask foreground',fontsize=8)

bax=fig.add_axes([.035,.14,.445,.41]);bax.set(xlim=(0,1),ylim=(0,1));bax.set_axis_off()
bax.text(0,1.04,'B  Frozen SAM ViT-B inference',fontsize=10,weight='bold')
box(bax,.0,.69,.43,.21,['RGB image','Image encoder: once'],size=8.5)
box(bax,.0,.23,.43,.21,['Five prompt boxes','Prompt encoder'],size=8.5)
box(bax,.61,.42,.38,.29,['Mask decoder','One mask per prompt','Five actual outputs'],size=8.3)
path_arrow(bax,[(.43,.795),(.80,.795),(.80,.71)])
path_arrow(bax,[(.43,.335),(.80,.335),(.80,.42)])
bax.text(.58,.85,'Shared image embedding',fontsize=7.5,ha='center')
bax.text(.60,.22,'Initial + four shifts',fontsize=7.8,ha='center')
bax.text(.0,.025,'Box expansion: 10% per side; clipped shifts: ±5%.',fontsize=8)

cax=fig.add_axes([.535,.14,.43,.41]);cax.set(xlim=(0,1),ylim=(0,1));cax.set_axis_off()
cax.text(0,1.04,'C  Separate review scores',fontsize=10,weight='bold')
cax.text(0,.82,'Method A: model confidence',fontsize=9,weight='bold',color='#0072B2')
cax.text(0,.68,'Risk A = 1 − predicted IoU of initial mask',fontsize=8.5)
cax.text(0,.48,'Method B: prompt disagreement',fontsize=9,weight='bold',color='#D55E00')
cax.text(0,.34,'Risk B = 1 − mean Dice(initial, shifted masks)',fontsize=8.5)
cax.text(0,.13,'Evaluate each score at its own locked cutoff.',fontsize=8.5)
cax.text(0,.025,'Review flag = 1 if risk ≥ cutoff.',fontsize=8.5)
fig.text(.035,.055,'Quality target: Dice(initial prediction, manual reference) < 0.70.',fontsize=8.5)
save(fig,'Figure_2')

evidence={'renderer':'Matplotlib vector rectangles, arrows, text and unchanged captured arrays; no generative-image service','style_spec':str(ROOT/'evidence/figure_style_spec.json'),'sources':{str(p.relative_to(REPO)):sha(p)for p in [lockfile,devfile,valfile,capture,capture.with_suffix('.json')]},'cohort_counts':counts,'excluded_normal_case_ids':lock['external_eligibility']['excluded_normal_case_ids_without_main_mask'],'example_case':'case001','example_quality_Dice':quality,'example_risk_B':riskb,'example_mask_pixels':[int(m.sum())for m in masks],'image_array_sha256':hashlib.sha256(image.tobytes()).hexdigest(),'mask_array_sha256':hashlib.sha256(masks.tobytes()).hexdigest(),'metadata_dpi':600,'font':'Liberation Sans','minimum_font_pt':7.5,'caption_mapping':{'1':'Figure 1. Cohort construction and fixed-threshold evaluation. (A) BUS-BRA patients are split into development and internal testing; the development cohort selects each review cutoff at a 20% target. (B) BrEaST contributes 252 patients after exclusion of four normal cases without a primary lesion mask. Each analysis patient contributes one image. Development cutoffs are transferred unchanged to the 1,103 internal and external test patients. Low-quality masks have initial-prediction Dice below 0.70 against the released reference. Counts refer to patients and their single initial masks.','2':'Figure 2. Reference-informed prompting, observed SAM outputs and separate review scores. (A) The released image and reference from BrEaST case001 [10] define the initial box after 10% expansion per side. Actual archived initial, left-, right-, up- and down-prompt masks are shown in their full image field; white is foreground. Shifts are 5% of the clipped initial width or height. (B) Frozen SAM ViT-B encodes each image once and uses the shared embedding for five single-mask predictions. (C) Method A is one minus initial-mask predicted IoU; method B is one minus the mean initial-to-shifted mask Dice. Each score is evaluated separately against its locked development cutoff. The reference-derived prompt represents known-location evaluation. The workflow is a conventional vector schematic and the image/masks are measured study data, not synthesized illustrations.'}}
(ROOT/'evidence/study_diagrams.json').write_text(json.dumps(evidence,indent=2)+'\n')
print('Redrew Figure 1 and Figure 2 from verified cohort records and actual captured masks.')
