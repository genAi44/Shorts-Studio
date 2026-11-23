// Playwright MCP scenario (run with browser_run_code_unsafe). tablet = desktop|tablet|mobile, run3 = run name.
// Records a video per device to test-results/videos/<tag>/<device>/ and screenshots to test-results/shots/<tag>/.
// No paid API is called: the render is mocked at the network layer.
async (page) => {
  const DEVICE = 'tablet';
  const ROOT = 'C:/Users/mhama/Desktop/shorts-studio/.claude/worktrees/ai-video-quality-analysis-523cb4/test-results';
  const specs = {
    desktop: {viewport: {width: 1280, height: 800}},
    tablet: {viewport: {width: 768, height: 1024}, hasTouch: true, isMobile: true},
    mobile: {viewport: {width: 390, height: 844}, hasTouch: true, isMobile: true, deviceScaleFactor: 2},
  };
  const sp = specs[DEVICE];
  const browser = page.context().browser();
  const ctx = await browser.newContext({...sp, recordVideo: {dir: ROOT + '/videos/run3/' + DEVICE, size: sp.viewport}});
  const p = await ctx.newPage();
  const log = {device: DEVICE, steps: [], console: [], pageerrors: [], failed: [], bad: []};
  p.on('console', m => { if (['error', 'warning'].includes(m.type())) log.console.push(m.type() + ': ' + m.text().slice(0, 200)); });
  p.on('pageerror', e => log.pageerrors.push(String(e).slice(0, 200)));
  p.on('requestfailed', r => log.failed.push(r.method() + ' ' + r.url().slice(0, 90) + ' ' + ((r.failure() || {}).errorText || '')));
  p.on('response', r => { if (r.status() >= 400) log.bad.push(r.status() + ' ' + r.request().method() + ' ' + r.url().slice(0, 90)); });
  p.on('dialog', d => d.dismiss());
  const shot = async (name) => { try { await p.screenshot({path: ROOT + '/shots/run3/' + DEVICE + '-' + name + '.png', fullPage: false}); } catch (e) {} };
  const step = async (name, fn) => {
    const t0 = Date.now();
    try { const note = await fn(); log.steps.push({name, ok: true, ms: Date.now() - t0, note: note === undefined ? '' : note}); }
    catch (e) { log.steps.push({name, ok: false, ms: Date.now() - t0, err: String(e).slice(0, 220)}); await shot('FAIL-' + name.replace(/\W+/g, '_')); }
  };
  const overflow = () => p.evaluate(() => ({hscroll: document.documentElement.scrollWidth - innerWidth, wide: [...document.querySelectorAll('body *')].filter(e => { const r = e.getBoundingClientRect(); return r.width > 0 && (r.right > innerWidth + 2 || r.left < -2) && getComputedStyle(e).position !== 'fixed' && e.offsetParent !== null; }).slice(0, 6).map(e => (e.id || e.className || e.tagName).toString().slice(0, 30) + ' ' + Math.round(e.getBoundingClientRect().left) + '..' + Math.round(e.getBoundingClientRect().right))}));
  const tiny = () => p.evaluate(() => [...document.querySelectorAll('button,select,input,textarea,a')].filter(e => e.offsetParent !== null).map(e => ({t: (e.id || e.textContent || e.tagName).toString().trim().slice(0, 24), w: Math.round(e.getBoundingClientRect().width), h: Math.round(e.getBoundingClientRect().height)})).filter(x => x.h < 36 || x.w < 36).slice(0, 12));
  const unlabeled = () => p.evaluate(() => [...document.querySelectorAll('input,select,textarea')].filter(e => e.offsetParent !== null && !(e.labels && e.labels.length) && !e.getAttribute('aria-label')).length);

  await step('load', async () => { await p.goto('http://127.0.0.1:8742/'); await p.waitForSelector('#idea'); await shot('01-load'); return JSON.stringify(await overflow()); });
  await step('status chips visible', async () => { const n = await p.locator('text=جاهز').count(); if (!n) throw new Error('no status chips'); return n + ' chips'; });
  await step('llm health (inline result, no blocking alert)', async () => { await p.click('#bLlmHealth'); await p.waitForTimeout(2800); await shot('02-health'); const m = (await p.locator('#llmHealthMsg').textContent()) || ''; if (!m.trim()) throw new Error('no inline health result'); return m.slice(0, 80); });
  await step('llm logs open/close', async () => { await p.click('#bToggleLlmLogs'); await p.waitForTimeout(600); const open = await p.locator('#llmLogsContent').isVisible(); await p.click('#bToggleLlmLogs'); await p.waitForTimeout(300); const closed = !(await p.locator('#llmLogsContent').isVisible()); if (!open || !closed) throw new Error('toggle failed open=' + open + ' closed=' + closed); });
  await step('llm settings open/close', async () => { await p.click('#bToggleLlmSettings'); await p.waitForTimeout(600); await shot('03-llm-settings'); const o = await overflow(); await p.click('#bToggleLlmSettings'); return JSON.stringify(o); });
  await step('empty idea shows a message without a request', async () => { await p.fill('#idea', ''); await p.click('#bGen'); await p.waitForTimeout(500); const m = (await p.locator('#genMsg').textContent()) || ''; if (!m.trim()) throw new Error('no validation message'); return m; });
  await step('load sample script', async () => { await p.click('#bSample'); await p.waitForSelector('#editor:not([hidden])', {timeout: 15000}); await p.waitForTimeout(800); await shot('04-sample'); return JSON.stringify(await overflow()); });
  await step('title/desc/tags editable', async () => { await p.fill('#title', 'عنوان اختبار QA'); await p.fill('#desc', 'وصف'); await p.fill('#tags', 'a، b'); if ((await p.inputValue('#title')) !== 'عنوان اختبار QA') throw new Error('title not kept'); });
  await step('validate conditions', async () => { await p.click('#bVal'); await p.waitForTimeout(1200); return 'clicked'; });
  await step('add-part button is hidden by design', async () => 'visible=' + (await p.locator('#bAdd').isVisible()));
  await step('director: simple beats (no model)', async () => { await p.click('#bDirAuto'); await p.waitForTimeout(3500); await shot('05-director'); return JSON.stringify(await overflow()); });
  await step('visual library search (no broken images)', async () => { await p.fill('#vlQuery', 'map'); await p.click('#bVlSearch'); await p.waitForTimeout(2500); await shot('06-library'); const broken = await p.evaluate(() => [...document.images].filter(i => i.offsetParent !== null && i.getAttribute('src') && i.complete && i.naturalWidth === 0).map(i => i.getAttribute('src'))); if (broken.length) throw new Error('broken: ' + broken.join(',')); });
  await step('style presets x3', async () => { const out = []; for (const s of ['atlas', 'chalkboard', 'dossier']) { await p.selectOption('#presetSel', s); await p.waitForTimeout(900); const v = JSON.parse(await p.inputValue('#stJson')); out.push(s + ':' + v.preset + '/' + v.bg.type); } await shot('07-preset'); return out.join(' '); });
  await step('random style', async () => { await p.click('#bRand'); await p.waitForTimeout(1500); const v = JSON.parse(await p.inputValue('#stJson')); return v.name; });
  await step('invalid style JSON shows a message', async () => { await p.fill('#stJson', '{ broken'); await p.waitForTimeout(400); await shot('08-bad-json'); const msg = (await p.locator('#stMsg').textContent()) || ''; if (!msg.includes('JSON')) throw new Error('no invalid-JSON message: [' + msg + ']'); return msg; });
  await step('valid preset clears the invalid state, then preview frame', async () => { await p.selectOption('#presetSel', 'atlas'); await p.waitForTimeout(800); const bc = await p.evaluate(() => document.querySelector('#stJson').style.borderColor); if (bc) throw new Error('stale red border after valid preset: ' + bc); await p.click('#bPrev'); await p.waitForTimeout(1000); await p.waitForSelector('#bPrev:not([disabled])', {timeout: 200000}); await p.waitForTimeout(500); await shot('09-preview'); return 'ok'; });
  await step('production controls', async () => { await p.locator('#bRender').scrollIntoViewIfNeeded(); await shot('10-production'); const o = {voice: await p.locator('#voice option').count(), engine: await p.locator('#engine option').count(), photos: await p.isChecked('#photos')}; await p.uncheck('#photos'); await p.check('#photos'); return JSON.stringify(o); });
  await step('render with mocked backend (no paid TTS)', async () => {
    await p.route('**/api/render', r => r.fulfill({status: 200, contentType: 'application/json', body: JSON.stringify({job: 'qa-mock'})}));
    let n = 0;
    await p.route('**/api/job/qa-mock', r => { n++; const done = n > 3; r.fulfill({status: 200, contentType: 'application/json', body: JSON.stringify({id: 'qa-mock', state: done ? 'done' : 'running', progress: done ? 1 : n / 4, error: null, log: ['الصوت 1/8: hook'], warnings: [], result: done ? {video: 'short.mp4', url: '/outputs/qa-mock/short.mp4', duration: 50, title: 't', description: 'd', credits: ''} : null})}); });
    await p.click('#bRender'); await p.waitForTimeout(1500); await shot('11-render-progress'); await p.waitForTimeout(6000); await shot('12-render-done');
    return 'polls=' + n;
  });
  await step('final layout audit', async () => JSON.stringify({overflow: await overflow(), tiny: await tiny(), unlabeled: await unlabeled()}));
  await p.waitForTimeout(500);
  const v = p.video();
  await ctx.close();
  log.video = v ? await v.path() : null;
  return log;
}
