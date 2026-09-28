from pathlib import Path
import json,base64,html,urllib.request,subprocess
R=Path(__file__).resolve().parents[1]
G=json.loads((R/'outputs/frontline-gamedata-20260907.json').read_text())['data']
H={h['name']:h for h in G['hero']}
OUT=R/'exports/frontline-v1';OUT.mkdir(exist_ok=True)
NODE='/Users/lyu/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
def build(i,title,sub,heroes,blocks,foot):
 o=['<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1440"><rect width="1080" height="1440" fill="#f0edf8"/><g font-family="PingFang SC,sans-serif">']
 def tx(x,y,s,z=29,c='#281e39',w=500):o.append(f'<text x="{x}" y="{y}" font-size="{z}" fill="{c}" font-weight="{w}">{html.escape(s)}</text>')
 def rect(x,y,w,h,c,r=15):o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{c}"/>')
 rect(42,39,7,26,'#753cf4',0);tx(63,62,'金铲铲 S18 · 缺牌应急',24,w=750);tx(908,62,f'0{i} / 04',23)
 for j,s in enumerate(title):tx(42,150+j*80,s,65,w=850)
 tx(45,285,sub,27,'#756187')
 for j,(name,label) in enumerate(heroes):
  x=46+j*247;p=R/'assets/ranking'/Path(H[name]['picture']).name
  if not p.exists():p.write_bytes(urllib.request.urlopen(H[name]['picture']).read())
  b=base64.b64encode(p.read_bytes()).decode();rect(x,323,237,186,'#fff')
  o.append(f'<image x="{x+66}" y="338" width="105" height="105" href="data:image/png;base64,{b}"/>')
  tx(x+118,0,'',1);o.append(f'<text x="{x+118}" y="481" text-anchor="middle" font-size="25" font-weight="700" fill="#281e39">{html.escape(label)}</text>')
 for j,(head,lines) in enumerate(blocks):
  y=546+j*247;rect(40,y,1000,226,'#fff');tx(64,y+45,head,31,'#753cf4',800)
  for k,s in enumerate(lines):tx(64,y+95+46*k,s,28)
 tx(44,1334,foot,25,'#59456f',700)
 tx(44,1380,'羁绊 / 模板：dataj.cc · 2026.09.07 · 18.1c',21,'#84718f')
 tx(44,1414,'替换为过渡思路，未做实战强度对比。',21,'#84718f')
 o.append('</g></svg>');p=OUT/f'{i:02d}.svg';p.write_text('\n'.join(o));subprocess.run([NODE,str(R/'scripts/export_png.cjs'),str(p),str(p.with_suffix('.png'))],check=True,capture_output=True)
build(1,['阿木木、大蓝没来','这局怎么接着打？'],'先看你玩哪套，再决定补谁。',[('阿木木','阿木木'),('苍蓝雕纹魔像','大蓝'),('黛安娜','皎月'),('瑟庄妮','猪妹')],[
 ('重装女警 → 先保四重装',['洛、蜘蛛、人马都在时，皎月可以补第四个重装。','她能补羁绊，但补不回大蓝的团队回蓝。']),
 ('裁决奶妈 → 主宰能补，地狱火会掉',['有约里克时，猪妹或洛可以临时补两主宰。','阿木木换掉后，与凯南组成的两地狱火会消失。']),
 ('野怪体系 → 先数场上还有几只',['大蓝同时占野怪和神谕位置，不能只看前排。','少他之后，七野怪和两神谕要分开检查。'])
 ],'这里的“大蓝”指四费苍蓝雕纹魔像。')
build(2,['重装女警缺大蓝','皎月先补第四重装'],'适用：洛、蜘蛛、人马已经在场。',[('洛','洛'),('伊莉丝','蜘蛛'),('赫卡里姆','人马'),('黛安娜','皎月')],[
 ('能保住什么',['这四张都有重装战士：可以保住四重装。','女警、其他后排按原阵容保留。']),
 ('会少什么',['失去大蓝施法提供的团队回蓝，以及控制、破法。','皎月是临时补位；羁绊一样，不代表功能一样。']),
 ('什么时候继续搜',['女警、蜘蛛质量没到位，先按原节奏补核心。','大蓝来了再比较场面；别为一张大蓝拆掉成型前排。'])
 ],'补位皎月无需另追三星，也别分走主C关键装备。')
build(3,['裁决奶妈缺阿木木','先让现有前排顶住'],'适用：上一条榜单里的婕拉裁决转分支。',[('约里克','约里克'),('瑟庄妮','猪妹'),('洛','洛'),('墨菲特','石头人')],[
 ('约里克 + 猪妹 / 洛，临时保两主宰',['猪妹或洛选一张，优先考虑手里已有的两星。','这是补主宰的位置，不能当作阿木木的完整替代。']),
 ('两地狱火会掉，别忽略这笔损失',['阿木木与凯南原本开两地狱火。','换成猪妹或洛后，这一档灼烧、重伤效果会失去。']),
 ('8级搜牌时，别只盯阿木木',['一起找婕拉、奶妈和石头人的两星提升。','石头人能先承担坦装；补位牌不要另吃一整套装备。'])
 ],'等阿木木到了再调整；同时检查队伍的重伤来源。')
build(4,['野怪体系缺大蓝','先算羁绊，再换前排'],'同样少一张牌，7人口和9人口可能完全不同。',[('苍蓝雕纹魔像','大蓝'),('苍蓝哨戒','小蓝'),('远古石甲虫','石甲虫'),('深红锋喙鸟','鸡哥')],[
 ('如果原本刚好七野怪',['少大蓝后只剩六，七野怪档位会掉。','先找尚未上场的其他野怪补数，再考虑外挂前排。']),
 ('如果照上一条的9人口鸡哥模板',['九张都是不同野怪，少大蓝仍有八张，可保七野怪。','但两神谕只剩小蓝一张：神谕羁绊会消失。']),
 ('坦装先用起来，别空等大蓝',['石甲虫是原模板已有的前排，可以按现有质量承装。','已经在场的野怪再上同名牌，不会多算一个羁绊。'])
 ],'只缺一张先补位；核心也缺、装备也不合，再考虑转阵。')
print(OUT)
