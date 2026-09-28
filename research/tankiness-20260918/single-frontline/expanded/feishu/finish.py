import json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parent
T='Ia2isc6J5hH2kzt2YGWcNH9qnXV'
def run(cmd,save,stdin=None):
 r=subprocess.run(['lark-cli','sheets',*cmd,'--as','user','--spreadsheet-token',T],input=stdin,text=True,capture_output=True)
 (P/save).write_text(r.stdout or r.stderr)
 assert r.returncode==0,(save,r.stderr)
 j=json.loads(r.stdout);assert j.get('ok'),j
 return j
info=run(['+workbook-info'],'workbook-info.json')['data']
assert len(info['sheets'])==8
S=json.loads((P/'sheets.json').read_text())['sheets']
ids={s.get('title',s.get('sheet_name')):s['sheet_id'] for s in info['sheets']}
guide=S[0]
idx=next(i for i,r in enumerate(guide['data'],2) if r[0]=='数据来源')
run(['+cells-set','--sheet-id',ids['阅读说明'],'--range',f'B{idx}','--cells','-'],'source-update.json',json.dumps([[{'value':guide['data'][idx-2][1]}]],ensure_ascii=False))
for s in S:
 name=s['name'];sid=ids[name]
 if name not in ['阅读说明','机制契约']:
  end=chr(64+len(s['columns']))
  run(['+filter-create','--sheet-id',sid,'--range',f'A1:{end}{len(s["data"])+1}'],f'filter-{sid}.json')
  run(['+filter-list','--sheet-id',sid],f'filter-read-{sid}.json')
  print('Filter:',name,flush=True)
run(['+table-get','--output-path','readback.json'],'readback-receipt.json')
print('Readback saved.',flush=True)
