from pathlib import Path
import json,importlib.util,time,collections,subprocess
ROOT=Path('/Users/lyu/Documents/ChatGPT/金铲铲');O=ROOT/'exports/frontline-episode-02-v1'
while json.loads((O/'manifest.json').read_text())['status']!='computed':time.sleep(2)
spec=importlib.util.spec_from_file_location('ep2',O/'archive.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
a.summarize()
x=json.loads((O/'ranking.json').read_text());old=json.loads((ROOT/'exports/frontline-episode-01-rerun-v5/ranking-no-heart.json').read_text());prior={r['hero']:r for r in old['leaderboard']}
lines=['# 第二期：2普通＋1神器','',f"共{x['totalConfigurations']:,}套，24位英雄；剔除探索者的护臂、心之钢海克斯。",'','|排名|英雄|通过档|普通装备＋神器|羁绊 / 人口|海克斯|第一期通过档|','|---|---|---:|---|---|---|---:|']
for r in x['leaderboard']:
 lines.append(f"|{r['rank']}|{r['hero']}|{r['passedDps']}|{'＋'.join(r['itemNames'])}|{' / '.join(str(v)+k for k,v in r['traits'].items())} · {r['slots']}人口|{r['augmentName']}|{prior[r['hero']]['passedDps']}|")
lines+=['','跨期可能同时改变装备、羁绊、人口及海克斯，差值不单独归因于神器。','神器模型沿用冻结实现：不模拟击杀收益；碎舰者按满足独处条件；光盾护盾按自身获得；永恒契约伙伴存活、每4秒施法。此处为模拟条件，并非实战保证。']
(O/'ranking.md').write_text('\n'.join(lines)+'\n')
# Check exact equipment scope for every retained row without re-running combat.
count=0;bycase=collections.Counter()
for r in a.read_rows():
 cats=[a.ITEMS[i]['category']for i in r['items']];assert sorted(cats)==[0,0,2]
 assert all(a.ITEMS[i]['id']!=30021 for i in r['items'])and r['augment']in [0,4]
 assert not r['ceilingReached']
 bycase[r['scenario']]+=1;count+=1
assert count==1655850 and len(bycase)==83 and set(bycase.values())=={19950}
# Reproduce each hero's selected pass and first fail with the frozen producer.
checks=[]
for r in x['leaderboard']:
 for d in [r['passedDps'],r['failedDps']]:
  if d<300:continue
  out=a.replay(r['id'],d);checks.append(dict(id=r['id'],dps=d,alive=out['result']['alive']))
(O/'scope-and-boundaries.json').write_text(json.dumps(dict(configurations=count,scenarios=len(bycase),equipmentScopePassed=True,boundaries=checks),ensure_ascii=False,indent=2))
m=json.loads((O/'manifest.json').read_text());m['status']='ranked';(O/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2))
(ROOT/'state/frontline-episode-02-current.json').write_text(json.dumps(dict(id=O.name,status='ranked',production=str(O),configurations=count,heroCount=24,excludedArtifact='探索者的护臂',videoStarted=False),ensure_ascii=False,indent=2))
print('SECOND EPISODE DATA READY',flush=True)
