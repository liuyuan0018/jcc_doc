import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
import createEngine from '../../tank-lab/dist/engine.mjs';
import {params,validate,traitText,CATEGORIES} from '../../tank-lab/dist/model.js';
import {filterResultRows,bestResultRows} from '../../tank-lab/dist/result-filter.js';

const HERE=path.dirname(fileURLToPath(import.meta.url));
const ROOT=path.resolve(HERE,'../..'),LAB=path.join(ROOT,'tank-lab');
const read=async p=>JSON.parse(await fs.readFile(p,'utf8'));
const recipePath=path.resolve(process.argv[2]??path.join(HERE,'recipe.json'));
const recipe=await read(recipePath),OUT=path.resolve(ROOT,recipe.output);
await fs.mkdir(path.join(OUT,'assets'),{recursive:true});
const jobDir=recipe.sourceDirectory?path.resolve(ROOT,recipe.sourceDirectory):path.join(LAB,'.local-jobs',recipe.sourceJob);
const job=await read(path.join(jobDir,'config.json'));
const sourceBytes=await fs.readFile(path.join(jobDir,'rows.jsonl'));
const sourceRows=sourceBytes.toString('utf8').trim().split('\n').map(s=>JSON.parse(s));
const scenarios=await read(path.join(LAB,'dist/data/scenarios.json'));
const {items}=await read(path.join(LAB,'dist/data/catalog.json'));
const heroes=await read(path.join(LAB,'dist/data/heroes.json'));
const wasm=await fs.readFile(path.join(LAB,'dist/engine.wasm'));
const engine=await createEngine({thisProgram:'/frontline',wasmBinary:wasm});
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const close=(a,b,label)=>assert.ok(Math.abs(a-b)<=1e-5+Math.abs(b)*1e-8,`${label}: ${a} != ${b}`);
let runs=0,sourceFieldChecks=0,frameChecks=0;
function simulate(config){
  validate(config,scenarios,items);
  const p=params(config),ptr=engine._malloc(p.length*8);let value;
  try{engine.HEAPF64.set(p,ptr/8);value=JSON.parse(engine.ccall('run_web','string',['number','number'],[ptr,p.length]));}finally{engine._free(ptr);}
  assert.ok(!value.error,value.error);runs++;
  assert.equal(value.frames.length,value.result.frame+1);
  assert.equal(value.frames.at(-1)[17],Number(value.result.alive));
  return value;
}
const rows=sourceRows.map(r=>{
  const s=scenarios.find(s=>s.index===r.scenario);assert.ok(s);
  const config={...job.request.config,scenario:r.scenario,items:[...r.items],aug:r.aug&3,
    soloPlate:!!(r.aug&4),glove:r.glove,dps:r.pressure?.passedDps??job.request.config.dps,
    wound:r.wound,attackers:r.attackers,resistanceMode:r.resistanceMode??0};
  return {...r,hero:s.hero,star:s.star,cost:s.cost,traits:s.traits,slots:s.slots,config};
});
const filtered=filterResultRows(rows,recipe.filters);
const globalPerHero=recipe.main.selectionMode==='per-hero-global';
if(globalPerHero){
  assert.equal(recipe.filters.cat,'','Global per-hero selection must not fix an equipment category');
  assert.equal(recipe.filters.aug,'','Global per-hero selection must not fix an augment');
  assert.equal(job.request.pool,'all');assert.equal(job.request.augScope,'all');
}
const best=bestResultRows(filtered,'pressure').sort((a,b)=>(b.pressure?.passedDps??-1)-(a.pressure?.passedDps??-1)||a.slots-b.slots||a.scenario-b.scenario);
// One screen representative per hero; tied alternatives remain in the selection manifest.
const unique=[...new Map(best.map(r=>[r.hero,best.find(b=>b.hero===r.hero)])).values()];
const selected=recipe.main.heroes?recipe.main.heroes.map(name=>unique.find(r=>r.hero===name)):unique.slice(0,recipe.main.topCount);
assert.equal(selected.length,recipe.main.topCount);
assert.ok(selected.every(Boolean),'A named comparison hero has no eligible result');
assert.ok(selected.every(r=>Number.isFinite(r.pressure.passedDps)&&!r.pressure.ceilingReached));
assert.ok(selected.every(r=>r.config.seconds===30),'v1 video template requires a 30-second observation window');
const shared=selected[0];
for(const r of selected){
  if(!globalPerHero){
    assert.equal(r.category,shared.category,'Do not mix equipment resources without explicit global per-hero selection');
    assert.equal(r.config.aug,shared.config.aug);
    assert.equal(r.config.soloPlate,shared.config.soloPlate);
  }
  for(const k of ['seconds','wound','woundStart','woundEnd','resistanceMode','attackers','physical','target','lock','pause','skills','ap'])
    assert.equal(r.config[k],shared.config[k],`Mixed condition: ${k}`);
}

