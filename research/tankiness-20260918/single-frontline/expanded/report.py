# -*- coding: utf-8 -*-
import json,re,html
from pathlib import Path
P=Path(__file__).resolve().parent
M=json.loads((P/'manifest.json').read_text());assert M['completed']
A=json.loads((P/'results.json').read_text());C=json.loads((P/'catalog.json').read_text());I=C['items'];SS=json.loads((P/'selected-sensitivity.json').read_text())
CAT=['普通三件套','1光明＋2普通','1神器＋2普通','1光明＋1神器＋1普通','至少2件光明／神器','含药水','普通手套候选包络','光明手套候选包络']
AUG=['无这两个海克斯','心之钢（0历史层）','金霖龙','心之钢＋金霖龙']
def score(x):return(x['result']['frame'],x['result']['hp']+x['result']['shield'])
def sec(r):return '≥30' if r['alive'] else f"{r['frame']/30:.2f}"
def trait(r):return '＋'.join(str(v)+k for k,v in r['traits'].items())
def itemnames(r):return '＋'.join(I[i]['name'] if i>=0 else '手套自身属性' for i in r['items'])
def best(hero,star,category=0,aug=0):
 rr=[r for r in A if r['hero']==hero and r['star']==star and r['category']==category and r['aug']==aug]
 return max(rr,key=score) if rr else None
heroes=list(dict.fromkeys(r['hero'] for r in A))
lines=['# 全装备池补全：30 帧单顶前排测试','','2026-09-18 · 固定 1400 混合原始 DPS · 一至三星分别计算','',
'**已补齐当前 S18 目录中、符合原测试“三格、无转职”条件的战斗装备候选，统一给全部 24 个角色重跑。**这次不再只让蜘蛛使用攻速／法强装：所有角色都可从同一装备池选择。',
'',f"共 **107 件可指定候选、{M['unordered_selectable_triples']:,} 种合法无序三件套、249 个角色／星级／羁绊情景，完成 {M['runs']:,} 次基准推演**。另包括 1,260 种手套候选双装包络，已计入运行次数。这里只把最终版本的一轮计入数量，不把中途修订重跑累计充数。",'',
'**装备覆盖完整不等于客户端机制已全部校准。**吸血按模拟实际伤害与目标双抗计算；施法动画、伤害标签、部分神器的阶段系数仍有明确假设。所有结论都是下述统一沙袋条件里的结果，不能直接当实战胜率或唯一最优出装。','',
'## 这次到底补了哪些','','| 类别 | 数量 | 处理 |','| --- | --- | --- |',
'| 普通成装 | 35 | 包括汲取剑／饮血剑、正义、夜刃、水银，以及全部攻速、法强、回蓝、输出装 |',
'| 光明成装 | 35 | 使用各自数值与特效，不简单统一翻倍 |',
'| 神器 | 31 | 包括中娅、死亡之蔑、禁忌雕像、双圣盾、智慧末刃、恶火小斧、光盾等 |',
'| 单次药水 | 6 | 生命、法力、爆炸及对应光明版；只计这一场消耗 |',
'| 随机手套 | 另列2种 | 各枚举630对候选双装作为包络；实际配装表与掉落概率未核实，不把最好随机结果当可指定推荐 |','',
'普通装允许重复；描述明确“唯一”的物品禁止重复。未标唯一物品的重复特效按模型契约处理。**纹章、人口冠冕、散件、局外永久补剂仍在原测试范围之外。**两个当前目录都未列出旧辅助装备，不把旧版救赎、军团等混入当前榜；视界专注按目录“金铲铲已移除”标记排除。全部纳入和排除条目见 [装备清单](coverage.md)。','',
'## 组合覆盖账单','','以下是无海克斯额外条件时，每个羁绊情景都会遍历的组合数。心之钢、金霖龙、双海克斯另按必带装备与人口条件增加分支。','',
'| 资源条件 | 每个情景的候选数 |','| --- | --- |']
for k in range(8):lines.append(f"| {CAT[k]} | {M['counts_by_aug_category']['0-'+str(k)]:,} |")
lines+=['','不把三件光明／神器的结果与三件普通装直接争第一。达到 30 秒的组合并列；保存一个期末血盾较多的展示样例，不意味着它能在 30 秒以后活得最长。','','## 蜘蛛：补全后看到了什么','',
'依然采用 3 人集火、1400 原始 DPS、50% 物理普攻＋50% 魔法，无重伤、破抗、真伤、敌方控制。下表固定 **6 重装、无这两个海克斯**。','',
'| 星级 | 装备条件 | 一个展示三件套 | 存活秒 | 此档通过30秒的组合数 |','| --- | --- | --- | --- | --- |']
for star in (1,2,3):
 for cat in (0,1,2,3):
  r=next(r for r in A if r['hero']=='伊莉丝' and r['star']==star and r['traits']=={'重装':6} and r['aug']==0 and r['category']==cat)
  lines.append(f"| {star}星 | {CAT[cat]} | {itemnames(r)} | {sec(r['result'])} | {r['survivors']:,} |")
