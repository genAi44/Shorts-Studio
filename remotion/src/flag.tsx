import React, {useMemo} from 'react';
import {interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import flagCountries from './generated/flagCountries.json';
import {SafeImg} from './SafeImg';
import type {FlagShape} from './schema';

export interface FlagProps {
  code: string;
  shape?: FlagShape;
  size?: number;
  animation?: 'none' | 'pop' | 'float' | 'wave';
  delayFrames?: number;
  style?: React.CSSProperties;
}

const ISO3_TO_ISO2: Record<string, string> = (flagCountries as any).iso3ToIso2 || {};
const COUNTRIES: Array<{iso2: string; iso3: string; ar: string[]; en: string[]}> =
  (flagCountries as any).countries || [];

/**
 * Resolves ISO-2 ("EG"), ISO-3 ("EGY"), Arabic name ("مصر"), or English name ("Egypt")
 * to lowercase ISO-2 code ("eg"). EXACT matches only.
 * Returns '' when unknown — callers must render nothing rather than a wrong/default flag.
 */
export const resolveCountryIso2 = (input: string): string => {
  const raw = (input || '').trim();
  if (!raw) return '';
  const upper = raw.toUpperCase();
  const lower = raw.toLowerCase();

  if (/^[A-Z]{2}$/.test(upper)) {
    // Python pipeline already verified flags/4x3/{iso2}.svg exists for every code it emits.
    return lower;
  }
  if (/^[A-Z]{3}$/.test(upper)) {
    return ISO3_TO_ISO2[upper] ? ISO3_TO_ISO2[upper].toLowerCase() : '';
  }

  for (const c of COUNTRIES) {
    if (c.ar.some((a) => a === raw)) return c.iso2.toLowerCase();
    if (c.en.some((e) => e.toLowerCase() === lower)) return c.iso2.toLowerCase();
  }

  return '';
};

export const Flag: React.FC<FlagProps> = ({
  code,
  shape = 'rect',
  size = 96,
  animation = 'pop',
  delayFrames = 0,
  style,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const localFrame = Math.max(0, frame - delayFrames);
  const iso2 = useMemo(() => resolveCountryIso2(code), [code]);
  if (!iso2) return null;

  let scale = 1;
  let translateY = 0;
  let skewDeg = 0;
  let opacity = 1;

  if (animation === 'pop') {
    const sp = spring({
      frame: localFrame,
      fps,
      config: {damping: 12, stiffness: 180, mass: 0.7},
    });
    scale = interpolate(sp, [0, 1], [0.25, 1]);
    opacity = Math.min(1, sp * 1.5);
  } else if (animation === 'float') {
    const sp = spring({frame: localFrame, fps, config: {damping: 15, stiffness: 140}});
    scale = sp;
    translateY = Math.sin((localFrame / fps) * Math.PI * 1.5) * 7;
    opacity = Math.min(1, sp * 1.5);
  } else if (animation === 'wave') {
    const sp = spring({frame: localFrame, fps, config: {damping: 14, stiffness: 150}});
    scale = sp;
    skewDeg = Math.sin((localFrame / fps) * Math.PI * 2.4) * 4;
    opacity = Math.min(1, sp * 1.5);
  }

  const isRound = shape === 'round';
  const ratioFolder = isRound ? '1x1' : '4x3';
  const width = isRound ? size : Math.round(size * (4 / 3));
  const height = size;
  const src = staticFile(`flags/${ratioFolder}/${iso2}.svg`);

  return (
    <div
      data-flag-iso2={iso2}
      data-flag-shape={shape}
      style={{
        width,
        height,
        borderRadius: isRound ? '50%' : Math.max(8, Math.round(size * 0.12)),
        overflow: 'hidden',
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        border: '3px solid rgba(255, 255, 255, 0.82)',
        boxShadow: '0 8px 24px rgba(0, 0, 0, 0.45)',
        opacity,
        transform: `translateY(${translateY.toFixed(2)}px) scale(${scale.toFixed(3)}) skewY(${skewDeg.toFixed(2)}deg)`,
        transformOrigin: 'center center',
        ...style,
      }}
    >
      <SafeImg
        src={src}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
        }}
      />
    </div>
  );
};

