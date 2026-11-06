#!/usr/bin/env python3
"""Build post hoc v8 supplementary-table data without changing source artifacts."""
import csv
import gzip
import hashlib
import io
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

SOURCE = Path('/workspace/research_source')
DEST = Path('/workspace/bmt_v8/evidence')
DATA = DEST / 'table_data'
CLOUD = SOURCE / 'experiments/cloud_validation_v1/results'
REPLAY = SOURCE / 'experiments/six_case_replay_v1'
DATA.mkdir(parents=True, exist_ok=True)


def read_json(path):
    return json.loads(path.read_text())


def read_csv(path):
    if path.suffix == '.gz':
        with gzip.open(path, 'rt', newline='') as f:
            return list(csv.DictReader(f))
    with path.open(newline='') as f:
        return list(csv.DictReader(f))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def csv_write(path, headers, rows):
    with path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)


def csv_dict_write(path, rows):
    assert rows
    csv_write(path, list(rows[0]), [list(row.values()) for row in rows])


def num(x):
    return float(x)


def integer(x):
    return int(x)


def signed(x, digits=2):
    value = float(x)
    if round(value, digits) == 0:
        value = 0.0
    return f'{value:+.{digits}f}' if value else f'{value:.{digits}f}'


def interval(est, low, high, factor=1):
    return f'{signed(float(est)*factor)} [{signed(float(low)*factor)}, {signed(float(high)*factor)}]'


def ci_only(low, high):
    return f'[{signed(low)}, {signed(high)}]'


def counted(n, denominator):
    return f'{int(n)}/{int(denominator)} ({100*float(n)/float(denominator):.2f})'


def countpct(n, denominator):
    return f'{int(n)} ({100*float(n)/float(denominator):.2f})'


source_files = [
    CLOUD/'budget_transfer/calibration.csv',
    CLOUD/'budget_transfer/performance.csv',
    CLOUD/'budget_transfer/paired_contrasts.csv',
    CLOUD/'budget_transfer/results.json',
    CLOUD/'bootstrap_stability/summary.json',
    CLOUD/'bootstrap_stability/iterations.csv.gz',
    CLOUD/'case_mix_decomposition.csv',
    CLOUD/'case_mix_decomposition.json',
    CLOUD/'case_mix_decomposition_bootstrap.csv.gz',
    REPLAY/'reports/six_case_summary.csv',
    REPLAY/'reports/all_48_numeric_comparisons.csv',
    REPLAY/'predictions/targeted_rerun_receipt.json',
    REPLAY/'qa/postrun_review.json',
    REPLAY/'runtime_resource.json',
] + sorted((REPLAY/'predictions').glob('*_targeted_rerun.npz'))
hashes_before = {str(p.relative_to(SOURCE)): sha(p) for p in source_files}

calibration = read_csv(CLOUD/'budget_transfer/calibration.csv')
performance = read_csv(CLOUD/'budget_transfer/performance.csv')
contrasts = read_csv(CLOUD/'budget_transfer/paired_contrasts.csv')
budget_json = read_json(CLOUD/'budget_transfer/results.json')
bootstrap = read_json(CLOUD/'bootstrap_stability/summary.json')
mix = read_csv(CLOUD/'case_mix_decomposition.csv')
mix_json = read_json(CLOUD/'case_mix_decomposition.json')
six = read_csv(REPLAY/'reports/six_case_summary.csv')
comparison = read_csv(REPLAY/'reports/all_48_numeric_comparisons.csv')
review = read_json(REPLAY/'qa/postrun_review.json')
receipt = read_json(REPLAY/'predictions/targeted_rerun_receipt.json')

tables = []


def add(tid, title, headers, rows, notes, widths=None):
    assert all(len(row) == len(headers) for row in rows), tid
    item = dict(id=tid, main_table_id=tid.rstrip('ABCDE'), title=title,
                headers=headers, rows=rows, notes=notes,
                classification='Post hoc exploratory',
                csv=f'table_data/{tid}.csv')
    if widths:
        item['column_widths_hint'] = widths
    tables.append(item)
    csv_write(DATA/f'{tid}.csv', headers, rows)


budgets = sorted({num(r['target_budget']) for r in calibration})
assert budgets == [.05,.10,.15,.20,.25,.30,.40,.50]
cal = {(num(r['target_budget']),r['method']):r for r in calibration}
rows=[]
for b in budgets:
    a,c = cal[(b,'A')],cal[(b,'B')]
    assert a['R']==c['R'] and a['N']==c['N']
    rows.append([f'{100*b:.0f}', f"{num(a['threshold']):.9f}", f"{num(c['threshold']):.9f}",
                 counted(a['R'],a['N']),counted(a['TP'],a['F']),counted(c['TP'],c['F'])])
