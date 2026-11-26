// Split from generativeCanvas.tsx (re-exported there).
import React from 'react';
import {AbsoluteFill, spring} from 'remotion';

// ------------------------------------------------------------------ Atmospheric Environment & Custom SVG Construction Layers
export const CanvasMoodBackground: React.FC<{
  mode?: boolean | string;
  environment?: string;
  accent: string;
  secondaryAccent: string;
  frame: number;
  fps: number;
}> = ({ mode, environment, accent, secondaryAccent, frame, fps }) => {
  const t = frame / Math.max(1, fps);
  const env = environment || (typeof mode === 'string' ? mode : 'topographic_contour');

  return (
    <AbsoluteFill style={{ pointerEvents: 'none', overflow: 'hidden' }}>
      {/* Ambient Radial Illumination & Rich Atmospheric Glow (Eliminates Dark Void) */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: `radial-gradient(ellipse 85% 60% at 50% 35%, ${accent}38 0%, ${secondaryAccent}22 48%, transparent 88%), radial-gradient(circle at 20% 78%, ${secondaryAccent}2e 0%, transparent 55%), radial-gradient(circle at 82% 22%, ${accent}2b 0%, transparent 50%)`,
        }}
      />

      <svg width={1080} height={1920} viewBox="0 0 1080 1920" style={{ position: 'absolute', inset: 0 }}>
        <defs>
          <linearGradient id="env_beam" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor={accent} stopOpacity="0.24" />
            <stop offset="50%" stopColor={secondaryAccent} stopOpacity="0.12" />
            <stop offset="100%" stopColor={accent} stopOpacity="0.02" />
          </linearGradient>
        </defs>

        {/* Topographic Contour / Wave Field */}
        {(env === 'topographic_contour' || env === 'kinetic_wave_field' || env === 'chronicle_strata_layers') &&
          Array.from({ length: 11 }).map((_, i) => {
            const yBase = 180 + i * 155;
            const shift = Math.sin(t * 1.4 + i * 0.7) * 28;
            const d = `M -40 ${yBase} Q 270 ${yBase - 65 + shift}, 540 ${yBase + shift * 0.5} T 1120 ${yBase - shift}`;
            return (
              <path
                key={i}
                d={d}
                fill="none"
                stroke={i % 2 === 0 ? accent : secondaryAccent}
                strokeWidth={i % 3 === 0 ? 2.2 : 1.2}
                strokeOpacity={0.18 + (i % 4) * 0.04}
              />
            );
          })}

        {/* Isometric City / Perspective Horizon Grid */}
        {(env === 'isometric_city_grid' || env === 'horizon_perspective_plane' || env === 'architectural_blueprint' || mode === 'lines') && (
          <g opacity={0.22}>
            {Array.from({ length: 14 }).map((_, i) => {
              const x = i * 84;
              return <line key={`v_${i}`} x1={x} y1={0} x2={x} y2={1920} stroke={accent} strokeWidth={1} strokeDasharray="8 12" />;
            })}
            {Array.from({ length: 22 }).map((_, i) => {
              const y = ((i * 90 + t * 24) % 1920);
              return <line key={`h_${i}`} x1={0} y1={y} x2={1080} y2={y} stroke={secondaryAccent} strokeWidth={1.2} opacity={0.65} />;
            })}
          </g>
        )}

        {/* Orbital Meridian / Radar / Hexagonal Matrix */}
        {(env === 'orbital_meridian_sphere' || env === 'hexagonal_data_matrix' || env === 'celestial_constellation' || mode === 'radar') && (
          <g transform={`translate(540, 880) rotate(${(t * 9).toFixed(2)})`} opacity={0.24}>
            <circle cx={0} cy={0} r={220} stroke={accent} strokeWidth={1.6} fill="none" />
            <circle cx={0} cy={0} r={380} stroke={secondaryAccent} strokeWidth={1.6} fill="none" strokeDasharray="10 8" />
            <circle cx={0} cy={0} r={540} stroke={accent} strokeWidth={1.4} fill="none" />
            <ellipse cx={0} cy={0} rx={520} ry={210} stroke={secondaryAccent} strokeWidth={1.4} fill="none" />
            <ellipse cx={0} cy={0} rx={210} ry={520} stroke={accent} strokeWidth={1.4} fill="none" />
            <line x1={-540} y1={0} x2={540} y2={0} stroke={accent} strokeWidth={1} strokeDasharray="5 7" />
            <line x1={0} y1={-680} x2={0} y2={680} stroke={secondaryAccent} strokeWidth={1} strokeDasharray="5 7" />
          </g>
        )}

        {/* Radial Light Cathedral Beams */}
        <polygon points="0,0 420,0 1080,1250 1080,1650" fill="url(#env_beam)" opacity={0.45} />
        <polygon points="1080,0 680,0 0,1320 0,1720" fill="url(#env_beam)" opacity={0.32} />
      </svg>
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ Custom SVG Vector Illustrations (Section C: SVG Construction)
export const CustomSvgIllustrationLayer: React.FC<{
  layers?: any[];
  frame: number;
  fps: number;
  accent: string;
  secondaryAccent: string;
}> = ({ layers, frame, fps, accent, secondaryAccent }) => {
  if (!layers || !layers.length) return null;
  const t = frame / Math.max(1, fps);
  const intro = spring({ fps, frame, config: { damping: 16, stiffness: 95 } });

  return (
    <svg
      width={1080}
      height={1920}
      viewBox="0 0 1080 1920"
      style={{ position: 'absolute', inset: 0, pointerEvents: 'none', zIndex: 4 }}
    >
      {layers.map((layer, idx) => {
        const kind = layer.kind || 'exploded_isometric_core';
        const pCol = layer.primary || accent;
        const sCol = layer.secondary || secondaryAccent;
        const hCol = layer.highlight || '#fde047';
        const cx = layer.x ?? 540;
        const cy = layer.y ?? 880;

        if (kind === 'metropolis_skyline') {
          const buildings = [
            { x: 150, w: 85, h: 310 },
            { x: 245, w: 95, h: 440 },
            { x: 350, w: 110, h: 520 },
            { x: 470, w: 140, h: 640 },
            { x: 620, w: 115, h: 490 },
            { x: 745, w: 95, h: 390 },
            { x: 850, w: 85, h: 290 },
          ];
          const baseLine = cy + 280;
          return (
            <g key={idx} opacity={0.48 * intro}>
              <circle cx={cx} cy={cy - 40} r={340} fill="none" stroke={pCol} strokeWidth={2} strokeDasharray="10 8" />
              {buildings.map((b, bi) => {
                const bh = b.h * Math.min(1, intro * (0.85 + bi * 0.04));
                const by = baseLine - bh;
                return (
                  <g key={bi}>
                    <rect
                      x={b.x}
                      y={by}
                      width={b.w}
                      height={bh}
                      rx={6}
                      fill={`${pCol}22`}
                      stroke={bi === 3 ? hCol : pCol}
                      strokeWidth={bi === 3 ? 3 : 2}
                    />
                    {Array.from({ length: 6 }).map((_, wi) => (
                      <rect
                        key={wi}
                        x={b.x + 16}
                        y={by + 24 + wi * 42}
                        width={b.w - 32}
                        height={14}
                        rx={3}
                        fill={bi === 3 ? hCol : sCol}
                        opacity={0.35 + 0.25 * Math.sin(t * 3 + bi + wi)}
                      />
                    ))}
                  </g>
                );
              })}
              <line x1={90} y1={baseLine} x2={990} y2={baseLine} stroke={hCol} strokeWidth={4} />
            </g>
          );
        }

        if (kind === 'orbital_cartography') {
          return (
            <g key={idx} transform={`translate(${cx}, ${cy}) scale(${(0.85 + 0.15 * intro).toFixed(3)})`} opacity={0.55}>
              <circle cx={0} cy={0} r={310} fill={`${pCol}18`} stroke={pCol} strokeWidth={3} />
              <ellipse cx={0} cy={0} rx={310} ry={130} fill="none" stroke={sCol} strokeWidth={2} strokeDasharray="8 6" />
              <ellipse cx={0} cy={0} rx={140} ry={310} fill="none" stroke={sCol} strokeWidth={2} strokeDasharray="8 6" />
              <g transform={`rotate(${(t * 22).toFixed(1)})`}>
                <circle cx={0} cy={0} r={390} fill="none" stroke={hCol} strokeWidth={2} strokeDasharray="16 18" />
                <circle cx={390} cy={0} r={12} fill={hCol} />
                <circle cx={-390} cy={0} r={12} fill={pCol} />
              </g>
            </g>
          );
        }

        if (kind === 'equilibrium_duel_stage') {
          const tilt = Math.sin(t * 2.2) * 7;
          return (
            <g key={idx} transform={`translate(${cx}, ${cy})`} opacity={0.52 * intro}>
              <polygon points="-70,220 70,220 0,80" fill={`${pCol}35`} stroke={hCol} strokeWidth={3} />
              <g transform={`rotate(${tilt.toFixed(2)})`}>
                <line x1={-360} y1={0} x2={360} y2={0} stroke={hCol} strokeWidth={6} strokeLinecap="round" />
                <circle cx={-320} cy={0} r={78} fill={`${pCol}28`} stroke={pCol} strokeWidth={3} />
                <circle cx={320} cy={0} r={78} fill={`${sCol}28`} stroke={sCol} strokeWidth={3} />
              </g>
            </g>
          );
        }

        // Default: Exploded Isometric Core / Chronicle Conduit
        return (
          <g key={idx} transform={`translate(${cx}, ${cy})`} opacity={0.5 * intro}>
            <g transform={`rotate(${(t * 15).toFixed(1)})`}>
              <polygon
                points="0,-290 250,-145 250,145 0,290 -250,145 -250,-145"
                fill={`${pCol}16`}
                stroke={pCol}
                strokeWidth={2.5}
              />
            </g>
            <g transform={`rotate(${(-t * 12).toFixed(1)})`}>
              <polygon
                points="0,-210 182,-105 182,105 0,210 -182,105 -182,-105"
                fill={`${sCol}18`}
                stroke={sCol}
                strokeWidth={2}
                strokeDasharray="10 6"
              />
            </g>
          </g>
        );
      })}
    </svg>
  );
};
