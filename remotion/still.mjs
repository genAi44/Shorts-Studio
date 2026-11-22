// node still.mjs <spec.json> <out.jpg | out_%d.jpg> <frame[,frame...]> <publicDir>
import fs from 'fs';
import path from 'path';
import {fileURLToPath} from 'url';
import {bundle} from '@remotion/bundler';
import {renderStill, selectComposition} from '@remotion/renderer';

const here = path.dirname(fileURLToPath(import.meta.url));
const [, , specPath, out, frame, pubDir] = process.argv;
const absoluteSpec = path.resolve(specPath);
const absoluteOut = path.resolve(out);
const absolutePubDir = pubDir ? path.resolve(pubDir) : undefined;
const spec = JSON.parse(fs.readFileSync(absoluteSpec, 'utf8'));
const browserExecutable = process.env.REMOTION_BROWSER || undefined;
const serveUrl = await bundle({entryPoint: path.join(here, 'src/index.ts'), publicDir: absolutePubDir});
const audit = process.env.AUDIT === '1';
const inputProps = audit ? {spec, audit: true} : {spec};
const composition = await selectComposition({serveUrl, id: 'Short', inputProps, browserExecutable});
for (const f of String(frame).split(',')) {
  const fr = Math.min(Number(f), composition.durationInFrames - 1);
  const logs = [];
  const output = out.replace('%d', String(f));
  await renderStill({composition, serveUrl, output, frame: fr, inputProps, imageFormat: 'jpeg', jpegQuality: 90, browserExecutable,
    onBrowserLog: audit ? (l) => { if (l.text.startsWith('[AUDIT]')) logs.push(JSON.parse(l.text.slice(7))); } : undefined});
  if (audit) fs.writeFileSync(output + '.audit.json', JSON.stringify(logs.at(-1) ?? {frame: fr, issues: [], missing: true}));
}
console.log(JSON.stringify({stage: 'done'}));
