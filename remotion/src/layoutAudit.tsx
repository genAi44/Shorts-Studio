import React, {useEffect, useState} from 'react';
import {continueRender, delayRender, useCurrentFrame} from 'remotion';
import {CANVAS_HEIGHT, CANVAS_WIDTH, CAPTION_ZONE, SAFE_TOP} from './layout';

/**
 * Dev-only DOM audit (enabled by the `audit` input prop, used by scripts/smoke_test.py).
 * After the frame is laid out it measures every visible text node and logs `[AUDIT]{json}` to the browser console:
 *  - edge:    text box closer than EDGE px to the canvas border (or outside it)
 *  - overlap: two unrelated text boxes intersecting by more than 25% of the smaller one
 *  - tiny:    effective font size (after transforms) below MIN_FONT, unreadable on a phone
 * Elements inside [data-audit-ignore] (blurred backdrops) are skipped; [data-caption] marks caption text.
 */
const EDGE = 20;
const MIN_FONT = 22;

type Item = {dir: string; text: string; l: number; t: number; r: number; b: number; fs: number; el: Element; caption: boolean};

const ancestorOpacity = (el: Element): number => {
  let op = 1;
  for (let e: Element | null = el; e; e = e.parentElement) op *= parseFloat(getComputedStyle(e).opacity || '1');
  return op;
};

const collect = (): Item[] => {
  const items: Item[] = [];
  document.querySelectorAll('body *').forEach((el) => {
    if (el.closest('[data-audit-ignore]')) return;
    const own = Array.from(el.childNodes).filter((n) => n.nodeType === 3 && (n.textContent || '').trim().length > 0);
    if (!own.length) return;
    const cs = getComputedStyle(el);
    if (cs.visibility === 'hidden' || cs.display === 'none' || ancestorOpacity(el) < 0.35) return;
    const range = document.createRange();
    let l = Infinity, t = Infinity, rr = -Infinity, b = -Infinity;
    own.forEach((n) => {
      range.selectNodeContents(n);
      const q = range.getBoundingClientRect();
      if (q.width < 1 || q.height < 1) return;
      l = Math.min(l, q.left); t = Math.min(t, q.top); rr = Math.max(rr, q.right); b = Math.max(b, q.bottom);
    });
    if (!Number.isFinite(l) || rr - l < 2 || b - t < 2) return;
    if (rr <= 0 || l >= CANVAS_WIDTH || b <= 0 || t >= CANVAS_HEIGHT) return; // fully off-canvas (marquee/entrance)
    const r = {left: l, top: t, right: rr, bottom: b, width: rr - l, height: b - t};
    let fs = parseFloat(cs.fontSize) || 0;
    if (el instanceof SVGGraphicsElement) {
      const m = el.getScreenCTM();
      if (m) fs *= Math.abs(m.a);
    } else if ((el as HTMLElement).offsetWidth > 0) {
      fs *= el.getBoundingClientRect().width / (el as HTMLElement).offsetWidth;
    }
    const dir = cs.direction;
    items.push({
      dir,
      text: own.map((n) => (n.textContent || '').trim()).join(' ').slice(0, 40),
      l: r.left, t: r.top, r: r.right, b: r.bottom, fs, el,
      caption: !!el.closest('[data-caption]'),
    });
  });
  return items;
};

export const auditItems = (items: Item[]) => {
  const issues: {type: string; text: string; other?: string; box: number[]; obox?: number[]; fs?: number}[] = [];
  for (const it of items) {
    const box = [it.l, it.t, it.r, it.b].map(Math.round);
    if (it.l < EDGE || it.r > CANVAS_WIDTH - EDGE || it.t < 0 || it.b > CANVAS_HEIGHT) issues.push({type: 'edge', text: it.text, box});
    if (it.fs > 0 && it.fs < MIN_FONT && !it.el.closest('[data-audit-kit]')) issues.push({type: 'tiny', text: it.text, box, fs: Math.round(it.fs)});
    // Arabic must be right-to-left (the kit's ArText sets dir=rtl); a LTR Arabic run is mis-ordered
    if (/[\u0600-\u06FF]/.test(it.text) && it.dir !== 'rtl') issues.push({type: 'rtl', text: it.text, box});
    // scene text must stay inside the safe zones: not in the caption zone, not above the safe top
    if (!it.caption && !it.el.closest('[data-audit-kit]') && (it.b > CAPTION_ZONE.top + 12 && it.t < CAPTION_ZONE.bottom || it.t < SAFE_TOP - 8)) issues.push({type: 'zone', text: it.text, box});
  }
  for (let i = 0; i < items.length; i++) {
    for (let j = i + 1; j < items.length; j++) {
      const a = items[i], b = items[j];
      if (a.el.contains(b.el) || b.el.contains(a.el)) continue;
      if (a.fs < MIN_FONT || b.fs < MIN_FONT) continue; // unreadable text is already reported as 'tiny'
      // Range rects include the font's tall ascent/descent: compare the ink core (12% trimmed top and bottom)
      const ta = a.t + (a.b - a.t) * 0.12, ba = a.b - (a.b - a.t) * 0.12, tb = b.t + (b.b - b.t) * 0.12, bb = b.b - (b.b - b.t) * 0.12;
      const w = Math.min(a.r, b.r) - Math.max(a.l, b.l);
      const h = Math.min(ba, bb) - Math.max(ta, tb);
      if (w <= 0 || h <= 0) continue;
      const small = Math.min((a.r - a.l) * (a.b - a.t), (b.r - b.l) * (b.b - b.t));
      if ((w * h) / small > 0.25) {
        issues.push({type: 'overlap', text: a.text, other: b.text, box: [a.l, a.t, a.r, a.b].map(Math.round), obox: [b.l, b.t, b.r, b.b].map(Math.round)});
      }
    }
  }
  return issues;
};

export const LayoutAudit: React.FC = () => {
  const frame = useCurrentFrame();
  const [handle] = useState(() => delayRender('layout-audit'));
  useEffect(() => {
    const id = setTimeout(() => {
      try {
        const items = collect();
        console.log('[AUDIT]' + JSON.stringify({frame, texts: items.filter((i) => !i.caption).length, issues: auditItems(items)}));
      } finally {
        continueRender(handle);
      }
    }, 150);
    return () => clearTimeout(id);
  }, [frame, handle]);
  return null;
};
