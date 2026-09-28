# -*- coding: utf-8 -*-
import json,re,math,html
from pathlib import Path
P=Path(__file__).resolve().parent; S=P.parent
load=lambda f:json.loads((S/f).read_text())
A=load('results.json');C=load('catalog.json');I=C['items'];M=load('manifest.json');SS=load('selected-sensitivity.json')
CAT=['普通三件套','1光明＋2普通','1神器＋2普通','1光明＋1神器＋1普通','至少2件光明／神器','含药水','普通手套理论包络','光明手套理论包络']
AUG=['无这两个海克斯','心之钢（0历史层）','金霖龙','心之钢＋金霖龙']
trait=lambda r:'＋'.join(str(v)+k for k,v in r['traits'].items())
names=lambda r:[I[i]['name'] if i>=0 else '手套自身属性' for i in r['items']]
score=lambda r:(r['result']['frame'],r['result']['hp']+r['result']['shield'])
sheets=[];styles=[]
def col(n):
 s=''
 while n:n,r=divmod(n-1,26);s=chr(65+r)+s
 return s
def add(name,columns,data,ints=(),floats=()):
 assert all(len(r)==len(columns) for r in data)
 dtypes={c:('int64' if c in ints else 'float64' if c in floats else 'object') for c in columns}
 formats={c:('#,##0' if c in ints else '#,##0.00') for c in (*ints,*floats)}
 name='180秒_'+name
 for j,c in enumerate(columns):
  if c in floats and max((abs(r[j]) for r in data),default=0)>1e9:formats[c]='0.00E+00'
 sheets.append(dict(name=name,columns=columns,data=data,dtypes=dtypes,formats=formats))
 end=col(len(columns));n=len(data)+1
 widths=[]
 for j,c in enumerate(columns):
  vals=[c]+[str(r[j]) for r in data]
  width=max(sum(15 if ord(k)>127 else 8 for k in v) for v in vals)+24
  widths.append(min(560 if len(columns)==2 else 360,max(90,width)))
 heights=[]
 for k,row in enumerate([columns]+data,1):
  lines=max(math.ceil(sum(15 if ord(c)>127 else 8 for c in str(v))/(widths[j]-20)) for j,v in enumerate(row))
  h=max(34,min(260,lines*21+12))
  if heights and heights[-1][2]==h:heights[-1][1]=k
  else:heights.append([k,k,h])
 styles.append(dict(name=name,cell_styles=[dict(range=f'A1:{end}{n}',font_size=11,vertical_alignment='middle',word_wrap='auto-wrap'),dict(range=f'A1:{end}1',font_weight='bold',background_color='#203C56',font_color='#FFFFFF')],col_sizes=[dict(range=col(j+1),size=w) for j,w in enumerate(widths)],row_sizes=[dict(range=f'{a}:{b}',size=h) for a,b,h in heights],freeze=dict(rows=1,cols=1)))
guide=[['观察窗变更','延长为180秒，30Hz不变。固定伤害压力，不加入实战加时/狂暴；180秒仍存活不代表无限续航。'],['版本','S18目录补全 · 2026-09-18 · 30帧单顶模拟'],
['先看哪里','本次为180秒观察；常用资源结果：24弈子×1至3星×普通/一光明/一神器；可筛选弈子、星级、资源。'],
['完整数据','全量摘要保留5679条情景/资源/海克斯摘要，不是每个三件套的逐场日志。'],
['数值解释','观察秒数是截至死亡或180秒的时间；“180秒仍存活”表示至少180秒，达到上限者并列，不视作180秒后最优。'],
['搭配选择','常用结果每行选一个原生防御羁绊情景；期末血盾仅用于挑展示样例，不能当实战唯一最优。'],
['承伤','3人集火、1400原始DPS、50%物理普攻＋50%魔法；无真伤、重伤、破抗和敌方控制。'],
['输出与吸血','输出目标双抗50、参考生命3000，不移动不死亡；普攻技能吸血按伤害结算，装备伤害基准不触发通用吸血。'],
['枚举范围',f"107件候选，{M['unordered_selectable_triples']}种合法无序三件套；最终基准{M['runs']}次推演。"],['星级','1/2/3星分别计算，费用不等于星级；三星四五费的获取难度需另行考虑。'],
['心之钢与金霖龙','心之钢从0历史层起、只作用普通坚定之心；金霖龙必带大亨、多占人口。'],
['手套结果','只是假设候选双装的理论包络；实际配装表和概率未验证，不能当可指定推荐。'],
['敏感性','216个已选配置各6项基础扰动，按装备追加来源冲突项；不是在扰动条件下重新全池优化。'],
['模型边界','装备覆盖不等于客户端校准；施法动画、伤害标签、部分神器阶段系数仍有假设。具体见机制契约。'],
['数据来源','DataJ https://www.dataj.cc/api/web/gamedata?setId=18 与 DataTFT https://jcc.datatft.com/assets/h5-data-cn-18-C8z_69Mb.json 的快照；均为第三方资料。DataJ内部S19/18.18.1b字段与公开S18/18.2a标签有冲突，不能视为官方补丁认证。'],
['装备伤害依据','https://teamfighttactics.leagueoflegends.com/en-gb/news/game-updates/teamfight-tactics-patch-12-17-notes/'],
['来源冲突','恶火小斧4%/3%，黎明圣盾15%/20%，收集者35%/40%；基准沿用DataJ，详见机制契约。'],
['本地来源',str(S)],['更新方式','新增180秒标签页，原30秒标签页保留。本表为该轮模拟的静态结果快照；修改单元格不会重跑战斗模拟。']]
add('阅读说明',['项目','说明'],guide)
cols=['弈子','费用','星级','资源条件','羁绊','海克斯条件','装备1','装备2','装备3','观察秒数','180秒状态','通过180秒组合数','测试组合数','期末生命','期末护盾','施法次数','实际治疗','实际输出','情景编号']
ints=['费用','星级','通过180秒组合数','测试组合数','施法次数','情景编号'];fl=['观察秒数','期末生命','期末护盾','实际治疗','实际输出']
def row(r):
 x=r['result']; ns=names(r); ns=(ns+['',''])[:3]
 return [r['hero'],r['cost'],r['star'],CAT[r['category']],trait(r),AUG[r['aug']],*ns,x['frame']/30,'180秒仍存活' if x['alive'] else '观察窗内阵亡',r['survivors'],r['runs'],x['hp'],x['shield'],x['casts'],x['heal'],x['damage'],r['scenario']]
