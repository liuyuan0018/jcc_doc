from pathlib import Path
import json,shutil,hashlib,subprocess,datetime
ROOT=Path('/Users/lyu/Documents/ChatGPT/金铲铲');OLD=ROOT/'exports/frontline-episode-01-rerun-v5';O=ROOT/'exports/frontline-episode-02-v1';S=ROOT/'tank-lab/src'
assert Path('/Volumes/Apple').is_mount();assert not (O/'raw').exists();O.mkdir(exist_ok=True);(O/'input').mkdir(exist_ok=True)
subprocess.run(['python3',str(S/'prepare_engine.py'),'--check'],check=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name in ['catalog.json','scenarios.json','profiles.json','heroes.json','dataj-gamedata.json']:shutil.copy2(OLD/'input'/name,O/'input'/name)
for name in ['web.cpp','engine-web.hpp','generated.hpp']:shutil.copy2(S/name,O/'input'/name)
s=(S/'archive-episode-one.cpp').read_text().replace('// Exhaustive episode-one archive:','// Exhaustive episode-two archive:')
start=s.index('  for(int i=0;');end=s.index('  vector<int> cases;',start)
s=s[:start]+'''  for(int i=0;i<int(ITEMS.size());i++)if(ITEMS[i].cat==0&&ITEMS[i].kind>=0)
   for(int j=i;j<int(ITEMS.size());j++)if(ITEMS[j].cat==0&&ITEMS[j].kind>=0)
    for(int k=0;k<int(ITEMS.size());k++)if(ITEMS[k].cat==2&&ITEMS[k].kind>=0&&ITEMS[k].kind!=SEEKER&&legal({i,j,k}))builds.push_back(makeBuild({i,j,k}));
'''+s[end:]
s=s.replace('aug:{0,1,4}','aug:{0,4}').replace('||(aug==1&&b.c[STEADFAST][0])','')
(O/'input/archive-episode-two.cpp').write_text(s)
m=json.loads((OLD/'manifest.json').read_text());m={k:m[k]for k in ['game','setId','statisticsVersion','source','heroCount','scenarioCount','stars','environment','retention','ranking','scenarios']}
m.update(id=O.name,status='preparing',equipment='Exactly 2 ordinary + 1 artifact; exclude Seekers Armguard (30021); no radiant/potion/glove envelope',excludedItems=[dict(id=30021,name='探索者的护臂',reason='Participation-in-kill scaling excluded at user request')],augments=[dict(mask=0,name='无指定海克斯'),dict(mask=4,name='单身板甲',requires='Normal Gargoyle')],expectedConfigurations=1655850,producer=dict(engineSha256=sha(S/'engine-web.hpp')),scope='Fixed-condition hero comparison; existing artifact model assumptions retained, no kills for on-kill effects')
(O/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2))
for target,src,flags in [('archive-episode-two','archive-episode-two.cpp',['-pthread','-lz']),('replay-native','web.cpp',['-DNATIVE_TEST'])]:
 subprocess.run(['clang++','-std=c++17','-O3',*flags,str(O/'input'/src),'-o',str(O/'input'/target)],check=True)
m.update(status='running',inputHashes={p.name:sha(p)for p in (O/'input').iterdir()},startedAt=datetime.datetime.now(datetime.timezone.utc).isoformat());(O/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2))
with (O/'execution.jsonl').open('w')as out,(O/'execution-stderr.txt').open('w')as err:subprocess.run([str(O/'input/archive-episode-two'),str(O/'raw'),'6'],stdout=out,stderr=err,check=True)
lines=[json.loads(x)for x in (O/'execution.jsonl').read_text().splitlines()];assert lines[-1]['type']=='complete' and lines[-1]['configurations']==1655850
assert sha(S/'engine-web.hpp')==m['producer']['engineSha256']
m.update(status='computed',execution=lines[-1],ceilingConfigurations=sum(x.get('ceilings',0)for x in lines),computedAt=datetime.datetime.now(datetime.timezone.utc).isoformat());(O/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2));print(json.dumps(m['execution']),flush=True)
