from pathlib import Path
import json,base64,html,urllib.request,argparse,subprocess
R=Path(__file__).resolve().parents[1]
G=json.loads((R/'references/web/s18-gamedata.json').read_text())['data']
D=json.loads((R/'outputs/ranking-cards-source-20260907.json').read_text())
H={h['name']:h for h in G['hero']}; E={str(e['id']):e for e in G['equip']}; T={str(t['id']):t for t in G['trait']}
A=R/'assets/ranking';A.mkdir(exist_ok=True)
OUT=R/'exports/ranking-complete-v2';OUT.mkdir(exist_ok=True)
NODE='/Users/lyu/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
CONFIG={
'重装女警':{'kind':'二费追三','gear':['凯特琳','伊莉丝','赫卡里姆'],'start':'女警、蜘蛛来得多，且有攻速装备时考虑。','roll':'6级先找两星，再追女警、蜘蛛三星；成型后升人口。','tip':'8人口成型参考；主C站后排，前排随对手方向调整。'},
'巨龙95':{'kind':'九人口运营','gear':['远古巨龙','德莱文','茂凯'],'start':'经济和血量好，中期能靠两星棋子稳住时考虑。','roll':'先用现有两星阵容过渡，9级搜大龙、德莱文和前排。','tip':'8枚棋子占9人口：远古巨龙占2人口，需预留位置。'},
'野怪小红':{'kind':'一费追三 → 九人口','gear':['绯红树怪','远古石甲虫','苍蓝哨戒'],'start':'小红来得多，有物理技能装，能开野怪过渡时考虑。','roll':'5级追小红，成型后升人口；不要为小蓝强行耗光经济。','tip':'后期9人口模板；8枚棋子中，远古巨龙占2人口。'},
'7野怪鸡哥':{'kind':'三费主C / 野怪体系','gear':['深红锋喙鸟','苍蓝雕纹魔像','绯红印记树怪'],'start':'攻速装合适，鸡哥与野怪牌来得顺时考虑。','roll':'7级先找两星鸡哥；来牌多再追三，否则升8/9补质量。','tip':'图为9人口模板；7野怪是羁绊名称，不是7人口阵容。'},
'永森95':{'kind':'九人口运营','gear':['伊泽瑞尔','德莱文','塔里克'],'start':'永森过渡顺、物理装多，且经济允许升9时考虑。','roll':'8级先用两星伊泽瑞尔稳血；9级再补五费与前排。','tip':'9人口成型参考；五费没来时，先保留两星打工牌。'},
'皎月螳螂':{'kind':'三费追三','gear':['黛安娜','卡兹克','赫卡里姆'],'start':'皎月、人马来得多，且能做法系近战装备时考虑。','roll':'7级先找两星核心，按来牌追三星；之后升8补齐模板。','tip':'8人口模板；皎月、人马先保质量，螳螂按来牌追三。'},
'裁决奶妈':{'kind':'四费运营 / 婕拉转职分支','gear':['婕拉','索拉卡','墨菲特'],'start':'有裁决转、法系装备合适时，考虑图示婕拉分支。','roll':'8级先搜两星婕拉、奶妈、石头人；稳住后升9补位。','tip':'图与码均为含艾翁的9人口模板；8人口先不上艾翁。'},
}
SHORT={'鬼索的狂暴之刃':'羊刀','海妖之怒':'海妖','锐利之刃':'锐利之刃','朔极之矛':'青龙刀','最后的轻语':'轻语','斯特拉克的挑战护手':'血手','石像鬼石板甲':'石像鬼板甲','圣盾使的誓约':'圣盾使誓约','强袭者的链枷':'强袭者链枷','班克斯的魔法帽':'班克斯魔法帽'}
manifest=[]
def asset(v):
 u=v['picture'];p=A/Path(u).name
 if not p.exists():p.write_bytes(urllib.request.urlopen(u).read())
 manifest.append({'name':v['name'],'url':u,'path':str(p.relative_to(R))})
 return 'data:image/png;base64,'+base64.b64encode(p.read_bytes()).decode()
