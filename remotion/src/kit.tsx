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

export {Pop, interpolate};
