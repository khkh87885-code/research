#!/usr/bin/env python3
"""Post hoc symmetric Kitagawa accounting; fixed protocol, no SAM inference.

Requires Python >=3.10, numpy, matplotlib, openpyxl.
Example:
  python scripts/case_mix_decomposition.py --source-root /path/to/repository \
    --protocol protocol/analysis_plan.json --output-root .
Outputs use raw fractions; *_pp and *_percent are explicitly scaled.
"""
from __future__ import annotations
import os
import time
_PROCESS_START = time.perf_counter()
# These assignments deliberately precede all numerical-library imports.
for _name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS',
              'VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS','BLIS_NUM_THREADS'):
    os.environ[_name] = '1'
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import openpyxl

STRATA = ('benign', 'malignant')
COHORTS = ('internal_holdout', 'external_test')
METHODS = ('A', 'B')
OUTCOMES = ('detection', 'review_fraction')
SUMMARY_METRICS = ('internal_rate','external_rate','overall_difference',
    'composition_associated','within_stratum_rate','standardized_internal_rate',
    'standardized_external_rate','standardized_difference')


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1024*1024), b''): h.update(b)
    return h.hexdigest()


def read_csv(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def json_safe(x):
    if isinstance(x, dict): return {str(k): json_safe(v) for k,v in x.items()}
    if isinstance(x, (tuple, list)): return [json_safe(v) for v in x]
    if isinstance(x, np.ndarray): return json_safe(x.tolist())
    if isinstance(x, (np.integer,)): return int(x)
    if isinstance(x, (float, np.floating)):
        return float(x) if np.isfinite(x) else None
    return x


def git_value(root, *args):
    return subprocess.check_output(['git','-C',str(root),*args], text=True).strip()


def load_and_verify(root, protocol):
    used = {
      'scores': 'reproducibility/records/validation_cases.csv',
      'internal_manifest': 'reproducibility/manifests/busbra_internal_holdout.csv',
      'external_manifest': 'reproducibility/manifests/breast_external.csv',
      'study_lock': 'reproducibility/study_lock.json',
      'v7_stratum_audit': 'submission/bmt_v7/Audit/pathology_audit.json',
      'busbra_metadata': 'data/raw/BUS-BRA/BUSBRA/bus_data.csv',
      'breast_metadata': 'data/raw/BrEaST/BrEaST-Lesions-USG-clinical-data-Dec-15-2023.xlsx',
    }
    for p in used.values():
        if not (root/p).is_file(): raise FileNotFoundError(root/p)
    head = git_value(root,'rev-parse','HEAD')
    if head != protocol['source_commit']:
        raise ValueError(f"Source HEAD {head} does not match protocol {protocol['source_commit']}")
    audit = json.loads((root/used['v7_stratum_audit']).read_text())
    lock = json.loads((root/used['study_lock']).read_text())
    thresholds = {m: float(lock['threshold_lock']['methods'][m]['threshold']) for m in METHODS}
    cutoff = float(lock['threshold_lock']['quality_reference']['cutoff'])
    assert cutoff == .70 and audit['low_quality_definition']['cutoff'] == cutoff
    assert thresholds == audit['unchanged_thresholds']
    hashes = {p: sha256(root/p) for p in used.values()}
    for p,digest in audit['source_inputs_sha256'].items():
        if p in hashes: assert hashes[p] == digest, ('audit_input_hash',p)
    scores = read_csv(root/used['scores'])
    manifests = {c: read_csv(root/used[k]) for c,k in zip(COHORTS,('internal_manifest','external_manifest'))}
    busrows = read_csv(root/used['busbra_metadata'])
    busmap = {r['ID']:r for r in busrows}
    assert len(busmap) == len(busrows)
    workbook = openpyxl.load_workbook(root/used['breast_metadata'],read_only=True,data_only=True)
    sheet = workbook['BrEaST-Lesions-USG clinical dat']
    rows = sheet.iter_rows(values_only=True)
    header = list(next(rows))
    breastmap = {}
    for row in rows:
        d=dict(zip(header,row))
        if d['CaseID'] is None: continue
        key=int(d['CaseID'])
        assert key not in breastmap
        breastmap[key]=d
    workbook.close()
    def key(r): return (r['dataset'],int(r['patient_id']),r['image_id'])
    assert len({key(r) for r in scores}) == len(scores)
    assert len(scores) == 1103
    arrays,checks = {},{}
    for c in COHORTS:
        rows = [r for r in scores if r['split'] == c]
        man = {key(r):r for r in manifests[c]}
        assert len(man) == len(manifests[c])
        assert len(rows) == len(man) == {'internal_holdout':851,'external_test':252}[c]
        assert {key(r) for r in rows} == set(man)
        assert len({(r['dataset'],int(r['patient_id'])) for r in rows}) == len(rows)
        data=[]
        for r in rows:
            mr=man[key(r)]
            label=r['pathology'].lower().strip()
            assert label in STRATA and label == mr['pathology'].lower().strip()
            if c == 'internal_holdout':
                raw=busmap[r['image_id']]
                assert int(raw['Case']) == int(r['patient_id'])
                assert raw['Pathology'].lower().strip() == label
            else:
                raw=breastmap[int(r['patient_id'])]
                assert raw['Classification'].lower().strip() == label
                assert Path(raw['Image_filename']).stem == r['image_id']
                assert Path(raw['Image_filename']).name == Path(mr['image_path']).name
                assert Path(raw['Mask_tumor_filename']).name == Path(mr['mask_path']).name
            assert r['status'] == 'scored'
            low=int(float(r['dice_vs_reference']) < cutoff)
            assert low == int(r['low_quality'])
            alerts=[int(float(r[f'risk_{m}']) >= thresholds[m]) for m in METHODS]
            assert alerts == [int(r[f'alert_{m}']) for m in METHODS]
            data.append([STRATA.index(label),low,*alerts])
        arrays[c]=np.asarray(data,dtype=np.int8)
        cc=count_cohort(arrays[c])
        checks[c]={}
        for s,name in enumerate(STRATA):
            checks[c][name]={}
            for j,m in enumerate(METHODS):
                actual={'N':int(cc['N'][s]),'low_quality':int(cc['low'][s]),
                        'review_count':int(cc['reviews'][j,s]),'TP':int(cc['tp'][j,s])}
                expected=audit['stratified'][c][name][m]
                assert all(actual[k] == expected[k] for k in actual), (c,name,m,actual,expected)
                checks[c][name][m]=actual
    return arrays,{'source_commit':head,'source_branch':git_value(root,'branch','--show-current'),
        'source_status_before':git_value(root,'status','--porcelain'),
        'audit_source_commit':audit['source_commit'],'input_sha256':hashes,
        'thresholds':thresholds,'quality_cutoff':cutoff,'stratum_counts':checks,
        'checks':'Score/manifest/official-metadata labels, patient uniqueness within each dataset namespace, quality labels, locked decisions and all v7 stratum counts matched exactly.',
        'patient_id_scope':'Patient identifiers are dataset-local. No claim of independently established cross-dataset patient identity exclusion is made.',
        'label_scope':'Dataset-reported benign/malignant classification; BrEaST includes follow-up-confirmed cases, so not all diagnoses are histopathologically confirmed.'}


def count_cohort(data):
    diag=data[:,0]
    low=data[:,1]
    return {'N':np.bincount(diag,minlength=2).astype(float),
            'low':np.bincount(diag,weights=low,minlength=2),
            'reviews':np.asarray([np.bincount(diag,weights=data[:,j+2],minlength=2) for j in range(2)]),
            'tp':np.asarray([np.bincount(diag,weights=data[:,j+2]*low,minlength=2) for j in range(2)])}


def decompose(internal, external, method_index, outcome):
    den_key='low' if outcome == 'detection' else 'N'
    num_key='tp' if outcome == 'detection' else 'reviews'
    di,de=internal[den_key],external[den_key]
    ni,ne=internal[num_key][method_index],external[num_key][method_index]
    def divide(n,d):
        return np.divide(n,d,out=np.full(2,np.nan),where=(d>0))
    pi,pe=divide(ni,di),divide(ne,de)
    wi=di/di.sum() if di.sum()>0 else np.full(2,np.nan)
    we=de/de.sum() if de.sum()>0 else np.full(2,np.nan)
    common=(wi+we)/2
    comp=(we-wi)*(pe+pi)/2
    within=(pe-pi)*common
    ri=float(ni.sum()/di.sum()) if di.sum()>0 else np.nan
    re=float(ne.sum()/de.sum()) if de.sum()>0 else np.nan
    si=float(np.sum(common*pi));se=float(np.sum(common*pe))
    c=float(np.sum(comp));r=float(np.sum(within));d=re-ri
    result={'internal_rate':ri,'external_rate':re,'overall_difference':d,
        'composition_associated':c,'within_stratum_rate':r,
        'standardized_internal_rate':si,'standardized_external_rate':se,
        'standardized_difference':se-si,'identity_residual':c+r-d,
        'standardization_identity_residual':(se-si)-r}
    for s,name in enumerate(STRATA):
        for k,v in [('internal_weight',wi[s]),('external_weight',we[s]),
                    ('common_weight',common[s]),('internal_stratum_rate',pi[s]),
                    ('external_stratum_rate',pe[s]),('composition_associated_term',comp[s]),
                    ('within_stratum_rate_term',within[s])]: result[f'{name}.{k}']=float(v)
    return result


def estimate_interval(values,point):
    finite=np.isfinite(values)
    valid=values[finite]
    ci=np.quantile(valid,[.025,.975],method='linear') if valid.size else [np.nan,np.nan]
    return {'estimate':point,'percentile_ci95':ci,'valid_replicates':int(valid.size),
        'invalid_replicates':int(len(values)-valid.size)}


def fmt_ci(stat, scale=100):
    p=stat['estimate'];lo,hi=stat['percentile_ci95']
    def f(v):return 'NA' if not np.isfinite(v) else f'{scale*v:.2f}'
    return f'{f(p)} [{f(lo)}, {f(hi)}]'


def export_plot(results,path):
    colors={'A':'#137c88','B':'#c46028'}
    fig,axes=plt.subplots(1,2,figsize=(12.8,5.6),layout='constrained')
    labels=[]
    for m in METHODS:
        labels.extend([f'{m}: overall E − I',f'{m}: composition-associated',f'{m}: within-stratum-rate'])
    for ax,outcome,title in zip(axes,OUTCOMES,('Low-quality detection','Review fraction')):
        row=0
        for m in METHODS:
            rr=results[f'{m}.{outcome}']
            for metric in ('overall_difference','composition_associated','within_stratum_rate'):
                stat=rr['statistics'][metric];p=100*stat['estimate'];lo,hi=100*np.asarray(stat['percentile_ci95'])
                ax.plot([lo,hi],[row,row],color=colors[m],lw=2,solid_capstyle='round')
                ax.scatter([p],[row],s=42,color=colors[m],zorder=3)
                row+=1
        ax.axvline(0,color='#777777',lw=.8,ls='--')
        ax.set(yticks=np.arange(6),yticklabels=labels,xlabel='Percentage points (external − internal)',title=title,ylim=(5.6,-.6))
        ax.grid(axis='x',color='#e4e8e9',lw=.7)
        for spine in ('top','right'):ax.spines[spine].set_visible(False)
        ax.tick_params(axis='y',length=0,labelsize=9)
    fig.suptitle('Diagnostic composition and symmetric Kitagawa accounting',fontsize=14)
    fig.supxlabel('Points: original records. Lines: percentile 95% intervals, 5,000 paired-patient bootstrap draws.\nWithin-stratum-rate term equals the direct-standardized difference; descriptive, not causal.',fontsize=9)
    fig.savefig(str(path)+'.png',dpi=300,facecolor='white')
    fig.savefig(str(path)+'.pdf',facecolor='white')
    plt.close(fig)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root',type=Path,required=True)
    parser.add_argument('--protocol',type=Path,required=True)
    parser.add_argument('--output-root',type=Path,required=True)
    args=parser.parse_args()
    root=args.source_root.resolve();out=args.output_root.resolve()
    for folder in ('results','figures','reports'): (out/folder).mkdir(parents=True,exist_ok=True)
    protocol=json.loads(args.protocol.read_text())
    plan=protocol['decomposition']
    reps=int(plan['bootstrap_replicates']);seed=int(plan['seed'])
    assert reps == 5000 and seed == 20261107
    start_utc=datetime.now(timezone.utc).isoformat()
    arrays,provenance=load_and_verify(root,protocol)
    provenance['protocol_sha256']=sha256(args.protocol)
    provenance['script_sha256']=sha256(Path(__file__).resolve())
    provenance['protocol_file']=str(args.protocol.resolve())
    provenance['source_root']=str(root)
    counts={c:count_cohort(arrays[c]) for c in COHORTS}
    points={f'{m}.{o}':decompose(counts[COHORTS[0]],counts[COHORTS[1]],j,o)
            for j,m in enumerate(METHODS) for o in OUTCOMES}
    metrics=list(next(iter(points.values())).keys())
    for p in points.values():
        assert abs(p['identity_residual']) < 1e-12
        assert abs(p['standardization_identity_residual']) < 1e-12
    draws={key:np.full((reps,len(metrics)),np.nan) for key in points}
    zeros={o:{c:{s:0 for s in STRATA} for c in COHORTS} for o in OUTCOMES}
    rng=np.random.Generator(np.random.PCG64(seed))
    t0=time.perf_counter()
    for b in range(reps):
        sampled={}
        for c in COHORTS:
            data=arrays[c]
            idx=rng.integers(0,len(data),size=len(data))
            sampled[c]=count_cohort(data[idx])
        for o in OUTCOMES:
            dk='low' if o == 'detection' else 'N'
            for c in COHORTS:
                for j,s in enumerate(STRATA):zeros[o][c][s]+=int(sampled[c][dk][j] == 0)
            for j,m in enumerate(METHODS):
                vals=decompose(sampled[COHORTS[0]],sampled[COHORTS[1]],j,o)
                draws[f'{m}.{o}'][b]=[vals[k] for k in metrics]
    bootstrap_seconds=time.perf_counter()-t0
    results={}
    for key,point in points.items():
        statistics={metric:estimate_interval(draws[key][:,j],point[metric]) for j,metric in enumerate(metrics)}
        residual=draws[key][:,metrics.index('identity_residual')]
        stdresidual=draws[key][:,metrics.index('standardization_identity_residual')]
        assert np.max(np.abs(residual[np.isfinite(residual)]),initial=0)<1e-12
        assert np.max(np.abs(stdresidual[np.isfinite(stdresidual)]),initial=0)<1e-12
        results[key]={'statistics':statistics,
          'bootstrap_max_absolute_identity_residual':float(np.max(np.abs(residual[np.isfinite(residual)]),initial=0)),
          'bootstrap_max_absolute_standardization_residual':float(np.max(np.abs(stdresidual[np.isfinite(stdresidual)]),initial=0))}
    # Raw paired draw export permits independent interval/identity verification.
    with (out/'results/case_mix_decomposition_bootstrap.csv').open('w',newline='') as f:
        writer=csv.writer(f);writer.writerow(['replicate','method','outcome',*metrics])
        for b in range(reps):
            for key in points:
                method,outcome=key.split('.',1)
                writer.writerow([b+1,method,outcome,*['NA' if not np.isfinite(v) else repr(float(v)) for v in draws[key][b]]])
    headers=['method','outcome']
    for metric in SUMMARY_METRICS:headers += [metric,metric+'_ci95_lower',metric+'_ci95_upper',metric+'_valid_replicates']
    with (out/'results/case_mix_decomposition.csv').open('w',newline='')as f:
        writer=csv.DictWriter(f,fieldnames=headers);writer.writeheader()
        for key,rr in results.items():
            method,outcome=key.split('.',1);row={'method':method,'outcome':outcome}
            for metric in SUMMARY_METRICS:
                stat=rr['statistics'][metric]
                row.update({metric:stat['estimate'],metric+'_ci95_lower':stat['percentile_ci95'][0],
                    metric+'_ci95_upper':stat['percentile_ci95'][1],metric+'_valid_replicates':stat['valid_replicates']})
            writer.writerow(row)
    with (out/'results/case_mix_decomposition_strata.csv').open('w',newline='')as f:
        writer=csv.writer(f);writer.writerow(['method','outcome','stratum','cohort','denominator','numerator','weight','common_weight','stratum_rate','composition_associated_term','within_stratum_rate_term'])
        for j,m in enumerate(METHODS):
            for o in OUTCOMES:
                p=points[f'{m}.{o}'];dk='low' if o == 'detection' else 'N';nk='tp' if o == 'detection' else 'reviews'
                for si,s in enumerate(STRATA):
                    for c,prefix in zip(COHORTS,('internal','external')):
                        writer.writerow([m,o,s,c,int(counts[c][dk][si]),int(counts[c][nk][j,si]),p[f'{s}.{prefix}_weight'],p[f'{s}.common_weight'],p[f'{s}.{prefix}_stratum_rate'],p[f'{s}.composition_associated_term'],p[f'{s}.within_stratum_rate_term']])
    export_plot(results,out/'figures/case_mix_decomposition')
    env={name:os.environ[name] for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS','BLIS_NUM_THREADS')}
    resource={'thread_environment':env,'python':sys.version,'numpy':np.__version__,'matplotlib':matplotlib.__version__,'openpyxl':openpyxl.__version__,'platform':platform.platform()}
    for name in ('cpu.max','memory.max'):
        path=Path('/sys/fs/cgroup')/name
        resource[name]=path.read_text().strip() if path.exists() else None
    try:
        import threadpoolctl
        resource['observed_threadpools']=threadpoolctl.threadpool_info()
    except ImportError:resource['observed_threadpools']='threadpoolctl unavailable; thread environment recorded'
    elapsed=time.perf_counter()-_PROCESS_START
    payload={'analysis':'post hoc diagnostic-composition standardization and symmetric Kitagawa decomposition',
      'started_utc':start_utc,'completed_utc':datetime.now(timezone.utc).isoformat(),
      'provenance':provenance,'design':plan,
      'direction':'external minus internal','rate_units':'raw fraction; multiply rates by 100 for percent and rate differences/components by 100 for percentage points',
      'bootstrap':{'replicates':reps,'seed':seed,'generator':'NumPy PCG64',
        'resampling':'Independently resample patients within internal then external in each repetition; A/B, quality and diagnosis kept paired. CSV row order retained.',
        'weights':'Recomputed per draw; detection weights use low-quality denominators, review weights use all-patient denominators.',
        'interval':'Unadjusted descriptive percentile 95%, NumPy linear quantiles over finite replicates only.',
        'zero_denominators':'NA; undefined stratum rates propagate to dependent components and standardized rates, even with zero weight; overall rate is valid if total denominator is positive.',
        'zero_stratum_denominator_counts':zeros},
      'results':results,'counts':counts,
      'runtime':{'bootstrap_seconds':bootstrap_seconds,'process_elapsed_seconds_through_exports':elapsed},
      'resources':resource,
      'interpretation_limits':['Post hoc descriptive accounting, not causal attribution. No percent-explained measures are reported.',
        'Two diagnostic strata cannot remove acquisition/device, annotation or other confounding.',
        'Only 16 external low-quality cases inform detection; bootstrap creates no independent new patients.',
        'Percentile intervals do not replace the original H1–H3 Newcombe intervals; a CI crossing zero does not establish equivalence.',
        'No development recalibration, model training or inference was run; no source manuscript or protocol was changed.']}
    lines=['# Case-mix standardization and symmetric Kitagawa accounting','',
      'Post hoc descriptive analysis of the fixed locked thresholds. Source main: `'+provenance['source_commit']+'`. No SAM model was loaded or run.','',
      '## Inputs and denominators','',provenance['checks'],provenance['label_scope'],
      'Internal: 851 patients, 93 low-quality masks (53 benign / 40 malignant). External: 252 patients, 16 low-quality masks (8 / 8). Detection weights are diagnostic shares among low-quality cases; review weights are shares among all cases. Identifiers are dataset-local.','',
      'Detection common benign/malignant weights: '+', '.join(f"{points['A.detection'][s+'.common_weight']:.8f}"for s in STRATA)+'.',
      'Review common benign/malignant weights: '+', '.join(f"{points['A.review_fraction'][s+'.common_weight']:.8f}"for s in STRATA)+'.','',
      '## Original records with bootstrap intervals','',
      'Values in the next table are percentage points [percentile 95% interval]. Direction is external minus internal.','',
      '| Method | Outcome | Overall difference | Composition-associated | Within-stratum-rate / standardized difference | Valid draws: overall / components |',
      '|---|---|---:|---:|---:|---:|']
    for key,rr in results.items():
        m,o=key.split('.',1);ss=rr['statistics']
        lines.append(f"| {m} | {o} | {fmt_ci(ss['overall_difference'])} | {fmt_ci(ss['composition_associated'])} | {fmt_ci(ss['within_stratum_rate'])} | {ss['overall_difference']['valid_replicates']} / {ss['within_stratum_rate']['valid_replicates']} |")
    lines += ['','Rates below are percent [percentile 95% interval], using the same recomputed common diagnostic weights in each draw.','',
      '| Method | Outcome | Observed internal | Observed external | Standardized internal | Standardized external |',
      '|---|---|---:|---:|---:|---:|']
    for key,rr in results.items():
        m,o=key.split('.',1);ss=rr['statistics']
        lines.append('| '+m+' | '+o+' | '+' | '.join(fmt_ci(ss[x]) for x in ('internal_rate','external_rate','standardized_internal_rate','standardized_external_rate'))+' |')
    lines += ['','## Accounting identities and resampling','',
      'For every method/outcome: C = Σ(wE−wI)(pE+pI)/2; R = Σ(pE−pI)(wE+wI)/2; D = external−internal = C+R. Common weights w*=(wE+wI)/2 give standardized external−internal = R. These are algebraic identities, not causal models.','',
      '5000 patient-bootstrap repetitions; PCG64 seed 20261107. Cohorts were independently resampled, with the same sampled patient indices retaining A/B, quality and diagnosis. Stratum weights and rates were recalculated in every repetition. Development calibration was not resampled in this module. Intervals use finite repetitions and unadjusted percentile limits. No missing denominator was filled.','',
      'Zero stratum-denominator draws: `'+json.dumps(zeros)+'`. Overall rates can remain estimable when a stratum-specific decomposition is undefined. Each statistic\'s valid and invalid counts are in JSON and summary CSV.','',
      'Maximum absolute bootstrap identity residuals: '+str(max(rr['bootstrap_max_absolute_identity_residual'] for rr in results.values()))+' (raw fractions); standardized-difference identity: '+str(max(rr['bootstrap_max_absolute_standardization_residual'] for rr in results.values()))+'.','',
      '## Interpretation','',
      'For detection, composition-associated terms refer specifically to the benign/malignant label composition of the low-quality subset, not the diagnostic composition of the full cohorts. A has negative composition-associated and within-stratum-rate terms; their sum is the observed negative overall detection difference. B has a negative composition-associated term and positive within-stratum-rate term. For review fractions, composition refers to the full-cohort diagnostic shares; both methods have a positive composition-associated term and a negative within-stratum-rate term. These signed accounting terms describe the observed two-stratum mixtures and do not identify causes.','',
      'Diagnostic standardization does not eliminate device/acquisition, reference-annotation or other confounding. External detection relies on 16 low-quality masks. Bootstrap intervals do not supply new patients or replace the original prespecified Newcombe intervals; zero-crossing does not establish equivalence.','',
      '## Runtime, resources and files','',
      f'Actual 5000-draw bootstrap time: {bootstrap_seconds:.6f} seconds. Actual process elapsed time through data verification, CSV exports and PNG/PDF rendering: {elapsed:.6f} seconds. The final JSON/Markdown write is excluded from that endpoint.',
      'Numerical thread settings: all 1. cgroup CPU quota: `'+str(resource['cpu.max'])+'`; memory limit: `'+str(resource['memory.max'])+'` bytes. Observed threadpools and package versions are in JSON.','',
      'Portable entry point: `scripts/case_mix_decomposition.py`; results: `results/case_mix_decomposition.json`, `.csv`, `_strata.csv`, `_bootstrap.csv`; figures: `figures/case_mix_decomposition.png` and `.pdf`. Input hashes, script hash and protocol hash are in JSON.','',
      'The v7 stratum audit was created at an earlier source commit; its relevant input hashes and counts match the current source exactly. Source manuscripts and the fixed protocol were not edited.','',
      '## SHA-256 inputs','',
      '| Input | SHA-256 |','|---|---|']
    for p,h in provenance['input_sha256'].items():lines.append(f'| `{p}` | `{h}` |')
    lines += [f"| protocol | `{provenance['protocol_sha256']}` |",f"| executable script | `{provenance['script_sha256']}` |",'']
    (out/'results/case_mix_decomposition.json').write_text(json.dumps(json_safe(payload),ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    (out/'reports/case_mix_decomposition.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({'status':'completed','bootstrap_seconds':bootstrap_seconds,
        'process_elapsed_seconds_through_exports':elapsed,'results':{key:{metric:json_safe(rr['statistics'][metric]) for metric in ('overall_difference','composition_associated','within_stratum_rate')} for key,rr in results.items()}},ensure_ascii=False,allow_nan=False))

if __name__ == '__main__':main()
