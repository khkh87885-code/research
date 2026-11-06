#!/usr/bin/env python3
"""Patient bootstrap of threshold calibration, sampling and rank stability.

Portable CLI: --repo REPO --output OUTPUT_ROOT --replicates 10000 --seed 20261106.
The adjacent protocol/analysis_plan.json remains the governing frozen plan.
No study calculation module is imported and no inference/training is performed.
"""
from __future__ import annotations

import os
for _variable in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS',
                  'NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS','BLIS_NUM_THREADS'):
    os.environ[_variable]='1'

import argparse
import csv
import hashlib
import json
import math
import platform
import resource
import subprocess
import sys
import time
from collections import Counter
from dataclasses import dataclass
from datetime import datetime,timezone
from fractions import Fraction
from pathlib import Path

import numpy as np

ROUTES=('fixed_cutoffs_test_sampling','development_calibration_only','full_resampling')
ROUTE_LABELS={ROUTES[0]:'1. Fixed cutoffs; test sampling',
              ROUTES[1]:'2. Development calibration only',
              ROUTES[2]:'3. Full development + test sampling'}
ENDPOINTS=('H1_A_external_minus_internal_detection_pp',
           'H2_A_external_minus_internal_review_pp',
           'external_fixed_B_minus_A_detection_pp',
           'external_equal_B_minus_A_detection_pp')


@dataclass
class Cohort:
    ids: np.ndarray
    quality: np.ndarray
    A: np.ndarray
    B: np.ndarray

    def __len__(self):return len(self.ids)

    def take(self,index):
        # Retain every draw including repeated patient indices.
        return Cohort(self.ids[index],self.quality[index],self.A[index],self.B[index])


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path):
    return list(csv.DictReader(path.open(encoding='utf-8-sig',newline='')))


def array_cohort(rows):
    assert len(rows)==len({r['patient_id']for r in rows})
    assert all(r['status']=='scored'for r in rows)
    q=np.array([float(r['dice_vs_reference'])<.7 for r in rows],dtype=bool)
    assert np.array_equal(q,np.array([int(r['low_quality'])for r in rows],dtype=bool))
    a=np.array([float(r['risk_A'])for r in rows],dtype=float)
    b=np.array([float(r['risk_B'])for r in rows],dtype=float)
    assert np.isfinite(a).all() and np.isfinite(b).all()
    # IDs deliberately remain strings: official lexicographic tie-breaking.
    return Cohort(np.array([r['patient_id']for r in rows],dtype=str),q,a,b)


def calibrate(scores,target=Fraction(1,5)):
    """Nearest attainable review count with all score ties kept together."""
    values,counts=np.unique(scores,return_counts=True)
    values=values[::-1];counts=counts[::-1]
    attainable=np.concatenate(([0],np.cumsum(counts)))
    distance=np.abs(target.denominator*attainable-target.numerator*len(scores))
    best=np.flatnonzero(distance==distance.min())
    selected=best[np.argmin(attainable[best])]
    threshold=float(np.nextafter(values[0],np.inf))if selected==0 else float(values[selected-1])
    reviewed=int(attainable[selected]);at_cutoff=int(np.count_nonzero(scores==threshold))
    assert int(np.count_nonzero(scores>=threshold))==reviewed
    return threshold,reviewed,at_cutoff


def fixed_counts(cohort,ta,tb):
    f=int(cohort.quality.sum());fa=cohort.A>=ta;fb=cohort.B>=tb
    return {'N':len(cohort),'F':f,'R_A':int(fa.sum()),'R_B':int(fb.sum()),
            'TP_A':int(np.count_nonzero(fa&cohort.quality)),
            'TP_B':int(np.count_nonzero(fb&cohort.quality)),
            'risk_equals_cutoff_A':int(np.count_nonzero(cohort.A==ta)),
            'risk_equals_cutoff_B':int(np.count_nonzero(cohort.B==tb))}


def rank_at_budget(cohort,k):
    """Risk descending, original CaseID string, draw-position replica index."""
    assert 0<k<=len(cohort)
    replica=np.arange(len(cohort),dtype=int)
    result={}
    for method in ('A','B'):
        score=getattr(cohort,method)
        order=np.lexsort((replica,cohort.ids,-score))
        selected=order[:k];boundary=score[selected[-1]]
        tied=score==boundary;above=int(np.count_nonzero(score>boundary))
        at_boundary=int(tied.sum());selected_at_boundary=k-above
        assert 0<selected_at_boundary<=at_boundary
        result[method]={'TP':int(cohort.quality[selected].sum()),'R':k,
                        'boundary_score':float(boundary),'boundary_tie_records':at_boundary,
                        'selected_at_boundary':selected_at_boundary,
                        'boundary_split':int(selected_at_boundary<at_boundary),
                        'boundary_unique_patients':len(set(cohort.ids[tied].tolist())),
                        'selected_replica_indices':selected.tolist()}
    return result


