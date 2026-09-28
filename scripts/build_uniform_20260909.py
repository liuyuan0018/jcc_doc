from pathlib import Path
import json,re,subprocess,shutil
R=Path(__file__).resolve().parents[1]
rs=json.loads((R/'outputs/ranking-uniform-20260909.json').read_text())
main=sorted([r for r in rs if r['stats']['sampleCount']>=100],key=lambda r:-r['stats']['top4Rate'])
obs=sorted([r for r in rs if r['stats']['sampleCount']<100],key=lambda r:-r['stats']['sampleCount'])
ordered=main+obs
base=(R/'scripts/build_rank_20260909.py').read_text()
base=base.replace("OUT=R/'exports/ranking-20260909'","OUT=R/'exports/ranking-20260909-unified'")
a=base.index('rows=[');b=base.index('\nOUT=',a)
base=base[:a]+"U={r['name']:r for r in json.loads((R/'outputs/ranking-uniform-20260909.json').read_text())}\nordered=sorted([r for r in U.values() if r['stats']['sampleCount']>=100],key=lambda r:-r['stats']['top4Rate'])+sorted([r for r in U.values() if r['stats']['sampleCount']<100],key=lambda r:-r['stats']['sampleCount'])\nrows=[(r['name'],r['stats']['top4Rate'],r['stats']['topRate'],r['stats']['avgPlacement']) for r in ordered]"+base[b:]
base=base.replace('S18强势阵容榜','S18成型阵容榜').replace('9套S级＋裁决转奶妈','同口径 · 主C三件套').replace('18.1c  /  前9套按前四率排序','≥100样本按前四率排序')
base=base.replace("y=309+i*137;c=C[n];h=","y=309+i*137;c={**C[n],'sampleCount':U[n]['stats']['sampleCount']};h=")
base=base.replace("  top4,win,avg=65.07,22.45,3.66;c={**c,'sampleCount':3020}\n",'')
base=base.replace("'#fff3df' if n=='裁决奶妈' else ('#ffffff' if i%2==0 else '#e8e1f2')","'#eeeeef' if c['sampleCount']<100 else ('#ffffff' if i%2==0 else '#e8e1f2')")
base=base.replace('婕拉三件套 · 单列不排序','婕拉 · 必须有裁决转')
base=base.replace("f'均排{avg:.2f} · {c[\"sampleCount\"]:,}局'","(f'样本{c[\"sampleCount\"]:,} · 待观察' if c['sampleCount']<100 else f'均排{avg:.2f} · 样本{c[\"sampleCount\"]:,}')")
base=base.replace("f'{top4:.1f}%'","'—' if c['sampleCount']<100 else f'{top4:.1f}%'").replace("f'{win:.1f}%'","'—' if c['sampleCount']<100 else f'{win:.1f}%'")
base=base.replace('18.1c版本总样本114,416局 · 月男183局 / 永森227局 / 古纳拉339局','各行均为图示主C三件套样本；不足100不定强度名次。')
base=base.replace('奶妈单列：婕拉裁决转＋青龙刀＋虚空杖的装备分项。','仅比较成装表现；不代表开局硬玩胜率，未控制星级等因素。')
base=base.replace('评级沿用原站','100样本为本次展示门槛')
exec(compile(base,str(R/'scripts/build_rank_20260909.py'),'exec'),{'__file__':str(R/'scripts/build_rank_20260909.py')})
out=R/'exports/ranking-20260909-unified'; src=R/'exports/ranking-20260909'; node='/Users/lyu/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
def render(p):subprocess.run([node,str(R/'scripts/export_png.cjs'),str(p),str(p.with_suffix('.png'))],check=True,capture_output=True)
render(out/'01-9.9强势阵容榜.svg')
for i,r in enumerate(ordered,2):
 n=r['name'];p=next(src.glob('*-'+n+'.svg'));s=p.read_text();s=re.sub(r'\d{2} / 11',f'{i:02d} / 11',s)
 if n=='古纳拉95':s=s.replace('339局样本','21个三件套样本').replace('（339局，样本较少）','（三件套样本21，待观察）')
 if n=='5迅射月男':s=s.replace('当前仅183局','三件套样本仅15')
 target=out/(f'{i:02d}-'+('裁决转奶妈' if n=='裁决奶妈' else n)+'.svg');target.write_text(s);render(target)
