# -*- coding: utf-8 -*-
from pathlib import Path
import json,sys,shutil,gzip
R=Path('/Users/lyu/Documents/ChatGPT/金铲铲');A=R/'exports/frontline-episode-01-rerun-v5';O=R/'exports/frontline-rammus-video-v9';O.mkdir(exist_ok=True);(O/'source').mkdir(exist_ok=True)
sys.path.insert(0,str(A));import archive as a
rows=json.loads((R/'exports/frontline-rammus-recomputed-v9/ranking.json').read_text());byid={r['id']:r for r in rows}
spec=[([5,24,27],4),([5,24,27],0),([5,24,24],0),([16,16,23],0),([24,27,33],0),([26,30,33],0),([5,27,30],4),([5,27,33],0)]
main=[next(r for r in rows if r['items']==sorted(i)and r['augment']==h)for i,h in spec]
labels={5:'饮血',16:'大天使',17:'冕卫',22:'冰甲',23:'头盔',24:'振奋',26:'反甲',27:'板甲',29:'坚定',30:'龙牙',33:'狂徒'}
keys={5:'bloodthirster',16:'archangels_staff',17:'crownguard',22:'2023',23:'adaptivehelm',24:'spirit_visage',26:'2054',27:'gargoyle_stoneplate',29:'nightharvester',30:'2031',33:'warmogs_armor'}
def equip(r):return [dict(label=labels[i],iconKey='item/'+keys[i])for i in r['items']]
def augments(r):return [dict(label='单身板甲',iconKey='augment/soloplate2')]if r['augment']==4 else[]
rep=dict(schemaVersion=1,id='rammus-revised-v9',title='三星龙龟 · 普通配装压测',conditions='6护卫 · 5人集火 · 33%重伤 · 双抗各降30% · 物魔各半',footnote='固定条件模拟 · 每档满血30秒 · 每50加压至首败',source=str(R/'exports/frontline-rammus-recomputed-v9/manifest.json'),isFixture=False,coverKey='cover/rammus-revised-v9',cards=[],runs=[],segments=[],captions=[])
for i,r in enumerate(main):
 r['label']=chr(65+i);rep['cards'].append(dict(id=r['id'],label=r['label'],soloLabel=r['label']+'组龙龟',heroName='龙龟',portraitKey='hero/rammus',quality='3费 · 3星',traits='6护卫',augment=r['augmentName'],augmentIconKey='augment/soloplate2'if r['augment']==4 else'',equipment=equip(r)))

for card in rep['cards']:
 compact=[]
 for item in card['equipment']:
  existing=next((e for e in compact if e['iconKey']==item['iconKey']),None)
  if existing:existing['label']=item['label']+'×2'
  else:compact.append(dict(item))
 card['equipment']=compact

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
  samples=[dict(time=f[0]/30,hp=f[1],maxHp=f[2],shield=f[3],alive=bool(f[17]),hasArmor=True,hasMagicResist=True,hasAbilityPower=True,armor=z[1],magicResist=z[2],abilityPower=z[3])for f,z in zip(x['frames'],x['presentation']['frames'])]
  events=[dict(id=f'e{i}',time=e[0]/30,kind=e[1],amount=e[2],source=e[3])for i,e in enumerate(x['presentation']['events'])if e[1]in['damage','heal','shieldGain','shieldBreak','death']]
  v=dict(id=f'{r["id"]}-{d}',cardId=r['id'],samples=samples,events=events);cache[r['id'],d]=v;rep['runs'].append(v);checks.append(dict(id=r['id'],dps=d,alive=x['result']['alive']))
def tracks(d,hold=False,initial=False):
 out=[]
 for r in main:
  used=min(d,r['failedDps']);v=cache[r['id'],used];frozen=hold or initial or d>r['failedDps'];ft=0 if initial else v['samples'][-1]['time']if frozen else 0
  out.append(dict(cardId=r['id'],runId=v['id'],frozen=frozen,frozenTime=ft,aliveLabel='准备压测'if initial else'30秒通过'if hold else'承压中',deadLabel='淘汰',resultLabel=''))
 return out
