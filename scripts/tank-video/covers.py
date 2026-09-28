#!/usr/bin/env python3
"""Programmatic covers built from verified replay data and original game artwork."""
from __future__ import annotations
from pathlib import Path
import argparse,hashlib,json,math
from PIL import Image,ImageDraw,ImageFont,ImageOps

ROOT=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output-dir',type=Path,default=ROOT/'exports/frontline-covers-v1')
parser.add_argument('--asset-dir',type=Path,default=ROOT/'exports/frontline-covers-v1')
parser.add_argument('--main-data',type=Path,default=ROOT/'exports/frontline-video-main-v2/01-hero-pressure.json')
parser.add_argument('--detail-data',type=Path,default=ROOT/'exports/frontline-video-detail-v2/02-vi-build-tiers.json')
parser.add_argument('--only',choices=['main','detail'])
args=parser.parse_args()
OUT=args.output_dir.resolve();ASSETS=args.asset_dir.resolve()
OUT.mkdir(parents=True,exist_ok=True)
W,H=1080,1440
COLOR={'paper':'#f3f0e5','ink':'#173f34','muted':'#617268','grid':'#e7e6da',
       'lime':'#d9f275','orange':'#ed733e','white':'#fffdf5','line':'#ced5c3','dark':'#173b31'}
FONT='/System/Library/Fonts/Hiragino Sans GB.ttc'
fonts={}
def font(size,bold=True):
    key=(size,bold)
    if key not in fonts:fonts[key]=ImageFont.truetype(FONT,size,index=2 if bold else 0)
    return fonts[key]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def output_path(p):
    try:return str(p.relative_to(ROOT))
    except ValueError:return str(p)
manifest=json.loads((ASSETS/'assets-manifest.json').read_text())
assets={(a['kind'],a['name']):a for a in manifest}
for a in manifest:assert sha(ASSETS/a['path'])==a['sha256']
main_path=args.main_data.resolve();detail_path=args.detail_data.resolve()
main=json.loads(main_path.read_text()) if args.only!='detail' else None
detail=json.loads(detail_path.read_text()) if args.only!='main' else None
if main:
    assert {b['hero'] for b in main['builds']}=={'蔚','拉莫斯','瑟庄妮','伊莉丝'}
    assert all(b['star']==3 for b in main['builds'])
if detail:
    assert [b['label'] for b in detail['builds']]==['配装 A','配装 B','配装 C']
    assert [b['pressure']['passedDps'] for b in detail['builds']]==[2150,2000,1850]
    last=detail['rounds'][-1]
    assert last['dps']==2200 and not last['replays'][0]['result']['alive'] and not last['replays'][2]['result']['alive']
    gap=(last['replays'][0]['result']['frame']-last['replays'][2]['result']['frame'])/30
    assert 6<=gap<6.5, 'Revisit the 6-second cover hook if the underlying replay changes.'

def canvas(height=H):
    im=Image.new('RGB',(W,height),COLOR['paper']);d=ImageDraw.Draw(im)
    # A quiet drafting-paper texture connects these covers to the video series.
    for x in range(12,W,48):
        for y in range(12,height,48):d.ellipse((x,y,x+2,y+2),fill=COLOR['grid'])
    return im

text_boxes=[]
def text(d,xy,s,size,fill=None,bold=True,anchor='lt',max_width=None,stroke=0):
    f=font(size,bold);box=d.textbbox(xy,s,font=f,anchor=anchor,stroke_width=stroke)
    if max_width is not None:assert box[2]-box[0]<=max_width,(s,box,max_width)
    assert box[0]>=0 and box[1]>=0 and box[2]<=W and box[3]<=H,(s,box)
    d.text(xy,s,font=f,fill=fill or COLOR['ink'],anchor=anchor,stroke_width=stroke,stroke_fill=fill or COLOR['ink'])
    text_boxes.append({'text':s,'bbox':box})

def pill(d,box,label,size=28,fill=None,ink=None):
    d.rounded_rectangle(box,radius=(box[3]-box[1])/2,fill=fill or COLOR['ink'])
    text(d,((box[0]+box[2])/2,(box[1]+box[3])/2),label,size,ink or COLOR['white'],anchor='mm',max_width=box[2]-box[0]-32)

