import React, {CSSProperties, useContext} from 'react';

import {AbsoluteFill, interpolate, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {SafeImg} from './SafeImg';
import {Icon} from './icons';

import {clamp01, enterStyle, useIdle, useProgress, useSpring} from './hooks';

import {MapLayoutCtx, MotionCtx, rgba, useTheme} from './theme';
import {BEAT_ZONE} from './layout';
import {Beat, RGB} from './types';
import {FireSparks, FloatBadge, MapOverlay} from './fx';
export {PhotoBeat} from './photoBeat';



const mix = (a: RGB, b: RGB, t: number): RGB => [0, 1, 2].map((i) => Math.round(a[i] + (b[i] - a[i]) * t)) as RGB;



// ------------------------------------------------------------------ خطوط مزدوجة داخل الجملة

export const useFont2 = (): CSSProperties => {

  const th = useTheme();

  return {fontFamily: `${th.family2}, 'Noto Kufi Arabic', sans-serif`, fontWeight: th.st.weight2};

};



// أي كلمات تأخذ الخط الثاني حسب نمط المونتاج.

export const isAlt = (i: number, n: number, pat: string): boolean => {

  if (n < 2) return false;

  if (pat === 'alt') return i % 2 === 1;

  if (pat === 'tail') return i >= Math.ceil(n / 2);

  if (pat === 'head') return i < Math.ceil(n / 2);

  return false;

};



const MixWord: React.FC<{w: string; i: number; n: number; size: number; hero: boolean; delay: number}> = ({w, i, n, size, hero, delay}) => {

  const th = useTheme();

  const f1 = {fontFamily: `${th.family}, 'Noto Kufi Arabic', sans-serif`, fontWeight: th.weight};

  const f2 = useFont2();

  const p = useSpring(delay + i * 0.05, 'snappy');

  const alt = isAlt(i, n, th.st.edit.mixpat);

  const blur = th.st.edit.blur ? (1 - clamp01(p)) * 4 : 0;

  const finalSize = Math.max(48, Math.round(alt ? size * 0.94 : size));

  return (

    <div style={{...(alt ? f2 : f1), ...enterStyle(p, 'rise', 44), filter: blur > 0.3 ? `blur(${blur}px)` : undefined,

      fontSize: finalSize, lineHeight: 1.2, color: hero && !alt ? rgba(th.p.accent) : rgba(th.p.text, alt ? 0.9 : 1),

      textShadow: th.shadow, display: 'inline-block', wordBreak: 'break-word'}}>{w}</div>

  );

};



export const MixedText: React.FC<{text: string; size: number; delay?: number; style?: CSSProperties}> = ({text, size, delay = 0.1, style}) => {

  const words = String(text || '').split(/\s+/).filter(Boolean).slice(0, 4);

  const th = useTheme();

  // كلمة «البطل»: أطول كلمة بالخط الأول

  let hero = -1, best = 0;

  words.forEach((w, i) => { if (!isAlt(i, words.length, th.st.edit.mixpat) && w.length >= best) { best = w.length; hero = i; } });

  return (

    <div dir="rtl" lang="ar" style={{display: 'flex', flexWrap: 'wrap', justifyContent: 'center', alignItems: 'baseline', columnGap: Math.round(size * 0.26), rowGap: 4, textAlign: 'center', ...style}}>

      {words.map((w, i) => <MixWord key={i} w={w} i={i} n={words.length} size={size} hero={i === hero} delay={delay} />)}

    </div>

  );

};



// ------------------------------------------------------------------ أشكال زخرفية صغيرة متحركة على الأطراف

const rnd = (seed: number) => { let s = (seed * 9301 + 49297) % 233280; return () => { s = (s * 9301 + 49297) % 233280; return s / 233280; }; };



interface Rect { x1: number; y1: number; x2: number; y2: number }



const isInsideKeepOut = (x: number, y: number, r: number, zones: Rect[]): boolean => {

  return zones.some((z) => x + r >= z.x1 && x - r <= z.x2 && y + r >= z.y1 && y - r <= z.y2);

};



const ALL_CANDIDATE_ANCHORS: [number, number][] = [

  [80, 160], [980, 160],

  [75, 540], [1005, 540],

  [75, 780], [1005, 780],

  [75, 1060], [1005, 1060],

  [80, 1340], [1000, 1340],

  [110, 1760], [970, 1760],

  [140, 340], [940, 340],

];



const Shape: React.FC<{kind: string; size: number; col: RGB}> = ({kind, size, col}) => {

  const c = rgba(col);

  if (kind === 'diamonds') return <div style={{width: size * 0.8, height: size * 0.8, background: c, borderRadius: size * 0.16, rotate: '45deg'}} />;

  if (kind === 'dots') return <div style={{width: size * 0.55, height: size * 0.55, background: c, borderRadius: '50%'}} />;

  if (kind === 'crosses') {

    return (

      <svg width={size} height={size} viewBox="-1 -1 2 2"><path d="M-0.18 -0.9H0.18V-0.18H0.9V0.18H0.18V0.9H-0.18V0.18H-0.9V-0.18H-0.18Z" fill={c} /></svg>

    );

  }

  return <svg width={size} height={size} viewBox="-1 -1 2 2"><path d="M0 -1Q0.05 -0.05 1 0Q0.05 0.05 0 1Q-0.05 0.05 -1 0Q-0.05 -0.05 0 -1Z" fill={c} /></svg>;

};



const Accent: React.FC<{kind: string; x: number; y: number; size: number; col: RGB; i: number}> = ({kind, x, y, size, col, i}) => {

  const {settled} = useContext(MotionCtx);

  const frame = useCurrentFrame();

  const {fps} = useVideoConfig();

  const p = useSpring(0.15 + i * 0.18, 'bouncy');

  const fy = useIdle(10, 3 + i * 0.6, i * 1.7);

  const rot = settled ? 0 : (frame / fps) * (14 + i * 6) * (i % 2 ? -1 : 1);

  return (

    <div style={{position: 'absolute', left: x - size / 2, top: y - size / 2 + fy, scale: 0.3 + 0.7 * p, opacity: clamp01(p * 1.5), rotate: `${rot}deg`}}>

      <Shape kind={kind} size={size} col={col} />

    </div>

  );

};



export const AccentShapes: React.FC<{seed: number; count?: number}> = ({seed, count = 3}) => {

  const th = useTheme();

  const kind = th.st.edit.shapes;

  if (kind === 'none') return null;



  // مناطق الحظر (keep-out zones) حول العنوان والترجمة ومتن النصوص

  const zones: Rect[] = [

    // 1. العنوان (Headline)

    th.st.headline.pos === 'top'

      ? {x1: 40, y1: 200, x2: 1040, y2: 460}

      : th.st.headline.pos === 'bottom'

      ? {x1: 40, y1: 1350, x2: 1040, y2: 1610}

      : {x1: 40, y1: th.zoneCy - 130, x2: 1040, y2: th.zoneCy + 130},

    // 2. الترجمة (Captions)

    {x1: 20, y1: th.capY - 140, x2: 1060, y2: th.capY + 140},

    // 3. متن النص في الوسط والسفلي (Body text)

    {x1: 70, y1: th.zoneCy + 120, x2: 1010, y2: th.zoneCy + 440},

  ];



  const r = rnd(seed + th.st.seed);

  // اختيار نقاط آمنة تماماً خارج مناطق الحظر

  const safeAnchors = ALL_CANDIDATE_ANCHORS.filter(([x, y]) => !isInsideKeepOut(x, y, 45, zones));

  const anchors = safeAnchors.length >= count ? safeAnchors : ALL_CANDIDATE_ANCHORS;

  const picked = [...anchors].sort(() => r() - 0.5).slice(0, count);

  const cols = [th.p.accent, th.p.accent2, th.p.hl[2 % th.p.hl.length]];



  return (

    <AbsoluteFill style={{pointerEvents: 'none'}}>

      {picked.map(([x, y], i) => (

        <Accent key={i} i={i} kind={kind} x={x} y={y} size={Math.round(50 + r() * 50)} col={cols[i % cols.length]} />

      ))}

    </AbsoluteFill>

  );

};



// ------------------------------------------------------------------ رقم متوهج يعدّ تصاعدياً

export const CountNum: React.FC<{text: string; size: number; y: number}> = ({text, size, y}) => {

  const th = useTheme();

  const p = useSpring(0.35, 'snappy');

  const g = useProgress(0.35, 1.2);

  const m = String(text).match(/^(\D*?)(\d[\d,\.]*)(.*)$/);

  let shown = text;

  if (m) {

    const raw = m[2].replace(/,/g, '');

    const target = parseFloat(raw);

    const dec = raw.includes('.') ? raw.split('.')[1].length : 0;

    const v = target * g;

    const body = m[2].includes(',') || target >= 10000 ? v.toLocaleString('en-US', {minimumFractionDigits: dec, maximumFractionDigits: dec}) : v.toFixed(dec);

    shown = `${m[1]}${body}${m[3]}`;

  }

  const glow = th.st.edit.glow ? `0 0 36px ${rgba(th.p.accent, 0.75)}, 0 0 90px ${rgba(th.p.accent, 0.45)}` : th.shadow;

  return (

    <div style={{position: 'absolute', left: 60, right: 60, top: y, textAlign: 'center', direction: 'ltr', fontFamily: `${th.family}, sans-serif`, fontWeight: th.weight, fontSize: size, lineHeight: 1.1, color: rgba(th.p.accent), textShadow: glow, ...enterStyle(p, 'rise', 40)}}>{shown}</div>

  );

};



// ------------------------------------------------------------------ الصورة (أو مكان محجوز في المعاينة)

export const Pic: React.FC<{beat: Beat; fit: 'cover' | 'contain'; style?: CSSProperties}> = ({beat, fit, style}) => {

  const th = useTheme();

  if (!beat.img) {

    return (

      <div style={{...style, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', background: `linear-gradient(135deg, ${rgba(th.p.accent, 0.55)}, ${rgba(th.p.accent2, 0.55)})`, color: rgba(th.p.text), fontSize: 44, padding: 40, textAlign: 'center', direction: 'ltr', fontFamily: 'sans-serif'}}>

        {beat.icon ? <Icon name={beat.icon} size={340} color={rgba(th.p.text)} strokeWidth={1.5} /> : null}
        <div dir="rtl" style={{fontSize: 64, fontWeight: 800, marginTop: beat.icon ? 24 : 0}}>{beat.text || beat.query || ''}</div>

      </div>

    );

  }

  return <SafeImg src={staticFile(beat.img)} style={{...style, objectFit: fit}} />;

};



const Duo: React.FC = () => {

  const th = useTheme();

  const dark = th.dark ? th.p.c2 : mix(th.p.text, th.p.c1, 0.1);

  const light = mix(th.p.accent, [255, 255, 255], 0.4);

  return (

    <>

      <div style={{position: 'absolute', inset: 0, background: rgba(dark), mixBlendMode: 'lighten'}} />

      <div style={{position: 'absolute', inset: 0, background: rgba(light), mixBlendMode: 'multiply'}} />

    </>

  );

};



// صورة داخل إطار مقصوص مع حركة كاميرا (Ken Burns) ومعالجة لونين اختيارية.

export const Framed: React.FC<{beat: Beat; w: number; h: number; style?: CSSProperties}> = ({beat, w, h, style}) => {

  const th = useTheme();

  const frame = useCurrentFrame();

  const {settled} = useContext(MotionCtx);

  const ken = th.st.edit.ken;

  const t = settled ? 0.5 : interpolate(frame, [0, Math.max(beat.dur, 2)], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: th.ease.inOut});

  const sc = ken === 'out' ? 1.22 - 0.18 * t : ken === 'pan' ? 1.16 : 1.02 + 0.19 * t;

  const tx = ken === 'pan' ? (t - 0.5) * 95 : 0;

  const ty = ken === 'in' ? (t - 0.5) * -30 : 0;

  return (

    <div style={{width: w, height: h, overflow: 'hidden', position: 'relative', isolation: 'isolate', ...style}}>

      <Pic beat={beat} fit="cover" style={{position: 'absolute', inset: 0, width: '100%', height: '100%', scale: sc, translate: `${tx}px ${ty}px`, filter: 'contrast(1.06) saturate(1.12)'}} />

    </div>

  );

};

