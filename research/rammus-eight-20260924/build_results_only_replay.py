#!/usr/bin/env python3
"""Make a small, truthful Unity replay for the eight ranked result pages."""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path('/Users/lyu/Documents/project/game/projects/jcc/client/Assets/Res/Replay/rammus-eight-results-v1.json')
DEST = SOURCE.with_name('rammus-results-pages-v1.json')
REPORT = ROOT / 'exports/frontline-rammus-eight-v1/production-v1/results-pages-source.json'


def main():
    full = json.loads(SOURCE.read_text())
    start = next(segment['start'] for segment in full['segments'] if segment['layout'] == 'results')
    pages = [copy.deepcopy(s) for s in full['segments'] if s['layout'] == 'results']
    assert len(pages) == 8 and abs(full['duration'] - start - 40) < 1e-7
    for page in pages:
        page['start'] = round(page['start'] - start, 9)
        page['end'] = round(page['end'] - start, 9)
    captions = [copy.deepcopy(c) for c in full['captions'] if c['start'] >= start]
    assert len(captions) == 8
    for cue in captions:
        cue['start'] = round(cue['start'] - start, 9)
        cue['end'] = round(cue['end'] - start, 9)
    replay = {key: full[key] for key in ('schemaVersion', 'title', 'conditions', 'footnote', 'cards', 'runs', 'results')}
    replay.update(id='rammus-results-pages-v1', source=full['source'] + '; results-only Unity render',
                  isFixture=False, duration=40.0, segments=pages, captions=captions)
    # The rendering contract requires one card and run; result pages never render them.
    replay['cards'] = full['cards'][:1]
    replay['runs'] = full['runs'][:1]
    DEST.write_text(json.dumps(replay, ensure_ascii=False, separators=(',', ':')))
    digest = hashlib.sha256(DEST.read_bytes()).hexdigest()
    REPORT.write_text(json.dumps({'fullReplay': str(SOURCE), 'fullReplaySha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                                  'resultsReplay': str(DEST), 'resultsReplaySha256': digest,
                                  'fullStartSeconds': start, 'durationSeconds': 40.0, 'pages': len(pages),
                                  'entries': len(replay['results']['entries'])}, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'path': str(DEST), 'sha256': digest, 'bytes': DEST.stat().st_size}, ensure_ascii=False))


if __name__ == '__main__':
    main()
