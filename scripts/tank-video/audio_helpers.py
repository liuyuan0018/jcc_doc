"""Audio-only helpers for cached narration and mixing. No video rendering."""
import hashlib
import json
import math
import re
import subprocess
from array import array
from pathlib import Path
import imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()
SR = 48000
PAN = 1 / math.sqrt(2)

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def save_json(path, data): Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')

def ff(args):
    return subprocess.run([FF, '-hide_banner', '-loglevel', 'error', '-y', *args],
                          capture_output=True, check=True)

def pcm(path, channels=2, filters=None):
    args = ['-i', str(path), '-vn']
    if filters: args += ['-af', filters]
    args += ['-ar', str(SR), '-ac', str(channels), '-f', 'f32le', 'pipe:1']
    out = array('f'); out.frombytes(ff(args).stdout); return out

def wav24(path, samples, channels=2):
    raw = Path(str(path) + '.f32'); raw.write_bytes(samples.tobytes())
    ff(['-f', 'f32le', '-ar', str(SR), '-ac', str(channels), '-i', str(raw),
        '-c:a', 'pcm_s24le', str(path)]); raw.unlink()

def speech_trim(samples):
    active = [i for i in range(0, len(samples), 480)
              if max(map(abs, samples[i:i + 480]), default=0) > 130 / 32768]
    assert active, 'silent TTS clip'
    start = max(0, active[0] - round(.05 * SR))
    end = min(len(samples), active[-1] + 480 + round(.09 * SR))
    return samples[start:end]

def fade_edges(samples, ms=8):
    n = round(ms / 1000 * SR)
    for i in range(n):
        w = .5 - .5 * math.cos(math.pi * i / (n - 1))
        samples[i] *= w; samples[-1 - i] *= w
    return samples

def loudness(path, filters=''):
    chain = (filters + ',' if filters else '') + 'loudnorm=I=-23:TP=-3:LRA=11:print_format=json'
    log = subprocess.run([FF, '-hide_banner', '-i', str(path), '-vn', '-af', chain,
                          '-f', 'null', '-'], capture_output=True, text=True, check=True).stderr
    return json.loads(re.search(r'\{\s*"input_i".*?\}', log, re.S).group())
