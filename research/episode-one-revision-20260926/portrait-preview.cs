var json=System.IO.File.ReadAllText("/Volumes/Apple/Codex/art-assets/金铲铲/exports/frontline-episode-01-video-v9/replay.json");
var doc=UnityEngine.JsonUtility.FromJson<Jcc.Presentation.ReplayDocument>(json);
UnityEditor.AssetDatabase.LoadAssetAtPath<Jcc.Presentation.ReplayAssetCatalog>("Assets/Res/Replay/ReplayAssets.asset").Validate(doc);
var loaded=new Jcc.Production.LoadedPackage{Json=json,Replay=new Jcc.Presentation.ReplaySession(doc),Package=new Jcc.Production.EpisodePackage{width=1080,height=1920,hideControls=true}};
using(var preview=new Jcc.Production.ProductionPreviewScene(loaded)) { preview.Capture(new Jcc.Production.PreviewPoint{id="results-portraits",time=177.5},"/Volumes/Apple/Codex/art-assets/金铲铲/exports/frontline-episode-01-video-v9"); }
return "Results portrait preview complete";