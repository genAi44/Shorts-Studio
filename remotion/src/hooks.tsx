import React, {CSSProperties, useContext} from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {MotionCtx, useTheme} from './theme';

export const PRESETS = {
  smooth: {damping: 200},
  snappy: {damping: 22, stiffness: 190, mass: 0.9},
  bouncy: {damping: 11, stiffness: 150, mass: 0.8},
} as const;
export type Preset = keyof typeof PRESETS;

// سبرنغ مؤخَّر بالثواني؛ يعود 1 فوراً في مشهد الـ LOOP (حالة ثابتة).
export const useSpring = (delaySec = 0, preset: Preset = 'snappy') => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {speed, settled} = useContext(MotionCtx);
  if (settled) return 1;
  return spring({frame: frame * speed - Math.round(delaySec * fps), fps, config: PRESETS[preset]});
};

export const clamp01 = (x: number) => Math.min(1, Math.max(0, x));

export type EnterKind = 'rise' | 'drop' | 'pop' | 'left' | 'right' | 'fade';
// دخول يحرّك 3 خصائص معاً: الشفافية + الإزاحة + المقياس.
export const enterStyle = (p: number, kind: EnterKind, dist = 60): CSSProperties => {
  const o = clamp01(p * 1.6);
  let tx = 0, ty = 0, sc = 0.96 + 0.04 * p;
  if (kind === 'rise') { ty = (1 - p) * dist; sc = 0.93 + 0.07 * p; }
  else if (kind === 'drop') { ty = -(1 - p) * dist; sc = 0.93 + 0.07 * p; }
  else if (kind === 'left') { tx = -(1 - p) * dist * 3.2; }
  else if (kind === 'right') { tx = (1 - p) * dist * 3.2; }
  else if (kind === 'pop') { sc = 0.5 + 0.5 * p; }
  return {opacity: o, translate: `${tx}px ${ty}px`, scale: sc};
};

export const Pop: React.FC<{
  delay?: number; kind?: EnterKind; preset?: Preset; dist?: number; style?: CSSProperties; children?: React.ReactNode;
}> = ({delay = 0, kind = 'rise', preset = 'snappy', dist = 60, style, children}) => {
  const p = useSpring(delay, preset);
  return <div style={{...enterStyle(p, kind, dist), ...style}}>{children}</div>;
};

export const useIdle = (amp = 6, period = 3.2, phase = 0) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return Math.sin((frame / fps) * ((2 * Math.PI) / period) + phase) * amp;
};

export const useFont = () => {
  const th = useTheme();
  return {fontFamily: `${th.family}, 'Noto Kufi Arabic', sans-serif`, fontWeight: th.weight} as CSSProperties;
};

// تقدّم 0→1 بمنحنى خروج ناعم (للعدّادات والخطوط)؛ يكون 1 مباشرة في حالة الثبات.
export const useProgress = (startSec = 0, durSec = 1.2) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {speed, settled} = useContext(MotionCtx);
  const th = useTheme();
  if (settled) return 1;
  return interpolate(frame * speed, [startSec * fps, (startSec + durSec) * fps], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: th.ease.out,
  });
};
