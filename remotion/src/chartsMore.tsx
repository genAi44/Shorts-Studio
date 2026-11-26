// Split from charts.tsx (re-exported there).
import React, {useMemo} from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {arc as d3Arc, pie as d3Pie} from 'd3-shape';
import type {ChartDataPoint, DrawChartInput} from './schema';
import {BarChart, DEFAULT_PALETTE, LineChart, formatChartNumber} from './charts';
import type {BaseChartProps} from './charts';

// 3. <PieDonutChart /> — Pure SVG + d3-shape (pie, arc) with RTL & Arabic numerals
export const PieDonutChart: React.FC<BaseChartProps & {donut?: boolean}> = ({
  data,
  style = {},
  donut = true,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const width = style.width ?? 900;
  const height = style.height ?? 640;
  const rtl = style.rtl ?? true;
  const arabicNumerals = style.arabicNumerals ?? false;
  const cx = width / 2;
  const cy = (height + (style.title ? 44 : 0)) / 2;
  const outerR = Math.min(width, height) * 0.28;
  const innerR = donut ? outerR * (style.donutInnerRadiusRatio ?? 0.56) : 0;

  const enterProg = spring({
    frame,
    fps,
    config: {damping: 15, stiffness: 120, mass: 0.9},
  });

  const arcs = useMemo(() => {
    const pGen = d3Pie<ChartDataPoint>()
      .value((d) => Math.max(0.01, d.value))
      .sort(null)
      .padAngle(0.025)
      .endAngle(Math.PI * 2 * Math.max(0.02, enterProg));
    return pGen(data);
  }, [data, enterProg]);

  const arcGen = useMemo(
    () => d3Arc<any>().innerRadius(innerR).outerRadius(outerR).cornerRadius(8),
    [innerR, outerR]
  );

  const total = useMemo(() => data.reduce((acc, d) => acc + d.value, 0) || 1, [data]);

  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      direction="ltr"
      data-chart={donut ? 'donut' : 'pie'}
      style={{overflow: 'visible'}}
    >
      <rect
        x={0}
        y={0}
        width={width}
        height={height}
        rx={28}
        fill="rgba(11, 18, 32, 0.88)"
        stroke="rgba(245, 197, 66, 0.35)"
        strokeWidth={2.5}
      />
      {style.title && (
        <text
          x={width / 2}
          y={54}
          textAnchor="middle"
          fill="#f8fafc"
          fontSize={34}
          fontWeight={800}
          direction={rtl ? 'rtl' : 'ltr'}
        >
          {style.title}
        </text>
      )}
      <g transform={`translate(${cx}, ${cy})`}>
        {arcs.map((a, idx) => {
          const col = a.data.color || DEFAULT_PALETTE[idx % DEFAULT_PALETTE.length];
          const pathD = arcGen(a) || '';
          const midAngle = (a.startAngle + a.endAngle) / 2 - Math.PI / 2;
          const r1 = outerR + 8;
          const r2 = outerR + 36;
          const x1 = Math.cos(midAngle) * r1;
          const y1 = Math.sin(midAngle) * r1;
          const x2 = Math.cos(midAngle) * r2;
          const y2 = Math.sin(midAngle) * r2;
          const isRight = Math.cos(midAngle) >= 0;
          const x3 = x2 + (isRight ? 28 : -28);
          const pct = Math.round((a.data.value / total) * 100);

          return (
            <g key={idx}>
              <path d={pathD} fill={col} stroke="#0b1220" strokeWidth={3} />
              {enterProg > 0.45 && (
                <g opacity={interpolate(enterProg, [0.45, 0.95], [0, 1], {extrapolateRight: 'clamp'})}>
                  <polyline
                    points={`${x1.toFixed(1)},${y1.toFixed(1)} ${x2.toFixed(1)},${y2.toFixed(1)} ${x3.toFixed(1)},${y2.toFixed(1)}`}
                    fill="none"
                    stroke={col}
                    strokeWidth={3}
                  />
                  <text
                    x={x3 + (isRight ? 10 : -10)}
                    y={y2 + 8}
                    textAnchor={isRight ? 'start' : 'end'}
                    fill="#f8fafc"
                    fontSize={22}
                    fontWeight={800}
                  >
                    {`${a.data.label} (${formatChartNumber(pct, arabicNumerals)}%)`}
                  </text>
                </g>
              )}
            </g>
          );
        })}
        {donut && (
          <text
            x={0}
            y={12}
            textAnchor="middle"
            fill="#f5c542"
            fontSize={36}
            fontWeight={900}
          >
            {formatChartNumber(100, arabicNumerals)}%
          </text>
        )}
      </g>
    </svg>
  );
};

