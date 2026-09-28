#!/usr/bin/env python3
"""Time-aligned TTS narration; video packets are copied unchanged.

Only public game commentary is sent to the selected Microsoft Edge TTS voice.
Audio clips are cached, timed against actual replay deaths, then mixed locally.
"""
import argparse
from array import array
import asyncio
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys
import wave
import edge_tts
import imageio_ffmpeg

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
SR=48000
FFMPEG=imageio_ffmpeg.get_ffmpeg_exe()
SCRIPT_SHA=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(args,**kwargs):return subprocess.run([FFMPEG,'-hide_banner',*args],check=True,**kwargs)

def decode(path):
    raw=run(['-loglevel','error','-i',str(path),'-f','s16le','-ac','1','-ar',str(SR),'pipe:1'],capture_output=True).stdout
    pcm=array('h');pcm.frombytes(raw)
    assert len(pcm)>SR*.1 and max(map(abs,pcm))>300,'Empty or silent speech'
    # Remove only outer silence, preserving pauses within the narration.
    active=[i for i in range(0,len(pcm),480) if max(map(abs,pcm[i:i+480]),default=0)>130]
    assert active
    start=max(0,active[0]-round(.05*SR));end=min(len(pcm),active[-1]+480+round(.09*SR))
    return pcm[start:end]

def wav(path,pcm):
    with wave.open(str(path),'wb') as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(SR);f.writeframes(pcm.tobytes())

def timestamp(s):
    n=round(s*1000)
    return f'{n//3600000:02}:{n//60000%60:02}:{n//1000%60:02},{n%1000:03}'

