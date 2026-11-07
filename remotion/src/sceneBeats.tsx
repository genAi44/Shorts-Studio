/**
 * sceneBeats.tsx — Vector-based scene beat components.
 * CitySceneBeat, ArchitectureBeat, MysterySceneBeat.
 * Everything is SVG/CSS — no raster images, no external assets.
 */

import React, {useId, useMemo} from 'react';
import {AbsoluteFill, useCurrentFrame, useVideoConfig} from 'remotion';
import {useTheme, rgba} from './theme';
import {clamp01, enterStyle, useFont, useIdle, useProgress, useSpring} from './hooks';
import {BEAT_ZONE} from './layout';
import type {Beat} from './types';

// ── Deterministic LCG PRNG ────────────────────────────────────────────────────
const mkRng = (seed: number) => {
  let s = ((seed ^ 0x6e37ba91) & 0xffffffff) >>> 0;
  return () => { s = ((s * 1664525 + 1013904223) & 0xffffffff) >>> 0; return s / 4294967296; };
};

// ── City Skyline ──────────────────────────────────────────────────────────────

type Win = {dx: number; dy: number; w: number; h: number; lit: boolean};
type Bldg = {x: number; w: number; h: number; fill: string; windows: Win[]; delay: number};

const mkBuildings = (rng: () => number, count: number, minH: number, maxH: number, minW: number, maxW: number, hue: number): Bldg[] => {
  const slot = 1080 / count;
  return Array.from({length: count}, (_, i) => {
    const w = minW + rng() * (maxW - minW);
    const h = minH + rng() * (maxH - minH);
    const x = i * slot - w / 2 + slot / 2 + (rng() - 0.5) * slot * 0.4;
    const lum = 9 + rng() * 10;
    const fill = `hsl(${hue + (rng() - 0.5) * 25},${18 + rng() * 18}%,${lum}%)`;
    const cols = Math.max(1, Math.floor(w / 30));
    const rows = Math.max(1, Math.floor(h / 50));
    const winW = 9 + rng() * 8;
    const winH = 11 + rng() * 10;
    const windows: Win[] = [];
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        if (rng() < 0.72) {
          windows.push({
            dx: (c + 0.5) * (w / cols) - winW / 2,
            dy: (r + 0.5) * (h / rows),
            w: winW,
            h: winH,
            lit: rng() < 0.6,
          });
        }
      }
    }
    return {x, w, h, fill, windows, delay: rng() * 0.25};
  });
};

const BldgEl: React.FC<{b: Bldg; prog: number; groundY: number}> = ({b, groundY, prog}) => {
  const topY = groundY - b.h;
  const p = clamp01((prog - b.delay) / (1 - b.delay + 0.001));
  const shift = (1 - p) * b.h * 0.9;
  const alpha = clamp01(p * 2.5);
  const winAlpha = clamp01((p - 0.5) * 3);

  return (
    <g transform={`translate(0,${shift})`} opacity={alpha}>
      <rect x={b.x} y={topY} width={b.w} height={b.h} fill={b.fill} rx={2} />
      <rect x={b.x + 2} y={topY - 7} width={b.w - 4} height={7} fill={b.fill} opacity={0.75} />
      {b.windows.map((win, i) =>
        win.lit ? (
          <rect
            key={i}
            x={b.x + win.dx}
            y={topY + win.dy}
            width={win.w}
            height={win.h}
            fill="rgba(255,218,100,0.75)"
            rx={1}
            opacity={winAlpha}
          />
        ) : null
      )}
    </g>
  );
};

