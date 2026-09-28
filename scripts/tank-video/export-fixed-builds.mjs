// Export only the named builds with the frozen engine; no equipment enumeration.
import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';

const specPath = path.resolve(process.argv[2]);
const spec = JSON.parse(fs.readFileSync(specPath, 'utf8'));
const input = path.resolve(spec.inputDir);
const engineDir = path.resolve(spec.engineDir ?? spec.inputDir);
const read = name => JSON.parse(fs.readFileSync(path.join(input, name), 'utf8'));
const {items} = read('catalog.json'), scenarios = read('scenarios.json');
const {DEFAULT, params, validate} = await import(pathToFileURL(path.join(input, 'model.js')));
const {default: Module} = await import(pathToFileURL(path.join(engineDir, 'engine.mjs')));
const engine = await Module({thisProgram: 'fixed-builds'});
const sc = scenarios.find(s => s.index === spec.config.scenario);
assert.ok(sc); assert.equal(spec.config.seconds, 30);
assert.equal(spec.builds.length, 8);
assert.equal(new Set(spec.builds.map(b => b.key)).size, 8);
const hash = file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
let totalSimulations = 0;
function simulate(config) {
  validate(config, scenarios, items);
  const p = params(config), ptr = engine._malloc(p.length * 8);
  let out;
  try {
    engine.HEAPF64.set(p, ptr / 8);
    out = JSON.parse(engine.ccall('run_web', 'string', ['number', 'number'], [ptr, p.length]));
  } finally { engine._free(ptr); }
  assert.ok(!out.error, out.error);
  assert.equal(out.frames.length, out.result.frame + 1);
  assert.equal(out.frames.at(-1)[17], Number(out.result.alive));
  for (const [i, f] of out.frames.entries()) {
    assert.equal(f[0], i); assert.ok(f.every(Number.isFinite));
    assert.ok(f[1] >= 0 && f[3] >= 0);
  }
  if (out.result.alive) assert.equal(out.result.frame, 900);
  if (spec.includePresentation) {
    assert.equal(out.presentation?.schemaVersion, 1, 'Engine lacks presentation telemetry');
    assert.equal(out.presentation.fps, 30);
    assert.equal(out.presentation.frames.length, out.frames.length);
    out.presentation.frames.forEach((f, i) => {
      assert.equal(f[0], i); assert.ok(f.every(Number.isFinite));
      assert.equal(f[1], out.frames[i][13]); assert.equal(f[2], out.frames[i][14]);
    });
  }
  totalSimulations++;
  return {dps: config.dps, result: out.result,
    frames: out.frames.map(f => [f[0], +f[1].toFixed(4), +f[2].toFixed(4),
      +f[3].toFixed(4), f[8], f[17]]),
    events: out.events.map(e => [e[0], e[1], +e[2].toFixed(4)]),
    ...(spec.includePresentation ? {presentation: out.presentation} : {})};
}
const builds = spec.builds.map(b => {
  const ids = b.itemNames.map(n => {
    const item = items.find(i => i.name === n && i.category === 0);
    assert.ok(item, `Unknown ordinary item: ${n}`); return item.index;
  });
  const chain = [];
  for (let dps = spec.startDps; dps <= spec.maxDps; dps += spec.step) {
    const run = simulate({...DEFAULT, ...spec.config, items: ids, dps});
    chain.push(run); if (!run.result.alive) break;
  }
  const fail = chain.at(-1);
  assert.equal(fail.result.alive, false, `${b.key}: expand upper bound`);
  const passedDps = chain.at(-2)?.dps ?? null;
  if (b.baseline) {
    assert.equal(passedDps, b.baseline.passedDps, `${b.key}: baseline pass changed`);
    assert.equal(fail.dps, b.baseline.failedDps, `${b.key}: baseline fail changed`);
  }
  console.log(`${b.key} ${b.label}: pass ${passedDps}, fail ${fail.dps} @ frame ${fail.result.frame}`);
  return {...b, items: ids, passedDps, failedDps: fail.dps, failedFrame: fail.result.frame,
    failedSeconds: +(fail.result.frame / 30).toFixed(2), chain};
});
const result = {schemaVersion: spec.includePresentation ? 2 : 1, purpose: spec.purpose,
  hero: {name: sc.hero, star: sc.star, cost: sc.cost, traits: sc.traits, slots: sc.slots, scenario: sc.index},
  aug: spec.config.aug | (spec.config.soloPlate ? 4 : 0), augLabel: spec.augLabel,
  environment: {...spec.config, startDps: spec.startDps, step: spec.step},
  source: {inputDir: spec.inputDir, ...(spec.engineDir ? {engineDir: spec.engineDir} : {}), specPath, specSha256: hash(specPath),
    hashes: Object.fromEntries(['engine.mjs','engine.wasm','model.js','catalog.json','scenarios.json']
      .map(n => [n, hash(path.join(n.startsWith('engine.') ? engineDir : input, n))]))},
  totalSimulations, builds,
  ranking: [...builds].sort((a,b) => b.passedDps-a.passedDps)
    .map(({key,label,passedDps,failedDps}) => ({key,label,passedDps,failedDps}))};
const output = path.resolve(spec.output);
fs.mkdirSync(path.dirname(output), {recursive: true});
fs.writeFileSync(output, JSON.stringify(result));
console.log(JSON.stringify({ok: true, totalSimulations, output, ranking: result.ranking}));
