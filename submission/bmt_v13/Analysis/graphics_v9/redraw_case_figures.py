#!/usr/bin/env python3
"""Publication case figures from six hash-verified captured CPU replay NPZs.
No inference, enhancement, cropping, intensity adjustment or generated imagery.
"""
from __future__ import annotations
import base64
from io import BytesIO
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
ET.register_namespace('', 'http://www.w3.org/2000/svg')
ET.register_namespace('xlink', 'http://www.w3.org/1999/xlink')
import numpy as np
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

ROOT = Path('/workspace/bmt_v9')
SOURCE = Path('/workspace/research_source/experiments/six_case_replay_v1/predictions')
OUT = ROOT/'outputs/Figures'
EVIDENCE = ROOT/'evidence/case_figures.json'
STYLE_PATH = ROOT/'evidence/figure_style_spec.json'
STYLE = json.loads(STYLE_PATH.read_text())
RECEIPT_PATH = SOURCE/'targeted_rerun_receipt.json'
RECEIPT = json.loads(RECEIPT_PATH.read_text())
W = 6.89
REF = STYLE['colors']['reference']
PRED = STYLE['colors']['prediction']
PROMPT = STYLE['colors']['prompt']
plt.rcParams.update({
    'font.family': 'Liberation Sans', 'font.size': 8.5,
    'axes.titlesize': 8.5, 'text.color': '#111111',
    'pdf.fonttype': 42, 'ps.fonttype': 42, 'svg.fonttype': 'none',
    'svg.image_inline': True, 'savefig.facecolor': 'white',
    'figure.facecolor': 'white', 'image.resample': False,
    'path.simplify': False,
})

def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def arr_hash(a):
    return hashlib.sha256(np.ascontiguousarray(a).tobytes(order='C')).hexdigest()

def dice(a,b):
    den = int(a.sum())+int(b.sum())
    return 1.0 if den == 0 else 2*int(np.logical_and(a,b).sum())/den

def bbox(a):
    yy,xx = np.where(a)
    return None if len(yy)==0 else [int(xx.min()), int(yy.min()), int(xx.max()), int(yy.max())]

CASES = {}
audit = []
for record in RECEIPT['cases']:
    path = SOURCE/record['artifact']
    filehash = sha256(path)
    assert filehash == record['artifact_sha256'], (path, 'hash mismatch')
    with np.load(path, allow_pickle=False) as z:
        data = {k:z[k].copy() for k in z.files}
    assert data['image'].dtype == np.uint8
    assert data['reference'].dtype == np.bool_
    assert data['masks'].dtype == np.bool_ and data['masks'].shape[0] == 5
    assert data['image'].shape[:2] == data['reference'].shape == data['masks'].shape[1:]
    d = dice(data['reference'], data['masks'][0])
    shifted = [dice(data['masks'][0], m) for m in data['masks'][1:]]
    values = {'dice_vs_reference': d,
              'risk_A': 1-float(data['raw_predicted_ious'][0]),
              'risk_B': 1-float(np.mean(shifted)),
              **dict(zip(['dice_shift_left','dice_shift_right','dice_shift_up','dice_shift_down'], shifted))}
    delta = {k:float(v-record['rerun'][k]) for k,v in values.items()}
    assert max(abs(x) for x in delta.values()) < 1e-12
    data.update(record=record, computed=values)
    CASES[record['image_id']] = data
    audit.append({
        'case_id':record['image_id'], 'archived_group':record['archived_group'],
        'artifact':str(path), 'artifact_sha256':filehash, 'matches_receipt':True,
        'arrays':{k:{'shape':list(data[k].shape),'dtype':str(data[k].dtype),
                     'sha256_raw_C_order_bytes':arr_hash(data[k])}
                  for k in ['image','reference','masks','boxes','raw_predicted_ious']},
        'individual_mask_sha256_raw_C_order_bytes':[arr_hash(a) for a in data['masks']],
        'reference_foreground_pixels':int(data['reference'].sum()),
        'reference_inclusive_xy_bounds':bbox(data['reference']),
        'prediction_foreground_pixels':[int(a.sum()) for a in data['masks']],
        'prediction_inclusive_xy_bounds':[bbox(a) for a in data['masks']],
        'recomputed_CPU_values':values, 'recomputed_minus_receipt':delta,
        'archived_CUDA_values_preserved':record['archived'],
        'CPU_minus_archived_initial_dice':float(d-record['archived']['dice_vs_reference']),
    })