add('S10A','Table S10. Complete post hoc review-budget scan. Panel A: development calibration.',
    ['Target budget (%)','A threshold','B threshold','Reviews R/N (%)','A detected TP/F (%)','B detected TP/F (%)'], rows,
    ['Post hoc exploratory analysis of the unchanged development cohort (N=213; low-quality cases F=24). A is confidence-based risk; B is prompt-instability risk. Low quality is reference Dice <0.70.',
     'Each threshold minimizes the absolute difference from the target review fraction using development risks only. Risk ties are kept together; a zero-review candidate is included; equally close candidates select fewer reviews. All selected candidates here are nonzero. Displayed thresholds are rounded; analyses use full-precision stored thresholds.',
     'R is the number selected for review; TP is the number of low-quality cases selected; F is the number of low-quality cases. Percentages in count cells use the displayed denominator. Settings were fixed before these new computations, not preregistered for the original study.'],
    [0.75,0.93,0.93,1.05,1.05,1.05])

perf={(num(r['target_budget']),r['split'],r['mode'],r['method']):r for r in performance}
paired={(num(r['target_budget']),r['split'],r['mode']):r for r in contrasts}
panels=[('B','internal_holdout','development_calibrated_threshold','BUS-BRA internal holdout: development-calibrated thresholds'),
        ('C','internal_holdout','test_cohort_equal_review','BUS-BRA internal holdout: test-cohort equal review'),
        ('D','external_test','development_calibrated_threshold','BrEaST external test: development-calibrated thresholds'),
        ('E','external_test','test_cohort_equal_review','BrEaST external test: test-cohort equal review')]
for panel,split,mode,label in panels:
    equal_review = mode == 'test_cohort_equal_review'
    rows=[]
    for b in budgets:
        a,c=perf[(b,split,mode,'A')],perf[(b,split,mode,'B')]
        p=paired[(b,split,mode)]
        rows.append([f'{100*b:.0f}',counted(a['R'],a['N']),counted(c['R'],c['N']),
                     counted(a['TP'],a['F']),counted(c['TP'],c['F']),
                     interval(p['detection_difference_pp'],p['detection_ci95_low_pp'],p['detection_ci95_high_pp']),
                     '0 (by design)' if equal_review else
                     interval(p['review_difference_pp'],p['review_ci95_low_pp'],p['review_ci95_high_pp'])])
    population='N=851; F=93' if split=='internal_holdout' else 'N=252; F=16'
    half_budget_note = 'Internal 50% therefore uses K=425.' if split=='internal_holdout' else 'External 50% therefore uses K=126.'
    policy=('The development thresholds in Panel A are transferred without test-cohort recalibration. Therefore actual review fractions may differ from the target and between A and B.'
            if mode=='development_calibrated_threshold' else
            'Each method selects the same K highest-risk cases within this test cohort. K is the nearest integer to target budget × N, with ties selecting fewer. '+half_budget_note+' Ranking is risk descending, followed by the exact archived patient-identifier string; no test labels are used to select K. This is a cohort-relative ranking policy, not a portable threshold.')
    interval_scope = ('Detection contrasts are paired within patients. Their nominal two-sided 95% confidence intervals use the original paired Newcombe method 10 with its correction for positive association. Review volume is exactly K for both methods, so the policy-level B−A review-fraction difference is zero by design; no policy review-difference interval is presented. The archived conditional Newcombe calculations for individual paired review flags are retained in the unrounded source CSV, and are not interpreted as intervals for the equal-K policy review-volume difference.'
                      if equal_review else
                      'Detection and review contrasts are paired within patients. Nominal two-sided 95% confidence intervals use the original paired Newcombe method 10 with its correction for positive association.')
    add('S10'+panel,f'Table S10 (continued). Panel {panel}: {label}.',
        ['Target (%)','A reviews R/N (%)','B reviews R/N (%)','A detected TP/F (%)','B detected TP/F (%)','B−A detection, pp [95% CI]',
         'B−A review, pp' if equal_review else 'B−A review, pp [95% CI]'],rows,
        [f'Post hoc exploratory analysis; {population}. Count-cell percentages use the displayed denominator. pp, percentage points.', policy,
         interval_scope,
         'The presented confidence intervals are conditional on the observed calibration and selection, exclude calibration uncertainty and re-ranking bootstrap uncertainty, and have no multiplicity correction. They do not replace or modify the original H1–H3 analyses.'],
        [.5,.87,.87,.87,.87,1.35,1.35])

