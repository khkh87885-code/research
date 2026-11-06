# Supplementary equation plan for v10

Preferred placement: after supplementary title/author front matter, before Table S1. Twelve equation groups carry provisional labels (S1)–(S12); root may remap these mechanically. Existing 19 table panels, figure labels and the 15-reference main list remain unchanged.

Main manuscript: retain approximately 11–14 compact groups for scoring and review policies. Keep full interval and post hoc mathematics here.

These equations specify the interval calculations and post hoc analyses used in this study. Definitions of the masks, risk scores, low-quality condition and review policies are given in the main Methods. Rates below are fractions unless explicitly multiplied by 100; interval limits for differences are reported in percentage points. Citations [11–13] refer to the main reference list.

## Proportion and difference intervals

For $x$ successes among $n$ observations, let $\hat p=x/n$ and $z=\Phi^{-1}(0.975)$. The two-sided 95% Wilson score limits without continuity correction are

<!-- wilson -->
$$
(L,U)=\frac{\hat p+\frac{z^2}{2n}\ \pm\ z\sqrt{\frac{\hat p(1-\hat p)}{n}+\frac{z^2}{4n^2}}}{1+\frac{z^2}{n}}.\tag{S1}
$$

Here $x$ and $n$ are the numerator and denominator of the reported proportion. Detection uses low-quality patients as its denominator; review uses all scored patients. A proportion with a zero denominator is undefined and is not assigned an interval.

For the first-minus-second contrast $\hat\Delta=\hat p_1-\hat p_2$, let $(L_j,U_j)$ be the Wilson limits of $\hat p_j$. The independent or paired Newcombe method 10 interval [11,12] is

<!-- newcombe_limits -->
$$
\begin{aligned}\mathcal R(x,y;\rho)&=\sqrt{\max(x^2+y^2-2\rho xy,0)},\\L_{\Delta}&=\hat\Delta-\mathcal R(\hat p_1-L_1,U_2-\hat p_2;\rho),\\U_{\Delta}&=\hat\Delta+\mathcal R(U_1-\hat p_1,\hat p_2-L_2;\rho).\end{aligned}\tag{S2}
$$

Set $\rho=0$ for the independent external-minus-internal H1 and H2 contrasts. For paired comparisons, define $a$, $b$, $c$ and $d$ as the numbers flagged by both methods, by the first method only, by the second method only, and by neither method, within the population used for the contrast. That population comprises low-quality patients for detection and all scored patients for review. For a B-minus-A contrast, first therefore denotes B. The paired method uses

<!-- paired_components -->
$$
N=a+b+c+d,\qquad T=ad-bc,\qquad M=(a+b)(c+d)(a+c)(b+d).\tag{S3}
$$

<!-- paired_correction -->
$$
T^{\mathrm{corr}}=T-\mathbf1\{T>0\}\min(T,N/2),\qquad \rho=\frac{T^{\mathrm{corr}}}{\sqrt M}\quad(M>0).\tag{S4}
$$

If $M=0$, set $\rho=0$. This correction acts only on positive association; a negative $T$ and its negative correlation are retained. The maximum with zero in $\mathcal R$ handles numerical round-off. H1 uses the original independent interval; H2, H3 and supplementary intervals are nominal without multiplicity adjustment. Equal-review paired intervals condition on the observed selections and do not include calibration or re-ranking uncertainty.

## Patient-bootstrap summaries

Let $\theta^{*(b)}$ denote the statistic in replicate $b$, and $\mathcal V$ the set of replicates for which that statistic is finite. The descriptive percentile interval is

<!-- bootstrap_ci -->
$$
\mathrm{CI}_{95\%}^{\mathrm{boot}}=[Q_{0.025}\{\theta^{*(b)}:b\in\mathcal V\},\ Q_{0.975}\{\theta^{*(b)}:b\in\mathcal V\}].\tag{S5}
$$

Quantiles use linear interpolation of the sorted finite replicate values. Undefined detection denominators remain missing; no values are imputed. The three calibration/sampling routes each use 10,000 patient-bootstrap replicates. Within each sampled patient record, A/B scores and the quality label remain paired; repeated patient draws are retained. Cohorts are resampled independently.

For joint direction summaries, let $\mathcal V_J$ contain replicates with both external B-minus-A detection contrasts defined: $\Delta_{\mathrm{fixed}}^*$ at transferred thresholds and $\Delta_{\mathrm{equal}}^*$ at equal top-50 review. The four mutually exclusive empirical frequencies are

<!-- bootstrap_original_opposite -->
$$
\begin{aligned}\hat f_{+,-}&=\frac{1}{\lvert\mathcal V_J\rvert}\sum_{b\in\mathcal V_J}\mathbf1\{\Delta_{\mathrm{fixed}}^{*(b)}>0,\ \Delta_{\mathrm{equal}}^{*(b)}<0\},\\\hat f_{-,+}&=\frac{1}{\lvert\mathcal V_J\rvert}\sum_{b\in\mathcal V_J}\mathbf1\{\Delta_{\mathrm{fixed}}^{*(b)}<0,\ \Delta_{\mathrm{equal}}^{*(b)}>0\}.\end{aligned}\tag{S6}
$$

