"""Two visual directions using the same lineup and unchanged downloaded assets."""
from pathlib import Path
import json,html,math
from build_sample import ROOT,uri
D=json.loads((ROOT/'lineups/裁决奶妈.json').read_text())

def build(mode):
 p={'dark':dict(bg='#111714',card='#1b2420',ink='#eff5ed',muted='#92a398',line='#35483c',accent='#c6f77f',tag='#293c27',grid='#1b2821'), 'light':dict(bg='#f4f3ee',card='#ffffff',ink='#20362d',muted='#76837b',line='#dbe3dc',accent='#167653',tag='#e7f0df',grid='#edf2ec')}[mode]
 out=[f'<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1440" viewBox="0 0 1080 1440"><rect width="1080" height="1440" fill="{p["bg"]}"/><g font-family="PingFang SC, Heiti SC, STHeiti, sans-serif">']
 def text(x,y,t,size=26,color=None,weight=500,anchor='start'):
  out.append(f'<text x="{x}" y="{y}" fill="{color or p["ink"]}" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}">{html.escape(t)}</text>')
 def rect(x,y,w,h,fill,r=16,stroke='none'):
  out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}"/>')
 def img(name,x,y,w,h,r=0):
  ident='clip'+str(len(out));rectdef=f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}"/>'
  out.append(f'<clipPath id="{ident}">{rectdef}</clipPath><image x="{x}" y="{y}" width="{w}" height="{h}" href="{uri(name)}" clip-path="url(#{ident})" preserveAspectRatio="xMidYMid slice"/>')
 def hexpts(x,y,r):return ' '.join(f'{x+math.cos(math.radians(a))*r:.1f},{y+math.sin(math.radians(a))*r:.1f}' for a in [-90,-30,30,90,150,210])
 text(48,60,'S18 / 自然之力',23,p['muted'],600)
 text(1032,60,'18.1c',23,p['muted'],600,'end')
 text(45,158,'裁决奶妈',84,p['ink'],800)
 rect(718,103,313,55,p['tag'],28);text(875,139,'婕拉携带转职版本',25,p['accent'],700,'middle')
 text(49,205,'转职给婕拉，装备归属一眼查清',27,p['muted'])
 for i,(a,l,w) in enumerate([('裁决使纹章','裁决使纹章',332),('朔极之矛','青龙刀',292),('虚空之杖','虚空之杖',324)]):
  x=[48,394,700][i];rect(x,239,w,60,p['card'],12);img(a,x+10,249,40,40,7);text(x+64,279,l,25,p['ink'],650)
 rect(32,324,1016,530,p['card'],24)
 text(57,366,'阵容站位',28,p['ink'],750);text(1020,365,'8 人口 · 参考站位',23,p['muted'],500,'end')
 for row in range(4):
  for col in range(7):
   x=108+132*col+(66 if row%2 else 0);y=437+112*row
   out.append(f'<polygon points="{hexpts(x,y,53)}" fill="{p["grid"]}" stroke="{p["line"]}" stroke-width="1.5"/>')
 for h in D['heroes']:
  x=108+132*h['col']+(66 if h['row']%2 else 0);y=437+112*h['row'];ident='hero'+str(len(out));pts=hexpts(x,y-3,53)
  out.append(f'<clipPath id="{ident}"><polygon points="{pts}"/></clipPath><image x="{x-53}" y="{y-56}" width="106" height="106" href="{uri(h["name"])}" clip-path="url(#{ident})"/><polygon points="{pts}" fill="none" stroke="{p["accent"] if h.get("role") else p["line"]}" stroke-width="2"/>')
  rect(x-49,y+24,98,29,p['card'],7);text(x,y+47,h['name'],22,p['ink'],650,'middle')
  if h.get('role'):
   rect(x-25,y-64,50,24,p['accent'],6);text(x,y-46,h['role'],17,p['bg'] if mode=='dark' else '#ffffff',750,'middle')
 text(48,904,'装备分配',28,p['ink'],750)
 for i,e in enumerate(D['equipment_rows']):
  y=929+i*112;rect(32,y,1016,99,p['card'],18)
  img(e['hero'],48,y+14,70,70,13)
  text(138,y+39,e['role'],17,p['muted'],600)
  text(137,y+74,e['hero'],30,p['ink'],750)
  if e.get('items'):
   for n,item in enumerate(e['items']):
    x=310+n*239
    if item.get('asset'):
     img(item['asset'],x,y+24,51,51,9);text(x+65,y+57,item['label'],25,p['ink'],600)
    else:
     rect(x,y+24,51,51,p['grid'],9);text(x+25,y+58,'＋',29,p['muted'],500,'middle');text(x+65,y+57,item['label'],25,p['ink'],600)
  else:text(310,y+59,e['note'],28,p['ink'],600)
 rect(32,1281,1016,104,p['tag'],18)
 text(58,1319,'替代与补强',19,p['accent'],700)
 text(58,1361,'凯南未到 → 慎暂代',29,p['ink'],650)
 text(603,1361,'9 人口 → 补拉露恩',29,p['ink'],650)
 text(48,1421,'裁决奶妈 / 婕拉转职版',17,p['muted'])
 text(1032,1421,'2026.09.07',17,p['muted'],500,'end')
 out.append('</g></svg>')
 dest=ROOT/f'exports/裁决奶妈-ui-{mode}-v1.svg';dest.write_text('\n'.join(out));print(dest)
for mode in ['dark','light']:build(mode)
