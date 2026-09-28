"""Refresh the accepted 9/19 SVG layouts with the verified 9/20 snapshot."""
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP
import copy
import hashlib
import json
import re
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'outputs/dual-rank-20260920'
REG_OLD = ROOT / 'exports/S18常规榜-20260919-修订版'
COLD_OLD = ROOT / 'exports/S18冷门榜-20260919-修订版'
REG = ROOT / 'exports/S18常规榜-20260920'
COLD = ROOT / 'exports/S18冷门榜-20260920'
NODE = '/Users/lyu/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
NS = '{http://www.w3.org/2000/svg}'
ET.register_namespace('', NS[1:-1])
for folder in (REG, COLD):
    folder.mkdir(exist_ok=True)

def read(key):
    return json.loads((DATA / f'{key}.json').read_text())['data']

rank = {r['name']: r for r in read('rank')}
special = read('special')
def carrier(eid, cid):
    return next(c['carrier'] for e in special if e['equipId'] == eid
                for c in e['comps'] if str(c['compId']) == str(cid))

cold_stats = {
    '花妖转凯南': carrier(41810, 112),
    '猎人转巨龙': carrier(41816, 89),
    '暗爪卡蜜尔': carrier(6073, 115),
    '护臂天使': next(e for e in read('kayle-gear') if e['equipId'] == 6084),
    '花妖转螳螂': next(e for e in read('khazix-gear') if e['equipId'] == 41810),
    '神谕大嘴': next(e for e in read('kog-ad-equips')['hero3Equips']
                       if set(e['equipIds']) == {2001, 2045, 2046}),
}
ashe = next(e for e in read('ashe-emblem')['heroEquips'] if e['id'] == '41806')
zyra = next(e for e in read('zyra-equips')['hero3Equips']
            if set(e['equipIds']) == {41818, 2004, 2011})

def one(x):
    return str(Decimal(str(x)).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP))

changes = []
def update_text(root, before, after, required=True):
    matches = [e for e in root.iter(NS+'text') if e.text == before]
    if required:
        assert matches, before
    for e in matches:
        e.text = after
        changes.append({'before': before, 'after': after})

def dates(root):
    for e in root.iter(NS+'text'):
        if not e.text:
            continue
        e.text = (e.text.replace('2026.09.19', '2026.09.20')
                  .replace('09.19 /', '09.20 /')
                  .replace('9.19更新', '9.20更新')
                  .replace('9/19 03:32', '9/20 03:26')
                  .replace('03:32数据', '03:26数据'))

def save(root, path):
    path.write_text(ET.tostring(root, encoding='unicode'))

def texts(nodes):
    return [e for node in nodes for e in node.iter(NS+'text')]

def set_row(nodes, stats, comma=True):
    ts = texts(nodes)
    meta = next(e for e in ts if e.text and e.text.startswith('均排'))
    sample = f"{stats['sampleCount']:,}" if comma else str(stats['sampleCount'])
    meta.text = f"均排{stats['avgPlacement']:.2f} · 样本{sample}"
    rate = next(e for e in ts if e.get('x') == '665')
    win = next(e for e in ts if e.get('x') == '861')
    rate.text = one(stats['top4Rate']) + '%'
    win.text = one(stats['topRate']) + '%'

regular_order = [r['name'] for r in sorted(
    [rank[n] for n in ['地狱火95','野怪小红','重装女警','巨龙95','古纳拉95',
                       '裁决螳螂','7野怪鸡哥','主宰女警','皎月螳螂']],
    key=lambda r: -r['top4Rate'])]

# Cover rows move as complete groups so portraits, items and data remain paired.
root = ET.parse(REG_OLD/'01-常规阵容强度榜.svg').getroot()
group = root.find(NS+'g')
children = list(group)
starts = [i for i,e in enumerate(children) if e.tag == NS+'rect'
          and e.get('x') == '40' and e.get('width') == '1000'
          and e.get('height') == '111']
assert len(starts) == 9
tail = next(i for i in range(starts[-1]+1, len(children))
            if children[i].tag == NS+'g')
blocks = {}
for start,end in zip(starts, starts[1:]+[tail]):
    nodes = children[start:end]
    name = next(e.text.split(' · ')[0] for e in texts(nodes) if e.get('x') == '166')
    blocks[name] = nodes
assert set(blocks) == set(regular_order)
for e in children[starts[0]:tail]:
    group.remove(e)
insert = starts[0]
for i,name in enumerate(regular_order):
    nodes = blocks[name]
    delta = 309 + 123*i - float(nodes[0].get('y'))
    for node in nodes:
        for e in node.iter():
            if 'y' in e.attrib:
                e.set('y', str(float(e.get('y')) + delta).removesuffix('.0'))
    nodes[0].set('fill', '#ffffff' if i % 2 == 0 else '#e8e1f2')
    set_row(nodes, rank[name])
    if name == '主宰女警':
        next(e for e in texts(nodes) if e.get('x') == '166').text = '主宰女警 · B'
    for node in nodes:
        group.insert(insert, node)
        insert += 1
