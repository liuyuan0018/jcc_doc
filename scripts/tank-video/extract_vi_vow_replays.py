"""Extract selected v3 Vi comparison tiers and verify archived settlements."""
import hashlib
import json
import sys
from pathlib import Path

CONTENT = Path(__file__).resolve().parents[2]
OUTPUT = CONTENT / 'exports/frontline-vi-vow-eight-v1'
ARCHIVE = Path('/Volumes/Apple/Codex/art-assets/金铲铲/exports/frontline-episode-01-rerun-v3')
sys.path.insert(0, str(ARCHIVE))
import archive  # noqa: E402

evidence_path = CONTENT / 'research/vi-vow-topic-20260923/evidence.json'
evidence = json.loads(evidence_path.read_text())
assert evidence['modelRevision'] == archive.MANIFEST['producer']['mechanicsRevision']
for rel, expected in evidence['sourceHashes'].items():
    assert hashlib.sha256((ARCHIVE / rel).read_bytes()).hexdigest() == expected

item_names = {
    5: '饮血剑', 9: '鬼索的狂暴之刃', 22: '圣盾使的誓约',
    27: '石像鬼石板甲', 33: '狂徒铠甲',
}
builds = []
report = []
for key, selected in evidence['builds'].items():
    summary = selected['summary']
    config_id = summary['id']
    tiers = range(1850, min(2250, summary['failedDps']) + 1, 50)
    chain = []
    for dps in tiers:
        out = archive.replay(config_id, dps)
        expected = next(stage['result'] for stage in selected['stages'] if stage['dps'] == dps)
        assert out['result']['frame'] == expected['frame']
        assert out['result']['alive'] == expected['alive']
        # Importer consumes six compact frame columns and separate v3 telemetry.
        out['frames'] = [[f[0], f[1], f[2], f[3], f[4], f[17]] for f in out['frames']]
        assert bool(out['frames'][-1][5]) == bool(expected['alive'])
        chain.append(out)
        report.append(dict(build=key, configurationId=config_id, dps=dps,
                           frame=expected['frame'], alive=expected['alive'],
                           presentationEvents=len(out['presentation']['events'])))
    builds.append(dict(key=key, label=key, items=summary['items'],
                       itemNames=[item_names[i] for i in summary['items']],
                       passedDps=summary['passedDps'], failedDps=summary['failedDps'],
                       failedFrame=summary['failedFrame'], chain=chain))

assert len(report) == 39, len(report)
assert next(x for x in report if x['build'] == 'H' and x['dps'] == 1900)['alive'] is False
payload = dict(schemaVersion=2, purpose='selected-8-comparison-video',
               hero=dict(name='蔚', star=3, cost=3, traits={'主宰': 6}, slots=6, scenario=149),
               aug=4, augLabel='单身板甲 · 独占一排',
               environment=evidence['environment'], source=dict(archive=str(ARCHIVE),
               mechanicsRevision=evidence['modelRevision'], evidence=str(evidence_path)),
               builds=builds)
source_path = OUTPUT / 'source-replays.json'
report_path = OUTPUT / 'replay-extraction-report.json'
for path in [source_path, report_path]:
    assert not path.exists(), f'Refusing overwrite: {path}'
source_path.write_text(json.dumps(payload, ensure_ascii=False, separators=(',', ':')))
report_path.write_text(json.dumps(dict(passed=True, stageCount=len(report),
                                       sourceSha256=hashlib.sha256(source_path.read_bytes()).hexdigest(),
                                       stages=report), ensure_ascii=False, indent=2) + '\n')
print(json.dumps(dict(passed=True, stageCount=len(report), source=str(source_path),
                      report=str(report_path)), ensure_ascii=False))
