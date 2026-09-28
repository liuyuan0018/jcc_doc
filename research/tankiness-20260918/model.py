"""S18 conditional tank model. Standard library only; not a game engine.
Run python3 model.py. Source snapshot is immutable; outputs regenerated locally.
"""
from pathlib import Path
import json, math, itertools, hashlib, datetime, re
ROOT=Path(__file__).resolve().parent
DATA=json.loads((ROOT/'sources/dataj-gamedata.json').read_text())['data']
TRAITS={'护卫':'341','主宰':'343','重装':'342','斗士':'340'}
TIERS={0:0,2:1,4:2,6:3}
# hp, hp%, armor, mr. Item effects are applied separately.
ITEMS={'狂徒':(500,.18,0,0),'板甲':(100,0,25,25),'反甲':(0,.06,50,0),
       '龙牙':(0,.06,0,60),'振奋':(300,0,0,0),'坚定之心':(250,0,20,0),
       '日炎':(150,.08,20,0),'圣盾誓约':(0,0,25,25),'适应头盔':(0,0,30,50)}
# Six core defensive items; 20 distinct three-item sets, no duplicate item effects.
BUILDS=[()]+[(x,) for x in list(ITEMS)[:6]]+list(itertools.combinations(list(ITEMS)[:6],3))
SCENARIOS={
 '物理普攻':dict(dps=700,p=1,m=0,aa=1),
 '魔法持续':dict(dps=700,p=0,m=1,aa=0),
 '物理技能':dict(dps=700,p=1,m=0,aa=0),
 '纯真伤':dict(dps=700,p=0,m=0,aa=0),
 '混合持续':dict(dps=700,p=.5,m=.5,aa=.5),
 '混合破双抗30%':dict(dps=700,p=.5,m=.5,aa=.5,shred=.3),
 '混合重伤33%':dict(dps=700,p=.5,m=.5,aa=.5,wound=.33),
 '真伤30%':dict(dps=700,p=.35,m=.35,aa=.35),
 '每秒2%最大生命真伤':dict(dps=500,p=.5,m=.5,aa=.5,burn=.02),
 '开场爆发':dict(dps=350,p=0,m=1,aa=0,burst=3500),
 '低压长战':dict(dps=200,p=.5,m=.5,aa=.5),
 '8秒后被集火':dict(dps=700,p=.5,m=.5,aa=.5,delay=8),
 '递增混伤':dict(dps=280,p=.5,m=.5,aa=.5,ramp=.10),
 '第6秒法术爆发':dict(dps=350,p=0,m=1,aa=0,bursts=[(6,3500)]),
}
# Canonical base-form records only; no transformed duplicates.
IDS=['11500','11501','11502','11503','11504','12500','12501','12502','12503',
'12504','12505','13500','13501','13502','13503','13506','13515','14500','14502','14503','14505','15450','15451','15452']
HEROES={h['id']:h for h in DATA['hero']}
# All listed profiles have modeled direct self defense. Death summons, CC and ally buffs excluded.
SUPPORTED=['奥恩','洛','蕾欧娜','可酷伯','雷克塞','峡谷迅捷蟹','阿利斯塔','瑟庄妮','慎','赫卡里姆','费德提克','黛安娜','拉莫斯','苍蓝雕纹魔像','莉莉娅','阿木木','茂凯']
def hero(base,star):return HEROES[str(star)+base[1:]]
def field(h,i):
 s=h['skillBriefValue'].split('|')[i].split('/')
 return float(s[min(int(h['id'][0])-1,len(s)-1)].strip('%'))
def profile(h):
 return dict(name=h['name'],hp=h['initHp'],a=h['armor'],m=h['magicResist'],star=int(h['id'][0]),raw=h)
