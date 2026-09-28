from pathlib import Path
import json,base64,html,urllib.request
R=Path(__file__).resolve().parents[1]; W=R/'references/web'
g=json.loads((R/'outputs/gamedata-20260908.json').read_text())['data'];cs=json.loads((R/'outputs/ranking-live-20260908.json').read_text())
H={h['name']:h for h in g['hero']};E={str(e['id']):e for e in g['equip']};C={c['name']:c for c in cs}
rows=[(c['name'],c['top4Rate'],c['topRate'],c['avgPlacement']) for c in sorted(cs,key=lambda c:-c['top4Rate']) if c['tier']=='S']
OUT=R/'exports/ranking-20260908';OUT.mkdir(exist_ok=True)
D=R/'assets/ranking';D.mkdir(exist_ok=True)
manifest=[]
def asset(v):
 url=v['picture'];p=D/Path(url).name
 if not p.exists(): p.write_bytes(urllib.request.urlopen(url).read())
 manifest.append({'name':v['name'],'url':url,'path':str(p.relative_to(R))})
 return 'data:image/png;base64,'+base64.b64encode(p.read_bytes()).decode()
O=['<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1714"><defs><pattern id="dot" width="18" height="18" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1.5" fill="#c4b5e5"/></pattern></defs><rect width="1080" height="1714" fill="#f0edf8"/><path d="M720 0H1080V246H924Z" fill="#e5dcf4"/><rect x="875" y="0" width="205" height="205" fill="url(#dot)"/><g font-family="PingFang SC, sans-serif">']
def t(x,y,s,z=26,c='#261d36',w=500):O.append(f'<text x="{x}" y="{y}" font-size="{z}" fill="{c}" font-weight="{w}">{html.escape(str(s))}</text>')
def rect(x,y,w,h,c,r=0):O.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{c}"/>')
def pic(v,x,y,w):
 q='p'+str(len(O));O.append(f'<clipPath id="{q}"><rect x="{x}" y="{y}" width="{w}" height="{w}" rx="8"/></clipPath><image x="{x}" y="{y}" width="{w}" height="{w}" href="{asset(v)}" clip-path="url(#{q})"/>')
rect(40,36,7,24,'#753cf4');t(59,57,'金铲铲之战 / S18',23,w=750);t(651,56,'9.7首发',22,'#796987');rect(810,24,230,46,'#753cf4',8);t(838,56,'9.8更新',29,'#fff',800)
t(38,146,'S18强势阵容榜',72,w=850);rect(710,94,330,64,'#753cf4',10);t(779,137,'附阵容码',34,'#fff',800)
rect(42,174,210,42,'#753cf4',5);t(59,204,'S 级阵容 · 9 套',25,'#fff',750)
t(279,205,'18.1c  /  按前四率降序',25,'#796987',650)
rect(40,241,1000,52,'#241b35',7);t(61,276,'阵容 / 主C参考装备',23,'#d9caec',650);t(679,276,'前四率',24,'#d9caec',700);t(859,276,'吃鸡率',24,'#ffba96',700)
for i,(n,top4,win,avg) in enumerate(rows):
 y=309+i*137;c=C[n];h=next(x for x in c['heroes'] if x['isCarry']);hn=h['heroName'];its=[E[e['equipId']] for e in c['equips'] if e['compHeroId']==h['id']]
 if n=='裁决奶妈':
  hn='婕拉';its=[e for e in g['equip'] if e['name']=='裁决使纹章'][:1]+[E['2004'],E['2011']]
 rect(40,y,1000,125,'#ffffff' if i%2==0 else '#e8e1f2',9)
 rect(40,y,5,125,'#753cf4',2);pic(H[hn],62,y+18,87)
 t(166,y+45,n,32,w=800);t(168,y+75,{'裁决奶妈':'婕拉转职参考','地狱火艾希':'艾希 · 需地狱火转','古纳拉95':'拉露恩 · 暂无阵容码'}.get(n,hn),18,'#8b789a')
 for j,it in enumerate(its):pic(it,409+j*61,y+36,48)
 t(167,y+107,f'均排{avg:.2f} · {c["sampleCount"]:,}局',20,'#796987')
 t(665,y+74,f'{top4:.1f}%',49,'#753cf4',850);t(861,y+74,f'{win:.1f}%',43,'#bd552e',800)
 if i==0:t(683,y+104,'本页最高',18,'#8e77a5')
 if n=='地狱火艾希':t(884,y+104,'本页最高',18,'#b77d62')
rect(40,1564,1000,3,'#753cf4')
t(42,1550,'完整阵容见后图 · 阵容码见正文（古纳拉95暂无码）',23,'#753cf4',700)
t(42,1601,'18.1c版本总样本96,024局 · 永森243局 / 古纳拉253局，样本较少',22,'#675776',650)
t(42,1639,'地狱火艾希需转职；统计为体系表现，非图示出装分支的独立胜率。',21,'#7c6e89')
t(42,1675,'来源：金铲铲大数据 dataj.cc/comp · 2026.09.08 · 评级沿用原站',21,'#7c6e89')
O.append('</g></svg>');(OUT/'01-9.8强势阵容榜.svg').write_text('\n'.join(O))
