import React, {useMemo} from 'react';
import {spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {EnterKind, Pop, PRESETS, useFont, useSpring} from './hooks';
import {CaptionScrim} from './fx';
import {CAPTION_ZONE, HEADLINE_ZONE} from './layout';
import {on, rgba, useTheme} from './theme';
import {Word} from './types';

// عنوان الشاشة للمقطع: الكلمات تدخل تباعاً (RTL)، وصندوق/حركة حسب الستايل.
export const Headline: React.FC<{text: string}> = ({text}) => {
  const th = useTheme();
  const font = useFont();
  const h = th.st.headline;
  const p = th.p;
  const words = text.split(/\s+/).filter(Boolean);
  const right = h.pos === 'center';
  const prog = useSpring(0.05, 'smooth');
  const kind: EnterKind = h.enter === 'drop' ? 'drop' : h.enter === 'pop' ? 'pop' : h.enter === 'fade' ? 'fade' : h.enter === 'slide' ? 'right' : 'rise';
  const wipe = h.enter === 'wipe';
  let box: React.CSSProperties = {};
  let color = rgba(p.text);
  let shadow = true;
  if (h.box === 'pill') { box = {background: rgba(p.accent), borderRadius: 999, padding: '14px 52px'}; color = on(p.accent); shadow = false; }
  else if (h.box === 'tag') { box = {background: rgba(p.accent2), borderRadius: 16, padding: '12px 42px'}; color = on(p.accent2); shadow = false; }
  else if (h.box === 'bar') { box = {borderRight: `14px solid ${rgba(p.accent)}`, paddingRight: 30}; }
  const headTop = Math.max(HEADLINE_ZONE.top, th.headY - 62);
  return (
    <div style={{position: 'absolute', left: HEADLINE_ZONE.left, right: HEADLINE_ZONE.right, top: headTop, display: 'flex', justifyContent: right ? 'flex-start' : 'center', clipPath: wipe ? `inset(0 0 0 ${(1 - Math.min(1, prog)) * 100}%)` : undefined}}>
      <div style={{position: 'relative', ...box}}>
        <div dir="rtl" lang="ar" style={{...font, display: 'flex', flexWrap: 'wrap', justifyContent: right ? 'flex-start' : 'center', columnGap: 18, fontSize: h.size, lineHeight: 1.3, color, textShadow: shadow ? th.shadow : undefined, textAlign: right ? 'right' : 'center'}}>
          {words.map((w, i) => (
            <Pop key={i} kind={wipe ? 'fade' : kind} delay={0.05 + i * 0.07} dist={44} preset={kind === 'pop' ? 'bouncy' : 'snappy'}>{w}</Pop>
          ))}
        </div>
        {h.box === 'underline' && (
          <div style={{position: 'absolute', right: 0, left: 0, bottom: -8, height: 10, borderRadius: 5, background: rgba(p.accent), transformOrigin: 'right center', scale: `${Math.min(1, prog)} 1`}} />
        )}
      </div>
    </div>
  );
};

type Chunk = Word[];
const DANGLING = new Set(['و', 'في', 'من', 'إلى', 'الى', 'على', 'عن', 'عند', 'مع', 'ثم', 'أو', 'أن', 'إن', 'لكن', 'حتى', 'بين', 'كل', 'التي', 'الذي', 'ما', 'لا', 'قد', 'هذا', 'هذه']);
const chunkWords = (words: Word[], maxChars: number, maxN: number): Chunk[] => {
  const out: Chunk[] = [];
  let cur: Word[] = [];
  let n = 0;
  for (const w of words) {
    if (cur.length && (n + w.t.length > maxChars || cur.length >= maxN)) {
      // never leave a dangling particle (من، في، إلى، و...) at the end of a caption: it starts the next one, so the phrase reads whole
      const tail: Word[] = [];
      while (cur.length > 1 && DANGLING.has(cur[cur.length - 1].t.replace(/[،؛؟?!.,:;]/g, ''))) tail.unshift(cur.pop() as Word);
      out.push(cur);
      cur = tail;
      n = tail.reduce((a, x) => a + x.t.length + 1, 0);
    }
    cur.push(w);
    n += w.t.length + 1;
  }
  if (cur.length) out.push(cur);
  return out;
};

// ترجمة متزامنة مع الكلمة المنطوقة (توقيت ElevenLabs).
export const Captions: React.FC<{words: Word[]}> = ({words}) => {
  const th = useTheme();
  const font = useFont();
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const c = th.st.caption;
  const p = th.p;
  const chunks = useMemo(() => chunkWords(words, c.size >= 68 ? 20 : 26, c.size >= 68 ? 4 : 5), [words, c.size]);
  const t = frame / fps;
  let ci = -1;
  chunks.forEach((ch, i) => { if (ch[0].s <= t + 0.02) ci = i; });
  if (ci < 0) return null;
  const chunk = chunks[ci];
  const start = Math.round(chunk[0].s * fps);
  const pop = spring({frame: frame - start, fps, config: PRESETS.snappy});
  const snapOpacity = Math.min(1, 0.78 + pop * 0.45);
  let act = 0;
  chunk.forEach((w, i) => { if (w.s <= t + 0.02) act = i; });
  const mode = c.mode;
  const hl = mode === 'box_word' ? 'box' : mode === 'underline' ? 'underline' : mode === 'stroke' && c.hl === 'box' ? 'color' : c.hl;
  const wp = spring({frame: frame - Math.round(chunk[act].s * fps), fps, config: PRESETS.bouncy});
  const wrapStyle: React.CSSProperties = {};
  if (mode === 'pill') Object.assign(wrapStyle, {background: rgba(p.c1, 0.84), borderRadius: 999, padding: '16px 44px'});
  const inner = (
    <div dir="rtl" lang="ar" style={{...font, display: 'flex', alignItems: 'center', justifyContent: 'center', columnGap: Math.round(c.size * 0.34), fontSize: c.size, lineHeight: 1.3, color: rgba(p.text), opacity: snapOpacity, translate: `0 ${(1 - pop) * 10}px`, scale: 0.96 + 0.04 * pop, ...wrapStyle}}>
      {chunk.map((w, i) => {
        const active = i === act;
        const st: React.CSSProperties = {display: 'inline-block', textShadow: mode === 'stroke' ? undefined : th.shadow};
        if (mode === 'stroke') Object.assign(st, {WebkitTextStroke: `${Math.round(c.size / 8)}px ${rgba(p.c2)}`, paintOrder: 'stroke fill'});
        if (active) {
          st.color = rgba(p.accent);
          if (hl === 'scale') st.scale = 1 + 0.18 * Math.min(1.2, wp);
          if (hl === 'box') Object.assign(st, {background: rgba(p.accent), color: on(p.accent), borderRadius: 18, padding: '0 16px', textShadow: undefined, scale: 1 + 0.07 * Math.min(1, wp)});
          if (hl === 'underline') Object.assign(st, {color: rgba(p.text), borderBottom: `8px solid ${rgba(p.accent)}`});
          // glow اللفظة النشطة (لجميع الأوضاع عدا box)
          if (hl !== 'box') st.filter = `drop-shadow(0 0 ${Math.round(10 * Math.min(1, wp))}px ${rgba(p.accent, 0.85)})`;
        }
        return <span key={i} style={st}>{w.t}</span>;
      })}
    </div>
  );
  const captionTop = Math.max(CAPTION_ZONE.top, th.capY - c.size * 1.1);
  if (mode === 'bar') {
    return (
      <>
        <CaptionScrim captionY={captionTop - 80} />
        <div data-caption style={{position: 'absolute', left: 0, right: 0, top: captionTop, height: c.size * 2.2, background: rgba(p.c1, 0.88), borderTop: `6px solid ${rgba(p.accent)}`, display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 20}}>{inner}</div>
      </>
    );
  }
  return (
    <>
      <CaptionScrim captionY={captionTop - 80} />
      <div data-caption style={{position: 'absolute', left: CAPTION_ZONE.left, right: CAPTION_ZONE.right, top: captionTop, height: c.size * 2.2, display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 20}}>{inner}</div>
    </>
  );
};
