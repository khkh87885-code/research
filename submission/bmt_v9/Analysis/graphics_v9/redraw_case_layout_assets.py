#!/usr/bin/env python3
"""Export one S6 case per A4 integration asset without altering production figures.
All source RGB arrays, masks and prompts are preserved. No model inference.
"""
from pathlib import Path
from io import BytesIO
import hashlib,json
import numpy as np
from PIL import Image
import fitz
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

ROOT=Path('/workspace/bmt_v9')
SOURCE=Path('/workspace/research_source/experiments/six_case_replay_v1/predictions')
OUT=ROOT/'layout_assets';OUT.mkdir(parents=True,exist_ok=True)
STYLE=json.loads((ROOT/'evidence/figure_style_spec.json').read_text())
RECEIPT=json.loads((SOURCE/'targeted_rerun_receipt.json').read_text())
RECORDS={c['image_id']:c for c in RECEIPT['cases']}
W=6.89;REF=STYLE['colors']['reference'];PRED=STYLE['colors']['prediction'];GRAY=STYLE['colors']['prompt']
plt.rcParams.update({'font.family':'Liberation Sans','font.size':8.5,
                     'pdf.fonttype':42,'ps.fonttype':42,'figure.facecolor':'white',
                     'savefig.facecolor':'white','image.resample':False,'path.simplify':False})

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def arrsha(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def dice(a,b):return 2*int(np.logical_and(a,b).sum())/(int(a.sum())+int(b.sum()))
def text(fig,x,y,s,**kw):return fig.text(x/W,y/fig.get_figheight(),s,**kw)
def image_ax(fig,x,top,width,data):
    h,w=data['image'].shape[:2];height=width*(h+1)/(w+1)
    ax=fig.add_axes([x/W,(top-height)/fig.get_figheight(),width/W,height/fig.get_figheight()])
    ax.imshow(data['image'],interpolation='nearest',resample=False,origin='upper')
    ax.set_xlim(-1,w);ax.set_ylim(h,-1);ax.set_axis_off()
    return ax

def contour(ax,a,color,lw):
    h,w=a.shape
    ax.contour(np.arange(-1,w+1),np.arange(-1,h+1),np.pad(a.astype(np.uint8),1),
               levels=[.5],colors=[color],linewidths=lw,antialiased=True)
def prompt(ax,b):
    x0,y0,x1,y1=[float(v) for v in b]
    ax.add_patch(Rectangle((x0,y0),x1-x0,y1-y0,fill=False,edgecolor=GRAY,
                          linewidth=.65,linestyle=(0,(3,2))))

items=[]
for panel,case_id in zip('ABCDEF',['case089','case175','case238','case024','case105','case222']):
    record=RECORDS[case_id];src=SOURCE/record['artifact']
    assert sha(src)==record['artifact_sha256']
    with np.load(src,allow_pickle=False)as z:data={k:z[k].copy() for k in z.files}
    assert data['image'].dtype==np.uint8 and data['masks'].dtype==np.bool_
    assert all(int(m.sum())>0 for m in data['masks'])
    ds=[dice(data['masks'][0],m) for m in data['masks'][1:]]
    vals={'dice_vs_reference':dice(data['reference'],data['masks'][0]),
          'risk_A':1-float(data['raw_predicted_ious'][0]),'risk_B':1-float(np.mean(ds))}
    assert all(abs(v-record['rerun'][k])<1e-12 for k,v in vals.items())
    h,w=data['image'].shape[:2]
    leftx=.22;leftw=2.85;sx=[3.62,5.13];smallw=1.32
    smallh=smallw*(h+1)/(w+1)
    body=max(leftw*(h+1)/(w+1),2*smallh+.30)
    H=max(3.70,body+1.14)
    fig=plt.figure(figsize=(W,H))
    text(fig,leftx+leftw/2,H-.10,'Reference + initial prediction',ha='center',va='top',fontsize=9)
    text(fig,(sx[0]+sx[1]+smallw)/2,H-.10,'Prompt-shift CPU predictions',ha='center',va='top',fontsize=9)
    top=H-.64
    text(fig,leftx,top+.22,panel,ha='left',va='baseline',fontsize=10,weight='bold')
    metric=f"{case_id}  |  CPU replay: Dice = {vals['dice_vs_reference']:.4f}; risk A = {vals['risk_A']:.4f}; risk B = {vals['risk_B']:.4f}"
    text(fig,leftx+.22,top+.22,metric,ha='left',va='baseline',fontsize=8.15)
    ax=image_ax(fig,leftx,top,leftw,data)
    contour(ax,data['reference'],REF,1.05);contour(ax,data['masks'][0],PRED,1.05);prompt(ax,data['boxes'][0])
    for j,direction in enumerate(['Left','Right','Up','Down'],1):
        x=sx[(j-1)%2];st=top-((j-1)//2)*(smallh+.30)
        text(fig,x+smallw/2,st+.055,f'{direction} | D = {ds[j-1]:.4f}',ha='center',va='bottom',fontsize=8)
        ax=image_ax(fig,x,st,smallw,data)
        contour(ax,data['reference'],REF,.8);contour(ax,data['masks'][j],PRED,.95);prompt(ax,data['boxes'][j])
    handles=[Line2D([0],[0],color=REF,lw=1.2,label='Reference contour'),
             Line2D([0],[0],color=PRED,lw=1.2,label='CPU prediction contour'),
             Line2D([0],[0],color=GRAY,lw=.8,linestyle=(0,(3,2)),label='Actual prompt box')]
    fig.legend(handles=handles,loc='center',bbox_to_anchor=(.5,.32/H),frameon=False,ncol=3,
               fontsize=8,handlelength=1.6,columnspacing=1.5,handletextpad=.6)
    text(fig,W/2,.10,'D: Dice vs initial CPU mask. Full original field of view; CPU replay values.',
         ha='center',va='center',fontsize=8)
    name=f'Figure_S6_case_{panel}_{case_id}';files=[]
    for ext in ['png','pdf']:
        path=OUT/f'{name}.{ext}'
        for ax in fig.axes:
            for im in ax.images:im.set_interpolation('nearest' if ext=='png' else 'none')
        fig.savefig(path,dpi=600,transparent=False)
        if ext=='png':
            with Image.open(path) as original:
                if original.mode=='RGBA':assert original.getextrema()[3]==(255,255)
                rgb=original.convert('RGB')
            rgb.save(path,format='PNG',compress_level=9,optimize=True,dpi=(600,600))
        files.append({'file':str(path),'sha256':sha(path),'bytes':path.stat().st_size})
    plt.close(fig)
    # Native PDF rasters must equal the exact input after correcting backend's
    # bottom-up storage scanlines. Full FOV and original RGB are thus checkable.
    doc=fitz.open(OUT/f'{name}.pdf');page=doc[0]
    native=[]
    for im in page.get_images(full=True):
        raw=doc.extract_image(im[0])['image'];a=np.asarray(Image.open(BytesIO(raw)).convert('RGB'))
        match=np.array_equal(a[::-1],data['image']);assert match
        native.append({'native_width':im[2],'native_height':im[3],
                       'exact_RGB_array_match_after_PDF_scanline_correction':match})
    assert len(native)==5
    spans=[s for b in page.get_text('dict')['blocks'] if 'lines'in b for l in b['lines'] for s in l['spans']]
    assert min(s['size'] for s in spans)>=7.99
    assert all(page.rect.contains(fitz.Rect(s['bbox'])) for s in spans)
    preview=ROOT/'qa'/f'{name}_preview.png';page.get_pixmap(matrix=fitz.Matrix(1.5,1.5)).save(preview)
    png=Image.open(OUT/f'{name}.png')
    item={'panel':panel,'case_id':case_id,'source_production_figure':'Figure_S6A' if panel in 'ABC' else 'Figure_S6B',
          'caption_continuation_label':f'Supplementary Figure S6, panel {panel} ({case_id}).',
          'width_inches':W,'height_inches':H,'png_pixels':list(png.size),'png_dpi':list(png.info['dpi']),
          'font_minimum_pt':8,'files':files,'preview':str(preview),
          'source_npz_sha256':sha(src),'source_original_RGB_sha256_raw_C_order':arrsha(data['image']),
          'reference_sha256_raw_C_order':arrsha(data['reference']),
          'five_actual_mask_sha256_raw_C_order':[arrsha(m) for m in data['masks']],
          'prediction_foreground_pixels':[int(m.sum()) for m in data['masks']],
          'CPU_values':vals,'shift_Dice_vs_initial':dict(zip(['left','right','up','down'],ds)),
          'source_pixel_validation':{'all_five_PDF_rasters_match_native_original_RGB':True,'pdf_images':native,
                                     'full_field_and_aspect_preserved':True,
                                     'no_pixel_enhancement_no_grayscale_conversion_no_inference':True,
                                     'actual_masks_and_boxes_unchanged':True},
          'layout_QA':{'all_text_in_page_bounds':True,'pdf_min_font_pt':min(s['size'] for s in spans)}}
    items.append(item)
    print(f"{panel} {case_id}: {W:.2f} x {H:.3f} in; PNG {png.size}; validated 5 original RGB rasters",flush=True)
index={'purpose':'A4 supplementary manuscript integration: one original S6 case panel per page, production S6A/B unchanged',
       'script':str(Path(__file__).resolve()),'script_sha256':sha(Path(__file__)),
       'panel_order':['A','B','C','D','E','F'],'assets':items,
       'shared_caption_source':'/workspace/bmt_v9/evidence/case_figures.json:captions.Figure_S6',
       'shared_caption_placement':'Use complete shared S6 caption once, then continuation labels A–F on subsequent case pages.',
       'within_case_mapping':{'left':'reference + initial CPU prediction + initial actual prompt',
                             'top_right_grid_left':'actual left-shift prediction',
                             'top_right_grid_right':'actual right-shift prediction',
                             'bottom_right_grid_left':'actual up-shift prediction',
                             'bottom_right_grid_right':'actual down-shift prediction'},
       'display_rules':'Identical to production S6: full FOV/native RGB, nearest-neighbor PNG, native-raster PDF, padded binary 0.5 contours, 8pt minimum.'}
(OUT/'layout_asset_index.json').write_text(json.dumps(index,indent=2,ensure_ascii=False)+'\n')
evidence_path=ROOT/'evidence/case_figures.json';evidence=json.loads(evidence_path.read_text())
evidence['layout_assets']={'index':str(OUT/'layout_asset_index.json'),'index_sha256':sha(OUT/'layout_asset_index.json'),**index}
evidence_path.write_text(json.dumps(evidence,indent=2,ensure_ascii=False)+'\n')
