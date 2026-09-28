var p=UnityEngine.Object.FindFirstObjectByType<Jcc.Presentation.ReplayPlayer>();var r=GameFramework.MediaCapture.Unity.UnityAvRecorder.Active;
if(r!=null&&r.State!=GameFramework.MediaCapture.Unity.RecordingState.Completed&&r.State!=GameFramework.MediaCapture.Unity.RecordingState.Faulted)throw new System.Exception("Recorder busy: "+r.State);
if(p.Clock.Playing)throw new System.Exception("Replay is currently running");
System.IO.File.WriteAllText("/Users/lyu/Documents/ChatGPT/金铲铲/exports/frontline-vi-eight-v2/previous-runtime.json",UnityEngine.JsonUtility.ToJson(p.Session.Document));
return "Idle, safe to prepare";
