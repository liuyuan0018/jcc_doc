"""Revise a verified replay with fitted narration, retaining combat data and battle duration."""
import argparse, asyncio, copy, importlib.util, json, math, shutil
from array import array
from pathlib import Path

ROOT = Path('/Users/lyu/Documents/ChatGPT/金铲铲')
ap = argparse.ArgumentParser(description=__doc__)
for key in ['baseline', 'ranking', 'profile', 'out']:
    ap.add_argument('--' + key, type=Path, required=True)
ap.add_argument('--id', required=True)
args = ap.parse_args()
args.out.mkdir(parents=True, exist_ok=True)
spec = importlib.util.spec_from_file_location('voices', ROOT/'research/rammus-eight-20260924/make_appendix_voice.py')
voices = importlib.util.module_from_spec(spec); spec.loader.exec_module(voices)
voices.OUT = args.out/'assets/tts'
shutil.copytree(args.baseline/'assets/tts', voices.OUT, dirs_exist_ok=True)
a = voices.audio
recipe = json.loads((ROOT/'exports/frontline-rammus-eight-v1/rammus-eight-recipe.json').read_text())
profile = json.loads(args.profile.read_text())
base = json.loads((args.baseline/'replay.json').read_text())
timeline = json.loads((args.baseline/'timeline.json').read_text())
original_events = {e['id']: e for e in timeline['events']}
texts = {**profile['mainCues'], **profile['scopeCues']}
page_count = profile.get('pageCount', 8)
for i in range(1, page_count + 1):
    key = f'P{i:02}'
    texts[key] = profile['pageCueOverrides'][key] if key in profile['pageCueOverrides'] else original_events[key]['spoken']

