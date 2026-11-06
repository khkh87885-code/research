#!/usr/bin/env python3
"""Run frozen replay and record observed process resources (Linux RSS KiB)."""
import os,subprocess,time,resource,json,sys
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[1]
command=[str(ROOT/'env/bin/python'),'-B',str(ROOT/'scripts/external_case_audit.py'),'rerun','--source','/workspace/research_source','--output',str(ROOT/'predictions'),'--sam-source','/workspace/bmt_v7/resources/segment-anything','--checkpoint',str(ROOT/'resources/sam_vit_b_01ec64.pth'),'--device','cpu','--threads','2']
env=os.environ.copy();env.update(PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='2')
started=datetime.now(timezone.utc).isoformat();start=time.perf_counter()
r=subprocess.run(command,env=env)
usage=resource.getrusage(resource.RUSAGE_CHILDREN)
record={'command':command,'started_utc':started,'completed_utc':datetime.now(timezone.utc).isoformat(),'return_code':r.returncode,'wall_seconds_including_loading_and_figures':time.perf_counter()-start,'user_cpu_seconds':usage.ru_utime,'system_cpu_seconds':usage.ru_stime,'peak_child_RSS_MiB':usage.ru_maxrss/1024,'thread_environment':{k:env[k]for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','PYTHONDONTWRITEBYTECODE']},'cpu_max':Path('/sys/fs/cgroup/cpu.max').read_text().strip(),'memory_max':Path('/sys/fs/cgroup/memory.max').read_text().strip()}
(ROOT/'runtime_resource.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2),flush=True);sys.exit(r.returncode)
