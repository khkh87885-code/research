#!/usr/bin/env python3
"""Publication Figure 4 from frozen curves, original CIs and same-K CSV.

No model inference, threshold fitting, new CI or significance test is performed.
The matched-budget panel is a post hoc display of points on the frozen curves.
"""
from pathlib import Path
import csv, hashlib, json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.text import Text
import numpy as np

BASE = Path('/workspace/policy_clarity')
SOURCE = BASE/'source/Reproducibility'
OUT = BASE/'outputs/Figures'
QA = BASE/'evidence/figure4_qa.json'
NAME = 'Breast Ultrasound Quality Control Figure 4'
PALETTE = {'A':'#0072B2', 'B':'#D55E00'}
INK, GRAY, WHITE = '#202020', '#666666', '#FFFFFF'
PRIMARY = SOURCE/'reference/primary.json'
SUPP = SOURCE/'reference/supplementary.json'
CURVES = SOURCE/'review_curve_counts.csv'
RECORDS = SOURCE/'records/validation_cases.csv'
MATCHED = BASE/'analysis/equal_review_counts.csv'

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def csvrows(path):
    with path.open(encoding='utf-8-sig',newline='')as f:return list(csv.DictReader(f))
def signed(n):return f'{n:+.2f}'.replace('-','−')
def exact_ci(item):
    lo,hi=item['ci95_pp']
    return f"{signed(item['difference_pp'])} [{signed(lo)}, {signed(hi)}]"

plt.rcParams.update({
    'font.family':'Liberation Sans','font.size':9.5,
    'axes.labelsize':9.5,'axes.titlesize':10.5,
    'xtick.labelsize':9.5,'ytick.labelsize':9.5,'legend.fontsize':9.2,
    'axes.linewidth':.7,'lines.linewidth':1.2,
    'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none',
    'figure.facecolor':WHITE,'axes.facecolor':WHITE,'savefig.facecolor':WHITE,
    'text.color':INK,'axes.labelcolor':INK,'axes.edgecolor':INK,
    'xtick.color':INK,'ytick.color':INK,'savefig.bbox':None,
})

def plain(ax,left=True):
    ax.spines[['top','right']].set_visible(False)
    ax.spines['left'].set_visible(left)
    ax.tick_params(width=.7,length=3,pad=3)
    ax.grid(False)

def header(fig,letter,title,x,y,subtitle):
    fig.text(x-.055,y,letter,fontsize=11.5,weight='bold',va='baseline')
    fig.text(x,y,title,fontsize=10.5,weight='bold',va='baseline')
    fig.text(x,y-.035,subtitle,fontsize=9.2,color=GRAY,va='baseline')

def operating(ax,x,y,method,policy):
    ax.plot(x,y,marker='s'if policy=='locked'else'o',ls='none',
            ms=5.0 if policy=='locked'else 6.2,
            mfc=PALETTE[method]if policy=='locked'else WHITE,
            mec=PALETTE[method],mew=1.0,zorder=5)

