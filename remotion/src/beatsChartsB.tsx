// Split from beats.tsx (re-exported there).
import React, {useId} from 'react';
import {AbsoluteFill} from 'remotion';
import {enterStyle, useFont, useProgress, useSpring} from './hooks';
import {rgba, useTheme} from './theme';
import {BEAT_ZONE} from './layout';
import {Beat} from './types';
import {cueSecOf} from './beats';

// ------------------------------------------------------------------ مخطط خطي (سلسلة زمنية)

export const LineChartBeat: React.FC<{beat: Beat}> = ({beat}) => {
  const th = useTheme();
  const font = useFont();
  const uid = useId().replace(/:/g, '');

  const points: {label: string; value: number}[] = Array.isArray(beat.points) ? beat.points : [];
  if (points.length < 2) return null as any;

  const maxVal = Math.max(...points.map(p => p.value));
  const minVal = Math.min(...points.map(p => p.value));
  const range = maxVal - minVal || 1;

  // Canvas area inside the full 1080×1920 frame
  // plot box derived from the layout contract: value labels past the first/last point stay inside the safe margins
  const PAD_L = BEAT_ZONE.left + 60, PAD_R = BEAT_ZONE.right + 60, PAD_T = BEAT_ZONE.chart_title_top + 160, PAD_B = BEAT_ZONE.bottom - 80;
  const W = 1080 - PAD_L - PAD_R;  // 900
  const H = PAD_B - PAD_T;          // 720

  const nx = (i: number) => PAD_L + (i / (points.length - 1)) * W;
  const ny = (v: number) => PAD_B - ((v - minVal) / range) * H;

  const polyPts = points.map((p, i) => `${nx(i).toFixed(1)},${ny(p.value).toFixed(1)}`).join(' ');
  const areaPath = `M ${nx(0).toFixed(1)},${PAD_B} ` +
    points.map((p, i) => `L ${nx(i).toFixed(1)},${ny(p.value).toFixed(1)}`).join(' ') +
    ` L ${nx(points.length - 1).toFixed(1)},${PAD_B} Z`;

  const gridProg = useProgress(cueSecOf(beat, 'grid_enter', 0.4), 0.4);
  const lineProg = useProgress(cueSecOf(beat, 'line_draw', 0.65), 0.9);
  const dotsProg = useProgress(cueSecOf(beat, 'dots_pop', 0.9), 0.5);
  const titleProg = useSpring(0.1, 'smooth');

  const accentC = rgba(th.p.accent);
  const accent2C = rgba(th.p.accent2);
  const textC = rgba(th.p.text);
  const lineLen = lineProg;  // 0→1 drives stroke-dashoffset

  // Approximate total polyline length for dasharray
  const totalLen = points.reduce((sum, p, i) => {
    if (i === 0) return 0;
    const dx = nx(i) - nx(i - 1);
    const dy = ny(p.value) - ny(points[i - 1].value);
    return sum + Math.sqrt(dx * dx + dy * dy);
  }, 0) || 1000;

  return (
    <AbsoluteFill>
      {/* Title */}
      {beat.title && (
        <div style={{
          position: 'absolute', left: BEAT_ZONE.left, right: BEAT_ZONE.right, top: BEAT_ZONE.chart_title_top,
          textAlign: 'center', ...font, fontSize: 58, fontWeight: 900,
          color: textC, textShadow: th.shadow, direction: 'rtl',
          ...enterStyle(titleProg, 'rise', 40),
        }}>{beat.title}</div>
      )}

      <svg width={1080} height={1920} style={{position: 'absolute', inset: 0}}>
        <defs>
          <linearGradient id={`${uid}ag`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={accentC} stopOpacity="0.35" />
            <stop offset="100%" stopColor={accentC} stopOpacity="0.0" />
          </linearGradient>
        </defs>

        {/* Horizontal grid lines */}
        {[0, 0.25, 0.5, 0.75, 1].map((frac, gi) => {
          const gy = PAD_B - frac * H;
          const gVal = minVal + frac * range;
          const op = gridProg * 0.35;
          return op > 0.01 ? (
            <g key={gi} opacity={op}>
              <line x1={PAD_L} y1={gy} x2={PAD_L + W} y2={gy} stroke={textC} strokeWidth={1.5} />
              <text x={PAD_L - 10} y={gy + 6} fontSize={28} fill={textC} textAnchor="end" fontFamily={th.family}>
                {gVal % 1 === 0 ? gVal.toFixed(0) : gVal.toFixed(1)}
              </text>
            </g>
          ) : null;
        })}

        {/* Area fill */}
        {lineProg > 0.01 && (
          <path d={areaPath} fill={`url(#${uid}ag)`} opacity={lineProg * 0.8} />
        )}

        {/* Animated line */}
        <polyline
          points={polyPts}
          fill="none"
          stroke={accentC}
          strokeWidth={6}
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeDasharray={`${totalLen} ${totalLen}`}
          strokeDashoffset={totalLen * (1 - lineLen)}
        />

        {/* Data point dots + labels */}
        {points.map((p, i) => {
          const px = nx(i), py = ny(p.value);
          const delay = 0.1 + i * 0.08;
          const dp = Math.max(0, Math.min(1, (dotsProg - delay + 0.1) * 5));
          if (dp < 0.01) return null;
          const above = py > PAD_T + 80;
          return (
            <g key={i} opacity={dp}>
              <circle cx={px} cy={py} r={12 * dp} fill={accentC} />
              <circle cx={px} cy={py} r={6} fill="rgba(255,255,255,0.9)" />
              {/* X-axis label */}
              <text x={px} y={PAD_B + 40} fontSize={30} fill={textC} textAnchor="middle" fontFamily={th.family}>{p.label}</text>
              {/* Value label above/below dot */}
              <text x={i === 0 ? px + 22 : px} y={above ? py - 20 : py + 48} fontSize={32} fontWeight={700} fill={accentC} textAnchor={i === 0 ? 'start' : 'middle'} fontFamily={th.family}>
                {p.value % 1 === 0 ? p.value.toFixed(0) : p.value.toFixed(1)}
                {beat.y_label ? ` ${beat.y_label}` : ''}
              </text>
            </g>
          );
        })}

        {/* Y-axis line */}
        <line x1={PAD_L} y1={PAD_T - 20} x2={PAD_L} y2={PAD_B + 10} stroke={textC} strokeWidth={2} opacity={gridProg * 0.5} />
        {/* X-axis line */}
        <line x1={PAD_L - 10} y1={PAD_B} x2={PAD_L + W} y2={PAD_B} stroke={textC} strokeWidth={2} opacity={gridProg * 0.5} />
      </svg>
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ مخطط دائري (توزيع نسبي)

export const PieChartBeat: React.FC<{beat: Beat}> = ({beat}) => {
  const th = useTheme();
  const font = useFont();

  const items: {label: string; value: number}[] = Array.isArray(beat.items) ? beat.items : [];
  if (items.length < 2) return null as any;

  const total = items.reduce((s, it) => s + it.value, 0) || 100;

  // 5 accent colors cycling: accent, accent2, hl0..hl2
  const COLORS_FN = (i: number) => {
    const palette = [th.p.accent, th.p.accent2, ...(th.p.hl || [])];
    return rgba(palette[i % palette.length]);
  };

  const CX = 540, CY = 900, R = 300, HOLE = 160;

  const segProg = useProgress(cueSecOf(beat, 'seg_enter', 0.3), 1.0);
  const labelProg = useProgress(cueSecOf(beat, 'labels_enter', 0.8), 0.6);
  const titleProg = useSpring(0.05, 'smooth');

  // Build arc paths
  let angle = -Math.PI / 2;  // start at top
  const segments = items.map((it, i) => {
    const frac = it.value / total;
    const startA = angle;
    const endA = angle + 2 * Math.PI * frac;
    angle = endA;
    const midA = (startA + endA) / 2;
    // arc path
    const x1 = CX + R * Math.cos(startA), y1 = CY + R * Math.sin(startA);
    const x2 = CX + R * Math.cos(endA), y2 = CY + R * Math.sin(endA);
    const hx1 = CX + HOLE * Math.cos(startA), hy1 = CY + HOLE * Math.sin(startA);
    const hx2 = CX + HOLE * Math.cos(endA), hy2 = CY + HOLE * Math.sin(endA);
    const large = frac > 0.5 ? 1 : 0;
    const path = `M ${hx1.toFixed(1)},${hy1.toFixed(1)} L ${x1.toFixed(1)},${y1.toFixed(1)} A ${R},${R} 0 ${large},1 ${x2.toFixed(1)},${y2.toFixed(1)} L ${hx2.toFixed(1)},${hy2.toFixed(1)} A ${HOLE},${HOLE} 0 ${large},0 ${hx1.toFixed(1)},${hy1.toFixed(1)} Z`;
    // label position outside pie
    const LR = R + 90;
    const lx = CX + LR * Math.cos(midA), ly = CY + LR * Math.sin(midA);
    return {path, color: COLORS_FN(i), lx, ly, midA, frac, label: it.label, value: it.value};
  });

  const textC = rgba(th.p.text);

  return (
    <AbsoluteFill>
      {/* Title */}
      {beat.title && (
        <div style={{
          position: 'absolute', left: BEAT_ZONE.left, right: BEAT_ZONE.right, top: BEAT_ZONE.chart_title_top,
          textAlign: 'center', ...font, fontSize: 58, fontWeight: 900,
          color: textC, textShadow: th.shadow, direction: 'rtl',
          ...enterStyle(titleProg, 'rise', 40),
        }}>{beat.title}</div>
      )}

      <svg width={1080} height={1920} style={{position: 'absolute', inset: 0}}>
        {segments.map((seg, i) => {
          const delay = i * (0.9 / items.length);
          const sp = Math.max(0, Math.min(1, (segProg - delay) * (items.length + 1)));
          const lp = Math.max(0, Math.min(1, (labelProg - i * 0.1) * 4));
          if (sp < 0.01) return null;

          // Animate segment scale from center
          const scale = 0.3 + 0.7 * sp;
          return (
            <g key={i} transform={`translate(${CX * (1 - scale)},${CY * (1 - scale)}) scale(${scale})`} opacity={sp}>
              <path d={seg.path} fill={seg.color} />
            </g>
          );
        })}

        {/* Labels with leader lines */}
        {segments.map((seg, i) => {
          const lp = Math.max(0, Math.min(1, (labelProg - i * 0.08) * 5));
          if (lp < 0.01) return null;
          // line from pie edge to label
          const edgeX = CX + (R + 20) * Math.cos(seg.midA);
          const edgeY = CY + (R + 20) * Math.sin(seg.midA);
          const anchor = seg.lx > CX ? 'start' : 'end';
          return (
            <g key={i} opacity={lp}>
              <line x1={edgeX.toFixed(1)} y1={edgeY.toFixed(1)} x2={seg.lx.toFixed(1)} y2={seg.ly.toFixed(1)}
                stroke={seg.color} strokeWidth={3} />
              <text x={(seg.lx + (seg.lx > CX ? 16 : -16)).toFixed(1)} y={(seg.ly + 6).toFixed(1)}
                fontSize={30} fontWeight={700} fill={seg.color} textAnchor={anchor} fontFamily={th.family}>
                {seg.label}
              </text>
              <text x={(seg.lx + (seg.lx > CX ? 16 : -16)).toFixed(1)} y={(seg.ly + 44).toFixed(1)}
                fontSize={26} fill={textC} textAnchor={anchor} fontFamily={th.family}>
                {seg.value.toFixed(1)}%
              </text>
            </g>
          );
        })}

        {/* Center donut label (biggest segment) */}
        {segProg > 0.6 && (() => {
          const biggest = items.reduce((m, it) => it.value > m.value ? it : m, items[0]);
          return (
            <g opacity={Math.min(1, (segProg - 0.6) * 3)}>
              <text x={CX} y={CY - 20} fontSize={34} fill={textC} textAnchor="middle" fontFamily={th.family}>{biggest.label}</text>
              <text x={CX} y={CY + 32} fontSize={52} fontWeight={900} fill={rgba(th.p.accent)} textAnchor="middle" fontFamily={th.family}>
                {biggest.value.toFixed(0)}%
              </text>
            </g>
          );
        })()}
      </svg>
    </AbsoluteFill>
  );
};
