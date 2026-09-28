import json,subprocess,time,hashlib,struct
from pathlib import Path
OUT=Path(__file__).resolve().parent
JCC=Path('/Users/lyu/Documents/project/game/projects/jcc/client')
CLI='/Users/lyu/.codex/plugins/cache/personal/unity-cli/2.0.1/skills/unity-cli/scripts/cli/cs.py'
def cs(code):
 r=subprocess.run(['python3','-B',CLI,'exec','--json','--input','-','--timeout','60'],input=json.dumps({'code':code}),cwd=JCC,capture_output=True,text=True)
 d=json.loads(r.stdout);assert d['ok'],d;return d
cs('UnityEngine.Application.runInBackground=true; \"Background rendering enabled for capture batch\"')
records=[]
for page in range(1,9):
 path=OUT/f'page-{page:02}.png'
 if not path.exists():
  cs(f'''var p=UnityEngine.Object.FindFirstObjectByType<Jcc.Presentation.ReplayPlayer>(); p.Pause();p.Seek({(page-1)*5+2}); UnityEngine.Canvas.ForceUpdateCanvases(); var v=UnityEditor.EditorWindow.GetWindow(typeof(UnityEditor.Editor).Assembly.GetType("UnityEditor.GameView"));v.Show();v.Focus(); var screenshot64=GameFramework.MediaCapture.Unity.UnityScreenshot.CaptureAsync({json.dumps(str(path),ensure_ascii=False)}); "requested page {page}"''')
  deadline=time.monotonic()+30
  while not path.exists() and time.monotonic()<deadline:time.sleep(.25)
  assert path.exists(), 'Screenshot did not finish; inspect pending UnityScreenshot host and Game View rendering.'
 png=path.read_bytes();size=struct.unpack('>II',png[16:24]);assert size==(1080,1920),size
 records.append(dict(page=page,time=(page-1)*5+2,path=str(path),size=size,sha256=hashlib.sha256(png).hexdigest()))
 print(f'Captured {page}/8',flush=True)
assert len({r['sha256'] for r in records})==8
(OUT/'screenshots.json').write_text(json.dumps(dict(api='GameFramework.MediaCapture.Unity.UnityScreenshot.CaptureAsync',replay='replay.json',images=records),ensure_ascii=False,indent=2))
