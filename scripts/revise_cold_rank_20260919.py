"""Add the verified physical Kog'Maw option to the existing cold-build package."""
from pathlib import Path
import copy
import hashlib
import json
import re
import subprocess
import xml.etree.ElementTree as ET

R = Path(__file__).resolve().parents[1]
OLD = R / 'exports/S18冷门榜-20260919'
OUT = R / 'exports/S18冷门榜-20260919-修订版'
P = R / 'outputs/cold-revision-20260919'
REG = R / 'exports/S18常规榜-20260919-修订版'
NODE = '/Users/lyu/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
OUT.mkdir(exist_ok=True)
P.mkdir(exist_ok=True)
NS = 'http://www.w3.org/2000/svg'
ET.register_namespace('', NS)

kog = json.loads((R/'outputs/regular-revision-20260919/comp119.json').read_text())['data']
triples = json.loads((R/'outputs/regular-revision-20260919/kog-ad-equips.json').read_text())['data']['hero3Equips']
triple = next(t for t in triples if set(t['equipIds']) == {2001, 2045, 2046})
assert (triple['sampleCount'], triple['top4Rate'], triple['topRate']) == (108, 59.26, 9.26)

for src in sorted(OLD.glob('*.svg')):
    text = src.read_text()
    if not src.name.startswith('01-'):
        text, count = re.subn(r'(\d{2}) / 06', r'\1 / 07', text)
        assert count == 1, src
    (OUT/src.name).write_text(text)

cover = OUT/'01-冷门构筑强度榜.svg'
root = ET.fromstring(cover.read_text())
group = root.find(f'{{{NS}}}g')
children = list(group)
starts = [i for i,e in enumerate(children) if e.tag == f'{{{NS}}}rect' and e.get('x') == '40' and e.get('width') == '1000' and e.get('height') == '172']
assert len(starts) == 5
ends = [starts[1], starts[2], 64, starts[4], 97]
original_last_row = [copy.deepcopy(e) for e in children[starts[-1]:ends[-1]]]

def move_row(nodes, offset):
    for element in nodes:
        for node in element.iter():
            if 'y' in node.attrib:
                y = float(node.get('y')) + offset
                node.set('y', str(y).removesuffix('.0'))
            if node.tag == f'{{{NS}}}rect' and node.get('height') == '172':
                node.set('height', '158')
    # Last text is the existing conditional-use line; lift it inside the shorter row.
    last_text = next(e for e in reversed(nodes) if e.tag == f'{{{NS}}}text')
    last_text.set('y', str(float(last_text.get('y'))-13).removesuffix('.0'))

for start,end,old_y,new_y in zip(starts,ends,[356,547,738,1042,1233],[356,534,712,939,1117]):
    move_row(children[start:end], new_y-old_y)

replacements = {
    '18.2a · 纹章 / 神器': '18.2a · 条件玩法',
    '3套条件强势＋2套观察': '3套条件强势＋3套观察',
    '小样本观察 · 英雄携装分项，不与上面直排': '顺牌与小样本观察 · 各分项单独看',
    '统计不是图示三件套的独立成绩；运营与补装为整理建议。': '大嘴为三件套分项；其余五套未锁三件套，不能直接横排。',
    '没关键装备？主页看《常规阵容榜》': '更多上分阵容，主页看《常规阵容榜》',
    '九套完整站位＋装备＋阵容码｜同系列另一篇': '九套主选＋神谕大嘴备选｜站位、装备、阵容码',
    '图2—6看玩法、开局与翻车点 · 基础框架码见正文': '图2—7看玩法、开局与翻车点 · 六套框架码见正文',
    '不同口径分区呈现，不混成统一胜率排名。': '前3套体系内携装；天使、螳螂为英雄携装；大嘴为三件套。',
    '五费成型有偏差；小样本不是稳定上分保证。': '携装样本有成型偏差；小样本不是稳定上分保证。',
}
found = set()
for e in group.findall(f'{{{NS}}}text'):
    original = e.text
    if original in replacements:
        e.text = replacements[original]
        found.add(original)
    if original == '小样本观察 · 英雄携装分项，不与上面直排':
        e.set('y', '915')
    if original == '统计不是图示三件套的独立成绩；运营与补装为整理建议。':
        e.set('y', '1495')
        e.set('font-size', '24')
    if original == '不同口径分区呈现，不混成统一胜率排名。':
        e.set('font-size', '22')
assert found == set(replacements)

# Reuse already checked portrait and item images from the regular cover.
reg_root = ET.parse(REG/'01-常规阵容强度榜.svg').getroot()
reg_images = [e for e in reg_root.iter(f'{{{NS}}}image') if 1416 <= float(e.get('y')) < 1527]
assert len(reg_images) == 4
move_row(original_last_row, 1295-1233)
new_images = [e for top in original_last_row for e in top.iter(f'{{{NS}}}image')]
assert len(new_images) == 4
for dest,src in zip(new_images,reg_images):
    dest.set('href',src.get('href'))