DUMMY=dict(name='同面板假人',hp=1800,a=50,m=50,star=2)
def stats(h,traits,items,n=3,hp_mode='all',brawler_flat=False,defender_extra=False):
 f=sum(ITEMS[i][0] for i in items);b=sum(ITEMS[i][1] for i in items)
 tier=traits.get('斗士',0)
 if tier:
  b+={2:.25,4:.4,6:.65}[tier]
  if brawler_flat:f+=120
 H=(h['hp']+f)*(1+b) if hp_mode=='all' else h['hp']*(1+b)+f
 a=h['a']+sum(ITEMS[i][2] for i in items);m=h['m']+sum(ITEMS[i][3] for i in items)
 if '板甲' in items:a+=10*n;m+=10*n
 if traits.get('护卫'):
  v={2:25,4:60,6:120}[traits['护卫']]+(12 if defender_extra else 0);a+=v;m+=v
 return H,a,m

def simulate(h,traits,items=(),scenario=None,skills=True,dt=.05,limit=30,first=4,period=8,n=3,
 hp_mode='all',brawler_flat=False,defender_extra=False,dr_mode='product',true_dr=False,
 shield_scale=1,attack_period=None,trace=False):
 s=dict(SCENARIOS['混合持续'] if scenario is None else scenario)
 H,A,M=stats(h,traits,items,n,hp_mode,brawler_flat,defender_extra)
 hp=H;shields=[];heals=[];buffs=[];used_half=False;used_vow=False;casts=0
 totals=dict(heal=0,overheal=0,shield_granted=0,shield_used=0,shield_expired=0,raw=0)
 records=[];alive=True
 def shield(v,dur,key,t):
  v*=shield_scale
  # Recasts refresh the same skill shield; do not assume unlimited stacking.
  for old in shields[:]:
   if old[2]==key:totals['shield_expired']+=old[0];shields.remove(old)
  shields.append([v,t+dur,key]);totals['shield_granted']+=v
 def heal(v):
  nonlocal hp
  v*=1-s.get('wound',0);take=min(v,H-hp);hp+=take
  totals['heal']+=take;totals['overheal']+=v-take
 z=traits.get('重装',0);q={0:0,2:.18,4:.3,6:.4}[z]
 if q:shield(q*H,10,'vanguard0',0)
 def passive(t):
  if not skills:return 0
  name=h['name'];raw=h.get('raw')
  if name=='阿木木':return H*(.04 if h['star']>=3 else .025)+field(raw,0)
  if name=='雷克塞':return (H*.01+field(raw,0))*(3 if any(b[2]=='reksai' and b[1]>t for b in buffs) else 1)
  return 0
 def cast(t):
  nonlocal casts
  casts+=1;name=h['name'];raw=h.get('raw')
  if name in ['奥恩','洛','慎','黛安娜']:
   idx=1 if name=='黛安娜' else 0;shield(field(raw,idx),2 if name=='黛安娜' else 4,'skill',t)
  elif name in ['瑟庄妮','苍蓝雕纹魔像']:shield(.1*H+field(raw,0),4,'skill',t)
  elif name=='可酷伯':heals.append([(.07*H+field(raw,0))/2,t+2,t])
  elif name=='阿利斯塔':heal(.08*H+field(raw,0))
  elif name=='峡谷迅捷蟹':heals.append([field(raw,1)/3,t+3,t]);buffs.append([.15,t+3,'dr'])
  elif name=='赫卡里姆':heals.append([field(raw,0)/3,t+3,t]);buffs.append([50,t+3,'resist'])
  elif name=='费德提克':heals.append([field(raw,0)/2,t+2,t])
  elif name=='莉莉娅':heal(field(raw,0))
  elif name=='茂凯':heal(field(raw,3)+.1*(H-hp))
  elif name=='雷克塞':buffs.append([0,t+3,'reksai'])
  elif name=='拉莫斯':shield(field(raw,0),4,'skill',t);buffs.append([60,t+4,'rammus'])
 def dr(t):
  rates=[]
  if traits.get('主宰'):rates.append({2:.2,4:.33,6:.45}[traits['主宰']])
  if z==6 and sum(x[0] for x in shields)>1e-9:rates.append(.05)
  if '振奋' in items:rates.append(.08)
  if '坚定之心' in items:rates.append(.15 if hp>H*.5 else .05)
  rates.extend(b[0] for b in buffs if b[2]=='dr' and b[1]>t)
  return math.prod(1-v for v in rates) if dr_mode=='product' else max(.01,1-sum(rates))
 def damage(raw,t):
  nonlocal hp,used_half,used_vow,alive
  ar=A;mr=M
  for b in buffs:
   if b[1]>t and (b[2]=='resist' or b[2]=='rammus' and any(x[2]=='skill' for x in shields)):ar+=b[0];mr+=b[0]
  if skills and h['name']=='蕾欧娜':
   bonus=field(h['raw'],0)*max(0,1-t/12);ar+=bonus;mr+=bonus
  ar*=1-s.get('shred',0);mr*=1-s.get('shred',0)
  p=s.get('p',.5);m=s.get('m',.5);tr=max(0,1-p-m)
  # AA portion is within physical fraction in these scenarios.
  coeff=(p-(s.get('aa',0)*.05 if '反甲' in items else 0))*100/(100+ar)+m*100/(100+mr)
  mult=dr(t);burn=s.get('burn',0)*H*(raw/s['dps']) if s['dps'] else 0
  dmg=raw*(coeff*mult+tr*(mult if true_dr else 1))+burn*(mult if true_dr else 1)
  totals['raw']+=raw+burn
  # An individual packet uses defenses at packet start; half-health shields only after surviving it.
  for sh in sorted(shields,key=lambda x:x[1]):
   take=min(sh[0],dmg);sh[0]-=take;dmg-=take;totals['shield_used']+=take
  shields[:]=[x for x in shields if x[0]>1e-9]
  hp-=dmg
  if hp<=0 or hp<=H*s.get('execute',0):alive=False;return
  if q and not used_half and hp<=H*.5:used_half=True;shield(q*H,10,'vanguard1',t)
  if '圣盾誓约' in items and not used_vow and hp<=H*.4:used_vow=True;shield(.2*H,limit,'vow',t)
 steps=round(limit/dt);next_cast=first;next_attack=attack_period if attack_period else 0
 death=limit
 for step in range(steps+1):
  t=step*dt
  for sh in shields[:]:
   if sh[1]<=t+1e-9:totals['shield_expired']+=sh[0];shields.remove(sh)
  if skills and h['name'] in SUPPORTED and t+1e-9>=next_cast:
   cast(t);next_cast+=period
  if step and abs(t-round(t))<dt/3:heal(passive(t))
  if step and '振奋' in items and abs(t-round(t))<dt/3:heal(.02*(H-hp))
  if step and '龙牙' in items and abs(t/2-round(t/2))<dt/6:heal(.025*H)
  for rate,end,start in heals:
   if step and t<=end+1e-9 and t>start+1e-9:heal(rate*dt)
  heals[:]=[x for x in heals if x[1]>t+1e-9]
  if step==0 and s.get('burst'):damage(s['burst'],t)
  for at,amount in s.get('bursts',[]):
   if alive and abs(t-at)<dt/3:damage(amount,t)
  if alive and step and t+1e-9>=s.get('delay',0):
   if attack_period:
    if t+1e-9>=next_attack:damage(s['dps']*attack_period*(1+s.get('ramp',0)*t),t);next_attack+=attack_period
   else:damage(s['dps']*dt*(1+s.get('ramp',0)*t),t)
  if trace and (step%max(1,round(.5/dt))==0 or not alive):records.append([round(t,3),max(0,round(hp,2)),round(sum(x[0] for x in shields),2)])
  if not alive:death=t;break
  # t=30 heals/casts are only relevant to the censored endpoint, not extended beyond horizon.
 return dict(time=round(death,5),censored=alive,H=round(H,3),casts=casts,half_triggered=used_half,hp_remaining=round(max(0,hp),4),shield_remaining=round(sum(x[0] for x in shields),4),
  **{k:round(v,4) for k,v in totals.items()},trace=records)

