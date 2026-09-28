var p=UnityEngine.Object.FindFirstObjectByType<Jcc.Presentation.ReplayPlayer>();
var samples=new System.Collections.Generic.List<double>();var start=UnityEditor.EditorApplication.timeSinceStartup;var prev=start;
UnityEditor.EditorApplication.CallbackFunction cb=null;
cb=()=>{var now=UnityEditor.EditorApplication.timeSinceStartup;samples.Add(now-prev);prev=now;if(now-start>=4){UnityEditor.EditorApplication.update-=cb;System.IO.File.WriteAllText("/Volumes/Apple/Codex/art-assets/金铲铲/exports/frontline-malphite-rerun-v1/production-v3/editor-cadence.txt",string.Join(",",samples));}};
UnityEditor.EditorApplication.update+=cb;
return "target="+UnityEngine.Application.targetFrameRate+" vsync="+UnityEngine.QualitySettings.vSyncCount+" background="+UnityEngine.Application.runInBackground+" paused="+UnityEditor.EditorApplication.isPaused+" focused="+UnityEngine.Application.isFocused+" state="+p.RecordingPreparation;
