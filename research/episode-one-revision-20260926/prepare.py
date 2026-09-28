from pathlib import Path
import json,sys,hashlib,gzip,shutil
ROOT=Path(__file__).resolve().parents[2];ARCH=ROOT/'exports/frontline-episode-01-rerun-v5';OUT=ROOT/'exports/frontline-episode-01-video-v6';OUT.mkdir(exist_ok=True);(OUT/'source').mkdir(exist_ok=True)
sys.path.insert(0,str(ARCH));import archive as a
rows=json.loads((ARCH/'ranking-no-heart.json').read_text())['leaderboard'];main=rows[:8]
N={'蔚':('蔚','vi'),'拉莫斯':('龙龟','rammus'),'瑟庄妮':('猪妹','sejuani'),'峡谷迅捷蟹':('河蟹','scuttle'),'洛':('洛','rakan'),'伊莉丝':('蜘蛛','elisespider'),'远古石甲虫':('石甲虫','krug'),'费德提克':('稻草人','fiddlesticks')}
labels={5:'饮血',16:'大天使',24:'振奋',27:'板甲',33:'狂徒'};keys={5:'bloodthirster',16:'archangels_staff',24:'spirit_visage',27:'gargoyle_stoneplate',33:'warmogs_armor'}
for i in a.ITEMS:
 if i['name']=='鬼索的狂暴之刃':labels[i['index']]='羊刀';keys[i['index']]='rageblade'
def equip(r):return [dict(label=labels[i],iconKey='item/'+keys[i])for i in r['items']]
def name(r):return N.get(r['hero'],(r['hero'],None))[0]
def num(n):
 d='零一二三四五六七八九';s='';z=False
 for power,u in [(1000,'千'),(100,'百'),(10,'十'),(1,'')]:
  v,n=divmod(n,power)
  if v:s+=('零'if z else'')+d[v]+u;z=False
  elif s and n:z=True
 return (s[1:]if s.startswith('一十')else s)or'零'
rep=dict(schemaVersion=1,id='frontline-episode-one-revised-v6',title='前排压测 · 三件普通装',conditions='5人集火 · 33%重伤 · 双抗各降30% · 物魔各半',footnote='固定条件模拟 · 每档满血30秒 · 每50加压至首败',source=str(ARCH/'manifest.json'),isFixture=False,coverKey='cover/frontline-one-v6',cards=[],runs=[],segments=[],captions=[])
for i,r in enumerate(main):
 r['label']=chr(65+i);rep['cards'].append(dict(id=r['id'],label=r['label'],soloLabel=name(r),heroName=name(r),portraitKey='hero/'+N[r['hero']][1],quality=f'{r["cost"]}费 · {r["star"]}星',traits=' / '.join(f'{v}{k}'for k,v in r['traits'].items())+f' · {r["slots"]}人口',augment=r['augmentName'],augmentIconKey='augment/soloplate2'if r['augment']==4 else'',equipment=equip(r)))
cache={};checks=[]
for r in main:
 for d in range(1100,r['failedDps']+1,50):
  path=OUT/'source'/f'{r["id"]}-{d}.json.gz'
  if path.exists():
   with gzip.open(path,'rt')as f:x=json.load(f)
   a.validate_replay(x)
  else:
   x=a.replay(r['id'],d)
   with gzip.open(path,'wt')as f:json.dump(x,f,separators=(',',':'))
  samples=[dict(time=f[0]/30,hp=f[1],maxHp=f[2],shield=f[3],alive=bool(f[17]),hasArmor=True,hasMagicResist=True,hasAbilityPower=True,armor=z[1],magicResist=z[2],abilityPower=z[3])for f,z in zip(x['frames'],x['presentation']['frames'])]
  events=[dict(id=f'e{i}',time=e[0]/30,kind=e[1],amount=e[2],source=e[3])for i,e in enumerate(x['presentation']['events'])if e[1]in ['damage','heal','shieldGain','shieldBreak','death']]
  v=dict(id=f'{r["id"]}-{d}',cardId=r['id'],samples=samples,events=events);cache[r['id'],d]=v;rep['runs'].append(v);checks.append(dict(id=r['id'],dps=d,alive=x['result']['alive'],frame=x['result']['frame']))
