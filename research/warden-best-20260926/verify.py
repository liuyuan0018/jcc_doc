import json,subprocess,sys,gzip,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'exports/warden-best-20260926';sys.path.insert(0,str(ROOT/'exports/frontline-episode-01-rerun-v3'));import archive
best=json.loads((OUT/'hero-ranking.json').read_text());verified=[];(OUT/'replays').mkdir(exist_ok=True)
for x in best:
 for b in x['builds']:
  r=dict(scenario=x['scenario'],items=b['items'],augment=b['augment'])
  for d in sorted({b['passedDps'],b['failedDps'],b['score'],b['score']+1}):
   o=json.loads(subprocess.check_output([str(OUT/'input/replay-native'),*map(str,archive.parameters(r,d))]));expected=d in [b['passedDps'],b['score']];assert o['result']['alive']==expected,(b['id'],d)
   archive.validate_replay(o)
   with gzip.open(OUT/'replays'/f'{b["id"]}-{d}.json.gz','wt')as f:json.dump(o,f,separators=(',',':'))
   verified.append(dict(id=b['id'],dps=d,alive=o['result']['alive'],frame=o['result']['frame']))
cat=archive.ITEMS;names={5:'饮血',16:'大天使',17:'冕卫',23:'头盔',24:'振奋',25:'正义',27:'板甲'}
lines=['# 2/4/6护卫：每位英雄最优配置','', '范围：6名护卫，1—3费三星、4费两星；18个英雄/羁绊条件，每条件8365套，合计150570套。草人6护卫8365套复用，其余142205套补算。','', '评分：30秒、300起每50加压至首败，再在最后粗档区间逐点细分至首败。均为减伤前每秒总来伤。5人集火，33%重伤，双抗各降30%，物魔各半，无控制。无海克斯及适用单身板甲；不计神器进度。','', '|护卫|英雄名次|英雄|星级|最优配装|海克斯|细分成绩|粗档通过/首败|','|---|---|---|---|---|---|---|---|']
for x in best:
 for b in x['builds']:lines.append(f'|{x["tier"]}|{x["heroRankInTier"]}|{x["hero"]}|{x["star"]}|'+ '＋'.join(names.get(i,cat[i]['name'])for i in b['items'])+f'|{"单身板甲"if b["augment"]else"无"}|{b["score"]}|{b["passedDps"]}/{b["failedDps"]}|')
lines+=['','这是每位英雄各自选优后的比较，不是相同装备、相同经济投入比较。沿用系列冻结模型，不宣称最新客户端实测。低于起点未通过的配置保留-1，不当作精确上限。三档均不存在英雄第一名并列。']
(OUT/'README.md').write_text('\n'.join(lines)+'\n');(OUT/'verification.json').write_text(json.dumps(dict(passed=True,verifiedReplayCount=len(verified),checks=verified,sourceHashesUnchanged=all(hashlib.sha256((OUT/'input'/n).read_bytes()).hexdigest()==h for n,h in json.loads((OUT/'manifest.json').read_text())['sourceHashes'].items())),indent=2));print('VERIFIED',len(verified))
