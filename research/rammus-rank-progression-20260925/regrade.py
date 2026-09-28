"""Regrade verified stage evidence; never run or modify combat simulation."""
import collections
import hashlib
import json
from pathlib import Path

ROOT = Path('/Users/lyu/Documents/ChatGPT/金铲铲')
SOURCE = ROOT / 'research/rammus-rank-integer-20260925'
OUT = Path(__file__).parent
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
manifest = json.loads((SOURCE / 'manifest.json').read_text())
old = json.loads((SOURCE / 'ranking.json').read_text())
assert manifest['status'] == 'verified' and old['poolSize'] == 8365
stages = {}
for path in sorted((SOURCE / 'raw').glob('*.jsonl')):
    assert sha(path) == manifest['rawHashes'][path.name]
    for line in path.read_text().splitlines():
        r = json.loads(line)
        stages[r['id']] = r

def alive(r, dps):
    return any(lo <= dps <= hi for lo, hi in r['passRanges'])

graded = []
for r in old['all']:
    scan = stages[r['id']]
    assert scan['passRanges'] == r['passRanges']
    fail = next(d for d in range(300, 2501, 50) if not alive(scan, d))
    coarse = fail - 50 if fail > 300 else 0
    assert coarse == r['coarsePassedDps'], (r['id'], coarse, r['coarsePassedDps'])
    # Refine only the final coarse bracket, ascending from its known passing endpoint.
    # Earlier coarse tiers remain the shared Main/Results protocol.
    score = 0 if coarse == 0 else next(d for d in range(coarse + 1, fail + 1) if not alive(scan, d)) - 1
    assert coarse <= score < fail
    if score:
        assert alive(scan, score) and not alive(scan, score + 1)
        assert all(alive(scan, d) for d in range(coarse, score + 1))
    graded.append(dict(id=r['id'], items=r['items'], augment=r['augment'], scenario=r['scenario'],
                       coarsePassedDps=coarse, coarseFirstFailDps=fail, passedDps=score,
                       refinedFirstFailDps=score + 1 if score else fail,
                       previousMaximumPass=r['highestPass']))

counts = collections.Counter(r['passedDps'] for r in graded)
for r in graded:
    r.update(rank=1 + sum(n for s, n in counts.items() if s > r['passedDps']), tieCount=counts[r['passedDps']])
graded.sort(key=lambda r: (-r['passedDps'], r['items'], r['augment']))
selected_ids = {r['id'] for r in old['selected']}
selected = [r for r in graded if r['id'] in selected_ids]
assert len(graded) == 8365 and len(selected) == 64
replay = json.loads((SOURCE / 'replay.json').read_text())
entries = {e['id']: e for e in replay['results']['entries']}
for r in selected:
    entries[r['id']].update(rank=r['rank'], passedDps=r['passedDps'], isTop=r['rank'] == 1)
replay.update(id='rammus-results64-progression-v4', source='Verified archived stages; 300+50 DPS until first failure; ascending step-1 refinement only inside the final coarse bracket, stop on first failure; no post-failure recovery contributes to score')
replay['results'].update(entries=[entries[r['id']] for r in selected],
                         barScaleDps=((graded[0]['passedDps'] + 99) // 100) * 100,
                         footnote='固定条件模拟 · 逐档加压至首次失败 · 最后两档间细分',
                         subtitle='8365种方案中，精选64套对比')

# Every visible battle, failure and survivor in Main must agree with the archived stages.
main = json.loads((ROOT / 'exports/frontline-rammus-eight-v1/production-v3/replay.json').read_text())
def equipment_key(eq):
    icons = []
    for e in eq:
        icons.extend([e['iconKey']] * (2 if '×2' in e['label'] else 1))
    return tuple(sorted(icons))
lookup = {equipment_key(e['equipment']): e['id'] for e in entries.values() if not e.get('augments')}
byid = {r['id']: r for r in graded}
checks = []
for card in main['cards']:
    key = lookup[equipment_key(card['equipment'])]
    row = byid[key]
    runs = [r for r in main['runs'] if r['cardId'] == card['id']]
    for run in runs:
        dps = int(run['id'].split(':')[1])
        assert bool(run['samples'][-1]['alive']) == alive(stages[key], dps), (key, dps)
    failed = [int(r['id'].split(':')[1]) for r in runs if not r['samples'][-1]['alive']]
    assert min(failed) == row['coarseFirstFailDps']
    checks.append(dict(card=card['id'], id=key, equipment=[e['label'] for e in card['equipment']],
                       coarsePass=row['coarsePassedDps'], firstFail=row['coarseFirstFailDps'],
                       refinedScore=row['passedDps'], rank=row['rank'], verifiedRuns=len(runs)))

report = dict(verified=True, criterion='first-failure progression with final-bracket refinement',
              protocol=dict(start=300, coarseStep=50, refinedStep=1, stopOnFirstFailure=True),
              poolSize=len(graded), selectedCount=len(selected), unchangedSelection=True,
              simulationCalls=0, sourceRankingSha256=sha(SOURCE / 'ranking.json'),
              sourceManifestSha256=sha(SOURCE / 'manifest.json'),
              mainChecks=checks, selected=selected, all=graded,
              selectedChangedScores=sum(r['passedDps'] != r['previousMaximumPass'] for r in selected),
              selectedTieGroups={str(s): sum(r['passedDps'] == s for r in selected)
                                 for s in {r['passedDps'] for r in selected}
                                 if sum(r['passedDps'] == s for r in selected) > 1})
(OUT / 'ranking.json').write_text(json.dumps(report, ensure_ascii=False))
(OUT / 'replay.json').write_text(json.dumps(replay, ensure_ascii=False))
(OUT / 'main-consistency.json').write_text(json.dumps(checks, ensure_ascii=False, indent=2))
print(json.dumps({k: v for k, v in report.items() if k not in ['all', 'selected']}, ensure_ascii=False, indent=2))