# Each output SVG image is rewritten to the *exact original* RGB PNG bytes.
# This retains native raster pixels inside vector output instead of embedding a
# renderer-resampled image. Vector masks and prompts remain separate SVG paths.
def embed_native_rasters(svgpath, images):
    ns = {'s':'http://www.w3.org/2000/svg'}
    tree = ET.parse(svgpath)
    nodes = tree.getroot().findall('.//s:image', ns)
    assert len(nodes) == len(images), (len(nodes),len(images))
    embedded = []
    for node, arr in zip(nodes, images):
        buf = BytesIO(); Image.fromarray(arr, mode='RGB').save(buf, format='PNG')
        raw = buf.getvalue()
        node.set('{http://www.w3.org/1999/xlink}href', 'data:image/png;base64,'+base64.b64encode(raw).decode())
        node.set('style','image-rendering:pixelated;image-rendering:crisp-edges')
        embedded.append({'embedded_png_sha256':hashlib.sha256(raw).hexdigest(),
                         'raw_RGB_array_sha256':arr_hash(arr), 'native_shape':list(arr.shape)})
    tree.write(svgpath, encoding='utf-8', xml_declaration=True)
    # Decode and independently assert equality of every embedded raster.
    reread = ET.parse(svgpath).getroot().findall('.//s:image', ns)
    for node, arr in zip(reread, images):
        href = node.attrib['{http://www.w3.org/1999/xlink}href']
        restored = np.asarray(Image.open(BytesIO(base64.b64decode(href.split(',',1)[1]))))
        assert np.array_equal(restored, arr)
    return embedded

exports = []
def save(fig, name, rasters):
    OUT.mkdir(parents=True, exist_ok=True)
    for ext in ['png','pdf','svg']:
        path = OUT/f'{name}.{ext}'
        # 'none' embeds native pixels for vector outputs. In Agg it is nearest
        # neighbour, with resampling disabled; no medical pixel interpolation.
        for ax in fig.axes:
            for im in ax.images:
                im.set_interpolation('nearest' if ext=='png' else 'none')
        fig.savefig(path, dpi=600, transparent=False)
        if ext=='svg':
            embeds = embed_native_rasters(path, rasters)
        else:
            embeds = None
        exports.append({'file':str(path),'sha256':sha256(path),'bytes':path.stat().st_size,
                        'width_inches':float(fig.get_figwidth()),
                        'height_inches':float(fig.get_figheight()),
                        'embedded_original_rasters':embeds})
    plt.close(fig)

# Coordinates are in physical inches, so text and image spacing are invariant.
def ftext(fig,x,y,text,**kwargs):
    return fig.text(x/W,y/fig.get_figheight(),text,**kwargs)

def image_axes(fig, x, top, width, data, rasters):
    h,w = data['image'].shape[:2]
    # Half-pixel exterior guard retains contours on image-edge foreground.
    height = width*(h+1)/(w+1)
    ax = fig.add_axes([x/W,(top-height)/fig.get_figheight(),width/W,height/fig.get_figheight()])
    ax.imshow(data['image'], interpolation='nearest', resample=False, origin='upper')
    ax.set_xlim(-1,w); ax.set_ylim(h,-1)
    ax.set_axis_off()
    rasters.append(data['image'])
    return ax,height

def contour(ax, mask, color, linewidth=1.0):
    # Padding prevents a nonempty image-edge mask (notably case175) from losing
    # its border. Values inside the original mask are never changed.
    h,w = mask.shape
    ax.contour(np.arange(-1,w+1),np.arange(-1,h+1),
               np.pad(mask.astype(np.uint8),1), levels=[0.5],
               colors=[color], linewidths=linewidth, antialiased=True)

def prompt(ax,box):
    x0,y0,x1,y1 = [float(v) for v in box]
    ax.add_patch(Rectangle((x0,y0),x1-x0,y1-y0,fill=False,
                          edgecolor=PROMPT,linewidth=.65,linestyle=(0,(3,2))))

def rowmetrics(case_id):
    d = CASES[case_id]['computed']
    return f"{case_id}  |  CPU replay: Dice = {d['dice_vs_reference']:.4f}; risk A = {d['risk_A']:.4f}; risk B = {d['risk_B']:.4f}"

def legend(fig, y, with_prompt=False):
    handles = [Line2D([0],[0],color=REF,lw=1.2,label='Reference contour'),
               Line2D([0],[0],color=PRED,lw=1.2,label='CPU prediction contour')]
    if with_prompt:
        handles.append(Line2D([0],[0],color=PROMPT,lw=.8,linestyle=(0,(3,2)),label='Actual prompt box'))
    fig.legend(handles=handles,loc='center',bbox_to_anchor=(.5,y/fig.get_figheight()),
               frameon=False,ncol=len(handles),fontsize=8.0,
               handlelength=1.6,columnspacing=1.5,handletextpad=.6)

