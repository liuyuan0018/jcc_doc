import json,html,re
from pathlib import Path
from sim30 import *
R=P/'fps30';a=json.loads((R/'best.json').read_text());e=json.loads((R/'elise-expanded-best.json').read_text());panels=json.loads((R/'elise-panels.json').read_text())
def sec(r):return '≥30' if r['alive'] else f"{r['time']:.2f}"
def items(r):return '＋'.join(r['items'])
def traits(r):return '＋'.join(f'{v}{k}' for k,v in r['traits'].items())
def rank(r):return(r['time'],r['hp_left']+r['shield_left'])
text=['# 30 帧单顶推演：蜘蛛的硬度在哪里','2026-09-18 · 30 Hz · 1400 原始混合 DPS · 模型结果，不是客户端战斗记录','''**上一版不能用来下实战排名结论。**蜘蛛的变身加血、普攻回血、再次施法加攻速有写入旧代码，但统一的每秒回蓝预算没有体现受击与普攻循环；纯肉装候选池还漏掉了它的攻速／法强续航路线。新版本把这两处分别修正，不为了符合印象调整数值。

**本次明确体现了三星蜘蛛的续航：6 重装、板甲＋羊刀＋大天使，通过 30 秒；同装备关闭技能，仅存活 8 秒。**在同样的 1400 DPS 压力下，一、二星这套成长装分别只能支撑 3.33／6.67 秒，启动之前就倒下。2 费是费用，不是 2 星；不能把三星的续航直接外推给二星。

原 13 件防御装池已重新计算 161,226 组；蜘蛛扩展池另算 8,568 组。全角色榜仍使用同一个 13 件池，扩展池只用于蜘蛛专项，不能跨池宣称全游戏第一。
''','## 蜘蛛的同条件对照','下表均为 6 重装、无心之钢／金霖龙、3 人单顶。开局均满血，无历史永久叠血。','| 星级 | 狂徒＋板甲＋振奋 | 同装关闭技能 | 板甲＋羊刀＋大天使 | 同装关闭技能 |','| --- | --- | --- | --- | --- |']
for star in (1,2,3):
 r=next(x for x in panels if x['star']==star and x['items']==['狂徒','板甲','振奋']);q=next(x for x in panels if x['star']==star and x['items']==['板甲','羊刀','大天使'])
 text.append(f"| {star}星 | {sec(r['baseline'])} 秒 | {sec(r['variants']['no_skill'])} 秒 | {sec(q['baseline'])} 秒 | {sec(q['variants']['no_skill'])} 秒 |")
text+=['','**关闭技能对照同时移除变身加血、普攻治疗和技能攻速；保留装备、羁绊与同样伤害输入。**这测的是技能整体贡献，不是单独回血收益。','','## 纯肉装与成长装分别怎么选','| 星级 | 羁绊 | 原 13 件池中的一个最优三件套 | 存活 | 扩展池中的一个最优三件套 | 存活 |','| --- | --- | --- | --- | --- | --- |']
for star in (1,2,3):
 for tier in (2,4,6):
  r=next(x for x in a if x['hero']=='伊莉丝' and x['star']==star and x['lane']=='普通' and x['traits']=={'重装':tier});q=next(x for x in e if x['star']==star and x['lane']=='普通' and x['traits']=={'重装':tier})
  text.append(f"| {star}星 | {tier}重装 | {items(r)} | {sec(r)} | {items(q)} | {sec(q)} |")
text+=['','“最优”只指本条件、本候选池、30 秒观察窗。同样通过 30 秒的装备并列；记录中的剩余生命仅用于选一个展示样例，不用于证明谁能活得更久。','''
## 三星蜘蛛：逐帧账本

样例：6 重装，板甲＋羊刀＋大天使。基础 2916 血，板甲加 100 血，初始 3016；变身加 725，最终上限 3741。基础攻速 0.65，初始法力 20／70。初始法强倍率 1.4（羊刀 10、大天使 30）。

- 第 42 帧（1.40 秒）首次变身；第 123 帧（4.10 秒）第一次获得后续施法的 175% 衰减攻速。
- 到第 900 帧，施法 12 次，普攻 54 次，其中蜘蛛形态攻击 53 次；有效技能治疗 17,912.2，另有 209.8 溢出治疗。
- 共承接 42,000 原始伤害；护盾实际吸收 2702.8。30 秒时还剩 3507.7 血。没有计入自身击杀敌人后减压，也没有外部治疗。
- 初始 20 蓝＋受击实际获得 663.17 蓝＋普攻实际获得 184.27 蓝＋装备实际获得 18.27 蓝＝施法消耗 840 蓝＋剩余 45.70 蓝。锁蓝与满蓝溢出分别记录，没有再额外塞固定回蓝预算。

这套装备的作用：板甲降低掉血速度，重装护盾争取启动时间；羊刀增加攻击次数，大天使提高每次攻击回血，技能再次施放再加攻速。后段回血能赶上掉血，前段能否活下来决定这条路线是否成立。
''']
q=next(x for x in panels if x['star']==3 and x['items']==['板甲','羊刀','大天使']);tr=json.loads((R/q['trace_file']).read_text())
text+=['| 时间 | 帧 | 当前血量 | 护盾 | 法力 | 已施法 | 累计蜘蛛普攻 |','| --- | --- | --- | --- | --- | --- | --- |']
for row in tr['trace']:
 if row['frame'] in (0,42,123,150,300,450,600,750,900):text.append(f"| {row['t']:.2f} | {row['frame']} | {row['hp']:.1f} | {row['shield']:.1f} | {row['mana']:.1f} | {row['casts']} | {row['spider_attacks']} |")
