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

type Item = {dir: string; text: string; l: number; t: number; r: number; b: number; fs: number; el: Element; caption: boolean; icon?: boolean};

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
  // icons are not text, but text drawn over them is just as unreadable: audit them as boxes (>= 40 px, visible)
  document.querySelectorAll('[data-audit-icon]').forEach((el) => {
    if (el.closest('[data-audit-ignore]') || ancestorOpacity(el) < 0.6) return; // faint ghost icons are decoration
    const q = el.getBoundingClientRect();
    if (q.width < 40 || q.height < 40 || q.right <= 0 || q.left >= CANVAS_WIDTH) return;
    // hidden behind an opaque card? sample a few points: if none of them hits the icon, it is not visible
    const pts = [[0.5, 0.5], [0.3, 0.3], [0.7, 0.3], [0.3, 0.7], [0.7, 0.7]];
    const seen = pts.some(([fx, fy]) => {
      const top = document.elementFromPoint(q.left + q.width * fx, q.top + q.height * fy);
      return !!top && (el.contains(top) || top.contains(el) === false && top.closest('svg') === el);
    });
    if (!seen && pts.every(([fx, fy]) => { const top = document.elementFromPoint(q.left + q.width * fx, q.top + q.height * fy); return !!top && !(top instanceof SVGElement); })) return;
    items.push({dir: 'ltr', text: '[icon]', l: q.left, t: q.top, r: q.right, b: q.bottom, fs: 999, el, caption: false, icon: true});
  });
  return items;
};

export const auditItems = (items: Item[]) => {
  const issues: {type: string; text: string; other?: string; box: number[]; obox?: number[]; fs?: number}[] = [];
  for (const it of items) {
    if (it.icon) continue;
    const box = [it.l, it.t, it.r, it.b].map(Math.round);
    if (it.l < EDGE || it.r > CANVAS_WIDTH - EDGE || it.t < 0 || it.b > CANVAS_HEIGHT) issues.push({type: 'edge', text: it.text, box});
    if (it.fs > 0 && it.fs < MIN_FONT && !it.el.closest('[data-audit-kit]')) issues.push({type: 'tiny', text: it.text, box, fs: Math.round(it.fs)});
    // Arabic must be right-to-left (the kit's ArText sets dir=rtl); a LTR Arabic run is mis-ordered
    if (/[\u0600-\u06FF]/.test(it.text) && it.dir !== 'rtl') issues.push({type: 'rtl', text: it.text, box});
    // scene text must stay inside the safe zones: not in the caption zone, not above the safe top
    if (!it.caption && !it.el.closest('[data-audit-kit]') && (it.b > CAPTION_ZONE.top + 12 && it.t < CAPTION_ZONE.bottom || it.t < SAFE_TOP - 8)) issues.push({type: 'zone', text: it.text, box});
  }
  // authored scenes that draw a map: nothing else may sit on the map stage (the card/lens/labels live there)
  const mapEl = typeof document !== 'undefined' ? document.querySelector('[data-audit-kit="map"]') : null;
  if (mapEl) {
    const m = mapEl.getBoundingClientRect();
    for (const it of items) {
      if (it.caption || it.el.closest('[data-audit-kit]')) continue;
      if (it.b > m.top + 40 && it.t < m.bottom - 40 && it.r > m.left && it.l < m.right) {
        issues.push({type: 'map', text: it.text, box: [it.l, it.t, it.r, it.b].map(Math.round), obox: [m.left, m.top, m.right, m.bottom].map(Math.round)});
      }
    }
  }
  for (let i = 0; i < items.length; i++) {
    for (let j = i + 1; j < items.length; j++) {
      const a = items[i], b = items[j];
      if (a.el.contains(b.el) || b.el.contains(a.el)) continue;
      if (a.icon && b.icon) continue;
      if (a.fs < MIN_FONT || b.fs < MIN_FONT) continue; // unreadable text is already reported as 'tiny'
      // Range rects include the font's tall ascent/descent: compare the ink core (12% trimmed top and bottom)
      const ta = a.t + (a.b - a.t) * 0.12, ba = a.b - (a.b - a.t) * 0.12, tb = b.t + (b.b - b.t) * 0.12, bb = b.b - (b.b - b.t) * 0.12;
      const w = Math.min(a.r, b.r) - Math.max(a.l, b.l);
      const h = Math.min(ba, bb) - Math.max(ta, tb);
      if (w <= 0 || h <= 0) continue;
      const small = Math.min((a.r - a.l) * (a.b - a.t), (b.r - b.l) * (b.b - b.t));
      if ((w * h) / small > (a.icon || b.icon ? 0.2 : 0.15)) {
        issues.push({type: 'overlap', text: a.text, other: b.text, box: [a.l, a.t, a.r, a.b].map(Math.round), obox: [b.l, b.t, b.r, b.b].map(Math.round)});
      }
    }
  }
  return issues;
};