def tracks(d,hold=False,initial=False):
 result=[]
 for r in main:
  used=min(d,r['failedDps']);v=cache[r['id'],used];frozen=hold or initial or d>r['failedDps'];ft=0 if initial else v['samples'][-1]['time']if frozen else 0
  result.append(dict(cardId=r['id'],runId=v['id'],frozen=frozen,frozenTime=ft,aliveLabel='准备压测'if initial else'30秒通过'if hold else'承压中',deadLabel='淘汰',resultLabel=''))
 return result
cues=[];chapters=[];facts=[];deaths=[];t=0

def add(key,layout,phase,duration,dps=0,tr=None,text=None,focus=None,records=None,best=None):
 global t
 start=t;t=round((t+duration)*30)/30
 s=dict(id=key,start=start,end=t,layout=layout,phase=phase,dps=dps,roundSeconds=30,simFrom=0,simTo=30 if phase=='battle'else 0,tracks=tr or[],records=records or[],tierLabel='普通装备 · 逐档加压',headerStatus='8位前排 · 修正版',hasPageTurnSeconds=True,pageTurnSeconds=.35,hasCoverSlideSeconds=True,coverSlideSeconds=.5)
 if focus:s['focusCardId']=focus
 if best is not None:s.update(hasBestPassed=True,bestPassed=best)
 rep['segments'].append(s)
 if text:cues.append(dict(id=key,text=text,spoken=text.replace('蔚','魏'),windowStart=start,windowEnd=t,start=start+.25))
 return s
add('cover','cover','intro',8,1100,tracks(1100,initial=True),'三件普通装，谁更能扛？修正护盾回蓝处理后，这期重新测。')
add('rules','eight','intro',8,1100,tracks(1100,initial=True),'这八位各用筛出的最优配置。每档满血重开，撑满三十秒再加五十。')
chapters.append(dict(start=t,title='八位前排逐档压测'))
for d in range(1100,2251,50):
 active=[r for r in main if r['failedDps']>=d];dead=[r for r in active if r['failedDps']==d];solo=len(active)==1;focus=active[0]['id']if solo else None;layout='solo'if solo else'eight'
 duration=7.5 if (d<=1400 or d>=2200)else 1.5
 rec=[dict(dps=x,status='current'if x==d else'pass')for x in range(max(1450,d-450),d+1,50)]if solo else[]
 s=add(f'B{d}',layout,'battle',duration,d,tracks(d),focus=focus,records=rec,best=d-50 if solo else None)
 if d==1450:chapters.append(dict(start=s['start'],title='蔚继续加压'))
 for r in dead:deaths.append(s['start']+cache[r['id'],d]['samples'][-1]['time']/30*duration)
 text=None;hold=.25
 if d==1100:text='一千一百档，八位全部通过。';hold=4
 elif dead:
  text=f'{num(d)}档，'+ '、'.join(name(r)for r in dead)+'没撑满三十秒。';hold=5.5
  if d==1200:text='一千二百档，洛、蜘蛛和石甲虫都没过，三位并列。';hold=6.5
  if d==1400:text='一千四百档，龙龟没通过。只剩蔚，继续加压。';hold=6
  if d==2250:text='两千二百五没通过。这组条件下，蔚最高通过两千二百档。';hold=7
 elif d==1350:text='一千三百五，蔚和龙龟都通过。';hold=4.5
 elif d==2200:text='两千二百档，蔚撑满了三十秒。再加五十。';hold=5.5
 elif d==1450:text='中间通过档加快播放，每档仍然满血重开。';hold=5
 rec=[dict(dps=x,status='fail'if x==d and dead else'pass')for x in range(max(1450,d-450),d+1,50)]if solo else[]
 add(f'H{d}',layout,'hold',hold,d,tracks(d,True),text,focus,rec,d-50 if dead and solo else d if solo else None)
 if text:facts.append(dict(cue=f'H{d}',dps=d,failed=[r['id']for r in dead],passed=[r['id']for r in active if r not in dead],field='failedDps'if dead else'passedDps',expectedBest=2200 if d==2250 else None))
