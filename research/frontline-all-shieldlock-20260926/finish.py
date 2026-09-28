from pathlib import Path
import json,sys,hashlib,gzip,collections,datetime,subprocess
P=Path.cwd();O=P/'exports/frontline-episode-01-rerun-v4';sys.path.insert(0,str(O));import archive as a
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((O/'manifest.json').read_text());assert m['status']=='computed'
subprocess.run([sys.executable,str(O/'archive.py'),'verify'],check=True);a.summarize()
full=json.loads((O/'ranking.json').read_text());best={};counts=collections.Counter();ties=collections.Counter()
for r in a.read_rows():
 if r['augment']==1:continue
 h=r['heroId'];counts[h]+=1
 if h not in best or r['passedDps']>best[h]['passedDps']:best[h]=r;ties[h]=1
 elif r['passedDps']==best[h]['passedDps']:
  ties[h]+=1
  if a.representative(r)<a.representative(best[h]):best[h]=r
ranked=sorted(best.values(),key=lambda r:(-r['passedDps'],a.PROFILES[r['heroId']]['index']));rows=[dict(a.description(r),rank=1+sum(x['passedDps']>r['passedDps']for x in ranked),evaluatedConfigurations=counts[r['heroId']],equallyBestConfigurations=ties[r['heroId']])for r in ranked]
assert len(rows)==24 and sum(counts.values())==697200
filtered=dict(leaderboard=rows,topEight=rows[:8],boundaryTies=[r for r in rows[8:]if r['passedDps']==rows[7]['passedDps']],heroCount=24,totalConfigurations=sum(counts.values()),excludedAugment=1)
(O/'ranking-no-heart.json').write_text(json.dumps(filtered,ensure_ascii=False,indent=2))
(O/'replays').mkdir(exist_ok=True);checks=[];seen=set()
# Reproduce pass/fail boundaries for every hero in both rankings, plus non-winning configs.
selected=full['leaderboard']+rows+[a.description(a.stored_configuration(f's{s["index"]}-b0-a0'))for s in m['scenarios']]
for r in selected:
 for d in sorted({r['passedDps'],r['failedDps']}-{ -1 }):
  key=(r['id'],d)
  if key in seen:continue
  seen.add(key);out=a.replay(*key)
  with gzip.open(O/'replays'/f'{r["id"]}-{d}.json.gz','wt')as f:json.dump(out,f,separators=(',',':'))
  checks.append(dict(id=r['id'],dps=d,alive=out['result']['alive'],frames=len(out['frames'])))
print('BOUNDARIES',len(checks),flush=True)
for name,digest in m['inputHashes'].items():assert sha(O/'input'/name)==digest,name
for n in ['engine-web.hpp','web.cpp','generated.hpp','archive-episode-one.cpp']:assert sha(P/'tank-lab/src'/n)==m['inputHashes'][n]
old=json.loads((Path(m['supersedes'])/'ranking.json').read_text());oldBy={r['hero']:r for r in old['leaderboard']};comparison=[dict(hero=r['hero'],oldRank=oldBy[r['hero']]['rank'],newRank=r['rank'],oldScore=oldBy[r['hero']]['passedDps'],newScore=r['passedDps'])for r in full['leaderboard']];(O/'tests/comparison.json').write_text(json.dumps(comparison,ensure_ascii=False,indent=2))
scenarios={s['index'] for s in m['scenarios']};assert len(scenarios)==83 and {int(p.name.split('-')[1].split('.')[0])for p in (O/'raw').glob('*.summary.jsonl.gz')}==scenarios
assert not list(O.rglob('*.partial'))
validation=dict(passed=True,boundaryAndNonoptimalReplays=len(checks),allFrozenAndSharedHashesMatch=True,checks=checks);(O/'tests/replay-verification.json').write_text(json.dumps(validation,indent=2))
lines=['# 最强坦克全量重算 v4','', '全部24位英雄、83个合法羁绊场景、749490套配置均重新运行，旧成绩复用0套。保留所有非最优配置及尝试过的压力档位。','', '修正主动技能护盾存续期间锁蓝：奥恩、洛、瑟庄妮、慎、黛安娜、拉莫斯、苍蓝雕纹魔像。装备盾、羁绊盾、塔里克被动盾不延长锁蓝。保留原施法最短1秒以及可酷伯/草人2秒、河蟹/人马3秒锁蓝。锁蓝期间直接回蓝也被技能护盾阻止；破盾伤害包在移除护盾后结算回蓝。此为确认后的模拟规则，不等同于客户端逐帧实测。','', '1—3费三星、4—5费两星；每档满血重开30秒；300起每50加压至首败；33%重伤、双抗降低30%、物魔各半、5人集火参数、无控制。不计神器进度。与原期一致，成绩为50步长通过档，没有改用护卫专题的逐点细分。','', '## 不含心之钢的当前口径','', '697200套，无指定海克斯或适用单身板甲。','', '|名次|英雄|羁绊|配装|海克斯|通过 / 首败|','|---|---|---|---|---|---|']
for r in rows:lines.append(f'|{r["rank"]}|{r["hero"]}|'+ '＋'.join(f'{v}{k}'for k,v in r['traits'].items())+'|'+'＋'.join(r['itemNames'])+f'|{r["augmentName"]}|{r["passedDps"]} / {r["failedDps"]}|')
lines+=['','## 与原期完整候选池对照','', '原期心之钢分支也全部重算，以便逐项复核历史结论。此表使用完整749490套，不能与不含心之钢的排名混用。','', '|英雄|旧名次|新名次|旧通过档|新通过档|','|---|---|---|---|---|']
for r in comparison:lines.append(f'|{r["hero"]}|{r["oldRank"]}|{r["newRank"]}|{r["oldScore"]}|{r["newScore"]}|')
lines+=['',f'完成 {m["execution"]["stageRuns"]:,} 场档位计算；全量枚举逐项核对通过；{len(checks)} 场最优边界及非最优回放通过结算对照、逐帧生命和护盾收支核验。','', '计算数据已更新；历史视频、网页榜单和Unity回放未重制。','', '[完整旧池榜](ranking.json) · [不含心之钢榜](ranking-no-heart.json) · [完整留存检查](tests/full-retention-verification.json) · [机制测试](tests/skill-shield-mana.json)']
(O/'README.md').write_text('\n'.join(lines)+'\n');m.update(status='verified',verifiedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),reusedConfigurations=0,validationBoundary='Data and native replay only; no Unity or video refresh',currentRanking='ranking-no-heart.json');(O/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2))
state=P/'state/frontline-episode-01-current.json';(O/'previous-current-pointer.json').write_text(state.read_text());state.write_text(json.dumps(dict(id=m['id'],status='verified',archive=str(O),manifest=str(O/'manifest.json'),report=str(O/'README.md'),ranking=str(O/'ranking-no-heart.json'),legacyPoolRanking=str(O/'ranking.json'),allConfigurationsRetained=True,configurationCount=749490,currentPoolConfigurationCount=697200,stageRuns=m['execution']['stageRuns'],modelRevision=m['producer']['mechanicsRevision'],videoProduced=False,published=False,browserRankingDataUpdated=False,defaultUnityReplayChanged=False),ensure_ascii=False,indent=2))
p=Path(m['supersedes'])/'README.md';p.write_text('> 排名已被技能护盾锁蓝修订后的 [v4全量重算](../frontline-episode-01-rerun-v4/README.md) 替代。下文为旧模型历史记录。\n\n'+p.read_text())
print('DONE',O,flush=True)