/** union box of everything the scene drew (text + icons, captions excluded): used to reject near-empty scenes */
const bboxOf = (items: Item[]): number[] | null => {
  const v = items.filter((i) => !i.caption);
  if (!v.length) return null;
  return [Math.min(...v.map((i) => i.l)), Math.min(...v.map((i) => i.t)), Math.max(...v.map((i) => i.r)), Math.max(...v.map((i) => i.b))].map(Math.round);
};

/** the designer's hero SVG as actually rendered: on-canvas box, how much of its viewBox the drawn content covers, visible shapes */
const heroOf = () => {
  const host = document.querySelector('[data-hero-svg]');
  const svg = host?.querySelector('svg');
  if (!host || !svg) return null;
  const q = svg.getBoundingClientRect();
  let cover = 0;
  try {
    const bb = svg.getBBox();
    const vb = svg.viewBox.baseVal;
    cover = vb && vb.width > 0 && vb.height > 0 ? Math.min(1, (bb.width * bb.height) / (vb.width * vb.height)) : 0;
  } catch { cover = 0; }
  let painted = 0;
  svg.querySelectorAll('path, rect, circle, ellipse, line, polyline, polygon').forEach((el) => {
    if (el.closest('defs, clipPath, mask, pattern, symbol, marker')) return;
    const cs = getComputedStyle(el);
    const r = el.getBoundingClientRect();
    const paint = (cs.fill !== 'none' && parseFloat(cs.fillOpacity || '1') > 0.02) || (cs.stroke !== 'none' && parseFloat(cs.strokeWidth || '0') > 0);
    if (paint && cs.display !== 'none' && cs.visibility !== 'hidden' && ancestorOpacity(el) > 0.05 && (r.width > 0.5 || r.height > 0.5)) painted++;
  });
  return {box: [q.left, q.top, q.right, q.bottom].map(Math.round), cover: Math.round(cover * 1000) / 1000, painted, opacity: Math.round(ancestorOpacity(host) * 100) / 100};
};

/** widest visible [data-hero] element (the scene's main drawing), or null when the scene marks none */
const heroBox = (): number[] | null => {
  let best: DOMRect | null = null;
  const ink = document.querySelector('[data-hero-ink]');  // an illustration: the bounds of what is drawn, not of its box
  if (ink && ancestorOpacity(ink) >= 0.35) {
    const q = ink.getBoundingClientRect();
    return [q.left, q.top, q.right, q.bottom].map(Math.round);
  }
  document.querySelectorAll('[data-hero]').forEach((el) => {
    if (ancestorOpacity(el) < 0.35) return;
    const q = el.getBoundingClientRect();
    if (!best || q.width > best.width) best = q;
  });
  const b = best as DOMRect | null;
  return b ? [b.left, b.top, b.right, b.bottom].map(Math.round) : null;
};

export const LayoutAudit: React.FC = () => {
  const frame = useCurrentFrame();
  const [handle] = useState(() => delayRender('layout-audit'));
  useEffect(() => {
    const id = setTimeout(() => {
      try {
        const items = collect();
        console.log('[AUDIT]' + JSON.stringify({frame, texts: items.filter((i) => !i.caption).length, bbox: bboxOf(items), issues: auditItems(items), hero: heroOf(), heroInk: heroBox(), strings: items.filter((i) => !i.caption && !i.icon).map((i) => i.text).slice(0, 60)}));
      } finally {
        continueRender(handle);
      }
    }, 150);
    return () => clearTimeout(id);
  }, [frame, handle]);
  return null;
};
