from sim import *
from collections import defaultdict
import html,re,gzip
D=json.loads((P/'robust_best.json').read_text())
B=json.loads((P/'best_per_hero_trait.json').read_text())
S=json.loads((P/'sensitivity.json').read_text())
M=json.loads((P/'manifest.json').read_text())
fullnames={'狂徒':'狂徒铠甲','板甲':'石像鬼石板甲','反甲':'棘刺背心','龙牙':'巨龙之爪','振奋':'振奋盔甲','坚定之心':'坚定之心','日炎':'日炎斗篷','圣盾誓约':'圣盾使的誓约','适应头盔':'适应性头盔','冕卫':'冕卫','薄暮':'薄暮法袍','离子':'离子火花','血手':'斯特拉克的挑战护手','金霖大亨':'大亨之铠（金霖龙）'}
lanenames={'普通':'普通装备自由组合','心之钢':'必带坚定之心＋心之钢','金霖龙':'必带大亨＋金霖龙','双海克斯':'必带坚定之心＋大亨，双海克斯'}
def timefmt(t):return '≥30' if t>=30 else f'{t:.2f}'
def gear(r):return '＋'.join(f'{n}×{c}' if c>1 else n for n,c in Counter(r['items']).items())
def traits(r):return '＋'.join(str(v)+k for k,v in r['traits'].items())
def best_by_hero(rows):
 out={}
 for r in rows:
  k=r['hero']
  # Fewer slots preferred only when survival ties; no claim of superior tankiness for remaining health.
  if k not in out or (r['worst_time'],-r['minimum_slots'])>(out[k]['worst_time'],-out[k]['minimum_slots']):out[k]=r
 return sorted(out.values(),key=lambda r:(-r['worst_time'],r['minimum_slots'],r['cost'],r['hero']))
def table(head,rows):return '\n'.join(['| '+' | '.join(head)+' |','| '+' | '.join(['---']*len(head))+' |']+['| '+' | '.join(map(str,r))+' |' for r in rows])
parts=[]
def add(s):parts.append(s.strip())
add('''# 单顶前排测试：谁在什么羁绊、什么三件套下最硬

2026-09-18 · 固定 1400 混合 DPS · 一至三星分别计算

**这一轮的稳定候选是一、二星的 6 主宰阿木木；蔚对回蓝条件更敏感，有更高的模型上限。**金霖龙加入后，二星 6 主宰阿木木和蔚都存在能通过 30 秒的组合，不能在本观察窗口内强行排出唯一第一。

这里的“稳定”仅指：**同一套装备，在每秒 10／20／30 三种基础回蓝预算下取最短存活时间**。它不是实战胜率、所有机制下的保证，也不是已验证游戏回蓝公式。下面同时展示三次结果，方便看清这个限制。

## 1. 固定条件

- 一个弈子单顶，3 个敌人一直以它为目标；板甲持续获得 3 目标收益。
- 总原始伤害 1400／秒，物理普攻与魔法各半；三名敌人每秒各命中一次、错开时刻，共 3 包／秒，每包约 466.67，包内物魔各半。
- 没有真伤、重伤、破抗、敌方控制；不因为我方击杀或控制而降低这条固定伤害输入。弈子自己的治疗、护盾、减伤、临时双抗、攻速回血与生命成长参与计算。
- 一／二／三星独立；只开其本身所属的护卫、主宰、重装、斗士的 2／4／6 档，不用转职，不计其他种族、野怪印记、外部治疗。洛可以同时开主宰与重装。
- 观察 30 秒，到期活着写“≥30”，不写成刚好 30 秒或无限坦。原弈子倒下即结束，不把约里克／石甲虫的死亡召唤物算作本体继续存活。
- 设 9 人口的羁绊组队上限，金霖龙额外占一格；只是可行性上限，不代表这些组合已经优化了完整阵容。比较羁绊档位时不把额外人口成本称为免费。

**额外的模型约束必须说明：施法回蓝目前仍未完成客户端校准。**本次用真实初始法力和法力上限，设每秒 20 点基础回蓝预算，并完整重跑 10、30 两档；装备回蓝另加，普通施法锁蓝 1 秒，引导技能按持续时间锁蓝。此预算已整体替代角色、普攻与受击回蓝，不能再重复加一遍。纳尔单独按逐星怒气描述计算。

因此，这是一项公开假设的沙袋测试。尤其是蔚这种低蓝耗、技能加攻速且普攻回血的弈子，**不能拿本表直接宣称真实对局中一定比阿木木硬**。

## 2. 装备池与海克斯

13 件普通候选：石像鬼石板甲、狂徒铠甲、坚定之心、振奋盔甲、巨龙之爪、棘刺背心、圣盾使的誓约、适应性头盔、冕卫、薄暮法袍、离子火花、日炎斗篷、斯特拉克的挑战护手。

允许重复普通装备：13 选 3（允许重复）共 455 种。大亨之铠每人最多一件，搭配两件普通装备另有 91 种。这里不是游戏里所有可能的保命装备：夜之锋刃的不可选取、汲取剑／正义的输出吸血、其他神器、光明装等不在本轮池中；它们需要额外规定输出目标和交互规则。

四组分开计算：

1. 普通装备自由三件组合，无这两个海克斯。
2. 必带坚定之心，并拥有“心之钢”；历史永久额外血量从 0 起，每存活 10 秒，每件坚定之心新增 16 永久最大生命。模型假定当场立即增加生命上限及当前生命。
3. 必带大亨之铠，并拥有“金霖龙”：大亨自带 300 血，强化额外 600 血、15% 减伤，携带者占 2 人口。每个伤害包结算后，若仍存活，增加 1 双抗、5 血，最多 35 层；本输入在约 11.67 秒满层。没有开局白送满层。
4. 两个海克斯都有，必带坚定之心和大亨之铠，第三件自由选择。

**必带坚定之心组比自由组合组时间短，不代表海克斯有害**，可能只是装备格约束不同。海克斯本身的变化必须在完全相同的三件套下比较；对应的配对结果也已保存。例如二星阿木木、6 主宰、狂徒＋龙牙＋坚定之心，在基准预算下，无海克斯和零历史层数的心之钢版本都是约 21.33 秒；新增生命没有让它再多接住一包伤害，不等于长期叠血没有价值。

## 3. 最先看这张结果表

取相同装备在三档回蓝预算里的最短时间，称为“本次保守结果”。一、二星包含所有费用；三星常规区只列一至三费，四五费三星放在后面，避免它们把普通对比全部挤成满 30 秒。
''')
rows=[]
for star in [1,2,3]:
 for lane in ['普通','心之钢','金霖龙','双海克斯']:
  a=best_by_hero([r for r in D if r['star']==star and r['lane']==lane and (star!=3 or r['cost']<=3)])
  t=a[0]['worst_time'];tops=[r for r in a if r['worst_time']==t]
  names='、'.join(r['hero'] for r in tops)
  rows.append([('3星一至三费' if star==3 else str(star)+'星'),lanenames[lane],names,timefmt(t)])
