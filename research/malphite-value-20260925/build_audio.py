import argparse,asyncio,importlib.util,json,shutil,re
from pathlib import Path
from array import array
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);args=p.parse_args();out=args.out.resolve()
s=importlib.util.spec_from_file_location('voice',ROOT/'research/rammus-eight-20260924/make_appendix_voice.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v);v.OUT=out/'assets/tts';a=v.audio
recipe=json.loads((out/'recipe.json').read_text());cues=json.loads((out/'cues.json').read_text());replay=json.loads((out/'replay-unvoiced.json').read_text());timeline=json.loads((out/'timeline-base.json').read_text())
async def main():
 clips={};sem=asyncio.Semaphore(3)
 async def one(c):
  async with sem:
   for attempt in range(3):
    try:
     clips[c['id']]=await v.make_one(c,recipe['tts'],recipe['voiceProcessing']);break
    except Exception:
     if attempt==2:raise
     print('retry',c['id'],flush=True);await asyncio.sleep(2)
   print(c['id'],round(clips[c['id']]['seconds'],2),flush=True)
 await asyncio.gather(*(one(c)for c in cues))
 budget=[dict(id=c['id'],windowStart=c['windowStart'],windowEnd=c['windowEnd'],speechEnd=c['start']+clips[c['id']]['seconds'],tail=c['windowEnd']-c['start']-clips[c['id']]['seconds'])for c in cues]
 a.save_json(out/'tts-manifest.json',clips);a.save_json(out/'pause-budget.json',budget)
 failed=[x for x in budget if x['tail']<.35]
 if failed:print('OVER BUDGET',json.dumps(failed));return
 duration=replay['duration'];samples=round(duration*a.SR);voice=array('f',[0.])*(samples*2)
 for c,b in zip(cues,budget):
  clip=a.pcm(v.OUT/(c['id']+'.wav'),1);off=round(c['start']*a.SR)*2
  for i,x in enumerate(clip):voice[off+2*i]+=x*a.PAN;voice[off+2*i+1]+=x*a.PAN
  c.update(actualEnd=b['speechEnd'],end=b['speechEnd']+.18)
  display=c.get('displayText',c['text'])
  if len(display)>22 and '\n' not in display:
   points=[m.end()for m in re.finditer('[，。]',display)if m.end()<len(display)]
   pos=min(points,key=lambda n:abs(n-len(display)/2))if points else len(display)//2
   display=display[:pos]+'\n'+display[pos:]
  if display:replay['captions'].append(dict(start=c['start'],end=c['end'],text=display))
 a.wav24(out/'voice-processed.wav',voice);del voice
 music=recipe['music'];mp=ROOT/music['path'];assert a.sha(mp)==music['sha256'];gain=sum(music['gains'].values())
 a.ff(['-stream_loop','-1','-i',str(mp),'-t',str(duration),'-af',f'highpass=f=45:p=2,equalizer=f=2200:t=o:w=2:g=-4,volume={gain}dB,afade=t=in:d={music["fadeInSeconds"]},afade=t=out:st={duration-music["fadeOutSeconds"]}:d={music["fadeOutSeconds"]}','-ar',str(a.SR),'-ac','2','-c:a','pcm_s24le',str(out/'music-bed.wav')])
 old=a.pcm(ROOT/'exports/frontline-rammus-eight-v1/production-v5/elimination-effects.wav',2);active=next(i for i,x in enumerate(old)if abs(x)>1e-7);active-=active%2;burst=old[active:active+int(.5*a.SR)*2];fx=array('f',[0.])*(samples*2)
 for at in timeline['deathAnchors']:
  off=round(at*a.SR)*2
  for i,x in enumerate(burst):fx[off+i]+=x
 a.wav24(out/'elimination-effects.wav',fx);del fx
 a.ff(['-i',str(out/'voice-processed.wav'),'-i',str(out/'music-bed.wav'),'-i',str(out/'elimination-effects.wav'),'-filter_complex','[0:a][1:a][2:a]amix=inputs=3:normalize=0:duration=longest[a]','-map','[a]','-c:a','pcm_s24le',str(out/'mix-master.wav')])
 timeline.update(events=cues,fps=30);a.save_json(out/'timeline.json',timeline);a.save_json(out/'replay.json',replay)
 def tc(t):
  ms=round(t*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000);return f'{h:02}:{m:02}:{s:02},{ms:03}'
 (out/'subtitles.srt').write_text('\n\n'.join(f'{i+1}\n{tc(c["start"])} --> {tc(c["end"])}\n{c["text"]}'for i,c in enumerate(cues)))
 (out/'chapters.txt').write_text('\n'.join(f'{int(c["start"]//60):02}:{int(c["start"]%60):02} {c["title"]}'for c in timeline['chapters']))
 shutil.copyfile(ROOT/'exports/frontline-rammus-eight-v1/production-v5/CREDITS.txt',out/'CREDITS.txt')
 loud=a.loudness(out/'mix-master.wav');assert float(loud['input_tp'])<0,loud
 a.save_json(out/'audio-validation.json',dict(passed=True,duration=duration,minTail=min(b['tail']for b in budget),loudness=loud,mixSha256=a.sha(out/'mix-master.wav')));print('AUDIO READY',duration,flush=True)
asyncio.run(main())
