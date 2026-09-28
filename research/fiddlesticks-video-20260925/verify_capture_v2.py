import json,subprocess,importlib.util,math,statistics,csv,argparse
from array import array
from pathlib import Path
ROOT=Path('/Users/lyu/Documents/ChatGPT/金铲铲')
ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,default=ROOT/'exports/frontline-rammus-eight-v1/production-v3');ap.add_argument('--take',default='rammus-continuous-v3d');ap.add_argument('--final',default='rammus-results64-v3-final.mp4');ap.add_argument('--review-cues',default='');args=ap.parse_args();OUT=args.out.resolve()
spec=importlib.util.spec_from_file_location('audio',ROOT/'scripts/tank-video/audio_helpers.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
raw=OUT/(args.take+'.mp4');alignment=json.loads((OUT/(args.take+'.alignment.json')).read_text());offset=alignment['prerollSeconds'];duration=alignment['timelineSeconds'];final=OUT/args.final
timeline=json.loads((OUT/'timeline.json').read_text());events={e['id']:e for e in timeline['events']}
# Only trim the measured preparation prefix from the single continuous take.
a.ff(['-ss',f'{offset:.9f}','-i',str(raw),'-t',f'{duration:.9f}','-map','0:v:0','-map','0:a:0','-c:v','h264_videotoolbox','-b:v','8000k','-c:a','aac','-b:a','192k','-movflags','+faststart',str(final)])
a.ff(['-i',str(final),'-f','null','-'])
def pcm(path,start,seconds):
 cmd=['-ss',str(start),'-i',str(path),'-t',str(seconds),'-vn','-ac','1','-ar','4000','-f','f32le','pipe:1'];x=array('f');x.frombytes(a.ff(cmd).stdout);return x
page_ids=sorted(k for k in events if k.startswith('P'))
summary_key='summary' if 'summary' in events else 'P02'
# Match actual captured audio against the mixed Unity input at separated timeline points.
review_cues=[k for k in args.review_cues.split(',') if k]
sync=[]
probe_keys=list(dict.fromkeys(['750','950','1150',summary_key,'P01','P05',page_ids[-1]]+review_cues))
for point in [1]+[events[k]['start']+.6 for k in probe_keys]:
 ref=pcm(OUT/'mix-master.wav',point,1.0);got=pcm(final,point-.15,1.3);n=min(4000,len(ref));ref=ref[:n];rm=sum(ref)/n;ref=[v-rm for v in ref];rr=sum(v*v for v in ref)
 def corr(lag):
  segment=got[lag:lag+n]
  if len(segment)!=n:return -2
  gm=sum(segment)/n;gg=sum((v-gm)**2 for v in segment)
  return sum(x*(y-gm) for x,y in zip(ref,segment))/math.sqrt(rr*gg) if rr*gg else -2
 coarse=max(range(0,len(got)-n+1,20),key=corr);lag=max(range(max(0,coarse-20),min(len(got)-n,coarse+20)+1),key=corr);value=corr(lag);error=lag/4000-.15
 sync.append(dict(time=point,audioOffsetSeconds=error,correlation=value));assert value>.94 and abs(error)<1/30,(point,error,value)
# Playback frame timing is separate from recorder's own frame-drop statistics.
rows=list(csv.DictReader((OUT/(args.take+'.frames.csv')).open()));print('frame columns',list(rows[0]),flush=True)
report=dict(fullDecode=True,source=str(raw),final=str(final),trimStartSeconds=offset,duration=duration,continuousTake=True,audioSync=sync,maxAudioOffsetSeconds=max(abs(x['audioOffsetSeconds']) for x in sync),finalSha256=a.sha(final))
(OUT/'verification-final.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
for name,time in [('cover',1),('first-elimination',events['750']['start']+1),('results-page2' if summary_key=='P02' else 'summary',events[summary_key]['start']+1),('results-page1',timeline['resultsStart']+1),('results-last-page',events[page_ids[-1]]['start']+1),('final-failure',events['1150']['start']+.8),('triple-elimination',events['950']['start']+.8),('results-page5',events['P05']['start']+.8)]:
 a.ff(['-ss',str(time),'-i',str(final),'-frames:v','1',str(OUT/(name+'.png'))])
for key in review_cues:
 a.ff(['-ss',str(events[key]['start']+.8),'-i',str(final),'-frames:v','1',str(OUT/('cue-'+key+'.png'))])
a.ff(['-ss',str(events['750']['start']-1),'-i',str(final),'-t','8','-c:v','copy','-c:a','copy',str(OUT/'review-elimination.mp4')])
a.ff(['-ss',str(timeline['resultsStart']-4),'-i',str(final),'-t','17','-c:v','copy','-c:a','copy',str(OUT/'review-results-transition.mp4')])
print(json.dumps(report,ensure_ascii=False),flush=True)
