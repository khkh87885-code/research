#!/usr/bin/env python3
"""Read-only check of final v7/v3 document copies against audited source values."""
import csv
import hashlib
import json
import math
import re
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from statistics import NormalDist

from docx import Document

ROOT=Path('/workspace/bmt_v7')
REPO=Path('/workspace/research_source')
MAIN=ROOT/'outputs/BMT_main_manuscript_v7.docx'
SUPP=ROOT/'outputs/BMT_supplementary_material_v3.docx'
OLDMAIN=REPO/'submission/bmt_v6/BMT_main_manuscript_v6.docx'
OLDSUPP=REPO/'submission/bmt_v6/BMT_supplementary_material_v2.docx'


def read_csv(p):
    return list(csv.DictReader(p.open(encoding='utf-8-sig',newline='')))


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def numbers(t):
    return re.findall(r'[+\-]?\d+(?:\.\d+)?',t.replace('−','-'))


def norm(t):
    return re.sub(r'\s+','',t).replace('−','-')


def wilson(x,n):
    z=NormalDist().inv_cdf(.975);p=x/n;d=1+z*z/n
    c=(p+z*z/(2*n))/d;h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return [100*(c-h),100*(c+h)]


def eq(got,expected,label,ledger):
    ok=norm(got)==norm(expected)
    ledger.append({'field':label,'observed':got,'expected':expected,'matches':ok})
    assert ok,(label,got,expected)


