/**
 * AnimatedMetric — Smooth number roll-up counter.
 * Used for population, ranking, area, GDP etc.
 * Already deterministic (pure frame math, no Date.now).
 */
import React from 'react';
import {interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {useFont, useSpring} from './hooks';
import {rgba, useTheme} from './theme';

/** Format large numbers with language-aware abbreviations. */
export const formatLargeNum = (n: number, lang = 'ar'): string => {
  const abs = Math.abs(n);
  const sign = n < 0 ? '-' : '';
  if (abs >= 1e9)
    return sign + (abs / 1e9).toFixed(1) + (lang === 'ar' ? ' مليار' : 'B');
  if (abs >= 1e6)
    return sign + (abs / 1e6).toFixed(1) + (lang === 'ar' ? ' مليون' : 'M');
  if (abs >= 1e3)
    return sign + (abs / 1e3).toFixed(0) + (lang === 'ar' ? ' ألف' : 'K');
  return sign + Math.abs(n).toLocaleString();
};

export const AnimatedMetric: React.FC<{
  value: number;
  prefix?: string;
  suffix?: string;
  /** delay in seconds from beat frame 0 */
  delay?: number;
  /** roll-up duration in seconds */
  dur?: number;
  fontSize?: number;
  color?: string;
  lang?: string;
  /** 'large' = M/B/K abbreviation, 'exact' = full digits with comma */
  format?: 'large' | 'exact';
  /** frame at which to apply a punch/shake pop (default none) */
  punchFrame?: number;
}> = ({
  value,
  prefix = '',
  suffix = '',
  delay = 0,
  dur = 1.5,
  fontSize = 72,
  color,
  lang = 'ar',
  format = 'large',
  punchFrame,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const th = useTheme();
  const font = useFont();

  // spring pop-in
  const sp = useSpring(delay, 'bouncy');

  // number roll-up with ease-out cubic
  const prog = interpolate(
    frame,
    [delay * fps, (delay + dur) * fps],
    [0, 1],
    {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
      easing: (t) => 1 - Math.pow(1 - t, 3),
    },
  );
  const current = Math.round(prog * value);

  // impact punch scale on a specific frame
  let punch = 1;
  if (punchFrame !== undefined) {
    const t = frame - punchFrame;
    if (t >= 0 && t < 10) {
      const d = 1 - t / 10;
      punch = 1 + 0.08 * Math.sin(t * Math.PI) * d;
    }
  }

  const display =
    format === 'large'
      ? formatLargeNum(current, lang)
      : current.toLocaleString();

  const col = color ?? rgba(th.p.accent);

  return (
    <div
      dir="ltr"
      style={{
        ...font,
        fontSize,
        fontWeight: 900,
        color: col,
        textShadow: `0 0 24px ${col}88, 0 4px 12px rgba(0,0,0,0.8)`,
        transform: `scale(${(0.6 + 0.4 * sp) * punch})`,
        display: 'inline-block',
        lineHeight: 1,
      }}
    >
      {prefix}
      {display}
      {suffix}
    </div>
  );
};

/**
 * MetricBadge — Pill-shaped container for a metric with label.
 * Drop-in replacement for the flat stat badges in icon scenes.
 */
export const MetricBadge: React.FC<{
  value: number;
  label?: string;
  prefix?: string;
  suffix?: string;
  delay?: number;
  lang?: string;
}> = ({value, label, prefix, suffix, delay = 0, lang = 'ar'}) => {
  const th = useTheme();
  const font = useFont();
  const sp = useSpring(delay + 0.1, 'snappy');

  return (
    <div
      style={{
        display: 'inline-flex',
        flexDirection: 'column',
        alignItems: 'center',
        background: 'rgba(10,15,25,0.82)',
        backdropFilter: 'blur(14px)',
        border: `2px solid ${rgba(th.p.accent, 0.6)}`,
        borderRadius: 20,
        padding: '10px 28px',
        boxShadow: `0 8px 24px rgba(0,0,0,0.5), 0 0 20px ${rgba(th.p.accent, 0.2)}`,
        transform: `scale(${sp}) translateY(${(1 - sp) * 24}px)`,
        opacity: Math.min(1, sp * 1.4),
      }}
    >
      <AnimatedMetric
        value={value}
        prefix={prefix}
        suffix={suffix}
        delay={delay}
        fontSize={52}
        lang={lang}
      />
      {label && (
        <div
          dir="rtl"
          style={{
            ...font,
            fontSize: 28,
            fontWeight: 700,
            color: rgba(th.p.text, 0.85),
            marginTop: 4,
          }}
        >
          {label}
        </div>
      )}
    </div>
  );
};
