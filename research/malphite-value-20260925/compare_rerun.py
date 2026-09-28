"""Compare full newly computed records, then independently reconstruct global and per-condition ranks."""
import csv,json,hashlib,collections,itertools
from pathlib import Path
root=Path(__file__).resolve().parents[2];old=root/'exports/frontline-malphite-v1';new=root/'exports/frontline-malphite-rerun-v1'
m=json.loads((new/'manifest.json').read_text());assert m['status']=='simulated'
pool=json.loads((Path(__file__).parent/'equipment-pool.json').read_text());rows=[];differences=[];count=0;identical=0
for part in m['parts']:
 name=f'part-{part["part"]:02}.jsonl';a=old/'raw'/name;b=new/'raw'/name
 if a.read_bytes()==b.read_bytes():identical+=1
 for la,lb in itertools.zip_longest(a.open(),b.open()):
  assert la is not None and lb is not None
  ra,rb=json.loads(la),json.loads(lb);count+=1
  if ra!=rb:differences.append(dict(old=ra,new=rb))
  e=part['sacrifice'];build=pool[int(rb['id'].split('-b')[-1])];rb.update(build);rb.update(tier=e['blackthorn'],cost=e['sacrificeCost'],star=e['sacrificeStar']);rows.append(rb)
assert count==250950 and len({r['id']for r in rows})==count
counts=collections.Counter(r['score']for r in rows);ranks={};rank=1
for score,n in sorted(counts.items(),reverse=True):ranks[score]=rank;rank+=n
rows.sort(key=lambda r:(-r['score'],r['id']))
with (new/'full-ranking.csv').open('w')as f:
 w=csv.writer(f);w.writerow(['id','rank','score','coarsePass','coarseFail','blackthorn','sacrificeCost','sacrificeStar','item1','item2','item3','augment'])
 for r in rows:w.writerow([r['id'],ranks[r['score']],r['score'],r['passedDps'],r['failedDps'],r['tier'],r['cost'],r['star'],*r['items'],r['augment']])
winners={}
for r in sorted(rows,key=lambda r:(-r['score'],r['augment'],r['id'])):winners.setdefault((r['tier'],r['cost'],r['star']),r)
selected=sorted(winners.values(),key=lambda r:(-r['score'],r['tier'],r['cost'],r['star']))
previous=json.loads((old/'main-four-best-review-v1/selection.json').read_text());same=[r['id']for r in selected]==[r['id']for r in previous]
(new/'best30.json').write_text(json.dumps(selected,ensure_ascii=False,separators=(',',':')))
source_ok=all(hashlib.sha256((new/'input'/n).read_bytes()).hexdigest()==h for n,h in m['sourceHashes'].items());inputs_ok=all(hashlib.sha256((new/'input'/n).read_bytes()).hexdigest()==h for n,h in m['inputHashes'].items())
report=dict(configurations=count,elapsedSeconds=m['elapsedSeconds'],identicalRawParts=identical,changedRecords=len(differences),allFieldsCompared=True,fullRankingCsvIdentical=(new/'full-ranking.csv').read_bytes()==(old/'full-ranking.csv').read_bytes(),best30IdentitiesAndOrderIdentical=same,sourceHashesMatch=source_ok,inputHashesMatch=inputs_ok,reusedRawResults=False,scope='Full rerun under unchanged model assumptions; does not validate in-game mechanics')
(new/'comparison.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
if differences:(new/'differences.json').write_text(json.dumps(differences,ensure_ascii=False))
print(json.dumps(report,ensure_ascii=False,indent=2))
