from pathlib import Path
import json,re,subprocess,shutil
R=Path(__file__).resolve().parents[1]
basecs=json.loads((R/'outputs/ranking-base-emblem-20260909.json').read_text());es={r['compId']:r for r in json.loads((R/'outputs/ranking-emblem-20260909.json').read_text())}
cs=[]
for c in basecs:
 if c['tier']!='S' and c['name']!='裁决奶妈':continue
 c=dict(c)
 if c['compId'] in es:
  for k in ['top4Rate','topRate','avgPlacement','sampleCount']:c[k]=es[c['compId']]['stats'][k]
  c['statScope']='指定英雄携带指定纹章，其他装备不限'
 else:c['statScope']='体系整体'
 cs.append(c)
cs.sort(key=lambda c:-c['top4Rate']);(R/'outputs/ranking-final-emblem-20260909.json').write_text(json.dumps(cs,ensure_ascii=False,indent=2))
base=(R/'scripts/build_rank_20260909.py').read_text().replace('outputs/ranking-live-20260909.json','outputs/ranking-final-emblem-20260909.json').replace("OUT=R/'exports/ranking-20260909'","OUT=R/'exports/ranking-20260909-emblem'")
base=base.replace("  top4,win,avg=65.07,22.45,3.66;c={**c,'sampleCount':3020}\n",'')
base=base.replace('9套S级＋裁决转奶妈','10套阵容 · 含转职分支').replace('18.1c  /  前9套按前四率排序','18.1c / 按前四率参考排序')
base=base.replace("'#fff3df' if n=='裁决奶妈' else ('#ffffff' if i%2==0 else '#e8e1f2')","'#ffffff' if i%2==0 else '#e8e1f2'")
base=base.replace('婕拉三件套 · 单列不排序','婕拉 · 裁决转').replace('需迅射转 · 观察 · 暂无码','大红迅射转 · 小样本观察')
base=base.replace("f'均排{avg:.2f} · {c[\"sampleCount\"]:,}局'","f'均排{avg:.2f} · 样本{c[\"sampleCount\"]:,}'")
base=base.replace('18.1c版本总样本114,416局 · 月男183局 / 永森227局 / 古纳拉339局','普通阵容取体系数据；转职分支仅限定纹章，其他装备不限。')
base=base.replace('奶妈单列：婕拉裁决转＋青龙刀＋虚空杖的装备分项。','月男58样本仅作观察；永森227、古纳拉339，排名可能波动。')
base=base.replace('评级沿用原站','纹章分项见正文')
exec(compile(base,str(R/'scripts/build_rank_20260909.py'),'exec'),{'__file__':str(R/'scripts/build_rank_20260909.py')})
out=R/'exports/ranking-20260909-emblem';src=R/'exports/ranking-20260909';node='/Users/lyu/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
def render(p):subprocess.run([node,str(R/'scripts/export_png.cjs'),str(p),str(p.with_suffix('.png'))],check=True,capture_output=True)
render(out/'01-9.9强势阵容榜.svg')
for i,c in enumerate(cs,2):
 n=c['name'];p=next(src.glob('*-'+n+'.svg'));s=p.read_text();s=re.sub(r'\d{2} / 11',f'{i:02d} / 11',s)
 if n=='裁决奶妈':s=s.replace('婕拉三件套分项：前四65.07% · 吃鸡22.45% · 3,020样本','婕拉带裁决转：前四61.97% · 11,410样本 · 其他装备不限')
 if n=='5迅射月男':s=s.replace('当前仅183局','转职分项仅58样本')
 target=out/(f'{i:02d}-'+('裁决转奶妈' if n=='裁决奶妈' else n)+'.svg');target.write_text(s);render(target)
