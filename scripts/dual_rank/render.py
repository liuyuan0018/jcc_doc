"""Render the maintained SVG templates without changing artwork or strategy."""
from datetime import datetime, timezone
from pathlib import Path
import copy
import json
import os
import re
import shutil
import struct
import subprocess
import xml.etree.ElementTree as ET

from model import ROOT, PipelineError, compare, context, digest, expand, need, read_json, snapshot, write_json

NS = '{http://www.w3.org/2000/svg}'
ET.register_namespace('', NS[1:-1])
RUNTIME = Path('/Users/lyu/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node')


def node():
    return os.environ.get('DUAL_RANK_NODE') or (str(RUNTIME) if RUNTIME.exists() else shutil.which('node'))


def card_specs(cfg, order, date):
    cards = cfg['cards']
    regular = [c for c in cards if c['track']=='regular' and c['kind']!='detail']
    regular += [next(c for c in cards if c['track']=='regular' and c['comp_id']==cid) for cid in order]
    cold = [copy.deepcopy(c) for c in cards if c['track']=='cold']
    observation = cfg.get('dated_observations', {}).get(date.isoformat())
    if observation:
        cold[0]['template'] = observation['cold_cover_template']
        cold[0]['height'] = observation['cold_cover_height']
        cold.append(observation['cold_card'])
        if observation.get('bonus_card'):
            cold.append(observation['bonus_card'])
        cold.extend(observation.get('additional_cards', []))
    return [('regular',regular),('cold',cold)]


def configuration_hash(cfg, date):
    # A one-day editorial observation must not invalidate earlier published
    # packages or future dates on which that observation is not rendered.
    effective = copy.deepcopy(cfg)
    observations = effective.pop('dated_observations', {})
    selected = observations.get(date.isoformat())
    if selected:
        effective['dated_observations'] = {date.isoformat(): selected}
    return digest(effective)


def svg_for(spec, ctx, order, cfg, page, total):
    root = ET.parse(ROOT/spec['template']).getroot()
    if spec['track']=='regular' and spec['kind']=='cover':
        group = root.find(NS+'g'); children = list(group)
        starts = [i for i,e in enumerate(children) if e.get('data-row')]
        need(len(starts)==len(cfg['regular']['ids']), 'Cover row/template mismatch')
        tail = next(i for i in range(starts[-1]+1,len(children)) if children[i].tag==NS+'g')
        rows = {children[start].get('data-row'):children[start:end] for start,end in zip(starts,starts[1:]+[tail])}
        for e in children[starts[0]:tail]: group.remove(e)
        index = starts[0]
        for n,cid in enumerate([x for x in order if x in cfg['regular']['ids']]):
            nodes=rows[cid]; delta=cfg['regular']['row_y']+n*cfg['regular']['row_step']-float(nodes[0].get('y'))
            for parent in nodes:
                for e in parent.iter():
                    if delta and e.get('y') is not None: e.set('y',f"{float(e.get('y'))+delta:g}")
            nodes[0].set('fill','#ffffff' if n%2==0 else '#e8e1f2')
            for e in nodes: group.insert(index,e);index+=1
    local={**ctx,'page':{'number':f'{page:02d}','total':f'{total:02d}'}}
    for e in root.iter():
        e.attrib.pop('data-row',None)
        if e.text and '{{' in e.text: e.text=expand(e.text,local)
    need((int(root.get('width')),int(root.get('height')))==(spec['width'],spec['height']), 'Template dimensions changed')
    return ET.tostring(root,encoding='unicode')


def png_size(path):
    data=Path(path).read_bytes()
    need(data[:8]==b'\x89PNG\r\n\x1a\n' and data[12:16]==b'IHDR', 'Invalid PNG: '+str(path))
    return struct.unpack('>II',data[16:24])


