import json,re
from pathlib import Path
out=Path(__file__).resolve().parents[2]/'exports/frontline-malphite-v1/production-v1'
for filename in ['replay.json','replay-unvoiced.json']:
 p=out/filename;r=json.loads(p.read_text())
 for s in r['segments']:
  if s['layout']in ['eight','solo']:
   if s['phase']=='hold':s['simFrom']=30;s['simTo']=30
   tier=s['headerStatus'].split('黑')[0];s['headerStatus']=tier+'黑荆棘';s['tierLabel']='逐档加压'if s['phase']=='battle'else'暂停查看'
   if s['phase']=='intro':
    for tr in s['tracks']:tr['aliveLabel']='准备开始'
 for c in r['captions']:
  text=c['text'].replace('\n','')
  if text.startswith(('二十五万','250,950套')):text='250,950套参与排名，同分并列。\n前段演示24套，片尾精选88套。'
  elif len(text)>22:
   positions=[m.end()for m in re.finditer('[，。]',text)if m.end()<len(text)]
   at=min(positions,key=lambda n:abs(n-len(text)/2))if positions else len(text)//2;text=text[:at]+'\n'+text[at:]
  c['text']=text
 for f in r['scopeTextOverrides']:
  k=f['path'].split('/')[-1]
  if k=='Total':f['text']='<size=76>8365 × 30 = 250,950</size>'
  if k=='CombinationDefinition':f['text']='前段演示24套 · 片尾精选88套'
  if k=='CombinationOrder':f['text']='投入条件单列，不作性价比总排名'
  if k=='RankingRule':f['text']='按压测成绩排序'
 p.write_text(json.dumps(r,ensure_ascii=False,separators=(',',':')))