route_order=['fixed_cutoffs_test_sampling','development_calibration_only','full_resampling']
route_labels={route:f'R{i+1}' for i,route in enumerate(route_order)}
endpoint_labels={
 'H1_A_external_minus_internal_detection_pp':'H1: A detection, external−internal',
 'H2_A_external_minus_internal_review_pp':'H2: A review, external−internal',
 'external_fixed_B_minus_A_detection_pp':'External B−A detection, threshold',
 'external_equal_B_minus_A_detection_pp':'External B−A detection, equal K=50'}
rows=[]
raw_endpoints=[]
for route in route_order:
    for endpoint,label in endpoint_labels.items():
        result=bootstrap['routes'][route]['endpoints_pp'][endpoint]
        rows.append([route_labels[route],label,signed(bootstrap['observed'][endpoint]),signed(result['median']),
                     ci_only(*result['percentile_95']),str(result['valid_replicates'])])
        raw_endpoints.append(dict(route=route,endpoint=endpoint,observed_pp=bootstrap['observed'][endpoint],
                                  median_pp=result['median'],lower_pp=result['percentile_95'][0],
                                  upper_pp=result['percentile_95'][1],valid_n=result['valid_replicates'],
                                  negative_n=result['negative_count'],zero_n=result['zero_count'],positive_n=result['positive_count']))
bootstrap_notes=[
    'Post hoc exploratory patient bootstrap: 10,000 replicates per route; seed 20261106; NumPy PCG64. Values are percentage points. Intervals are nominal, unadjusted 2.5th–97.5th percentile intervals over valid replicates, using linear quantiles. All 12 endpoints have 10,000 valid replicates and zero NA replicates.',
    'R1: test-cohort patient sampling at the locked development cutoffs; conditional on the observed development calibration. R2: development-patient resampling with recalibration to approximately 20% review, evaluated on the unchanged test cohorts; conditional on those observed test cohorts. R3: full development-plus-test patient resampling, combining calibration variability and test-sampling variability within the observed empirical cohorts. A/B risks and quality stay paired within each sampled patient.',
    'In R2, the equal-K=50 endpoint is necessarily constant because the test cohort and its risk ranking remain fixed; its degenerate interval is not evidence of population certainty. R1 and R3 share test draws, while R2 and R3 share development draws.',
    'Every sampled draw is retained, including repeat draws of the same patient; these repetitions are not independent new cases. Equal review selects exactly 50 draw records by descending risk, original identifier string, then replica index. Calibration keeps all risk ties together and chooses fewer reviews when equally close; zero-denominator detection is NA without imputation.',
    'The observed external low-quality paired table has both=10, A-only=0, B-only=3, neither=3. R1 cannot generate an A-only detection from this empirical support, so its threshold B−A contrast is structurally nonnegative. Its [0.00, +40.00] pp percentile interval does not exclude a population advantage for A.',
    'These descriptive percentile intervals supplement, and do not replace, the original paired Newcombe intervals. The original external threshold B−A interval remains [−4.28, +40.04] pp. Empirical sign and reversal fractions are neither p-values nor posterior probabilities, and do not establish superiority or equivalence.'
]
add('S11A','Table S11. Post hoc three-route bootstrap sensitivity. Panel A: endpoint intervals.',
    ['Route','Endpoint','Observed (pp)','Bootstrap median (pp)','Nominal percentile 95% interval (pp)','Valid n'],
    rows,bootstrap_notes,[.4,2.25,.75,.9,1.45,.5])
csv_dict_write(DATA/'S11_endpoints_unrounded.csv',raw_endpoints)

rows=[]
raw_directions=[]
for route in route_order:
    patterns=bootstrap['routes'][route]['joint_direction_patterns']
    for fs,fl in [('negative','<0'),('zero','=0'),('positive','>0')]:
        row=[route_labels[route],fl]
        for es in ['negative','zero','positive']:
            cell=patterns['sign_matrix'][fs][es]
            row.append(countpct(cell['count'],patterns['valid_replicates']))
            raw_directions.append(dict(route=route,threshold_contrast_sign=fs,equal_review_contrast_sign=es,
                                       count=cell['count'],fraction=cell['fraction'],valid_n=patterns['valid_replicates']))
        rows.append(row)
