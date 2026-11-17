import path from 'node:path';
import {bundle} from '@remotion/bundler';
import {selectComposition, renderStill} from '@remotion/renderer';

const REM_DIR = process.cwd();
const b = await bundle({entryPoint: path.join(REM_DIR, 'src', 'index.ts'), publicDir: path.join(REM_DIR, 'public')});
const modes = [
  'generative_canvas'
];

for (const m of modes) {
  const c = await selectComposition({serveUrl: b, id: 'ComponentShowcase', inputProps: {mode: m}});
  const outPath = path.join(REM_DIR, '..', 'tests', 'renders', `still_${m}.png`);
  await renderStill({
    composition: c,
    serveUrl: b,
    output: outPath,
    frame: 50,
    inputProps: {mode: m},
    imageFormat: 'png',
  });
  console.log(`Rendered still_${m}.png`);
}