text+=['',f"完整的 901 帧状态及事件：[三星蜘蛛逐帧 JSON](fps30/{q['trace_file']})。",'' ,'''## 30 帧到底怎么算

每帧 1/30 秒，整数帧推进。顺序：过期与衰减 → 普攻、持续治疗、装备／怒气回蓝 → 已满蓝施法 → 当帧受击 → 存活才处理受击回蓝和血线触发 → 再检查满蓝。致死受击不会靠同次受击产生的蓝复活。普通技能防御效果简化为施法起点生效；攻击停顿与锁蓝单独处理。

1. 坦克每次攻击 5 蓝；受击回蓝主情景为 `min(42.5, 原始伤害×1%＋减免后伤害×3%)`，护盾吸收前计算。适应头盔对各回蓝来源增加 15%，重复持有按加法。
2. 法力不超过当前上限；技能扣空本次蓝，锁蓝期间的普攻、受击和自然回蓝不保留。圣盾血线回蓝按特殊直接回蓝处理，且有满蓝上限。
3. 蜘蛛人形／蛛形源数据中的攻速、蓝量一致，不额外虚构变身双抗或更低蓝耗。首次施法只变身，后续才有 175% 攻速；4 秒内线性衰减，刷新而不叠加。攻速上限设为 5。
4. 普通施法锁蓝基准 1 秒、攻击停顿 0.3 秒；明确引导类按 2／3 秒暂停攻击和回蓝。效果即时、攻击相位、锁蓝和衰减曲线仍是模型假设，没有客户端逐帧校准。
5. 本次角色表确认蜘蛛、蔚等为坦克；黛安娜为战士，只靠普攻和装备回蓝，阶段攻速暂取 20%；纳尔按专属怒气，每次变身后上限由 70 改为 50。黛安娜的阶段攻速是独立限制，不外推为所有阶段。
6. 羊刀每秒 +7% 攻速，自带 10% 攻速、10 法强；大天使自带 30 法强、1 回蓝／秒，从第 5 秒起每 5 秒 +20 法强；泰坦每次攻击／受击 +2 法强，最多 25 层，自带 10% 攻速与 20 护甲。输出不影响这条固定伤害输入。

普通池：狂徒、板甲、反甲、龙牙、振奋、坚定之心、日炎、圣盾誓约、适应头盔、冕卫、薄暮、离子、血手；允许重复，455 个三件套。金霖龙组为两件普通装＋大亨，91 套。保留心之钢零历史层数、双海克斯两个独立组。金霖龙额外 600 血、15% 减伤并多占一格，伤害包后活着才叠大亨。

伤害输入仍是 1400／秒、物理普攻与魔法各半、三名敌人每秒各发一包混合伤害，错开共 3 包／秒。没有真伤、重伤、破抗、敌方控制或来自队友的治疗。板甲按 3 名敌人持续集火。不开其他种族羁绊，死亡召唤物不计作本体存活。羁绊最多 9 人口；活过 30 秒只写 ≥30。

## 敏感性与核验边界

同一套三星蜘蛛（板甲＋羊刀＋大天使）另测：锁蓝改为 2 秒或 4 秒、攻击停顿改为 0 或 0.5 秒、护盾吸收不计入受击回蓝的减免后部分、伤害频率改为每秒 1／6 包、减免后回蓝系数改为 5%，均能活到 30 秒。每次只改一个因素；这不是所有组合扰动的保证。每秒 1 包是集中伤害敏感性，不能理解为仍有三名敌人各打一包。

同样是三星，狂徒＋板甲＋振奋在基准下为 22.67 秒，锁蓝改 4 秒降为 20.67 秒。装备循环比单纯把计算频率提高更影响结论。

9 个代表样本（蜘蛛／蔚／阿木木各一至三星）在 30／60／120 Hz 下的存活时间、施法次数一致；独立检查覆盖攻击回蓝、护盾受击回蓝、锁蓝、致死事件、法力收支、护盾收支、蜘蛛逐次回血和角色差异。它们验证程序内部逻辑，不等于验证真实游戏机制。详见 [checks30.json](checks30.json)。

## 全角色：原 13 件防御装池的二星结果

下面是同池、基准锁蓝参数的条件结果，按角色列出普通组中最优羁绊与三件套。尤其蔚的技能覆盖率仍受真实锁蓝影响；不再把本表称为已经验证的实战排名。
''','| 弈子 | 费用 | 羁绊 | 三件套 | 存活秒 |','| --- | --- | --- | --- | --- |']
for name in dict.fromkeys(h['name'] for h in PROFILES):
 r=max((x for x in a if x['hero']==name and x['star']==2 and x['lane']=='普通'),key=rank)
 text.append(f"| {name} | {r['cost']} | {traits(r)} | {items(r)} | {sec(r)} |")