add(table(['比较区','条件','领先或并列通过的弈子','最短存活秒'],rows))
add('''“并列通过”表示该输入没有把他们区分开。展示某套装备只是提供一个可复现的例子，不是唯一最优三件套。

## 4. 二星弈子的具体答案

下面每一行都固定同一弈子、同一羁绊、同一套装备，只改变基础回蓝预算。每组展示领先的 6 个不同弈子。
''')
for lane in ['普通','心之钢','金霖龙','双海克斯']:
 add('### '+lanenames[lane])
 rows=[]
 for r in best_by_hero([r for r in D if r['star']==2 and r['lane']==lane])[:6]:rows.append([r['hero'],traits(r),gear(r)]+[timefmt(t) for t in r['times']])
 add(table(['二星弈子','羁绊','三件套','10蓝/秒','20蓝/秒','30蓝/秒'],rows))
add('''### 为什么二星阿木木的结果更稳定

普通装的 6 主宰、狂徒＋板甲＋龙牙例子，可以手算核对：

- 二星基础 2340 血；装备固定生命为 500＋100，百分比生命为 18%＋6%。按本模型合成规则，最大生命 = (2340＋600)×1.24 = **3645.6**。
- 护甲 = 60＋25＋3×10 = **115**；魔抗再加龙牙 60，为 **175**。
- 每秒实际伤害 = 1400×[0.5×100÷215＋0.5×100÷275]×0.55 ≈ **319.07**。
- 阿木木每秒回 2.5% 最大生命＋25，即 **116.14**；龙牙每 2 秒回 **91.14**，平均每秒 **45.57**。
- 把离散回血临时当连续回复，粗算 3645.6÷(319.07−116.14−45.57)≈**23.17 秒**。逐包与整秒回血模拟约 **22.67 秒**；差别来自伤害与回血的实际到达时刻，而非公式自相矛盾。

阿木木的直接续航来自每秒被动；本试验又固定敌人持续输出，不把主动眩晕转成减压，所以三档回蓝不改变这组存活时间。蔚需要主动提供攻速、减伤并配合普攻回血，回蓝预算会显著改变表现。

## 5. 羁绊从 2→4→6，增加了多少

这里只比较二星同一弈子；每个档位重新从普通装备池选择本次保守结果最好的一套。因为装备也可能变化，本表不能当作“只加羁绊”的净增益实验。
''')
rows=[]
for name in ['阿木木','蔚','茂凯','苍蓝雕纹魔像','塔里克','拉莫斯','瑟提']:
 a=[r for r in D if r['hero']==name and r['star']==2 and r['lane']=='普通']
 row=[name]
 for t in [2,4,6]:
  r=next(r for r in a if list(r['traits'].values())==[t]);row.append(timefmt(r['worst_time'])+'秒；'+gear(r))
 rows.append(row)
