import json,subprocess,copy,hashlib,csv
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent;BASE=ROOT/'exports/frontline-malphite-v1';OUT=BASE/'production-v1';OUT.mkdir(exist_ok=True);(OUT/'source').mkdir(exist_ok=True)
data=json.loads((BASE/'ranking.json').read_text());main=data['main'];labels={5:'饮血',16:'大天使',17:'冕卫',22:'冰甲',23:'头盔',24:'振奋',26:'反甲',27:'板甲',29:'坚定',30:'龙牙',33:'狂徒'};keys={5:'bloodthirster',16:'archangels_staff',17:'crownguard',22:'2023',23:'adaptivehelm',24:'spirit_visage',26:'2054',27:'gargoyle_stoneplate',29:'nightharvester',30:'2031',33:'warmogs_armor'}
# Every selected Results item is known before rendering; do not invent missing asset keys.
assert all(i in keys for r in data['selected'] for i in r['items'])
def equipment(r):return [dict(iconKey='item/'+keys[i],label=labels[i]) for i in r['items']]
def num(n):
 digits='零一二三四五六七八九';s='';lastzero=False
 for power,unit in [(1000,'千'),(100,'百'),(10,'十'),(1,'')]:
  v,n=divmod(n,power)
  if v:
   if lastzero:s+='零'
   s+=digits[v]+unit;lastzero=False
  elif s and n:lastzero=True
 return (s[1:] if s.startswith('一十') else s) or '零'
def run(r,dps):
 path=OUT/'source'/f'{r["key"]}-{dps}.json'
 if path.exists():o=json.loads(path.read_text())
 else:
  e=r['sacrifice'];args=[r['id'],*r['items'],r['augment'],e['hp'],e['hpp'],e['armor'],0,dps]
  o=json.loads(subprocess.check_output([str(BASE/'input/simulate'),'replay'],input=(' '.join(map(str,args))+'\n').encode()));path.write_text(json.dumps(o,separators=(',',':')))
 stage=next(s for s in r['stages']if s[0]==dps);assert o['result']['alive']==bool(stage[1])and o['result']['frame']==stage[2]
 events=[dict(id=f'e{i}',time=e[0]/30,kind=e[1],amount=e[2],source=e[3])for i,e in enumerate(o['events'])if e[1]in ['damage','heal','shieldGain','shieldBreak','death']]
 samples=[dict(time=f[0]/30,hp=f[1],maxHp=f[2],shield=f[3],alive=bool(f[17]),hasArmor=True,hasMagicResist=True,hasAbilityPower=True,armor=a[1],magicResist=a[2],abilityPower=a[3])for f,a in zip(o['frames'],o['attributes'])]
 return dict(id=f'{r["key"]}-{dps}',cardId=r['key'],samples=samples,events=events)
replay=dict(schemaVersion=1,id='malphite-value-v1',title='石头人 · 羁绊与献祭',conditions='两星 · 5人集火 · 33%重伤 · 双抗各降30% · 物魔各半',footnote='固定条件模拟 · 从300起每50加压 · 每档满血重开30秒',source='frontline-malphite-v1/manifest.json; declared hypotheses; user-confirmed shield mana lock',isFixture=False,coverKey='cover/malphite-value-v1',cards=[],runs=[],segments=[],captions=[])
for r in main:replay['cards'].append(dict(id=r['key'],label=r['label'],heroName='石头人',portraitKey='hero/malphite',quality='墨菲特 · 4费 · 2星',traits=f'{r["tier"]}黑 · 献祭{r["cost"]}费{r["star"]}星',augment='单身板甲'if r['augment']else'无',augmentIconKey='augment/soloplate2'if r['augment']else'',equipment=equipment(r)))
cues=[];chapters=[];t=0;deathAnchors=[];facts=[]
def add(key,layout,phase,seconds,dps=0,tracks=None,text=None,tier=2,focus=None,records=None,best=None):
 global t
 start=t;t=round((t+seconds)*30)/30
 s=dict(id=key,start=start,end=t,layout=layout,phase=phase,dps=dps,roundSeconds=30,simFrom=0,simTo=30 if phase=='battle'else 0,tracks=tracks or [],records=records or [],tierLabel=f'{tier}黑荆棘 · '+('逐档加压'if phase=='battle'else'暂停查看'),headerStatus=f'{tier}黑荆棘 · 8套代表',hasPageTurnSeconds=True,pageTurnSeconds=.35,hasCoverSlideSeconds=True,coverSlideSeconds=.5)
 if focus:s['focusCardId']=focus
 if best is not None:s.update(hasBestPassed=True,bestPassed=best)
 replay['segments'].append(s)
 if text:cues.append(dict(id=key,text=text,spoken=text,windowStart=start,windowEnd=t,start=start+.25))
 return s
