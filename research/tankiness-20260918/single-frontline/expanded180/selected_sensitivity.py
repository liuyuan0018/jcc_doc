# -*- coding: utf-8 -*-
import json
from check import P,I,S,run
C=json.loads((P/'catalog.json').read_text());A=json.loads((P/'results.json').read_text());I=C['items']
def score(x):return(x['result']['frame'],x['result']['hp']+x['result']['shield'])
variants={'target30':['target=30'],'target100':['target=100'],'lock2':['lock=60'],'pause05':['pause=15'],'itemvamp_on':['itemvamp=1'],'aoe_third':['aoevamp=0.3333333333']}
rows=[]
for hero in dict.fromkeys(s['hero'] for s in S):
 for star in (1,2,3):
  for cat in (0,1,2):
   r=max((r for r in A if r['hero']==hero and r['star']==star and r['aug']==0 and r['category']==cat),key=score)
   names=[I[i]['name'] for i in r['items']];vs=dict(variants)
   if '恶火小斧' in names:vs['axe03']=['axe=0.03']
   if '黎明圣盾' in names:vs['dawn20']=['dawn=0.20']
   if any('夜之锋刃' in n for n in names):vs['edge0']=['edge=0']
   checks={name:run(hero,star,r['traits'],names,opts=opts) for name,opts in vs.items()}
   rows.append(dict(hero=hero,star=star,category=cat,traits=r['traits'],items=names,baseline=r['result'],variants=checks,min_frame=min(x['frame'] for x in checks.values())))
(P/'selected-sensitivity.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2));print('selected configs',len(rows),'variant runs',sum(len(x['variants']) for x in rows))