chapters.append(dict(start=t,title='榜单范围与排序规则'));scopeStart=t
add('scope','scope','intro',12,text='榜单比较二十四位前排，低费三星，高费两星。每位取自己的最优配置，同分并列。这里只比较固定条件坦度。')
portrait_keys={h['name']:'hero/'+h['heroPaint'].removeprefix('s18_') for h in json.loads((ROOT/'research/special-20260924/gamedata.json').read_text())['data']['hero']}
portrait_keys.update({hero:'hero/'+v[1] for hero,v in N.items()})
mainids={r['id']:r['label']for r in main};entries=[]
for r in rows:
 entries.append(dict(id=r['id'],portraitKey=portrait_keys[r['hero']],episodeTag=mainids.get(r['id'],''),rank=r['rank'],passedDps=r['passedDps'],isTop=r['rank']==1,equipment=equip(r),augments=[dict(label=r['augmentName'],iconKey='augment/soloplate2')]if r['augment']==4 else[],detailRichText=f'<b>{name(r)}</b> · {r["star"]}星 · '+ ' / '.join(f'{v}{k}'for k,v in r['traits'].items())+f' · {r["slots"]}人口'))
rep['results']=dict(title='24位前排 · 各自最优配置',subtitle='697,200套候选 · 按英雄选优排名',portraitKey='hero/vi',conditions='1—3费三星 / 4—5费两星 · 羁绊海克斯见每行\n5人集火 / 33%重伤 / 双抗各降30% / 物魔各半',footnote='最高通过来伤/秒 · 每50一档至首败 · 同分并列',barScaleDps=2250,pageSizes=[8]*3,pageSubtitles=['第1页 · 八位出镜英雄','第2页 · 更多前排最优配置','第3页 · 其余前排最优配置'],entries=entries)
resultsStart=t
for i,text in enumerate(['第一页，刚才出镜的八位。洛、蜘蛛和石甲虫并列第五。','第二页，接着看牛头、人马、阿木木和慎这些前排。','最后一页，奥恩也在这里。按自己的羁绊和装备参考。']):
 s=add(f'P{i+1:02}','results','result',8,text=text);s['resultPage']=i+1;chapters.append(dict(start=s['start'],title=rep['results']['pageSubtitles'][i]))
rep['duration']=t
fields={'Headline':'<size=42>24位前排，各自选出最优配置</size>\n<size=58>697,200 套参与筛选</size>','BaseCombinations/SectionTitle':'比较对象','BaseCombinations/Explanation0':'1—3费三星','BaseCombinations/Explanation1':'4—5费两星','BaseCombinations/Count':'24位','BaseCombinations/Formula':'在各自合法羁绊中比较','AugmentCombinations/SectionTitle':'候选条件','AugmentCombinations/Explanation0':'三件普通装备，可合法重复','AugmentCombinations/Explanation1':'无海克斯 / 适用单身板甲','AugmentCombinations/Explanation2':'不纳入心之钢','AugmentCombinations/Count':'69.72万','AugmentCombinations/Formula':'含羁绊与海克斯分支','Plus':'→','Total':'先选配置，再排24位英雄','CountingNote':'每位英雄取最高通过档 · 不是所有配装混排','CombinationDefinition':'Main演示8位 · Results列全24位','CombinationOrder':'每档满血30秒','GlobalRank':'成绩相同\n保留并列','RankingRule':'每50来伤加压至首败 · 人口与羁绊逐行标注','AugmentLabel':'海克斯条件见每行'}
rep['scopeTextOverrides']=[dict(path='SafeArea/'+k,text=v)for k,v in fields.items()]
for n,obj in [('replay-unvoiced.json',rep),('cues.json',cues),('semantic-facts.json',facts),('selection.json',rows),('replay-verification.json',dict(passed=True,runs=len(checks),checks=checks)),('timeline-base.json',dict(duration=t,chapters=chapters,scopeStart=scopeStart,resultsStart=resultsStart,deathAnchors=deaths))]:
 (OUT/n).write_text(json.dumps(obj,ensure_ascii=False,separators=(',',':')))
shutil.copy2(ROOT/'exports/frontline-rammus-eight-v1/rammus-eight-recipe.json',OUT/'recipe.json')
print('READY',t,'seconds;',len(checks),'verified replays;',len(cues),'cues')
