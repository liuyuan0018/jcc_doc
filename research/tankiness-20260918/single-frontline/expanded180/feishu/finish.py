# -*- coding: utf-8 -*-
import json,subprocess,math
from pathlib import Path
P=Path(__file__).resolve().parent;T='Ia2isc6J5hH2kzt2YGWcNH9qnXV'
def run(cmd,save):
 r=subprocess.run(['lark-cli','sheets',*cmd,'--as','user','--spreadsheet-token',T],text=True,capture_output=True)
 (P/save).write_text(r.stdout or r.stderr)
 assert r.returncode==0,(save,r.stderr)
 j=json.loads(r.stdout);assert j.get('ok'),j
 return j
info=run(['+workbook-info'],'after-info.json')['data'];assert len(info['sheets'])==17
ids={s.get('title',s.get('sheet_name')):s['sheet_id'] for s in info['sheets']}
S=json.loads((P/'sheets.json').read_text())['sheets']
for s in S:
 name=s['name'];sid=ids[name]
 if name not in ['180秒_阅读说明','180秒_机制契约']:
  end=chr(64+len(s['columns']))
  run(['+filter-create','--sheet-id',sid,'--range',f'A1:{end}{len(s["data"])+1}'],f'filter-{sid}.json')
  q=run(['+filter-list','--sheet-id',sid],f'filter-read-{sid}.json')['data']['sheets'][0]['filters'][0]['details']
  assert q['visible_rows_count']==len(s['data']) and q['filtered_out_rows_count']==0
  print('Filter verified',name,flush=True)
run(['+sheet-move','--sheet-id',ids['180秒_阅读说明'],'--index','0'],'move-guide.json')
receipt=run(['+table-get','--output-path','readback.json'],'readback-receipt.json');assert receipt['data']['complete']
actual={s['name']:s for s in json.loads((P/'readback.json').read_text())['sheets']}
old=json.loads((P.parent.parent/'expanded/feishu/readback.json').read_text())['sheets']
n=0
for s in [*S,*old]:
 q=actual[s['name']];assert s['columns']==q['columns'] and len(s['data'])==len(q['data'])
 for r,t in zip(s['data'],q['data']):
  assert len(r)==len(t)
  for v,w in zip(r,t):
   assert math.isclose(v,float(w),rel_tol=1e-8,abs_tol=.005) if isinstance(v,(int,float)) else v==w,(s['name'],v,w)
   n+=1
 print('Verified',s['name'],len(q['data']),flush=True)
for name in ['180秒_常用资源结果','180秒_阅读说明']:
 run(['+sheet-info','--sheet-id',ids[name],'--range','A1:B5','--include','row_heights,col_widths,frozen'],'layout-'+ids[name]+'.json')
(P/'verification.json').write_text(json.dumps(dict(verified_sheets=17,new_sheets=9,preserved_sheets=8,matched_cells=n,guide_id=ids['180秒_阅读说明']),ensure_ascii=False,indent=2))
print('All values and old sheets matched. Guide:',ids['180秒_阅读说明'])