for tier in [2,4,6]:
 group=[r for r in main if r['tier']==tier];first=min(r['failedDps'] for r in group)-50;last=max(r['failedDps']for r in group);cache={}
 for r in group:
  for d in range(first,r['failedDps']+1,50):
   v=run(r,d);cache[r['key'],d]=v;replay['runs'].append(v)
 def tracks(d,hold=False):
  result=[]
  for r in group:
   used=min(d,r['failedDps']);v=cache[r['key'],used];frozen=hold or d>r['failedDps'];ft=v['samples'][-1]['time']if frozen else 0
   result.append(dict(cardId=r['key'],runId=v['id'],frozen=frozen,frozenTime=ft,aliveLabel='30秒通过'if hold else'承压中',deadLabel='淘汰',resultLabel=''))
  return result
 if tier==2:
  covertracks=tracks(first,True)
  for tr in covertracks:tr['frozenTime']=0
  add('cover','cover','intro',6.5,first,covertracks,'石头人，羁绊开到几档，献祭多少就够用？')
  add('rules','eight','intro',9,first,covertracks,'每档满血重开，撑满三十秒再加压。这里只比较石头人的固定条件坦度。')
 intro=tracks(first,True)
 for tr in intro:tr['frozenTime']=0
 chapters.append(dict(start=t,title=f'{tier}黑荆棘 · 八套代表'))
 introtext={2:'先看两黑荆棘。每套的献祭规模和海克斯，都标在卡片上。',4:'接着看四黑荆棘。沿用相同的八组搭配，比较增加羁绊的收益。',6:'最后看六黑荆棘。继续用相同组别，看看额外投入换来多少坦度。'}[tier]
 add(f'G{tier}-intro','eight','intro',7.5,first,intro,introtext,tier)
 for d in range(first,last+1,50):
  active=[r for r in group if r['failedDps']>=d];dead=[r for r in active if r['failedDps']==d];solo=len(active)==1;focus=active[0]['key']if solo else None
  rec=[dict(dps=x,status='current'if x==d else'pass')for x in range(max(first,d-450),d+1,50)]if solo else []
  duration=4 if dead or solo else 1.5
  s=add(f'G{tier}-{d}-battle','solo'if solo else'eight','battle',duration,d,tracks(d),tier=tier,focus=focus,records=rec,best=d-50 if solo else None)
  for r in dead:
   v=cache[r['key'],d];death=next((e['time']for e in v['events']if e['kind']=='death'),v['samples'][-1]['time']);deathAnchors.append(s['start']+death/30*duration)
  text=None;hold=.5
  if dead:
   names='、'.join(r['label']for r in dead);text=f'{num(d)}档，{names}没撑住。';hold=4.5
   if d==last:text=f'{num(d)}档没通过。这轮最高通过{num(d-50)}档。';hold=6.5
   facts.append(dict(cue=f'G{tier}-{d}',kind='failure',dps=d,cardIds=[r['key']for r in dead],highestPassed=d-50 if d==last else None))
  elif d==first:text=f'{num(d)}档，八套全部通过。';hold=4.5
  rec=[dict(dps=x,status='fail'if x==d and dead else'pass')for x in range(max(first,d-450),d+1,50)]if solo else []
  add(f'G{tier}-{d}','solo'if solo else'eight','hold',hold,d,tracks(d,True),text,tier,focus,rec,d-50 if dead and solo else d if solo else None)
 # Use frozen end states; comparisons refer explicitly to known coarse passes.
 summary={2:'两黑也要看祭品。低费两星和三星，带来的坦度并不一样。',4:'同穿振奋板甲狂徒，两黑献祭一费三星，与四黑献祭一费两星，都通过了九百档。',6:'多开羁绊不等于一定更划算。棋子投入和阵容占位，要分开考虑。'}[tier]
 add(f'G{tier}-compare','eight','hold',10 if tier==4 else 7.5,last,tracks(last,True),summary,tier)