summary_notes=[]
for route in route_order:
    p=bootstrap['routes'][route]['joint_direction_patterns']
    pattern_cell=lambda key: f"{p[key]['count']} ({100*p[key]['count']/p['valid_replicates']:.2f}%)"
    summary_notes.append(f"{route_labels[route]}: observed-direction reversal (+,−), {pattern_cell('original_direction_reversal')}; opposite reversal (−,+), {pattern_cell('opposite_direction_reversal')}; any strict reversal, {pattern_cell('any_strict_reversal')}; either contrast tied, {pattern_cell('any_difference_tie')}.")
add('S11B','Table S11 (continued). Panel B: joint direction matrix for the external B−A detection contrasts.',
    ['Route','Threshold B−A sign','Equal K=50 B−A <0, n (%)','Equal K=50 B−A =0, n (%)','Equal K=50 B−A >0, n (%)'],rows,
    ['Post hoc exploratory bootstrap. Rows show the sign of the threshold contrast; columns show the sign of the equal-review contrast. Each cell is a count and percentage of 10,000 jointly valid paired replicates. Route definitions and empirical-support caveats are given in Panel A. Strict reversal requires opposite nonzero signs; ties are reported separately.']+summary_notes,
    [.45,1.05,1.65,1.65,1.65])
csv_dict_write(DATA/'S11_direction_matrix_unrounded.csv',raw_directions)

rows=[]
for r in mix:
    outcome='Detection' if r['outcome']=='detection' else 'Review fraction'
    cells=[f"{r['method']}: {outcome}"]
    for key in ['overall_difference','composition_associated','within_stratum_rate']:
        cells.append(interval(r[key],r[key+'_ci95_lower'],r[key+'_ci95_upper'],100))
    assert r['composition_associated_valid_replicates']==r['within_stratum_rate_valid_replicates']
    cells += [r['overall_difference_valid_replicates'],r['composition_associated_valid_replicates']]
    rows.append(cells)
add('S12','Table S12. Post hoc diagnostic-stratum symmetric Kitagawa decomposition of external-minus-internal differences.',
    ['Method: outcome','Overall difference, pp [95% interval]','Composition-associated term, pp [95% interval]','Within-stratum term, pp [95% interval]','Valid overall n','Valid component n'],rows,
    ['Post hoc descriptive accounting at the locked 20%-development-budget thresholds (A=0.13705134391784668; B=0.06972856653991777), without recalibration. Direction is external minus internal. Strata are dataset-reported benign and malignant diagnoses; not every diagnosis was histopathologically confirmed.',
     'Symmetric Kitagawa identity: overall difference = Σ[(wE−wI)(pE+pI)/2] + Σ[(pE−pI)(wE+wI)/2]. Detection weights are the diagnostic proportions among low-quality cases; review weights are the diagnostic proportions among all patients. The first sum is composition-associated and the second is the within-stratum term. Weights are recomputed in every draw.',
     'Intervals are nominal, unadjusted descriptive percentile 95% intervals from 5,000 independent within-cohort patient bootstrap replicates (seed 20261107; NumPy PCG64; linear finite-value quantiles); A/B, quality and diagnosis remain paired. Duplicate draws are repeated observations of existing patients, not new cases.',
     'Overall detection differences have 5,000 valid replicates. One draw has no external benign low-quality case, making its detection stratum rate undefined; the NA propagates to both detection components, leaving 4,999 valid component replicates. Review-fraction components and overall differences have 5,000 valid replicates. Undefined rates are not imputed even when their stratum weight is zero.',
     'Two diagnostic strata cannot remove device, acquisition, annotation or other confounding. This decomposition is not a causal attribution and no percent-explained claim is made. Percentile intervals supplement the original H1–H3 Newcombe intervals; crossing zero does not demonstrate equivalence.'],
    [1.0,1.45,1.45,1.45,.55,.55])

case_max={r['image_id']: max(abs(num(c['difference'])) for c in comparison if c['image_id']==r['image_id']) for r in six}
rows=[]
for r in six:
    rows.append([r['image_id'],f"{num(r['original_dice']):.6f}",f"{num(r['rerun_dice']):.6f}",
                 f"{num(r['dice_difference']):+.8f}",'1→1','5/5'])
