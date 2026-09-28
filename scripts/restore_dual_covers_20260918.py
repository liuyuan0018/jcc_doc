from build_rank_cards import *
P=R/'outputs/dual-rank-20260918';M=R/'exports/S18常规榜-20260918';COLD=R/'exports/S18冷门榜-20260918'
g=json.loads((P/'gamedata.json').read_text())['data'];H={h['name']:h for h in g['hero']};E={str(e['id']):e for e in g['equip']}
cs=[json.loads((P/f'comp-{i}.json').read_text())['data'] for i in [112,113,99,104,89,100,116,106,109]]
cs[0]['equips']=json.loads((R/'outputs/comp-112-20260916-post.json').read_text())['data']['equips']
(P/'cover-source.json').write_text(json.dumps(cs,ensure_ascii=False))
base=(R/'scripts/build_rank_20260909.py').read_text()
s=base.replace('outputs/gamedata-20260909.json','outputs/dual-rank-20260918/gamedata.json').replace('outputs/ranking-live-20260909.json','outputs/dual-rank-20260918/cover-source.json').replace("OUT=R/'exports/ranking-20260909'","OUT=R/'exports/S18常规榜-20260918'").replace("if c['tier']=='S' or c['name']=='裁决奶妈'","if True")
s=s.replace("next(x for x in c['heroes'] if x['isCarry'])","next(x for x in c['heroes'] if x['heroName']=='艾希') if n=='地狱火95' else next(x for x in c['heroes'] if x['isCarry'])")
for a,b in [('9.7首发','03:25数据'),('9.9更新','9.18更新'),('S18强势阵容榜','S18常规阵容榜'),('9套S级＋裁决转奶妈','18.2a · 热修独立统计'),('18.1c  /  前9套按前四率排序','7套S＋2套A · 前四率排序'),('拉露恩 · 暂无阵容码','拉露恩'),('完整阵容见后图 · 阵容码见正文（古纳拉 / 月男暂无码）','图2选阵容 · 图3—11站位装备 · 九套码见正文'),('18.1c版本总样本114,416局 · 月男183局 / 永森227局 / 古纳拉339局','18.2a独立样本25,912局 · 数据截至9/18 03:25。'),('奶妈单列：婕拉裁决转＋青龙刀＋虚空杖的装备分项。','体系前四率排序；小样本有波动，分档沿用来源。'),('2026.09.09 · 评级沿用原站','2026.09.18 · 非官方样本')]:s=s.replace(a,b)
s=s.replace("'均排{avg:.2f} · {c[\"sampleCount\"]:,}局'","'均排{avg:.2f} · 样本{c[\"sampleCount\"]:,}'")
s=s.replace("else n,30,w=800)","else (n+' · A' if c['tier']=='A' else n),30,w=800)")
s=s.replace("rect(40,1701,1000,3,'#753cf4')","rect(40,1550,1000,90,'#fff0d5',10)\nt(59,1586,'有纹章 / 神器？主页看《冷门构筑榜》',30,'#9b5920',800)\nt(59,1623,'花妖凯南 · 猎人巨龙 · 暗爪卡蜜尔｜同系列另一篇',25,'#9b5920',650)\nrect(40,1701,1000,3,'#753cf4')")
exec(compile(s,'cover-main','exec'),{'__file__':str(R/'scripts/build_rank_20260909.py')})
p=M/'01-9.9强势阵容榜.svg';p.rename(M/'01-常规阵容强度榜.svg')
# reuse original background, type scale, badges and row primitives for the sister cover
ns={'__file__':str(R/'scripts/build_rank_20260909.py'),'R':R,'H':H,'E':E,'g':g,'asset':asset,'html':html}
start=base.index("O=['<svg");end=base.index("rect(40,36,7,24")
exec(base[start:end],ns);t=ns['t'];rect=ns['rect'];pic=ns['pic'];O=ns['O']
rect(40,36,7,24,'#753cf4');t(59,57,'金铲铲之战 / S18',23,w=750);t(651,56,'03:25数据',22,'#796987');rect(810,24,230,46,'#753cf4',8);t(838,56,'9.18更新',29,'#fff',800)
t(38,146,'S18冷门构筑榜',72,w=850);rect(710,94,330,64,'#753cf4',10);t(747,137,'有条件再玩',34,'#fff',800)
rect(42,174,286,42,'#753cf4',5);t(59,204,'18.2a · 纹章 / 神器',25,'#fff',750);t(352,205,'3套条件强势＋2套观察',25,'#796987',650)
rect(40,241,1000,52,'#241b35',7);t(61,276,'构筑 / 主C参考装备',23,'#d9caec',650);t(679,276,'前四率',24,'#d9caec',700);t(859,276,'吃鸡率',24,'#ffba96',700)
t(43,333,'条件强势 · 所属体系内携带者分项',25,'#753cf4',750)
rows=[('花妖转凯南','凯南',[2020,2039,41810],85.71,37.5,2.54,112,'先有花妖转；能稳血上9再考虑。'),('猎人转巨龙','远古巨龙',[2001,2039,41816],74.07,38.89,2.82,108,'先有猎人转；巨龙占2人口。'),('暗爪卡蜜尔','卡蜜尔',[2001,2039,6073],71.65,14.17,3.45,127,'早拿暗爪＋来牌多，5级追三。'),('护臂天使','凯尔',[2010,2038,6084],71.74,26.09,3.35,46,'只有46个样本，暂不定强度档。'),('花妖转螳螂','卡兹克',[2005,2039,41810],68.18,11.36,3.84,44,'只有44个样本，先当试玩线索。')]
for i,(name,hero,eq,top,win,avg,n,tip) in enumerate(rows):
 y=356+i*191 if i<3 else 1042+(i-3)*191
 if i==3:t(43,1017,'小样本观察 · 英雄携装分项，不与上面直排',25,'#9b5920',750)
 rect(40,y,1000,172,'#fff3df' if i>=3 else ('#ffffff' if i%2==0 else '#e8e1f2'),9);rect(40,y,5,172,'#753cf4' if i<3 else '#c99343',2);pic(H[hero],62,y+18,87)
 t(166,y+45,name,30,w=800);t(168,y+75,hero,17,'#8b789a');t(167,y+107,f'均排{avg:.2f} · 样本{n}',20,'#796987')
 for j,e in enumerate(eq):pic(E[str(e)],409+j*61,y+36,48)
 t(665,y+74,f'{top:.1f}%',49,'#753cf4',850);t(861,y+74,f'{win:.1f}%',43,'#bd552e',800);t(166,y+149,tip,24,'#796987',650)
t(43,1473,'统计不是图示三件套的独立成绩；运营与补装为整理建议。',25,'#796987')
rect(40,1550,1000,90,'#fff0d5',10);t(59,1586,'没关键装备？主页看《常规阵容榜》',30,'#9b5920',800);t(59,1623,'九套完整站位＋装备＋阵容码｜同系列另一篇',25,'#9b5920',650)
t(42,1687,'图2—6看玩法、开局与翻车点 · 基础框架码见正文',23,'#753cf4',700);rect(40,1701,1000,3,'#753cf4');t(42,1738,'不同口径分区呈现，不混成统一胜率排名。',22,'#675776',650);t(42,1776,'五费成型有偏差；小样本不是稳定上分保证。',21,'#7c6e89');t(42,1812,'来源：DataJ · 18.2a · 截至9/18 03:25 · 非官方样本',21,'#7c6e89');O.append('</g></svg>');(COLD/'01-冷门构筑强度榜.svg').write_text('\n'.join(O))
for p in [M/'01-常规阵容强度榜.svg',COLD/'01-冷门构筑强度榜.svg']:subprocess.run([NODE,str(R/'scripts/export_png.cjs'),str(p),str(p.with_suffix('.png'))],check=True,capture_output=True)
