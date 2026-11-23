// Error-handling + keyboard scenario (run with browser_run_code_unsafe). run3 = run name. Failures are injected at the network layer.
async (page) => {
  const ROOT = 'C:/Users/mhama/Desktop/shorts-studio/.claude/worktrees/ai-video-quality-analysis-523cb4/test-results';
  const browser = page.context().browser();
  const ctx = await browser.newContext({viewport: {width: 1280, height: 800}, recordVideo: {dir: ROOT + '/videos/run3/errors', size: {width: 1280, height: 800}}});
  const p = await ctx.newPage();
  const log = {device: 'errors', steps: [], pageerrors: [], bad: []};
  p.on('pageerror', e => log.pageerrors.push(String(e).slice(0, 200)));
  p.on('response', r => { if (r.status() >= 400) log.bad.push(r.status() + ' ' + r.request().method() + ' ' + r.url().slice(0, 80)); });
  p.on('dialog', d => d.dismiss());
  const shot = async (n) => { try { await p.screenshot({path: ROOT + '/shots/run3/errors-' + n + '.png'}); } catch (e) {} };
  const step = async (name, fn) => {
    const t0 = Date.now();
    try { const note = await fn(); log.steps.push({name, ok: true, ms: Date.now() - t0, note: note === undefined ? '' : note}); }
    catch (e) { log.steps.push({name, ok: false, ms: Date.now() - t0, err: String(e).slice(0, 200)}); await shot('FAIL-' + name.replace(/\W+/g, '_')); }
  };
  const text = async (sel) => ((await p.locator(sel).first().textContent()) || '').trim();

  await step('load + sample', async () => { await p.goto('http://127.0.0.1:8742/'); await p.click('#bSample'); await p.waitForSelector('#editor:not([hidden])'); });
  await step('keyboard: Tab order and a visible focus ring', async () => {
    await p.goto('http://127.0.0.1:8742/'); const seen = [];
    for (let i = 0; i < 6; i++) { await p.keyboard.press('Tab'); seen.push(await p.evaluate(() => document.activeElement.id || document.activeElement.tagName)); }
    await p.goto('http://127.0.0.1:8742/'); await p.keyboard.press('Tab');
    const ring = await p.evaluate(() => { const cs = getComputedStyle(document.activeElement); return cs.outlineStyle !== 'none' && parseFloat(cs.outlineWidth) > 0; });
    if (!ring) throw new Error('no visible focus ring'); return seen.join(' > ');
  });
  await step('Enter in the empty idea box does not crash', async () => { await p.fill('#idea', ''); await p.focus('#idea'); await p.keyboard.press('Enter'); await p.waitForTimeout(300); });
  await step('server 500 on /api/script shows the message', async () => {
    await p.route('**/api/script', r => r.fulfill({status: 500, contentType: 'application/json', body: JSON.stringify({error: 'خطأ تجريبي من الخادم'})}));
    await p.fill('#idea', 'فكرة اختبار'); await p.click('#bGen'); await p.waitForTimeout(1500); await shot('01-script-500');
    const m = await text('#genMsg'); await p.unroute('**/api/script'); if (!m.includes('خطأ')) throw new Error('no error shown: [' + m + ']'); return m;
  });
  await step('network failure on /api/script is not silent', async () => {
    await p.route('**/api/script', r => r.abort('connectionrefused'));
    await p.click('#bGen'); await p.waitForTimeout(1500); await shot('02-script-offline');
    const m = await text('#genMsg'); await p.unroute('**/api/script'); if (!m.trim()) throw new Error('silent failure'); return m;
  });
  await step('director 500 shows the error', async () => {
    await p.click('#bSample'); await p.waitForSelector('#editor:not([hidden])'); await p.waitForFunction(() => !document.querySelector('#dirMsg').textContent.includes('جارٍ'), null, {timeout: 90000});
    await p.route('**/api/direct', r => r.fulfill({status: 500, contentType: 'application/json', body: JSON.stringify({error: 'تعذر الإخراج'})}));
    await p.click('#bDirAuto'); await p.waitForTimeout(1500); await shot('03-direct-500');
    const m = await text('#dirMsg'); await p.unroute('**/api/direct'); if (!m.includes('تعذر')) throw new Error('director error not shown: [' + m + ']'); return m;
  });
  await step('preview 500 shows the error and re-enables the button', async () => {
    await p.route('**/api/preview', r => r.fulfill({status: 500, contentType: 'application/json', body: JSON.stringify({error: 'فشل الرسم التجريبي'})}));
    await p.click('#bPrev'); await p.waitForTimeout(1500); await shot('04-preview-500');
    const m = await text('#pvMsg'); const dis = await p.isDisabled('#bPrev'); await p.unroute('**/api/preview');
    if (!m.includes('فشل') || dis) throw new Error('msg=[' + m + '] disabled=' + dis); return m;
  });
  await step('render failure shows the error', async () => {
    await p.route('**/api/render', r => r.fulfill({status: 200, contentType: 'application/json', body: JSON.stringify({job: 'qa-err'})}));
    await p.route('**/api/job/qa-err', r => r.fulfill({status: 200, contentType: 'application/json', body: JSON.stringify({id: 'qa-err', state: 'error', progress: 0.3, error: 'فشل التوليد التجريبي', log: [], warnings: [], result: null})}));
    await p.locator('#bRender').scrollIntoViewIfNeeded(); await p.click('#bRender'); await p.waitForTimeout(4000); await shot('05-render-error');
    const body = await p.locator('body').innerText(); await p.unroute('**/api/render'); await p.unroute('**/api/job/qa-err');
    if (!body.includes('فشل التوليد التجريبي')) throw new Error('render error text not shown'); return 'shown';
  });
  await step('render success without a video url is handled', async () => {
    await p.route('**/api/render', r => r.fulfill({status: 200, contentType: 'application/json', body: JSON.stringify({job: 'qa-nourl'})}));
    await p.route('**/api/job/qa-nourl', r => r.fulfill({status: 200, contentType: 'application/json', body: JSON.stringify({id: 'qa-nourl', state: 'done', progress: 1, error: null, log: [], warnings: [], result: {title: 't'}})}));
    await p.click('#bRender'); await p.waitForTimeout(4000); await shot('06-render-nourl');
    const bad = []; p.once('response', () => {}); const html = await p.locator('#result').innerHTML(); await p.unroute('**/api/render'); await p.unroute('**/api/job/qa-nourl');
    if (html.includes('src="undefined"') || html.includes('href="undefined"')) throw new Error('broken video/download link'); return 'no broken link';
  });
  await step('fact check completes (real Gemini call, free tier)', async () => { await p.click('#bFact'); await p.waitForFunction(() => !document.querySelector('#bFact').disabled, null, {timeout: 120000}); await shot('07-fact'); return (await p.locator('#bFact').evaluate(e => e.closest('.card').innerText)).slice(150, 260).replace(/\n/g, ' '); });
  await p.waitForTimeout(400);
  const v = p.video(); await ctx.close(); log.video = v ? await v.path() : null;
  return log;
}
