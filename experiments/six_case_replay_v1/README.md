# 六例SAM预测轮廓重放：已完成

[两页A4轮廓图 PDF](reports/six_case_contours_A4.pdf) · [中文报告 PDF](reports/six_case_replay_report_zh.pdf) · [Word](reports/six_case_replay_report_zh.docx) · [逐例汇总CSV](reports/six_case_summary.csv) · [48项全精度对照](reports/all_48_numeric_comparisons.csv)

2026-11-06，已从允许访问的GitHub公开发布附件取得与冻结原权重SHA-256完全一致的文件，并在当前Codex主机完成六例定向CPU推理。六个NPZ内保存真实初始及四方向平移预测，共30张掩膜；所有掩膜均非空。

| 项目 | 实测结果 |
| --- | --- |
| 原权重SHA-256 | `ec2df62732614e57411cdcf32a23ffdf28910380d03139ee0f4fcbe91eb8c912` |
| 权重大小 | 375,042,383 bytes |
| 精确SAM源码提交 | `dca509fe793f601edb92606367a655c15ac00fdf` |
| 总墙钟时间（含加载和作图） | 59.419秒 |
| 六例编码/五提示推理时间合计 | 51.613秒 |
| 峰值进程RSS | 3,220.4 MiB，约3.15 GiB |
| 12个A/B复核决定、6个低质量标签 | 全部与原记录相同 |
| 初始参考Dice最大绝对差 | 0.00009610643066648716 |
| 48字段最大绝对差 | 0.0014354348103014225（case105左移一致性Dice） |

相同权重和输入的CPU重放存在小幅数值差异，48字段中6项精确相等、42项不等。保存的是本轮实际CPU掩膜；原六例CUDA数组未归档，无法核验新旧逐像素一致。原研究评分和H1–H3保持不变。

case089、case175、case238仍为共同漏检；case024、case105、case222仍为B补检。参考导出的提示框、10%逐边扩展、±5%平移、float32及单mask输出保持冻结定义。没有新增患者或改用独立操作者提示。

## 文件与证据

- `checkpoint_acquisition_receipt.json`、`checkpoint_sources.md`：公开下载路径、实测完整哈希和文件大小。镜像附件名为`sam_b.pt`，保存为原规范名；字节未转换。推理使用原Meta SAM源码。
- `replay_protocol.json`：本次源仓库提交与冻结脚本SHA-256。
- `predictions/`：6个NPZ、原始高清轮廓图PNG/PDF、实际推理回执。NPZ字段为`image`、`reference`、`masks`（初始/左/右/上/下）、`boxes`、`raw_predicted_ious`。
- `reports/`：适合阅读的两页A4图、逐例汇总和48项对照。
- `qa/`：独立预检、数值重算、文件完整性与视觉核验。case175预测是贴近图像上缘的窄带，高清核验确认其3861个像素，不能误读为空掩膜。
- `runtime_resource.json`、`requirements-lock.txt`：实测运行环境、完整依赖和资源。

当前工作区保留375MB权重和独立虚拟环境；归档包包含代码、完整预测和证据，不重复打包模型或环境。

## 复现

使用Python3.12，在独立环境安装依赖。对源仓库可检出`a739a6c06ffafec40ce9f3eb4c97d6b516f3fc84`；原始图像、参考和逐例评分来自同一仓库，脚本会检查锁定哈希。

```sh
python -m venv /path/to/replay_env
/path/to/replay_env/bin/python -m pip install --extra-index-url https://download.pytorch.org/whl/cpu -r requirements-lock.txt
git clone https://github.com/facebookresearch/segment-anything.git /path/to/segment-anything
git -C /path/to/segment-anything checkout --detach dca509fe793f601edb92606367a655c15ac00fdf
python download_exact_checkpoint.py
PYTHONDONTWRITEBYTECODE=1 /path/to/replay_env/bin/python -B scripts/external_case_audit.py rerun --source /path/to/research --output /path/to/new_replay_output --sam-source /path/to/segment-anything --checkpoint resources/sam_vit_b_01ec64.pth --device cpu --threads 2
```

上述命令在本目录执行，输出目录必须不存在；使用普通Python，保留`assert`校验。下载脚本会拒绝覆盖已有权重，完整哈希不符即拒绝使用。镜像来源为https://github.com/ultralytics/assets/releases/download/v8.3.0/sam_b.pt，经过继承的代理和TLS校验访问允许的GitHub资源主机，未改变网络策略。

原环境为Python3.8.20/NumPy1.24.4/torch2.4.1+cu118/RTX3060 Laptop；本轮为Python3.12.14/NumPy1.26.4/torch2.4.1+cpu/2线程。实测时间用于本机，不作原GPU性能比较。
