"""Conditional single-frontline test. All outputs are model results, not game logs.
python3 sim.py runs 1-3 stars, native defensive traits, defensive triples.
"""
import sys,json,itertools,math,time,hashlib
from pathlib import Path
from collections import Counter,defaultdict
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P.parent))
from model import HEROES,IDS,TRAITS,hero,field
# hp, hp%, armor, mr, ap%, mana/sec
ITEM={
'狂徒':(500,.18,0,0,0,0),'板甲':(100,0,25,25,0,0),'反甲':(0,.06,50,0,0,0),
'龙牙':(0,.06,0,60,0,0),'振奋':(300,0,0,0,0,2),'坚定之心':(250,0,20,0,0,0),
'日炎':(150,.08,20,0,0,0),'圣盾誓约':(0,0,25,25,0,1),'适应头盔':(0,0,30,50,0,3),
'冕卫':(100,0,20,0,20,0),'薄暮':(250,0,0,20,0,0),'离子':(250,0,0,35,15,0),
'血手':(300,0,0,0,0,0),'金霖大亨':(900,0,0,0,0,0)}
NORMAL=[x for x in ITEM if x!='金霖大亨']
PROFILES=[]
for base in IDS:
 for star in [1,2,3]:
  h=hero(base,star)
  vals=[field(h,i) for i in range(len(h['skillBriefValue'].split('|')))]
  PROFILES.append(dict(id=h['id'],name=h['name'],star=star,cost=h['price'],H=h['initHp'],A=h['armor'],M=h['magicResist'],AS=float(h['attackSpeed']),mp=h['initMp'],cap=h['maxMp'],v=vals,jobs=h['jobId'].split('|')))

def trait_options(h):
 native=[k for k,v in TRAITS.items() if v in h['jobs']]
 # Only native defensive membership. Team aura from unrelated professions intentionally disabled.
 out=[]
 for counts in itertools.product([0,2,4,6],repeat=len(native)):
  if not any(counts):continue
  ts={k:v for k,v in zip(native,counts) if v}
  # Rakan is the sole double member among these four. Minimum distinct trait bodies.
  slots=sum(counts)-(1 if len(ts)==2 else 0)
  out.append((ts,slots))
 return out

def prepare(items,traits,healthy=False):
 c=Counter(items);x=[sum(ITEM[i][j] for i in items) for j in range(6)]
 x[1]+={0:0,2:.25,4:.4,6:.65}[traits.get('斗士',0)]
 res={0:0,2:25,4:60,6:120}[traits.get('护卫',0)]
 x[2]+=res+30*c['板甲'];x[3]+=res+30*c['板甲']
 return (c,x,traits.get('重装',0),{0:0,2:.2,4:.33,6:.45}[traits.get('主宰',0)],healthy)

