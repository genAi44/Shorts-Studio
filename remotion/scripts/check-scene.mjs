// node scripts/check-scene.mjs <scene.tsx>
// Static gate for LLM-written scenes. Prints one JSON object: {ok, violations: [..], diagnostics: [..]}.
//  1. AST allowlist: imports only 'react' | 'remotion' | '../kit'; a default-exported component; no network / eval / fs /
//     dynamic import / timers / randomness / DOM globals / external URLs / raster refs / event handlers / CSS animation.
//  2. Type check (tsc API) of the file against the project's tsconfig; only diagnostics of THIS file are reported.
import fs from 'fs';
import path from 'path';
import {createRequire} from 'module';
import {fileURLToPath} from 'url';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '..');
const require = createRequire(path.join(root, 'package.json'));
const ts = require('typescript');

const file = path.resolve(process.argv[2]);
const src = fs.readFileSync(file, 'utf8');
const sf = ts.createSourceFile(file, src, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);

const ALLOWED_IMPORTS = new Set(['react', 'remotion', '../kit']);
const FORBIDDEN_IDENTS = new Set([
  'eval', 'Function', 'fetch', 'XMLHttpRequest', 'WebSocket', 'EventSource', 'require', 'process', 'window', 'document', 'globalThis',
  'self', 'localStorage', 'sessionStorage', 'indexedDB', 'navigator', 'location', 'setTimeout', 'setInterval', 'requestAnimationFrame',
  'Worker', 'SharedWorker', 'importScripts', 'Date', 'performance', 'crypto', 'XMLSerializer', 'Image', 'Audio',
]);
const FORBIDDEN_HOOKS = new Set(['useEffect', 'useLayoutEffect', 'useState', 'useReducer', 'useInsertionEffect', 'useSyncExternalStore']);
const FORBIDDEN_TAGS = new Set(['script', 'iframe', 'img', 'image', 'link', 'object', 'embed', 'video', 'audio', 'canvas', 'use']);
// GSAP is allowed only through useGsapTimeline (a paused timeline seeked from the frame): nothing that plays it on GSAP's own
// clock or runs code from it
const FORBIDDEN_GSAP = new Set(['play', 'resume', 'restart', 'reverse', 'ticker', 'delayedCall', 'globalTimeline', 'exportRoot', 'call',
  'eventCallback', 'onUpdate', 'onComplete', 'onStart', 'onRepeat', 'onReverseComplete', 'onInterrupt', 'registerPlugin', 'quickTo', 'quickSetter']);
const FORBIDDEN_STYLE_PROPS = new Set(['transition', 'transitionProperty', 'transitionDuration', 'animation', 'animationName', 'animationDuration', 'animationDelay', 'willChange']);
const violations = [];
const add = (node, msg) => {
  const {line} = sf.getLineAndCharacterOfPosition(node.getStart(sf));
  violations.push(`line ${line + 1}: ${msg}`);
};

