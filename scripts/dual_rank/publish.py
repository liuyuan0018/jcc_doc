"""Prepare browser operations and validate saved receipts; never call private APIs."""
from datetime import datetime, timezone
from pathlib import Path
import re

from model import ROOT, STATE, digest, need, read_json, write_json
from render import verify


def resolve(path):
    return Path(path) if Path(path).is_absolute() else ROOT/path


def plan(package,cfg,state):
    package=Path(package).resolve();verify(package,cfg)
    m=read_json(package/'manifest.json');published=read_json(resolve(state['published_manifest']))
    need(not m.get('test_fixture'),'Synthetic validation data cannot enter the publishing flow')
    previous={n['key']:n for n in published['notes']}
    payload={'schema_version':1,'package':str(package),'notes':[], 'browser_module':str(ROOT/'scripts/dual_rank/browser.mjs')}
    for note in m['notes']:
        old=previous[note['key']]
        body=Path(note['body_file']).read_text().strip()
        old_body=resolve(old['body_file']).read_text().strip()
        old_images=[{**im,'file':str(resolve(im['file'])),
                     'asset_id':im.get('saved_asset_id') or im.get('saved_spectrum_asset_id') or im.get('asset_id')} for im in old['images']]
        same_images=len(old_images)==len(note['images']) and all(digest(Path(a['file']).read_bytes())==digest(Path(b['file']).read_bytes()) for a,b in zip(old_images,note['images']))
        action='noop' if note['title']==old['title'] and body==old_body and same_images else 'update_existing'
        if note['status'] in ['submitted','published']: action='verify_existing_submission'
        payload['notes'].append({'key':note['key'],'note_id':note['note_id'],'action':action,
           'edit_url':f"https://creator.xiaohongshu.com/publish/update?source=&id={note['note_id']}&noteType=normal",
           'title':note['title'],'body':body,'images':note['images'],'topics':note['topics'],
           'baseline':{'title':old['title'],'body':old_body,'topics':old['topics'],'images':old_images},
           'visual_complete':not m['visual']['needs_inspection'],
           'receipt_file':str(package/f"browser-{note['key']}.json")})
    write_json(package/'publish-plan.json',payload)
    return {'ok':True,'plan':str(package/'publish-plan.json'),'actions':[{k:n[k] for k in ['key','action']} for n in payload['notes']],
            'visual_to_check':len(m['visual']['needs_inspection']),'model_calls':0}


def record_visual(package,files,note,cfg):
    package=Path(package).resolve();verify(package,cfg);m=read_json(package/'manifest.json')
    inspected={str(Path(f).resolve()) for f in files}
    remaining=set(m['visual']['needs_inspection'])
    need(inspected <= remaining,'Only currently uninspected images can be recorded')
    need(note.strip(),'Record what was visually checked')
    m['visual'].setdefault('inspections',[]).append({'at':datetime.now(timezone.utc).isoformat(),'files':sorted(inspected),'note':note})
    m['visual']['needs_inspection']=sorted(remaining-inspected)
    if not m['visual']['needs_inspection']:m['status']='checks_and_visual_passed'
    write_json(package/'manifest.json',m)
    return {'ok':True,'visual_to_check':len(m['visual']['needs_inspection'])}


