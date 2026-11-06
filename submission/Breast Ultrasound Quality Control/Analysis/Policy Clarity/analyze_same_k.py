"""Post hoc descriptive lookup of K33/35/50 from unchanged archived CUDA scores.

No inference, bootstrap, threshold recalibration or inferential testing occurs.
"""
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
import csv,hashlib,json,math,subprocess

ROOT=Path('/workspace/research_source')
BASE=ROOT/'submission/Breast Ultrasound Quality Control/Reproducibility'
OUT=Path('/workspace/policy_clarity/analysis')
PATHS={'validation_cases':BASE/'records/validation_cases.csv','review_curves':BASE/'review_curve_counts.csv','study_lock':BASE/'study_lock.json','primary_reference':BASE/'reference/primary.json','supplementary_reference':BASE/'reference/supplementary.json','source_checksum_manifest':BASE/'SHA256SUMS.txt'}
BUDGETS=(33,35,50)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rows(p):
 with Path(p).open(encoding='utf-8-sig',newline='')as f:return list(csv.DictReader(f))
def IDs(items):return[r['patient_id']for r in items]
def display_ids(ids):return[byid[i]['image_id']for i in sorted(ids)]

checks=[]
def ck(name,ok,detail=''):
 checks.append({'name':name,'pass':bool(ok),'detail':detail});assert ok,(name,detail)

hashes_before={k:sha(p)for k,p in PATHS.items()}
manifest={line.split(None,1)[1]:line.split(None,1)[0]for line in PATHS['source_checksum_manifest'].read_text().splitlines()if line.strip()}
for key in ['validation_cases','review_curves','primary_reference','supplementary_reference','study_lock']:
 rel=PATHS[key].relative_to(BASE).as_posix();ck('archived manifest SHA matches '+rel,sha(PATHS[key])==manifest[rel])
for rel in ['reproducibility/records/validation_cases.csv','experiments/formal_validation/validation_cases.csv']:
 ck('identical original CUDA score archive '+rel,sha(ROOT/rel)==hashes_before['validation_cases'])
allrows=rows(PATHS['validation_cases']);external=[r for r in allrows if r['split']=='external_test'and r['status']=='scored']
ck('external cohort252 unique patients',len(external)==252 and len(set(IDs(external)))==252)
ck('external rows are BrEaST',all(r['dataset']=='BrEaST'for r in external))
ck('all external patient IDs kept as stored strings',all(isinstance(r['patient_id'],str)and r['patient_id']for r in external))
ck('all external rows have finite original scores',all(all(math.isfinite(float(r[k]))for k in ['dice_vs_reference','risk_A','risk_B'])for r in external))
byid={r['patient_id']:r for r in external}
low={r['patient_id']for r in external if float(r['dice_vs_reference'])<0.70}
ck('external low-quality denominator16',len(low)==16)
ck('archived quality flags agree with strict Dice cutoff',all(int(r['low_quality'])==int(float(r['dice_vs_reference'])<.70)for r in external))
lock=json.loads(PATHS['study_lock'].read_text());primary=json.loads(PATHS['primary_reference'].read_text());supp=json.loads(PATHS['supplementary_reference'].read_text())
thresholds={m:lock['threshold_lock']['methods'][m]['threshold']for m in 'AB'}
ck('checkpoint identity retained',all(r['checkpoint_sha256']==lock['threshold_lock']['model']['weight_sha256']for r in external))
ck('SAM source identity retained',all(r['sam_commit']==lock['threshold_lock']['model']['source_commit']for r in external))
for r in external:
 ck('risk definition consistency '+r['image_id'],abs(float(r['risk_A'])-(1-float(r['sam_predicted_iou'])))<1e-15 and abs(float(r['risk_B'])-(1-sum(float(r['dice_shift_'+d])for d in ['left','right','up','down'])/4))<1e-15)
ranked={m:sorted(external,key=lambda r:(-float(r['risk_'+m]),r['patient_id']))for m in 'AB'}
for m in 'AB':
 alternate=sorted(sorted(external,key=lambda r:r['patient_id']),key=lambda r:float(r['risk_'+m]),reverse=True)
 ck('independent stable-sort ranking equals tuple ranking '+m,IDs(alternate)==IDs(ranked[m]))

