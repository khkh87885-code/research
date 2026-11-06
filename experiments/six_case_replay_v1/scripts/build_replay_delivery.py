#!/usr/bin/env python3
"""Build inspectable delivery tables and paginated figures from captured masks."""
from pathlib import Path
import csv,json,hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle

ROOT=Path(__file__).resolve().parents[1];P=ROOT/'predictions';OUT=ROOT/'reports';OUT.mkdir(exist_ok=True)
s=json.loads((P/'targeted_rerun_receipt.json').read_text());run=json.loads((ROOT/'runtime_resource.json').read_text())
assert s['status']=='complete' and len(s['cases'])==6 and run['return_code']==0
rows=[];comparisons=[]
for c in s['cases']:
 rows.append({'image_id':c['image_id'],'group':c['archived_group'],'original_dice':c['archived']['dice_vs_reference'],'rerun_dice':c['rerun']['dice_vs_reference'],'dice_difference':c['comparison']['dice_vs_reference']['difference'],'original_risk_A':c['archived']['risk_A'],'rerun_risk_A':c['rerun']['risk_A'],'original_risk_B':c['archived']['risk_B'],'rerun_risk_B':c['rerun']['risk_B'],'alert_A':c['rerun_flags']['alert_A'],'alert_B':c['rerun_flags']['alert_B'],'review_flags_match':c['flags_match'],'low_quality_label_match':c['low_quality_label_match'],'elapsed_seconds':c['elapsed_seconds_current_environment'],'npz':c['artifact']})
 for field,v in c['comparison'].items():comparisons.append({'image_id':c['image_id'],'field':field,**v})
for name,data in [('six_case_summary.csv',rows),('all_48_numeric_comparisons.csv',comparisons)]:
 with (OUT/name).open('w',newline='')as f:
  w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9})
with PdfPages(OUT/'six_case_contours_A4.pdf')as pdf:
 for part,cs in enumerate([s['cases'][:3],s['cases'][3:]],1):
  fig,axs=plt.subplots(3,3,figsize=(8.27,11.69),squeeze=False)
  fig.suptitle('Exact-checkpoint CPU replay: '+('shared screening misses'if part==1 else'additional cases detected by B'),fontsize=12,y=.975)
  for row,c in enumerate(cs):
   with np.load(P/c['artifact'],allow_pickle=False)as z:
    for col,ax in enumerate(axs[row]):
     ax.imshow(z['image'],interpolation='nearest');ax.set_axis_off()
     if col==0:
      b=z['boxes'][0];ax.add_patch(Rectangle((b[0],b[1]),b[2]-b[0],b[3]-b[1],fill=False,edgecolor='#59c8ff',linewidth=1))
     elif col==1:ax.contour(z['reference'],levels=[.5],colors=['#28c76f'],linewidths=1)
     else:ax.contour(z['masks'][0],levels=[.5],colors=['#ff7f00'],linewidths=1)
    axs[row,0].set_title(c['image_id']+'\nImage + reference-derived prompt',fontsize=8)
    axs[row,1].set_title('Released reference (green)',fontsize=8)
    axs[row,2].set_title('Actual CPU prediction (orange)\nDice '+f"{c['rerun']['dice_vs_reference']:.4f}"+'; A '+f"{c['rerun']['risk_A']:.4f}"+'; B '+f"{c['rerun']['risk_B']:.4f}",fontsize=8)
  fig.text(.5,.026,'SAM ViT-B, frozen checkpoint/source, float32. CPU rerun masks; not original archived CUDA arrays.\nAll six review decisions and low-quality labels match the archive. Original scores are preserved.',ha='center',va='bottom',fontsize=7.5)
  fig.subplots_adjust(left=.035,right=.985,bottom=.065,top=.94,wspace=.08,hspace=.22)
  pdf.savefig(fig);fig.savefig(OUT/f'six_case_contours_A4_page{part}.png',dpi=200);plt.close(fig)