def build(d,index):
 c=CONFIG[d['name']];pop=len(d['heroes'])+int(any(h['heroName']=='远古巨龙' for h in d['heroes']))
 O=['<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1440"><rect width="1080" height="1440" fill="#f0edf8"/><path d="M795 0H1080V208H940Z" fill="#e5dcf4"/><g font-family="PingFang SC, sans-serif">']
 def tx(x,y,s,z=26,color='#281e39',w=500):O.append(f'<text x="{x}" y="{y}" font-size="{z}" fill="{color}" font-weight="{w}">{html.escape(str(s))}</text>')
 def rect(x,y,w,h,color,r=0,stroke=None):O.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{color}"'+(f' stroke="{stroke}" stroke-width="2"' if stroke else '')+'/>')
 def pic(v,x,y,w):
  q=f'p{len(O)}';O.append(f'<clipPath id="{q}"><rect x="{x}" y="{y}" width="{w}" height="{w}" rx="7"/></clipPath><image x="{x}" y="{y}" width="{w}" height="{w}" href="{asset(v)}" clip-path="url(#{q})"/>')
 rect(40,35,7,24,'#753cf4');tx(61,57,'金铲铲之战 / S18 · 18.1c',23,w=750);tx(900,57,f'{index+1:02d} / 08',24,w=750)
 tx(40,139,d['name'],64,w=850)
 rect(42,164,154,41,'#753cf4',5);tx(59,193,f'{pop}人口模板',25,'#fff',750);tx(219,194,c['kind'],26,'#756187',650)
 traits=[f"{T[t['id']]['num']}{t['name']}" for t in d['traits'] if t['id'] in T and T[t['id']]['num']>1]
 tx(43,244,'主要羁绊  '+' · '.join(traits[:4]),23,'#756187')
 rect(38,269,1004,509,'#fff',16);tx(61,299,'参考站位 · 上方为敌方',22,'#84718f');tx(793,299,'3★ 为追三参考',20,'#84718f')
 bypos={h['position']:h for h in d['heroes']};assert len(bypos)==len(d['heroes'])
 for row in range(4):
  for col in range(7):
   x=61+col*133+(28 if row%2 else 0);y=318+row*109
   h=bypos.get(f'{row+1},{col+1}')
   rect(x,y,119,101,'#f0ebf7' if h else '#faf8fc',9, '#d8c8ed' if h else '#eee8f4')
   if not h:continue
   n=h['heroName'];pic(H[n],x+28,y+6,63)
   colors={1:'#8c939d',2:'#2fa774',3:'#3e85d7',4:'#9a55d5',5:'#bf902a'}
   rect(x+4,y+4,21,23,colors[h['price']],4);tx(x+9,y+21,h['price'],15,'#fff',750)
   if h['heroStarNum']==3:rect(x+84,y+4,32,21,'#fff1bb',4);tx(x+86,y+20,'3★',15,'#946b0b',800)
   if len(n)>5:tx(x+9,y+85,n[:3],18,w=650);tx(x+9+54,y+85,n[3:],18,w=650)
   else:tx(x+(119-len(n)*21)/2,y+91,n,21,w=650)
 tx(42,818,'核心装备参考',29,w=800);tx(700,817,'按来装调整，不必强求全套',22,'#84718f')
 for j,n in enumerate(c['gear']):
  y=837+j*93;hero=next(h for h in d['heroes'] if h['heroName']==n);es=[E[e['equipId']] for e in d['equips'] if e['compHeroId']==hero['id']]
  assert len(es)==3
  rect(40,y,1000,83,'#fff',10);pic(H[n],57,y+13,57);tx(127,y+48,n,22,w=750)
  for k,e in enumerate(es):
   x=336+k*226;pic(e,x,y+19,45);tx(x+55,y+48,SHORT.get(e['name'],e['name']),19,'#54415f',650)
 rect(40,1136,1000,194,'#e6dcf4',12)
 tx(61,1176,'什么开局',23,'#753cf4',800);tx(194,1176,c['start'],25)
 tx(61,1220,'搜牌方向',23,'#753cf4',800);tx(194,1220,c['roll'],25)
 tx(61,1271,c['tip'],24,'#59456f',650)
 tx(42,1372,'看阵容：左右滑图  ·  直接开打：正文复制对应阵容码',26,'#753cf4',750)
 tx(42,1408,f"模板 / 装备：dataj.cc/comp/{d['compId']} · 2026.09.07｜运营为整理建议",19,'#84718f')
 O.append('</g></svg>');p=OUT/f'{index+1:02d}-{d["name"]}.svg';p.write_text('\n'.join(O));subprocess.run([NODE,str(R/'scripts/export_png.cjs'),str(p),str(p.with_suffix('.png'))],check=True,capture_output=True)
 return {'name':d['name'],'population':pop,'heroes':len(d['heroes']),'path':str(p.with_suffix('.png').relative_to(R)),'source':d['source_url'],'code_matches_source':True}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--sample',action='store_true');args=ap.parse_args();results=[]
 for i,d in enumerate(D):
  if args.sample and i:break
  results.append(build(d,i+1))
 (R/'outputs/ranking-card-assets.json').write_text(json.dumps(list({x['url']:x for x in manifest}.values()),ensure_ascii=False,indent=2))
 (R/'outputs/ranking-card-checks.json').write_text(json.dumps(results,ensure_ascii=False,indent=2));print(json.dumps(results,ensure_ascii=False))
