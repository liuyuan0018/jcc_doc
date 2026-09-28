"""Apply the approved player-facing Ice Armor terminology to the episode recipe."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
path = ROOT / 'exports/frontline-vi-vow-eight-v1/vi-vow-recipe.json'
recipe = json.loads(path.read_text())
for key, value in recipe['ui'].items():
    if isinstance(value, str): recipe['ui'][key] = value.replace('圣盾', '冰甲')
for cue in recipe['cues']:
    cue['text'] = cue['text'].replace('圣盾', '冰甲')
    cue['spoken'] = cue['spoken'].replace('圣盾', '冰甲')
recipe['program']['anchors']['V15']['offset'] = 9.35
recipe['timeline']['normalSimRate'] = 4.8
breaks = {
    'V01':['蔚的饮血换成冰甲，再搭狂徒或者羊刀，','会更能扛吗？'],
    'V02':['这次选八套来对照。统一三星蔚、六主宰，','带单身板甲，都是固定条件模拟。'],
    'V03':['每档满血重开，撑满三十秒，再加五十来伤。','先看饮血双板和冰甲双板，只换这一件。'],
    'V05':['冰甲羊刀和双冰甲都没过一千九，','最高通过一千八百五，并列。'],
    'V07':['冰甲狂徒在两千这档停下，','最高通过一千九百五。'],
    'V08':['饮血羊刀、饮血加冰甲，都停在这一档，','最高通过两千。'],
    'V09':['冰甲双板和饮血狂徒，也都没过。','两套最高通过两千零五十。'],
    'V14':['这组条件下，饮血双板最高；只把饮血换冰甲，','少通过三档。其余换法的成绩也都在这里。'],
    'V15':['这是本次八套的模拟对照，','实战还要看对手、站位和阵容。'],
}
for cue in recipe['cues']:
    if cue['id'] in breaks:
        assert ''.join(breaks[cue['id']]) == cue['text']
        cue['displayLines'] = breaks[cue['id']]
path.write_text(json.dumps(recipe, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(dict(recipe=str(path), affected=[c['id'] for c in recipe['cues'] if '冰甲' in c['text']]),ensure_ascii=False))
