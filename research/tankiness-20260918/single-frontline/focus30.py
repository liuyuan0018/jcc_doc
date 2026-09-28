import itertools,json,gzip,time
from sim30 import *
R=P/'fps30';R.mkdir(exist_ok=True)
def score(r):return (r['time'],r['hp_left']+r['shield_left'])
def clean(r):return {k:v for k,v in r.items() if k not in ('events','trace')}
def run():
 best=[];count=0;start=time.time()
 with gzip.open(R/'elise-expanded.jsonl.gz','wt') as out:
  for star in (1,2,3):
   h=next(h for h in PROFILES if h['name']=='伊莉丝' and h['star']==star)
   for z in (2,4,6):
    for lane,pool,healthy in [('普通',list(itertools.combinations_with_replacement(NORMAL+['羊刀','大天使','泰坦'],3)),False),('金霖龙',[x+('金霖大亨',) for x in itertools.combinations_with_replacement(NORMAL+['羊刀','大天使','泰坦'],2)],False)]:
     w=None;survivors=0
     for items in pool:
      r=clean(sim(h,prepare(items,{'重装':z},healthy)))
      row=dict(hero='伊莉丝',star=star,cost=2,traits={'重装':z},items=items,lane=lane,**r)
      out.write(json.dumps(row,ensure_ascii=False)+'\n');count+=1;survivors+=int(r['alive'])
      if w is None or score(row)>score(w):w=row
     best.append(dict(w,surviving_builds=survivors))
   print('Elise',star,count,round(time.time()-start),flush=True)
 (R/'elise-expanded-best.json').write_text(json.dumps(best,ensure_ascii=False,indent=2))
 # Same builds show skill contribution; plus mechanism sensitivity rather than mana budgets.
 panels=[]
 for star in (1,2,3):
  h=next(h for h in PROFILES if h['name']=='伊莉丝' and h['star']==star)
  builds=[('狂徒','板甲','振奋'),('板甲','羊刀','大天使'),('板甲','板甲','振奋')]
  builds+= [tuple(r['items']) for r in best if r['star']==star and r['traits']=={'重装':6}]
  for items in dict.fromkeys(builds):
   cfg=prepare(items,{'重装':6})
   baseline=sim(h,cfg,trace=True)
   filename=f'elise-{star}-'+str(len(panels))+'.json'
   (R/filename).write_text(json.dumps(baseline,ensure_ascii=False,indent=2))
   variants={k:clean(sim(h,cfg,**kw)) for k,kw in [('no_skill',dict(skills=False)),('lock2',dict(lock_seconds=2)),('lock4',dict(lock_seconds=4)),('pause0',dict(cast_pause=0)),('pause0.5',dict(cast_pause=.5)),('shield_no_mana',dict(shield_mana=False)),('hit6',dict(frequency=6)),('hit1',dict(frequency=1)),('post5',dict(post_coef=.05))]}
   panels.append(dict(star=star,items=items,traits={'重装':6},trace_file=filename,baseline=clean(baseline),variants=variants))
 (R/'elise-panels.json').write_text(json.dumps(panels,ensure_ascii=False,indent=2))
 print('focus done',count,round(time.time()-start),flush=True)
if __name__=='__main__':run()
