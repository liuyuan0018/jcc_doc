// Usage: node scripts/export_png.cjs input.svg output.png
const path = require('path');
let sharp;
try { sharp = require('sharp'); }
catch {
  sharp = require(path.join(process.env.CODEX_NODE_MODULES || '/Users/lyu/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules', 'sharp'));
}
const [input, output] = process.argv.slice(2);
if (!input || !output) throw new Error('Provide input SVG and output PNG');
sharp(input).png().toFile(output).then(info => console.log(info)).catch(err => { console.error(err); process.exitCode = 1; });
