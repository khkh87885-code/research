# Independent bootstrap review receipt

**PASS.** Read-only review of the frozen protocol, current implementation and realized production outputs completed at 2026-11-06T09:22:24.025319+00:00.

Current script SHA-256: `86bd575634946c8810b22b962bf4ac73f83ced3751c4f9a30c348ef140728720`. It matches the script hash recorded by production. Source commit: `f9cfdc49b6e6a9e037443f6ce077006bc9377960`.

The reviewer independently checked all 3,279 discrete calibration configurations for cohort sizes 1–7 and risk scores −1, 0, 1 against ordinary-Python candidate enumeration. Another 150 synthetic samples with repeated patients and string-ID ties matched independent Python sorting. The checks confirmed tie-group calibration, nearest 20% with fewer reviews at equal distance, the zero-review option, A/B/label pairing, occurrence preservation, and ordering by risk, original CaseID string, then draw position. Zero-quality denominators, mixed and all-NA distributions, and a full 3×3 sign matrix plus one NA record passed.

Read-only checks of all 30,000 production CSV rows confirmed 10,000 iterations per route; each route's percentile bounds, medians and sign counts matched the JSON; all 3×3 matrices summed to 10,000 jointly valid iterations. Route 2 retained −6.25 pp in all 10,000 equal-top50 values and preserved the original 93/16 quality denominators. Routes 1 and 3 shared identical equal-review values for each corresponding iteration. All equal-review selections retained 50 draw records.

The external original patient IDs are unpadded strings. The observed low-quality paired table was independently reconfirmed: both 10, A-only 0, B-only 3, neither 3. Accordingly, route 1 cannot create A-only records and its fixed-cutoff B−A contrast is structurally nonnegative under this empirical support. This does not exclude a population A advantage. The original paired Newcombe interval [-4.28359563, 40.03889796] pp is preserved.

An earlier all-NA summary-key inconsistency was fixed by the implementation owner; the current unified schema and None-valued undefined summaries were rechecked. No current numerical implementation blocker remains.

The reviewer **did not rerun the large bootstrap**, train a model, run model inference, or modify the implementation, protocol or original data. This receipt validates algorithms through small independent checks and aggregates existing production outputs; it does not add inferential resamples. Plot rendering and page layout were outside this receipt's scope.
