#!/usr/bin/env python3
"""Exploratory benign/malignant stratification of frozen segmentation QC scores.

This script reads archived records and official dataset labels. It does not
recalibrate thresholds, alter masks or scores, run SAM, or perform hypothesis
tests. Python standard library + openpyxl are required.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import platform
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import NormalDist

from openpyxl import load_workbook

METHODS=('A','B')
STRATA=('benign','malignant')
SPLITS=('development','internal_holdout','external_test')
Z=NormalDist().inv_cdf(0.975)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path):
    with path.open(encoding='utf-8-sig',newline='') as h:
        return list(csv.DictReader(h))


def pid(value):
    return str(int(value))


def identity(row):
    return row['dataset'],pid(row['patient_id']),row['image_id']


def wilson(x,n):
    if not n:
        return None
    p=x/n;z2=Z*Z;d=1+z2/n
    center=(p+z2/(2*n))/d
    half=Z*math.sqrt(p*(1-p)/n+z2/(4*n*n))/d
    return [max(0,center-half),min(1,center+half)]


def rate(x,n):
    bounds=wilson(x,n)
    return {'numerator':x,'denominator':n,'fraction':x/n if n else None,
            'percent':100*x/n if n else None,
            'wilson_ci95_percent':None if bounds is None else [100*v for v in bounds]}


def summarize(rows,method,threshold,cutoff):
    flags=[(float(r['dice_vs_reference'])<cutoff,float(r['risk_'+method])>=threshold) for r in rows]
    tab=Counter(flags)
    tp,fp,tn,fn=tab[True,True],tab[False,True],tab[False,False],tab[True,False]
    n=len(rows);f=tp+fn;r=tp+fp
    assert n==tp+fp+tn+fn
    return {'N':n,'low_quality':f,'review_count':r,'TP':tp,'FP':fp,'TN':tn,'FN':fn,
            'low_quality_fraction':rate(f,n),'review_fraction':rate(r,n),
            'detection':rate(tp,f),'misses_per_100':100*fn/n}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo',type=Path,default=Path('/workspace/research_source'))
    p.add_argument('--output',type=Path,default=Path('/workspace/bmt_v7/evidence'))
    a=p.parse_args();repo=a.repo.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
    repro=repo/'reproducibility';lock=json.loads((repro/'study_lock.json').read_text())
    cutoff=lock['threshold_lock']['quality_reference']['cutoff'];assert cutoff==0.70
    thresholds={m:lock['threshold_lock']['methods'][m]['threshold'] for m in METHODS}
    assert thresholds=={'A':0.13705134391784668,'B':0.06972856653991777}
    inputs={}
    manifests={}
    for split,c in lock['cohorts'].items():
        path=repro/c['manifest'];manifests[split]=read_csv(path);inputs[str(path.relative_to(repo))]=digest(path)
        assert digest(path)==lock['files_sha256'][c['manifest']]
    dev=read_csv(repro/'records/development_cases.csv')
    for r in dev:
        r.update(dataset='BUS-BRA',split='development')
        for m in METHODS:r['alert_'+m]=r['candidate_alert_'+m]
    tests=read_csv(repro/'records/validation_cases.csv')
    groups={'development':dev,
            'internal_holdout':[r for r in tests if r['split']=='internal_holdout'],
            'external_test':[r for r in tests if r['split']=='external_test']}
    for rel in ('records/development_cases.csv','records/validation_cases.csv'):
        inputs[str((repro/rel).relative_to(repo))]=digest(repro/rel)
        assert digest(repro/rel)==lock['files_sha256'][rel]
    match_counts={}
    for split,rows in groups.items():
        manifest={identity(r):r for r in manifests[split]}
        assert len(manifest)==len(rows)==len({identity(r)for r in rows})
        assert len({(r['dataset'],pid(r['patient_id']))for r in rows})==len(rows)
        assert {identity(r)for r in rows}==set(manifest)
        for r in rows:
            assert r['pathology'] in STRATA
            assert r['pathology']==manifest[identity(r)]['pathology']
            assert r['status']=='scored'
            assert int(r['low_quality'])==int(float(r['dice_vs_reference'])<cutoff)
            for m in METHODS:
                assert int(r['alert_'+m])==int(float(r['risk_'+m])>=thresholds[m])
        match_counts[split]=len(rows)
    dev_ids={(r['dataset'],pid(r['patient_id']))for r in dev}
    int_ids={(r['dataset'],pid(r['patient_id']))for r in groups['internal_holdout']}
    assert dev_ids.isdisjoint(int_ids)

    # Validate labels against original distributed metadata, not just a copied manifest.
    buspath=repo/'data/raw/BUS-BRA/BUSBRA/bus_data.csv';busrows=read_csv(buspath)
    bus={r['ID']:r for r in busrows};assert len(bus)==len(busrows)
    by_case=defaultdict(set)
    for r in busrows:by_case[pid(r['Case'])].add(r['Pathology'])
    assert all(len(v)==1 for v in by_case.values())
    for r in dev+groups['internal_holdout']:
        b=bus[r['image_id']]
        assert pid(b['Case'])==pid(r['patient_id']) and b['Pathology']==r['pathology']
    breastpath=repo/'data/raw/BrEaST/BrEaST-Lesions-USG-clinical-data-Dec-15-2023.xlsx'
    book=load_workbook(breastpath,read_only=True,data_only=True)
    ws=book[book.sheetnames[0]];source=list(ws.iter_rows(values_only=True))
    header=list(source[0]);breastrows=[dict(zip(header,v))for v in source[1:]if v[0] is not None]
    breast={pid(r['CaseID']):r for r in breastrows};assert len(breast)==len(breastrows)==256
    ext_manifest={pid(r['patient_id']):r for r in manifests['external_test']}
    verification=Counter()
    for r in groups['external_test']:
        b=breast[pid(r['patient_id'])];m=ext_manifest[pid(r['patient_id'])]
        assert b['Classification']==r['pathology']
        assert b['Image_filename']==Path(m['image_path']).name
        assert b['Mask_tumor_filename']==Path(m['mask_path']).name
        verification[b['Verification']]+=1
    excluded=sorted(int(r['CaseID'])for r in breastrows if not r['Mask_tumor_filename'])
    assert excluded==[45,61,209,213]
    assert all(breast[str(i)]['Classification']=='normal' for i in excluded)
    assert set(breast)-set(ext_manifest)=={str(i)for i in excluded}
    book.close()
    for path in (buspath,breastpath):inputs[str(path.relative_to(repo))]=digest(path)

    stratified={split:{label:{m:summarize([r for r in groups[split]if r['pathology']==label],m,thresholds[m],cutoff)
                                   for m in METHODS}for label in STRATA}for split in SPLITS}
    overall={split:{m:summarize(groups[split],m,thresholds[m],cutoff)for m in METHODS}for split in SPLITS}
    for split in SPLITS:
        for m in METHODS:
            for field in ('N','low_quality','review_count','TP','FP','TN','FN'):
                assert sum(stratified[split][label][m][field]for label in STRATA)==overall[split][m][field]
    provided={('internal_holdout','benign'):(53,51,41),('internal_holdout','malignant'):(40,20,27),
              ('external_test','benign'):(8,5,7),('external_test','malignant'):(8,5,6)}
    provided_check=[]
    for (split,label),(low,ta,tb) in provided.items():
        v=stratified[split][label]
        observed=(v['A']['low_quality'],v['A']['TP'],v['B']['TP'])
        assert observed==(low,ta,tb)
        provided_check.append({'split':split,'stratum':label,'expected_low_TPA_TPB':[low,ta,tb],
                               'observed_low_TPA_TPB':observed,'matches':True})
    for label,bounds in [('benign',[87.25,98.96]),('malignant',[35.20,64.80])]:
        actual=stratified['internal_holdout'][label]['A']['detection']['wilson_ci95_percent']
        assert [round(x,2)for x in actual]==bounds
    result={'analysis':'post hoc exploratory stratification of segmentation quality control by dataset-provided benign/malignant labels',
            'audit_utc':datetime.now(timezone.utc).isoformat(),
            'source_commit':subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip(),
            'python':platform.python_version(),'source_inputs_sha256':inputs,
            'low_quality_definition':{'reference_dice_operator':'<','cutoff':cutoff},
            'unchanged_thresholds':thresholds,'thresholds_recalibrated':False,
            'new_SAM_inference':False,'hypothesis_tests_performed':False,
            'score_manifest_join_key':['dataset','canonical_integer_patient_id','image_id'],
            'score_manifest_pathology_matches':match_counts,
            'missing_labels':0,'conflicting_labels':0,'duplicate_patient_rows':0,
            'BUS_BRA_development_internal_patient_overlap':0,
            'label_sources':{
                'BUS-BRA':{'file':str(buspath.relative_to(repo)),'label_column':'Pathology',
                           'join':'score.image_id = ID; score.patient_id = Case','matched_patients':1064,
                           'patient_label_inconsistencies_in_full_source':0},
                'BrEaST':{'file':str(breastpath.relative_to(repo)),'worksheet':ws.title,
                          'label_column':'Classification','join':'canonical patient_id = CaseID; confirm image and main mask filenames',
                          'matched_patients':252,'verification_counts':dict(verification),'excluded_normal_ids_without_main_mask':excluded,
                          'caution':'Classification includes biopsy and follow-up confirmation; not all cases are histopathologically confirmed.'}},
            'stratified':stratified,'overall_for_main_table_2':overall,
            'user_supplied_checks':provided_check,
            'all_strata_recombine_to_original_overall_counts':True,
            'interpretation_limits':['Low-quality segmentation is the condition being detected; these are not cancer classification metrics.',
                                     'Exploratory post hoc subgroups; no subgroup hypotheses or interaction tests were specified or performed.',
                                     'No causal claim about lesion biology, size or image appearance is supported.',
                                     'External stratum-specific detection denominators are only eight, limiting precision.',
                                     'Development estimates use the threshold-selection cohort and are not independent validation.']}
    (out/'pathology_audit.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    rows=[]
    for split in SPLITS:
        for label in STRATA:
            for method,v in stratified[split][label].items():
                record={'dataset':'BrEaST'if split=='external_test'else'BUS-BRA','split':split,'diagnostic_stratum':label,'method':method,
                        'threshold':thresholds[method],'reference_dice_cutoff':cutoff}
                record.update({k:v[k]for k in ('N','low_quality','review_count','TP','FP','TN','FN','misses_per_100')})
                for metric in ('low_quality_fraction','review_fraction','detection'):
                    record[metric+'_percent']=v[metric]['percent']
                    record[metric+'_ci95_lower_percent']=v[metric]['wilson_ci95_percent'][0]
                    record[metric+'_ci95_upper_percent']=v[metric]['wilson_ci95_percent'][1]
                rows.append(record)
    with (out/'pathology_stratified_metrics.csv').open('w',newline='')as h:
        writer=csv.DictWriter(h,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    print(json.dumps({'patients':sum(len(g)for g in groups.values()),'rows':len(rows),
                      'stratified':stratified,'user_supplied_checks_all_match':True,
                      'BrEaST_verification_counts':dict(verification)},allow_nan=False))


if __name__=='__main__':main()
