import json,sys,subprocess,hashlib,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).parent
sys.path.insert(0,str(ROOT/'exports/frontline-episode-01-rerun-v3'));import archive
source=ROOT/'research/fiddlesticks-video-20260925/ranking.json';d=json.loads(source.read_text());rows=d['all'];top=sorted([r for r in rows if 9 in r['items']],key=lambda r:(-r['score'],r['id']))[:8]
paths=[Path(p)for p in d['sourceHashes']if Path(p).name in ['web.cpp','engine-web.hpp','generated.hpp','replay-native']];hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest()for p in paths};assert all(h==d['sourceHashes'][p]for p,h in hashes.items())
lines=[]
for i,r in enumerate(top):
 for mode in ['original','without']:
  z=dict(r);z['items']=r['items'].copy()
  if mode=='without':z['items'][z['items'].index(9)]=-1
  lines.append(' '.join(map(str,[f'{i}-{mode}',*archive.parameters(z,300)])))
(OUT/'input.txt').write_text('\n'.join(lines)+'\n')
r=subprocess.check_output([str(OUT/'scan')],input=('\n'.join(lines)+'\n').encode());(OUT/'runs.jsonl').write_bytes(r);runs={x['id']:x for x in map(json.loads,r.decode().splitlines())};summary=[]
for i,row in enumerate(top):
 assert runs[f'{i}-original']['score']==row['score']
 pair=row['items'].copy();pair.remove(9)
 def has_pair(r):return not(collections.Counter(pair)-collections.Counter(r['items']))
 alternatives=[r for r in rows if r['augment']==row['augment']and 9 not in r['items']and has_pair(r)]
 best=max(alternatives,key=lambda x:x['score']);best=dict(items=best['items'],score=best['score'],rank=best['rank'])
 low=runs[f'{i}-without']['score'];summary.append(dict(items=row['items'],augment=row['augment'],rank=row['rank'],withRageblade=row['score'],withoutRageblade=low,gain=row['score']-low,gainPercent=round((row['score']/low-1)*100,2),bestReplacement=best))
assert hashes=={str(p):hashlib.sha256(p.read_bytes()).hexdigest()for p in paths}
result=dict(conditions=d['hero'],sourceHashes=hashes,sourceRankingSha256=hashlib.sha256(source.read_bytes()).hexdigest(),scoring=d['scoring'],originalEightReproduced=True,comparisons=summary)
(OUT/'comparison.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(summary,ensure_ascii=False,indent=2))
