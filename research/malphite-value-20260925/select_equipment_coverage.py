"""Explicit gear coverage for the approved 8 Main / 72 Results revision."""
import csv,json,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'exports/frontline-malphite-rerun-v1'
rows=[]
for z in csv.DictReader((BASE/'full-ranking.csv').open()):
 rows.append(dict(id=z['id'],rank=int(z['rank']),score=int(z['score']),tier=int(z['blackthorn']),cost=int(z['sacrificeCost']),star=int(z['sacrificeStar']),items=[int(z[k])for k in ['item1','item2','item3']],augment=int(z['augment']),passedDps=int(z['coarsePass']),failedDps=int(z['coarseFail'])))
lookup={(r['tier'],r['cost'],r['star'],tuple(r['items']),r['augment']):r for r in rows}
def get(t,c,s,items,aug=0):return lookup[t,c,s,tuple(sorted(items)),aug].copy()
main=[next(r.copy()for r in rows if r['tier']==t)for t in [2,4,6]]
main += [get(6,3,3,[24,27,33]),get(6,3,3,[27,30,33]),get(6,3,3,[26,30,33]),get(2,3,2,[27,30,33]),get(4,3,2,[26,27,33])]
for i,r in enumerate(main):r.update(key=f'M{i+1:02}',reason='本档羁绊最高分'if i<3 else'同条件常见装备对照'if i<6 else'两星献祭常见肉装')
selected={};reasons={}
def add(r,why):
 selected[r['id']]=r.copy();reasons.setdefault(r['id'],[]).append(why)
for r in rows[:8]:add(r,'总榜前8')
for r in main:add(r,'Main出镜')
common=[[24,27,33],[27,30,33],[26,30,33],[26,27,33],[24,26,30],[17,27,33],[22,27,30],[23,27,33]]
for t in [2,4,6]:
 for s in [2,3]:
  for items in common:add(get(t,3,s,items),'常见装备矩阵：3费2/3星献祭 × 2/4/6黑')
for t in [2,4,6]:
 for s in [2,3]:add(get(t,3,s,[24,27,33],4),'相同装备有无单身板甲对照')
for c,s in [(1,2),(1,3),(2,2),(2,3),(3,2),(3,3),(4,1),(4,2),(5,1),(5,2)]:
 add(next(r for r in rows if (r['tier'],r['cost'],r['star'])==(6,c,s)),'六黑十种献祭各自最高分')
if len(selected)<72:add(get(4,3,2,[27,29,33]),'坚定之心常见肉装补充')
assert len(selected)==72,len(selected)
result=sorted(selected.values(),key=lambda r:(-r['score'],r['id']))
assert {r['id']for r in main}<={r['id']for r in result}
assert {r['id']for r in result[:8]}=={r['id']for r in rows[:8]}
counts=lambda rs:{str(i):sum(i in r['items']for r in rs)for i in [24,26,27,30,33]}
plan=dict(status='selection_verified_recording_pending',source=str(BASE/'full-ranking.csv'),simulationCount=len(rows),mainCount=8,resultsCount=72,main=main,resultsIds=[r['id']for r in result],selectionReasons=reasons,coverage=dict(main=counts(main),results=counts(result)),narrative='前三套各羁绊最高分；六黑同条件常见肉装直接对照；Results按真实总榜名次排序，展示常见装备矩阵和适用海克斯。')
p=Path(__file__).with_name('main-eight-selection-v5.json');p.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
labels={24:'振奋',26:'反甲',27:'板甲',30:'龙牙',33:'狂徒'}
lines=['# v5出镜选择','', '|编号|黑荆棘|献祭|装备|海克斯|细分成绩|真实总榜名次|','|---|---|---|---|---|---|---|']
for r in main:lines.append(f'|{r["key"]}|{r["tier"]}|{r["cost"]}费{r["star"]}星|'+ '＋'.join(labels[i]for i in r['items'])+f'|{"单身板甲"if r["augment"]else"无"}|{r["score"]}|{r["rank"]}|')
lines+=['','Results：前8名＋常见装备跨羁绊及献祭矩阵＋海克斯对照＋六黑十种献祭最高分，共72套、不重复，全部按真实总榜名次排序。',json.dumps(plan['coverage'],ensure_ascii=False)]
p.with_suffix('.md').write_text('\n'.join(lines)+'\n');print('\n'.join(lines))
