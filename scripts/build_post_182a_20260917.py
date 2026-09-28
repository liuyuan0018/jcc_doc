from pathlib import Path
import re,json,subprocess,html,shutil
R=Path(__file__).resolve().parents[1]; OLD=R/'exports/S18-18.2原笔记修正-20260916';OUT=R/'exports/S18-18.2a热修提醒-20260917';OUT.mkdir(exist_ok=True)
NODE='/Users/lyu/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
if not Path(NODE).exists():NODE=shutil.which('node')
replacements={
'地狱火95':('艾希带转：前四76.2%｜9789样本；非体系胜率。','9.17：升9需68经验；先稳血，带转选择待新样本验证。'),
'巨龙95':('8枚棋子占9人口：远古巨龙占2人口，需预留位置。','9.17：升9需68经验；8枚棋子占9人口，巨龙占2。'),
'野怪小红':('后期9人口模板；8枚棋子中，远古巨龙占2人口。','9.17：升9更贵；小红与大红是不同弈子，勿混用改动。'),
'重装女警':('8人口成型参考；主C站后排，前排随对手方向调整。','9.17：大蓝护盾提高；这套的热修后表现仍待观察。'),
'7野怪鸡哥':('图为9人口模板；7野怪是羁绊名称，不是7人口阵容。','9.17：大红混合调整、大蓝护盾提高；升9需68经验。'),
'古纳拉95':('8枚棋子占9人口；石皮树、生命花为召唤物。','9.17：升9需68经验；巨龙占2人口，召唤物不占。'),
'射箭韦鲁斯':('其他低费按来牌追三，不必把图示三星全部追齐。','9.17：凯尔单体上调、冲击波下调；慎的护盾提高。'),
'卡丽蜜儿':('阿卡丽主C；其他低费按来牌追三，不必全员三星。','9.17：卡蜜尔护盾、伤害下调；本套先观察，别硬玩。'),
'永森95':('9人口成型参考；五费没来时，先保留两星打工牌。','9.17：旧版统计已降A；小样本观察，暂不列S级推荐。')}
for p in sorted(OLD.glob('*.svg')):
 if p.name.startswith('01'):continue
 name=p.stem.split('-',1)[1];s=p.read_text();a,z=replacements[name];assert a in s;s=s.replace(a,z)
 s=s.replace('金铲铲之战 / S18 · 18.2','金铲铲之战 / S18 · 9.16配置参考')
 s=s.replace('2026.09.16｜运营为整理建议','9.16配置沿用 · 9.17热修提示')
 s=s.replace('九人口运营 / 379样本观察','九人口运营 / 旧版A档观察')
 s=s.replace('九人口运营 / 2956样本参考','九人口运营 / 升9节奏调整')
 s=s.replace('18.2配置参考 · 装备随来装调整｜阵容码见正文','9.16配装参考 · 18.2a强度待验证｜阵容码见正文')
 if name=='地狱火95':s=s.replace('九人口运营 / 艾希带转','九人口运营 / 原带转方案参考')
 if name=='卡丽蜜儿':s=s.replace('一费追三 / 阿卡丽主C','一费追三 / 热修后先观察')
 (OUT/p.name).write_text(s)
# Preserve the accepted card style; cover prioritizes the patch over stale rates.
S=['<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1650" viewBox="0 0 1080 1650">','<rect width="1080" height="1650" fill="#f0ecf8"/>','<style>text{font-family:"PingFang SC","Microsoft YaHei",sans-serif}</style>']
def rect(x,y,w,h,c,r=16):S.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{c}"/>')
def t(x,y,v,size=28,c='#292139',weight=400):S.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{c}" font-weight="{weight}">{html.escape(v)}</text>')
rect(40,37,7,26,'#793af7',0);t(60,60,'金铲铲之战 / S18',25,weight=600);rect(805,28,235,55,'#793af7');t(839,67,'9.17 热修',30,'white',700)
t(40,166,'18.2a 今晚怎么打',65,weight=800);t(43,226,'先看改动，再看后面的9套配置参考',31,'#806c95',600)
blocks=[('01','95更贵，先稳血再上9',['8→9、9→10所需经验：64 → 68','运营建议：先保两星质量，别照旧节奏硬冲人口。']),('02','卡蜜尔削弱，卡丽蜜儿先观察',['护盾与技能伤害下调；阿卡丽仍是图示主C。','运营建议：有来牌再考虑，旧前四率不代表热修强度。']),('03','大蓝、慎护盾提高',['大蓝护盾：330/430 → 350/450（法术加成）','前排受益，但不能据此断言整套阵容变成T0。']),('04','大红是混合调整，别认成小红',['绯红印记树怪：攻击、无视护甲提高，技能伤害下调。','野怪小红主C是「绯红树怪」，不是这次调整的大红。'])]
for i,(n,title,lines) in enumerate(blocks):
 y=273+i*227;rect(40,y,1000,203,'white');rect(62,y+23,66,49,'#e9ddfc',10);t(76,y+58,n,28,'#793af7',700);t(148,y+59,title,36,weight=700)
 for j,line in enumerate(lines):t(65,y+116+j*43,line,27,'#655473')
