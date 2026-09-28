"""Fetch observed public DataJ endpoints into an immutable, coherent snapshot."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json
import shutil
import tempfile
import time

from model import ROOT, PipelineError, digest, need, read_json, snapshot, write_json


def fetch(cfg, get=None):
    source=cfg['source'];receipts=[]
    def read(key,endpoint):
        url=source['base_url']+endpoint['path']+'?'+urlencode({'setId':source['set_id'],'gameVersion':source['version'],**endpoint.get('query',{})})
        for attempt in range(2):
            try:
                if get:
                    data=get(url)
                else:
                    with urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0','Accept':'application/json'}),timeout=25) as response:
                        data=json.loads(response.read())
                need(data.get('success') is True and data.get('code')==200 and data.get('data') is not None,key+': source returned an error')
                return key,data,{'key':key,'url':url,'fetched_at':datetime.now(timezone.utc).isoformat(),'ok':True}
            except Exception:
                if attempt: raise
                time.sleep(0.5)
    versions=read('versions',{'path':source['versions_path']})
    latest=max(versions[1]['data'],key=lambda v:v['startTime'])
    need(latest['gameVersion']==source['version'],'New game version detected: '+latest['gameVersion']+'; review configuration before building')
    before=read('summary',source['endpoints']['summary'])
    endpoints={k:v for k,v in source['endpoints'].items() if k!='summary'}
    with ThreadPoolExecutor(max_workers=6) as pool:
        results=list(pool.map(lambda kv:read(*kv),endpoints.items()))
    after=read('summary',source['endpoints']['summary'])
    need(before[1]['data']==after[1]['data'],'Source updated while collecting; retry a new snapshot')
    root=ROOT/'outputs/dual-rank-snapshots';root.mkdir(exist_ok=True)
    temporary=Path(tempfile.mkdtemp(prefix='.fetch-',dir=root))
    try:
        for key,data,receipt in [versions,before,*results]:
            write_json(temporary/f'{key}.json',data);receipts.append(receipt)
        receipts.append({**after[2],'key':'summary_consistency_check'})
        write_json(temporary/'requests.json',receipts)
        snap=snapshot(temporary,cfg)
        identity=digest(snap['semantic_hashes'])[:12]
        final=root/(datetime.fromisoformat(snap['when']).strftime('%Y%m%d-%H%M')+'-'+identity)
        if final.exists():
            # Identical data already archived. Preserve that archive's original receipt.
            need(snapshot(final,cfg)['semantic_hashes']==snap['semantic_hashes'],'Snapshot identity collision')
            shutil.rmtree(temporary)
        else: temporary.rename(final)
        return snapshot(final,cfg),len(receipts)
    except Exception:
        if temporary.exists(): shutil.rmtree(temporary)
        raise
