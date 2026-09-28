from pathlib import Path
import json,gzip,subprocess,shutil,hashlib,sys,concurrent.futures,time,collections
R=Path('/Users/lyu/Documents/ChatGPT/金铲铲');A=R/'exports/frontline-episode-01-rerun-v5';O=R/'exports/ornn-recomputed-20260928';S=Path('/Users/lyu/Documents/project/game/projects/jcc/tank-lab/src');assert Path('/Volumes/Apple').is_mount();O.mkdir(exist_ok=True);(O/'input').mkdir(exist_ok=True)
sys.path.insert(0,str(A));import archive as a
for n in ['web.cpp','engine-web.hpp','generated.hpp']:shutil.copy2(S/n,O/'input'/n)
for n in ['catalog.json','scenarios.json','profiles.json']:shutil.copy2(A/'input'/n,O/'input'/n)
src=(R/'research/warden-best-20260926-v2/scan.cpp').read_text().replace('int d=300;','int d=50;').replace('max(300,pass+1)','max(50,pass+1)');(O/'input/scan.cpp').write_text(src)
subprocess.run(['clang++','-std=c++17','-O3','-I',str(O/'input'),str(O/'input/scan.cpp'),'-o',str(O/'input/scan')],check=True)
subprocess.run(['clang++','-std=c++17','-O3','-DNATIVE_TEST',str(O/'input/web.cpp'),'-o',str(O/'input/replay-native')],check=True)
hashes={n:hashlib.sha256((S/n).read_bytes()).hexdigest()for n in ['web.cpp','engine-web.hpp','generated.hpp']}
def run(sc):
 meta=[json.loads(l)for l in gzip.open(A/f'raw/scenario-{sc}.summary.jsonl.gz','rt')];meta=[r for r in meta if r['augment']in[0,4]];assert len(meta)==8400
 feed=''.join(' '.join(map(str,[r['id'],*a.parameters(r,50)]))+'\n'for r in meta);(O/f's{sc}-input.txt').write_text(feed)
 t=time.monotonic();p=subprocess.run([str(O/'input/scan')],input=feed,text=True,capture_output=True,check=True);(O/f's{sc}-runs.jsonl').write_text(p.stdout);fresh={r['id']:r for r in map(json.loads,p.stdout.splitlines())};assert len(fresh)==8400
 for r in meta:r.update(fresh[r['id']]);r.update(a.description(r));r['refinedDps']=r['score'];assert r['failedDps']>0
 meta.sort(key=lambda r:(-r['score'],r['id']));counts=collections.Counter(r['score']for r in meta);ranks={};n=1
 for score,c in sorted(counts.items(),reverse=True):ranks[score]=n;n+=c
 for r in meta:r['rank']=ranks[r['score']]
 (O/f's{sc}-ranking.json').write_text(json.dumps(meta,ensure_ascii=False));print(sc,round(time.monotonic()-t,2),[(r['itemNames'],r['augmentName'],r['score'])for r in meta[:2]],flush=True)
 return dict(scenario=sc,configurations=len(meta),stages=sum(len(r['stages'])+len(r['refinement'])for r in meta),seconds=time.monotonic()-t)
with concurrent.futures.ThreadPoolExecutor(max_workers=2)as ex:results=list(ex.map(run,[6,8]))
for n,h in hashes.items():assert hashlib.sha256((S/n).read_bytes()).hexdigest()==h
(O/'manifest.json').write_text(json.dumps(dict(sourceHashes=hashes,scenarios=results,rule='50 +50 until first failure, refine last interval +1 until first failure',excludedAugments=['心之钢'],targetHits=3,targetRes=50),ensure_ascii=False,indent=2))
