import json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parent
old=json.loads((P.parent/'expanded/results.json').read_text());new=json.loads((P/'results.json').read_text())
bykey=lambda r:(r['scenario'],r['aug'],r['category'])
oldkeys={bykey(r):r for r in old}
for r in new:
 o=oldkeys[bykey(r)];assert r['runs']==o['runs'] and r['survivors']<=o['survivors']
 if not o['result']['alive']:assert o['items']==r['items'] and o['result']==r['result']
def best(rows):
 out={}
 for r in rows:
  if r['aug'] or r['category']>2:continue
  k=(r['hero'],r['star'],r['category'])
  score=lambda q:(q['result']['frame'],q['result']['hp']+q['result']['shield'])
  if k not in out or score(r)>score(out[k]):out[k]=r
 return out
ob=best(old);nb=best(new);rows=[]
for k,o in ob.items():
 q=json.loads(subprocess.check_output([str(P/'engine'),'one',str(o['scenario']),*[str(i) for i in o['items']],'0'],text=True))
 rows.append(dict(hero=k[0],star=k[1],category=k[2],old=o,old_extended=q,new=nb[k]))
(P/'comparison.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
print('Monotonic survival counts verified for',len(new),'summary rows; continued',len(rows),'old choices.')
