from build_rank_cards import *
G=json.loads((R/'outputs/gamedata-20260908.json').read_text())['data']
H={h['name']:h for h in G['hero']};E={str(e['id']):e for e in G['equip']};T={str(t['id']):t for t in G['trait']}
OUT=R/'exports/ranking-20260908';OUT.mkdir(exist_ok=True)
CONFIG.update({
'地狱火艾希':{'kind':'九人口运营 / 地狱火转职','gear':['艾希','希维尔','阿木木','凯南'],'start':'有地狱火转，且经济、血量允许升9时考虑。','roll':'先用两星牌稳血，9级找艾希、凯南及前排质量。','tip':'四名原生地狱火＋艾希转职，凑出5地狱火。'},
'古纳拉95':{'kind':'九人口运营 / 253局样本','gear':['拉露恩','远古巨龙','纳尔','苍蓝雕纹魔像'],'start':'经济、血量好，能用现有两星牌稳住时考虑。','roll':'9级找拉露恩、巨龙、纳尔，先补两星与前排。','tip':'8枚棋子占9人口；石皮树、生命花为召唤物。'}
})
def build(d,index):
 c=CONFIG[d['name']];pop=sum(h['heroType']==0 for h in d['heroes'])+int(any(h['heroName']=='远古巨龙' for h in d['heroes']))
 O=['<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1653"><rect width="1080" height="1653" fill="#f0edf8"/><path d="M795 0H1080V208H940Z" fill="#e5dcf4"/><g font-family="PingFang SC, sans-serif">']
 def tx(x,y,s,z=26,color='#281e39',w=500):O.append(f'<text x="{x}" y="{y}" font-size="{z}" fill="{color}" font-weight="{w}">{html.escape(str(s))}</text>')
 def rect(x,y,w,h,color,r=0,stroke=None):O.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{color}"'+(f' stroke="{stroke}" stroke-width="2"' if stroke else '')+'/>')
 def pic(v,x,y,w):
  q=f'p{len(O)}';O.append(f'<clipPath id="{q}"><rect x="{x}" y="{y}" width="{w}" height="{w}" rx="7"/></clipPath><image x="{x}" y="{y}" width="{w}" height="{w}" href="{asset(v)}" clip-path="url(#{q})"/>')
 rect(40,35,7,24,'#753cf4');tx(61,57,'金铲铲之战 / S18 · 18.1c',23,w=750);tx(900,57,f'{index+1:02d} / 10',24,w=750)
 tx(40,139,d['name'],64,w=850)
 rect(42,164,154,41,'#753cf4',5);tx(59,193,f'{pop}人口模板',25,'#fff',750);tx(219,194,c['kind'],26,'#756187',650)
 traits=[f"{T[t['id']]['num']}{t['name']}" for t in d['traits'] if t['id'] in T and T[t['id']]['num']>1]
 tx(43,244,'主要羁绊  '+' · '.join(traits[:4]),23,'#756187')
 rect(38,269,1004,509,'#fff',16);tx(61,299,'参考站位 · 上方为敌方',22,'#84718f');tx(760,299,'召唤物不计人口' if d['compId']=='113' else '艾希需地狱火转',20,'#84718f')
 bypos={h['position']:h for h in d['heroes']};assert len(bypos)==len(d['heroes'])
 for row in range(4):
  for col in range(7):
   x=61+col*133+(28 if row%2 else 0);y=318+row*109
   h=bypos.get(f'{row+1},{col+1}')
   rect(x,y,119,101,'#f0ebf7' if h else '#faf8fc',9, '#d8c8ed' if h else '#eee8f4')
   if not h:continue
   n=h['heroName'];pic(H[n],x+28,y+6,63)
   colors={1:'#8c939d',2:'#2fa774',3:'#3e85d7',4:'#9a55d5',5:'#bf902a'}
   rect(x+4,y+4,44 if h['heroType'] else 21,23,colors.get(h['price'],'#84718f'),4);tx(x+7,y+21,'召唤' if h['heroType'] else h['price'],14,'#fff',750)
   if h['heroStarNum']==3:rect(x+84,y+4,32,21,'#fff1bb',4);tx(x+86,y+20,'3★',15,'#946b0b',800)
   if len(n)>5:tx(x+9,y+85,n[:3],18,w=650);tx(x+9+54,y+85,n[3:],18,w=650)
   else:tx(x+(119-len(n)*21)/2,y+91,n,21,w=650)
 tx(42,818,'核心装备参考',29,w=800);tx(700,817,'按来装调整，不必强求全套',22,'#84718f')
 for j,n in enumerate(c['gear']):
  y=837+j*123;hero=next(h for h in d['heroes'] if h['heroName']==n);es=[E[e['equipId']] for e in d['equips'] if e['compHeroId']==hero['id']]
  assert len(es)==3
  rect(40,y,1000,113,'#fff',10);pic(H[n],71,y+14,55);tx(98-len(n)*min(23,120//len(n))/2,y+98,n,min(23,120//len(n)),w=750)
  for k,e in enumerate(es):
   x=181+k*284;pic(e,x+12,y+8,64);tx(x+90,y+48,e['name'],min(22,192//len(e['name'])),w=750)
   alias=SHORT.get(e['name']);
   if alias and alias!=e['name']:tx(x+90,y+74,alias,19,'#84718f')
   for j2,key in enumerate(['synthesis1','synthesis2']):pic(E[str(e[key])],x+12+j2*38,y+78,26)
   tx(x+38,y+98,'+',18,'#9581a9')
 rect(40,1349,1000,194,'#e6dcf4',12)
 tx(61,1389,'什么开局',23,'#753cf4',800);tx(194,1389,c['start'],25)
 tx(61,1433,'搜牌方向',23,'#753cf4',800);tx(194,1433,c['roll'],25)
 tx(61,1484,c['tip'],24,'#59456f',650)
 tx(42,1585,'来源暂未提供阵容码 · 按图手动配置（253局，样本较少）' if d['compId']=='113' else '需地狱火转 · 金铲铲＋反曲之弓｜纯阵容码见正文',26,'#753cf4',750)
 tx(42,1621,f"模板 / 装备：dataj.cc/comp/{d['compId']} · 2026.09.08｜运营为整理建议",19,'#84718f')
 O.append('</g></svg>');p=OUT/f'{index+1:02d}-{d["name"]}.svg';p.write_text('\n'.join(O));subprocess.run([NODE,str(R/'scripts/export_png.cjs'),str(p),str(p.with_suffix('.png'))],check=True,capture_output=True)
 return {'name':d['name'],'population':pop,'heroes':len(d['heroes']),'path':str(p.with_suffix('.png').relative_to(R)),'source':f"https://www.dataj.cc/comp/{d['compId']}",'code_available':bool(d['gameCode'])}

if __name__=='__main__':
 results=[]
 for id,index in [('112',1),('113',7)]:
  d=json.loads((R/f'outputs/comp-{id}-20260908.json').read_text())['data'];results.append(build(d,index))
 (R/'outputs/new-card-build-20260908.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
 print(results)