def main():
    primary=json.loads(PRIMARY.read_text());supp=json.loads(SUPP.read_text())
    rows=csvrows(CURVES);records=csvrows(RECORDS);same=csvrows(MATCHED)
    assert [int(r['K_per_method'])for r in same]==[33,35,50]
    assert all(int(r['N'])==252 and int(r['low_quality_N'])==16 for r in same)
    assert all(r['analysis_role']=='post hoc descriptive same-K presentation'for r in same)
    fig=plt.figure(figsize=(6.89,6.80))
    a=fig.add_axes([.105,.59,.36,.29]);b=fig.add_axes([.61,.59,.36,.29])
    curves={};primitives={'curves':[],'operating_points':[],'paired_contrasts':[],'matched_K':[]}
    line_styles={'A':'-','B':(0,(4,2))}
    for ax,split,letter,title in [(a,'internal_holdout','A','Internal holdout'),(b,'external_test','B','External test')]:
        cohort=primary['cohorts'][split];n,f=cohort['N'],cohort['F']
        plain(ax);ax.set(xlim=(0,n),ylim=(0,104),yticks=[0,25,50,75,100])
        ax.set_xticks([0,200,400,600,800]if split=='internal_holdout'else[0,50,100,150,200,250])
        ax.set_xlabel('Patients selected for review (count)',labelpad=7)
        if ax is a:ax.set_ylabel('Low-quality patients detected (%)',labelpad=7)
        header(fig,letter,title,ax.get_position().x0,.952,f'N = {n}; low quality n = {f}')
        for method in ['A','B']:
            current=sorted([r for r in rows if r['split']==split and r['method']==method],key=lambda r:int(r['reviewed']))
            x=np.array([int(r['reviewed'])for r in current]);y=np.array([int(r['low_quality_detected'])for r in current])
            ranked=sorted([r for r in records if r['split']==split and r['status']=='scored'],key=lambda r:(-float(r['risk_'+method]),r['patient_id']))
            expected=np.r_[0,np.cumsum([int(r['low_quality'])for r in ranked])]
            assert np.array_equal(x,np.arange(n+1))and np.array_equal(y,expected)
            curves[(split,method)]=(x,y)
            ax.step(x,100*y/f,where='post',color=PALETTE[method],ls=line_styles[method],lw=1.25)
            locked=cohort['methods'][method];assert y[locked['R']]==locked['TP']
            operating(ax,locked['R'],100*locked['TP']/f,method,'locked')
            primitives['curves'].append({'split':split,'method':method,'N':n,'F':f,'x':x.tolist(),'detected_count':y.tolist()})
            primitives['operating_points'].append({'split':split,'method':method,'policy':'locked','K':locked['R'],'detected':locked['TP']})
            if split=='external_test':
                top=supp['external_equal_review']['methods'][method];assert y[top['R']]==top['TP']
                operating(ax,top['R'],100*top['TP']/f,method,'top50')
                primitives['operating_points'].append({'split':split,'method':method,'policy':'top50','K':top['R'],'detected':top['TP']})
        if split=='internal_holdout':
            ax.text(.45,.29,'Locked cutoffs',transform=ax.transAxes,fontsize=9.2,weight='bold')
            ax.text(.45,.18,'A: 71/93; K = 174',transform=ax.transAxes,fontsize=9.2,color=PALETTE['A'])
            ax.text(.45,.07,'B: 68/93; K = 150',transform=ax.transAxes,fontsize=9.2,color=PALETTE['B'])
    handles=[Line2D([0],[0],color=PALETTE[m],ls=line_styles[m],lw=1.25,label='Method '+m)for m in ['A','B']]
    handles += [Line2D([0],[0],marker='s',ms=5,ls='none',color=GRAY,label='Locked cutoff'),
                Line2D([0],[0],marker='o',ms=5.5,ls='none',mfc=WHITE,mec=GRAY,label='Top 50 per method')]
    fig.legend(handles=handles,loc='center',bbox_to_anchor=(.525,.493),ncol=4,frameon=False,
               columnspacing=1.1,handlelength=1.9,handletextpad=.5)

    # C retains the exact original paired nominal intervals; they are not reused
    # as uncertainty estimates for the three matched-count display points.
    header(fig,'C','External paired contrasts',.105,.415,'Original paired nominal 95% CIs')
    c=fig.add_axes([.225,.165,.245,.195]);plain(c,left=False)
    c.set(xlim=(-45,50),ylim=(-.65,1.65),xticks=[-40,0,40],yticks=[1,0],
          yticklabels=['Locked cutoffs\nA: 35; B: 33','Top 50\nK = 50 each'])
    c.tick_params(axis='y',length=0,pad=8)
    c.axvline(0,color=GRAY,lw=.8,ls=(0,(3,2)),zorder=0)
    c.set_xlabel('B − A (percentage points)',labelpad=7)
    contrast_items=[('Locked',primary['contrasts']['H3'],'s'),
                    ('Top 50',supp['external_equal_review']['detection_B_minus_A'],'o')]
    for y,(label,item,marker)in zip([1,0],contrast_items):
        x=item['difference_pp'];lo,hi=item['ci95_pp']
        c.errorbar(x,y,xerr=[[x-lo],[hi-x]],fmt=marker,color=INK,ecolor=INK,ms=5,
                   mfc=WHITE if marker=='o'else INK,mew=.9,elinewidth=1,capsize=2.4,capthick=.8,zorder=3)
        c.text(x,y+.29,signed(x),ha='center',fontsize=9.2)
        primitives['paired_contrasts'].append({'label':label,**item})
    fig.text(.065,.064,'Locked: '+exact_ci(contrast_items[0][1]),fontsize=9.0)
    fig.text(.065,.038,'Top 50: '+exact_ci(contrast_items[1][1]),fontsize=9.0)

    # D shows three reviewed categories; equal spacing is categorical, not a
    # numeric slope. The complete numeric rank curves remain in A/B.
    header(fig,'D','Matched review counts',.61,.415,'Post hoc display; low quality n = 16')
    d=fig.add_axes([.61,.165,.36,.195]);plain(d)
    d.set(xlim=(-.48,2.48),ylim=(0,16.8),xticks=[0,1,2],
          xticklabels=[str(int(r['K_per_method']))for r in same],yticks=[0,4,8,12,16])
    d.set_xlabel('Review count per method (K)',labelpad=7)
    d.set_ylabel('Detected (of 16)',labelpad=6)
    marker_map={'A':'o','B':'^'}
    for i,row in enumerate(same):
        k=int(row['K_per_method'])
        for method,offset in [('A',-.11),('B',.11)]:
            detected=int(row[method+'_detected'])
            assert curves[('external_test',method)][1][k]==detected
            d.plot(i+offset,detected,marker=marker_map[method],ls='none',color=PALETTE[method],ms=5.8,mew=.9)
            d.text(i+offset,detected+.85,str(detected),ha='center',va='bottom',color=PALETTE[method],fontsize=10)
            primitives['matched_K'].append({'K':k,'method':method,'detected':detected,'low_quality_N':16,'N':252,'role':row['analysis_role'],'budget_role':row['budget_role']})
    dlegend=[Line2D([0],[0],color=PALETTE[m],marker=marker_map[m],ls='none',ms=5.5,label='Method '+m)for m in ['A','B']]
    fig.legend(handles=dlegend,loc='center',bbox_to_anchor=(.79,.045),ncol=2,frameon=False,columnspacing=1.4,handletextpad=.4)
    fig.canvas.draw();renderer=fig.canvas.get_renderer();fw,fh=fig.bbox.width,fig.bbox.height
    texts=[];outside=[]
    for t in fig.findobj(Text):
        if not t.get_visible()or not t.get_text().strip():continue
        bb=t.get_window_extent(renderer)
        if bb.x0<-.5 or bb.y0<-.5 or bb.x1>fw+.5 or bb.y1>fh+.5:outside.append(t.get_text())
        texts.append({'text':t.get_text(),'font_pt':t.get_fontsize(),'bbox_figure_fraction':[bb.x0/fw,bb.y0/fh,bb.x1/fw,bb.y1/fh]})
    assert not outside,outside
    assert min(x['font_pt']for x in texts)>=9
    OUT.mkdir(parents=True,exist_ok=True)
    for ext in ['pdf','png']:
        fig.savefig(OUT/(NAME+'.'+ext),**({'dpi':600}if ext=='png'else{'metadata':{'CreationDate':None,'ModDate':None,'Title':'Risk-ranked review curves and matched review counts'}}))
    preview=BASE/'evidence/figure4_preview.png';fig.savefig(preview,dpi=160)
    report={'status':'PASS_PENDING_VISUAL_REVIEW','source_files':{str(p):sha(p)for p in [PRIMARY,SUPP,CURVES,RECORDS,MATCHED,Path(__file__)]},
            'size_inches':[6.89,6.8],'png_dpi':600,'minimum_font_pt':min(x['font_pt']for x in texts),
            'out_of_canvas_text':outside,'primitives':primitives,'text_geometry':texts,
            'original_intervals_preserved':True,'new_intervals_computed':False,'same_K_display_role':'post hoc descriptive',
            'outputs':{ext:{'path':str(OUT/(NAME+'.'+ext)),'sha256':sha(OUT/(NAME+'.'+ext))}for ext in ['pdf','png']},
            'preview':str(preview),'no_image_synthesis':True,'no_brand_marks':True}
    QA.write_text(json.dumps(report,indent=2)+'\n');plt.close(fig)
    print(json.dumps({k:report[k]for k in ['status','size_inches','minimum_font_pt','outputs','preview']},indent=2))

if __name__=='__main__':main()
