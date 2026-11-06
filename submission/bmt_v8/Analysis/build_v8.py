"""Revise the author-approved v7 into a new author-review edition.

Original cohort score tables and primary endpoints remain unchanged.
"""
from pathlib import Path
from copy import deepcopy
import argparse,csv,hashlib,json,re,shutil,sys
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph

R=Path('/workspace/bmt_v8');O=R/'outputs';E=R/'evidence'
BASE=Path('/workspace/research_source/submission/bmt_v7')
REPO='https://github.com/khkh87885-code/research'
SOURCE='6a7da8181db6ba3db0bb9fa8bef628f284791b2e'
TITLE='Fixed-threshold transfer and equal-review ranking in breast ultrasound segmentation quality control'
RUNNING='Threshold transfer and review budgets'
NAR=json.loads((E/'narrative_review.json').read_text())
sys.path.insert(0,'/workspace/bmt_revision/scripts')
from build_revision import format_doc
NN='\u202f'

def after(p,text='',style='Normal'):
 elem=OxmlElement('w:p');p._p.addnext(elem);q=Paragraph(elem,p._parent);q.style=style;q.add_run(text);return q
def append_after(p,items):
 for text,style in items:p=after(p,text,style)
 return p
def paras(d):
 yield from d.paragraphs
 for t in d.tables:
  for row in t.rows:
   for c in row.cells:yield from c.paragraphs
def normalize(d):
 for p in paras(d):
  value=re.sub(r'(?<=\d)[ \t\u00a0\u202f]*%',NN+'%',p.text)
  if value!=p.text:p.text=value
def review_props(d,kind):
 d.core_properties.title=TITLE
 d.core_properties.author='Haoze Lan; Ziyuan Zhu'
 d.core_properties.last_modified_by='BMT v8 revision workflow'
 d.core_properties.comments=kind+'; author review edition. Prior v7 approval is historical and is not certification of new v8 approval.'

