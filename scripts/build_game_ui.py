"""Game-card visual direction; downloaded game artwork stays unchanged."""
import json,math,html
from build_sample import ROOT,uri
D=json.loads((ROOT/'lineups/裁决奶妈.json').read_text())
O=['<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1440" viewBox="0 0 1080 1440">', '<defs><pattern id="dots" width="14" height="14" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1" fill="#bdb4d9" opacity=".25"/></pattern></defs>', '<rect width="1080" height="1440" fill="#f0edf8"/><path d="M810 0 H1080 V307 H960 Z" fill="#e6def5"/><path d="M0 145 L615 0 H715 L0 170 Z" fill="#e9e2f5"/><rect x="803" width="277" height="306" fill="url(#dots)"/>','<g font-family="PingFang SC, Heiti SC, STHeiti, sans-serif">']
INK='#221834';MUT='#7d718e';PUR='#753cf4';ORANGE='#ff8647'
def txt(x,y,t,size=25,color=INK,weight=500,anchor='start'):
 O.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{weight}" text-anchor="{anchor}">{html.escape(t)}</text>')
def rect(x,y,w,h,fill,r=0,stroke='none'):
 O.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" rx="{r}" stroke="{stroke}"/>')
def pic(name,x,y,w,h,r=0):
 q='c'+str(len(O));O.append(f'<clipPath id="{q}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}"/></clipPath><image x="{x}" y="{y}" width="{w}" height="{h}" href="{uri(name)}" clip-path="url(#{q})" preserveAspectRatio="xMidYMid slice"/>')
def hexp(x,y,r):return ' '.join(f'{x+math.cos(math.radians(a))*r:.1f},{y+math.sin(math.radians(a))*r:.1f}' for a in [-90,-30,30,90,150,210])
# A compact, asymmetric title zone: lineup remains the first visual read.
rect(40,36,8,24,PUR);txt(60,56,'S18 / 自然之力',21,INK,700);txt(1038,56,'18.1c',21,MUT,600,'end')
txt(37,167,'裁决奶妈',100,INK,850)
O.append(f'<path d="M44 188 H328 L311 225 H27 Z" fill="{PUR}"/>');txt(54,215,'婕拉携带转职版本',26,'#fff',750)
# Small paired portrait fragments give the header character without new artwork.
pic('索拉卡',901,104,118,118,6);rect(903,220,115,5,'#b79be9')
pic('婕拉',781,87,130,130,6);rect(781,216,130,7,ORANGE)
O.append(f'<path d="M750 91 L727 135 L751 135 L728 179" fill="none" stroke="{PUR}" stroke-width="7"/>')
for x,name,label in [(40,'裁决使纹章','裁决使纹章'),(414,'朔极之矛','青龙刀'),(729,'虚空之杖','虚空之杖')]:
 pic(name,x,258,48,48,6);txt(x+63,291,label,27,INK,750)
# The board is a single game surface, with quiet grid marks and three role accents.
O.append('<path d="M40 339 H1012 L1044 371 V847 H64 L32 815 V347 Z" fill="#241b35"/>')
O.append('<path d="M44 343 H155 L139 351 H44 Z" fill="#a57eff"/>')
txt(57,383,'阵容站位',28,'#f5edff',750);txt(1019,382,'8 人口 / 参考站位',22,'#b1a2c7',600,'end')
for row in range(4):
 for col in range(7):
  x=108+132*col+(66 if row%2 else 0);y=446+108*row
  O.append(f'<polygon points="{hexp(x,y,51)}" fill="#2b213d" stroke="#4b3b61" stroke-width="1.5"/>')
for h in D['heroes']:
 x=108+132*h['col']+(66 if h['row']%2 else 0);y=446+108*h['row'];q='h'+str(len(O));points=hexp(x,y-4,54)
 color=ORANGE if h.get('role')=='主C' else '#b79afa' if h.get('role') else '#655178'
 O.append(f'<clipPath id="{q}"><polygon points="{points}"/></clipPath><image x="{x-54}" y="{y-58}" width="108" height="108" href="{uri(h["name"])}" clip-path="url(#{q})"/><polygon points="{points}" fill="none" stroke="{color}" stroke-width="2.5"/>')
 rect(x-51,y+23,102,30,'#241b35',3);txt(x,y+46,h['name'],22,'#f5edff',650,'middle')
 if h.get('role'):
  O.append(f'<path d="M{x-28} {y-63} H{x+29} L{x+24} {y-39} H{x-33} Z" fill="{color}"/>');txt(x-2,y-45,h['role'],17,'#241b35',850,'middle')
# Equipment rows use rules instead of stacked rounded containers.
txt(40,903,'装备分配',29,INK,800)
for i,e in enumerate(D['equipment_rows']):
 y=929+i*112
 O.append(f'<path d="M40 {y-6} H1040" stroke="#d6cce7" stroke-width="1.5"/>')
 pic(e['hero'],42,y+12,72,72,6)
 c=ORANGE if i==0 else PUR
 txt(136,y+37,e['role'],17,c,800);txt(135,y+74,e['hero'],31,INK,800)
 if e.get('items'):
  for n,it in enumerate(e['items']):
   x=314+n*240
   if it.get('asset'):
    pic(it['asset'],x,y+22,54,54,6);txt(x+68,y+58,it['label'],25,INK,650)
   else:
    rect(x,y+22,54,54,'#e4dcef',6);txt(x+27,y+60,'＋',29,MUT,500,'middle');txt(x+68,y+58,it['label'],25,INK,650)
 else:txt(314,y+59,e['note'],28,INK,650)
O.append(f'<path d="M40 1280 H1040" stroke="{PUR}" stroke-width="3"/>')
txt(42,1318,'替代 / 补强',20,PUR,800)
txt(42,1360,'凯南未到 → 慎暂代',30,INK,750);txt(617,1360,'9 人口 → 补拉露恩',30,INK,750)
O.append(f'<path d="M992 1387 L1006 1373 M1013 1387 L1027 1373 M1034 1387 L1048 1373" stroke="{PUR}" stroke-width="3"/>')
txt(42,1414,'裁决奶妈 · 婕拉转职版',17,MUT);txt(1038,1414,'2026.09.07',17,MUT,500,'end')
O.append('</g></svg>')
p=ROOT/'exports/裁决奶妈-ui-game-v2.svg';p.write_text('\n'.join(O));print(p)
