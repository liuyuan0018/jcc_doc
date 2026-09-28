using UnityEngine;
using UnityEditor;
using Jcc.Presentation;
using TMPro;
using System.Linq;
if(!Application.isPlaying)throw new System.Exception("Play not ready");
var p=UnityEngine.Object.FindFirstObjectByType<ReplayPlayer>();p.Pause();p.narration=null;
if(!p.LoadJson(System.IO.File.ReadAllText("/Users/lyu/Documents/ChatGPT/金铲铲/research/rammus-results64-20260925/replay.json"),false))throw new System.Exception(p.LastError);
p.Seek(12);
foreach(var c in p.GetComponentsInChildren<ReplayControls>(true))c.gameObject.SetActive(false);
var page=UnityEngine.Object.FindFirstObjectByType<ScoreResultsPageView>();
var rows=page.GetComponentsInChildren<ScoreResultRowView>();
for(int i=0;i<rows.Length;i++) {
 var r=rows[i].transform.Find("Rank").GetComponent<TMP_Text>();
 r.text="并列第\n"+p.Session.Document.results.entries[16+i].rank;
 r.fontSize=20;r.fontStyle=FontStyles.Normal;r.color=new Color(.55f,.50f,.64f);r.enableAutoSizing=false;
 r.alignment=TextAlignmentOptions.Center;r.lineSpacing=0;
}
foreach(var t in page.GetComponentsInChildren<TMP_Text>()) {
 if(t.text.StartsWith("按最高连续通过档排序")) t.text="每档增加50来伤 · 同档不分高低";
}
Application.runInBackground=true;
var v=EditorWindow.GetWindow(typeof(Editor).Assembly.GetType("UnityEditor.GameView"));v.Show();v.Focus();v.Repaint();EditorApplication.QueuePlayerLoopUpdate();
Canvas.ForceUpdateCanvases();
var shot=GameFramework.MediaCapture.Unity.UnityScreenshot.CaptureAsync("/Users/lyu/Documents/ChatGPT/金铲铲/research/rammus-results64-20260925/rank-secondary-preview.png");
"Requested page 3 runtime typography preview; prefab unchanged"