def safe_difference(x1,n1,x2,n2):
    return float('nan')if not n1 or not n2 else 100*(x1/n1-x2/n2)


def evaluate(internal,external,taus,ranked):
    i=fixed_counts(internal,*taus);e=fixed_counts(external,*taus)
    equal_delta=ranked['B']['TP']-ranked['A']['TP']
    fixed_delta=e['TP_B']-e['TP_A']
    return {'N_internal':i['N'],'F_internal':i['F'],'N_external':e['N'],'F_external':e['F'],
            'internal_reviews_A':i['R_A'],'internal_reviews_B':i['R_B'],
            'internal_TP_A':i['TP_A'],'internal_TP_B':i['TP_B'],
            'external_reviews_A':e['R_A'],'external_reviews_B':e['R_B'],
            'external_TP_A':e['TP_A'],'external_TP_B':e['TP_B'],
            'external_equal_TP_A':ranked['A']['TP'],'external_equal_TP_B':ranked['B']['TP'],
            'external_equal_count':ranked['A']['R'],
            ENDPOINTS[0]:safe_difference(e['TP_A'],e['F'],i['TP_A'],i['F']),
            ENDPOINTS[1]:safe_difference(e['R_A'],e['N'],i['R_A'],i['N']),
            ENDPOINTS[2]:100*fixed_delta/e['F']if e['F']else float('nan'),
            ENDPOINTS[3]:100*equal_delta/e['F']if e['F']else float('nan'),
            'original_direction_reversal':int(fixed_delta>0 and equal_delta<0)if e['F']else None,
            'opposite_direction_reversal':int(fixed_delta<0 and equal_delta>0)if e['F']else None,
            'any_strict_reversal':int(fixed_delta*equal_delta<0)if e['F']else None,
            'fixed_difference_tie':int(fixed_delta==0)if e['F']else None,
            'equal_difference_tie':int(equal_delta==0)if e['F']else None,
            'internal_risk_equals_cutoff_A':i['risk_equals_cutoff_A'],
            'internal_risk_equals_cutoff_B':i['risk_equals_cutoff_B'],
            'external_risk_equals_cutoff_A':e['risk_equals_cutoff_A'],
            'external_risk_equals_cutoff_B':e['risk_equals_cutoff_B'],
            **{f'equal_{m}_{key}':ranked[m][key]for m in ('A','B')
               for key in ('boundary_tie_records','selected_at_boundary','boundary_split','boundary_unique_patients')}}


def checks():
    # A tie of two highest scores at a target of one review is equally far from
    # zero and two. The rule chooses zero, not an arbitrary one of the tied pair.
    t,r,n=calibrate(np.array([1.,1.,0.,0.,0.]));assert r==0 and t>1 and n==0
    t,r,n=calibrate(np.array([1.,1.,1.,0.,0.,0.,0.,0.,0.,0.]));assert r==3 and t==1 and n==3
    c=Cohort(np.array(['2','10','2','1']),np.array([1,0,1,0],bool),np.ones(4),np.ones(4))
    ranked=rank_at_budget(c,2)
    assert ranked['A']['selected_replica_indices']==[3,1]
    assert ranked['A']['boundary_split']==1
    duplicate=Cohort(np.array(['2','2','1']),np.array([1,1,0],bool),np.array([1.,1.,0.]),np.array([1.,1.,0.]))
    assert fixed_counts(duplicate,.5,.5)['TP_A']==2
    assert rank_at_budget(duplicate,1)['A']['selected_replica_indices']==[0]
    empty=Cohort(np.array(['1','2']),np.zeros(2,bool),np.array([.1,.2]),np.array([.3,.4]))
    e=evaluate(empty,empty,(.15,.35),rank_at_budget(empty,1))
    assert math.isnan(e[ENDPOINTS[0]])and math.isnan(e[ENDPOINTS[2]])and math.isnan(e[ENDPOINTS[3]])
    assert math.isfinite(e[ENDPOINTS[1]])and e['original_direction_reversal']is None
    return {'calibration_ties_grouped':True,'equidistant_calibration_fewer_reviews':True,
            'CaseID_string_then_replica_index':True,'duplicate_draws_retained':True,
            'zero_quality_denominators_NA':True}


def distribution(values):
    a=np.array(values,dtype=float);valid=a[np.isfinite(a)]
    if not len(valid):return {'valid_replicates':0,'NA_replicates':len(a),
                             'median':None,'percentile_95':None,
                             'negative_count':0,'zero_count':0,'positive_count':0,
                             'negative_fraction':None,'zero_fraction':None,'positive_fraction':None}
    return {'valid_replicates':len(valid),'NA_replicates':len(a)-len(valid),
            'median':float(np.median(valid)),
            'percentile_95':np.quantile(valid,[.025,.975],method='linear').tolist(),
            'negative_count':int(np.count_nonzero(valid<0)),
            'zero_count':int(np.count_nonzero(valid==0)),
            'positive_count':int(np.count_nonzero(valid>0)),
            'negative_fraction':float(np.mean(valid<0)),
            'zero_fraction':float(np.mean(valid==0)),
            'positive_fraction':float(np.mean(valid>0))}