def sim(h,cfg,dps=1400,mana_base=20,trace=False,frequency=3,dt=1/60,limit=30,hp_rule='all',dr_add=False):
 c,stats,z,jug,healthy=cfg
 fixed,bhp,a,m,ap,regen=stats
 H=(h['H']+fixed)*(1+bhp) if hp_rule=='all' else h['H']*(1+bhp)+fixed
 healthfactor=(1+bhp) if hp_rule=='all' else 1
 hp=H;initialH=H;A=h['A']+a;M=h['M']+m
 name=h['name'];v=h['v'];star=h['star'];AS=h['AS'];mp=h['mp']+20*c['圣盾誓约'];cap=h['cap']
 shields=[];hots=[];buffs=[];half=False;vow=False;sterak=False;taric=False;sett=False
 transformed=False;stacks=0;casts=0;lastcast=-999;locked=0;attackcharge=0
 granted=absorbed=lost=heal_total=overheal=rawtotal=hp_gain=0.;next_hit=1/frequency
 rows=[];death=limit;alive=True
 # shield [amount,expiry,tag,decay/sec]; same skill refreshes, equipment copies are separate tags.
 def shield(value,dur,tag,t,decay=0):
  nonlocal granted,lost
  for old in shields[:]:
   if old[2]==tag:lost+=old[0];shields.remove(old)
  shields.append([value,t+dur,tag,decay]);granted+=value
 def heal(value):
  nonlocal hp,heal_total,overheal
  take=max(0,min(H-hp,value));hp+=take;heal_total+=take;overheal+=value-take
 def growth(value):
  nonlocal H,hp,hp_gain
  H+=value;hp+=value;hp_gain+=value
 def apmult(t):return 1+(ap+(25*c['冕卫'] if t>=8 else 0))/100
 def addhot(total,dur,t):hots.append((total/dur,t+dur,t))
 def buff(value,end,key):
  buffs[:]=[b for b in buffs if b[2]!=key]
  buffs.append((value,end,key))
 def cast(t):
  nonlocal mp,casts,locked,lastcast,transformed
  casts+=1;mp=0;lastcast=t
  amp=apmult(t);locked=t+1
  if name in ['奥恩','洛','慎','黛安娜']:
   shield(v[1] * amp if name=='黛安娜' else v[0]*amp,2 if name=='黛安娜' else 4,'skill',t)
  elif name in ['瑟庄妮','苍蓝雕纹魔像']:shield(.1*H+v[0]*amp,4,'skill',t)
  elif name=='可酷伯':addhot(.07*H+v[0]*amp,2,t);locked=t+2
  elif name=='雷克塞':buff(0,t+3,'reksai')
  elif name=='峡谷迅捷蟹':addhot(v[1]*amp,3,t);buff(.15,t+3,'dr');locked=t+3
  elif name=='阿利斯塔':heal(.08*H+v[0]*amp)
  elif name=='伊莉丝':
   if not transformed:transformed=True;growth(v[0]*healthfactor)
   else:buff(1.75,t+4,'elise')
  elif name=='约里克':heal(v[2]*amp)
  elif name=='赫卡里姆':addhot(v[0]*amp,3,t);buff(50,t+3,'resist');locked=t+3
  elif name=='蔚':heal(v[1]*amp);buff(v[2]/100,t+3,'vi');buff(.15,t+3,'dr')
  elif name=='费德提克':addhot(v[0]*amp,2,t);locked=t+2
  elif name=='远古石甲虫':growth(v[1]*amp*healthfactor)
  elif name=='拉莫斯':shield(v[0]*amp,4,'skill',t);buff(60,t+4,'rammus')
  elif name=='莉莉娅':heal(v[0]*amp)
  elif name=='瑟提':heal(.12*H+v[0]*amp)
  elif name=='茂凯':heal(v[3]*amp+(.1 if star<3 else 1)*(H-hp))
  elif name=='塔里克':heal(v[1]*amp)
  elif name=='纳尔' and not transformed:transformed=True;growth(v[2]*healthfactor)
 if z:shield({2:.18,4:.3,6:.4}[z]*H,10,'vanguard0',0)
 for k in range(c['冕卫']):shield(.25*H,8,'crown'+str(k),0)
 steps=round(limit/dt)
 for step in range(steps+1):
  t=step*dt
  for sh in shields[:]:
   if sh[1]<=t+1e-8:lost+=sh[0];shields.remove(sh)
   elif step and sh[3]:
    remove=min(sh[0],sh[3]*dt);lost+=remove;sh[0]-=remove
  shields[:]=[x for x in shields if x[0]>1e-8]
  buffs[:]=[b for b in buffs if b[1]>t+1e-8]
  amp=apmult(t)
  if step:
   attackmult=1
   for val,end,key in buffs:
    if key=='vi':attackmult+=val
    elif key=='elise':attackmult+=val*(end-t)/4
   # Self attacks continue except while channeling; a one-second standard cast lock stops mana, not attacks.
   channel=name in ['可酷伯','峡谷迅捷蟹','赫卡里姆','费德提克'] and t<locked
   if not channel:attackcharge+=AS*attackmult*dt
   while attackcharge>=1-1e-9:
    attackcharge-=1
    if name=='蔚':heal(.02*H)
    if name=='伊莉丝' and transformed:heal(v[2]*amp)
    if name=='纳尔' and t+1e-9>=locked:mp+=(20 if star>=3 else 5)
   if t+1e-9>=locked:
    rate=((50 if star>=3 else 5) if name=='纳尔' else mana_base)+regen
    mp+=rate*dt*(1+.15*c['适应头盔'])
   for rate,end,start in hots:
    if t>start+1e-8 and t<=end+1e-8:heal(rate*dt)
   hots[:]=[x for x in hots if x[1]>t+1e-8]
   if abs(t-round(t))<dt/3:
    if name=='阿木木':heal((.04 if star>=3 else .025)*H+v[0]*amp)
    if name=='雷克塞':heal((.01*H+v[0])*(3 if any(b[2]=='reksai' for b in buffs) else 1))
    for _ in range(c['振奋']):heal(.02*(H-hp))
   if abs(t/2-round(t/2))<dt/6:
    for _ in range(c['龙牙']):heal(.025*H)
   if healthy and c['坚定之心'] and abs(t/10-round(t/10))<dt/30:
    growth(16*c['坚定之心']*healthfactor)
  if mp>=cap-1e-9 and t+1e-9>=locked:cast(t)
  if step and t+1e-8>=next_hit:
   next_hit+=1/frequency
   ar=A+stacks;mr=M+stacks
   if t<15:ar+=15*c['薄暮'];mr+=15*c['薄暮']
   if name=='蕾欧娜':ar+=v[0]*amp*max(0,1-t/12);mr+=v[0]*amp*max(0,1-t/12)
   for val,end,key in buffs:
    if key=='resist' or key=='rammus' and any(s[2]=='skill' for s in shields):ar+=val;mr+=val
   rates=[jug]+[.08]*c['振奋']+[.15 if hp>H*.5 else .05]*c['坚定之心']
   if c['金霖大亨']:rates.append(.15)
   if z==6 and shields:rates.append(.05)
   rates.extend(b[0] for b in buffs if b[2]=='dr')
   mul=max(.01,1-sum(rates)) if dr_add else math.prod(1-r for r in rates)
   raw=dps/frequency;rawtotal+=raw
   # Each source emits one half-physical-attack, half-magic packet. Exactly 3 packets/s by default.
   dmg=raw*.5*(.95**c['反甲']*100/(100+ar)+100/(100+mr))*mul
   for sh in sorted(shields,key=lambda x:x[1]):
    take=min(dmg,sh[0]);sh[0]-=take;dmg-=take;absorbed+=take
   shields[:]=[x for x in shields if x[0]>1e-8]
   hp-=dmg
   if hp<=0:alive=False;death=t
   else:
    if c['金霖大亨'] and stacks<35:stacks+=1;growth(5*healthfactor)
    if z and not half and hp<=H*.5:half=True;shield({2:.18,4:.3,6:.4}[z]*H,10,'vanguard1',t)
    if c['圣盾誓约'] and not vow and hp<=H*.4:
     vow=True;mp+=15*c['圣盾誓约']
     for k in range(c['圣盾誓约']):shield(.2*H,limit,'vow'+str(k),t)
    if c['血手'] and not sterak and hp<=H*.6:
     sterak=True
     for k in range(c['血手']):shield(.4*H,4,'sterak'+str(k),t,.4*H/4)
    if name=='塔里克' and not taric and hp<=H*.5:
     taric=True;shield((1 if star>=3 else .15)*H+v[0],99 if star>=3 else 3,'taric',t)
    if name=='瑟提' and not sett and hp<=H*.4:sett=True;mp+=100
  if trace and (step%max(1,round(.5/dt))==0 or not alive):rows.append(dict(t=round(t,4),hp=round(max(0,hp),2),shield=round(sum(s[0] for s in shields),2),H=round(H,2),mana=round(mp,2),stacks=stacks,casts=casts))
  if not alive:break
 return dict(time=round(death,5),alive=alive,initial_hp=round(initialH,4),final_max_hp=round(H,4),hp_left=round(max(0,hp),4),casts=casts,heal=round(heal_total,4),overheal=round(overheal,4),shield_granted=round(granted,4),shield_used=round(absorbed,4),shield_lost=round(lost,4),shield_left=round(sum(s[0] for s in shields),4),stacks=stacks,half=half,raw_input=round(rawtotal,4),hp_gain=round(hp_gain,4),trace=rows)

