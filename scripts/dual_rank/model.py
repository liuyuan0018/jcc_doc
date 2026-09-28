"""Validated source records and deterministic editorial data. No model calls."""
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from zoneinfo import ZoneInfo
import hashlib
import json
import math
import re

ROOT = Path(__file__).resolve().parents[2]
BJT = ZoneInfo('Asia/Shanghai')
STATE = ROOT / 'state/dual-rank.json'
SLOT = re.compile(r'\{\{([\w.]+)(?::([^{}]+))?\}\}')
METRICS = ('sampleCount', 'avgPlacement', 'top4Rate', 'topRate')
CONFIG_FIELDS = ('heroes', 'equips', 'traits', 'gameCode', 'dataMode')


class PipelineError(Exception):
    pass


def read_json(path):
    return json.loads(Path(path).read_text())


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(path)


def digest(value):
    if not isinstance(value, bytes):
        value = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
    return hashlib.sha256(value).hexdigest()


def config():
    return read_json(ROOT / 'config/dual-rank.json')


def need(condition, message):
    if not condition:
        raise PipelineError(message)


def one(items, predicate, description):
    matched = [x for x in items if predicate(x)]
    need(len(matched) == 1, f'{description}: expected one record, got {len(matched)}')
    return matched[0]


def metric(record, scope, source_key, **identity):
    out = {**identity, 'scope': scope, 'source_key': source_key}
    for key in METRICS:
        value = record.get(key)
        need(type(value) in (int, float) and math.isfinite(value), f'{source_key}: missing/invalid {key}')
        out[key] = value
    need(type(out['sampleCount']) is int and out['sampleCount'] > 0, f'{source_key}: no usable sample')
    need(1 <= out['avgPlacement'] <= 8, f'{source_key}: invalid placement')
    need(0 <= out['topRate'] <= out['top4Rate'] <= 100, f'{source_key}: invalid rates')
    return out