chapters.append(dict(start=t,title='全量计算范围与排序规则'));scopeStart=t
add('scope','scope','intro',14,text='二十五万零九百五十套全部参与排名。前面演示二十四套，片尾精选八十八套。名次来自总榜，同分并列。')
mainids={r['id']:f'{r["tier"]}黑 {r["label"]}'for r in main}
entries=[]
for r in data['selected']:
 entries.append(dict(id=r['id'],episodeTag=mainids.get(r['id'],''),rank=r['rank'],passedDps=r['score'],isTop=r['rank']==1,equipment=equipment(r),augments=[dict(label='单身板甲',iconKey='augment/soloplate2')]if r['augment']else[],detailRichText=f'<b>{r["tier"]}黑荆棘</b> · 献祭{r["cost"]}费{r["star"]}星'))
replay['results']=dict(title='石头人 · 投入与坦度',subtitle='250,950组计算 · 精选88套配置',portraitKey='hero/malphite',conditions='两星石头人 · 羁绊、献祭及海克斯见每行\n5人集火 / 33%重伤 / 双抗各降30% / 物魔各半 / 无控制',footnote='来伤细分成绩排序 · 羁绊与献祭逐行标注 · 同分并列',barScaleDps=max(r['score']for r in data['top'])+50,pageSizes=[8]*11,pageSubtitles=[f'精选配置 {i*8+1}—{i*8+8} / 88 · 标注真实总榜名次'for i in range(11)],entries=entries)
resultsStart=t
for i in range(11):
 text='第一页，先看总榜前八套。'if i==0 else f'第{num(i+1)}页，羁绊和献祭条件看每行。'if i<10 else'最后一页。按自己的装备和祭品，选择合适的投入。'
 s=add(f'P{i+1:02}','results','result',6.5,text=text);s['resultPage']=i+1;chapters.append(dict(start=s['start'],title=f'配置索引第{i+1}页 · {i*8+1}—{i*8+8}'))
replay['duration']=t
fields={'Headline':'<size=41>羁绊、献祭与装备，投入多少就够？</size>\n<size=58>比较 250,950 种配置</size>','BaseCombinations/SectionTitle':'装备与海克斯','BaseCombinations/Explanation0':'7770套普通三件装备','BaseCombinations/Explanation1':'加595套单身板甲配置','BaseCombinations/Count':'8365','BaseCombinations/Formula':'允许重复装备 · 装备顺序不计','AugmentCombinations/SectionTitle':'羁绊与献祭','AugmentCombinations/Explanation0':'2 / 4 / 6黑荆棘','AugmentCombinations/Explanation1':'每档比较10种坦克献祭','AugmentCombinations/Explanation2':'费用与星级逐行标注','AugmentCombinations/Count':'30','AugmentCombinations/Formula':'3档羁绊 × 10档献祭','Plus':'×','Total':'8365 × 30 = 250,950','CountingNote':'相同装备，不同羁绊、献祭或海克斯分别计算','CombinationDefinition':'Main演示24套 · Results精选88套','CombinationOrder':'全量参与评分','GlobalRank':'标出在250,950种配置中\n排第几','RankingRule':'按压测成绩排序，不是综合性价比排名','AugmentLabel':'投入条件单独标注'}
replay['scopeTextOverrides']=[dict(path='SafeArea/'+k,text=v)for k,v in fields.items()]
for name,obj in [('replay-unvoiced.json',replay),('cues.json',cues),('semantic-facts.json',facts),('timeline-base.json',dict(duration=t,chapters=chapters,scopeStart=scopeStart,resultsStart=resultsStart,deathAnchors=deathAnchors)),('recipe.json',json.load(open(ROOT/'exports/frontline-rammus-eight-v1/rammus-eight-recipe.json')))]: (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,separators=(',',':')))
print('episode',t,'seconds;',len(replay['runs']),'runs;',len(cues),'voice cues')
