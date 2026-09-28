# -*- coding: utf-8 -*-
import json,itertools,collections,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent
assert 'COMPLETE ' in (P/'progress.log').read_text(), 'exhaustive run is not complete'
C=json.loads((P/'catalog.json').read_text());I=C['items'];S=json.loads((P/'scenarios.json').read_text())
counts=collections.Counter();coverage=collections.Counter();triples=0
for ids in itertools.combinations_with_replacement(range(len(I)),3):
 if any(ids[j]==ids[j-1] and I[ids[j]]['unique'] for j in (1,2)):continue
 cats=[I[i]['category'] for i in ids];na=cats.count(2);nr=cats.count(1)
 category=5 if 3 in cats else 4 if na>1 or nr>1 else 3 if na and nr else 2 if na else 1 if nr else 0
 healthy=any(I[i]['name']=='坚定之心' for i in ids);gold=any(I[i]['name']=='大亨之铠' for i in ids)
 for aug in range(4):
  if aug&1 and not healthy or aug&2 and not gold:continue
  counts[aug,category]+=1
 coverage.update(set(ids));triples+=1
for cat in (0,1):
 pool=[i for i in range(len(I)) if I[i]['category']==cat]
 for ids in itertools.combinations_with_replacement(pool,2):
  for aug in (0,1):
   if aug==1 and not any(I[i]['name']=='坚定之心' for i in ids):continue
   counts[aug,6+cat]+=1
records=[];runs=0
for sc in S:
 f=P/f"scenario-{sc['index']}.jsonl"
 rows=[json.loads(l) for l in f.read_text().splitlines()];actual={(r['aug'],r['category']):r['runs'] for r in rows}
 expected={k:v for k,v in counts.items() if not(k[0]&2 and sc['slots']>=9)}
 assert actual==expected,(sc['index'],actual,expected)
 for row in rows:
  r=row['result'];assert row['survivors']<=row['runs'] and 0<r['frame']<=5400
  assert abs(r['mana_initial']+r['mana_gain']-r['mana_spent']-r['mana'])<.01
  assert abs(r['shield_granted']-r['shield_used']-r['shield_lost']-r['shield'])<.1+1e-8*max(r['shield_granted'],r['shield'])
  row.update(hero=sc['hero'],star=sc['star'],cost=sc['cost'],traits=sc['traits'],slots=sc['slots'])
 records+=rows;runs+=sum(actual.values())
assert len(coverage)==107
manifest=dict(completed=True,observation_seconds=180,fps=30,profiles=72,heroes=24,scenarios=len(S),items=107,item_counts=C['counts'],unordered_selectable_triples=triples,glove_possible_pairs=1260,runs=runs,summary_rows=len(records),counts_by_aug_category={f'{k[0]}-{k[1]}':v for k,v in counts.items()},item_coverage={str(i):coverage[i] for i in range(107)},checks=['all 249 scenarios complete','independent Python combination count equals C++ run count','all 107 candidates appear','all output mana and shield ledgers pass','each simulation internally asserts mana and shield ledgers'],sha256={f:hashlib.sha256((P/f).read_bytes()).hexdigest() for f in ['engine.cpp','generated.hpp','catalog.json','profiles.json','scenarios.json']})
(P/'results.json').write_text(json.dumps(records,ensure_ascii=False,indent=2));(P/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in manifest.items() if k not in ('item_coverage','sha256','counts_by_aug_category')},ensure_ascii=False,indent=2))
