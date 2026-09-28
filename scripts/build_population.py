from pathlib import Path
import json,base64,html
R=Path(__file__).resolve().parents[1]
A={a['name']:a for a in json.loads((R/'catalog/assets.json').read_text())['assets']}
O=['<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1440"><rect width="1080" height="1440" fill="#f0edf8"/><g font-family="PingFang SC, sans-serif">']
def t(x,y,s,z=28,c='#221834',w=600): O.append(f'<text x="{x}" y="{y}" font-size="{z}" fill="{c}" font-weight="{w}">{html.escape(s)}</text>')
def box(x,y,w,h,c): O.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{c}"/>')
t(42,55,'S18 / 18.1c',22,'#753cf4',800);t(842,55,'进阶补位 / 02',22)
t(40,150,'裁决奶妈',76,w=850);t(42,211,'9 → 10 人口怎么补？',43,'#753cf4',800)
box(40,252,1000,227,'#241b35');t(63,299,'先认准这 8 张核心棋子',29,'#fff',750)
names=['婕拉','索拉卡','墨菲特','阿木木','凯南','费德提克','阿兹尔','约里克']
for i,n in enumerate(names):
 x=64+i*121
 b=base64.b64encode((R/A[n]['path']).read_bytes()).decode()
 O.append(f'<image x="{x}" y="321" width="96" height="96" href="data:image/png;base64,{b}"/>')
 t(x+2,451,n,23,'#f5edff')
t(40,544,'09',55,'#753cf4',850);t(153,540,'核心 8 张 ＋ 1 张补位',35,w=800)
t(42,585,'大数据展示的三种九人口分支，三选一',25,'#7d718e')
for x,n in [(40,'慎'),(382,'伊泽瑞尔'),(724,'拉露恩')]:
 box(x,611,316,108,'#e3d8f6');t(x+24,679,'＋ '+n,39,'#221834',800)
box(40,751,1000,335,'#241b35')
t(63,817,'10',55,'#b99aff',850);t(177,813,'核心 8 张 ＋ 拉露恩 ＋ 1 张',35,'#fff',800)
t(65,860,'最后一张：慎 / 拉克丝 / 莉莉娅，三选一',27,'#c7b5df')
for x,n in [(65,'慎'),(390,'拉克丝'),(715,'莉莉娅')]:
 box(x,888,297,88,'#463257');t(x+25,945,'＋ '+n,35,'#fff',750)
t(65,1027,'九人口用了伊泽瑞尔？',26,'#ffad7c',750)
t(65,1063,'转上述十人口分支：下伊泽瑞尔，补拉露恩和所选棋子。',25,'#eee4fb')
t(40,1145,'阵容码与分支的区别',30,'#753cf4',800)
t(42,1190,'正文首行码是来源站的含艾翁展示模板。',27)
t(42,1232,'采用本页分支时，下艾翁，按 9 / 10 人口补位。',27)
t(42,1282,'婕拉仍带：裁决使纹章 ＋ 青龙刀 ＋ 虚空之杖',27,w=750)
O.append('<path d="M40 1320 H1040" stroke="#753cf4" stroke-width="3"/>')
t(42,1360,'来源：金铲铲大数据 · 裁决奶妈 · 9 / 10 人口页签',21,'#7d718e')
t(42,1400,'dataj.cc/comp/90 · 查询 2026.09.07 · 分支选择参考',20,'#7d718e')
O.append('</g></svg>')
(R/'exports/裁决奶妈-人口补位-v1.svg').write_text('\n'.join(O))
