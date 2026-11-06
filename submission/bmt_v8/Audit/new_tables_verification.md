# Numerical verification of post hoc Tables S10–S13

Status: passed; 139 checks passed; 10 panels under four main supplementary table numbers.

All source artifact hashes were unchanged during the build. No main table, Table S1–S9 or source data was edited.

The 64 budget performance rows and 32 paired contrasts cover eight budgets × two cohorts × two policies × two methods. All archived conditional paired-flag Newcombe calculations were independently recomputed from paired cells.

Publication presentation change: S10C and S10E equal-K review-fraction differences are 0 (by design), with no policy review-difference interval. Nonzero-width conditional intervals for individual paired binary review flags remain unchanged in the scientific archive and unrounded CSV; they are not interpreted as intervals for the equal-K policy review-volume difference. S10B/S10D transferred-threshold review intervals and all detection intervals are unchanged.

Publication presentation change: S10E external 50% equal review uses K=126. S10C internal 50% remains K=425.

The 12 bootstrap endpoint intervals and all three 3×3 sign matrices were independently recomputed from 30,000 raw bootstrap records.

The 12 Kitagawa overall/component intervals and valid counts were independently recomputed from 20,000 raw component records. Detection overall uses 5,000 draws, whereas detection composition and within-stratum terms use 4,999 finite draws.

All 48 CPU replay metrics were independently recomputed from saved NPZ arrays, exactly matching the replay values; all 30 masks were nonempty and all 12 A/B decisions were preserved.

All tables explicitly identify the work as post hoc. Nominal percentile intervals supplement the original Newcombe intervals; repeated patient draws are not new cases.

Product tables use relative source identifiers only. Full-precision data and presentation CSVs are in table_data/.