def summarize(records,point):
    summaries={}
    for route in ROUTES:
        rows=[r for r in records if r['route']==route]
        endpoints={key:distribution([r[key]for r in rows])for key in ENDPOINTS}
        joint=[r for r in rows if r['original_direction_reversal']is not None]
        sign=Counter(('positive'if r[ENDPOINTS[2]]>0 else'negative'if r[ENDPOINTS[2]]<0 else'zero',
                      'positive'if r[ENDPOINTS[3]]>0 else'negative'if r[ENDPOINTS[3]]<0 else'zero')for r in joint)
        joint_summary={'valid_replicates':len(joint),'NA_replicates':len(rows)-len(joint)}
        for field in ('original_direction_reversal','opposite_direction_reversal','any_strict_reversal',
                      'fixed_difference_tie','equal_difference_tie'):
            count=sum(r[field]for r in joint)
            joint_summary[field]={'count':count,'fraction':count/len(joint)if joint else None}
        any_ties=sum(r['fixed_difference_tie']or r['equal_difference_tie']for r in joint)
        joint_summary['any_difference_tie']={'count':any_ties,'fraction':any_ties/len(joint)if joint else None}
        joint_summary['both_differences_tie']={'count':sign['zero','zero'],
                                             'fraction':sign['zero','zero']/len(joint)if joint else None}
        joint_summary['sign_matrix']={fixed:{equal:{'count':sign[fixed,equal],
                                                   'fraction':sign[fixed,equal]/len(joint)if joint else None}
                                            for equal in ('negative','zero','positive')}
                                      for fixed in ('negative','zero','positive')}
        assert sum(sign.values())==len(joint)
        ties={}
        for m in ('A','B'):
            ties[m]={'equal_boundary_split_count':sum(r[f'equal_{m}_boundary_split']for r in rows),
                     'equal_boundary_multiple_records_count':sum(r[f'equal_{m}_boundary_tie_records']>1 for r in rows),
                     'equal_boundary_tie_record_count_distribution':dict(sorted(Counter(r[f'equal_{m}_boundary_tie_records']for r in rows).items())),
                     'development_cutoff_tie_record_distribution':dict(sorted(Counter(r[f'development_at_cutoff_{m}']for r in rows).items())),
                     'development_review_count_distribution':dict(sorted(Counter(r[f'development_reviews_{m}']for r in rows).items()))}
        summaries[route]={'label':ROUTE_LABELS[route],'endpoints_pp':endpoints,
                          'joint_direction_patterns':joint_summary,'tie_accounting':ties,
                          'thresholds':{m:distribution([r['threshold_'+m]for r in rows])for m in ('A','B')},
                          'zero_low_quality_denominators':{
                              'internal':sum(r['F_internal']==0 for r in rows),
                              'external':sum(r['F_external']==0 for r in rows)},
                          'unique_original_patient_counts':{
                              c:{'minimum':min(r['unique_'+c]for r in rows),
                                 'median':float(np.median([r['unique_'+c]for r in rows])),
                                 'maximum':max(r['unique_'+c]for r in rows)}for c in ('development','internal','external')}}
    assert all(r['threshold_A']==point['threshold_A']and r['threshold_B']==point['threshold_B']
               for r in records if r['route']==ROUTES[0])
    assert all(r[ENDPOINTS[3]]==point[ENDPOINTS[3]]for r in records if r['route']==ROUTES[1])
    assert all(r['F_internal']==93 and r['F_external']==16 for r in records if r['route']==ROUTES[1])
    return summaries


