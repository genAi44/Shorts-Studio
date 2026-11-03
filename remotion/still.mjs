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
const inputProps = {spec};
const composition = await selectComposition({serveUrl, id: 'Short', inputProps, browserExecutable});
for (const f of String(frame).split(',')) {
  const fr = Math.min(Number(f), composition.durationInFrames - 1);
  await renderStill({composition, serveUrl, output: out.replace('%d', String(f)), frame: fr, inputProps, imageFormat: 'jpeg', jpegQuality: 90, browserExecutable});
}
console.log(JSON.stringify({stage: 'done'}));
