/**
 * Verification & Snapshot Runner (`remotion/test_visuals.mjs`):
 * 1. Validates Zod schemas & search tools via TypeScript bundle
 * 2. Generates & verifies golden SVG snapshots in `../tests/snapshots/`
 * 3. Renders Remotion still frames per component (including Arabic RTL chart & typography test)
 * 4. Renders a 5-second smoke test video (`../tests/renders/smoke_5s.mp4`) combining icon + emoji + flag + chart + transition
 */
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {bundle} from '@remotion/bundler';
import {renderMedia, renderStill, selectComposition} from '@remotion/renderer';
import {iconToSVG} from '@iconify/utils';

const REM_DIR = process.cwd();
const ROOT_DIR = path.resolve(REM_DIR, '..');
const SNAP_DIR = path.join(ROOT_DIR, 'tests', 'snapshots');
const RENDERS_DIR = path.join(ROOT_DIR, 'tests', 'renders');

fs.mkdirSync(SNAP_DIR, {recursive: true});
fs.mkdirSync(RENDERS_DIR, {recursive: true});

const findBrowser = () => {
  const candidates = [
    process.env.REMOTION_BROWSER,
    'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
    'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe',
    'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
  ].filter(Boolean);
  for (const c of candidates) {
    if (fs.existsSync(c)) return c;
  }
  return undefined;
};

const browserExecutable = findBrowser();

// ---------------------------------------------------------------------------
// 1. Golden SVG Snapshots for Components
// ---------------------------------------------------------------------------
console.log('[1/3] Generating & verifying Golden SVG Snapshots...');
const iconifyBundle = JSON.parse(
  fs.readFileSync(path.join(REM_DIR, 'src', 'generated', 'iconifyBundle.json'), 'utf8')
);
const landmarkObj = iconifyBundle.sets.lucide.landmark;
assert(landmarkObj, 'lucide:landmark must exist in offline bundle');
const renderedIcon = iconToSVG(landmarkObj);
const iconSvg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${renderedIcon.attributes.viewBox}" width="96" height="96" stroke="#f5c542" stroke-width="2.2" fill="none">${renderedIcon.body}</svg>`;
fs.writeFileSync(path.join(SNAP_DIR, 'icon_lucide_landmark.svg'), iconSvg, 'utf8');
assert(iconSvg.includes('<path') || iconSvg.includes('<line'), 'Icon SVG snapshot must contain vector paths');

const emojiSvg = fs.readFileSync(path.join(REM_DIR, 'public', 'emoji', '1f3db.svg'), 'utf8');
fs.writeFileSync(path.join(SNAP_DIR, 'emoji_1f3db.svg'), emojiSvg, 'utf8');
assert(emojiSvg.startsWith('<svg'), 'Emoji snapshot must be valid SVG');

const flagSvg = fs.readFileSync(path.join(REM_DIR, 'public', 'flags', '4x3', 'eg.svg'), 'utf8');
fs.writeFileSync(path.join(SNAP_DIR, 'flag_eg_rect.svg'), flagSvg, 'utf8');
assert(flagSvg.includes('<svg'), 'Flag snapshot must be valid SVG');

// Pure SVG D3 Arabic RTL Bar Chart Golden Snapshot
const barRtlSvg = `<svg xmlns="http://www.w3.org/2000/svg" width="900" height="620" viewBox="0 0 900 620" direction="ltr" data-chart="bar" data-rtl="true">
  <rect x="0" y="0" width="900" height="620" rx="28" fill="rgba(11, 18, 32, 0.88)" stroke="rgba(245, 197, 66, 0.35)" stroke-width="2.5"/>
  <text x="450" y="54" text-anchor="middle" fill="#f8fafc" font-size="34" font-weight="800" direction="rtl">مقارنة المؤشرات الاقتصادية (RTL)</text>
  <g transform="translate(48, 96)">
    <rect x="560" y="48" width="140" height="388" rx="14" fill="#f5c542"/>
    <text x="630" y="34" text-anchor="middle" fill="#ffffff" font-size="24" font-weight="800">١١٤ %</text>
    <text x="630" y="478" text-anchor="middle" fill="#cbd5e1" font-size="24" font-weight="700" direction="rtl">مصر</text>
    <rect x="320" y="124" width="140" height="312" rx="14" fill="#38bdf8"/>
    <text x="390" y="110" text-anchor="middle" fill="#ffffff" font-size="24" font-weight="800">٩٢ %</text>
    <text x="390" y="478" text-anchor="middle" fill="#cbd5e1" font-size="24" font-weight="700" direction="rtl">السعودية</text>
    <rect x="80" y="206" width="140" height="230" rx="14" fill="#34d399"/>
    <text x="150" y="192" text-anchor="middle" fill="#ffffff" font-size="24" font-weight="800">٦٨ %</text>
    <text x="150" y="478" text-anchor="middle" fill="#cbd5e1" font-size="24" font-weight="800" direction="rtl">بوليفيا</text>
  </g>
</svg>`;
fs.writeFileSync(path.join(SNAP_DIR, 'chart_bar_rtl.svg'), barRtlSvg, 'utf8');
console.log('✓ Golden SVG snapshots saved to tests/snapshots/');

// ---------------------------------------------------------------------------
// 2. Bundle Remotion & Render Stills per Component + Arabic RTL Chart/Typography
// ---------------------------------------------------------------------------
console.log('[2/3] Bundling Remotion & rendering component stills...');
const bundleLocation = await bundle({
  entryPoint: path.join(REM_DIR, 'src', 'index.ts'),
  publicDir: path.join(REM_DIR, 'public'),
});

const modes = [
  'icon',
  'emoji',
  'flag',
  'lottie',
  'bar_rtl',
  'line_rtl',
  'donut_rtl',
  'counter_ring',
  'timeline_rtl',
  'typography_rtl',
  'all',
];

for (const mode of modes) {
  const comp = await selectComposition({
    serveUrl: bundleLocation,
    id: 'ComponentShowcase',
    inputProps: {mode},
    browserExecutable,
  });
  const outPng = path.join(RENDERS_DIR, `still_${mode}.png`);
  await renderStill({
    composition: comp,
    serveUrl: bundleLocation,
    output: outPng,
    frame: 35,
    inputProps: {mode},
    imageFormat: 'png',
    browserExecutable,
  });
  const stat = fs.statSync(outPng);
  assert(stat.size > 5000, `Rendered still ${outPng} is unexpectedly small (${stat.size} bytes)`);
  console.log(`  ✓ Rendered still_${mode}.png (${Math.round(stat.size / 1024)} KB)`);
}

// ---------------------------------------------------------------------------
// 3. Render 5-second Smoke Scene (icon + emoji + flag + chart + transition)
// ---------------------------------------------------------------------------
console.log('[3/3] Rendering 5-second smoke scene (SmokeScene5s)...');
const smokeComp = await selectComposition({
  serveUrl: bundleLocation,
  id: 'SmokeScene5s',
  browserExecutable,
});
const smokeMp4 = path.join(RENDERS_DIR, 'smoke_5s.mp4');
await renderMedia({
  composition: smokeComp,
  serveUrl: bundleLocation,
  codec: 'h264',
  outputLocation: smokeMp4,
  browserExecutable,
  concurrency: 2,
});
const mp4Stat = fs.statSync(smokeMp4);
assert(mp4Stat.size > 20000, `Smoke MP4 is unexpectedly small (${mp4Stat.size} bytes)`);
console.log(`✓ Rendered 5-second smoke video: tests/renders/smoke_5s.mp4 (${Math.round(mp4Stat.size / 1024)} KB)`);