// 4. <NumberCounter /> — Animated numeric callout driven by Remotion frames
export const NumberCounter: React.FC<{
  value: number;
  label: string;
  unit?: string;
  arabicNumerals?: boolean;
  rtl?: boolean;
  color?: string;
}> = ({value, label, unit = '', arabicNumerals = false, rtl = true, color = '#f5c542'}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const sp = spring({
    frame,
    fps,
    config: {damping: 16, stiffness: 110, mass: 0.9},
  });
  const cur = Math.round(value * Math.min(1, sp));
  const text = formatChartNumber(cur, arabicNumerals, unit);
  const fontSize = text.length > 10 ? 72 : text.length > 7 ? 88 : 108;

  return (
    <div
      dir={rtl ? 'rtl' : 'ltr'}
      data-chart="counter"
      style={{
        padding: '36px 52px',
        borderRadius: 32,
        background: 'rgba(11, 18, 32, 0.90)',
        border: `3px solid ${color}`,
        boxShadow: '0 18px 48px rgba(0,0,0,0.55)',
        display: 'inline-flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 14,
      }}
    >
      <div
        style={{
          fontSize,
          fontWeight: 900,
          color,
          lineHeight: 1.05,
          letterSpacing: -1,
          textShadow: `0 0 28px ${color}55`,
        }}
      >
        {text}
      </div>
      <div style={{fontSize: 34, fontWeight: 700, color: '#f8fafc', textAlign: 'center'}}>
        {label}
      </div>
    </div>
  );
};

// 5. <ProgressRing /> — Animated SVG radial progress gauge
export const ProgressRing: React.FC<{
  value: number;
  max?: number;
  label?: string;
  size?: number;
  arabicNumerals?: boolean;
  color?: string;
}> = ({value, max = 100, label = '', size = 340, arabicNumerals = false, color = '#f5c542'}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const sp = spring({frame, fps, config: {damping: 15, stiffness: 115}});
  const ratio = Math.max(0, Math.min(1, value / Math.max(1, max))) * sp;
  const strokeW = 24;
  const r = (size - strokeW * 2) / 2;
  const c = 2 * Math.PI * r;
  const dashOffset = c * (1 - ratio);
  const shownPct = Math.round(ratio * 100);

  return (
    <svg
      width={size}
      height={size + (label ? 64 : 0)}
      viewBox={`0 0 ${size} ${size + (label ? 64 : 0)}`}
      data-chart="progress_ring"
    >
      <g transform={`translate(${size / 2}, ${size / 2})`}>
        <circle r={r} fill="rgba(11, 18, 32, 0.85)" stroke="rgba(255,255,255,0.12)" strokeWidth={strokeW} />
        <circle
          r={r}
          fill="none"
          stroke={color}
          strokeWidth={strokeW}
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={dashOffset}
          transform="rotate(-90)"
        />
        <text x={0} y={14} textAnchor="middle" fill="#ffffff" fontSize={54} fontWeight={900}>
          {formatChartNumber(shownPct, arabicNumerals)}%
        </text>
      </g>
      {label && (
        <text
          x={size / 2}
          y={size + 42}
          textAnchor="middle"
          fill="#e2e8f0"
          fontSize={28}
          fontWeight={700}
        >
          {label}
        </text>
      )}
    </svg>
  );
};

