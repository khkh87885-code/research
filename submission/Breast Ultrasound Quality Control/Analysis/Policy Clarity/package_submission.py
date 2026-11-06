#!/usr/bin/env python3
"""Deploy the reviewed policy/budget clarification and seal its upload package."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
from urllib.parse import unquote
from datetime import datetime,timezone
import hashlib,json,re,shutil,subprocess
from docx import Document

TASK=Path('/workspace/policy_clarity')
ROOT=Path('/workspace/research_source')
DEST=ROOT/'submission/Breast Ultrasound Quality Control'
OUT=TASK/'outputs'
PREFIX='Breast Ultrasound Quality Control'
BASE='4245aaa10a9ce1589807fbdb74b20f59893ec6ee'
CSV_NAME=PREFIX+' Matched Review Counts.csv'
QA=TASK/'qa/independent_content_layout_qa.json'
QA_SHA='adfe3e95683b601df44eba46d30847c24a18ac51645f3e6527563147ed5c4862'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()
def copy(a,b):b.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(a,b);assert sha(a)==sha(b)
def publishable(p):return p.is_file()and '__pycache__'not in p.parts and p.suffix!='.pyc'

if __name__=='__main__':
    assert git('rev-parse','HEAD')==BASE
    raw=subprocess.check_output(['git','status','--porcelain=v1','-uall','-z'],cwd=ROOT).decode()
    dirty={x[3:]for x in raw.split('\0')if x}
    if dirty:
        # A conservative word-count guard stopped the first deployment before
        # it was sealed or published. Verify those exact owned bytes before
        # completing the reviewed, shorter delivery.
        previous=json.loads((TASK/'partial_deployment.json').read_text())
        assert dirty<=set(previous)
        for name,value in previous.items():assert sha(ROOT/name)==value,name
    assert sha(QA)==QA_SHA
    q=json.loads(QA.read_text());assert q['status']=='PASS'and q['final_documents_pending']is False
    assert all(c['status']=='PASS'for c in q['checks'])
    for name,value in q['hashes'].items():assert sha(TASK/name)==value,name
    primary=Document(OUT/(PREFIX+' Manuscript.docx'))
    word_count=len(re.findall(r'\S+',' '.join(p.text for p in primary.paragraphs)+' '+' '.join(c.text for t in primary.tables for row in t.rows for c in row.cells)))
    assert word_count<6000,word_count
    # Deploy only named delivery artifacts, leaving the local illustrated DOCX
    # as a review/build intermediate rather than another Main Document.
    outputs=[p for p in OUT.iterdir()if p.is_file()and p.name not in ['root README.md',PREFIX+' Illustrated Manuscript.docx']]
    for p in outputs:copy(p,DEST/p.name)
    for p in (OUT/'Figures').iterdir():copy(p,DEST/'Figures'/p.name)
    copy(OUT/'root README.md',ROOT/'README.md')
    copy(TASK/'analysis/equal_review_counts.csv',DEST/'Analysis/Table Data'/CSV_NAME)
    work=DEST/'Analysis/Policy Clarity';audit=DEST/'Audit/Policy Clarity'
    for name in ['analyze_same_k.py']:
        copy(TASK/'analysis'/name,work/name)
    for p in (TASK/'scripts').glob('*.py'):copy(p,work/p.name)
    copy(TASK/'analysis/equal_review_counts.csv',work/CSV_NAME)
    for p in [TASK/'analysis/same_k_report.json',TASK/'analysis/same_k_report.md',
              TASK/'evidence/related_work_comparison.json',TASK/'evidence/related_work_comparison.md',
              TASK/'evidence/figure4_qa.json',TASK/'evidence/figure4_caption.md',
              TASK/'evidence/manuscript_edits.json',TASK/'evidence/illustrated_build.json',
              TASK/'evidence/final_render_validation.json',
              QA,TASK/'qa/independent_content_layout_qa.md']:
        copy(p,audit/p.name)
    copy(ROOT/'planning/formal_experiment_protocol.md',audit/'original protocol.md')
    assert not any(p.name.startswith('prior_source_')for p in audit.iterdir())
    # Keep the few verbatim source passages in one evidence format only.
    public_summary=audit/'related_work_comparison.md'
    public_summary.write_text('\n'.join(line for line in public_summary.read_text().splitlines()if not(line.lstrip().startswith('-')and '\u201c'in line))+'\n')
    (work/'README.md').write_text('''# Matched review-count presentation

The same original BrEaST252 case scores are ranked by descending risk and the stored patient-identifier string as a lexicographic tie-breaker. The added descriptive K33/K35 points use the previously reported locked-cutoff review volumes; K50 repeats the original protocol supplementary budget. No new inference, calibration, interval, hypothesis test or resampling is run. The existing H1–H3, original Top50 interval and all original scores remain.

The named CSV is also uploaded as supplementary data under Analysis/Table Data. Source scores, curves and fixed primary references remain in ../../Reproducibility. Their source hashes and full paired count derivation are in ../../Audit/Policy Clarity/same_k_report.json. The original source commit is4245aaa10a9ce1589807fbdb74b20f59893ec6ee.

The standalone scripts retain their original /workspace/research_source and /workspace/policy_clarity paths. To replay the scientific lookup, use the repository at the documented source commit, set ROOT/BASE/OUT in analyze_same_k.py for the local checkout, and run it with Python. It reads records/validation_cases.csv, review_curve_counts.csv, study_lock.json and reference JSON from Reproducibility, verifies input hashes and regenerates the three-row CSV and the audit. draw_figure4.py reads the same frozen references and this CSV; adjust BASE/SOURCE paths for the local workspace. build_manuscripts.py uses an immutable copy of the source submission in TASK/source and writes TASK/outputs. package_submission.py is the original hash-gated deployment script for this managed workspace.

Only concise source comparisons are publicly archived. Temporary complete article retrievals are not bundled. The evidence compares the two closest papers without claiming first fixed-budget screening or absence of inaccessible methods. Current DOCX/PDF findings do not constitute a direct WPS or Microsoft Word runtime test.
''')
    names=[PREFIX+' Manuscript.docx',*[f'Figures/{PREFIX} Figure {i}.png'for i in range(1,6)],
           PREFIX+' Ethical and Legal Declarations.docx',PREFIX+' Cover Letter.docx',
           PREFIX+' Supplementary Material.docx',PREFIX+' Supplementary Figure S6.pdf',
           PREFIX+' Data and Code Availability.docx',PREFIX+' Reviewer Candidates.docx',
           PREFIX+' Additional Quality Control Metrics.csv',
           'Analysis/Table Data/'+PREFIX+' Table S13 Unrounded Comparisons.csv',
           'Analysis/Table Data/'+CSV_NAME,PREFIX+' Submission Guide.md']
    assert len(names)==16
    zpath=ROOT/'submission'/(PREFIX+' Submission Files.zip')
    with ZipFile(zpath,'w',ZIP_DEFLATED,compresslevel=9)as z:
        for name in names:assert '_'not in name;z.write(DEST/name,name)
    with ZipFile(zpath)as z:
        assert z.testzip()is None and z.namelist()==names
        for name in names:assert z.read(name)==(DEST/name).read_bytes()
    assert zpath.stat().st_size<12_300_000
    for name in [PREFIX+' Supplementary Material.docx',PREFIX+' Supplementary Material.pdf',PREFIX+' Supplementary Figure S6.pdf']:
        assert(DEST/name).stat().st_size<10_000_000
    for p in [ROOT/'README.md',DEST/'README zh.md']:
        for url in re.findall(r'\]\(([^)]+)\)',p.read_text()):
            if '://'not in url and not url.startswith('#'):
                assert ' 'not in url
                assert(p.parent/unquote(url)).exists(),(p,url)
    status={'created_utc':datetime.now(timezone.utc).isoformat(),'source_commit':BASE,
            'scope':'Related-work positioning and matched-count presentation',
            'main_abstract_words_including_labels':188,'main_visible_word_count_including_tables_and_references':word_count,
            'main_scientific_tables_and_cells':[3,66],'supplement_tables_and_cells':[19,898],
            'native_math_groups':[3,2],'original_primary_values_and_intervals_preserved':True,
            'K33_K35_role':'post hoc descriptive extraction from archived ranking curves',
            'K50_role':'original protocol supplementary budget, repeated in matched-count display',
            'new_model_inference':False,'new_resampling':False,'new_intervals_or_hypothesis_tests':False,
            'external_patients_and_low_quality':[252,16],'upload_materials_including_guide':names,
            'zip_bytes':zpath.stat().st_size,'zip_sha256':sha(zpath),'independent_qa_sha256':QA_SHA,
            'native_word_or_wps_executed':False,'journal_submission_executed':False}
    (audit/'preparation status.json').write_text(json.dumps(status,indent=2)+'\n')
    mf=PREFIX+' File Manifest.json';files=[{'path':p.relative_to(DEST).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)}for p in sorted(DEST.rglob('*'))if publishable(p)and p.name!=mf]
    (DEST/mf).write_text(json.dumps({'paper_title':'Fixed-threshold transfer and equal-review ranking in breast ultrasound segmentation quality control','files':files},indent=2)+'\n')
    known={x.split()[2]for x in git('ls-tree','-r',BASE).splitlines()};entries=[]
    for p in [ROOT/'README.md',zpath]+sorted(p for p in DEST.rglob('*')if publishable(p)):
        data=p.read_bytes();assert len(data)<12_300_000
        blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        entries.append({'path':p.relative_to(ROOT).as_posix(),'local_path':str(p),'bytes':len(data),'sha':blob,'already_in_base':blob in known})
    (TASK/'upload_manifest.json').write_text(json.dumps({'base_commit':BASE,'base_tree':git('rev-parse',BASE+'^{tree}'),'entries':entries},indent=2)+'\n')
    print(json.dumps({'deployed_files':len(files)+1,'upload_paths':len(entries),'zip_bytes':zpath.stat().st_size,'new_blob_bytes':sum(e['bytes']for e in entries if not e['already_in_base']),'all_visible_main_words':word_count},indent=2))
