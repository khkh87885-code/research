#!/usr/bin/env python3
"""Independent read-only validation of case-mix-decomposition input records."""
import argparse,csv,hashlib,json,subprocess,time
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
import openpyxl

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(p):
 with p.open(encoding='utf-8-sig',newline='') as h:return list(csv.DictReader(h))
def key(x):return (x['dataset'],int(x['patient_id']),x['image_id'])

def main():
 t=time.perf_counter();a=argparse.ArgumentParser();a.add_argument('--source-root',default='/workspace/research_source');a.add_argument('--output',default='/workspace/bmt_cloud_validation/reports/case_mix_input_check.json');args=a.parse_args();r=Path(args.source_root)
 protocol=Path('/workspace/bmt_cloud_validation/protocol/analysis_plan.json');plan=json.loads(protocol.read_text());audit=json.loads((r/'submission/bmt_v7/Audit/pathology_audit.json').read_text());lock=json.loads((r/'reproducibility/study_lock.json').read_text());head=subprocess.check_output(['git','-C',str(r),'rev-parse','HEAD'],text=True).strip();branch=subprocess.check_output(['git','-C',str(r),'branch','--show-current'],text=True).strip();assert head==plan['source_commit'];assert branch=='main'
 expected_hashes=audit['source_inputs_sha256'];hashes={p:sha(r/p) for p in expected_hashes};assert hashes==expected_hashes
 dev=rows(r/'reproducibility/records/development_cases.csv');test=rows(r/'reproducibility/records/validation_cases.csv')
 for x in dev:
  x['dataset']='BUS-BRA';x['split']='development'
  for method in ['A','B']:x['alert_'+method]=x['candidate_alert_'+method]
 allrows=dev+test
 manifests={}
 for p in ['busbra_development.csv','busbra_internal_holdout.csv','breast_external.csv']:
  for x in rows(r/'reproducibility/manifests'/p):
   k=key(x);assert k not in manifests;manifests[k]=x
 assert len(allrows)==1316 and len(manifests)==1316 and len({key(x)for x in allrows})==1316
 assert len({(x['dataset'],int(x['patient_id']))for x in allrows})==1316
 bus={x['ID']:x for x in rows(r/'data/raw/BUS-BRA/BUSBRA/bus_data.csv')}
 wb=openpyxl.load_workbook(r/'data/raw/BrEaST/BrEaST-Lesions-USG-clinical-data-Dec-15-2023.xlsx',read_only=True,data_only=True);it=wb[wb.sheetnames[0]].iter_rows(values_only=True);cols=next(it);breast={int(x['CaseID']):x for x in (dict(zip(cols,z))for z in it) if x['CaseID'] is not None};wb.close()
 th={m:lock['threshold_lock']['methods'][m]['threshold'] for m in ['A','B']};assert th==audit['unchanged_thresholds']
 groups={};official_confirmed=Counter()
 for x in allrows:
  m=manifests[key(x)];assert x['pathology']==m['pathology'];label=x['pathology'];assert label in ['benign','malignant'];assert int(x['low_quality'])==int(float(x['dice_vs_reference'])<.7);assert x['status']=='scored'
  if x['dataset']=='BUS-BRA':
   z=bus[x['image_id']];assert int(x['patient_id'])==int(z['Case']) and label==z['Pathology']
  else:
   z=breast[int(x['patient_id'])];assert label==z['Classification'];assert x['image_id']+'.png'==z['Image_filename'];assert Path(m['mask_path']).name==z['Mask_tumor_filename'];official_confirmed[z['Verification']]+=1
  for method in ['A','B']:
   alert=int(float(x['risk_'+method])>=th[method]);assert alert==int(x['alert_'+method]);g=groups.setdefault(x['split'],{}).setdefault(label,{}).setdefault(method,Counter());g['N']+=1;g['low_quality']+=int(x['low_quality']);g['review_count']+=alert;g['TP']+=alert*int(x['low_quality']);g['FP']+=alert*(1-int(x['low_quality']));g['TN']+=(1-alert)*(1-int(x['low_quality']));g['FN']+=(1-alert)*int(x['low_quality'])
 for split,strata in groups.items():
  for label,methods in strata.items():
   for m,g in methods.items():
    for field,value in g.items():assert value==audit['stratified'][split][label][m][field],(split,label,m,field,value)
 dev_ids={int(x['patient_id'])for x in dev};internal=[x for x in test if x['split']=='internal_holdout'];external=[x for x in test if x['split']=='external_test'];assert not dev_ids.intersection({int(x['patient_id'])for x in internal})
 image_hashes={}
 for label,rr,root in [('internal',internal,r/'data/raw/BUS-BRA'),('external',external,r/'data/raw/BrEaST')]:
  image_hashes[label]={sha(root/manifests[key(x)]['image_path']) for x in rr}
 image_overlap=image_hashes['internal']&image_hashes['external'];assert not image_overlap
 out={'check_utc':datetime.now(timezone.utc).isoformat(),'source_commit':head,'source_branch':branch,'protocol_sha256':sha(protocol),'source_inputs_sha256':hashes,'audit_sha256':sha(r/'submission/bmt_v7/Audit/pathology_audit.json'),'study_lock_sha256':sha(r/'reproducibility/study_lock.json'),'all_matches':True,'score_rows':len(allrows),'validation_rows':len(test),'unique_dataset_qualified_patient_ids':len(allrows),'duplicate_patient_rows':0,'score_manifest_raw_metadata_label_mismatches':0,'risk_threshold_vs_archived_alert_mismatches':0,'quality_vs_archived_label_mismatches':0,'BUS_BRA_development_internal_patient_overlap':0,'internal_external_exact_image_sha256_overlap':len(image_overlap),'cross_dataset_patient_identity_caution':'Dataset-qualified IDs are disjoint, but numeric IDs are dataset-local. No record linkage is available to establish absence of the same person across independently released datasets; exact image hashes showed no overlap.','thresholds':th,'stratified_counts':groups,'external_label_verification_counts':dict(official_confirmed),'prior_pathology_audit_source_commit':audit['source_commit'],'prior_audit_hash_identity_note':'Prior pathology audit reports an older source commit; all seven source input hashes match current main exactly.','model_inference_performed':False,'elapsed_seconds':time.perf_counter()-t}
 Path(args.output).write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'output':args.output,'all_matches':True,'source_commit':head,'elapsed_seconds':out['elapsed_seconds'],'counts':groups},indent=2))
if __name__=='__main__':main()
