from build_rank_cards import *
import build_new_cards_20260908 as b
import copy,re
P=R/'outputs/dual-rank-20260918'
G=json.loads((P/'gamedata.json').read_text())['data'];H={h['name']:h for h in G['hero']};E={str(e['id']):e for e in G['equip']};T={str(t['id']):t for t in G['trait']}
M=R/'exports/S18常规榜-20260918';C=R/'exports/S18冷门榜-20260918'
for p in [M,C]:p.mkdir(exist_ok=True)
def comp(i):return json.loads((P/f'comp-{i}.json').read_text())['data']
ids=[112,113,99,104,89,100,116,106,109];ds=[comp(i) for i in ids]
class Card:
 def __init__(s,title,kicker,sub):
  s.o=['<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1653"><rect width="1080" height="1653" fill="#f0edf8"/><g font-family="PingFang SC,sans-serif">'];s.tx(48,61,kicker,25,'#753cf4',750);s.tx(48,147,title,62,w=850);s.tx(50,203,sub,27,'#756187')
 def tx(s,x,y,t,z=28,col='#281e39',w=500):s.o.append(f'<text x="{x}" y="{y}" font-size="{z}" fill="{col}" font-weight="{w}">{html.escape(str(t))}</text>')
 def rect(s,x,y,w,h,col='#ffffff'):s.o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="{col}"/>')
 def pic(s,v,x,y,w):s.o.append(f'<image href="{asset(v)}" x="{x}" y="{y}" width="{w}" height="{w}"/>')
 def link(s,other):
  s.rect(42,1430,996,133,'#753cf4');s.tx(65,1477,'同系列另一篇 · 到主页看',25,'white',700);s.tx(65,1528,'→ '+other,38,'white',850)
 def save(s,path):
  s.tx(47,1611,'DataJ 高分段样本 · 18.2a · 数据截至 9/18 03:25',21,'#84718f');s.o.append('</g></svg>');path.write_text('\n'.join(s.o));subprocess.run([NODE,str(R/'scripts/export_png.cjs'),str(path),str(path.with_suffix('.png'))],check=True,capture_output=True)
# Regular cover
s=Card('常规阵容强度榜','金铲铲 S18 / 18.2a / 09.18','9套站位＋装备＋阵容码 · 按体系前四率排序')
s.tx(64,265,'体系 / 来源分档',23,'#84718f');s.tx(600,265,'前四',23,'#84718f');s.tx(770,265,'登顶',23,'#84718f');s.tx(923,265,'样本',23,'#84718f')
for j,d in enumerate(ds):
 y=287+j*108;s.rect(42,y,996,94);s.rect(60,y+20,55,52,'#753cf4' if d['tier']=='S' else '#9582ad');s.tx(76,y+56,d['tier'],29,'white',800);s.tx(139,y+56,d['name'],34,w=750);s.tx(599,y+56,f"{d['top4Rate']:.2f}%",31,w=800);s.tx(770,y+56,f"{d['topRate']:.2f}%",28);s.tx(923,y+56,d['sampleCount'],25)
s.tx(49,1313,'地狱火继续用艾希带转；裁决螳螂进入主榜。',29,w=700);s.tx(49,1360,'分档沿用来源；热修独立样本 25,912 局。',26,'#756187');s.link('冷门构筑榜｜纹章 / 神器怎么玩');s.save(M/'01-常规阵容强度榜.svg')
# change page
s=Card('今天怎么选','09.18 / 常规榜阅读指南','18.2a 已有独立统计，不再混用 18.2 累计数据')
blocks=[('想运营上9','地狱火95、古纳拉95、巨龙95。','先保经济和血量；成型数据不等于硬玩成功率。'),('来牌多，考虑追三','野怪小红、重装女警、裁决螳螂。','主宰女警、皎月螳螂作为顺牌备选。'),('地狱火转继续给艾希','带转分项：1,092样本 / 前四77.66%。','封面66.44%是整个体系，两种口径分开看。'),('卡丽蜜儿暂不放进常规主榜','体系前四45.98%；暗爪卡蜜尔分支另看冷门榜。','不能把特定神器的成绩套给普通出装。')]
for j,(a,x,y) in enumerate(blocks):
 yy=282+j*259;s.rect(42,yy,996,232);s.tx(68,yy+57,a,35,w=800);s.tx(68,yy+118,x,29);s.tx(68,yy+174,y,27,'#756187')