replay_notes=[
    'Post hoc targeted CPU replay of the six archived external low-quality cases missed by A: case089, case175 and case238 were missed by both methods; case024, case105 and case222 were detected only by B. The same six patients are replayed; this is not an independent validation cohort or a full-cohort rerun.',
    'Low quality is reference Dice <0.70. Five predicted masks were saved per case (initial, left, right, up, down); all 30/30 are nonempty. Mask nonemptiness does not establish segmentation adequacy.',
    'Reference Dice and risks were independently recomputed directly from the saved NPZ arrays and agree exactly with the replay receipt. Displayed values are rounded; unrounded case data and all 48 numerical comparisons are supplied as CSV.',
    'Replay used CPU inference with the archived model checkpoint and frozen prompt geometry. The result checks numerical and decision reproducibility for these selected cases only; it is not a clinical-validity assessment.'
]
add('S13A','Table S13. Post hoc six-case targeted CPU replay. Panel A: reference Dice and saved-mask checks.',
    ['Case','Archived Dice','CPU replay Dice','Replay−archive Dice','Low quality (archive→CPU)','Nonempty masks'],rows,
    replay_notes,[.65,.95,.95,1.25,1.45,.9])
rows=[]
for r in six:
    rows.append([r['image_id'],f"{num(r['original_risk_A']):.6f}→{num(r['rerun_risk_A']):.6f}",
                 f"{num(r['original_risk_B']):.6f}→{num(r['rerun_risk_B']):.6f}",
                 f"{r['alert_A']}→{r['alert_A']}",f"{r['alert_B']}→{r['alert_B']}",f"{case_max[r['image_id']]:.8f}"])
add('S13B','Table S13 (continued). Panel B: archived and replayed risks and review decisions.',
    ['Case','A risk (archive→CPU)','B risk (archive→CPU)','A review (archive→CPU)','B review (archive→CPU)','Maximum |Δ| across 8 fields'],rows,
    ['Post hoc exploratory replay; A is 1 minus the initial SAM predicted IoU, and B is 1 minus mean Dice consistency between the initial mask and four shifted-prompt masks. Review=1 when risk is greater than or equal to the locked threshold: A=0.13705134391784668 and B=0.06972856653991777. The archived and replayed A/B review decisions agree in 12/12 comparisons; all six low-quality labels agree.',
     'Eight numerical fields per case are reference Dice, initial predicted IoU, risk A, risk B and the four prompt-shift Dice values. Of 48 comparisons, 6 are exactly equal and 42 differ numerically. Maximum |Δ| across all fields is 0.0014354348103014225 (case105, left-shift Dice). Maximum |Δ| in reference Dice is 0.00009610643066648716 (case222); risk A, 0.00004601478576660156 (case222); risk B, 0.0003589758947518673 (case105). Numerical replay is therefore not bitwise identical.',
     'These selected cases provide a reproducibility check for the saved predictions and fixed decisions, not additional patients or evidence of a performance improvement.'],
    [.65,1.5,1.5,1.05,1.05,1.0])

# Export unrounded inputs alongside the formatted presentation cells.
for name,records in [('S10_calibration_unrounded',calibration),('S10_performance_unrounded',performance),
                     ('S10_paired_contrasts_unrounded',contrasts),('S12_decomposition_unrounded',mix),
                     ('S13_cases_unrounded',six),('S13_all_48_comparisons_unrounded',comparison)]:
    csv_dict_write(DATA/f'{name}.csv',records)

# Numeric checks use underlying raw artifacts, not formatted cells.
checks=[]


def check(name, condition, detail=None):
    checks.append(dict(check=name,passed=bool(condition),detail=detail))
    assert condition, (name,detail)


check('S10 complete scan dimensions',len(calibration)==16 and len(performance)==64 and len(contrasts)==32,
      dict(calibration=len(calibration),performance=len(performance),paired=len(contrasts),budgets=budgets))
for csv_records,json_key in [(calibration,'calibration'),(performance,'performance')]:
    archived=budget_json[json_key]
    check('S10 CSV vs JSON '+json_key,len(csv_records)==len(archived) and all(
        all((v=='' and item.get(k) is None) or (isinstance(item.get(k),bool) and (v=='True')==item[k]) or
            (isinstance(item.get(k),(int,float)) and num(v)==item[k]) or v==item.get(k)
            for k,v in row.items()) for row,item in zip(csv_records,archived)))

z=1.959963984540054


def wilson(x,n):
    p=x/n; d=1+z*z/n; c=(p+z*z/(2*n))/d
    h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return max(0.,c-h),min(1.,c+h)


def paired_ci(both,b_only,a_only,neither):
    n=both+b_only+a_only+neither
    prod=(both+b_only)*(a_only+neither)*(both+a_only)*(b_only+neither)
    numerator=both*neither-b_only*a_only
    if numerator>0: numerator=max(numerator-n/2,0.)
    phi=numerator/math.sqrt(prod) if prod else 0.
    p1=(both+b_only)/n; p2=(both+a_only)/n
    l1,u1=wilson(both+b_only,n); l2,u2=wilson(both+a_only,n)
    rad=lambda a,b: math.sqrt(max(a*a+b*b-2*phi*a*b,0.))
    return p1-p2,p1-p2-rad(p1-l1,u2-p2),p1-p2+rad(u1-p1,p2-l2)


