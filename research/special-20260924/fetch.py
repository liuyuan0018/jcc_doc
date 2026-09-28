"""Archive current public DataJ responses for the 9/24 special-build review."""
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json

OUT = Path(__file__).resolve().parent
BASE = 'https://www.dataj.cc/api/web'
QUERIES = {
    'gamedata': ('/gamedata', {'setId': 18}),
    'hex': ('/stats/hex', {'setId': 18, 'gameVersion': '18.2a'}),
    'dark-ritual-comps': ('/stats/hex/20778/comps', {'setId': 18, 'gameVersion': '18.2a'}),
    'comp120': ('/comp/120', {'setId': 18, 'gameVersion': '18.2a'}),
    'comp120-hexes': ('/comp/120/hexes', {'setId': 18, 'gameVersion': '18.2a'}),
}


def main():
    receipts = []
    for key, (path, params) in QUERIES.items():
        url = BASE + path + '?' + urlencode(params)
        with urlopen(Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}), timeout=30) as response:
            data = json.load(response)
        if data.get('code') != 200 or data.get('success') is not True or data.get('data') is None:
            raise RuntimeError(f'{key}: source did not return usable data')
        (OUT / f'{key}.json').write_text(json.dumps(data, ensure_ascii=False, indent=2))
        receipts.append({'key': key, 'url': url, 'fetched_at': datetime.now(timezone.utc).isoformat()})
        value = data['data']
        print(json.dumps({'key': key, 'shape': type(value).__name__, 'count': len(value) if hasattr(value, '__len__') else None}, ensure_ascii=False))
    (OUT / 'requests.json').write_text(json.dumps(receipts, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