imgs=sorted(out.glob('*.png'));assert len(imgs)==11
upload=out/'手动上传-仅图片';upload.mkdir(exist_ok=True)
for p in imgs:shutil.copy2(p,upload/p.name)
codes=dict(re.findall(r'【([^】]+)】\n([A-Za-z0-9]+)',(src/'正文.txt').read_text()));codes['裁决奶妈']=codes['裁决转奶妈']
body='''9月9日更新｜S18·18.1c
普通阵容看体系数据；需转职的配置只限定纹章，其他装备不限制。裁决转奶妈只讨论婕拉带裁决转的分支。

图1看榜单，图2—11按顺序看站位、装备合成和搜牌方向。月男分项仅58样本，暂作观察，不宜据此认定强于奶妈。
阵容码复制名称下方完整字母数字，换行部分也别漏。

'''
for i,c in enumerate(cs,2):
 n=c['name'];body+='【'+('裁决转奶妈' if n=='裁决奶妈' else n)+'】\n'+(codes[n] if n in codes else f'暂无阵容码，按图{i}手动配置。')+'\n\n'
body+='''转职条件：奶妈的裁决转给婕拉；艾希需地狱火转（金铲铲＋反曲之弓）；月男的大红需迅射转（金锅锅＋反曲之弓），5名迅射开4迅射档。先有对应转职，再考虑图示配置。

来源：金铲铲大数据，9月9日18.1c。艾希、奶妈、月男分别取上述英雄携带对应纹章的装备分项；其余取体系统计，按前四率参考排序。样本为来源统计记录，不代表固定九人阵容实战胜率。永森227、古纳拉339样本也需继续观察。

普通装备按来装调整。奶妈码含9人口艾翁；古纳拉的巨龙占2人口，石皮树和生命花不占人口。

#金铲铲之战 #金铲铲S18 #阵容推荐 #阵容码 #金铲铲大数据'''
title='9月9日S18阵容榜（附阵容码）';assert len(body)<1000
for name,text in [('标题',title),('正文',body),('置顶评论-更新后再发',(src/'置顶评论-更新后再发.txt').read_text())]:(out/(name+'.txt')).write_text(text+'\n')
guide='# 最新发布素材 · 转职口径修正版\n\n未上传、未提交。替换原笔记6a9e3a720000000028003f36；图片仅使用本文件夹「手动上传-仅图片」内01—11，共11张；复制同目录标题、正文，实际更新后再发置顶评论。\n\n口径：普通七套采用体系统计；艾希、裁决转奶妈、月男分别采用指定英雄携带必要纹章的单装备分项，不锁定其他装备。按前四率降序作参考，月男58样本显著标注观察，不代表精确强弱差异。未重新赋S/A评级。来源单装备记录可能存在重复或聚合，与体系样本不一定一一对应，不能用分项减总量推算无转对照。只证明携带条件相关表现，不证明因果。\n\n之前主C三件套版已作废，不要上传。保留原站位装备参考，仅更新页码、奶妈统计说明与月男样本。阵容码未做游戏内导入验证。\n\n图片顺序：\n'+ '\n'.join(p.name for p in imgs)
(out/'发布说明.md').write_text(guide)
(R/'posts/S18-9.9更新-转职口径修正版.md').write_text(guide+'\n\n## 标题\n'+title+'\n\n## 正文\n'+body)
p=R/'README.md';s=p.read_text();s=s[s.index('# 金铲铲 · Codex 本地项目'):];p.write_text('## 最新发布素材 · 9.9转职口径修正版\n\n[发布文件夹](exports/ranking-20260909-emblem/) · [发布文案](posts/S18-9.9更新-转职口径修正版.md)\n\n已制作，未上传、未提交。普通阵容用体系数据；转职分支仅限定对应纹章，不限其他装备。之前三件套版已作废。\n\n'+s)
(R/'exports/ranking-20260909-unified/已作废-请勿上传.txt').write_text('此版将统计过度限制为主C三件套，已作废。请使用同级ranking-20260909-emblem文件夹。\n')
print('BODY',len(body));print([(c['name'],c['top4Rate'],c['sampleCount']) for c in cs])