def snapshot(folder, cfg):
    folder = Path(folder).resolve()
    raw = {}
    hashes = {}
    semantic_hashes = {}
    for key in ['versions', *cfg['source']['endpoints']]:
        path = folder / f'{key}.json'
        need(path.is_file(), f'Missing snapshot file: {path}')
        envelope = read_json(path)
        need(envelope.get('success') is True and envelope.get('code') == 200 and envelope.get('data') is not None, f'{key}: unsuccessful source response')
        raw[key] = envelope['data']
        hashes[key] = digest(path.read_bytes())
        semantic_hashes[key] = digest(envelope['data'])
    summary = raw['summary']
    need(summary['setId'] == cfg['source']['set_id'], 'Season differs from maintained configuration')
    need(summary['gameVersion'] == cfg['source']['version'], 'Version differs from maintained configuration')
    when = datetime.fromisoformat(summary['dataUpdatedAt'].replace('Z', '+00:00'))
    need(when.tzinfo is not None, 'Source timestamp has no timezone')
    when = when.astimezone(BJT)
    latest = max(raw['versions'], key=lambda v: v['startTime'])
    need(latest['gameVersion'] == summary['gameVersion'], 'New version available; review builds before refreshing old version')
    selected_version = one(raw['versions'], lambda v: v['gameVersion'] == summary['gameVersion'], 'version')
    need(selected_version['battleCount'] == summary['gamesAnalyzed'], 'Snapshot count changed during collection')
    need(type(summary['gamesAnalyzed']) is int and summary['gamesAnalyzed'] > 0, 'Invalid source population')
    ranks = {}
    for row in raw['rank']:
        cid = str(row['compId'])
        need(cid not in ranks, f'Duplicate rank id: {cid}')
        ranks[cid] = row
    comp_ids = list(dict.fromkeys(cfg['regular']['ids'] + cfg['regular']['reserve_ids'] + [x['comp_id'] for x in cfg['cold']]))
    regular = {}
    comps = {}
    for cid in comp_ids:
        need(cid in ranks, f'Maintained lineup disappeared: {cid}')
        key = 'comp119' if cid == '119' else 'comp-' + cid
        row = raw[key]
        need(str(row['compId']) == cid, f'{key}: identity mismatch')
        for field in CONFIG_FIELDS:
            need(field in row, f'{key}: missing {field}')
        need(row['gameCode'] and len(row['gameCode'].split('#')) >= 3, f'{key}: invalid lineup code')
        # Layouts contain accepted editorial overrides. Source changes are detected,
        # never silently copied over those overrides.
        comps[cid] = {k: row[k] for k in CONFIG_FIELDS}
        regular[cid] = metric(ranks[cid], 'comp', 'rank', comp_id=cid, name=ranks[cid]['name'], tier=ranks[cid]['tier'], data_mode=ranks[cid].get('dataMode'))
    def carrier(eid, cid, hero=None):
        equip = one(raw['special'], lambda e: str(e['equipId']) == str(eid), f'equip {eid}')
        comp = one(equip['comps'], lambda c: str(c['compId']) == cid, f'equip {eid}/comp {cid}')
        c = comp.get('carrier')
        need(c is not None, f'equip {eid}/comp {cid}: missing carrier')
        if hero:
            need(str(c['heroId']) == hero, f'equip {eid}/comp {cid}: carrier changed')
        return c
    cold = {}
    for item in cfg['cold']:
        source = raw[item['source_key']]
        if item['scope'] == 'carrier':
            row = carrier(item['equip'], item['comp_id'], item['hero_id'])
        elif item['scope'] == 'hero_item':
            row = one(source, lambda e: str(e['equipId']) == str(item['equip']), item['id'])
        elif item['scope'] == 'hero_triple':
            need(str(source['compId']) == item['comp_id'] and str(source['heroId']) == item['hero_id'], 'Triple population identity changed')
            row = one(source['hero3Equips'], lambda e: set(map(str,e['equipIds'])) == set(map(str,item['equip'])), item['id'])
        else:
            raise PipelineError('Unsupported statistical scope: '+item['scope'])
        cold[item['id']] = metric(row, item['scope'], item['source_key'], comp_id=item['comp_id'], hero_id=item['hero_id'], equip=item['equip'], name=item['name'])
    ashe = raw['ashe-emblem']; zyra = raw['zyra-equips']
    need(str(ashe['compId']) == '112' and str(ashe['heroId']) == '5454', 'Ashe population identity changed')
    need(str(zyra['compId']) == '90' and str(zyra['heroId']) == '4512', 'Zyra population identity changed')
    extra = {
        'ashe': metric(one(ashe['heroEquips'], lambda e: str(e['id']) == '41806', 'Ashe emblem'), 'comp_hero_item', 'ashe-emblem'),
        'zyra': metric(one(zyra['hero3Equips'], lambda e: set(e['equipIds']) == {41818,2004,2011}, 'Zyra triple'), 'comp_hero_triple', 'zyra-equips'),
        'dragon': metric(carrier(41806, '89', '5458'), 'carrier', 'special'),
    }
    return {'folder': str(folder), 'test_fixture': (folder/'TEST_FIXTURE.json').exists(), 'summary': summary, 'when': when.isoformat(), 'regular': regular, 'cold': cold, 'extra': extra,
            'comps': comps, 'rank_ids': sorted(ranks), 'source_hashes': hashes, 'semantic_hashes': semantic_hashes}


