from pathlib import Path
import json,re,subprocess,shutil,sys
import build_new_cards_20260908 as b
R=Path(__file__).resolve().parents[1];OUT=R/'exports/S18-18.2新笔记-20260911';OUT.mkdir(exist_ok=True)
g=json.loads((R/'outputs/gamedata-20260911.json').read_text())['data'];b.G=g;b.H={h['name']:h for h in g['hero']};b.E={str(e['id']):e for e in g['equip']};b.T={str(t['id']):t for t in g['trait']};b.OUT=OUT
b.CONFIG['射箭韦鲁斯']={'kind':'一费主C追三 / 无需转职','gear':['韦鲁斯','凯尔','瑟庄妮'],'start':'韦鲁斯来得多、物理装合适时考虑。','roll':'5级追韦鲁斯三星；稳住后升人口补前排。','tip':'其他低费按来牌追三，不必把图示三星全部追齐。'}
b.CONFIG['5迅射月男']={'kind':'迅射转职 / 9.11热修观察','gear':['厄斐琉斯','绯红印记树怪','阿木木','苍蓝雕纹魔像'],'start':'先有迅射转给大红；4迅射档已削弱，谨慎参考。','roll':'保两星前排与月男，按经济升9补齐图示阵容。','tip':'5名迅射开4迅射档；热修后每次攻击加成9%→8%。'}
b.CONFIG['古纳拉95']['kind']='九人口运营 / 273样本观察'
b.CONFIG['永森95']['kind']='九人口运营 / 69样本观察'
cs=[c for c in json.loads((R/'outputs/ranking-live-20260911.json').read_text()) if c['tier']=='S']
for c in cs:
 if c['compId'] in ['112','114']:
  d=json.loads((R/f"outputs/emblem-{c['compId']}-20260911.json").read_text())['data'];eid='41806' if c['compId']=='112' else '41815';v=next(r for r in d['heroEquips'] if str(r['id'])==eid)
  for k in ['top4Rate','topRate','avgPlacement','sampleCount']:c[k]=v[k]
cs.sort(key=lambda c:-c['top4Rate'])
(R/'outputs/ranking-post182.json').write_text(json.dumps(cs,ensure_ascii=False,indent=2))
checks=[]
for i,c in enumerate(cs,1):
 if '--sample' in sys.argv and c['name']!='射箭韦鲁斯':continue
 d=json.loads((R/f"outputs/comp-{c['compId']}-20260911.json").read_text())['data'];name=d['name']
 assert len({h['position'] for h in d['heroes']})==len(d['heroes'])
 for n in b.CONFIG[name]['gear']:
  h=next(h for h in d['heroes'] if h['heroName']==n);eq=[b.E[e['equipId']] for e in d['equips'] if e['compHeroId']==h['id']];assert len(eq)==3
  for e in eq:
   assert str(e['synthesis1']) in b.E and str(e['synthesis2']) in b.E
 result=b.build(d,i);p=OUT/f'{i+1:02d}-{name}.svg';s=p.read_text().replace('18.1c','18.2').replace('2026.09.08','2026.09.11')
 if name!='地狱火艾希':s=s.replace('艾希需地狱火转', '大红需迅射转' if name=='5迅射月男' else '3★ 为追三参考')
 if name=='古纳拉95':s=s.replace('来源暂未提供阵容码 · 按图手动配置（253局，样本较少）','阵容码已补齐 · 见正文｜巨龙占2人口，召唤物不占人口')
 elif name=='5迅射月男':s=s.replace('需地狱火转 · 金铲铲＋反曲之弓｜纯阵容码见正文','迅射转＝金锅锅＋反曲之弓 · 数据为9.11热修前')
 elif name=='射箭韦鲁斯':s=s.replace('需地狱火转 · 金铲铲＋反曲之弓｜纯阵容码见正文','图示3迅射档 · 9.11调整4/5档加成｜阵容码见正文')
 elif name!='地狱火艾希':s=s.replace('需地狱火转 · 金铲铲＋反曲之弓｜纯阵容码见正文','18.2首日配置参考 · 装备随来装调整｜阵容码见正文')
 p.write_text(s);subprocess.run([b.NODE,str(R/'scripts/export_png.cjs'),str(p),str(p.with_suffix('.png'))],check=True,capture_output=True);checks.append(result)
