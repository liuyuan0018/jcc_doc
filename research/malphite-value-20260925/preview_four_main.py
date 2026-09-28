import json,csv,subprocess,copy,argparse
from pathlib import Path
root=Path(__file__).resolve().parents[2];base=root/'exports/frontline-malphite-v1';parser=argparse.ArgumentParser();parser.add_argument('--best',action='store_true');opts=parser.parse_args();out=base/('main-four-best-review-v1' if opts.best else 'main-four-review-v1');out.mkdir(exist_ok=True);(out/'source').mkdir(exist_ok=True)
allrows=list(csv.DictReader((base/'full-ranking.csv').open()))
if opts.best:
 groups={}
 for row in allrows:
  key=tuple(row[k]for k in ['blackthorn','sacrificeCost','sacrificeStar']);groups.setdefault(key,[]).append(row)
 rows=[]
 for group in groups.values():
  group.sort(key=lambda x:(-int(x['score']),int(x['augment']),x['id']));row=copy.deepcopy(group[0]);row['tiedBestCount']=sum(x['score']==row['score']for x in group);rows.append(row)
else:rows=[r for r in allrows if [r['item1'],r['item2'],r['item3']]==['24','27','33']and r['augment']=='0']
assert len(rows)==30
labels={5:'饮血',16:'大天使',17:'冕卫',22:'冰甲',23:'头盔',24:'振奋',26:'反甲',27:'板甲',29:'坚定',30:'龙牙',33:'狂徒'}
keys={5:'bloodthirster',16:'archangels_staff',17:'crownguard',22:'2023',23:'adaptivehelm',24:'spirit_visage',26:'2054',27:'gargoyle_stoneplate',29:'nightharvester',30:'2031',33:'warmogs_armor'}
assert all(int(row[k])in keys for row in rows for k in ['item1','item2','item3'])

rows.sort(key=lambda r:(-int(r['score']),int(r['blackthorn']),int(r['sacrificeCost']),int(r['sacrificeStar'])))
manifest=json.loads((base/'manifest.json').read_text());conditions={(p['sacrifice']['blackthorn'],p['sacrifice']['sacrificeCost'],p['sacrifice']['sacrificeStar']):p['sacrifice']for p in manifest['parts']}
old=json.loads((base/'production-v1/replay.json').read_text());r={k:copy.deepcopy(old[k])for k in ['schemaVersion','conditions','source','isFixture','coverKey','results']};r.update(id='malphite-main-four-review-v1',title='石头人 · 30套献祭对照',footnote=('各条件取装备与海克斯池最高成绩 · 同分并列' if opts.best else '固定振奋 / 板甲 / 狂徒 · 无海克斯 · 同分并列'),duration=40,cards=[],runs=[],segments=[],captions=[])
for n,row in enumerate(rows):
 tier,cost,star=map(int,[row['blackthorn'],row['sacrificeCost'],row['sacrificeStar']]);score=int(row['score']);rank=1+sum(int(x['score'])>score for x in rows);key=row['id'];e=conditions[tier,cost,star]
 path=out/'source'/f'{key}.json'
 if not path.exists():
  args=[key,*[int(row[k])for k in ['item1','item2','item3']],int(row['augment']),e['hp'],e['hpp'],e['armor'],0,850];x=json.loads(subprocess.check_output([str(base/'input/simulate'),'replay'],input=(' '.join(map(str,args))+'\n').encode()));path.write_text(json.dumps(x,separators=(',',':')))
 else:x=json.loads(path.read_text())
 f=x['frames'][0];a=x['attributes'][0]
 r['cards'].append(dict(id=key,label=f'{rank} · {tier}黑',heroName='石头人',portraitKey='hero/malphite',quality='墨菲特 · 4费 · 2星',traits=f'{tier}黑 · 献祭{cost}费{star}星',augment='单身板甲'if int(row['augment'])==4 else'无',augmentIconKey='augment/soloplate2'if int(row['augment'])==4 else'',equipment=[dict(label=labels[int(row[k])],iconKey='item/'+keys[int(row[k])])for k in ['item1','item2','item3']]))
 r['runs'].append(dict(id=key,cardId=key,samples=[dict(time=0,hp=f[1],maxHp=f[2],shield=f[3],alive=bool(f[17]),hasArmor=True,hasMagicResist=True,hasAbilityPower=True,armor=a[1],magicResist=a[2],abilityPower=a[3])],events=[]))
for p in range(4):
 subset=rows[p*8:(p+1)*8];start=p*10
 r['segments'].append(dict(id=f'main-{p+1}',start=start,end=start+10,layout='eight',phase='intro',dps=850,roundSeconds=30,simFrom=0,simTo=0,tierLabel='成绩降序',headerStatus=f'第{p+1}幕 / 4',hasPageTurnSeconds=True,pageTurnSeconds=0,tracks=[dict(cardId=x['id'],runId=x['id'],frozen=True,frozenTime=0,aliveLabel=f'细分 {int(x["score"]):,}',deadLabel='淘汰')for x in subset]))
 r['captions'].append(dict(start=start,end=start+10,text=f'第{p*8+1}—{p*8+len(subset)}项 · 按细分成绩降序，同分并列。\n开战前配置预览，羁绊与献祭见每张卡。'))
(out/'replay-preview.json').write_text(json.dumps(r,ensure_ascii=False,separators=(',',':')));(out/'selection.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
cs='''var json=System.IO.File.ReadAllText(PATH);
var doc=UnityEngine.JsonUtility.FromJson<Jcc.Presentation.ReplayDocument>(json);
var loaded=new Jcc.Production.LoadedPackage{Json=json,Replay=new Jcc.Presentation.ReplaySession(doc),Package=new Jcc.Production.EpisodePackage{width=1080,height=1920,hideControls=true}};
using(var preview=new Jcc.Production.ProductionPreviewScene(loaded)) { POINTS }
return "Four Main screenshots complete";
'''.replace('PATH',json.dumps(str(out/'replay-preview.json'),ensure_ascii=False)).replace('POINTS','\n'.join('preview.Capture(new Jcc.Production.PreviewPoint{id="main-'+str(i+1)+'",time='+str(i*10+1)+'},'+json.dumps(str(out),ensure_ascii=False)+');'for i in range(4)))
Path(__file__).with_name('preview-four-best.cs' if opts.best else 'preview-four-main.cs').write_text(cs)
print(out)
print('Augment winners:',sum(int(x['augment'])==4 for x in rows))
print([(x['blackthorn'],x['sacrificeCost'],x['sacrificeStar'],x['score'],x['augment'])for x in rows])