sp=next(r for r in A if r['hero']=='伊莉丝' and r['star']==3 and r['traits']=={'重装':6} and r['category']==0 and r['aug']==0)
lines+=['',f"三星蜘蛛在普通成装池里有 **{sp['survivors']} 套**通过 30 秒；“板甲＋羊刀＋大天使”仍是其中一个有效样例。说明它确实存在靠攻速、法强、逐次回血支撑的续航路线。一、二星的启动承受能力仍不同，不能把2费与2星混为一谈。",'',
'## 所有角色的普通成装结果','',
'下面每行取该角色、该星级的一个最佳原生防御羁绊情景。达到 30 秒的样例不互相排序。三星四五费的获取成本与普通追三星不同，按费用自行区分。全量 5,679 个情景／资源／海克斯摘要保存在 [results.json](results.json)。','',
'| 弈子 | 费用 | 星级 | 羁绊 | 展示三件套 | 存活秒 | 同一羁绊下通过30秒的三件套数 |','| --- | --- | --- | --- | --- | --- | --- |']
for star in (1,2,3):
 for hero in heroes:
  r=best(hero,star);lines.append(f"| {hero} | {r['cost']} | {star} | {trait(r)} | {itemnames(r)} | {sec(r['result'])} | {r['survivors']:,} |")
lines+=['','## 心之钢与金霖龙保留为独立条件','',
'心之钢历史永久层数从 0 起，当前场中普通坚定之心每活 10 秒加 16 血；不把未证实的强化收益给光明坚定之心。金霖龙必须携带大亨之铠，多占一个人口，额外 600 血、15% 减伤，受击逐次叠大亨而不是开局满层。','',
'二星、限定一件神器搭配两件普通装备（含金霖龙时神器固定为大亨）的示例：','',
'| 弈子 | 海克斯条件 | 羁绊 | 三件套 | 存活秒 |','| --- | --- | --- | --- | --- |']
for hero in ['伊莉丝','蔚','阿木木','茂凯','拉莫斯']:
 for aug in (2,3):
  r=best(hero,2,2,aug)
  lines.append(f"| {hero} | {AUG[aug]} | {trait(r)} | {itemnames(r)} | {sec(r['result'])} |")