add(table(['二星弈子','2档','4档','6档'],rows))
add('''完整筛选表保留洛的双职业组合。洛同时吃两个防御羁绊，不等于所有弈子可以无条件同时吃六主宰和六重装；本轮没有把不存在的职业或免费转职加给其他弈子。

## 6. 三星应怎样看

一至三费三星，普通装备组中达到三档回蓝预算均通过 30 秒的具体组合：
''')
rows=[]
for r in D:
 if r['star']==3 and r['cost']<=3 and r['lane']=='普通' and r['all_alive']:
  rows.append([r['hero'],r['cost'],traits(r),gear(r),'≥30／≥30／≥30'])
add(table(['弈子','费用','羁绊','见证三件套','10／20／30预算'],rows))
add('''四、五费三星另列：这一输入下多名单位在低档羁绊就能通过，不能声称其中剩血最多的就是最硬。
''')
rows=[]
for r in best_by_hero([r for r in D if r['star']==3 and r['cost']>=4 and r['lane']=='普通']):rows.append([r['hero'],traits(r),gear(r)]+[timefmt(t) for t in r['times']])
add(table(['三星高费','较低人口的通过配置','三件套','10蓝/秒','20蓝/秒','30蓝/秒'],rows))
add('''逐星特殊数据也参与了实现：三星阿木木回血比例为 4%；三星茂凯主动包含 100% 已损失生命回复；三星塔里克被动盾为 100% 最大生命＋10000、持续 99 秒；三星纳尔每秒 50 怒气、每次攻击 20 怒气，变形加 15000 血。没有把低星机制原样复制给三星。

## 7. 哪些结论能用，哪些还需要谨慎

- **普通装备、希望结果少依赖施法速度：一、二星先看 6 主宰阿木木。**这只是在本轮 24 个弈子与装备池、固定输入、三档回蓝预算中得到的保守比较，不是完整版本排名。
- **愿意押注频繁施法：蔚是强候选。**不要直接照搬某一档预算里出现的三振奋、三头盔；它们对回蓝、重复装备效果的叠加解释，以及施法动作会更敏感。
- **有金霖龙：二星 6 主宰阿木木、蔚可以进入同一“30 秒通过组”。**大亨增强还多花一个人口和一个海克斯，不能与普通装备称作同成本。
- **心之钢从零历史层数开始，单场提升通常较小。**一件在完整 30 秒也只新增 48 基础额外生命，受到本模型生命加成后再变大；它的长期叠血价值需要另设“开战前已有多少永久生命”。本轮没有把多回合收益凭空加进来。
- **1400 DPS 的观察上限有限。**三星高费大面积通过时，正确结论是输入不足以区分；若继续找其中第一，下一轮应提高压力或增加真实爆发，而不是用剩余血量硬排。

## 8. 验证和已知边界
''')
add(f'''三档回蓝预算各执行 **{M['runs']:,}** 组，共 **{M['runs']*3:,}** 组条件测试；不是这么多局实战。基准步长 **1/60 秒**，伤害间隔 **1/3 秒**；代表配置再以 1/120 秒复核。已检查解析式与伤害包取整误差、护盾数量守恒、大亨 35 层上限、心之钢单场增长、致命伤害不能靠结算后叠层复活。

生命合成基准为 (基础血＋固定血)×(1＋百分比血总和)；不同来源减伤乘算。重复装备的固有属性和触发效果按各副本计算，头盔回蓝倍率按 1＋15%×件数。冕卫第 8 秒提供后续法强；薄暮双抗在第 15 秒失效；血手盾线性衰减；同名技能增益刷新，不无限叠加。上述规则中未取得客户端实测的部分，均仍是模型假设。

基础回蓝、法力锁定、装备叠加、生命合成次序、同一帧触发顺序都可能改变精细排名。已另外保存固定装备下的生命合成／减伤合成／受击频率敏感性结果。尤其是把受击频率从 3 次改成 6 次，即使总 DPS 不变，也会使大亨更早满层。

为了保持固定输入，主动控制、反伤杀敌、日炎重伤敌人、离子破抗等间接减压未计；夜刃、输出吸血等也未补上假定敌人面板。不能用这些沙袋结果判定功能装备在实战里弱。
''')
rows=[]
for id_ in ['23501','24503','33501','33515']:
 for lane in ['普通','金霖龙']:
  r=[x for x in S if x['id']==id_ and x['lane']==lane]
  if not r:continue
  vals={x['variant']:x for x in r}
  rows.append([r[0]['hero']+' '+str(r[0]['star'])+'星',lane,gear(r[0])]+[timefmt(vals[k]['time']) for k in ['基准','步长1/120','百分比不放大固定血','每秒1伤害包','每秒6伤害包']])
