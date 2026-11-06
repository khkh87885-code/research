#!/usr/bin/env python3
"""Independent count-based and full paired-bootstrap replay QA; no model inference."""
import os
for _k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[_k]='1'
import csv,json,math,hashlib,time
from pathlib import Path
from fractions import Fraction as F
from collections import Counter
from datetime import datetime,timezone
import numpy as np

B=Path('/workspace/bmt_cloud_validation');R=Path('/workspace/research_source')
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def cs(p):
 with p.open(encoding='utf-8-sig',newline='')as x:return list(csv.DictReader(x))
def close(a,b):
 if not math.isfinite(a)or not math.isfinite(b):return (math.isnan(a)and math.isnan(b))
 return abs(a-b)<1e-12

def calc(i,e,m,outcome):
 """Use cross-weighted counterfactual means to derive symmetric terms independently."""
 ans={};q=[];w=[];p=[]
 for cohort,data in [('internal',i),('external',e)]:
  eligible=data[:,1] if outcome=='detection' else np.ones(len(data),dtype=np.int64)
  den=np.bincount(data[:,0],weights=eligible,minlength=2)
  num=np.bincount(data[:,0],weights=eligible*data[:,2+m],minlength=2)
  rates=np.divide(num,den,out=np.full(2,np.nan),where=den>0)
  weights=den/den.sum() if den.sum()>0 else np.full(2,np.nan)
  overall=float(num.sum()/den.sum()) if den.sum()>0 else np.nan
  q.append(overall);w.append(weights);p.append(rates);ans[cohort+'_rate']=overall
  for s,label in enumerate(['benign','malignant']):
   ans[label+'.'+cohort+'_weight']=weights[s];ans[label+'.'+cohort+'_stratum_rate']=rates[s]
 cross_E_I=float(np.sum(w[1]*p[0]));cross_I_E=float(np.sum(w[0]*p[1]))
 c=.5*((q[1]-cross_I_E)+(cross_E_I-q[0]));r=.5*((q[1]-cross_E_I)+(cross_I_E-q[0]));common=.5*(w[0]+w[1])
 std_i=float(np.sum(common*p[0]));std_e=float(np.sum(common*p[1]));diff=q[1]-q[0]
 ans.update(overall_difference=diff,composition_associated=c,within_stratum_rate=r,standardized_internal_rate=std_i,standardized_external_rate=std_e,standardized_difference=std_e-std_i,identity_residual=c+r-diff,standardization_identity_residual=std_e-std_i-r)
 for s,label in enumerate(['benign','malignant']):
  ans[label+'.common_weight']=common[s];ans[label+'.composition_associated_term']=(w[1][s]-w[0][s])*.5*(p[1][s]+p[0][s]);ans[label+'.within_stratum_rate_term']=(p[1][s]-p[0][s])*common[s]
 return ans,{'internal':np.bincount(i[:,0],weights=i[:,1] if outcome=='detection'else np.ones(len(i)),minlength=2),'external':np.bincount(e[:,0],weights=e[:,1] if outcome=='detection'else np.ones(len(e)),minlength=2)}

t0=time.perf_counter();res=B/'results/case_mix_decomposition.json';boot=B/'results/case_mix_decomposition_bootstrap.csv';a=json.loads(res.read_text());source=cs(R/'reproducibility/records/validation_cases.csv');lock=json.loads((R/'reproducibility/study_lock.json').read_text());thresholds={m:lock['threshold_lock']['methods'][m]['threshold']for m in ['A','B']}
arrays={}
for split in ['internal_holdout','external_test']:
 rows=[x for x in source if x['split']==split]
 arrays[split]=np.asarray([[int(x['pathology']=='malignant'),int(float(x['dice_vs_reference'])<.7),int(float(x['risk_A'])>=thresholds['A']),int(float(x['risk_B'])>=thresholds['B'])]for x in rows],dtype=np.int64)