export const CitySceneBeat: React.FC<{beat: Beat}> = ({beat}) => {
  const th = useTheme();
  const font = useFont();
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const rawId = useId();
  const id = `cs${rawId.replace(/[^a-z0-9]/gi, '')}`;

  const seed = typeof beat.seed === 'number' ? beat.seed : (beat.from ?? 0) + 11;

  const {bgBuilds, midBuilds, fgBuilds, stars} = useMemo(() => {
    const rng = mkRng(seed);
    const bgBuilds = mkBuildings(rng, 8, 170, 310, 55, 100, 215);
    const midBuilds = mkBuildings(rng, 6, 260, 460, 85, 150, 220);
    const fgBuilds = mkBuildings(rng, 4, 330, 580, 120, 200, 228);
    const stars = Array.from({length: 28}, () => ({
      x: rng() * 1080,
      y: BEAT_ZONE.top + rng() * 450,
      r: 0.8 + rng() * 2.2,
      phase: rng() * Math.PI * 2,
    }));
    return {bgBuilds, midBuilds, fgBuilds, stars};
  }, [seed]);

  const groundY = 1200;
  const bgProg = useProgress(0.05, 0.75);
  const midProg = useProgress(0.15, 0.75);
  const fgProg = useProgress(0.28, 0.75);
  const titleProg = useSpring(0.65, 'smooth');

  const title = String(beat.title ?? '');
  const subtitle = String(beat.subtitle ?? beat.sub ?? beat.text ?? '');

  return (
    <AbsoluteFill>
      <svg width={1080} height={1920} style={{position: 'absolute', inset: 0}}>
        <defs>
          <linearGradient id={`${id}sky`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#040d1a" />
            <stop offset="55%" stopColor="#0b2240" />
            <stop offset="100%" stopColor="#122d55" />
          </linearGradient>
          <linearGradient id={`${id}gnd`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#08121f" />
            <stop offset="100%" stopColor="#030810" />
          </linearGradient>
        </defs>

        {/* Sky */}
        <rect x={0} y={BEAT_ZONE.top} width={1080} height={groundY - BEAT_ZONE.top} fill={`url(#${id}sky)`} />

        {/* Stars */}
        {stars.map((s, i) => (
          <circle
            key={i} cx={s.x} cy={s.y} r={s.r}
            fill="white"
            opacity={0.3 + 0.4 * (0.5 + 0.5 * Math.sin((frame / fps) * 1.8 + s.phase))}
          />
        ))}

        {/* Background buildings */}
        {bgBuilds.map((b, i) => <BldgEl key={i} b={b} prog={bgProg} groundY={groundY} />)}

        {/* Midground buildings */}
        {midBuilds.map((b, i) => <BldgEl key={i} b={b} prog={midProg} groundY={groundY} />)}

        {/* Accent horizon glow */}
        <ellipse cx={540} cy={groundY} rx={500} ry={45}
          fill={rgba(th.p.accent, 0.1 * fgProg)}
        />

        {/* Foreground buildings */}
        {fgBuilds.map((b, i) => <BldgEl key={i} b={b} prog={fgProg} groundY={groundY} />)}

        {/* Ground */}
        <rect x={0} y={groundY} width={1080} height={1920 - groundY} fill={`url(#${id}gnd)`} />

        {/* Road lines */}
        {[groundY + 20, groundY + 50].map((y, i) => (
          <line key={i} x1={0} y1={y} x2={1080} y2={y}
            stroke={rgba(th.p.text, i === 0 ? 0.07 : 0.04)} strokeWidth={2}
          />
        ))}
      </svg>

      {/* City name overlay */}
      {title && (
        <div style={{
          position: 'absolute',
          top: BEAT_ZONE.top + 50,
          left: 80, right: 80,
          ...enterStyle(titleProg, 'rise', 48),
          textAlign: 'center',
          direction: 'rtl',
        }}>
          <div style={{...font, fontSize: 88, fontWeight: 900, color: rgba(th.p.accent), textShadow: th.shadow, lineHeight: 1.15}}>
            {title}
          </div>
          {subtitle && (
            <div style={{...font, fontSize: 50, fontWeight: 600, color: rgba(th.p.text, 0.82), marginTop: 10}}>
              {subtitle}
            </div>
          )}
        </div>
      )}
    </AbsoluteFill>
  );
};

// ── Architecture Beat ─────────────────────────────────────────────────────────

interface ArchData {
  columns: number; buildW: number; buildH: number;
  primaryFill: string; stoneFill: string;
  winRows: number; winsPerRow: number;
}

const mkArchData = (seed: number): ArchData => {
  const rng = mkRng(seed);
  const cols = 5 + Math.round(rng() * 2);
  const buildW = 500 + rng() * 100;
  const buildH = 420 + rng() * 100;
  const h1 = 38 + rng() * 10; const s1 = 18 + rng() * 25; const l1 = 68 + rng() * 10;
  return {
    columns: cols, buildW, buildH,
    primaryFill: `hsl(${h1},${s1}%,${l1}%)`,
    stoneFill: `hsl(40,15%,60%)`,
    winRows: 2, winsPerRow: cols - 1,
  };
};

export const ArchitectureBeat: React.FC<{beat: Beat}> = ({beat}) => {
  const th = useTheme();
  const font = useFont();
  const rawId = useId();
  const id = `ab${rawId.replace(/[^a-z0-9]/gi, '')}`;
  const seed = typeof beat.seed === 'number' ? beat.seed : (beat.from ?? 0) + 42;

  const arch = useMemo(() => mkArchData(seed), [seed]);

  const revealProg = useProgress(0.05, 1.0);
  const detailProg = useProgress(0.5, 0.8);
  const titleProg = useSpring(0.7, 'smooth');

  const title = String(beat.title ?? '');
  const subtitle = String(beat.subtitle ?? beat.sub ?? beat.era ?? '');

  const BASE_Y = 1200;
  const TOP_Y = BASE_Y - arch.buildH;
  const BX = (1080 - arch.buildW) / 2;
  const PED_H = 80;
  const FRIZE_H = 40;
  const COL_W = 22;
  const COLS_H = arch.buildH * 0.75;

  const colSpacing = arch.buildW / (arch.columns + 1);
  const colXs = Array.from({length: arch.columns}, (_, i) => BX + (i + 1) * colSpacing - COL_W / 2);

  const winW = 36; const winH = 50;
  const winRowH = arch.buildH / (arch.winRows + 1.5);

  const clipTopY = BASE_Y - arch.buildH * revealProg - PED_H - 20;
  const clipH = (arch.buildH + PED_H + 20) * revealProg + 60;

  return (
    <AbsoluteFill>
      <svg width={1080} height={1920} style={{position: 'absolute', inset: 0}}>
        <defs>
          <linearGradient id={`${id}sky`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#0d1520" />
            <stop offset="100%" stopColor="#1a2d44" />
          </linearGradient>
          <linearGradient id={`${id}face`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={arch.primaryFill} />
            <stop offset="100%" stopColor="hsl(42,20%,62%)" />
          </linearGradient>
          <clipPath id={`${id}reveal`}>
            <rect x={0} y={clipTopY} width={1080} height={clipH} />
          </clipPath>
        </defs>

        {/* Sky BG */}
        <rect x={0} y={BEAT_ZONE.top} width={1080} height={1920 - BEAT_ZONE.top} fill={`url(#${id}sky)`} />

        <g clipPath={`url(#${id}reveal)`}>
          {/* Steps */}
          {[0, 1, 2].map(i => (
            <rect key={i}
              x={BX - i * 20} y={BASE_Y + i * 18}
              width={arch.buildW + i * 40} height={18}
              fill={arch.stoneFill} opacity={0.9 - i * 0.15}
            />
          ))}

          {/* Main facade */}
          <rect x={BX} y={TOP_Y} width={arch.buildW} height={arch.buildH} fill={`url(#${id}face)`} />

          {/* Frieze */}
          <rect x={BX - 10} y={TOP_Y - FRIZE_H} width={arch.buildW + 20} height={FRIZE_H}
            fill={arch.stoneFill} opacity={0.95} />

          {/* Pediment */}
          <polygon
            points={`${BX - 20},${TOP_Y - FRIZE_H} ${BX + arch.buildW / 2},${TOP_Y - FRIZE_H - PED_H} ${BX + arch.buildW + 20},${TOP_Y - FRIZE_H}`}
            fill={arch.stoneFill}
          />

          {/* Columns */}
          {colXs.map((cx, i) => (
            <g key={i}>
              <rect x={cx} y={TOP_Y} width={COL_W} height={COLS_H} fill={arch.stoneFill} rx={COL_W / 2} />
              <rect x={cx - 5} y={TOP_Y - 15} width={COL_W + 10} height={14} fill={arch.stoneFill} rx={3} />
              <rect x={cx - 4} y={BASE_Y - 18} width={COL_W + 8} height={18} fill={arch.stoneFill} rx={2} />
            </g>
          ))}

          {/* Windows — 2 rows */}
          {Array.from({length: arch.winRows}, (_, row) => {
            const wy = TOP_Y + (row + 1) * winRowH - winH / 2;
            const wSpacing = arch.buildW / (arch.winsPerRow + 1);
            return Array.from({length: arch.winsPerRow}, (_, col) => {
              const wx = BX + (col + 1) * wSpacing - winW / 2;
              const lit = detailProg > 0.3;
              return (
                <g key={`w${row}_${col}`}>
                  <rect x={wx - 2} y={wy - 2} width={winW + 4} height={winH + 2}
                    fill={arch.stoneFill} rx={3} />
                  <rect x={wx} y={wy + winH * 0.3} width={winW} height={winH * 0.7}
                    fill={lit ? `rgba(255,235,160,${0.75 * detailProg})` : 'rgba(20,40,70,0.9)'}
                    rx={1}
                  />
                  <path
                    d={`M ${wx} ${wy + winH * 0.3} A ${winW / 2} ${winH * 0.32} 0 0 1 ${wx + winW} ${wy + winH * 0.3} Z`}
                    fill={lit ? `rgba(255,235,160,${0.75 * detailProg})` : 'rgba(20,40,70,0.9)'}
                  />
                </g>
              );
            });
          })}

          {/* Central door */}
          {(() => {
            const dw = 70; const dh = 110;
            const dx = 540 - dw / 2;
            const dy = BASE_Y - dh;
            return (
              <g>
                <rect x={dx - 3} y={dy - 15} width={dw + 6} height={dh + 15} fill={arch.stoneFill} rx={3} />
                <rect x={dx} y={dy + dw * 0.65} width={dw} height={dh - dw * 0.65} fill="rgba(15,25,40,0.95)" />
                <path d={`M ${dx} ${dy + dw * 0.65} A ${dw / 2} ${dw * 0.65} 0 0 1 ${dx + dw} ${dy + dw * 0.65} Z`}
                  fill="rgba(15,25,40,0.95)" />
              </g>
            );
          })()}
        </g>

        {/* Ground shadow */}
        <rect x={BX - 30} y={BASE_Y + 54} width={arch.buildW + 60} height={20}
          fill="rgba(0,0,0,0.25)" rx={10} />
      </svg>

      {/* Text overlay */}
      {title && (
        <div style={{
          position: 'absolute',
          top: BEAT_ZONE.top + 50,
          left: 80, right: 80,
          ...enterStyle(titleProg, 'rise', 44),
          textAlign: 'center',
          direction: 'rtl',
        }}>
          <div style={{...font, fontSize: 80, fontWeight: 900, color: rgba(th.p.accent), textShadow: th.shadow, lineHeight: 1.2}}>
            {title}
          </div>
          {subtitle && (
            <div style={{...font, fontSize: 46, fontWeight: 600, color: rgba(th.p.text, 0.85), marginTop: 10}}>
              {subtitle}
            </div>
          )}
        </div>
      )}
    </AbsoluteFill>
  );
};

// ── Shared: Question text block ───────────────────────────────────────────────

const QuestionText: React.FC<{
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
      bottom: 320,
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
          <rect x={0} y={BEAT_ZONE.top} width={1080} height={1920 - BEAT_ZONE.top} fill={`url(#${id}bg)`} />

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
          <rect x={0} y={BEAT_ZONE.top} width={1080} height={1920 - BEAT_ZONE.top} fill={`url(#${id}bg)`} />

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
        <rect x={0} y={BEAT_ZONE.top} width={1080} height={1920 - BEAT_ZONE.top} fill={`url(#${id}bg)`} />

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
