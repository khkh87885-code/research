#!/usr/bin/env python3
"""Seal a naming-only delivery after independent review and prepare CAS upload."""
from pathlib import Path
import hashlib,json,shutil,subprocess
TASK=Path('/workspace/paper_filenames')
ROOT=Path('/workspace/research_source')
BASE='f7f61104b5d7039dd8537c6c9963200627d07dd1'
DEST=ROOT/'submission/breast_ultrasound_quality_control'
PREFIX='Breast_Ultrasound_Quality_Control'
MANIFEST=PREFIX+'_File_Manifest.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()

if __name__=='__main__':
    assert git('rev-parse','HEAD')==BASE
    report=TASK/'evidence/independent_naming_qa.json'
    qa=json.loads(report.read_text())
    assert qa['status']=='PASS'
    assert not qa.get('unresolved_findings',[])
    for name in ['independent_naming_qa.json','independent_naming_qa.md','upload_files.json']:
        p=TASK/'evidence'/name
        if p.exists():shutil.copy2(p,DEST/'Audit/file_naming'/name)
    for p in (TASK/'scripts').glob('*.py'):
        shutil.copy2(p,DEST/'Analysis/file_preparation'/p.name)
    check=TASK/'scripts/check_named_submission.py'
    if check.exists():shutil.copy2(check,DEST/'Analysis/file_preparation'/check.name)
    files=[{'path':p.relative_to(DEST).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)}for p in sorted(DEST.rglob('*'))if p.is_file()and p.name!=MANIFEST]
    (DEST/MANIFEST).write_text(json.dumps({'paper_title':'Fixed-threshold transfer and equal-review ranking in breast ultrasound segmentation quality control','files':files},indent=2)+'\n')
    # Remove only the unchanged former current delivery; its exact source bytes
    # remain in the task backup and in the parent Git commit.
    old=ROOT/'submission/bmt_v13';backup=TASK/'source'
    oldfiles={p.relative_to(old).as_posix():sha(p)for p in old.rglob('*')if p.is_file()}
    backups={p.relative_to(backup).as_posix():sha(p)for p in backup.rglob('*')if p.is_file()}
    assert oldfiles==backups and len(oldfiles)==132
    oldzip=ROOT/'submission/BMT_v13_submission_files.zip'
    assert sha(oldzip)==sha(TASK/'source_submission_files.zip')
    removed=['submission/bmt_v13/'+p for p in oldfiles]+['submission/BMT_v13_submission_files.zip']
    shutil.rmtree(old);oldzip.unlink()
    tree=git('rev-parse',BASE+'^{tree}')
    known={line.split()[2]for line in git('ls-tree','-r',BASE).splitlines()}
    paths=[ROOT/'README.md',ROOT/'submission'/(PREFIX+'_Submission_Files.zip')]+sorted(p for p in DEST.rglob('*')if p.is_file())
    entries=[]
    for p in paths:
        data=p.read_bytes();assert len(data)<12_300_000
        blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        entries.append({'path':p.relative_to(ROOT).as_posix(),'local_path':str(p),'bytes':len(data),'sha':blob,'already_in_base':blob in known})
    result={'base_commit':BASE,'base_tree':tree,'entries':entries,'deletions':removed,'independent_qa_sha256':sha(report)}
    (TASK/'upload_manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'added_or_updated':len(entries),'former_delivery_paths_removed':len(removed),'new_blob_bytes':sum(x['bytes']for x in entries if not x['already_in_base']),'zip_bytes':(ROOT/'submission'/(PREFIX+'_Submission_Files.zip')).stat().st_size},indent=2))
