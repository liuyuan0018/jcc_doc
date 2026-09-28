import argparse,json,csv,hashlib
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--baseline',type=Path,required=True);args=p.parse_args();out=args.out;old=args.baseline
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=read(out/'replay.json');b=read(old/'replay.json');t=read(out/'timeline.json');d=read(Path('research/rammus-rank-progression-20260925/ranking.json'));entries=r['results']['entries'];lookup={x['id']:x for x in d['all']};main={x['id']:x['card'] for x in d['mainChecks']};events={x['id']:x for x in t['events']}
assert r['cards']==b['cards'] and r['runs']==b['runs'];assert r['segments'][:42]==b['segments'][:42]
appendix=r['segments'][42:]
scopes=[s for s in appendix if s['layout']=='scope']
if scopes:
 assert len(scopes)==1 and appendix[0]==scopes[0]
 assert scopes[0]['end']>scopes[0]['start'] and any(e['id'].startswith('S') and scopes[0]['start']<=e['start']<scopes[0]['end'] for e in t['events'])
 assert all(s['layout']=='results' for s in appendix[1:])
else:
 assert all(s['layout']=='results' for s in appendix)
assert len(entries)==len({x['id'] for x in entries})==72
assert [x['id'] for x in entries[:8]]==[x['id'] for x in d['all'][:8]]
for x in entries:
 row=lookup[x['id']];assert (row['rank'],row['passedDps'])==(x['rank'],x['passedDps']);assert x['episodeTag']==main.get(x['id'],'');assert row['augment'] in [0,4]
assert {x['episodeTag'] for x in entries if x['episodeTag']}==set('ABCDEFGH')
assert {x['id'] for x in d['selected']}<={x['id'] for x in entries}
claims=[('V03',950,list('ABCDEFGH'),True),('V04',1000,['G'],False),('V05',1100,['H'],False),('V06',1150,['D'],False),('V07',1300,['B','C'],False),('V09',1700,['A'],False),('V11',1850,['E','F'],True),('V12',1900,['E','F'],False)]
checks=[]
for key,dps,cards,passed in claims:
 e=events[key];s=next(s for s in r['segments'] if s['start']<=e['start']<s['end']);assert s['dps']==dps and s['phase']=='hold'
 for card in cards:
  run=next(run for run in r['runs'] if run['cardId']==card and int(run['id'].split(':')[1])==dps);assert bool(run['samples'][-1]['alive'])==passed
  if not passed:assert next(x for x in d['mainChecks'] if x['card']==card)['firstFail']==dps
 checks.append(dict(cue=key,text=e['text'],currentDps=dps,cards=cards,passed=passed))
budget=[]
for e in t['events']:
 s=next(s for s in r['segments'] if s['start']<=e['start']<s['end']);assert e['actualEnd']+.35<=s['end']+1e-8;assert s['phase']!='battle';assert '停在' not in e['text'];budget.append(dict(id=e['id'],windowStart=s['start'],windowEnd=s['end'],speechEnd=e['actualEnd'],tail=s['end']-e['actualEnd']))
(out/'pause-budget.json').write_text(json.dumps(budget,indent=2))
with (out/'Results-72.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.writer(f);w.writerow(['页','分组','总榜名次','出镜编号','装备','海克斯','细分成绩','ID'])
 for i,e in enumerate(entries):w.writerow([i//8+1,'总榜前8' if i<8 else '特征精选',e['rank'],e['episodeTag'],' / '.join(x['label'] for x in e['equipment']),' / '.join(x['label'] for x in e['augments']) or '无',e['passedDps'],e['id']])
(out/'data-validation.json').write_text(json.dumps(dict(passed=True,rankingSha256=sha(Path('research/rammus-rank-progression-20260925/ranking.json')),poolSize=d['poolSize'],mainCardsRunsAndTimingUnchanged=True,resultsCount=72,top8Exact=True,unique=True,allMainTagged=True,previousSelectionPreserved=True,narrationFacts=checks,allSpeechFits=True),ensure_ascii=False,indent=2))
print('Validated',r['duration'],'seconds; Results starts',t['resultsStart']);print(json.dumps(checks,ensure_ascii=False,indent=2))