i=arrays['internal_holdout'];e=arrays['external_test'];point={};exact_checks={};summ=[]
# Separate exact rational derivation from raw cohort/stratum counts.
for m,method in enumerate(['A','B']):
 for outcome in ['detection','review_fraction']:
  k=method+'.'+outcome;z,_=calc(i,e,m,outcome);point[k]=z
  ws=[];ps=[];overall=[];dennums=[]
  for data in [i,e]:
   D=data[:,1]if outcome=='detection'else np.ones(len(data),dtype=np.int64)
   ds=[int(D[data[:,0]==s].sum())for s in [0,1]];ns=[int((D*data[:,2+m])[data[:,0]==s].sum())for s in [0,1]];ws.append([F(d,sum(ds))for d in ds]);ps.append([F(n,d)for n,d in zip(ns,ds)]);overall.append(F(sum(ns),sum(ds)));dennums.append({'denominators':ds,'numerators':ns})
  c=sum((ws[1][s]-ws[0][s])*(ps[1][s]+ps[0][s])/2 for s in [0,1]);rr=sum((ps[1][s]-ps[0][s])*(ws[1][s]+ws[0][s])/2 for s in [0,1]);difference=overall[1]-overall[0];common=[(ws[1][s]+ws[0][s])/2 for s in [0,1]];si=sum(common[s]*ps[0][s]for s in [0,1]);se=sum(common[s]*ps[1][s]for s in [0,1]);assert c+rr==difference and se-si==rr
  for metric,expected in z.items():assert close(float(a['results'][k]['statistics'][metric]['estimate']),float(expected)),(k,metric)
  exact_checks[k]={'counts_rederived_from_scores':dennums,'internal_weights':[str(v)for v in ws[0]],'external_weights':[str(v)for v in ws[1]],'common_weights':[str(v)for v in common],'overall_difference_exact':str(difference),'composition_associated_exact':str(c),'within_stratum_rate_exact':str(rr),'composition_plus_within_equals_overall_exact':True,'standardized_difference_equals_within_exact':True}
  summ.append({'method':method,'outcome':outcome,'overall_difference_pp':100*float(difference),'composition_associated_pp':100*float(c),'within_stratum_rate_pp':100*float(rr),'standardized_internal_percent':100*float(si),'standardized_external_percent':100*float(se)})
records=cs(boot);assert len(records)==20000
lookup={}
for row in records:
 key=(int(row['replicate']),row['method']+'.'+row['outcome']);assert key not in lookup;lookup[key]=row
assert {key[0]for key in lookup}==set(range(1,5001))
for r in range(1,5001):assert {k for rr,k in lookup if rr==r}==set(point)
metrics=list(next(iter(a['results'].values()))['statistics']);replayed={k:{metric:[]for metric in metrics}for k in point};max_diff=0.;mismatches=[];zero=Counter();rng=np.random.Generator(np.random.PCG64(20261107))
for rep in range(1,5001):
 ii=i[rng.integers(0,len(i),size=len(i))];ee=e[rng.integers(0,len(e),size=len(e))]
 for m,method in enumerate(['A','B']):
  for outcome in ['detection','review_fraction']:
   k=method+'.'+outcome;z,ds=calc(ii,ee,m,outcome);record=lookup[(rep,k)]
   if m==0:
    for co in ['internal','external']:
     for s,label in enumerate(['benign','malignant']):zero[(outcome,co,label)]+=int(ds[co][s]==0)
   for metric in metrics:
    value=float(z[metric]);replayed[k][metric].append(value);raw=record[metric];published=np.nan if raw=='NA'else float(raw)
    # Identity residual has equivalent alternative arithmetic order; compare at tolerance.
    if not close(value,published):mismatches.append((rep,k,metric,value,published))
    if math.isfinite(value)and math.isfinite(published):max_diff=max(max_diff,abs(value-published))
assert not mismatches,mismatches[:5]
valid={};max_ci_diff=0.
for k in point:
 valid[k]={}
 for metric,values in replayed[k].items():
  finite=np.asarray(values)[np.isfinite(values)];s=a['results'][k]['statistics'][metric];assert len(finite)==s['valid_replicates'];assert 5000-len(finite)==s['invalid_replicates'];ci=np.quantile(finite,[.025,.975],method='linear')if len(finite)else [np.nan,np.nan]
  for j,value in enumerate(ci):assert close(float(value),float(s['percentile_ci95'][j])),(k,metric,'CI')
  max_ci_diff=max(max_ci_diff,max(abs(float(ci[j])-s['percentile_ci95'][j])for j in [0,1]));valid[k][metric]={'valid':len(finite),'invalid':5000-len(finite)}