def manuscript():
 d=Document(BASE/'BMT_main_manuscript_v7.docx');p=list(d.paragraphs)
 # Preserve reference identities while inserting Kitagawa as reference 13.
 for q in p:
  new=re.sub(r'\[(13|14)\]',lambda m:'['+str(int(m.group(1))+1)+']',q.text)
  if new!=q.text:q.text=new
 p[0].text=TITLE;p[1].text='Running title  '+RUNNING
 abstract=dict(NAR['abstract'])
 abstract['methods']=abstract['methods'].replace('Frozen SAM predictions','Frozen Segment Anything Model predictions')
 abstract['conclusions']='Fixed-threshold transfer and equal-review ranking answer different deployment questions. Observed score comparisons depended on the policy and budget; external detection remained imprecise. Reporting detection, review fraction and misses together makes the operating rule explicit.'
 for i,key in enumerate(['objectives','methods','results','conclusions'],9):p[i].text=key.title()+'  '+abstract[key]
 p[16].text=('Case-level quality estimation without a new manual mask has been studied with reverse classification accuracy [3]. For promptable models, Kinalioglu combined mask changes under small prompt perturbations with model confidence for failure screening [4]. Loke et al. directly compared prompt-perturbation uncertainty with predicted IoU in SAM/MedSAM; most case-level differences remained unresolved after paired testing and multiplicity correction [5]. These studies motivate a separate operating question: a score can be evaluated by transferring a numerical cutoff or by allocating the same number of reviews. The former preserves a development operating rule; the latter compares rankings at a specified capacity. Their implications for detection and workload need to be distinguished when scores are transferred between datasets.')
 p[17].text=('We evaluated these two operating policies using model-confidence and prompt-disagreement risks on identical initial masks from a frozen SAM. Each score was calibrated to a 20% development review target in BUS-BRA, then its numerical cutoff was applied unchanged to internal BUS-BRA and external BrEaST patients. The prespecified primary contrast, H1, compared external-minus-internal low-quality detection for confidence-based method A; H2 assessed its review fraction, and H3 compared the two scores on the same low-quality external masks at the locked cutoffs. Equal-review ranking addressed the capacity-constrained question separately. Complete-budget and resampling analyses examined the scope and stability of the comparison, while diagnostic-stratum accounting and prediction contours provided context for workload differences and missed cases.')
 p[27].text=p[27].text.replace('Two empty predicted masks had a consistency Dice coefficient of 1.','The consistency Dice coefficient was defined as 1 when both predicted masks were empty.')
 p[28].text=p[28].text.replace('An initial empty prediction against a nonempty reference contributed a Dice coefficient of 0.','An empty initial prediction against a nonempty reference would contribute a Dice coefficient of 0.')
 p[29].text=('OpenAI Codex assisted with study-design discussions and implementation of research, statistical and plotting code. The pipeline processed public images with frozen SAM weights, and figures were rendered conventionally from recorded data and captured predictions. The human authors retain responsibility for the implementation and calculated outputs. A precise underlying Codex model identifier was not available in the archived study records.')
 p[35].text=('We repeated detection analyses with reference Dice cutoffs of 0.50 and 0.80 while retaining both locked risk thresholds. We also ranked the external cases by each risk score and selected the top 50 per method, the count closest to a 20% review fraction among 252 cases. Risk ties followed the unmodified archived patient-identifier strings in lexicographic order (for example, "1", "10", "100"), rather than numeric or zero-padded image-identifier order. This equal-review comparison used a common number of reviews in the observed external cohort; its paired interval is conditional on the observed rankings.')
 added=[
 ('Post hoc policy sensitivity and diagnostic accounting','Heading 2'),
 ('The following exploratory analyses were specified for this revision after the original study. They retain the original scores, low-quality definition and H1–H3. We examined development review targets of 5%, 10%, 15%, 20%, 25%, 30%, 40% and 50%, calibrating a separate threshold for each method with the same tied-group and nearest-target rules. Selection used development risks and counts, without quality labels. Each numerical threshold was transferred unchanged to both test cohorts. A separate equal-review policy selected the nearest integer to the target fraction of each test cohort, taking fewer cases at an exact half-integer tie.','Normal'),
 ('We used 10,000 patient-bootstrap replicates per route (seed 20261106) to separate three sources of variation: test-cohort sampling at the original cutoffs; development resampling and cutoff recalibration with the original test cohorts unchanged; and both together. Cohorts were sampled independently, with paired A/B scores and labels retained within every record. Repeated draws were retained. Equal-review ranking selected exactly 50 external draw records, ordered by descending risk, original identifier string and draw-position index. The strict original direction pattern required external B-minus-A detection above zero at transferred cutoffs and below zero at equal review; ties were reported separately. Percentile 95% intervals are descriptive, nominal sensitivity intervals and do not replace the prespecified Newcombe intervals.','Normal'),
 ('We also used symmetric Kitagawa accounting and direct standardization across dataset-reported benign/malignant strata [13]. The external-minus-internal difference was partitioned into a composition-associated term and a within-stratum-rate term. Common weights were the arithmetic mean of the two cohort weights. Detection used the diagnostic shares among low-quality masks, whereas review fractions used shares among all scored patients. We obtained nominal percentile intervals from 5,000 independently sampled cohort-level patient-bootstrap replicates (seed 20261107), recalculating all weights and rates. Undefined stratum denominators remained missing. This accounting describes the observed mixtures and does not estimate causal effects.','Normal')]
 append_after(p[37],added)
 p[39].text=('The original study assessed computational reproducibility by recomputing statistics from archived case scores and by rerunning all 1,316 images in the original computing environment. Its recorded comparisons covered eight numerical fields, quality labels, review decisions, calibration and review-curve counts. For the present revision, we additionally replayed the six A-missed external cases on a CPU using the checksum-identical original checkpoint, exact SAM source and frozen float32 prompt rules. We saved the initial and four shifted predictions for each case and compared all eight numerical fields and decisions with the archive. The two exercises have separate environments and receipts; all cohort analyses continue to use the original scores.')
 p[53].text=('The archived same-environment raw-image rerun scored all 1,316 cases. The maximum absolute difference was zero for each of the eight numerical fields, and all quality and review decisions matched (Table S5). Statistical replay reproduced the thresholds, primary and supplementary results, and count-level review curves. These checks concern computational reproducibility of the recorded pipeline.')
 # Add new analyses after S1–S9 have been cited, preserving supplement numbering.
 additions=[
 ('Review-policy and calibration sensitivity','Heading 2'),
 ('Across the complete budget grid, external B-minus-A detection under transferred cutoffs was positive at targets of 5–20%, negative at 25%, 30% and 50%, and zero at 40%. Under equal-review ranking, it was positive at 5–15%, negative at 20%, and zero at 25–50% (Table S10 and Figure S3). Neither score consistently detected more low-quality masks across these policies and budgets.','Normal'),
 ('The strict 20%-target direction pattern occurred in 39.61% of fixed-cutoff test-sampling replicates, 90.40% of development-only calibration replicates and 30.94% of full development-and-test replicates. At least one comparison was tied in 28.08% of full replicates. Full-resampling percentile intervals were [−39.03, +11.71] percentage points for A detection and [−12.70, −1.55] for its review fraction, in external-minus-internal order (Table S11 and Figure S4). These frequencies describe empirical resampling, not p-values or population probabilities. At the original fixed cutoffs, the absence of an observed A-only low-quality detection structurally constrains the test-sampling bootstrap difference to be nonnegative; its [0.00, +40.00] percentile interval cannot exclude a population A advantage. The original H3 Newcombe interval remains unchanged.','Normal'),
 ('Diagnostic composition and standardized differences','Heading 2'),
 ('For A, the −6.56-point external-minus-internal review difference comprised a +0.64-point composition-associated term and a −7.20-point within-stratum-rate term. Its detection difference had corresponding terms of −1.62 and −12.23 points. For B, the review terms were +0.79 and −5.32 points, and the detection terms were −0.78 and +8.91 points (Table S12 and Figure S5). The within-stratum term equals the difference after standardization to common diagnostic weights. Detection components were defined in 4,999/5,000 replicates; one replicate had no external benign low-quality case. Overall differences and all review components had 5,000 valid replicates.','Normal'),
 ('Spatial inspection from targeted CPU replay','Heading 2'),
 ('The six-case CPU replay saved 30 nonempty prediction masks. All 12 A/B review decisions and six quality labels matched the original records. Initial reference Dice differed by at most 9.61 × 10−5; the largest difference across all 48 numerical comparisons was 0.00143543 for left-shift consistency Dice in case105 (Table S13). Figure 5 shows the three shared misses, with all six cases in Figure S6. In case175, the predicted region lay along the upper image edge and had little overlap with the released reference (replayed Dice 0.0293), while both risks remained below their review cutoffs. These are newly captured CPU masks; the original six CUDA arrays were not archived, so pixel identity could not be tested.','Normal')]
 append_after(p[59],additions)
 p[61].text='Decision rules and deployment workload'
 p[62].text=('A fixed numerical cutoff and a fixed review count make different commitments when a quality-control score is transferred. A cutoff can be applied case by case, leaving the resulting review fraction as an outcome. Ranking fixes the number selected within a defined cohort or batch. In the 20%-target example, B detected 13/16 low-quality external masks at its transferred cutoff and A detected 10/16; at 50 reviews each, the counts were 13/16 and 14/16. The complete budget scan showed that this ordering depended on the target as well as the rule. Evaluating both policies therefore distinguishes the transfer of a development operating point from detection at a specified review capacity.')
 p[63].text=('Method A selected approximately one fifth of the internal cohort and one seventh of the external cohort for review. Its external detection contrast was less precise: workload was estimated from all 252 external patients, whereas detection used the 16 low-quality masks. The review fraction combines the prevalence of low-quality masks with the flagged fractions in low-quality and acceptable groups. BrEaST had both a smaller low-quality fraction and a smaller flagged fraction among acceptable masks. Misses per 100 patients depend on that prevalence too, explaining why they can remain similar while detection point estimates differ.')
 p[64].text=('The diagnostic-stratum analysis gives a more specific description of this workload difference. For A, the positive composition-associated term and negative within-stratum-rate term act in opposite directions; the latter is also the common-weight standardized difference. Thus the two-stratum accounting locates the observed difference in rates within the diagnostic groups, without identifying its cause. For detection, these weights describe the low-quality subset, not all patients. Dataset differences in acquisition, devices and reference annotation remain combined with the observed diagnostic mixtures.')
 p[66].text=('Prompt disagreement added three detections at the locked external operating point. Its yield relative to confidence was not uniform across budgets, and the bootstrap characterized the sensitivity of the 20% direction pattern to calibration and test sampling. The development-only result is conditional on the original test patients and rankings; the full-resampling result also incorporates their empirical variation. Together with the original paired interval, these analyses support a policy-specific interpretation of the observed counts rather than a general ordering of the scores.')
 p[67].text=('Confidence and prompt disagreement capture different properties of the same initial prediction. A uses the model quality estimate, whereas B probes stability under four specified box translations. The replay contours make their shared blind spot visible: a consistently selected region can remain poorly aligned with the reference. Case175 is an inspectable example of this behavior, with a narrow upper-edge prediction and very low reference Dice. Prior work combined structural responses with confidence [4] and directly compared perturbation uncertainty with predicted IoU [5]. The present evaluation complements those approaches by jointly reporting detection, review volume and misses under explicit operating policies.')
 p[69].text=('The findings apply to reference-informed, known-location boxes. Reader-drawn or automatically generated boxes require separate evaluation. The study used one SAM checkpoint, one image per patient and one independent external dataset; overlap with the SA-1B pretraining archive could not be determined [1]. Sixteen external low-quality masks limit detection precision, and empirical resampling does not add independent patients. The new budget, resampling and accounting analyses are post hoc; they define the scope of the operating example rather than confirming a prespecified population-level reversal.')
 p[70].text=('Reference Dice measures agreement with released contours, and the operational cutoff requires separate clinical justification. Simulated review counts do not measure reader time, correction success or downstream measurement accuracy. Future evaluations should predefine the review policy and assess detection and workload jointly with independently supplied prompts and additional external cohorts.')
 p[71].text=('All recorded predictions were nonempty. In future data, simultaneous empty initial and shifted masks could nevertheless receive zero disagreement risk under the stated consistency convention; any explicit empty-mask review rule would be a prospective policy change.')
 p[72].text=('In this known-location breast ultrasound evaluation, transferring development-calibrated numerical cutoffs changed the fraction of cases flagged for review. The relative detection yield depended on the operating policy and budget, with no uniformly better score across the complete grid. Joint reporting of detection, review fraction and missed cases, together with an explicit choice of fixed cutoff or fixed review count, provides a practical basis for interpreting segmentation-quality screening across datasets.')
 p[74].text=('AI use and acknowledgments. OpenAI Codex assisted with study-design discussions, research and statistical code, plotting scripts, and substantive drafting and editing. Figures were rendered with Python/Matplotlib from released images, captured SAM masks and recorded scores. Editorial drafting used the Scientific Agent Skills workflow [14]. A precise underlying Codex model identifier was not available in the archived study records. The human authors retain responsibility for the work.')
 p[76].text=('Author contributions. All authors have accepted responsibility for the entire content of this manuscript. Haoze Lan: research conceptualization and principal study design. Ziyuan Zhu: code review, GitHub repository uploads and manuscript revision.')
 p[80].text=('Data and code availability. The original BUS-BRA version 1.0 images and reference masks are available at https://doi.org/10.5281/zenodo.8231412 and BrEaST version 1 at https://doi.org/10.7937/9WKK-Q141 [8, 10]. Study-specific manifests, case scores, scoring and statistical code, and reproducibility records are available in the research repository [15]. The original study archive is retained at commit 592566b4c5f39e261c676eb034139a974e9cdfd5; the additional budget, bootstrap, diagnostic-accounting and six-case replay evidence is archived at commit '+SOURCE+'. Original datasets and derived materials are distinguished in the data, experiments and reproducibility directories. The checkpoint is not bundled; documented source URLs and its SHA-256 allow identity verification. The supplementary materials include the new tables, actual replay contours and executable analysis references.')
 after(p[93],'13.  Kitagawa EM. Components of a difference between two rates. J Am Stat Assoc 1955;50:1168–1194. https://doi.org/10.1080/01621459.1955.10501299','Reference entry')
 p[94].text=re.sub(r'^13\.','14.',p[94].text)
 p[95].text=('15.  Research materials for fixed review thresholds in breast ultrasound segmentation [Internet]. GitHub; 2026 [cited 2026 Nov 6]. Evidence archive commit '+SOURCE+'. Available from: '+REPO+'/tree/'+SOURCE+'.')
 after(p[107],'Figure 5.  Three shared screening misses with actual targeted CPU predictions. Rows show BrEaST case089 (A, B), case175 (C, D) and case238 (E, F) [10]. Left panels overlay the released reference contour (green) and reference-derived initial prompt (blue); right panels overlay the initial prediction captured in the CPU replay (orange). Both review scores missed these three low-quality masks at the original locked cutoffs. Predictions use the original checksum-matched SAM ViT-B weights, exact source and prompt rules. Displayed Dice values come from this replay. The maximum initial-reference-Dice difference across all six replayed cases was 9.61 × 10−5; original study scores remain in Table S9. All six replayed cases and numerical comparisons appear in Figure S6 and Table S13.','Figure legend')
 normalize(d);format_doc(d,RUNNING,main=True);review_props(d,'Main manuscript v8')
 assert [[[c.text for c in row.cells]for row in t.rows]for t in d.tables]==[[[c.text for c in row.cells]for row in t.rows]for t in Document(BASE/'BMT_main_manuscript_v7.docx').tables]
 d.save(O/'BMT_main_manuscript_v8.docx')
 return d

