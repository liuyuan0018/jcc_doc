"""Verify the five-tier Ornn narrative and emit subtitles and chapters."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'exports/frontline-ornn-two-warden-eight-v1/production-v1'
SOURCE = ROOT / 'research/ornn-two-warden-eight-20260923/presentation-150-350-v1'
timeline = json.loads((OUT / 'content-pipeline/timeline.json').read_text())
replay = json.loads((OUT / 'replay.json').read_text())
source = json.loads((SOURCE / 'source-replays.json').read_text())
evidence = json.loads((SOURCE / 'verification.json').read_text())
assert evidence['passed'] and evidence['stageCount'] == 30
assert evidence['reusedReplays'] == 16 and evidence['frozenCliSupplements'] == 14
assert len(replay['cards']) == 8 and len(replay['runs']) == 30
assert replay['duration'] == timeline['duration']
assert [card['id'] for card in replay['cards']] == list('ABCDEFGH')
assert [tier['dps'] for tier in timeline['tiers']] == [150, 200, 250, 300, 350]
assert [cue['id'] for cue in timeline['cues']] == [f'O{i:02}' for i in range(1, 12)]
assert all('神器' not in cue['text'] and '神器' not in cue['spoken'] for cue in timeline['cues'])
assert all(segment['layout'] != 'solo' for segment in replay['segments'])
assert source['aug'] == 0 and source['environment']['noArtifactProgress']
for build in source['builds']:
    assert build['chain'][-2]['result']['alive']
    assert not build['chain'][-1]['result']['alive']

tiers = {tier['dps']: tier for tier in timeline['tiers']}
events = {(event['dps'], event['build']): event['at'] for event in timeline['events']}
cues = {cue['id']: cue for cue in timeline['cues']}
result_start = next(segment['start'] for segment in timeline['segments'] if segment['kind'] == 'result')
checks = {
    'O01 finishes on cover': cues['O01']['actualEnd'] < timeline['coverSeconds'],
    'O04 after 150 all pass': cues['O04']['start'] >= tiers[150]['battleEnd'],
    'O05 after C 200 death': cues['O05']['start'] >= events[200, 'C'] + .7,
    'O06 after A B G 250 deaths and settlement': cues['O06']['start'] >= max(
        events[250, 'A'], events[250, 'B'], events[250, 'G']) + .7,
    'O07 after F 300 death': cues['O07']['start'] >= events[300, 'F'] + .7,
    'O08 after D E H 300 pass': cues['O08']['start'] >= tiers[300]['battleEnd'],
    'O09 after D E H 350 deaths and settlement': cues['O09']['start'] >= max(
        events[350, 'D'], events[350, 'E'], events[350, 'H']) + .7,
    'O10 O11 on full result': all(cues[key]['start'] >= result_start for key in ('O10', 'O11')),
}
assert all(checks.values()), checks
result = next(segment for segment in replay['segments'] if segment['phase'] == 'result')
expected_ranks = dict(A='并列第5', B='并列第5', C='第8', D='并列第1',
                      E='并列第1', F='第4', G='并列第5', H='并列第1')
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
    resultLabels=8, ranks=expected_ranks, episodeSeconds=timeline['duration']),
    ensure_ascii=False, indent=2) + '\n')
print(json.dumps(dict(passed=True, subtitles=11, checks=len(checks),
                      duration=timeline['duration']), ensure_ascii=False))
