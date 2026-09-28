"""Checks target mana attribution, lock, transform and attack-heal feedback."""
import json
from sim30 import *
def check():
 h=next(h for h in PROFILES if h['name']=='伊莉丝' and h['star']==2)
 for star in (1,2,3):
  hh=next(h for h in PROFILES if h['name']=='伊莉丝' and h['star']==star)
  alt=hero('12515',star)
  assert hh['AS']==float(alt['attackSpeed']) and hh['cap']==alt['maxMp'] and hh['H']==alt['initHp']
 # Isolate attacks: .65 attacks/sec, starting20, 5 per attack => first cast on 10th attack.
 r=sim(h,prepare((),{}),dps=0,trace=True,limit=20)
 assert r['cast_frames'][0]==462,r['cast_frames']
 assert len(r['trace'])==601
 assert r['final_max_hp']==h['H']+475
 # Isolate one shielded damage event; count damage to shield for mana.
 r=sim(dict(h,AS=0),prepare((),{'重装':6}),limit=1/3,trace=True)
 dmg=1400/3/1.45*.95
 assert abs(r['final_mana']-(20+1400/3*.01+.03*dmg))<1e-7
 # Block sources during lock and prohibit casts from fatal hits.
 r=sim(dict(h,mp=70),prepare(('振奋',),{}),trace=True,limit=.5)
 assert r['cast_frames']==[0] and r['final_mana']==0
 r=sim(h,prepare((),{'重装':4}),dps=1e8,trace=True)
 assert not r['alive'] and r['casts']==0 and not r['half']
 # Ledger and attack/heal counts, including head amplification and lifeline.
 for name in ('伊莉丝','蔚','阿木木','纳尔','黛安娜'):
  hh=next(x for x in PROFILES if x['name']==name and x['star']==2)
  r=sim(hh,prepare(('适应头盔','圣盾誓约','振奋'),{'重装':4}),trace=True)
  g=sum(r['mana'].get(x,0) for x in ('attack','damage','regen','start','vow','sett'))
  assert abs(r['initial_mana']+g-r['mana'].get('spent',0)-r['final_mana'])<1e-7
  assert abs(r['shield_granted']-r['shield_used']-r['shield_lost']-r['shield_left'])<.001
  if name=='伊莉丝':assert abs(r['spider_heal']+r['overheal']-90*r['spider_attacks'])<1e-5
  if name=='黛安娜':assert r['mana'].get('damage',0)==0
  if name=='纳尔':assert r['mana'].get('damage',0)==0
 # Same build at 30/60/120Hz: timestamps can cross a packet boundary, report observed difference.
 convergence=[]
 for n in ('伊莉丝','蔚','阿木木'):
  for star in (1,2,3):
   hh=next(x for x in PROFILES if x['name']==n and x['star']==star)
   cfg=prepare(('狂徒','板甲','振奋'),{'重装' if n=='伊莉丝' else '主宰':6})
   rr=[sim(hh,cfg,fps=f) for f in (30,60,120)]
   convergence.append(dict(hero=n,star=star,times=[r['time'] for r in rr],casts=[r['casts'] for r in rr]))
 return dict(passed=True,checks=['3 star human/spider records agree','10 tank attacks fill 20/70 mana at frame462 without incoming damage','shielded damage mana arithmetic','mana lock rejects damage and regeneration','fatal hit cannot rescue via cast','5 archetype mana ledgers','shield conservation','Elise per-attack healing accounting','fighter and rage receive no damage mana'],convergence=convergence)
if __name__=='__main__':
 r=check();(P/'checks30.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));print(json.dumps(r,ensure_ascii=False,indent=2))
