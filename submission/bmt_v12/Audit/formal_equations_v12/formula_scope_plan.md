# v12 concise equation plan

Dice supplies the common quality/agreement definition. The two risks define the methods being compared. The two Kitagawa terms are the only unfamiliar mathematical accounting operation retained in the exploratory supplement. Routine arithmetic, algorithms fully specified by finite selection rules, named standard interval procedures and error bookkeeping do not require separate displayed equations.

## Main

Anchor paragraph 26

We obtained the initial prompt box from the tight bounding box of the nonempty reference mask, using half-open pixel bounds with upper coordinates one pixel beyond the last foreground index, expanded each horizontal side by 10 % of the width and each vertical side by 10 % of the height, and clipped the result to the image. This is a reference-informed, known-location (oracle-localization) setting, not a test of autonomous lesion localization. We encoded the image once and used the resulting embedding for the initial prediction and four additional predictions (Figure 2). The fixed 10 % context margin was used consistently across datasets.

Anchor paragraph 27

For each image, let $P_0$ be the initial binary prediction, $P_j$ its prediction under shifted prompt $j$, and $G$ the manual reference mask. For binary masks $U,V$ with at least one foreground pixel between them, Dice agreement is

Equation (1)

$$D(U,V)=\frac{2\lvert U\cap V\rvert}{\lvert U\rvert+\lvert V\rvert}.$$

Here $\lvert\cdot\rvert$ counts foreground pixels. For consistency scoring, Dice is defined as one when both predicted masks are empty. Method A uses the confidence risk in Eq. (2):

Equation (2)

$$r_{\mathrm{A}}=1-\widehat q.$$

Here $\widehat q$ denotes the raw predicted intersection over union (IoU) returned by the SAM quality head for the initial mask. For method B, we shifted the initial clipped box left and right by 5 % of its width and up and down by 5 % of its height, clipping each shifted box to the image. The four initial-to-shifted Dice values define the disagreement risk

Equation (3)

$$r_{\mathrm{B}}=1-\frac{1}{4}\sum_{j=1}^{4}D(P_0,P_j).$$

All four directions were retained when clipping produced coincident boxes. These deterministic shifts probe local stability relative to box size. Method B adds four mask-decoder passes while reusing the image embedding. Recorded inference times cover the combined pipeline; A-only and incremental B times were not separately benchmarked.

Anchor paragraph 28

The quality reference for both methods was the initial prediction’s Dice against the manual mask, $D(P_0,G)$ in Eq. (1). An empty initial prediction against the nonempty reference has Dice zero. Low quality was defined as reference Dice below 0.70, an operational cutoff for this evaluation. The raw model confidence in Eq. (2) and prediction-consistency score in Eq. (3) remain separate from this reference-quality outcome.

Anchor paragraph 33

The analysis included cases with a valid reference Dice and both finite risk scores. The procedure allowed one retry with the same configuration after a technical failure and recorded persistent failures separately. We report low-quality detection as the number of flagged low-quality masks divided by the number of low-quality masks. Simulated review is the number of flagged cases divided by all scored cases. Misses per 100 patients is 100 times the number of unflagged low-quality masks divided by all scored cases. Rates with a zero denominator were left undefined.

Anchor paragraph 36

As post hoc descriptive quality-control measures, we additionally tabulated true-positive (TP), false-positive (FP), true-negative (TN) and false-negative (FN) counts, sensitivity, specificity, positive predictive value (PPV) and negative predictive value (NPV), with Wilson 95 % intervals (Tables S6 and S7). Low-quality segmentation was the positive condition and a review flag the positive test. These measures assess mask-quality screening, not diagnosis of breast cancer.

Anchor paragraph 41

We also used symmetric Kitagawa accounting and direct standardization across dataset-reported benign/malignant strata [13]. The external-minus-internal difference was partitioned into a composition-associated term and a within-stratum-rate term. Common weights were the arithmetic mean of the two cohort weights. Detection used the diagnostic shares among low-quality masks, whereas review fractions used shares among all scored patients. We obtained nominal percentile intervals from 5,000 independently sampled cohort-level patient-bootstrap replicates (seed 20261107), recalculating all weights and rates. Undefined stratum denominators remained missing. This accounting describes the observed mixtures and does not estimate causal effects. The two component definitions are given in Eqs. (S1) and (S2) with Table S12.

## Supplement

Anchor paragraph 77

For diagnostic stratum $s$, let $w_{c,s}$ be its weight and $p_{c,s}$ its outcome rate in cohort $c$, with E denoting external and I internal testing. For detection, weights are diagnostic shares among low-quality patients and rates are stratum-specific low-quality detection. For review, weights are diagnostic shares among all scored patients and rates are stratum-specific review fractions. Rates in Eqs. (S1) and (S2) are fractions; Table S12 reports differences in percentage points. The symmetric Kitagawa composition-associated term and within-stratum-rate term are

Equation (S1)

$$C=\sum_s(w_{E,s}-w_{I,s})\frac{p_{E,s}+p_{I,s}}{2},$$

Equation (S2)

$$W=\sum_s(p_{E,s}-p_{I,s})\frac{w_{E,s}+w_{I,s}}{2}.$$

Together, $C$ and $W$ sum to the external-minus-internal overall rate difference when the stratum rates are defined. Weights and rates are recomputed in each bootstrap draw.

Anchor paragraph 81

Direct standardization uses the arithmetic mean of the two cohort weights for each diagnostic stratum. When the stratum rates are defined, the resulting standardized external-minus-internal difference equals the within-stratum-rate term $W$ in Eq. (S2). Overall rates are calculated directly from aggregate numerators and denominators. Components may not sum to the displayed total after rounding. Method: Kitagawa EM, J Am Stat Assoc 1955;50:1168–1194, doi:10.1080/01621459.1955.10501299.

## Layout refinements

Move the qhat definition after Eq2 so punctuation cannot begin a new line.
Use ordinary upright E/I cohort names in prose, consistent with descriptive subscripts.
State fractional-rate versus percentage-point table units explicitly.
