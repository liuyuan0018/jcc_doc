#!/usr/bin/env python3
"""Remaster the cached original narration, keeping all video packets and cue times."""
from pathlib import Path
from array import array
import argparse,hashlib,json,math,re,subprocess,wave
import imageio_ffmpeg

ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser()
p.add_argument('--source',type=Path,default=ROOT/'exports/frontline-video-voice-v1/01-hero-pressure-voice.mp4')
p.add_argument('--output',type=Path,default=ROOT/'exports/frontline-video-voice-v2/01-hero-pressure-voice-soft.mp4')
args=p.parse_args()
SRC=args.source.resolve().with_suffix('')
DEST=args.output.resolve()
assert DEST!=SRC.with_suffix('.mp4'),'Remaster to a new file; retain the original narration'
OUT=DEST.parent
OUT.mkdir(parents=True,exist_ok=True)
FF=imageio_ffmpeg.get_ffmpeg_exe()
SR=48000
def run(args):return subprocess.run([FF,'-hide_banner',*args],capture_output=True,check=True)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def stats(path,filters=''):
    f=(filters+',' if filters else '')+'loudnorm=I=-22:TP=-5:LRA=11:print_format=json'
    s=run(['-i',str(path),'-vn','-af',f,'-f','null','-']).stderr.decode()
    return json.loads(re.search(r'\{\s*"input_i".*?\}',s,re.S).group())
def pcm(path):
    a=array('h');a.frombytes(run(['-loglevel','error','-i',str(path),'-vn','-ac','1','-ar',str(SR),'-f','s16le','pipe:1']).stdout)
    return a
def write_wav(path,a):
    with wave.open(str(path),'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(SR);w.writeframes(a.tobytes())

report=json.loads(SRC.with_suffix('.verification.json').read_text())
assert sha(SRC.with_suffix('.mp4'))==report['outputSha256']
raw=pcm(SRC.with_suffix('.wav'));original=pcm(SRC.with_suffix('.mp4'))
assert len(raw)==round(report['duration']*SR)
# Quiet 8 ms cosine edges avoid discontinuities without moving speech.
for c in report['cues']:
    st=round(c['start']*SR);en=round(c['actualEnd']*SR);n=round(.008*SR)
    for i in range(n):
        weight=.5-.5*math.cos(math.pi*i/(n-1))
        raw[st+i]=round(raw[st+i]*weight)
        raw[en-1-i]=round(raw[en-1-i]*weight)
faded=OUT/(DEST.stem+'-faded.wav');write_wav(faded,raw)
# Control brief syllable peaks rather than only attenuating the whole track.
# Peak detection and a soft knee catch short bursts missed by the previous
# 6 ms RMS detector. No auto makeup or dynamic loudness boost is applied.
chain='highpass=f=85:p=2,equalizer=f=3500:t=o:w=1:g=-1.5,deesser=i=0.15:m=0.25:f=0.5,acompressor=threshold=0.1:ratio=3:attack=0.3:release=70:makeup=1:knee=2.82843:detection=peak'
measured=stats(faded,chain)
# Fixed gain, constrained by true-peak headroom. Do not use dynamic loudness boosting.
gain=min(-21-float(measured['input_i']),-5.2-float(measured['input_tp']))
master=OUT/(DEST.stem+'-master.wav')
run(['-loglevel','error','-y','-i',str(faded),'-af',chain+f',volume={gain:.6f}dB','-ar',str(SR),'-ac','1','-c:a','pcm_s16le',str(master)])
run(['-loglevel','error','-y','-i',str(SRC.with_suffix('.mp4')),'-i',str(master),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k','-ar',str(SR),'-t',str(report['duration']),'-movflags','+faststart',str(DEST)])
after=pcm(DEST);old=stats(SRC.with_suffix('.mp4'));new=stats(DEST)
assert sum(abs(v)>=32760 for v in after)==0
assert float(new['input_tp'])<=-4.8,new
assert abs(len(after)/SR-report['duration'])<1/30
def cue_metrics(a,c):
    values=a[round(c['start']*SR):round(c['actualEnd']*SR)]
    peak=max(map(abs,values))/32768
    rms=math.sqrt(sum(v*v for v in values)/len(values))/32768
    return dict(peakDbfs=round(20*math.log10(max(peak,1e-9)),2),
                rmsDbfs=round(20*math.log10(max(rms,1e-9)),2),
                crestDb=round(20*math.log10(max(peak,1e-9)/max(rms,1e-9)),2))
per_cue=[dict(id=c['id'],text=c['text'],start=c['start'],end=c['actualEnd'],
              original=cue_metrics(original,c),revised=cue_metrics(after,c)) for c in report['cues']]
def video_hash(path):return run(['-loglevel','error','-i',str(path),'-map','0:v:0','-c','copy','-f','hash','-hash','sha256','-']).stdout.decode().strip()
assert video_hash(DEST)==video_hash(SRC.with_suffix('.mp4'))
decoded=run(['-i',str(DEST),'-f','null','-']).stderr.decode()
assert int(re.findall(r'frame=\s*(\d+)',decoded)[-1])==report['videoFrames']
result=dict(passed=True,sourceVideoSha256=sha(SRC.with_suffix('.mp4')),sourceRawSha256=sha(SRC.with_suffix('.wav')),
    outputSha256=sha(DEST),scriptSha256=sha(__file__),duration=report['duration'],videoFrames=report['videoFrames'],
    videoPacketsUnchanged=True,cueTimesUnchanged=True,cues=report['cues'],sourceNarrationReport=str(SRC.with_suffix('.verification.json')),
    sourceNarrationReportSha256=sha(SRC.with_suffix('.verification.json')),fadeMs=8,filterChain=chain,fixedGainDb=gain,
    oldIntegratedLufs=float(old['input_i']),newIntegratedLufs=float(new['input_i']),oldTruePeakDbtp=float(old['input_tp']),newTruePeakDbtp=float(new['input_tp']),
    sourceDigitalClippedSamples=sum(abs(v)>=32760 for v in original),outputDigitalClippedSamples=sum(abs(v)>=32760 for v in after),
    perCue=per_cue,
    decodedAudioSeconds=len(after)/SR,audioVideoDurationDeltaSeconds=len(after)/SR-report['duration'],perceptualReview='Awaiting user listening feedback; measurements do not rule out synthesis or playback artifacts')
DEST.with_suffix('.verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
for ext in ['.srt','.transcript.txt']:
    DEST.with_suffix(ext).write_bytes(SRC.with_suffix(ext).read_bytes())
print(json.dumps(result,ensure_ascii=False,indent=2))
print(DEST)
