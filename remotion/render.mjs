// node render.mjs <spec.json> <out.mp4> <publicDir>
import fs from 'fs';
import path from 'path';
import {fileURLToPath} from 'url';
import {bundle} from '@remotion/bundler';
import {renderMedia, selectComposition} from '@remotion/renderer';

const here = path.dirname(fileURLToPath(import.meta.url));
const [, , specPath, out, pubDir] = process.argv;
const absoluteSpec = path.resolve(specPath);
const absoluteOut = path.resolve(out);
const absolutePubDir = pubDir ? path.resolve(pubDir) : undefined;
const spec = JSON.parse(fs.readFileSync(absoluteSpec, 'utf8'));
const browserExecutable = process.env.REMOTION_BROWSER || undefined;
const log = (o) => console.log(JSON.stringify(o));

log({stage: 'bundle'});
const serveUrl = await bundle({entryPoint: path.join(here, 'src/index.ts'), publicDir: absolutePubDir});
const inputProps = {spec};
const composition = await selectComposition({serveUrl, id: 'Short', inputProps, browserExecutable});
log({stage: 'render', frames: composition.durationInFrames});
await renderMedia({
  composition, serveUrl, codec: 'h264', outputLocation: absoluteOut, inputProps, crf: 23, x264Preset: 'veryfast',
  browserExecutable, concurrency: Number(process.env.REMOTION_CONCURRENCY) || null,
  scale: Number(process.env.REMOTION_SCALE) || 1,
  onProgress: ({progress}) => log({progress}),
});
log({stage: 'done'});
