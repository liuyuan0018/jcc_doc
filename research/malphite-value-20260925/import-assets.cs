var path="Assets/Res/GUI/Image/Cover/malphite-value-v1.png";
var ti=(UnityEditor.TextureImporter)UnityEditor.AssetImporter.GetAtPath(path);
ti.textureType=UnityEditor.TextureImporterType.Sprite;ti.spriteImportMode=UnityEditor.SpriteImportMode.Single;ti.mipmapEnabled=false;ti.maxTextureSize=2048;ti.textureCompression=UnityEditor.TextureImporterCompression.Uncompressed;ti.SaveAndReimport();
var catalog=UnityEditor.AssetDatabase.LoadAssetAtPath<Jcc.Presentation.ReplayAssetCatalog>("Assets/Res/Replay/ReplayAssets.asset");
var entries=new System.Collections.Generic.List<Jcc.Presentation.ReplayAssetCatalog.Entry>(catalog.entries);
foreach(var pair in new[]{new[]{"cover/malphite-value-v1",path},new[]{"hero/malphite","Assets/Res/GUI/Image/HeadIcon/malphite.png"}}){var sprite=UnityEditor.AssetDatabase.LoadAssetAtPath<UnityEngine.Sprite>(pair[1]);if(!sprite)throw new System.Exception(pair[1]);entries.RemoveAll(e=>e.key==pair[0]);entries.Add(new Jcc.Presentation.ReplayAssetCatalog.Entry{key=pair[0],sprite=sprite});}
catalog.entries=entries.ToArray();UnityEditor.EditorUtility.SetDirty(catalog);UnityEditor.AssetDatabase.SaveAssets();return "Imported Malphite cover and portrait";
