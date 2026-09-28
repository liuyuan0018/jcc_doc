var json=System.IO.File.ReadAllText("/Volumes/Apple/Codex/art-assets/金铲铲/exports/frontline-episode-01-video-v6/replay.json");
var doc=UnityEngine.JsonUtility.FromJson<Jcc.Presentation.ReplayDocument>(json);
UnityEditor.AssetDatabase.LoadAssetAtPath<Jcc.Presentation.ReplayAssetCatalog>("Assets/Res/Replay/ReplayAssets.asset").Validate(doc);
var loaded=new Jcc.Production.LoadedPackage{Json=json,Replay=new Jcc.Presentation.ReplaySession(doc),Package=new Jcc.Production.EpisodePackage{width=1080,height=1920,hideControls=true}};
using(var preview=new Jcc.Production.ProductionPreviewScene(loaded)) { preview.Capture(new Jcc.Production.PreviewPoint{id="check-cover",time=1},"/Volumes/Apple/Codex/art-assets/金铲铲/exports/frontline-episode-01-video-v6");
preview.Capture(new Jcc.Production.PreviewPoint{id="check-main",time=10},"/Volumes/Apple/Codex/art-assets/金铲铲/exports/frontline-episode-01-video-v6");
preview.Capture(new Jcc.Production.PreviewPoint{id="check-first-fail",time=36.0},"/Volumes/Apple/Codex/art-assets/金铲铲/exports/frontline-episode-01-video-v6");
preview.Capture(new Jcc.Production.PreviewPoint{id="check-solo",time=137.86666666666667},"/Volumes/Apple/Codex/art-assets/金铲铲/exports/frontline-episode-01-video-v6");
preview.Capture(new Jcc.Production.PreviewPoint{id="check-scope",time=165.36666666666667},"/Volumes/Apple/Codex/art-assets/金铲铲/exports/frontline-episode-01-video-v6");
preview.Capture(new Jcc.Production.PreviewPoint{id="check-results-first",time=177.36666666666667},"/Volumes/Apple/Codex/art-assets/金铲铲/exports/frontline-episode-01-video-v6");
preview.Capture(new Jcc.Production.PreviewPoint{id="check-results-last",time=193.36666666666667},"/Volumes/Apple/Codex/art-assets/金铲铲/exports/frontline-episode-01-video-v6"); }
return "Preview complete";
