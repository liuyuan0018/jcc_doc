# -*- coding: utf-8 -*-
import json
from pathlib import Path
P=Path(__file__).resolve().parent
read=lambda f:json.loads((P/f).read_text())
A=read('results.json');M=read('manifest.json');I=read('catalog.json')['items'];C=read('comparison.json')
names=lambda r:'＋'.join(I[i]['name'] if i>=0 else '手套自身属性' for i in r['items'])
sec=lambda r:'≥180' if r['alive'] else f"{r['frame']/30:.2f}"
trait=lambda r:'＋'.join(str(v)+k for k,v in r['traits'].items())
cats=['普通三件套','1光明＋2普通','1神器＋2普通','1光明＋1神器＋1普通']
lines=['# 180秒观察窗：全装备池单顶测试','','2026-09-18 · 30Hz · 180秒 · 固定1400原始DPS','',
'只延长观察窗，其余承伤、技能、装备和人口条件与[30秒版](../expanded/report.md)一致。没有引入实战加时、狂暴或平局规则。180秒仍存活者并列，不代表无限续航；期末血盾只用于选择展示样例。','',
f"最终运行 {M['runs']:,} 次，249个角色/星级/羁绊情景，107件候选，5,679条摘要。每个模拟检查法力与护盾账本及数值有限性；216个代表配置在30秒模式下与旧结果一致。",'',
'## 三星蜘蛛：原15套的延长结果','','固定6重装、无这两个海克斯。12套通过180秒，3套在30秒后阵亡。','','| 原组合 | 180秒观察结果（秒） |','| --- | --- |']
for r in read('elise-old15-extended.json'):lines.append(f"| {names(r)} | {sec(r['result'])} |")
lines+=['','## 蜘蛛各星级与资源','','| 星级 | 资源 | 展示组合 | 观察秒数 | 通过180秒组合数 |','| --- | --- | --- | --- | --- |']
for star in (1,2,3):
 for cat in range(4):
  r=next(r for r in A if r['hero']=='伊莉丝' and r['star']==star and r['traits']=={'重装':6} and r['category']==cat and r['aug']==0)
  lines.append(f"| {star} | {cats[cat]} | {names(r)} | {sec(r['result'])} | {r['survivors']} |")
lines+=['','## 普通装：新旧观察窗对照','','旧展示装延长是同一羁绊同一装备继续到180秒；新展示装来自180秒全池重算。达到观察上限时不进行无限续航排名。','','| 弈子 | 星级 | 原展示装延长（秒） | 新羁绊 | 新展示装 | 新观察（秒） |','| --- | --- | --- | --- | --- | --- |']
for r in sorted((r for r in C if r['category']==0),key=lambda r:(r['star'],r['new']['cost'],r['hero'])):
 n=r['new'];lines.append(f"| {r['hero']} | {r['star']} | {sec(r['old_extended'])} | {trait(n)} | {names(n)} | {sec(n['result'])} |")
lines+=['','## 解释边界与文件','',
'长观察窗放大了装备成长、护盾转生命、技能循环的作用，也放大了未校准机制的影响。这是固定沙袋条件下的持续承压结果，不是实战胜率排名。随机手套仍仅是理论候选包络。','',
'- [完整机制契约](mechanics.md)','- [全量摘要](results.json)、[组合覆盖与输入哈希](manifest.json)','- [216个新旧配置对照](comparison.json)、[新选配置敏感性](selected-sensitivity.json)','- [30秒回归核对](regression.json)、[独立机制检查](engine_checks.log)','- [飞书在线表格](https://my.feishu.cn/sheets/Ia2isc6J5hH2kzt2YGWcNH9qnXV)','',
'复现：编译 engine.cpp 后运行 `./engine run 0 249 4`；默认180秒，单配置可传 `seconds=30` 做对照。原30秒产物完整保留。']
(P/'report.md').write_text('\n'.join(lines))
print('Wrote 180-second report')