new_text = {
    '花妖转螳螂':'神谕大嘴', '卡兹克':'克格莫 · 物理三件套',
    '均排4.13 · 样本117':'均排4.14 · 样本108',
    '61.5%':'59.3%', '13.7%':'9.3%',
    '117个携装样本，先当试玩线索。':'普通装备可玩；大嘴、人马来得顺再追。',
}
for top in original_last_row:
    for e in top.iter():
        if e.tag == f'{{{NS}}}text' and e.text in new_text:
            e.text = new_text[e.text]
        if 'id' in e.attrib:
            e.set('id','cold-kog-'+e.get('id'))
        if 'clip-path' in e.attrib:
            e.set('clip-path',e.get('clip-path').replace('url(#','url(#cold-kog-'))
for i,e in enumerate(original_last_row):
    group.insert(97+i,e)
cover.write_text(ET.tostring(root,encoding='unicode'))

board = (REG/'12-神谕大嘴.svg').read_text()
assert '12 / 12' in board
(OUT/'07-神谕大嘴.svg').write_text(board.replace('12 / 12','07 / 07'))

body = '''纹章、神器到了手，再考虑花妖转凯南、猎人转巨龙和暗爪卡蜜尔。五费分支要有经济和血量，一费分支先看来牌。

没有专属纹章或神器，但大嘴、人马来得多、物理装也合适，可以考虑神谕大嘴：7级先凑两星和前排，来牌多再追大嘴三星。站位、装备和搜牌看图7。

护臂天使、花妖转螳螂分别只有116/117个携装样本，先当有条件的尝试。大嘴无尽＋锐利之刃＋巨杀是108样本、前四59.26%；体系整体前四50.21%，别把成型数据当成开局硬玩的成功率。

图2—7看完整站位、主C装备与翻车点。其他常规阵容看主页《常规阵容榜》。

下面是基础框架码，尚未做游戏内导入校验；导入后对照图片调整英雄、站位和装备：

花妖转凯南（地狱火95框架）
MjIwMDY3MzAyODc5ODA4NTYxNzg5MjQwODA3MzIw

猎人转巨龙（巨龙95框架）
MjIwMDY3MzAyODc5ODA4NTYxNzg3MTgyMDgwODEz

暗爪卡蜜尔
MjIwMDY3MzAyODc5ODA4NTYxNzg5MTEwOTYxNDE2

护臂天使（森林天使框架）
MjIwMDY3MzAyODc5ODA4NTYxNzg3MTgxOTg4MDM0

花妖转螳螂（裁决螳螂框架）
MjIwMDY3MzAyODc5ODA4NTYxNzg5MjE4MDI5MTQ5

神谕大嘴（7人口核心）
''' + kog['gameCode'].split('#')[-1] + '''

前3套看体系内携装，天使、螳螂看英雄携装，大嘴三件套单列，不能直接横排强度。
数据：DataJ非官方高分段样本，18.2a，9/19 03:32。运营建议尚无逐局实战复核。'''
assert len(body) < 930, len(body)
assert len(re.findall(r'MjIw\w+',body)) == 6
(P/'cold-body.txt').write_text(body+'\n')
(P/'cold-title.txt').write_text('金铲铲S18冷门榜9.19｜附阵容码')

checks=[]
for src in sorted(OUT.glob('*.svg')):
    ET.parse(src)
    subprocess.run([NODE,str(R/'scripts/export_png.cjs'),str(src),str(src.with_suffix('.png'))],check=True,capture_output=True)
    checks.append({'file':src.name,'png_sha256':hashlib.sha256(src.with_suffix('.png').read_bytes()).hexdigest()})
manifest = {'status':'rendered_pending_visual_QA','baseline':str(OLD),'output':str(OUT),
    'images':[str(p) for p in sorted(OUT.glob('*.png'))], 'note_id':'6aacd475000000002b01f439',
    'operation':'edit_existing','publish_permission':'USER_WILL_CLICK_DO_NOT_SUBMIT','body_length':len(body),
    'body_codes':6,'cover_rows':6,'kog_statistics':{'system':kog,'triple':triple},
    'source_updated_at':'2026-09-18T19:32:50.884Z','collection':'s18金铲铲阵容数据库',
    'preservation':'Existing five detail cards differ only in total page count; seventh card reuses verified Kog card with new page number.'}
assert len(manifest['images']) == 7
(P/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
(P/'artifact-checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'images':7,'body_length':len(body),'codes':6},ensure_ascii=False))
