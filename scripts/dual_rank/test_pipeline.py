"""Regression and failure-injection tests for actual maintenance risks."""
from datetime import date
from pathlib import Path
import copy
import json
import shutil
import tempfile
import unittest
from unittest import mock
import xml.etree.ElementTree as ET

from model import ROOT, STATE, PipelineError, compare, config, context, expand, read_json, snapshot, write_json
from render import build, card_specs, verify
from publish import plan, record_readback, record_noop
from fetch import fetch


class PipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg=config();cls.base=ROOT/cls.cfg['baseline']['snapshot'];cls.snap=snapshot(cls.base,cls.cfg)
        cls.work=ROOT/'outputs/dual-rank-pipeline-validation';cls.work.mkdir(exist_ok=True)

    def fixture(self):
        folder=Path(tempfile.mkdtemp(dir=self.work,prefix='fixture-'))
        for key in ['versions',*self.cfg['source']['endpoints']]:shutil.copyfile(self.base/f'{key}.json',folder/f'{key}.json')
        write_json(folder/'TEST_FIXTURE.json',{'purpose':'Synthetic failure-injection only; never publish'})
        self.addCleanup(shutil.rmtree,folder)
        return folder

    def mutate(self,folder,key,fn):
        path=folder/f'{key}.json';data=read_json(path);fn(data['data']);write_json(path,data)

    def test_golden_body_title_and_all_pixels(self):
        folder=self.work/'baseline';m=build(self.snap,self.cfg,date(2026,9,20),folder,self.snap)
        verify(folder,self.cfg)
        self.assertEqual(len(m['visual']['identical']),19)
        self.assertFalse(m['visual']['needs_inspection'])
        for key in ['regular','cold']:
            for part in ['body','title']:
                actual=(folder/f'{key}-{part}.txt').read_bytes();expected=(self.base/f'{key}-{part}.txt').read_bytes()
                if part=='body':
                    expected=expected.replace('阵容码尚未做游戏内导入校验，导入后对照配图检查。'.encode(), '导入阵容码后，照配图检查站位和装备。'.encode())
                    expected=expected.replace('游戏内导入尚未校验，请对照配图调整：'.encode(), '导入后照配图调整：'.encode())
                    expected=expected.replace('运营为建议，尚无逐局实战复核。'.encode(), '看装备、来牌和血量决定转不转。'.encode())
                self.assertEqual(actual if part=='body' else actual.strip(),expected if part=='body' else expected.strip())

    def test_cache_and_noop_publish(self):
        folder=self.work/'cached';m=build(self.snap,self.cfg,date(2026,9,20),folder,self.snap)
        self.assertEqual(m['rendered'],0);self.assertEqual(m['cache_hits'],19)
        result=plan(folder,self.cfg,{'published_manifest':str(folder/'manifest.json')})
        self.assertEqual([x['action'] for x in result['actions']],['noop','noop'])

    def test_null_is_not_zero(self):
        folder=self.fixture();self.mutate(folder,'rank',lambda rows:next(x for x in rows if x['compId']=='112').update(top4Rate=None))
        with self.assertRaisesRegex(PipelineError,'missing/invalid top4Rate'):snapshot(folder,self.cfg)

    def test_duplicate_scope_is_not_silently_selected(self):
        folder=self.fixture();self.mutate(folder,'kayle-gear',lambda rows:rows.append(copy.deepcopy(next(x for x in rows if x['equipId']==6084))))
        with self.assertRaisesRegex(PipelineError,'expected one record'):snapshot(folder,self.cfg)

    def test_missing_lineup_code_rejected(self):
        folder=self.fixture();self.mutate(folder,'comp-112',lambda d:d.pop('gameCode'))
        with self.assertRaisesRegex(PipelineError,'missing gameCode'):snapshot(folder,self.cfg)

    def test_source_configuration_change_is_reviewed(self):
        folder=self.fixture();self.mutate(folder,'comp-112',lambda d:d['heroes'][0].update(position='3,1'))
        delta=compare(self.snap,snapshot(folder,self.cfg),self.cfg)
        self.assertIn({'type':'lineup_configuration','comp_id':'112','field':'heroes'},delta['review_required'])
        with self.assertRaisesRegex(PipelineError,'review required'):build(snapshot(folder,self.cfg),self.cfg,date(2026,9,20),self.work/'must-not-render',self.snap)

    def test_carrier_change_rejected(self):
        folder=self.fixture()
        def mutate(rows):
            e=next(e for e in rows if e['equipId']==41810);next(c for c in e['comps'] if c['compId']=='112')['carrier']['heroId']='5454'
        self.mutate(folder,'special',mutate)
        with self.assertRaisesRegex(PipelineError,'carrier changed'):snapshot(folder,self.cfg)

    def test_new_version_rejected(self):
        folder=self.fixture();self.mutate(folder,'versions',lambda rows:rows.insert(0,{**rows[0],'gameVersion':'18.3','startTime':'2026-09-21T00:00:00Z'}))
        with self.assertRaisesRegex(PipelineError,'New version'):snapshot(folder,self.cfg)

    def test_population_drop_and_large_swing_need_review(self):
        folder=self.fixture();self.mutate(folder,'rank',lambda rows:next(x for x in rows if x['compId']=='112').update(sampleCount=100,top4Rate=80))
        delta=compare(self.snap,snapshot(folder,self.cfg),self.cfg)
        self.assertTrue(any(x['type']=='sample_decreased' for x in delta['review_required']))
        self.assertTrue(any(x['type']=='large_rate_change' for x in delta['review_required']))

    def test_rounding(self):
        self.assertEqual(expand('{{r:.1f}}',{'r':70.65}),'70.7')
        with self.assertRaises(PipelineError):expand('{{missing}}',{})

    def test_spider_extension_is_source_bound_and_date_scoped(self):
        current=snapshot(ROOT/'outputs/dual-rank-snapshots/20260924-0317-8ca3252076a0',self.cfg)
        ctx,order=context(current,date(2026,9,24),self.cfg)
        self.assertEqual(ctx['cold_observation']['row']['sampleCount'],2714)
        self.assertEqual(ctx['cold_observation']['code'],read_json(ROOT/'research/special-20260924/comp120.json')['data']['gameCode'].split('#')[-1])
        self.assertEqual([c['name'] for c in card_specs(self.cfg,order,date(2026,9,24))[1][1]][-1],'黑暗仪式蜘蛛')
        next_day=snapshot(ROOT/'outputs/dual-rank-snapshots/20260925-0311-a1477f1d58f9',self.cfg)
        next_ctx,next_order=context(next_day,date(2026,9,25),self.cfg)
        self.assertEqual(next_ctx['cold_observation']['row']['sampleCount'],3553)
        self.assertEqual(len(card_specs(self.cfg,next_order,date(2026,9,25))[1][1]),8)
        cover=ROOT/'templates/dual-rank/cold/冷门构筑强度榜-蜘蛛.svg'
        cover_text='\n'.join(expand(e.text,next_ctx) for e in ET.parse(cover).getroot().iter('{http://www.w3.org/2000/svg}text') if e.text)
        self.assertIn('均排4.19 · 样本3553',cover_text)
        self.assertIn('55.1%',cover_text)
        self.assertNotIn('样本2714',cover_text)
        wrong=copy.deepcopy(self.cfg)
        wrong['dated_observations']['2026-09-24']['source_comp_sha256']='0'*64
        with self.assertRaisesRegex(PipelineError,'composition source changed'):
            context(current,date(2026,9,24),wrong)

    def test_fetch_mid_collection_update_rejected(self):
        calls=0
        def get(url):
            nonlocal calls
            if '/gamedata/gameVersion?' in url:return read_json(self.base/'versions.json')
            if '/stats/summary?' in url:
                calls+=1;d=read_json(self.base/'summary.json')
                if calls>1:d['data']['gamesAnalyzed']+=1
                return d
            from urllib.parse import urlparse,parse_qs
            path=urlparse(url).path;query=parse_qs(urlparse(url).query)
            key=next(k for k,e in self.cfg['source']['endpoints'].items() if e['path']==path and all(query.get(q)==[v] for q,v in e.get('query',{}).items()))
            return read_json(self.base/f'{key}.json')
        with self.assertRaisesRegex(PipelineError,'Source updated while collecting'):fetch(self.cfg,get=get)

    def test_tampered_file_rejected(self):
        folder=self.work/'tamper';build(self.snap,self.cfg,date(2026,9,20),folder,self.snap)
        path=folder/'regular-body.txt';path.write_text(path.read_text()+'错误数据')
        with self.assertRaisesRegex(PipelineError,'Body changed'):verify(folder,self.cfg)
        shutil.rmtree(folder)

    def test_next_day_ranking_scope_and_date_propagation(self):
        folder=self.work/'next-day-source';folder.mkdir(exist_ok=True)
        for key in ['versions',*self.cfg['source']['endpoints']]:shutil.copyfile(self.base/f'{key}.json',folder/f'{key}.json')
        write_json(folder/'TEST_FIXTURE.json',{'purpose':'Synthetic next-day integration test. Not current/live data.'})
        self.mutate(folder,'summary',lambda d:d.update(dataUpdatedAt='2026-09-20T19:26:03.412Z',gamesAnalyzed=88156))
        self.mutate(folder,'versions',lambda d:d[0].update(battleCount=88156))
        self.mutate(folder,'rank',lambda rows:next(x for x in rows if x['compId']=='89').update(top4Rate=61.5))
        self.mutate(folder,'kog-ad-equips',lambda d:next(x for x in d['hero3Equips'] if set(x['equipIds'])=={2001,2045,2046}).update(sampleCount=300,top4Rate=58.15))
        out=self.work/'next-day';m=build(snapshot(folder,self.cfg),self.cfg,date(2026,9,21),out,self.snap);verify(out,self.cfg)
        body=(out/'regular-body.txt').read_text();cold=(out/'cold-body.txt').read_text()
        self.assertLess(body.index('巨龙95｜'),body.index('野怪小红｜'))
        self.assertIn('49.21%（2223样本）',cold);self.assertIn('58.15%（300）',cold)
        self.assertTrue(all('9.21' in n['title'] for n in m['notes']))
        for note in m['notes']:
            for img in note['images']:
                texts='\n'.join(e.text or '' for e in ET.parse(img['svg']).getroot().iter('{http://www.w3.org/2000/svg}text'))
                self.assertNotRegex(texts,r'2026\.09\.20|9/20|9\.20更新|09\.20 /')
        with self.assertRaisesRegex(PipelineError,'Synthetic'):plan(out,self.cfg,read_json(STATE))

    def test_pending_submission_resumes_before_fetch(self):
        import cli
        with tempfile.TemporaryDirectory(dir=self.work) as temp:
            folder=Path(temp);state=read_json(STATE);state['latest_package']=str(folder)
            write_json(folder/'state.json',state)
            write_json(folder/'manifest.json',{'status':'checks_passed','notes':[{'status':'prepared'}]})
            write_json(folder/'browser-cold.json',{'stage':'submission_attempted','intent':{'type':'submit'}})
            with mock.patch.object(cli,'STATE',folder/'state.json'),mock.patch.object(cli,'fetch') as fetch_mock:
                result=cli.main(['update'])
            self.assertEqual(result['status'],'resume_publication');fetch_mock.assert_not_called()

    def test_unchanged_note_receipts_complete_without_resubmission(self):
        import publish
        with tempfile.TemporaryDirectory(dir=self.work) as temp:
            folder=Path(temp)/'package';shutil.copytree(self.work/'cached',folder)
            state={**read_json(STATE),'published_manifest':str(self.work/'cached/manifest.json')};tempstate=Path(temp)/'state.json';write_json(tempstate,state)
            plan(folder,self.cfg,state);p=read_json(folder/'publish-plan.json')
            with mock.patch.object(publish,'STATE',tempstate):
                for i,note in enumerate(p['notes']):
                    receipt={'stage':'noop','note_id':note['note_id'],'before':{'observed_at':'2026-09-20T00:00:00Z',
                        'note_id':note['note_id'],'title':note['title'],'body':note['body'],'topics':note['topics'],
                        'images':[{'asset_id':x['asset_id'],'width':1080,'height':1851} for x in note['baseline']['images']]}}
                    path=Path(temp)/'simulated-receipt.json';write_json(path,receipt)
                    result=record_noop(folder,path,self.cfg,state)
                    self.assertEqual(result['status'],'unchanged')
                    self.assertEqual(result['package_status'],'partially_submitted' if i==0 else 'published')
            self.assertEqual(read_json(tempstate)['published_manifest'],str(folder/'manifest.json'))


class CurrentObservationTests(unittest.TestCase):
    def test_0928_observations_keep_existing_cards_and_append_inferno(self):
        cfg=config()
        current=snapshot(ROOT/'outputs/dual-rank-snapshots/20260928-0331-23a96356d4f8',cfg)
        ctx,order=context(current,date(2026,9,28),cfg)
        cold_cards=card_specs(cfg,order,date(2026,9,28))[1][1]
        self.assertEqual([card['name'] for card in cold_cards[-3:]],
                         ['黑暗仪式蜘蛛','献祭螳螂阿兹尔','地狱火巨龙'])
        self.assertEqual(len(cold_cards),10)
        self.assertEqual(ctx['cold_observation']['last_page'],'10')
        self.assertIn('图9献祭沙皇',ctx['cold_observation']['body_section'])
        self.assertIn('图10地狱火巨龙',ctx['cold_observation']['body_section'])
        self.assertIn('暂无同条件数据',ctx['cold_observation']['body_section'])


if __name__=='__main__':
    unittest.main(verbosity=2)
