import React, {useMemo} from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {evolvePath} from '@remotion/paths';
import {scaleBand, scaleLinear} from 'd3-scale';
import {arc as d3Arc, area as d3Area, curveMonotoneX, line as d3Line, pie as d3Pie} from 'd3-shape';
import {max as d3Max} from 'd3-array';
import type {ChartDataPoint, ChartStyle, DrawChartInput} from './schema';
export {ChartVisual, NumberCounter, PieDonutChart, ProgressRing, Timeline} from './chartsMore';

const ARABIC_DIGITS = ['٠', '١', '٢', '٣', '٤', '٥', '٦', '٧', '٨', '٩'];

export const formatChartNumber = (
  val: number | string,
  arabicNumerals = false,
  unit = ''
): string => {
  const formatted =
    typeof val === 'number'
      ? Number.isInteger(val)
        ? val.toLocaleString('en-US')
        : val.toFixed(1)
      : String(val);
  const out = arabicNumerals
    ? formatted.replace(/\d/g, (d) => ARABIC_DIGITS[Number(d)]).replace(/,/g, '٬')
    : formatted;
  return unit ? `${out} ${unit}` : out;
};

export const DEFAULT_PALETTE = [
  '#f5c542',
  '#38bdf8',
  '#34d399',
  '#f87171',
  '#a78bfa',
  '#fb923c',
  '#2dd4bf',
  '#e879f9',
];

export interface BaseChartProps {
  data: ChartDataPoint[];
  style?: Partial<ChartStyle>;
  durationInFrames?: number;
}

// 1. <BarChart /> — Pure SVG + d3-scale (scaleBand, scaleLinear) with RTL & Arabic numerals support
export const BarChart: React.FC<BaseChartProps> = ({
  data,
  style = {},
  durationInFrames = 90,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const width = style.width ?? 900;
  const height = style.height ?? 620;
  const rtl = style.rtl ?? true;
  const arabicNumerals = style.arabicNumerals ?? false;
  const unit = style.unit ?? '';
  const pad = {top: style.title ? 96 : 44, right: 48, bottom: 88, left: 48};
  const plotW = width - pad.left - pad.right;
  const plotH = height - pad.top - pad.bottom;

  const {xScale, yScale, maxVal} = useMemo(() => {
    const labels = data.map((d, i) => d.label || `#${i + 1}`);
    const domainLabels = rtl ? [...labels].reverse() : labels;
    const x = scaleBand<string>()
      .domain(domainLabels)
      .range([0, plotW])
      .padding(0.28);
    const mv = Math.max(1, d3Max(data, (d) => d.value) ?? 100);
    const y = scaleLinear().domain([0, mv * 1.12]).range([plotH, 0]);
    return {xScale: x, yScale: y, maxVal: mv};
  }, [data, plotW, plotH, rtl]);

  const gridTicks = [0, 0.25, 0.5, 0.75, 1];

  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      direction="ltr"
      data-chart="bar"
      data-rtl={rtl ? 'true' : 'false'}
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
      <g transform={`translate(${pad.left}, ${pad.top})`}>
        {gridTicks.map((t, idx) => {
          const gy = yScale(maxVal * t);
          return (
            <line
              key={idx}
              x1={0}
              y1={gy}
              x2={plotW}
              y2={gy}
              stroke="rgba(255,255,255,0.09)"
              strokeDasharray="6 6"
              strokeWidth={1.5}
            />
          );
        })}
        {data.map((d, idx) => {
          const key = d.label || `#${idx + 1}`;
          const bx = xScale(key) ?? 0;
          const bw = xScale.bandwidth();
          const sp = spring({
            frame: Math.max(0, frame - idx * 4),
            fps,
            config: {damping: 14, stiffness: 140, mass: 0.8},
          });
          const targetY = yScale(d.value);
          const targetH = Math.max(4, plotH - targetY);
          const curH = targetH * sp;
          const curY = plotH - curH;
          const col = d.color || style.accentColor || DEFAULT_PALETTE[idx % DEFAULT_PALETTE.length];
          const shownVal = Math.round(d.value * sp);

          return (
            <g key={key}>
              <rect
                x={bx}
                y={curY}
                width={bw}
                height={curH}
                rx={Math.min(14, bw / 4)}
                fill={col}
              />
              <text
                x={bx + bw / 2}
                y={curY - 14}
                textAnchor="middle"
                fill="#ffffff"
                fontSize={24}
                fontWeight={800}
              >
                {formatChartNumber(shownVal, arabicNumerals, unit)}
              </text>
              <text
                x={bx + bw / 2}
                y={plotH + 42}
                textAnchor="middle"
                fill="#cbd5e1"
                fontSize={24}
                fontWeight={700}
                direction={rtl ? 'rtl' : 'ltr'}
              >
                {d.label}
              </text>
            </g>
          );
        })}
      </g>
    </svg>
  );
};