def render_figure(summary,destination,replicates):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.titlesize':11,
                         'axes.labelsize':10,'axes.spines.top':False,'axes.spines.right':False,
                         'pdf.fonttype':42,'svg.fonttype':'none'})
    blue='#24648A';orange='#B86824';gray='#6B7280';light='#D9DEE3'
    fig,axs=plt.subplots(2,2,figsize=(13,8.8),layout='constrained',gridspec_kw={'height_ratios':[1,1.35]})
    labels=['R1  Test sampling','R2  Calibration only','R3  Full resampling'];y=np.arange(3)[::-1]
    for panel,key,title in [(axs[0,0],ENDPOINTS[0],'A  Method A detection: external − internal'),
                            (axs[0,1],ENDPOINTS[1],'B  Method A review: external − internal')]:
        for yy,route in zip(y,ROUTES):
            dist=summary['routes'][route]['endpoints_pp'][key]
            if dist['percentile_95']is None:
                panel.text(.5,yy,'NA',transform=panel.get_yaxis_transform(),ha='center');continue
            lo,hi=dist['percentile_95'];med=dist['median']
            panel.plot([lo,hi],[yy,yy],color=blue,lw=2)
            panel.plot([lo,lo],[yy-.06,yy+.06],color=blue,lw=1)
            panel.plot([hi,hi],[yy-.06,yy+.06],color=blue,lw=1)
            panel.scatter([med],[yy],s=35,color=blue,zorder=4)
        panel.axvline(0,color='#444444',lw=.9)
        panel.axvline(summary['observed'][key],color=gray,lw=1.1,ls='--')
        panel.set(yticks=y,yticklabels=labels,xlabel='Difference (percentage points)',title=title,ylim=(-.55,2.55))
        panel.grid(axis='x',color='#E6E8EB',lw=.6);panel.set_axisbelow(True)
    c=axs[1,0]
    for ri,route in enumerate(ROUTES):
        for policy,key,color,marker,dy in [('fixed',ENDPOINTS[2],blue,'o',.15),('top 50',ENDPOINTS[3],orange,'s',-.15)]:
            yy=2-ri+dy;dist=summary['routes'][route]['endpoints_pp'][key]
            if dist['percentile_95']is None:
                c.text(.5,yy,'NA',transform=c.get_yaxis_transform(),ha='center');continue
            lo,hi=dist['percentile_95'];med=dist['median']
            c.plot([lo,hi],[yy,yy],color=color,lw=2)
            c.scatter([med],[yy],color=color,marker=marker,s=35,zorder=4)
    c.axvline(0,color='#444444',lw=.9)
    c.set(yticks=y,yticklabels=labels,xlabel='B − A detection (percentage points)',
          title='C  External contrast under the two review rules',ylim=(-.55,2.55))
    c.grid(axis='x',color='#E6E8EB',lw=.6);c.set_axisbelow(True)
    c.legend(handles=[Line2D([0],[0],color=blue,marker='o',label='Numerical cutoffs'),
                      Line2D([0],[0],color=orange,marker='s',label='Equal top 50')],loc='upper center',bbox_to_anchor=(.5,-.15),ncol=2,frameon=False)
    d=axs[1,1];segments=[('Original direction',blue),('Opposite direction',orange),('Any zero contrast',light),('Same nonzero sign',gray)]
    percentages=[]
    for route in ROUTES:
        j=summary['routes'][route]['joint_direction_patterns'];n=j['valid_replicates']
        vals=[j['original_direction_reversal']['count'],j['opposite_direction_reversal']['count'],j['any_difference_tie']['count']]
        vals.append(n-sum(vals));assert vals[-1]>=0
        percentages.append([100*v/n for v in vals]if n else [0,0,0,0])
    for yy,route in zip(y,ROUTES):
        if not summary['routes'][route]['joint_direction_patterns']['valid_replicates']:
            d.text(50,yy,'NA: no jointly valid resamples',ha='center',va='center')
    left=np.zeros(3)
    for si,(label,color)in enumerate(segments):
        vals=np.array([v[si]for v in percentages]);d.barh(y,vals,left=left,color=color,height=.55,label=label)
        for yy,l,v in zip(y,left,vals):
            if v>=8:d.text(l+v/2,yy,f'{v:.1f}%',ha='center',va='center',fontsize=9,color='white'if si in (0,1,3)else'#202020')
        left+=vals
    d.set(xlim=(0,100),yticks=y,yticklabels=labels,xlabel='Empirical fraction of jointly valid resamples (%)',
          title='D  Joint fixed-cutoff / equal-review signs',ylim=(-.55,2.55))
    d.legend(loc='upper center',bbox_to_anchor=(.5,-.15),ncol=2,frameon=False,fontsize=9)
    fig.suptitle(f'Patient bootstrap stability: {replicates:,} replicates per route',fontsize=15)
    fig.supxlabel('Dots: bootstrap medians; lines: descriptive percentile 95% intervals. Dashed: observed A contrast.\n'
                  'Original direction = fixed B−A > 0 and equal-review B−A < 0. These fractions are not p-values or posterior probabilities.\n'
                  'R1 fixed-cutoff resampling cannot create A-only detections absent from the observed paired data.',fontsize=9)
    destination.mkdir(parents=True,exist_ok=True)
    fig.savefig(destination/'bootstrap_stability.png',dpi=300)
    fig.savefig(destination/'bootstrap_stability.pdf')
    plt.close(fig)


