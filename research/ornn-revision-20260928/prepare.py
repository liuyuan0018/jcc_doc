from pathlib import Path
import json,sys,shutil,gzip,subprocess,collections
R=Path('/Users/lyu/Documents/ChatGPT/金铲铲');A=R/'exports/frontline-episode-01-rerun-v5';D=R/'exports/ornn-recomputed-20260928';sys.path.insert(0,str(A));import archive as a
labels={5:'饮血',9:'羊刀',16:'大天使',17:'冕卫',20:'法爆',22:'冰甲',23:'头盔',24:'振奋',25:'正义',26:'反甲',27:'板甲',29:'坚定',30:'龙牙',33:'狂徒'}
keys={5:'bloodthirster',9:'rageblade',16:'archangels_staff',17:'crownguard',20:'2038',22:'2023',23:'adaptivehelm',24:'spirit_visage',25:'2039',26:'2054',27:'gargoyle_stoneplate',29:'nightharvester',30:'2031',33:'warmogs_armor'}
def equip(r):return [dict(label=labels[i],iconKey='item/'+keys[i])for i in r['items']]
def augments(r):return [dict(label='单身板甲',iconKey='augment/soloplate2')]if r['augment']==4 else[]
def produce(tier,sc):
 O=R/f'exports/ornn-{tier}warden-video-20260928';O.mkdir(exist_ok=True);(O/'source').mkdir(exist_ok=True)
 rows=json.loads((D/f's{sc}-ranking.json').read_text());best=rows[0];no=next(r for r in rows if r['augment']==0)
 spec=[(best['items'],4),(best['items'],0),(no['items'],0),([5,16,25],0),([24,27,33],0),([26,30,33],0),([5,27,30],4),([5,27,33],0)]
 main=[next(r for r in rows if r['items']==sorted(i)and r['augment']==h)for i,h in spec];assert len({r['id']for r in main})==8
 rep=dict(schemaVersion=1,id=f'ornn-{tier}warden-v2',title=f'三星奥恩 · {tier}护卫普通配装压测',conditions=f'{tier}护卫 · 5人集火 · 33%重伤 · 双抗各降30% · 物魔各半',footnote='固定条件模拟 · 每档满血30秒 · 每50加压至首败',source=str(D/'manifest.json'),isFixture=False,coverKey=f'cover/ornn-{tier}warden-v2',cards=[],runs=[],segments=[],captions=[])
 for i,r in enumerate(main):
  r['label']=chr(65+i);es=[]
  for e in equip(r):
   old=next((x for x in es if x['iconKey']==e['iconKey']),None)
   if old:old['label']=e['label']+'×'+str(r['items'].count(next(k for k in r['items']if labels[k]==e['label'])))
   else:es.append(dict(e))
  rep['cards'].append(dict(id=r['id'],label=r['label'],soloLabel=r['label']+'组奥恩',heroName='奥恩',portraitKey='hero/ornn',quality='1费 · 3星',traits=f'{tier}护卫',augment=r['augmentName'],augmentIconKey='augment/soloplate2'if r['augment']==4 else'',equipment=es))
 cache={};checks=[];startDps=min(r['passedDps']for r in main);endDps=max(r['failedDps']for r in main)
 for r in main:
  for d in range(startDps,r['failedDps']+1,50):
   p=O/'source'/f'{r["id"]}-{d}.json.gz'
   if p.exists():x=json.load(gzip.open(p,'rt'))
   else:
    x=json.loads(subprocess.check_output([str(D/'input/replay-native'),*map(str,a.parameters(r,d))],text=True));a.validate_replay(x)
    with gzip.open(p,'wt')as f:json.dump(x,f,separators=(',',':'))
   stage=next(z for z in r['stages']if z[0]==d);assert x['result']['alive']==bool(stage[1]) and x['result']['frame']==stage[2]
   samples=[dict(time=f[0]/30,hp=f[1],maxHp=f[2],shield=f[3],alive=bool(f[17]),hasArmor=True,hasMagicResist=True,hasAbilityPower=True,armor=z[1],magicResist=z[2],abilityPower=z[3])for f,z in zip(x['frames'],x['presentation']['frames'])]
   events=[dict(id=f'e{i}',time=e[0]/30,kind=e[1],amount=e[2],source=e[3])for i,e in enumerate(x['presentation']['events'])if e[1]in['damage','heal','shieldGain','shieldBreak','death']]
   v=dict(id=f'{r["id"]}-{d}',cardId=r['id'],samples=samples,events=events);cache[r['id'],d]=v;rep['runs'].append(v);checks.append(dict(id=r['id'],dps=d,alive=x['result']['alive']))
 def tracks(d,hold=False,initial=False):
  out=[]
  for r in main:
   used=min(d,r['failedDps']);v=cache[r['id'],used];frozen=hold or initial or d>r['failedDps'];ft=0 if initial else v['samples'][-1]['time']if frozen else 0
   out.append(dict(cardId=r['id'],runId=v['id'],frozen=frozen,frozenTime=ft,aliveLabel='准备压测'if initial else'30秒通过'if hold else'承压中',deadLabel='淘汰',resultLabel=''))
  return out
 cues=[];chapters=[];facts=[];deaths=[];t=0
 def add(key,layout,phase,duration,dps=0,tr=None,text=None,focus=None,records=None,best=None):
  nonlocal t
  start=t;t=round((t+duration)*30)/30
  s=dict(id=key,start=start,end=t,layout=layout,phase=phase,dps=dps,roundSeconds=30,simFrom=30 if phase=='hold'else 0,simTo=30 if phase in['battle','hold']else 0,tracks=tr or[],records=records or[],tierLabel='逐档加压'if phase=='battle'else'暂停查看',headerStatus='奥恩继续加压'if layout=='solo'else'8套代表配装',hasPageTurnSeconds=True,pageTurnSeconds=.35,hasCoverSlideSeconds=True,coverSlideSeconds=.5)
  if focus:s['focusCardId']=focus
  if best is not None:s.update(hasBestPassed=True,bestPassed=best)
  rep['segments'].append(s)
  if text:cues.append(dict(id=key,text=text,spoken=text,windowStart=start,windowEnd=t,start=start+.5))
  return s
 add('cover','cover','intro',8,startDps,tracks(startDps,initial=True),f'三星奥恩，{tier}护卫。重构模拟算法后，重新测八千四百套普通配装。')
 add('rules','eight','intro',10,startDps,tracks(startDps,initial=True),'八套代表一起比，每档满血三十秒。海克斯看卡片，心之钢不计入。')
 chapters.append(dict(start=t,title='八套代表逐档压测'))
 for d in range(startDps,endDps+1,50):
  active=[r for r in main if r['failedDps']>=d];dead=[r for r in active if r['failedDps']==d];solo=len(active)==1;focus=active[0]['id']if solo else None;layout='solo'if solo else'eight';dur=7.5 if dead or d in[startDps,endDps-50]else 2.5
  records=[dict(dps=x,status='current'if x==d else'pass')for x in range(startDps,d+1,50)]if solo else[]
  s=add(f'B{d}',layout,'battle',dur,d,tracks(d),focus=focus,records=records,best=d-50 if solo else None)
  for r in dead:deaths.append(s['start']+cache[r['id'],d]['samples'][-1]['time']/30*dur)
  text=None;hold=.25
  if d==startDps:text=f'{d}档，八套全部通过。继续加压。';hold=5
  elif d==endDps:text=f'{d}档，最后一组没通过。最高通过{d-50}档。';hold=7
  elif dead:text=f'{d}档，'+ '、'.join(r['label']+'组'for r in dead)+'没撑满三十秒。';hold=6 if len(dead)<3 else 8
  elif d==endDps-50:text=f'{d}档通过，再加五十。';hold=5
  records=[dict(dps=x,status='fail'if x==d and dead else'pass')for x in range(startDps,d+1,50)]if solo else[]
  add(f'H{d}',layout,'hold',hold,d,tracks(d,True),text,focus,records,d-50 if dead and solo else d if solo else None)
  if text:facts.append(dict(cue=f'H{d}',currentDps=d,failed=[r['label']for r in dead],passed=[r['label']for r in active if r not in dead],coarseBest=max(r['passedDps']for r in main)))
 selected=rows[:8].copy();seen={r['id']for r in selected}
 def take(r):
  if r['id']not in seen and len(selected)<72 and all(i in labels for i in r['items']):selected.append(r);seen.add(r['id'])
 for r in main:take(r)
 for item in labels:
  for aug in [0,4]:
   for r in [r for r in rows if item in r['items']and r['augment']==aug][:3]:take(r)
 for r in rows:take(r)
 selected=selected[:8]+sorted(selected[8:],key=lambda r:(-r['score'],r['id']));assert len(selected)==72;mainids={r['id']:r['label']for r in main}
 entries=[dict(id=r['id'],rank=r['rank'],passedDps=r['score'],isTop=r['rank']==1,episodeTag=mainids.get(r['id'],''),equipment=equip(r),augments=augments(r))for r in selected]
 titles=['总榜前8套']+[f'特征配置 {i*8-7}—{i*8} / 64'for i in range(1,9)]
 rep['results']=dict(title=f'三星奥恩 · {tier}护卫 · 8400套总榜',subtitle='前8＋64套特征配置 · 全量名次',portraitKey='hero/ornn',conditions=f'三星 / {tier}护卫 / 海克斯见每行\n5人集火 / 33%重伤 / 双抗各降30% / 物魔各半',footnote='末区间每1细分至首败 · 同分并列 · A—H为出镜组',barScaleDps=endDps,pageSizes=[8]*9,pageSubtitles=titles,entries=entries)
 scope=t;chapters.append(dict(start=t,title='8400套与总榜排序规则'))
 add('scope','scope','intro',12,text='先列总榜前八，再选六十四套。名次来自全部八千四百套，最后区间每次加一。字母对应出镜组。')
 template=json.loads((R/'exports/frontline-rammus-video-v9/replay.json').read_text());rep['scopeTextOverrides']=[dict(x,text=x['text'].replace('三星龙龟 · 六护卫',f'三星奥恩 · {tier}护卫'))for x in template['scopeTextOverrides']]
 resultStart=t
 for i,title in enumerate(titles):
  text=f'第一页，总榜前八。榜首细分成绩{best["score"]}。'if i==0 else f'第{i+1}页，常见配装，保留全量名次。'if i<8 else'最后一页。字母对应刚才出场的配装。'
  s=add(f'P{i+1:02}','results','result',6,text=text);s['resultPage']=i+1;chapters.append(dict(start=s['start'],title=title))
 rep['duration']=t
 for n,x in [('replay-unvoiced.json',rep),('cues.json',cues),('semantic-facts.json',facts),('selection.json',dict(main=main,results=selected)),('replay-verification.json',dict(passed=True,runs=len(checks),checks=checks)),('timeline-base.json',dict(duration=t,chapters=chapters,scopeStart=scope,resultsStart=resultStart,deathAnchors=deaths))]:(O/n).write_text(json.dumps(x,ensure_ascii=False,separators=(',',':')))
 recipe=json.loads((R/'exports/frontline-rammus-video-v9/recipe.json').read_text());recipe.update(id=rep['id'],duration=t,sourceArchive=str(D),resultsCount=72);(O/'recipe.json').write_text(json.dumps(recipe,ensure_ascii=False,indent=2));shutil.copytree(R/'exports/frontline-rammus-video-v9/assets/tts',O/'assets/tts',dirs_exist_ok=True)
 print('READY',tier,t,len(checks),[(r['label'],r['items'],r['augment'],r['score'])for r in main],flush=True)
for tier,sc in [(2,6),(6,8)]:produce(tier,sc)
