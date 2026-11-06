# BMT v7 云端补充验证（2026-11-06）

已在当前 Codex 云端主机完成三项事后探索性验证：完整预算扫描、三路线患者bootstrap、良恶性构成标准化/对称分解。未执行新模型推理、训练或增加独立患者。原预设H1–H3和Newcombe区间保留。

[中文执行报告 PDF](reports/BMT_cloud_validation_report_zh.pdf) · [Word](reports/BMT_cloud_validation_report_zh.docx) · [Markdown](reports/BMT_cloud_validation_report_zh.md)

| 模块 | 计算量 | 实际记录耗时 | 关键结果 |
| --- | --- | --- | --- |
| 预算扫描 | 8预算、2规则、2测试队列、2方法 | 1.071秒，含导出作图 | 没有方法在全预算下始终检出更多低质量病例 |
| 校准/抽样/排序稳定性 | 3路线，各10,000次 | 5.914秒，含CSV/图；bootstrap本身4.042秒 | 全部重采样下原方向严格反转3,094/10,000次（30.94%），任一差值为零28.08% |
| 诊断构成分解 | 4终点，各5,000次 | 2.830秒，含检查/导出/作图；bootstrap本身1.107秒 | A复核率外部−内部−6.56pp = 构成相关+0.64pp + 层内率−7.20pp |

这些耗时对应各脚本记录的端点，不包含开发、人工审阅和报告制作，不能相加宣称为整项工作的总耗时。环境为CPU配额2核、8GiB，无GPU；数值单进程/线程1。

原方向严格反转：外部固定阈值B−A检出率>0且等复核50例B−A<0。30.94%是当前样本下的经验重采样频率，不是p值、总体概率或新患者信息。路线1中原样本无A-only低质量病例，因此经验bootstrap无法生成它，固定阈值差值被限制为非负；其[0,+40]pp百分位区间不能排除总体A优势，不能替换原配对Newcombe区间[−4.28,+40.04]pp。构成分解是描述性代数分账，不是因果效应或“解释比例”。

## 文件

- `protocol/analysis_plan.json`：计算前固定的本轮事后方案；不是原研究预注册。
- `protocol/clarification_addendum.json`：原字符串patient_id同分规则、抽样重复保留、半整数向下和检出率权重说明。
- `scripts/`：三个独立命令行入口及交付报告构建脚本。
- `results/`：全精度JSON/CSV、逐次bootstrap、输入/脚本哈希、种子和实际运行信息。归档版将两份大CSV无损压缩为`.csv.gz`；原CSV的字节数和SHA-256见`RAW_CSV_COMPRESSION.json`。
- `figures/`：三张PNG和矢量PDF。
- `reports/`、`qa/`：中文总报告、各模块报告及独立数值/方法/视觉复核记录。

全部预算一并报告；不按本轮网格选择有利预算。外部仍为252例患者和16例低质量掩膜。原始影像/模型权重不重复打包。

## 从新clone复现

三个入口都会校验源提交为`f9cfdc49b6e6a9e037443f6ce077006bc9377960`。最新main增加了本轮归档，不能直接作为源HEAD。先建固定提交的独立worktree，再向新的输出目录运行；显式提供全部路径，以免使用历史默认路径。

```sh
git clone https://github.com/khkh87885-code/research.git research
git -C research worktree add --detach ../bmt_validation_source f9cfdc49b6e6a9e037443f6ce077006bc9377960
python -m venv .venv-bmt-validation
. .venv-bmt-validation/bin/activate
python -m pip install -r research/experiments/cloud_validation_v1/requirements.txt
bmt_bundle="$PWD/research/experiments/cloud_validation_v1"
bmt_source="$PWD/bmt_validation_source"
bmt_output="$PWD/bmt_validation_rerun"
mkdir -p "$bmt_output"
python "$bmt_bundle/scripts/budget_transfer.py" --source-root "$bmt_source" --output-root "$bmt_output" --protocol "$bmt_bundle/protocol/analysis_plan.json"
python "$bmt_bundle/scripts/bootstrap_stability.py" --repo "$bmt_source" --output "$bmt_output" --replicates 10000 --seed 20261106 --plan "$bmt_bundle/protocol/analysis_plan.json"
python "$bmt_bundle/scripts/case_mix_decomposition.py" --source-root "$bmt_source" --output-root "$bmt_output" --protocol "$bmt_bundle/protocol/analysis_plan.json"
```

记录环境Python 3.12.14。命令只读已有评分和元数据，无需PyTorch、GPU或模型权重。输入来源/许可沿用仓库`data/README.md`及`reproducibility/README.md`。运行时间、路径、时间戳等provenance会随复跑环境变化；用数值与原始CSV内容核验结果。

报告构建不是上述数值复现的依赖。若需重建中文DOCX，额外安装`requirements-report.txt`并使用Noto Sans CJK SC字体；`scripts/build_execution_report.py`读取其相邻目录的已有JSON/CSV作报告，不重算统计。PDF转换另需LibreOffice。

gzip文件可用`gzip -dk 路径.csv.gz`解压，或直接用Python `gzip.open(...,'rt')`读取。不要在归档结果目录覆盖原始运行记录。

## 尚未执行的模型验证

优先补六例漏检真实预测轮廓。当前精确SAM ViT-B检查点未找到，官方检查点下载主机不在当前网络允许范围；本轮未执行推理。可用精确权重后，沿用`submission/bmt_v7/Analysis/CASE_RERUN_README.md`的校验与定向重放流程。合成框扰动、独立操作者提示框和新增外部队列是不同验证，需要各自输入与预先固定的设计。

本轮通讯元数据按作者最新确认使用邮编400016；来源记录中的官方401331作为历史证据保留。没有进行期刊投稿。
