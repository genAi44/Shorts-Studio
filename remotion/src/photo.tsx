import React, {CSSProperties, useContext} from 'react';

import {AbsoluteFill, interpolate, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {SafeImg} from './SafeImg';
import {Icon} from './icons';

import {clamp01, enterStyle, useIdle, useProgress, useSpring} from './hooks';

import {MapLayoutCtx, MotionCtx, rgba, useTheme} from './theme';
import {BEAT_ZONE} from './layout';
import {Beat, RGB} from './types';
import {FireSparks, FloatBadge, MapOverlay} from './fx';



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

const CountNum: React.FC<{text: string; size: number; y: number}> = ({text, size, y}) => {

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

const Pic: React.FC<{beat: Beat; fit: 'cover' | 'contain'; style?: CSSProperties}> = ({beat, fit, style}) => {

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

const Framed: React.FC<{beat: Beat; w: number; h: number; style?: CSSProperties}> = ({beat, w, h, style}) => {

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



// ------------------------------------------------------------------ مقطع الصورة

export const PhotoBeat: React.FC<{beat: Beat}> = ({beat}) => {

  const th = useTheme();

  const ed = th.st.edit;

  const {settled} = useContext(MotionCtx);

  const {splitBottom} = useContext(MapLayoutCtx);

  const pop = useSpring(0.05, 'bouncy');

  const sm = useSpring(0.05, 'smooth');

  const ring = useProgress(0.1, 0.9);

  const idle = useIdle(9, 3.8);

  const frame = useCurrentFrame();

  const {fps} = useVideoConfig();

  const hasNum = !!beat.number;

  const cy = splitBottom ? 400 : th.zoneCy - (hasNum ? 230 : 110);

  const textY = th.zoneCy + (hasNum ? 170 : 330);

  const capSize = Math.max(48, Math.round(th.st.text.size * 0.62));

  const spin = settled ? 0 : (frame / fps) * 8;

  const cut = !!beat.cut;

  const S = splitBottom ? 450 : (hasNum ? 540 : 620);



  let media: React.ReactNode;

  if (cut) {

    const R = S + 90;

    const C = 2 * Math.PI * (R / 2 - 3);

    media = (

      <>

        {ed.cutout === 'glow' && <div style={{position: 'absolute', left: 540 - R * 0.8, top: cy - R * 0.8, width: R * 1.6, height: R * 1.6, borderRadius: '50%', background: `radial-gradient(circle, ${rgba(th.p.accent, 0.5)}, transparent 68%)`, opacity: sm}} />}

        {ed.cutout === 'blob' && <div style={{position: 'absolute', left: 540 - S * 0.52, top: cy - S * 0.5, width: S * 1.04, height: S, background: rgba(th.p.accent, 0.92), borderRadius: '58% 42% 55% 45% / 48% 56% 44% 52%', rotate: `${spin * 2 - 8}deg`, scale: 0.6 + 0.4 * pop, opacity: clamp01(pop * 1.6)}} />}

        {ed.cutout === 'ring' && (

          <svg width={R} height={R} viewBox={`0 0 ${R} ${R}`} style={{position: 'absolute', left: 540 - R / 2, top: cy - R / 2, rotate: `${spin}deg`, overflow: 'visible'}}>

            <circle cx={R / 2} cy={R / 2} r={R / 2 - 3} fill="none" stroke={rgba(th.p.text, 0.8)} strokeWidth={4} strokeLinecap="round" strokeDasharray={`3 14`} strokeDashoffset={C * (1 - ring)} opacity={ring} />

            <circle cx={R / 2} cy={R / 2} r={R / 2 - 3} fill="none" stroke={rgba(th.p.accent, 0.9)} strokeWidth={5} strokeLinecap="round" pathLength={1} strokeDasharray={`0.18 1`} strokeDashoffset={-ring * 0.9} />

          </svg>

        )}

        <Pic beat={beat} fit="contain" style={{position: 'absolute', left: 540 - S / 2, top: cy - S / 2 + idle, width: S, height: S, filter: 'drop-shadow(0 26px 28px rgba(0,0,0,0.38))', ...enterStyle(pop, 'pop')}} />

      </>

    );

  } else if (ed.photo === 'bleed') {

    const H = splitBottom ? 680 : (hasNum ? 1200 : 1400);

    media = (

      <div style={{position: 'absolute', left: 0, right: 0, top: splitBottom ? 80 : cy - H / 2, opacity: clamp01(sm * 1.5), translate: `0 ${(1 - sm) * 50}px`, WebkitMaskImage: 'linear-gradient(to bottom, transparent, #000 14%, #000 84%, transparent)', maskImage: 'linear-gradient(to bottom, transparent, #000 14%, #000 84%, transparent)'}}>

        <Framed beat={beat} w={1080} h={H} />

      </div>

    );

  } else if (ed.photo === 'free') {

    // frameless: no border, no card; the photo dissolves into the background through a soft elliptical mask
    const w = splitBottom ? 960 : (hasNum ? 940 : 1000), h = splitBottom ? 540 : (hasNum ? 680 : 800);
    const fade = 'radial-gradient(ellipse 50% 50% at 50% 50%, #000 58%, transparent 100%)';

    media = (

      <div style={{position: 'absolute', left: 540 - w / 2, top: cy - h / 2 + idle * 0.5, opacity: clamp01(sm * 1.5), scale: 0.94 + 0.06 * sm, WebkitMaskImage: fade, maskImage: fade}}>

        <Framed beat={beat} w={w} h={h} />

      </div>

    );

  } else if (ed.photo === 'circle') {

    // frameless: a round crop with only a soft shadow (no border line)
    const D = splitBottom ? 470 : (hasNum ? 600 : 700);

    media = (

      <div style={{position: 'absolute', left: 540 - D / 2, top: cy - D / 2 + idle * 0.5, filter: 'drop-shadow(0 26px 30px rgba(0,0,0,0.38))', ...enterStyle(pop, 'pop')}}>

        <Framed beat={beat} w={D} h={D} style={{borderRadius: '50%'}} />

      </div>

    );

  } else if (ed.photo === 'polaroid') {

    const w = splitBottom ? 920 : (hasNum ? 820 : 920);

    const h = splitBottom ? 520 : (hasNum ? 620 : 760);

    media = (

      <div style={{position: 'absolute', left: 540 - w / 2, top: cy - h / 2 + idle * 0.5, padding: 10, background: 'rgba(255,255,255,0.08)', backdropFilter: 'blur(16px)', border: '1px solid rgba(255,255,255,0.18)', borderRadius: 28, boxShadow: '0 30px 60px rgba(0,0,0,0.45)', ...enterStyle(pop, 'rise', 60)}}>

        <Framed beat={beat} w={w} h={h} style={{borderRadius: 20}} />

      </div>

    );

  } else if (ed.photo === 'arch') {

    const w = splitBottom ? 920 : (hasNum ? 820 : 920), h = splitBottom ? 520 : (hasNum ? 660 : 820);

    media = (

      <div style={{position: 'absolute', left: 540 - w / 2, top: cy - h / 2 + idle * 0.5, borderRadius: 28, overflow: 'hidden', border: `2.5px solid ${rgba(th.p.accent, 0.72)}`, boxShadow: `0 28px 54px rgba(0,0,0,0.45), 0 0 36px ${rgba(th.p.accent, 0.22)}`, ...enterStyle(pop, 'rise', 60)}}>

        <Framed beat={beat} w={w} h={h} />

      </div>

    );

  } else if (ed.photo === 'tilt') {

    const w = splitBottom ? 900 : (hasNum ? 800 : 900), h = splitBottom ? 500 : (hasNum ? 600 : 720);

    media = (

      <div style={{position: 'absolute', left: 540 - w / 2, top: cy - h / 2 + idle * 0.5, rotate: `${1.5 - 1.5 * (1 - pop)}deg`, ...enterStyle(pop, 'left', 40)}}>

        <div style={{position: 'absolute', left: 18, top: 18, width: w, height: h, borderRadius: 28, background: rgba(th.p.accent, 0.85)}} />

        <Framed beat={beat} w={w} h={h} style={{borderRadius: 28, boxShadow: '0 26px 44px rgba(0,0,0,0.35)'}} />

      </div>

    );

  } else {

    const w = splitBottom ? 920 : (hasNum ? 820 : 920), h = splitBottom ? 520 : (hasNum ? 640 : 780);

    media = (

      <div style={{position: 'absolute', left: 540 - w / 2, top: cy - h / 2 + idle * 0.5, borderRadius: 28, overflow: 'hidden', border: `2.5px solid ${rgba(th.p.accent, 0.7)}`, boxShadow: '0 24px 48px rgba(0,0,0,0.4)', ...enterStyle(pop, 'pop')}}>

        <Framed beat={beat} w={w} h={h} />

      </div>

    );

  }



  return (

    <AbsoluteFill>

      {media}

      {hasNum ? <CountNum text={String(beat.number)} size={150} y={textY - 20} /> : null}

      {!splitBottom && beat.text && beat.text.trim().length > 0 && !(beat.narration && beat.narration.includes(beat.text.trim())) ? (

        <div style={{

          position: 'absolute', left: 60, right: 60, top: Math.min(hasNum ? textY + 120 : textY, BEAT_ZONE.bottom - 180),

          padding: '16px 28px', borderRadius: 28,

          background: rgba(th.dark ? th.p.c2 : th.p.c1, 0.72),

          backdropFilter: 'blur(20px)',

          WebkitBackdropFilter: 'blur(20px)',

          boxShadow: `0 14px 34px rgba(0,0,0,0.32), inset 0 0 0 1.5px ${rgba(th.p.accent, 0.35)}`,

          display: 'flex', justifyContent: 'center'

        }}>

          <MixedText text={beat.text} size={Math.max(48, hasNum ? Math.round(capSize * 0.82) : capSize)} delay={0} />

        </div>

      ) : null}

    </AbsoluteFill>

  );

};