max_paired_error=0.
for row in contrasts:
    key=(num(row['target_budget']),row['split'],row['mode'])
    a,b=perf[key+('A',)],perf[key+('B',)]
    for outcome,denominator,numerator in [('detection','F','TP'),('review','N','R')]:
        counts=[integer(row[f'{outcome}_{s}']) for s in ['both','B_only','A_only','neither']]
        estimate,low,high=paired_ci(*counts)
        check(f'S10 cell margins {key} {outcome}',
              counts[0]+counts[1]==integer(b[numerator]) and counts[0]+counts[2]==integer(a[numerator])
              and sum(counts)==integer(a[denominator]))
        expected=[num(row[outcome+s]) for s in ['_difference_pp','_ci95_low_pp','_ci95_high_pp']]
        max_paired_error=max(max_paired_error,max(abs(100*x-y) for x,y in zip([estimate,low,high],expected)))
check('S10 archived paired-flag Newcombe calculations independently recomputed',max_paired_error<1e-10,
      {'max_absolute_error_pp':max_paired_error,'scope':'Archived conditional paired-flag calculations, including equal-K review flags; equal-K review-flag intervals are not published as policy review-volume intervals.'})
check('S10 internal half-budget K=425',all(integer(perf[(.5,'internal_holdout','test_cohort_equal_review',m)]['R'])==425 for m in ['A','B']))
check('S10 external half-budget K=126',all(integer(perf[(.5,'external_test','test_cohort_equal_review',m)]['R'])==126 for m in ['A','B']))
for tid,split in [('S10C','internal_holdout'),('S10E','external_test')]:
    table=next(t for t in tables if t['id']==tid)
    check(tid+' equal-K policy review difference publication presentation',
          all(row[-1]=='0 (by design)' for row in table['rows']) and 'CI' not in table['headers'][-1]
          and all(integer(perf[(b,split,'test_cohort_equal_review','A')]['R'])==integer(perf[(b,split,'test_cohort_equal_review','B')]['R']) for b in budgets),
          {'policy_review_difference_pp':0,'interval_presented':False,'source_conditional_paired_flag_intervals':'Retained unchanged in archived input and unrounded CSV.'})
    check(tid+' cohort-specific half-budget note',
          any(('Internal 50% therefore uses K=425.' if split=='internal_holdout' else 'External 50% therefore uses K=126.') in n for n in table['notes']))
for tid,split in [('S10B','internal_holdout'),('S10D','external_test')]:
    table=next(t for t in tables if t['id']==tid)
    check(tid+' transferred-threshold review difference intervals retained',
          all(row[-1]==interval(paired[(b,split,'development_calibrated_threshold')]['review_difference_pp'],
                                paired[(b,split,'development_calibrated_threshold')]['review_ci95_low_pp'],
                                paired[(b,split,'development_calibrated_threshold')]['review_ci95_high_pp'])
              for row,b in zip(table['rows'],budgets)))

iterations=read_csv(CLOUD/'bootstrap_stability/iterations.csv.gz')
check('S11 raw replicate count',len(iterations)==30000)
by_route=defaultdict(list)
for row in iterations: by_route[row['route']].append(row)
max_boot_error=0.
for route in route_order:
    records=by_route[route]
    check('S11 route count '+route,len(records)==10000)
    for endpoint in endpoint_labels:
        values=np.array([float(r[endpoint]) for r in records])
        result=bootstrap['routes'][route]['endpoints_pp'][endpoint]
        ci=np.quantile(values[np.isfinite(values)],[.025,.975],method='linear')
        max_boot_error=max(max_boot_error,max(abs(ci-np.array(result['percentile_95']))))
        check('S11 endpoint sign counts '+route+' '+endpoint,
              [int(np.sum(values<0)),int(np.sum(values==0)),int(np.sum(values>0))]==
              [result['negative_count'],result['zero_count'],result['positive_count']])
    sign=lambda x: 'negative' if float(x)<0 else ('positive' if float(x)>0 else 'zero')
    actual=defaultdict(int)
    for r in records:
        actual[(sign(r['external_fixed_B_minus_A_detection_pp']),sign(r['external_equal_B_minus_A_detection_pp']))]+=1
    expected=bootstrap['routes'][route]['joint_direction_patterns']['sign_matrix']
    check('S11 independently recomputed 3x3 direction matrix '+route,
          all(actual[(fs,es)]==expected[fs][es]['count'] for fs in ['negative','zero','positive'] for es in ['negative','zero','positive']))
