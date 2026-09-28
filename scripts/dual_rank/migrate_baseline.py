"""One-time extraction of the accepted 2026-09-20 designs; not a daily updater."""
from pathlib import Path
import hashlib
import json
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'outputs/dual-rank-20260920'
OUT = ROOT / 'templates/dual-rank'
NS = '{http://www.w3.org/2000/svg}'
ET.register_namespace('', NS[1:-1])


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    config_path = ROOT / 'config/dual-rank.json'
    if config_path.exists():
        raise SystemExit('Already migrated; do not overwrite maintained templates/configuration.')
    load = lambda n: json.loads((DATA / f'{n}.json').read_text())['data']
    rank = {str(x['compId']): x for x in load('rank')}
    names = {x['name']: str(x['compId']) for x in load('rank')}
    specs = [
        ('kennen', '花妖转凯南', '112', 'carrier', 'special', 41810, '5453'),
        ('dragon', '猎人转巨龙', '89', 'carrier', 'special', 41816, '5458'),
        ('camille', '暗爪卡蜜尔', '115', 'carrier', 'special', 6073, '1505'),
        ('kayle', '护臂天使', '88', 'hero_item', 'kayle-gear', 6084, '2512'),
        ('khazix', '花妖转螳螂', '116', 'hero_item', 'khazix-gear', 41810, '3505'),
        ('kog', '神谕大嘴', '119', 'hero_triple', 'kog-ad-equips', [2001, 2045, 2046], '3512'),
    ]
    cold = [dict(zip(['id', 'name', 'comp_id', 'scope', 'source_key', 'equip', 'hero_id'], x)) for x in specs]
    note_manifest = json.loads((DATA / 'manifest.json').read_text())
    requests = json.loads((DATA / 'requests.json').read_text())
    from urllib.parse import urlparse, parse_qs
    endpoints = {}
    for req in requests:
        url = urlparse(req['url'])
        endpoints[req['key']] = {'path': url.path, 'query': {k: v[0] for k, v in parse_qs(url.query).items() if k not in ['setId', 'gameVersion']}}
    config = {
        'schema_version': 1,
        'source': {'base_url': 'https://www.dataj.cc', 'set_id': 18, 'version': '18.2a',
                   'versions_path': '/api/web/gamedata/gameVersion', 'endpoints': endpoints},
        'baseline': {'snapshot': 'outputs/dual-rank-20260920', 'manifest': 'outputs/dual-rank-20260920/manifest.json',
                     'accepted_date': '2026-09-20', 'user_feedback': '看起来好了'},
        'regular': {'ids': ['112','104','89','116','100','113','99','106','109'], 'reserve_ids': ['119'],
                    'sort': 'top4Rate', 'row_y': 309, 'row_step': 123},
        'cold': cold,
        'review': {'large_top4_change_pp': 5, 'description': 'Change detector only; not an evidence/sample-size threshold for recommending a build.'},
        'notes': {n['key']: {'note_id': n['note_id'], 'title_template': n['title'].replace('9.20', '{{date.short}}'),
                           'topics': n['topics'], 'collection': n['saved_readback']['collection'],
                           'preserve_live_topics_and_settings': True} for n in note_manifest['notes']},
        'cards': [],
    }
    bindings = {}
    def bind(before, after):
        bindings[before] = after
    bind('封面64.4%是体系统计，两条分支未分别排强度。', '封面{{regular.112.top4Rate:.1f}}%是体系统计，两条分支未分别排强度。')
    bind('裁决转＋青龙刀＋虚空杖：297样本，前四45.79%。', '裁决转＋青龙刀＋虚空杖：{{extra.zyra.sampleCount}}样本，前四{{extra.zyra.top4Rate:.2f}}%。')
    bind('艾希带转：3,502样本 / 前四74.76%，非体系胜率。', '艾希带转：{{extra.ashe.sampleCount:,}}样本 / 前四{{extra.ashe.top4Rate:.2f}}%，非体系胜率。')
    bind('九人口运营 / 966局样本', '九人口运营 / {{regular.113.sampleCount}}局样本')
    bind('神谕体系：2223样本 · 前四49.21% · 登顶9.76% · 均名4.51', '神谕体系：{{regular.119.sampleCount}}样本 · 前四{{regular.119.top4Rate:.2f}}% · 登顶{{regular.119.topRate:.2f}}% · 均名{{regular.119.avgPlacement:.2f}}')
    bind('对应三件套分项：253样本 · 前四57.71% · 登顶11.46%', '对应三件套分项：{{cold.kog.sampleCount}}样本 · 前四{{cold.kog.top4Rate:.2f}}% · 登顶{{cold.kog.topRate:.2f}}%')
    bind('均名4.08；携装样本有成型偏差，不能当作开局硬玩的成功率。', '均名{{cold.kog.avgPlacement:.2f}}；携装样本有成型偏差，不能当作开局硬玩的成功率。')
    bind('18.2a版本样本88,056 · 数据截至9/20 03:26。', '{{source.version}}版本样本{{source.games:,}} · 数据截至{{source.short_time}}。')
    bind('184个携装样本，暂不定强度档。', '{{cold.kayle.sampleCount}}个携装样本，暂不定强度档。')
    bind('172个携装样本，先当试玩线索。', '{{cold.khazix.sampleCount}}个携装样本，先当试玩线索。')
    bind('地狱火转巨龙也可看：545样本，前四80.37%。', '地狱火转巨龙也可看：{{extra.dragon.sampleCount}}样本，前四{{extra.dragon.top4Rate:.2f}}%。')
    bind('全体系前四仅47.52%，普通装备不能照搬。', '全体系前四仅{{regular.115.top4Rate:.2f}}%，普通装备不能照搬。')
    bind('184个英雄携装样本，没有锁定整套阵容。', '{{cold.kayle.sampleCount}}个英雄携装样本，没有锁定整套阵容。')
    bind('别按70.65%当稳定上分结论，先小范围试。', '别按{{cold.kayle.top4Rate:.2f}}%当稳定上分结论，先小范围试。')
    bind('172个英雄携装样本，不能和上面三套直排。', '{{cold.khazix.sampleCount}}个英雄携装样本，不能和上面三套直排。')
    for track, folder in [('regular','S18常规榜-20260920'),('cold','S18冷门榜-20260920')]:
        (OUT/track).mkdir(exist_ok=True)
        for path in sorted((ROOT/'exports'/folder).glob('*.svg')):
            root = ET.parse(path).getroot()
            name = path.stem.split('-',1)[1]
            kind = 'cover' if path.name.startswith('01-') else 'guide' if name == '今天怎么选' else 'detail'
            cid = names.get(name) if track == 'regular' else next((c['comp_id'] for c in cold if c['name'] == name), None)
            cold_id = next((c['id'] for c in cold if c['name'] == name), None) if track == 'cold' else None
            if kind == 'cover':
                group = root.find(NS+'g'); children = list(group)
                height = '111' if track == 'regular' else '158'
                starts = [i for i,e in enumerate(children) if e.tag == NS+'rect' and e.get('x')=='40' and e.get('width')=='1000' and e.get('height')==height]
                tail = next(i for i in range(starts[-1]+1,len(children)) if children[i].tag==NS+'g') if track=='regular' else len(children)
                for start,end in zip(starts,starts[1:]+[tail]):
                    nodes = children[start:end]; texts = [e for n in nodes for e in n.iter(NS+'text')]
                    title = next(e for e in texts if e.get('x')=='166')
                    row_name = title.text.split(' · ')[0]
                    key = names[row_name] if track=='regular' else next(c['id'] for c in cold if c['name']==row_name)
                    prefix = track+'.'+key
                    nodes[0].set('data-row',key)
                    if track=='regular':
                        title.text = '{{'+prefix+'.label}}'
                        config['regular'].setdefault('labels',{})[key] = {'base_name':row_name,'baseline_tier':rank[key]['tier'],'show_tier': ' · ' in (next(e for e in ET.parse(path).getroot().iter(NS+'text') if e.text and e.text.split(' · ')[0]==row_name).text)}
                    next(e for e in texts if e.text and e.text.startswith('均排')).text = '{{'+prefix+'.metadata}}'
                    next(e for e in texts if e.get('x')=='665').text = '{{'+prefix+'.top4Rate:.1f}}%'
                    next(e for e in texts if e.get('x')=='861').text = '{{'+prefix+'.topRate:.1f}}%'
                if track=='regular':
                    g = next(e for e in group if e.tag==NS+'g')
                    for e in g.iter(NS+'text'):
                        if e.text and e.text.startswith('均排'): e.text='{{regular.119.metadata}}'
                        elif e.get('x')=='665': e.text='{{regular.119.top4Rate:.1f}}%'
                        elif e.get('x')=='861': e.text='{{regular.119.topRate:.1f}}%'
            for e in root.iter(NS+'text'):
                if not e.text: continue
                text=bindings.get(e.text,e.text)
                if cold_id and cold_id!='kog' and text.startswith('前四 '):
                    prefix='cold.'+cold_id
                    text='前四 {{'+prefix+'.top4Rate:.2f}}% · 登顶 {{'+prefix+'.topRate:.2f}}% · 均名 {{'+prefix+'.avgPlacement:.2f}} · {{'+prefix+'.sampleCount}}样本'
                if re.fullmatch(r'\d{2} / \d{2}',text): text='{{page.number}} / {{page.total}}'
                text=text.replace('2026.09.20','{{date.full}}').replace('09.20 /','{{date.padded}} /').replace('9.20更新','{{date.short}}更新').replace('9/20 03:26','{{source.short_time}}').replace('03:26数据','{{source.time}}数据').replace('18.2a','{{source.version}}')
                e.text=text
            template = OUT/track/(name+'.svg')
            template.write_text(ET.tostring(root,encoding='unicode'))
            config['cards'].append({'track':track,'kind':kind,'name':name,'comp_id':cid,'cold_id':cold_id,
                 'template':str(template.relative_to(ROOT)),'baseline_svg':str(path.relative_to(ROOT)),
                 'baseline_png':str(path.with_suffix('.png').relative_to(ROOT)),
                 'baseline_svg_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                 'baseline_png_sha256':hashlib.sha256(path.with_suffix('.png').read_bytes()).hexdigest(),
                 'width':int(root.get('width')),'height':int(root.get('height'))})
    # The fixed prose is already written for players. Only facts and order become slots.
    body=(DATA/'regular-body.txt').read_text()
    start=body.index('地狱火95｜');end=body.index('\n\n地狱火轮子',start)
    body=body[:start]+'{{regular_rows}}'+body[end:]
    body=body.replace('57.71%（253样本）','{{cold.kog.top4Rate:.2f}}%（{{cold.kog.sampleCount}}样本）')
    (OUT/'regular-body.txt').write_text(body.replace('9月20日','{{date.chinese}}').replace('9/20 03:26','{{source.short_time}}').replace('18.2a','{{source.version}}'))
    body=(DATA/'cold-body.txt').read_text()
    for before,after in [
        ('84.79%（401样本）','{{cold.kennen.top4Rate:.2f}}%（{{cold.kennen.sampleCount}}样本）'),
        ('75.34%（365）','{{cold.dragon.top4Rate:.2f}}%（{{cold.dragon.sampleCount}}）'),
        ('69.75%（357）','{{cold.camille.top4Rate:.2f}}%（{{cold.camille.sampleCount}}）'),
        ('70.65%（184样本）','{{cold.kayle.top4Rate:.2f}}%（{{cold.kayle.sampleCount}}样本）'),
        ('59.30%（172）','{{cold.khazix.top4Rate:.2f}}%（{{cold.khazix.sampleCount}}）'),
        ('49.21%（2223样本）','{{regular.119.top4Rate:.2f}}%（{{regular.119.sampleCount}}样本）'),
        ('57.71%（253）','{{cold.kog.top4Rate:.2f}}%（{{cold.kog.sampleCount}}）')]:
        assert before in body,before
        body=body.replace(before,after)
    for c in cold:
        detail=load('comp119' if c['comp_id']=='119' else 'comp-'+c['comp_id'])
        body=body.replace(detail['gameCode'].split('#')[-1],'{{codes.'+c['comp_id']+'}}')
    (OUT/'cold-body.txt').write_text(body.replace('9月20日','{{date.chinese}}').replace('9/20 03:26','{{source.short_time}}').replace('18.2a','{{source.version}}'))
    config_path.parent.mkdir(exist_ok=True)
    config_path.write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n')
    state=ROOT/'state/dual-rank.json';state.parent.mkdir(exist_ok=True)
    if not state.exists():
        state.write_text(json.dumps({'schema_version':1,'published_manifest':config['baseline']['manifest'],
                                    'published_snapshot':config['baseline']['snapshot'],'latest_package':None},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'templates':len(config['cards']),'config':str(config_path)},ensure_ascii=False))


if __name__ == '__main__':
    main()
