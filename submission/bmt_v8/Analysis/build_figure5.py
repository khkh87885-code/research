from pathlib import Path
import hashlib,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

ROOT=Path('/workspace/bmt_v8');SOURCE=Path('/workspace/research_source/experiments/six_case_replay_v1/predictions');OUT=ROOT/'outputs/Figures';OUT.mkdir(parents=True,exist_ok=True)
receipt=json.loads((SOURCE/'targeted_rerun_receipt.json').read_text());cases=receipt['cases'][:3]
assert [x['image_id']for x in cases]==['case089','case175','case238']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8.5})
fig,axs=plt.subplots(3,2,figsize=(6.89,7.7),squeeze=False)
panels=list('ABCDEF');evidence=[]
for row,c in enumerate(cases):
 file=SOURCE/c['artifact'];h=hashlib.sha256(file.read_bytes()).hexdigest();assert h==c['artifact_sha256']
 with np.load(file,allow_pickle=False)as z:
  for col,ax in enumerate(axs[row]):
   ax.imshow(z['image'],interpolation='nearest');ax.set_axis_off()
   if col==0:
    ax.contour(z['reference'],levels=[.5],colors=['#1b9e77'],linewidths=.9)
    b=z['boxes'][0];ax.add_patch(Rectangle((b[0],b[1]),b[2]-b[0],b[3]-b[1],fill=False,edgecolor='#56b4e9',linewidth=.8))
    ax.set_title(panels[row*2+col]+'  '+c['image_id']+': reference and prompt',fontsize=8.5,pad=5,loc='left')
   else:
    ax.contour(z['masks'][0],levels=[.5],colors=['#d95f02'],linewidths=.9)
    ax.set_title(panels[row*2+col]+'  CPU prediction; Dice '+f"{c['rerun']['dice_vs_reference']:.4f}",fontsize=8.5,pad=5,loc='left')
  evidence.append({'image_id':c['image_id'],'source_npz':c['artifact'],'sha256':h,'actual_prediction_foreground_pixels':int(z['masks'][0].sum()),'rerun_dice':c['rerun']['dice_vs_reference'],'archived_risk_A':c['archived']['risk_A'],'archived_risk_B':c['archived']['risk_B']})
fig.subplots_adjust(left=.035,right=.985,bottom=.02,top=.97,wspace=.10,hspace=.25)
fig.savefig(OUT/'Figure_5.png',dpi=600);fig.savefig(OUT/'Figure_5.pdf');plt.close(fig)
(ROOT/'evidence/figure5_provenance.json').write_text(json.dumps({'source':'Actual captured CPU replay masks; no model rerun during figure rendering','cases':evidence,'width_inches':6.89,'height_inches':7.7,'raster_dpi':600,'font_pt':8.5,'panels':'A-F','reference_color':'#1b9e77','prediction_color':'#d95f02','prompt_color':'#56b4e9'},indent=2)+'\n')
print('Built Figure 5 from three shared-miss actual CPU predictions.')
