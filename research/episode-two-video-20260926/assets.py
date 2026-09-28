from pathlib import Path
import shutil,json,urllib.request,uuid,re
R=Path('/Users/lyu/Documents/ChatGPT/金铲铲');P=R/'exports/frontline-episode-02-video-v1';C=Path('/Users/lyu/Documents/project/game/projects/jcc/client')
r=json.loads((P/'recipe.json').read_text());t=json.loads((P/'timeline-base.json').read_text());r.update(id='frontline-episode-two-video-v1',version=1,sourceArchive='frontline-episode-02-v2',duration=t['duration'],displayPoolConfigurations=1706880);r.pop('revision',None);(P/'recipe.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
x=json.loads((R/'exports/frontline-episode-02-v2/input/dataj-gamedata.json').read_text())['data'];refs=[]
for group,names in [('equip',['连指手套','光盾徽章','飞升护符','大亨之铠','禁忌雕像']),('hex',['金霖龙'])]:
 for name in names:
  o=next(o for o in x[group]if o['name']==name);url=o.get('picture')or o['icon'];key=url.rsplit('/',1)[1].removesuffix('.png');typ='item'if group=='equip'else'augment'
  folder=C/'Assets/Res/GUI/Image'/('Equipment'if typ=='item'else'Augment');folder.mkdir(exist_ok=True);target=folder/(key+'.png')
  if not target.exists():
   urllib.request.urlretrieve(url,target);meta=(C/'Assets/Res/GUI/Image/HeadIcon/vi.png.meta').read_text();target.with_suffix('.png.meta').write_text(re.sub(r'guid: [a-f0-9]+','guid: '+uuid.uuid4().hex,meta,count=1))
  refs.append(dict(key=typ+'/'+key,path=str(target.relative_to(C))))
(P/'new-assets.json').write_text(json.dumps(refs,ensure_ascii=False,indent=2));print(refs)
