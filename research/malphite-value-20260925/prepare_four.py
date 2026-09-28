import json,subprocess,csv,collections,copy,argparse,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'exports/frontline-malphite-rerun-v1';
p=argparse.ArgumentParser();p.add_argument('--selection',type=Path);p.add_argument('--out',type=Path);p.add_argument('--revisions',type=Path);p.add_argument('--episode-id',default='malphite-eight-v3');args=p.parse_args()
OUT=args.out.resolve() if args.out else BASE/'production-v2';OUT.mkdir(exist_ok=True);(OUT/'source').mkdir(exist_ok=True)
old=json.loads((ROOT/'exports/frontline-malphite-v1/production-v1/replay.json').read_text());manifest=json.loads((BASE/'manifest.json').read_text());main=json.loads((BASE/'best30.json').read_text());conditions={(p['sacrifice']['blackthorn'],p['sacrifice']['sacrificeCost'],p['sacrifice']['sacrificeStar']):p['sacrifice']for p in manifest['parts']}
representative=args.selection is not None
if representative:
 plan=json.loads(args.selection.read_text());main=plan['main']
 wanted={x['id'] for x in main};raw={}
 for path in (BASE/'raw').glob('*.jsonl'):
  for line in path.open():
   x=json.loads(line)
   if x['id'] in wanted:raw[x['id']]=x
 for x in main:x.update(raw[x['id']])
mainCount=len(main);groupCount=math.ceil(mainCount/8);resultCount=mainCount+64;pageCount=math.ceil(resultCount/8)

labels={5:'饮血',16:'大天使',17:'冕卫',22:'冰甲',23:'头盔',24:'振奋',26:'反甲',27:'板甲',29:'坚定',30:'龙牙',33:'狂徒'};keys={5:'bloodthirster',16:'archangels_staff',17:'crownguard',22:'2023',23:'adaptivehelm',24:'spirit_visage',26:'2054',27:'gargoyle_stoneplate',29:'nightharvester',30:'2031',33:'warmogs_armor'}
def equipment(r):return [dict(iconKey='item/'+keys[i],label=labels[i])for i in r['items']]
def num(n):
 digits='零一二三四五六七八九';s='';zero=False
 for power,unit in [(1000,'千'),(100,'百'),(10,'十'),(1,'')]:
  v,n=divmod(n,power)
  if v:s+=('零'if zero else'')+digits[v]+unit;zero=False
  elif s and n:zero=True
 return (s[1:]if s.startswith('一十')else s)or'零'
def run(row,dps):
 path=OUT/'source'/f'{row["key"]}-{dps}.json'
 if not path.exists():
  e=conditions[row['tier'],row['cost'],row['star']];args=[row['id'],*row['items'],row['augment'],e['hp'],e['hpp'],e['armor'],0,dps]
  result=subprocess.check_output([str(BASE/'input/simulate'),'replay'],input=(' '.join(map(str,args))+'\n').encode());path.write_bytes(result)
 o=json.loads(path.read_text());stage=next(x for x in row['stages']if x[0]==dps);assert o['result']['alive']==bool(stage[1])and o['result']['frame']==stage[2]
 return dict(id=f'{row["key"]}-{dps}',cardId=row['key'],events=[dict(id=f'e{i}',time=e[0]/30,kind=e[1],amount=e[2],source=e[3])for i,e in enumerate(o['events'])if e[1]in ['damage','heal','shieldGain','shieldBreak','death']],samples=[dict(time=f[0]/30,hp=f[1],maxHp=f[2],shield=f[3],alive=bool(f[17]),hasArmor=True,hasMagicResist=True,hasAbilityPower=True,armor=a[1],magicResist=a[2],abilityPower=a[3])for f,a in zip(o['frames'],o['attributes'])])