text+=['','## 一至三星与海克斯明细','每行是相应角色、星级、海克斯条件下的一个最优候选；三星四五费单独看，不与常规追三星成本等价。全量候选及回蓝账本在 fps30 内按角色 ID 压缩保存。','| 星级 | 弈子 | 费用 | 组别 | 羁绊 | 三件套 | 存活秒 |','| --- | --- | --- | --- | --- | --- | --- |']
for star in (1,2,3):
 for name in dict.fromkeys(h['name'] for h in PROFILES):
  for lane in ('普通','心之钢','金霖龙','双海克斯'):
   rr=[x for x in a if x['hero']==name and x['star']==star and x['lane']==lane]
   r=max(rr,key=rank)
   text.append(f"| {star} | {name} | {r['cost']} | {lane} | {traits(r)} | {items(r)} | {sec(r)} |")
text+=['','''## 数据与来源

- 弈子、技能、装备与羁绊主快照：[DataJ 本地原始文件](../sources/dataj-gamedata.json)，9 月 18 日抓取；来源标记存在版本／赛季字段混用，不能仅据其中 version 字段宣称官方版本认证。
- 本次补充 [DataTFT S18 数据](https://jcc.datatft.com/assets/h5-data-cn-18-C8z_69Mb.json)，保存为 [datatft-s18.json](../sources/datatft-s18.json)，交叉核对蜘蛛面板、技能、角色和重装档位。第三方整理，不当作官方战斗引擎。
- Riot [14.23 补丁](https://teamfighttactics.leagueoflegends.com/en-ph/news/game-updates/teamfight-tactics-patch-14-23-notes/)明确将减免后受击回蓝从 5% 改为 3%；[15.1 补丁](https://teamfighttactics.leagueoflegends.com/en-gb/news/game-updates/teamfight-tactics-patch-15-1-notes-2025/)明确坦克普攻 5 蓝、仅特定角色受击回蓝。它们支持机制沿革，不单独证明金铲铲当前客户端全部实现。
- [13.7 补丁](https://teamfighttactics.leagueoflegends.com/en-au/news/game-updates/teamfight-tactics-patch-13-7-notes-2025/)包含减免后受击回蓝不再溢出的修复。本次所有来源统一设满蓝上限，来源特例仍需客户端记录确认。
- [引擎 sim30.py](sim30.py)、[全量运行 run30.py](run30.py)、[蜘蛛专项 focus30.py](focus30.py)、[运行清单](fps30/manifest.json)、[敏感性账本](fps30/elise-panels.json)。

**交付边界：30 帧事件推演、全量重算、蜘蛛专项与内部核验已完成；尚未完成游戏客户端逐帧校准。旧固定回蓝报告保留为历史对照，已标记停用。**
''']
md=re.sub(r'(?<=\|)\n\n(?=\|)', '\n', '\n\n'.join(text));(P/'report30.md').write_text(md)
# Small portable renderer for this generated report. No remote dependencies.
def inline(t):
 t=html.escape(t);t=re.sub(r'\*\*(.+?)\*\*',r'<strong>\1</strong>',t);t=re.sub(r'`(.+?)`',r'<code>\1</code>',t)
 return re.sub(r'\[([^\]]+)\]\(([^)]+)\)',r'<a href="\2">\1</a>',t)
parts=[];intable=False
for line in md.splitlines():
 if line.startswith('|'):
  cells=[x.strip() for x in line.strip('|').split('|')]
  if all(re.fullmatch(r'[- :]+',x) for x in cells):continue
  if not intable:parts.append('<div class="scroll"><table>');intable=True
  parts.append('<tr>'+''.join('<td>'+inline(c)+'</td>' for c in cells)+'</tr>');continue
 if not line.strip():continue
 if intable:parts.append('</table></div>');intable=False
 if line.startswith('# '):parts.append('<h1>'+inline(line[2:])+'</h1>')
 elif line.startswith('## '):parts.append('<h2>'+inline(line[3:])+'</h2>')
 else:parts.append('<p>'+inline(line)+'</p>')
if intable:parts.append('</table></div>')
(P/'report30.html').write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>30帧蜘蛛续航推演</title><style>body{font:16px/1.75 system-ui;max-width:1100px;margin:40px auto;padding:0 20px;color:#253044;background:#f8fafc}h1,h2{color:#152a47}h2{margin-top:42px}p{max-width:950px}table{border-collapse:collapse;width:100%;background:white;font-size:14px}td{padding:9px;border:1px solid #dce4ed}tr:first-child{font-weight:700;background:#e9eff7}.scroll{overflow:auto;margin:20px 0}a{color:#125ab0}code{background:#e9edf3;padding:2px 4px}</style><body>'+''.join(parts)+'</body></html>')
print('Wrote',P/'report30.md')
