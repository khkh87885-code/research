#!/usr/bin/env python3
"""Execute documented CLI workflows in a new detached source worktree/output."""
import csv
import gzip
import hashlib
import importlib.metadata
import io
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from datetime import datetime,timezone
from pathlib import Path

BUNDLE=Path('/workspace/bmt_cloud_validation')
SOURCE=Path('/workspace/research_source')
TEMP_SOURCE=Path('/workspace/bmt_validation_source_tmp')
TEMP_OUTPUT=Path('/workspace/bmt_validation_rerun_tmp')
QA=BUNDLE/'qa'
EXPECTED_COMMIT='f9cfdc49b6e6a9e037443f6ce077006bc9377960'


def sha_bytes(value):return hashlib.sha256(value).hexdigest()
def sha(path):return sha_bytes(path.read_bytes())
def git(root,*args):return subprocess.check_output(['git','-C',str(root),*args],text=True).strip()


def tree_snapshot(root):
    # Check every scientific input actually consumed by the three entrypoints.
    # Postal/README/manuscript packaging edits in the active checkout are not
    # numerical inputs and need not match an older fixed-commit worktree.
    lock=json.loads((root/'reproducibility/study_lock.json').read_text())
    names=['reproducibility/study_lock.json']+['reproducibility/'+rel for rel in lock['files_sha256']]
    names+=['reproducibility/study_statistics.py','reproducibility/reproduce.py',
            'submission/bmt_v7/Audit/pathology_audit.json',
            'data/raw/BUS-BRA/BUSBRA/bus_data.csv',
            'data/raw/BrEaST/BrEaST-Lesions-USG-clinical-data-Dec-15-2023.xlsx']
    files={};total=0
    for name in names:
        path=root/name
        assert path.is_file(),str(path)
        data=path.read_bytes();files[name]=sha_bytes(data);total+=len(data)
    h=hashlib.sha256()
    for name,digest in sorted(files.items()):h.update(name.encode()+b'\0'+digest.encode()+b'\n')
    return files,{'scientific_input_files':len(files),'scientific_input_bytes':total,
                  'scientific_input_aggregate_sha256':h.hexdigest(),'files_sha256':files}


def archive_csv_bytes(relative):
    plain=BUNDLE/relative;compressed=Path(str(plain)+'.gz')
    if plain.is_file():return plain.read_bytes(),str(plain)
    if compressed.is_file():
        with gzip.open(compressed,'rb')as h:return h.read(),str(compressed)
    raise FileNotFoundError(plain)


def compare_csv(relative):
    original,source_path=archive_csv_bytes(relative);fresh=(TEMP_OUTPUT/relative).read_bytes()
    left=list(csv.reader(io.StringIO(original.decode('utf-8-sig'))))
    right=list(csv.reader(io.StringIO(fresh.decode('utf-8-sig'))))
    assert len(left)==len(right),(relative,'row count',len(left),len(right))
    assert left[0]==right[0],(relative,'header')
    exact_cells=0;numeric_equivalent=0
    for ri,(a,b)in enumerate(zip(left,right)):
        assert len(a)==len(b),(relative,ri,'columns')
        for ci,(v,w)in enumerate(zip(a,b)):
            if v==w:exact_cells+=1;continue
            try:
                assert float(v)==float(w),(relative,ri,ci,v,w)
                numeric_equivalent+=1
            except (ValueError,AssertionError):raise AssertionError((relative,ri,ci,v,w))
    return {'file':relative,'original_read_from':source_path,'original_sha256':sha_bytes(original),
            'rerun_sha256':sha_bytes(fresh),'byte_identical':original==fresh,
            'data_rows':len(left)-1,'header_columns':len(left[0]),'exactly_equal_cells':exact_cells,
            'format_only_numeric_cells':numeric_equivalent,'all_cells_numerically_or_textually_equal':True}