async def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--recipe',type=Path,default=HERE/'voice-main.json')
    parser.add_argument('--voice',help='Optional supported TTS voice override')
    args=parser.parse_args()
    recipe=json.loads(args.recipe.read_text())
    if args.voice:recipe['voice']=args.voice
    source=ROOT/recipe['source'];dest=ROOT/recipe['output'];dest.parent.mkdir(parents=True,exist_ok=True)
    cache=dest.parent/'speech-clips';cache.mkdir(exist_ok=True)
    info=json.loads(source.with_suffix('.verification.json').read_text())
    assert sha(source)==info['videoSha256'],'Source video has changed'
    data=json.loads(source.with_suffix('.json').read_text())
    assert sha(source.with_suffix('.json'))==info['dataSha256']
    if 'expectedBuilds' in recipe:
        assert data['kind']==recipe['kind']
        assert len(data['builds'])==len(recipe['expectedBuilds'])
        for b,expected in zip(data['builds'],recipe['expectedBuilds']):
            for key,value in expected.items():
                actual=b['pressure']['passedDps'] if key=='passedDps' else b[key]
                assert actual==value,f'Review narration after lane/config change: {key}'
    else:
        assert [b['hero'] for b in data['builds'][:2]]==['蔚','拉莫斯'],'Review the closing sentence for another ranking'
    segments=[s for s in info['segments'] if s['kind']=='battle']
    cues=[]
    for item in recipe['cues']:
        c=dict(item)
        if 'death' in c:
            ref=c['death'];rd=data['rounds'][ref['round']]
            match_key='label' if 'label' in ref else 'hero'
            matches=[i for i,b in enumerate(data['builds']) if b[match_key]==ref[match_key]]
            assert len(matches)==1,'Death narration must identify exactly one screen lane'
            hero=matches[0]
            result=rd['replays'][hero]['result'];assert not result['alive']
            seg=segments[ref['round']]
            c['eventAt']=seg['start']+(result['frame']/30)/rd['seconds']*(seg['end']-seg['start'])
            c['start']=c['eventAt']+ref['offset']
        assert 0<=c['start']<c['end']<=info['duration']
        c['spoken']=c['text']
        for word,spoken in recipe.get('pronunciation',{}).items():c['spoken']=c['spoken'].replace(word,spoken)
        cues.append(c)
    for a,b in zip(cues,cues[1:]):assert a['end']<=b['start'],f'Overlapping cue windows: {a["id"]}'
    sem=asyncio.Semaphore(3)
    async def synth(c):
        key=hashlib.sha256(json.dumps([recipe['voice'],recipe['rate'],recipe['pitch'],c['spoken']],ensure_ascii=False).encode()).hexdigest()[:14]
        target=cache/(c['id']+'-'+key+'.mp3')
        if not target.exists() or target.stat().st_size<100:
            async with sem:
                temporary=target.with_suffix('.partial.mp3')
                voice=edge_tts.Communicate(c['spoken'],recipe['voice'],rate=recipe['rate'],pitch=recipe['pitch'])
                await asyncio.wait_for(voice.save(str(temporary)),45)
                temporary.replace(target)
        c['clip']=target.name;c['clipSha256']=sha(target)
        print('Speech ready:',c['id'],flush=True)
    await asyncio.gather(*(synth(c) for c in cues))
    mix=array('h',[0])*round(info['duration']*SR)
    for c in cues:
        pcm=decode(cache/c['clip']);original=len(pcm)/SR
        budget=c['end']-c['start']-.04
        tempo=max(1.0,original/budget)
        if tempo>1.28:raise RuntimeError(f'Rewrite cue {c["id"]}: {original:.2f}s speech for {budget:.2f}s window; refusing rushed audio')
        if tempo>1.001:
            temp=cache/(c['id']+'-trimmed.wav');wav(temp,pcm)
            stretched=cache/(c['id']+'-fit.wav')
            run(['-loglevel','error','-y','-i',str(temp),'-af',f'atempo={tempo:.8f}','-c:a','pcm_s16le','-ar',str(SR),str(stretched)],capture_output=True)
            pcm=decode(stretched)
        duration=len(pcm)/SR
        assert duration<=c['end']-c['start']+.01,(c['id'],duration,c['end']-c['start'])
        start=round(c['start']*SR)
        mix[start:start+len(pcm)]=pcm
        c.update(originalDuration=original,duration=duration,actualEnd=c['start']+duration,tempo=tempo)
        print(c['id'],f'{c["start"]:.2f} → {c["actualEnd"]:.2f}',f'tempo {tempo:.3f}',flush=True)
    assert len(mix)==round(info['duration']*SR)
    raw=dest.with_suffix('.wav');wav(raw,mix)
    temp=dest.with_name(dest.stem+'.partial.mp4')
    run(['-loglevel','error','-y','-i',str(source),'-i',str(raw),'-map','0:v:0','-map','1:a:0',
         '-c:v','copy','-c:a','aac','-b:a','160k','-ar',str(SR),'-af','loudnorm=I=-16:TP=-1.5:LRA=11',
         '-t',str(info['duration']),'-movflags','+faststart',str(temp)],capture_output=True)
    temp.replace(dest)
    # Verify every decoded video frame and presence of a non-silent AAC track.
    decoded=run(['-i',str(dest),'-f','null','-'],capture_output=True,text=True)
    frames=re.findall(r'frame=\s*(\d+)',decoded.stderr)
    assert frames and int(frames[-1])==info['frames']
    assert 'Audio: aac' in decoded.stderr and '48000 Hz' in decoded.stderr
    def video_hash(p):
        return run(['-loglevel','error','-i',str(p),'-map','0:v:0','-c','copy','-f','hash','-hash','sha256','-'],capture_output=True,text=True).stdout.strip()
    assert video_hash(source)==video_hash(dest),'Video packets changed during audio mux'
    volume=run(['-i',str(dest),'-vn','-af','volumedetect','-f','null','-'],capture_output=True,text=True)
    mean=float(re.search(r'mean_volume: ([\d.\-]+) dB',volume.stderr).group(1))
    peak=float(re.search(r'max_volume: ([\d.\-]+) dB',volume.stderr).group(1))
    assert -40<mean<-3 and peak<=0
    subtitles=[f'{i+1}\n{timestamp(c["start"])} --> {timestamp(c["actualEnd"])}\n{c["text"]}\n' for i,c in enumerate(cues)]
    dest.with_suffix('.srt').write_text('\n'.join(subtitles))
    dest.with_suffix('.transcript.txt').write_text('\n'.join(c['text'] for c in cues)+'\n')
    report=dict(passed=True,voice=recipe['voice'],provider='Microsoft Edge online TTS via edge-tts 7.2.8',
                duration=info['duration'],videoFrames=info['frames'],sampleRate=SR,audioCodec='aac',
                videoPacketsUnchanged=True,videoSourceSha256=info['videoSha256'],outputSha256=sha(dest),
                scriptSha256=SCRIPT_SHA,meanVolumeDb=mean,maxVolumeDb=peak,
                deathCuesFollowEvents=True,overlappingCues=False,cues=cues)
    dest.with_suffix('.verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    (dest.parent/'recipe.json').write_text(json.dumps(recipe,ensure_ascii=False,indent=2))
    print('Done:',dest,flush=True)
    print(json.dumps({k:v for k,v in report.items() if k!='cues'},ensure_ascii=False),flush=True)

if __name__=='__main__':asyncio.run(main())
