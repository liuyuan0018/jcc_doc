from pathlib import Path
import json,base64,html,urllib.request,subprocess,collections
R=Path(__file__).resolve().parents[1];OUT=R/'exports/gunala-two-page-sample';OUT.mkdir(exist_ok=True)
G=json.loads((R/'outputs/gamedata-20260908.json').read_text())['data'];H={str(h['id']):h for h in G['hero']};HX={str(h['id']):h for h in G['hex']};E={str(h['id']):h for h in G['equip']};D=json.loads((R/'outputs/comp113-initialBattleBuilds.json').read_text());A=R/'assets/ranking';NODE='/Users/lyu/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
s=(R/'exports/ranking-20260908/08-古纳拉95.svg').read_text().replace('08 / 10','01 / 02').replace('古纳拉95</text>','古纳拉95 · 成型</text>',1)
p=OUT/'01-古纳拉95-成型与装备.svg';p.write_text(s)
subprocess.run([NODE,str(R/'scripts/export_png.cjs'),str(p),str(p.with_suffix('.png'))],check=True,capture_output=True)
o=['<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1653"><rect width="1080" height="1653" fill="#f0edf8"/><g font-family="PingFang SC,sans-serif">']
def tx(x,y,t,z=23,c='#281e39',w=600):o.append(f'<text x="{x}" y="{y}" font-size="{z}" fill="{c}" font-weight="{w}">{html.escape(str(t))}</text>')
def rect(x,y,w,h,c='#fff'):o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{c}"/>')
def pic(v,x,y,w):
 u=v.get('picture',v.get('icon'));p=A/Path(u).name
 if not p.exists():p.write_bytes(urllib.request.urlopen(u).read())
 o.append(f'<image x="{x}" y="{y}" width="{w}" height="{w}" href="data:image/png;base64,{base64.b64encode(p.read_bytes()).decode()}"/>')
rect(40,35,7,24,'#753cf4');tx(61,57,'金铲铲之战 / S18 · 18.1c',23);tx(900,57,'02 / 02',24)
tx(40,137,'古纳拉95 · 怎么选',58,w=850);tx(42,190,'人口分布、变阵与强化参考',27,c='#753cf4');tx(42,226,'体系样本253局 · 9.8数据 · 来源暂未提供阵容码',23,c='#84718f')
for i,lv in enumerate([7,8,9,10]):
 x=40+255*i;v=next(t for t in D if t['peopleNum']==lv);rect(x,248,235,93,'#753cf4' if lv==9 else '#fff');tx(x+20,283,f'{lv}人口',25,'#fff' if lv==9 else '#281e39');tx(x+20,322,f"{v['playRate']:.1f}%",30,'#fff' if lv==9 else '#753cf4',800)
tx(42,375,'9人口变阵参考',29,w=800);tx(580,374,'样本数不同，不当作换牌收益',22,'#84718f')
bs=next(x for x in D if x['peopleNum']==9)['builds'][:3]
labels=['原模板','乐芙兰替牛头','洛替塔里克']
for j,b in enumerate(bs):
 y=393+j*122;rect(40,y,1000,111)
 tx(57,y+28,labels[j],20,'#753cf4',750)
 for i,h in enumerate(b['heroes']):
  z=H[str(h['heroId'])];x=59+i*104;pic(z,x,y+38,48);n=z['name'];tx(x+24-len(n)*14/2,y+103,n,14)
 tx(906,y+49,f"{b['avgPlacement']:.2f}",28,w=800);tx(902,y+78,'平均排名',17,'#84718f');tx(902,y+102,f"{b['sampleCount']}局",18,'#84718f')
tx(42,797,'前期过渡示例',29,w=800);tx(580,795,'独立4人口样本，不是固定升级路线',21,'#84718f')
b=next(x for x in D if x['peopleNum']==4)['builds'][0];rect(40,815,1000,113)
for i,h in enumerate(b['heroes']):
 z=H[str(h['heroId'])];x=64+i*120;pic(z,x,830,55);tx(x+27-len(z['name'])*19/2,914,z['name'],19)
tx(582,855,'洛 · 卡尔玛 · 约里克 · 芸阿娜',23);tx(582,890,'仅15条样本，按来牌和两星质量过渡',21,'#84718f')
tx(42,977,'强化推荐 · 来源站列表',29,w=800);tx(42,1011,'不代表胜率排名，也不是固定拿取顺序。',22,'#84718f')
hexes=json.loads((R/'outputs/comp113-initialRecommendedHexes.json').read_text())['hexes']
for j,h in enumerate(hexes):
 x=40+j%5*204;y=1032+j//5*121;rect(x,y,184,110);pic(HX[h['id']],x+65,y+10,53);tx(x+92-len(h['name'])*20/2,y+91,h['name'],20)
tx(42,1317,'散件需求 · 对应前页四名棋子的参考满装',26,w=800)
c=collections.Counter();comp=json.loads((R/'outputs/comp-113-20260908.json').read_text())['data']
for e in comp['equips']:
 for k in ['synthesis1','synthesis2']:c[str(E[e['equipId']][k])]+=1
for j,(id,n) in enumerate(c.most_common()):
 x=48+j*123;pic(E[id],x,1342,48);tx(x+55,1378,f'×{n}',22)
rect(40,1414,1000,121,'#e6dcf4');tx(61,1453,'两点提醒',25,'#753cf4',800);tx(61,1490,'古纳拉只有253局，第三个变阵仅3局，先看组合，不盲追均排。',24);tx(61,1520,'散件数量是参考满装合计，不是开局必须凑齐的清单。',22,'#59456f')
tx(42,1580,'先看成型图，再按对局来牌调整。暂无阵容码，可手动配置。',25,'#753cf4',750)
tx(42,1621,'来源：金铲铲大数据 dataj.cc/comp/113 · 2026.09.08',21,'#84718f')
o.append('</g></svg>');p=OUT/'02-古纳拉95-变阵与选择.svg';p.write_text('\n'.join(o));subprocess.run([NODE,str(R/'scripts/export_png.cjs'),str(p),str(p.with_suffix('.png'))],check=True,capture_output=True)
print(OUT)