def main():
    start=time.perf_counter();result={'started_utc':datetime.now(timezone.utc).isoformat(),
        'README_sha256':sha(BUNDLE/'README.md'),'source_commit':git(SOURCE,'rev-parse','HEAD'),
        'test_scope':'Documented three CLI entrypoints using a fresh fixed-commit detached worktree and a new output directory in the existing pinned environment; no algorithm changes.',
        'preflight_history':'portable_reproduction_preflight_failure.json preserves the initial over-broad tracked-tree comparison failure before any analysis command ran. Expected postal/packaging edits are excluded from the scientific-input scope.',
        'commands':[],'status':'RUNNING'}
    assert not TEMP_SOURCE.exists() and not TEMP_OUTPUT.exists(),'Temporary paths must not pre-exist.'
    assert result['source_commit']==EXPECTED_COMMIT
    pins={}
    for line in(BUNDLE/'requirements.txt').read_text().splitlines():
        line=line.strip()
        if not line or line.startswith('#'):continue
        name,version=line.split('==');actual=importlib.metadata.version(name);assert actual==version,(name,actual,version)
        pins[name]={'required':version,'installed':actual,'matches':True}
    result['environment']={'python':platform.python_version(),'dependencies':pins,
                           'fresh_pip_install_executed':False,'dependency_note':'Existing versions match all exact requirements; package installation and a new isolated venv were not retested.'}
    inputs,source_before=tree_snapshot(SOURCE);result['original_source_before']=source_before
    scripts=['budget_transfer.py','bootstrap_stability.py','case_mix_decomposition.py']
    code_before={name:sha(BUNDLE/'scripts'/name)for name in scripts}
    plan=BUNDLE/'protocol/analysis_plan.json';plan_before=sha(plan)
    archive_before={str(p.relative_to(BUNDLE)):sha(p)for p in(BUNDLE/'results').rglob('*')if p.is_file()}
    subprocess.run(['git','-C',str(SOURCE),'worktree','add','--detach',str(TEMP_SOURCE),EXPECTED_COMMIT],check=True,capture_output=True,text=True)
    TEMP_OUTPUT.mkdir();(TEMP_OUTPUT/'.portable_check_created').write_text('temporary outputs created by portable_reproduction_check.py\n')
    try:
        fresh_inputs,source_copy=tree_snapshot(TEMP_SOURCE);assert fresh_inputs==inputs
        assert git(TEMP_SOURCE,'rev-parse','HEAD')==EXPECTED_COMMIT
        assert git(TEMP_SOURCE,'branch','--show-current')==''
        assert git(TEMP_SOURCE,'status','--porcelain')==''
        result['detached_worktree_before']=source_copy
        env=os.environ.copy()
        env.update({key:'1'for key in('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS','BLIS_NUM_THREADS')})
        commands=[
            [sys.executable,str(BUNDLE/'scripts/budget_transfer.py'),'--source-root',str(TEMP_SOURCE),'--output-root',str(TEMP_OUTPUT),'--protocol',str(plan)],
            [sys.executable,str(BUNDLE/'scripts/bootstrap_stability.py'),'--repo',str(TEMP_SOURCE),'--output',str(TEMP_OUTPUT),'--replicates','10000','--seed','20261106','--plan',str(plan)],
            [sys.executable,str(BUNDLE/'scripts/case_mix_decomposition.py'),'--source-root',str(TEMP_SOURCE),'--output-root',str(TEMP_OUTPUT),'--protocol',str(plan)],
        ]
        for args in commands:
            t=time.perf_counter();run=subprocess.run(args,env=env,capture_output=True,text=True)
            result['commands'].append({'argv':args,'wall_seconds':time.perf_counter()-t,'exit_code':run.returncode,'stdout':run.stdout,'stderr':run.stderr})
            assert run.returncode==0,(args,run.returncode,run.stderr)
        csvs=['results/budget_transfer/calibration.csv','results/budget_transfer/performance.csv','results/budget_transfer/paired_contrasts.csv',
              'results/bootstrap_stability/iterations.csv','results/case_mix_decomposition.csv',
              'results/case_mix_decomposition_strata.csv','results/case_mix_decomposition_bootstrap.csv']
        result['CSV_comparisons']=[compare_csv(p)for p in csvs]
        assert next(v for v in result['CSV_comparisons']if v['file']=='results/bootstrap_stability/iterations.csv')['byte_identical']
        deterministic={}
        comparisons=[('results/budget_transfer/results.json',['calibration','performance','paired_contrasts','verification']),
                     ('results/bootstrap_stability/summary.json',['classification','source_commit','source_inputs_sha256','protocol_sha256','script_sha256','replicates_per_route','seed','RNG','observed','edge_case_checks','routes','observed_external_low_quality_paired_table','original_paired_Newcombe_H3_ci95_pp','fixed_cutoff_empirical_support_constraint','iterations_csv_sha256','iterations_csv_rows','source_files_unchanged']),
                     ('results/case_mix_decomposition.json',['analysis','design','direction','rate_units','bootstrap','results','counts','interpretation_limits'])]
        for relative,fields in comparisons:
            a=json.loads((BUNDLE/relative).read_text());b=json.loads((TEMP_OUTPUT/relative).read_text())
            checks={key:a[key]==b[key]for key in fields};assert all(checks.values()),(relative,checks)
            deterministic[relative]={'fields_checked':checks,'all_deterministic_fields_equal':True,
                                     'excluded_provenance':'Timestamps, runtime, process memory, absolute source/output paths and detached/main branch labels may differ.'}
        original_ids=json.loads((BUNDLE/'results/budget_transfer/selected_case_ids.json').read_text())
        fresh_ids=json.loads((TEMP_OUTPUT/'results/budget_transfer/selected_case_ids.json').read_text())
        assert original_ids==fresh_ids;result['budget_selected_case_ids_identical']=True
        result['deterministic_JSON_comparisons']=deterministic
        original_after,original_summary=tree_snapshot(SOURCE);fresh_after,fresh_summary=tree_snapshot(TEMP_SOURCE)
        assert original_after==inputs==fresh_after
        result['original_source_after']=original_summary;result['detached_worktree_after']=fresh_summary
        result['all_scientific_source_input_file_bytes_unchanged']=True
        assert {name:sha(BUNDLE/'scripts'/name)for name in scripts}==code_before
        assert sha(plan)==plan_before
        assert all((BUNDLE/p).is_file()and sha(BUNDLE/p)==h for p,h in archive_before.items())
        result['algorithm_script_sha256']=code_before;result['protocol_sha256']=plan_before
        result['archive_result_files_unchanged']=len(archive_before)
        result['original_source_git_status_after']=git(SOURCE,'status','--porcelain')
        result['detached_source_git_status_after']=git(TEMP_SOURCE,'status','--porcelain')
        result['original_point_H1_H2_fixed_equal_pp']={k:json.loads((TEMP_OUTPUT/'results/bootstrap_stability/summary.json').read_text())['observed'][k]
              for k in('H1_A_external_minus_internal_detection_pp','H2_A_external_minus_internal_review_pp','external_fixed_B_minus_A_detection_pp','external_equal_B_minus_A_detection_pp')}
        result['status']='PASS'
    except Exception as exc:
        result['status']='FAIL';result['error']=repr(exc)
    finally:
        if result['status']=='PASS':
            subprocess.run(['git','-C',str(SOURCE),'worktree','remove','--force',str(TEMP_SOURCE)],check=True,capture_output=True,text=True)
            assert TEMP_OUTPUT.parent==Path('/workspace')and(TEMP_OUTPUT/'.portable_check_created').is_file()
            shutil.rmtree(TEMP_OUTPUT)
            result['temporary_worktree_and_outputs_removed']=not TEMP_SOURCE.exists()and not TEMP_OUTPUT.exists()
        else:result['temporary_worktree_and_outputs_removed']=False
        result['completed_utc']=datetime.now(timezone.utc).isoformat();result['total_check_wall_seconds']=time.perf_counter()-start
        QA.mkdir(parents=True,exist_ok=True)
        (QA/'portable_reproduction_check.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
        lines=['# Portable reproduction check','',f"**{result['status']}** — three documented command-line entrypoints were tested in a newly created detached source worktree and new output directory.",'',
               f"Source commit: `{EXPECTED_COMMIT}`. Python: {result['environment']['python']}. Existing dependencies match exact requirements; a fresh pip installation/isolated virtual environment and remote git-clone transfer were not retested.",'',
               '## Executed commands','']
        for cmd in result['commands']:
            lines.extend(['```sh',' '.join(cmd['argv']),'```',f"Exit {cmd['exit_code']}; wall time {cmd['wall_seconds']:.3f} s.",''])
        if result['status']=='PASS':
            lines+=['## Result agreement','',
                    '| Result CSV | Data rows | Byte-identical | Full cell agreement |','| --- | ---: | --- | --- |']
            for row in result['CSV_comparisons']:
                lines.append(f"| `{row['file']}` | {row['data_rows']} | {row['byte_identical']} | {row['all_cells_numerically_or_textually_equal']} |")
            b=next(v for v in result['CSV_comparisons']if v['file']=='results/bootstrap_stability/iterations.csv')
            c=next(v for v in result['CSV_comparisons']if v['file']=='results/case_mix_decomposition_bootstrap.csv')
            lines+=['',f"Bootstrap iteration CSV SHA-256: `{b['rerun_sha256']}`; case-mix iteration CSV SHA-256: `{c['rerun_sha256']}`.",'',
                    'All selected deterministic JSON fields and budget-selected patient IDs agree exactly. Runtime, timestamps, absolute paths and branch provenance are allowed to differ and were not mistaken for numerical discrepancies.','',
                    f"All {source_before['scientific_input_files']:,} scientific input/helper files ({source_before['scientific_input_bytes']:,} bytes) had identical before/after contents in both the original and detached source trees. Aggregate byte checksum: `{source_before['scientific_input_aggregate_sha256']}`. All three algorithm scripts, the plan and all pre-existing archived result files were unchanged.",'',
                    'The initial preflight failure is retained in portable_reproduction_preflight_failure.json. It preceded all analysis execution and resulted from comparing unrelated active-checkout postal/README/package edits with the fixed commit. The successful check covers every actual scientific input/helper and the detached worktree state; it does not require unrelated packaging files in the active checkout to match the older source commit.','',
                    'The temporary worktree and output directory were removed after checks passed. The original archived results were not overwritten. This test exercises path portability in the installed pinned environment; it does not claim a new independent scientific replication or fresh dependency-installation test.']
        else:lines+=['## Failure','',result.get('error','Unknown failure'),'', 'Temporary directories were preserved for inspection.']
        lines+=['',f"Total verification wall time: {result['total_check_wall_seconds']:.3f} s."]
        (QA/'portable_reproduction_check.md').write_text('\n'.join(lines)+'\n')
        print(json.dumps({'status':result['status'],'error':result.get('error'),
                          'total_wall_seconds':result['total_check_wall_seconds'],
                          'temporary_paths_removed':result['temporary_worktree_and_outputs_removed']}))
    if result['status']!='PASS':raise SystemExit(1)


if __name__=='__main__':main()