# Figure 5: comparison of the three shared screening misses.
main_ids = ['case089','case175','case238']
margin=.20; gap=.13; panelw=(W-2*margin-2*gap)/3
heights=[panelw*(CASES[k]['image'].shape[0]+1)/(CASES[k]['image'].shape[1]+1) for k in main_ids]
H=.72+sum(heights)+3*.43+.39
fig=plt.figure(figsize=(W,H)); rasters=[]
for j,title in enumerate(['Original image','Reference','Initial CPU prediction']):
    ftext(fig,margin+j*(panelw+gap)+panelw/2,H-.16,title,ha='center',va='top',fontsize=9.0)
row_top=H-.72
for r,case_id in enumerate(main_ids):
    data=CASES[case_id]
    ftext(fig,margin,row_top+.29,rowmetrics(case_id),ha='left',va='baseline',fontsize=8.5)
    for j in range(3):
        x=margin+j*(panelw+gap)
        ftext(fig,x,row_top+.055,chr(ord('A')+r*3+j),ha='left',va='bottom',weight='bold',fontsize=10)
        ax,_=image_axes(fig,x,row_top,panelw,data,rasters)
        if j==1: contour(ax,data['reference'],REF)
        if j==2: contour(ax,data['masks'][0],PRED)
    row_top-=heights[r]+.43
legend(fig,.20)
save(fig,'Figure_5',rasters)