s.tx(48,1380,'图3—11：站位、装备合成、开局和搜牌方向。',30,w=750);s.link('冷门构筑榜｜封面互相指路');s.save(M/'02-今天怎么选.svg')
# Board cards preserve renderer
b.H=H;b.E=E;b.T={k:v for k,v in T.items() if v.get("num") is not None};b.OUT=M
b.CONFIG['地狱火95']={'kind':'九人口运营 / 艾希带转','gear':['艾希','希维尔','阿木木','凯南'],'start':'有地狱火转，物理装合适且能升9时考虑。','roll':'先用两星牌稳血，升9找艾希、凯南和前排。','tip':'艾希带转分项：前四77.66% / 1092样本，非体系胜率。'}
b.CONFIG['古纳拉95']['kind']='九人口运营 / 290局样本'
b.CONFIG['裁决螳螂']={'kind':'三费追三 / 裁决体系','gear':['卡兹克','索拉卡','赫卡里姆'],'start':'螳螂、人马来得顺，近战法系装合适时考虑。','roll':'7级稳质量追核心三星，成型后升8补奶妈。','tip':'图中石皮树、生命花为召唤物；不占人口。'}
b.CONFIG['主宰女警']={'kind':'二费追三 / 主宰前排','gear':['凯特琳','峡谷迅捷蟹','瑟庄妮'],'start':'女警、河蟹来牌多，且有攻速装备时考虑。','roll':'6级先找两星，再追女警与前排三星。','tip':'女警后排输出，河蟹和猪妹优先承伤。'}
for j,d0 in enumerate(ds):
 d=copy.deepcopy(d0)
 if d['compId']=='112':d['equips']=json.loads((R/'outputs/comp-112-20260916-post.json').read_text())['data']['equips']
 b.build(d,j+2);p=M/f'{j+3:02d}-{d["name"]}.svg';x=p.read_text().replace('18.1c','18.2a').replace(' / 10',' / 11').replace('2026.09.08','2026.09.18')
 x=x.replace('来源暂未提供阵容码 · 按图手动配置（253局，样本较少）','阵容码见正文 · 巨龙占2人口；召唤物不占人口')
 if d['compId']=='112':x=x.replace('需地狱火转 · 金铲铲＋反曲之弓｜纯阵容码见正文','导入阵容码后按图调整装备 · 地狱火转给艾希')
 else:x=x.replace('艾希需地狱火转','3★ 为追三参考').replace('需地狱火转 · 金铲铲＋反曲之弓｜纯阵容码见正文','18.2a 配置参考 · 装备随来装调整｜阵容码见正文')
 p.write_text(x);subprocess.run([NODE,str(R/'scripts/export_png.cjs'),str(p),str(p.with_suffix('.png'))],check=True,capture_output=True)
