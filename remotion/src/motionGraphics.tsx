/**
 * motionGraphics.tsx — Reusable motion graphics primitives.
 *
 * SVGDraw     : animates SVG strokeDashoffset so paths "draw themselves" in sync with the script.
 * CounterRoll : rolls numbers up/down with spring + optional suffix (%, K, M, …).
 * RoughHighlight: animated underline / circle highlight using @remotion/rough-notation.
 * MorphIcon   : cross-fades between two SVG paths (icon swap on a keyword).
 * ScalePopBadge: stat badge that pops in on a keyword frame with spring overshoot.
 */
import React, {useMemo} from 'react';
import {AbsoluteFill, Easing, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {Highlight, Underline, Circle as RoughCircle, Box as RoughBox} from '@remotion/rough-notation';
import {evolvePath, getLength, scalePath, warpPath} from '@remotion/paths';

// ─── SVGDraw ──────────────────────────────────────────────────────────────────
/**
 * Animates the `d` attribute of an SVG path as a draw-on effect.
 *
 * Usage:
 *   <SVGDraw
 *     d="M 0 0 L 400 0 L 400 300 Z"
 *     stroke="#FFD400"
 *     strokeWidth={4}
 *     startFrame={30}
 *     durationFrames={45}
 *   />
 */
export const SVGDraw: React.FC<{
  d: string;
  stroke?: string;
  strokeWidth?: number;
  fill?: string;
  width?: number;
  height?: number;
  startFrame?: number;
  durationFrames?: number;
  easing?: (t: number) => number;
  style?: React.CSSProperties;
}> = ({
  d,
  stroke = 'currentColor',
  strokeWidth = 3,
  fill = 'none',
  width = 1080,
  height = 1920,
  startFrame = 0,
  durationFrames = 30,
  easing = Easing.out(Easing.cubic),
  style,
}) => {
  const frame = useCurrentFrame();
  const progress = interpolate(
    frame,
    [startFrame, startFrame + durationFrames],
    [0, 1],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing},
  );
  const {strokeDasharray, strokeDashoffset} = evolvePath(progress, d);
  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      style={{position: 'absolute', inset: 0, width: '100%', height: '100%', ...style}}
    >
      <path
        d={d}
        fill={fill}
        stroke={stroke}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeDasharray={strokeDasharray}
        strokeDashoffset={strokeDashoffset}
      />
    </svg>
  );
};

// ─── CounterRoll ──────────────────────────────────────────────────────────────
/**
 * Rolls a number from `from` to `to` with spring physics.
 *
 * Usage:
 *   <CounterRoll from={0} to={150} suffix="%" startFrame={20} fontSize={80} />
 */
