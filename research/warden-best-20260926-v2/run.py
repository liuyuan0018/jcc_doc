import json,hashlib,shutil,subprocess,concurrent.futures,time,sys,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'exports/warden-best-20260926-v2';assert Path('/Volumes/Apple').is_mount();OUT.mkdir(exist_ok=True);(OUT/'input').mkdir(exist_ok=True);(OUT/'raw').mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name in ['web.cpp','engine-web.hpp','generated.hpp']:shutil.copy2(ROOT/'tank-lab/src'/name,OUT/'input'/name)
shutil.copy2(Path(__file__).with_name('scan.cpp'),OUT/'input/scan.cpp')
subprocess.run(['clang++','-std=c++17','-O3','-I',str(OUT/'input'),str(OUT/'input/scan.cpp'),'-o',str(OUT/'input/scan')],check=True)
shutil.copy2(Path(__file__).with_name('check.cpp'),OUT/'input/check.cpp')
subprocess.run(['clang++','-std=c++17','-O2','-I',str(OUT/'input'),str(OUT/'input/check.cpp'),'-o',str(OUT/'input/check')],check=True)
checks=subprocess.check_output([str(OUT/'input/check')]);(OUT/'mechanics-verification.json').write_bytes(checks);print(checks.decode(),flush=True)
sys.path.insert(0,str(ROOT/'exports/frontline-episode-01-rerun-v3'));import archive
sc=[s for s in archive.SCENARIOS.values()if '护卫'in s['traits']and s['star']==(3 if s['cost']<=3 else 2)];pool=json.loads((ROOT/'research/malphite-value-20260925/equipment-pool.json').read_text());assert len(pool)==8365
# All scenarios freshly calculated with own-skill-shield mana lock for Ornn/Shen/Rammus.
manifest=dict(status='running',scope='2/4/6护卫最强英雄，1—3费三星，4—5费两星；三件普通装备；无/适用单身板甲；不计神器进度',scenarios=sc,poolPerScenario=len(pool),total=len(sc)*len(pool),scoring='300 +50首败停止，再从最后通过档+1细分至首败；低于起点未通过记-1、不作精确分数',sourceHashes={n:sha(OUT/'input'/n)for n in ['web.cpp','engine-web.hpp','generated.hpp','scan.cpp','scan']},environment=dict(seconds=30,attackers=5,wound=.33,resistanceReduction=.3,physicalShare=.5,control=False),reusedScenario=None, manaLockContract="Ornn/Shen/Rammus own skill shield blocks all sources including direct mana; equipment/trait shields do not; existing minimum cast lock retained")
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
meta={}
for s in sc:
 lines=[]
 for bi,b in enumerate(pool):
  key=f's{s["index"]}-p{bi}';r=dict(id=key,scenario=s['index'],items=b['items'],augment=b['augment']);meta[key]=r;lines.append(' '.join(map(str,[key,*archive.parameters(r,300)])))
 (OUT/'input'/f's{s["index"]}.txt').write_text('\n'.join(lines)+'\n')
start=time.monotonic()
def one(s):
 dest=OUT/'raw'/f's{s["index"]}.jsonl'
 if not dest.exists():
  with (OUT/'input'/f's{s["index"]}.txt').open()as fi,dest.with_suffix('.partial').open('w')as fo:subprocess.run([str(OUT/'input/scan')],stdin=fi,stdout=fo,check=True)
  dest.with_suffix('.partial').rename(dest)
 rows=[json.loads(x)for x in dest.open()];assert len(rows)==8365 and all(r['failedDps']>=0 and r['refinedFail']>=0 for r in rows);return s,rows
allrows=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=4)as ex:
 for done,f in enumerate(concurrent.futures.as_completed([ex.submit(one,s)for s in sc]),1):
  s,rs=f.result()
  for r in rs:r.update(meta[r['id']],hero=s['hero'],star=s['star'],tier=s['traits']['护卫'])
  allrows+=rs;print(f'{done}/18 {s["hero"]} {s["traits"]} complete; {time.monotonic()-start:.1f}s',flush=True)
assert len(allrows)==150570
best=[]
for s in sc:
 rs=[r for r in allrows if r['scenario']==s['index']];score=max(r['score']for r in rs);w=[r for r in rs if r['score']==score];best.append(dict(hero=s['hero'],star=s['star'],tier=s['traits']['护卫'],scenario=s['index'],score=score,tieCount=len(w),builds=[{k:r[k]for k in ['id','items','augment','score','passedDps','failedDps']}for r in w]))
for x in best:x['heroRankInTier']=1+sum(y['tier']==x['tier']and y['score']>x['score']for y in best)
best.sort(key=lambda x:(x['tier'],-x['score'],x['hero']));(OUT/'hero-ranking.json').write_text(json.dumps(best,ensure_ascii=False,indent=2))
counts=collections.Counter(r['score']for r in allrows);rank={};n=0
for score,c in sorted(counts.items(),reverse=True):rank[score]=n+1;n+=c
with (OUT/'full-ranking.jsonl').open('w')as f:
 for r in sorted(allrows,key=lambda r:(-r['score'],r['id'])):
  z={k:r[k]for k in ['id','hero','star','tier','items','augment','score','passedDps','failedDps']};z['configurationRank']=rank[r['score']];f.write(json.dumps(z,ensure_ascii=False)+'\n')
for n,h in manifest['sourceHashes'].items():assert sha(OUT/'input'/n)==h
manifest.update(status='complete',newlyComputed=18*8365,reused=0,elapsedSeconds=time.monotonic()-start,belowStart=sum(r['score']<0 for r in allrows));(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2));print(json.dumps(best,ensure_ascii=False),flush=True)
