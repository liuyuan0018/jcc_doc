"""Reuse approved packages; insert an existing narrated scope window without resimulation/TTS."""
import json, shutil, copy, importlib.util
from pathlib import Path
import numpy as np
ROOT=Path('/Users/lyu/Documents/ChatGPT/金铲铲')
spec=importlib.util.spec_from_file_location('audio',ROOT/'scripts/tank-video/audio_helpers.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
R=ROOT/'exports/frontline-rammus-eight-v1/production-v7';F=ROOT/'exports/frontline-fiddlesticks-v1/production-v4'
RO=R.parent/'production-v8';FO=F.parent/'production-v5'
files=['replay.json','timeline.json','subtitles.srt','chapters.txt','tts-manifest.json','pause-budget.json','pause-window-profile.json','semantic-review.md','Results-72.csv','CREDITS.txt','voice-processed.wav','elimination-effects.wav','music-bed.wav','mix-master.wav']
for src,out in [(R,RO),(F,FO)]:
 out.mkdir(exist_ok=False)
 for n in files:
  if (src/n).exists():shutil.copy2(src/n,out/n)
 shutil.copytree(src/'assets',out/'assets')
rt=json.load(open(R/'timeline.json'));r=json.load(open(R/'replay.json'));f=json.load(open(F/'replay.json'));ft=json.load(open(F/'timeline.json'));old=copy.deepcopy(f)
scope=next(s for s in r['segments'] if s['layout']=='scope');start=ft['resultsStart'];delta=scope['end']-scope['start'];duration=f['duration']+delta
for s in f['segments']:
 if s['start']>=start:
  s['start']+=delta;s['end']+=delta
new=copy.deepcopy(scope);new.update(start=start,end=start+delta)
f['segments'].append(new);f['segments'].sort(key=lambda x:x['start'])
for c in f['captions']:
 if c['start']>=start:c['start']+=delta;c['end']+=delta
for e in ft['events']:
 if e['start']>=start:
  for k in ['start','actualEnd','end']:e[k]+=delta
for e in rt['events']:
 if e['id'].startswith('S'):
  n=copy.deepcopy(e)
  for k in ['start','actualEnd','end']:n[k]+=start-scope['start']
  ft['events'].append(n)
for c in r['captions']:
 if scope['start']<=c['start']<scope['end']:
  n=copy.deepcopy(c);n['start']+=start-scope['start'];n['end']+=start-scope['start'];f['captions'].append(n)
f['captions'].sort(key=lambda x:x['start']);ft['events'].sort(key=lambda x:x['start'])
f.update(duration=duration,id='fiddlesticks-results72-safearea-v5',coverKey='cover/fiddlesticks-total-v5')
f['source']+='; v5 presentation only: scope narration reused from Rammus v7, SafeArea .9'
ft.update(duration=duration,scopeStart=start,resultsStart=start+delta)
# Remove stale derived fields; authoritative segments/captions now match replay.
ft['segments']=copy.deepcopy(f['segments']);ft['cues']=copy.deepcopy(f['captions'])
for c in ft['chapters']:
 if c['start']>=start:c['start']+=delta
ft['chapters'].append(dict(start=start,title='8365种方案与总榜规则'));ft['chapters'].sort(key=lambda x:x['start'])
manifest=json.load(open(FO/'tts-manifest.json'));rm=json.load(open(R/'tts-manifest.json'))
for k in ['S01','S02','S03']:
 manifest[k]=rm[k]
 for p in (R/'assets/tts').glob(k+'.*'):shutil.copy2(p,FO/'assets/tts'/p.name)
a.save_json(FO/'tts-manifest.json',manifest)
frames=round(delta*a.SR);cut=round(start*a.SR);sourcecut=round(scope['start']*a.SR)
def pcm(p):return np.array(a.pcm(p,2),dtype=np.float32).reshape(-1,2)
voice=pcm(F/'voice-processed.wav');scopevoice=pcm(R/'voice-processed.wav')[sourcecut:sourcecut+frames]
voice=np.concatenate([voice[:cut],scopevoice,voice[cut:]])
fx=pcm(F/'elimination-effects.wav');fx=np.concatenate([fx[:cut],np.zeros((frames,2),np.float32),fx[cut:]])
assert len(voice)==round(duration*a.SR) and len(fx)==len(voice)
recipe=json.load(open(F/'recipe.json'));music=recipe['music'];musicpath=ROOT/music['path'];assert a.sha(musicpath)==music['sha256']
gain=sum(music['gains'].values())
bgm=np.array(a.pcm(musicpath,2,f'atrim=start=0:end={duration+1:.3f},asetpts=PTS-STARTPTS,highpass=f=45:p=2,equalizer=f=2200:t=o:w=2:g=-4,volume={gain:.8f}dB'),np.float32).reshape(-1,2)[:len(voice)]
t=np.arange(len(bgm))/a.SR;fade=np.ones(len(bgm));m=t<music['fadeInSeconds'];fade[m]=.5-.5*np.cos(np.pi*t[m]/music['fadeInSeconds']);m=t>duration-music['fadeOutSeconds'];fade[m]=.5-.5*np.cos(np.pi*(duration-t[m])/music['fadeOutSeconds']);bgm*=fade[:,None]
mix=voice+fx+bgm;assert np.max(np.abs(mix))<1
for name,v in [('voice-processed',voice),('elimination-effects',fx),('music-bed',bgm),('mix-master',mix)]:
 tmp=FO/(name+'.f32');tmp.write_bytes(v.astype('float32').tobytes());a.ff(['-f','f32le','-ar',str(a.SR),'-ac','2','-i',str(tmp),'-c:a','pcm_s24le',str(FO/(name+'.wav'))]);tmp.unlink()
assert f['cards']==old['cards'] and f['runs']==old['runs'] and f['results']==old['results']
assert [s for s in f['segments'] if s['end']<=start]==[s for s in old['segments'] if s['end']<=start]
budget=[]
for e in ft['events']:
 s=next(s for s in f['segments'] if s['start']<=e['start']<s['end']);margin=s['end']-e['actualEnd'];assert margin>=.35-1e-6,(e['id'],margin)
 budget.append(dict(id=e['id'],layout=s['layout'],start=e['start'],actualEnd=e['actualEnd'],windowEnd=s['end'],tailSeconds=margin))
a.save_json(FO/'replay.json',f);a.save_json(FO/'timeline.json',ft);a.save_json(FO/'pause-budget.json',budget)
def tc(t):
 ms=round(t*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000);return f'{h:02}:{m:02}:{s:02},{ms:03}'
(FO/'subtitles.srt').write_text('\n\n'.join(f'{i+1}\n{tc(c["start"])} --> {tc(c["end"])}\n{c["text"]}' for i,c in enumerate(f['captions']))+'\n')
(FO/'chapters.txt').write_text('\n'.join(f'{int(c["start"]//60):02}:{int(c["start"]%60):02} {c["title"]}' for c in ft['chapters'])+'\n')
r.update(id='rammus-results72-safearea-v8',coverKey='cover/rammus-total-v8');a.save_json(RO/'replay.json',r)
for src,out in [(R,RO),(F,FO)]:
 a.save_json(out/'revision-validation.json',dict(source=str(src),newTtsCalls=0,combatUnchanged=True,coverChanged=True,safeAreaScale=[.9,.9,1],scopeInserted=out==FO,scopeSeconds=delta if out==FO else 0,duration=json.load(open(out/'replay.json'))['duration'],sourceMixSha256=a.sha(src/'mix-master.wav'),mixSha256=a.sha(out/'mix-master.wav')))
print('Prepared',RO,FO,'F scope',start,start+delta,'durations',r['duration'],f['duration'])
