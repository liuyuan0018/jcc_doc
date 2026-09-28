# -*- coding: utf-8 -*-
from pathlib import Path
import json,sys,gzip,shutil,collections
R=Path('/Users/lyu/Documents/ChatGPT/金铲铲');A=R/'exports/frontline-episode-01-rerun-v5';O=R/'exports/frontline-vi-eight-v2';O.mkdir(exist_ok=True);(O/'source').mkdir(exist_ok=True)
assert Path('/Volumes/Apple').is_mount()
sys.path.insert(0,str(A));import archive as a
rows=[]
for sn in [147,148,149]:
 with gzip.open(A/'raw'/f'scenario-{sn}.summary.jsonl.gz','rt') as f:
  rows.extend(a.description(json.loads(line)) for line in f if '"augment":1,' not in line)
rows.sort(key=lambda r:(-r['passedDps'],r['scenario'],r['items'],r['augment']))
counts=collections.Counter(r['passedDps']for r in rows);ranks={};n=1
for score in sorted(counts,reverse=True):ranks[score]=n;n+=counts[score]
for r in rows:r['rank']=ranks[r['passedDps']]
spec=[[5,27,27],[9,11,27],[9,27,33],[11,27,33],[5,27,33],[5,24,27],[16,27,27],[5,9,27]]
main=[next(r for r in rows if r['scenario']==149 and r['items']==items and r['augment']==4)for items in spec]
labels={5:'饮血',9:'羊刀',11:'泰坦',16:'大天使',17:'冕卫',22:'冰甲',23:'头盔',24:'振奋',26:'反甲',27:'板甲',29:'坚定',30:'龙牙',33:'狂徒'}
keys={5:'bloodthirster',9:'rageblade',11:'titans_resolve',16:'archangels_staff',17:'crownguard',22:'2023',23:'adaptivehelm',24:'spirit_visage',26:'2054',27:'gargoyle_stoneplate',29:'nightharvester',30:'2031',33:'warmogs_armor'}
def equip(r):return [dict(label=labels[i],iconKey='item/'+keys[i])for i in r['items']]
def augments(r):return [dict(label='单身板甲',iconKey='augment/soloplate2')]if r['augment']==4 else[]
rep=dict(schemaVersion=1,id='vi-eight-revised-v2',title='三星蔚 · 普通配装压测',conditions='Main：6主宰 · 单身板甲 · 5人集火 · 33%重伤 · 双抗各降30%',footnote='固定条件模拟 · 每档满血30秒 · 每50加压至首败',source=str(A/'manifest.json'),isFixture=False,coverKey='cover/vi-eight',cards=[],runs=[],segments=[],captions=[])
for i,r in enumerate(main):
 r['label']=chr(65+i);rep['cards'].append(dict(id=r['id'],label=r['label'],soloLabel=r['label']+'组蔚',heroName='蔚',portraitKey='hero/vi',quality='3费 · 3星',traits='6主宰 · 6人口',augment=r['augmentName'],augmentIconKey='augment/soloplate2',equipment=equip(r)))
cache={};checks=[];startDps=min(r['passedDps']for r in main);endDps=max(r['failedDps']for r in main)
for r in main:
 for d in range(startDps,r['failedDps']+1,50):
  path=O/'source'/f'{r["id"]}-{d}.json.gz'
  if path.exists():
   with gzip.open(path,'rt')as f:x=json.load(f)
  else:
   x=a.replay(r['id'],d)
   with gzip.open(path,'wt')as f:json.dump(x,f,separators=(',',':'))
  a.validate_replay(x)
  assert x['result']['alive']==(d<=r['passedDps'])
  samples=[dict(time=f[0]/30,hp=f[1],maxHp=f[2],shield=f[3],alive=bool(f[17]),hasArmor=True,hasMagicResist=True,hasAbilityPower=True,armor=z[1],magicResist=z[2],abilityPower=z[3])for f,z in zip(x['frames'],x['presentation']['frames'])]
  events=[dict(id=f'e{i}',time=e[0]/30,kind=e[1],amount=e[2],source=e[3])for i,e in enumerate(x['presentation']['events'])if e[1]in['damage','heal','shieldGain','shieldBreak','death']]
  v=dict(id=f'{r["id"]}-{d}',cardId=r['id'],samples=samples,events=events);cache[r['id'],d]=v;rep['runs'].append(v);checks.append(dict(id=r['id'],dps=d,alive=x['result']['alive']))
