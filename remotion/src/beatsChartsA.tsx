// Split from beats.tsx (re-exported there).
import React, {useId} from 'react';
import {AbsoluteFill, interpolate, staticFile} from 'remotion';
import {SafeImg} from './SafeImg';
import {FireSparks, GlowText, MapOverlay} from './fx';
import {clamp01, enterStyle, useFont, useProgress, useSpring} from './hooks';
import {rgba, useTheme} from './theme';
import {BEAT_ZONE} from './layout';
import {Beat} from './types';
import {cueSecOf, parseNum} from './beats';

export const StatRingV2Beat: React.FC<{beat: Beat}> = ({beat}) => {
  const th = useTheme();
  const font = useFont();
  const p = useProgress(0.12, 1.4);
  const a = useSpring(0.08, 'bouncy');
  const cy = th.zoneCy - 60;
  const s = String(beat.number ?? '');
  const pn = parseNum(s);
  const show = pn ? pn.pre + (pn.commas ? (pn.val * p).toLocaleString('en-US', {minimumFractionDigits: pn.dec, maximumFractionDigits: pn.dec}) : (pn.val * p).toFixed(pn.dec)) + pn.suf : s;

  const R = 230;
  const C = 2 * Math.PI * R;
  const iconPath = beat.icon || 'icons/coin/gold_bars.svg';
  const iconSrc = staticFile(iconPath);

  return (
    <AbsoluteFill style={{overflow: 'hidden'}}>
      <MapOverlay opacity={0.6} />
      <FireSparks n={20} />

      <svg
        width={1080}
        height={1920}
        style={{position: 'absolute', inset: 0, opacity: clamp01(a * 1.5)}}
      >
        <defs>
          <linearGradient id="ringGradV2" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor={rgba(th.p.accent, 0.6)} />
            <stop offset="50%" stopColor={rgba(th.p.accent)} />
            <stop offset="100%" stopColor={rgba(th.p.accent2)} />
          </linearGradient>
          <filter id="ringGlowV2" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="0" stdDeviation="16" floodColor={rgba(th.p.accent)} floodOpacity="0.8" />
          </filter>
        </defs>
        <circle cx={540} cy={cy - 120} r={R} fill="none" stroke="rgba(255, 255, 255, 0.12)" strokeWidth={16} />
        <circle
          cx={540}
          cy={cy - 120}
          r={R}
          fill="none"
          stroke="url(#ringGradV2)"
          strokeWidth={18}
          strokeLinecap="round"
          strokeDasharray={C}
          strokeDashoffset={C * (1 - p)}
          transform={`rotate(-90 540 ${cy - 120})`}
          filter="url(#ringGlowV2)"
        />
      </svg>

      <div
        style={{
          position: 'absolute',
          left: 540 - 100,
          top: cy - 120 - 100,
          width: 200,
          height: 200,
          borderRadius: '50%',
          background: 'radial-gradient(circle at 35% 35%, rgba(45, 55, 72, 0.7), rgba(15, 23, 42, 0.85))',
          border: `2px solid ${rgba(th.p.accent, 0.5)}`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backdropFilter: 'blur(10px)',
          ...enterStyle(a, 'pop'),
        }}
      >
        <SafeImg src={iconSrc} fallbackSrc={staticFile('icons/star/star.svg')} style={{width: 120, height: 120, objectFit: 'contain'}} />
      </div>

      <div
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          top: cy + 150,
          textAlign: 'center',
          ...enterStyle(a, 'rise', 40),
        }}
      >
        <GlowText fontSize={130} gold={false}>
          {show}
        </GlowText>
      </div>

      {beat.label && (
        <div
          dir="rtl"
          style={{
            position: 'absolute',
            left: 90,
            right: 90,
            top: cy + 320,
            display: 'flex',
            justifyContent: 'center',
          }}
        >
          <div
            style={{
              padding: '12px 36px',
              borderRadius: 30,
              background: 'rgba(15, 23, 42, 0.85)',
              border: `1.5px solid ${rgba(th.p.accent, 0.5)}`,
              fontFamily: th.family,
              fontSize: 48,
              fontWeight: 700,
              color: '#FFFFFF',
              boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
              textShadow: th.shadow,
            }}
          >
            {beat.label}
          </div>
        </div>
      )}
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ مخطط الارتفاع (جبل فوق سطح البحر)

