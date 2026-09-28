from pathlib import Path
import json,base64,html,urllib.request
R=Path(__file__).resolve().parents[1]; W=R/'references/web'
g=json.loads((R/'outputs/gamedata-20260909.json').read_text())['data'];cs=json.loads((R/'outputs/ranking-live-20260909.json').read_text())
H={h['name']:h for h in g['hero']};E={str(e['id']):e for e in g['equip']};C={c['name']:c for c in cs}
rows=[(c['name'],c['top4Rate'],c['topRate'],c['avgPlacement']) for c in sorted(cs,key=lambda c:-c['top4Rate']) if c['tier']=='S' or c['name']=='裁决奶妈']
OUT=R/'exports/ranking-20260909';OUT.mkdir(exist_ok=True)
D=R/'assets/ranking';D.mkdir(exist_ok=True)
manifest=[]
def asset(v):
 url=v['picture'];p=D/Path(url).name
 if not p.exists(): p.write_bytes(urllib.request.urlopen(url).read())
 manifest.append({'name':v['name'],'url':url,'path':str(p.relative_to(R))})
 return 'data:image/png;base64,'+base64.b64encode(p.read_bytes()).decode()
O=['<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1851"><defs><pattern id="dot" width="18" height="18" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1.5" fill="#c4b5e5"/></pattern></defs><rect width="1080" height="1851" fill="#f0edf8"/><path d="M720 0H1080V246H924Z" fill="#e5dcf4"/><rect x="875" y="0" width="205" height="205" fill="url(#dot)"/><g font-family="PingFang SC, sans-serif">']
def t(x,y,s,z=26,c='#261d36',w=500):O.append(f'<text x="{x}" y="{y}" font-size="{z}" fill="{c}" font-weight="{w}">{html.escape(str(s))}</text>')
def rect(x,y,w,h,c,r=0):O.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{c}"/>')
def pic(v,x,y,w):
 q='p'+str(len(O));O.append(f'<clipPath id="{q}"><rect x="{x}" y="{y}" width="{w}" height="{w}" rx="8"/></clipPath><image x="{x}" y="{y}" width="{w}" height="{w}" href="{asset(v)}" clip-path="url(#{q})"/>')
rect(40,36,7,24,'#753cf4');t(59,57,'金铲铲之战 / S18',23,w=750);t(651,56,'9.7首发',22,'#796987');rect(810,24,230,46,'#753cf4',8);t(838,56,'9.9更新',29,'#fff',800)
t(38,146,'S18强势阵容榜',72,w=850);rect(710,94,330,64,'#753cf4',10);t(779,137,'附阵容码',34,'#fff',800)
rect(42,174,286,42,'#753cf4',5);t(59,204,'9套S级＋裁决转奶妈',25,'#fff',750)
t(352,205,'18.1c  /  前9套按前四率排序',25,'#796987',650)
rect(40,241,1000,52,'#241b35',7);t(61,276,'阵容 / 主C参考装备',23,'#d9caec',650);t(679,276,'前四率',24,'#d9caec',700);t(859,276,'吃鸡率',24,'#ffba96',700)
for i,(n,top4,win,avg) in enumerate(rows):
 y=309+i*137;c=C[n];h=next(x for x in c['heroes'] if x['heroName']=='厄斐琉斯') if n=='5迅射月男' else next(x for x in c['heroes'] if x['isCarry']);hn=h['heroName'];its=[E[e['equipId']] for e in c['equips'] if e['compHeroId']==h['id']]
 if n=='裁决奶妈':
  top4,win,avg=65.07,22.45,3.66;c={**c,'sampleCount':3020}
  hn='婕拉';its=[e for e in g['equip'] if e['name']=='裁决使纹章'][:1]+[E['2004'],E['2011']]
 rect(40,y,1000,125,'#fff3df' if n=='裁决奶妈' else ('#ffffff' if i%2==0 else '#e8e1f2'),9)
 rect(40,y,5,125,'#753cf4',2);pic(H[hn],62,y+18,87)
 t(166,y+45,'裁决转奶妈' if n=='裁决奶妈' else n,30,w=800);t(168,y+75,{'裁决奶妈':'婕拉三件套 · 单列不排序','地狱火艾希':'艾希 · 需地狱火转','古纳拉95':'拉露恩 · 暂无阵容码','5迅射月男':'需迅射转 · 观察 · 暂无码'}.get(n,hn),17,'#8b789a')
 for j,it in enumerate(its):pic(it,409+j*61,y+36,48)
 t(167,y+107,f'均排{avg:.2f} · {c["sampleCount"]:,}局',20,'#796987')
 t(665,y+74,f'{top4:.1f}%',49,'#753cf4',850);t(861,y+74,f'{win:.1f}%',43,'#bd552e',800)
 if i==0:t(683,y+104,'本页最高',18,'#8e77a5')
 if n=='地狱火艾希':t(884,y+104,'本页最高',18,'#b77d62')
rect(40,1701,1000,3,'#753cf4')
t(42,1687,'完整阵容见后图 · 阵容码见正文（古纳拉 / 月男暂无码）',23,'#753cf4',700)
t(42,1738,'18.1c版本总样本114,416局 · 月男183局 / 永森227局 / 古纳拉339局',22,'#675776',650)
t(42,1776,'奶妈单列：婕拉裁决转＋青龙刀＋虚空杖的装备分项。',21,'#7c6e89')
t(42,1812,'来源：金铲铲大数据 dataj.cc/comp · 2026.09.09 · 评级沿用原站',21,'#7c6e89')
O.append('</g></svg>');(OUT/'01-9.9强势阵容榜.svg').write_text('\n'.join(O))
