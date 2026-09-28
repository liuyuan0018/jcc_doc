// Batched SVG rendering. Only a short receipt reaches the caller.
const fs = require('fs');
const path = require('path');
let sharp;
try { sharp = require('sharp'); }
catch { sharp = require(path.join(process.env.CODEX_NODE_MODULES || '/Users/lyu/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules', 'sharp')); }
if (process.argv[2] === '--fingerprint') {
  process.stdout.write(JSON.stringify({node:process.version, sharp:sharp.versions}));
} else {
  (async () => {
    const jobs = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
    for (const job of jobs) {
      const info = await sharp(job.svg).png().toFile(job.png);
      if (info.width !== job.width || info.height !== job.height) throw new Error('Unexpected image dimensions: '+job.png);
    }
    process.stdout.write(JSON.stringify({rendered:jobs.length}));
  })().catch(e => { process.stderr.write(String(e)); process.exitCode=1; });
}
