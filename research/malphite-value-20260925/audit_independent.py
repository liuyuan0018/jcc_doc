"""Independent scalar check of three defensive builds; no engine imports.
Tests implementation consistency under declared assumptions, not in-game mechanics.
"""
import json,csv,subprocess,math
from pathlib import Path
root=Path(__file__).resolve().parents[2];base=root/'exports/frontline-malphite-v1';out=base/'audit-v1';out.mkdir(exist_ok=True)
conditions={(p['sacrifice']['blackthorn'],p['sacrifice']['sacrificeCost'],p['sacrifice']['sacrificeStar']):p['sacrifice']for p in json.loads((base/'manifest.json').read_text())['parts']}
def simulate(e,gear,aug,dps):
 nv=gear.count(24);ng=gear.count(27);nw=gear.count(33)
 H=(2340+e['hp']+300*nv+100*ng+500*nw)*(1+e['hpp']+.18*nw+(.17 if aug and ng else 0))
 resistance=(120+e['armor']+75*ng)*.7
 hp=H;mp=30.;charge=0.;shield=0.;expiry=-1;locked=0;paused=0;casts=0;attacks=0;heals=0.;used=0.;petrified=False
 def gain(v,f):
  nonlocal mp
  if not petrified and f>=locked:mp=min(80.,mp+v)
 def cast(f):
  nonlocal mp,shield,expiry,locked,paused,casts,petrified
  if not petrified and mp>=80-1e-8 and f>=locked:
   casts+=1;mp=0.;shield=850.;expiry=f+120;locked=f+30;paused=f+120;petrified=True
 for f in range(901):
  if petrified and expiry<=f:shield=0.;petrified=False;paused=min(paused,f)
  if f:
   if f>=paused:charge+=.55/30
   while charge>=1-1e-8:charge-=1;attacks+=1;gain(5,f)
   gain(2*nv/30,f)
   if f%30==0:
    heal=.02*nv*(H-hp)*.67;hp+=heal;heals+=heal
  cast(f)
  if f and f%10==0:
   raw=dps/3;post=raw*100/(100+resistance)*(.92**nv);damage=post
   absorbed=min(shield,damage);shield-=absorbed;damage-=absorbed;used+=absorbed;hp-=damage
   if hp<=0:return dict(alive=False,frame=f,H=H,casts=casts,attacks=attacks,hp=hp,heal=heals,used=used)
   if petrified and shield<=1e-8:petrified=False;paused=min(paused,f)
   gain(min(42.5,.01*raw+.03*post),f)
  cast(f)
 return dict(alive=True,frame=900,H=H,casts=casts,attacks=attacks,hp=hp,heal=heals,used=used)
rows=[r for r in csv.DictReader((base/'full-ranking.csv').open())if (tuple(int(r[k])for k in ['item1','item2','item3']),int(r['augment']))in [((24,24,24),0),((24,24,27),4),((24,27,33),0)]]
checks=[]
for row in rows:
 e=conditions[tuple(int(row[k])for k in ['blackthorn','sacrificeCost','sacrificeStar'])];gear=[int(row[k])for k in ['item1','item2','item3']];aug=int(row['augment'])
 for dps in [int(row['score']),int(row['score'])+1]:
  a=simulate(e,gear,aug,dps);args=[row['id'],*gear,aug,e['hp'],e['hpp'],e['armor'],0,dps]
  b=json.loads(subprocess.check_output([str(base/'input/simulate'),'replay'],input=(' '.join(map(str,args))+'\n').encode()))['result'];b['used']=b['shield_used']
  issues={k:[a[k],b.get(k)]for k in ['alive','frame','casts','attacks','H','heal','used']if not math.isclose(a[k],b[k],rel_tol=1e-6,abs_tol=1e-5)}
  checks.append(dict(id=row['id'],dps=dps,issues=issues))
(out/'independent-check.json').write_text(json.dumps(dict(count=len(checks),passed=not any(x['issues']for x in checks),checks=checks),indent=2))
print('CHECKS',len(checks),'MISMATCHES',sum(bool(x['issues'])for x in checks));print([x for x in checks if x['issues']][:3])