def write_report(summary,path):
    lines=['# Bootstrap threshold, sampling and ranking stability','',
           'This post hoc exploratory analysis follows the frozen cloud validation plan. It does not change the original locked analysis or replace its Newcombe intervals. No new model inference, training or independent patients were introduced.','',
           '## Principal descriptive findings','']
    full=summary['routes'][ROUTES[2]];full_h1=full['endpoints_pp'][ENDPOINTS[0]]['percentile_95'];full_h2=full['endpoints_pp'][ENDPOINTS[1]]['percentile_95']
    j=full['joint_direction_patterns'];orig=j['original_direction_reversal'];opposite=j['opposite_direction_reversal'];ties=j['any_difference_tie']
    lines+=[f"Under full resampling, the A detection contrast had a percentile interval of [{full_h1[0]:+.2f}, {full_h1[1]:+.2f}] pp, while its review-fraction contrast had an interval of [{full_h2[0]:+.2f}, {full_h2[1]:+.2f}] pp. The original strict direction pattern occurred in {orig['count']}/{j['valid_replicates']} jointly valid resamples ({100*orig['fraction']:.2f}%); the opposite pattern occurred in {100*opposite['fraction']:.2f}%, and at least one zero contrast occurred in {100*ties['fraction']:.2f}%. These frequencies describe the observed-sample resampling experiment, not population probabilities.",'',
           '## Observed values and design','',
           f"The observed A external-minus-internal detection difference is {summary['observed'][ENDPOINTS[0]]:.8f} percentage points (pp), and its review difference is {summary['observed'][ENDPOINTS[1]]:.8f} pp. The external B-minus-A detection difference is +18.75 pp at the locked cutoffs and −6.25 pp when each method ranks and selects 50 cases. These were verified before resampling.",'',
           f"We used {summary['replicates_per_route']:,} iterations, seed {summary['seed']}, and one process with BLAS-related thread limits set to one. Independent NumPy SeedSequence child streams generated patient indices within development (213), internal (851) and external (252) cohorts. A/B scores and quality labels travelled together. The same draws were shared across relevant routes to isolate each source of variation; the three cohort streams remained independent.",'',
           'Route 1 holds the original numerical cutoffs fixed and resamples both test cohorts. Route 2 resamples only development and recalibrates both 20% cutoffs while retaining the original test cohorts and original equal-top50 selections. Route 3 combines development recalibration with test-cohort resampling. Calibration keeps score ties together and chooses the attainable review count nearest 20%, with fewer reviews when equally close.','',
           'Each resampled external cohort retains 252 draw records, including repeated original patient IDs. Equal-review sorting is descending risk, original CaseID string, then draw-position replica index; it selects exactly 50 draw records without deduplication. These repeated draws represent empirical resampling, not additional patients.','',
           '## Descriptive percentile intervals','',
           '| Route | Endpoint | Observed, pp | Bootstrap median, pp | Percentile 95%, pp | Valid / total |',
           '| --- | --- | ---: | ---: | --- | --- |']
    endpoint_labels={ENDPOINTS[0]:'H1: A detection, external − internal',ENDPOINTS[1]:'H2: A review, external − internal',
                     ENDPOINTS[2]:'External fixed-cutoff B − A detection',ENDPOINTS[3]:'External equal-top50 B − A detection'}
    for route in ROUTES:
        for key in ENDPOINTS:
            s=summary['routes'][route]['endpoints_pp'][key]
            bounds='NA'if s['percentile_95']is None else f"[{s['percentile_95'][0]:+.2f}, {s['percentile_95'][1]:+.2f}]"
            median='NA'if s['median']is None else f"{s['median']:+.2f}"
            lines.append(f"| {ROUTE_LABELS[route]} | {endpoint_labels[key]} | {summary['observed'][key]:+.2f} | {median} | {bounds} | {s['valid_replicates']}/{summary['replicates_per_route']} |")
    lines+=['','## Empirical signs and direction reversal','',
            'All fractions below use jointly valid external contrasts as the denominator. Zero contrasts are reported separately and are never counted as a strict reversal. Full 3×3 fixed/equal sign matrices and the sign fractions for each endpoint are in summary.json.','',
            '| Route | Joint valid | Original direction: fixed>0, equal<0 | Opposite: fixed<0, equal>0 | Any zero contrast | Same nonzero sign |',
            '| --- | ---: | --- | --- | --- | --- |']
    for route in ROUTES:
        j=summary['routes'][route]['joint_direction_patterns'];n=j['valid_replicates'];fields=['original_direction_reversal','opposite_direction_reversal','any_difference_tie']
        counts=[j[f]['count']for f in fields];rest=n-sum(counts)
        values=[f'{x}/{n} ({100*x/n:.2f}%)'if n else'NA (0 jointly valid)'for x in counts+[rest]]
        lines.append('| '+ROUTE_LABELS[route]+' | '+str(n)+' | '+' | '.join(values)+' |')
    lines+=['','## Calibration and tie accounting','',
            'At the original locked thresholds, the external low-quality paired table has 10 detected by both, zero detected by A alone, three detected by B alone and three detected by neither. Route 1 resamples only these observed patient records, so it cannot create an A-only detection. Its fixed-cutoff B-minus-A contrast is structurally constrained to be nonnegative, producing a percentile interval [0.00,40.00] pp. That empirical-support constraint cannot exclude an A advantage in the population or establish equivalence/noninferiority. The original paired Newcombe interval [−4.28,+40.04] pp is retained and must not be replaced by the bootstrap interval. No smoothing, prior or invented discordant cases were introduced.','',
            'Route 2 necessarily retains −6.25 pp for the equal-top50 contrast because neither the test cases nor their rankings are changed. Variation in its fixed-cutoff contrast isolates development-calibration variability, rather than new test-sampling information.','',
            '| Route | Method | Cutoff percentile 95% | Median cutoff | Equal-top50 boundary split / total |',
            '| --- | --- | --- | --- | --- |']
    for route in ROUTES:
        for m in ('A','B'):
            dist=summary['routes'][route]['thresholds'][m];lo,hi=dist['percentile_95'];t=summary['routes'][route]['tie_accounting'][m]
            lines.append(f"| {ROUTE_LABELS[route]} | {m} | [{lo:.9f}, {hi:.9f}] | {dist['median']:.9f} | {t['equal_boundary_split_count']}/{summary['replicates_per_route']} |")
    lines+=['',
            'A split boundary tie means that equal-top50 selects only part of a set of equal-risk draw records. It is allowed by the ranking rule and resolved by original CaseID and replica index. This differs from calibration, where a tied score group must be reviewed together. Complete boundary multiplicities and development review-count distributions are retained.','',
            '## Missing denominators and interpretation','']
    for route in ROUTES:
        z=summary['routes'][route]['zero_low_quality_denominators']
        lines.append(f"- {ROUTE_LABELS[route]}: zero-low-quality denominators occurred in {z['internal']} internal and {z['external']} external resamples. Affected detection contrasts are NA; review fractions remain defined.")
    lines+=['',
            'These empirical fractions describe how often signs appear when resampling the observed patients under the stated rules. They are neither p-values nor posterior probabilities that a method is superior or that a reversal is a population property. Percentile intervals are descriptive bootstrap intervals and do not replace the original independent/paired Newcombe intervals. An interval spanning zero does not establish equivalence. The external sample contains only 16 observed low-quality cases; resampling does not remedy that limited independent information.','',
            '## Provenance and computation','',
            f"- Source commit: `{summary['source_commit']}`.",
            f"- Analysis plan SHA-256: `{summary['protocol_sha256']}`.",
            f"- Script SHA-256 during computation: `{summary['script_sha256']}`.",
            f"- Bootstrap computation wall time: {summary['runtime']['bootstrap_wall_seconds']:.3f} s; CPU time: {summary['runtime']['bootstrap_cpu_seconds']:.3f} s.",
            f"- Total recorded wall time through plot/CSV generation: {summary['runtime']['total_wall_seconds']:.3f} s.",
            f"- Peak process RSS: {summary['runtime']['peak_RSS_MiB']:.1f} MiB.",
            '- All source input SHA-256 values, runtime library versions, RNG derivation, valid counts and boundary tests are recorded in summary.json. Source files were rehashed after computation and remained unchanged.',
            '- Implementation is independent of the original study modules. Original point estimates and synthetic edge cases were checked before the full run. The repeated-ID and zero-denominator rules were exercised explicitly.',
            '- `results/bootstrap_stability/iterations.csv` contains all three routes for every iteration. Undefined numbers or indicators use the literal NA. No zero-denominator detection value was imputed as zero.','',
            '![Bootstrap stability](../figures/bootstrap_stability.png)']
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text('\n'.join(lines)+'\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--replicates',type=int,default=10000)
    parser.add_argument('--seed',type=int,default=20261106)
    parser.add_argument('--plan',type=Path,default=Path(__file__).resolve().parents[1]/'protocol/analysis_plan.json')
    args=parser.parse_args();assert args.replicates>0
    start=time.perf_counter();start_cpu=time.process_time();started=datetime.now(timezone.utc).isoformat()
    repo=args.repo.resolve();output=args.output.resolve();plan=json.loads(args.plan.read_text());plan_hash=digest(args.plan)
    assert args.replicates==plan['bootstrap']['replicates']and args.seed==plan['bootstrap']['seed'], 'CLI settings must match this frozen plan; use a new explicit plan for a changed experiment.'
    commit=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
    assert commit==plan['source_commit']
    frozen=repo/'reproducibility';lock=json.loads((frozen/'study_lock.json').read_text())
    paths=[frozen/'study_lock.json',frozen/'records/development_cases.csv',frozen/'records/validation_cases.csv']
    for c in lock['cohorts'].values():paths.append(frozen/c['manifest'])
    paths.append(frozen/'reference/primary.json')
    hashes={str(p.relative_to(repo)):digest(p)for p in paths}
    for p in paths[1:]:assert hashes[str(p.relative_to(repo))]==lock['files_sha256'][str(p.relative_to(frozen))]
    devrows=read_csv(paths[1]);testrows=read_csv(paths[2])
    dev=array_cohort(devrows)
    internalrows=[r for r in testrows if r['split']=='internal_holdout'];externalrows=[r for r in testrows if r['split']=='external_test']
    internal=array_cohort(internalrows);external=array_cohort(externalrows)
    assert (len(dev),len(internal),len(external))==(213,851,252)
    assert set(dev.ids).isdisjoint(set(internal.ids))
    for split,rows in [('development',devrows),('internal_holdout',internalrows),('external_test',externalrows)]:
        manifest=read_csv(frozen/lock['cohorts'][split]['manifest'])
        getkeys=lambda rr:sorted((r['patient_id'],r['image_id'],r['pathology'])for r in rr)
        assert getkeys(rows)==getkeys(manifest)
    ta=lock['threshold_lock']['methods']['A']['threshold'];tb=lock['threshold_lock']['methods']['B']['threshold']
    baseA=calibrate(dev.A);baseB=calibrate(dev.B);assert baseA[:2]==(ta,43)and baseB[:2]==(tb,43)
    k=plan['bootstrap']['external_equal_review_count'];assert k==50
    baseline_ranked=rank_at_budget(external,k);point=evaluate(internal,external,(ta,tb),baseline_ranked)
    point.update(threshold_A=ta,threshold_B=tb,development_reviews_A=43,development_reviews_B=43)
    flag_a=external.A>=ta;flag_b=external.B>=tb;low=external.quality
    paired={'both':int(np.count_nonzero(low&flag_a&flag_b)),
            'A_only':int(np.count_nonzero(low&flag_a&~flag_b)),
            'B_only':int(np.count_nonzero(low&~flag_a&flag_b)),
            'neither':int(np.count_nonzero(low&~flag_a&~flag_b))}
    assert paired=={'both':10,'A_only':0,'B_only':3,'neither':3}
    for key,expected in zip(ENDPOINTS,[-13.844086021505376,-6.5576446011228615,18.75,-6.25]):
        assert math.isclose(point[key],expected,abs_tol=1e-12),(key,point[key],expected)
    boundary_tests=checks()
    seed_sequence=np.random.SeedSequence(args.seed);children=seed_sequence.spawn(3)
    rng_dev,rng_internal,rng_external=[np.random.default_rng(c)for c in children]
    records=[];bootstrap_start=time.perf_counter();bootstrap_cpu=time.process_time()
    for iteration in range(1,args.replicates+1):
        d=dev.take(rng_dev.integers(0,len(dev),size=len(dev)))
        i=internal.take(rng_internal.integers(0,len(internal),size=len(internal)))
        e=external.take(rng_external.integers(0,len(external),size=len(external)))
        a_new,ra_new,at_a=calibrate(d.A);b_new,rb_new,at_b=calibrate(d.B)
        reranked=rank_at_budget(e,k)
        uniques={'development':len(set(d.ids.tolist())),'internal':len(set(i.ids.tolist())),
                 'external':len(set(e.ids.tolist()))}
        for route,ci,ce,taus,rr,dr,da in [
                (ROUTES[0],i,e,(ta,tb),reranked,(43,43),(baseA[2],baseB[2])),
                (ROUTES[1],internal,external,(a_new,b_new),baseline_ranked,(ra_new,rb_new),(at_a,at_b)),
                (ROUTES[2],i,e,(a_new,b_new),reranked,(ra_new,rb_new),(at_a,at_b))]:
            values=evaluate(ci,ce,taus,rr)
            values={'iteration':iteration,'route':route,'threshold_A':taus[0],'threshold_B':taus[1],
                    'development_reviews_A':dr[0],'development_reviews_B':dr[1],
                    'development_at_cutoff_A':da[0],'development_at_cutoff_B':da[1],
                    'unique_development':len(dev)if route==ROUTES[0]else uniques['development'],
                    'unique_internal':len(internal)if route==ROUTES[1]else uniques['internal'],
                    'unique_external':len(external)if route==ROUTES[1]else uniques['external'],**values}
            records.append(values)
    bootstrap_wall=time.perf_counter()-bootstrap_start;bootstrap_cpu=time.process_time()-bootstrap_cpu
    route_summaries=summarize(records,point)
    assert len(records)==3*args.replicates
    for offset in range(0,len(records),3):
        assert records[offset][ENDPOINTS[3]]==records[offset+2][ENDPOINTS[3]] or(
            math.isnan(records[offset][ENDPOINTS[3]])and math.isnan(records[offset+2][ENDPOINTS[3]]))
    resultdir=output/'results/bootstrap_stability';resultdir.mkdir(parents=True,exist_ok=True)
    csvpath=resultdir/'iterations.csv'
    with csvpath.open('w',newline='')as handle:
        writer=csv.DictWriter(handle,fieldnames=list(records[0]));writer.writeheader()
        for row in records:
            writer.writerow({key:('NA'if val is None or isinstance(val,float)and not math.isfinite(val)else val)
                             for key,val in row.items()})
    summary={'classification':plan['classification'],'source_commit':commit,
             'source_inputs_sha256':hashes,'protocol_sha256':plan_hash,
             'script_sha256':digest(Path(__file__).resolve()),'replicates_per_route':args.replicates,'seed':args.seed,
             'RNG':{'bit_generator':'PCG64','root_seed':args.seed,'SeedSequence_spawn_keys':{
                 label:list(c.spawn_key)for label,c in zip(('development','internal','external'),children)},
                 'common_draws_across_routes':'development draws shared R2/R3; test draws shared R1/R3; cohort streams independent'},
             'bootstrap_unit':'patient; every sampled draw retained including duplicates; A/B/quality paired',
             'ranking_rule':'descending risk, original CaseID string, draw-position replica index; exactly 50 draw records',
             'calibration_rule':'all risk ties grouped; abs(5R-N) minimized; fewer reviews if equally close; zero-review candidate included',
             'interval_method':'2.5th and 97.5th percentiles of valid replicates; NumPy quantile method=linear',
             'undefined_detection':'NA for zero low-quality denominator; no imputation',
             'direction_fraction_denominator':'jointly valid fixed and equal external contrasts; individual endpoint sign fractions use that endpoint valid count',
             'observed':point,'edge_case_checks':boundary_tests,'routes':route_summaries,
             'observed_external_low_quality_paired_table':paired,
             'original_paired_Newcombe_H3_ci95_pp':json.loads((frozen/'reference/primary.json').read_text())['contrasts']['H3']['ci95_pp'],
             'fixed_cutoff_empirical_support_constraint':'The observed A-only cell is zero. Route 1 fixed-cutoff patient resampling cannot create A-only detections and therefore B-minus-A is structurally >=0; its [0,40] pp percentile interval does not rule out a population A advantage or replace the original paired Newcombe interval [-4.28,+40.04] pp.',
             'runtime':{'started_utc':started,'bootstrap_wall_seconds':bootstrap_wall,'bootstrap_cpu_seconds':bootstrap_cpu,
                        'single_process':True,'BLAS_thread_environment':{k:os.environ[k]for k in('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS','BLIS_NUM_THREADS')},
                        'python':platform.python_version(),'numpy':np.__version__,'implementation':'independent code; no original study modules imported'},
             'iterations_csv_sha256':digest(csvpath),'iterations_csv_rows':len(records),
             'source_files_unchanged':all(digest(repo/p)==h for p,h in hashes.items()),
             'cautions':['Post hoc exploratory resampling of observed patients, not independent new patients.',
                         'Empirical sign/reversal fractions are not p-values, posterior probabilities or proof of method superiority.',
                         'Descriptive percentile intervals do not replace original Newcombe confidence intervals.',
                         'Risk-rank selections may split bootstrap duplicate ties by the stated stable rule; calibration ties remain grouped.',
                         'Observed A-only=0 means route 1 cannot generate A-only detections; its nonnegative fixed B-minus-A distribution is an empirical-support constraint, not evidence excluding an A advantage.',
                         'Route 2 equal-top50 is necessarily constant because original test cohorts remain fixed.']}
    assert summary['source_files_unchanged']
    assert digest(args.plan)==plan_hash,'Governing plan changed during computation.'
    render_figure(summary,output/'figures',args.replicates)
    summary['runtime'].update(completed_utc=datetime.now(timezone.utc).isoformat(),
                              total_wall_seconds=time.perf_counter()-start,total_cpu_seconds=time.process_time()-start_cpu,
                              peak_RSS_MiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024)
    write_report(summary,output/'reports/bootstrap_stability.md')
    (resultdir/'summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'observed_pp':{k:point[k]for k in ENDPOINTS},'routes':{
        route:{'original_reversal':route_summaries[route]['joint_direction_patterns']['original_direction_reversal'],
               'joint_valid':route_summaries[route]['joint_direction_patterns']['valid_replicates']}for route in ROUTES},
        'bootstrap_wall_seconds':bootstrap_wall,'total_wall_seconds':summary['runtime']['total_wall_seconds'],
        'iterations_csv':str(csvpath),'summary_json':str(resultdir/'summary.json')}))


if __name__=='__main__':main()