def analytic(H,A,trait,tier):
 if trait=='护卫':return H*(1+(A+{2:25,4:60,6:120}[tier])/100)
 if trait=='主宰':return H*(1+A/100)/(1-{2:.2,4:.33,6:.45}[tier])
 if trait=='斗士':return H*(1+{2:.25,4:.4,6:.65}[tier])*(1+A/100)
 q={2:.18,4:.3,6:.4}[tier];return H*(1+A/100)*(1+2*q/(.95 if tier==6 else 1))

def checks():
 rows=[]
 for name in TRAITS:
  for tier in [2,4,6]:
   # High DPS ensures both shields consumed before expiration; small packets approximate continuous model.
   expect=analytic(1800,50,name,tier)/2000
   got=simulate(DUMMY,{name:tier},scenario=dict(dps=2000,p=.5,m=.5,aa=0),skills=False,dt=.001)['time']
   assert abs(expect-got)<.004,(name,tier,expect,got)
   rows.append(dict(test=name+str(tier),expected=expect,observed=got,error=got-expect))
 # Shield expiration and lethal hit test detect mistakes hidden by an EHP-only model.
 slow=simulate(DUMMY,{'重装':4},scenario=dict(dps=10,p=1,m=0),skills=False)
 assert slow['shield_expired']>0 and slow['censored']
 lethal=simulate(DUMMY,{'重装':4},scenario=dict(dps=0,p=0,m=1,burst=5000),skills=False)
 assert lethal['time']==0 and not lethal['half_triggered']
 x=simulate(profile(hero('11503',2)),{'斗士':4},('龙牙',),SCENARIOS['混合持续'])
 y=simulate(profile(hero('11503',2)),{'斗士':4},('龙牙',),SCENARIOS['混合重伤33%'])
 assert x['time']>=y['time']
 for base in ['11500','11503','14503']:
  for dt in [.1,.05,.025]:
   r=simulate(profile(hero(base,2)),{next(k for k,v in TRAITS.items() if v in hero(base,2)['jobId'].split('|')):4},('狂徒','板甲','振奋'),dt=dt)
   rows.append(dict(test='步长-'+base,dt=dt,time=r['time'],censored=r['censored']))
 return rows