def header(im,number,section):
    d=ImageDraw.Draw(im)
    d.rounded_rectangle((58,53,91,91),radius=6,fill=COLOR['ink'])
    for x in [65,75,85]:d.line((x,60,x,84),fill=COLOR['lime'],width=3)
    text(d,(106,54),'前排实验室',32,max_width=500)
    pill(d,(835,47,1022,98),'S18',30,fill=COLOR['ink'])
    text(d,(59,137),f'{number} / {section}',29,COLOR['muted'],max_width=950)
    return d

crop_boxes={
    '蔚':(720,0,1520,710),
    '拉莫斯':(680,0,1580,710),
    '瑟庄妮':(760,0,1500,750),
    '伊莉丝':(750,0,1520,750),
}
aliases={'蔚':'蔚','拉莫斯':'龙龟','瑟庄妮':'猪妹','伊莉丝':'蜘蛛'}
def hero_crop(name,size,portrait=False):
    a=assets[('hero',name)];im=Image.open(ASSETS/a['path']).convert('RGB')
    if portrait and name=='蔚':box=(830,0,1400,750)
    else:box=crop_boxes[name]
    return ImageOps.fit(im.crop(box),size,method=Image.Resampling.LANCZOS,centering=(.5,.38))

def rounded_paste(im,tile,xy,radius=18):
    mask=Image.new('L',tile.size,0);d=ImageDraw.Draw(mask)
    d.rounded_rectangle((0,0,tile.width-1,tile.height-1),radius=radius,fill=255)
    im.paste(tile,xy,mask)

def hero_card(im,name,xy,size=(470,291)):
    x,y=xy;w,h=size
    # Image crop and label use the original artwork, never a generated likeness.
    tile=Image.new('RGB',size,COLOR['ink'])
    art=hero_crop(name,(w,h-66));tile.paste(art,(0,0))
    td=ImageDraw.Draw(tile)
    td.text((24,h-50),aliases[name],font=font(40),fill=COLOR['white'],anchor='lt')
    td.text((w-23,h-45),'3 星',font=font(27),fill=COLOR['lime'],anchor='rt')
    rounded_paste(im,tile,(x,y),18)

def main_cover():
    im=canvas();d=header(im,'01','英雄对比')
    text(d,(57,211),'都给神装',118,stroke=1,max_width=964)
    # Broad, high-contrast second line is the primary feed thumbnail hook.
    d.rounded_rectangle((49,337,1029,509),radius=12,fill=COLOR['lime'])
    text(d,(60,354),'谁最能扛？',146,stroke=1,max_width=960)
    pill(d,(62,536,454,596),'重伤＋减抗全开',32,fill=COLOR['orange'],ink=COLOR['ink'])
    text(d,(1020,553),'各自最优配装',32,COLOR['muted'],anchor='rt',max_width=520)
    for b,xy in zip(main['builds'],[(60,628),(550,628),(60,941),(550,941)]):
        hero_card(im,b['hero'],xy)
    d=ImageDraw.Draw(im)
    d.rounded_rectangle((60,1264,1020,1350),radius=13,fill=COLOR['ink'])
    text(d,(540,1307),'四位前排  ·  30 秒压力测试',38,COLOR['white'],anchor='mm',max_width=904)
    text(d,(540,1391),main.get('coverScopeLabel','金鳞龙条件  ·  机制模拟'),27,COLOR['muted'],anchor='mm',max_width=980)
    return im

short={'振奋盔甲':'振奋','巨龙之爪':'龙牙','大亨之铠':'大亨','冕卫':'冕卫','圣盾使的誓约':'圣盾','棘刺背心':'反甲'}
def item_icon(im,name,xy,size=100):
    a=assets[('item',name)];icon=Image.open(ASSETS/a['path']).convert('RGB')
    icon=icon.resize((size,size),Image.Resampling.LANCZOS)
    rounded_paste(im,icon,xy,8)