async function buildFromRow(r,label){
  const hero=heroes.find(h=>h.name===r.hero);assert.ok(hero);
  const portrait=path.join(LAB,'dist',hero.image),dest='assets/'+path.basename(portrait);
  await fs.copyFile(portrait,path.join(OUT,dest));
  return {hero:r.hero,star:r.star,cost:r.cost,traits:r.traits,traitLabel:traitText(r),
    teamSlots:r.slots+(r.config.aug===2?1:0),label:label??r.hero,portrait:dest,
    portraitSha256:sha(await fs.readFile(portrait)),equipment:r.items.map(i=>items[i].name),
    config:r.config,pressure:r.pressure};
}
function verifySource(r){
  const q=simulate(r.config);
  for(const [k,v] of Object.entries(r.result)){
    if(typeof v==='number')close(q.result[k],v,`${r.hero}.${k}`);else assert.equal(q.result[k],v);
    sourceFieldChecks++;
  }
  for(let d=job.request.config.dps;d<=r.pressure.passedDps;d+=job.request.pressure.step)
    assert.equal(simulate({...r.config,dps:d}).result.alive,true,`${r.hero} failed within source passing interval`);
  assert.equal(simulate({...r.config,dps:r.pressure.failedDps}).result.alive,false);
}
selected.forEach(verifySource);
const mainBuilds=await Promise.all(selected.map(r=>buildFromRow(r,recipe.main.heroLabels?.[r.hero])));
function packRound(builds,dps){
  const replays=builds.map(b=>{
    const config={...b.config,dps},q=simulate(config);
    q.frames.forEach((f,i)=>{assert.equal(f[0],i);assert.ok(f.every(Number.isFinite));assert.ok(f[1]>=0&&f[3]>=0);frameChecks++;});
    return {config,...q};
  });
  return {dps,seconds:builds[0].config.seconds,replays};
}
const mainRounds=[...new Set(selected.map(r=>r.pressure.failedDps))].sort((a,b)=>a-b).map(d=>packRound(mainBuilds,d));
const source={job:recipe.sourceJob,rowsSha256:sha(sourceBytes),engineSha256:sha(wasm),
  recipeSha256:sha(await fs.readFile(recipePath)),filters:recipe.filters,matchingScenarios:filtered.length,
  comparedHeroes:unique.length,pressureDefinition:'固定配置从基础档逐档重置，连续通过至首次失败；不是数学意义上的全局极限。',
  selectionTies:best.filter(r=>selected.some(s=>s.hero===r.hero)).map(r=>({hero:r.hero,scenario:r.scenario,traits:r.traits,items:r.items,pressure:r.pressure}))};
if(recipe.sourceDirectory)source.directory=recipe.sourceDirectory;
if(recipe.main.heroes)source.selectionMethod='Named comparison heroes; inclusion does not claim these are the overall top four.';
if(globalPerHero){
  source.selectionMode='per-hero-global';
  source.perHeroSelection=selected.map(r=>{
    const candidates=filtered.filter(c=>c.hero===r.hero&&c.star===r.star);
    const highest=Math.max(...candidates.map(c=>c.pressure?.passedDps??-1));
    assert.equal(r.pressure.passedDps,highest);
    return {hero:r.hero,star:r.star,summaryRows:candidates.length,
      baselineBuildCases:candidates.reduce((n,c)=>n+c.runs,0),
      searchedCategories:[...new Set(candidates.map(c=>c.category))].sort(),
      searchedAugments:[...new Set(candidates.map(c=>c.aug))].sort(),
      highestPassedDps:highest,selectedItems:r.items,selectedAugment:r.aug,
      selectedScenario:r.scenario,tiedSummaryWinners:candidates.filter(c=>c.pressure?.passedDps===highest).length};
  });
}
const common={schemaVersion:1,source,simFps:30,frameFields:['frame','hp','maxHp','shield','mana','manaCap','lockFrames','pauseFrames','casts','attacks','heal','shieldUsed','damage','armor','mr','transformed','untargetable','alive','blockedMana'],
  render:recipe.render,modelNotice:'机制模拟 · 非实机录像',
  conditions:{seconds:shared.config.seconds,wound:shared.config.wound,resistanceMode:shared.config.resistanceMode,
    attackers:shared.config.attackers,physicalShare:shared.config.physical,
    aug:selected.every(r=>r.config.aug===shared.config.aug)?shared.config.aug:null,
    category:selected.every(r=>r.category===shared.category)?shared.category:null},
  limitations:['技能锁蓝尚未逐英雄实机核验','固定每秒3个伤害包；集火人数仅参与石像鬼计算','全程重伤和减抗，不含真实走位与敌方技能',
    globalPerHero?'全装备池独立选装；不同英雄的资源类型可不同，本片比较当前模型中的配置上限':'同资源与环境，英雄费用及羁绊类型不同，均在画面标明']};
const main={...common,...recipe.main,kind:'hero-pressure',builds:mainBuilds,rounds:mainRounds,
  scopeLabel:recipe.main.scopeLabel??`允许${Math.max(...filtered.flatMap(r=>Object.values(r.traits)))}羁绊 · ${CATEGORIES[shared.category]}`,
  introCaption:recipe.main.introCaption??'各穿自己的最优配置，一起加压。',
  outroCaption:recipe.main.outroCaption??'只比较这组条件下的持续承压能力。',pressureStart:job.request.config.dps,pressureStep:job.request.pressure.step};