<!-- bootstrap_tie_same -->
$$
\begin{aligned}\hat f_0&=\frac{1}{\lvert\mathcal V_J\rvert}\sum_{b\in\mathcal V_J}\mathbf1\{\Delta_{\mathrm{fixed}}^{*(b)}=0\ \mathrm{or}\ \Delta_{\mathrm{equal}}^{*(b)}=0\},\\\hat f_{\mathrm{same}}&=\frac{1}{\lvert\mathcal V_J\rvert}\sum_{b\in\mathcal V_J}\mathbf1\{\Delta_{\mathrm{fixed}}^{*(b)}\Delta_{\mathrm{equal}}^{*(b)}>0\}.\end{aligned}\tag{S7}
$$

The original strict pattern is $(+,-)$, the opposite strict pattern is $(-,+)$, and the frequency of any strict reversal is $\hat f_{+,-}+\hat f_{-,+}$. A zero contrast is not a strict reversal. These frequencies describe resampling of the observed patients and are not p-values, posterior probabilities or population probabilities.

At the locked thresholds, the 16 external low-quality patients comprise 10 detected by both methods, none by A only, three by B only and three by neither. R1 cannot create an A-only detection from this empirical support, so its fixed-threshold B-minus-A distribution is structurally nonnegative. Its percentile interval does not exclude a population advantage for A. Bootstrap intervals supplement, and do not replace, the prespecified Newcombe intervals.

## Diagnostic-stratum accounting and standardization

For cohort $c\in\{I,E\}$ and dataset-reported diagnostic stratum $s\in\{\mathrm{benign},\mathrm{malignant}\}$, write $d_{c,s}$ for the denominator and $u_{c,s}$ for its numerator. In the detection analysis, $d_{c,s}=F_{c,s}$ (low-quality patients) and $u_{c,s}=TP_{c,s}$ (flagged low-quality patients). In the review analysis, $d_{c,s}=N_{c,s}$ (all scored patients) and $u_{c,s}=R_{c,s}$ (flagged patients). Then

<!-- stratum_rates_weights -->
$$
p_{c,s}=\frac{u_{c,s}}{d_{c,s}},\qquad w_{c,s}=\frac{d_{c,s}}{\sum_t d_{c,t}},\qquad P_c=\frac{\sum_s u_{c,s}}{\sum_s d_{c,s}}.\tag{S8}
$$

When the stratum rates are defined, $P_c=\sum_s w_{c,s}p_{c,s}$. The symmetric Kitagawa identity [13] partitions the external-minus-internal difference into a composition-associated term $C$ and a within-stratum-rate term $W$:

<!-- kitagawa_total -->
$$
\Delta_{EI}=P_E-P_I=C+W.\tag{S9}
$$

<!-- kitagawa_components -->
$$
\begin{aligned}C&=\sum_s(w_{E,s}-w_{I,s})\frac{p_{E,s}+p_{I,s}}{2},\\W&=\sum_s(p_{E,s}-p_{I,s})\frac{w_{E,s}+w_{I,s}}{2}.\end{aligned}\tag{S10}
$$

Using the arithmetic-mean common weights gives direct-standardized cohort rates and a standardized difference equal to $W$:

<!-- common_weights -->
$$
\begin{aligned}w_s^*&=\frac{w_{E,s}+w_{I,s}}{2},\qquad P_c^{\mathrm{std}}=\sum_s w_s^*p_{c,s},\\P_E^{\mathrm{std}}-P_I^{\mathrm{std}}&=W.\end{aligned}\tag{S11}
$$

All weights and stratum rates are recalculated in each of 5,000 within-cohort patient-bootstrap replicates. A stratum rate with a zero denominator remains undefined, even if its weight is zero; the missing value propagates to any component that uses that rate. Overall rates are calculated from aggregate numerators and denominators and remain defined when the total denominator is positive. This leaves 4,999 valid detection-component replicates because one draw has no external benign low-quality patient; detection totals and all review terms have 5,000 valid replicates. Each term uses its own finite-value percentile interval. Point components add to the total before rounding; interval endpoints need not add. This post hoc accounting is descriptive, not causal attribution or a percent-explained analysis, and two diagnostic strata do not remove other confounding.

## Numerical replay differences

For the six selected patients, let $v_{ij}^{\mathrm{CPU}}$ and $v_{ij}^{\mathrm{archive}}$ be the CPU-replayed and archived values of numerical field $j$. The eight fields are reference Dice, initial predicted IoU, risk A, risk B and the four initial-to-shifted Dice values. We calculated signed differences and maximum absolute differences as

<!-- replay_errors -->
$$
\begin{aligned}\delta_{ij}&=v_{ij}^{\mathrm{CPU}}-v_{ij}^{\mathrm{archive}},\qquad\epsilon_j=\max_{i\in\mathcal I_6}\lvert\delta_{ij}\rvert,\\\epsilon_{\mathrm{all}}&=\max_{i\in\mathcal I_6,\ j\in\{1,\ldots,8\}}\lvert\delta_{ij}\rvert.\end{aligned}\tag{S12}
$$

Here $\mathcal I_6$ is the same six-patient subset, so $\epsilon_{\mathrm{all}}$ summarizes 48 numerical comparisons. Exact equality and agreement of the fixed review decisions were checked separately. Numerical agreement of selected scores or decisions does not establish pixel identity with the unarchived original CUDA masks, create independent patients, or demonstrate improved screening performance.

## Integration notes

JSON blocks use type=heading|paragraph|equation; paragraph mathematics has single-dollar delimiters. Formula labels are provisional. Display rows are aligned as needed for page width. Absolute-value/norm delimiters are fixed (not dynamically sized). The compact T correction exactly preserves negative correlations and reproduces the piecewise source implementation. Overall stratum-accounting cohort rates use aggregate numerators/denominators, preserving defined totals when one stratum rate is missing.