def build(snap, cfg, date, output, baseline):
    difference=compare(baseline,snap,cfg)
    need(not difference['review_required'], 'Semantic/source review required: '+json.dumps(difference['review_required'],ensure_ascii=False))
    output=Path(output).resolve()
    need(output != Path(snap['folder']) and not (Path(snap['folder']).is_relative_to(output)), 'Output cannot overwrite source snapshot')
    output.mkdir(parents=True,exist_ok=True)
    ctx,order=context(snap,date,cfg)
    renderer=ROOT/'scripts/dual_rank/render.cjs'
    need(node(), 'Node runtime not available')
    runtime=json.loads(subprocess.check_output([node(),str(renderer),'--fingerprint'],text=True))
    cache=ROOT/'outputs/dual-rank-cache';cache.mkdir(exist_ok=True)
    jobs=[];artifacts=[];notes=[]
    for track,specs in card_specs(cfg,order,date):
        folder=output/track;folder.mkdir(exist_ok=True)
        body=expand((ROOT/f'templates/dual-rank/{track}-body.txt').read_text(),ctx)
        title=expand(cfg['notes'][track]['title_template'],ctx)
        need('{{' not in body and not re.search(r'本次补进|本次重写|本次修订',body), 'Unresolved template or creator-process prose')
        (output/f'{track}-body.txt').write_text(body)
        (output/f'{track}-title.txt').write_text(title)
        images=[]
        for i,spec in enumerate(specs,1):
            svg=svg_for(spec,ctx,order,cfg,i,len(specs));path=folder/f"{i:02d}-{spec['name']}.svg";path.write_text(svg)
            key=digest({'svg':digest(svg.encode()),'renderer':digest(renderer.read_bytes()),'runtime':runtime})
            cached=cache/f'{key}.png'
            if not cached.exists(): jobs.append({'svg':str(path),'png':str(cached),'width':spec['width'],'height':spec['height']})
            artifact={'track':track,'index':i,'name':spec['name'],'svg':str(path),'file':str(path.with_suffix('.png')),
                      'width':spec['width'],'height':spec['height'],'cache_file':str(cached),'cache_key':key,
                      'svg_sha256':digest(svg.encode()),'baseline_png':spec.get('baseline_png'), 'template':spec['template']}
            artifacts.append(artifact);images.append(artifact)
        notes.append({**cfg['notes'][track], 'key':track,'title':title,'body_file':str(output/f'{track}-body.txt'),
                      'body_sha256':digest(body.encode()),'images':images,'code_count':sum(s['kind']=='detail' for s in specs) if track=='cold' else len(order),
                      'status':'prepared'})
    write_json(output/'render-jobs.json',jobs)
    with (output/'render.log').open('w') as log:
        subprocess.run([node(),str(renderer),str(output/'render-jobs.json')],stdout=log,stderr=log,check=True)
    from PIL import Image, ImageChops, ImageOps, ImageDraw
    identical=[];changed=[];change_strips=[]
    for a in artifacts:
        shutil.copyfile(a['cache_file'],a['file'])
        a['png_sha256']=digest(Path(a['file']).read_bytes())
        need(png_size(a['file'])==(a['width'],a['height']), 'PNG size mismatch')
        with Image.open(a['file']) as im:
            if a['baseline_png']:
                with Image.open(ROOT/a['baseline_png']) as old:
                    diff=ImageChops.difference(im.convert('RGB'),old.convert('RGB')) if im.size==old.size else None
            else:
                diff=None
            same=diff is not None and diff.getbbox() is None
            if not same and diff is not None and a['index']!=1:
                channels=diff.split();mask=ImageChops.lighter(ImageChops.lighter(channels[0],channels[1]),channels[2])
                active=[i for i,has_pixels in enumerate(mask.getprojection()[1]) if has_pixels]
                bands=[]
                for y in active:
                    if bands and y-bands[-1][1]<=24:bands[-1][1]=y
                    else:bands.append([y,y])
                for top,bottom in bands:
                    crop=im.convert('RGB').crop((0,max(0,top-12),im.width,min(im.height,bottom+13)))
                    label=Image.new('RGB',(im.width,30),'#eeeeee');ImageDraw.Draw(label).text((10,8),f"{a['track']} / {a['index']:02d} / y={top}-{bottom}",fill='#222222')
                    change_strips.extend([label,crop.copy()])
        a['pixel_identical_to_accepted']=same
        (identical if same else changed).append(a['file'])
    # Small review sheet; originals remain available when an affected line needs inspection.
    thumbs=[]
    for a in artifacts:
        with Image.open(a['file']) as im:
            thumb=ImageOps.contain(im.convert('RGB'),(270,510))
            tile=Image.new('RGB',(290,550),'#eceaf1');tile.paste(thumb,((290-thumb.width)//2,20));thumbs.append(tile)
    sheet=Image.new('RGB',(290*5,550*((len(thumbs)+4)//5)),'#eceaf1')
    for i,im in enumerate(thumbs):sheet.paste(im,((i%5)*290,(i//5)*550))
    sheet.save(output/'review.jpg',quality=85)
    if change_strips:
        detail_sheet=Image.new('RGB',(max(x.width for x in change_strips),sum(x.height for x in change_strips)),'white')
        y=0
        for strip in change_strips:detail_sheet.paste(strip,(0,y));y+=strip.height
        detail_sheet.save(output/'changed-details.jpg',quality=90)
    manifest={'schema_version':1,'created_at':datetime.now(timezone.utc).isoformat(),'date':date.isoformat(),'test_fixture':snap['test_fixture'],
              'status':'checks_passed_visual_reused' if not changed else 'checks_passed_needs_visual_check',
              'source':{'snapshot':snap['folder'],'version':snap['summary']['gameVersion'],'updated_at':snap['summary']['dataUpdatedAt'],
                        'source_hashes':snap['source_hashes']},
              'configuration_sha256':configuration_hash(cfg,date),'notes':notes,'diff':difference,
              'visual':{'method':'pixel comparison against accepted 2026-09-20 PNGs','identical':identical,'needs_inspection':changed,
                        'overview':str(output/'review.jpg'),'changed_detail_regions':str(output/'changed-details.jpg') if change_strips else None},
              'rendered':len(jobs),'cache_hits':len(artifacts)-len(jobs),'model_calls':0}
    write_json(output/'normalized.json',snap)
    write_json(output/'diff.json',difference)
    write_json(output/'manifest.json',manifest)
    return manifest


def verify(package,cfg):
    package=Path(package).resolve();m=read_json(package/'manifest.json')
    date=datetime.fromisoformat(m['date']).date()
    need(m['configuration_sha256']==configuration_hash(cfg,date),'Configuration changed since build')
    snap=snapshot(m['source']['snapshot'],cfg)
    need(m.get('test_fixture',False)==snap['test_fixture'],'Test fixture provenance changed')
    need(snap['source_hashes']==m['source']['source_hashes'],'Snapshot changed since build')
    ctx,order=context(snap,date,cfg)
    checks=[]
    for (track,specs),note in zip(card_specs(cfg,order,date),m['notes']):
        need(note['key']==track and len(note['images'])==len(specs),'Image count/track mismatch')
        body=Path(note['body_file']).read_text()
        need(digest(body.encode())==note['body_sha256'],'Body changed since build')
        need(body==expand((ROOT/f'templates/dual-rank/{track}-body.txt').read_text(),ctx),'Body differs from source/configuration')
        need(note['title']==expand(cfg['notes'][track]['title_template'],ctx),'Title date/style mismatch')
        need((package/f'{track}-title.txt').read_text()==note['title'],'Title file mismatch')
        need(note['topics']==cfg['notes'][track]['topics'],'Topic entities changed')
        for i,(spec,a) in enumerate(zip(specs,note['images']),1):
            need(a['index']==i and a['name']==spec['name'],'Image order mismatch')
            expected=svg_for(spec,ctx,order,cfg,i,len(specs))
            need(Path(a['svg']).read_text()==expected,'SVG does not match current source: '+a['name'])
            need(digest(Path(a['file']).read_bytes())==a['png_sha256'],'PNG changed since render: '+a['name'])
            need(png_size(a['file'])==(spec['width'],spec['height']),'Invalid image dimensions')
        checks.append({'track':track,'images':len(specs),'codes':note['code_count'],'body_chars':len(body),'title_chars':len(note['title'])})
    result={'ok':True,'checks':checks,'source_date':m['source']['updated_at'],'visual_status':m['status']}
    write_json(package/'checks.json',result)
    return result