# special build pages
builds=[
 dict(name='花妖转凯南',hero='凯南',eq=[2020,2039,41810],comp=112,n=112,top=85.71,win=37.50,avg=2.54,level='条件强势',mech=['群体技能容易参与击败，接花妖的击败回蓝。','单花妖已有回蓝；凑2花妖后才有队友治疗。'],entry=['先有花妖转，且经济、血量允许升9。','沿用地狱火九五框架；转职交凯南。'],route=['前中期两星牌稳血，9级补凯南和五费质量。','凯南在前排后方侧翼，避免第一时间吃集火。'],risk=['没有凯南就先给打工牌；残血别硬等五费。','本图原阵没有第二名花妖，不默认有治疗。']),
 dict(name='猎人转巨龙',hero='远古巨龙',eq=[2001,2039,41816],comp=89,n=108,top=74.07,win=38.89,avg=2.82,level='条件强势',mech=['猎人转补物理加成，参与击败后继续加成。','巨龙的物理吐息与范围普攻能利用这份属性。'],entry=['先有猎人转，再看能否稳血上9。','巨龙占2人口；德莱文与巨龙转职凑猎人。'],route=['8级先用两星牌稳场，9级再找龙和前排。','巨龙放后排侧翼，留出吐息打多人的角度。'],risk=['五费成型样本有偏差，不能开局无脑冲。','地狱火转巨龙也可看：151样本，前四77.48%。']),
 dict(name='暗爪卡蜜尔',hero='卡蜜尔',eq=[2001,2039,6073],comp=115,n=127,top=71.65,win=14.17,avg=3.45,level='条件强势',mech=['击败目标后解负面，冲向4格内最远敌人。','接下两次暴击增伤，给近战C连续收割机会。'],entry=['早有暗行者之爪，卡蜜尔本体多时考虑。','沿用卡丽蜜儿框架，优先保证卡蜜尔装备。'],route=['5级追卡蜜尔与一费前排，成型再升人口。','卡蜜尔放侧翼切入，奥恩先接第一轮伤害。'],risk=['卡在第一只肉盾就难启动，观察对位再换边。','全体系前四仅45.98%，普通装备不能照搬。']),
 dict(name='护臂天使',hero='凯尔',eq=[2010,2038,6084],comp=88,n=46,top=71.74,win=26.09,avg=3.35,level='小样本观察',mech=['参与击败后叠法强、护甲和魔抗。','天使持续普攻吃法强收益，前排需撑住时间。'],entry=['早拿探索者的护臂，天使与前排来牌顺。','以森林天使框架试玩；羊刀、法爆为补装参考。'],route=['6级找两星天使与前排，顺牌再追三星。','天使放后排，与主坦同侧，避开对方切入点。'],risk=['仅46个英雄携装样本，没有锁定整套阵容。','别按71.74%当稳定上分结论，先小范围试。']),
 dict(name='花妖转螳螂',hero='卡兹克',eq=[2005,2039,41810],comp=116,n=44,top=68.18,win=11.36,avg=3.84,level='小样本观察',mech=['花妖参与击败回蓝，帮助螳螂接下一次技能。','搭配原生花妖奶妈，可补到2花妖治疗。'],entry=['先有花妖转，且螳螂、人马来牌顺。','参考裁决螳螂框架；夜刃、正义是补装建议。'],route=['7级保两星核心，再按来牌追三；8级补奶妈。','螳螂放前排侧翼，观察落点，别扎进集火区。'],risk=['仅44个英雄携装样本，不能和上面三套直排。','花妖转占一个装备格，爆发不足时会卡击败。'])]
s=Card('冷门构筑强度榜','金铲铲 S18 / 18.2a / 09.18','拿到关键条件再玩 · 3套主看，2套观察')
s.tx(50,273,'条件强势 / 阵容内携带者分项',29,'#753cf4',800)
for j,d in enumerate(builds[:3]):
 y=300+j*211;s.rect(42,y,996,191);s.pic(H[d['hero']],65,y+25,103);s.pic(E[str(d['eq'][-1])],179,y+60,65);s.tx(272,y+58,d['name'],38,w=800);s.tx(272,y+111,f"前四 {d['top']:.2f}% · 登顶 {d['win']:.2f}%",30);s.tx(272,y+158,f"{d['n']}样本 · 平均排名{d['avg']:.2f}",25,'#756187')
s.tx(50,1000,'小样本观察 / 英雄携装分项',29,'#9b6926',800)
for j,d in enumerate(builds[3:]):
 y=1025+j*137;s.rect(42,y,996,119,'#fff5df');s.pic(H[d['hero']],65,y+19,78);s.tx(166,y+48,d['name'],33,w=800);s.tx(166,y+90,f"{d['n']}样本 · 前四{d['top']:.2f}% · 暂不定强度档",26)
