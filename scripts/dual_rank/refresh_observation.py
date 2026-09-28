#!/usr/bin/env python3
"""Bind the maintained spider/Azir observation to one coherent DataJ snapshot."""
from argparse import ArgumentParser
from copy import deepcopy
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json

from model import ROOT, PipelineError, config, digest, metric, need, read_json, snapshot, write_json


def response(url):
    request = Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'})
    with urlopen(request, timeout=25) as opened:
        body = json.load(opened)
    need(body.get('success') is True and body.get('code') == 200 and body.get('data') is not None,
         'DataJ response failed: ' + url)
    return body


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', required=True)
    parser.add_argument('--date', required=True, type=date.fromisoformat)
    args = parser.parse_args()
    cfg = config()
    snap = snapshot(args.snapshot, cfg)
    need(not snap['test_fixture'], 'Test fixture cannot become a dated observation')
    need(args.date >= date.fromisoformat('2026-09-28'), 'Use the existing dated observations for earlier days')
    summary = snap['summary']
    base = cfg['source']['base_url']
    query = urlencode({'setId': cfg['source']['set_id'], 'gameVersion': cfg['source']['version']})
    summary_url = base + '/api/web/stats/summary?' + query
    comp_url = base + '/api/web/comp/120?' + query

    before = response(summary_url)['data']
    need(before == summary, 'Snapshot is no longer the current DataJ summary')
    comp_response = response(comp_url)
    after = response(summary_url)['data']
    need(after == before, 'DataJ updated while fetching the observation')
    comp = comp_response['data']
    need(str(comp.get('compId')) == '120' and comp.get('name') == '黑暗仪式蜘蛛'
         and comp.get('dataMode') == 'stats' and len(comp.get('heroes', [])) == 9,
         'Black Ritual Spider identity or board changed')
    metric(comp, 'comp', 'comp120', comp_id='120', name=comp['name'])

    record_dir = ROOT / 'research' / f'special-{args.date:%Y%m%d}'
    record_dir.mkdir(parents=True, exist_ok=True)
    comp_file = record_dir / 'comp120.json'
    write_json(comp_file, comp_response)
    write_json(record_dir / 'requests.json', {
        'snapshot': snap['folder'], 'summary_url': summary_url, 'comp_url': comp_url,
        'fetched_at': datetime.now(timezone.utc).isoformat(),
        'source_updated_at': summary['dataUpdatedAt'],
    })

    observation = deepcopy(cfg['dated_observations']['2026-09-26'])
    observation['source_updated_at'] = summary['dataUpdatedAt']
    observation['source_comp_file'] = str(comp_file.relative_to(ROOT))
    observation['source_comp_sha256'] = digest(comp_file.read_bytes())
    cfg['dated_observations'][args.date.isoformat()] = observation
    write_json(ROOT / 'config/dual-rank.json', cfg)
    return {
        'date': args.date.isoformat(), 'source_updated_at': summary['dataUpdatedAt'],
        'spider_sample': comp['sampleCount'], 'spider_top4': comp['top4Rate'],
        'azir_observation': True, 'source_file': str(comp_file),
    }


if __name__ == '__main__':
    try:
        print(json.dumps(main(), ensure_ascii=False))
    except Exception as error:
        raise SystemExit(str(error))