def compare(old, new, cfg):
    changed = []
    review = []
    for cid, row in new['comps'].items():
        for field in CONFIG_FIELDS:
            if row[field] != old['comps'].get(cid, {}).get(field):
                review.append({'type': 'lineup_configuration', 'comp_id': cid, 'field': field})
        if new['regular'][cid]['data_mode'] != old['regular'][cid]['data_mode']:
            review.append({'type':'statistical_mode_changed','comp_id':cid})
    if new['summary']['dataUpdatedAt'] < old['summary']['dataUpdatedAt']:
        review.append({'type': 'source_time_regressed'})
    if new['summary']['gamesAnalyzed'] < old['summary']['gamesAnalyzed']:
        review.append({'type': 'source_population_decreased'})
    for section in ['regular', 'cold', 'extra']:
        for key, row in new[section].items():
            before = old[section][key]
            fields = {k: {'before': before[k], 'after': row[k]} for k in METRICS if row[k] != before[k]}
            if fields:
                changed.append({'scope': section, 'id': key, 'fields': fields})
            if row['sampleCount'] < before['sampleCount']:
                review.append({'type': 'sample_decreased', 'scope': section, 'id': key})
            if abs(row['top4Rate'] - before['top4Rate']) >= cfg['review']['large_top4_change_pp']:
                review.append({'type': 'large_rate_change', 'scope': section, 'id': key})
    order = lambda snap: sorted(cfg['regular']['ids'], key=lambda cid: (-snap['regular'][cid]['top4Rate'], cfg['regular']['ids'].index(cid)))
    before_order, after_order = order(old), order(new)
    ranks = [{'id': cid, 'name': new['regular'][cid]['name'], 'before':before_order.index(cid)+1,'after':after_order.index(cid)+1} for cid in after_order if before_order.index(cid) != after_order.index(cid)]
    tiers = [{'id':cid,'before':old['regular'][cid]['tier'],'after':new['regular'][cid]['tier']} for cid in new['regular'] if old['regular'][cid]['tier'] != new['regular'][cid]['tier']]
    if any(new['regular'][cid]['top4Rate'] > new['regular'][after_order[-1]]['top4Rate'] for cid in cfg['regular']['reserve_ids']):
        review.append({'type': 'reserve_exceeds_main', 'detail': 'Review reserve wording and body ordering claim'})
    reviewed=[]
    review_key=digest({'baseline':old['semantic_hashes'],'snapshot':new['semantic_hashes']})
    receipt=ROOT/'state/dual-rank-reviews'/f'{review_key}.json'
    if receipt.exists():
        decision=read_json(receipt)
        need(decision.get('review_key')==review_key and bool(decision.get('reason')), 'Invalid source review receipt')
        reviewed=[a for a in review if a['type']=='large_rate_change' and a in decision.get('accepted_alerts',[])]
        review=[a for a in review if a not in reviewed]
    return {'same_source': old['semantic_hashes'] == new['semantic_hashes'], 'statistics': changed,
            'ranking': ranks, 'tiers': tiers, 'review_required': review,
            'reviewed_alerts':reviewed,'review_receipt':str(receipt) if reviewed else None,
            'new_candidates': sorted(set(new['rank_ids']) - set(old['rank_ids'])),
            'order': after_order + cfg['regular']['reserve_ids']}


def expand(text, context):
    def replace(match):
        value = context
        for key in match[1].split('.'):
            need(isinstance(value, dict) and key in value, 'Missing template value: ' + match[1])
            value = value[key]
        fmt = match[2]
        if fmt and fmt.endswith('f'):
            precision = int(fmt.split('.')[1][:-1])
            value = Decimal(str(value)).quantize(Decimal(1).scaleb(-precision), rounding=ROUND_HALF_UP)
        return format(value, fmt or '')
    result = SLOT.sub(replace, text)
    need('{{' not in result and '}}' not in result, 'Unresolved template slot')
    return result


