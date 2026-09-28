"""Audit the Vi Sterak narrative and export subtitles and chapters."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'exports/frontline-vi-sterak-eight-v1/production-v1'
SOURCE = ROOT / 'research/vi-sterak-eight-20260924'


def stamp(seconds):
    ms = round(seconds * 1000)
    hours, ms = divmod(ms, 3600000)
    minutes, ms = divmod(ms, 60000)
    seconds, ms = divmod(ms, 1000)
    return f'{hours:02}:{minutes:02}:{seconds:02},{ms:03}'


def main():
    timeline = json.loads((OUT / 'content-pipeline/timeline.json').read_text())
    replay = json.loads((OUT / 'replay.json').read_text())
    source = json.loads((SOURCE / 'source-replays.json').read_text())
    verification = json.loads((SOURCE / 'verification.json').read_text())
    assert verification['passed'] and verification['attemptedStageCount'] == 277
    assert len(replay['cards']) == 8 and len(replay['runs']) == 45
    assert replay['duration'] == timeline['duration']
    assert [card['id'] for card in replay['cards']] == list('ABCDEFGH')
    assert [tier['dps'] for tier in timeline['tiers']] == list(range(1750, 2251, 50))
    assert [cue['id'] for cue in timeline['cues']] == [f'V{i:02}' for i in range(1, 17)]
    b1950 = next(run for run in replay['runs'] if run['id'] == 'B:1950')
    assert b1950['samples'][-1]['alive'] is False
    assert b1950['samples'][-1]['time'] == 30

    tiers = {tier['dps']: tier for tier in timeline['tiers']}
    events = {(event['dps'], event['build']): event['at'] for event in timeline['events']}
    cues = {cue['id']: cue for cue in timeline['cues']}
    result_start = next(seg['start'] for seg in timeline['segments'] if seg['kind'] == 'result')
    checks = {
        'V01 on cover': cues['V01']['actualEnd'] < timeline['coverSeconds'],
        'V04 after all 1750 pass': cues['V04']['start'] >= tiers[1750]['battleEnd'],
        'V05 after H 1800 failure': cues['V05']['start'] >= max(events[1800, 'H'], tiers[1800]['battleEnd']),
        'V06 after D and F 1850 failures': cues['V06']['start'] >= max(events[1850, 'D'], events[1850, 'F'], tiers[1850]['battleEnd']),
        'V07 after B 1950 failure': cues['V07']['start'] >= max(events[1950, 'B'], tiers[1950]['battleEnd']),
        'V08 after C 2000 failure': cues['V08']['start'] >= max(events[2000, 'C'], tiers[2000]['battleEnd']),
        'V09 after G 2050 failure': cues['V09']['start'] >= max(events[2050, 'G'], tiers[2050]['battleEnd']),
        'V10 after E 2100 failure': cues['V10']['start'] >= max(events[2100, 'E'], tiers[2100]['battleEnd']),
        'V11 after A 2100 pass': cues['V11']['start'] >= tiers[2100]['battleEnd'],
        'V12 after A 2150 pass': cues['V12']['start'] >= tiers[2150]['battleEnd'],
        'V13 after A 2200 pass': cues['V13']['start'] >= tiers[2200]['battleEnd'],
        'V14 after A 2250 failure': cues['V14']['start'] >= max(events[2250, 'A'], tiers[2250]['battleEnd']),
        'V15 and V16 on result': all(cues[key]['start'] >= result_start for key in ('V15', 'V16')),
        'V15 both differences from A': 'A→B' in cues['V15']['text'] and 'A→C' in cues['V15']['text'],
    }
    assert all(checks.values()), checks
    result = next(seg for seg in replay['segments'] if seg['phase'] == 'result')
    ranks = {'A': '第1', 'B': '第5', 'C': '第4', 'D': '并列第6',
             'E': '第2', 'F': '并列第6', 'G': '第3', 'H': '第8'}
    for build in source['builds']:
        track = next(track for track in result['tracks'] if track['cardId'] == build['key'])
        assert track['resultLabel'] == f"最高{build['passedDps']:,}"
        assert track['deadLabel'] == ranks[build['key']]

    subtitles = '\n'.join(
        f"{i}\n{stamp(cue['start'])} --> {stamp(cue['end'])}\n" + '\n'.join(cue['lines']) + '\n'
        for i, cue in enumerate(timeline['cues'], 1))
    (OUT / 'subtitles.srt').write_text(subtitles, encoding='utf-8')
    chapters = []
    for seg in timeline['segments']:
        if seg['kind'] not in ('cover', 'intro', 'result', 'battle'):
            continue
        title = {'cover': '封面', 'intro': '固定条件', 'result': '八套结果'}.get(seg['kind']) or f"每秒来伤 {seg['dps']}"
        seconds = round(seg['start'])
        chapters.append(f'{seconds // 60:02}:{seconds % 60:02} {title}')
    (OUT / 'chapters.txt').write_text('\n'.join(chapters) + '\n')
    (OUT / 'narrative-check.json').write_text(json.dumps(dict(
        passed=True, checks=checks, resultLabels=8, ranks=ranks,
        b1950FailedAtFrame900=True, episodeSeconds=timeline['duration']),
        ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(dict(passed=True, checks=len(checks),
                          subtitles=len(timeline['cues']), duration=timeline['duration']),
                     ensure_ascii=False))


if __name__ == '__main__':
    main()
