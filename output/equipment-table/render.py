from pathlib import Path
import json, os, shutil
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parent
SRC=Path('/var/folders/tq/cxcc076d76v4pqpgc6znmm1c0000gn/T/codex-clipboard-f08f342d-13af-4c69-b5c3-0cc8a5ff2b38.png')
assert Path('/Volumes/Apple').is_mount()
OUT=Path('/Volumes/Apple/Codex/art-assets/金铲铲/publish/doc/装备组合表现')
assert os.access(OUT,os.W_OK)
rows='''384 0.7 2.60 -1.24 81.5 47.4
602 1.1 2.87 -0.97 77.4 39.7
355 0.7 3.06 -0.78 72.7 37.5
653 1.2 2.98 -0.86 75.8 36.0
1207 2.3 3.19 -0.65 71.8 35.1
924 1.8 3.25 -0.59 71.2 33.2
326 0.6 3.85 +0.02 59.8 27.9
377 0.7 3.14 -0.70 74.8 27.9
544 1.0 3.42 -0.42 68.0 27.4
761 1.4 3.41 -0.43 69.8 24.3
461 0.9 3.21 -0.63 76.1 24.1
557 1.1 3.47 -0.37 68.9 23.9
339 0.7 3.62 -0.21 66.1 23.6
551 1.1 3.59 -0.24 65.9 23.4
487 0.9 3.64 -0.19 65.5 23.4
639 1.2 3.48 -0.36 68.4 23.3
416 0.8 3.43 -0.41 70.4 23.3
634 1.2 3.35 -0.49 71.8 22.9
342 0.7 3.25 -0.59 74.6 22.8
1889 3.6 3.56 -0.28 67.4 22.4
488 0.9 3.56 -0.27 68.2 21.1
875 1.7 3.52 -0.32 68.7 21.0
849 1.6 3.51 -0.33 69.1 20.9'''
records=[x.split()for x in rows.splitlines()];assert len(records)==23
ICONS=Path('/Users/lyu/Documents/project/game/projects/jcc/client/Assets/Res/GUI/Image/Equip')
# Equipment IDs mapped from the original 23 rows, in exact source order.
pairs=[('41806','41816'),('steraksgage','41806'),('2039','41806'),('2045','41806'),('2009','41806'),('2053','41806'),('2004','41806'),('steraksgage','41816'),('2053','41816'),('2009','2053'),('steraksgage','strikersflail'),('steraksgage','2009'),('2045','41816'),('2009','2045'),('bloodthirster','2053'),('steraksgage','2039'),('2045','2046'),('2053','strikersflail'),('strikersflail','2045'),('steraksgage','2053'),('2039','2045'),('steraksgage','2045'),('2053','2039')]
assert len(pairs)==len(records)
for pair in pairs:
 for icon in ('2001',*pair):assert (ICONS/(icon+'.png')).is_file(),icon
S=2;im=Image.new('RGB',(1200*S,1630*S),'#F7F5FF');d=ImageDraw.Draw(im)
FONT='/System/Library/Fonts/STHeiti Light.ttc';BOLD='/System/Library/Fonts/STHeiti Medium.ttc'
def text(x,y,s,size=26,color='#252B38',bold=False,center=True):
 f=ImageFont.truetype(BOLD if bold else FONT,size*S)
 d.text((x*S,y*S),s,font=f,fill=color,anchor='mm'if center else'lm')
def rect(box,color):d.rectangle(tuple(v*S for v in box),fill=color)
rect((49,57,57,115),'#7950D4');text(77,86,'装备组合表现',49,bold=True,center=False)
text(79,144,'23组组合 · 按登顶率降序',25,'#7950D4',center=False)
xs=[143,285,416,543,672,804,941,1080]
rect((48,185,1152,235),'#7950D4')
for x,s in zip(xs,['装备组合','评级','对局数','出场率','平均排名','名次差','前四率','登顶率']):text(x,210,s,25,'white',True)
data=[]
for i,r in enumerate(records):
 y=235+i*58;rect((48,y,1152,y+57),'#FFF4CC'if i==0 else'white')
 icon_ids=['2001',*pairs[i]]
 for j,icon_id in enumerate(icon_ids):
  icon=Image.open(ICONS/(icon_id+'.png')).convert('RGBA').resize((48*S,48*S),Image.Resampling.LANCZOS)
  im.paste(icon,((62+j*57)*S,(y+5)*S),icon)
 d.rounded_rectangle((264*S,(y+15)*S,306*S,(y+43)*S),radius=14*S,fill='#EEE5FF')
 text(285,y+29,'S',23,'#7950D4',True)
 vals=[f'{int(r[0]):,}',r[1]+'%',r[2],r[3],r[4]+'%',r[5]+'%']
 for j,(x,v)in enumerate(zip(xs[2:],vals)):
  color=('#B83C43'if r[3].startswith('+')else'#26896F')if j==3 else('#7950D4'if j==5 else'#252B38')
  text(x,y+29,v,27,color,j==5)
 data.append({'row':i+1,'iconIds':icon_ids,'iconPaths':[str(ICONS/(v+'.png'))for v in icon_ids],'rating':'S','games':int(r[0]),'pickRate':r[1]+'%','averageRank':r[2],'rankDelta':r[3],'top4':r[4]+'%','winRate':r[5]+'%'})
(ROOT/'data.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
im.save(ROOT/'装备组合表现.png')
old=OUT/'装备组合表现.png'
if old.exists()and not(ROOT/'imagegen-history.png').exists():shutil.copy2(old,ROOT/'imagegen-history.png')
shutil.copy2(ROOT/'装备组合表现.png',old)
print(old)
