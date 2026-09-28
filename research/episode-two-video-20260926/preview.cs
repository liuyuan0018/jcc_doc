typeof(Jcc.Presentation.ReplayAssetCatalog).GetField("lookup",System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.NonPublic).SetValue(UnityEditor.AssetDatabase.LoadAssetAtPath<Jcc.Presentation.ReplayAssetCatalog>("Assets/Res/Replay/ReplayAssets.asset"),null);
var json=System.IO.File.ReadAllText("/Volumes/Apple/Codex/art-assets/金铲铲/exports/frontline-episode-02-video-v1/replay.json");
var doc=UnityEngine.JsonUtility.FromJson<Jcc.Presentation.ReplayDocument>(json);
UnityEditor.AssetDatabase.LoadAssetAtPath<Jcc.Presentation.ReplayAssetCatalog>("Assets/Res/Replay/ReplayAssets.asset").Validate(doc);
var loaded=new Jcc.Production.LoadedPackage{Json=json,Replay=new Jcc.Presentation.ReplaySession(doc),Package=new Jcc.Production.EpisodePackage{width=1080,height=1920,hideControls=true}};
using(var preview=new Jcc.Production.ProductionPreviewScene(loaded)) {
preview.Capture(new Jcc.Production.PreviewPoint{id="preview-main",time=10},"/Volumes/Apple/Codex/art-assets/金铲铲/exports/frontline-episode-02-video-v1");
preview.Capture(new Jcc.Production.PreviewPoint{id="preview-scope",time=190.96666666666667},"/Volumes/Apple/Codex/art-assets/金铲铲/exports/frontline-episode-02-video-v1");
preview.Capture(new Jcc.Production.PreviewPoint{id="preview-results",time=212.96666666666667},"/Volumes/Apple/Codex/art-assets/金铲铲/exports/frontline-episode-02-video-v1");
}
return "Episode 2 previews complete";