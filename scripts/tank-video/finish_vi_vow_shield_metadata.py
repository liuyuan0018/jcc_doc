"""Audit corrected H narrative and emit revision-v3 subtitles and chapters."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'exports/frontline-vi-vow-eight-v1/production-v3'
SOURCE = ROOT / 'research/vi-vow-topic-20260923/vow-shield-revision-v1'
timeline = json.loads((OUT / 'content-pipeline/timeline.json').read_text())
replay = json.loads((OUT / 'replay.json').read_text())
source = json.loads((SOURCE / 'source-replays.json').read_text())
verification = json.loads((SOURCE / 'verification.json').read_text())
assert verification['passed'] and verification['stageCount'] == 53
assert len(replay['cards']) == 8 and len(replay['runs']) == 53
assert replay['duration'] == timeline['duration']
assert [card['id'] for card in replay['cards']] == list('ABCDEFGH')
assert [tier['dps'] for tier in timeline['tiers']] == list(range(1750, 2251, 50))
assert [cue['id'] for cue in timeline['cues']] == [f'V{i:02}' for i in range(1, 6)] + ['V05B'] + [f'V{i:02}' for i in range(6, 16)]
assert all('圣盾' not in cue['text'] and '圣盾' not in cue['spoken'] for cue in timeline['cues'])
assert all('圣盾' not in item['label'] for card in replay['cards'] for item in card['equipment'])
h_fail = next(run for run in replay['runs'] if run['id'] == 'H:1800')
assert h_fail['samples'][-1]['alive'] is False
assert h_fail['samples'][-1]['time'] == 880 / 30

tiers = {tier['dps']: tier for tier in timeline['tiers']}
events = {(event['dps'], event['build']): event['at'] for event in timeline['events']}
cues = {cue['id']: cue for cue in timeline['cues']}
result_start = next(segment['start'] for segment in timeline['segments'] if segment['kind'] == 'result')
checks = {
    'V04 after 1750 pass': cues['V04']['start'] >= tiers[1750]['battleEnd'],
    'V05 after H 1800 death and settlement': cues['V05']['start'] >= max(events[1800, 'H'], tiers[1800]['battleEnd']),
    'V05B after F 1900 death and settlement': cues['V05B']['start'] >= max(events[1900, 'F'], tiers[1900]['battleEnd']),
    'V06 after 1950 pass': cues['V06']['start'] >= tiers[1950]['battleEnd'],
    'V07 after E 2000 death': cues['V07']['start'] >= events[2000, 'E'],
    'V08 after D and G 2050 deaths': cues['V08']['start'] >= max(events[2050, 'D'], events[2050, 'G'], tiers[2050]['battleEnd']),
    'V09 after B and C 2100 deaths': cues['V09']['start'] >= max(events[2100, 'B'], events[2100, 'C'], tiers[2100]['battleEnd']),
    'V10 after A 2100 pass': cues['V10']['start'] >= tiers[2100]['battleEnd'],
    'V11 after 2150 pass': cues['V11']['start'] >= tiers[2150]['battleEnd'],
    'V12 after 2200 pass': cues['V12']['start'] >= tiers[2200]['battleEnd'],
    'V13 after A 2250 death': cues['V13']['start'] >= events[2250, 'A'],
    'V14 and V15 on result page': all(cues[key]['start'] >= result_start for key in ('V14', 'V15')),
    'cover narration finishes before cut': cues['V01']['actualEnd'] < timeline['coverSeconds'],
}
assert all(checks.values()), checks
result = next(segment for segment in replay['segments'] if segment['phase'] == 'result')
expected_ranks = {'A': '第1', 'B': '并列第2', 'C': '并列第2', 'D': '并列第4',
                  'E': '第6', 'F': '第7', 'G': '并列第4', 'H': '第8'}
for build in source['builds']:
    track = next(track for track in result['tracks'] if track['cardId'] == build['key'])
    assert track['resultLabel'] == f"最高{build['passedDps']:,}"
    assert track['deadLabel'] == expected_ranks[build['key']]


def stamp(seconds):
    ms = round(seconds * 1000)
    hours, ms = divmod(ms, 3600000)
    minutes, ms = divmod(ms, 60000)
    seconds, ms = divmod(ms, 1000)
    return f'{hours:02}:{minutes:02}:{seconds:02},{ms:03}'


subtitles = '\n'.join(
    f"{index}\n{stamp(cue['start'])} --> {stamp(cue['end'])}\n" + '\n'.join(cue['lines']) + '\n'
    for index, cue in enumerate(timeline['cues'], 1)
)
(OUT / 'subtitles.srt').write_text(subtitles, encoding='utf-8')
chapters = []
for segment in timeline['segments']:
    if segment['kind'] in ('cover', 'intro', 'result', 'battle'):
        title = {'cover': '封面', 'intro': '固定条件', 'result': '八套结果'}.get(segment['kind']) or f"每秒来伤 {segment['dps']}"
        seconds = round(segment['start'])
        chapters.append(f'{seconds // 60:02}:{seconds % 60:02} {title}')
(OUT / 'chapters.txt').write_text('\n'.join(chapters) + '\n', encoding='utf-8')
(OUT / 'narrative-check.json').write_text(json.dumps(dict(passed=True, checks=checks,
    resultLabels=8, ranks=expected_ranks, h1800FailedFrame=880,
    episodeSeconds=timeline['duration']), ensure_ascii=False, indent=2) + '\n')
print(json.dumps(dict(passed=True, subtitles=len(timeline['cues']), checks=len(checks),
                      duration=timeline['duration']), ensure_ascii=False))