rect(40,1202,1000,219,'#fff0d5');t(64,1250,'今晚暂不把旧胜率当新版本排名',35,'#9b5920',700)
t(64,1300,'18:00核对：数据站仍只有18.2口径，累计199,240局。',28,'#9b5920');t(64,1345,'尚无18.2a独立筛选；永森旧版已降A，仅作观察。',28,'#9b5920');t(64,1390,'后9图沿用9.16站位配装，逐图补充热修提醒。',28,'#9b5920')
t(40,1481,'9套阵容码保留在正文，可复制',37,'#793af7',700);t(40,1533,'地狱火码导入后，按图手动调整装备。',28,'#806c95');rect(40,1560,1000,3,'#793af7',0);t(40,1606,'依据：9.17官方公告 / dataj.cc · 运营为整理建议',24,'#806c95');S.append('</svg>');(OUT/'01-18.2a热修提醒.svg').write_text(''.join(S))
for p in sorted(OUT.glob('*.svg')):subprocess.run([NODE,str(R/'scripts/export_png.cjs'),str(p),str(p.with_suffix('.png'))],check=True,capture_output=True)
body='''9月17日18:00更新｜18.2a热修提醒
今晚先注意：升9、升10都要68经验；卡蜜尔护盾和伤害被削，卡丽蜜儿先观察。大蓝、慎护盾提高。调整的大红是绯红印记树怪，不是野怪小红主C绯红树怪。

数据站仍只有18.2累计口径，没有18.2a独立筛选，所以先撤下旧胜率封面。后9图保留9.16站位配装，并补上热修提醒；图序不代表新版排名。永森旧版已降A，不再列S级推荐。

阵容码复制名称下方完整字母数字。地狱火导入后按图手调装备，艾希带转沿用原方案，热修后表现待验证。

'''
oldbody=(OLD/'正文.txt').read_text();codes=re.findall(r'【([^】]+)】\n([A-Za-z0-9]+)',oldbody);assert len(codes)==9
for name,code in codes:body+=f'【{name}】\n{code}\n\n'
body+='''地狱火转＝金铲铲＋反曲之弓，先有转再考虑。追三看实际来牌，不必全员三星；普通装备不强求全套。巨龙占2人口，古纳拉的石皮树、生命花不占人口。

来源：金铲铲之战9.17官方公告；金铲铲大数据18.2非官方样本199,240局，尚未单拆热修后对局。本文为改动提醒与原配置参考。

#金铲铲之战 #金铲铲S18 #阵容推荐 #阵容码 #版本更新'''
title='S18热修9.17｜附9套阵容码';assert len(body)<=1000 and len(title)<=20,(len(body),len(title))
(OUT/'正文.txt').write_text(body+'\n');(OUT/'标题.txt').write_text(title+'\n');(OUT/'发布说明.md').write_text('更新原笔记6aa37e050000000029013c00；10图9码。首图替换旧胜率榜，其余沿用9.16站位配装并增加热修提醒。巨龙与永森来源最新装备有变化，本轮未采用，明确标注9.16配置。未游戏导入验证。来源：https://www.taptap.cn/moment/849355947523443908 及 https://www.dataj.cc/comp 。\n')
(R/'outputs/post182a-20260917-checks.json').write_text(json.dumps({'status':'draft_not_published','images':10,'codes':9,'body_chars':len(body),'independent_182a_filter':False,'source_version':'18.2','total_matches':199240,'template_date':'2026-09-16','game_import_verified':False},ensure_ascii=False,indent=2))
print(title,len(body),OUT)
