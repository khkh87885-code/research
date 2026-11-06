# Independent case-mix decomposition check

**PASS.** Independently recomputed raw-score counts and exact rational arithmetic confirm all four original-record decompositions and direct-standardized differences. All 20,000 exported bootstrap rows match an independent replay of the 5,000 paired-patient draws at tolerance 1e-12, including all percentile intervals and NA/valid counts.

| Method | Outcome | Overall E−I, pp | Composition-associated, pp | Within-stratum-rate, pp | Standardized internal, % | Standardized external, % |
|---|---|---:|---:|---:|---:|---:|
| A | detection | -13.844086 | -1.615439 | -12.228647 | 74.728647 | 62.500000 |
| A | review_fraction | -6.557645 | 0.644644 | -7.202289 | 20.734258 | 13.531969 |
| B | detection | 8.131720 | -0.781345 | 8.913066 | 72.773762 | 81.686828 |
| B | review_fraction | -4.531084 | 0.791241 | -5.322325 | 18.017192 | 12.694867 |

Exact Fraction identities hold: composition-associated + within-stratum-rate = overall external − internal; direct-standardized external − internal = within-stratum-rate.

- Detection weights are the diagnostic composition among low-quality cases: internal 53/93 and 40/93; external 8/16 and 8/16. They are not all-patient diagnostic proportions.
- One bootstrap replicate (2468) has no low-quality benign external case. Detection decomposition components and external standardized rates/differences are NA for both methods; overall rates and internal standardized rates remain defined.
- A detection composition-associated component is negative (-1.615439237 pp), and the within-stratum-rate component is negative (-12.228646784 pp).
- This is post hoc descriptive accounting, not causal attribution or removal of device/annotation confounding.
- All calculations use archived scores; no model inference was run.

Maximum bootstrap value discrepancy: 2.5e-16 raw fraction. Maximum percentile-limit discrepancy: 1.39e-16. Actual independent-check elapsed time: 4.164270 seconds.