s.tx(48,1367,'不同口径分开看；先有装备，再看经济与来牌。',26,'#756187');s.link('常规阵容榜｜9套站位＋装备＋码');s.save(C/'01-冷门构筑强度榜.svg')
for i,d in enumerate(builds):
 s=Card(d['name'],f"09.18 / {d['level']} / {i+2:02d}—06",f"前四 {d['top']:.2f}% · 登顶 {d['win']:.2f}% · 均名 {d['avg']:.2f} · {d['n']}样本")
 s.pic(H[d['hero']],50,245,106)
 for k,eid in enumerate(d['eq']):
  x=208+k*275;s.pic(E[str(eid)],x,247,69);s.tx(x,346,E[str(eid)]['name'],23,w=650)
 s.tx(50,399,'装备为参考搭配；统计未证明这三件套的独立成绩。',25,'#756187')
 for j,(label,lines) in enumerate([('玩法变化',d['mech']),('什么开局值得玩',d['entry']),('搜牌与站位',d['route']),('最容易翻车的地方',d['risk'])]):
  y=438+j*195;s.rect(42,y,996,177,'#fff5df' if j==3 else '#fff');s.tx(64,y+45,label,30,'#753cf4',800)
  for k,line in enumerate(lines):s.tx(64,y+96+k*41,line,27)
 names=[h['heroName'] for h in comp(d['comp'])['heroes'] if h['heroType']==0]
 s.tx(49,1270,'阵容框架 · 来源码见正文，导入后手动调整装备',26,w=800)
 for j in range(0,len(names),5):s.tx(49,1316+j//5*39,' / '.join(names[j:j+5]),26,'#756187')
 s.rect(42,1424,996,129,'#e6dcf4');s.tx(63,1468,'统计口径：'+('所属体系内的携带者分项' if i<3 else '英雄携带该装备，未锁定本图框架'),25,w=750);s.tx(63,1517,'成型表现不等于开局成功率；运营与补装为整理建议。',25,'#756187');s.save(C/f'{i+2:02d}-{d["name"]}.svg')
# post text
codes=lambda ds:'\n\n'.join(d['name']+'\n'+d['gameCode'].split('#')[-1] for d in ds)
main='9.18更新｜18.2a热修独立统计。\n地狱火仍在前排，裁决螳螂进入主榜；卡丽蜜儿普通体系先放下，有暗爪再看另一篇冷门榜。两篇封面都有指路。\n\n图1榜单，图2选阵容，图3—11站位装备。地狱火继续艾希带转：1092样本，前四77.66%；封面66.44%是整个体系。\n\n'+codes(ds)+'\n\n码来自DataJ，未游戏导入验证。地狱火导入后按图改装，把转给艾希；巨龙占2人口，召唤物不占人口。\n来源：DataJ高分段样本，18.2a共25912局，截至9/18 03:25。按体系前四率排序，分档沿用来源；不是全服统计。\n#金铲铲之战 #金铲铲S18 #阵容推荐 #阵容码'
cold='纹章、神器到了手，才考虑转这几套。\n花妖转凯南、猎人转巨龙、暗爪卡蜜尔，是这次优先看的3个分支。护臂天使、花妖转螳螂只有46/44个样本，放观察区，不当稳分答案。\n\n每页写了开局、机制、搜牌和翻车点。五费分支要有经济和血量，一费分支要看来牌。没有核心装备，回主页常规榜选阵容；两篇封面互相指路。\n\n下面是基础框架码，导入后按图手动换装备，未游戏导入验证：\n\n'+codes([comp(i) for i in [112,89,115,88,116]])+'\n\n前3套为所属体系内携带者分项；后2套为英雄携装分项，未锁定完整阵容。不能混排，也不是图上三件套的独立胜率。\n来源：DataJ高分段样本，18.2a，截至9/18 03:25。运营与补装是整理建议，尚无逐局实战复核。\n#金铲铲之战 #金铲铲S18 #冷门阵容 #神器 #阵容码'
for name,body in [('常规榜',main),('冷门榜',cold)]:
 (R/f'posts/{name}-20260918-body.txt').write_text(body);print(name,len(body))
(P/'manifest.json').write_text(json.dumps({'main':{'title':'S18常规阵容榜9.18｜附阵容码','images':[str(p) for p in sorted(M.glob('*.png'))]},'cold':{'title':'S18冷门构筑榜9.18｜有条件再玩','images':[str(p) for p in sorted(C.glob('*.png'))]},'state':'prepared_not_submitted'},ensure_ascii=False,indent=2))
