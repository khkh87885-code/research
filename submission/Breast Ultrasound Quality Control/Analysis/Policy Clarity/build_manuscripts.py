#!/usr/bin/env python3
"""Clarify prior work and matched review counts without replacing primary results."""
from pathlib import Path
from copy import deepcopy
import csv,json,hashlib,shutil,re
from docx import Document
from docx.text.paragraph import Paragraph
from docx.shared import Pt
from docx.oxml.ns import qn
from lxml import etree

BASE=Path('/workspace/policy_clarity')
SOURCE=BASE/'source'
OUT=BASE/'outputs'
PREFIX='Breast Ultrasound Quality Control'
CSV_NAME=PREFIX+' Matched Review Counts.csv'
NS={'m':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
EDIT_LOG=[]

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def all_math(d):return [etree.tostring(x)for x in d.element.findall('.//m:oMath',NS)]
def cells(t):return [[c.text for c in r.cells]for r in t.rows]
def replace(doc,start,new):
    found=[p for p in doc.paragraphs if p.text.startswith(start)]
    assert len(found)==1,(start,len(found))
    p=found[0];assert not p._p.findall('.//m:oMath',NS)
    EDIT_LOG.append({'before':p.text,'after':new});p.text=new;return p
def after(p,text):
    e=deepcopy(p._p);p._p.addnext(e);q=Paragraph(e,p._parent)
    q.text=text;EDIT_LOG.append({'before':None,'after':text});return q

def build_main():
    path=SOURCE/(PREFIX+' Manuscript.docx');d=Document(path)
    maths=all_math(d);tables=[cells(t)for t in d.tables]
    replace(d,'Case-level quality estimation without',
      'Reverse classification accuracy estimates case-level segmentation quality without a new manual mask [3]. Kinalioglu combined structural prompt responses with confidence and reported failure recovery among the highest-risk 10\u202f% of masks [4]. Loke et al. compared prompt-perturbation uncertainty with predicted IoU, entropy and test-time augmentation across SAM/MedSAM using paired tests and multiplicity control [5]. Building on these scoring and ranking studies, we examine development-calibrated numerical cutoff transfer to internal and external breast ultrasound cohorts. Comparisons at the same actual review counts and joint reporting of detection, workload and misses distinguish cutoff transfer from capacity-constrained ranking.')
    replace(d,'We repeated detection analyses with',
      'We repeated detection analyses with reference Dice cutoffs of 0.50 and 0.80 while retaining both locked risk thresholds. The original protocol additionally specified an equal-review supplementary comparison in BrEaST: each score ranked the external cases and selected the top 50, the count closest to a 20 % review fraction among 252 cases. Risk ties followed the unmodified archived patient-identifier strings in lexicographic order (for example, "1", "10", "100"), rather than numeric or zero-padded image-identifier order. This planned supplementary comparison used a common review count in the observed external cohort; its paired interval is conditional on the observed rankings. It is separate from H3, which compares the development-locked cutoffs.')
    p=[p for p in d.paragraphs if p.text.startswith('The following exploratory analyses')][0]
    tail='We examined'+p.text.split('We examined',1)[1]
    p=replace(d,'The following exploratory analyses',
      'After the original study, we conducted additional post hoc policy and diagnostic-accounting analyses. These retain the original scores, low-quality definition and H1–H3. '+tail)
    after(p,'Post hoc descriptive readouts were taken at 33 and 35 reviews per method, the two external volumes produced by the transferred cutoffs; the 50-review readout repeated the original-protocol supplementary budget. All were extracted from the archived external ranking curves without new inference, calibration, intervals or hypothesis tests. The original contrasts and intervals remain unchanged.')
    p=[p for p in d.paragraphs if p.text.startswith('At 50/252 reviews')][0]
    after(p,'At matched counts of either 33 or 35 reviews, A detected 10/16 low-quality masks and B detected 13/16, retaining the three-case difference observed at transferred cutoffs (Table S4 and Figure 4D). Increasing the common budget from 35 to 50 added four low-quality detections for A and none for B. The ordering therefore also varied with budget under the same ranking rule. These post hoc readouts describe this cohort without establishing population-level superiority.')
    replace(d,'A fixed numerical cutoff and a fixed review count',
      'A numerical cutoff preserves a development decision threshold, whereas ranking at a fixed count allocates a specified number of reviews within a cohort or batch. In BrEaST, the transferred cutoffs selected 35 patients with A and 33 with B. At matched counts of either 33 or 35, B still detected 13/16 low-quality masks and A detected 10/16; the count difference at the cutoffs therefore was not explained solely by their unequal review volumes. At 50 reviews each, A detected 14/16 and B detected 13/16. The ordering also changed as the budget varied under the same equal-review ranking rule. Reporting the numerical cutoff, actual review count, detections and misses together makes both the operating rule and its budget explicit, without attributing the ordering change to policy alone.')
    p=[p for p in d.paragraphs if p.text.startswith('Confidence and prompt disagreement capture')][0]
    prefix=p.text.split('Prior work combined',1)[0].strip()
    p=replace(d,'Confidence and prompt disagreement capture',prefix)
    after(p,'Budget-constrained failure screening is already established [4], as are cross-dataset and prompt-regime comparisons of uncertainty scores [5]. Here, the transferred cutoff leaves workload as an outcome, while equal-count ranking fixes the number selected. Our resampling routes separate calibration and test-sampling uncertainty. The matched-count readouts further identify budget-dependent ordering within this operating example.')
    # Keep the original abstract contrasts and interval; add the matched-count
    # observation adjacent to the existing fixed-cutoff comparison.
    p=[p for p in d.paragraphs if p.text.startswith('Results  Confidence-based detection')][0]
    old=p.text;needle='versus 10/16 for confidence; at 50 reviews per method'
    assert needle in old
    abstract_results=replace(d,'Results  Confidence-based detection',old.replace(needle,'versus 10/16 for confidence; these counts were unchanged in post hoc readouts at matched 33 or 35 reviews. At 50 reviews per method'))
    text=abstract_results.text
    abstract_results.clear()
    abstract_results.add_run('Results').bold=True
    abstract_results.add_run(text[len('Results'):]).bold=False
    caption=('Figure 4.  Risk-ranked review curves, original paired contrasts and matched counts. A/B: internal (93 low-quality/851 patients) and external (16/252) curves, ranked by descending risk and lexicographic CaseID. Low quality is Dice <0.70. Blue solid/circle and orange dashed/triangle encodings identify A and B. Filled squares mark locked cutoffs: internal A, 71/93 at 174 reviews; B, 68/93 at 150; external A, 10/16 at 35; B, 13/16 at 33. Open circles mark 50 external reviews per method (A: 14/16; B: 13/16). C: B-minus-A detection differences with original paired nominal 95\u202f% Newcombe method 10 intervals: +18.75 [−4.28, +40.04] percentage points at locked cutoffs and −6.25 [−31.61, +19.57] at top 50. The top-50 interval conditions on observed rankings. D: detection counts at the same external K (A/B: 10/13 at 33 and 35; 14/13 at 50), each among 16 low-quality patients. K33/35 are post hoc archived-curve readouts; K50 is the original-protocol supplementary budget. No new interval or test is assigned to D.')
    replace(d,'Figure 4.',caption)
    # Point to the additional machine-readable artifact while retaining all
    # original frozen evidence commits and their provenance.
    p=[p for p in d.paragraphs if p.text.startswith('Data availability.')][0]
    replace(d,'Data availability.',p.text+' Matched-count presentation data and analysis scripts are supplied in the current submission directory under Analysis/Policy Clarity, with '+CSV_NAME+' provided as supplementary data.')
    assert all_math(d)==maths
    assert [cells(t)for t in d.tables]==tables
    d.save(OUT/(PREFIX+' Manuscript.docx'))
    ps=d.paragraphs;start=next(i for i,p in enumerate(ps)if p.text=='Abstract');stop=next(i for i,p in enumerate(ps)if p.text.startswith('Keywords'))
    abstract=' '.join(p.text for p in ps[start+1:stop]);count=len(re.findall(r"\S+",abstract))
    assert count<=200,count
    words=len(re.findall(r'\S+',' '.join(p.text for p in d.paragraphs)+' '+' '.join(c.text for t in d.tables for row in t.rows for c in row.cells)))
    assert words<6000,words
    return {'abstract_words_including_section_labels':count,'main_visible_words_including_tables_and_references':words,'main_tables':len(tables),'main_cells':sum(len(r)for t in tables for r in t),'caption':caption}

def build_supplement():
    d=Document(SOURCE/(PREFIX+' Supplementary Material.docx'));maths=all_math(d)
    old_tables=[cells(t)for t in d.tables]
    replace(d,'Table S4.', 'Table S4.  BrEaST performance at matched review counts')
    t=d.tables[3];template=deepcopy(t.rows[-1]._tr)
    for row in list(t.rows)[1:]:t._tbl.remove(row._tr)
    t.cell(0,0).text='Method / K'
    for p in t.cell(0,0).paragraphs:
        for run in p.runs:
            run.font.name='Times New Roman';run.font.size=Pt(9);run.bold=True
    rows=list(csv.DictReader((BASE/'analysis/equal_review_counts.csv').open()))
    for row in rows:
        k=int(row['K_per_method'])
        for method in ['A','B']:
            t._tbl.append(deepcopy(template));r=t.rows[-1]
            vals=[f'{method} / {k}',f"{int(row[method+'_detected'])}/16 ({float(row[method+'_detection_percent']):.2f} %)",f"{k}/252 ({float(row['review_percent']):.2f} %)",str(int(row[method+'_missed'])),f"{float(row[method+'_missed_per_100_patients']):.2f}"]
            for c,v in zip(r.cells,vals):
                c.text=v
                for p in c.paragraphs:
                    for run in p.runs:run.font.name='Times New Roman';run.font.size=Pt(9)
    replace(d,'Each method selected 50 of the 252',
      'The original protocol specified the equal-review supplementary comparison closest to 20 % of BrEaST, giving 50/252 reviews per method. The additional 33- and 35-review rows are post hoc descriptive readouts at the already reported transferred-cutoff review volumes. They use the same original scores and risk-descending ranking, with lexicographic case-identifier tie-breaking. Low quality is reference Dice <0.70; each detection denominator is 16 and each review denominator is 252.')
    p=[p for p in d.paragraphs if p.text.startswith('Among the 16 low-quality cases, both methods flagged 12')][0]
    replace(d,'Among the 16 low-quality cases, both methods flagged 12','At K=50, '+p.text[0].lower()+p.text[1:])
    p=[p for p in d.paragraphs if p.text.startswith('At K=50, among')][0]
    after(p,'At both K=33 and K=35, the low-quality paired counts are: both scores detect 10, A only 0, B only 3, and neither 3. Increasing the common budget from 35 to 50 adds four low-quality detections for A and none for B. These readouts describe the observed curves; no additional interval, hypothesis test or resampling analysis was performed. Machine-readable counts, denominators and paired outcomes are supplied in '+CSV_NAME+'.')
    replace(d,'Revision audit provenance.',
      'Computational audit provenance. Archived-score replay and the original same-environment full-cohort image rerun remain distinct from the six-case CPU replay reported in Table S13. The targeted replay saved new prediction arrays and retained the original scores for every cohort analysis. Computational reproducibility is distinct from independent validation.')
    assert all_math(d)==maths
    assert len(d.tables)==19
    for i,tbl in enumerate(d.tables):
        if i!=3:assert cells(tbl)==old_tables[i]
    assert [r[1:]for r in cells(d.tables[3])[-2:]]==[r[1:]for r in old_tables[3][1:]]
    assert sum(len(r.cells)for t in d.tables for r in t.rows)==898
    d.save(OUT/(PREFIX+' Supplementary Material.docx'))

def ancillary():
    path=SOURCE/(PREFIX+' Cover Letter.docx');d=Document(path)
    replace(d,'The confidence threshold selected',
      'The confidence threshold selected 20.45 % of internal patients and 13.89 % externally. At matched counts of either 33 or 35 external reviews per score, confidence detected 10/16 low-quality masks and prompt disagreement detected 13/16; at 50 reviews, the counts were 14/16 and 13/16. The observed ordering therefore also changed with budget under the same equal-review ranking rule. This manuscript evaluates cutoff transfer alongside that ranking behavior, building on prior scoring and fixed-budget work. Three bootstrap routes and descriptive diagnostic-stratum accounting characterize sampling and case-mix context without changing the prespecified H1–H3 analyses.')
    d.save(OUT/path.name)
    extra=' The matched-count presentation CSV and its analysis script are also supplied in the current submission directory under Analysis/Policy Clarity, with '+CSV_NAME+' included as supplementary data.'
    path=SOURCE/(PREFIX+' Data and Code Availability.docx');d=Document(path)
    p=[p for p in d.paragraphs if p.text.startswith('The original BUS-BRA')][0];p.text=p.text+extra
    d.add_paragraph('Matched-count data and script: https://github.com/khkh87885-code/research/tree/main/submission/Breast%20Ultrasound%20Quality%20Control/Analysis/Policy%20Clarity')
    d.save(OUT/path.name)
    path=SOURCE/(PREFIX+' Ethical and Legal Declarations.docx');d=Document(path)
    original=[[c.text for c in row.cells]for row in d.tables[0].rows]
    d.tables[0].cell(8,1).text=d.tables[0].cell(8,1).text+extra
    assert all([c.text for c in row.cells]==original[i]for i,row in enumerate(d.tables[0].rows)if i!=8)
    d.save(OUT/path.name)

if __name__=='__main__':
    OUT.mkdir(exist_ok=True)
    (OUT/'Figures').mkdir(exist_ok=True)
    for p in (SOURCE/'Figures').iterdir():
        target=OUT/'Figures'/p.name
        if not target.exists():shutil.copy2(p,target)
    result=build_main();build_supplement();ancillary()
    (BASE/'evidence/manuscript_edits.json').write_text(json.dumps({'summary':result,'edits':EDIT_LOG},indent=2)+'\n')
    print(json.dumps(result,indent=2))
