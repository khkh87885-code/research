#!/usr/bin/env python3
"""Lock inspected independent reports and the immutable delivery bytes."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json
BASE=Path('/workspace/bmt_v13')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
reports={}
for name in ['independent_math_qa','typography_audit','render_validation']:
    p=BASE/'evidence'/(name+'.json');d=json.loads(p.read_text())
    assert d['status']=='PASS'
    assert d.get('final_documents_pending',False) is False
    assert not d.get('unresolved_findings',[])
    assert all(c.get('pass',c.get('passed',False)) for c in d.get('checks',[]))
    reports[name]={'path':str(p.relative_to(BASE)),'sha256':sha(p)}
files=sorted(p for p in (BASE/'outputs').iterdir() if p.suffix in ['.docx','.pdf'])
assert len(files)==8
record={'revision':'v13','created_utc':datetime.now(timezone.utc).isoformat(),
        'status':'PASS','final_documents_pending':False,
        'scope':'DOCX mathematical/content preservation plus actual exported PDF layout; WPS remains unexecuted',
        'known_failing_viewer':'WPS','direct_wps_tested':False,'direct_microsoft_word_tested':False,
        'reports':reports,'documents':{p.name:{'sha256':sha(p),'bytes':p.stat().st_size}for p in files},
        'scientific_data_changed':False,'new_experiments':False,'journal_submission_executed':False,
        'retained_equations':{'main':['1','2','3'],'supplement':['S1','S2']}}
dest=BASE/'evidence/final_revision_qa.json'
dest.write_text(json.dumps(record,indent=2)+'\n')
print(sha(dest))