imgs=sorted(out.glob('*.png'));assert len(imgs)==11
upload=out/'手动上传-仅图片';upload.mkdir(exist_ok=True)
for p in imgs:shutil.copy2(p,upload/p.name)
oldbody=(src/'正文.txt').read_text(); codes=dict(re.findall(r'【([^】]+)】\n([A-Za-z0-9]+)',oldbody));codes['裁决奶妈']=codes['裁决转奶妈']
body='''9月9日更新｜S18·18.1c
本次统一看图示主C三件套的成装表现，按前四率排序。裁决转奶妈只统计婕拉裁决转＋青龙刀＋虚空杖。
图2—6依次为艾希、裁决转奶妈、女警、皎月、小红；图7—11为样本不足的观察配置，不代表强度倒数。

阵容码复制名称下方完整字母数字，换行部分也别漏。

'''
for i,r in enumerate(ordered,2):
 n=r['name'];body+='【'+('裁决转奶妈' if n=='裁决奶妈' else n)+'】\n'+(codes[n] if n in codes else f'暂无阵容码，按图{i}手动配置。')+'\n\n'
body+='''奶妈先有裁决转再考虑，转职给婕拉；艾希需地狱火转（金铲铲＋反曲之弓）；月男图示大红需迅射转（金锅锅＋反曲之弓），5名迅射开4迅射档。

来源：金铲铲大数据，9月9日18.1c装备分项。每行是对应三件套样本；100样本为本次展示门槛，并非原站评级。鸡哥59、古纳拉21、巨龙16、月男15、永森2，暂不定强度名次。数据仅反映成装表现，未控制星级、经济等条件，不代表开局硬玩胜率。

奶妈码为含艾翁的9人口模板；古纳拉的巨龙占2人口，石皮树和生命花不占人口。

#金铲铲之战 #金铲铲S18 #阵容推荐 #阵容码 #金铲铲大数据'''
title='9月9日S18成型榜（附阵容码）';assert len(body)<1000 and len(title)<=20
for name,text in [('标题',title),('正文',body),('置顶评论-更新后再发',(src/'置顶评论-更新后再发.txt').read_text())]:(out/(name+'.txt')).write_text(text+'\n')
guide='# 9.9统一口径版 · 未上传、未提交\n\n更新原笔记6a9e3a720000000028003f36。仅上传本文件夹的「手动上传-仅图片」内11张图，按01—11顺序。标题和正文使用同目录TXT。\n\n十套统一取图示主C精确三件套分项。>=100样本按前四率降序；其余为观察配置，按样本量降序展示，不赋强度名次。100为编辑展示门槛，不能消除成装选择偏差、星级和经济等混杂。没有统一数据支持十套可靠的完整强度排名。新增素材未经游戏实战验证。\n\n图片顺序：\n'+ '\n'.join(p.name for p in imgs)
(out/'发布说明.md').write_text(guide)
(R/'posts/S18-9.9更新-统一口径版.md').write_text(guide+'\n\n## 标题\n'+title+'\n\n## 正文\n'+body)
p=R/'README.md';s=p.read_text();s=s[s.index('# 金铲铲 · Codex 本地项目'):];p.write_text('## 最新素材 · 9.9统一口径版\n\n[发布文件夹](exports/ranking-20260909-unified/) · [发布文案](posts/S18-9.9更新-统一口径版.md)\n\n已制作，未上传。5套成装前四率排序，5套样本不足待观察。此前版本保留作历史。\n\n'+s)
print('ORDER',[(r['name'],r['stats']['sampleCount'],r['stats']['top4Rate']) for r in ordered]);print('BODY',len(body))