def tracks(d,hold=False,initial=False):
 out=[]
 for r in main:
  used=min(d,r['failedDps']);v=cache[r['id'],used];frozen=hold or initial or d>r['failedDps'];ft=0 if initial else v['samples'][-1]['time']if frozen else 0
  out.append(dict(cardId=r['id'],runId=v['id'],frozen=frozen,frozenTime=ft,aliveLabel='准备压测'if initial else'30秒通过'if hold else'承压中',deadLabel='淘汰',resultLabel=''))
 return out
s=(R/'research/episode-two-video-20260926/prepare.py').read_text();exec(s[s.index('cues=[];chapters=[];facts=[];deaths=[];t=0'):s.index("add('cover'")].replace("'8位前排'","'8套代表配装'"))
add('cover','cover','intro',7,startDps,tracks(startDps,initial=True),'蔚的八套出装，你常用哪套？这次补上完整配装池的排名。')
add('rules','eight','intro',10,startDps,tracks(startDps,initial=True),'主画面统一三星六主宰，带单身板甲。每档满血三十秒，过关再加五十。')
chapters.append(dict(start=t,title='八套代表配置逐档压测'))
texts={1850:'一千八百五，八套全部通过。',1900:'一千九百档，羊刀泰坦和泰坦狂徒都没过。',2000:'两千档，羊刀狂徒没撑满三十秒。',2050:'两千零五十档，羊刀饮血也倒了。',2100:'两千一百档，饮血狂徒和饮血振奋都没过，最高通过两千零五十。',2150:'两千一百五，大天使双板没过。饮血双板继续加压。',2200:'两千二百档，饮血双板撑满三十秒。',2250:'两千二百五没过。饮血双板最高通过两千二百。'}
for d in range(startDps,endDps+1,50):
 active=[r for r in main if r['failedDps']>=d];dead=[r for r in active if r['failedDps']==d];solo=len(active)==1;focus=active[0]['id']if solo else None;layout='solo'if solo else'eight'
 duration=7 if dead or solo else 3
 rec=[dict(dps=x,status='current'if x==d else'pass')for x in range(2150,d+1,50)]if solo else[]
 segment=add(f'B{d}',layout,'battle',duration,d,tracks(d),focus=focus,records=rec,best=d-50 if solo else None)
 for r in dead:deaths.append(segment['start']+cache[r['id'],d]['samples'][-1]['time']/30*duration)
 hold=8 if d==2100 else 6.5 if d in [2150,2250]else 5 if d in texts else .3
 rec=[dict(dps=x,status='fail'if x==d and dead else'pass')for x in range(2150,d+1,50)]if solo else[]
 add(f'H{d}',layout,'hold',hold,d,tracks(d,True),texts.get(d),focus,rec,d-50 if dead and solo else d if solo else None)
 if d in texts:facts.append(dict(cue=f'H{d}',dps=d,failed=[r['id']for r in dead],passed=[r['id']for r in active if r not in dead],field='failedDps'if dead else'passedDps'))
selected=rows[:8].copy();ids={r['id']for r in selected}
def include(r):
 if r['id']not in ids:selected.append(r);ids.add(r['id'])
for r in main:include(r)
# Keep practical defensive/attack-speed contrasts, lower traits, and no-augment branches.
for sn in [149,148,147]:
 for aug in [0,4]:
  for item in [5,9,11,16,24,26,27,30,33]:
   candidate=next((r for r in rows if r['scenario']==sn and r['augment']==aug and item in r['items']and all(i in labels for i in r['items'])),None)
   if candidate:include(candidate)
for r in rows:
 if len(selected)>=72:break
 if all(i in labels for i in r['items']):include(r)
assert len(selected)==72
selected.sort(key=lambda r:(r['rank'],r['scenario'],r['items'],r['augment']))
mainids={r['id']:r['label']for r in main};entries=[]
for r in selected:
 entries.append(dict(id=r['id'],episodeTag=mainids.get(r['id'],''),rank=r['rank'],passedDps=r['passedDps'],isTop=r['rank']==1,equipment=equip(r),augments=augments(r),detailRichText='3星蔚 · '+ ' / '.join(f'{v}{k}'for k,v in r['traits'].items())+f' · {r["slots"]}人口'))
