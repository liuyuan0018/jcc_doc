"""Create subtitles and audit the episode's evidence-to-narration ordering."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'exports/frontline-vi-vow-eight-v1'
timeline = json.loads((OUT/'content-pipeline/timeline.json').read_text())
replay = json.loads((OUT/'replay.json').read_text())
evidence = json.loads((ROOT/'research/vi-vow-topic-20260923/evidence.json').read_text())
report = json.loads((OUT/'replay-extraction-report.json').read_text())
assert report['passed'] and report['stageCount'] == 39
assert len(replay['cards']) == 8 and len(replay['runs']) == 39 and replay['duration'] == timeline['duration'] == 129.5
assert [c['id'] for c in replay['cards']] == list('ABCDEFGH')
assert all('圣盾' not in c['text'] and '圣盾' not in c['spoken'] for c in timeline['cues'])
assert all('圣盾' not in item['label'] for card in replay['cards'] for item in card['equipment'])
assert next(r for r in replay['runs'] if r['id']=='H:1900')['samples'][-1]['alive'] is False

tiers = {t['dps']:t for t in timeline['tiers']}
events = {(e['dps'],e['build']):e['at'] for e in timeline['events']}
cues = {c['id']:c for c in timeline['cues']}
checks = {
    'V04 after 1850 pass':cues['V04']['start'] >= tiers[1850]['battleEnd'],
    'V05 after F and H deaths and settlement':cues['V05']['start'] >= max(events[1900,'F'],events[1900,'H'],tiers[1900]['battleEnd']),
    'V06 after 1950 pass':cues['V06']['start'] >= tiers[1950]['battleEnd'],
    'V07 after E 2000 death':cues['V07']['start'] >= events[2000,'E'],
    'V08 after D and G 2050 deaths':cues['V08']['start'] >= max(events[2050,'D'],events[2050,'G'],tiers[2050]['battleEnd']),
    'V09 after B and C 2100 deaths':cues['V09']['start'] >= max(events[2100,'B'],events[2100,'C'],tiers[2100]['battleEnd']),
    'V10 after A 2100 pass':cues['V10']['start'] >= tiers[2100]['battleEnd'],
    'V11 after 2150 pass':cues['V11']['start'] >= tiers[2150]['battleEnd'],
    'V12 after 2200 pass':cues['V12']['start'] >= tiers[2200]['battleEnd'],
    'V13 after A 2250 death':cues['V13']['start'] >= events[2250,'A'],
    'V14 and V15 on result page':all(cues[x]['start'] >= next(s['start'] for s in timeline['segments'] if s['kind']=='result') for x in ('V14','V15')),
    'cover narration finishes before cut':cues['V01']['actualEnd'] < timeline['coverSeconds'],
}
assert all(checks.values()), checks
for card in replay['cards']:
    key=card['id']; row=evidence['builds'][key]['summary']
    result=next(s for s in replay['segments'] if s['phase']=='result')
    track=next(t for t in result['tracks'] if t['cardId']==key)
    assert track['resultLabel']==f"最高{row['passedDps']:,}"

def stamp(seconds):
    ms=round(seconds*1000); h,ms=divmod(ms,3600000); m,ms=divmod(ms,60000); s,ms=divmod(ms,1000)
    return f'{h:02}:{m:02}:{s:02},{ms:03}'
subs='\n'.join(f"{i}\n{stamp(c['start'])} --> {stamp(c['end'])}\n"+'\n'.join(c['lines'])+'\n' for i,c in enumerate(timeline['cues'],1))
(OUT/'subtitles.srt').write_text(subs,encoding='utf-8')
chapters=[]
for segment in timeline['segments']:
    if segment['kind'] in ('cover','intro','result','battle'):
        title={'cover':'封面','intro':'固定条件','result':'八套结果'}.get(segment['kind']) or f"每秒来伤 {segment['dps']}"
        seconds=round(segment['start']);chapters.append(f'{seconds//60:02}:{seconds%60:02} {title}')
(OUT/'chapters.txt').write_text('\n'.join(chapters)+'\n',encoding='utf-8')
(OUT/'narrative-check.json').write_text(json.dumps(dict(passed=True,checks=checks,resultLabels=8,
    h1900Alive=False,episodeSeconds=timeline['duration']),ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(passed=True,subtitles=len(timeline['cues']),checks=len(checks)),ensure_ascii=False))