# Reuse the shared segment constructor from the current production template.
template=(R/'research/episode-two-video-20260926/prepare.py').read_text();code=template[template.index('cues=[];chapters=[];facts=[];deaths=[];t=0'):template.index("add('cover'")].replace("'蔚继续加压'","'龙龟继续加压'").replace("'8位前排'","'8套代表配装'")
exec(code)
add('cover','cover','intro',8,startDps,tracks(startDps,initial=True),'重构模拟算法、修正问题后，重新看龙龟的八千四百套配装。')
add('rules','eight','intro',10,startDps,tracks(startDps,initial=True),'三星六护卫，八套代表配置。每档满血三十秒，过关再加五十。海克斯看卡片。')
chapters.append(dict(start=t,title='八套代表配装逐档压测'))
for d in range(startDps,endDps+1,50):
 active=[r for r in main if r['failedDps']>=d];dead=[r for r in active if r['failedDps']==d];solo=len(active)==1;focus=active[0]['id']if solo else None;layout='solo'if solo else'eight'
 dur=7.5 if dead or d in[startDps,endDps-50]else 2.5
 records=[dict(dps=x,status='current'if x==d else'pass')for x in range(max(startDps,d-450),d+1,50)]if solo else[]
 s=add(f'B{d}',layout,'battle',dur,d,tracks(d),focus=focus,records=records,best=d-50 if solo else None)
 for r in dead:deaths.append(s['start']+cache[r['id'],d]['samples'][-1]['time']/30*dur)
 text=None;hold=.25
 if d==startDps:text='五百五十档，八套全部通过。继续加压。';hold=5
 elif d==600:text='六百档，双大天使加头盔先淘汰。';hold=5
 elif d==900:text='九百档，反甲、龙牙、狂徒没撑满三十秒。';hold=5.5
 elif d==1000:text='一千档，饮血、板甲、狂徒没通过。';hold=5
 elif d==1050:text='一千零五十，两套无海克斯的板甲组合淘汰。';hold=5.5
 elif d==1250:text='一千二百五，带单身板甲的饮血龙牙组合淘汰。';hold=6
 elif d==1300:text='一千三百，饮血双振奋没通过，只剩A组继续。';hold=6
 elif d==1350:text='一千三百五十，A组撑满三十秒。再加五十。';hold=5.5
 elif d==1400:text='一千四百没通过。A组最高通过一千三百五十档。';hold=6
 records=[dict(dps=x,status='fail'if x==d and dead else'pass')for x in range(max(startDps,d-450),d+1,50)]if solo else[]
 add(f'H{d}',layout,'hold',hold,d,tracks(d,True),text,focus,records,d-50 if dead and solo else d if solo else None)
 if text:facts.append(dict(cue=f'H{d}',currentDps=d,failed=[r['label']for r in dead],passed=[r['label']for r in active if r not in dead],coarseBest=max(r['passedDps']for r in main)))
# First eight global results, then sixty-four distinct representative results.
selected=rows[:8].copy();seen={r['id']for r in selected}
old=json.loads((R/'exports/frontline-rammus-eight-v1/production-v8/replay.json').read_text())
for r in main+[byid[e['id']]for e in old['results']['entries']]:
 if r['id']not in seen and len(selected)<72:selected.append(r);seen.add(r['id'])
for r in rows:
 if len(selected)==72:break
 if r['id']not in seen and all(i in labels for i in r['items']):selected.append(r);seen.add(r['id'])
