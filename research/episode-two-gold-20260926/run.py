from pathlib import Path
import json,shutil,subprocess,hashlib,importlib.util,collections
R=Path('/Users/lyu/Documents/ChatGPT/金铲铲');old=R/'exports/frontline-episode-02-v1';p=R/'exports/frontline-episode-02-v2';p.mkdir(exist_ok=True);assert not (p/'raw').exists();shutil.copytree(old/'input',p/'input',dirs_exist_ok=True)
s=(old/'input/archive-episode-two.cpp').read_text().replace('auto eligible=[](const Build& b,int aug){return aug==0||(aug==4&&b.c[GARGOYLE][0]);};','auto eligible=[](const Build& b,int aug){return aug==2&&b.n(MOGUL);};').replace('aug:{0,4}','aug:{2}').replace('if(h.star==(h.cost<=3?3:2))cases.push_back(i);','if(h.star==(h.cost<=3?3:2)&&SCENARIOS[i].slots<9)cases.push_back(i);')
assert 'aug:{0,4}'not in s and 'aug==2&&b.n(MOGUL)' in s
(p/'input/archive-gold.cpp').write_text(s)
subprocess.run(['clang++','-std=c++17','-O3','-pthread','-lz',str(p/'input/archive-gold.cpp'),'-o',str(p/'input/archive-gold')],check=True)
with (p/'gold-execution.jsonl').open('w')as f:subprocess.run([str(p/'input/archive-gold'),str(p/'gold-raw'),'6'],stdout=f,check=True)
events=[json.loads(l)for l in (p/'gold-execution.jsonl').read_text().splitlines()];assert events[-1]['type']=='complete' and not sum(e.get('ceilings',0)for e in events)
(p/'raw').mkdir()
for src in (old/'raw').glob('*.gz'):
 supplement=p/'gold-raw'/src.name
 with (p/'raw'/src.name).open('wb')as out:
  with src.open('rb')as f:shutil.copyfileobj(f,out)
  if supplement.exists():
   with supplement.open('rb')as f:shutil.copyfileobj(f,out)
m=json.loads((old/'manifest.json').read_text());m.update(id=p.name,status='computed',supersedes=str(old),reusedConfigurations=m['execution']['configurations'],supplementExecution=events[-1]);m['execution']={'configurations':m['reusedConfigurations']+events[-1]['configurations'],'stageRuns':m['execution']['stageRuns']+events[-1]['stageRuns']};m['expectedConfigurations']=m['execution']['configurations'];m['augments'].append(dict(mask=2,name='金霖龙',datajId='20651',requires='Moguls Mail and one extra slot; scenario slots < 9',hp=600,damageReduction=.15));m['inputHashes']={f.name:hashlib.sha256(f.read_bytes()).hexdigest()for f in (p/'input').iterdir()};(p/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2))
s=(old/'archive.py').read_text().replace('-a[014]','-a[0124]').replace("4: '单身板甲'","4: '单身板甲', 2: '金霖龙'").replace("traits=sc['traits'], slots=sc['slots'],","traits=sc['traits'], slots=sc['slots'] + int(row['augment']==2),")
# The appended gzip member stores new gold-only rows after the retained original rows.
a=s.index('    expected =',s.index('def verify_scenario'));b=s.index('    raw_path =',a)
s=s[:a]+'''    base = [(f's{sn}-b{bi}-a{aug}',list(t),aug)for bi,t in enumerate(triples)for aug in [0,4]if aug==0 or gargoyle in t]
    mogul = next(i['index']for i in ITEMS if i['name']=='大亨之铠')
    gold = [(f's{sn}-b{bi}-a2',list(t),2)for bi,t in enumerate(triples)if mogul in t and SCENARIOS[sn]['slots']<9]
    expected = iter(base+gold)
'''+s[b:]
(p/'archive.py').write_text(s)
spec=importlib.util.spec_from_file_location('ep2gold',p/'archive.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a);a.summarize()
x=json.loads((p/'ranking.json').read_text());before={r['hero']:r for r in json.loads((old/'ranking.json').read_text())['leaderboard']}
checks=[]
for r in x['leaderboard']:
 if r['augment']==2:
  for d in [r['passedDps'],r['failedDps']]:
   out=a.replay(r['id'],d);checks.append(dict(id=r['id'],dps=d,alive=out['result']['alive']))
(p/'gold-boundaries.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2))
lines=['# 第二期：补入金霖龙后的完整榜单','','|名次|英雄|通过档|配装|海克斯|人口|补算前成绩|','|---|---|---:|---|---|---:|---:|']
for r in x['leaderboard']:lines.append(f"|{r['rank']}|{r['hero']}|{r['passedDps']}|{'＋'.join(r['itemNames'])}|{r['augmentName']}|{r['slots']}|{before[r['hero']]['passedDps']}|")
(p/'ranking.md').write_text('\n'.join(lines)+'\n');m['status']='ranked';(p/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2))
(R/'state/frontline-episode-02-current.json').write_text(json.dumps(dict(id=p.name,status='ranked',production=str(p),configurations=x['totalConfigurations'],heroCount=24,excludedArtifact='探索者的护臂',augments=['无指定海克斯','单身板甲','金霖龙'],videoStarted=False),ensure_ascii=False,indent=2))
print(json.dumps(dict(supplement=events[-1],total=x['totalConfigurations'],changed=[dict(hero=r['hero'],score=r['passedDps'],previous=before[r['hero']]['passedDps'],rank=r['rank'])for r in x['leaderboard']if r['passedDps']!=before[r['hero']]['passedDps']]),ensure_ascii=False),flush=True)