check('S11 all 12 percentile intervals recomputed from raw draws',max_boot_error<1e-10,{'max_absolute_error_pp':float(max_boot_error)})
check('S11 R1 zero A-only empirical support',all(num(r['external_fixed_B_minus_A_detection_pp'])>=0 for r in by_route[route_order[0]]))
check('S11 R2 equal-review conditional endpoint constant',len({r['external_equal_B_minus_A_detection_pp'] for r in by_route[route_order[1]]})==1)
with gzip.open(CLOUD/'bootstrap_stability/iterations.csv.gz','rb') as f:
    raw_hash=hashlib.sha256(f.read()).hexdigest()
check('S11 raw CSV decompression hash',raw_hash==bootstrap['iterations_csv_sha256'],{'sha256':raw_hash})

mix_draws=read_csv(CLOUD/'case_mix_decomposition_bootstrap.csv.gz')
max_mix_error=0.
for row in mix:
    records=[r for r in mix_draws if r['method']==row['method'] and r['outcome']==row['outcome']]
    check('S12 draw count '+row['method']+' '+row['outcome'],len(records)==5000)
    for key in ['overall_difference','composition_associated','within_stratum_rate']:
        values=np.array([float(r[key]) if r[key] not in ['', 'NA', 'nan'] else np.nan for r in records])
        finite=values[np.isfinite(values)]
        expected_n=integer(row[key+'_valid_replicates'])
        ci=np.quantile(finite,[.025,.975],method='linear')
        expected=np.array([num(row[key+'_ci95_lower']),num(row[key+'_ci95_upper'])])
        max_mix_error=max(max_mix_error,max(abs(ci-expected)))
        check('S12 finite replicate count '+row['method']+' '+row['outcome']+' '+key,len(finite)==expected_n,
              dict(valid_n=len(finite)))
    check('S12 observed additive identity '+row['method']+' '+row['outcome'],
          abs(num(row['overall_difference'])-num(row['composition_associated'])-num(row['within_stratum_rate']))<1e-14)
check('S12 all 12 component intervals recomputed from raw draws',max_mix_error<1e-12,{'max_absolute_error_fraction':float(max_mix_error)})

directions=['left','right','up','down']
raw_values=[]
nonempty=0
max_replay_array_error=0.
thresholds={'A':.13705134391784668,'B':.06972856653991777}
for row in six:
    path=REPLAY/'predictions'/row['npz']
    with np.load(path) as arrays:
        masks=arrays['masks']; reference=arrays['reference']
        dice=lambda a,b: 2.0*int(np.count_nonzero(a&b))/(int(a.sum())+int(b.sum())) if int(a.sum())+int(b.sum()) else 1.0
        shift=[dice(masks[0],x) for x in masks[1:]]
        predicted=float(arrays['raw_predicted_ious'][0])
        values={'dice_vs_reference':dice(masks[0],reference),'sam_predicted_iou':predicted,
                'risk_A':1-predicted,'risk_B':1-sum(shift)/4,
                **{'dice_shift_'+d:v for d,v in zip(directions,shift)}}
        foreground=[int(x.sum()) for x in masks]
        nonempty+=sum(x>0 for x in foreground)
        for field,value in values.items():
            comp=next(r for r in comparison if r['image_id']==row['image_id'] and r['field']==field)
            max_replay_array_error=max(max_replay_array_error,abs(value-num(comp['rerun'])))
            raw_values.append(dict(image_id=row['image_id'],field=field,archived=num(comp['archived']),
                                   recomputed_cpu=value,difference=value-num(comp['archived'])))
        check('S13 case decisions '+row['image_id'],all(int(values['risk_'+m]>=thresholds[m])==integer(row['alert_'+m]) for m in ['A','B']))
        check('S13 quality label '+row['image_id'],int(values['dice_vs_reference']<.7)==int(num(row['original_dice'])<.7))
check('S13 all 30 saved masks nonempty',nonempty==30,{'nonempty':nonempty,'total':30})
check('S13 all 48 metrics independently recomputed from arrays',len(raw_values)==48 and max_replay_array_error==0.,{'max_absolute_recompute_error':max_replay_array_error})
maximum=max(raw_values,key=lambda r:abs(r['difference']))
check('S13 maximum absolute numerical difference',maximum['image_id']=='case105' and maximum['field']=='dice_shift_left' and
      abs(abs(maximum['difference'])-.0014354348103014225)<1e-16,maximum)
