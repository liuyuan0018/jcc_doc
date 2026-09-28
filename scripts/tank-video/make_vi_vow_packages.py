"""Create this episode's Unity preview and full-video packages from current capabilities."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'exports/frontline-vi-vow-eight-v1'
UNITY = Path('/Users/lyu/Documents/project/game/projects/jcc/client')
sys.path.insert(0, str(UNITY / 'Tools/Production'))
from episode_package import create_package  # noqa: E402

timeline = json.loads((OUT / 'content-pipeline/timeline.json').read_text())
caps = json.loads((OUT / 'capabilities-v2.json').read_text())
tiers = {t['dps']:t for t in timeline['tiers']}
events = {(e['dps'],e['build']):e for e in timeline['events']}
result = next(s for s in timeline['segments'] if s['kind']=='result')
points = [
    dict(id='cover-subtitle',time=1.5),
    dict(id='cover-last',time=timeline['coverSeconds']-1/30),
    dict(id='intro',time=timeline['coverSeconds']+1.0),
    dict(id='first-tier',time=(tiers[1850]['battleStart']+tiers[1850]['battleEnd'])/2),
    dict(id='H-before-death',time=events[(1900,'H')]['at']-0.1),
    dict(id='H-after-death',time=events[(1900,'H')]['at']+0.1),
    dict(id='F-H-settled',time=tiers[1900]['battleEnd']+1.0),
    dict(id='E-settled',time=tiers[2000]['battleEnd']+1.0),
    dict(id='D-G-settled',time=tiers[2050]['battleEnd']+1.0),
    dict(id='B-C-settled',time=tiers[2100]['battleEnd']+1.0),
    dict(id='page-turn-half',time=tiers[2150]['battleStart']+0.75),
    dict(id='solo-2150',time=tiers[2150]['battleEnd']+0.1),
    dict(id='A-2200-pass',time=tiers[2200]['battleEnd']+0.1),
    dict(id='A-2250-death',time=events[(2250,'A')]['at']+0.1),
    dict(id='result',time=result['start']+3),
    dict(id='ending',time=timeline['duration']-0.1),
]
preview = create_package(OUT/'replay.json', OUT/'preview-package-v2.json', caps,
                         'vi-vow-eight-preview-v2',points)
video = create_package(OUT/'replay.json', OUT/'video-package-v2.json', caps,
                       'vi-vow-eight-video-v2',points,
                       video=dict(fps=30,startFrame=0,frameCount=timeline['frames']))
print(json.dumps(dict(previewCount=len(preview['previewFrames']),frames=video['video']['frameCount'],
                      fingerprint=video['rendererFingerprint'],points=points),ensure_ascii=False))
