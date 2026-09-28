"""Build the 9/24 Spider extension from the archived DataJ board and local icons.

The established six-card artwork remains the source for the cover variant.
No network request or editorial model call is needed when regenerating it.
"""
from copy import deepcopy
from pathlib import Path
import base64
import json
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
S = 'http://www.w3.org/2000/svg'
X = 'http://www.w3.org/1999/xlink'
ET.register_namespace('', S)
ET.register_namespace('xlink', X)


def icon(name):
    path = ROOT / 'assets/ranking' / name
    data = path.read_bytes()
    if not data.startswith(b'\x89PNG\r\n\x1a\n'):
        raise ValueError(f'Not a PNG: {path}')
    return 'data:image/png;base64,' + base64.b64encode(data).decode()


def node(parent, tag, attrs=None, label=None):
    child = ET.SubElement(parent, f'{{{S}}}{tag}', {k:str(v) for k,v in (attrs or {}).items()})
    if label is not None:
        child.text = label
    return child


def move_y(parent, amount):
    for child in parent.iter():
        for attr in ('y', 'cy'):
            if attr in child.attrib:
                child.set(attr, str(int(float(child.get(attr))) + amount))


def write_cover(comp):
    source = ROOT / 'templates/dual-rank/cold/冷门构筑强度榜.svg'
    target = ROOT / 'templates/dual-rank/cold/冷门构筑强度榜-蜘蛛.svg'
    root = ET.parse(source).getroot()
    root.set('height', '2040')
    for child in root:
        if child.tag == f'{{{S}}}rect' and child.get('height') == '1851':
            child.set('height', '2040')
    group = root.find(f'{{{S}}}g')
    children = list(group)
    assert children[97].get('data-row') == 'kog' and len(children) == 122
    children[10].text = '3套条件强势＋4套观察'
    for child in children[113:]:
        move_y(child, 178)
    children[113].text = '大嘴为三件套分项；蜘蛛为阵容统计，其余五套为携装分项。'
    children[117].text = '图2—8看玩法、开局与翻车点 · 七套阵容码见正文'
    children[119].text = '前3套体系内携装；天使、螳螂为英雄携装；大嘴三件套；蜘蛛阵容样本。'
    block = [deepcopy(c) for c in children[97:113]]
    for child in block:
        move_y(child, 178)
        for part in child.iter():
            for attr in ('id', 'clip-path'):
                if attr in part.attrib:
                    part.set(attr, part.get(attr).replace('cold-kog-', 'cold-spider-'))
    block[0].set('data-row', 'spider')
    block[4].text = '黑暗仪式蜘蛛'
    block[5].text = '伊莉丝 · 2-1强化限定'
    block[6].text = '均排{{cold_observation.row.avgPlacement:.2f}} · 样本{{cold_observation.row.sampleCount}}'
    block[13].text = '{{cold_observation.row.top4Rate:.1f}}%'
    block[14].text = '{{cold_observation.row.topRate:.1f}}%'
    block[15].text = '2-1拿黑暗仪式；6级先追蜘蛛三。'
    for element,asset in zip((block[3],block[8],block[10],block[12]),
                             ('s18_head_elise.png','2010.png','2052.png','2248.png')):
        element.set(f'{{{X}}}href', icon(asset))
        element.attrib.pop('href', None)
    for i,child in enumerate(block):
        group.insert(113+i,child)
    target.write_text(ET.tostring(root, encoding='unicode'))
    return target