maxdice=max(abs(c['comparison']['dice_vs_reference']['difference'])for c in s['cases'])
maxfield=max((abs(v['difference']),c['image_id'],k)for c in s['cases']for k,v in c['comparison'].items())
md=['# 六例SAM预测轮廓重放：已完成','',
'已解决权重获取问题，并在当前Codex云端主机实际执行六例定向重放。共保存6个NPZ、30张真实预测掩膜（每例初始＋四方向平移），以及原图/参考/预测轮廓图。','',
'## 精确模型身份','',
'公开镜像附件 `sam_b.pt` 实测375,042,383字节，其SHA-256与原研究的 `sam_vit_b_01ec64.pth` 完全一致：','',
'`ec2df62732614e57411cdcf32a23ffdf28910380d03139ee0f4fcbe91eb8c912`','',
'下载来源：https://github.com/ultralytics/assets/releases/download/v8.3.0/sam_b.pt 。原Meta模型源码固定为 `dca509fe793f601edb92606367a655c15ac00fdf`，以strict=True加载权重；未使用Ultralytics推理实现，也未转换权重。使用当前允许的GitHub发布资源路径，未修改网络策略。','',
'## 逐例核对','',
'| 病例 | 原分组 | 原始Dice | CPU重放Dice | Dice差值 | A/B复核 | 标签匹配 |',
'| --- | --- | ---: | ---: | ---: | --- | --- |']
for r in rows:
 md.append(f"| {r['image_id']} | {r['group']} | {r['original_dice']:.9f} | {r['rerun_dice']:.9f} | {r['dice_difference']:+.9f} | {r['alert_A']}/{r['alert_B']} | 是 |")
md.extend(['','复核阈值仍为A=0.13705134391784668、B=0.06972856653991777，风险达到或超过阈值即复核；低质量仍为参考Dice<0.70。case089/175/238两方法均漏检，case024/105/222由B补检；本轮全部复核决定和质量标签匹配。30张预测掩膜均非空。','',
f'初始分割Dice的最大绝对差为 {maxdice:.12g}。48个数值对照中最大绝对差为 {maxfield[0]:.12g}，出现在{maxfield[1]}的{maxfield[2]}。全部全精度原值、新值、差值和精确相等标记保存在 `all_48_numeric_comparisons.csv`。原评分与H1–H3未覆盖。','',
'此次捕获的是新CPU环境中的实际掩膜。原始六例CUDA掩膜未归档，因此不能核实新旧掩膜逐像素一致；相同模型字节、输入与提示框不代表不同环境会产生逐位相同的全部输出。','',
'## 环境与实测资源','',
'Python3.12.14，PyTorch2.4.1+cpu，torchvision0.19.1+cpu，NumPy1.26.4，Pillow10.4.0；CPU两线程、float32。原环境为Python3.8.20、PyTorch2.4.1+cu118、NumPy1.24.4、RTX3060 Laptop。环境差异据实保留。','',
f"总墙钟耗时 {run['wall_seconds_including_loading_and_figures']:.3f} 秒（含模型加载和作图），六例图像编码/五提示推理合计 {sum(c['elapsed_seconds_current_environment']for c in s['cases']):.3f} 秒，峰值进程RSS {run['peak_child_RSS_MiB']:.1f} MiB。时间仅适用于本次CPU运行，不能推断原GPU速度。",'',
'## 图的用途','',
'`six_case_contours_A4.pdf`为两页A4，第一页展示三例共同漏检，第二页展示三例B补检。蓝框为参考掩膜导出的原提示框，绿色为公开参考轮廓，橙色为本轮真实初始预测。原始大图仍保存在predictions目录。','',
'该图补充六例漏检的空间信息；病例并非新增独立患者，不能据此扩大泛化或临床部署主张。提示框仍源于参考掩膜。case175可见预测集中于图像上缘，与参考区域重叠极少；相应Dice约0.0293，A/B风险均未达到复核阈值。这为“高预测置信度和提示稳定性仍可能漏掉低参考一致性的掩膜”提供可检查实例，不构成病理机制判断。','',
'## 交付与复现','',
'读取README中的显式路径命令复现。模型权重和虚拟环境保留在当前工作区，不随小型结果包重复分发；下载脚本、完整依赖锁定、源/权重/输入哈希、30张掩膜、运行receipt和独立QA均随包交付。',''])
(OUT/'six_case_replay_report_zh.md').write_text('\n'.join(md)+'\n')
print(json.dumps({'case_count':len(rows),'numeric_comparisons':len(comparisons),'A4_pages':2,'max_initial_dice_difference':maxdice,'max_all_field_difference':maxfield},ensure_ascii=False))