best={}
for r in A:
 if r['aug']==0 and r['category']<3:
  k=(r['hero'],r['star'],r['category'])
  if k not in best or score(r)>score(best[k]):best[k]=r
selected=sorted(best.values(),key=lambda r:(r['category'],r['star'],r['cost'],r['hero']))
assert len(A)==5679 and len(selected)==216
add('常用资源结果',cols,[row(r) for r in selected],ints,fl)
sp=load('elise-old15-extended.json');assert len(sp)==15
add('蜘蛛原15套延长',['装备1','装备2','装备3','羁绊与星级','观察秒数','状态','期末生命','期末护盾','施法次数','实际治疗'],[[*names(r),'6重装 · 三星',r['result']['frame']/30,('180秒仍存活' if r['result']['alive'] else '观察窗内阵亡'),r['result']['hp'],r['result']['shield'],r['result']['casts'],r['result']['heal']] for r in sp],['施法次数'],
['观察秒数','期末生命','期末护盾','实际治疗'])
add('全量摘要',cols,[row(r) for r in A],ints,fl)
variants={'target30':'目标双抗30','target100':'目标双抗100','lock2':'施法锁蓝2秒','pause05':'攻击停顿0.5秒','itemvamp_on':'允许装备伤害吸血（上界）','aoe_third':'AOE吸血按三分之一'}
sens=[]
for r in SS:
 for k,v in r['variants'].items():sens.append([r['hero'],r['star'],CAT[r['category']],trait(r),'＋'.join(r['items']),variants.get(k,k),r['baseline']['frame']/30,'仍存活' if r['baseline']['alive'] else '阵亡',v['frame']/30,'仍存活' if v['alive'] else '阵亡'])
assert len(sens)>=1296
add('同配置敏感性',['弈子','星级','资源','羁绊','三件套','单项扰动','基准秒数','基准180秒状态','扰动秒数','扰动180秒状态'],sens,['星级'],
['基准秒数','扰动秒数'])
strip=lambda t:html.unescape(re.sub('<[^>]+>','',t))
add('装备覆盖',['编号','装备','类别','唯一限制','包含该装备的合法三件套数','目录效果描述'],[[i['index'],i['name'],
['普通','光明','神器','药水'][i['category']],'最多1件' if i['unique'] else '目录未标唯一',M['item_coverage'][str(i['index'])],strip(i['effect'])] for i in I],['编号','包含该装备的合法三件套数'])
add('排除与单独处理',['名称','原因'],[[e['name'],e['reason']] for e in C['exclusions']])
section='概述';mr=[]
for line in (S/'mechanics.md').read_text().splitlines():
 if line.startswith('#'):section=line.lstrip('# ')
 elif line.strip() and not re.fullmatch(r'[| :\-]+',line):mr.append([section,line])
add('机制契约',['主题','实现与限制'],mr)
comparison=load('comparison.json')
cr=[]
for r in comparison:
 o=r['old'];n=r['new'];v=r['old_extended']
 cr.append([r['hero'],r['star'],CAT[r['category']],trait(o),'＋'.join(names(o)),o['result']['frame']/30,'仍存活' if o['result']['alive'] else '阵亡',v['frame']/30,'仍存活' if v['alive'] else '阵亡',trait(n),'＋'.join(names(n)),n['result']['frame']/30,'仍存活' if n['result']['alive'] else '阵亡',n['survivors']])
add('新旧对照',['弈子','星级','资源','旧羁绊','旧展示装','旧观察秒','旧30秒状态','旧装延长秒','旧装180秒状态','新羁绊','新展示装','新观察秒','新180秒状态','新情景通过组合数'],cr,['星级','新情景通过组合数'],['旧观察秒','旧装延长秒','新观察秒'])
for fn,obj in [('sheets.json',{'sheets':sheets}),('styles.json',{'styles':styles})]:(P/fn).write_text(json.dumps(obj,ensure_ascii=False))
print([(s['name'],len(s['data']),len(s['columns'])) for s in sheets])