await fs.writeFile(path.join(OUT,main.id+'.json'),JSON.stringify(main));
console.log('Main:',mainBuilds.map(b=>`${b.hero} ${b.pressure.passedDps}`).join(', '));

let tierBuilds=[];
if(recipe.detail){
const target=unique.find(r=>r.hero===recipe.detail.hero);assert.ok(target,'Detail hero not present');
const pool=recipe.detail.pool.map(name=>{const i=items.find(i=>i.name===name);assert.ok(i,`Unknown item ${name}`);return i;});
const fixed=items.find(i=>i.name===recipe.detail.fixedItem);assert.ok(fixed);
assert.ok(pool.every(i=>i.category===0));assert.equal(fixed.category,2);
const candidates=[];
for(let a=0;a<pool.length;a++)for(let b=a;b<pool.length;b++){
  if(a===b&&pool[a].unique)continue;
  const ids=[pool[a].index,pool[b].index,fixed.index],config={...target.config,items:ids};
  let passedDps=null,failedDps=null;
  for(let d=recipe.detail.pressureStart;d<=recipe.detail.pressureMax;d+=recipe.detail.pressureStep){
    const r=simulate({...config,dps:d}).result;
    if(!r.alive){failedDps=d;break;}passedDps=d;
  }
  candidates.push({items:ids,equipment:ids.map(i=>items[i].name),pressure:{passedDps,failedDps,ceilingReached:failedDps===null},config});
}
const usable=candidates.filter(c=>c.pressure.passedDps!==null&&!c.pressure.ceilingReached)
 .sort((a,b)=>a.pressure.passedDps-b.pressure.passedDps||(new Set(b.items).size-new Set(a.items).size)||a.items[0]-b.items[0]||a.items[1]-b.items[1]);
const scores=[...new Set(usable.map(c=>c.pressure.passedDps))];
const tiers=recipe.detail.quantiles.map(q=>usable.find(c=>c.pressure.passedDps===scores[Math.round(q*(scores.length-1))]));
assert.equal(new Set(tiers.map(t=>t.pressure.passedDps)).size,tiers.length,'Pool did not produce distinct tiers');
for(let i=1;i<tiers.length;i++)assert.ok(tiers[i].pressure.passedDps-tiers[i-1].pressure.passedDps>=recipe.detail.minTierGap,'Tiers too close; do not fabricate a gap');
// Keep old v1 recipes reproducible; new recipes show the strongest lane first.
const displayOrder=recipe.detail.displayOrder??(recipe.version===1?'ascending':'descending');
assert.ok(['ascending','descending'].includes(displayOrder));
const displayTiers=[...tiers].sort((a,b)=>(displayOrder==='descending'?-1:1)*(a.pressure.passedDps-b.pressure.passedDps));
tierBuilds=await Promise.all(displayTiers.map((c,i)=>buildFromRow({...target,...c,config:{...c.config,dps:c.pressure.passedDps}},'配装 '+String.fromCharCode(65+i))));
// Pressure still rises over time; only screen lanes and their replay ownership change.
const tierRounds=tiers.map(c=>c.pressure.failedDps).sort((a,b)=>a-b).map(d=>packRound(tierBuilds,d));
const detail={...common,...recipe.detail,kind:'build-tiers',builds:tierBuilds,rounds:tierRounds,
  displayOrder,scopeLabel:'固定同一羁绊与海克斯 · 每次只换配装',introCaption:recipe.detail.introCaption??'同一个英雄，三套配装，能拉开多大差距？',
  outroCaption:'这是配装梯度示例，不是所有对局的通用推荐。',
  candidateSelection:{pool:recipe.detail.pool,fixedItem:recipe.detail.fixedItem,candidateCount:candidates.length,
    quantiles:recipe.detail.quantiles,method:'对候选池中合法两件组合逐档承压，按不同通过档位的分位点选三套；不混用不同羁绊或资源。',candidates}};
await fs.writeFile(path.join(OUT,detail.id+'.json'),JSON.stringify(detail));
}
await fs.copyFile(recipePath,path.join(OUT,'recipe.json'));
await fs.copyFile(recipePath,path.join(OUT,'render-recipe.json'));
const validation={passed:true,simulationRuns:runs,sourceFieldChecks,traceFramesChecked:frameChecks,
  independentRoundReset:true,commonDamagePerRound:true,logicalFps:30,source,
  main:mainBuilds.map(b=>({hero:b.hero,pressure:b.pressure,equipment:b.equipment})),
  detail:tierBuilds.map(b=>({label:b.label,pressure:b.pressure,equipment:b.equipment}))};
await fs.writeFile(path.join(OUT,'data-verification.json'),JSON.stringify(validation,null,2));
console.log('Detail:',validation.detail);console.log('Exported',OUT,`${runs} simulations; ${frameChecks} replay frames checked`);