curves=rows(PATHS['review_curves']);extcurves=[r for r in curves if r['split']=='external_test']
curve_index={(r['method'],int(r['reviewed'])):r for r in extcurves}
ck('complete archived external curve grid506points',len(extcurves)==506 and len(curve_index)==506)
for m in 'AB':
 tp=0
 for k in range(253):
  if k:tp+=int(ranked[m][k-1]['patient_id']in low)
  r=curve_index[m,k]
  ck('external curve '+m+' K'+str(k),int(r['scored_patients'])==252 and int(r['low_quality_patients'])==16 and int(r['low_quality_detected'])==tp)

locked={m:{r['patient_id']for r in external if float(r['risk_'+m])>=thresholds[m]}for m in 'AB'}
for m,k,tp in [('A',35,10),('B',33,13)]:
 ck('locked '+m+' '+str(k)+' reviews '+str(tp)+' detections',len(locked[m])==k and len(locked[m]&low)==tp)
 ck('archived alert flags '+m,all(int(r['alert_'+m])==int(r['patient_id']in locked[m])for r in external))
 ck('locked '+m+' matches primary reference',primary['cohorts']['external_test']['methods'][m]['R']==k and primary['cohorts']['external_test']['methods'][m]['TP']==tp)
 ck('same-K ranking recovers locked set '+m,set(IDs(ranked[m][:k]))==locked[m])

def paired(aa,bb,pop):
 groups={'both':pop&aa&bb,'A_only':(pop&aa)-bb,'B_only':(pop&bb)-aa,'neither':pop-aa-bb}
 return {'counts':{k:len(v)for k,v in groups.items()},'patient_ids':{k:sorted(v)for k,v in groups.items()},'image_ids':{k:display_ids(v)for k,v in groups.items()}}

outputs=[];details={};allids=set(byid)
for k in BUDGETS:
 selected={m:set(IDs(ranked[m][:k]))for m in 'AB'}
 lowpairs=paired(selected['A'],selected['B'],low)
 ck('paired low-quality categories sum16 K'+str(k),sum(lowpairs['counts'].values())==16)
 row={'cohort':'BrEaST external test','analysis_role':'post hoc descriptive same-K presentation','budget_role':('original protocol supplementary budget; repeated in this post hoc presentation'if k==50 else'post hoc matched count from archived transferred-cutoff review volume'),'K_per_method':k,'N':252,'low_quality_N':16,'review_fraction':k/252,'review_percent':100*k/252}
 detail={'K':k,'selection':{},'paired_detection_among_low_quality':lowpairs,'paired_review_among_all_patients':paired(selected['A'],selected['B'],allids)}
 for m in 'AB':
  ordered=ranked[m];score=float(ordered[k-1]['risk_'+m]);at=[r['patient_id']for r in ordered if float(r['risk_'+m])==score];above=sum(float(r['risk_'+m])>score for r in ordered);tp=len(selected[m]&low);fn=16-tp;fp=k-tp;tn=236-fp
  ck('curve point agreement '+m+' K'+str(k),int(curve_index[m,k]['low_quality_detected'])==tp)
  row.update({m+'_detected':tp,m+'_missed':fn,m+'_false_positive':fp,m+'_true_negative':tn,m+'_detection_fraction':tp/16,m+'_detection_percent':100*tp/16,m+'_PPV_fraction':tp/k,m+'_PPV_percent':100*tp/k,m+'_missed_per_100_patients':100*fn/252})
  detail['selection'][m]={'reviewed':k,'TP':tp,'FN':fn,'FP':fp,'TN':tn,'detection_fraction':tp/16,'PPV_fraction':tp/k,'missed_per_100_patients':100*fn/252,'selected_patient_ids_in_rank_order':IDs(ordered[:k]),'selected_low_quality_patient_ids':sorted(selected[m]&low),'missed_low_quality_patient_ids':sorted(low-selected[m]),'selected_low_quality_image_ids':display_ids(selected[m]&low),'missed_low_quality_image_ids':display_ids(low-selected[m]),'boundary':{'score':score,'last_selected_patient_id':ordered[k-1]['patient_id'],'next_patient_id':ordered[k]['patient_id']if k<252 else None,'next_score':float(ordered[k]['risk_'+m])if k<252 else None,'patients_strictly_above_boundary':above,'boundary_tie_group_size':len(at),'boundary_tie_patient_ids_in_rank_order':at,'selected_at_boundary':k-above,'boundary_tie_split':k-above<len(at)},'archived_curve_TP':int(curve_index[m,k]['low_quality_detected'])}
 row.update({'B_minus_A_detection_count':row['B_detected']-row['A_detected'],'B_minus_A_detection_percentage_points':100*(row['B_detected']-row['A_detected'])/16,**{'paired_low_quality_'+name:value for name,value in lowpairs['counts'].items()}})
 outputs.append(row);details[str(k)]=detail

