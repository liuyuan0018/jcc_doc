"""Bounded revision: preserve nine ranked boards, add an evidenced Kog'Maw option."""
from pathlib import Path
import base64
import copy
import html
import json
import re
import subprocess
import urllib.request
import xml.etree.ElementTree as ET

R = Path(__file__).resolve().parents[1]
P = R / 'outputs/regular-revision-20260919'
OLD = R / 'exports/S18常规榜-20260919'
OUT = R / 'exports/S18常规榜-20260919-修订版'
OUT.mkdir(exist_ok=True)
NODE = '/Users/lyu/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
g = json.loads((P / 'gamedata.json').read_text())['data']
heroes = {h['name']: h for h in g['hero']}
equips = {str(e['id']): e for e in g['equip']}
rank = json.loads((P / 'rank.json').read_text())['data']
kog = json.loads((P / 'comp119.json').read_text())['data']
triple = next(x for x in json.loads((P / 'kog-ad-equips.json').read_text())['data']['hero3Equips'] if set(x['equipIds']) == {2001, 2045, 2046})
assert (kog['sampleCount'], kog['top4Rate']) == (966, 50.21)
assert (triple['sampleCount'], triple['top4Rate']) == (108, 59.26)

def replace(s, a, b):
    assert a in s, a
    return s.replace(a, b)

# Existing artwork is the baseline; only named text and page totals change.
for src in sorted(OLD.glob('*.svg')):
    s = src.read_text()
    s = re.sub(r'(\d{2}) / 11', r'\1 / 12', s)
    if src.name.startswith('01-'):
        s = replace(s, '7套S＋2套A · 前四率排序', '9套主选 · 按体系前四率排序')
        s = replace(s, '有纹章 / 神器？主页看《冷门构筑榜》', '新增备选：神谕大嘴（图12）')
        s = replace(s, '花妖凯南 · 猎人巨龙 · 暗爪卡蜜尔｜同系列另一篇', '物理装顺、来牌多再玩；补充玩法不参与上方排序')
        s = replace(s, '图2选阵容 · 图3—11站位装备 · 九套码见正文', '图2选阵容 · 十套码见正文 · 特殊装备看主页《冷门榜》')
        s = replace(s, '18.2a独立样本57,568局', '18.2a版本样本57,568')
        s = replace(s, '体系前四率排序；小样本有波动，分档沿用来源。', '体系数据不等于指定出装或开局硬玩的成功率。')
    if src.name.startswith('03-'):
        s = replace(s, '九人口运营 / 艾希带转', '九人口运营 / 轮子与艾希分装')
        s = replace(s, '有地狱火转，物理装合适且能升9时考虑。', '轮子物理装顺；艾希分支需地狱火转。')
        s = replace(s, '先用两星牌稳血，升9找艾希、凯南和前排。', '先用两星牌稳血，8级补质量，再看经济上9。')
        s = replace(s, '艾希带转分项：前四77.66% / 1192样本，非体系胜率。', '艾希带转：2,366样本 / 前四75.91%，非体系胜率。')
    (OUT / src.name).write_text(s)

ASSETS = []
def asset(d):
    url = d['picture']
    p = R / 'assets/ranking' / Path(url).name
    if not p.exists():
        p.write_bytes(urllib.request.urlopen(url, timeout=20).read())
    ASSETS.append({'name': d['name'], 'source': url, 'path': str(p)})
    return 'data:image/png;base64,' + base64.b64encode(p.read_bytes()).decode()

class Card:
    def __init__(self, height=1653):
        self.height = height
        self.o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="{height}">',
                  f'<rect width="1080" height="{height}" fill="#f0edf8"/>',
                  '<path d="M795 0H1080V208H940Z" fill="#e5dcf4"/>',
                  '<g font-family="PingFang SC, sans-serif">']
    def t(self, x, y, text, size=28, color='#281e39', weight=500):
        self.o.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{weight}">{html.escape(str(text))}</text>')
    def rect(self, x, y, w, h, color='#fff', r=12):
        self.o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{color}"/>')
    def pic(self, data, x, y, size):
        q = f'clip{len(self.o)}'
        self.o.append(f'<clipPath id="{q}"><rect x="{x}" y="{y}" width="{size}" height="{size}" rx="6"/></clipPath>')
        self.o.append(f'<image href="{asset(data)}" x="{x}" y="{y}" width="{size}" height="{size}" clip-path="url(#{q})"/>')
    def save(self, name):
        self.o.append('</g></svg>')
        path = OUT / f'{name}.svg'
        path.write_text('\n'.join(self.o))

