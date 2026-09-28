"""Build fixed-asset repair and a data-driven SVG; never synthesizes game artwork."""
from pathlib import Path
import json, base64, html, math
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parents[1]
CAT=json.loads((ROOT/'catalog/assets.json').read_text())
ASSETS={a['name']:a for a in CAT['assets']}

def uri(name):
    a=ASSETS[name]
    return 'data:image/png;base64,'+base64.b64encode((ROOT/a['path']).read_bytes()).decode()

def repair():
    base=Image.open(ROOT/'exports/裁决奶妈-站位图-v2.png').convert('RGB')
    before=base.copy(); mask_all=Image.new('L',base.size,0)
    # Polygons cover artwork only. Original frames, labels and badges remain intact.
    heroes=[
      ('墨菲特',(479,301,602,438),[(483,330),(510,315),(572,315),(597,330),(597,402),(580,407),(503,407),(483,402)]),
      ('阿木木',(620,297,744,435),[(625,333),(681,302),(740,333),(740,403),(723,409),(642,409),(625,402)]),
      ('凯南',(408,438,531,571),[(412,476),(470,444),(526,476),(526,541),(512,548),(432,548),(412,538)]),
      ('约里克',(196,578,324,714),[(201,610),(259,578),(317,610),(317,678),(300,683),(220,683),(201,675)]),
      ('费德提克',(618,576,744,714),[(625,609),(681,578),(739,609),(739,677),(722,683),(641,683),(625,676)]),
      ('婕拉',(109,720,247,862),[(115,748),(137,736),(212,736),(242,749),(242,823),(219,832),(131,832),(115,821)]),
      ('索拉卡',(407,716,534,859),[(411,747),(436,734),(504,734),(528,746),(528,823),(510,831),(430,831),(411,821)]),
      ('阿兹尔',(833,716,960,859),[(838,749),(894,718),(953,749),(953,824),(932,831),(857,831),(838,821)]),
      ('婕拉',(23,913,140,1038),[(27,944),(52,918),(104,918),(135,944),(135,1007),(109,1031),(50,1031),(27,1007)]),
      ('墨菲特',(23,1051,140,1171),[(27,1077),(51,1055),(106,1055),(135,1078),(135,1145),(108,1165),(51,1165),(27,1143)]),
      ('索拉卡',(23,1187,139,1308),[(27,1212),(51,1191),(106,1191),(134,1213),(134,1281),(109,1301),(52,1301),(27,1280)])
    ]
    for name,box,poly in heroes:
        icon=Image.open(ROOT/ASSETS[name]['path']).convert('RGB').resize((box[2]-box[0],box[3]-box[1]),Image.Resampling.LANCZOS)
        layer=Image.new('RGB',base.size);layer.paste(icon,box[:2])
        mask=Image.new('L',base.size);ImageDraw.Draw(mask).polygon(poly,fill=255)
        # Protect the existing role badges where they overlap a portrait.
        for protected in [(496,277,589,325),(129,700,222,749),(424,700,514,746),(116,914,206,961),(116,1051,207,1098),(116,1187,208,1236)]:
            ImageDraw.Draw(mask).rectangle(protected,fill=0)
        base.paste(layer,(0,0),mask)
        from PIL import ImageChops
        mask_all=ImageChops.lighter(mask_all,mask)
    items=[('裁决使纹章',(315,948,384,1017)),('朔极之矛',(576,949,647,1016)),('虚空之杖',(811,948,884,1018)),('石像鬼石板甲',(346,1087,411,1151)),('狂徒铠甲',(582,1085,648,1151))]
    for name,box in items:
        icon=Image.open(ROOT/ASSETS[name]['path']).convert('RGB').resize((box[2]-box[0],box[3]-box[1]),Image.Resampling.LANCZOS)
        base.paste(icon,box[:2]);ImageDraw.Draw(mask_all).rectangle((box[0],box[1],box[2]-1,box[3]-1),fill=255)
    # Pixel-exact preservation outside the explicitly permitted repair masks.
    from PIL import ImageChops
    delta=ImageChops.difference(before,base)
    outside=ImageChops.multiply(delta,ImageChops.invert(mask_all).convert('RGB'))
    assert outside.getbbox() is None, 'Changed pixels outside repair masks'
    base.save(ROOT/'exports/裁决奶妈-站位图-v3-原素材.png')
    mask_all.save(ROOT/'outputs/v3-repair-mask.png')
    return {'outside_mask_changed_pixels':0,'portrait_instances':len(heroes),'item_instances':len(items),'output':'exports/裁决奶妈-站位图-v3-原素材.png'}