for m,tp in [('A',14),('B',13)]:
 ck('original top50 '+m+' detection unchanged',details['50']['selection'][m]['TP']==tp==supp['external_equal_review']['methods'][m]['TP'])
 ck('original top50 '+m+' exact ranked selected IDs unchanged',details['50']['selection'][m]['selected_patient_ids_in_rank_order']==supp['external_equal_review']['methods'][m]['selected_case_ids_in_rank_order'])
ck('original top50 low-quality paired table unchanged',details['50']['paired_detection_among_low_quality']['counts']==supp['external_equal_review']['paired_low_quality'])
ck('same counts at33and35',all(details['33']['selection'][m]['TP']==details['35']['selection'][m]['TP']for m in 'AB'))
added={m:(set(IDs(ranked[m][:50]))-set(IDs(ranked[m][:35])))&low for m in 'AB'}
ck('A adds4 and B adds0 low-quality detections at36..50',len(added['A'])==4 and not added['B'])
for k,p in PATHS.items():ck('source file unchanged '+k,sha(p)==hashes_before[k])
OUT.mkdir(parents=True,exist_ok=True)
with (OUT/'equal_review_counts.csv').open('w',encoding='utf-8',newline='')as f:
 writer=csv.DictWriter(f,fieldnames=list(outputs[0]));writer.writeheader();writer.writerows(outputs)
