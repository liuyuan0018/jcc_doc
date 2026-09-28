"""Prepare the approved Vi Sterak episode recipe without rendering."""

import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'exports/frontline-vi-sterak-eight-v1/production-v1'
SOURCE = ROOT / 'research/vi-sterak-eight-20260924/source-replays.json'
COVER = ROOT / 'exports/frontline-vi-sterak-eight-v1/cover/cover-9x16-v1.png'
BASE = ROOT / 'exports/frontline-vi-vow-eight-v1/production-v3/vi-vow-recipe.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cue(number, text, display=None):
    row = dict(id=f'V{number:02}', text=text, spoken=text.replace('蔚', '魏'))
    if display:
        row['displayLines'] = display
        row['text'] = ''.join(display)
    return row


def main():
    assert SOURCE.exists() and COVER.exists()
    source = json.loads(SOURCE.read_text())
    assert len(source['builds']) == 8 and sum(len(b['chain']) for b in source['builds']) == 45
    assert not OUT.exists(), f'Refusing overwrite: {OUT}'
    (OUT / 'input/assets').mkdir(parents=True)
    (OUT / 'input/cover').mkdir(parents=True)
    shutil.copyfile(SOURCE, OUT / 'input/assets/vi-sterak-data.json')
    shutil.copyfile(COVER, OUT / 'input/cover/cover-9x16.png')

    recipe = json.loads(BASE.read_text())
    recipe.update(id='frontline-vi-sterak-eight-v1', version=1,
                  sourceDir='exports/frontline-vi-sterak-eight-v1/production-v1/input',
                  outputDir='exports/frontline-vi-sterak-eight-v1/production-v1/content-pipeline',
                  outputName='frontline-vi-sterak-eight-v1.mp4',
                  replayData='vi-sterak-data.json', coverPath='cover/cover-9x16.png')
    recipe['immutable'] = [
        dict(path='research/vi-sterak-eight-20260924/source-replays.json', sha256=sha(SOURCE)),
        dict(path='exports/frontline-vi-sterak-eight-v1/cover/cover-9x16-v1.png', sha256=sha(COVER)),
    ]
    recipe['protectedOutputDirs'] = ['exports/frontline-vi-vow-eight-v1',
                                     'exports/frontline-ornn-two-warden-eight-v1']
    recipe['ui'].update(
        brand='蔚带血手 · 8套配装模拟对照',
        legend='A—H 固定位置 · 选定八套对照',
        footnote='固定条件模拟 · 非实机对战 · 每档满血重开30秒',
        resultFootnote='A→B 少6档 · A→C 少5档 · 本次选定八套',
        resultHeader='蔚带血手 · 八套配装结果',
        resultCondition='三星 · 6主宰 · 6人口 · 单身板甲 · 独占一排',
        titleAux='蔚 · 血手八套',
    )
    recipe['timeline'].update(introMinSeconds=3.2, cueGapSeconds=.35,
                              normalSimRate=8.0,
                              fastBattleSeconds=2.2, fastHoldSeconds=.6,
                              normalHoldMinSeconds=1.8, resultMinSeconds=20.0)
    speeds = {1750: 'fast', 1900: 'fast', 2150: 'fast'}
    recipe['program'] = dict(
        tiers=[dict(dps=d, speed=speeds.get(d, 'normal'),
                    layout='solo' if d >= 2150 else 'eight')
               for d in range(1750, 2251, 50)],
        soloLane=0, focusCardId='A',
        anchors={
            'V01': dict(type='cover'),
            'V02': dict(type='intro'),
            'V03': dict(type='tierStart', tier=0, offset=.1),
            'V04': dict(type='tierPassed', tier=0, offset=.25),
            'V05': dict(type='death', tier=1, build='H', offset=3.1),
            'V06': dict(type='death', tier=2, build='F', offset=3.1),
            'V07': dict(type='death', tier=4, build='B', offset=3.1),
            'V08': dict(type='death', tier=5, build='C', offset=3.1),
            'V09': dict(type='death', tier=6, build='G', offset=3.1),
            'V10': dict(type='death', tier=7, build='E', offset=3.1),
            'V11': dict(type='tierStart', tier=8, offset=.1),
            'V12': dict(type='tierPassed', tier=8, offset=.25),
            'V13': dict(type='tierPassed', tier=9, offset=.25),
            'V14': dict(type='death', tier=10, build='A', offset=3.1),
            'V15': dict(type='result', offset=.2),
            'V16': dict(type='result', offset=11.2),
        })
    recipe['cues'] = [
        cue(1, '有朋友想看蔚带血手。是替掉饮血，还是留着饮血，换一件板甲？',
            ['斯特拉克的挑战护手（血手）：', '替饮血，还是留饮血换一件板甲？']),
        cue(2, '这次选八套，统一三星蔚、六主宰和单身板甲，做固定条件模拟。',
            ['这次选八套：三星蔚、六主宰、单身板甲，', '统一做固定条件模拟。']),
        cue(3, '每档满血重开，撑满三十秒，再加五十来伤。先看前三套，只换一件装备。',
            ['每档满血重开，撑满三十秒，再加五十来伤。', '先看前三套，只换一件装备。']),
        cue(4, '一千七百五，八套都过了，继续加。'),
        cue(5, '血手、板甲加羊刀先停下，最高通过一千七百五。',
            ['血手、板甲加羊刀先停下，', '最高通过一千七百五。']),
        cue(6, '血手搭冰甲和狂徒的两套，都没过这一档，最高通过一千八，算并列。',
            ['血手搭冰甲和狂徒的两套，都没过1850；', '最高通过1800，并列。']),
        cue(7, '血手双板也没撑住，最高通过一千九。'),
        cue(8, '饮血、板甲加血手，最高通过一千九百五。这次带血手的五套，到这里都停下了。',
            ['饮血、板甲加血手，最高通过1950。', '带血手的五套，到这里都停下了。']),
        cue(9, '饮血、冰甲加板甲，最高通过两千。'),
        cue(10, '饮血、板甲加狂徒，最高通过两千零五十。'),
        cue(11, '饮血双板还在，继续加压。'),
        cue(12, '两千一百五通过。'),
        cue(13, '两千二，也撑满了三十秒。'),
        cue(14, '两千二百五没过，最高通过两千二。'),
        cue(15, '这组条件下，血手替饮血，少通过六档；留着饮血，换一件板甲，少通过五档。两种换法都没超过饮血双板。',
            ['A→B：2200→1900，少6档。', 'A→C：2200→1950，少5档。']),
        cue(16, '这五套血手搭配里，饮血加板甲最高。但不同星级、羁绊和对手，不能直接照搬。',
            ['五套血手搭配里，饮血加板甲最高。', '星级、羁绊和对手不同，不能照搬。']),
    ]
    path = OUT / 'recipe.json'
    path.write_text(json.dumps(recipe, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(dict(recipe=str(path), tiers=11, cues=16,
                          sourceSha256=sha(SOURCE)), ensure_ascii=False))


if __name__ == '__main__':
    main()