def record_readback(package,evidence,cfg,state):
    package=Path(package).resolve();verify(package,cfg);m=read_json(package/'manifest.json')
    need(not m.get('test_fixture'),'Synthetic validation data cannot be recorded as published')
    need(not m['visual']['needs_inspection'],'Visual check is incomplete')
    receipt=read_json(evidence)
    need(receipt.get('observed_at') and receipt.get('note_id'),'Missing browser observation identity/time')
    note=next((n for n in m['notes'] if n['note_id']==receipt['note_id']),None)
    need(note is not None,'Receipt belongs to another note')
    need(receipt.get('title')==note['title'],'Saved title mismatch')
    lines=lambda text:[line.strip() for line in text.splitlines() if line.strip()]
    need(lines(receipt.get('body',''))==lines(Path(note['body_file']).read_text()),'Saved body mismatch')
    need(receipt.get('topics')==note['topics'],'Saved topic IDs/names/order mismatch')
    images=receipt.get('images',[])
    need(len(images)==len(note['images']),'Saved image count mismatch')
    upload=receipt.get('uploaded_images',[])
    need([x.get('png_sha256') for x in upload]==[x['png_sha256'] for x in note['images']],'Upload receipt/file order mismatch')
    ids=[x.get('asset_id') for x in images]
    need(all(ids) and len(set(ids))==len(ids),'Saved asset IDs missing/duplicated')
    need(ids==[x.get('asset_id') for x in upload],'Saved images differ from uploaded order')
    need(all(x.get('width',0)>0 and x.get('height',0)>0 for x in images),'Saved images not loaded')
    def settings_key(s):
        return {**s,'text':re.sub(r'(引用笔记\n《金铲铲S18(?:冷门榜|阵容榜))\d{1,2}\.\d{1,2}(｜附阵容码》)',r'\1<date>\2',s['text'])}
    need(bool(receipt.get('settings')) and settings_key(receipt['settings'])==settings_key(receipt['settings_before']),'Settings changed or were not read')
    stage=receipt.get('platform_status')
    need(stage in ['submitted','published'],'Missing actual platform submission state')
    if stage=='published':
        need(receipt.get('manager_filter')=='已发布' and receipt.get('manager_title')==note['title'],'Published list not verified')
    need(note['status']!='published' or stage=='published','Cannot regress a published receipt')
    note['status']=stage;note['saved_readback']=receipt
    for a,b in zip(note['images'],images):a['saved_asset_id']=b['asset_id']
    finish(package,m,state)
    return {'ok':True,'key':note['key'],'status':stage,'package_status':m['status']}


def finish(package,m,state):
    m['status']='published' if all(n['status'] in ['published','unchanged'] for n in m['notes']) else 'partially_submitted'
    write_json(package/'manifest.json',m)
    if m['status']=='published':
        state['published_manifest']=str(package/'manifest.json');state['published_snapshot']=m['source']['snapshot'];state['latest_package']=str(package)
        write_json(STATE,state)


def record_noop(package,evidence,cfg,state):
    package=Path(package).resolve();plan(package,cfg,state)
    m=read_json(package/'manifest.json');p=read_json(package/'publish-plan.json');r=read_json(evidence)
    need(r.get('stage')=='noop' and r.get('before',{}).get('observed_at'),'Missing live noop preflight receipt')
    note=next((n for n in m['notes'] if n['note_id']==r.get('note_id')),None)
    need(note is not None,'Receipt belongs to another note')
    action=next(n for n in p['notes'] if n['note_id']==note['note_id'])
    need(action['action']=='noop','This note has changes and must not be recorded as unchanged')
    live=r['before'];lines=lambda s:[x.strip() for x in s.splitlines() if x.strip()]
    need(live.get('note_id')==note['note_id'] and live['title']==note['title'],'Noop title/identity mismatch')
    need(lines(live['body'])==lines(action['body']) and live['topics']==note['topics'],'Noop body/topic mismatch')
    need([x.get('asset_id') for x in live['images']]==[x['asset_id'] for x in action['baseline']['images']],'Noop image identity/order mismatch')
    need(all(x.get('width',0)>0 and x.get('height',0)>0 for x in live['images']),'Noop images not loaded')
    note['status']='unchanged';note['saved_readback']=live;note.setdefault('inherited_publication',state['published_manifest'])
    for a,b in zip(note['images'],live['images']):a['saved_asset_id']=b['asset_id']
    finish(package,m,state)
    return {'ok':True,'key':note['key'],'status':'unchanged','package_status':m['status']}
