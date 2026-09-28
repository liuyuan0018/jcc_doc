"""30 Hz conditional combat model; mechanics assumptions are explicit in report30.md.
Legacy sim.py and results remain available for comparison, not current rankings.
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
ITEM.update({'羊刀':(0,0,0,0,10,0),'大天使':(0,0,0,0,30,1),'泰坦':(0,0,20,0,0,0)})
ROLE_SOURCE=json.loads((P.parent/'sources/datatft-s18.json').read_text())
ROLE={h['displayName']:h['roleKey'] for h in ROLE_SOURCE['heros18']}
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

def sim(h,cfg,dps=1400,trace=False,frequency=3,fps=30,limit=30,hp_rule='all',dr_add=False,post_coef=.03,lock_seconds=1,cast_pause=.3,shield_mana=True,skills=True):
 dt=1/fps
 assert fps%frequency==0
 hit_interval=fps//frequency
 role=ROLE.get(h['name'],'APTank')
 mana_attack=5 if role.endswith('Tank') else 7 if role.endswith('Caster') else 10
 c,stats,z,jug,healthy=cfg
 fixed,bhp,a,m,ap,regen=stats
 H=(h['H']+fixed)*(1+bhp) if hp_rule=='all' else h['H']*(1+bhp)+fixed
 healthfactor=(1+bhp) if hp_rule=='all' else 1
 hp=H;initialH=H;A=h['A']+a;M=h['M']+m
 name=h['name'];v=h['v'];star=h['star'];AS=h['AS'];mp=h['mp']+20*c['圣盾誓约'];cap=h['cap']
 shields=[];hots=[];buffs=[];half=False;vow=False;sterak=False;taric=False;sett=False
 transformed=False;stacks=0;casts=0;lastcast=-999;locked=0;attackcharge=0
 pause_until=0;titan_stacks=0;attacks=0;spider_attacks=0;spider_heal=0.;mana_totals=defaultdict(float);events=[];cast_frames=[];frame=0
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
 def apmult(t):return 1+(ap+(25*c['冕卫'] if t>=8 else 0)+20*c['大天使']*int(t//5)+2*c['泰坦']*titan_stacks)/100
 def gain(value,source,ignore_lock=False):
  nonlocal mp
  if not value:return
  value*=1+.15*c['适应头盔']
  mana_totals['attempt_'+source]+=value
  if frame<locked and not ignore_lock:
   mana_totals['blocked_'+source]+=value;return
  actual=min(value,max(0,cap-mp));mp+=actual
  mana_totals[source]+=actual;mana_totals['overflow']+=value-actual
  if trace:events.append(dict(frame=frame,t=round(frame/fps,4),kind='mana',source=source,amount=round(actual,5),mana=round(mp,5)))
 def addhot(total,dur,t):hots.append((total/dur,t+dur,t))
 def buff(value,end,key):
  buffs[:]=[b for b in buffs if b[2]!=key]
  buffs.append((value,end,key))
 def cast(t):
  nonlocal mp,casts,locked,lastcast,transformed,pause_until,cap
  if not skills:return
  casts+=1;mana_totals['spent']+=mp;mp=0;lastcast=t;cast_frames.append(frame)
  amp=apmult(t);locked=frame+round(lock_seconds*fps);pause_until=frame+round(cast_pause*fps)
  if trace:events.append(dict(frame=frame,t=round(t,4),kind='cast',cast=casts))
  if name in ['奥恩','洛','慎','黛安娜']:
   shield(v[1] * amp if name=='黛安娜' else v[0]*amp,2 if name=='黛安娜' else 4,'skill',t)
  elif name in ['瑟庄妮','苍蓝雕纹魔像']:shield(.1*H+v[0]*amp,4,'skill',t)
  elif name=='可酷伯':addhot(.07*H+v[0]*amp,2,t);locked=frame+2*fps;pause_until=locked
  elif name=='雷克塞':buff(0,t+3,'reksai')
  elif name=='峡谷迅捷蟹':addhot(v[1]*amp,3,t);buff(.15,t+3,'dr');locked=frame+3*fps;pause_until=locked
  elif name=='阿利斯塔':heal(.08*H+v[0]*amp)
  elif name=='伊莉丝':
   if not transformed:transformed=True;growth(v[0]*healthfactor)
   else:buff(1.75,t+4,'elise')
  elif name=='约里克':heal(v[2]*amp)
  elif name=='赫卡里姆':addhot(v[0]*amp,3,t);buff(50,t+3,'resist');locked=frame+3*fps;pause_until=locked
  elif name=='蔚':heal(v[1]*amp);buff(v[2]/100,t+3,'vi');buff(.15,t+3,'dr')
  elif name=='费德提克':addhot(v[0]*amp,2,t);locked=frame+2*fps;pause_until=locked
  elif name=='远古石甲虫':growth(v[1]*amp*healthfactor)
  elif name=='拉莫斯':shield(v[0]*amp,4,'skill',t);buff(60,t+4,'rammus')
  elif name=='莉莉娅':heal(v[0]*amp)
  elif name=='瑟提':heal(.12*H+v[0]*amp)
  elif name=='茂凯':heal(v[3]*amp+(.1 if star<3 else 1)*(H-hp))
  elif skills and name=='塔里克':heal(v[1]*amp)
  elif name=='纳尔' and not transformed:transformed=True;growth(v[2]*healthfactor);cap=50
 if z:shield({2:.18,4:.3,6:.4}[z]*H,10,'vanguard0',0)
 for k in range(c['冕卫']):shield(.25*H,8,'crown'+str(k),0)
 # Equipment start-of-combat mana benefits from amplification. Native initial mana does not.
 mp=h['mp'];initial_mana=mp;gain(20*c['圣盾誓约'],'start',True)
 steps=round(limit*fps)
 for step in range(steps+1):
  frame=step;t=frame/fps
  for sh in shields[:]:
   if sh[1]<=t+1e-8:lost+=sh[0];shields.remove(sh)
   elif step and sh[3]:
    remove=min(sh[0],sh[3]*dt);lost+=remove;sh[0]-=remove
  shields[:]=[x for x in shields if x[0]>1e-8]
  buffs[:]=[b for b in buffs if b[1]>t+1e-8]
  amp=apmult(t)
  if step:
   attackmult=1+(.2 if role.endswith('Fighter') else 0)+c['羊刀']*(.1+.07*int(t))+c['泰坦']*.1
   for val,end,key in buffs:
    if key=='vi':attackmult+=val
    elif key=='elise':attackmult+=val*(end-t)/4
   # Explicit cast animation pause is separate from mana lock.
   if frame>=pause_until:attackcharge+=min(5,AS*attackmult)*dt
   while attackcharge>=1-1e-9:
    attackcharge-=1;attacks+=1
    if c['泰坦']:titan_stacks=min(25,titan_stacks+1)
    if trace:events.append(dict(frame=frame,t=round(t,4),kind='attack',AS=round(min(5,AS*attackmult),4)))
    if skills and name=='蔚':heal(.02*H)
    if skills and name=='伊莉丝' and transformed:
     before=heal_total;heal(v[2]*amp);spider_attacks+=1;spider_heal+=heal_total-before
    gain((20 if star>=3 else 5) if name=='纳尔' else mana_attack,'attack')
   rate=((50 if star>=3 else 5) if name=='纳尔' else (2 if role.endswith('Caster') else 0))+regen
   gain(rate*dt,'regen')
   for rate,end,start in hots:
    if t>start+1e-8 and t<=end+1e-8:heal(rate*dt)
   hots[:]=[x for x in hots if x[1]>t+1e-8]
   if abs(t-round(t))<dt/3:
    if skills and name=='阿木木':heal((.04 if star>=3 else .025)*H+v[0]*amp)
    if skills and name=='雷克塞':heal((.01*H+v[0])*(3 if any(b[2]=='reksai' for b in buffs) else 1))
    for _ in range(c['振奋']):heal(.02*(H-hp))
   if abs(t/2-round(t/2))<dt/6:
    for _ in range(c['龙牙']):heal(.025*H)
   if healthy and c['坚定之心'] and abs(t/10-round(t/10))<dt/30:
    growth(16*c['坚定之心']*healthfactor)
  if skills and mp>=cap-1e-9 and frame>=locked:cast(t)
  if step and step%hit_interval==0:
   ar=A+stacks;mr=M+stacks
   if t<15:ar+=15*c['薄暮'];mr+=15*c['薄暮']
   if skills and name=='蕾欧娜':ar+=v[0]*amp*max(0,1-t/12);mr+=v[0]*amp*max(0,1-t/12)
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
   post_damage=dmg
   for sh in sorted(shields,key=lambda x:x[1]):
    take=min(dmg,sh[0]);sh[0]-=take;dmg-=take;absorbed+=take
   shields[:]=[x for x in shields if x[0]>1e-8]
   hp-=dmg
   if hp<=0:alive=False;death=t
   else:
    if role.endswith('Tank'):gain(min(42.5,.01*raw+post_coef*(post_damage if shield_mana else dmg)),'damage')
    if c['泰坦']:titan_stacks=min(25,titan_stacks+1)
    if c['金霖大亨'] and stacks<35:stacks+=1;growth(5*healthfactor)
    if z and not half and hp<=H*.5:half=True;shield({2:.18,4:.3,6:.4}[z]*H,10,'vanguard1',t)
    if c['圣盾誓约'] and not vow and hp<=H*.4:
     vow=True;gain(15*c['圣盾誓约'],'vow',True)
     for k in range(c['圣盾誓约']):shield(.2*H,limit,'vow'+str(k),t)
    if c['血手'] and not sterak and hp<=H*.6:
     sterak=True
     for k in range(c['血手']):shield(.4*H,4,'sterak'+str(k),t,.4*H/4)
    if skills and name=='塔里克' and not taric and hp<=H*.5:
     taric=True;shield((1 if star>=3 else .15)*H+v[0],99 if star>=3 else 3,'taric',t)
    if skills and name=='瑟提' and not sett and hp<=H*.4:sett=True;gain(100,'sett',True)
  if alive and skills and mp>=cap-1e-9 and frame>=locked:cast(t)
  if trace:rows.append(dict(frame=frame,t=round(t,4),locked=frame<locked,attacks=attacks,spider_attacks=spider_attacks,transformed=transformed,AS=round(min(5,AS*(attackmult if step else 1)),4),hp=round(max(0,hp),2),shield=round(sum(s[0] for s in shields),2),H=round(H,2),mana=round(mp,2),stacks=stacks,casts=casts))
  if not alive:break
 return dict(time=round(death,5),alive=alive,initial_hp=round(initialH,4),final_max_hp=round(H,4),hp_left=round(max(0,hp),4),casts=casts,heal=round(heal_total,4),overheal=round(overheal,4),shield_granted=round(granted,4),shield_used=round(absorbed,4),shield_lost=round(lost,4),shield_left=round(sum(s[0] for s in shields),4),stacks=stacks,half=half,raw_input=round(rawtotal,4),hp_gain=round(hp_gain,4),attacks=attacks,spider_attacks=spider_attacks,spider_heal=round(spider_heal,4),cast_frames=cast_frames,mana=dict(mana_totals),initial_mana=initial_mana,final_mana=mp,events=events,trace=rows)
