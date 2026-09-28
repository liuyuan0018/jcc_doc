import json,sys,random,subprocess,hashlib,time
from pathlib import Path
ROOT=Path('/Users/lyu/Documents/ChatGPT/金铲铲');OUT=Path(__file__).parent.resolve();SRC=ROOT/'research/vi-vow-topic-20260923/vow-shield-revision-v1/input';sys.path.insert(0,str(ROOT/'exports/frontline-episode-01-rerun-v3'));import archive
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=[SRC/n for n in ['web.cpp','engine-web.hpp','generated.hpp','replay-native']];before={str(p):sha(p) for p in files}
data=json.loads((ROOT/'research/rammus-results64-20260925/ranking.json').read_text());assert before[str(SRC/'replay-native')]==data['hashes']['revisedReplay']
selected=data['selected'];ids={r['id'] for r in selected};other=[r for r in data['all'] if r['id'] not in ids and r['passedDps']>=300];pilot=selected+random.Random(20260925).sample(other,64)
lines=[' '.join(map(str,[r['id'],r['passedDps'],r['failedDps'],*archive.parameters(r,r['passedDps'])])) for r in pilot];(OUT/'input.txt').write_text('\n'.join(lines)+'\n')
t=time.monotonic();subprocess.run(['clang++','-std=c++17','-O3','-pthread','-I',str(SRC),str(OUT/'pilot.cpp'),'-o',str(OUT/'pilot')],check=True);compileSecs=time.monotonic()-t
with (OUT/'stages.jsonl').open('w') as f:subprocess.run([str(OUT/'pilot')],stdin=(OUT/'input.txt').open(),stdout=f,check=True)
rows=[json.loads(s) for s in (OUT/'stages.jsonl').read_text().splitlines()];assert len(rows)==128
assert before=={str(p):sha(p) for p in files}
reversals=[{k:r[k] for k in ['id','lo','hi','highestPass','firstFail','binaryPass','reversals']} for r in rows if r['reversals']]
mismatch=[r['id'] for r in rows if r['highestPass']!=r['binaryPass']]
bounds=[r['id'] for r in rows if not r['stages'][0]['result']['alive'] or r['stages'][-1]['result']['alive']]
report=dict(configurations=128,selected64=64,seed=20260925,gridCalls=sum(len(r['stages']) for r in rows),binaryCalls=sum(r['binaryCalls'] for r in rows),gridSeconds=sum(r['gridSeconds'] for r in rows),binarySeconds=sum(r['binarySeconds'] for r in rows),compileSeconds=compileSecs,reversals=reversals,binaryMismatches=mismatch,boundaryMismatches=bounds,sourceHashes=before)
(OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False))