def run():
 out=ROOT/'results';out.mkdir(exist_ok=True)
 (out/'checks.json').write_text(json.dumps(checks(),ensure_ascii=False,indent=2))
 catalog=[]
 for base in IDS:
  for star in [1,2,3]:
   h=hero(base,star);catalog.append(dict(id=h['id'],name=h['name'],star=star,cost=h['price'],hp=h['initHp'],armor=h['armor'],mr=h['magicResist'],jobs=h['jobId'],skill=h['skillDesc'],skill_values=h['skillValueDesc'],dynamic_supported=h['name'] in SUPPORTED,version=h['version']))
 (out/'champions.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2))
 controlled=[]
 for name,tier,build,scene in itertools.product(TRAITS,[2,4,6],BUILDS,SCENARIOS):
  r=simulate(DUMMY,{name:tier},build,SCENARIOS[scene],skills=False)
  controlled.append(dict(trait=name,tier=tier,build=list(build),scenario=scene,**r))
 (out/'controlled.json').write_text(json.dumps(controlled,ensure_ascii=False))
 native=[]
 for base in IDS:
  for star in [1,2,3]:
   h=hero(base,star)
   if h['name'] not in SUPPORTED:continue
   for name in [k for k,v in TRAITS.items() if v in h['jobId'].split('|')]:
    for tier,build,scene in itertools.product([0,2,4,6],[(),('狂徒','板甲','振奋'),('反甲','龙牙','振奋')],['混合持续','混合重伤33%','开场爆发']):
     r=simulate(profile(h),{name:tier},build,SCENARIOS[scene])
     native.append(dict(hero=h['name'],star=star,cost=h['price'],trait=name,tier=tier,build=list(build),scenario=scene,**r))
 (out/'native.json').write_text(json.dumps(native,ensure_ascii=False))
 sensitivity=[]
 # Explicitly vary one assumption at a time, maintaining same controlled panel/build.
 variants=[('基准',{}),('百分比只放大基础血',{'hp_mode':'base'}),('斗士另加120',{'brawler_flat':True}),('护卫另加12',{'defender_extra':True}),('减伤直接相加',{'dr_mode':'add'}),('真伤也吃减伤',{'true_dr':True}),('护盾减半',{'shield_scale':.5}),('板甲1目标',{'n':1}),('板甲5目标',{'n':5}),('每2秒一大包',{'attack_period':2})]
 for name,tier,scene,(label,opts) in itertools.product(TRAITS,[2,4,6],['混合持续','真伤30%'],variants):
  r=simulate(DUMMY,{name:tier},('狂徒','板甲','振奋'),SCENARIOS[scene],skills=False,**opts)
  sensitivity.append(dict(trait=name,tier=tier,scenario=scene,variant=label,**r))
 for base,period in itertools.product(['11500','11503','12502','14503'],[4,8,12]):
  h=hero(base,2);name=next(k for k,v in TRAITS.items() if v in h['jobId'].split('|'))
  r=simulate(profile(h),{name:4},('狂徒','板甲','振奋'),period=period)
  sensitivity.append(dict(hero=h['name'],variant='施法周期'+str(period),**r))
 for base,first in itertools.product(['11500','11503','12502','14503'],[2,4,6]):
  h=hero(base,2);name=next(k for k,v in TRAITS.items() if v in h['jobId'].split('|'))
  r=simulate(profile(h),{name:4},(),first=first)
  sensitivity.append(dict(hero=h['name'],variant='首施法'+str(first),**r))
 for r in controlled+native+sensitivity:
  assert abs(r['shield_granted']-r['shield_used']-r['shield_expired']-r['shield_remaining'])<.001
 (out/'sensitivity.json').write_text(json.dumps(sensitivity,ensure_ascii=False))
 inputs=[]
 for name,tier,dps,gap,kind in itertools.product(TRAITS,[2,4,6],[150,350,700,1400,2800,5600],[.1,.5,1,2,3],['物理普攻','魔法持续','混合持续','真伤30%','纯真伤']):
  scene=dict(SCENARIOS[kind],dps=dps)
  r=simulate(DUMMY,{name:tier},('狂徒','板甲','振奋'),scene,skills=False,attack_period=gap)
  inputs.append(dict(trait=name,tier=tier,dps=dps,packet=dps*gap,gap=gap,kind=kind,**r))
 (out/'damage_inputs.json').write_text(json.dumps(inputs,ensure_ascii=False))
 meta=dict(damage_inputs=len(inputs),snapshot_file_mtime_utc=datetime.datetime.fromtimestamp((ROOT/'sources/dataj-gamedata.json').stat().st_mtime,datetime.timezone.utc).isoformat(),computed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),url='https://www.dataj.cc/api/web/gamedata?setId=18',sha256=hashlib.sha256((ROOT/'sources/dataj-gamedata.json').read_bytes()).hexdigest(),controlled=len(controlled),native=len(native),sensitivity=len(sensitivity),source_status='Third-party live snapshot. Internal season=S19 conflicts with public S18 label; record version is not a certified patch.',horizon=30,dt=.05)
 (out/'manifest.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2));print(json.dumps(meta,ensure_ascii=False))
if __name__=='__main__':run()
