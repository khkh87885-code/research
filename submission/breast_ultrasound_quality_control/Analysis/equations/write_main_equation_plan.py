from pathlib import Path
from docx import Document
import json,hashlib,re
source=Path('/workspace/research_source/submission/bmt_v9/BMT_main_manuscript_v9.docx')
d=Document(source)
replacements=[]
def p(t):return {'type':'paragraph','text':t}
def e(label,latex):return {'type':'equation','label':str(label),'latex':latex}
def add(index,blocks):replacements.append({'source_paragraph_index':index,'anchor_exact':d.paragraphs[index].text,'blocks':blocks})
add(26,[
p(r'For patient $i$, let $G_i$ be the nonempty binary reference mask and $B_i=(x_i^-,y_i^-,x_i^+,y_i^+)$ its tight bounding box. Upper coordinates are one pixel beyond the largest foreground index, so $w_i=x_i^+-x_i^-$ and $h_i=y_i^+-y_i^-$. The initial prompt expands each side by 10 % and clips coordinates to the image:'),
e(1,r'\begin{aligned}B_{0,i}&=\operatorname{clip}_{\Omega_i}(B_i+e_i),\\e_i&=(-0.10w_i,-0.10h_i,0.10w_i,0.10h_i).\end{aligned}'),
p(r'Here $\operatorname{clip}_{\Omega_i}$ clips horizontal coordinates to $[0,W_i]$ and vertical coordinates to $[0,H_i]$, where $W_i,H_i$ are the image dimensions. Writing the clipped box width and height as $w_{0,i},h_{0,i}$, its four perturbations are'),
e(2,r'\begin{aligned}B_{j,i}&=\operatorname{clip}_{\Omega_i}\{B_{0,i}+(u_{j,i},v_{j,i},u_{j,i},v_{j,i})\},\\(u_{j,i},v_{j,i})&\in\{(-0.05w_{0,i},0),(0.05w_{0,i},0),\\&\qquad(0,-0.05h_{0,i}),(0,0.05h_{0,i})\}.\end{aligned}'),
p(r'The four entries in Eq. (2) correspond to left, right, up and down, respectively. This reference-informed, known-location (oracle-localization) setting does not test autonomous lesion localization. We encoded the image once and reused its embedding for the initial and four shifted-prompt predictions (Figure 2). The same 10 % context margin and 5 % shifts were used across datasets.')])
add(27,[
p(r'Let $P_{0,i}$ denote the initial binary prediction and $P_{j,i}$ its prediction under shift $j$. For two binary masks $U,V$, with $|\cdot|$ denoting foreground-pixel count, Dice agreement is'),
e(3,r'D(U,V)=\begin{cases}\dfrac{2\lvert U\cap V\rvert}{\lvert U\rvert+\lvert V\rvert},&\lvert U\rvert+\lvert V\rvert>0,\\1,&\lvert U\rvert+\lvert V\rvert=0.\end{cases}'),
p(r'Method A uses the raw predicted intersection over union (IoU), $\widehat q_i$, returned by the SAM quality head for the initial mask:'),
e(4,r'r_{A,i}=1-\widehat q_i.'),
p(r'Method B uses disagreement between the initial prediction and the four shifted-prompt predictions:'),
e(5,r'r_{B,i}=1-\frac14\sum_{j=1}^{4}D(P_{0,i},P_{j,i}).'),
p(r'Thus $\widehat q_i$ in Eq. (4) is a model output, whereas Eq. (5) measures prediction-to-prediction consistency. All four directions were retained when clipping produced coincident boxes. Method B adds four mask-decoder passes while reusing the image embedding. Recorded inference times cover the combined pipeline; A-only and incremental B times were not separately benchmarked.')])
add(28,[
p(r'The quality reference for both methods was $D(P_{0,i},G_i)$, separate from the scores in Eqs. (4) and (5). We defined the low-quality indicator as'),
e(6,r'Y_i=\mathbf{1}\{D(P_{0,i},G_i)<\tau\},\qquad \tau=0.70.'),
p(r'Here $\mathbf{1}\{\cdot\}$ is one when its condition holds and zero otherwise. This is an operational quality cutoff. An empty initial prediction against the nonempty reference has Dice zero under Eq. (3).')])
add(31,[
p(r'For method $m\in\{A,B\}$, candidate cutoff $t$ flags patient $i$ when the risk meets or exceeds the cutoff. Its development review fraction is'),
e(7,r'\begin{aligned}a_{m,i}(t)&=\mathbf{1}\{r_{m,i}\ge t\},\\v_{m,\mathrm{dev}}(t)&=\frac{1}{N_{\mathrm{dev}}}\sum_{i\in\mathrm{dev}}a_{m,i}(t).\end{aligned}'),
p(r'The candidate set $\mathcal T_m$ contains every distinct development risk and a cutoff above the maximum risk, representing zero reviews. For target fraction $b$, calibration selects'),
e(8,r't_m^*=\underset{t\in\mathcal T_m}{\operatorname{argmin}_{\mathrm{lex}}}(\lvert v_{m,\mathrm{dev}}(t)-b\rvert,\ v_{m,\mathrm{dev}}(t)).'),
p(r'The ordered pair in Eq. (8) is minimized lexicographically: first the absolute target discrepancy, then the review fraction. Thus cutoff ties are kept together and equally close choices select fewer cases. The primary target was $b=0.20$, a prespecified one-in-five scenario rather than measured clinical capacity. The exact thresholds were locked before test scoring and transferred unchanged to both test cohorts.')])
add(33,[
p(r'The analysis included cases with valid reference Dice and both finite risk scores. One retry with the same configuration was allowed after a technical failure; persistent failures were recorded separately. In a cohort of $N$ scored patients, let $F=\sum_iY_i$ be the number of low-quality masks. Writing $a_{m,i}$ for the flag under the evaluated policy, the counts are $TP_m=\sum_iY_i a_{m,i}$, $FP_m=\sum_i(1-Y_i)a_{m,i}$, $FN_m=F-TP_m$ and $TN_m=N-F-FP_m$. These count flagged low-quality, flagged acceptable, unflagged low-quality and unflagged acceptable masks, respectively. The reported outcomes are'),
e(9,r'\begin{aligned}d_m&=\frac{TP_m}{F},\qquad v_m=\frac{TP_m+FP_m}{N},\\M_m&=100\frac{FN_m}{N},\qquad F=TP_m+FN_m.\end{aligned}'),
p(r'Here $d_m$ is low-quality detection, $v_m$ is simulated review fraction and $M_m$ is missed low-quality masks per 100 patients. Rates with a zero denominator were left undefined.')])
add(34,[
p(r'Let $E$ and $I$ denote BrEaST external testing and BUS-BRA internal testing. The dated plan specified the following differences in percentage points:'),
e(10,r'\begin{aligned}\Delta_{H1}&=100(d_{A,E}-d_{A,I}),\\\Delta_{H2}&=100(v_{A,E}-v_{A,I}),\\\Delta_{H3}&=100(d_{B,E}-d_{A,E}).\end{aligned}'),
p(r'H1 was primary; H2 assessed the corresponding workload difference. H3 compared the scores on the same external low-quality masks at separately locked cutoffs that gave equal development review counts. We calculated two-sided 95 % confidence intervals (CIs) using Newcombe score method 10 for the independent proportions in H1 and H2 [11] and its paired counterpart in H3 [12]. H2, H3 and supplementary intervals are nominal, with no multiplicity adjustment. The exact interval equations are given in the Supplementary mathematical methods.')])
add(35,[
p(r'Sensitivity analyses replaced $\tau$ in Eq. (6) by 0.50 or 0.80 while retaining the locked risk thresholds. A separate equal-review policy selects the same nearest-integer count for each method:'),
e(11,r'\begin{aligned}K(b,N)&=\min\underset{k\in\{0,\ldots,N\}}{\operatorname{argmin}}\lvert k-bN\rvert,\\a_{m,i}^{(K)}&=\mathbf{1}\{\operatorname{rank}_m(i)\le K(b,N)\}.\end{aligned}'),
p(r'The minimum in Eq. (11) resolves an exact half-integer tie in favor of fewer reviews. Rank is determined by decreasing risk, then the unmodified archived patient-identifier string in lexicographic order, for example "1", "10", "100". With $b=0.20$ and $N=252$, each method selects the top 50 external cases. This paired interval conditions on the observed rankings.')])
add(36,[
p(r'Post hoc descriptive quality-control measures used low-quality segmentation as the positive condition and a review flag as the positive test. Sensitivity equals $d_m$ in Eq. (9); the remaining measures are'),
e(12,r'\begin{aligned}\operatorname{Specificity}_m&=\frac{TN_m}{TN_m+FP_m},\\\operatorname{PPV}_m&=\frac{TP_m}{TP_m+FP_m},\\\operatorname{NPV}_m&=\frac{TN_m}{TN_m+FN_m}.\end{aligned}'),
p(r'PPV and NPV denote positive and negative predictive value. We reported the TP, FP, TN and FN counts and Wilson 95 % intervals for these proportions. These measures assess mask-quality screening, not diagnosis of breast cancer; the Wilson equation is provided in the Supplementary mathematical methods.')])
add(39,[
p(r'The following exploratory analyses were specified for this revision after the original study and retain its scores, low-quality definition and H1–H3. We evaluated $b\in\{0.05,0.10,0.15,0.20,0.25,0.30,0.40,0.50\}$. For each method and target, Eq. (8) selects a threshold using development risks and counts without quality labels; the resulting numerical cutoff is transferred unchanged to both test cohorts. Separately, Eq. (11) selects a cohort-specific equal-review count and ranking.')])
add(40,[
p(r'We used 10,000 patient-bootstrap replicates per route (seed 20261106) to separate test-cohort sampling at the original cutoffs, development resampling and recalibration with fixed test cohorts, and both together. Cohorts were sampled independently, keeping A/B scores and quality labels paired within each record. Repeated draws were retained. Equal review selects exactly 50 external draw records, ordered by decreasing risk, original identifier string and draw-position index. The strict original direction pattern requires external B-minus-A detection above zero at transferred cutoffs and below zero at equal review; ties are separate. Bootstrap percentile 95 % intervals and direction-frequency equations are given in the Supplementary mathematical methods. These are descriptive, nominal sensitivity analyses and do not replace the prespecified Newcombe intervals.')])
add(41,[
p(r'We also used symmetric Kitagawa accounting and direct standardization across dataset-reported benign/malignant strata [13]. Let $s$ denote a diagnostic stratum, $w_{c,s}$ its weight and $p_{c,s}$ its outcome rate in cohort $c\in\{E,I\}$. When all stratum rates are defined, $P_c=\sum_s w_{c,s}p_{c,s}$ and the external-minus-internal difference is'),
e(13,r'\begin{aligned}\Delta_P=P_E-P_I&=C+W,\\C&=\sum_s(w_{E,s}-w_{I,s})\frac{p_{E,s}+p_{I,s}}{2},\\W&=\sum_s(p_{E,s}-p_{I,s})\frac{w_{E,s}+w_{I,s}}{2}.\end{aligned}'),
p(r'Here $C$ is the composition-associated term and $W$ the within-stratum-rate term. Common weights give directly standardized rates:'),
e(14,r'\begin{aligned}w_s^*&=\frac{w_{E,s}+w_{I,s}}{2},\qquad P_c^{\mathrm{std}}=\sum_s w_s^*p_{c,s},\\P_E^{\mathrm{std}}-P_I^{\mathrm{std}}&=W.\end{aligned}'),
p(r'For detection, $w_{c,s}=F_{c,s}/F_c$ and $p_{c,s}=TP_{c,s}/F_{c,s}$; for review, $w_{c,s}=N_{c,s}/N_c$ and $p_{c,s}=R_{c,s}/N_{c,s}$, where $R_{c,s}$ is the flagged count. We obtained nominal percentile intervals from 5,000 independent cohort-level patient-bootstrap replicates (seed 20261107), recalculating weights and rates. Undefined stratum rates remained missing and propagated to dependent components, including when the associated weight was zero. Overall rates were computed directly from aggregate numerators and denominators. This accounting describes observed mixtures and does not estimate causal effects.')])
add(43,[
p(d.paragraphs[43].text+' The absolute-error equation used for numerical comparisons is given in the Supplementary mathematical methods.')])
plan={'source_docx':str(source),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'scope':'Explicit mathematical definitions of existing methods; no new analysis or scientific-result change','display_equation_count':14,'main_numbering':list(range(1,15)),'replacements':replacements,'preserve_other_paragraphs':True,'preserve_all_tables_and_captions':True,'preserve_results_declarations_references':True,'citation_policy':'No reference added. [11] and [12] stay in the H1-H3 interval paragraph; [13] stays in the Kitagawa paragraph. First-appearance sequence remains unchanged.','notation_notes':['Risk r carries patient index; review fraction v carries cohort index, avoiding their conflation.','SAM predicted IoU is raw quality-head output and is not equated with reference IoU.','Candidate infinity is represented by any cutoff above maximum risk; zero review is included.','argmin_lex is explicitly defined as ordered-pair lexicographic minimization.','Top-K minimum over argmin encodes the fewer-at-half tie rule, not banker rounding.','The four directions remain four terms even if clipping produces coincident boxes.','The box upper edge max foreground index+1 matches the actual code.','Undefined rates are NA, with no zero-denominator imputation.','Full Wilson, paired Newcombe with corrected phi, bootstrap, empirical-support caveats and replay-error equations are delegated to Supplementary mathematical methods.'],'source_code_references':['submission/bmt_v9/Reproducibility/score_images.py:34','submission/bmt_v9/Reproducibility/score_images.py:41','submission/bmt_v9/Reproducibility/study_statistics.py:77','submission/bmt_v9/Reproducibility/study_statistics.py:241','experiments/cloud_validation_v1/scripts/budget_transfer.py:129','experiments/cloud_validation_v1/scripts/budget_transfer.py:146','experiments/cloud_validation_v1/scripts/case_mix_decomposition.py:170']}
# Word counts use plain prose (inline math retained as source notation, not a claim about final Word count).
before=' '.join(x['anchor_exact'] for x in replacements);after=' '.join(x.get('text','') for y in replacements for x in y['blocks'] if x['type']=='paragraph')
plan['planning_counts']={'replaced_original_prose_whitespace_words':len(before.split()),'replacement_prose_with_inline_latex_whitespace_words':len(after.split()),'equation_word_count_note':'Final guideline word count must be measured from rendered DOCX; this planning count includes inline LaTeX tokens.'}
out=Path('/workspace/bmt_v10/evidence/main_equation_plan.json');out.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
print(out);print(plan['planning_counts'])
