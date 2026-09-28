"""Historical v3 highest-pass preparer. Current production uses revise.py with pause-window-profile.json and progression ranking."""
import asyncio,importlib.util,json,math,shutil,hashlib
from pathlib import Path
ROOT=Path('/Users/lyu/Documents/ChatGPT/金铲铲');HERE=Path(__file__).parent.resolve();OLD=ROOT/'exports/frontline-rammus-eight-v1/production-v1';OUT=ROOT/'exports/frontline-rammus-eight-v1/production-v3';OUT.mkdir(exist_ok=True)
spec=importlib.util.spec_from_file_location('voices',ROOT/'research/rammus-eight-20260924/make_appendix_voice.py');voices=importlib.util.module_from_spec(spec);spec.loader.exec_module(voices);voices.OUT=OUT/'assets/tts';audio=voices.audio
recipe=json.loads((ROOT/'exports/frontline-rammus-eight-v1/rammus-eight-recipe.json').read_text())
texts={
'V16':'下面看补测后的配装成绩。',
'S01':'这次一共比较了八千三百六十五种配装方案。',
'S02':'同一套装备，有无单身板甲分开算。',
'S03':'我们选了六十四套，按补测后的最高通过来伤排序。',
'P01':'第一页，先看这八套。',
'P02':'第二页，第九到十六套。',
'P03':'第三页，第十七到二十四套。',
'P04':'第四页，第二十五到三十二套。',
'P05':'第五页，第三十三到四十套。',
'P06':'第六页，第四十一到四十八套。',
'P07':'第七页，第四十九到五十六套。',
'P08':'最后一页，第五十七到六十四套，可以暂停查看。'}
async def main():
 sem=asyncio.Semaphore(3)
 async def one(key,text):
  async with sem:
   result=await voices.make_one(dict(id=key,spoken=text),recipe['tts'],recipe['voiceProcessing']);print(key,result['seconds'],flush=True);return key,result
 clips=dict(await asyncio.gather(*(one(k,v) for k,v in texts.items())))
 (OUT/'tts-manifest.json').write_text(json.dumps(clips,ensure_ascii=False,indent=2))
 base=json.loads((ROOT/'research/rammus-eight-20260924/rammus-eight-unity-base.json').read_text());oldTimeline=json.loads((OLD/'timeline.json').read_text())
 # Keep the already fitted captions/conditions used in the existing full Unity input.
 full=json.loads((Path('/Users/lyu/Documents/project/game/projects/jcc/client/Assets/Res/Replay/rammus-eight-results-v1.json')).read_text())
 base['captions']=[c for c in full['captions'] if c['start']<131.6];base['footnote']='固定条件模拟 · 每50来伤逐档演示 · 完整补测见片尾'
 events=[c for c in oldTimeline['cues'] if c['id']!='V16']
 def roundFrame(s):return math.ceil(s*30)/30
 def addCue(key,start):
  length=clips[key]['seconds'];end=start+length
  text=texts[key];display=text
  if len(text)>26:
   # Only scope uses these longer lines; its full-width footer can wrap.
   at=next((i+1 for i,c in enumerate(text) if c=='，' and i>8),len(text)//2);display=text[:at]+'\n'+text[at:]
  events.append(dict(id=key,text=text,spoken=text,start=start,actualEnd=end,end=end+.25))
  base['captions'].append(dict(start=start,end=end+.25,text=display));return end
 bridgeEnd=addCue('V16',131.63333333333333);scopeStart=roundFrame(bridgeEnd+.8);base['segments'][-1]['end']=scopeStart
 def segment(key,layout,start,end,**kw):return dict(id=key,layout=layout,phase='intro' if layout=='scope' else 'result',start=start,end=end,roundSeconds=30,dps=0,simFrom=0,simTo=0,tracks=[],records=[],hasPageTurnSeconds=True,pageTurnSeconds=0,**kw)
 t=scopeStart+.3
 for key in ['S01','S02','S03']:t=addCue(key,t)+.5
 scopeEnd=roundFrame(t+.6);base['segments'].append(segment('scope-8365','scope',scopeStart,scopeEnd))
 rankings=json.loads((ROOT/'research/rammus-rank-integer-20260925/replay.json').read_text());base['results']=rankings['results']
 t=scopeEnd;chapters=[dict(start=0,title='八套逐档压测'),dict(start=scopeStart,title='8365种方案怎么比较')]
 for i in range(8):
  key=f'P{i+1:02}';endCue=addCue(key,t+.3);end=roundFrame(max(t+6,endCue+.9));base['segments'].append(segment(f'results-{i+1}','results',t,end,resultPage=i+1));chapters.append(dict(start=t,title=f'配装第{i+1}页 · {i*8+1}—{i*8+8}套'));t=end
 base.update(duration=t,id='rammus-full-results64-v3',source=rankings['source']+'; original 8-build coarse demonstration retained; mixed full timeline')
 # Timeline statements must end before their associated scope/results page ends.
 for event in events:
  if event['id'].startswith(('P','S')):
   s=next(s for s in base['segments'] if s['start']<=event['start']<s['end']);assert event['actualEnd']+.3<=s['end']
 assert all(base['segments'][i]['end']==base['segments'][i+1]['start'] for i in range(len(base['segments'])-1))
 (OUT/'replay.json').write_text(json.dumps(base,ensure_ascii=False,separators=(',',':')))
 timeline=dict(duration=t,events=events,chapters=chapters,scopeStart=scopeStart,resultsStart=scopeEnd,fps=30)
 (OUT/'timeline.json').write_text(json.dumps(timeline,ensure_ascii=False,indent=2))
 def timecode(t):
  ms=round(t*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000);return f'{h:02}:{m:02}:{s:02},{ms:03}'
 (OUT/'subtitles.srt').write_text('\n\n'.join(f'{i+1}\n{timecode(c["start"])} --> {timecode(c["end"])}\n{c["text"]}' for i,c in enumerate(base['captions']))+'\n')
 (OUT/'chapters.txt').write_text('\n'.join(f'{int(c["start"]//60):02}:{int(c["start"]%60):02} {c["title"]}' for c in chapters)+'\n')
 # Reuse the prior voice stem through the authorized replacement boundary.
 samples=round(t*audio.SR);voice=audio.pcm(OLD/'voice-processed.wav',2);del voice[round(131.6*audio.SR)*2:];voice.extend([0.]*(samples*2-len(voice)))
 for event in events:
  if event['id'] not in clips:continue
  values=audio.pcm(voices.OUT/(event['id']+'.wav'),1);offset=round(event['start']*audio.SR)*2
  for i,v in enumerate(values):voice[offset+2*i]+=v*audio.PAN;voice[offset+2*i+1]+=v*audio.PAN
 audio.wav24(OUT/'voice-processed.wav',voice)
 music=recipe['music'];musicPath=ROOT/music['path'];assert audio.sha(musicPath)==music['sha256'];gain=music['gains']['wallpaperV2RecipeGainDb']+music['gains']['approvedV5AddDb']
 filters=f'atrim=start=0:end={t+1:.3f},asetpts=PTS-STARTPTS,highpass=f=45:p=2,equalizer=f=2200:t=o:w=2:g=-4,volume={gain:.8f}dB'
 mix=audio.pcm(musicPath,2,filters);assert len(mix)>=samples*2;del mix[samples*2:]
 for i in range(samples):
  seconds=i/audio.SR;factor=1.
  if seconds<music['fadeInSeconds']:factor=.5-.5*math.cos(math.pi*seconds/music['fadeInSeconds'])
  elif seconds>t-music['fadeOutSeconds']:factor=.5-.5*math.cos(math.pi*(t-seconds)/music['fadeOutSeconds'])
  mix[i*2]*=factor;mix[i*2+1]*=factor
 audio.wav24(OUT/'music-bed.wav',mix)
 effects=audio.pcm(OLD/'elimination-effects.wav',2)
 for i,v in enumerate(voice):mix[i]+=v
 for i,v in enumerate(effects):
  if i<len(mix):mix[i]+=v
 peak=max(map(abs,mix));assert peak<1,peak;audio.wav24(OUT/'mix-master.wav',mix)
 shutil.copyfile(OLD/'CREDITS.txt',OUT/'CREDITS.txt')
 report=dict(duration=t,sampleRate=audio.SR,peakLinear=peak,replaySha256=audio.sha(OUT/'replay.json'),mixSha256=audio.sha(OUT/'mix-master.wav'),reusedVoiceBefore=131.6,voiceSourceSha256=audio.sha(OLD/'voice-processed.wav'),newCues=list(clips),continuousTimeline=True)
 (OUT/'preparation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False),flush=True)
asyncio.run(main())
