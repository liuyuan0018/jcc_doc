from pathlib import Path
import hashlib,json,gzip
P=Path(__file__).resolve().parents[2];R=Path(__file__).resolve().parent;old=P/'exports/frontline-episode-01-rerun-v4/raw';new=P/'exports/combat-buff-refactor-20260926/raw-final'
sha=lambda b:hashlib.sha256(b).hexdigest()
a={p.name:p for p in old.glob('*.gz')};b={p.name:p for p in new.glob('*.gz')};assert a.keys()==b.keys() and len(a)==166
records=[]
for name in sorted(a):
 h1=sha(a[name].read_bytes());h2=sha(b[name].read_bytes())
 if h1!=h2:
  with gzip.open(a[name],'rb')as f:raw1=f.read()
  with gzip.open(b[name],'rb')as f:raw2=f.read()
  assert raw1==raw2,name
 records.append(dict(file=name,baselineSha256=h1,refactoredSha256=h2,exact=True))
e=json.loads((R/'batch-execution.jsonl').read_text().splitlines()[-1]);assert e['type']=='complete' and e['configurations']==749490 and e['stageRuns']==3196989
x=dict(passed=True,configurations=e['configurations'],battles=e['stageRuns'],elapsedSeconds=e['elapsedSeconds'],allSummaryAndStageResultsExact=True,files=records,sourceHashes={p.name:sha(p.read_bytes())for p in (P/'tank-lab/src/combat').iterdir()if p.suffix in ['.hpp','.inc']},engineHash=sha((P/'tank-lab/src/engine-web.hpp').read_bytes()))
(R/'batch-verification.json').write_text(json.dumps(x,indent=2));print({k:v for k,v in x.items()if k not in ['files','sourceHashes']})