c = Card()
c.t(48, 61, '09.19 / 常规榜阅读指南', 25, '#753cf4', 750)
c.t(48, 147, '今天怎么选', 62, weight=850)
c.t(50, 203, '9套主选＋神谕大嘴备选 · 先看装备、来牌和经济', 27, '#756187')
blocks = [
    ('新增：神谕大嘴，来牌顺再玩',
     '物理装顺，大嘴与前排来得多，再考虑这条线。',
     '7级追大嘴；石甲虫、人马按数量选一个主坦追三。'),
    ('地狱火分清轮子和艾希',
     '轮子拿物理输出装；艾希分支需要地狱火转。',
     '封面65.3%是体系统计，两条分支未分别排强度。'),
    ('九五先稳血；低费看数量',
     '地狱火、巨龙、古纳拉：8级补质量，再考虑上9。',
     '小红先追三；女警、螳螂按来牌走各自的追三路线。'),
    ('裁决婕拉暂不补进主推',
     '裁决转＋青龙刀＋虚空杖：205样本，前四45.85%。',
     '这是对应体系内的婕拉三件套分项，有转也别硬冲。'),
]
for j, (title, line1, line2) in enumerate(blocks):
    y = 282 + j * 259
    c.rect(42, y, 996, 232)
    c.t(68, y + 57, title, 35, weight=800)
    c.t(68, y + 118, line1, 28)
    c.t(68, y + 174, line2, 26, '#756187')
c.t(48, 1380, '图3—11看主选站位；图12看神谕大嘴，十套码见正文。', 29, weight=750)
c.rect(42, 1430, 996, 133, '#753cf4')
c.t(65, 1477, '有特殊纹章 / 神器 · 到主页看', 25, 'white', 700)
c.t(65, 1528, '→ 冷门构筑榜', 38, 'white', 850)
c.t(47, 1611, 'DataJ 非官方高分段样本 · 18.2a · 数据截至9/19 03:32', 21, '#84718f')
c.save('02-今天怎么选')

# Seven-unit core is a diagram, not a claim about a population-filtered statistic.
c = Card(1851)
c.t(48, 58, '金铲铲之战 / S18 · 18.2a', 23, '#753cf4', 750)
c.t(905, 58, '12 / 12', 24, weight=750)
c.t(45, 145, '神谕大嘴', 65, weight=850)
c.rect(660, 92, 380, 63, '#fff0d5')
c.t(689, 134, '来牌顺的补充选项', 32, '#9b5920', 800)
c.t(48, 204, '7人口核心 · 5神谕 / 3野怪 / 2重装 · 物理出装', 27, '#756187')
c.t(48, 249, '神谕体系：966样本 · 前四50.21% · 登顶10.25% · 均名4.50', 24, '#756187')
c.rect(40, 278, 1000, 469)
c.t(61, 314, '参考站位 · 上方为敌方', 23, '#84718f')
c.t(643, 314, '大嘴追三；前排按来牌选主坦', 22, '#84718f')
bypos = {h['position']: h for h in kog['heroes']}
assert len(bypos) == len(kog['heroes']) == 7
names_short = {'苍蓝雕纹魔像': '苍蓝雕纹魔像', '远古石甲虫': '远古石甲虫'}
for row in range(4):
    for col in range(7):
        x, y = 61 + col * 133 + (25 if row % 2 else 0), 330 + row * 99
        h = bypos.get(f'{row+1},{col+1}')
        c.rect(x, y, 119, 92, '#eee6f6' if h else '#faf8fc', 8)
        if h:
            name = h['heroName']
            c.pic(heroes[name], x + 31, y + 5, 58)
            if name == '克格莫':
                c.rect(x+84, y+4, 31, 21, '#fff1bb', 4)
                c.t(x+85, y+20, '3★', 15, '#946b0b', 800)
            sz = 18 if len(name) > 5 else 21
            c.t(x + (119-len(name)*sz)/2, y+83, name, sz, weight=650)

