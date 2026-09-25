var scene=UnityEditor.SceneManagement.EditorSceneManager.NewPreviewScene();
try {
var doc=UnityEngine.JsonUtility.FromJson<Jcc.Presentation.ReplayDocument>(System.IO.File.ReadAllText("/Users/lyu/Documents/ChatGPT/金铲铲/research/malphite-value-20260925/three-round-fixture.json"));
doc.results=null;var session=new Jcc.Presentation.ReplaySession(doc);
var root=(UnityEngine.GameObject)UnityEditor.PrefabUtility.InstantiatePrefab(UnityEditor.AssetDatabase.LoadAssetAtPath<UnityEngine.GameObject>("Assets/Res/GUI/Prefabs/Root.prefab"),scene);
var presenter=root.GetComponentInChildren<Jcc.Presentation.ReplayPresenter>(true);presenter.Load(session);
foreach(double time in new[]{.5,1.5,2.5,.5}) {presenter.Render(time,false);var segment=doc.segments[(int)time];for(int i=0;i<8;i++)if(presenter.MainCards[i].BoundCardId!=segment.tracks[i].cardId)throw new System.Exception("卡片跨轮绑定错误");}
return "24 cards, three groups and backward seek checked";
} finally {UnityEditor.SceneManagement.EditorSceneManager.ClosePreviewScene(scene);}
