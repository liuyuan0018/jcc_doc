from pathlib import Path
import json,re,subprocess,shutil,sys
import build_new_cards_20260908 as b
R=Path(__file__).resolve().parents[1];OUT=R/'exports/S18-18.2原笔记修正-20260913';OUT.mkdir(exist_ok=True)
g=json.loads((R/'outputs/gamedata-20260913.json').read_text())['data'];b.G=g;b.H={h['name']:h for h in g['hero']};b.E={str(e['id']):e for e in g['equip']};b.T={str(t['id']):t for t in g['trait']};b.OUT=OUT
b.CONFIG['射箭韦鲁斯']={'kind':'一费主C追三 / 无需转职','gear':['韦鲁斯','凯尔','瑟庄妮'],'start':'韦鲁斯来得多、物理装合适时考虑。','roll':'5级追韦鲁斯三星；稳住后升人口补前排。','tip':'其他低费按来牌追三，不必把图示三星全部追齐。'}
b.CONFIG['卡丽蜜儿']={'kind':'一费追三 / 阿卡丽主C','gear':['阿卡丽','卡蜜尔','奥恩','韦鲁斯'],'start':'阿卡丽、卡蜜尔来得多，装备适合近战输出时考虑。','roll':'5级追核心三星，前排同步提质量，再升人口。','tip':'阿卡丽主C；其他低费按来牌追三，不必全员三星。'}
b.CONFIG['5迅射月男']={'kind':'迅射转职 / 9.11热修观察','gear':['厄斐琉斯','绯红印记树怪','阿木木','苍蓝雕纹魔像'],'start':'先有迅射转给大红；4迅射档已削弱，谨慎参考。','roll':'保两星前排与月男，按经济升9补齐图示阵容。','tip':'5名迅射开4迅射档；热修后每次攻击加成9%→8%。'}
b.CONFIG['地狱火95']={'kind':'九人口运营 / 希维尔主C','gear':['希维尔','艾希','阿木木','凯南'],'start':'有地狱火转，物理装备合适且经济允许升9时考虑。','roll':'先稳住希维尔和前排质量，再升9补艾希、凯南。','tip':'地狱火转给希维尔；艾希副C，按来装分配装备。'}
b.CONFIG['古纳拉95']['kind']='九人口运营 / 1350样本参考'
b.CONFIG['永森95']['kind']='九人口运营 / 222样本观察'
cs=[c for c in json.loads((R/'outputs/ranking-live-20260913.json').read_text()) if c['tier']=='S']
for c in cs:
 if c['compId']=='112':c.update(json.loads((R/'outputs/comp-112-20260913.json').read_text())['data'])
cs.sort(key=lambda c:-c['top4Rate'])
(R/'outputs/ranking-post182.json').write_text(json.dumps(cs,ensure_ascii=False,indent=2))
checks=[]
for i,c in enumerate(cs,1):
 if '--sample' in sys.argv and c['name']!='卡丽蜜儿':continue
 d=json.loads((R/f"outputs/comp-{c['compId']}-20260913.json").read_text())['data'];name=d['name']
 assert len({h['position'] for h in d['heroes']})==len(d['heroes'])
 for n in b.CONFIG[name]['gear']:
  h=next(h for h in d['heroes'] if h['heroName']==n);eq=[b.E[e['equipId']] for e in d['equips'] if e['compHeroId']==h['id']];assert len(eq)==3
  for e in eq:
   assert str(e['synthesis1']) in b.E and str(e['synthesis2']) in b.E
 result=b.build(d,i);p=OUT/f'{i+1:02d}-{name}.svg';s=p.read_text().replace('18.1c','18.2').replace('2026.09.08','2026.09.13')
 if name=='地狱火95':s=s.replace('艾希需地狱火转','希维尔需地狱火转')
 elif name!='地狱火艾希':s=s.replace('艾希需地狱火转', '大红需迅射转' if name=='5迅射月男' else '3★ 为追三参考')
 if name=='古纳拉95':s=s.replace('来源暂未提供阵容码 · 按图手动配置（253局，样本较少）','阵容码已补齐 · 见正文｜巨龙占2人口，召唤物不占人口')
 elif name=='5迅射月男':s=s.replace('需地狱火转 · 金铲铲＋反曲之弓｜纯阵容码见正文','迅射转＝金锅锅＋反曲之弓 · 数据为9.11热修前')
 elif name=='射箭韦鲁斯':s=s.replace('需地狱火转 · 金铲铲＋反曲之弓｜纯阵容码见正文','图示3迅射档 · 9.11调整4/5档加成｜阵容码见正文')
 elif name not in ['地狱火艾希','地狱火95']:s=s.replace('需地狱火转 · 金铲铲＋反曲之弓｜纯阵容码见正文','18.2配置参考 · 装备随来装调整｜阵容码见正文')
 p.write_text(s);subprocess.run([b.NODE,str(R/'scripts/export_png.cjs'),str(p),str(p.with_suffix('.png'))],check=True,capture_output=True);checks.append(result)