c.t(44, 798, '装备与合成参考', 32, weight=800)
c.t(47, 840, '大嘴：无尽＋锐利之刃＋巨杀；物理路线，别按法系配装。', 26, '#756187')
gear_names = ['克格莫', '远古石甲虫', '赫卡里姆']
gear_ids = [[2001, 2045, 2046], [2028, 2023, 2025], [2025, 2028, 2034]]
short = {'石像鬼石板甲': '石像鬼板甲', '圣盾使的誓约': '圣盾使誓约'}
for j, (name, ids) in enumerate(zip(gear_names, gear_ids)):
    y = 866 + j * 104
    c.rect(42, y, 996, 93)
    c.pic(heroes[name], 57, y+17, 58)
    c.t(129, y+53, name, 23, weight=750)
    for k, eid in enumerate(ids):
        x = 329 + k * 228
        e = equips[str(eid)]
        c.pic(e, x, y+16, 49)
        c.t(x+57, y+39, short.get(e['name'], e['name']), 21, '#54415f', 650)
        for j2, component in enumerate([e['synthesis1'], e['synthesis2']]):
            assert str(component) in equips
            c.pic(equips[str(component)], x+59+j2*51, y+53, 24)
        c.t(x+88, y+72, '+', 19, '#84718f', 700)
c.t(48, 1203, '前排只优先做一套肉装，给先到两星、后续更容易追三的主坦。', 25, '#756187')
c.rect(42, 1235, 996, 186)
c.t(66, 1278, '为什么这样玩', 30, '#753cf4', 800)
c.t(66, 1323, '5神谕给回蓝，物理大嘴靠连续施法打伤害。', 28)
c.t(66, 1369, '技能会打目标和附近另一人；别把“瞬秒后排”当固定效果。', 26, '#756187')
c.rect(42, 1444, 996, 191)
c.t(66, 1487, '什么时候继续追，什么时候先稳场', 30, '#753cf4', 800)
c.t(66, 1532, '7级先凑两星与前排，来牌多再追大嘴三星。', 28)
c.t(66, 1578, '同行多、牌少或血量危险就先补战力，别死守利息等三星。', 26, '#756187')
c.rect(42, 1660, 996, 117, '#fff0d5')
c.t(64, 1699, '对应三件套分项：108样本 · 前四59.26% · 登顶9.26%', 27, '#9b5920', 750)
c.t(64, 1742, '均名4.14；携装样本有成型偏差，不能当作开局硬玩的成功率。', 24, '#756187')
c.t(47, 1821, 'DataJ comp/119 · 18.2a · 截至9/19 03:32｜前排补装与运营为整理建议', 20, '#84718f')
c.save('12-神谕大嘴')

# Put the supplement on the cover as a full row, preserving the nine main entries.
cover = OUT / '01-常规阵容强度榜.svg'
svg_ns = 'http://www.w3.org/2000/svg'
ET.register_namespace('', svg_ns)
root = ET.fromstring(cover.read_text())
group = root.find(f'{{{svg_ns}}}g')
assert group is not None
children = list(group)
row_starts = [i for i, el in enumerate(children) if el.tag == f'{{{svg_ns}}}rect' and el.get('x') == '40' and el.get('width') == '1000' and el.get('height') == '125']
assert len(row_starts) == 9
footer_start = next(i for i, el in enumerate(children) if el.tag == f'{{{svg_ns}}}rect' and el.get('y') == '1550')
for index, begin in enumerate(row_starts):
    end = row_starts[index+1] if index < 8 else footer_start
    offset = -14 * index
    for el in children[begin:end]:
        for node in el.iter():
            if 'y' in node.attrib:
                node.set('y', str(float(node.get('y')) + offset).removesuffix('.0'))
            if node.tag == f'{{{svg_ns}}}rect' and node.get('height') == '125':
                node.set('height', '111')

row = Card()
row.o = []
y = 309 + 9 * 123
row.rect(40, y, 1000, 111, '#fff3df', 9)
row.rect(40, y, 5, 111, '#c99343', 2)
row.pic(heroes['克格莫'], 62, y+18, 87)
row.t(166, y+45, '神谕大嘴', 30, weight=800)
row.t(168, y+75, '顺牌备选 · 克格莫', 17, '#9b5920')
row.t(167, y+107, '均排4.50 · 样本966', 20, '#796987')
for j, eid in enumerate([2001, 2045, 2046]):
    row.pic(equips[str(eid)], 409+j*61, y+36, 48)
