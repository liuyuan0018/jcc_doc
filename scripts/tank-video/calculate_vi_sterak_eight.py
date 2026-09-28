"""Verify the eight Vi Sterak builds against the current frozen native model.

Read the archived full pressure chains, recompute every attempted tier with the
current engine, and save actual replay data for the 1750+ video window.
"""

import gzip
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

from calculate_ornn_two_warden_eight import validate_replay


ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = Path('/Volumes/Apple/Codex/art-assets/金铲铲/exports/frontline-episode-01-rerun-v3')
FROZEN = ROOT / 'research/vi-vow-topic-20260923/vow-shield-revision-v1/input'
OUT = ROOT / 'research/vi-sterak-eight-20260924'
BUILDS = {
    'A': [5, 27, 27], 'B': [6, 27, 27], 'C': [5, 6, 27],
    'D': [6, 22, 27], 'E': [5, 27, 33], 'F': [6, 27, 33],
    'G': [5, 22, 27], 'H': [6, 9, 27],
}
EXPECTED = {
    'engine-web.hpp': 'f476fd9f561189c41d446c525b47ec268e997fe64cfcbd7c7138b077d5301faa',
    'web.cpp': '62bf18cdf292557225b5fd20c15ee8fdd418a9ca0df26fa847b8bcb9a14912df',
    'generated.hpp': '9f153b1105b950cce6b733a9f01ec2370ed0e0d6a6a5d7981ae9fb2309fbc3df',
    'replay-native': '89f153456035771b5d41dea3bc628578342343907c9c917d2908f7de252d2e01',
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parameters(items, dps):
    return [149, *items, 0, 30, dps, 50, 30, 9, .5, 0, 1,
            -1, -1, -1, -1, -1, -1, 0, 1, 0, 15, .15, .04, 0, 0,
            1000000, 120, 5, 1, .33, 0, 5401, 3]


def run(params):
    result = json.loads(subprocess.check_output(
        [str(FROZEN / 'replay-native'), *map(str, params)], text=True))
    assert 'error' not in result, result.get('error')
    validate_replay(result)
    return result


def same(old, new):
    assert old.keys() == new.keys()
    for key, value in old.items():
        if isinstance(value, bool):
            assert value == new[key], key
        else:
            assert math.isclose(value, new[key], rel_tol=1e-7, abs_tol=1e-5), (key, value, new[key])


def main():
    for name, digest in EXPECTED.items():
        assert sha(FROZEN / name) == digest, name
        if (ROOT / 'tank-lab/src' / name).exists():
            assert sha(ROOT / 'tank-lab/src' / name) == digest, name
    catalog = json.loads((ARCHIVE / 'input/catalog.json').read_text())['items']
    assert [(catalog[i]['id'], catalog[i]['name']) for i in (5, 6, 9, 22, 27, 33)] == [
        (529, '饮血剑'), (618, '斯特拉克的挑战护手'),
        (539, '鬼索的狂暴之刃'), (616, '圣盾使的誓约'),
        (581, '石像鬼石板甲'), (597, '狂徒铠甲')]
    scenarios = json.loads((ARCHIVE / 'input/scenarios.json').read_text())
    sc = scenarios[149]
    assert (sc['hero'], sc['star'], sc['traits'], sc['slots']) == ('蔚', 3, {'主宰': 6}, 6)
    assert all(27 in items for items in BUILDS.values())
    assert not OUT.exists(), f'Refusing overwrite: {OUT}'
    OUT.mkdir()
    (OUT / 'replays').mkdir()

    archived = {}
    with gzip.open(ARCHIVE / 'raw/scenario-149.runs.jsonl.gz', 'rt') as stream:
        for line in stream:
            row = json.loads(line)
            for key, items in BUILDS.items():
                if row['items'] == items and row['augment'] == 4:
                    archived[key] = row
            if len(archived) == 8:
                break
    assert len(archived) == 8, archived.keys()

    builds, settlements, replay_count = [], [], 0
    for key, items in BUILDS.items():
        old = archived[key]
        assert old['stages'][0]['dps'] == 300
        assert old['failedDps'] == old['passedDps'] + 50
        display = []
        for index, stage in enumerate(old['stages']):
            dps = stage['dps']
            assert dps == 300 + 50 * index
            params = parameters(items, dps)
            actual = run(params)
            same(stage['result'], actual['result'])
            result = actual['result']
            settlements.append(dict(build=key, dps=dps, frame=result['frame'],
                                    alive=result['alive'], result=result))
            if dps >= 1750:
                actual['frames'] = [[f[0], f[1], f[2], f[3], f[4], f[17]]
                                    for f in actual['frames']]
                display.append(dict(configurationId=old['id'], dps=dps,
                                    parameters=params, **actual))
                replay_count += 1
        assert settlements[-1]['dps'] == old['failedDps']
        assert display and display[0]['dps'] == 1750
        builds.append(dict(key=key, label=key, items=items,
                           itemNames=[catalog[i]['name'] for i in items],
                           passedDps=old['passedDps'], failedDps=old['failedDps'],
                           failedFrame=display[-1]['result']['frame'], chain=display))
        print(f'{key}: {old["passedDps"]} pass, {old["failedDps"]} fail, '
              f'{len(old["stages"])} attempted, {len(display)} display', flush=True)

    for build in builds:
        build['rank'] = 1 + sum(other['passedDps'] > build['passedDps'] for other in builds)
    source = dict(schemaVersion=2, purpose='vi-sterak-eight-comparison-video',
                  hero=dict(name='蔚', star=3, cost=3, traits={'主宰': 6},
                            slots=6, scenario=149),
                  aug=4, augLabel='单身板甲 · 独占一排',
                  environment=dict(seconds=30, fps=30, startDps=300, step=50,
                                   maxDps=20000, targetRes=50, physicalShare=.5,
                                   attackers=5, wound=.33, woundStart=0,
                                   woundEnd=5401, resistanceMode=3,
                                   lockFrames=30, pauseFrames=9, control=False,
                                   fixedDamagePacketsPerSecond=3),
                  source=dict(archive=str(ARCHIVE),
                              archiveModel='dataj-s18-skill-hecarim-20260922',
                              modelRevision='dataj-s18-vow-single-normal-shield-20260923',
                              engineSha256=EXPECTED['replay-native'],
                              selectedArchiveIds={key: archived[key]['id'] for key in BUILDS}),
                  builds=[{k: v for k, v in build.items() if k != 'rank'} for build in builds])
    (OUT / 'source-replays.json').write_text(
        json.dumps(source, ensure_ascii=False, separators=(',', ':')))
    results = dict(id='vi-sterak-eight-20260924',
                   metric='highest consecutive 50-DPS pass before first failure',
                   builds=[{k: v for k, v in build.items() if k != 'chain'} for build in builds],
                   attemptedStages=settlements)
    (OUT / 'results.json').write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n')
    report = dict(passed=True, modelRevision=source['source']['modelRevision'],
                  allBuildsUseSoloPlate=True, normalSterakItemId=618,
                  attemptedStageCount=len(settlements), displayReplayCount=replay_count,
                  oldArchiveResultComparisons=len(settlements),
                  perFrameConservationChecks=len(settlements),
                  sourceHashes={name: sha(FROZEN / name) for name in EXPECTED},
                  sourceSha256=sha(OUT / 'source-replays.json'),
                  resultsSha256=sha(OUT / 'results.json'))
    (OUT / 'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(dict(passed=True, stages=len(settlements),
                          displayReplays=replay_count,
                          ranking=[(b['key'], b['passedDps'], b['rank']) for b in builds]),
                     ensure_ascii=False))


if __name__ == '__main__':
    main()