def write_detail(comp):
    target = ROOT / 'templates/dual-rank/cold/黑暗仪式蜘蛛.svg'
    root = ET.Element(f'{{{S}}}svg', {'width':'1080','height':'2040','viewBox':'0 0 1080 2040'})
    defs = node(root,'defs')
    node(root,'rect',{'width':1080,'height':2040,'fill':'#f0edf8'})
    node(root,'path',{'d':'M720 0H1080V246H924Z','fill':'#e5dcf4'})
    g = node(root,'g',{'font-family':'PingFang SC, sans-serif'})

    def box(x,y,w,h,fill='#ffffff',stroke=None,r=14):
        attrs={'x':x,'y':y,'width':w,'height':h,'rx':r,'fill':fill}
        if stroke:attrs.update({'stroke':stroke,'stroke-width':2})
        return node(g,'rect',attrs)

    def text(x,y,label,size=23,fill='#261d36',weight=500,anchor=None):
        attrs={'x':x,'y':y,'font-size':size,'fill':fill,'font-weight':weight}
        if anchor:attrs['text-anchor']=anchor
        return node(g,'text',attrs,label)

    def picture(x,y,asset,size=64,clip=None):
        if clip:
            cp=node(defs,'clipPath',{'id':clip})
            node(cp,'rect',{'x':x,'y':y,'width':size,'height':size,'rx':10})
        attrs={'x':x,'y':y,'width':size,'height':size,f'{{{X}}}href':icon(asset)}
        if clip:attrs['clip-path']=f'url(#{clip})'
        return node(g,'image',attrs)

    # Header and conditional statistics.
    box(40,37,7,24,'#753cf4',r=0)
    text(59,58,'金铲铲之战 / S18 · {{source.version}}',23,'#261d36',750)
    box(857,25,183,46,'#753cf4',r=8)
    text(875,57,'{{date.short}}更新',26,'#ffffff',800)
    text(40,151,'黑暗仪式蜘蛛',68,'#261d36',850)
    box(739,102,301,58,'#753cf4',r=10)
    text(766,141,'2-1拿强化再玩',27,'#ffffff',750)
    text(43,212,'9人口上限摆位 · 6级先追蜘蛛三星',29,'#796987',650)
    box(40,237,1000,112,'#fff0d5',r=12)
    text(63,279,'阵容统计：{{cold_observation.row.sampleCount}}样本 · 均排{{cold_observation.row.avgPlacement:.2f}}',25,'#8b4b15',700)
    text(63,320,'前四 {{cold_observation.row.top4Rate:.2f}}%  ·  登顶 {{cold_observation.row.topRate:.2f}}%  ·  条件观察',31,'#9b5920',850)

    # 4x7 board. The positions and units come directly from comp/120.
    box(40,369,1000,631)
    box(40,369,1000,49,'#241b35',r=10)
    text(60,403,'参考站位 · 上方为敌方',24,'#ffffff',750)
    text(733,403,'对位可左右镜像',20,'#d9caec',550)
    label={'伊莉丝':'蜘蛛','卡西奥佩娅':'蛇女','苍蓝雕纹魔像':'苍蓝雕纹魔像'}
    asset={'伊莉丝':'elise','莫甘娜':'morgana','卡西奥佩娅':'cassiopeia','黛安娜':'diana',
           '赫卡里姆':'hecarim','塔里克':'taric','拉露恩':'alune','苍蓝雕纹魔像':'sentinel','洛':'rakan'}
    board_rows={}
    for hero in comp['heroes']:
        row,col=map(int,hero['position'].split(','))
        if (row,col) in board_rows:raise ValueError('Duplicate board position')
        board_rows[row,col]=hero
    for (row,col),hero in sorted(board_rows.items()):
        cx=121+(col-1)*136
        cy=471+(row-1)*128
        shade='#fff0d5' if hero['heroName']=='伊莉丝' else '#eee8f6'
        box(cx-46,cy-7,92,100,shade,r=12)
        picture(cx-38,cy, 's18_head_'+asset[hero['heroName']]+'.png',76,f'spider-{row}-{col}')
        text(cx,cy+98,label.get(hero['heroName'],hero['heroName']),17,'#261d36',700,'middle')
        if hero['heroName']=='伊莉丝':
            box(cx+17,cy-10,32,24,'#bd552e',r=5)
            text(cx+33,cy+8,'3★',16,'#ffffff',800,'middle')
    text(61,973,'蜘蛛放前排中右；后排蛇女避集火。五费没到先用两星前排过渡。',21,'#796987',580)

    # Item owners are the same as DataJ comp/120; no inferred substitutions.
    box(40,1017,1000,319)
    text(59,1061,'装备归属 · 先保证蜘蛛三件',30,'#753cf4',800)
    equip_rows=[
        (1090,'伊莉丝','elise',[('2010.png','鬼索'),('2052.png','泰坦'),('2248.png','石像鬼板甲')]),
        (1174,'卡西奥佩娅','cassiopeia',[('2004.png','青龙刀'),('2038.png','法爆'),('2003.png','科技枪')]),
        (1258,'莫甘娜','morgana',[('voidstaff.png','虚空之杖'),('2020.png','鬼书')]),
    ]
    for i,(y,name,asset_name,items) in enumerate(equip_rows):
        if i:node(g,'line',{'x1':60,'y1':y-18,'x2':1020,'y2':y-18,'stroke':'#e8e1f2','stroke-width':2})
        picture(62,y-18,'s18_head_'+asset_name+'.png',52,f'equip-owner-{i}')
        text(126,y+14,name,23,'#261d36',700)
        for j,(file,item_name) in enumerate(items):
            x=343+j*215
            picture(x,y-18,file,52,f'equip-{i}-{j}')
            text(x+60,y+13,item_name,20,'#675776',650)

    box(40,1353,1000,159,'#fff0d5')
    text(61,1398,'黑暗仪式改变了什么',30,'#9b5920',800)
    text(63,1445,'2-1选到后获得卡蜜尔、蜘蛛、女警；魔女不再给战利品。',23,'#654529',600)
    text(63,1485,'魔女精粹兑换奖励时，改为给魔女弈子增加法术加成。',23,'#654529',600)

    box(40,1530,1000,329)
    text(60,1573,'开局、搜牌与止损',30,'#753cf4',800)
    steps=[
        ('进场','2-1拿到强化；用魔女和两星前排稳血，蜘蛛对子多再定。'),
        ('搜牌','6级用余钱追蜘蛛3；蛇女、皎月、人马顺带留，别全追。'),
        ('升级','蜘蛛3后补莫甘娜和苍蓝雕纹魔像；9级再找塔里克、拉露恩。'),
        ('止损','没强化，或6级蜘蛛少、血量经济危险，先用两星战力稳场。'),
    ]
    for i,(head,line) in enumerate(steps):
        y=1620+i*55
        box(60,y-27,68,37,'#e8e1f2',r=7)
        text(72,y,head,22,'#753cf4',750)
        text(145,y,line,22,'#261d36',550)

    box(40,1877,1000,129,'#e8e1f2')
    text(61,1915,'阵容码：{{cold_observation.code}}',20,'#261d36',650)
    text(61,1951,'DataJ comp/120 · {{source.version}} · 截至{{source.short_time}} · 非官方高分段样本',20,'#675776',550)
    text(61,1986,'阵容统计有成型偏差；运营是建议，尚无逐局实战复核。',20,'#675776',550)
    target.write_text(ET.tostring(root,encoding='unicode'))
    return target


if __name__=='__main__':
    comp=json.loads((ROOT/'research/special-20260924/comp120.json').read_text())['data']
    if comp['compId']!='120' or len(comp['heroes'])!=9 or len(comp['equips'])!=8:
        raise ValueError('Spider source changed; review before rendering')
    print(write_cover(comp))
    print(write_detail(comp))