row.t(665, y+74, '50.2%', 49, '#753cf4', 850)
row.t(861, y+74, '10.3%', 43, '#bd552e', 800)
new_group = ET.fromstring(f'<g xmlns="{svg_ns}">' + '\n'.join(row.o) + '</g>')
# Prefix clip identifiers so the new row cannot collide with existing cover IDs.
for node in new_group.iter():
    if 'id' in node.attrib:
        node.set('id', 'kog-' + node.get('id'))
    if 'clip-path' in node.attrib:
        node.set('clip-path', node.get('clip-path').replace('url(#', 'url(#kog-'))
group.insert(footer_start, new_group)
relabels = {
    '9套主选 · 按体系前四率排序': '9套主选＋1套顺牌备选',
    '新增备选：神谕大嘴（图12）': '有纹章 / 神器？主页看《冷门构筑榜》',
    '物理装顺、来牌多再玩；补充玩法不参与上方排序': '花妖凯南 · 猎人巨龙 · 暗爪卡蜜尔｜同系列另一篇',
    '图2选阵容 · 十套码见正文 · 特殊装备看主页《冷门榜》': '图2选阵容 · 图3—12站位与装备 · 十套码见正文',
    '体系数据不等于指定出装或开局硬玩的成功率。': '九套主选按体系前四率排序；神谕大嘴单列为顺牌备选。',
}
for node in root.iter(f'{{{svg_ns}}}text'):
    if node.text in relabels:
        node.text = relabels[node.text]
cover.write_text(ET.tostring(root, encoding='unicode'))

ids = ['112', '104', '100', '89', '113', '116', '99', '106', '109']
ds = [json.loads((R / f'outputs/dual-rank-20260919/comp-{i}.json').read_text())['data'] for i in ids] + [kog]
body = '18.2a选阵容先看装备和来牌，10套阵容码在下面。\n\n大嘴、人马来得多，物理装也合适，再考虑神谕大嘴；核心没来齐就别硬追，站位和装备看图12。大嘴体系前四50.21%；无尽＋锐利之刃＋巨杀的108个携装样本前四59.26%，不能当成开局硬玩也有六成前四。\n\n'
body += '\n\n'.join(d['name']+'\n\n'+d['gameCode'].split('#')[-1] for d in ds)
body += '\n\n地狱火轮子拿物理装；艾希分支需要地狱火转，导入后按图调整装备。巨龙占2人口；神谕码为7人口核心。\n\n特殊纹章、神器看主页《冷门构筑榜》。\n\n数据：DataJ非官方高分段样本，18.2a，9/19 03:32。前四率只作选阵容参考，还要看自己的来牌、装备和同行。阵容码尚未做游戏内导入校验，导入后对照图片检查。'
assert len(body) < 925, len(body)
(P / 'main-body.txt').write_text(body)
(P / 'main-title.txt').write_text('金铲铲S18阵容榜9.19｜附阵容码')
(P / 'new-assets.json').write_text(json.dumps(ASSETS, ensure_ascii=False, indent=2))

for path in sorted(OUT.glob('*.svg')):
    ET.parse(path)
    subprocess.run([NODE, str(R/'scripts/export_png.cjs'), str(path), str(path.with_suffix('.png'))], check=True, capture_output=True)

manifest = {
    'baseline': str(OLD), 'output': str(OUT), 'images': [str(p) for p in sorted(OUT.glob('*.png'))],
    'ranked_comp_ids': ids, 'supplement_comp_ids': ['119'], 'source_comp_count': len(rank),
    'version': '18.2a', 'data_updated_at': '2026-09-18T19:32:50.884Z',
    'publish_permission': 'USER_WILL_CLICK_DO_NOT_SUBMIT', 'status': 'rendered_pending_visual_QA',
    'bound_topics_to_preserve': ['金铲铲之战', '金铲铲S18', '金铲铲自然之力', '金铲铲阵容', '金铲铲阵容码', '金铲铲', '金铲铲攻略', '金铲铲推荐阵容'],
    'topic_selection_note': 'Current 2026-09-19 editor snapshot only; future posts must query #金铲铲 suggestions and compare live browse counts.',
    'collection': 's18金铲铲阵容数据库', 'body_length': len(body),
    'limits': ['No game import verification', 'No match replay verification', 'DataJ tier not causal strength', 'Population in diagram is not a statistical filter'],
}
assert len(manifest['images']) == 12
(P / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
print(json.dumps({'images': 12, 'body_length': len(body), 'dataj_comps_reviewed': len(rank)}, ensure_ascii=False))