selected=selected[:8]+sorted(selected[8:],key=lambda r:(-r['refinedDps'],r['id']));assert len(selected)==72 and all(r['id']in seen for r in main)
mainids={r['id']:r['label']for r in main}
entries=[dict(id=r['id'],rank=r['rank'],passedDps=r['refinedDps'],isTop=r['rank']==1,episodeTag=mainids.get(r['id'],''),equipment=equip(r),augments=augments(r))for r in selected]
pageTitles=['总榜前8套']+[f'特征配置 {i*8-7}—{i*8} / 64'for i in range(1,9)]
rep['results']=dict(title='三星龙龟 · 8400套配装总榜',subtitle='前8＋64套特征配置 · 显示全量名次',portraitKey='hero/rammus',conditions='三星 / 6护卫 / 海克斯见每行\n5人集火 / 33%重伤 / 双抗各降30% / 物魔各半',footnote='末区间每1细分至首败 · 同分并列 · A—H为出镜组',barScaleDps=1400,pageSizes=[8]*9,pageSubtitles=pageTitles,entries=entries)
chapters.append(dict(start=t,title='8400套与总榜排序规则'));scopeStart=t
add('scope','scope','intro',12,text='片尾列总榜前八，再选六十四套。名次来自全部八千四百套。最后区间每次加一，字母标记刚才的出镜组。')
fields={'Headline':'<size=44>三星龙龟 · 六护卫</size>\n<size=64>8,400 套参与排名</size>','BaseCombinations/SectionTitle':'普通配装','BaseCombinations/Explanation0':'三件普通装备','BaseCombinations/Explanation1':'包含合法重复装备','BaseCombinations/Count':'7770','BaseCombinations/Unit':'套','BaseCombinations/Formula':'按组合计数，不区分顺序','AugmentCombinations/SectionTitle':'海克斯分支','AugmentCombinations/Explanation0':'包含板甲的组合','AugmentCombinations/Explanation1':'搭配单身板甲','AugmentCombinations/Explanation2':'不纳入心之钢','AugmentCombinations/Count':'630','AugmentCombinations/Unit':'套','AugmentCombinations/Formula':'含多板甲的合法组合','Plus':'+','Total':'<size=68>共 8,400 套</size>','CountingNote':'每50加压至首败，最后区间每1细分','CombinationDefinition':'榜首8套＋64套特征配置','CombinationOrder':'每档满血30秒','GlobalRank':'显示全量名次','RankingRule':'成绩相同，保留并列','AugmentLabel':'A—H为Main出镜组'}
rep['scopeTextOverrides']=[dict(path='SafeArea/'+k,text=v)for k,v in fields.items()]
resultsStart=t
for i,title in enumerate(pageTitles):
 text='第一页，总榜前八套。A组细分成绩一千三百五十五。'if i==0 else f'第{i+1}页，更多配装。左侧保留全量排名。'if i==1 else f'第{i+1}页，继续看常见配装的成绩。'if i<8 else'最后一页，双大天使也在里面。按自己的装备查找。'
 s=add(f'P{i+1:02}','results','result',6,text=text);s['resultPage']=i+1;chapters.append(dict(start=s['start'],title=title))
rep['duration']=t
for n,obj in [('replay-unvoiced.json',rep),('cues.json',cues),('semantic-facts.json',facts),('selection.json',dict(main=main,results=selected)),('replay-verification.json',dict(passed=True,runs=len(checks),checks=checks)),('timeline-base.json',dict(duration=t,chapters=chapters,scopeStart=scopeStart,resultsStart=resultsStart,deathAnchors=deaths))]:(O/n).write_text(json.dumps(obj,ensure_ascii=False,separators=(',',':')))
recipe=json.loads((R/'exports/frontline-episode-02-video-v1/recipe.json').read_text());recipe.update(id='rammus-revised-v9',duration=t,sourceArchive='frontline-rammus-recomputed-v9',displayPoolConfigurations=8400);(O/'recipe.json').write_text(json.dumps(recipe,ensure_ascii=False,indent=2))
shutil.copytree(R/'exports/frontline-episode-02-video-v1/assets/tts',O/'assets/tts',dirs_exist_ok=True)
print('READY',t,'seconds',len(checks),'replays',len(cues),'cues')
