import json,hashlib,subprocess,sys,time
from pathlib import Path
ROOT=Path('/Users/lyu/Documents/ChatGPT/金铲铲');OUT=Path(__file__).parent.resolve();SRC=ROOT/'research/vi-vow-topic-20260923/vow-shield-revision-v1/input'
sys.path.insert(0,str(ROOT/'exports/frontline-episode-01-rerun-v3'));import archive
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=ROOT/'research/rammus-results64-20260925/ranking.json';data=json.loads(source.read_text());rows=data['all'];assert len(rows)==8365
files=[SRC/n for n in ['web.cpp','engine-web.hpp','generated.hpp','replay-native']];hashes={str(p):sha(p) for p in files};assert hashes[str(SRC/'replay-native')]==data['hashes']['revisedReplay']
(OUT/'input.txt').write_text('\n'.join(' '.join(map(str,[r['id'],*archive.parameters(r,300)])) for r in rows)+'\n')
manifest=dict(status='running',lower=300,upper=2500,step=1,configurations=8365,threads=4,criterion='maximum tested passing DPS, do not stop on failure',sourceHashes=hashes,inputRankingSha256=sha(source))
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2))
subprocess.run(['clang++','-std=c++17','-O3','-pthread','-I',str(SRC),str(OUT/'scan.cpp'),'-lz','-o',str(OUT/'scan')],check=True)
start=time.monotonic()
subprocess.run([str(OUT/'scan'),str(OUT/'raw'),'300','2500','4'],stdin=(OUT/'input.txt').open(),check=True)
assert hashes=={str(p):sha(p) for p in files}
result=[json.loads(s) for p in sorted((OUT/'raw').glob('*.jsonl')) for s in p.read_text().splitlines()];assert len(result)==len({r['id'] for r in result})==8365
manifest.update(status='computed_pending_validation',elapsedSeconds=time.monotonic()-start,totalStages=8365*2201,ceilingConfigurations=[r['id'] for r in result if r['atCeiling']],nonmonotonicConfigurations=sum(r['reversals']>0 for r in result),binarySha256=sha(OUT/'scan'))
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(manifest),flush=True)