async def main():
    sem = asyncio.Semaphore(3)
    async def one(key, text):
        async with sem:
            clip = await voices.make_one(dict(id=key, spoken=text), recipe['tts'], recipe['voiceProcessing'])
            print(key, clip['seconds'], 'reused' if clip['processedReused'] else 'new', flush=True)
            return key, clip
    clips = dict(await asyncio.gather(*(one(k, v) for k, v in texts.items())))
    replay = copy.deepcopy(base)
    replay.update(id=args.id, captions=[], segments=[])
    ranking = json.loads(args.ranking.read_text())
    replay.update(results=ranking['results'], source=ranking['source'] + '; original combat, compact static narration')
    replay['footnote'] = '固定条件模拟 · 每50来伤逐档加压 · 细分成绩见片尾'
    events = []; maps = []; tail = profile['speechTailSeconds']
    frame = lambda t: math.ceil((t - 1e-9)*30)/30
    def cue(key, start):
        end = start + clips[key]['seconds']
        event = dict(id=key, text=texts[key], spoken=texts[key], start=start, actualEnd=end, end=end+.18)
        events.append(event)
        text = texts[key]
        if len(text) > 24:
            pos = text.find('，') + 1
            if pos > 0: text = text[:pos] + '\n' + text[pos:]
        replay['captions'].append(dict(start=start, end=end+.18, text=text))
        return end
    t = 0.0
    originals = [s for s in base['segments'] if s['layout'] not in ['scope', 'results'] and s['id'] not in profile.get('skipSegments', [])]
    for original in originals:
        segment = copy.deepcopy(original); start = t
        for key in profile['mainCues']:
            old = original_events[key]
            assigned = profile.get('mainCueSegments', {}).get(key)
            if (assigned == original['id']) if assigned else (original['start'] <= old['start'] < original['end']):
                offset = (.3 if key=='V01' else .25 if key in ['V02','V16'] else profile['pauseCueOffsetSeconds']) if assigned else (.25 if key == 'V16' else old['start'] - original['start'])
                cue(key, start + offset)
        duration = original['end'] - original['start']
        if segment['phase'] != 'battle' and 'staticWindows' in profile:
            duration = profile['staticWindows'].get(segment['id'], profile['defaultHoldSeconds'])
        elif segment['phase'] != 'battle':
            active_end = max((e['actualEnd'] for e in events), default=start)
            duration = max(.4, active_end + tail - start)
            if not any(original['start'] <= original_events[k]['start'] < original['end'] for k in profile['mainCues']) and active_end <= start:
                duration = min(duration, original['end'] - original['start'])
        t = start + duration if segment['phase'] == 'battle' else frame(start + duration)
        segment.update(start=start, end=t); replay['segments'].append(segment)
        maps.append(dict(oldStart=original['start'], oldEnd=original['end'], start=start, end=t, phase=segment['phase']))
    scope_start = t
    if profile['scopeCues']: t += .25
    for key in profile['scopeCues']:
        t = cue(key, t) + .25
    if profile['scopeCues']: t = frame(t + .25)
    if 'scopeSeconds' in profile:
        assert t <= scope_start + profile['scopeSeconds'] + .01, 'Scope narration exceeds fixed window; shorten text'
        t = scope_start + profile['scopeSeconds']
    def segment(key, layout, start, end, **kw):
        return dict(id=key, layout=layout, phase='intro' if layout=='scope' else 'result', start=start, end=end,
                    roundSeconds=30, dps=0, simFrom=0, simTo=0, tracks=[], records=[], hasPageTurnSeconds=True, pageTurnSeconds=0, **kw)
    if t > scope_start: replay['segments'].append(segment('scope-8365', 'scope', scope_start, t))
    results_start=t; chapters=[dict(start=0,title='八套逐档压测')]
    if t > scope_start: chapters.append(dict(start=scope_start,title='8365种方案怎么比较'))
    for i in range(page_count):
        start=t; end_voice=cue(f'P{i+1:02}',start+.3)
        assert end_voice+tail<=start+profile['pageSeconds'], 'Page narration exceeds fixed window; shorten text'
        t=start+profile['pageSeconds']
        replay['segments'].append(segment(f'results-{i+1}','results',start,t,resultPage=i+1))
        title=profile['chapterTitles'][i] if 'chapterTitles' in profile else f'配装第{i+1}页 · {i*8+1}—{i*8+8}套'
        chapters.append(dict(start=start,title=title))
    replay['duration']=t
    # Meaningful invariants: combat state and mappings do not change; only static pacing changes.
    assert replay['runs']==base['runs'] and replay['cards']==base['cards']
    new_battles=[s for s in replay['segments'] if s['phase']=='battle']
    old_battles=[s for s in base['segments'] if s['phase']=='battle']
    for old,new in zip(old_battles,new_battles):
        assert {k:v for k,v in old.items() if k not in ['start','end']}=={k:v for k,v in new.items() if k not in ['start','end']}
        assert abs((old['end']-old['start'])-(new['end']-new['start']))<1e-8
    for left,right in zip(events,events[1:]): assert left['actualEnd']+.15<=right['start']
    for left,right in zip(replay['segments'],replay['segments'][1:]): assert abs(left['end']-right['start'])<1e-8
    # All speech on a static view must finish before the next battle/page.
    for e in events:
        seg=next(s for s in replay['segments'] if s['start']<=e['start']<s['end'])
        if seg['phase']!='battle': assert e['actualEnd']+tail<=seg['end']+1e-8,(e['id'],seg['id'])
    # Preserve actual death-to-speech delay for each retained elimination cue.
    timing=[]
    for key in ['V04','V05','V06','V07','V09','V12']:
        old=original_events[key];new=next(e for e in events if e['id']==key)
        m=next(m for m in maps if m['oldStart']<=old['start']<m['oldEnd'])
        if 'mainCueSegments' not in profile:
            assert abs((old['start']-m['oldStart'])-(new['start']-m['start']))<1e-8
        else:
            assigned=next(s for s in replay['segments'] if s['id']==profile['mainCueSegments'][key])
            assert assigned['phase']=='hold' and assigned['start']<=new['start'] and new['actualEnd']+tail<=assigned['end']+1e-8
        timing.append(dict(id=key,oldStart=old['start'],start=new['start'],seconds=clips[key]['seconds']))
    (args.out/'replay.json').write_text(json.dumps(replay,ensure_ascii=False,separators=(',',':')))
    (args.out/'timeline.json').write_text(json.dumps(dict(duration=t,events=events,chapters=chapters,scopeStart=scope_start,resultsStart=results_start,fps=30,timeMap=maps),ensure_ascii=False,indent=2))
    (args.out/'tts-manifest.json').write_text(json.dumps(clips,ensure_ascii=False,indent=2))
    def tc(t):
        ms=round(t*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000)
        return f'{h:02}:{m:02}:{s:02},{ms:03}'
    (args.out/'subtitles.srt').write_text('\n\n'.join(f'{i+1}\n{tc(c["start"])} --> {tc(c["end"])}\n{c["text"]}' for i,c in enumerate(replay['captions']))+'\n')
    (args.out/'chapters.txt').write_text('\n'.join(f'{int(c["start"]//60):02}:{int(c["start"]%60):02} {c["title"]}' for c in chapters)+'\n')
    samples=round(t*a.SR);voice=array('f',[0.])*(samples*2)
    for event in events:
        clip=a.pcm(voices.OUT/(event['id']+'.wav'),1);offset=round(event['start']*a.SR)*2
        for i,v in enumerate(clip): voice[offset+2*i]+=v*a.PAN;voice[offset+2*i+1]+=v*a.PAN
    a.wav24(args.out/'voice-processed.wav',voice)
    music=recipe['music'];music_path=ROOT/music['path'];assert a.sha(music_path)==music['sha256']
    gain=music['gains']['wallpaperV2RecipeGainDb']+music['gains']['approvedV5AddDb']
    filters=f'atrim=start=0:end={t+1:.3f},asetpts=PTS-STARTPTS,highpass=f=45:p=2,equalizer=f=2200:t=o:w=2:g=-4,volume={gain:.8f}dB'
    mix=a.pcm(music_path,2,filters);assert len(mix)>=samples*2;del mix[samples*2:]
    for i in range(samples):
        seconds=i/a.SR;factor=1.
        if seconds<music['fadeInSeconds']:factor=.5-.5*math.cos(math.pi*seconds/music['fadeInSeconds'])
        elif seconds>t-music['fadeOutSeconds']:factor=.5-.5*math.cos(math.pi*(t-seconds)/music['fadeOutSeconds'])
        mix[2*i]*=factor;mix[2*i+1]*=factor
    a.wav24(args.out/'music-bed.wav',mix)
    # Remap each non-silent SFX burst by its original segment, preserving the complete tail.
    effects_source=args.baseline/'elimination-effects.wav'
    if not effects_source.exists(): effects_source=ROOT/'exports/frontline-rammus-eight-v1/production-v1/elimination-effects.wav'
    effects=a.pcm(effects_source,2)
    windows=[];step=round(.01*a.SR)*2
    for i in range(0,len(effects),step):
        if max(map(abs,effects[i:i+step]),default=0)>1e-7:
            if windows and i-windows[-1][1]<=round(.1*a.SR)*2:windows[-1][1]=i+step
            else:windows.append([i,i+step])
    effect_track=array('f',[0.])*(samples*2)
    for begin,end in windows:
        old_time=begin/(2*a.SR);m=next(m for m in maps if m['oldStart']<=old_time<m['oldEnd'])
        offset=round((m['start']+old_time-m['oldStart'])*a.SR)*2
        for i,v in enumerate(effects[begin:end]):effect_track[offset+i]+=v
    a.wav24(args.out/'elimination-effects.wav',effect_track)
    for i,v in enumerate(voice):mix[i]+=v+effect_track[i]
    peak=max(map(abs,mix));assert peak<1
    a.wav24(args.out/'mix-master.wav',mix)
    shutil.copyfile(args.baseline/'CREDITS.txt',args.out/'CREDITS.txt')
    report=dict(passed=True,duration=t,previousDuration=base['duration'],scopeStart=scope_start,resultsStart=results_start,
                combatUnchanged=True,battleDurationsUnchanged=True,eliminationSpeechAnchors=timing,
                fixedPauseWindows=('staticWindows' in profile),profileSha256=a.sha(args.profile),
                pauseWindows=[dict(id=s['id'],duration=s['end']-s['start']) for s in replay['segments'] if s['phase']!='battle'],
                removedCues=sorted(set(original_events)-set(texts)),peak=peak,
                replaySha256=a.sha(args.out/'replay.json'),mixSha256=a.sha(args.out/'mix-master.wav'),
                sourceReplaySha256=a.sha(args.baseline/'replay.json'),sfxBursts=len(windows))
    (args.out/'timeline-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)
asyncio.run(main())