pageTitles=['第1页 · 总榜前8套']+[f'第{i+1}页 · 特征配装 · 保留全量名次'for i in range(1,9)]
rep['results']=dict(title='蔚 · 普通配装成绩',subtitle='25,200套参与排名 · 展示72套',portraitKey='hero/vi',conditions='3星蔚 · 羁绊/海克斯逐行标注\n5人集火 / 33%重伤 / 双抗各降30% / 物魔各半',footnote='每50加压至首败 · 最高通过来伤/秒 · 同分并列',barScaleDps=2250,pageSizes=[8]*9,pageSubtitles=pageTitles,entries=entries)
scopeStart=t;chapters.append(dict(start=t,title='25200套与总榜排序规则'))
add('scope','scope','intro',12,text='总榜算了两万五千二百套，包含二四六主宰和海克斯分支。先看前八，再看六十四套精选。字母是刚才的出镜组。')
fields={'Headline':'<size=44>三星蔚 · 普通三件套</size>\n<size=64>25,200 套参与排名</size>','BaseCombinations/SectionTitle':'普通配装','BaseCombinations/Explanation0':'三件普通装备','BaseCombinations/Explanation1':'含合法重复装备','BaseCombinations/Count':'7770','BaseCombinations/Unit':'套','BaseCombinations/Formula':'不区分装备顺序','AugmentCombinations/SectionTitle':'单身板甲分支','AugmentCombinations/Explanation0':'含普通板甲的组合','AugmentCombinations/Explanation1':'独占一排时生效','AugmentCombinations/Explanation2':'不纳入心之钢','AugmentCombinations/Count':'630','AugmentCombinations/Unit':'套','AugmentCombinations/Formula':'每个羁绊档位分别计算','Plus':'+','Total':'<size=58>8,400 × 3 = 25,200 套</size>','CountingNote':'2 / 4 / 6主宰 · 每50加压至首败','CombinationDefinition':'榜首8套＋64套特征配置','CombinationOrder':'每档满血30秒','GlobalRank':'显示全量名次','RankingRule':'成绩相同，保留并列','AugmentLabel':'A—H为Main出镜组'}
rep['scopeTextOverrides']=[dict(path='SafeArea/'+k,text=v)for k,v in fields.items()]
resultsStart=t
for i,title in enumerate(pageTitles):
 text='第一页，总榜前八。大天使双板也在这里。'if i==0 else f'第{i+1}页，更多配装。注意每行的羁绊和海克斯。'if i<8 else'最后一页。按自己的装备找配置，名次来自完整配装池。'
 seg=add(f'P{i+1:02}','results','result',6,text=text);seg['resultPage']=i+1;chapters.append(dict(start=seg['start'],title=title))
rep['duration']=t
for n,obj in [('replay-unvoiced.json',rep),('cues.json',cues),('semantic-facts.json',facts),('selection.json',dict(main=main,results=selected,poolCount=len(rows))),('replay-verification.json',dict(passed=True,runs=len(checks),checks=checks)),('timeline-base.json',dict(duration=t,chapters=chapters,scopeStart=scopeStart,resultsStart=resultsStart,deathAnchors=deaths))]:(O/n).write_text(json.dumps(obj,ensure_ascii=False,separators=(',',':')))
recipe=json.loads((R/'exports/frontline-rammus-video-v9/recipe.json').read_text());recipe.update(id='vi-eight-revised-v2',duration=t,sourceArchive=A.name,mainCount=8,resultsCount=72,displayPoolConfigurations=len(rows));(O/'recipe.json').write_text(json.dumps(recipe,ensure_ascii=False,indent=2))
shutil.copy2(R/'exports/frontline-vi-eight-source-v1/cover/cover-9x16-v2.png',O/'cover-video.png');shutil.copy2(R/'exports/frontline-vi-eight-source-v1/cover/cover-3x4-v1.png',O/'cover-approved.png')
print('READY',t,'seconds',len(checks),'verified replays',len(cues),'cues',len(selected),'results')