add(table(['弈子','组别','固定装备','基准','1/120秒','另一血量规则','1包/秒','6包/秒'],rows))
add('''## 9. 数据与复算

数值来自本项目保留的 [9 月 18 日 DataJ 目录快照](../sources/dataj-gamedata.json)，公开入口为 [DataJ 数据目录](https://www.dataj.cc/api/web/gamedata?setId=18)。这是第三方数据，不是官方战斗日志。已有综合报告保留在上级目录，本次结果独立存放。

- [全部弈子、羁绊的保守最佳配置](robust_best.json)
- [基准 20 回蓝预算的最佳配置](best_per_hero_trait.json)
- [心之钢与普通坚定之心同装配对](heart_comparisons.json)
- [事件曲线](traces.json) · [敏感性结果](sensitivity.json) · [验证记录](checks.json)
- [模拟代码](sim.py) · [比较代码](analyze.py) · [运行清单](manifest.json)
- 全量逐组合结果另存 `all_results.jsonl.gz`、`mana-10/all_results.jsonl.gz`、`mana-30/all_results.jsonl.gz`。

```sh
cd /Users/lyu/Documents/ChatGPT/金铲铲/research/tankiness-20260918/single-frontline
python3 sim.py 20
python3 sim.py 10
python3 sim.py 30
python3 analyze.py
python3 report.py
```
''')
text='\n\n'.join(parts)+'\n';(P/'report.md').write_text(text)
def inline(s):
 s=html.escape(s);s=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',r'<a href="\2">\1</a>',s);s=re.sub(r'\*\*(.*?)\*\*',r'<strong>\1</strong>',s);return re.sub(r'`([^`]+)`',r'<code>\1</code>',s)
htmlparts=[];lines=text.splitlines();i=0
while i<len(lines):
 l=lines[i]
 if l.startswith('```'):
  code=[];i+=1
  while i<len(lines) and not lines[i].startswith('```'):code.append(lines[i]);i+=1
  htmlparts.append('<pre>'+html.escape('\n'.join(code))+'</pre>')
 elif l.startswith('|'):
  rows=[]
  while i<len(lines) and lines[i].startswith('|'):rows.append(lines[i]);i+=1
  htmlparts.append('<div class="scroll"><table>')
  for j,row in enumerate(rows):
   if j==1:continue
   tag='th' if j==0 else 'td';htmlparts.append('<tr>'+''.join(f'<{tag}>'+inline(c.strip())+f'</{tag}>' for c in row.strip('|').split('|'))+'</tr>')
  htmlparts.append('</table></div>');continue
 elif l.startswith('#'):
  n=len(l)-len(l.lstrip('#'));htmlparts.append(f'<h{n}>'+inline(l[n:].strip())+f'</h{n}>')
 elif l.strip():htmlparts.append('<p>'+inline(l)+'</p>')
 i+=1
style='''body{margin:0;background:#f0f4f7;color:#22313d;font:16px/1.8 system-ui,-apple-system,"PingFang SC",sans-serif}main{max-width:1200px;margin:28px auto;background:#fff;padding:38px 46px;border-radius:14px}h1{font-size:30px;line-height:1.5}h2{margin-top:42px;padding-top:20px;border-top:2px solid #e1e9f0;color:#1c526c}h3{margin-top:25px}strong{color:#14465f}table{border-collapse:collapse;width:100%;font-size:14px;line-height:1.65}th,td{padding:10px;border:1px solid #dbe4eb;text-align:left}th{background:#19465e;color:white}tr:nth-child(even){background:#f4f8fb}.scroll{overflow:auto;margin:18px 0}a{color:#00649b}code{font-size:13px;word-break:break-all}pre{background:#182f41;color:#dcebf5;padding:18px;overflow:auto}p{margin:12px 0}@media(max-width:700px){main{margin:0;padding:20px}h1{font-size:24px}}@media print{body{background:white}main{margin:0;padding:0}tr{break-inside:avoid}h2,h3{break-after:avoid}table{font-size:10px}}'''
(P/'report.html').write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>单顶前排测试 · 1400 DPS</title><style>'+style+'</style><main>'+''.join(htmlparts)+'</main></html>')
print('Report written',len(text),'characters')
