# Analysis and revision evidence

The main manuscript uses the original frozen scores. `../Reproducibility/` retains the verified statistical-replay package and its input hashes.

`table_data/` contains display tables and unrounded values supporting Tables S10–S13. The original budget/bootstrap/decomposition programs and complete draw records are archived at:

https://github.com/khkh87885-code/research/tree/6a7da8181db6ba3db0bb9fa8bef628f284791b2e/experiments/cloud_validation_v1

The exact-checkpoint six-case inference program, all 30 captured masks, dependency lock and independent checks are archived at:

https://github.com/khkh87885-code/research/tree/6a7da8181db6ba3db0bb9fa8bef628f284791b2e/experiments/six_case_replay_v1

Those directories document fixed-source worktrees and portable command-line arguments. `S13_all_48_comparisons_unrounded.csv` supplies every original/replayed value; `S13_independent_array_recomputation.csv` checks values directly from captured arrays. Equal-review review-fraction differences are presented as zero by design; the original conditional binary-flag score calculations remain archived and are not interpreted as uncertainty in that policy difference.

The `build_*.py` files record the local document/figure construction recipes and original workspace locations used for this revision. They render recorded data and actual arrays, and do not generate substitute model predictions. Font sizes, source hashes and production dimensions are recorded in `../Audit/new_figure_provenance.json` and `figure5_provenance.json`. The independent manuscript review is in `../Audit/independent_review.md`.
