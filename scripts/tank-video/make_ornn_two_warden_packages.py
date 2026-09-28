"""Create five-tier Ornn preview and full-video packages from live capabilities."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'exports/frontline-ornn-two-warden-eight-v1/production-v1'
UNITY = Path('/Users/lyu/Documents/project/game/projects/jcc/client')
sys.path.insert(0, str(UNITY / 'Tools/Production'))
from episode_package import create_package  # noqa: E402

timeline = json.loads((OUT / 'content-pipeline/timeline.json').read_text())
caps = json.loads((OUT / 'capabilities.json').read_text())
tiers = {tier['dps']: tier for tier in timeline['tiers']}
events = {(event['dps'], event['build']): event for event in timeline['events']}
result = next(segment for segment in timeline['segments'] if segment['kind'] == 'result')
points = [
    dict(id='cover-clean', time=0.0),
    dict(id='cover-subtitle', time=1.4),
    dict(id='intro', time=timeline['coverSeconds'] + 1.0),
    dict(id='first-tier', time=(tiers[150]['battleStart'] + tiers[150]['battleEnd']) / 2),
    dict(id='all-pass-150', time=tiers[150]['battleEnd'] + .4),
    dict(id='C-before-death', time=events[200, 'C']['at'] - .1),
    dict(id='C-settled', time=events[200, 'C']['at'] + 1.2),
    dict(id='A-B-G-before-last-death', time=events[250, 'G']['at'] - .1),
    dict(id='A-B-G-settled', time=events[250, 'G']['at'] + 1.2),
    dict(id='O06-subtitle', time=next(cue['start'] for cue in timeline['cues'] if cue['id'] == 'O06') + 1.0),
    dict(id='F-settled', time=events[300, 'F']['at'] + 1.2),
    dict(id='D-E-H-pass-300', time=tiers[300]['battleEnd'] + 5.0),
    dict(id='H-before-350-death', time=events[350, 'H']['at'] - .1),
    dict(id='D-E-H-settled-350', time=tiers[350]['battleEnd'] + 3.2),
    dict(id='result', time=result['start'] + 3.0),
    dict(id='ending', time=timeline['duration'] - .1),
]
preview = create_package(OUT / 'replay.json', OUT / 'preview-package.json', caps,
                         'ornn-two-warden-preview-v1', points)
video = create_package(OUT / 'replay.json', OUT / 'video-package.json', caps,
                       'ornn-two-warden-video-v1', points,
                       video=dict(fps=30, startFrame=0, frameCount=timeline['frames']))
print(json.dumps(dict(previewCount=len(preview['previewFrames']),
                      frames=video['video']['frameCount'],
                      fingerprint=video['rendererFingerprint']), ensure_ascii=False))