if '--sample' in sys.argv:print(checks);sys.exit()
base=(R/'scripts/build_rank_20260909.py').read_text().replace('outputs/gamedata-20260909.json','outputs/gamedata-20260913.json').replace('outputs/ranking-live-20260909.json','outputs/ranking-post182.json').replace("OUT=R/'exports/ranking-20260909'","OUT=R/'exports/S18-18.2原笔记修正-20260913'")
base=base.replace('9.7首发','9.12数据').replace('9.9更新','9.13更新').replace('S18强势阵容榜','S18新版阵容榜').replace('9套S级＋裁决转奶妈','18.2版本 · 附9套码').replace('18.1c  /  前9套按前四率排序','按前四率排序 / 条件见图')
base=base.replace('拉露恩 · 暂无阵容码','拉露恩 · 1350样本参考').replace('需迅射转 · 观察 · 暂无码','大红迅射转 · 热修观察')
base=base.replace("'均排{avg:.2f} · {c[\"sampleCount\"]:,}局'","'均排{avg:.2f} · 样本{c[\"sampleCount\"]:,}'")
base=base.replace("rect(40,1701,1000,3,'#753cf4')","rect(40,1550,1000,90,'#fff0d5',10)\nt(59,1587,'地狱火95：希维尔带转主C，艾希副C。',24,'#9b5920',700)\nt(59,1624,'数据更新至9.12，未单独拆出热修后的对局。',23,'#9b5920')\nrect(40,1701,1000,3,'#753cf4')")
base=base.replace('完整阵容见后图 · 阵容码见正文（古纳拉 / 月男暂无码）','完整阵容见后图 · 9套阵容码均已放在正文')
base=base.replace('18.1c版本总样本114,416局 · 月男183局 / 永森227局 / 古纳拉339局','数据：9.12 / 18.2 / 75,984局；永森222样本仅作观察。')
base=base.replace('奶妈单列：婕拉裁决转＋青龙刀＋虚空杖的装备分项。','各阵容均取体系数据；地狱火图示需希维尔带转。')
base=base.replace('2026.09.09 · 评级沿用原站','9.13整理 · 非官方统计')
exec(compile(base,str(R/'scripts/build_rank_20260909.py'),'exec'),{'__file__':str(R/'scripts/build_rank_20260909.py')})
p=OUT/'01-9.9强势阵容榜.svg';t=OUT/'01-18.2新版阵容榜.svg';p.rename(t);subprocess.run([b.NODE,str(R/'scripts/export_png.cjs'),str(t),str(t.with_suffix('.png'))],check=True,capture_output=True)
imgs=sorted(OUT.glob('*.png'));assert len(imgs)==10
upload=OUT/'上传图片';upload.mkdir(exist_ok=True)
for p in imgs:shutil.copy2(p,upload/p.name)
title='S18阵容榜9.13｜附9套阵容码'
body='9月13日更新｜S18·18.2\n卡丽蜜儿继续上升，巨龙95保持靠前；地狱火95更新为希维尔带转主C、艾希副C。月男移出本篇主推荐，裁决转奶妈与皎月暂不收录。\n\n图1看榜单，图2—10按同一顺序看站位、装备合成和搜牌方向。阵容码只复制名称下方完整字母数字，换行部分也要一起复制。\n\n'
for c in cs:
 d=json.loads((R/f"outputs/comp-{c['compId']}-20260913.json").read_text())['data'];code=d['gameCode'].split('#')[-1];assert re.fullmatch('[A-Za-z0-9]+',code)
 body+='【'+c['name']+'】\n'+code+'\n\n'
body+='希维尔图示需地狱火转（金铲铲＋反曲之弓），先有转再考虑；其他配置不强求图示普通装备全套。卡丽蜜儿、韦鲁斯等追三阵容按来牌决定，图中三星不代表必须全部追齐。\n\n9月11日已调整4/5迅射攻速加成，并修复2裁决使异常真伤。当前统计更新至9月12日，未单独拆分热修后的对局，不能把变化全归因于热修。\n\n来源：金铲铲大数据，18.2共75,984局。各阵容均取体系数据，按前四率排序。永森仅222样本，继续观察；高前四率不等于任意开局都能复现。\n\n巨龙占2人口；古纳拉的石皮树、生命花不占人口。\n\n#金铲铲之战 #金铲铲S18 #阵容推荐 #阵容码 #版本更新'
assert len(title)<=20 and len(body)<=1000,(len(title),len(body))
comment='9月13日数据已更新～卡丽蜜儿继续上升，9套阵容码都在正文。月男这次移出主推荐，地狱火转给希维尔，艾希副C。大家玩下来哪套更稳，也可以在评论区聊聊。'
for name,text in [('标题',title),('正文',body),('置顶评论-发布后再用',comment)]:(OUT/(name+'.txt')).write_text(text+'\n')
guide='# 9.13 地狱火模板修正\n\n更新原笔记 6aa37e050000000029013c00。地狱火95采用9月13日抓取模板及阵容码：希维尔主C带地狱火转、艾希副C。榜单采用体系数据67.72%前四率、30.48%吃鸡率、6459样本。其他八套配置保留。\n\n'+'\n'.join(p.name for p in imgs)
(OUT/'发布说明.md').write_text(guide);(R/'posts/S18-18.2新笔记-9.13发布稿.md').write_text(guide+'\n\n## 标题\n'+title+'\n\n## 正文\n'+body+'\n\n## 置顶评论\n'+comment)
(R/'outputs/post182-20260913-checks.json').write_text(json.dumps({'cards':checks,'body_chars':len(body),'title_chars':len(title),'codes':9,'images':10,'status':'draft_not_published'},ensure_ascii=False,indent=2))
print('完成',len(imgs),'图',len(body),'字')
