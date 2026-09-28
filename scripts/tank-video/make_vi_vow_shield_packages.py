"""Create corrected H preview and full-video manifests from live capabilities."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'exports/frontline-vi-vow-eight-v1/production-v3'
UNITY = Path('/Users/lyu/Documents/project/game/projects/jcc/client')
sys.path.insert(0, str(UNITY / 'Tools/Production'))
from episode_package import create_package  # noqa: E402

timeline = json.loads((OUT / 'content-pipeline/timeline.json').read_text())
caps = json.loads((OUT / 'capabilities.json').read_text())
tiers = {tier['dps']: tier for tier in timeline['tiers']}
events = {(event['dps'], event['build']): event for event in timeline['events']}
result = next(segment for segment in timeline['segments'] if segment['kind'] == 'result')
points = [
    dict(id='cover', time=1.5),
    dict(id='intro', time=timeline['coverSeconds'] + 1.0),
    dict(id='first-tier', time=(tiers[1750]['battleStart'] + tiers[1750]['battleEnd']) / 2),
    dict(id='all-pass-1750', time=tiers[1750]['battleEnd'] + 1.0),
    dict(id='H-before-death', time=events[1800, 'H']['at'] - 0.1),
    dict(id='H-after-death', time=events[1800, 'H']['at'] + 1.0),
    dict(id='H-settled', time=tiers[1800]['battleEnd'] + 3.2),
    dict(id='seven-pass-1850', time=tiers[1850]['battleEnd'] + 0.2),
    dict(id='F-after-death', time=events[1900, 'F']['at'] + 1.0),
    dict(id='F-settled', time=tiers[1900]['battleEnd'] + 3.2),
    dict(id='E-settled', time=tiers[2000]['battleEnd'] + 1.0),
    dict(id='D-G-settled', time=tiers[2050]['battleEnd'] + 3.2),
    dict(id='B-C-settled', time=tiers[2100]['battleEnd'] + 3.2),
    dict(id='page-turn-half', time=tiers[2150]['battleStart'] + 0.75),
    dict(id='solo-2150', time=tiers[2150]['battleEnd'] + 0.1),
    dict(id='A-2200-pass', time=tiers[2200]['battleEnd'] + 0.1),
    dict(id='A-2250-death', time=events[2250, 'A']['at'] + 1.0),
    dict(id='result', time=result['start'] + 3.0),
    dict(id='ending', time=timeline['duration'] - 0.1),
]
preview = create_package(OUT / 'replay.json', OUT / 'preview-package.json', caps,
                         'vi-vow-eight-shield-preview-v3', points)
video = create_package(OUT / 'replay.json', OUT / 'video-package.json', caps,
                       'vi-vow-eight-shield-video-v3', points,
                       video=dict(fps=30, startFrame=0, frameCount=timeline['frames']))
print(json.dumps(dict(previewCount=len(preview['previewFrames']),
                      frames=video['video']['frameCount'],
                      fingerprint=video['rendererFingerprint']), ensure_ascii=False))
