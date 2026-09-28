"""Create representative and full Unity render manifests for Vi Sterak."""

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'exports/frontline-vi-sterak-eight-v1/production-v1'
UNITY = Path('/Users/lyu/Documents/project/game/projects/jcc/client')
sys.path.insert(0, str(UNITY / 'Tools/Production'))
from episode_package import create_package  # noqa: E402


def main():
    timeline = json.loads((OUT / 'content-pipeline/timeline.json').read_text())
    caps = json.loads((OUT / 'capabilities.json').read_text())
    tiers = {t['dps']: t for t in timeline['tiers']}
    events = {(e['dps'], e['build']): e['at'] for e in timeline['events']}
    result = next(s for s in timeline['segments'] if s['kind'] == 'result')
    cue = {c['id']: c for c in timeline['cues']}
    points = [
        dict(id='cover-clean', time=0),
        dict(id='cover-full-name', time=1.4),
        dict(id='intro', time=timeline['coverSeconds'] + .6),
        dict(id='first-tier', time=(tiers[1750]['battleStart'] + tiers[1750]['battleEnd']) / 2),
        dict(id='all-pass-1750', time=tiers[1750]['battleEnd'] + .3),
        dict(id='H-before-1800', time=events[1800, 'H'] - .1),
        dict(id='H-settled-1800', time=tiers[1800]['battleEnd'] + 1.5),
        dict(id='D-F-settled-1850', time=tiers[1850]['battleEnd'] + 1.5),
        dict(id='five-pass-1900', time=tiers[1900]['battleEnd'] + .2),
        dict(id='B-frame900-fail', time=tiers[1950]['battleEnd'] + .6),
        dict(id='C-settled-2000', time=tiers[2000]['battleEnd'] + 1.5),
        dict(id='G-settled-2050', time=tiers[2050]['battleEnd'] + 1.5),
        dict(id='E-settled-2100', time=tiers[2100]['battleEnd'] + 1.5),
        dict(id='solo-2150', time=tiers[2150]['battleStart'] + 1.5),
        dict(id='A-pass-2200', time=tiers[2200]['battleEnd'] + .2),
        dict(id='A-fail-2250', time=events[2250, 'A'] + 1.0),
        dict(id='result-A-B-C', time=cue['V15']['start'] + 2.0),
        dict(id='result-five-sterak', time=cue['V16']['start'] + 2.0),
        dict(id='ending', time=timeline['duration'] - .1),
    ]
    preview = create_package(OUT / 'replay.json', OUT / 'preview-package.json', caps,
                             'vi-sterak-eight-preview-v1', points)
    video = create_package(OUT / 'replay.json', OUT / 'video-package.json', caps,
                           'vi-sterak-eight-video-v1', points,
                           video=dict(fps=30, startFrame=0,
                                      frameCount=timeline['frames']))
    print(json.dumps(dict(previewCount=len(preview['previewFrames']),
                          frames=video['video']['frameCount'],
                          fingerprint=video['rendererFingerprint']), ensure_ascii=False))


if __name__ == '__main__':
    main()
