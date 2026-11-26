// Split from sceneBeats.tsx (re-exported there).
import React, {useId} from 'react';
import {AbsoluteFill, useCurrentFrame, useVideoConfig} from 'remotion';
import {useTheme, rgba} from './theme';
import {clamp01, enterStyle, useFont, useProgress, useSpring} from './hooks';
import {BEAT_ZONE, CAPTION_ZONE} from './layout';
import type {Beat} from './types';

// ── Shared: Question text block ───────────────────────────────────────────────

// Panel behind a scene: confined to the beat zone with feathered top/bottom so it never shows as a hard rectangle
// and never reaches the caption zone.
export const SoftBg: React.FC<{id: string}> = ({id}) => {
  const y = BEAT_ZONE.top - 60;
  const h = BEAT_ZONE.bottom - BEAT_ZONE.top + 120;
  return (
    <>
      <defs>
        <linearGradient id={`${id}fy`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#fff" stopOpacity="0" />
          <stop offset="0.14" stopColor="#fff" />
          <stop offset="0.86" stopColor="#fff" />
          <stop offset="1" stopColor="#fff" stopOpacity="0" />
        </linearGradient>
        <mask id={`${id}fm`}><rect x={0} y={y} width={1080} height={h} fill={`url(#${id}fy)`} /></mask>
      </defs>
      <rect x={0} y={y} width={1080} height={h} fill={`url(#${id}bg)`} mask={`url(#${id}fm)`} />
    </>
  );
};

export const QuestionText: React.FC<{
  question: string; subtitle: string; textProg: number;
  th: ReturnType<typeof useTheme>; font: React.CSSProperties;
}> = ({question, subtitle, textProg, th, font}) => {
  if (!question) return null;
  const lines = question.split(/[،؟?.]/u).filter(Boolean).map(s => s.trim()).filter(Boolean);
  const main = lines[0] ?? question;
  const rest = lines.slice(1).join(' ').trim();

  return (
    <div style={{
      position: 'absolute',
      left: 80, right: 80,
      bottom: 1920 - CAPTION_ZONE.top + 20, // sits just above the captions, never under them
      ...enterStyle(textProg, 'rise', 44),
      textAlign: 'center',
      direction: 'rtl',
    }}>
      {subtitle && (
        <div style={{
          ...font, fontSize: 38, fontWeight: 600,
          color: rgba(th.p.text, 0.6),
          marginBottom: 16,
          letterSpacing: '0.08em',
        }}>{subtitle}</div>
      )}
      <div style={{
        ...font, fontSize: 68, fontWeight: 800,
        color: rgba(th.p.text, 0.95),
        lineHeight: 1.4, textShadow: th.shadow,
      }}>{main}</div>
      {rest && (
        <div style={{
          ...font, fontSize: 54, fontWeight: 700,
          color: rgba(th.p.text, 0.75),
          marginTop: 10, lineHeight: 1.4,
        }}>{rest}</div>
      )}
    </div>
  );
};

// ── Mystery Scene ─────────────────────────────────────────────────────────────

export const MysterySceneBeat: React.FC<{beat: Beat}> = ({beat}) => {
  const th = useTheme();
  const font = useFont();
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const rawId = useId();
  const id = `ms${rawId.replace(/[^a-z0-9]/gi, '')}`;

  const seed = typeof beat.seed === 'number' ? beat.seed : (beat.from ?? 0) + 7;
  const rawVariant = typeof beat.variant === 'number' ? beat.variant : (Math.abs(seed) % 3);
  const variant = rawVariant % 3;

  const title = String(beat.title ?? '');
  const question = String(beat.question ?? beat.text ?? title);
  const subtitle = String(beat.subtitle ?? beat.sub ?? '');

  const bgProg = useProgress(0.0, 0.5);
  const qProg = useSpring(0.1, 'bouncy');
  const textProg = useSpring(0.4, 'smooth');
  const ringPulse = (Math.sin((frame / fps) * 2.1) + 1) / 2;

  const CX = 540;
  const CY = 820;
  const accent = rgba(th.p.accent);

  // ── Variant 0: Cosmic rings ───────────────────────────────────────────────
  if (variant === 0) {
    return (
      <AbsoluteFill>
        <svg width={1080} height={1920} style={{position: 'absolute', inset: 0}}>
          <defs>
            <radialGradient id={`${id}bg`} cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#0d1830" />
              <stop offset="100%" stopColor="#05090f" />
            </radialGradient>
          </defs>
          <SoftBg id={id} />

          {[300, 230, 170, 110].map((r, i) => {
            const delay = i * 0.08;
            const rp = clamp01((bgProg * 2) - delay);
            const pulse = 0.08 + 0.06 * ringPulse * (1 - i * 0.15);
            const pulsedR = r * (1 + pulse * rp);
            return (
              <circle key={i} cx={CX} cy={CY} r={pulsedR}
                fill="none"
                stroke={i === 0 ? rgba(th.p.accent, 0.25 + 0.1 * ringPulse) : rgba(th.p.text, 0.08 + 0.04 * i)}
                strokeWidth={i === 0 ? 3 : 1.5}
                strokeDasharray={i % 2 !== 0 ? `${r * 0.3} ${r * 0.08}` : undefined}
                opacity={rp}
              />
            );
          })}

          {Array.from({length: 16}, (_, i) => {
            const ang = (i / 16) * Math.PI * 2 + (frame / fps) * 0.3;
            const dist = 240 + Math.sin(ang * 2 + frame / fps) * 30;
            return (
              <circle key={i}
                cx={CX + dist * Math.cos(ang)}
                cy={CY + dist * Math.sin(ang)}
                r={3}
                fill={accent}
                opacity={0.4 * bgProg}
              />
            );
          })}

          <circle cx={CX} cy={CY} r={120}
            fill={rgba(th.p.accent, 0.07 + 0.05 * ringPulse)}
          />
        </svg>

        <div style={{
          position: 'absolute', left: 0, right: 0, top: CY - 130,
          textAlign: 'center',
          ...enterStyle(qProg, 'pop', 0),
        }}>
          <div style={{
            ...font, fontSize: 240, fontWeight: 900, lineHeight: 1,
            color: accent,
            textShadow: `0 0 60px ${rgba(th.p.accent, 0.5)}, 0 4px 32px rgba(0,0,0,0.6)`,
          }}>؟</div>
        </div>

        <QuestionText question={question} subtitle={subtitle} textProg={textProg} th={th} font={font} />
      </AbsoluteFill>
    );
  }

  // ── Variant 1: Hexagonal frame ────────────────────────────────────────────
  if (variant === 1) {
    const HEX_R = 220;
    const hexPts = (r: number) => Array.from({length: 6}, (_, i) => {
      const ang = (i / 6) * Math.PI * 2 - Math.PI / 6;
      return `${CX + r * Math.cos(ang)},${CY + r * Math.sin(ang)}`;
    }).join(' ');

    return (
      <AbsoluteFill>
        <svg width={1080} height={1920} style={{position: 'absolute', inset: 0}}>
          <defs>
            <radialGradient id={`${id}bg`} cx="50%" cy="45%" r="55%">
              <stop offset="0%" stopColor="#101a2e" />
              <stop offset="100%" stopColor="#060910" />
            </radialGradient>
          </defs>
          <SoftBg id={id} />

          <polygon points={hexPts(HEX_R + 25)}
            fill="none"
            stroke={rgba(th.p.accent, 0.15 + 0.1 * ringPulse)}
            strokeWidth={2}
            opacity={bgProg}
            transform={`rotate(${(frame / fps) * 2},${CX},${CY})`}
          />

          <polygon points={hexPts(HEX_R)}
            fill={rgba(th.p.c1, 0.4)}
            stroke={accent}
            strokeWidth={4}
            opacity={bgProg}
          />

          {Array.from({length: 6}, (_, i) => {
            const ang = (i / 6) * Math.PI * 2 - Math.PI / 6;
            return (
              <circle key={i}
                cx={CX + HEX_R * Math.cos(ang)}
                cy={CY + HEX_R * Math.sin(ang)}
                r={8} fill={accent} opacity={bgProg * 0.9}
              />
            );
          })}

          <polygon points={hexPts(HEX_R)}
            fill={rgba(th.p.accent, 0.04 + 0.03 * ringPulse)}
          />
        </svg>

        <div style={{
          position: 'absolute', left: 0, right: 0, top: CY - 130,
          textAlign: 'center',
          ...enterStyle(qProg, 'pop', 0),
        }}>
          <div style={{
            ...font, fontSize: 220, fontWeight: 900, lineHeight: 1,
            color: accent,
            textShadow: `0 0 50px ${rgba(th.p.accent, 0.45)}, 0 4px 24px rgba(0,0,0,0.6)`,
          }}>؟</div>
        </div>

        <QuestionText question={question} subtitle={subtitle} textProg={textProg} th={th} font={font} />
      </AbsoluteFill>
    );
  }

  // ── Variant 2: Radial / target ────────────────────────────────────────────
  return (
    <AbsoluteFill>
      <svg width={1080} height={1920} style={{position: 'absolute', inset: 0}}>
        <defs>
          <radialGradient id={`${id}bg`} cx="50%" cy="45%" r="60%">
            <stop offset="0%" stopColor="#0e1a2b" />
            <stop offset="100%" stopColor="#050810" />
          </radialGradient>
        </defs>
        <SoftBg id={id} />

        {Array.from({length: 24}, (_, i) => {
          const ang = (i / 24) * Math.PI * 2 + (frame / fps) * 0.15;
          const len = 180 + (i % 3) * 50;
          return (
            <line key={i}
              x1={CX} y1={CY}
              x2={CX + len * Math.cos(ang)}
              y2={CY + len * Math.sin(ang)}
              stroke={rgba(th.p.text, 0.06 + (i % 2 === 0 ? 0.03 : 0))}
              strokeWidth={1}
              opacity={bgProg}
            />
          );
        })}

        {[80, 160, 250].map((r, i) => (
          <circle key={i} cx={CX} cy={CY} r={r}
            fill="none"
            stroke={i === 0 ? accent : rgba(th.p.text, 0.08)}
            strokeWidth={i === 0 ? 2.5 : 1}
            opacity={bgProg * (0.9 - i * 0.2)}
          />
        ))}

        <line x1={80} y1={CY + 300} x2={1000} y2={CY + 300}
          stroke={rgba(th.p.accent, 0.3 * bgProg)} strokeWidth={2}
        />
        {[0.2, 0.5, 0.8].map((frac, i) => (
          <circle key={i}
            cx={80 + frac * 920} cy={CY + 300} r={6}
            fill={rgba(th.p.accent, 0.5 * bgProg)}
          />
        ))}
      </svg>

      <div style={{
        position: 'absolute', left: 0, right: 0, top: CY - 130,
        textAlign: 'center',
        ...enterStyle(qProg, 'pop', 0),
      }}>
        <div style={{
          ...font, fontSize: 230, fontWeight: 900, lineHeight: 1,
          color: accent,
          textShadow: `0 0 55px ${rgba(th.p.accent, 0.48)}, 0 4px 28px rgba(0,0,0,0.6)`,
        }}>؟</div>
      </div>

      <QuestionText question={question} subtitle={subtitle} textProg={textProg} th={th} font={font} />
    </AbsoluteFill>
  );
};