def score(r):
 # Do not fabricate survival ordering beyond the horizon: remainder is only a secondary inventory.
 return (r['time'],r['hp_left']+r['shield_left'])

def check():
 # Independent constant-defense analytical comparison on discrete 1/3-second packets.
 d=dict(PROFILES[0],name='dummy',mp=0,cap=10**9,H=1800,A=50,M=50,AS=0)
 for name,t in [('护卫',4),('主宰',4),('斗士',4),('重装',4)]:
  cfg=prepare((),{name:t});r=sim(d,cfg,dps=3000)
  E={'护卫':3780,'主宰':2700/.67,'斗士':3780,'重装':4320}[name]
  assert abs(r['time']-E/3000)<=1/3+1e-4,(name,r)
 r=sim(d,prepare(('金霖大亨',),{}),dps=50,trace=True)
 assert r['stacks']==35 and r['alive']
 assert abs(r['final_max_hp']-2875)<1e-5
 base=sim(d,prepare(('坚定之心',),{}),dps=50)
 healthy=sim(d,prepare(('坚定之心',),{},True),dps=50)
 assert abs(healthy['final_max_hp']-base['final_max_hp']-48)<1e-5
 # Fatal packet must not gain a survival stack or shield after death.
 r=sim(d,prepare(('金霖大亨',),{'重装':4}),dps=100000)
 assert not r['alive'] and not r['half'] and r['stacks']==0
 return dict(status='passed',checks=['4 analytic/discrete bounds','35 stack cap and +175 life','healthy gains 3x16 over30s','lethal packet cannot trigger survival effects'])