lines+=['','## 新增机制与检查','',
'- 吸血来源拆成自身普攻／技能伤害与装备直接伤害。基准中反甲、离子等装备直接伤害不触发通用全能吸血，不享受一般伤害增幅；智慧末刃自己的明确治疗条款另算。这依据 [Riot 对装备伤害的说明](https://teamfighttactics.leagueoflegends.com/en-gb/news/game-updates/teamfight-tactics-patch-12-17-notes/)，当前具体标签仍需客户端逐项校准。',
'- 夜刃的短暂不可选取与中娅3秒免疫记为“避开的原始伤害”；窗口结束恢复集火，不能因永久无人选取而虚构无限坦。中娅期间禁止普攻、施法。',
'- 死亡之蔑将掉血的一半延迟4秒，延迟扣血也能触发半血装备；禁忌雕像将新护盾的相应部分转成生命，避免同时算成护盾和血量。',
'- 普通／光明版本、生命与法力药水、攻速／法强成长、按攻击回蓝、蓝上限缩减、双圣盾和被动回复均按帧或事件结算。',
'- 所有模拟内部检查回蓝和护盾收支；另用独立 Python 枚举核对 249 个情景的组合数、107 件候选的覆盖。9个旧代表样本的时间、施法和回血保持一致；另测107件逐项样例、中娅动作禁用，以及无普攻技能伤害时反甲不能吸血等独立算例。','',
'## 哪些结论仍依赖假设','',
'输出目标基准双抗50、用于百分比伤害的上限3000，不会阵亡；因此有击杀条件的额外收益不触发，固定输入DPS也不因击杀降低。主榜不计己方控制减压；另有控制开启情景。普通施法锁蓝1秒、攻击停顿0.3秒，夜刃避伤窗0.5秒；这些没有客户端逐帧校准。','',
'暴击、纳什回蓝、链枷层数使用期望值，不是随机实战。目标选择、AOE命中数、普通与光明同名效果叠加、特殊怒气与回蓝装备交互等按 [机制契约](mechanics.md) 处理。','',
'恶火小斧（最大生命伤害4%／3%）、黎明圣盾（护甲治疗15%／20%）、收集者（AD35%／40%）在两个来源中存在冲突。基准保留原DataJ值，前两项做候选复算；黎明圣盾完整阶段曲线仍未知。不要把其中一套数值说成已获官方认证。','',
'对24个角色×3星级×普通／一光明／一神器的 **216个选中配置**，另外改变目标双抗、锁蓝、攻击停顿、装备伤害吸血、AOE吸血等条件复算。**这只是同配置敏感性，不是每个新情景再次穷举后得到的最优结果。**', '',
'| 普通装代表 | 星级 | 基准秒 | 同配置单项扰动的最短秒 |','| --- | --- | --- | --- |']
for hero in ['伊莉丝','蔚','阿木木','茂凯','拉莫斯']:
 for star in (2,3):
  q=next(x for x in SS if x['hero']==hero and x['star']==star and x['category']==0)
  low=min(x['frame'] for x in q['variants'].values());lowtext='≥30' if low==900 and all(x['alive'] for x in q['variants'].values()) else f'{low/30:.2f}'
  lines.append(f"| {hero} | {star} | {sec(q['baseline'])} | {lowtext} |")
