"""Check narration claims against replay facts, and preserve a reviewed baseline."""
import argparse,json,hashlib
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--baseline',type=Path,required=True);args=ap.parse_args();out=args.out;old=args.baseline
read=lambda path:json.loads(path.read_text());sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
r=read(out/'replay.json');b=read(old/'replay.json');t=read(out/'timeline.json');bt=read(old/'timeline.json');plan=read(out/'results-plan.json');source=read(out/'source-data.json');events={e['id']:e for e in t['events']};builds={b['key']:b for b in source['builds']}
for key in ['cards','runs','segments','results','duration']:assert r[key]==b[key],key
assert len(r['results']['entries'])==72
claims=plan['narrationClaims'];assert {c['cue'] for c in claims}=={e['id'] for e in t['events'] if e['id'].isdigit()}
report=[]
for c in claims:
 e=events[c['cue']];seg=next(s for s in r['segments'] if s['start']<=e['start']<s['end']);assert seg['phase']=='hold' and seg['dps']==c['dps'];assert e['actualEnd']+.35<=seg['end']+1e-8
 for key in c['cards']:
  build=builds[key];run=next(x for x in build['chain'] if x['dps']==c['dps']);res=run['result']
  if c['kind']=='failed':assert build['failedDps']==c['dps'] and not res['alive'] and res['frame']<900
  else:assert res['alive'] and res['frame']==900
  if 'highestPassedDps' in c:assert build['passedDps']==c['highestPassedDps']
 report.append(dict(**c,text=e['text'],start=e['start'],speechEnd=e['actualEnd'],windowEnd=seg['end'],factsMatched=True))
changed=set(plan['narrationOverrides']);before={e['id']:e for e in bt['events']}
for e in t['events']:
 seg=next(s for s in r['segments'] if s['start']<=e['start']<s['end']);assert e['actualEnd']+.35<=seg['end']+1e-8
 assert e['start']==before[e['id']]['start']
 if e['id'] not in changed:assert e==before[e['id']]
assert not any('停在' in e['text'] for e in t['events'])
for f in ['music-bed.wav','elimination-effects.wav','source-data.json']:assert sha(out/f)==sha(old/f),f
for key in before:
 if key not in changed:assert sha(out/'assets/tts'/f'{key}.wav')==sha(old/'assets/tts'/f'{key}.wav')
report=dict(passed=True,claims=report,changedCues=sorted(changed),unchangedCardsRunsSegmentsResults=True,unchangedOtherSpeechAndMusic=True,allWindowsFit=True,semanticReview='Field/event checks automated; complete sentence meaning reviewed separately, not inferred from audio correlation.',replaySha256=sha(out/'replay.json'),audioSha256=sha(out/'mix-master.wav'))
(out/'narration-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))