kog_group = next(e for e in group if e.tag == NS+'g')
set_row([kog_group], rank['神谕大嘴'], comma=False)
update_text(root, '18.2a版本样本57,568 · 数据截至9/19 03:32。',
            '18.2a版本样本88,056 · 数据截至9/20 03:26。')
dates(root)
save(root, REG/'01-常规阵容强度榜.svg')

root = ET.parse(REG_OLD/'02-今天怎么选.svg').getroot()
update_text(root, '新增：神谕大嘴，来牌顺再玩', '神谕大嘴，来牌顺再玩')
update_text(root, '7级追大嘴；石甲虫、人马按数量选一个主坦追三。',
            '7级先稳两星与前排，来牌多再追大嘴三星。')
update_text(root, '封面65.3%是体系统计，两条分支未分别排强度。',
            '封面64.4%是体系统计，两条分支未分别排强度。')
update_text(root, '裁决婕拉暂不补进主推', '裁决婕拉有转也别硬冲')
update_text(root, '裁决转＋青龙刀＋虚空杖：205样本，前四45.85%。',
            f"裁决转＋青龙刀＋虚空杖：{zyra['sampleCount']}样本，前四{zyra['top4Rate']:.2f}%。")
dates(root)
save(root, REG/'02-今天怎么选.svg')

# Preserve each accepted board and the custom equipment branch; only its
# statistics, source date and page number are refreshed.
for i,name in enumerate(regular_order, 3):
    src = next(REG_OLD.glob(f'*-{name}.svg'))
    root = ET.parse(src).getroot()
    for e in root.iter(NS+'text'):
        if e.text and re.fullmatch(r'\d{2} / 12', e.text):
            e.text = f'{i:02d} / 12'
    if name == '地狱火95':
        update_text(root, '艾希带转：2,366样本 / 前四75.91%，非体系胜率。',
                    f"艾希带转：{ashe['sampleCount']:,}样本 / 前四{ashe['top4Rate']:.2f}%，非体系胜率。")
    if name == '古纳拉95':
        update_text(root, '九人口运营 / 659局样本',
                    f"九人口运营 / {rank[name]['sampleCount']}局样本")
    dates(root)
    save(root, REG/f'{i:02d}-{name}.svg')

root = ET.parse(REG_OLD/'12-神谕大嘴.svg').getroot()
kog = rank['神谕大嘴']; triple = cold_stats['神谕大嘴']
update_text(root, '神谕体系：966样本 · 前四50.21% · 登顶10.25% · 均名4.50',
            f"神谕体系：{kog['sampleCount']}样本 · 前四{kog['top4Rate']:.2f}% · 登顶{kog['topRate']:.2f}% · 均名{kog['avgPlacement']:.2f}")
update_text(root, '对应三件套分项：108样本 · 前四59.26% · 登顶9.26%',
            f"对应三件套分项：{triple['sampleCount']}样本 · 前四{triple['top4Rate']:.2f}% · 登顶{triple['topRate']:.2f}%")
update_text(root, '均名4.14；携装样本有成型偏差，不能当作开局硬玩的成功率。',
            f"均名{triple['avgPlacement']:.2f}；携装样本有成型偏差，不能当作开局硬玩的成功率。")
dates(root)
save(root, REG/'12-神谕大嘴.svg')
cold_kog = copy.deepcopy(root)
update_text(cold_kog, '12 / 12', '07 / 07')
save(cold_kog, COLD/'07-神谕大嘴.svg')

root = ET.parse(COLD_OLD/'01-冷门构筑强度榜.svg').getroot()
group = root.find(NS+'g'); children = list(group)
starts = [i for i,e in enumerate(children) if e.tag == NS+'rect'
          and e.get('x') == '40' and e.get('width') == '1000'
          and e.get('height') == '158']
assert len(starts) == 6
for j,start in enumerate(starts):
    end = starts[j+1] if j+1 < len(starts) else len(children)
    nodes = children[start:end]
    name = next(e.text for e in texts(nodes) if e.get('x') == '166')
    set_row(nodes, cold_stats[name], comma=False)
update_text(root, '116个携装样本，暂不定强度档。', '184个携装样本，暂不定强度档。')
update_text(root, '117个携装样本，先当试玩线索。', '172个携装样本，先当试玩线索。')
dates(root)
save(root, COLD/'01-冷门构筑强度榜.svg')