if '--sample' in sys.argv:print(checks);sys.exit()
base=(R/'scripts/build_rank_20260909.py').read_text().replace('outputs/gamedata-20260909.json','outputs/gamedata-20260911.json').replace('outputs/ranking-live-20260909.json','outputs/ranking-post182.json').replace("OUT=R/'exports/ranking-20260909'","OUT=R/'exports/S18-18.2新笔记-20260911'")
base=base.replace('9.7首发','9.10数据').replace('9.9更新','9.11读榜').replace('S18强势阵容榜','S18新版阵容榜').replace('9套S级＋裁决转奶妈','18.2首日 · 附9套码').replace('18.1c  /  前9套按前四率排序','前四率排序 / 非热修后榜')
base=base.replace('拉露恩 · 暂无阵容码','拉露恩 · 273样本观察').replace('需迅射转 · 观察 · 暂无码','大红迅射转 · 热修观察')
base=base.replace("'均排{avg:.2f} · {c[\"sampleCount\"]:,}局'","'均排{avg:.2f} · 样本{c[\"sampleCount\"]:,}'")
base=base.replace("rect(40,1701,1000,3,'#753cf4')","rect(40,1550,1000,90,'#fff0d5',10)\nt(59,1587,'9.11热修：4/5迅射攻速加成下调；2裁决真伤异常修复。',24,'#9b5920',700)\nt(59,1624,'月男图示4迅射受影响；本榜统计未覆盖热修。',23,'#9b5920')\nrect(40,1701,1000,3,'#753cf4')")
base=base.replace('完整阵容见后图 · 阵容码见正文（古纳拉 / 月男暂无码）','完整阵容见后图 · 9套阵容码均已放在正文')
base=base.replace('18.1c版本总样本114,416局 · 月男183局 / 永森227局 / 古纳拉339局','数据：9.10 / 18.2 / 15,432局；永森69样本仅作观察。')
base=base.replace('奶妈单列：婕拉裁决转＋青龙刀＋虚空杖的装备分项。','艾希、月男仅限定必要纹章；其他取体系数据，普通装备不限。')
base=base.replace('2026.09.09 · 评级沿用原站','9.11整理 · 热修前参考')
exec(compile(base,str(R/'scripts/build_rank_20260909.py'),'exec'),{'__file__':str(R/'scripts/build_rank_20260909.py')})
p=OUT/'01-9.9强势阵容榜.svg';t=OUT/'01-18.2新版阵容榜.svg';p.rename(t);subprocess.run([b.NODE,str(R/'scripts/export_png.cjs'),str(t),str(t.with_suffix('.png'))],check=True,capture_output=True)
imgs=sorted(OUT.glob('*.png'));assert len(imgs)==10
upload=OUT/'上传图片';upload.mkdir(exist_ok=True)
for p in imgs:shutil.copy2(p,upload/p.name)
title='S18新版阵容榜｜9.11热修提醒'
body='''18.2新版另开一篇，方便和旧版区分。
本篇采用9月10日首日数据，附9月11日热修提示，不能当作热修后的确定排名。

先看变化：补入射箭韦鲁斯；裁决转奶妈、皎月不再列入本篇强势推荐。艾希仍需地狱火转，月男图示大红需迅射转，普通装备按来装调整。

9.11热修：4/5迅射每次攻击攻速加成由9%/15%降至8%/12%；修复2裁决使错误附带真实伤害。月男图示开4迅射，需继续观察；韦鲁斯图示3迅射不属于本次直接调整档位。

图1看榜单，图2—10按顺序看站位与装备合成。只复制阵容名下面的字母数字，手机换行部分也要一起复制。

'''
for c in cs:
 d=json.loads((R/f"outputs/comp-{c['compId']}-20260911.json").read_text())['data'];code=d['gameCode'].split('#')[-1];assert re.fullmatch('[A-Za-z0-9]+',code)
 body+='【'+c['name']+'】\n'+code+'\n\n'
body+='''来源：金铲铲大数据18.2首日15,432局。艾希、月男取对应英雄携带必要纹章的分项，其余取体系数据，按前四率排序。永森仅69样本，古纳拉273样本，暂作参考。

阵容码仅便于配置，不保证来牌与转职。巨龙占2人口，古纳拉的石皮树、生命花不占人口。

#金铲铲之战 #金铲铲S18 #阵容推荐 #阵容码 #版本更新'''
assert len(title)<=20 and len(body)<=1000,(len(title),len(body))
comment='18.2新版单独开了一篇，9套阵容码都在正文，月男和古纳拉的也补上啦～本篇是9月10日首日数据，9月11日热修影响已标在图里，别和旧版混用。'
for name,text in [('标题',title),('正文',body),('置顶评论-发布后再用',comment)]:(OUT/(name+'.txt')).write_text(text+'\n')
guide='# 18.2新笔记试稿 · 未发布\n\n新建图文笔记，保留旧笔记。按上传图片文件夹01—10顺序选择10张PNG，标题正文使用同目录TXT。没有压缩包。\n\n来源数据为9月10日18.2首日，采集于9月11日；热修提示来自官方9月11日公告 https://jcc.qq.com/#/news/14805020511287824089 。补丁数据不是热修后统计。阵容配置、装备和9条码已回读来源18.2接口；新卡与9套图采用来源模板，运营为整理建议，未做游戏导入或实战验证。9套中永森低样本作为观察。已核对页码、图序、码与配方引用。\n\n'+ '\n'.join(p.name for p in imgs)
(OUT/'发布说明.md').write_text(guide);(R/'posts/S18-18.2新笔记-试稿.md').write_text(guide+'\n\n## 标题\n'+title+'\n\n## 正文\n'+body+'\n\n## 置顶评论\n'+comment)
(R/'outputs/post182-checks.json').write_text(json.dumps({'cards':checks,'body_chars':len(body),'title_chars':len(title),'codes':9,'images':10,'status':'draft_not_published'},ensure_ascii=False,indent=2))
print('完成',len(imgs),'图',len(body),'字')
