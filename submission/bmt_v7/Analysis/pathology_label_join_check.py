#!/usr/bin/env python3
"""Read-only check of dataset-reported diagnostic labels in fixed study cohorts."""
import csv
import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import openpyxl

ROOT=Path('/workspace/research_source')
OUT=Path('/workspace/bmt_v7/evidence')


def read_csv(path):
    with path.open(encoding='utf-8-sig',newline='') as handle:
        return list(csv.DictReader(handle))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    source_paths={
        'busbra_official':'data/raw/BUS-BRA/BUSBRA/bus_data.csv',
        'breast_official':'data/raw/BrEaST/BrEaST-Lesions-USG-clinical-data-Dec-15-2023.xlsx',
        'development_scores':'reproducibility/records/development_cases.csv',
        'test_scores':'reproducibility/records/validation_cases.csv',
        'development_manifest':'reproducibility/manifests/busbra_development.csv',
        'internal_manifest':'reproducibility/manifests/busbra_internal_holdout.csv',
        'external_manifest':'reproducibility/manifests/breast_external.csv',
    }
    raw_bus=read_csv(ROOT/source_paths['busbra_official'])
    bus_by_image={r['ID']:r for r in raw_bus}
    assert len(bus_by_image)==len(raw_bus)==1875
    bus_patient_labels=defaultdict(set)
    for r in raw_bus:bus_patient_labels[int(r['Case'])].add(r['Pathology'])
    bus_conflict={k:sorted(v)for k,v in bus_patient_labels.items()if len(v)>1}
    assert len(bus_patient_labels)==1064 and not bus_conflict
    workbook=openpyxl.load_workbook(ROOT/source_paths['breast_official'],data_only=True)
    values=list(workbook.worksheets[0].values)
    breast=[dict(zip(values[0],row))for row in values[1:]if any(v is not None for v in row)]
    breast_by_id={int(r['CaseID']):r for r in breast}
    assert len(breast_by_id)==len(breast)==256
    manifests={
        'development':read_csv(ROOT/source_paths['development_manifest']),
        'internal_holdout':read_csv(ROOT/source_paths['internal_manifest']),
        'external_test':read_csv(ROOT/source_paths['external_manifest']),
    }
    development=read_csv(ROOT/source_paths['development_scores'])
    tests=read_csv(ROOT/source_paths['test_scores'])
    for r in development:r.update(dataset='BUS-BRA',split='development')
    scores={'development':development,
            'internal_holdout':[r for r in tests if r['split']=='internal_holdout'],
            'external_test':[r for r in tests if r['split']=='external_test']}
    diagnostics={};mismatches=[];missing=[];verification_by_class=defaultdict(Counter)
    for split,rows in manifests.items():
        dataset='BrEaST' if split=='external_test' else 'BUS-BRA'
        key=lambda r:(r['dataset'],int(r['patient_id']),r['image_id'])
        manifest_index={key(r):r for r in rows}
        score_index={key(r):r for r in scores[split]}
        duplicate_manifest=len(rows)-len(manifest_index)
        duplicate_score=len(scores[split])-len(score_index)
        unmatched_manifest=set(manifest_index)-set(score_index)
        unmatched_score=set(score_index)-set(manifest_index)
        assert not duplicate_manifest and not duplicate_score
        assert not unmatched_manifest and not unmatched_score
        assert len({int(r['patient_id'])for r in rows})==len(rows)
        for identity,row in manifest_index.items():
            assert row['dataset']==dataset and row['split']==split
            assert row['pathology']in ('benign','malignant')
            scored=score_index[identity]
            if row['pathology']!=scored['pathology']:
                mismatches.append({'scope':'score_manifest','key':identity})
            if dataset=='BUS-BRA':
                original=bus_by_image.get(row['image_id'])
                if original is None:missing.append(identity);continue
                assert int(original['Case'])==int(row['patient_id'])
                official_label=original['Pathology']
            else:
                original=breast_by_id.get(int(row['patient_id']))
                if original is None:missing.append(identity);continue
                official_label=original['Classification']
                assert Path(row['image_path']).name==original['Image_filename']
                assert Path(row['mask_path']).name==original['Mask_tumor_filename']
                assert row['image_id']==Path(original['Image_filename']).stem
                verification_by_class[official_label][original['Verification']]+=1
            if row['pathology']!=official_label:
                mismatches.append({'scope':'manifest_official','key':identity,
                                   'stored':row['pathology'],'official':official_label})
        diagnostics[split]={
            'dataset':dataset,'manifest_rows':len(rows),'score_rows':len(scores[split]),
            'distinct_patients':len({int(r['patient_id'])for r in rows}),
            'duplicate_manifest_full_keys':duplicate_manifest,'duplicate_score_full_keys':duplicate_score,
            'unmatched_manifest_keys':len(unmatched_manifest),'unmatched_score_keys':len(unmatched_score),
            'missing_or_nonbinary_labels':sum(r['pathology']not in ('benign','malignant') for r in rows),
            'label_counts':dict(Counter(r['pathology']for r in rows)),
        }
    dev_ids={int(r['patient_id'])for r in manifests['development']}
    internal_ids={int(r['patient_id'])for r in manifests['internal_holdout']}
    external_ids={int(r['patient_id'])for r in manifests['external_test']}
    assert dev_ids.isdisjoint(internal_ids)
    assert dev_ids|internal_ids==set(bus_patient_labels)
    eligible={int(r['CaseID'])for r in breast if r['Mask_tumor_filename'] and r['Classification']in ('benign','malignant')}
    excluded=[{'CaseID':r['CaseID'],'Classification':r['Classification'],
               'Mask_tumor_filename':r['Mask_tumor_filename']}for r in breast if not r['Mask_tumor_filename']]
    assert external_ids==eligible
    assert {r['CaseID']for r in excluded}=={45,61,209,213}
    assert not mismatches and not missing
    copy_pairs=[
        ('reproducibility/records/development_cases.csv','experiments/development_213/development_cases.csv'),
        ('reproducibility/records/validation_cases.csv','experiments/formal_validation/validation_cases.csv'),
        ('reproducibility/manifests/busbra_development.csv','data/manifests/busbra_development.csv'),
        ('reproducibility/manifests/busbra_internal_holdout.csv','data/manifests/busbra_internal_holdout.csv'),
        ('reproducibility/manifests/breast_external.csv','data/manifests/breast_external_test/manifest.csv'),
    ]
    for rel in ['records/development_cases.csv','records/validation_cases.csv','manifests/busbra_development.csv',
                'manifests/busbra_internal_holdout.csv','manifests/breast_external.csv']:
        copy_pairs.append(('reproducibility/'+rel,'submission/bmt_v6/Reproducibility/'+rel))
    copies=[]
    for a,b in copy_pairs:
        same=sha(ROOT/a)==sha(ROOT/b);assert same,(a,b)
        copies.append({'file_a':a,'file_b':b,'identical_bytes':same})
    result={
        'audit_date_utc':datetime.now(timezone.utc).isoformat(),
        'source_commit':subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip(),
        'source_paths':source_paths,'source_sha256':{k:sha(ROOT/v)for k,v in source_paths.items()},
        'scope':'All 1316 study cases, with labels joined to the available official source tables.',
        'official_busbra':{'image_rows':len(raw_bus),'unique_ID':len(bus_by_image),
                          'unique_Case':len(bus_patient_labels),'within_patient_label_conflicts':len(bus_conflict),
                          'join':'manifest.image_id = bus_data.ID; check integer patient_id = Case',
                          'label_column':'Pathology'},
        'official_breast':{'workbook_sheet':workbook.worksheets[0].title,
                          'case_rows':len(breast),'unique_CaseID':len(breast_by_id),
                          'join':'integer manifest.patient_id = workbook.CaseID; additionally match Image_filename and Mask_tumor_filename',
                          'actual_identifier_header':'CaseID','dictionary_identifier_header':'Case_ID',
                          'label_column':'Classification','excluded_without_primary_mask':excluded,
                          'selected_labels':dict(Counter(r['Classification']for r in breast if int(r['CaseID'])in eligible)),
                          'verification_by_label':{k:dict(v)for k,v in verification_by_class.items()}},
        'cohort_join_checks':diagnostics,
        'BUS_BRA_development_internal_patient_overlap':len(dev_ids&internal_ids),
        'BUS_BRA_development_internal_cover_all_official_patients':True,
        'dataset_scoped_keys_required':True,
        'coincident_numeric_patient_IDs_across_datasets':len((dev_ids|internal_ids)&external_ids),
        'score_manifest_label_mismatches':0,'manifest_official_label_mismatches':0,
        'official_unmatched_selected_cases':0,'copy_identity_checks':copies,
        'interpretation':'Dataset-reported benign/malignant diagnostic classes; not all BrEaST labels are biopsy-confirmed. This grouping is not a cancer-classification endpoint.',
        'original_data_modified':False,'SAM_inference_run':False,
    }
    (OUT/'pathology_label_join_audit.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    md=f'''# Pathology-label source and join audit

Source commit: `{result['source_commit']}`. All 1,316 study cases were audited read-only. No SAM inference was performed.

## Official labels and keys

- BUS-BRA labels come from `data/raw/BUS-BRA/BUSBRA/bus_data.csv`, column **Pathology**. The table has 1,875 unique image IDs and 1,064 unique patient `Case` values. Each selected `image_id` was joined to `ID`, and its integer `patient_id` was checked against `Case`. No patient has contradictory labels between image views.
- BrEaST labels come from `data/raw/BrEaST/BrEaST-Lesions-USG-clinical-data-Dec-15-2023.xlsx`, first sheet `{workbook.worksheets[0].title}`, column **Classification**. The actual identifier header is **CaseID** (the dictionary calls it `Case_ID`). The integer patient ID was joined to `CaseID`, with exact filename checks against `Image_filename` and `Mask_tumor_filename`.
- Keys retain the dataset identity. Numeric IDs coincide across datasets in {result['coincident_numeric_patient_IDs_across_datasets']} cases; joining on patient number alone would incorrectly mix different people.

## Coverage and diagnostics

| Cohort | Cases | Benign | Malignant | Missing/nonbinary labels | Label conflicts | Unmatched score/manifest rows |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
'''
    for split,d in diagnostics.items():
        md+=f"| {split} | {d['manifest_rows']} | {d['label_counts']['benign']} | {d['label_counts']['malignant']} | 0 | 0 | 0 |\n"
    md+='''
There are no duplicate full keys in the score or manifest files, no duplicate patients within a cohort, no missing official-source matches, no score–manifest label conflicts, and no manifest–official label conflicts. BUS-BRA development and internal testing share **0 patients**, and together cover all 1,064 official BUS-BRA patients.

BrEaST cases **45, 61, 209 and 213** are labelled normal and have no main tumour mask; they are the only four such official cases and are excluded. The selected external IDs exactly equal the 252 eligible benign/malignant cases with a main mask.

The experiment copies, release copies and current v6 submission copies were compared byte-for-byte: all 10 checked score/manifest copy pairs agree.

## Wording implication

Use **dataset-reported benign/malignant classification**. Among the 252 external cases, the official workbook reports **197 confirmed by biopsy** and **55 confirmed by follow-up care**. Therefore, describing every external label as histopathologically confirmed would be inaccurate. The labels define exploratory strata only; the positive outcome remains low-quality segmentation (reference Dice < 0.70), not malignancy.

This validates label propagation against the official files available in the repository; it does not independently reassess clinical diagnoses or obtain new patient records. No source data were changed.
'''
    (OUT/'pathology_label_join_audit.md').write_text(md)
    print(json.dumps({'cohorts':diagnostics,'label_conflicts':0,'official_unmatched':0,
                      'BUS_BRA_development_internal_overlap':0,
                      'external_verification':result['official_breast']['verification_by_label']},ensure_ascii=False))


if __name__=='__main__':main()
