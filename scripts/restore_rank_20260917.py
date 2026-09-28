from pathlib import Path
import json,subprocess,re,shutil
R=Path(__file__).resolve().parents[1];O=R/'exports/S18-18.2a热修含榜单-20260917';O.mkdir(exist_ok=True);old=R/'exports/S18-18.2a热修提醒-20260917'
cs=json.loads((R/'outputs/ranking-api-20260917-1800.json').read_text())['data'];ids=['112','104','100','89','99','113','110','115','91'];cs=[c for c in cs if c['compId'] in ids]
for c in cs:
 d=json.loads((R/f"outputs/comp-{c['compId']}-20260916{'-post' if c['compId']=='112' else ''}.json").read_text())['data']
 for k in ['heroes','equips']:c[k]=d[k]
(R/'outputs/ranking-cover-20260917.json').write_text(json.dumps(cs,ensure_ascii=False,indent=2))
s=(R/'scripts/build_rank_20260909.py').read_text().replace('outputs/gamedata-20260909.json','outputs/gamedata-20260913.json').replace('outputs/ranking-live-20260909.json','outputs/ranking-cover-20260917.json').replace("OUT=R/'exports/ranking-20260909'","OUT=R/'exports/S18-18.2a热修含榜单-20260917'").replace("if c['tier']=='S' or c['name']=='裁决奶妈'","if True")
for a,b in [('9.7首发','18:00采集'),('9.9更新','9.17更新'),('S18强势阵容榜','S18阵容参考榜'),('9套S级＋裁决转奶妈','18.2累计 · 非热修后'),('18.1c  /  前9套按前四率排序','8套S＋永森A档观察'),('拉露恩 · 暂无阵容码','拉露恩'),('完整阵容见后图 · 阵容码见正文（古纳拉 / 月男暂无码）','图2热修提醒 · 图3—11阵容参考 · 九套码见正文'),('18.1c版本总样本114,416局 · 月男183局 / 永森227局 / 古纳拉339局','9.17 18:00采集：18.2累计199,240局；未单拆18.2a。'),('奶妈单列：婕拉裁决转＋青龙刀＋虚空杖的装备分项。','配装沿用9.16参考；卡蜜尔已削弱，热修后重新观察。'),('2026.09.09 · 评级沿用原站','2026.09.17 · 非官方样本')]:s=s.replace(a,b)
s=s.replace("'均排{avg:.2f} · {c[\"sampleCount\"]:,}局'","'均排{avg:.2f} · 样本{c[\"sampleCount\"]:,}'")
s=s.replace("else n,30,w=800)","else ('永森95 · A' if n=='永森95' else n),30,w=800)")
s=s.replace("rect(40,1701,1000,3,'#753cf4')","rect(40,1550,1000,90,'#fff0d5',10)\nt(59,1587,'18.2a已更新：升9/10更贵，卡蜜尔削弱。',26,'#9b5920',700)\nt(59,1624,'本页是18.2累计统计，不代表热修后的强度排名。',24,'#9b5920')\nrect(40,1701,1000,3,'#753cf4')")
exec(compile(s,str(R/'scripts/build_rank_20260909.py'),'exec'),{'__file__':str(R/'scripts/build_rank_20260909.py')})
(O/'01-9.9强势阵容榜.svg').rename(O/'01-18.2累计阵容榜.svg')
for p in sorted(old.glob('*.svg')):
 n=int(p.name[:2]);v=p.read_text()
 if n==1:v=v.replace('后9图沿用9.16站位配装，逐图补充热修提醒。','图3—11沿用9.16站位配装，逐图补充热修提醒。').replace('今晚暂不把旧胜率当新版本排名','图1为18.2累计榜，非热修后排名')
 else:v=v.replace(f'{n:02d} / 10',f'{n+1:02d} / 11')
 (O/f'{n+1:02d}-{p.name[3:]}').write_text(v)
for p in O.glob('*.svg'):subprocess.run([ '/Users/lyu/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node',str(R/'scripts/export_png.cjs'),str(p),str(p.with_suffix('.png'))],check=True,capture_output=True)
body=(old/'正文.txt').read_text().replace('所以先撤下旧胜率封面。后9图保留9.16站位配装，并补上热修提醒；图序不代表新版排名。','图1保留18.2累计榜，图2看热修提醒；图3—11保留9.16站位配装并补上提示，卡片沿用原顺序。榜单不是热修后排名。')
(O/'正文.txt').write_text(body);(O/'标题.txt').write_text('S18阵容榜9.17｜附9套阵容码\n');print(len(body),len(list(O.glob('*.png'))))
