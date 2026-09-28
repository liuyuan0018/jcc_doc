"""Prepare the frozen Vi vow episode's content recipe for TTS and Unity export."""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'exports/frontline-vi-vow-eight-v1'
SOURCE = OUT / 'input'
RECIPE = OUT / 'vi-vow-recipe.json'
assert not RECIPE.exists()
(SOURCE / 'assets').mkdir(parents=True, exist_ok=True)
shutil.copyfile(OUT / 'source-replays.json', SOURCE / 'assets/vi-vow-data.json')
recipe = json.loads((ROOT / 'scripts/tank-video/vi-eight-recipe.json').read_text())
recipe.update(id='frontline-vi-vow-eight-v1', version=1,
              sourceDir='exports/frontline-vi-vow-eight-v1/input',
              outputDir='exports/frontline-vi-vow-eight-v1/content-pipeline',
              outputName='frontline-vi-vow-eight-v1.mp4',
              replayData='vi-vow-data.json', coverPath='cover/cover-9x16.png')
recipe['ui'].update(brand='蔚穿圣盾 · 8套配装模拟对照',
                    legend='A—H 固定位置 · 选定八套对照',
                    footnote='固定条件模拟 · 非实机对战 · 每档满血重开30秒',
                    resultFootnote='本次选定八套的持续承压对照 · 实战看对手、站位和阵容',
                    resultHeader='蔚穿圣盾 · 八套配装结果',
                    resultCondition='三星 · 6主宰 · 6人口 · 单身板甲 · 独占一排',
                    titleAux='蔚 · 圣盾八套')
recipe['timeline'].update(introMinSeconds=3.2, cueGapSeconds=0.35,
                          fastBattleSeconds=2.2, fastHoldSeconds=0.6,
                          normalHoldMinSeconds=1.8, resultMinSeconds=14.0)
recipe['program'] = dict(
    tiers=[dict(dps=d, speed='fast' if d in (1850, 1950, 2150) else 'normal',
                layout='solo' if d >= 2150 else 'eight')
           for d in range(1850, 2251, 50)],
    soloLane=0, focusCardId='A',
    anchors={
        'V01':dict(type='cover'),
        'V02':dict(type='intro'),
        'V03':dict(type='tierStart',tier=0,offset=0.1),
        'V04':dict(type='tierPassed',tier=0,offset=0.25),
        'V05':dict(type='death',tier=1,build='H',offset=3.1),
        'V06':dict(type='tierPassed',tier=2,offset=0.25),
        'V07':dict(type='death',tier=3,build='E',offset=0.5),
        'V08':dict(type='death',tier=4,build='G',offset=3.1),
        'V09':dict(type='death',tier=5,build='C',offset=3.1),
        'V10':dict(type='tierStart',tier=6,offset=0.1),
        'V11':dict(type='tierPassed',tier=6,offset=0.25),
        'V12':dict(type='tierPassed',tier=7,offset=0.25),
        'V13':dict(type='death',tier=8,build='A',offset=3.1),
        'V14':dict(type='result',offset=0.2),
        'V15':dict(type='result',offset=8.0),
    })
texts = [
    '蔚的饮血换成圣盾，再搭狂徒或者羊刀，会更能扛吗？',
    '这次选八套来对照。统一三星蔚、六主宰，带单身板甲，都是固定条件模拟。',
    '每档满血重开，撑满三十秒，再加五十来伤。先看饮血双板和圣盾双板，只换这一件。',
    '一千八百五，八套都过了，继续加。',
    '圣盾羊刀和双圣盾都没过一千九，最高通过一千八百五，并列。',
    '剩下六套通过，继续到两千。',
    '圣盾狂徒在两千这档停下，最高通过一千九百五。',
    '饮血羊刀、饮血加圣盾，都停在这一档，最高通过两千。',
    '圣盾双板和饮血狂徒，也都没过。两套最高通过两千零五十。',
    '剩下饮血双板，继续往上试。',
    '两千一百五通过，再加五十。',
    '两千二也撑满了三十秒。',
    '两千二百五没过，最高通过两千二。',
    '这组条件下，饮血双板最高；只把饮血换圣盾，少通过三档。其余换法的成绩也都在这里。',
    '这是本次八套的模拟对照，实战还要看对手、站位和阵容。',
]
recipe['cues'] = [dict(id=f'V{i:02}',text=t,spoken=t.replace('蔚','魏')) for i,t in enumerate(texts,1)]
RECIPE.write_text(json.dumps(recipe,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(recipe=str(RECIPE),cues=len(recipe['cues']),tiers=len(recipe['program']['tiers'])),ensure_ascii=False))
