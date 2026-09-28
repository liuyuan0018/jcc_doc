import gzip,time,json,itertools,hashlib
from concurrent.futures import ProcessPoolExecutor,as_completed
from sim30 import *
R=P/'fps30';R.mkdir(exist_ok=True)
def score(r):return (r['time'],r['hp_left']+r['shield_left'])
def worker(h):
 normal=list(itertools.combinations_with_replacement(NORMAL,3));gold=[x+('金霖大亨',) for x in itertools.combinations_with_replacement(NORMAL,2)]
 best=[];count=0
 with gzip.open(R/(h['id']+'.jsonl.gz'),'wt') as out:
  for ts,slots in trait_options(h):
   for lane,pool,healthy in [('普通',normal,False),('心之钢',normal,True),('金霖龙',gold,False),('双海克斯',gold,True)]:
    extra=1 if lane in ('金霖龙','双海克斯') else 0
    if slots+extra>9:continue
    winner=None;survivors=0
    for items in pool:
     if healthy and '坚定之心' not in items:continue
     r=sim(h,prepare(items,ts,healthy));r.pop('trace');r.pop('events')
     assert abs(r['shield_granted']-r['shield_used']-r['shield_lost']-r['shield_left'])<.001
     row=dict(id=h['id'],hero=h['name'],star=h['star'],cost=h['cost'],traits=ts,items=items,lane=lane,minimum_slots=slots+extra,**r)
     out.write(json.dumps(row,ensure_ascii=False)+'\n');count+=1;survivors+=int(r['alive'])
     if winner is None or score(row)>score(winner):winner=row
    if winner:best.append(dict(winner,surviving_builds=survivors))
 return best,count
if __name__=='__main__':
 start=time.time();records=[];count=0
 with ProcessPoolExecutor(max_workers=4) as pool:
  futures={pool.submit(worker,h):h for h in PROFILES}
  for f in as_completed(futures):
   best,n=f.result();records+=best;count+=n;h=futures[f]
   print(h['name'],h['star'],count,round(time.time()-start,1),flush=True)
 (R/'best.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
 meta=dict(runs=count,elapsed=round(time.time()-start,1),fps=30,normal_triples=455,gold_triples=91,profiles=len(PROFILES),role_source='datatft-s18.json',source_sha256=hashlib.sha256((P.parent/'sources/dataj-gamedata.json').read_bytes()).hexdigest())
 (R/'manifest.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2));print(meta)