r={k:copy.deepcopy(old[k])for k in ['schemaVersion','conditions','isFixture']};r.update(id=args.episode_id if representative else 'malphite-four-v2',title='石头人 · 八套代表配置' if representative else '石头人 · 30种献祭条件',source=str(BASE/'manifest.json'),footnote='固定条件模型 · 每档满血重开30秒 · 每50来伤加压',coverKey='cover/malphite-eight-v3' if representative else 'cover/malphite-four-v2',cards=[],runs=[],segments=[],captions=[])
for i,row in enumerate(main):
 row['key']=f'M{i+1:02}';row['label']=f'{i+1:02}';row['conditionRank']=1+sum(x['score']>row['score']for x in main)
 r['cards'].append(dict(id=row['key'],label=f'{row["label"]} · {row["tier"]}黑' if representative else f'{row["label"]} · {row["tier"]}黑',soloLabel=f'{row["label"]} 石头人' if representative else '',heroName='石头人',portraitKey='hero/malphite',quality='墨菲特 · 4费 · 2星',traits=f'{row["tier"]}黑 · 献祭{row["cost"]}费{row["star"]}星',augment='单身板甲'if row['augment']else'无',augmentIconKey='augment/soloplate2'if row['augment']else'',equipment=equipment(row)))
t=0;cues=[];chapters=[];deathAnchors=[];facts=[]
def add(key,layout,phase,seconds,dps=0,tracks=None,text=None,group=1,focus=None,records=None,best=None):
 global t
 start=t;t=round((t+seconds)*30)/30;s=dict(id=key,start=start,end=t,layout=layout,phase=phase,dps=dps,roundSeconds=30,simFrom=30 if phase=='hold'else 0,simTo=30 if phase in ['battle','hold']else 0,tracks=tracks or[],records=records or[],tierLabel='逐档加压'if phase=='battle'else'暂停查看',headerStatus='八套同场压测' if representative else f'第{group}幕 / {groupCount}',hasPageTurnSeconds=True,pageTurnSeconds=.35,hasCoverSlideSeconds=True,coverSlideSeconds=.5)
 if focus:s['focusCardId']=focus
 if best is not None:s.update(hasBestPassed=True,bestPassed=best)
 r['segments'].append(s)
 if text:cues.append(dict(id=key,text=text,spoken=text,windowStart=start,windowEnd=t,start=start+.25))
 return s
