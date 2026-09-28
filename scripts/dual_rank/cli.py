#!/usr/bin/env python3
"""Single low-output entry point for both maintained ranking notes."""
from datetime import date as Date, datetime, timezone
from pathlib import Path
import argparse
import json
import sys
import fcntl
import traceback

from model import BJT, ROOT, STATE, PipelineError, compare, config, digest, need, read_json, snapshot, write_json
from fetch import fetch
from render import build, verify


def compact(m, package):
    d=m['diff']
    return {'ok':True,'status':m['status'],'package':str(package),'images':sum(len(n['images']) for n in m['notes']),
            'rank_changes':len(d['ranking']),'tier_changes':len(d['tiers']),'config_or_source_alerts':len(d['review_required']),
            'rendered':m['rendered'],'cache_hits':m['cache_hits'],
            'visual_identical':len(m['visual']['identical']),'visual_to_check':len(m['visual']['needs_inspection']),'model_calls':0}


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    sub=ap.add_subparsers(dest='command',required=True)
    sub.add_parser('status');sub.add_parser('fetch')
    diff=sub.add_parser('diff');diff.add_argument('--snapshot',required=True);diff.add_argument('--baseline');diff.add_argument('--full',action='store_true')
    for name in ['build','update']:
        p=sub.add_parser(name);p.add_argument('--snapshot',required=name=='build');p.add_argument('--date',type=Date.fromisoformat);p.add_argument('--output')
    p=sub.add_parser('verify');p.add_argument('--package',required=True)
    p=sub.add_parser('publish-plan');p.add_argument('--package',required=True)
    p=sub.add_parser('record-readback');p.add_argument('--package',required=True);p.add_argument('--evidence',required=True)
    p=sub.add_parser('record-noop');p.add_argument('--package',required=True);p.add_argument('--evidence',required=True)
    p=sub.add_parser('record-visual');p.add_argument('--package',required=True);p.add_argument('--files',nargs='+',required=True);p.add_argument('--note',required=True)
    args=ap.parse_args(argv);cfg=config();state=read_json(STATE)
    if args.command=='status':
        return {'ok':True,'version':cfg['source']['version'],**state}
    if args.command=='verify': return verify(args.package,cfg)
    if args.command in ['publish-plan','record-readback','record-noop','record-visual']:
        from publish import plan, record_readback, record_noop, record_visual
        if args.command=='publish-plan': return plan(args.package,cfg,state)
        if args.command=='record-readback': return record_readback(args.package,args.evidence,cfg,state)
        if args.command=='record-noop': return record_noop(args.package,args.evidence,cfg,state)
        return record_visual(args.package,args.files,args.note,cfg)
    if args.command=='update' and state.get('latest_package'):
        previous=Path(state['latest_package'])
        if (previous/'manifest.json').exists():
            pm=read_json(previous/'manifest.json')
            receipts=[read_json(p) for p in previous.glob('browser-*.json') if not p.name.endswith('-saved.json')]
            pending=any(n['status']=='submitted' for n in pm['notes']) or pm['status']=='partially_submitted' or any(r.get('intent') or r.get('stage') in ['submission_attempted','saved_readback'] for r in receipts)
            if pending and pm['status']!='published':
                return {'ok':True,'status':'resume_publication','package':str(previous),'message':'Continue the recorded update; do not submit again without checking its saved result'}
    if args.command=='fetch':
        snap,requests=fetch(cfg)
        return {'ok':True,'snapshot':snap['folder'],'source_time':snap['when'],'requests':requests,'model_calls':0}
    baseline=snapshot(getattr(args,'baseline',None) or ROOT/state['published_snapshot'],cfg)
    if getattr(args,'snapshot',None):
        snap=snapshot(args.snapshot,cfg)
    else: snap,_=fetch(cfg)
    difference=compare(baseline,snap,cfg)
    if args.command=='diff':
        report=ROOT/'outputs/dual-rank-reviews'/f"diff-{digest(difference)[:12]}.json";write_json(report,difference)
        return {'ok':True,**difference} if args.full else {'ok':True,'same_source':difference['same_source'],
             'ranking':difference['ranking'],'tiers':difference['tiers'],'statistics_changed':len(difference['statistics']),
             'review_required':difference['review_required'],'new_candidates':difference['new_candidates'],'report':str(report)}
    if args.command=='update':
        state['last_checked_at']=datetime.now(timezone.utc).isoformat();state['last_checked_snapshot']=snap['folder']
        state['last_check']={'same_source':difference['same_source'],'review_required':difference['review_required']}
        write_json(STATE,state)
        if difference['same_source']:
            return {'ok':True,'status':'no_new_data','rendered':0,'publish_needed':False,'snapshot':snap['folder'],'model_calls':0}
    date=args.date or (datetime.now(BJT).date() if args.command=='update' else datetime.fromisoformat(snap['when']).date())
    if difference['review_required']:
        review=ROOT/'outputs/dual-rank-reviews'/f"{date.isoformat()}-{digest(difference)[:10]}.json"
        write_json(review,difference)
        return {'ok':False,'status':'needs_content_review','alerts':difference['review_required'],'report':str(review),'model_calls':0}
    package=Path(args.output).resolve() if args.output else ROOT/'outputs/dual-rank-runs'/f'{date.isoformat()}-{digest(snap["semantic_hashes"])[:12]}'
    if (package/'manifest.json').exists():
        existing=read_json(package/'manifest.json')
        need(not any(n['status'] in ['submitted','published','unchanged'] for n in existing['notes']), 'Cannot overwrite a submitted package: '+str(package))
    m=build(snap,cfg,date,package,baseline);verify(package,cfg)
    if args.command=='update': state['latest_package']=str(package);write_json(STATE,state)
    return compact(m,package)


if __name__=='__main__':
    try:
        (ROOT/'state').mkdir(exist_ok=True)
        with (ROOT/'state/dual-rank.lock').open('a') as lock:
            try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:raise PipelineError('Another dual-rank command is running; use its result before starting another update')
            result=main()
        print(json.dumps(result,ensure_ascii=False,separators=(',',':')))
        sys.exit(0 if result.get('ok') else 2)
    except Exception as e:
        log=ROOT/'outputs/dual-rank-errors'/f"{datetime.now(timezone.utc):%Y%m%dT%H%M%S%f}.log"
        log.parent.mkdir(parents=True,exist_ok=True);log.write_text(traceback.format_exc())
        print(json.dumps({'ok':False,'error':str(e)[:600],'details':str(log),'model_calls':0},ensure_ascii=False,separators=(',',':')))
        sys.exit(2)
