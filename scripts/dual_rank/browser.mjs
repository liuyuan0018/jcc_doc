/**
 * Runs inside cua_repl only. Pass locators grounded in the CURRENT editor DOM.
 * No private API, CDP, injected page mutation, persistent coordinates or login data.
 * Each operation reads its result and writes a checkpoint before another action.
 */
import fs from 'node:fs/promises';

const canonical=value=>Array.isArray(value)?value.map(canonical):value&&typeof value==='object'?Object.fromEntries(Object.keys(value).sort().map(k=>[k,canonical(value[k])])):value;
const equal=(a,b)=>JSON.stringify(canonical(a))===JSON.stringify(canonical(b));
const check=(ok,message)=>{if(!ok)throw new Error(message);};
// Creator can remove empty paragraphs on save. Preserve live spacing while
// comparing every nonempty line, including each code/name pair, in order.
const lines=text=>text.trim().split('\n').map(x=>x.trim()).filter(Boolean);
const asset=src=>src.match(/\/spectrum\/([^?]+)/)?.[1] || null;
// The linked original note's displayed date refreshes when its own update saves.
const settingsKey=s=>({...s,text:s.text.replace(/(引用笔记\n《金铲铲S18(?:冷门榜|阵容榜))\d{1,2}\.\d{1,2}(｜附阵容码》)/g,'$1<date>$2')});

export async function inspect(pw,surface){
  const url=await pw.url();
  const state=await pw.playwright.evaluate(s=>{
    const title=document.querySelector(s.title);
    const editor=document.querySelector(s.editor);
    if(!title || !editor)throw new Error('Editor surface changed or has not loaded');
    if(document.querySelectorAll(s.title).length!==1 || document.querySelectorAll(s.editor).length!==1)throw new Error('Ambiguous editor surface');
    const paragraphs=[...editor.querySelectorAll('p')].map((p,index)=>({index,text:p.textContent.trim(),topics:p.querySelectorAll('[data-topic]').length}));
    const topics=[...editor.querySelectorAll('[data-topic]')].map(e=>{const d=JSON.parse(e.getAttribute('data-topic'));return {id:d.id,name:d.name};});
    const imageNodes=[...document.querySelectorAll(s.images)];
    const fileInputs=[...document.querySelectorAll('input[type=file][multiple]')];
    const caps=fileInputs.flatMap(e=>[...e.parentElement.innerText.matchAll(/(\d+)\s*\/\s*(\d+)/g)]).filter(m=>Number(m[1])===imageNodes.length).map(m=>Number(m[2]));
    const page=document.body.innerText;const begin=page.indexOf('内容设置');const end=page.indexOf('笔记预览',begin);
    if(begin<0 || end<begin)throw new Error('Settings panel needs a new live surface mapping');
    return {title:title.value,paragraphs,topics,
      images:imageNodes.map(e=>({src:e.currentSrc||e.src,width:e.naturalWidth,height:e.naturalHeight})),
      image_limit:caps.length===1?caps[0]:null,
      settings:{text:page.slice(begin,end).trim(),checkboxes:[...document.querySelectorAll('input[type=checkbox]')].map(e=>e.checked)}};
  },surface);
  state.note_id=new URL(url).searchParams.get('id');
  state.images=state.images.map(x=>({...x,asset_id:asset(x.src)}));
  const body=state.paragraphs.filter(p=>!p.topics).map(p=>p.text);
  while(body.length&&!body.at(-1))body.pop();while(body.length&&!body[0])body.shift();
  state.body=body.join('\n');state.observed_at=new Date().toISOString();
  return state;
}

export function checkBaseline(live,note){
  check(live.note_id===note.note_id,'Wrong original note');
  check(live.title===note.baseline.title,'Title was edited since the published baseline; merge current changes');
  check(equal(lines(live.body),lines(note.baseline.body)),'Body was edited since baseline; merge current changes');
  check(equal(live.topics,note.baseline.topics),'Topic entities were edited since baseline; preserve current choices');
  const expected=note.baseline.images.map(x=>x.saved_asset_id||x.asset_id);
  check(expected.every(Boolean),'Published baseline is missing saved image IDs');
  check(equal(live.images.map(x=>x.asset_id),expected),'Published images differ from baseline');
  check(live.images.every(x=>x.width>0&&x.height>0),'Images have not finished loading');
  return true;
}

