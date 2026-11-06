#!/usr/bin/env python3
"""Independent, read-only numerical audit of the frozen BMT study records.

No study helper is imported. Newcombe paired method 10 is independently
implemented from section 5 of Newcombe (1998), Stat Med 17:2635-2650 and checked
against published Table III examples. Outputs never overwrite source records.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import platform
import subprocess
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
from statistics import NormalDist

from PIL import Image

Z = NormalDist().inv_cdf(0.975)
METHODS = ('A', 'B')


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def score_limits(events, denominator):
    if denominator == 0:
        return None
    # Algebraic Wilson roots; independent of the archived helper's implementation.
    discriminant = Z * math.sqrt(Z * Z + 4 * events * (1 - events / denominator))
    root_sum = 2 * events + Z * Z
    divisor = 2 * (denominator + Z * Z)
    return [(root_sum - discriminant) / divisor,
            (root_sum + discriminant) / divisor]


def difference(first_x, first_n, second_x, second_n, rho=0.0):
    p, q = first_x / first_n, second_x / second_n
    pl, pu = score_limits(first_x, first_n)
    ql, qu = score_limits(second_x, second_n)
    lower_radius = math.sqrt((p-pl)**2 + (qu-q)**2 - 2*rho*(p-pl)*(qu-q))
    upper_radius = math.sqrt((pu-p)**2 + (q-ql)**2 - 2*rho*(pu-p)*(q-ql))
    return {'difference_pp': 100*(p-q),
            'ci95_pp': [100*(p-q-lower_radius), 100*(p-q+upper_radius)]}


def paired_interval(e, f, g, h):
    """First=B, second=A: e=both, f=B-only, g=A-only, h=neither."""
    n = e+f+g+h
    product = (e+f)*(g+h)*(e+g)*(f+h)
    numerator = e*h-f*g
    if numerator > 0:
        numerator = max(numerator-n/2, 0)
    rho = numerator/math.sqrt(product) if product else 0.0
    answer = difference(e+f,n,e+g,n,rho)
    answer.update(paired_counts={'both':e,'B_only':f,'A_only':g,'neither':h},
                  corrected_phi=rho)
    return answer


def benchmark_paired():
    examples = [
        ((36,12,2,0), [0.0569,0.3404]),
        ((20,12,2,16), [0.0562,0.3292]),
        ((18,12,2,18), [0.0562,0.3290]),
        ((35,14,0,1), [0.1461,0.4175]),
        ((53,0,0,1), [-0.0729,0.0729]),
        ((27,0,0,27), [-0.0351,0.0351]),
    ]
    results=[]
    for cells, expected in examples:
        calculated=[x/100 for x in paired_interval(*cells)['ci95_pp']]
        passed=all(abs(a-b)<=0.000051 for a,b in zip(calculated,expected))
        assert passed, (cells, calculated, expected)
        results.append({'cells_e_f_g_h':cells,'published_ci95':expected,
                        'calculated_ci95':calculated,'agrees_at_published_precision':passed})
    return results


def fraction(events, denominator):
    return {'events':events,'denominator':denominator,
            'fraction':events/denominator if denominator else None,
            'ci95':score_limits(events,denominator)}


def counts(rows, threshold, cutoff):
    low=[float(r['dice_vs_reference'])<cutoff for r in rows]
    reviewed=[float(r[threshold[0]])>=threshold[1] for r in rows]
    tp=sum(a and b for a,b in zip(low,reviewed))
    fp=sum(not a and b for a,b in zip(low,reviewed))
    fn=sum(a and not b for a,b in zip(low,reviewed))
    tn=sum(not a and not b for a,b in zip(low,reviewed))
    n=len(rows)
    assert tp+fp+fn+tn==n
    return {'N':n,'F':sum(low),'R':sum(reviewed),'TP':tp,'FP':fp,'TN':tn,'FN':fn,
            'sensitivity':fraction(tp,tp+fn),'specificity':fraction(tn,tn+fp),
            'ppv':fraction(tp,tp+fp),'npv':fraction(tn,tn+fn),
            'review':fraction(tp+fp,n),'misses_per_100':100*fn/n}


def pairs(rows, threshold, cutoff):
    combinations=Counter((float(r['risk_B'])>=threshold['B'],
                          float(r['risk_A'])>=threshold['A'])
                         for r in rows if float(r['dice_vs_reference'])<cutoff)
    return paired_interval(combinations[True,True],combinations[True,False],
                           combinations[False,True],combinations[False,False])


def assert_close(got, expected, name, checked):
    if isinstance(expected, (list,tuple)):
        assert len(got)==len(expected),name
        for idx,(g,e) in enumerate(zip(got,expected)):
            assert_close(g,e,f'{name}[{idx}]',checked)
    elif isinstance(expected, (int,float)):
        assert math.isclose(got,expected,rel_tol=0,abs_tol=1e-11),(name,got,expected)
    else:
        assert got==expected,(name,got,expected)
    checked.append(name)


def validate_raw(source, manifests, lock):
    summary={}
    selected_digests=[]
    for split,rows in manifests.items():
        counters=Counter()
        changed_alpha=[]
        for row in rows:
            root=source/'data/raw'/('BUS-BRA' if row['dataset']=='BUS-BRA' else 'BrEaST')
            image=root/row['image_path']; mask=root/row['mask_path']
            assert image.is_file() and mask.is_file()
            ih,mh=sha256(image),sha256(mask)
            if row.get('image_sha256'):
                assert ih==row['image_sha256'] and mh==row['mask_sha256']
                counters['manifest_hashes_verified']+=2
            selected_digests.append({'split':split,'patient_id':row['patient_id'],
                                     'image_sha256':ih,'mask_sha256':mh})
            size=int(row['width']),int(row['height'])
            with Image.open(image) as im:
                assert im.size==size
                if row['dataset']=='BrEaST':
                    a=im.convert('RGBA')
                    b=Image.new('RGBA',a.size,(0,0,0,255))
                    composite=Image.alpha_composite(b,a).convert('RGB')
                    if im.convert('RGB').tobytes()!=composite.tobytes():
                        changed_alpha.append(int(row['patient_id']))
            with Image.open(mask) as m:
                assert m.size==size
                assert m.convert('1').getbbox() is not None
            counters['pairs_readable_same_size_nonempty_reference']+=1
        summary[split]=dict(counters)
        if split=='external_test':
            assert sorted(changed_alpha)==sorted(lock['external_alpha_changed_ids'])
            summary[split]['alpha_changed_ids']=sorted(changed_alpha)
    return summary,selected_digests


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',type=Path,default=Path('/workspace/research_source'))
    parser.add_argument('--output',type=Path,default=Path('/workspace/bmt_revision/evidence'))
    args=parser.parse_args();source=args.source;out=args.output
    out.mkdir(parents=True,exist_ok=True)
    repro=source/'reproducibility';lock=read_json(repro/'study_lock.json')
    original_primary=read_json(repro/'reference/primary.json')
    original_supp=read_json(repro/'reference/supplementary.json')
    checked=[]
    validation_receipt=read_json(source/'experiments/formal_validation/validation_summary.json')
    lock_time=datetime.fromisoformat(lock['threshold_lock']['locked_at'])
    test_start=datetime.fromisoformat(validation_receipt['started_at'])
    assert lock_time<test_start
    integrity={str(p):sha256(repro/p) for p in lock['files_sha256']}
    for name,expected in lock['files_sha256'].items():
        assert integrity[name]==expected,(name,integrity[name],expected)
    manifests={s:read_csv(repro/c['manifest']) for s,c in lock['cohorts'].items()}
    for s,rows in manifests.items():
        assert len(rows)==lock['cohorts'][s]['count']==len({r['patient_id'] for r in rows})
    assert {r['patient_id'] for r in manifests['development']}.isdisjoint(
           r['patient_id'] for r in manifests['internal_holdout'])
    development=read_csv(repro/'records/development_cases.csv')
    for r in development:
        r.update(dataset='BUS-BRA',split='development')
        for m in METHODS:r[f'alert_{m}']=r[f'candidate_alert_{m}']
    tests=read_csv(repro/'records/validation_cases.csv')
    groups={'development':development,
            'internal_holdout':[r for r in tests if r['split']=='internal_holdout'],
            'external_test':[r for r in tests if r['split']=='external_test']}
    threshold={m:lock['threshold_lock']['methods'][m]['threshold'] for m in METHODS}
    recalibration={}
    for split,rows in groups.items():
        assert len(rows)==len(manifests[split])
        keys=lambda rr:sorted((r['patient_id'],r['image_id'],r['pathology']) for r in rr)
        assert keys(rows)==keys(manifests[split])
        for r in rows:
            assert r['status']=='scored'
            dice=float(r['dice_vs_reference']);assert 0<=dice<=1
            assert int(r['low_quality'])==int(dice<0.7)
            assert math.isclose(float(r['risk_A']),1-float(r['sam_predicted_iou']),abs_tol=1e-15)
            perturb=[float(r[f'dice_shift_{d}']) for d in ('left','right','up','down')]
            assert all(0<=x<=1 for x in perturb)
            assert math.isclose(float(r['risk_B']),1-sum(perturb)/4,abs_tol=1e-15)
            assert all(int(r[f'alert_{m}'])==int(float(r[f'risk_{m}'])>=threshold[m]) for m in METHODS)
    for m in METHODS:
        values=sorted({float(r[f'risk_{m}']) for r in development})
        candidates=values+[math.nextafter(values[-1],math.inf)]
        target=Fraction('0.2')
        candidates_with_counts=[(v,sum(float(r[f'risk_{m}'])>=v for r in development)) for v in candidates]
        chosen=min(candidates_with_counts,key=lambda a:(abs(a[1]-target*len(development)),a[1]))
        assert chosen==(threshold[m],43)
        recalibration[m]={'threshold':chosen[0],'reviewed':chosen[1],
                          'target_fraction':0.2,'target_count':float(target*len(development))}
    cohorts={str(cutoff):{s:{m:counts(rows,(f'risk_{m}',threshold[m]),cutoff)
                                    for m in METHODS}for s,rows in groups.items()}
             for cutoff in (0.5,0.7,0.8)}
    main_cohort=cohorts['0.7'];internal=main_cohort['internal_holdout']['A'];external=main_cohort['external_test']['A']
    h1=difference(external['TP'],external['F'],internal['TP'],internal['F'])
    h2=difference(external['R'],external['N'],internal['R'],internal['N'])
    h3=pairs(groups['external_test'],threshold,0.7)
    contrasts={'H1':h1,'H2':h2,'H3':h3}
    for h,value in contrasts.items():
        for field in ('difference_pp','ci95_pp'):
            assert_close(value[field],original_primary['contrasts'][h][field],f'{h}.{field}',checked)
    for s in ('internal_holdout','external_test'):
        for m in METHODS:
            actual=main_cohort[s][m];original=original_primary['cohorts'][s]
            for field in ('N','F'):assert_close(actual[field],original[field],f'{s}.{field}',checked)
            for field in ('R','TP','FN'):assert_close(actual[field],original['methods'][m][field],f'{s}.{m}.{field}',checked)
    sensitivity={}
    for cutoff in (0.5,0.8):
        values=cohorts[str(cutoff)];a=values['external_test']['A'];b=values['internal_holdout']['A']
        delta=difference(a['TP'],a['F'],b['TP'],b['F']);paired=pairs(groups['external_test'],threshold,cutoff)
        old=original_supp['fixed_threshold_dice_sensitivity'][f'{cutoff:.2f}']
        for s in ('internal_holdout','external_test'):
            for m in METHODS:
                for field in ('TP','FN','R'):
                    assert_close(values[s][m][field],old['cohorts'][s]['methods'][m][field],f'{cutoff}.{s}.{m}.{field}',checked)
        for key,new in [('A_detection_external_minus_internal',delta),('external_detection_B_minus_A',paired)]:
            for field in ('difference_pp','ci95_pp'):
                assert_close(new[field],old[key][field],f'{cutoff}.{key}.{field}',checked)
        sensitivity[str(cutoff)]={'A_external_minus_internal':delta,'external_B_minus_A':paired}
    erows=groups['external_test'];k=min(range(len(erows)+1),key=lambda k:(abs(Fraction(k,len(erows))-Fraction('0.2')),k))
    assert k==50
    ranked={m:sorted(erows,key=lambda r:(-float(r[f'risk_{m}']),r['patient_id']))[:k] for m in METHODS}
    selected={m:{r['patient_id'] for r in ranked[m]} for m in METHODS}
    low={r['patient_id'] for r in erows if float(r['dice_vs_reference'])<0.7}
    pp=Counter((p in selected['B'],p in selected['A']) for p in low)
    eq=paired_interval(pp[True,True],pp[True,False],pp[False,True],pp[False,False])
    eq.update(N=len(erows),F=len(low),R_per_method=k,
              TP={m:len(low&selected[m]) for m in METHODS},
              selected_case_ids={m:[r['patient_id'] for r in ranked[m]] for m in METHODS})
    old=original_supp['external_equal_review']
    for field in ('difference_pp','ci95_pp'):
        assert_close(eq[field],old['detection_B_minus_A'][field],f'equal_review.{field}',checked)
    for m in METHODS:
        assert_close(eq['TP'][m],old['methods'][m]['TP'],f'equal_review.{m}.TP',checked)
        assert eq['selected_case_ids'][m]==old['methods'][m]['selected_case_ids_in_rank_order']
    # Six published examples provide an external benchmark for paired interval code.
    benchmarks=benchmark_paired()
    raw_checks,raw_digests=validate_raw(source,manifests,lock)
    result={'audit_utc':datetime.now(timezone.utc).isoformat(),
            'repository_commit':subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip(),
            'audit_python':platform.python_version(),
            'original_records_unchanged':True,
            'source_files_sha256':integrity,'thresholds':threshold,
            'recalibration':recalibration,'cohorts_by_dice_cutoff':cohorts,
            'documented_threshold_timeline':{'locked_at':lock_time.isoformat(),
                                            'formal_testing_started_at':test_start.isoformat(),
                                            'lock_precedes_testing':True},
            'contrasts':contrasts,'sensitivity_contrasts':sensitivity,
            'external_equal_review':eq,'original_result_fields_checked':checked,
            'all_compared_fields_match':True,
            'paired_ci_published_benchmarks':benchmarks,
            'raw_image_reference_checks':raw_checks,
            'model_inference_rerun_in_current_audit':False,
            'original_image_rerun_receipt_verified_by_analysis':True,
            'exact_software_versions_in_original_receipt':lock['environment'],
            'checkpoint_sha256_recorded':lock['threshold_lock']['model']['weight_sha256'],
            'checkpoint_bytes_available_in_repository':False,
            'original_archive_bytes_available_in_repository':False,
            'interpretation':['Known-location/oracle prompts from reference masks; retrospective public-data evaluation.',
                              'Primary external-minus-internal sensitivity CI crosses zero; external low-quality denominator is 16.',
                              'No equivalence, clinical validation, causal transportability or superiority is established.',
                              'Additional specificity/PPV/NPV are descriptive post hoc utility summaries, not new prespecified endpoints.',
                              'Equal-review interval is conditional on the observed ranking selections and ignores re-ranking variability.']}
    (out/'audit_results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    (out/'selected_raw_file_sha256.json').write_text(json.dumps(raw_digests,indent=2)+'\n')
    records=[]
    for cutoff,cohort in cohorts.items():
        for split,methods in cohort.items():
            for m,v in methods.items():
                row={'dice_cutoff':cutoff,'split':split,'method':m}
                row.update({key:v[key] for key in ('N','F','R','TP','FP','TN','FN','misses_per_100')})
                for metric in ('sensitivity','specificity','ppv','npv','review'):
                    row[metric+'_numerator']=v[metric]['events']
                    row[metric+'_denominator']=v[metric]['denominator']
                    row[metric+'_percent']=100*v[metric]['fraction']
                    row[metric+'_ci95_lower_percent']=100*v[metric]['ci95'][0]
                    row[metric+'_ci95_upper_percent']=100*v[metric]['ci95'][1]
                records.append(row)
    with (out/'utility_metrics.csv').open('w',newline='') as handle:
        w=csv.DictWriter(handle,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
    print(json.dumps({'patients':sum(len(r)for r in groups.values()),'thresholds':threshold,
                      'contrasts':contrasts,'equal_review':{k:eq[k]for k in ('TP','difference_pp','ci95_pp')},
                      'all_compared_fields_match':True,'raw_checks':raw_checks}))


if __name__=='__main__':
    main()
