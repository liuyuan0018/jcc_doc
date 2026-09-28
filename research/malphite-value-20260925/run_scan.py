import concurrent.futures,json,subprocess,time,os,hashlib,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,default=ROOT/'exports/frontline-malphite-v1');args=parser.parse_args();OUT=args.out.resolve();START=time.monotonic()
manifest=json.loads((OUT/'manifest.json').read_text());(OUT/'raw').mkdir(exist_ok=True)
def one(p):
 n=p['part'];dest=OUT/'raw'/f'part-{n:02}.jsonl';tmp=dest.with_suffix('.partial')
 if dest.exists():return n,'reused'
 with (OUT/'input'/f'part-{n:02}.txt').open()as fi,tmp.open('w')as fo:subprocess.run([str(OUT/'input/simulate')],stdin=fi,stdout=fo,check=True)
 count=0
 with tmp.open()as f:
  for line in f:
   v=json.loads(line);count+=1
   if v['failedDps']<0 or v['refinedFail']<0:raise RuntimeError('Ceiling reached: '+v['id'])
 if count!=p['count']:raise RuntimeError('Incomplete part')
 tmp.rename(dest);return n,count
with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:
 for done,f in enumerate(concurrent.futures.as_completed([pool.submit(one,p)for p in manifest['parts']]),1):
  n,count=f.result();print(f'part {n:02} complete {count}; {done}/30; elapsed {time.monotonic()-START:.1f}s',flush=True)
  (OUT/'scan-progress.json').write_text(json.dumps({'completedParts':done,'totalParts':30,'elapsedSeconds':time.monotonic()-START}))
for name,h in manifest['sourceHashes'].items():assert hashlib.sha256((OUT/'input'/name).read_bytes()).hexdigest()==h
manifest.update(status='simulated',elapsedSeconds=time.monotonic()-START);(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
print('ALL COMPLETE',flush=True)
