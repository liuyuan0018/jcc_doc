from pathlib import Path
import json,base64,html,urllib.request,subprocess
R=Path(__file__).resolve().parents[1]
G=json.loads((R/'outputs/equipment-recipes-20260907.json').read_text())['data']
E={str(e['id']):e for e in G['equip']};H={h['name']:h for h in G['hero']}
from build_rank_cards import CONFIG,SHORT
DATA=json.loads((R/'outputs/ranking-cards-source-20260907.json').read_text())
O=R/'exports/ranking-recipes-v3';O.mkdir(exist_ok=True)
a=[];checks=[]
def tx(x,y,t,size=22,color='#281e39',weight=600,anchor='start'):
 a.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{weight}" text-anchor="{anchor}">{html.escape(t)}</text>')
def rect(x,y,w,h,c):a.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{c}"/>')
def pic(item,x,y,w):
 p=R/'assets/ranking'/Path(item['picture']).name
 if not p.exists():p.write_bytes(urllib.request.urlopen(item['picture']).read())
 b=base64.b64encode(p.read_bytes()).decode();a.append(f'<image x="{x}" y="{y}" width="{w}" height="{w}" href="data:image/png;base64,{b}"/>')
for idx,D in enumerate(DATA,2):
 src=(R/f'exports/ranking-complete-v2/{idx:02d}-{D["name"]}.svg').read_text()
 head=src[:src.index('<text x="42" y="818"')].replace('height="1440"','height="1530"')
 tail=src[src.index('<rect x="40" y="1136"'):].removesuffix('</g></svg>')
 a=[]
 tx(42,818,'核心装备参考',29,weight=800);tx(690,817,'按来装调整，不必强求全套',22,'#84718f')
 for row,n in enumerate(CONFIG[D['name']]['gear']):
  y=837+row*123;rect(40,y,1000,113,'#ffffff');pic(H[n],71,y+14,55);tx(98,y+98,n,min(23,120//len(n)),anchor='middle')
  h=next(h for h in D['heroes'] if h['heroName']==n)
  eqs=[E[e['equipId']] for e in D['equips'] if e['compHeroId']==h['id']]
  for col,e in enumerate(eqs):
   x=181+col*284;ids=[str(e['synthesis1']),str(e['synthesis2'])]
   assert all(i in E for i in ids),e['name']
   pieces=[E[i] for i in ids]
   pic(e,x+12,y+8,64);tx(x+90,y+48,e['name'],min(22,192//len(e['name'])),weight=750)
   alias=SHORT.get(e['name'])
   if alias and alias!=e['name']:tx(x+90,y+74,alias,19,'#84718f')
   for k,p in enumerate(pieces):
    pic(p,x+12+k*38,y+78,26)
   tx(x+44,y+98,'+',18,'#9581a9',anchor='middle')
   checks.append({'hero':n,'item':e['name'],'components':[p['name'] for p in pieces],'source_ids':ids})
 a.append('<g transform="translate(0 90)">'+tail+'</g></g></svg>')
 p=O/f'{idx:02d}-{D["name"]}.svg';p.write_text(head+'\n'.join(a))
 node='/Users/lyu/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
 subprocess.run([node,str(R/'scripts/export_png.cjs'),str(p),str(p.with_suffix('.png'))],check=True,capture_output=True)
 print(p.with_suffix('.png'))
(R/'outputs/equipment-recipe-batch-checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2))