for gi in range(groupCount):
 group=main[gi*8:(gi+1)*8];first=min(x['failedDps']for x in group)-50;last=max(x['failedDps']for x in group);cache={}
 for row in group:
  for d in range(first,row['failedDps']+1,50):
   v=run(row,d);cache[row['key'],d]=v;r['runs'].append(v)
 def tracks(d,hold=False,intro=False):
  result=[]
  for row in group:
   used=min(d,row['failedDps']);v=cache[row['key'],used];frozen=intro or hold or d>row['failedDps'];ft=0 if intro else v['samples'][-1]['time']if frozen else 0
   result.append(dict(cardId=row['key'],runId=v['id'],frozen=frozen,frozenTime=ft,aliveLabel='准备开始'if intro else'30秒通过'if hold else'承压中',deadLabel='淘汰',resultLabel=''))
  return result
 if gi==0:
  add('cover','cover','intro',5.5,first,tracks(first,True,True),'八套石头人，谁能扛到最后？' if representative else '石头人的羁绊和献祭，搭配什么装备？')
  add('selection-rule','eight','intro',10,first,tracks(first,True,True),'今天选八套代表配置同场压测。羁绊、献祭、装备和海克斯，都在卡片上。' if representative else '三十种条件，各选当前模型下成绩最高的配装，包含单身板甲。分四幕，按细分成绩降序展示。')
  add('battle-rule','eight','intro',7,first,tracks(first,True,True),'每档满血重开，撑满三十秒再加压。卡片编号用于查找，海克斯看每套。')
 chapters.append(dict(start=t,title='八套同场压测' if representative else f'第{gi+1}幕 · 配置{gi*8+1}—{gi*8+len(group)}'))
 txt=['第一幕，一到八号。羁绊和献祭条件看每张卡。','第二幕，九到十六号。继续比较各条件的配装。','第三幕，十七到二十四号。规则和前两幕相同。','第四幕，最后六套。这里只呈现固定条件下的压测结果。'][gi]
 if not representative:add(f'G{gi+1}-intro','eight','intro',6.5,first,tracks(first,True,True),txt,gi+1)
 for d in range(first,last+1,50):
  active=[x for x in group if x['failedDps']>=d];dead=[x for x in active if x['failedDps']==d];solo=len(active)==1;focus=active[0]['key']if solo else None
  rec=[dict(dps=x,status='current'if x==d else'pass')for x in range(max(first,d-450),d+1,50)]if solo else[]
  s=add(f'G{gi+1}-{d}-battle','solo'if solo else'eight','battle',4 if dead or solo else 1.5,d,tracks(d),group=gi+1,focus=focus,records=rec,best=d-50 if solo and d>first else None)
  for x in dead:
   v=cache[x['key'],d];death=next((e['time']for e in v['events']if e['kind']=='death'),v['samples'][-1]['time']);deathAnchors.append(s['start']+death/30*(s['end']-s['start']))
  text=None;hold=.5
  if dead:
   names='、'.join(num(int(x['label']))+'号'for x in dead);text=f'{num(d)}档，{names}没撑住。';hold=5.5 if len(dead)>2 else 4.5
   if d==last:text=f'{num(d)}档没通过。本轮最高通过{num(d-50)}档。';hold=6.5
   facts.append(dict(cue=f'G{gi+1}-{d}',kind='failure',dps=d,cardIds=[x['key']for x in dead],highestPassed=d-50 if d==last else None))
  elif d==first:text=f'{num(d)}档，八套全部通过。';hold=4.5
  rec=[dict(dps=x,status='fail'if x==d and dead else'pass')for x in range(max(first,d-450),d+1,50)]if solo else[]
  add(f'G{gi+1}-{d}','solo'if solo else'eight','hold',hold,d,tracks(d,True),text,gi+1,focus,rec,d-50 if dead and solo else d if solo else None)
# Select 30 Main plus 64 extra unique configurations, including all global top eight.
allrows=[]
for z in csv.DictReader((BASE/'full-ranking.csv').open()):
 allrows.append(dict(id=z['id'],rank=int(z['rank']),score=int(z['score']),tier=int(z['blackthorn']),cost=int(z['sacrificeCost']),star=int(z['sacrificeStar']),items=[int(z[k])for k in ['item1','item2','item3']],augment=int(z['augment'])))
lookup={x['id']:x for x in allrows};selected={x['id']:lookup[x['id']]for x in main}
if representative:
 for x in json.loads((BASE/'best30.json').read_text()):selected.setdefault(x['id'],lookup[x['id']])
for x in allrows[:8]:selected.setdefault(x['id'],x)
meat={17,22,23,24,26,27,29,30,33};seen=set()
for x in allrows:
 condition=(x['tier'],x['cost'],x['star'],x['augment'])
 if len(selected)<resultCount and condition not in seen and all(i in meat for i in x['items']):
  seen.add(condition);selected.setdefault(x['id'],x)
for x in json.loads((ROOT/'exports/frontline-malphite-v1/ranking.json').read_text())['selected']:
 if len(selected)>=resultCount:break
 selected.setdefault(x['id'],lookup[x['id']])
for x in allrows:
 if len(selected)>=resultCount:break
 if all(i in meat for i in x['items']):selected.setdefault(x['id'],x)
if representative and plan.get('resultsIds'):
 selected={key:lookup[key]for key in plan['resultsIds']}
 assert len(selected)==len(plan['resultsIds']), 'Duplicate result IDs'
 assert {x['id']for x in main}<=set(selected)