let hasDefault = false;
const visit = (node) => {
  if (ts.isImportDeclaration(node)) {
    const spec = node.moduleSpecifier.text;
    if (!ALLOWED_IMPORTS.has(spec)) add(node, `import '${spec}' is not allowed (only react, remotion, ../kit)`);
  }
  if (ts.isExportDeclaration(node) && node.moduleSpecifier) add(node, 're-exports are not allowed');
  if (ts.isExportAssignment(node)) hasDefault = true;
  if ((ts.isFunctionDeclaration(node) || ts.isClassDeclaration(node)) && node.modifiers?.some((m) => m.kind === ts.SyntaxKind.DefaultKeyword)) hasDefault = true;
  if (ts.isCallExpression(node) && node.expression.kind === ts.SyntaxKind.ImportKeyword) add(node, 'dynamic import() is not allowed');
  if (ts.isIdentifier(node)) {
    const p = node.parent;
    const isPropName = (ts.isPropertyAccessExpression(p) && p.name === node) || (ts.isPropertyAssignment(p) && p.name === node)
      || (ts.isJsxAttribute(p) && p.name === node) || (ts.isBindingElement(p) && p.propertyName === node);
    if (!isPropName && FORBIDDEN_IDENTS.has(node.text)) add(node, `'${node.text}' is forbidden (no network, DOM, timers, wall-clock or eval)`);
    if (FORBIDDEN_HOOKS.has(node.text) && !ts.isImportSpecifier(p)) add(node, `hook '${node.text}' is forbidden: frames drive everything, no state or effects`);
  }
  if (ts.isPropertyAccessExpression(node) && ts.isIdentifier(node.expression) && node.expression.text === 'Math' && node.name.text === 'random') add(node, 'Math.random is forbidden (non-deterministic)');
  if (ts.isPropertyAccessExpression(node) && FORBIDDEN_GSAP.has(node.name.text)) add(node, `GSAP '.${node.name.text}' is forbidden: build the timeline with tl.to/from/fromTo/set at positions in seconds, the frame seeks it`);
  if (ts.isPropertyAssignment(node) && (ts.isIdentifier(node.name) || ts.isStringLiteral(node.name)) && FORBIDDEN_GSAP.has(node.name.text)) add(node, `GSAP '${node.name.text}' is forbidden: no callbacks, the frame seeks the timeline`);
  if ((ts.isJsxElement(node)) && node.openingElement.tagName.getText(sf) === 'style') {
    const css = node.children.map((c) => c.getText(sf)).join(' ');
    if (/(^|[^-])(animation|transition)\s*:|@keyframes|url\(/i.test(css)) add(node, '<style> may not use animation / transition / @keyframes / url(): animate with GSAP or spring/interpolate');
  }
  if (ts.isNewExpression(node) && ts.isIdentifier(node.expression) && node.expression.text === 'Date') add(node, 'new Date is forbidden');
  if (ts.isJsxOpeningElement(node) || ts.isJsxSelfClosingElement(node)) {
    const tag = node.tagName.getText(sf);
    if (FORBIDDEN_TAGS.has(tag)) add(node, `<${tag}> is forbidden`);
    if (tag === 'Counter') {
      const attrs = node.attributes.properties.filter((x) => ts.isJsxAttribute(x));
      const to = attrs.find((x) => x.name.getText(sf) === 'to');
      const lit = to && to.initializer && ts.isJsxExpression(to.initializer) && to.initializer.expression && ts.isNumericLiteral(to.initializer.expression) ? Number(to.initializer.expression.text) : null;
      const has = (n) => attrs.some((x) => x.name.getText(sf) === n);
      if (lit !== null && Number.isInteger(lit) && lit >= 1000 && lit <= 2100 && !has('year') && !has('suffix') && !has('decimals')) {
        add(node, `<Counter to={${lit}}> looks like a year and would print "${lit.toLocaleString('en-US')}": add the year prop (<Counter year to={${lit}} />); for a real count of ${lit} items add a suffix`);
      }
    }
    for (const a of node.attributes.properties) {
      if (ts.isJsxAttribute(a)) {
        const n = a.name.getText(sf);
        if (/^on[A-Z]/.test(n)) add(a, `event handler '${n}' is forbidden`);
        if (n === 'dangerouslySetInnerHTML') add(a, 'dangerouslySetInnerHTML is forbidden');
        if (n === 'href' || n === 'xlinkHref' || n === 'src') add(a, `attribute '${n}' (external resource) is forbidden`);
      }
    }
  }
  if (ts.isPropertyAssignment(node) && (ts.isIdentifier(node.name) || ts.isStringLiteral(node.name)) && FORBIDDEN_STYLE_PROPS.has(node.name.text)) {
    add(node, `style '${node.name.text}' is forbidden: CSS animation/transition is not frame-deterministic (use spring/interpolate)`);
  }
  if (ts.isStringLiteralLike(node) || ts.isTemplateExpression(node) || ts.isNoSubstitutionTemplateLiteral(node)) {
    const t = ts.isTemplateExpression(node) ? node.getText(sf) : node.text;
    if (/https?:\/\/|\/\/[a-z0-9.-]+\.[a-z]{2,}|javascript:|data:[a-z]+\/|@import|@keyframes/i.test(t)) add(node, 'external URL / data URI / css import is forbidden');
    if (/\.(png|jpe?g|gif|webp|bmp|avif|mp4|webm|mp3|wav)\b/i.test(t)) add(node, 'raster/media file reference is forbidden (use inline SVG, kit Icon, or data.* provided by the pipeline)');
    if (/url\((?!\s*['"]?#)/i.test(t)) add(node, 'url() may only reference an in-document #id');
  }
  ts.forEachChild(node, visit);
};
visit(sf);
if (!hasDefault) violations.push('the file must `export default` the scene component');

// ---- type check (only this file's diagnostics)
const cfgPath = path.join(root, 'tsconfig.json');
const cfg = ts.readConfigFile(cfgPath, ts.sys.readFile);
const parsed = ts.parseJsonConfigFileContent(cfg.config, ts.sys, root);
// Type-check as if the file lived in src/authored (where it will be copied), so '../kit' resolves wherever the file is.
const virtual = path.join(root, 'src', 'authored', path.basename(file));
const opts = {...parsed.options, noEmit: true};
const host = ts.createCompilerHost(opts);
const getSF = host.getSourceFile.bind(host);
host.getSourceFile = (fn, lang, ...rest) => (path.resolve(fn) === virtual ? ts.createSourceFile(fn, src, lang, true, ts.ScriptKind.TSX) : getSF(fn, lang, ...rest));
const exists = host.fileExists.bind(host);
host.fileExists = (fn) => path.resolve(fn) === virtual || exists(fn);
const readF = host.readFile.bind(host);
host.readFile = (fn) => (path.resolve(fn) === virtual ? src : readF(fn));
const program = ts.createProgram([virtual], opts, host);
const diagnostics = ts.getPreEmitDiagnostics(program, program.getSourceFile(virtual))
  .filter((d) => d.file && path.resolve(d.file.fileName) === virtual)
  .map((d) => {
    const {line} = d.file.getLineAndCharacterOfPosition(d.start || 0);
    return `line ${line + 1}: TS${d.code} ${ts.flattenDiagnosticMessageText(d.messageText, '\n')}`;
  });

console.log(JSON.stringify({ok: violations.length === 0 && diagnostics.length === 0, violations, diagnostics}));
