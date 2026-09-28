"""Create the dated, evidence-bounded Azir sacrifice observation card."""
from base64 import b64encode
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'templates/dual-rank/cold/献祭螳螂阿兹尔.svg'


def rect(x, y, w, h, fill, r=12, stroke=None, sw=0):
    extra = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ''
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}"{extra}/>'


def txt(x, y, value, size=28, color='#261d36', weight=600):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{weight}">{escape(value)}</text>'


def icon(x, y, name):
    path = ROOT / f'assets/ranking/s18_head_{name}.png'
    data = b64encode(path.read_bytes()).decode('ascii')
    return (rect(x-5, y-5, 128, 128, '#eee8f6', 15)
            + f'<image x="{x}" y="{y}" width="118" height="118" href="data:image/png;base64,{data}"/>')


parts = [
    '<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="2040" viewBox="0 0 1080 2040">',
    rect(0, 0, 1080, 2040, '#f0edf8', 0),
    '<path d="M720 0H1080V246H924Z" fill="#e5dcf4"/>',
    '<g font-family="PingFang SC, sans-serif">',
    rect(40, 37, 7, 24, '#753cf4', 0),
    txt(59, 58, '金铲铲之战 / S18 · {{source.version}}', 23, weight=750),
    rect(857, 25, 183, 46, '#753cf4', 8),
    txt(875, 57, '{{date.short}}更新', 26, '#ffffff', 800),
    txt(40, 151, '献祭三星螳螂', 68, weight=850),
    rect(766, 102, 274, 58, '#753cf4', 10),
    txt(785, 141, '阿兹尔主C', 28, '#ffffff', 750),
    txt(43, 211, '黑荆棘 · 高投入玩法观察', 29, '#796987', 650),
    rect(40, 237, 1000, 130, '#fff0d5'),
    txt(63, 282, '先看条件：三星卡兹克＋阿兹尔＋黑荆棘格', 29, '#9b5920', 800),
    txt(63, 326, '尚无“三星螳螂作祭品”的独立战绩，不列强度名次。', 25, '#8b4b15', 650),
    rect(40, 387, 1000, 430, '#ffffff'),
    rect(40, 387, 1000, 52, '#241b35', 10),
    txt(60, 423, '核心操作 · 先养螳螂，再让阿兹尔接力', 25, '#ffffff', 750),
    icon(141, 487, 'khazix'),
    icon(821, 487, 'azir'),
    txt(150, 638, '卡兹克 3★', 29, '#261d36', 750),
    txt(137, 676, '先完成裁决进化', 24, '#796987', 650),
    rect(401, 504, 270, 105, '#eee8f6', 15),
    txt(431, 549, '放进黑荆棘格', 28, '#753cf4', 800),
    txt(444, 590, '战斗开始献祭', 24, '#675776', 600),
    '<path d="M290 555H380M378 543L396 555L378 567M688 555H788M786 543L804 555L786 567" fill="none" stroke="#753cf4" stroke-width="7" stroke-linecap="round"/>',
    txt(824, 638, '阿兹尔主C', 29, '#261d36', 750),
    txt(792, 676, '吃祭品增益打输出', 24, '#796987', 650),
    txt(62, 757, '黑荆棘按祭品定位、费用和星级给成员加属性；阿兹尔本身有黑荆棘。', 23, '#675776', 550),
    rect(40, 837, 1000, 375, '#ffffff'),
    txt(61, 892, '成型前，按这个顺序检查', 34, '#753cf4', 800),
    rect(60, 916, 108, 46, '#e8e1f2', 9), txt(74, 948, '羁绊', 23, '#753cf4', 750),
    txt(188, 949, '至少2黑荆棘：阿兹尔＋雷克塞/墨菲特。', 26),
    rect(60, 984, 108, 46, '#e8e1f2', 9), txt(74, 1016, '祭品', 23, '#753cf4', 750),
    txt(188, 1017, '螳螂先拿到裁决进化；三星后再放祭格。', 26),
    rect(60, 1052, 108, 46, '#e8e1f2', 9), txt(74, 1084, '主C', 23, '#753cf4', 750),
    txt(188, 1085, '阿兹尔至少两星，后排避开切入对位。', 26),
    rect(60, 1120, 108, 46, '#e8e1f2', 9), txt(74, 1152, '前排', 23, '#753cf4', 750),
    txt(188, 1153, '祭掉螳螂会少一张棋子，前排先站稳。', 26),
    rect(40, 1232, 1000, 264, '#fff0d5'),
    txt(61, 1288, '阿兹尔装备：续航＋法强，再补功能位', 33, '#9b5920', 800),
    txt(64, 1351, '科技枪', 30, '#261d36', 750),
    txt(330, 1351, '帽子 / 大天使', 30, '#261d36', 750),
    txt(696, 1351, '虚空杖 / 羊刀', 30, '#261d36', 750),
    txt(64, 1410, '祭品带来的回蓝、增伤以当前对局显示为准；别硬凑固定三件。', 25, '#8b4b15', 600),
    txt(64, 1459, '肉装优先给留场前排，螳螂将被献祭时不要占核心装备。', 25, '#8b4b15', 600),
    rect(40, 1516, 1000, 305, '#ffffff'),
    txt(61, 1572, '搜牌与止损', 34, '#753cf4', 800),
    txt(64, 1631, '7级稳住阿兹尔两星与前排，再用经济找双三星。', 27),
    txt(64, 1690, '螳螂被抢、血量吃紧，别为三星祭品拖垮阵容。', 27),
    txt(64, 1749, '螳螂没三星时先用普通祭品，不照搬三星收益。', 27),
    rect(40, 1841, 1000, 165, '#e8e1f2'),
    txt(61, 1894, '暂无这套祭品条件的专属阵容码；按核心条件手动调整。', 24, '#261d36', 650),
    txt(61, 1939, '机制：黑荆棘规则＋卡兹克进化；强度尚待独立数据/实战复核。', 22, '#675776', 550),
    txt(61, 1983, '适用数据版本：金铲铲 {{source.version}} · 截至{{source.short_time}}', 21, '#7c6e89', 500),
    '</g></svg>'
]
OUT.write_text(''.join(parts))
print(OUT)
