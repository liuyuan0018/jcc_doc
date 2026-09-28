#!/usr/bin/env python3
"""Extend the established fixed-gain mix across the eight Unity result pages."""
import hashlib
import importlib.util
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EPISODE = ROOT / 'exports/frontline-rammus-eight-v1/production-v1'
RECIPE = ROOT / 'exports/frontline-rammus-eight-v1/rammus-eight-recipe.json'
PIPELINE = ROOT / 'scripts/tank-video/audio_helpers.py'
spec = importlib.util.spec_from_file_location('audio_helpers', PIPELINE)
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    timeline = json.loads((EPISODE / 'appendix-timeline.json').read_text())
    recipe = json.loads(RECIPE.read_text())
    duration = timeline['duration']
    samples = round(duration*engine.SR)
    music_cfg = recipe['music']
    source = ROOT / music_cfg['path']
    assert sha(source) == music_cfg['sha256']
    gains = music_cfg['gains']
    gain = gains['wallpaperV2RecipeGainDb'] + gains['approvedV5AddDb']
    filters = (f'atrim=start=0:end={duration+1:.3f},asetpts=PTS-STARTPTS,'
               f'highpass=f=45:p=2,equalizer=f=2200:t=o:w=2:g=-4,volume={gain:.8f}dB')
    mix = engine.pcm(source, 2, filters)
    assert len(mix) >= samples*2, 'Music source too short'
    del mix[samples*2:]
    fade_in = music_cfg['fadeInSeconds']
    fade_out = music_cfg['fadeOutSeconds']
    for i in range(samples):
        t = i / engine.SR
        factor = 1.0
        if t < fade_in:
            factor = .5-.5*math.cos(math.pi*t/fade_in)
        elif t > duration-fade_out:
            factor = .5-.5*math.cos(math.pi*(duration-t)/fade_out)
        mix[2*i] *= factor
        mix[2*i+1] *= factor

    for filename in ('voice-processed.wav', 'elimination-effects.wav'):
        stem = engine.pcm(EPISODE / filename, 2)
        assert len(stem) <= len(mix)
        for i, value in enumerate(stem):
            mix[i] += value

    for cue in timeline['events']:
        if not cue['id'].startswith('P'):
            continue  # V16 is already in voice-processed.wav.
        voice = engine.pcm(EPISODE / 'assets/tts' / (cue['id'] + '.wav'), 1)
        start = round(cue['start']*engine.SR)
        assert abs(len(voice)/engine.SR-(cue['end']-cue['start'])) < .05
        for i, value in enumerate(voice):
            mix[2*(start+i)] += value*engine.PAN
            mix[2*(start+i)+1] += value*engine.PAN
    peak = max(map(abs, mix))
    assert peak < 1.0, f'Mix clips: {peak}'
    out = EPISODE / 'mix-master-full.wav'
    engine.wav24(out, mix)
    report = {'path': str(out), 'sha256': sha(out), 'duration': duration,
              'sampleRate': engine.SR, 'peakLinear': peak, 'musicSha256': sha(source),
              'pageVoiceIds': [e['id'] for e in timeline['events'] if e['id'].startswith('P')]}
    (EPISODE / 'mix-full-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
