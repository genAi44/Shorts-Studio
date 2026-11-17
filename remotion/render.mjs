// node render.mjs <spec.json> <out.mp4> <publicDir> [quality]
// quality: 'draft' | 'standard' | 'high' | 'cinematic'
import fs from 'fs';
import path from 'path';
import {fileURLToPath} from 'url';
import {bundle} from '@remotion/bundler';
import {renderMedia, selectComposition} from '@remotion/renderer';

const here = path.dirname(fileURLToPath(import.meta.url));
const [, , specPath, out, pubDir, qualityArg] = process.argv;
const absoluteSpec = path.resolve(specPath);
const absoluteOut = path.resolve(out);
const absolutePubDir = pubDir ? path.resolve(pubDir) : undefined;
const spec = JSON.parse(fs.readFileSync(absoluteSpec, 'utf8'));
const browserExecutable = process.env.REMOTION_BROWSER || undefined;
const log = (o) => console.log(JSON.stringify(o));

// تنقيط الجودة السينمائية
const qualitySettings = {
  draft: {crf: 28, preset: 'veryfast'},
  standard: {crf: 23, preset: 'veryfast'},
  high: {crf: 20, preset: 'medium'},
  cinematic: {crf: 18, preset: 'slow'},
};
const quality = qualityArg || process.env.REMOTION_QUALITY || 'standard';
const settings = qualitySettings[quality] || qualitySettings.standard;

log({stage: 'bundle', quality});
const serveUrl = await bundle({entryPoint: path.join(here, 'src/index.ts'), publicDir: absolutePubDir});
const inputProps = {spec};
const composition = await selectComposition({serveUrl, id: 'Short', inputProps, browserExecutable});
log({stage: 'render', frames: composition.durationInFrames, quality, crf: settings.crf, preset: settings.preset});
await renderMedia({
  composition, serveUrl, codec: 'h264', outputLocation: absoluteOut, inputProps,
  crf: settings.crf, x264Preset: settings.preset,
  browserExecutable, concurrency: Number(process.env.REMOTION_CONCURRENCY) || null,
  scale: Number(process.env.REMOTION_SCALE) || 1,
  onProgress: ({progress}) => log({progress}),
});
log({stage: 'done'});
