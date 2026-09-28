const string path="Assets/Res/GUI/Prefabs/Results.prefab";
var root=UnityEditor.PrefabUtility.LoadPrefabContents(path);
try{root.transform.Find("SafeArea/ColumnLeft").GetComponent<TMPro.TMP_Text>().text="名次 / 配置";UnityEditor.PrefabUtility.SaveAsPrefabAsset(root,path);}
finally{UnityEditor.PrefabUtility.UnloadPrefabContents(root);}
return "Column label updated";
