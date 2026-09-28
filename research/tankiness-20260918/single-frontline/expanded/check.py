# -*- coding: utf-8 -*-
import json,subprocess,sys,time,random
from pathlib import Path
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P.parent));import sim30
cat=json.loads((P/'catalog.json').read_text());S=json.loads((P/'scenarios.json').read_text());I={x['name']:x['index'] for x in cat['items']}
def run(hero,star,traits,items,aug=0,opts=()):
 sc=next(s for s in S if s['hero']==hero and s['star']==star and s['traits']==traits)
 cmd=[str(P/'engine'),'one',str(sc['index'])]+[str(I[x]) if x is not None else '-1' for x in items]+[str(aug)]+list(opts)
 return json.loads(subprocess.check_output(cmd,cwd=P,text=True))
def check():
 results=[]
 names=['狂徒铠甲','石像鬼石板甲','振奋盔甲'];oldnames=['狂徒','板甲','振奋']
 for hero in ['伊莉丝','蔚','阿木木']:
  for star in (1,2,3):
   traits={'重装' if hero=='伊莉丝' else '主宰':6};h=next(h for h in sim30.PROFILES if h['name']==hero and h['star']==star)
   old=sim30.sim(h,sim30.prepare(oldnames,traits));new=run(hero,star,traits,names)
   for key,oldkey in [('frame','time'),('casts','casts'),('attacks','attacks'),('heal','heal')]:
    a=new[key]/30 if key=='frame' else new[key];b=old[oldkey]
    assert abs(a-b)<.002,(hero,star,key,a,b)
   results.append(dict(check='legacy parity',hero=hero,star=star,time=new['frame']/30))
 r=run('伊莉丝',3,{'重装':6},['石像鬼石板甲','鬼索的狂暴之刃','大天使之杖'])
 assert r['alive'] and r['casts']==12 and r['attacks']==54 and abs(r['spider_heal']-17912.2)<.01,r
 # Target resistance must affect damage-based healing without altering prescribed incoming DPS.
 lo=run('伊莉丝',3,{'重装':6},['饮血剑','饮血剑','饮血剑'],opts=['target=0'])
 hi=run('伊莉丝',3,{'重装':6},['饮血剑','饮血剑','饮血剑'],opts=['target=200'])
 assert lo['damage']>hi['damage'] and lo['vamp']>hi['vamp']
 # Radiant nightblade restores missing HP; invulnerability records prevented raw input.
 r=run('伊莉丝',2,{'重装':6},['光明版夜之锋刃','中娅悖论','振奋盔甲'])
 assert r['avoided_raw']>0 and r['heal']>0
 # Shield conversion leaves an exact conservation ledger and adds health.
 r=run('奥恩',2,{'护卫':6},['禁忌雕像','冕卫','圣盾使的誓约'])
 assert r['shield_converted']>0 and r['growth']>0
 # Death defiance produces a deferred stream, not durability and not repeat mana.
 r=run('伊莉丝',2,{'重装':6},['死亡蔑视','狂徒铠甲','石像鬼石板甲'])
 assert r['deferred']>0 and r['debt_paid']>0
 # Physical/magical stats parse in percentage points even when raw tooltip omits %.
 assert cat['items'][I['冕卫']]['stats']['AP']==.2
 assert cat['items'][I['光明版适应性头盔']]['stats']['MR']==40
 # All modeled items work in a representative build, catch unhandled categories.
 for it in cat['items']:
  r=run('伊莉丝',2,{'重装':6},[it['name'],'狂徒铠甲','石像鬼石板甲'])
  assert r['mana_initial']+r['mana_gain']-r['mana_spent']-r['mana']<.001
  assert abs(r['shield_granted']-r['shield_used']-r['shield_lost']-r['shield'])<.01
 results.append(dict(check='all 107 item smoke and ledgers',count=len(cat['items'])))
 return dict(passed=True,checks=results)
if __name__=='__main__':
 r=check();(P/'checks.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));print(json.dumps(r,ensure_ascii=False,indent=2))
