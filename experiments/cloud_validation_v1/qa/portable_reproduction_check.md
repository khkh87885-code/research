# Portable reproduction check

**PASS** — three documented command-line entrypoints were tested in a newly created detached source worktree and new output directory.

Source commit: `f9cfdc49b6e6a9e037443f6ce077006bc9377960`. Python: 3.12.14. Existing dependencies match exact requirements; a fresh pip installation/isolated virtual environment and remote git-clone transfer were not retested.

## Executed commands

```sh
/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python /workspace/bmt_cloud_validation/scripts/budget_transfer.py --source-root /workspace/bmt_validation_source_tmp --output-root /workspace/bmt_validation_rerun_tmp --protocol /workspace/bmt_cloud_validation/protocol/analysis_plan.json
```
Exit 0; wall time 1.506 s.

```sh
/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python /workspace/bmt_cloud_validation/scripts/bootstrap_stability.py --repo /workspace/bmt_validation_source_tmp --output /workspace/bmt_validation_rerun_tmp --replicates 10000 --seed 20261106 --plan /workspace/bmt_cloud_validation/protocol/analysis_plan.json
```
Exit 0; wall time 6.434 s.

```sh
/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python /workspace/bmt_cloud_validation/scripts/case_mix_decomposition.py --source-root /workspace/bmt_validation_source_tmp --output-root /workspace/bmt_validation_rerun_tmp --protocol /workspace/bmt_cloud_validation/protocol/analysis_plan.json
```
Exit 0; wall time 3.317 s.

## Result agreement

| Result CSV | Data rows | Byte-identical | Full cell agreement |
| --- | ---: | --- | --- |
| `results/budget_transfer/calibration.csv` | 16 | True | True |
| `results/budget_transfer/performance.csv` | 64 | True | True |
| `results/budget_transfer/paired_contrasts.csv` | 32 | True | True |
| `results/bootstrap_stability/iterations.csv` | 30000 | True | True |
| `results/case_mix_decomposition.csv` | 4 | True | True |
| `results/case_mix_decomposition_strata.csv` | 16 | True | True |
| `results/case_mix_decomposition_bootstrap.csv` | 20000 | True | True |

Bootstrap iteration CSV SHA-256: `c387d4964494b696f78171d202806767f21a594491ce1c9cfdf47f40f1e5d87e`; case-mix iteration CSV SHA-256: `3a126a9c1d82eb8f5fde9d6731ce74d9e6876205a6cbcc0acad4cd8e23fecf39`.

All selected deterministic JSON fields and budget-selected patient IDs agree exactly. Runtime, timestamps, absolute paths and branch provenance are allowed to differ and were not mistaken for numerical discrepancies.

All 13 scientific input/helper files (913,812 bytes) had identical before/after contents in both the original and detached source trees. Aggregate byte checksum: `63f40bfc4abcceb38f6e32e9450a2d9c0c13bed1fb3d223c63a2f1767aa6617c`. All three algorithm scripts, the plan and all pre-existing archived result files were unchanged.

The initial preflight failure is retained in portable_reproduction_preflight_failure.json. It preceded all analysis execution and resulted from comparing unrelated active-checkout postal/README/package edits with the fixed commit. The successful check covers every actual scientific input/helper and the detached worktree state; it does not require unrelated packaging files in the active checkout to match the older source commit.

The temporary worktree and output directory were removed after checks passed. The original archived results were not overwritten. This test exercises path portability in the installed pinned environment; it does not claim a new independent scientific replication or fresh dependency-installation test.

Total verification wall time: 13.623 s.
