/**
 * Scene kit: the ONLY module an authored scene (remotion/src/authored/*.tsx, written by the art director) may import
 * besides 'react' and 'remotion'. Documented in docs/SCENE_KIT.md. Everything here is deterministic (frame-driven).
 */
import React, {CSSProperties} from 'react';
import {Easing, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {rgba, useTheme} from './theme';
import {clamp01, enterStyle, Pop, useFont, useIdle, useProgress, useSpring} from './hooks';
import {BEAT_ZONE, CANVAS_HEIGHT, CANVAS_WIDTH, CAPTION_ZONE, HEADLINE_ZONE, SAFE_BOTTOM, SAFE_TOP} from './layout';
import {Icon} from './icons';
import {MapOverlayLayer} from './mapOverlay';

export {Icon, useSpring as useSpr, enterStyle as enter, useProgress, useIdle, clamp01};
export type {EnterKind, Preset} from './hooks';

/** Props every authored scene receives. `data` = {sentence, entities, map_overlay, ...} prepared by the pipeline. */
export type SceneProps = {dur: number; data: any};

/** The layout contract (1080x1920). Place everything inside `beat`; never inside `caption`. */
export const LAYOUT = {cx: CANVAS_WIDTH / 2, cy: BEAT_ZONE.center_y, W: CANVAS_WIDTH, H: CANVAS_HEIGHT, safeTop: SAFE_TOP, safeBottom: SAFE_BOTTOM, headline: HEADLINE_ZONE, beat: BEAT_ZONE, caption: CAPTION_ZONE} as const;

/** Easing curves (bezier only). */
export const ease = {
  out: Easing.bezier(0.16, 1, 0.3, 1),
  inOut: Easing.bezier(0.65, 0, 0.35, 1),
  in: Easing.bezier(0.7, 0, 0.84, 0.35),
  back: Easing.bezier(0.34, 1.4, 0.64, 1),
} as const;

/** Seconds -> frames helper that respects the project fps. */
export const useKit = () => {
  const th = useTheme();
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const p = th.p;
  const dark = th.dark;
  /** colour by name with alpha: c('accent', 0.4) */
  const c = (name: 'text' | 'accent' | 'accent2' | 'ground' | 'ground2' | 'hl0' | 'hl1' | 'hl2', a = 1) =>
    rgba(name === 'ground' ? p.c1 : name === 'ground2' ? p.c2 : th.tok(name === 'text' ? 'text' : name), a);
  return {
    frame, fps, t: frame / fps, sec: (s: number) => Math.round(s * fps),
    dark, c, shadow: th.shadow,
    card: dark ? rgba(p.c2, 0.92) : 'rgba(255,255,255,0.9)',
    cardBorder: rgba(p.accent, 0.85),
    font: `${th.family}, 'Noto Kufi Arabic', sans-serif`,
    fontWeight: th.weight,
  };
};

/** Absolutely positioned box (px on the 1080x1920 canvas). Use LAYOUT numbers for x/y/w/h. */
export const Abs: React.FC<{x: number; y: number; w?: number; h?: number; style?: CSSProperties; children?: React.ReactNode}> = ({x, y, w, h, style, children}) => (
  <div style={{position: 'absolute', left: x, top: y, width: w, height: h, ...style}}>{children}</div>
);

/** Glass/paper card that follows the video theme (dark glass on dark grounds, white card on light grounds). */
export const Card: React.FC<{style?: CSSProperties; children?: React.ReactNode}> = ({style, children}) => {
  const k = useKit();
  return <div style={{background: k.card, border: `3px solid ${k.cardBorder}`, borderRadius: 28, boxShadow: '0 18px 44px rgba(0,0,0,0.28)', ...style}}>{children}</div>;
};

const Word: React.FC<{text: string; delay: number; reveal: string}> = ({text, delay, reveal}) => {
  const p = useSpring(delay, 'snappy');
  const st = reveal === 'none' ? {} : enterStyle(p, reveal === 'fade' ? 'fade' : 'rise', 36);
  return <span style={{display: 'inline-block', margin: '0 0.16em', ...st}}>{text}</span>;
};

/**
 * Arabic-safe text: dir=rtl, lang=ar, no letter-spacing, animates WORD by word (never per letter, which breaks joining).
 * Always use it for Arabic strings.
 */
export const ArText: React.FC<{
  children: string; size?: number; weight?: number; color?: string; align?: 'center' | 'right' | 'left'; delay?: number;
  reveal?: 'words' | 'fade' | 'none'; maxWidth?: number; lineHeight?: number; style?: CSSProperties;
}> = ({children, size = 64, weight, color, align = 'center', delay = 0, reveal = 'words', maxWidth = LAYOUT.W - 160, lineHeight = 1.3, style}) => {
  const th = useTheme();
  const font = useFont();
  const words = String(children || '').split(/\s+/).filter(Boolean);
  return (
    <div dir="rtl" lang="ar" style={{...font, fontWeight: weight ?? th.weight, fontSize: size, lineHeight, letterSpacing: 0, color: color ?? rgba(th.p.text), textAlign: align, maxWidth, textShadow: th.shadow, ...style}}>
      {words.map((w, i) => <Word key={i} text={w} delay={delay + i * 0.07} reveal={reveal} />)}
    </div>
  );
};

/** Number rolling from `from` to `to` (LTR digits, tabular). */
export const Counter: React.FC<{to: number; from?: number; delay?: number; dur?: number; size?: number; color?: string; suffix?: string; decimals?: number; style?: CSSProperties}> = ({to, from = 0, delay = 0, dur = 1.2, size = 160, color, suffix = '', decimals = 0, style}) => {
  const th = useTheme();
  const font = useFont();
  const p = useProgress(delay, dur);
  const v = from + (to - from) * p;
  const txt = v.toLocaleString('en-US', {minimumFractionDigits: decimals, maximumFractionDigits: decimals});
  return <div style={{...font, direction: 'ltr', fontVariantNumeric: 'tabular-nums', fontSize: size, fontWeight: 900, lineHeight: 1.1, color: color ?? rgba(th.p.accent), textShadow: th.shadow, ...style}}>{txt}{suffix}</div>;
};

/** Progress ring 0..1 (animated). */
export const Ring: React.FC<{value: number; size?: number; stroke?: number; delay?: number; color?: string; children?: React.ReactNode}> = ({value, size = 460, stroke = 28, delay = 0.1, color, children}) => {
  const th = useTheme();
  const p = useProgress(delay, 1.3);
  const r = (size - stroke) / 2;
  const C = 2 * Math.PI * r;
  return (
    <div style={{position: 'relative', width: size, height: size}}>
      <svg width={size} height={size}>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={rgba(th.p.text, 0.16)} strokeWidth={stroke} />
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={color ?? rgba(th.p.accent)} strokeWidth={stroke} strokeLinecap="round" strokeDasharray={C} strokeDashoffset={C * (1 - clamp01(value) * p)} transform={`rotate(-90 ${size / 2} ${size / 2})`} />
      </svg>
      <div style={{position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column'}}>{children}</div>
    </div>
  );
};

/** Horizontal bar 0..1 (animated). */
export const Bar: React.FC<{value: number; w?: number; h?: number; delay?: number; color?: string}> = ({value, w = 700, h = 30, delay = 0.1, color}) => {
  const th = useTheme();
  const p = useProgress(delay, 1.0);
  return (
    <div style={{width: w, height: h, borderRadius: h / 2, background: rgba(th.p.text, 0.14), overflow: 'hidden'}}>
      <div style={{width: `${clamp01(value) * p * 100}%`, height: '100%', borderRadius: h / 2, background: color ?? rgba(th.p.accent)}} />
    </div>
  );
};

/** The vector map engine (same renderer as the built-in map scenes). `overlay` = data.map_overlay. */
export const MapLayer: React.FC<{overlay: any; mode?: 'full-stage' | 'split-bottom' | 'hud'}> = ({overlay, mode = 'full-stage'}) => <MapOverlayLayer overlay={overlay} mode={mode} />;

// ---------------------------------------------------------------- layout recipes
// Composition patterns (one hero idea per screen, text as part of the layout, cumulative build-up). Each one is
// a ready, tested arrangement the art director can combine or imitate; all are frame-driven and inside LAYOUT.beat.

/** Recipe: one KEY word big and heavy in the accent colour, the rest of the line small and light above/below it. */
export const KeyLine: React.FC<{keyword: string; lead?: string; tail?: string; size?: number; delay?: number; maxWidth?: number}> = ({keyword, lead, tail, size = 120, delay = 0, maxWidth = 900}) => {
  const k = useKit();
  const small = Math.max(30, Math.round(size * 0.42));
  return (
    <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: Math.round(size * 0.1), width: maxWidth}}>
      {lead ? <ArText size={small} weight={500} color={k.c('text', 0.78)} delay={delay} maxWidth={maxWidth}>{lead}</ArText> : null}
      <ArText size={size} weight={900} color={k.c('accent')} delay={delay + 0.12} maxWidth={maxWidth} lineHeight={1.15}>{keyword}</ArText>
      {tail ? <ArText size={small} weight={500} color={k.c('text', 0.78)} delay={delay + 0.3} maxWidth={maxWidth}>{tail}</ArText> : null}
    </div>
  );
};

const HubNode: React.FC<{x: number; y: number; size: number; delay: number; icon?: string; label?: string; accent?: boolean}> = ({x, y, size, delay, icon, label, accent}) => {
  const k = useKit();
  const p = useSpring(delay, 'bouncy');
  return (
    <Abs x={x - 130} y={y - size / 2} w={260} style={{...enterStyle(p, 'pop', 0), display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10}}>
      <div style={{width: size, height: size, borderRadius: size / 2, background: k.card, border: `3px solid ${accent ? k.c('accent') : k.cardBorder}`, boxShadow: '0 14px 30px rgba(0,0,0,0.25)', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
        {icon ? <Icon name={icon} size={Math.round(size * 0.5)} color={k.c('accent')} /> : null}
      </div>
      {label ? <ArText size={30} weight={700} maxWidth={250} reveal="fade" delay={delay + 0.1} lineHeight={1.2}>{label}</ArText> : null}
    </Abs>
  );
};

const Spoke: React.FC<{x1: number; y1: number; x2: number; y2: number; delay: number}> = ({x1, y1, x2, y2, delay}) => {
  const k = useKit();
  const p = useProgress(delay, 0.5);
  const len = Math.hypot(x2 - x1, y2 - y1);
  return (
    <svg width={LAYOUT.W} height={LAYOUT.H} style={{position: 'absolute', left: 0, top: 0}}>
      <line x1={x1} y1={y1} x2={x2} y2={y2} stroke={k.c('accent', 0.55)} strokeWidth={4} strokeLinecap="round" strokeDasharray={`${len}`} strokeDashoffset={len * (1 - p)} />
    </svg>
  );
};

/** Recipe: a hub in the middle and 2..7 satellites around it, spokes drawn one by one. `center` = the hub content. */
export const Hub: React.FC<{items: {icon?: string; label?: string}[]; center?: React.ReactNode; cy?: number; radius?: number; delay?: number}> = ({items, center, cy = LAYOUT.beat.center_y - 40, radius = 330, delay = 0.1}) => {
  const n = Math.max(1, Math.min(7, items.length));
  const cx = LAYOUT.cx;
  const hub = useSpring(delay, 'snappy');
  return (
    <>
      {items.slice(0, n).map((it, i) => {
        const a = -Math.PI / 2 + (i * 2 * Math.PI) / n;
        const x = cx + Math.cos(a) * radius, y = cy + Math.sin(a) * radius;
        return <Spoke key={`s${i}`} x1={cx} y1={cy} x2={x} y2={y} delay={delay + 0.25 + i * 0.12} />;
      })}
      <Abs x={cx - 130} y={cy - 130} w={260} h={260} style={{...enterStyle(hub, 'pop', 0), display: 'flex', alignItems: 'center', justifyContent: 'center'}}>{center}</Abs>
      {items.slice(0, n).map((it, i) => {
        const a = -Math.PI / 2 + (i * 2 * Math.PI) / n;
        return <HubNode key={`n${i}`} x={cx + Math.cos(a) * radius} y={cy + Math.sin(a) * radius} size={140} delay={delay + 0.35 + i * 0.12} icon={it.icon} label={it.label} />;
      })}
    </>
  );
};

const StepCol: React.FC<{x: number; w: number; bottom: number; h: number; delay: number; label: string; last: boolean}> = ({x, w, bottom, h, delay, label, last}) => {
  const k = useKit();
  const p = useSpring(delay, 'smooth');
  return (
    <>
      <Abs x={x} y={bottom - h} w={w} h={h} style={{borderRadius: '22px 22px 6px 6px', background: last ? k.c('accent') : k.c('accent', 0.4), border: `3px solid ${k.c('accent')}`, transformOrigin: '50% 100%', transform: `scaleY(${p})`, opacity: Math.min(1, p * 2)}} />
      <Abs x={x - 10} y={bottom - h - 100} w={w + 20} style={{...enterStyle(clamp01((p - 0.4) / 0.6), 'rise', 24), display: 'flex', justifyContent: 'center'}}>
        <ArText size={34} weight={800} maxWidth={w + 10} reveal="none" lineHeight={1.15}>{label}</ArText>
      </Abs>
    </>
  );
};

/** Recipe: 2..5 rising steps (first step on the right for Arabic). Labels sit on top of each step. */
export const Steps: React.FC<{items: string[]; w?: number; bottom?: number; maxH?: number; delay?: number}> = ({items, w = 900, bottom = LAYOUT.beat.bottom - 40, maxH = 540, delay = 0.1}) => {
  const n = Math.max(2, Math.min(5, items.length));
  const colW = w / n - 14;
  return (
    <>
      {items.slice(0, n).map((label, i) => {
        const x = LAYOUT.cx + w / 2 - (i + 1) * (w / n) + 7; // right -> left
        const h = 150 + (i * (maxH - 150)) / (n - 1);
        return <StepCol key={i} x={x} w={colW} bottom={bottom} h={h} delay={delay + i * 0.35} label={label} last={i === n - 1} />;
      })}
    </>
  );
};

const StackRow: React.FC<{y: number; delay: number; text: string; icon?: string}> = ({y, delay, text, icon}) => {
  const k = useKit();
  const p = useSpring(delay, 'snappy');
  return (
    <Abs x={110} y={y} w={860} style={enterStyle(p, 'right', 70)}>
      <Card style={{padding: '22px 30px', display: 'flex', alignItems: 'center', flexDirection: 'row-reverse', gap: 24}}>
        {icon ? <Icon name={icon} size={52} color={k.c('accent')} /> : null}
        <div style={{flex: 1}}><ArText size={42} weight={800} align="right" maxWidth={680} reveal="none" lineHeight={1.2}>{text}</ArText></div>
      </Card>
    </Abs>
  );
};

/** Recipe: a list that builds up row by row (rows stay). 2..6 rows. */
export const Stack: React.FC<{items: {text: string; icon?: string}[]; top?: number; step?: number; delay?: number}> = ({items, top = LAYOUT.beat.top + 60, step = 0.5, delay = 0.1}) => (
  <>
    {items.slice(0, 6).map((it, i) => <StackRow key={i} y={top + i * 150} delay={delay + i * step} text={it.text} icon={it.icon} />)}
  </>
);

/** Recipe: a pinned card on a string (swings gently). Put an Icon / Counter / ArText inside. Not for photos (use the photo beat). */
export const Pinned: React.FC<{x?: number; y?: number; w?: number; h?: number; rotate?: number; delay?: number; children?: React.ReactNode}> = ({x = LAYOUT.cx - 220, y = LAYOUT.beat.top + 80, w = 440, h = 460, rotate = -4, delay = 0.1, children}) => {
  const k = useKit();
  const p = useSpring(delay, 'bouncy');
  const sway = useIdle(1.6, 4, rotate);
  return (
    <Abs x={x} y={y} w={w} h={h} style={{...enterStyle(p, 'drop', 120), transform: `translateY(${(1 - p) * -120}px) rotate(${rotate + sway}deg)`, transformOrigin: '50% 0%'}}>
      <div style={{position: 'absolute', left: w / 2 - 14, top: -26, width: 28, height: 56, borderRadius: 14, border: `5px solid ${k.c('text', 0.7)}`, background: 'transparent'}} />
      <div style={{width: w, height: h, background: k.dark ? 'rgba(245,240,230,0.96)' : '#ffffff', borderRadius: 10, boxShadow: '0 22px 40px rgba(0,0,0,0.32)', padding: 22, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#141210'}}>{children}</div>
    </Abs>
  );
};

/** Recipe: big soft ribbon crossing behind the content (continuity decoration, low alpha, drawn on progressively). */
export const Ribbon: React.FC<{variant?: 0 | 1 | 2; width?: number}> = ({variant = 0, width = 90}) => {
  const k = useKit();
  const p = useProgress(0, 1.4);
  const paths = [
    'M -80 380 C 300 260 520 760 1160 560',
    'M 1160 330 C 700 460 420 1000 -80 1180',
    'M -80 1200 C 360 900 700 1500 1160 1000',
  ];
  const len = 2000;
  return (
    <svg width={LAYOUT.W} height={LAYOUT.H} style={{position: 'absolute', left: 0, top: 0}}>
      <path d={paths[variant]} fill="none" stroke={k.c('accent', 0.14)} strokeWidth={width} strokeLinecap="round" strokeDasharray={len} strokeDashoffset={len * (1 - p)} />
    </svg>
  );
};

export {Pop, interpolate};
