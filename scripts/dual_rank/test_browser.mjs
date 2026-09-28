// Fake browser unit tests plus live read-only receipts in the validation folder.
// This file never connects to a browser or publishes a note.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {createSession,checkBaseline,lines} from './browser.mjs';

const work=await fs.mkdtemp(path.join(os.tmpdir(),'dual-rank-browser-test-'));
let passed=0;
try{
  const note={key:'cold',note_id:'test-note',action:'update_existing',title:'next',body:'new one\n\nnew two',topics:[{name:'topic',id:'topic-id'}],
    baseline:{title:'old',body:'old one\n\nold two',topics:[{name:'topic',id:'topic-id'}],images:[{asset_id:'old0'},{asset_id:'old1'}]},
    images:[0,1,2].map(i=>({file:`/local/${i}.png`,png_sha256:`hash${i}`})),visual_complete:true,receipt_file:path.join(work,'receipt.json')};
  const dom={title:'old',paragraphs:[{index:0,text:'old one',topics:0},{index:1,text:'',topics:0},{index:2,text:'old two',topics:0},{index:3,text:'#topic',topics:1}],
    topics:[{id:'topic-id',name:'topic'}],images:[0,1].map(i=>({src:`https://example.invalid/spectrum/old${i}`,width:1080,height:1851})),image_limit:3,settings:{text:'collection / original\n引用笔记\n《金铲铲S18冷门榜9.20｜附阵容码》',checkboxes:[true,true]}};
  let uploads=0,submissions=0,failAfterUpload=false;
  const pw={url:async()=>`https://creator.xiaohongshu.com/publish/update?id=${note.note_id}`,playwright:{
    evaluate:async()=>structuredClone(dom),
    locator:selector=>({fill:async text=>{assert.equal(selector,'title');dom.title=text;},locator:()=>({nth:index=>({fill:async text=>{dom.paragraphs[index].text=text;}})})}),
    waitForEvent:async()=>({isMultiple:()=>true,setFiles:async files=>{uploads++;for(const file of files)dom.images.push({src:'blob:'+file,width:1080,height:1851});if(failAfterUpload){failAfterUpload=false;throw new Error('connection interrupted after upload');}}})
  }};
  const tab={getAXState:async()=>''};const surface={title:'title',editor:'editor',images:'images'};
  let session=await createSession(pw,tab,note,surface);
  assert.equal((await session.preflight()).stage,'checked');passed++;
  const live=await session.inspect();
  assert.doesNotThrow(()=>checkBaseline({...live,body:'old one\nold two'},note));passed++;
  assert.throws(()=>checkBaseline({...live,body:'user changed something'},note),/Body was edited/);passed++;
  assert.throws(()=>checkBaseline({...live,topics:[{id:'another',name:'topic'}]},note),/Topic entities/);passed++;
  assert.throws(()=>checkBaseline({...live,images:[...live.images].reverse()},note),/images differ/);passed++;
  await session.fillText();assert.equal(dom.paragraphs[1].text,'');assert.equal(dom.paragraphs[3].text,'#topic');assert.equal(dom.title,'next');passed++;
  const clicks={clickAdd:async()=>{},clickRemoveFirst:async()=>{assert.ok(dom.images.length>1);dom.images.shift();}};
  failAfterUpload=true;
  await assert.rejects(()=>session.replaceImages(clicks),/interrupted/);
  session=await createSession(pw,tab,note,surface);
  assert.equal((await session.preflight()).can_resume,false);
  assert.equal((await session.reconcile()).resumed,true);assert.equal(uploads,1);passed++;
  let result;
  for(let i=0;i<12;i++){result=await session.replaceImages(clicks);if(result.stage==='images_filled')break;}
  assert.equal(result.stage,'images_filled');assert.deepEqual(dom.images.map(x=>x.src),note.images.map(x=>'blob:'+x.file));assert.equal(uploads,3);passed++;
  await session.submit(async()=>{submissions++;});await assert.rejects(()=>session.submit(async()=>{submissions++;}),/already attempted/);assert.equal(submissions,1);passed++;
  for(let i=0;i<dom.images.length;i++)dom.images[i].src='https://example.invalid/spectrum/new'+i;
  const saved=await session.savedReadback({platform_status:'published',manager_filter:'已发布',manager_title:note.title});
  const receipt=JSON.parse(await fs.readFile(saved.evidence,'utf8'));
  assert.deepEqual(receipt.uploaded_images.map(x=>x.png_sha256),note.images.map(x=>x.png_sha256));assert.deepEqual(receipt.images.map(x=>x.asset_id),['new0','new1','new2']);passed++;
  const again=await session.savedReadback({platform_status:'published',manager_filter:'已发布',manager_title:note.title,title:'do not overwrite actual DOM',body:'wrong'});
  assert.equal(JSON.parse(await fs.readFile(again.evidence,'utf8')).title,note.title);passed++;
  dom.settings.text=dom.settings.text.replace('9.20','9.21');
  await session.savedReadback({platform_status:'published'});passed++;
  dom.settings.checkboxes[0]=false;
  await assert.rejects(()=>session.savedReadback({platform_status:'published'}),/Settings changed/);passed++;
  dom.settings.checkboxes[0]=true;dom.settings.text=dom.settings.text.replace('冷门榜','阵容榜');
  await assert.rejects(()=>session.savedReadback({platform_status:'published'}),/Settings changed/);passed++;
  console.log(JSON.stringify({ok:true,tests:passed,simulated:true,live_writes:0}));
}finally{await fs.rm(work,{recursive:true,force:true});}
