var json=System.IO.File.ReadAllText("/Volumes/Apple/Codex/art-assets/金铲铲/exports/frontline-malphite-v1/production-v1/replay.json");
var doc=UnityEngine.JsonUtility.FromJson<Jcc.Presentation.ReplayDocument>(json);
var loaded=new Jcc.Production.LoadedPackage{Json=json,Replay=new Jcc.Presentation.ReplaySession(doc),Package=new Jcc.Production.EpisodePackage{width=1080,height=1920,hideControls=true}};
System.IO.Directory.CreateDirectory("/Volumes/Apple/Codex/art-assets/金铲铲/exports/frontline-malphite-v1/production-v1/preview-v3");
using(var preview=new Jcc.Production.ProductionPreviewScene(loaded)) {
preview.Capture(new Jcc.Production.PreviewPoint{id="cover",time=1},"/Volumes/Apple/Codex/art-assets/金铲铲/exports/frontline-malphite-v1/production-v1/preview-v3");
preview.Capture(new Jcc.Production.PreviewPoint{id="G2-intro",time=16.5},"/Volumes/Apple/Codex/art-assets/金铲铲/exports/frontline-malphite-v1/production-v1/preview-v3");
preview.Capture(new Jcc.Production.PreviewPoint{id="G4-intro",time=86.0},"/Volumes/Apple/Codex/art-assets/金铲铲/exports/frontline-malphite-v1/production-v1/preview-v3");
preview.Capture(new Jcc.Production.PreviewPoint{id="G6-intro",time=179.0},"/Volumes/Apple/Codex/art-assets/金铲铲/exports/frontline-malphite-v1/production-v1/preview-v3");
preview.Capture(new Jcc.Production.PreviewPoint{id="G6-1700",time=259.5},"/Volumes/Apple/Codex/art-assets/金铲铲/exports/frontline-malphite-v1/production-v1/preview-v3");
preview.Capture(new Jcc.Production.PreviewPoint{id="scope",time=273.5},"/Volumes/Apple/Codex/art-assets/金铲铲/exports/frontline-malphite-v1/production-v1/preview-v3");
preview.Capture(new Jcc.Production.PreviewPoint{id="P01",time=287.5},"/Volumes/Apple/Codex/art-assets/金铲铲/exports/frontline-malphite-v1/production-v1/preview-v3");
preview.Capture(new Jcc.Production.PreviewPoint{id="P04",time=307.0},"/Volumes/Apple/Codex/art-assets/金铲铲/exports/frontline-malphite-v1/production-v1/preview-v3");
}
return "Screenshots complete";
