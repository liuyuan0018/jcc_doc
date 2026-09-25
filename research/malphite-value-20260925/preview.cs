using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using UnityEditor;
using UnityEditor.SceneManagement;
using TMPro;
using UnityEngine.TextCore.LowLevel;

using Jcc.Presentation;
public static class MalphiteDetailsPreview {
const string PrefabPath="Assets/Res/GUI/Prefabs/Results.prefab";
static Color Paper=new Color(.95f,.93f,.98f);
 public static string Preview(){if(EditorApplication.isPlayingOrWillChangePlaymode)throw new Exception("Exit PlayMode first");var scene=EditorSceneManager.NewPreviewScene();RenderTexture rt=null;Texture2D image=null;try{var camGo=new GameObject("ScopePreviewCamera",typeof(Camera));UnityEngine.SceneManagement.SceneManager.MoveGameObjectToScene(camGo,scene);var camera=camGo.GetComponent<Camera>();camera.scene=scene;camera.overrideSceneCullingMask=EditorSceneManager.GetSceneCullingMask(scene);camera.transform.position=new Vector3(0,0,-10);camera.clearFlags=CameraClearFlags.SolidColor;camera.backgroundColor=Paper;camera.orthographic=true;camera.orthographicSize=960;camera.enabled=false;camera.allowHDR=false;camera.allowMSAA=false;
 var canvasGo=new GameObject("ScopePreviewCanvas",typeof(RectTransform),typeof(Canvas),typeof(CanvasScaler));UnityEngine.SceneManagement.SceneManager.MoveGameObjectToScene(canvasGo,scene);var canvas=canvasGo.GetComponent<Canvas>();canvas.renderMode=RenderMode.ScreenSpaceCamera;canvas.worldCamera=camera;canvas.planeDistance=10;var scale=canvasGo.GetComponent<CanvasScaler>();scale.uiScaleMode=CanvasScaler.ScaleMode.ScaleWithScreenSize;scale.referenceResolution=new Vector2(1080,1920);var page=(GameObject)PrefabUtility.InstantiatePrefab(AssetDatabase.LoadAssetAtPath<GameObject>(PrefabPath),scene);page.transform.SetParent(canvasGo.transform,false);var rect=(RectTransform)page.transform;rect.anchorMin=Vector2.zero;rect.anchorMax=Vector2.one;rect.sizeDelta=Vector2.zero;rect.anchoredPosition=Vector2.zero;rect.pivot=new Vector2(0,1);
 rt=new RenderTexture(1080,1920,24,RenderTextureFormat.ARGB32,RenderTextureReadWrite.sRGB);rt.Create();camera.targetTexture=rt;var catalog=UnityEngine.Object.Instantiate(AssetDatabase.LoadAssetAtPath<ReplayAssetCatalog>("Assets/Res/Replay/ReplayAssets.asset"));
var list=catalog.entries.ToList();list.Add(new ReplayAssetCatalog.Entry{key="fixture/augment",sprite=AssetDatabase.LoadAssetAtPath<Sprite>("Assets/Res/GUI/Image/Common/Marks/augment_hex.png")});list.Add(new ReplayAssetCatalog.Entry{key="fixture/malphite",sprite=AssetDatabase.LoadAssetAtPath<Sprite>("Assets/Res/GUI/Image/HeadIcon/malphite.png")});catalog.entries=list.ToArray();
try {
var entries=new ReplayResultEntry[8];
for(int i=0;i<8;i++) entries[i]=new ReplayResultEntry{id="fixture-"+i,rank=i==7?250950:i+1,passedDps=1850-i*50,isTop=i==0,episodeTag=i<3?(2+i*2)+"黑 A":"",detailRichText="<b>"+(2+(i%3)*2)+"黑荆棘</b> · 献祭："+(1+i%5)+"费"+(i<6?2+i%2:1+i%2)+"星坦克",equipment=new[]{new ReplayEquipment{label="板甲",iconKey="item/gargoyle_stoneplate"},new ReplayEquipment{label="狂徒",iconKey="item/warmogs_armor"},new ReplayEquipment{label="振奋",iconKey="item/spirit_visage"}},augments=i%2==0?new[]{new ReplayResultAugment{label="单身板甲",iconKey="fixture/augment"}}:new ReplayResultAugment[0]};
var data=new ReplayResults{title="石头人 · 羁绊与献祭",subtitle="UI 布局样例，非模拟结果",portraitKey="fixture/malphite",conditions="此图只检查通用信息区，所有成绩均为样例",footnote="两黑、四黑、六黑分别展示8套 · 片尾88套精选",barScaleDps=2000,pageSizes=new[]{8},entries=entries};
Canvas.ForceUpdateCanvases();var view=page.GetComponent<ScoreResultsPageView>();view.Bind(data,catalog);view.Render(data,catalog,1,"");
Canvas.ForceUpdateCanvases();foreach(var t in page.GetComponentsInChildren<TMP_Text>())t.ForceMeshUpdate();
} finally {UnityEngine.Object.DestroyImmediate(catalog);}
Canvas.ForceUpdateCanvases();camera.Render();var old=RenderTexture.active;RenderTexture.active=rt;image=new Texture2D(1080,1920,TextureFormat.RGBA32,false,false);image.ReadPixels(new Rect(0,0,1080,1920),0,0);image.Apply();RenderTexture.active=old;string path="/Users/lyu/Documents/ChatGPT/金铲铲/research/malphite-value-20260925/results-layout.png";File.WriteAllBytes(path,image.EncodeToPNG());
 var warnings=new List<string>();foreach(var t in page.GetComponentsInChildren<TMP_Text>()){if(t.enableWordWrapping)continue;var pref=t.GetPreferredValues(t.text,float.PositiveInfinity,float.PositiveInfinity);if(pref.x>t.rectTransform.rect.width+2)warnings.Add(t.name+": "+pref.x+">"+t.rectTransform.rect.width);}File.WriteAllText("/Users/lyu/Documents/ChatGPT/金铲铲/research/malphite-value-20260925/results-text-fit.txt",string.Join("\n",warnings));return path+" | overflow="+warnings.Count;
 }finally{if(image)UnityEngine.Object.DestroyImmediate(image);if(rt){rt.Release();UnityEngine.Object.DestroyImmediate(rt);}EditorSceneManager.ClosePreviewScene(scene);}}
}
MalphiteDetailsPreview.Preview()
