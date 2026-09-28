if (UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode) throw new System.Exception("Exit Play mode first");
var path="Assets/Res/GUI/Prefabs/Components/ScoreResultRow.prefab";
var root=UnityEditor.PrefabUtility.LoadPrefabContents(path);
try {
 var node=root.transform.Find("HeroPortrait");
 if(!node){node=new UnityEngine.GameObject("HeroPortrait",typeof(UnityEngine.RectTransform),typeof(UnityEngine.UI.Image)).transform;node.SetParent(root.transform,false);node.gameObject.layer=5;}
 var rect=(UnityEngine.RectTransform)node;
 rect.anchorMin=rect.anchorMax=rect.pivot=new UnityEngine.Vector2(0,1);
 rect.anchoredPosition=new UnityEngine.Vector2(56,-14);rect.sizeDelta=new UnityEngine.Vector2(66,66);
 var image=node.GetComponent<UnityEngine.UI.Image>();image.preserveAspect=true;image.raycastTarget=false;
 root.GetComponent<Jcc.Presentation.ScoreResultRowView>().ConfigurePortrait(image);
 node.gameObject.SetActive(false);
 UnityEditor.PrefabUtility.SaveAsPrefabAsset(root,path);
}finally{UnityEditor.PrefabUtility.UnloadPrefabContents(root);}
var catalog=UnityEditor.AssetDatabase.LoadAssetAtPath<Jcc.Presentation.ReplayAssetCatalog>("Assets/Res/Replay/ReplayAssets.asset");
var list=new System.Collections.Generic.List<Jcc.Presentation.ReplayAssetCatalog.Entry>(catalog.entries);
var json=System.IO.File.ReadAllText("/Users/lyu/Documents/ChatGPT/金铲铲/exports/frontline-episode-01-video-v9/replay.json");
var doc=UnityEngine.JsonUtility.FromJson<Jcc.Presentation.ReplayDocument>(json);
foreach(var e in doc.results.entries){
 if(list.Exists(x=>x.key==e.portraitKey))continue;
 var sprite=UnityEditor.AssetDatabase.LoadAssetAtPath<UnityEngine.Sprite>("Assets/Res/GUI/Image/HeadIcon/"+e.portraitKey.Substring(5)+".png");
 if(!sprite)throw new System.Exception("Missing portrait "+e.portraitKey);
 list.Add(new Jcc.Presentation.ReplayAssetCatalog.Entry{key=e.portraitKey,sprite=sprite});
}
catalog.entries=list.ToArray();UnityEditor.EditorUtility.SetDirty(catalog);UnityEditor.AssetDatabase.SaveAssets();
return "Results portrait slot and resource bindings saved";
