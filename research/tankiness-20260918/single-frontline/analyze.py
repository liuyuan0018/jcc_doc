from sim import *
import gzip

def reader(path):
 if path.exists():return path.open()
 return gzip.open(str(path)+'.gz','rt')

def key(r):return (r['id'],tuple(sorted(r['traits'].items())),tuple(r['items']),r['lane'])
def group(r):return (r['id'],tuple(sorted(r['traits'].items())),r['lane'])

def run():
 paths=[P/'mana-10/all_results.jsonl',P/'all_results.jsonl',P/'mana-30/all_results.jsonl']
 streams=[reader(p) for p in paths]
 robust={};winners={};matchingheart={};heartcomparisons=[];n=0
 for lines in zip(*streams):
  rs=[json.loads(x) for x in lines];assert len(set(key(r) for r in rs))==1
  r=dict(rs[1]);r['times']=[x['time'] for x in rs];r['all_alive']=all(x['alive'] for x in rs);r['worst_time']=min(r['times'])
  r['lowest_remaining']=min(x['hp_left']+x['shield_left'] for x in rs)
  g=group(r)
  if g not in robust or (r['worst_time'],r['lowest_remaining'])>(robust[g]['worst_time'],robust[g]['lowest_remaining']):robust[g]=r
  if r['lane']=='普通' and '坚定之心' in r['items']:
   matchingheart[key(r)[:-1]]=r
  if r['lane']=='心之钢':
   base=matchingheart[key(r)[:-1]]
   heartcomparisons.append(dict(id=r['id'],hero=r['hero'],star=r['star'],traits=r['traits'],items=r['items'],normal_time=base['time'],healthy_time=r['time'],gain=round(r['time']-base['time'],5)))
  n+=1
 for f in streams:
  assert not f.readline(), 'Mismatched result file lengths'
  f.close()
 assert n==161226
 # Representatives for convergence and additional mechanism sensitivity, selected from robust winners.
 byid={h['id']:h for h in PROFILES};sens=[];traces=[]
 for id_ in ['11503','12500','13501','23501','24503','33501','33515','35450','35451','35452']:
  options=[r for r in robust.values() if r['id']==id_ and r['lane'] in ['普通','金霖龙']]
  for lane in ['普通','金霖龙']:
   rr=max((r for r in options if r['lane']==lane),key=lambda r:(r['worst_time'],r['lowest_remaining']))
   h=byid[id_];cfg=prepare(rr['items'],rr['traits'],False)
   for label,kw in [('基准',{}),('步长1/30',{'dt':1/30}),('步长1/120',{'dt':1/120}),('百分比不放大固定血',{'hp_rule':'base'}),('减伤相加',{'dr_add':True}),('每秒1伤害包',{'frequency':1}),('每秒6伤害包',{'frequency':6})]:
    v=sim(h,cfg,**kw)
    sens.append(dict(id=id_,hero=h['name'],star=h['star'],lane=lane,traits=rr['traits'],items=rr['items'],variant=label,**v))
   traces.append(dict(id=id_,hero=h['name'],star=h['star'],lane=lane,traits=rr['traits'],items=rr['items'],**sim(h,cfg,trace=True,dt=1/30)))
 # Since 6 packets/s requires a grid representing 1/6, main grid1/15 would alias; rerun its exact-grid branch.
 for r in sens:
  if r['variant']=='每秒6伤害包':r.update(sim(byid[r['id']],prepare(r['items'],r['traits']),frequency=6,dt=1/30))
 (P/'robust_best.json').write_text(json.dumps(list(robust.values()),ensure_ascii=False,indent=2))
 (P/'sensitivity.json').write_text(json.dumps(sens,ensure_ascii=False,indent=2))
 (P/'traces.json').write_text(json.dumps(traces,ensure_ascii=False))
 (P/'heart_comparisons.json').write_text(json.dumps(heartcomparisons,ensure_ascii=False))
 print('rows aligned:',n,'robust best:',len(robust),'heart paired:',len(heartcomparisons),'sensitivity:',len(sens))
 for star in [1,2,3]:
  for lane in ['普通','心之钢','金霖龙','双海克斯']:
   a=[r for r in robust.values() if r['star']==star and r['lane']==lane and (star!=3 or r['cost']<=3)]
   best=max(r['worst_time'] for r in a)
   print(star,lane,best,[(r['hero'],r['traits'],r['items'],r['times']) for r in a if r['worst_time']==best][:6])
if __name__=='__main__':run()
