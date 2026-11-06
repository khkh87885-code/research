# Independent design and resource review

Reviewed against the fixed `protocol/analysis_plan.json` (SHA-256 `c34718732b856ab31d0d8ae19c88bbbf0f43a9614ea14433d8f62210cc1409c7`), created 6 November 2026 before these supplemental computations. The archived source is commit `f9cfdc49b6e6a9e037443f6ce077006bc9377960`. This reviewer did not change the protocol or computation scripts, install dependencies, download models, edit the manuscript or push files.

## Design verdict

The three planned modules are feasible with the existing scores and are suitable as **post hoc exploratory sensitivity/stability/accounting analyses**. No design-level statistical blocker was identified. They cannot supply independent patients, establish clinical effectiveness, prove equivalence or independently validate the image model. Implementation and output consistency are checked separately below.

## Definitions that must be preserved

1. **Patient resampling and pairing.** Each original patient has one retained image. Bootstrap within the three cohorts independently, retaining the same sampled index for A, B, quality and diagnosis. Repeated draws are frequencies in a resampled empirical dataset: keep every occurrence, do not deduplicate patient IDs, and do not claim they are new independent patients. The 252 external patients remain the empirical basis for all 10,000 draws.
2. **Threshold calibration.** Refit each risk cutoff only from its development resample when that route calls for recalibration. Search observed distinct scores plus the zero-review option, flag `risk >= cutoff`, keep all cutoff ties and choose fewer reviews at equal distance from the target. The same target need not give the same achieved development count for A and B; show achieved counts. Do not tune the target using external outcomes or present a post hoc best target as an independently validated operating rule.
3. **Equal-review ranking.** Use the original lexicographic **string `patient_id`**, as explicitly documented in `study_statistics.py`; an integer ID or zero-padded `image_id` is a different tie rule. For a bootstrap sample, stable occurrence position can resolve repeated identical IDs. Select exactly k occurrences, retain their labels, and rerank the resampled scores when testing equal-review performance. Do not resample already selected top-50 flags and still describe the result as exactly 50 reviews.
4. **Nearest-count ties.** Choose the smaller integer at exactly half a patient. In particular, internal N=851 at target 50% gives **425**, not 426. Python's default `round(425.5)` would violate the plan. The original external 20% comparison remains k=50/252.
5. **Bootstrap routes answer distinct questions.** Test resampling at original cutoffs measures test-sample variation conditional on those cutoffs; calibration-only resampling measures cutoff sensitivity conditional on the original test set; full resampling propagates both empirical sources. The calibration-only route's equal-top-50 external B-minus-A value must stay −6.25 percentage points, because those rankings and the original test patients are unchanged.
6. **Direction frequencies.** A strict reversal means fixed-threshold external B-minus-A detection >0 and equal-review B-minus-A <0 in the same joint-valid draw. Count zero differences as ties and report joint-valid denominators. Such frequencies describe bootstrap stability; they are neither posterior probabilities of superiority nor p-values.
7. **Intervals and validity.** Percentile 95% intervals are descriptive, statistic-specific resampling intervals. Preserve the original Newcombe H1–H3 intervals rather than replacing them. Report valid iterations and undefined-denominator counts. In the decomposition, a missing stratum denominator makes its rate and dependent components undefined, even if a multiplying weight is zero. Overall rates can remain valid when their own denominators are positive. Do not impute zero or omit missingness silently.
8. **Detection decomposition weights.** Detection uses w_s=F_s/F, where F denotes low-quality cases, and p_s=TP_s/F_s. It does not use all-patient diagnosis shares or TP_s/TP. Review uses w_s=N_s/N and p_s=R_s/N_s. Thus detection composition is the diagnostic composition **among low-quality cases**. Do not describe it as the whole cohort's pathology mix or attribute it causally to diagnosis.
9. **Symmetric accounting.** Use E-minus-I consistently. The composition and within-stratum components sum to the raw difference. The directly standardized difference under arithmetic-mean weights equals the within-stratum component. Sampling strata, outcomes and A/B must remain paired. Near-zero totals and opposing components make percentage-explained language misleading; report percentage-point components instead.
10. **Clinical labels and scope.** The legacy field `pathology` is a dataset-reported benign/malignant classification, not universal histopathological verification. Rejoin by patient/case ID to the frozen manifests and the prior label audit. The bootstrap does not propagate image selection, reader/annotation variability, model refitting, unseen hospitals, model-pretraining overlap or independently supplied prompts.

## Independent baseline anchors

| Cohort | N | Low-quality cases | A TP / reviewed | B TP / reviewed |
| --- | ---: | ---: | ---: | ---: |
| BUS-BRA internal | 851 | 93 | 71 / 174 | 68 / 150 |
| BrEaST external | 252 | 16 | 10 / 35 | 13 / 33 |

At the original 20% development target the cutoffs must be A=0.13705134391784668 and B=0.06972856653991777, both reviewing 43/213 development cases. E-minus-I differences are A detection −13.844086 pp, B detection +8.131720 pp, A review −6.557645 pp and B review −4.531084 pp. External B-minus-A detection is +18.75 pp at the locked cutoffs and −6.25 pp at equal 50 reviews. These anchors were independently recomputed from the preserved individual-case CSV before inspecting new module results.

## Current resources and feasible next work

