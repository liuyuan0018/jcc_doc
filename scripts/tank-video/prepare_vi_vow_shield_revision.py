"""Create an isolated production input for the corrected double-Vow episode."""
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EPISODE = ROOT / 'exports/frontline-vi-vow-eight-v1'
REVISION = EPISODE / 'production-v3'
SOURCE = ROOT / 'research/vi-vow-topic-20260923/vow-shield-revision-v1'
HANDOFF = ROOT / 'posts/蔚圣盾八套-制作交接-20260923.md'
EXPECTED_SOURCE_SHA = '69cfce2f851f09fddf1965e8fe0b20301060d895968f70314fddb3a9a3e0af2e'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert sha(SOURCE / 'source-replays.json') == EXPECTED_SOURCE_SHA
    assert json.loads((SOURCE / 'verification.json').read_text())['passed']
    assert '修订版16句' in HANDOFF.read_text()
    recipe_path = REVISION / 'vi-vow-recipe.json'
    assert not recipe_path.exists(), f'Refusing overwrite: {recipe_path}'
    (REVISION / 'input/assets').mkdir(parents=True, exist_ok=True)
    (REVISION / 'input/cover').mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SOURCE / 'source-replays.json', REVISION / 'input/assets/vi-vow-data.json')
    shutil.copyfile(EPISODE / 'cover/cover-9x16-v2.png', REVISION / 'input/cover/cover-9x16.png')
    recipe = json.loads((EPISODE / 'vi-vow-recipe.json').read_text())
    recipe.update(id='frontline-vi-vow-eight-shield-v3', version=3,
                  sourceDir='exports/frontline-vi-vow-eight-v1/production-v3/input',
                  outputDir='exports/frontline-vi-vow-eight-v1/production-v3/content-pipeline',
                  outputName='frontline-vi-vow-eight-shield-v3.mp4')
    recipe['program']['tiers'] = [
        dict(dps=d, speed='fast' if d in (1750, 1850, 1950, 2150) else 'normal',
             layout='solo' if d >= 2150 else 'eight')
        for d in range(1750, 2251, 50)
    ]
    anchors = recipe['program']['anchors']
    anchors.update(V03=dict(type='tierStart', tier=0, offset=0.1),
                   V04=dict(type='tierPassed', tier=0, offset=0.25),
                   V05=dict(type='death', tier=1, build='H', offset=3.1),
                   V05B=dict(type='death', tier=3, build='F', offset=3.1),
                   V06=dict(type='tierPassed', tier=4, offset=0.25),
                   V07=dict(type='death', tier=5, build='E', offset=0.5),
                   V08=dict(type='death', tier=6, build='G', offset=3.1),
                   V09=dict(type='death', tier=7, build='C', offset=3.1),
                   V10=dict(type='tierStart', tier=8, offset=0.1),
                   V11=dict(type='tierPassed', tier=8, offset=0.25),
                   V12=dict(type='tierPassed', tier=9, offset=0.25),
                   V13=dict(type='death', tier=10, build='A', offset=3.1))
    cues = recipe['cues']
    by_id = {cue['id']: cue for cue in cues}
    for key, new_text in {
        'V04': '一千七百五，八套都过了，继续加。',
        'V05': '双冰甲没过一千八，最高通过一千七百五。',
    }.items():
        by_id[key]['text'] = new_text
        by_id[key]['spoken'] = new_text
        by_id[key].pop('displayLines', None)
    new_text = '冰甲羊刀在一千九这档停下，最高通过一千八百五。'
    cues.insert(next(i for i, cue in enumerate(cues) if cue['id'] == 'V05') + 1,
                dict(id='V05B', text=new_text, spoken=new_text))
    assert len(cues) == 16
    assert [cue['id'] for cue in cues] == [f'V{i:02}' for i in range(1, 6)] + ['V05B'] + [f'V{i:02}' for i in range(6, 16)]
    recipe_path.write_text(json.dumps(recipe, ensure_ascii=False, indent=2) + '\n')
    old_tts = EPISODE / 'content-pipeline/assets/tts'
    new_tts = REVISION / 'content-pipeline/assets/tts'
    shutil.copytree(old_tts, new_tts)
    print(json.dumps(dict(recipe=str(recipe_path), sourceSha256=EXPECTED_SOURCE_SHA,
                          cues=len(cues), tiers=len(recipe['program']['tiers']),
                          oldTtsFilesReused=len(list(new_tts.iterdir()))), ensure_ascii=False))


if __name__ == '__main__':
    main()