assert len(selected)==resultCount,len(selected);selected=sorted(selected.values(),key=lambda x:(-x['score'],x['id']));mainids={x['id']:x['label']for x in main}
entries=[dict(id=x['id'],episodeTag=mainids.get(x['id'],''),rank=x['rank'],passedDps=x['score'],isTop=x['rank']==1,equipment=equipment(x),augments=[dict(label='单身板甲',iconKey='augment/soloplate2')]if x['augment']else[],detailRichText=f'<b>{x["tier"]}黑荆棘</b> · 献祭{x["cost"]}费{x["star"]}星坦克')for x in selected]
r['results']=dict(title='石头人 · 羁绊与献祭',subtitle=f'250,950组计算 · 精选{resultCount}套',portraitKey='hero/malphite',conditions='两星石头人 · 羁绊、献祭与海克斯逐行标注\n5人集火 / 33%重伤 / 双抗各降30% / 物魔各半 / 无控制',footnote='固定条件模型 · 同分并列 · 出镜编号对应前段',barScaleDps=2200,pageSizes=[min(8,resultCount-i*8) for i in range(pageCount)],pageSubtitles=[f'精选 {i*8+1}—{min(resultCount,i*8+8)} / {resultCount} · 真实总榜名次'for i in range(pageCount)],entries=entries)
scopeStart=t;chapters.append(dict(start=t,title='计算范围与总榜规则'))
add('scope','scope','intro',14,text=f'二十五万零九百五十套参与排名。前面演示{num(mainCount)}套，片尾精选{num(resultCount)}套。按细分成绩排序，同分并列。')
r['scopeTextOverrides']=copy.deepcopy(old['scopeTextOverrides'])
for field in r['scopeTextOverrides']:
 k=field['path'].split('/')[-1]
 if k=='Headline':field['text']='<size=41>2 / 4 / 6黑荆棘 × 10种坦克献祭</size>\n<size=58>比较 250,950 种配置</size>'
 if k=='CombinationDefinition':field['text']=f'前段演示{mainCount}套 · 片尾精选{resultCount}套'
 if k=='CombinationOrder':field['text']='八套代表同场压测 · 装备及海克斯见卡片' if representative else '各条件选模型最高成绩 · 装备及海克斯见卡片'
 if k=='AugmentLabel':field['text']='条件逐行标明'
 if k=='Footer':field['text']='固定条件模型结果，不代表所有实战情境'
resultsStart=t
for i in range(pageCount):
 text='第一页，先看总榜前八套。' if i==0 else f'第{num(i+1)}页，出镜编号对应前面八套。' if i==3 else f'第{num(i+1)}页，羁绊和献祭条件看每行。' if i<pageCount-1 else '最后一页，以上是本轮固定条件的模拟成绩。'
 s=add(f'P{i+1:02}','results','result',6.5,text=text);s['resultPage']=i+1;chapters.append(dict(start=s['start'],title=f'总榜精选第{i+1}页 · {i*8+1}—{min(resultCount,i*8+8)}'))

r['duration']=t
revisions=json.loads((args.revisions or Path(__file__).with_name('narration-revisions-v3.json' if representative else 'narration-revisions-v2.json')).read_text())
for cue in cues:cue.update(revisions.get(cue['id'],{}))
recipeSource=json.loads((ROOT/'exports/frontline-malphite-v1/production-v1/recipe.json').read_text())
recipe={k:recipeSource[k] for k in ['tts','voiceProcessing','music']}
recipe.update(id=r['id'],version=3 if representative else 2,outputDir=str(OUT),replayData='replay.json',coverPath='cover-9x16.png',timeline='timeline.json',cues='cues.json',semanticFacts='semantic-facts.json',sourceDir=str(BASE),selection=str(args.selection) if args.selection else 'best30.json',capture=dict(route='Unity media-capture',fps=30,continuousTake=True,audioMaster='mix-master.wav'))
for name,obj in [('replay-unvoiced.json',r),('cues.json',cues),('semantic-facts.json',facts),('timeline-base.json',dict(duration=t,chapters=chapters,scopeStart=scopeStart,resultsStart=resultsStart,deathAnchors=deathAnchors)),('main-selection.json',main),('results-selection.json',selected),('recipe.json',recipe)]: (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,separators=(',',':')))
print('READY',t,'seconds',len(r['runs']),'runs',len(cues),'cues',flush=True)
