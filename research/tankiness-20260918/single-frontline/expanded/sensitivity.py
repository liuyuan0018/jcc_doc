# -*- coding: utf-8 -*-
"""Targeted changed-mechanism checks and one-factor sensitivity; no second exhaustive claim."""
import json,csv,shutil,subprocess
from pathlib import Path
from check import P,I,S,run
cases=[]
def check_case(hero,star,traits,items):
 base=run(hero,star,traits,items)
 variants={
 'target_30':['target=30'],'target_100':['target=100'],'lock_2s':['lock=60'],
 'pause_0.5s':['pause=15'],'item_damage_vamp_on':['itemvamp=1'],'aoe_vamp_one_third':['aoevamp=0.3333333333'],
 'shield_no_post_mana':['shieldmana=0'],'control_on':['control=1'],
 }
 if any('夜之锋刃' in i for i in items):variants.update(edge_zero=['edge=0'],edge_1s=['edge=30'])
 if '恶火小斧' in items:variants['axe_3pct']=['axe=0.03']
 if '黎明圣盾' in items:variants['dawn_20pct']=['dawn=0.20']
 if '永恒契约' in items:variants.update(ally_no_cast=['allyperiod=0'],ally_dead_10s=['allydeath=300'])
 if any('海克斯科技枪刃' in i for i in items):variants['gunblade_self_eligible']=['gunself=1']
 if '智慧末刃' in items or '巫妖之祸' in items:variants.update(stage_2=['stage=2'],stage_6=['stage=6'])
 out={k:run(hero,star,traits,items,opts=v) for k,v in variants.items()}
 return dict(hero=hero,star=star,traits=traits,items=items,baseline=base,variants=out)
if __name__=='__main__':
 # Explicit stasis test: events can regenerate mana, but cannot attack or cast during Zhonya.
 run('伊莉丝',2,{'重装':6},['中娅悖论','适应性头盔','振奋盔甲'],opts=['trace=1'])
 tr=list(csv.DictReader((P/'trace.csv').open()))
 z=next(int(r['frame']) for r in tr if r['event']=='zhonya')
 assert not [r for r in tr if r['event'] in ('cast','attack') and z<int(r['frame'])<z+90]
 shutil.copyfile(P/'trace.csv',P/'trace-zhonya.csv')
 # Test all specific new defensive families plus one ordinary loadout for all 24 heroes.
 for hero in dict.fromkeys(s['hero'] for s in S):
  opts=[s for s in S if s['hero']==hero and s['star']==2 and len(s['traits'])==1 and 6 in s['traits'].values()]
  sc=opts[0]
  cases.append(check_case(hero,2,sc['traits'],['石像鬼石板甲','饮血剑','正义之手']))
 for items in [
  ['石像鬼石板甲','鬼索的狂暴之刃','大天使之杖'],
  ['石像鬼石板甲','夜之锋刃','振奋盔甲'],
  ['石像鬼石板甲','光明版夜之锋刃','中娅悖论'],
  ['石像鬼石板甲','死亡蔑视','饮血剑'],
  ['石像鬼石板甲','黎明圣盾','黄昏圣盾'],
  ['石像鬼石板甲','恶火小斧','智慧末刃'],
  ['石像鬼石板甲','永恒契约','海克斯科技枪刃'],
  ['禁忌雕像','光明版冕卫','适应性头盔'],
  ['石像鬼石板甲','法力药水','生命药水']]:
  cases.append(check_case('伊莉丝',3,{'重装':6},items))
 (P/'sensitivity.json').write_text(json.dumps(dict(stasis_action_check='passed',cases=cases),ensure_ascii=False,indent=2))
 print('sensitivity cases',len(cases),'stasis passed')
