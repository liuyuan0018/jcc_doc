import json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parent
S=json.loads((P/"scenarios.json").read_text())
I={x["name"]:x["index"] for x in json.loads((P/"catalog.json").read_text())["items"]}
def run(hero,star,traits,items,aug=0,opts=()):
 sc=next(s for s in S if s["hero"]==hero and s["star"]==star and s["traits"]==traits)
 return json.loads(subprocess.check_output([str(P/"engine"),"one",str(sc["index"]),*[str(I[x]) if x else "-1" for x in items],str(aug),*opts],cwd=P,text=True))
