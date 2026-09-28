from pathlib import Path
import json,shutil
out=Path(__file__).resolve().parents[2]/'exports/frontline-episode-01-video-v6'
fix={'BaseCombinations/Count':'24','BaseCombinations/Unit':'位','AugmentCombinations/Count':'<size=104>69.72</size>','AugmentCombinations/Unit':'<size=40>万套</size>','AugmentCombinations/Explanation0':'三件普通装备','AugmentCombinations/Explanation1':'含适用单身板甲','AugmentCombinations/Explanation2':'不纳入心之钢','Total':'<size=64>各英雄最优配置排名</size>','RankingRule':'最高通过档排序','CombinationDefinition':'演示8位 · 榜单列全24位','CombinationOrder':'从300起，每档增加50来伤'}
for filename in ['replay.json','replay-unvoiced.json']:
 p=out/filename;r=json.loads(p.read_text())
 for c in r['cards']:c['label']=c['label'][0]+' '+c['heroName']
 for s in r['segments']:
  s['tierLabel']='逐档加压'if s['phase']=='battle'else'暂停查看';s['headerStatus']='蔚继续加压'if s['layout']=='solo'else'8位前排'
  if s['phase']=='hold':s['simFrom']=30;s['simTo']=30
 for key,val in fix.items():
  path='SafeArea/'+key;x=next((x for x in r['scopeTextOverrides']if x['path']==path),None)
  if x:x['text']=val
  else:r['scopeTextOverrides'].append(dict(path=path,text=val))
 p.write_text(json.dumps(r,ensure_ascii=False,separators=(',',':')))
shutil.copy2(out/'replay.json','/Users/lyu/Documents/project/game/projects/jcc/client/Assets/Res/Replay/frontline-one-v6.json')
p=Path(__file__).with_name('preview.cs');s=p.read_text().replace('id="preview-','id="check-');p.with_name('check.cs').write_text(s)
