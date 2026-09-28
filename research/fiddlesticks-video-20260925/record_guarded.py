"""Keep imports outside a single call to the existing continuous recorder; restore afterward."""
import importlib.util,subprocess,sys
from pathlib import Path
JCC=Path('/Users/lyu/Documents/project/game/projects/jcc/client');OUT=Path('/Users/lyu/Documents/ChatGPT/金铲铲/exports/frontline-fiddlesticks-v1/production-v1');SKILL=Path('/Users/lyu/.codex/plugins/cache/personal/unity-media-capture/0.1.0+codex.20260809113714/skills/unity-record-and-share')
spec=importlib.util.spec_from_file_location('capture',SKILL/'scripts/unity_media_capture.py');cap=importlib.util.module_from_spec(spec);spec.loader.exec_module(cap)
cap.run_csharp(JCC,'UnityEditor.AssetDatabase.DisallowAutoRefresh(); "Automatic asset refresh held for one recording"')
try:
 subprocess.run([sys.executable,'-B',str(JCC/'Tools/Production/record_replay.py'),'--capture-skill',str(SKILL),'--replay',str(OUT/'replay.json'),'--audio-asset','Assets/Res/Audio/Fiddlesticks/mix-master-v1.wav','--output',str(OUT/'fiddlesticks-continuous-v1c.mp4')],cwd=JCC,check=True)
finally:
 cap.run_csharp(JCC,'UnityEditor.AssetDatabase.AllowAutoRefresh(); "Automatic asset refresh restored"')
