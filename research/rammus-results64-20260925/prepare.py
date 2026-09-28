import json,gzip,hashlib,sys,subprocess,collections,concurrent.futures
from pathlib import Path
ROOT=Path('/Users/lyu/Documents/ChatGPT/金铲铲'); OUT=Path(__file__).parent; ARC=ROOT/'exports/frontline-episode-01-rerun-v3'; JCC=Path('/Users/lyu/Documents/project/game/projects/jcc/client')
sys.path.insert(0,str(ARC));import archive
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
audit=json.loads((ROOT/'research/rammus-eight-20260924/appendix-model-audit.json').read_text())
exe=ROOT/'research/vi-vow-topic-20260923/vow-shield-revision-v1/input/replay-native'
assert sha(exe)==audit['hashes']['revisedReplay']
source=ARC/'raw/scenario-185.summary.jsonl.gz';assert sha(source)==audit['hashes']['summary']
with gzip.open(source,'rt') as f:rows=[json.loads(s) for s in f]
rows=[r for r in rows if r['augment']==0 or (r['augment']==4 and r['items'].count(27)==1)]
assert len(rows)==8365
byid={r['id']:r for r in rows}
for c in audit['correctedChains']:
 for k in ['passedDps','failedDps']:byid[c['id']][k]=c[k]
def run(r,dps):return json.loads(subprocess.check_output([str(exe),*map(str,archive.parameters(r,dps))]))['result']
corrections=[]
for r in rows:
 if r['augment']==4 and r['items'].count(22)>1:
  stages=[]
  for dps in range(300,5001,50):
   result=run(r,dps);stages.append(dict(dps=dps,result=result))
   if not result['alive']:break
  assert not stages[-1]['result']['alive']
  r['passedDps']=stages[-2]['dps'];r['failedDps']=stages[-1]['dps'];corrections.append(dict(id=r['id'],stages=stages))
# Approved 24 equipment pairs plus 16 ordinary configurations.
pairs=[(33,30),(33,24),(33,26),(33,29),(33,22),(33,23),(30,24),(30,26),(30,29),(30,22),(24,26),(24,29),(24,22),(24,23),(26,29),(29,22),(33,33),(30,30),(5,33),(5,24),(5,16),(16,33),(16,24),(16,23)]
extra=[(27,27,x) for x in [33,30,24,29,22,5,16]]+[(26,30,33),(26,30,24),(33,30,24),(33,24,29),(33,24,22),(33,30,29),(5,16,23),(16,16,23),(5,16,16)]
wanted={(tuple(sorted((27,*p))),a) for p in pairs for a in [0,4]}|{(tuple(sorted(p)),0) for p in extra}
assert len(wanted)==64
selected=[r for r in rows if (tuple(r['items']),r['augment']) in wanted];assert len(selected)==64
counts=collections.Counter(r['passedDps'] for r in rows)
for r in rows:r['rank']=1+sum(c for score,c in counts.items() if score>r['passedDps'])
selected.sort(key=lambda r:(-r['passedDps'],r['items'],r['augment']))
def verify(r):
 for dps,alive in [(r['passedDps'],True),(r['failedDps'],False)]:
  result=run(r,dps);assert bool(result['alive'])==alive,(r['id'],dps,result)
 return dict(id=r['id'],passedDps=r['passedDps'],failedDps=r['failedDps'],verified=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:checks=list(pool.map(verify,selected))
assert sha(exe)==audit['hashes']['revisedReplay']
base=json.loads((JCC/'Assets/Res/Replay/rammus-results-pages-v1.json').read_text())
# Use exact item keys already present on the original eight cards.
full=json.loads((JCC/'Assets/Res/Replay/rammus-eight-results-v1.json').read_text());keymap={e['label']:e['iconKey'] for c in full['cards'] for e in c['equipment']};print(keymap)
labels={5:'饮血',16:'大天使',22:'冰甲',23:'头盔',24:'振奋',26:'反甲',27:'板甲',29:'坚定之心',30:'龙牙',33:'狂徒'}
keys={5:'bloodthirster',16:'archangels_staff',22:'2023',23:'adaptivehelm',24:'spirit_visage',27:'gargoyle_stoneplate',30:'2031',33:'warmogs_armor'}
keys[26]=keymap['反甲'].removeprefix('item/');keys[29]=keymap.get('坚定之心',keymap.get('坚定')).removeprefix('item/')
entries=[]
for r in selected:
 entries.append(dict(id=r['id'],rank=r['rank'],passedDps=r['passedDps'],isTop=r['rank']==1,episodeTag='',equipment=[dict(label=labels[i],iconKey='item/'+keys[i]) for i in r['items']],augments=[dict(label='单身板甲',iconKey='augment/soloplate2')] if r['augment']==4 else []))
base.update(id='rammus-results64-v2',source='scenario185: archived 8365 eligible configurations + corrected duplicate Vow; 64 selected boundaries reverified',duration=40,captions=[],isFixture=False)
base['results'].update(title='龙龟，怎么配更能扛？',subtitle='8365种方案中，精选64套对比',conditions='三星龙龟 · 6护卫 · 海克斯见每行配置\n5人集火 / 33%重伤 / 双抗各降30% / 物魔各半 / 无控制',footnote='固定条件模拟 · 名次来自8365种方案 · 同成绩并列',entries=entries,pageSizes=[8]*8,barScaleDps=max(r['passedDps'] for r in rows)+50)
for i,s in enumerate(base['segments']):s.update(start=i*5,end=(i+1)*5,resultPage=i+1,hasPageTurnSeconds=True,pageTurnSeconds=0)
(OUT/'replay.json').write_text(json.dumps(base,ensure_ascii=False))
(OUT/'ranking.json').write_text(json.dumps(dict(poolSize=len(rows),selected=selected,all=rows,checks=checks,corrections=corrections,hashes=audit['hashes']),ensure_ascii=False))
print(json.dumps(dict(entries=len(entries),pages=8,ranks=[e['rank'] for e in entries]),ensure_ascii=False))