def table_format(t,widths):
 widths=[6.4*w/sum(widths)for w in widths];t.autofit=False
 for col,w in zip(t.columns,widths):col.width=Inches(w)
 for ri,row in enumerate(t.rows):
  pr=row._tr.get_or_add_trPr()
  if pr.find(qn('w:cantSplit'))is None:pr.append(OxmlElement('w:cantSplit'))
  if ri==0 and pr.find(qn('w:tblHeader'))is None:pr.append(OxmlElement('w:tblHeader'))
  for ci,(cell,w)in enumerate(zip(row.cells,widths)):
   cell.width=Inches(w)
   for p in cell.paragraphs:
    p.paragraph_format.space_after=Pt(3);p.paragraph_format.line_spacing=1
    for run in p.runs:run.font.name='Times New Roman';run.font.size=Pt(8.5);run.bold=ri==0

def supplement():
 d=Document(BASE/'BMT_supplementary_material_v3.docx');old=list(d.paragraphs);old[1].text=TITLE;old[2].text='Haoze Lan; Ziyuan Zhu; v8 author-review revision, 6 November 2026'
 old[23].text=('Revision audit provenance. Archived-score replay and the original same-environment full-cohort image rerun remain distinct from the six-case CPU replay reported in Table S13. The latter was actually executed for this revision, saved new prediction arrays and retained the original scores for every cohort analysis. Computational reproducibility is distinct from independent validation.')
 old[41].text=('Actual predictions for these six cases have now been captured in a targeted CPU replay using the checksum-identical checkpoint and exact SAM source. Figure S6 shows the replayed contours and Table S13 compares the new values with the archived scores. The original six CUDA arrays were not retained; pixel identity across environments cannot be checked. Table S9 continues to report the original scores. The Figure 2 case001 illustration is not used as a substitute for a missed case.')
 new=json.loads((E/'new_tables.json').read_text())
 for spec in new['tables']:
  h=d.add_heading(spec['title'],1);h.paragraph_format.page_break_before=True
  t=d.add_table(rows=1,cols=len(spec['headers']));t.style='Table Grid'
  for cell,text in zip(t.rows[0].cells,spec['headers']):cell.text=str(text)
  for values in spec['rows']:
   for cell,text in zip(t.add_row().cells,values):cell.text=str(text)
  table_format(t,spec['column_widths_hint'])
  for text in spec['notes']:d.add_paragraph(text)
  if spec['id']=='S12':d.add_paragraph('For diagnostic stratum s, C = Σ(w_E,s−w_I,s)(p_E,s+p_I,s)/2 and W = Σ(p_E,s−p_I,s)(w_E,s+w_I,s)/2, so D=C+W. Common weights w*=(w_E+w_I)/2 give a standardized external-minus-internal difference equal to W. Components may not sum to the displayed total after rounding. Method: Kitagawa EM, J Am Stat Assoc 1955;50:1168–1194, doi:10.1080/01621459.1955.10501299.')
  if spec['id']=='S13A':d.add_paragraph('The CPU replay used Python 3.12.14, PyTorch 2.4.1+cpu, torchvision 0.19.1+cpu, NumPy 1.26.4 and Pillow 10.4.0, with two PyTorch threads and float32 weights. The original GPU environment is in Table S1. Total wall time, including loading and figure generation, was 59.419 seconds; peak process RSS was 3,220.4 MiB. All 48 full-precision comparisons are supplied as S13_all_48_comparisons_unrounded.csv, alongside the captured arrays in the fixed evidence repository.')
 figs=[
 ('S3','Post hoc budget dependence','Figure_S3.png','Figure S3. Complete review-budget scan. A shows actual review fractions after development-threshold transfer; B and C show external and internal low-quality detection under transferred cutoffs and equal-review ranking; D shows paired external B-minus-A detection differences. Each target was evaluated using both rules, with no selection of a favorable budget. External and internal low-quality denominators are 16 and 93. Error bars in D are nominal paired Newcombe 95% intervals conditional on observed calibration and rankings; they do not incorporate recalibration or reranking uncertainty. Numerical values are in Table S10.'),
 ('S4','Post hoc calibration and sampling sensitivity','Figure_S4.png','Figure S4. Patient-bootstrap sensitivity, 10,000 replicates per route. A and B show A external-minus-internal detection and review contrasts; C shows external B-minus-A detection under transferred cutoffs and equal-top50 ranking. Points and bars denote medians and descriptive percentile 95% intervals, with original estimates identified separately. D shows the joint sign-pattern frequencies: original strict pattern (fixed>0/equal<0), opposite pattern, at least one zero contrast, or matching nonzero signs. Frequencies are empirical resampling summaries, not p-values or population probabilities. Test-only resampling cannot generate an unobserved A-only low-quality detection at the fixed cutoffs; its nonnegative support must not be used to exclude a population A advantage. The original H3 Newcombe interval is retained. Complete routes, denominators and the sign matrix are in Table S11.'),
 ('S5','Diagnostic composition accounting','Figure_S5.png','Figure S5. Symmetric Kitagawa accounting at the original locked cutoffs. A shows low-quality detection and B simulated review. Rows give the overall external-minus-internal difference and its composition-associated and within-stratum-rate terms for each score. Points show original estimates; bars show nominal percentile 95% intervals from 5,000 patient-bootstrap draws. Detection components have 4,999 valid draws; overall differences and review components have 5,000. Detection weights describe diagnostic shares among low-quality cases; review weights describe shares among all patients. The within-stratum term equals the common-weight standardized difference. These are descriptive accounting terms, not causal effects. Values and rounding details are in Table S12.'),
 ('S6A','Targeted CPU replay: shared misses','Figure_S6A.png','Figure S6 (A). Targeted CPU predictions for the three shared screening misses, case089, case175 and case238. Left panels show the original image with released reference (green) and initial reference-derived prompt (blue); right panels show the actual replay prediction (orange). Both A and B remain below their review cutoffs. The model checkpoint, source, float32 precision and prompt geometry match the frozen protocol. Dice labels are from the CPU replay. Table S13 reports environment details and summarizes the comparisons; all 48 full-precision values are supplied in S13_all_48_comparisons_unrounded.csv. Original scores are retained in Table S9.'),
 ('S6B','Targeted CPU replay: B-only detections','Figure_S6B.png','Figure S6 (B). Remaining A-missed low-quality cases, case024, case105 and case222, detected by B. Colors and panel layout follow part A. All 30 captured masks across the six patients are nonempty, and all quality labels and A/B review flags match the archive. The maximum initial-reference-Dice difference is 9.61 × 10−5; the maximum over all 48 fields is 0.00143543 (case105 left-shift consistency). These are new CPU arrays; original CUDA arrays were not saved, so cross-environment pixel identity cannot be verified. No new independent patients were introduced.')]
 for tag,title,file,caption in figs:
  h=d.add_heading(title,1);h.paragraph_format.page_break_before=True
  d.add_picture(str(O/'Figures'/file),width=Inches(6.4))
  d.add_paragraph(caption,'Caption')
 normalize(d);format_doc(d,'Supplementary material: review policies')
 # Restore compact publication-table format after the shared formatter.
 for t,spec in zip(d.tables[9:],new['tables']):table_format(t,spec['column_widths_hint'])
 review_props(d,'Supplementary material v4')
 assert [[[c.text for c in row.cells]for row in t.rows]for t in d.tables[:9]]==[[[c.text for c in row.cells]for row in t.rows]for t in Document(BASE/'BMT_supplementary_material_v3.docx').tables]
 d.save(O/'BMT_supplementary_material_v4.docx')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--main',action='store_true');p.add_argument('--supplement',action='store_true');a=p.parse_args()
 if a.main:manuscript()
 if a.supplement:supplement()
 print('Built requested v8 documents.')