for i,name in enumerate(list(cold_stats)[:5], 2):
    root = ET.parse(COLD_OLD/f'{i:02d}-{name}.svg').getroot(); stats = cold_stats[name]
    line = next(e for e in root.iter(NS+'text') if e.text and e.text.startswith('前四 '))
    line.text = f"前四 {stats['top4Rate']:.2f}% · 登顶 {stats['topRate']:.2f}% · 均名 {stats['avgPlacement']:.2f} · {stats['sampleCount']}样本"
    if name == '猎人转巨龙':
        alt = carrier(41806,89)
        update_text(root, '地狱火转巨龙也可看：353样本，前四78.75%。',
                    f"地狱火转巨龙也可看：{alt['sampleCount']}样本，前四{alt['top4Rate']:.2f}%。")
    if name == '暗爪卡蜜尔':
        update_text(root, '全体系前四仅46.93%，普通装备不能照搬。',
                    f"全体系前四仅{rank['卡丽蜜儿']['top4Rate']:.2f}%，普通装备不能照搬。")
    if name == '护臂天使':
        update_text(root, '116个英雄携装样本，没有锁定整套阵容。',
                    '184个英雄携装样本，没有锁定整套阵容。')
        update_text(root, '别按68.10%当稳定上分结论，先小范围试。',
                    '别按70.65%当稳定上分结论，先小范围试。')
    if name == '花妖转螳螂':
        update_text(root, '117个英雄携装样本，不能和上面三套直排。',
                    '172个英雄携装样本，不能和上面三套直排。')
    dates(root)
    save(root, COLD/f'{i:02d}-{name}.svg')

# Keep a record of the previous body-only delivery before correcting its date note.
archive = DATA/'body-only-published-baseline'
archive.mkdir(exist_ok=True)
for name in ['manifest.json','editor-readback.json','content-checks.json',
             'cold-body.txt','regular-body.txt','cold-title.txt','regular-title.txt']:
    target = archive/name
    if not target.exists():
        target.write_bytes((DATA/name).read_bytes())
body_updates = {
    'cold': ('9月20日上分先看手里的纹章、神器和来牌。今天的数值见正文，配图数据截至9月19日。',
             '9月20日上分先看手里的纹章、神器和来牌。封面看数据和适用条件，图2—7看站位、装备与搜牌。'),
    'regular': ('9月20日选阵容，先看装备和来牌。下方10套按前四率排序，括号内是样本数；配图数据截至9月19日。',
                '9月20日选阵容，先看装备和来牌。下方10套按前四率排序，括号内是样本数；封面与内页均为18.2a数据。'),
}
for key,(before,after) in body_updates.items():
    path = DATA/f'{key}-body.txt'; body=path.read_text()
    if before in body:
        path.write_text(body.replace(before,after))
    else:
        assert after in body
    path = DATA/f'{key}-title.txt'
    path.write_text(path.read_text().replace('9.19','9.20'))

artifacts=[]
for folder, old in [(REG,REG_OLD),(COLD,COLD_OLD)]:
    files=sorted(folder.glob('*.svg'))
    assert len(files)==(12 if folder==REG else 7)
    for path in files:
        root = ET.parse(path).getroot()
        strings=[e.text or '' for e in root.iter(NS+'text')]
        assert not any(re.search(r'9\.19|09\.19|9/19|03:32', s) for s in strings), path
        # The artwork is source-preserving: identical embedded images per board.
        if not path.name.startswith('01-'):
            baseline=next(old.glob('*-'+path.name.split('-',1)[1]))
            oldroot=ET.parse(baseline).getroot()
            assert [e.get('href') for e in root.iter(NS+'image')] == [e.get('href') for e in oldroot.iter(NS+'image')]
            assert (root.get('width'),root.get('height')) == (oldroot.get('width'),oldroot.get('height'))
        subprocess.run([NODE,str(ROOT/'scripts/export_png.cjs'),str(path),str(path.with_suffix('.png'))],check=True,capture_output=True)
        artifacts.append({'svg':str(path),'png':str(path.with_suffix('.png')),
                          'png_sha256':hashlib.sha256(path.with_suffix('.png').read_bytes()).hexdigest(),
                          'width':int(root.get('width')),'height':int(root.get('height'))})
(DATA/'image-update.json').write_text(json.dumps({'status':'rendered_pending_visual_check',
    'source_updated_at':read('summary')['dataUpdatedAt'],'regular_order':regular_order+['神谕大嘴'],
    'cold_order':list(cold_stats),'artifacts':artifacts,'text_changes':changes,
    'preserved':'Existing design, artwork, lineup configuration and code/name associations.'},ensure_ascii=False,indent=2))
print(json.dumps({'images':len(artifacts),'regular_order':regular_order,'status':'rendered_pending_visual_check'},ensure_ascii=False))