def context(snap, date, cfg):
    when = datetime.fromisoformat(snap['when'])
    need(date >= when.date(), 'Publication date is earlier than source data')
    ctx = {k: json.loads(json.dumps(snap[k])) for k in ['regular','cold','extra']}
    ctx['source'] = {'version':snap['summary']['gameVersion'], 'games':snap['summary']['gamesAnalyzed'],
                     'time':when.strftime('%H:%M'), 'short_time':f'{when.month}/{when.day} {when:%H:%M}'}
    ctx['date'] = {'full':date.strftime('%Y.%m.%d'),'short':f'{date.month}.{date.day}', 'padded':date.strftime('%m.%d'), 'chinese':f'{date.month}月{date.day}日'}
    ctx['codes'] = {cid: row['gameCode'].split('#')[-1] for cid,row in snap['comps'].items()}
    # One-day editorial observations are bound to an exact source timestamp.
    # A later refresh on that day must be reviewed instead of reusing stale rates.
    observation = cfg.get('dated_observations', {}).get(date.isoformat())
    if observation:
        need(observation['source_updated_at'] == snap['summary']['dataUpdatedAt'],
             'Dated observation source changed; review the observation before rebuilding')
        comp_path = ROOT / observation['source_comp_file']
        need(digest(comp_path.read_bytes()) == observation['source_comp_sha256'],
             'Dated composition source changed; review the composition before rebuilding')
        comp = read_json(comp_path)['data']
        need(comp['compId'] == observation['cold_card']['comp_id'] and comp['name'] == '黑暗仪式蜘蛛'
             and comp['dataMode'] == 'stats' and len(comp['heroes']) == 9,
             'Dated composition identity or board changed')
        spider = {key:comp[key] for key in ['name','sampleCount','avgPlacement','top4Rate','topRate','gameCode']}
        spider['metadata'] = f"均排{spider['avgPlacement']:.2f} · 样本{spider['sampleCount']}"
    ctx['cold_observation'] = {
        'cover_head': '更多上分阵容，主页看《常规阵容榜》',
        'cover_detail': '九套主选＋神谕大嘴备选｜站位、装备、阵容码',
        'body_section': '',
        'last_page': '7',
        'code_intro': '以下为基础框架码',
        'code_section': '',
        **(observation['cold'] if observation else {}),
    }
    if observation:
        ctx['cold_observation']['row'] = spider
        ctx['cold_observation']['code'] = spider['gameCode'].split('#')[-1]
        ctx['cold_observation']['last_page'] = '8'
        ctx['cold_observation']['code_intro'] = '以下为阵容码'
        ctx['cold_observation']['code_section'] = '\n\n黑暗仪式蜘蛛（9人口上限）\n' + spider['gameCode'].split('#')[-1]
        ctx['cold_observation']['body_section'] = expand(
            ctx['cold_observation'].pop('body_section_template'), ctx)
        if observation.get('bonus_card'):
            ctx['cold_observation']['last_page'] = '9'
            ctx['cold_observation']['body_section'] += observation['cold']['bonus_section']
        if observation.get('additional_cards'):
            ctx['cold_observation']['last_page'] = str(8 + bool(observation.get('bonus_card')) + len(observation['additional_cards']))
            ctx['cold_observation']['body_section'] += observation['cold'].get('additional_section', '')
    for section in ['regular','cold']:
        for key,row in ctx[section].items():
            sample = f"{row['sampleCount']:,}" if section=='regular' and key not in cfg['regular']['reserve_ids'] else str(row['sampleCount'])
            row['metadata'] = f"均排{row['avgPlacement']:.2f} · 样本{sample}"
            if section == 'regular' and key in cfg['regular']['labels']:
                label = cfg['regular']['labels'][key]
                row['label'] = label['base_name'] + (f" · {row['tier']}" if label['show_tier'] or row['tier'] != label['baseline_tier'] else '')
    order = sorted(cfg['regular']['ids'], key=lambda cid: (-ctx['regular'][cid]['top4Rate'], cfg['regular']['ids'].index(cid))) + cfg['regular']['reserve_ids']
    ctx['regular_rows'] = '\n\n'.join(f"{ctx['regular'][cid]['name']}｜前四{ctx['regular'][cid]['top4Rate']:.2f}%（{ctx['regular'][cid]['sampleCount']}）\n{ctx['codes'][cid]}" for cid in order)
    return ctx, order
