from pathlib import Path
import json
R=Path('/Users/lyu/Documents/ChatGPT/金铲铲');s=(R/'research/episode-one-revision-20260926/prepare.py').read_text()
s=s.replace('frontline-episode-01-rerun-v5','frontline-episode-02-v2').replace('frontline-episode-01-video-v6','frontline-episode-02-video-v1').replace('ranking-no-heart.json','ranking.json').replace('frontline-episode-one-revised-v6','frontline-episode-two-v1').replace('frontline-one-v6','frontline-two-v1').replace('前排压测 · 三件普通装','前排压测 · 两普通一神器')
a=s.index('labels={');b=s.index('def equip',a)
s=s[:a]+'''labels={5:'饮血',16:'大天使',24:'振奋',27:'板甲',33:'狂徒',85:'大亨',87:'飞升护符',89:'连指手套',96:'光盾徽章',100:'禁忌雕像'}
keys={5:'bloodthirster',16:'archangels_staff',24:'spirit_visage',27:'gargoyle_stoneplate',33:'warmogs_armor',85:'5004',87:'talisman_of_ascension',89:'mittens',96:'lightshield_crest',100:'forbidden_idol'}
def augments(r):
 return [dict(label=r['augmentName'],iconKey='augment/'+('soloplate2'if r['augment']==4 else'thegoldendragon2'))]if r['augment']in[2,4]else[]
'''+s[b:]
s=s.replace("label=r['label'],soloLabel", "label=r['label']+' '+name(r),soloLabel")
s=s.replace('range(1100,', 'range(1250,').replace('2251','2601').replace("tierLabel='普通装备 · 逐档加压',headerStatus='8位前排 · 修正版'","tierLabel='逐档加压'if phase=='battle'else'暂停查看',headerStatus='蔚继续加压'if layout=='solo'else'8位前排'")
s=s.replace("simFrom=0,simTo=30 if phase=='battle'else 0", "simFrom=30 if phase=='hold'else 0,simTo=30 if phase in['battle','hold']else 0")
a=s.index("add('cover'");b=s.index("chapters.append(dict(start=t,title='榜单",a)
s=s[:a]+'''add('cover','cover','intro',8,1250,tracks(1250,initial=True),'两件普通装，一件神器。这次从一百七十多万套配置里，比较谁更能扛。')
add('rules','eight','intro',10,1250,tracks(1250,initial=True),'每档满血重开，撑满三十秒再加五十。护臂排除，光盾按护盾给自己计算。')
chapters.append(dict(start=t,title='八位前排逐档压测'))
for d in range(1250,2601,50):
 active=[r for r in main if r['failedDps']>=d];dead=[r for r in active if r['failedDps']==d];solo=len(active)==1;focus=active[0]['id']if solo else None;layout='solo'if solo else'eight'
 duration=7.5 if (d<=1650 or d>=2550)else 1.5
 rec=[dict(dps=x,status='current'if x==d else'pass')for x in range(max(1700,d-450),d+1,50)]if solo else[]
 s=add(f'B{d}',layout,'battle',duration,d,tracks(d),focus=focus,records=rec,best=d-50 if solo else None)
 if d==1700:chapters.append(dict(start=s['start'],title='蔚继续加压'))
 for r in dead:deaths.append(s['start']+cache[r['id'],d]['samples'][-1]['time']/30*duration)
 text=None;hold=.25
 if d==1250:text='一千二百五，八位全部通过。';hold=4
 elif dead:
  text=f'{num(d)}档，'+ '、'.join(name(r)for r in dead)+'没撑满三十秒。';hold=5.5
  if d==1350:text='一千三百五，蜘蛛和稻草人都没过，两位并列。';hold=6
  if d==1650:text='一千六百五，龙龟没通过。只剩蔚，继续加压。';hold=6
  if d==2600:text='两千六百没通过。这组条件下，蔚最高通过两千五百五十档。';hold=7
 elif d==1600:text='一千六百档，蔚和龙龟都通过。';hold=4.5
 elif d==2550:text='两千五百五，蔚撑满了三十秒。再加五十。';hold=5.5
 elif d==1700:text='中间通过档加快播放，每档仍然满血重开。';hold=5
 rec=[dict(dps=x,status='fail'if x==d and dead else'pass')for x in range(max(1700,d-450),d+1,50)]if solo else[]
 add(f'H{d}',layout,'hold',hold,d,tracks(d,True),text,focus,rec,d-50 if dead and solo else d if solo else None)
 if text:facts.append(dict(cue=f'H{d}',dps=d,failed=[r['id']for r in dead],passed=[r['id']for r in active if r not in dead],field='failedDps'if dead else'passedDps',expectedBest=2550 if d==2600 else None))
'''+s[b:]
s=s.replace("augments=[dict(label=r['augmentName'],iconKey='augment/soloplate2')]if r['augment']==4 else[]","augments=augments(r)")
s=s.replace('697,200','1,706,880').replace('69.72万','170.688万').replace('barScaleDps=2250','barScaleDps=2600')
s=s.replace('三件普通装备，可合法重复','2普通＋1神器，排除护臂').replace('无海克斯 / 适用单身板甲','无 / 单身板甲 / 金霖龙')
s=s.replace('第一页，刚才出镜的八位。洛、蜘蛛和石甲虫并列第五。','第一页，刚才出镜的八位。蜘蛛和稻草人并列第六。').replace('第二页，接着看牛头、人马、阿木木和慎这些前排。','第二页，阿木木也是并列第八。牛头这套大亨搭配金霖龙，多占一个人口。').replace("'results','result',8,","'results','result',10,")
s=s.replace("shutil.copy2(ROOT/'exports/frontline-rammus-eight-v1/rammus-eight-recipe.json',OUT/'recipe.json')", "shutil.copy2(ROOT/'exports/frontline-episode-01-video-v9/recipe.json',OUT/'recipe.json')")
s=s.replace("'BaseCombinations/Count':'24位'","'BaseCombinations/Count':'24','BaseCombinations/Unit':'位'").replace("'AugmentCombinations/Count':'170.688万'","'AugmentCombinations/Count':'<size=76>170.688</size>','AugmentCombinations/Unit':'<size=40>万套</size>'").replace("'Total':'先选配置，再排24位英雄'","'Total':'<size=64>各英雄最优配置排名</size>'").replace("'RankingRule':'每50来伤加压至首败 · 人口与羁绊逐行标注'","'RankingRule':'最高通过档排序'").replace("'CombinationDefinition':'Main演示8位 · Results列全24位'","'CombinationDefinition':'演示8位 · 榜单列全24位'")
(R/'research/episode-two-video-20260926/prepare.py').write_text(s)