lines+=['','## 文件与复现','',
'- [候选装备与排除清单](coverage.md)、[所有机制、假设与边界](mechanics.md)。',
'- [全部情景摘要](results.json)、[组合数与输入哈希](manifest.json)、[代表样本检查](checks.json)、[独立机制算例日志](engine_checks.log)。',
'- [216个配置敏感性结果](selected-sensitivity.json)、[新增机制专项敏感性](sensitivity.json)、[中娅逐帧事件](trace-zhonya.csv)。',
'- [C++引擎](engine.cpp)、[候选生成器](catalog.py)、[独立覆盖校验器](validate_results.py)。',
'- [原始DataJ快照](../../sources/dataj-gamedata.json)、[交叉核对的DataTFT快照](../../sources/datatft-s18.json)。两者均为第三方资料，不能用作官方API或完整客户端机制证明。','',
'复现：在本目录依次运行 `python3 catalog.py`、`clang++ -O3 -std=c++17 -pthread engine.cpp -o engine`、`./engine run 0 249 4 > progress.log`、`python3 validate_results.py`。运行前保留已有输出；check.py、engine_checks.cpp与sensitivity.py提供独立检查入口。','',
'**本轮完成的是装备池补全、统一30帧重算与模型内部验证。旧13件池报告保留作对照；当前结果以本报告和同目录运行清单为准。**']
md='\n'.join(lines)
survivors=[json.loads(l) for l in (P/'elise3-normal-survivors.jsonl').read_text().splitlines()]
assert len(survivors)==15
extra=['## 三星蜘蛛通过30秒的15套普通装','','固定6重装，其他条件同上。以下并列通过本观察窗，不按列表先后排序。','','| 序号 | 三件套 |','| --- | --- |']
for n,row in enumerate(survivors,1):extra.append(f"| {n} | {itemnames(row)} |")
extra+=['','独立导出的每套伤害、治疗与回蓝账本见 [15套结果](elise3-normal-survivors.jsonl)。','']
md=md.replace('## 所有角色的普通成装结果','\n'.join(extra)+'\n## 所有角色的普通成装结果')
(P/'report.md').write_text(md)
# Coverage is a checklist, not a claim that the original proprietary client was inspected.
co=['# 装备覆盖清单','','全部候选均参与每个可行角色／星级／原生防御羁绊的三件套枚举。源描述和原始数值见 catalog.json；“纳入”表示执行覆盖，不等于所有机制经过游戏客户端校准。','','| 编号 | 名称 | 类别 | 唯一限制 | 包含该物品的无序三件套数 |','| --- | --- | --- | --- | --- |']
for i in I:co.append(f"| {i['index']} | {i['name']} | {['普通','光明','神器','药水'][i['category']]} | {'最多1件' if i['unique'] else '目录未标唯一'} | {M['item_coverage'][str(i['index'])]:,} |")
co+=['','## 单独处理或排除','','| 物品 | 处理原因 |','| --- | --- |']
for e in C['exclusions']:co.append(f"| {e['name']} | {e['reason']} |")
co+=['','旧辅助装备：当前两个目录未列为S18候选，不混入历史数值。随机手套的双装仅是候选包络；实际配装表、概率未验证。']
(P/'coverage.md').write_text('\n'.join(co))
# Self-contained HTML edition for reading; no remote scripts, images, or services.
def inline(t):
 t=html.escape(t);t=re.sub(r'\*\*(.+?)\*\*',r'<strong>\1</strong>',t);t=re.sub(r'`(.+?)`',r'<code>\1</code>',t)
 return re.sub(r'\[([^\]]+)\]\(([^)]+)\)',r'<a href="\2">\1</a>',t)
parts=[];table=False
for line in md.splitlines():
 if line.startswith('|'):
  cells=[x.strip() for x in line.strip('|').split('|')]
  if all(re.fullmatch(r'[- :]+',x) for x in cells):continue
  if not table:parts.append('<div class="scroll"><table>');table=True
  parts.append('<tr>'+''.join('<td>'+inline(c)+'</td>' for c in cells)+'</tr>');continue
 if table:parts.append('</table></div>');table=False
 if not line:continue
 if line.startswith('# '):parts.append('<h1>'+inline(line[2:])+'</h1>')
 elif line.startswith('## '):parts.append('<h2>'+inline(line[3:])+'</h2>')
 else:parts.append('<p>'+inline(line)+'</p>')
if table:parts.append('</table></div>')
(P/'report.html').write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>全装备池单顶推演</title><style>body{font:16px/1.75 system-ui;max-width:1180px;margin:40px auto;padding:0 20px;color:#263548;background:#f8fafc}h1,h2{color:#163c60}h2{margin-top:38px}table{border-collapse:collapse;width:100%;font-size:14px;background:white}td{padding:9px;border:1px solid #dbe4ed}tr:first-child{background:#e7edf5;font-weight:bold}.scroll{overflow:auto;margin:16px 0}a{color:#1764af}code{background:#e5ebf2;padding:2px 4px}</style><body>'+''.join(parts)+'</body></html>')
print('Wrote report.md, report.html, coverage.md')