def build_svg(lineup='lineups/裁决奶妈.json', output='exports/裁决奶妈-可复用模板-v1.svg'):
    data=json.loads((ROOT/lineup).read_text())
    cells=[(h['row'],h['col']) for h in data['heroes']]
    assert len(cells)==len(set(cells)), 'Duplicate board positions'
    assert all(0<=r<4 and 0<=c<7 for r,c in cells), 'Invalid board position'
    assert len(data['title_keywords'])==4
    assert len(data['equipment_rows'])==3
    out=['<svg xmlns="http://www.w3.org/2000/svg" width="1086" height="1448" viewBox="0 0 1086 1448">',
      '<defs><radialGradient id="bg"><stop stop-color="#0a385a"/><stop offset="1" stop-color="#031323"/></radialGradient><linearGradient id="gold" x2="1" y2="1"><stop stop-color="#fff1a8"/><stop offset=".5" stop-color="#f4c75c"/><stop offset="1" stop-color="#b27c26"/></linearGradient><linearGradient id="row"><stop stop-color="#082740"/><stop offset="1" stop-color="#04172c"/></linearGradient></defs>',
      '<rect width="1086" height="1448" fill="url(#bg)"/>',
      '<g font-family="PingFang SC, Heiti SC, STHeiti, sans-serif" font-weight="700">']
    def text(x,y,t,size=28,color='#f4f9ff',anchor='middle'):
        out.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" text-anchor="{anchor}">{html.escape(t)}</text>')
    def panel(x,y,w,h,color='#eac568',fill='url(#row)',cut=22):
        points=f'{x+cut},{y} {x+w-cut},{y} {x+w},{y+cut} {x+w},{y+h-cut} {x+w-cut},{y+h} {x+cut},{y+h} {x},{y+h-cut} {x},{y+cut}'
        out.append(f'<polygon points="{points}" fill="{fill}" stroke="{color}" stroke-width="3"/>')
    def hexpoints(cx,cy,r):
        return ' '.join(f'{cx+math.cos(math.radians(a))*r:.2f},{cy+math.sin(math.radians(a))*r:.2f}' for a in [-90,-30,30,90,150,210])
    def portrait(name,cx,cy,r,color,tag=None):
        ident=f'p{len(out)}';points=hexpoints(cx,cy,r)
        out.append(f'<clipPath id="{ident}"><polygon points="{points}"/></clipPath>')
        out.append(f'<image x="{cx-r}" y="{cy-r}" width="{r*2}" height="{r*2}" href="{uri(name)}" clip-path="url(#{ident})" preserveAspectRatio="xMidYMid slice"/>')
        out.append(f'<polygon points="{points}" fill="none" stroke="{color}" stroke-width="4"/>')
        panel(cx-49,cy+36,98,33,color,cut=10);text(cx,cy+61,name,23)
        if tag:
            panel(cx-43,cy-r-4,86,37,color,cut=12);text(cx,cy-r+24,tag,27,color)
    panel(16,20,1054,121);panel(28,31,1030,98,'#39d9ec',cut=23)
    parts=data['title_keywords'];xs=[182,432,651,898]
    for x,t in zip(xs,parts):text(x,104,t,51,'url(#gold)' if x in [182,898] else '#d5f8ff')
    for x in [333,533,768]:text(x,102,'│',44,'#53e8f0')
    panel(279,153,528,60,'#36dce9',cut=25);text(543,195,f"{data['season']} · {data['patch']} 参考站位",38,'#fce18d')
    panel(365,226,356,40,'#36dce9',cut=15);text(543,255,data['variant_label'],27,'#62edfa')
    # Four rows of seven cells. All portraits and positions are data-driven.
    out.append('<path d="M270 209 H48 L22 235 V867 L48 893 H1038 L1064 867 V235 L1038 209 H817" fill="none" stroke="#ebc766" stroke-width="3"/>')
    for row in range(4):
      for col in range(7):
        cx=100+136*col+(68 if row%2 else 0);cy=370+138*row
        if cx+64>1050:continue
        out.append(f'<polygon points="{hexpoints(cx,cy,72)}" fill="#062442" stroke="#638bbd" stroke-width="3"/>')
        out.append(f'<polygon points="{hexpoints(cx,cy,66)}" fill="none" stroke="#315779" stroke-width="1"/>')
    for h in data['heroes']:
        cx=100+136*h['col']+(68 if h['row']%2 else 0);cy=370+138*h['row']
        portrait(h['name'],cx,cy,71,h.get('color','#8ab5e6'),h.get('role'))
    for i,eq in enumerate(data['equipment_rows']):
        y=928+136*i;color=eq['color'];panel(24,y,1040,110,color,cut=24)
        # Portrait remains a fixed sourced bitmap inside a vector frame.
        pts=hexpoints(80,y+53,64);ident=f'row{i}'
        out.append(f'<clipPath id="{ident}"><polygon points="{pts}"/></clipPath><image x="16" y="{y-11}" width="128" height="128" href="{uri(eq["hero"])}" clip-path="url(#{ident})"/><polygon points="{pts}" fill="none" stroke="{color}" stroke-width="4"/>')
        panel(123,y-9,78,35,color,cut=10);text(162,y+17,eq['role'],25,color)
        text(169,y+76,eq['hero']+'：',44,color,'start')
        if eq.get('items'):
            for n,item in enumerate(eq['items']):
                x=329+n*240
                out.append(f'<rect x="{x}" y="{y+22}" width="213" height="71" rx="30" fill="#061a30" stroke="{color}" stroke-width="2"/>')
                if item.get('asset'):
                    out.append(f'<image x="{x+6}" y="{y+28}" width="60" height="60" href="{uri(item["asset"])}"/><rect x="{x+6}" y="{y+28}" width="60" height="60" fill="none" stroke="#ead48b"/>')
                    text(x+137,y+69,item['label'],27)
                else:text(x+106,y+69,item['label'],29)
                if n<2:text(x+228,y+69,'+',31)
        else:
            out.append(f'<rect x="347" y="{y+22}" width="687" height="71" rx="35" fill="#221040" stroke="{color}" stroke-width="2"/>');text(690,y+70,eq['note'],31)
    panel(23,1330,1040,81,'#eac568');text(543,1384,data['footer'],36)
    text(1025,1434,data['reference_date']+' · '+data['season'],17,'#89a7ba','end')
    out.append('</g></svg>')
    p=ROOT/output;p.write_text('\n'.join(out))
    return str(p.relative_to(ROOT))

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--lineup',default='lineups/裁决奶妈.json')
    parser.add_argument('--output',default='exports/裁决奶妈-可复用模板-v1.svg')
    parser.add_argument('--skip-repair',action='store_true')
    args=parser.parse_args()
    result={} if args.skip_repair else repair()
    result['reusable_svg']=build_svg(args.lineup,args.output)
    (ROOT/'outputs/build-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False))
