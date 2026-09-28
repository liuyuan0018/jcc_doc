from build_rank_cards import *
P=R/'outputs/dual-rank-20260918';OUT=R/'exports/S18冷门榜-20260918'
g=json.loads((P/'gamedata.json').read_text())['data'];H={h['name']:h for h in g['hero']};E={str(e['id']):e for e in g['equip']}
source=(R/'scripts/build_dual_rank_20260918.py').read_text();a=source.index('builds=[');z=source.index("\ns=Card('冷门构筑强度榜'",a);exec(source[a:z])
for i,d in enumerate(builds):
 c=json.loads((P/f'comp-{d["comp"]}.json').read_text())['data'];pop=sum(h['heroType']==0 for h in c['heroes'])+int(any(h['heroName']=='远古巨龙' for h in c['heroes']))
 O=['<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="2040"><rect width="1080" height="2040" fill="#f0edf8"/><path d="M795 0H1080V208H940Z" fill="#e5dcf4"/><g font-family="PingFang SC,sans-serif">']
 def t(x,y,s,z=26,color='#281e39',w=500):O.append(f'<text x="{x}" y="{y}" font-size="{z}" fill="{color}" font-weight="{w}">{html.escape(str(s))}</text>')
 def rect(x,y,w,h,col='#fff',r=12):O.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{col}"/>')
 def pic(v,x,y,w):O.append(f'<image x="{x}" y="{y}" width="{w}" height="{w}" href="{asset(v)}"/>')
 rect(40,35,7,24,'#753cf4',0);t(61,57,'金铲铲之战 / S18 · 18.2a',23,w=750);t(895,57,f'{i+2:02d} / 06',24,w=750);t(40,139,d['name'],64,w=850)
 rect(42,164,154,41,'#753cf4',5);t(59,193,f'{pop}人口参考',25,'#fff',750);t(220,194,d['level']+' / 先有关键装备',26,'#756187',650)
 t(43,244,f"前四 {d['top']:.2f}% · 登顶 {d['win']:.2f}% · 均名 {d['avg']:.2f} · {d['n']}样本",26,'#756187')
 rect(38,269,1004,509);t(61,299,'参考站位 · 上方为敌方',22,'#84718f');t(744,299,'召唤物不占人口 / 3★追三',20,'#84718f')
 pos={h['position']:h for h in c['heroes']}
 priorities={'卡蜜尔','奥恩'} if i==2 else {'凯尔','奥恩'} if i==3 else {'卡兹克','赫卡里姆'} if i==4 else set()
 for row in range(4):
  for col in range(7):
   x=61+col*133+(28 if row%2 else 0);y=318+row*109;h=pos.get(f'{row+1},{col+1}');rect(x,y,119,101,'#f0ebf7' if h else '#faf8fc',9)
   if not h:continue
   n=h['heroName'];pic(H[n],x+28,y+6,63);cl={1:'#8c939d',2:'#2fa774',3:'#3e85d7',4:'#9a55d5',5:'#bf902a'}.get(h['price'],'#84718f');rect(x+4,y+4,44 if h['heroType'] else 21,23,cl,4);t(x+7,y+21,'召唤' if h['heroType'] else h['price'],14,'#fff',750)
   if n in priorities:rect(x+84,y+4,32,21,'#fff1bb',4);t(x+86,y+20,'3★',15,'#946b0b',800)
   t(x+(119-len(n)*min(21,110//len(n)))/2,y+91,n,min(21,110//len(n)),w=650)
 t(42,818,'主C装备参考',29,w=800);t(607,818,'最后一件是本套关键，先拿到再定阵',23,'#84718f')
 rect(40,837,1000,123);pic(H[d['hero']],64,849,65);t(59,944,d['hero'],22,w=750)
 for k,eid in enumerate(d['eq']):
  x=202+k*276;pic(E[str(eid)],x,849,63);t(x,944,E[str(eid)]['name'],22,w=650)
 t(43,999,'统计未锁定三件套；普通补装为参考，按来装调整。',25,'#756187')
 # Keep concrete mechanics and constraints while adding board contract clarifications
 if i==0:
  d['entry']=['先有花妖转，经济、血量允许升9；转职给凯南。','图示4名原生地狱火开3档；有额外地狱火转再开5档。']
 if i==1:d['route'][1]='巨龙放后排侧翼，德莱文与带转巨龙开2猎人。'
 for j,(label,lines) in enumerate([('什么开局',d['entry']),('机制变化',d['mech']),('搜牌与对位',d['route']),('注意这两点',d['risk'])]):
  y=1029+j*183;rect(40,y,1000,165,'#fff0d5' if j==3 else '#fff');t(62,y+40,label,28,'#753cf4',800)
  for k,line in enumerate(lines):t(62,y+90+k*42,line,26)
 t(42,1806,'来源框架码见正文 · 导入后按本图手动改装备',29,'#753cf4',750)
 t(42,1853,'图上三星标记是追牌重点，不要求所有低费一起追三。',25,'#756187')
 t(42,1900,'统计：'+('所属体系内携带者分项。' if i<3 else '英雄携装分项，未锁定本图完整阵容。'),25,'#756187')
 t(42,1945,'尚无逐局实战复核；成型战绩不代表开局硬玩成功率。',25,'#756187')
 t(42,2003,f"模板 / 装备：dataj.cc/comp/{d['comp']} · 2026.09.18｜18.2a",21,'#84718f');O.append('</g></svg>')
 p=OUT/f'{i+2:02d}-{d["name"]}.svg';p.write_text('\n'.join(O));subprocess.run([NODE,str(R/'scripts/export_png.cjs'),str(p),str(p.with_suffix('.png'))],check=True,capture_output=True)
print('5 board cards rendered')