// 2. <LineChart /> — Pure SVG + d3-scale & d3-shape (line, area, curveMonotoneX) + @remotion/paths evolvePath
export const LineChart: React.FC<BaseChartProps> = ({
  data,
  style = {},
  durationInFrames = 90,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const width = style.width ?? 900;
  const height = style.height ?? 600;
  const rtl = style.rtl ?? true;
  const arabicNumerals = style.arabicNumerals ?? false;
  const unit = style.unit ?? '';
  const pad = {top: style.title ? 96 : 48, right: 64, bottom: 84, left: 64};
  const plotW = width - pad.left - pad.right;
  const plotH = height - pad.top - pad.bottom;

  const {points, linePath, areaPath} = useMemo(() => {
    const n = Math.max(1, data.length);
    const mv = Math.max(1, d3Max(data, (d) => d.value) ?? 100);
    const x = scaleLinear()
      .domain([0, Math.max(1, n - 1)])
      .range(rtl ? [plotW, 0] : [0, plotW]);
    const y = scaleLinear().domain([0, mv * 1.15]).range([plotH, 0]);

    const pts = data.map((d, i) => ({
      x: x(i),
      y: y(d.value),
      d,
    }));
    const sortedForCurve = [...pts].sort((a, b) => a.x - b.x);
    const lGen = d3Line<{x: number; y: number}>()
      .x((p) => p.x)
      .y((p) => p.y)
      .curve(curveMonotoneX);
    const aGen = d3Area<{x: number; y: number}>()
      .x((p) => p.x)
      .y0(plotH)
      .y1((p) => p.y)
      .curve(curveMonotoneX);

    return {
      points: pts,
      linePath: lGen(sortedForCurve) || '',
      areaPath: aGen(sortedForCurve) || '',
    };
  }, [data, plotW, plotH, rtl]);

  const drawProg = interpolate(frame, [0, Math.min(durationInFrames * 0.65, fps * 1.4)], [0.01, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  let evo: {strokeDasharray?: string; strokeDashoffset?: number} = {};
  if (linePath && drawProg < 0.999) {
    try {
      evo = evolvePath(drawProg, linePath);
    } catch {
      evo = {};
    }
  }
  const strokeColor = style.accentColor || '#f5c542';

  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      direction="ltr"
      data-chart="line"
      data-rtl={rtl ? 'true' : 'false'}
      style={{overflow: 'visible'}}
    >
      <defs>
        <linearGradient id="lineAreaGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={strokeColor} stopOpacity={0.42} />
          <stop offset="100%" stopColor={strokeColor} stopOpacity={0.02} />
        </linearGradient>
      </defs>
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
      <g transform={`translate(${pad.left}, ${pad.top})`}>
        {areaPath && <path d={areaPath} fill="url(#lineAreaGrad)" opacity={drawProg} />}
        {linePath && (
          <path
            d={linePath}
            fill="none"
            stroke={strokeColor}
            strokeWidth={6}
            strokeLinecap="round"
            strokeDasharray={evo.strokeDasharray}
            strokeDashoffset={evo.strokeDashoffset}
          />
        )}
        {points.map((pt, idx) => {
          const sp = spring({
            frame: Math.max(0, frame - idx * 4),
            fps,
            config: {damping: 12, stiffness: 170},
          });
          return (
            <g key={idx} opacity={Math.min(1, sp * 1.4)}>
              <circle
                cx={pt.x}
                cy={pt.y}
                r={10 * sp}
                fill="#0b1220"
                stroke={strokeColor}
                strokeWidth={5}
              />
              <text
                x={pt.x}
                y={pt.y - 20}
                textAnchor="middle"
                fill="#ffffff"
                fontSize={22}
                fontWeight={800}
              >
                {formatChartNumber(pt.d.value, arabicNumerals, unit)}
              </text>
              <text
                x={pt.x}
                y={plotH + 42}
                textAnchor="middle"
                fill="#cbd5e1"
                fontSize={22}
                fontWeight={700}
                direction={rtl ? 'rtl' : 'ltr'}
              >
                {pt.d.label}
              </text>
            </g>
          );
        })}
      </g>
    </svg>
  );
};