report={'analysis':'Post hoc descriptive same-review-count display at K33,35,50','computed_utc':datetime.now(timezone.utc).isoformat(),'source_repository_head_when_read':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'source_inputs':{k:{'path':str(p),'sha256':hashes_before[k]}for k,p in PATHS.items()},'original_inference_environment':lock['environment'],'scores_used':'Unchanged original CUDA-recorded scores; the current readable submission CSV is byte-identical to both reproducibility/records/validation_cases.csv and experiments/formal_validation/validation_cases.csv. No six-case CPU scores overwrite any input.','selection_rules':{'cohort':'external_test / BrEaST, status scored','N':252,'quality_cutoff':0.70,'quality_operator':'<','low_quality_N':16,'risk_order':'descending original float risk score','tie_break':'Unmodified original patient_id string, ascending lexicographic order; no int conversion and no zero-padding.','budgets':[33,35,50],'budget_reason':'K33 and K35 are the two already reported external locked-cutoff review counts; K50 is the original protocol supplementary budget, repeated in the new same-K presentation. This three-point descriptive presentation was requested before this computation and is not an optimal-budget search or a clinical-capacity validation.'},'original_locked_thresholds':thresholds,'locked_verification':{m:{'reviewed':len(locked[m]),'detected':len(locked[m]&low),'patient_ids':sorted(locked[m])}for m in 'AB'},'global_score_ties':{m:{'tied_score_groups':sum(v>1 for v in Counter(float(r['risk_'+m])for r in external).values()),'patients_in_tied_groups':sum(v for v in Counter(float(r['risk_'+m])for r in external).values()if v>1)}for m in 'AB'},'complete_external_curve_points_verified':506,'summary_rows':outputs,'budget_details':details,'new_low_quality_detections_A_K36_to_K50':display_ids(added['A']),'new_low_quality_detections_B_K36_to_K50':display_ids(added['B']),'checks':checks,'checks_passed':len(checks),'status':'PASS','new_hypothesis_tests':False,'new_confidence_intervals':False,'bootstrap_rerun':False,'threshold_recalibration':False,'model_inference_rerun':False,'main_H1_H2_H3_replaced':False,'prior_top50_planned_status_reclassified':False,'interpretation':['At both K33 and K35, A detects10/16 and B13/16. Equalizing review counts locally therefore does not eliminate the three-detection B advantage observed at locked cutoffs. The unequal locked review volumes A35/B33 alone do not explain that advantage.','Within the same equal-review ranking policy, increasing K35toK50 adds4 low-quality detections to A and0toB; A then detects14/16 versus B13/16. This is evidence of budget-dependent ranking-curve crossing within the observed cohort, not a rule that changing policies must reverse performance.','The comparison of original locked A35/B33 with top50 per method changes both the decision constraint and actual review volume. The added same-K display separates those quantities descriptively; it does not estimate a causal policy effect.','Each external low-quality patient changes detection by6.25percentage points. The K50 A advantage is one patient, so these counts do not establish population superiority. Original H1-H3 and original top50 intervals and plan identity remain unchanged.','The new three-budget display is post hoc and descriptive. K33/35 are post hoc matched counts from archived transferred-cutoff review volumes. K50 is the original protocol supplementary budget, repeated here without reclassification. No budget was selected to maximize significance, and no p-values, new intervals or bootstrap estimates were calculated.'],'outputs':{'equal_review_counts.csv':{'sha256':sha(OUT/'equal_review_counts.csv'),'rows':len(outputs)}}}
(OUT/'same_k_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
md=['# 同实际复核量比较：K=33、35、50','','本次新增为事后描述性展示；使用原归档CUDA评分，不重跑模型、重校准阈值、重采样或显著性检验。K33/35为由原锁阈值外部复核数形成的事后匹配点；K50为原方案预定的补充预算点，本次重复呈现，不改变其原计划身份。','','| 每方法K | 预算点身份 | 复核占比 | A检出/16 | B检出/16 | A漏检 | B漏检 | A PPV | B PPV | 配对both/Aonly/Bonly/neither |','|---:|---|---:|---:|---:|---:|---:|---:|---:|---|']
for row in outputs:
 pair='/'.join(str(row['paired_low_quality_'+x])for x in ['both','A_only','B_only','neither'])
 role='原方案补充预算，本次重复呈现'if row['K_per_method']==50 else'事后匹配原锁阈值复核数'
 md.append(f"| {row['K_per_method']} | {role} | {row['review_percent']:.2f}% | {row['A_detected']} | {row['B_detected']} | {row['A_missed']} | {row['B_missed']} | {row['A_PPV_percent']:.2f}% | {row['B_PPV_percent']:.2f}% | {pair} |")
md+=['','K33和K35时，A均检出10例、B均检出13例；因此锁阈值下B的3例优势并非仅因A35/B33复核数不等。保持同一种等复核数排序政策，将K35增加到K50，A新增4例而B没有新增；K50时A比B多1例。这个结果说明本队列内排序曲线随预算发生交叉，不能概括成“切换政策必然导致排序反转”。','',f"A在排名36–50间新增的低质量病例为：{', '.join(display_ids(added['A']))}；B没有新增。",'','三组预算的六个边界均无同分切割；排序仍严格使用risk降序和原patient_id字符串字典序。完整两方法外部曲线506个计数点已全部独立交叉验证。原locked A35=10/16、B33=13/16和top50 A14/B13均匹配归档结果。','','每个外部低质量病例对应6.25个百分点，K50的A优势仅为1例；本展示不证明总体优效，不替代原Newcombe区间或H1–H3。','','数据来源与校验：',f"- 原始评分SHA256：`{hashes_before['validation_cases']}`；与原formal_validation和reproducibility两份CSV逐字节一致。",f"- 完整曲线SHA256：`{hashes_before['review_curves']}`。",f"- 运行规则、阈值、所选ID序列、低质量配对ID、边界tie与{len(checks)}项检查见same_k_report.json。",'- PPV分母是各方法复核人数K；检出率分母是16个低质量病例；每100患者漏检数分母是252。','','原数据、原论文和生产图均未修改。']
(OUT/'same_k_report.md').write_text('\n'.join(md)+'\n')
print(json.dumps({'rows':outputs,'checks_passed':len(checks),'global_score_ties':report['global_score_ties'],'extra_A_failures_36_50':display_ids(added['A']),'source_sha256':hashes_before['validation_cases'],'output_files':[str(OUT/x)for x in ['equal_review_counts.csv','same_k_report.json','same_k_report.md']]},ensure_ascii=False,indent=2))