check('S13 replay source scope',receipt['status']=='complete' and receipt['all_flags_match'] and not receipt['all_fields_exact'])
csv_dict_write(DATA/'S13_independent_array_recomputation.csv',raw_values)

hashes_after={str(p.relative_to(SOURCE)):sha(p) for p in source_files}
check('Source artifacts unchanged during table build',hashes_before==hashes_after)
check('Only supplementary identifiers S10–S13 generated',all(t['id'].startswith(('S10','S11','S12','S13')) for t in tables))
check('No absolute paths in table product text','/workspace/' not in json.dumps(tables))

payload=dict(schema_version=1,created_utc=datetime.now(timezone.utc).isoformat(),
             purpose='Append-only post hoc v8 supplement: original main tables and Tables S1–S9 remain unchanged.',
             formatting=dict(unit_note='All pp are percentage points; all intervals are nominal 95%.',
                             suggested_font_pt=8.0,repeat_header_rows=True,
                             panel_note='Panel suffixes keep the continuous main numbering S10–S13; no S14 is introduced.'),
             tables=tables,sources=[dict(path=k,sha256=v) for k,v in hashes_before.items()],
             numeric_verification='new_tables_numeric_verification.json')
(DEST/'new_tables.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
verification=dict(status='passed',created_utc=datetime.now(timezone.utc).isoformat(),
                  table_count=len(tables),main_table_count=4,checks=checks,
                  publication_presentation_changes=[
                      {'table':'S10E','change':'Corrected the external equal-review 50% budget note to K=126; the internal S10C 50% note remains K=425.'},
                      {'tables':['S10C','S10E'],'change':'Equal-K policy review-fraction differences are presented as 0 (by design), with no policy review-difference interval. Archived conditional Newcombe calculations for individual paired binary review flags remain unchanged and are not interpreted as equal-K policy review-volume intervals.'},
                      {'tables':['S10B','S10D'],'change':'Transferred-threshold review-difference confidence intervals are retained. All detection-difference confidence intervals are unchanged.'}],
                  source_artifacts_unchanged=hashes_before==hashes_after,
                  source_sha256=hashes_before,
                  presentation_csv_sha256={t['csv']:sha(DATA/(t['id']+'.csv')) for t in tables},
                  output_json_sha256=sha(DEST/'new_tables.json'))
(DEST/'new_tables_numeric_verification.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2)+'\n')
summary=['# Numerical verification of post hoc Tables S10–S13','',
         f"Status: {verification['status']}; {len(checks)} checks passed; {len(tables)} panels under four main supplementary table numbers.",
         '', 'All source artifact hashes were unchanged during the build. No main table, Table S1–S9 or source data was edited.',
         '', 'The 64 budget performance rows and 32 paired contrasts cover eight budgets × two cohorts × two policies × two methods. All archived conditional paired-flag Newcombe calculations were independently recomputed from paired cells.',
         '', 'Publication presentation change: S10C and S10E equal-K review-fraction differences are 0 (by design), with no policy review-difference interval. Nonzero-width conditional intervals for individual paired binary review flags remain unchanged in the scientific archive and unrounded CSV; they are not interpreted as intervals for the equal-K policy review-volume difference. S10B/S10D transferred-threshold review intervals and all detection intervals are unchanged.',
         '', 'Publication presentation change: S10E external 50% equal review uses K=126. S10C internal 50% remains K=425.',
         '', 'The 12 bootstrap endpoint intervals and all three 3×3 sign matrices were independently recomputed from 30,000 raw bootstrap records.',
         '', 'The 12 Kitagawa overall/component intervals and valid counts were independently recomputed from 20,000 raw component records. Detection overall uses 5,000 draws, whereas detection composition and within-stratum terms use 4,999 finite draws.',
         '', 'All 48 CPU replay metrics were independently recomputed from saved NPZ arrays, exactly matching the replay values; all 30 masks were nonempty and all 12 A/B decisions were preserved.',
         '', 'All tables explicitly identify the work as post hoc. Nominal percentile intervals supplement the original Newcombe intervals; repeated patient draws are not new cases.',
         '', 'Product tables use relative source identifiers only. Full-precision data and presentation CSVs are in table_data/.']
(DEST/'new_tables_verification.md').write_text('\n'.join(summary)+'\n')
print(json.dumps(dict(status='passed',table_panels=[t['id'] for t in tables],checks=len(checks),
                      output='new_tables.json'),ensure_ascii=False))
