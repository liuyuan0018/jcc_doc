var json=System.IO.File.ReadAllText("/Volumes/Apple/Codex/art-assets/金铲铲/exports/frontline-malphite-rerun-v1/production-v2/replay.json");
var doc=UnityEngine.JsonUtility.FromJson<Jcc.Presentation.ReplayDocument>(json);
var loaded=new Jcc.Production.LoadedPackage{Json=json,Replay=new Jcc.Presentation.ReplaySession(doc),Package=new Jcc.Production.EpisodePackage{width=1080,height=1920,hideControls=true}};
System.IO.Directory.CreateDirectory("/Volumes/Apple/Codex/art-assets/金铲铲/exports/frontline-malphite-rerun-v1/production-v2/preflight");
using(var preview=new Jcc.Production.ProductionPreviewScene(loaded)) { preview.CheckCaptions(); preview.Capture(new Jcc.Production.PreviewPoint{id="cover",time=1},"/Volumes/Apple/Codex/art-assets/金铲铲/exports/frontline-malphite-rerun-v1/production-v2/preflight");
preview.Capture(new Jcc.Production.PreviewPoint{id="selection-rule",time=6.5},"/Volumes/Apple/Codex/art-assets/金铲铲/exports/frontline-malphite-rerun-v1/production-v2/preflight");
preview.Capture(new Jcc.Production.PreviewPoint{id="G1-intro",time=23.5},"/Volumes/Apple/Codex/art-assets/金铲铲/exports/frontline-malphite-rerun-v1/production-v2/preflight");
preview.Capture(new Jcc.Production.PreviewPoint{id="G1-2150",time=103.5},"/Volumes/Apple/Codex/art-assets/金铲铲/exports/frontline-malphite-rerun-v1/production-v2/preflight");
preview.Capture(new Jcc.Production.PreviewPoint{id="G2-intro",time=110.0},"/Volumes/Apple/Codex/art-assets/金铲铲/exports/frontline-malphite-rerun-v1/production-v2/preflight");
preview.Capture(new Jcc.Production.PreviewPoint{id="G3-intro",time=164.0},"/Volumes/Apple/Codex/art-assets/金铲铲/exports/frontline-malphite-rerun-v1/production-v2/preflight");
preview.Capture(new Jcc.Production.PreviewPoint{id="G4-intro",time=215.5},"/Volumes/Apple/Codex/art-assets/金铲铲/exports/frontline-malphite-rerun-v1/production-v2/preflight");
preview.Capture(new Jcc.Production.PreviewPoint{id="scope",time=256.5},"/Volumes/Apple/Codex/art-assets/金铲铲/exports/frontline-malphite-rerun-v1/production-v2/preflight");
preview.Capture(new Jcc.Production.PreviewPoint{id="P01",time=270.5},"/Volumes/Apple/Codex/art-assets/金铲铲/exports/frontline-malphite-rerun-v1/production-v2/preflight");
preview.Capture(new Jcc.Production.PreviewPoint{id="P12",time=342.0},"/Volumes/Apple/Codex/art-assets/金铲铲/exports/frontline-malphite-rerun-v1/production-v2/preflight"); }
return "Captions and keyframes passed";