// 6. <Timeline /> — Visual chronological timeline (pure SVG, RTL & Arabic numerals aware)
export const Timeline: React.FC<BaseChartProps> = ({data, style = {}}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const width = style.width ?? 920;
  const height = style.height ?? 560;
  const rtl = style.rtl ?? true;
  const arabicNumerals = style.arabicNumerals ?? false;
  const spineX = rtl ? width - 190 : 190;
  const topY = style.title ? 120 : 72;
  const botY = height - 64;
  const stepY = data.length > 1 ? (botY - topY) / (data.length - 1) : 0;
  const spineProg = spring({frame, fps, config: {damping: 16, stiffness: 110}});
  const accent = style.accentColor || '#f5c542';

  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      direction="ltr"
      data-chart="timeline"
      data-rtl={rtl ? 'true' : 'false'}
    >
      <rect
        x={0}
        y={0}
        width={width}
        height={height}
        rx={28}
        fill="rgba(11, 18, 32, 0.90)"
        stroke="rgba(245, 197, 66, 0.35)"
        strokeWidth={2.5}
      />
      {style.title && (
        <text x={width / 2} y={56} textAnchor="middle" fill="#f8fafc" fontSize={34} fontWeight={800}>
          {style.title}
        </text>
      )}
      <line
        x1={spineX}
        y1={topY}
        x2={spineX}
        y2={topY + (botY - topY) * spineProg}
        stroke={accent}
        strokeWidth={6}
        strokeLinecap="round"
      />
      {data.map((d, idx) => {
        const y = topY + idx * stepY;
        const sp = spring({
          frame: Math.max(0, frame - idx * 6),
          fps,
          config: {damping: 13, stiffness: 150},
        });
        const yearStr = formatChartNumber(d.year || d.value, arabicNumerals);
        return (
          <g key={idx} opacity={Math.min(1, sp * 1.4)}>
            <circle cx={spineX} cy={y} r={14 * sp} fill="#0b1220" stroke={accent} strokeWidth={6} />
            <text
              x={rtl ? spineX + 32 : spineX - 32}
              y={y + 9}
              textAnchor={rtl ? 'start' : 'end'}
              fill={accent}
              fontSize={28}
              fontWeight={900}
            >
              {yearStr}
            </text>
            <text
              x={rtl ? spineX - 36 : spineX + 36}
              y={y + 9}
              textAnchor={rtl ? 'end' : 'start'}
              fill="#f8fafc"
              fontSize={26}
              fontWeight={700}
              direction={rtl ? 'rtl' : 'ltr'}
            >
              {d.label}
            </text>
          </g>
        );
      })}
    </svg>
  );
};

// Unified dispatcher for `draw_chart` specs
export const ChartVisual: React.FC<{spec: DrawChartInput}> = ({spec}) => {
  const {type, data, style, durationInFrames} = spec;
  if (type === 'bar') return <BarChart data={data} style={style} durationInFrames={durationInFrames} />;
  if (type === 'line') return <LineChart data={data} style={style} durationInFrames={durationInFrames} />;
  if (type === 'pie') return <PieDonutChart data={data} style={style} donut={false} />;
  if (type === 'donut') return <PieDonutChart data={data} style={style} donut={true} />;
  if (type === 'counter') {
    const first = data[0] ?? {label: '', value: 0};
    return (
      <NumberCounter
        value={first.value}
        label={first.label}
        unit={style?.unit}
        arabicNumerals={style?.arabicNumerals}
        rtl={style?.rtl}
        color={style?.accentColor}
      />
    );
  }
  if (type === 'progress_ring') {
    const first = data[0] ?? {label: '', value: 75};
    return (
      <ProgressRing
        value={first.value}
        label={first.label}
        arabicNumerals={style?.arabicNumerals}
        color={style?.accentColor}
      />
    );
  }
  return <Timeline data={data} style={style} durationInFrames={durationInFrames} />;
};
