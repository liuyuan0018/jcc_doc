import json,gzip,hashlib,sys,subprocess,collections,concurrent.futures
from pathlib import Path
ROOT=Path('/Users/lyu/Documents/ChatGPT/金铲铲');OUT=Path(__file__).parent;ARC=ROOT/'exports/frontline-episode-01-rerun-v3';SRC=ROOT/'research/vi-vow-topic-20260923/vow-shield-revision-v1/input'
sys.path.insert(0,str(ARC));import archive
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
hashes={str(p):sha(p) for p in [SRC/'web.cpp',SRC/'engine-web.hpp',SRC/'generated.hpp',SRC/'replay-native',ARC/'raw/scenario-158.runs.jsonl.gz',ARC/'raw/scenario-158.summary.jsonl.gz']}
with gzip.open(ARC/'raw/scenario-158.runs.jsonl.gz','rt') as f:rows=[json.loads(x) for x in f]
rows=[r for r in rows if r['augment']==0 or (r['augment']==4 and r['items'].count(27)==1)]
assert len(rows)==8365
corrections=[]
for r in rows:
 if r['items'].count(22)>1:
  stages=[]
  for d in range(300,5001,50):
   result=json.loads(subprocess.check_output([str(SRC/'replay-native'),*map(str,archive.parameters(r,d))]))['result'];stages.append(dict(dps=d,result=result))
   if not result['alive']:break
  assert not stages[-1]['result']['alive'];r.update(stages=stages,passedDps=stages[-2]['dps'] if len(stages)>1 else -1,failedDps=stages[-1]['dps']);corrections.append(r['id'])
for r in rows:
 assert r['stages'][-1]['dps']==r['failedDps'] and not r['stages'][-1]['result']['alive']
 assert all(s['result']['alive'] for s in r['stages'][:-1])
(p:=OUT/'refinement-input.txt').write_text('\n'.join(' '.join(map(str,[r['id'],r['passedDps']+1 if r['passedDps']>=300 else 300,r['failedDps'],*archive.parameters(r,300)])) for r in rows)+'\n')
subprocess.run(['clang++','-std=c++17','-O3','-I',str(SRC),str(OUT/'refine.cpp'),'-o',str(OUT/'refine')],check=True)
with p.open() as fi,(OUT/'refinement.jsonl').open('w') as fo:subprocess.run([str(OUT/'refine')],stdin=fi,stdout=fo,check=True)
fine={r['id']:r for r in map(json.loads,(OUT/'refinement.jsonl').read_text().splitlines())}
for r in rows:
 s=fine[r['id']]['stages'];assert not s[-1]['result']['alive'];r['score']=s[-2]['dps'] if len(s)>1 else r['passedDps'];r['refinedFail']=s[-1]['dps'];assert r['score']<r['failedDps']
counts=collections.Counter(r['score'] for r in rows)
for r in rows:r['rank']=1+sum(n for score,n in counts.items() if score>r['score'])
rows.sort(key=lambda r:(-r['score'],r['id']))
# Main: four conventional defensive sets plus four sustain/AP comparisons, no augment.
wanted=[((26,30,33),0),((24,27,33),0),((24,27,33),4),((24,24,27),0),((24,24,27),4),((16,24,27),0),((5,24,27),0),((5,16,24),0)]
main=[]
for k,(w,aug) in zip('ABCDEFGH',wanted):
 r=next(r for r in rows if r['items']==sorted(w) and r['augment']==aug);main.append(dict(key=k,**r))
# Results: conventional tank combinations dominate; preserve all applicable augment branches for selected sets.
meat={22,23,24,26,27,29,30,33}
selected={r['id']:r for r in main}
# 40 defensive configurations, then 16 sustain/AP and 8 paired augment controls.
for r in [r for r in rows if all(i in meat for i in r['items'])][:40]:selected[r['id']]=r
for r in [r for r in rows if r['augment']==0 and sum(i in meat for i in r['items'])>=1 and any(i in [5,16] for i in r['items'])][:12]:selected[r['id']]=r
for r in list(selected.values()):
 if r['augment']!=0:
  mate=next(x for x in rows if x['items']==r['items'] and x['augment']==0);selected[mate['id']]=mate
for r in rows:
 if len(selected)>=64:break
 if all(i in meat for i in r['items']):selected[r['id']]=r
selected=sorted(selected.values(),key=lambda r:(-r['score'],r['id']))
main_ids={r['id'] for r in main};paired_items={tuple(r['items']) for r in selected if r['augment']}
for r in list(reversed(selected)):
 if len(selected)<=64:break
 if r['id'] not in main_ids and r['augment']==0 and tuple(r['items']) not in paired_items:selected.remove(r)
assert len(selected)==64
assert hashes=={p:sha(Path(p)) for p in hashes}
report=dict(hero=archive.SCENARIOS[158],environment=archive.MANIFEST['environment'],sourceHashes=hashes,correctedDoubleVow=corrections,poolSize=len(rows),main=main,selected=selected,all=rows,scoring='300 +50 first failure, then +1 from last passed coarse tier until first failure; ties preserved')
(OUT/'ranking.json').write_text(json.dumps(report,ensure_ascii=False,separators=(',',':')))
print('pool',len(rows),'selected',len(selected),'meat',sum(all(i in meat for i in r['items']) for r in selected),'augment counts',collections.Counter(r['augment'] for r in selected))
for r in main:print(r['key'],r['id'],r['passedDps'],r['score'],[archive.ITEMS[i]['name'] for i in r['items']])
