import json,gzip,collections,hashlib,sys,subprocess,math,concurrent.futures
from pathlib import Path
ROOT=Path('/Users/lyu/Documents/ChatGPT/金铲铲');OUT=Path(__file__).parent.resolve();OLD=ROOT/'research/rammus-results64-20260925';JCC=Path('/Users/lyu/Documents/project/game/projects/jcc/client')
sys.path.insert(0,str(ROOT/'exports/frontline-episode-01-rerun-v3'));import archive
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((OUT/'manifest.json').read_text());assert manifest['status']=='computed_pending_validation';assert not manifest['ceilingConfigurations'], 'Extend uniform upper range before finalizing'
source=json.loads((OLD/'ranking.json').read_text());byid={r['id']:r for r in source['all']}
scanned=[json.loads(s) for p in sorted((OUT/'raw').glob('*.jsonl')) for s in p.read_text().splitlines()];new={r['id']:r for r in scanned};assert set(new)==set(byid)
# Read every retained stage; verify contiguous complete coverage and reconstructed maxima/ranges.
seen=set();stageCount=0
for path in sorted((OUT/'raw').glob('*.csv.gz')):
 with gzip.open(path,'rt') as f:
  assert next(f).strip()=='id,dps,alive,frame,hp,shield'
  current=None;last=0;highest=-1;count=0;passed=0;previous=False;ranges=[];rangeStart=None
  def check():
   if current is None:return
   if previous:ranges.append([rangeStart,last])
   assert current not in seen and count==2201 and last==2500,(current,count,last)
   assert highest==new[current]['highestPass'] and passed==new[current]['passCount'] and ranges==new[current]['passRanges'],current
   seen.add(current)
  for line in f:
   key,dps,alive,frame,hp,shield=line.rstrip().split(',');dps=int(dps);alive=alive=='1'
   if key!=current:
    check();current=key;last=299;highest=-1;count=0;passed=0;previous=False;ranges=[];rangeStart=None
   assert dps==last+1 and (not alive or int(frame)==900),(key,dps)
   if alive:
    highest=dps;passed+=1
    if not previous:rangeStart=dps
   elif previous:ranges.append([rangeStart,dps-1])
   previous=alive;last=dps;count+=1;stageCount+=1
  check()
assert seen==set(byid) and stageCount==manifest['totalStages']
print('All retained stages validated:',stageCount,flush=True)
for r in scanned:
 original=byid[r['id']];r.update(items=original['items'],augment=original['augment'],scenario=185,coarsePassedDps=original['passedDps'],passedDps=r['highestPass'])
counts=collections.Counter(r['highestPass'] for r in scanned)
for r in scanned:r['rank']=1+sum(n for score,n in counts.items() if score>r['highestPass']);r['tieCount']=counts[r['highestPass']]
scanned.sort(key=lambda r:(-r['highestPass'],r['items'],r['augment']))
selectedIds={r['id'] for r in source['selected']};selected=[r for r in scanned if r['id'] in selectedIds];assert len(selected)==64
exe=ROOT/'research/vi-vow-topic-20260923/vow-shield-revision-v1/input/replay-native';assert sha(exe)==manifest['sourceHashes'][str(exe)]
def verify(r):
 assert r['highestPass']>=300
 checks=[]
 for dps,expected in [(r['highestPass'],True),(r['highestPass']+1,False)]:
  output=json.loads(subprocess.check_output([str(exe),*map(str,archive.parameters(byid[r['id']],dps))]))['result'];assert bool(output['alive'])==expected,(r['id'],dps)
  if expected:assert all(math.isclose(output[k],v,rel_tol=1e-8,abs_tol=1e-6) for k,v in r['bestResult'].items()),r['id']
  checks.append(dict(dps=dps,alive=expected))
 return dict(id=r['id'],checks=checks)
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:checks=list(pool.map(verify,selected))
assert sha(exe)==manifest['sourceHashes'][str(exe)]
replay=json.loads((OLD/'replay.json').read_text());entries={r['id']:r for r in replay['results']['entries']};newEntries=[]
for r in selected:
 e=entries[r['id']];e.update(rank=r['rank'],passedDps=r['highestPass'],isTop=r['rank']==1);newEntries.append(e)
replay.update(id='rammus-results64-integer-v3',source='8365 configurations; exhaustively scanned integer DPS 300..2500; maximum tested pass; failures do not terminate scan')
replay['results'].update(entries=newEntries,barScaleDps=((scanned[0]['highestPass']+99)//100)*100,footnote='固定条件模拟 · 扫描来伤300—2500 · 取最高通过值',subtitle='8365种方案中，精选64套对比')
(OUT/'replay.json').write_text(json.dumps(replay,ensure_ascii=False))
(JCC/'Assets/Res/Replay/rammus-results64-integer-v3.json').write_text(json.dumps(replay,ensure_ascii=False))
report=dict(verified=True,range=[300,2500],step=1,criterion='maximum passing tested DPS',stageCount=stageCount,poolSize=8365,uniqueScores=len(counts),tiedGroups=sum(n>1 for n in counts.values()),tiedConfigurations=sum(n for n in counts.values() if n>1),selectedTiedGroups={str(score):sum(r['highestPass']==score for r in selected) for score in sorted({r['highestPass'] for r in selected},reverse=True) if sum(r['highestPass']==score for r in selected)>1},selected=selected,all=scanned,checks=checks)
(OUT/'ranking.json').write_text(json.dumps(report,ensure_ascii=False))
manifest.update(status='verified',validation='all stage coverage, pass ranges and maxima; selected native replay boundaries',replaySha256=sha(OUT/'replay.json'),rawHashes={p.name:sha(p) for p in sorted((OUT/'raw').glob('*'))})
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps({k:v for k,v in report.items() if k not in ['selected','all','checks']},ensure_ascii=False),flush=True)
print('Top selected:',[(r['id'],r['rank'],r['highestPass'],r['tieCount']) for r in selected[:8]],flush=True)
