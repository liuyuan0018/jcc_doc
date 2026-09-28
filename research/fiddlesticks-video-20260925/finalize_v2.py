import csv,hashlib,json,collections
from pathlib import Path
ROOT=Path('/Users/lyu/Documents/ChatGPT/金铲铲');HERE=Path(__file__).parent;OUT=ROOT/'exports/frontline-fiddlesticks-v1/production-v2';d=json.loads((HERE/'ranking.json').read_text());r=json.loads((OUT/'replay.json').read_text());t=json.loads((OUT/'timeline.json').read_text());items=json.loads((ROOT/'exports/frontline-episode-01-rerun-v3/input/catalog.json').read_text())['items'];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert d['poolSize']==len(d['all'])==8365 and len(d['selected'])==64
assert all(x['augment'] in [0,4] for x in d['all'])
for row in d['all']:assert row['rank']==1+sum(n for score,n in collections.Counter(x['score'] for x in d['all']).items() if score>row['score'])
checks=[]
for b,c in zip(d['main'],r['cards']):
 assert c['augment']=={0:'无指定海克斯',4:'单身板甲'}[b['augment']]
 if b['augment']:assert c['augmentIconKey']=='augment/soloplate2'
 runs=[x for x in r['runs'] if x['cardId']==b['key']]
 for run in runs:
  dps=int(run['id'].split(':')[1]);old=next(s for s in b['stages'] if s['dps']==dps)['result'];assert run['samples'][-1]['alive']==old['alive'];assert abs(run['samples'][-1]['time']-old['frame']/30)<1e-8
 assert b['passedDps']<=b['score']<b['failedDps'];checks.append(dict(key=b['key'],id=b['id'],augment=b['augment'],coarsePassed=b['passedDps'],coarseFirstFailed=b['failedDps'],fineScore=b['score'],displayRuns=len(runs)))
for l,rr in zip(r['segments'],r['segments'][1:]):assert abs(l['end']-rr['start'])<1e-8
for e in t['events']:
 seg=next(s for s in r['segments'] if s['start']<=e['start']<s['end']);assert seg['phase']!='battle';assert e['actualEnd']+.35<=seg['end']+1e-8
for row,entry in zip(d['selected'],r['results']['entries']):assert (row['id'],row['rank'],row['score'])==(entry['id'],entry['rank'],entry['passedDps'])
assert all(sha(Path(p))==h for p,h in d['sourceHashes'].items())
(OUT/'data-validation.json').write_text(json.dumps(dict(passed=True,main=checks,resultsCount=64,globalPool=8365,heartsteelExcluded=True,allSourceHashesUnchanged=True,replaySha256=sha(OUT/'replay.json'),audioSha256=sha(OUT/'mix-master.wav'),pauseProfileSha256=sha(OUT/'pause-window-profile.json'),speechAfterResolvedTier=True),ensure_ascii=False,indent=2))
with (OUT/'Results-64.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.writer(f);w.writerow(['全体名次','装备1','装备2','装备3','海克斯','逐档细分成绩','粗档通过','粗档首败','配置ID'])
 for x in d['selected']:w.writerow([x['rank'],*[items[i]['name'] for i in x['items']],{0:'无',4:'单身板甲'}[x['augment']],x['score'],x['passedDps'],x['failedDps'],x['id']])
meat={22,23,24,26,27,29,30,33};pure=sum(all(i in meat for i in x['items']) for x in d['selected']);print('pure defensive',pure)
rows='\n'.join(f'| {x["key"]} | '+ ' / '.join(items[i]['name'] for i in x['items'])+f' | '+{0:'无',4:'单身板甲'}[x['augment']]+f' | {x["passedDps"]} | {x["failedDps"]} | {x["score"]} |' for x in d['main'])
(HERE/'README.md').write_text('# 草人配装测评：当前 v2\n\n当前输入与成片目录为 exports/frontline-fiddlesticks-v1/production-v2。production-v1 是已被用户后续要求替代的历史稿，不再作为交付版本。\n\n采用三星6护卫、6人口；环境复用龙龟v5。Main含同装备有无单身板甲的两组对照。用户明确排除心之钢；当前候选池8365套（7770无海克斯、595适用单身板甲），Results与Main都不包含心之钢。历史原始扫描中的其他分支仅留证，不参与本期评分。\n\n从300每次加50至首次失败；最后通过档和首败档之间从低到高+1细分，同样遇首败停止。所有候选同一规则、同分并列；单身板甲假定独占一排且一件普通板甲。双冰甲受影响的旧链定向修正。不是从300逐点扫描，也不声称首败以上全不能通过。\n\n精选64套，其中'+str(pure)+'套是本期常规肉装池的纯肉组合。名次来自全部8365套，不是把精选名单重新编号；这不是完整前64名。\n\n| Main | 配装 | 海克斯 | 粗档通过 | 粗档首败 | 细分成绩 |\n|---|---|---|---:|---:|---:|\n'+rows+'\n\n当前制作入口：build_episode_v2.py；固定暂停配方 pause-window-profile-v2.json。source-data.json保留51场真实回放；录制调用Unity项目Tools/Production/record_replay.py，media-capture实时连续录制，非逐帧导出。\n')
audit=json.loads((HERE/'model-audit.json').read_text());audit.update(poolSize=8365,augmentCounts={'0':7770,'4':595},selectedPureDefensive=pure,augments='无；单身板甲（恰好一件普通板甲且独占一排）。心之钢按用户要求排除。');(HERE/'model-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2))
(OUT/'笔记文案.md').write_text('标题：草人怎么穿？8套配装对照\n\n草人自带回血，装备继续补回复，还是直接堆肉？\n\n这次选了8套代表配装，加入两组同装备、有无单身板甲的对照。从低档逐档加压，每档满血重开，撑满30秒才通过；最后留下的配置继续测到首次失败。\n\n片尾精选64套，其中'+str(pure)+'套是常规肉装组合。按统一细分成绩排序，名次来自本次8365种方案，精选名单不是完整前64名。每页保留语音提示，方便按章节查找。\n\n条件：三星草人、6护卫、6人口、三件普通装备；5人集火参数、33%重伤、双抗各降30%、物理魔法各半、无控制。海克斯看每套标注，单身板甲假定独占一排；本期不纳入心之钢。\n\n这是固定条件的机制模拟，实战还有站位、控制和敌方技能等影响。\n\n#金铲铲之战 #金铲铲 #稻草人 #装备搭配\n')
print('Current data and pause windows validated')