export const CounterRoll: React.FC<{
  from?: number;
  to: number;
  decimals?: number;
  prefix?: string;
  suffix?: string;
  startFrame?: number;
  durationFrames?: number;
  fontSize?: number;
  color?: string;
  fontWeight?: number | string;
  style?: React.CSSProperties;
}> = ({
  from = 0,
  to,
  decimals = 0,
  prefix = '',
  suffix = '',
  startFrame = 0,
  durationFrames = 45,
  fontSize = 72,
  color = 'currentColor',
  fontWeight = 900,
  style,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const sp = spring({
    frame: frame - startFrame,
    fps,
    config: {mass: 1, damping: 22, stiffness: 160},
    durationInFrames: durationFrames,
  });
  const value = from + (to - from) * sp;
  const display = value.toFixed(decimals);
  return (
    <span
      style={{
        fontSize,
        fontWeight,
        color,
        fontVariantNumeric: 'tabular-nums',
        display: 'inline-block',
        ...style,
      }}
    >
      {prefix}{display}{suffix}
    </span>
  );
};

// ─── RoughHighlight ───────────────────────────────────────────────────────────
/**
 * Wraps text in an animated rough-notation highlight/underline/circle.
 *
 * Usage:
 *   <RoughHighlight type="highlight" color="#FFD400" startFrame={30}>
 *     كلمة مفتاحية
 *   </RoughHighlight>
 */
export const RoughHighlight: React.FC<{
  children: React.ReactNode;
  type?: 'highlight' | 'underline' | 'circle' | 'box';
  color?: string;
  strokeWidth?: number;
  startFrame?: number;
  durationFrames?: number;
  style?: React.CSSProperties;
}> = ({
  children,
  type = 'underline',
  color = '#FFD400',
  strokeWidth = 3,
  startFrame = 0,
  durationFrames = 20,
  style,
}) => {
  const frame = useCurrentFrame();
  const progress = interpolate(
    frame,
    [startFrame, startFrame + durationFrames],
    [0, 1],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
  );
  const commonProps = {color, strokeWidth, progress};
  let annotation: React.ReactNode;
  if (type === 'highlight')    annotation = <Highlight     {...commonProps}>{children}</Highlight>;
  else if (type === 'circle')  annotation = <RoughCircle   {...commonProps}>{children}</RoughCircle>;
  else if (type === 'box')     annotation = <RoughBox      {...commonProps}>{children}</RoughBox>;
  else                         annotation = <Underline     {...commonProps}>{children}</Underline>;
  return (
    <span style={{display: 'inline-block', position: 'relative', ...style}}>
      {annotation}
    </span>
  );
};

// ─── ScalePopBadge ────────────────────────────────────────────────────────────
/**
 * Stat badge that pops in with spring overshoot on a keyword frame.
 *
 * Usage:
 *   <ScalePopBadge label="+150%" subLabel="نمو الإنتاجية" startFrame={45} />
 */
export const ScalePopBadge: React.FC<{
  label: string;
  subLabel?: string;
  startFrame?: number;
  accentColor?: string;
  textColor?: string;
  bg?: string;
  fontSize?: number;
  style?: React.CSSProperties;
}> = ({
  label,
  subLabel,
  startFrame = 0,
  accentColor = '#FFD400',
  textColor = '#141210',
  bg = '#FFF6E3',
  fontSize = 48,
  style,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const sp = spring({
    frame: frame - startFrame,
    fps,
    config: {mass: 0.7, damping: 10, stiffness: 280},
  });
  const scale = interpolate(sp, [0, 1], [0.4, 1], {extrapolateRight: 'clamp'});
  const opacity = interpolate(sp, [0, 0.3], [0, 1], {extrapolateRight: 'clamp'});
  return (
    <div
      style={{
        display: 'inline-flex',
        flexDirection: 'column',
        alignItems: 'center',
        background: bg,
        border: `6px solid ${accentColor}`,
        borderRadius: 20,
        padding: '14px 28px',
        transform: `scale(${scale})`,
        opacity,
        boxShadow: `8px 8px 0 ${accentColor}`,
        ...style,
      }}
    >
      <span style={{fontSize, fontWeight: 900, color: textColor, lineHeight: 1}}>{label}</span>
      {subLabel && (
        <span style={{fontSize: fontSize * 0.42, fontWeight: 600, color: textColor, opacity: 0.7, marginTop: 4}}>
          {subLabel}
        </span>
      )}
    </div>
  );
};

// ─── MorphIcon ────────────────────────────────────────────────────────────────
/**
 * Cross-fades between two SVG icon paths at a trigger frame.
 * Both paths must have the same number of commands for best results.
 *
 * Usage:
 *   <MorphIcon fromPath="M..." toPath="M..." triggerFrame={40} size={80} color="#E63329" />
 */
export const MorphIcon: React.FC<{
  fromPath: string;
  toPath: string;
  triggerFrame?: number;
  durationFrames?: number;
  size?: number;
  color?: string;
  style?: React.CSSProperties;
}> = ({fromPath, toPath, triggerFrame = 0, durationFrames = 20, size = 80, color = 'currentColor', style}) => {
  const frame = useCurrentFrame();
  const p = interpolate(
    frame,
    [triggerFrame, triggerFrame + durationFrames],
    [0, 1],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)},
  );
  // Cross-fade: show fromPath fading out, toPath fading in
  return (
    <svg viewBox="0 0 24 24" width={size} height={size} style={{display: 'inline-block', ...style}}>
      <path d={fromPath} fill={color} opacity={1 - p} />
      <path d={toPath}   fill={color} opacity={p} />
    </svg>
  );
};

// ─── DrawUnderline ────────────────────────────────────────────────────────────
/**
 * Simple animated underline that draws from left to right under text.
 * Useful when you don't need full RoughAnnotation.
 */
export const DrawUnderline: React.FC<{
  width: number;
  color?: string;
  strokeWidth?: number;
  startFrame?: number;
  durationFrames?: number;
  style?: React.CSSProperties;
}> = ({width, color = '#FFD400', strokeWidth = 5, startFrame = 0, durationFrames = 15, style}) => {
  const frame = useCurrentFrame();
  const progress = interpolate(frame, [startFrame, startFrame + durationFrames], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.quad),
  });
  return (
    <svg
      width={width}
      height={strokeWidth + 4}
      style={{display: 'block', ...style}}
    >
      <line
        x1={0}
        y1={strokeWidth / 2 + 2}
        x2={width * progress}
        y2={strokeWidth / 2 + 2}
        stroke={color}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
      />
    </svg>
  );
};
