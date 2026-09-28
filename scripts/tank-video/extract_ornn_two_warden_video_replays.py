"""Build the 150-350 Ornn presentation grid from verified frozen replays."""
import gzip
import hashlib
import json
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'research/ornn-two-warden-eight-20260923'
OUT = EVIDENCE / 'presentation-150-350-v1'
TOOLS = runpy.run_path(str(ROOT / 'scripts/tank-video/calculate_ornn_two_warden_eight.py'))
sha = TOOLS['sha']
run = TOOLS['run']
validate_replay = TOOLS['validate_replay']
parameters = TOOLS['parameters']


def main():
    outputs = (OUT / 'source-replays.json', OUT / 'verification.json')
    assert not any(path.exists() for path in outputs), 'Refusing to overwrite presentation evidence'
    inputs = json.loads((EVIDENCE / 'inputs.json').read_text())
    results = json.loads((EVIDENCE / 'results.json').read_text())
    verified = json.loads((EVIDENCE / 'verification.json').read_text())
    assert verified['passed'] and verified['stageRuns'] == 36
    assert sha(EVIDENCE / 'inputs.json') == verified['inputsSha256']
    assert sha(EVIDENCE / 'results.json') == verified['resultsSha256']
    for name, expected in verified['sourceHashes'].items():
        assert sha(EVIDENCE / 'input' / name) == expected, name
    assert inputs['scenario']['index'] == 3 and inputs['scenario']['hero'] == '奥恩'
    assert inputs['scenario']['star'] == 2 and inputs['scenario']['traits'] == {'护卫': 2}
    assert inputs['environment']['augment'] == 0 and not inputs['environment']['soloPlate']
    assert verified['allItemsOrdinary'] and verified['noArtifactProgress']

    builds, stages, generated, reused = [], [], 0, 0
    for row in results['builds']:
        key = row['key']
        expected_stages = {stage['dps']: stage for stage in row['stages']}
        source_files = {item['dps']: item for label, item in verified['replayFiles'].items()
                        if label.startswith(key + ':')}
        chain = []
        for dps in range(150, min(350, row['failedDps']) + 1, 50):
            expected = expected_stages.get(dps)
            params = parameters(row['itemIndexes'], dps)
            if expected:
                assert params == expected['parameters']
            if dps in source_files:
                saved = source_files[dps]
                path = EVIDENCE / saved['path']
                assert sha(path) == saved['sha256']
                replay = json.loads(gzip.decompress(path.read_bytes()))
                origin = 'verified-replay'
                reused += 1
            else:
                replay = dict(parameters=params,
                              **run(EVIDENCE / inputs['engine'], params))
                origin = 'frozen-cli-supplement'
                generated += 1
            assert replay['parameters'] == params
            validate_replay(replay)
            if expected:
                assert replay['result'] == expected['result'], (key, dps)
            else:
                assert dps < row['passedDps'] and replay['result']['alive'], (key, dps)
                assert replay['result']['frame'] == 900
            assert bool(replay['frames'][-1][17]) == bool(replay['result']['alive'])
            full_frame_count = len(replay['frames'])
            replay['frames'] = [[frame[index] for index in (0, 1, 2, 3, 4, 17)]
                                for frame in replay['frames']]
            chain.append(dict(configurationId=f'ornn-2warden-{key}', dps=dps, **replay))
            stages.append(dict(build=key, dps=dps, origin=origin,
                               alive=replay['result']['alive'],
                               frame=replay['result']['frame'],
                               frameCount=full_frame_count,
                               presentationEvents=len(replay['presentation']['events'])))
        assert chain[0]['result']['alive'] and not chain[-1]['result']['alive']
        assert chain[-2]['dps'] == row['passedDps'] and chain[-1]['dps'] == row['failedDps']
        builds.append(dict(key=key, label=key, items=row['itemIndexes'],
                           itemNames=row['itemNames'], passedDps=row['passedDps'],
                           failedDps=row['failedDps'], failedFrame=row['failedFrame'],
                           chain=chain))
    assert (len(stages), reused, generated) == (30, 16, 14)
    assert {row['key']: row['passedDps'] for row in builds} == dict(
        A=200, B=200, C=150, D=300, E=300, F=250, G=200, H=300)
    payload = dict(schemaVersion=2, purpose='selected-8-ornn-two-warden-video',
                   hero=dict(name='奥恩', star=2, cost=1, traits={'护卫': 2},
                             slots=2, scenario=3), aug=0, augLabel='无指定海克斯',
                   environment=inputs['environment'],
                   source=dict(modelRevision=inputs['modelRevision'],
                               evidence=str(EVIDENCE),
                               originalInputsSha256=verified['inputsSha256'],
                               originalResultsSha256=verified['resultsSha256'],
                               engineSha256=verified['sourceHashes']['replay-native']),
                   builds=builds)
    OUT.mkdir(parents=True, exist_ok=True)
    source_bytes = json.dumps(payload, ensure_ascii=False, separators=(',', ':')).encode()
    outputs[0].write_bytes(source_bytes)
    report = dict(passed=True, stageCount=len(stages), reusedReplays=reused,
                  frozenCliSupplements=generated,
                  sourceSha256=hashlib.sha256(source_bytes).hexdigest(),
                  expectedResultsSha256=verified['resultsSha256'], stages=stages)
    outputs[1].write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(dict(passed=True, stages=len(stages), reused=reused,
                          generated=generated, source=str(outputs[0]),
                          sha256=report['sourceSha256']), ensure_ascii=False))


if __name__ == '__main__':
    main()
