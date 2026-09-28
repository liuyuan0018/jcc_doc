from pathlib import Path
import json,shutil,hashlib,subprocess,datetime
P=Path.cwd();O=P/'exports/frontline-episode-01-rerun-v4';OLD=P/'exports/frontline-episode-01-rerun-v3';assert Path('/Volumes/Apple').is_mount();assert not (O/'raw').exists();O.mkdir(exist_ok=True);(O/'input').mkdir(exist_ok=True);(O/'tests').mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for n in ['catalog.json','scenarios.json','profiles.json','heroes.json','dataj-gamedata.json']:shutil.copy2(OLD/'input'/n,O/'input'/n)
for n in ['web.cpp','engine-web.hpp','generated.hpp','archive-episode-one.cpp']:shutil.copy2(P/'tank-lab/src'/n,O/'input'/n)
shutil.copy2(OLD/'archive.py',O/'archive.py');shutil.copy2(Path(__file__).with_name('check.cpp'),O/'input/check.cpp')
m=json.loads((OLD/'manifest.json').read_text());m={k:m[k] for k in ['game','setId','statisticsVersion','source','heroCount','scenarioCount','stars','equipment','augments','environment','retention','ranking','scenarios']};m.update(id=O.name,status='preflight',supersedes=str(OLD),producer={'mechanicsRevision':'all-active-skill-shield-lock-20260926'},reusedConfigurations=0,scopeNote='Full legacy pool including Heart augment; additionally publish filtered no-Heart ranking. No prior scores reused.')
(O/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2))
def build(name,source,flags=[]):
 subprocess.run(['clang++','-std=c++17','-O3',*flags,str(source),'-o',str(O/'input'/name)],check=True)
build('check',O/'input/check.cpp');v=subprocess.check_output([str(O/'input/check')]);(O/'tests/skill-shield-mana.json').write_bytes(v);print(v.decode(),flush=True)
for name in ['hecarim-cast','vi-cast','skill-coefficients','wound','mana-resistance','presentation-events']:
 source=O/'tests'/f'{name}.cpp';source.write_text((P/'tank-lab/tests'/f'{name}.cpp').read_text().replace('../src/engine-web.hpp','../input/engine-web.hpp'));build(name,source);r=subprocess.check_output([str(O/'input'/name)]);(O/'tests'/f'{name}.txt').write_bytes(r)
build('archive-episode-one',O/'input/archive-episode-one.cpp',['-pthread','-lz']);build('replay-native',O/'input/web.cpp',['-DNATIVE_TEST'])
m.update(status='running',inputHashes={p.name:sha(p)for p in (O/'input').iterdir()},startedAt=datetime.datetime.now(datetime.timezone.utc).isoformat());(O/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2))
with (O/'execution.jsonl').open('w')as out,(O/'execution-stderr.txt').open('w')as err:subprocess.run([str(O/'input/archive-episode-one'),str(O/'raw'),'6'],stdout=out,stderr=err,check=True)
lines=[json.loads(l)for l in (O/'execution.jsonl').read_text().splitlines()];assert lines[-1]['type']=='complete' and lines[-1]['configurations']==749490;assert len(lines)==85 and sum(x.get('ceilings',0)for x in lines)==0
m.update(status='computed',execution=lines[-1],computedAt=datetime.datetime.now(datetime.timezone.utc).isoformat());(O/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2));print(lines[-1],flush=True)
