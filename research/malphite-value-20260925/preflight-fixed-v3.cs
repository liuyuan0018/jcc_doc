var catalog=UnityEditor.AssetDatabase.LoadAssetAtPath<Jcc.Presentation.ReplayAssetCatalog>("Assets/Res/Replay/ReplayAssets.asset");
typeof(Jcc.Presentation.ReplayAssetCatalog).GetField("lookup",System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.NonPublic).SetValue(catalog,null);
var json=System.IO.File.ReadAllText("/Volumes/Apple/Codex/art-assets/金铲铲/exports/frontline-malphite-rerun-v1/production-v3/replay.json");
var doc=UnityEngine.JsonUtility.FromJson<Jcc.Presentation.ReplayDocument>(json);
var loaded=new Jcc.Production.LoadedPackage{Json=json,Replay=new Jcc.Presentation.ReplaySession(doc),Package=new Jcc.Production.EpisodePackage{width=1080,height=1920,hideControls=true}};
using(var preview=new Jcc.Production.ProductionPreviewScene(loaded)) { preview.CheckCaptions();
preview.Capture(new Jcc.Production.PreviewPoint{id="cover",time=1.25},"/Volumes/Apple/Codex/art-assets/金铲铲/exports/frontline-malphite-rerun-v1/production-v3/preflight-fixed");
preview.Capture(new Jcc.Production.PreviewPoint{id="G1-1450",time=93.75},"/Volumes/Apple/Codex/art-assets/金铲铲/exports/frontline-malphite-rerun-v1/production-v3/preflight-fixed");
} return "Captions and seven keyframes passed";