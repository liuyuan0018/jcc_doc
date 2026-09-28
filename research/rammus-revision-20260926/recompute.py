from pathlib import Path
import json,gzip,sys,subprocess,hashlib,time
R=Path('/Users/lyu/Documents/ChatGPT/金铲铲');D=Path(__file__).resolve().parent;A=R/'exports/frontline-episode-01-rerun-v5';O=R/'exports/frontline-rammus-recomputed-v9';O.mkdir(exist_ok=True)
sys.path.insert(0,str(A));import archive
rows=[json.loads(x)for x in gzip.open(A/'raw/scenario-185.summary.jsonl.gz','rt')];rows=[r for r in rows if r['augment']in[0,4]];assert len(rows)==8400
src=(R/'research/rammus-rank-integer-20260925/scan.cpp').read_text().replace('for(int d=lower;d<=upper;d++){','int begin=int(job.p[6]); int limit=begin+50;\n   for(int d=begin;d<=limit;d++){').replace('stages.append(line,len);','stages.append(line,len); if(!r.alive)break;')
(D/'scan.cpp').write_text(src)
(O/'input.txt').write_text('\n'.join(' '.join(map(str,[r['id'],*archive.parameters(r,max(300,r['passedDps']))]))for r in rows)+'\n')
subprocess.run(['clang++','-std=c++17','-O3','-pthread','-I',str(A/'input'),str(D/'scan.cpp'),'-lz','-o',str(D/'scan')],check=True)
t=time.monotonic();subprocess.run([str(D/'scan'),str(O/'raw'),'300','1400','4'],stdin=(O/'input.txt').open(),check=True)
fine={r['id']:r for p in (O/'raw').glob('*.jsonl') for r in map(json.loads,p.read_text().splitlines())};assert len(fine)==8400
for r in rows:r.update(refinedDps=fine[r['id']]['highestPass']);r.update(archive.description(r))
rows.sort(key=lambda r:(-r['refinedDps'],r['id']))
for r in rows:r['rank']=1+sum(x['refinedDps']>r['refinedDps']for x in rows)
(O/'ranking.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
manifest=dict(configurations=len(rows),elapsedSeconds=time.monotonic()-t,source=str(A),engineSha256=hashlib.sha256((A/'input/engine-web.hpp').read_bytes()).hexdigest(),rule='300 +50 to first failure, then ascending +1 from last passing stage to first failure; no binary search',fineStageRuns=sum(1 for p in (O/'raw').glob('*.csv.gz')for l in gzip.open(p,'rt'))-4)
(O/'manifest.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(manifest));print(json.dumps(rows[:8],ensure_ascii=False))