The current local checks show Python 3.12.14, a 2-CPU quota and 8 GiB RAM; `torch` and `segment_anything` are not installed, `nvidia-smi` and GPU device nodes are absent, and the required checkpoint file is absent. Exact SAM source is retained under `/workspace/bmt_v7/resources/segment-anything`. The parent's fresh `protocol/environment_status.json` reports a running environment with restricted networking enforced: the official checkpoint host is not allowed, whereas the CPU-wheel host `download.pytorch.org` is allowed. Current available environment tools expose status/diagnostics/listing, with no environment-configuration write interface. No repeated mirror downloads or dependency installations were performed for this review.

| 可行性级别 | 工作 | 最小条件与可回答的问题 |
| --- | --- | --- |
| **当前可完成** | Budget sweep、三路线bootstrap、对称分解、原始数值和标签核验 | 现有逐例分数/清单即可；评估固定分数上的操作点、重采样稳定性和描述性构成差异。无需GPU或模型权重。 |
| **原则上CPU可做，目前缺权重** | 仅6例精确SAM定向复核及真实预测图 | 上传或允许下载约375 MB的原checkpoint，并核对精确SHA；安装CPU PyTorch/torchvision与兼容NumPy/Pillow，采用2线程、float32、inference mode并记录实际峰值内存。8 GiB环境有合理可行性，但应由真实执行确认，不保证提前无OOM或给出未测耗时。 |
| **需要模型与更长算力预算** | 全队列新提示幅度、初始框规则、模型对照、真正的推理成本测量 | 所有涉及的开发和测试病例都需按预定规则推理、重新校准所需阈值；获取相应精确模型权重和依赖。GPU有利于实际完成规模化实验，不能以CPU六例的耗时推算原RTX成本。只重跑六个已知漏检病例不能估计全队列性能。 |
| **需要新的独立数据或人工工作** | 独立人工提示、读者时间/修正效果、临床效益、独立医院外部验证 | 保存盲法读者绘制的真实提示和操作者信息/时间，或获得新队列及合适标签。围绕同一参考框的合成位移仍是相关的算法扰动，不能充作独立人工提示、新患者或临床读者研究。 |

The minimal six-case checkpoint is `sam_vit_b_01ec64.pth`, SHA-256 `ec2df62732614e57411cdcf32a23ffdf28910380d03139ee0f4fcbe91eb8c912`, with clean SAM source commit `dca509fe793f601edb92606367a655c15ac00fdf`. The prepared CPU plan uses torch 2.4.1+cpu, torchvision 0.19.1+cpu, Pillow 10.4.0 and NumPy 1.26.4 under Python 3.12; those differ from the original Windows/CUDA/Python 3.8/NumPy 1.24 environment and must be disclosed. Compare all eight saved numerical fields, quality/review flags and actual mask arrays; preserve differences and never replace original results silently. The existing script is `/workspace/bmt_v7/scripts/external_case_audit.py`.

Both risk methods use the same initial prediction. B requires four additional prompted predictions after one image encoding. That implementation fact is not a measured B/A latency ratio, clinical review-time saving or hardware cost estimate. Equal-review refers to patient flags, not equal model runtime.

## Cross-module output review

**All three completed modules passed the following independent numerical and definition checks.** The fixed plan remained unchanged. The accompanying clarification addendum records the original string-ID tie key, half-ties-down integer budget and detection-denominator weights; it does not change budgets or endpoints.

- Independently recalculated all 16 development cutoffs, 64 budget performance rows and 32 paired rows (64 detection/review contrasts). Counts, selected-policy point values, 128 Wilson limits and 128 paired Newcombe limits agree. The 20% point exactly reproduces the original thresholds and H1–H3 anchors. The internal 50% equal-review policy uses 425 patients as planned. The full eight-budget grid is reported rather than selecting a favorable point.
- Independently recalculated all four decomposition rows' 32 scalar estimates. Signs, C+R=D and the standardized-difference identity agree. Recalculated all 64 percentile limits from the exported bootstrap values and verified the statistic-specific valid counts. One of 5,000 draws has no external benign low-quality case: the detection components therefore use 4,999 valid draws, while the overall differences still use 5,000. No undefined stratum rate was replaced with zero.
- Checked all 30,000 bootstrap records against their saved integer counts (120,000 endpoint calculations), all 24 endpoint percentile limits, medians, sign counts and joint-valid reversal/tie denominators. Calibration-only equal-top50 stays exactly −6.25 pp. The three routes retain sampled multiplicities and A/B pairing; ranking uses the original string ID followed by sample occurrence position. The separate bootstrap protocol reviewer also exercised repeated-ID, boundary-tie and zero-denominator cases and found no remaining implementation blocker.

### Important boundary interpretation

At the original fixed cutoffs the 16 external low-quality cases contain **zero A-only detections**. An ordinary empirical test bootstrap cannot create that unobserved outcome. Its fixed-cutoff B-minus-A difference is consequently constrained to be nonnegative, producing the reported descriptive percentile interval [0, +40] pp. This is a boundary of the empirical resampling scheme, not evidence that the population difference cannot favor A. Preserve the original paired Newcombe interval [−4.28, +40.04] pp and do not turn the bootstrap interval into a superiority claim.

Likewise, the narrow calibration-only intervals condition on the unchanged original test cohorts. They quantify development-cutoff variation, not total uncertainty about performance in new patients. The full resampling route includes both empirical sources but still reuses only 16 observed external low-quality patients. Its original-direction reversal frequency is a stability description, not a parameter probability.

No script, endpoint, budget, seed or interval method was changed by this independent review. Findings are limited to the preserved score analyses; no new image-model execution or clinical validation is implied.