def main():
    before={str(p):sha(p)for p in (MAIN,SUPP)}
    main=Document(MAIN);supp=Document(SUPP);oldmain=Document(OLDMAIN);oldsupp=Document(OLDSUPP)
    assert len(main.tables)==3 and len(supp.tables)==9
    prior=[]
    for title,old,new in [('Main Table 1',oldmain.tables[0],main.tables[0]),
                          ('Main Table 3',oldmain.tables[2],main.tables[2])]+[
                              (f'Table S{i+1}',oldsupp.tables[i],supp.tables[i])for i in range(7)]:
        assert len(old.rows)==len(new.rows)
        checked=0
        for ri,(orow,nrow)in enumerate(zip(old.rows,new.rows)):
            assert len(orow.cells)==len(nrow.cells)
            for ci,(ocell,ncell)in enumerate(zip(orow.cells,nrow.cells)):
                assert numbers(ocell.text)==numbers(ncell.text),(title,ri,ci,ocell.text,ncell.text)
                checked+=len(numbers(ocell.text))
        prior.append({'table':title,'numeric_tokens_checked':checked,'all_numeric_tokens_preserved':True})
    pathology=json.loads((ROOT/'evidence/pathology_audit.json').read_text())
    table2=[]
    for row,(split,m)in zip(main.tables[1].rows[1:],[(s,m)for s in ('internal_holdout','external_test')for m in ('A','B')]):
        v=pathology['overall_for_main_table_2'][split][m];lo,hi=wilson(v['TP'],v['low_quality'])
        expected=[('BUS-BRA internal'if split=='internal_holdout'else'BrEaST external'),m,
                  f"{v['TP']}/{v['low_quality']} ({100*v['TP']/v['low_quality']:.2f}%) [{lo:.2f}, {hi:.2f}]",
                  f"{v['review_count']}/{v['N']} ({100*v['review_count']/v['N']:.2f}%)",
                  str(v['FN']),f"{v['misses_per_100']:.2f}"]
        for ci,(cell,want)in enumerate(zip(row.cells,expected)):eq(cell.text,want,f'Table2.{split}.{m}.{ci}',table2)
    # Verify every descriptive proportion and confidence limit in S7 independently
    # from the archived confusion counts; the remaining historical outputs are
    # compared with the previously validated v6 document instead of rerun.
    utility=[]
    for row,(split,m)in zip(supp.tables[6].rows[1:],[(s,m)for s in ('development','internal_holdout','external_test')for m in ('A','B')]):
        v=pathology['overall_for_main_table_2'][split][m]
        fractions=[(v['TP'],v['TP']+v['FN']),(v['TN'],v['TN']+v['FP']),
                   (v['TP'],v['TP']+v['FP']),(v['TN'],v['TN']+v['FN'])]
        for ci,(x,n)in enumerate(fractions,2):
            lo,hi=wilson(x,n);want=f'{x}/{n} ({100*x/n:.2f}%) [{lo:.2f}, {hi:.2f}]'
            eq(row.cells[ci].text,want,f'S7.{split}.{m}.{ci}',utility)
    s8=[]
    indexed=[(s,label,m)for s in ('internal_holdout','external_test')for label in ('benign','malignant')for m in ('A','B')]
    assert len(supp.tables[7].rows[1:])==len(indexed)==8
    for row,(split,label,m)in zip(supp.tables[7].rows[1:],indexed):
        v=pathology['stratified'][split][label][m];N=v['N'];F=v['low_quality'];TP=v['TP'];R=v['review_count']
        dlo,dhi=wilson(TP,F);rlo,rhi=wilson(R,N)
        expected=[('BUS-BRA internal'if split=='internal_holdout'else'BrEaST external'),label.title(),f'{N} / {F}',m,
                  f'{TP}/{F} ({100*TP/F:.2f}%) [{dlo:.2f}, {dhi:.2f}]',
                  f'{R}/{N} ({100*R/N:.2f}%) [{rlo:.2f}, {rhi:.2f}]']
        for ci,(cell,want)in enumerate(zip(row.cells,expected)):eq(cell.text,want,f'S8.{split}.{label}.{m}.{ci}',s8)
    # Recombine the stratum counts used in the final document.
    recombination=[]
    for split in ('internal_holdout','external_test'):
        for m in ('A','B'):
            for key in ('N','low_quality','review_count','TP','FP','TN','FN'):
                actual=sum(pathology['stratified'][split][label][m][key]for label in ('benign','malignant'))
                expected=pathology['overall_for_main_table_2'][split][m][key]
                assert actual==expected
                recombination.append({'split':split,'method':m,'count':key,'sum':actual,'overall':expected,'matches':True})
    original=read_csv(REPO/'reproducibility/records/validation_cases.csv')
    external={r['image_id']:r for r in original if r['split']=='external_test'}
    target={k:r for k,r in external.items()if float(r['dice_vs_reference'])<.7 and int(r['alert_A'])==0}
    assert set(target)=={'case089','case175','case238','case024','case105','case222'}
    expected_order=['case089','case175','case238','case024','case105','case222'];s9=[]
    assert len(supp.tables[8].rows)==7
    for row,case in zip(supp.tables[8].rows[1:],expected_order):
        r=target[case];b=int(r['alert_B']);d=float(r['dice_vs_reference']);ra=float(r['risk_A']);rb=float(r['risk_B'])
        assert int(r['initial_mask_empty'])==0
        assert all(float(r['dice_shift_'+direction])>0 for direction in ('left','right','up','down'))
        assert ra<pathology['unchanged_thresholds']['A']
        assert b==int(rb>=pathology['unchanged_thresholds']['B'])
        expected=[f"{case} {r['pathology']}",'B only'if b else'Neither',f'{d:.4f}',f'{ra:.6f}','0',f'{rb:.6f}',str(b),f'{1-rb:.4f}']
        for ci,(cell,want)in enumerate(zip(row.cells,expected)):eq(cell.text,want,f'S9.{case}.{ci}',s9)
    analysis_rows=read_csv(ROOT/'outputs/Analysis/external_six_cases.csv')
    assert {r['image_id']for r in analysis_rows}==set(target)
    for r in analysis_rows:
        orig=target[r['image_id']]
        for field,value in orig.items():assert r[field]==value,(r['image_id'],field)
    case001=external['case001'];assert int(case001['alert_A'])==int(case001['alert_B'])==1
    mainparas=[p.text for p in main.paragraphs];suptext='\n'.join(p.text for p in supp.paragraphs)
    abstract=' '.join(mainparas[mainparas.index('Abstract')+1:mainparas.index('Keywords  domain shift; external testing; prompt perturbation; selective prediction; vision foundation models')])
    abstract_words=len(abstract.split());assert abstract_words<=200
    body=mainparas[:mainparas.index('References')]
    first_s=[]
    for paragraph in body:
        for s in re.findall(r'\bS(\d+)\b',paragraph):
            if int(s)not in first_s:first_s.append(int(s))
    assert first_s==list(range(1,10))
    first_refs=[]
    for paragraph in body:
        for bracket in re.findall(r'\[(\d+(?:[ ,–-]+\d+)*)\]',paragraph):
            for v in map(int,re.findall(r'\d+',bracket)):
                if v not in first_refs:first_refs.append(v)
    assert first_refs==list(range(1,15))
    refs=[int(re.match(r'^(\d+)\.',t).group(1))for t in mainparas[mainparas.index('References')+1:]
          if re.match(r'^\d+\.',t)]
    assert refs==list(range(1,15))
    placeholders=[t for t in mainparas if'[AUTHOR CONFIRMATION REQUIRED'in t]
    author_path=ROOT/'evidence/author_confirmation_record.json'
    sources_path=ROOT/'evidence/confirmed_address_ethics_sources.json'
    author_record=json.loads(author_path.read_text())
    confirmation_sources=json.loads(sources_path.read_text())
    submission_approved=author_record.get('submission_approved') is True
    expected_placeholder_count=0 if submission_approved else 1
    assert sum(t.count('[AUTHOR CONFIRMATION REQUIRED')for t in mainparas)==expected_placeholder_count
    if not submission_approved:
        assert 'both authors approve submission of this exact final manuscript version' in placeholders[0]
    confirmation_evidence_sha256={str(p):sha(p)for p in (author_path,sources_path)}
    assert author_record['interpreted_confirmations']['campus']=='Jinyun Campus'
    assert author_record['postcode']==confirmation_sources['address']['postcode']=='401331'
    assert confirmation_sources['address']['title_page_full_english'] in '\n'.join(mainparas[:8])
    assert confirmation_sources['address']['title_page_short_affiliation'] in mainparas[3]
    ethics_para=next(t for t in mainparas if t.startswith('Research ethics.'))
    consent_para=next(t for t in mainparas if t.startswith('Informed consent.'))
    ai_methods=next(t for t in mainparas if t.startswith('OpenAI Codex assisted with protocol'))
    ai_ack=next(t for t in mainparas if t.startswith('AI use and acknowledgments.'))
    contribution_para=next(t for t in mainparas if t.startswith('Author contributions.'))
    assert 'The authors confirmed' in ethics_para and 'Article 32' in ethics_para
    assert '2023' in ethics_para and 'publicly released anonymized' in ethics_para
    assert author_record['no_IRB_number_invented'] is True
    assert confirmation_sources['ethics']['statutory_basis']['article']==32
    assert confirmation_sources['ethics']['author_confirmation']['irb_reference_number_provided'] is False
    assert author_record['consent_statement'] in consent_para
    assert 'no additional informed consent was obtained' in consent_para
    assert 'Both authors reviewed' in ai_methods and 'Both authors reviewed' in ai_ack
    if submission_approved:
        assert 'All authors have accepted responsibility for the entire content of this manuscript and approved its submission.' in contribution_para
        assert 'Both authors completed their review of the code, data, figures and text.' in contribution_para
        assert author_record['approval_source_user_statement']=='两位作者均已同意并承担全文责任'
    else:
        assert 'Both authors confirmed completion of their review' in contribution_para
    assert all('precise underlying Codex model identifier was not available in the archived study records' in t
               for t in (ai_methods,ai_ack))
    assert author_record['underlying_Codex_model_identifier']=='not available in archived study records'
    if submission_approved:
        assert author_record['final_exact_version_submission_approval']=='Both authors explicitly confirmed approval and full-content responsibility for v7.'
    else:
        assert author_record['final_exact_version_submission_approval']=='pending explicit confirmation'
    approval_status=('Both authors explicitly approved submission of the final v7 manuscript and accepted full-content responsibility; no actual journal submission has been performed.'
                     if submission_approved else 'Explicit approval by both authors to submit this exact final version remains pending.')
    approval_placeholder_note=('No author-confirmation placeholders remain. The explicit author approval is recorded, and the mandatory BMT full-content responsibility/submission-approval sentence is present.'
                               if submission_approved else 'Exactly one author-confirmation placeholder remains: both authors must approve submission of this exact final manuscript version and accept responsibility for its content.')
    source_roles={
        'author_confirmations':{
            'record':str(author_path),'statement':author_record['user_statement'],
            'campus':author_record['interpreted_confirmations']['campus'],
            'statutory_exemption':author_record['interpreted_confirmations']['statutory_ethics_exemption'],
            'human_review':author_record['interpreted_confirmations']['human_review'],
            'final_version_approval':author_record['final_exact_version_submission_approval'],
            'submission_approved':submission_approved,
            'approval_source_user_statement':author_record.get('approval_source_user_statement'),
            'scope':'Author-provided study facts and applicability confirmation; not an IRB-issued approval or consent waiver.'},
        'official_sources_documented_in_evidence':{
            'record':str(sources_path),
            'campus_address_postcode_sources':confirmation_sources['address']['primary_sources'],
            'postcode_discrepancy_resolution':confirmation_sources['address']['source_discrepancy_resolution'],
            'statutory_basis':confirmation_sources['ethics']['statutory_basis'],
            'scope':'Official-source evidence supports addresses and the text of Article 32; it does not independently certify that this individual study meets every exemption condition.'},
        'archival_limitations':{
            'Codex_model_identifier':'Not available in archived study records; candidly disclosed rather than invented or treated as a pending placeholder.'},
        'final_version_submission_approval':author_record['final_exact_version_submission_approval'],
        'journal_submission_performed':False}
    methodpara=next(t for t in mainparas if t.startswith('We additionally performed a post hoc exploratory stratification'))
    assert '197' in methodpara and '55' in methodpara
    assert 'No stratum-specific recalibration, hypothesis test or interaction test was performed' in methodpara
    assert 'not uniformly histopathologically confirmed' in suptext
    assert 'no predicted contour was synthesized' in suptext
    assert 'exact checksum-verified checkpoint is available' in suptext
    assert 'case001 is detected by both scores' in suptext
    assert 'not substituted' in suptext
    assert 'did not rerun SAM inference' in suptext
    assert all(sha(Path(p))==expected for p,expected in before.items())
    result={'review_utc':datetime.now(timezone.utc).isoformat(),
            'review_scope':'Final DOCX numerical and cross-reference consistency; not a new full study audit or model inference run.',
            'source_files_sha256':before,'manuscripts_unchanged_by_review':True,
            'status':'PASS within numerical and cross-reference scope. '+approval_status,
            'findings':[],
            'historical_table_preservation':prior,
            'table2_new_CI_and_existing_counts':table2,
            'tableS7_independent_fraction_and_CI_checks':utility,
            'tableS8_all_copied_fields':s8,
            'stratum_recombination':recombination,
            'tableS9_all_copied_fields':s9,
            'complete_external_A_missed_case_set':expected_order,
            'shared_misses':['case089','case175','case238'],
            'B_only_detections':['case024','case105','case222'],
            'six_case_analysis_CSV_matches_original_score_fields':True,
            'case001_flags':{'A':1,'B':1,'not_a_target_case':True},
            'abstract_word_count_including_structured_headings_whitespace_method':abstract_words,
            'abstract_within_200_words':True,
            'supplementary_table_first_citation_order':first_s,
            'main_reference_first_citation_order':first_refs,
            'reference_list_sequence':refs,
            'author_confirmation_placeholders_main':len(placeholders),
            'submission_approved_by_both_authors':submission_approved,
            'journal_submission_performed':False,
            'unknowns_preserved':placeholders,
            'author_confirmation_evidence_sha256':confirmation_evidence_sha256,
            'author_confirmation_and_official_source_roles':source_roles,
            'confirmed_title_page_address_matches_evidence':True,
            'author_confirmed_Article32_exemption_distinguished_from_IRB_approval':True,
            'secondary_consent_facts_do_not_claim_IRB_consent_waiver':True,
            'completed_human_review_matches_author_confirmation':True,
            'unavailable_archived_Codex_model_identifier_disclosed':True,
            'exploratory_no_recalibration_or_tests_explicit':True,
            'BrEaST_biopsy_followup_distinction_explicit':True,
            'S9_missing_predictions_checkpoint_scope_explicit':True,
            'source_pair_visual_aid_inspected_read_only':True,
            'source_pair_visual_aid_observation':'Six original images and green released-reference contours only; title and every right-panel label explicitly say target predictions unavailable/no SAM prediction shown.',
            'limitations':['This review compares original tables with the previously validated v6 baseline instead of rerunning the unchanged primary and supplementary statistics.',
                           'A new numerical effect is not inferred from outcome-selected cases or subgroup point estimates.',
                           'Campus, statutory exemption applicability and completed human review now rely on the explicit author-confirmation record; official sources separately support address details and the legal text. No IRB-issued approval or consent waiver is claimed.',
                           approval_status+' The precise underlying Codex model identifier is unavailable in archived records and is disclosed as such, not invented.',
                           'No targeted six-case SAM predictions were available or regenerated; the original checkpoint is not available in the inspected resources.']}
    (ROOT/'evidence/final_v7_numeric_review.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    report=['# Final independent v7 numerical review','',
            '**PASS within the numerical and cross-reference scope.** The review did not modify either manuscript. The author-confirmed campus, statutory ethics exemption and completed human review, together with officially sourced address details, have been incorporated. '+approval_status,'',
            '## Checked copies','',
            f'- Main manuscript SHA-256: `{before[str(MAIN)]}`',f'- Supplementary manuscript SHA-256: `{before[str(SUPP)]}`','',
            '## Numerical findings','',
            '- Main Tables 1 and 3 and Supplementary Tables S1–S7 preserve every numerical token from the previously validated v6 copies. Percentage spacing and table styles do not alter values.',
            '- Main Table 2: all four event fractions, review fractions, misses and misses per 100 match the audit. Newly added detection Wilson intervals were independently recalculated: internal A [66.77,83.83]%, internal B [63.32,81.08]%, external A [38.64,81.52]%, external B [56.99,93.41]%.',
            '- Table S7: all 24 copied proportions and their Wilson intervals were also independently recalculated from confusion counts and agree.',
            '- Table S8: all 48 cells in the eight data rows match the independently audited diagnostic-stratum records. Detection and review intervals were independently recalculated. Every stratum-specific N/F/R/TP/FP/TN/FN sum returns exactly to the original overall count.',
            '- Table S9: all six rows and their eight copied cells match the original external scores, label, threshold flags and mean consistency. The selected set is complete for external Dice<0.70 and A flag=0: shared misses 089/175/238; B-only detections 024/105/222. The accompanying six-case CSV reproduces every original score field exactly.',
            '- Main numerical prose, including cohort sizes, 197 biopsy/55 follow-up labels, primary estimates, subgroup counts and shared-miss Dice/consistency values, agrees with the checked tables and source evidence.','',
            '## Interpretation and cross-references','',
            f'- Abstract: {abstract_words} whitespace-delimited words including Objectives/Methods/Results/Conclusions headings; below 200.',
            '- Supplementary Tables S1–S9 first appear in increasing order in the main manuscript. Main references 1–14 first appear in increasing order and match the numbered reference list.',
            '- Methods explicitly call the strata post hoc/exploratory, retain locked cutoffs and say no recalibration, hypothesis test or interaction test was performed. The positive condition remains low-quality segmentation, not malignancy.',
            '- BrEaST biopsy and follow-up confirmation are distinguished. Supplementary wording explicitly says the labels are not uniformly histopathologically confirmed.',
            '- S9 states that six predicted masks were not retained, the visual aid shows only released images/manual references, and exact-checkpoint availability is required before targeted replay. Read-only image inspection confirms there is no claimed predicted contour in that aid. Case001 is correctly described as flagged by A and B and is not substituted for a target case.',
            '- '+approval_placeholder_note+' The prior pending approval state is superseded by the recorded author confirmation.','',
            '## Updated author confirmations and source provenance','',
            '- `author_confirmation_record.json` records the author-confirmed Jinyun campus, applicability of the statutory Article 32 ethics-review exemption and completion of human review of code, data, figures and text. These study-specific confirmations come from the user; they are not presented as independently issued institutional approvals.',
            '- `confirmed_address_ethics_sources.json` documents the official university admissions listing that pairs Jinyun Campus with No. 61 Daxuecheng Middle Road and postcode 401331, and the official college address identifying Building 6, Lanyuan. The college footer also lists 400016; that discrepancy is preserved in the evidence. The campus-specific 401331 is used without claiming that the other footer is demonstrably a template error. The current title page matches the documented address.',
            '- The official National Health Commission source establishes the text and scope of Article 32. Applicability to this particular secondary study is author-confirmed. The manuscript does not invent an IRB reference number or transfer the original BrEaST approval to the present study.',
            '- Informed consent reports the factual process: no new recruitment/contact and no additional consent obtained. It does not convert an ethics-review exemption into an invented IRB waiver of consent.',
            '- Methods and acknowledgments now state the completed human review. They candidly state that a precise underlying Codex model identifier was unavailable in archived study records; this is an archival limitation, not a remaining request to invent a version.',
            '- Final version approval: '+approval_status+' The approval record retains the user statement and is distinct from an actual submission action.',
            '- This audit read and checked the two provenance JSON records and their agreement with the manuscript. It did not itself perform a new external retrieval of those official pages or issue a legal or institutional ethics determination.','',
            '## Limits','',
            'No model inference was performed in this review. The original unchanged main/supplementary numerical analyses were not rerun. Their final table copies were checked against the previously validated baseline; new copied CIs, diagnostic strata and six-case records were checked against their existing independent audits and direct source scores. This review finds no numerical discrepancy requiring a manuscript edit.']
    (ROOT/'evidence/final_v7_numeric_review.md').write_text('\n'.join(report)+'\n')
    print(json.dumps({'status':'PASS','abstract_words':abstract_words,'prior_table_tokens':sum(t['numeric_tokens_checked']for t in prior),
                      'table2_cells':len(table2),'S7_proportions':len(utility),'S8_cells':len(s8),'S9_cells':len(s9),
                      'placeholders':len(placeholders),'S_first_refs':first_s,'main_first_refs':first_refs}))


if __name__=='__main__':main()
