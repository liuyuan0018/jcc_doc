var json=System.IO.File.ReadAllText("/Users/lyu/Documents/ChatGPT/金铲铲/exports/frontline-malphite-v1/main-four-review-v1/replay-preview.json");
var doc=UnityEngine.JsonUtility.FromJson<Jcc.Presentation.ReplayDocument>(json);
var loaded=new Jcc.Production.LoadedPackage{Json=json,Replay=new Jcc.Presentation.ReplaySession(doc),Package=new Jcc.Production.EpisodePackage{width=1080,height=1920,hideControls=true}};
using(var preview=new Jcc.Production.ProductionPreviewScene(loaded)) { preview.Capture(new Jcc.Production.PreviewPoint{id="main-1",time=1},"/Users/lyu/Documents/ChatGPT/金铲铲/exports/frontline-malphite-v1/main-four-review-v1");
preview.Capture(new Jcc.Production.PreviewPoint{id="main-2",time=11},"/Users/lyu/Documents/ChatGPT/金铲铲/exports/frontline-malphite-v1/main-four-review-v1");
preview.Capture(new Jcc.Production.PreviewPoint{id="main-3",time=21},"/Users/lyu/Documents/ChatGPT/金铲铲/exports/frontline-malphite-v1/main-four-review-v1");
preview.Capture(new Jcc.Production.PreviewPoint{id="main-4",time=31},"/Users/lyu/Documents/ChatGPT/金铲铲/exports/frontline-malphite-v1/main-four-review-v1"); }
return "Four Main screenshots complete";
