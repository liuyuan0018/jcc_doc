import json,sys,subprocess,hashlib,copy,importlib.util,asyncio,math,shutil,argparse
from pathlib import Path
from array import array
ROOT=Path('/Users/lyu/Documents/ChatGPT/金铲铲');HERE=Path(__file__).parent;OUT=ROOT/'exports/frontline-fiddlesticks-v1/production-v2';ARC=ROOT/'exports/frontline-episode-01-rerun-v3';SRC=ROOT/'research/vi-vow-topic-20260923/vow-shield-revision-v1/input';JCC=Path('/Users/lyu/Documents/project/game/projects/jcc/client')
ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,default=OUT);ap.add_argument('--results-plan',type=Path);ap.add_argument('--reuse',type=Path);args=ap.parse_args();OUT=args.out.resolve();OUT.mkdir(parents=True,exist_ok=True)
plan=json.loads(args.results_plan.read_text()) if args.results_plan else None
if args.reuse:
 for part in ['assets/tts','source']:
  shutil.copytree(args.reuse/part,OUT/part,dirs_exist_ok=True)
sys.path.insert(0,str(ARC));import archive
spec=importlib.util.spec_from_file_location('voices',ROOT/'research/rammus-eight-20260924/make_appendix_voice.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v);v.OUT=OUT/'assets/tts';a=v.audio
spec=importlib.util.spec_from_file_location('convert',JCC/'ArtSource/GUI/ReplayDevelopment/import_legacy_replay.py');conv=importlib.util.module_from_spec(spec);spec.loader.exec_module(conv)
data=json.loads((HERE/'ranking.json').read_text());recipe=json.loads((ROOT/'exports/frontline-rammus-eight-v1/rammus-eight-recipe.json').read_text());base=json.loads((ROOT/'exports/frontline-rammus-eight-v1/production-v5/replay.json').read_text())
labels={5:'饮血',16:'大天使',17:'冕卫',22:'冰甲',23:'头盔',24:'振奋',26:'反甲',27:'板甲',29:'坚定',30:'龙牙',33:'狂徒'}
keys={5:'bloodthirster',16:'archangels_staff',17:'crownguard',22:'2023',23:'adaptivehelm',24:'spirit_visage',26:'2054',27:'gargoyle_stoneplate',29:'nightharvester',30:'2031',33:'warmogs_armor'}
# Pause budgets are authored before requesting speech; generation never stretches them.
windows=[('cover',3.2,'草人八套配装，谁更能扛？'),('intro',5.3,'三星六护卫，海克斯看每套。每档撑三十秒。'),('700',2.5,'七百，全部通过。'),('750',3.25,'反甲龙牙狂徒，停在七百。'),('800',.5,None),('850',2.5,'剩下七套都过了。'),('900',3.25,'振奋板甲狂徒，停在八百五。'),('950',4.25,'双振奋和大天使这两套，停在九百。'),('1000',4.5,'单身板甲狂徒和饮血板甲，停在九百五。'),('1050',3.75,'饮血大天使振奋，停在一千。'),('1100',2.75,'一千一，单身板甲通过。'),('1150',4.25,'一千一百五没过，这套停在一千一。'),('summary',6.5,'片尾六十四套，按细分成绩排序，海克斯逐行标明。')]
page_text=['第一页，先看靠前的回血组合。','第二页，继续看饮血和振奋搭配。','第三页，比较肉装和海克斯。','第四页，看看同装备的不同条件。','第五页，更多常规肉装对照。','第六页，继续比较不同肉装。','第七页，按装备查找需要的组合。','最后八套，暂停查看。']
# Navigation does not assert individual contents; generic wording where rows mix types.
page_text=['第一页，先看排名靠前的组合。','第二页，继续看配装成绩。','第三页，海克斯也要一起看。','第四页，看看你常用的装备。','第五页，更多常规肉装对照。','第六页，继续比较不同肉装。','第七页，按装备查找需要的组合。','最后八套，暂停查看。']
profile=dict(windows=[dict(id=k,seconds=s,text=t) for k,s,t in windows],pageSeconds=6,speechTailSeconds=.35,cueOffset=.25,pageCues=page_text)
if plan:
 if plan.get('removeSummary'):windows=[w for w in windows if w[0]!='summary']
 windows=[(key,seconds,plan.get('narrationOverrides',{}).get(key,text)) for key,seconds,text in windows]
 page_text=plan['pageCues']
 profile.update(windows=[dict(id=k,seconds=s,text=t) for k,s,t in windows],pageCues=page_text)
(OUT/'pause-window-profile.json').write_text(json.dumps(profile,ensure_ascii=False,indent=2))
async def main():
 clips={};sem=asyncio.Semaphore(3)
 async def one(k,text):
  async with sem:
   clip=await v.make_one(dict(id=k,spoken=text),recipe['tts'],recipe['voiceProcessing']);clips[k]=clip;print('voice',k,round(clip['seconds'],3),flush=True)
 await asyncio.gather(*(one(k,t) for k,s,t in windows if t),*(one(f'P{i+1:02}',t) for i,t in enumerate(page_text)))
 for k,s,text in windows:
  if text:assert .25+clips[k]['seconds']+.35<=s,(k,clips[k]['seconds'],s)
 for i in range(len(page_text)):assert .3+clips[f'P{i+1:02}']['seconds']+.35<=6
 print('All fixed budgets passed',flush=True)
 source=dict(hero=dict(name='费德提克',star=3,cost=3,traits={'护卫':6},slots=6,scenario=158),aug=0,augLabel='无指定海克斯',environment=data['environment'],builds=[])
 replaydir=OUT/'source';replaydir.mkdir(parents=True,exist_ok=True)
 for row in data['main']:
  chain=[]
  for dps in range(700,row['failedDps']+1,50):
   cache=replaydir/f"{row['key']}-{dps}.json"
   if cache.exists():run=json.loads(cache.read_text())
   else:
    run=json.loads(subprocess.check_output([str(SRC/'replay-native'),*map(str,archive.parameters(row,dps))]));archive.validate_replay(run);cache.write_text(json.dumps(run,separators=(',',':')))
   old=next(s for s in row['stages'] if s['dps']==dps)['result'];assert all(math.isclose(val,run['result'][k],rel_tol=1e-9,abs_tol=1e-7) for k,val in old.items()),(row['key'],dps)
   run.update(dps=dps);run['frames']=[[f[i] for i in [0,1,2,3,4,17]] for f in run['frames']];chain.append(run)
  source['builds'].append(dict(key=row['key'],label='·'.join(labels[i] for i in row['items']),items=row['items'],itemNames=[archive.ITEMS[i]['name'] for i in row['items']],augLabel={0:'无指定海克斯',1:'心之钢',4:'单身板甲'}[row['augment']],passedDps=row['passedDps'],failedDps=row['failedDps'],chain=chain))
 recipe['castDefaults'].update(hero='草人',avatar='tank-lab/dist/assets/s18_head_fiddlesticks.png',_traitText='6护卫 · 6人口')
 recipe['ui'].update(conditions='三星草人 · 6护卫 · 5人集火 / 33%重伤 / 双抗各降30% / 物魔各半',heroName='草人')
 tiers=[dict(dps=d,layout='solo' if d>=1100 else 'eight') for d in range(700,1151,50)]
 recipe['program']=dict(tiers=tiers,focusCardId='E');timeline=dict(simFps=30,segments=[],cues=[],events=[]);t=0;events=[];budget=[]
 def segment(kind,seconds,key=None,tier=None):
  nonlocal t
  start=t;t=round((t+seconds)*30)/30
  s=dict(kind=kind,start=start,end=t)
  if tier is not None:s['tier']=tier
  timeline['segments'].append(s)
  if key and key in clips:
   end=start+.25+clips[key]['seconds'];text=next(text for k,_,text in windows if k==key)
   events.append(dict(id=key,text=text,spoken=text,start=start+.25,actualEnd=end,end=end+.18));timeline['cues'].append(dict(start=start+.25,end=end+.18,lines=[text]));budget.append(dict(id=key,windowStart=start,windowEnd=t,speechEnd=end,tail=t-end));assert end+.35<=t
 for key,seconds,text in windows[:2]:segment(key,seconds,key)
 for i,tier in enumerate(tiers):
  seconds=1.5 if tier['dps']==800 else 5 if tier['dps']>=1100 else 3.75
  segment('battle',seconds,tier=i)
  for b in source['builds']:
   if b['failedDps']==tier['dps']:
    run=b['chain'][-1];timeline['events'].append(dict(tier=i,build=b['key'],at=timeline['segments'][-1]['start']+run['result']['frame']/900*seconds))
  key=str(tier['dps']);segment('hold',next(s for k,s,_ in windows if k==key),key,i)
 if not plan or not plan.get('removeSummary'):segment('result',6.5,'summary',len(tiers)-1)
 timeline['duration']=t
 profile_conv=dict(id='fiddlesticks-eight-augments-v2',title='草人 · 八套配装模拟对照',coverKey='cover/fiddlesticks-v1',portraitKeys={'费德提克':'hero/fiddlesticks'},items={archive.ITEMS[i]['name']:[key,labels[i]] for i,key in keys.items()})
 replay=conv.convert(source,timeline,recipe,profile_conv)
 if plan:replay['id']=plan['id']
 for card,row in zip(replay['cards'],data['main']):
  card['heroName']='草人'
  if row['augment']:card['augmentIconKey']='augment/'+{1:'heartsteel',4:'soloplate2'}[row['augment']]
 replay['footnote']='固定条件模拟 · 每50来伤逐档加压 · 细分成绩见片尾'
 # Results begin only after Main resolves; real global ranks, not renumbered selected rows.
 entries=[dict(id=r['id'],rank=r['rank'],passedDps=r['score'],isTop=r['rank']==1,episodeTag='',equipment=[dict(label=labels[i],iconKey='item/'+keys[i]) for i in r['items']],augments=[dict(label={1:'心之钢',4:'单身板甲'}[r['augment']],iconKey='augment/'+{1:'heartsteel',4:'soloplate2'}[r['augment']])] if r['augment'] else []) for r in data['selected']]
 assert len(entries)==64
 replay['results']=dict(title='草人，怎么配更能扛？',subtitle='8365种方案中，精选64套对比',portraitKey='hero/fiddlesticks',barScaleDps=max(r['score'] for r in data['all'])+50,conditions='三星草人 · 6护卫 · 海克斯见每行配置\n5人集火 / 33%重伤 / 双抗各降30% / 物魔各半 / 无控制',footnote='固定条件模拟 · 逐档加压至首次失败 · 最后两档间细分',pageSizes=[8]*8,entries=entries)
 if plan:
  main_ids={r['id']:r['key'] for r in data['main']}
  entries=[dict(id=r['id'],rank=r['rank'],passedDps=r['score'],isTop=r['rank']==1,episodeTag=main_ids.get(r['id'],''),equipment=[dict(label=labels[i],iconKey='item/'+keys[i]) for i in r['items']],augments=[dict(label='单身板甲',iconKey='augment/soloplate2')] if r['augment']==4 else []) for r in plan['entries']]
  replay['results'].update(entries=entries,subtitle=plan['subtitle'],pageSubtitles=plan['pageSubtitles'],pageSizes=[8]*len(page_text),footnote='固定条件模拟 · 首败停止后细分 · 出镜A—H对应前段八组')
  assert len(entries)==len(page_text)*8
 results_start=t;chapters=[dict(start=0,title='草人八套逐档压测')]
 for i,text in enumerate(page_text):
  key=f'P{i+1:02}';start=t;t+=6;end=start+.3+clips[key]['seconds'];events.append(dict(id=key,text=text,spoken=text,start=start+.3,actualEnd=end,end=end+.18));replay['captions'].append(dict(start=start+.3,end=end+.18,text=text));replay['segments'].append(dict(id=f'results-{i+1}',layout='results',phase='result',start=start,end=t,roundSeconds=30,dps=0,simFrom=0,simTo=0,tracks=[],records=[],hasPageTurnSeconds=True,pageTurnSeconds=0,resultPage=i+1));budget.append(dict(id=key,windowStart=start,windowEnd=t,speechEnd=end,tail=t-end));chapters.append(dict(start=start,title=f'配装第{i+1}页 · {i*8+1}—{i*8+8}套'))
 replay['duration']=t
 if plan:
  for chapter,title in zip(chapters[1:],plan['chapterTitles']):chapter['title']=title
  (OUT/'results-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2))
 # Subtitles wrap only at a natural punctuation point.
 for c in replay['captions']:
  if len(c['text'])>22:
   pos=c['text'].find('，')+1
   if pos:c['text']=c['text'][:pos]+'\n'+c['text'][pos:]
 timeline.update(duration=t,events=events,chapters=chapters,resultsStart=results_start,fps=30)
 for name,value in [('replay.json',replay),('timeline.json',timeline),('pause-budget.json',budget),('tts-manifest.json',clips),('recipe.json',recipe),('source-data.json',source)]:
  (OUT/name).write_text(json.dumps(value,ensure_ascii=False,separators=(',',':')))
 samples=round(t*a.SR);voice=array('f',[0.])*(samples*2)
 for e in events:
  clip=a.pcm(v.OUT/(e['id']+'.wav'),1);offset=round(e['start']*a.SR)*2
  for i,x in enumerate(clip):voice[offset+2*i]+=x*a.PAN;voice[offset+2*i+1]+=x*a.PAN
 a.wav24(OUT/'voice-processed.wav',voice)
 music=recipe['music'];mp=ROOT/music['path'];assert a.sha(mp)==music['sha256'];gain=music['gains']['wallpaperV2RecipeGainDb']+music['gains']['approvedV5AddDb'];mix=a.pcm(mp,2,f'atrim=start=0:end={t+1},asetpts=PTS-STARTPTS,highpass=f=45:p=2,equalizer=f=2200:t=o:w=2:g=-4,volume={gain}dB');del mix[samples*2:]
 for i in range(samples):
  seconds=i/a.SR;factor=1
  if seconds<music['fadeInSeconds']:factor=.5-.5*math.cos(math.pi*seconds/music['fadeInSeconds'])
  elif seconds>t-music['fadeOutSeconds']:factor=.5-.5*math.cos(math.pi*(t-seconds)/music['fadeOutSeconds'])
  mix[2*i]*=factor;mix[2*i+1]*=factor
 a.wav24(OUT/'music-bed.wav',mix)
 # Reuse one established elimination sound, placed at the actual death anchor for each build.
 old=a.pcm(ROOT/'exports/frontline-rammus-eight-v1/production-v5/elimination-effects.wav',2);active=next(i for i,x in enumerate(old) if abs(x)>1e-7);active-=active%2;burst=old[active:active+int(.5*a.SR)*2];fx=array('f',[0.])*(samples*2)
 for b in source['builds']:
  seg=next(s for s in replay['segments'] if s['phase']=='battle' and s['dps']==b['failedDps']);death=b['chain'][-1]['result']['frame']/30;at=seg['start']+(death-seg['simFrom'])/(seg['simTo']-seg['simFrom'])*(seg['end']-seg['start']);off=round(at*a.SR)*2
  for i,x in enumerate(burst):fx[off+i]+=x
 a.wav24(OUT/'elimination-effects.wav',fx)
 for i,x in enumerate(voice):mix[i]+=x+fx[i]
 peak=max(map(abs,mix));assert peak<1; a.wav24(OUT/'mix-master.wav',mix)
 def tc(t):
  ms=round(t*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000);return f'{h:02}:{m:02}:{s:02},{ms:03}'
 (OUT/'subtitles.srt').write_text('\n\n'.join(f'{i+1}\n{tc(c["start"])} --> {tc(c["end"])}\n{c["text"]}' for i,c in enumerate(replay['captions']))+'\n')
 (OUT/'chapters.txt').write_text('\n'.join(f'{int(c["start"]//60):02}:{int(c["start"]%60):02} {c["title"]}' for c in chapters))
 shutil.copyfile(ROOT/'exports/frontline-rammus-eight-v1/production-v5/CREDITS.txt',OUT/'CREDITS.txt')
 for p,h in data['sourceHashes'].items():assert a.sha(Path(p))==h
 (OUT/'timeline-validation.json').write_text(json.dumps(dict(passed=True,duration=t,peak=peak,runs=len(replay['runs']),allSpeechWithinFixedWindows=True,minTail=min(x['tail'] for x in budget),mainCoarseResultsMatch=True,sourceHashes=data['sourceHashes']),indent=2))
 print('READY',t,'seconds',len(replay['runs']),'runs',flush=True)
asyncio.run(main())