export const ElevationProfileBeat: React.FC<{beat: Beat}> = ({beat}) => {
  const th = useTheme();
  const font = useFont();
  const uid = useId().replace(/:/g, '');

  const SEA_Y = BEAT_ZONE.sea_y;
  const PEAK_Y = BEAT_ZONE.peak_y;
  const CX = 540;

  const mountainProg = useProgress(0, 0.65);
  const seaProg = useProgress(0.35, 0.4);
  const heightProg = useProgress(cueSecOf(beat, 'metric_start', 0.55), 1.1);

  const clipY = interpolate(mountainProg, [0, 1], [SEA_Y, PEAK_Y - 20], {extrapolateRight: 'clamp'});
  const lineY = interpolate(heightProg, [0, 1], [SEA_Y, PEAK_Y], {extrapolateRight: 'clamp'});

  const h_str = String(beat.height || '0');
  const pn = parseNum(h_str);
  const hVal = pn ? Math.round(pn.val * Math.min(1, heightProg)) : 0;
  const hShow = hVal.toLocaleString('en-US');

  const unit = String(beat.unit || 'م');
  const seaLabel = String(beat.sea_label || 'سطح البحر');

  const mPath = `M 160 ${SEA_Y} C 250 ${SEA_Y} 390 980 500 700 C 520 600 530 490 ${CX} ${PEAK_Y} C 550 490 560 600 580 700 C 690 980 830 ${SEA_Y} 920 ${SEA_Y} Z`;
  const accentC = rgba(th.p.accent);
  const accent2C = rgba(th.p.accent2);
  const textC = rgba(th.p.text);

  return (
    <AbsoluteFill>
      <svg width={1080} height={1920} style={{position: 'absolute', inset: 0}}>
        <defs>
          <linearGradient id={`${uid}g`} x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor={accentC} stopOpacity="0.85" />
            <stop offset="65%" stopColor={accent2C} stopOpacity="0.6" />
            <stop offset="100%" stopColor={accent2C} stopOpacity="0.2" />
          </linearGradient>
          <clipPath id={`${uid}c`}>
            <rect x={0} y={clipY} width={1080} height={SEA_Y - clipY + 60} />
          </clipPath>
          <filter id={`${uid}f`} x="-10%" y="-10%" width="120%" height="120%">
            <feDropShadow dx="0" dy="-6" stdDeviation="20" floodColor={accentC} floodOpacity="0.5" />
          </filter>
        </defs>

        {/* Mountain body */}
        <path d={mPath} fill={`url(#${uid}g)`} clipPath={`url(#${uid}c)`} filter={`url(#${uid}f)`} />
        <path d={mPath} fill="none" stroke={rgba(th.p.accent, 0.45)} strokeWidth={3} clipPath={`url(#${uid}c)`} />
        {/* Snow cap */}
        <ellipse cx={CX} cy={PEAK_Y + 24} rx={58} ry={22} fill="rgba(235,248,255,0.9)" clipPath={`url(#${uid}c)`} />

        {/* Sea level horizontal line */}
        <line x1={80} y1={SEA_Y} x2={1000} y2={SEA_Y}
          stroke={accent2C} strokeWidth={4} strokeLinecap="round"
          opacity={Math.min(1, seaProg * 2.5)} />

        {/* Dashed height indicator line rising from sea to peak */}
        {heightProg > 0.01 && (
          <line x1={CX} y1={SEA_Y} x2={CX} y2={lineY}
            stroke={textC} strokeWidth={3}
            strokeDasharray="14 10" strokeLinecap="round" opacity={0.7} />
        )}

        {/* Tick marks at 25%, 50%, 75% of height */}
        {([0.25, 0.5, 0.75] as number[]).map((frac, i) => {
          const tickY = SEA_Y - (SEA_Y - PEAK_Y) * frac;
          const op = Math.max(0, Math.min(0.5, (heightProg - frac) * 4));
          return op > 0 ? (
            <line key={i} x1={CX - 24} y1={tickY} x2={CX + 24} y2={tickY}
              stroke={textC} strokeWidth={2} opacity={op} />
          ) : null;
        })}

        {/* Sea level label */}
        {seaProg > 0.3 && (
          <text x={96} y={SEA_Y - 14} fontSize={34} fontWeight={700}
            fill={accent2C} opacity={Math.min(1, (seaProg - 0.3) * 4)}
            fontFamily={th.family} textAnchor="end" direction="rtl">
            {seaLabel} = 0 م
          </text>
        )}
      </svg>

      {/* Peak name */}
      {beat.title && mountainProg > 0.72 && (
        <div style={{
          position: 'absolute', left: 80, right: 80, top: PEAK_Y - 215,
          textAlign: 'center', ...font, fontSize: 60, fontWeight: 900,
          color: textC, textShadow: th.shadow, direction: 'rtl',
          opacity: Math.min(1, (mountainProg - 0.72) * 4),
          translate: `0 ${(1 - Math.min(1, (mountainProg - 0.72) * 4)) * -20}px`,
        }}>
          {beat.title}
        </div>
      )}

      {/* Floating height counter badge alongside the dashed line */}
      {heightProg > 0.04 && (
        <div style={{
          position: 'absolute',
          left: CX + 28,
          top: lineY - 46,
          transform: `scale(${Math.min(1, heightProg * 2.5)})`,
          transformOrigin: 'left center',
        }}>
          <div style={{
            display: 'inline-flex', alignItems: 'baseline', gap: 8,
            padding: '8px 24px',
            borderRadius: 32,
            background: 'rgba(8, 12, 24, 0.9)',
            border: `2px solid ${accentC}`,
            boxShadow: `0 0 20px ${rgba(th.p.accent, 0.5)}`,
            whiteSpace: 'nowrap',
          }}>
            <span style={{...font, fontSize: 72, color: accentC, direction: 'ltr', lineHeight: 1}}>{hShow}</span>
            <span style={{...font, fontSize: 38, color: textC, lineHeight: 1}}>{unit}</span>
          </div>
        </div>
      )}
    </AbsoluteFill>
  );
};