def detail_cover():
    im=canvas();d=header(im,'02','配装对比')
    text(d,(57,211),'同一个蔚',118,stroke=1,max_width=964)
    d.rounded_rectangle((49,337,1029,509),radius=12,fill=COLOR['lime'])
    # The numeral is measured from the saved 2200-DPS A/C replay: 6.33 seconds.
    x=62;y=355
    for value,size,ink in [('多扛',146,COLOR['ink']),('6',164,COLOR['orange']),('秒？',146,COLOR['ink'])]:
        f=font(size);text(d,(x,y+(146-size)),value,size,ink,stroke=1,max_width=980-x)
        x+=d.textlength(value,font=f)+6
    pill(d,(62,536,383,596),'只换两件装备',31,fill=COLOR['orange'],ink=COLOR['ink'])
    text(d,(1020,553),'三星蔚 · 6 主宰',32,COLOR['muted'],anchor='rt',max_width=584)
    portrait=hero_crop('蔚',(362,608),True)
    rounded_paste(im,portrait,(60,629),18)
    d=ImageDraw.Draw(im)
    # Three rows preserve the video's A -> B -> C order and item identities.
    for i,b in enumerate(detail['builds']):
        y=629+i*210
        d.rounded_rectangle((449,y,1020,y+188),radius=16,fill=COLOR['white'],outline=COLOR['ink'] if i==0 else COLOR['line'],width=4 if i==0 else 2)
        pill(d,(469,y+25,588,y+75),b['label'],25,fill=COLOR['ink'] if i==0 else '#657a64')
        for j,name in enumerate(b['equipment']):
            x=614+j*126
            item_icon(im,name,(x,y+19),100)
            d=ImageDraw.Draw(im)
            text(d,(x+50,y+151),short[name],28,anchor='mm',max_width=114)
        if i==0:text(d,(529,y+132),'先看 A',24,COLOR['muted'],anchor='mm',max_width=118)
    d=ImageDraw.Draw(im)
    d.rounded_rectangle((60,1264,1020,1350),radius=13,fill=COLOR['ink'])
    text(d,(540,1307),'同英雄  ·  同羁绊  ·  同海克斯',35,COLOR['white'],anchor='mm',max_width=902)
    text(d,(540,1391),'2200 来伤档 · A 对 C · 机制模拟',26,COLOR['muted'],anchor='mm',max_width=985)
    return im

outputs=[]
renderers=[]
if main:renderers.append(('01-hero-pressure-cover',main_cover))
if detail:renderers.append(('02-vi-build-tiers-cover',detail_cover))
for name,render in renderers:
    begin=len(text_boxes);im=render();png=OUT/(name+'.png');jpg=OUT/(name+'.jpg')
    im.save(png);im.save(jpg,quality=96,subsampling=0)
    tall=canvas(1920);tall.paste(im,(0,240))
    tall_path=OUT/(name+'-9x16.png');tall.save(tall_path)
    assert tall.crop((0,240,1080,1680)).tobytes()==im.tobytes()
    thumb=im.resize((270,360),Image.Resampling.LANCZOS);thumb.save(OUT/(name+'-thumbnail.png'))
    outputs.append({'name':name,'png':output_path(png),'jpeg':output_path(jpg),
                    'portrait9x16':output_path(tall_path),'size':[W,H],
                    'sha256':sha(png),'jpegSha256':sha(jpg),'portraitSha256':sha(tall_path),
                    'text':text_boxes[begin:]})
sheet=Image.new('RGB',(len(outputs)*552+24,744),'#deded5')
for i,o in enumerate(outputs):
    cover=Image.open(ROOT/o['png']);sheet.paste(cover.resize((540,720),Image.Resampling.LANCZOS),(12+i*552,12))
sheet.save(OUT/('cover-pair-preview.jpg' if len(outputs)>1 else 'cover-preview.jpg'),quality=95,subsampling=0)
small=Image.new('RGB',(len(outputs)*282,384),'#deded5')
for i,o in enumerate(outputs):
    cover=Image.open(ROOT/o['png']);small.paste(cover.resize((270,360),Image.Resampling.LANCZOS),(6+i*282,12))
small.save(OUT/'feed-thumbnail-check.png')
report={'passed':True,'generation':'Pillow typography and original source images; no generative character or equipment artwork',
        'mainVideoDataSha256':sha(main_path) if main else None,'detailVideoDataSha256':sha(detail_path) if detail else None,'scriptSha256':sha(__file__),
        'assetDirectory':str(ASSETS),'assetsManifestSha256':sha(ASSETS/'assets-manifest.json'),
        'mainCast':[b['hero'] for b in main['builds']] if main else [],
        'detailGear':[{k:b[k] for k in ['label','equipment','pressure']} for b in detail['builds']] if detail else [],
        'detailHook':{'dps':2200,'aSeconds':last['replays'][0]['result']['frame']/30,
                      'cSeconds':last['replays'][2]['result']['frame']/30,'deltaSeconds':gap,'headlineRoundedSeconds':6} if detail else None,
        'allTextInsideCanvas':True,'centerCropOf9x16Matches3x4':True,'outputs':outputs,'visualReview':'pending'}
(OUT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps({k:v for k,v in report.items() if k!='outputs'},ensure_ascii=False))
print(OUT)