zero_out={o:{co:{s:zero[(o,cc,s)]for s in ['benign','malignant']}for co,cc in [('internal_holdout','internal'),('external_test','external')]}for o in ['detection','review_fraction']};assert zero_out==a['bootstrap']['zero_stratum_denominator_counts']
out={'audit_utc':datetime.now(timezone.utc).isoformat(),'check':'Independent raw-score count and paired-bootstrap replay of diagnostic composition/Kitagawa module','status':'PASS','method':'Point estimates use exact Fraction arithmetic on independently recomputed raw-score counts. Bootstrap draws replay PCG64 with the fixed seed, deriving aggregate composition and rate terms from cross-weighted means rather than importing the production function.','inputs_sha256':{'results_json':h(res),'bootstrap_csv':h(boot),'source_scores':h(R/'reproducibility/records/validation_cases.csv'),'protocol':h(B/'protocol/analysis_plan.json')},'thresholds':thresholds,'point_estimates':summ,'exact_count_checks':exact_checks,'bootstrap':{'replicates':5000,'rows':len(records),'seed':20261107,'all_replicate_method_outcome_keys_complete':True,'patient_replay':True,'all_exported_values_match_independent_replay_at_tolerance':True,'maximum_absolute_difference_raw_fraction':max_diff,'all_percentile_CIs_and_valid_counts_match':True,'maximum_absolute_percentile_ci_difference_raw_fraction':max_ci_diff,'zero_stratum_denominator_counts':zero_out,'valid_counts':valid},'notes':['Detection weights are the diagnostic composition among low-quality cases: internal 53/93 and 40/93; external 8/16 and 8/16. They are not all-patient diagnostic proportions.','One bootstrap replicate (2468) has no low-quality benign external case. Detection decomposition components and external standardized rates/differences are NA for both methods; overall rates and internal standardized rates remain defined.','A detection composition-associated component is negative (-1.615439237 pp), and the within-stratum-rate component is negative (-12.228646784 pp).','This is post hoc descriptive accounting, not causal attribution or removal of device/annotation confounding.','All calculations use archived scores; no model inference was run.'],'elapsed_seconds':time.perf_counter()-t0}
qa=B/'qa';qa.mkdir(exist_ok=True);(qa/'case_mix_decomposition_independent_check.json').write_text(json.dumps(out,indent=2)+'\n')
lines=['# Independent case-mix decomposition check','','**PASS.** Independently recomputed raw-score counts and exact rational arithmetic confirm all four original-record decompositions and direct-standardized differences. All 20,000 exported bootstrap rows match an independent replay of the 5,000 paired-patient draws at tolerance 1e-12, including all percentile intervals and NA/valid counts.','','| Method | Outcome | Overall E−I, pp | Composition-associated, pp | Within-stratum-rate, pp | Standardized internal, % | Standardized external, % |','|---|---|---:|---:|---:|---:|---:|']
for x in summ:lines.append(f"| {x['method']} | {x['outcome']} | {x['overall_difference_pp']:.6f} | {x['composition_associated_pp']:.6f} | {x['within_stratum_rate_pp']:.6f} | {x['standardized_internal_percent']:.6f} | {x['standardized_external_percent']:.6f} |")
lines.extend(['','Exact Fraction identities hold: composition-associated + within-stratum-rate = overall external − internal; direct-standardized external − internal = within-stratum-rate.','',*['- '+x for x in out['notes']],'',f"Maximum bootstrap value discrepancy: {max_diff:.3g} raw fraction. Maximum percentile-limit discrepancy: {max_ci_diff:.3g}. Actual independent-check elapsed time: {out['elapsed_seconds']:.6f} seconds."])
(qa/'case_mix_decomposition_independent_check.md').write_text('\n'.join(lines)+'\n');print(json.dumps({'status':'PASS','point_estimates':summ,'elapsed_seconds':out['elapsed_seconds'],'maximum_bootstrap_difference':max_diff,'maximum_ci_difference':max_ci_diff},indent=2))