export async function createSession(pw,tab,note,surface){
  let receipt;
  try{receipt=JSON.parse(await fs.readFile(note.receipt_file,'utf8'));}
  catch(e){if(e.code!=='ENOENT')throw e;receipt=null;}
  const save=async()=>{const tmp=note.receipt_file+'.tmp';await fs.writeFile(tmp,JSON.stringify(receipt,null,2));await fs.rename(tmp,note.receipt_file);};
  const observe=()=>inspect(pw,surface);
  const refresh=async()=>{await tab.getAXState({emit:false});return observe();};
  const stable=live=>{check(live.note_id===note.note_id,'Original note changed');check(equal(live.topics,receipt.before.topics),'Topic entities changed');check(equal(settingsKey(live.settings),settingsKey(receipt.before.settings)),'Settings changed');};
  return {
    async preflight(){
      const live=await observe();
      if(receipt){
        check(receipt.note_id===note.note_id && equal(receipt.target_files,note.images.map(x=>x.png_sha256)),'Checkpoint belongs to another build');
        stable(live);
        return {stage:receipt.stage,can_resume:!receipt.intent,note_id:note.note_id};
      }
      checkBaseline(live,note);
      receipt={note_id:note.note_id,stage:note.action==='noop'?'noop':'checked',before:live,target_files:note.images.map(x=>x.png_sha256),uploaded:[],intent:null};
      await save();
      return {stage:receipt.stage,title:live.title,images:live.images.length,topics:live.topics.length,image_limit:live.image_limit};
    },
    async fillText(){
      check(receipt && ['checked','text_filled'].includes(receipt.stage),'Run preflight before editing text');
      const live=await observe();stable(live);
      const before=lines(note.baseline.body),after=lines(note.body);
      check(before.length===after.length,'Paragraph structure changed; needs a content merge');
      const ps=live.paragraphs.filter(p=>!p.topics&&p.text);
      check(ps.length===before.length,'Live paragraph structure changed');
      for(let i=0;i<before.length;i++)check(ps[i].text===before[i]||ps[i].text===after[i],'Paragraph was changed outside this update');
      check(live.title===note.baseline.title||live.title===note.title,'Title changed outside this update');
      // Retrying text operations is safe: every paragraph must be either its old or target value.
      for(let i=0;i<after.length;i++)if(ps[i].text!==after[i]){
        await pw.playwright.locator(surface.editor).locator('p').nth(ps[i].index).fill(after[i]);
      }
      if(live.title!==note.title)await pw.playwright.locator(surface.title).fill(note.title);
      const saved=await refresh();stable(saved);check(equal(lines(saved.body),after),'Text readback failed');
      check(saved.title===note.title,'Title readback failed');receipt.stage='text_filled';await save();
      return {stage:receipt.stage,topics:saved.topics.length};
    },
    async replaceImages({clickAdd,clickRemoveFirst}){
      check(receipt && ['text_filled','images_in_progress'].includes(receipt.stage),'Text must be filled before replacing media');
      check(!receipt.intent,'An upload/removal result is uncertain: inspect checkpoint before retrying');
      const live=await observe();stable(live);
      const originals=new Set(receipt.before.images.map(x=>x.src));
      const old=live.images.filter(x=>originals.has(x.src));
      const fresh=live.images.filter(x=>!originals.has(x.src));
      check(fresh.length===receipt.uploaded.length,'Upload state differs from checkpoint');
      check(live.image_limit && note.images.length<=live.image_limit,'Image limit unavailable or insufficient');
      check(live.images.every(x=>x.width>0&&x.height>0),'Wait for current images to load');
      // Make space without ever clearing the editor's last image. Caller supplies
      // grounded semantic clicks; the runtime never stores old page coordinates.
      const room=live.image_limit-live.images.length;
      const remaining=note.images.slice(receipt.uploaded.length);
      if(remaining.length && room>0){
        const batch=remaining.slice(0,room);
        receipt.stage='images_in_progress';receipt.intent={type:'upload',files:batch.map(x=>x.file),before:live.images.map(x=>x.src)};await save();
        const chooserPromise=pw.playwright.waitForEvent('filechooser',{timeoutMs:10000});
        await clickAdd();const chooser=await chooserPromise;check(await chooser.isMultiple(),'Wrong file chooser');
        await chooser.setFiles(batch.map(x=>x.file));
        const next=await refresh();stable(next);
        check(next.images.length===live.images.length+batch.length,'Upload pending or failed; inspect before retry');
        check(equal(next.images.slice(0,live.images.length).map(x=>x.src),live.images.map(x=>x.src)),'Existing image order changed');
        receipt.uploaded.push(...batch.map((x,i)=>({file:x.file,png_sha256:x.png_sha256,preview_src:next.images[live.images.length+i].src})));
        receipt.intent=null;await save();return {stage:receipt.stage,uploaded:receipt.uploaded.length,old_remaining:old.length};
      }
      if(old.length){
        check(live.images.length>1 && originals.has(live.images[0].src),'Old images must form a prefix; never clear the last image');
        receipt.stage='images_in_progress';receipt.intent={type:'remove',src:live.images[0].src,before:live.images.map(x=>x.src)};await save();
        await clickRemoveFirst();const next=await refresh();stable(next);
        check(equal(next.images.map(x=>x.src),live.images.slice(1).map(x=>x.src)),'Removal did not match the intended image');
        receipt.intent=null;await save();return {stage:receipt.stage,uploaded:receipt.uploaded.length,old_remaining:old.length-1};
      }
      check(equal(live.images.map(x=>x.src),receipt.uploaded.map(x=>x.preview_src)),'Uploaded image order changed');
      check(live.images.length===note.images.length,'Incomplete media set');
      receipt.stage='images_filled';await save();return {stage:receipt.stage,images:live.images.length};
    },
    async reconcile(){
      check(receipt?.intent,'There is no pending operation');
      const live=await refresh();stable(live);const intent=receipt.intent;
      if(intent.type==='upload'){
        check(equal(live.images.slice(0,intent.before.length).map(x=>x.src),intent.before),'Existing images changed during upload');
        if(live.images.length===intent.before.length)return {stage:'waiting_for_upload',retry_action:false};
        check(live.images.length===intent.before.length+intent.files.length,'Partial or unexpected upload; inspect the editor');
        const batch=note.images.slice(receipt.uploaded.length,receipt.uploaded.length+intent.files.length);
        check(equal(batch.map(x=>x.file),intent.files),'Pending upload belongs to another file list');
        receipt.uploaded.push(...batch.map((x,i)=>({file:x.file,png_sha256:x.png_sha256,preview_src:live.images[intent.before.length+i].src})));
      }else if(intent.type==='remove'){
        if(equal(live.images.map(x=>x.src),intent.before))return {stage:'removal_not_applied',retry_action:false};
        check(equal(live.images.map(x=>x.src),intent.before.slice(1)),'Removal result differs from the intended image');
      }else{return {stage:'submission_attempted',retry_action:false,next:'Inspect manager and saved original; never repeat submit'};}
      receipt.intent=null;await save();return {stage:receipt.stage,resumed:true};
    },
    async submit(clickSubmit){
      check(receipt?.stage==='images_filled'&&!receipt.intent,'Media/text have not been verified or submission was already attempted');
      check(note.visual_complete,'Inspect changed rendered images before submission');
      const live=await observe();stable(live);
      check(live.title===note.title&&equal(lines(live.body),lines(note.body)),'Editor content changed before submission');
      check(equal(live.images.map(x=>x.src),receipt.uploaded.map(x=>x.preview_src)),'Editor images changed before submission');
      check(live.images.every(x=>x.width>0&&x.height>0),'Media not ready');
      receipt.stage='submission_attempted';receipt.intent={type:'submit',at:new Date().toISOString()};await save();
      await clickSubmit();await tab.getAXState({emit:false});
      return {stage:receipt.stage,next:'Read manager result, reopen the original note, then savedReadback. Never submit again on an uncertain result.'};
    },
    async savedReadback(platform){
      check(['submission_attempted','saved_readback'].includes(receipt?.stage),'No matching submission checkpoint');
      const saved=await observe();stable(saved);
      check(saved.title===note.title&&equal(lines(saved.body),lines(note.body)),'Saved content does not match submitted content');
      check(saved.images.length===note.images.length&&saved.images.every(x=>x.asset_id&&x.width>0&&x.height>0),'Saved images incomplete');
      check(saved.images.every(x=>!receipt.before.images.some(old=>old.asset_id===x.asset_id)),'Old image still present after replacement');
      const platformEvidence=Object.fromEntries(['platform_status','manager_filter','manager_title','manager_url','manager_observed_at'].filter(k=>k in platform).map(k=>[k,platform[k]]));
      receipt.saved={...saved,...platformEvidence,settings_before:receipt.before.settings,
        uploaded_images:receipt.uploaded.map((x,i)=>({...x,asset_id:saved.images[i].asset_id}))};
      receipt.stage='saved_readback';receipt.intent=null;await save();
      const evidence=note.receipt_file.replace(/\.json$/,'-saved.json');await fs.writeFile(evidence,JSON.stringify(receipt.saved,null,2));
      return {stage:receipt.stage,evidence};
    },
    async runToReady(clicks,{budgetMs=20000}={}){
      const started=Date.now();
      if(!receipt)await this.preflight();
      if(receipt.stage==='noop')return {stage:'noop',images:note.images.length};
      if(receipt.intent){const r=await this.reconcile();if(!r.resumed)return r;}
      if(receipt.stage==='checked')await this.fillText();
      while(['text_filled','images_in_progress'].includes(receipt.stage)&&Date.now()-started<Math.min(budgetMs,45000)){
        const r=await this.replaceImages(clicks);if(r.stage==='images_filled')return r;
      }
      return {stage:receipt.stage,uploaded:receipt.uploaded.length,continue_in_same_session:receipt.stage==='images_in_progress'};
    },
    async inspect(){return observe();}
  };
}

export { lines, asset };