# Supplement S6A/B: one composite case panel per row, showing all 5 masks.
# Left: full-FOV reference + initial mask. Right: four independent full-FOV
# shifted-mask images (left/right/up/down) with actual archived prompt boxes.
supp_layout = {}
for part,ids,letters in [
    ('A',['case089','case175','case238'],['A','B','C']),
    ('B',['case024','case105','case222'],['D','E','F'])]:
    leftx=.22; leftw=2.90; sx=[3.62,5.13]; smallw=1.35
    bodyheights=[]
    for case_id in ids:
        h,w=CASES[case_id]['image'].shape[:2]
        bodyheights.append(max(leftw*(h+1)/(w+1), 2*smallw*(h+1)/(w+1)+.30))
    H=.77+sum(bodyheights)+3*.45+.38
    fig=plt.figure(figsize=(W,H)); rasters=[]
    ftext(fig,leftx+leftw/2,H-.16,'Reference + initial prediction',ha='center',va='top',fontsize=9)
    ftext(fig,(sx[0]+sx[1]+smallw)/2,H-.16,'Prompt-shift CPU predictions',ha='center',va='top',fontsize=9)
    row_top=H-.77
    rows=[]
    for r,(case_id,letter) in enumerate(zip(ids,letters)):
        data=CASES[case_id]
        ftext(fig,leftx,row_top+.24,letter,ha='left',va='baseline',weight='bold',fontsize=10)
        ftext(fig,leftx+.22,row_top+.24,rowmetrics(case_id),ha='left',va='baseline',fontsize=8.15)
        ax,_=image_axes(fig,leftx,row_top,leftw,data,rasters)
        contour(ax,data['reference'],REF,1.05)
        contour(ax,data['masks'][0],PRED,1.05)
        prompt(ax,data['boxes'][0])
        sh=smallw*(data['image'].shape[0]+1)/(data['image'].shape[1]+1)
        dirs=['Left','Right','Up','Down']
        metrics=['dice_shift_left','dice_shift_right','dice_shift_up','dice_shift_down']
        for j,(direction,metric) in enumerate(zip(dirs,metrics),1):
            x=sx[(j-1)%2]; top=row_top-((j-1)//2)*(sh+.30)
            ftext(fig,x+smallw/2,top+.055,f"{direction} | D = {data['computed'][metric]:.4f}",
                  ha='center',va='bottom',fontsize=8.0)
            ax,_=image_axes(fig,x,top,smallw,data,rasters)
            contour(ax,data['reference'],REF,.8)
            contour(ax,data['masks'][j],PRED,.95)
            prompt(ax,data['boxes'][j])
        rows.append({'panel':letter,'case_id':case_id,'left':'reference + initial CPU prediction + initial actual prompt',
                     'right_grid':{'top_left':'left-shift mask','top_right':'right-shift mask',
                                   'bottom_left':'up-shift mask','bottom_right':'down-shift mask'},
                     'D_label':'Dice between initial CPU prediction and the displayed shifted CPU prediction'})
        row_top-=bodyheights[r]+.45
    legend(fig,.32,with_prompt=True)
    ftext(fig,W/2,.10,'D: Dice vs initial CPU mask. All images retain the full original field of view.',
          ha='center',va='center',fontsize=8.0)
    save(fig,f'Figure_S6{part}',rasters)
    supp_layout[f'Figure_S6{part}']=rows

caption5 = ('Figure 5. Three shared screening misses in the external set. '
            'Rows show case089 (A–C), case175 (D–F), and case238 (G–I); columns show the original released RGB ultrasound image, '
            'the released reference contour (blue), and the actual initial CPU replay prediction contour (orange). '
            'Row values are CPU replay Dice against the reference and risks A and B, rather than the original archived CUDA scores. '
            'All panels preserve the full original image field and aspect ratio. In case175, the nonempty prediction includes a thin upper-edge band. '
            'Masks were captured in the six-case exact-checkpoint CPU replay; no new model inference was performed to create this figure. '
            'Original CUDA scores and primary study estimates were retained unchanged.')
caption6 = ('Supplementary Figure S6. Actual prompt-shift responses in the six-case CPU replay. '
            'S6A contains shared misses case089 (A), case175 (B), and case238 (C); '
            'S6B contains B-only detections case024 (D), case105 (E), and case222 (F). '
            'Each case panel shows the reference (blue) and initial CPU prediction (orange) at left. '
            'The right 2 × 2 grid shows actual predictions after left (top left), right (top right), up (bottom left), and down (bottom right) prompt shifts; '
            'orange denotes the displayed CPU prediction, blue the same reference, and dashed gray the actual prompt box. '
            'Each D value is the Dice between that shifted prediction and the initial CPU prediction, rather than its Dice against the reference. '
            'Row values give initial CPU Dice against the reference and risks A/B. '
            'All 30 nonempty prediction masks from the six existing patients are shown, with original RGB pixels, full fields of view, and unchanged mask geometry. '
            'The case175 masks touch the upper image boundary; the right-shift prediction is a narrow nonempty band. '
            'CPU masks are not the unarchived original CUDA masks, and original CUDA scores were not overwritten. '
            'These six cases are not additional independent patients.')
result = {
    'source_receipt':str(RECEIPT_PATH),'source_receipt_sha256':sha256(RECEIPT_PATH),
    'style_spec':str(STYLE_PATH),'style_spec_sha256':sha256(STYLE_PATH),
    'script':str(Path(__file__).resolve()),'model_inference_performed':False,
    'figure_5_panel_mapping':{'A-C':'case089','D-F':'case175','G-I':'case238',
                              'columns':['original image','reference contour','initial CPU prediction contour']},
    'supplementary_panel_mapping':supp_layout,
    'mask_order':['initial','left','right','up','down'],
    'display_rules':{
        'image':'Original uint8 RGB arrays unchanged; no grayscale conversion, enhancement, normalization, cropping, or synthesis.',
        'FOV':'Full original field and aspect ratio in every image; outer half-pixel guard permits complete boundary display.',
        'PNG':'Nearest-neighbor interpolation, resample=False, 600 dpi.',
        'PDF':'Native RGB raster embedded by interpolation=none; vector contours and text.',
        'SVG':'Each image element embeds exact native RGB PNG; decoded equality asserted; crisp-edges/pixelated display; vector contours and editable text.',
        'contours':'Binary level 0.5 of actual boolean arrays, padded with false exterior only to recover image-edge boundaries; no change to array geometry.',
        'prompts':'Actual float32 boxes from each NPZ, unchanged; dashed gray; supplementary panels only.',
        'font':'Liberation Sans; minimum 8 pt (row headers 8.15 pt); panel letters bold 10 pt.',
        'legend':'Single shared legend per figure; reference blue #0072B2; CPU prediction orange #D55E00; actual prompt gray dashed.',
        'CPU_provenance':'All displayed numeric values are independently recalculated CPU replay values; archived CUDA values retained separately.'},
    'metric_definitions':{
        'Dice':'2 * intersection foreground / sum of foreground counts (both empty convention 1; no masks empty here)',
        'risk_A':'1 - raw_predicted_ious[0]',
        'risk_B':'1 - mean(Dice(initial, shifted)) across left/right/up/down'},
    'case_audit':audit, 'all_30_masks_nonempty':all(all(x>0 for x in c['prediction_foreground_pixels']) for c in audit),
    'max_recomputed_metric_absolute_error':max(abs(v) for c in audit for v in c['recomputed_minus_receipt'].values()),
    'captions':{'Figure_5':caption5,'Figure_S6':caption6},
    'exports':exports,
    'visual_QA':{'status':'pending independent render inspection'},
}
EVIDENCE.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
print(json.dumps({'outputs':[e['file'] for e in exports],
                  'all_30_masks_nonempty':result['all_30_masks_nonempty'],
                  'max_recomputed_metric_error':result['max_recomputed_metric_absolute_error']},indent=2))