def run(mana=20):
 R=P if mana==20 else P/f"mana-{mana:g}"
 R.mkdir(exist_ok=True)
 start=time.time();checkdata=check();(R/'checks.json').write_text(json.dumps(checkdata,ensure_ascii=False,indent=2))
 normal=list(itertools.combinations_with_replacement(NORMAL,3))
 gold=[x+('金霖大亨',) for x in itertools.combinations_with_replacement(NORMAL,2)]
 best=defaultdict(list);count=0
 # Persist best triple for each hero, star, trait configuration, and augment lane.
 records=[]
 with (R/'all_results.jsonl').open('w') as out:
  for h in PROFILES:
   for ts,slots in trait_options(h):
    for lane,pool,healthy in [('普通',normal,False),('心之钢',normal,True),('金霖龙',gold,False),('双海克斯',gold,True)]:
     if slots+(1 if '金霖' in lane or lane=='双海克斯' else 0)>9:continue
     winner=None;ties=0
     for items in pool:
      if healthy and '坚定之心' not in items:continue
      cfg=prepare(items,ts,healthy);r=sim(h,cfg,mana_base=mana)
      assert abs(r['shield_granted']-r['shield_used']-r['shield_lost']-r['shield_left'])<.001
      row=dict(id=h['id'],hero=h['name'],star=h['star'],cost=h['cost'],traits=ts,items=items,lane=lane,minimum_slots=slots+(bool(cfg[0]['金霖大亨'])),**r)
      row.pop('trace');out.write(json.dumps(row,ensure_ascii=False)+'\n');count+=1
      if winner is None or score(row)>score(winner):winner=row
     if winner:records.append(winner)
   print(h['name'],h['star'],'done',count,'elapsed',round(time.time()-start),flush=True)
 (R/'best_per_hero_trait.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
 meta=dict(runs=count,elapsed=round(time.time()-start,1),normal_items=len(NORMAL),normal_triples=len(normal),gold_triples=len(gold),dps=1400,sources=3,frequency=3,mana_base=mana,limit=30,dt=1/60,hp_rule='all',budget=9,source_sha256=hashlib.sha256((P.parent/'sources/dataj-gamedata.json').read_bytes()).hexdigest())
 (R/'manifest.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2));print(meta)
if __name__=='__main__':run(float(sys.argv[1]) if len(sys.argv)>1 else 20)
