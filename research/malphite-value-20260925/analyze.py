import json,collections,csv
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent;OUT=ROOT/'exports/frontline-malphite-v1';pool=json.loads((HERE/'equipment-pool.json').read_text());manifest=json.loads((OUT/'manifest.json').read_text());rows=[]
for part in manifest['parts']:
 e=part['sacrifice']
 for line in (OUT/'raw'/f'part-{part["part"]:02}.jsonl').open():
  r=json.loads(line);b=int(r['id'].split('-b')[-1]);r.update(pool[b]);r.update(tier=e['blackthorn'],cost=e['sacrificeCost'],star=e['sacrificeStar'],sacrifice=e);rows.append(r)
assert len(rows)==250950 and len({r['id']for r in rows})==250950
counts=collections.Counter(r['score'] for r in rows);rank={};n=1
for score,count in sorted(counts.items(),reverse=True):rank[score]=n;n+=count
rows.sort(key=lambda r:(-r['score'],r['id']))
for r in rows:r['rank']=rank[r['score']]
lookup={(r['tier'],r['cost'],r['star'],tuple(r['items']),r['augment']):r for r in rows}
base=(24,27,33);other=(17,22,27)
choices=[(1,2,base,0),(1,3,base,0),(2,2,base,0),(3,3,base,0),(4,2,base,0),(5,2,base,0),(2,2,other,0),(2,2,base,4)]
main=[]
for tier in [2,4,6]:
 for letter,choice in zip('ABCDEFGH',choices):
  cost,star,gear,aug=choice;r=dict(lookup[tier,cost,star,gear,aug]);r['key']=f'{tier}{letter}';r['label']=letter;main.append(r)
# Include all Main identities, real top eight, then defensive examples spanning all 30 sacrifice conditions.
selected={r['id']:r for r in main}
for r in rows[:8]:selected.setdefault(r['id'],r)
meat={17,22,23,24,26,27,29,30,33}
for tier in [2,4,6]:
 for cost,stars in [(1,[2,3]),(2,[2,3]),(3,[2,3]),(4,[1,2]),(5,[1,2])]:
  for star in stars:
   for aug in [0,4]:
    candidates=[r for r in rows if r['tier']==tier and r['cost']==cost and r['star']==star and r['augment']==aug and all(i in meat for i in r['items'])]
    if candidates:selected.setdefault(candidates[0]['id'],candidates[0])
# Bounded fill with conventional defensive items; maintain unique identities.
for r in rows:
 if len(selected)>=88:break
 if all(i in meat for i in r['items']):selected.setdefault(r['id'],r)
assert len(selected)==88,len(selected)
selected=sorted(selected.values(),key=lambda r:(-r['score'],r['id']))
report={'poolSize':len(rows),'main':main,'selected':selected,'scoreCounts':sorted(counts.items(),reverse=True),'scoring':manifest['scoring'],'top':rows[:8]}
(OUT/'ranking.json').write_text(json.dumps(report,ensure_ascii=False,separators=(',',':')))
with (OUT/'full-ranking.csv').open('w')as f:
 w=csv.writer(f);w.writerow(['id','rank','score','coarsePass','coarseFail','blackthorn','sacrificeCost','sacrificeStar','item1','item2','item3','augment'])
 for r in rows:w.writerow([r['id'],r['rank'],r['score'],r['passedDps'],r['failedDps'],r['tier'],r['cost'],r['star'],*r['items'],r['augment']])
for r in main:print(r['key'],r['cost'],r['star'],r['items'],r['augment'],'score',r['score'],'coarse',r['passedDps'],r['failedDps'],'rank',r['rank'])
print('top',[(r['tier'],r['cost'],r['star'],r['items'],r['augment'],r['score'])for r in rows[:3]])
