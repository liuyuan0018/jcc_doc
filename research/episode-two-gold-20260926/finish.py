from pathlib import Path
import json,importlib.util
R=Path('/Users/lyu/Documents/ChatGPT/金铲铲');old=R/'exports/frontline-episode-02-v1';p=R/'exports/frontline-episode-02-v2'
m=json.loads((p/'manifest.json').read_text());events=[json.loads(l)for l in (p/'gold-execution.jsonl').read_text().splitlines()]
spec=importlib.util.spec_from_file_location('ep2gold',p/'archive.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
x=json.loads((p/'ranking.json').read_text());before={r['hero']:r for r in json.loads((old/'ranking.json').read_text())['leaderboard']}
checks=[]
for r in x['leaderboard']:
 if r['augment']==2:
  for d in [r['passedDps'],r['failedDps']]:
   out=a.replay(r['id'],d);checks.append(dict(id=r['id'],dps=d,alive=out['result']['alive']))
(p/'gold-boundaries.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2))
lines=['# 第二期：补入金霖龙后的完整榜单','','|名次|英雄|通过档|配装|海克斯|人口|补算前成绩|','|---|---|---:|---|---|---:|---:|']
for r in x['leaderboard']:lines.append(f"|{r['rank']}|{r['hero']}|{r['passedDps']}|{'＋'.join(r['itemNames'])}|{r['augmentName']}|{r['slots']}|{before[r['hero']]['passedDps']}|")
(p/'ranking.md').write_text('\n'.join(lines)+'\n');m['status']='ranked';(p/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2))
(R/'state/frontline-episode-02-current.json').write_text(json.dumps(dict(id=p.name,status='ranked',production=str(p),configurations=x['totalConfigurations'],heroCount=24,excludedArtifact='探索者的护臂',augments=['无指定海克斯','单身板甲','金霖龙'],videoStarted=False),ensure_ascii=False,indent=2))
print(json.dumps(dict(supplement=events[-1],total=x['totalConfigurations'],changed=[dict(hero=r['hero'],score=r['passedDps'],previous=before[r['hero']]['passedDps'],rank=r['rank'])for r in x['leaderboard']if r['passedDps']!=before[r['hero']]['passedDps']]),ensure_ascii=False),flush=True)
