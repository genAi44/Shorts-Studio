// Split from generativeCanvas.tsx (re-exported there).
import React from 'react';
import {evolvePath} from '@remotion/paths';
import {Icon} from './icons';
import {Emoji} from './emoji';
import {Flag} from './flag';
import type {BadgePrimitive, CounterPrimitive, GaugePrimitive, GenCtx, PathPrimitive, ShapePrimitive} from './generativeCanvas';

export const renderShape = (ctx: GenCtx): React.ReactNode => {
  const {el, frame, fps, accent, settled, x, y, progress, opacity, transform, loopStyle, wrap} = ctx;
  const s = el as ShapePrimitive;
  const w = s.w ?? 120;
  const h = s.h ?? w;
  const fill = s.fill || `${accent}22`;
  const stroke = s.stroke || accent;
  const strokeW = s.strokeWidth ?? 3;
  const radius = s.r ?? (s.shape === 'circle' ? '50%' : s.shape === 'pill' ? 999 : 20);

  if (s.shape === 'triangle') {
    return wrap(
      <svg width={w} height={h} viewBox="0 0 100 100" style={{ overflow: 'visible' }}>
        <polygon
          points="50,4 96,96 4,96"
          fill={fill}
          stroke={stroke}
          strokeWidth={strokeW}
          strokeLinejoin="round"
        />
      </svg>
    );
  }

  if (s.shape === 'shield') {
    return wrap(
      <svg width={w} height={h} viewBox="0 0 100 120" style={{ overflow: 'visible' }}>
        <path
          d="M50 8 L88 24 C88 72 50 112 50 112 C50 112 12 72 12 24 Z"
          fill={fill}
          stroke={stroke}
          strokeWidth={strokeW}
          strokeLinejoin="round"
        />
      </svg>
    );
  }

  if (s.shape === 'star') {
    return wrap(
      <svg width={w} height={h} viewBox="0 0 24 24" style={{ overflow: 'visible' }}>
        <polygon
          points="12,2 15,8.5 22,9.3 17,14 18.5,21 12,17.3 5.5,21 7,14 2,9.3 9,8.5"
          fill={fill}
          stroke={stroke}
          strokeWidth={strokeW * 0.5}
          strokeLinejoin="round"
        />
      </svg>
    );
  }

  if (s.shape === 'ring') {
    return wrap(
      <div
        style={{
          width: w,
          height: w,
          borderRadius: '50%',
          border: `${strokeW}px solid ${stroke}`,
          background: fill === `${accent}22` ? 'transparent' : fill,
          boxShadow: `0 0 24px ${stroke}33`,
        }}
      />
    );
  }

  return wrap(
    <div
      style={{
        width: w,
        height: h,
        borderRadius: radius,
        background: fill,
        border: strokeW > 0 ? `${strokeW}px solid ${stroke}` : undefined,
        boxShadow: `0 16px 36px rgba(0,0,0,0.4), 0 0 24px ${stroke}22`,
      }}
    />
  );
};

export const renderPath = (ctx: GenCtx): React.ReactNode => {
  const {el, frame, fps, accent, settled, x, y, progress, opacity, transform, loopStyle, wrap} = ctx;
  const p = el as PathPrimitive;
  let pathD = p.d || '';
  const color = p.stroke || accent;
  const strokeW = p.strokeWidth ?? 4;

  if (!pathD) {
    const from = p.from || [180, 1100];
    const to = p.to || [900, 600];
    const ctrl = p.control || [(from[0] + to[0]) / 2, Math.min(from[1], to[1]) - 160];
    if (p.curve === 'mountain') {
      pathD = `M ${from[0]} ${from[1]} L ${(from[0] + to[0]) / 2} ${Math.min(from[1], to[1]) - 240} L ${to[0]} ${to[1]}`;
    } else if (p.curve === 'zigzag') {
      const midX = (from[0] + to[0]) / 2;
      pathD = `M ${from[0]} ${from[1]} L ${midX - 40} ${(from[1] + to[1]) / 2} L ${midX + 40} ${(from[1] + to[1]) / 2 - 20} L ${to[0]} ${to[1]}`;
    } else {
      pathD = `M ${from[0]} ${from[1]} Q ${ctrl[0]} ${ctrl[1]} ${to[0]} ${to[1]}`;
    }
  }

  // Animated stroke evolve
  let evolved = { strokeDasharray: 'none', strokeDashoffset: 0 };
  try {
    evolved = evolvePath(progress, pathD);
  } catch {
    // Fallback if path string isn't standard SVG bezier
    evolved = {
      strokeDasharray: '1000',
      strokeDashoffset: (1 - progress) * 1000,
    };
  }

  return (
    <svg
      width={1080}
      height={1920}
      style={{
        position: 'absolute',
        inset: 0,
        pointerEvents: 'none',
        zIndex: el.zIndex ?? 8,
        overflow: 'visible',
      }}
    >
      <path
        d={pathD}
        fill="none"
        stroke={color}
        strokeWidth={strokeW}
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeDasharray={p.strokeDasharray || evolved.strokeDasharray}
        strokeDashoffset={evolved.strokeDashoffset}
        style={{
          filter: `drop-shadow(0 0 12px ${color}66)`,
        }}
      />
    </svg>
  );
};

export const renderBadge = (ctx: GenCtx): React.ReactNode => {
  const {el, frame, fps, accent, settled, x, y, progress, opacity, transform, loopStyle, wrap} = ctx;
  const b = el as BadgePrimitive;
  const pad = b.size === 'lg' ? '16px 32px' : b.size === 'sm' ? '8px 18px' : '12px 24px';
  const fSize = b.size === 'lg' ? 30 : b.size === 'sm' ? 22 : 26;
  const bg = b.bg || 'rgba(15, 23, 42, 0.92)';
  const textCol = b.textColor || '#ffffff';
  const borderCol = b.borderColor || (b as any).color || `${accent}88`;

  return wrap(
    <div
      dir="rtl"
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 14,
        padding: pad,
        background: bg,
        borderRadius: 999,
        border: `2px solid ${borderCol}`,
        boxShadow: `0 12px 30px rgba(0,0,0,0.55), 0 0 20px ${borderCol}33`,
        backdropFilter: 'blur(16px)',
        color: textCol,
        maxWidth: 880,
      }}
    >
      {b.flag && <Flag code={b.flag} size={fSize + 6} shape="round" />}
      {b.emoji && <Emoji char={b.emoji} size={fSize + 4} animation="none" />}
      {b.icon && <Icon name={b.icon} size={fSize + 4} color={accent} animation="none" />}
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center' }}>
        <span style={{ fontSize: fSize, fontWeight: 700, lineHeight: 1.3 }}>{b.text}</span>
        {b.sub && <span style={{ fontSize: fSize * 0.75, opacity: 0.75 }}>{b.sub}</span>}
      </div>
    </div>
  );
};

export const renderCounter = (ctx: GenCtx): React.ReactNode => {
  const {el, frame, fps, accent, settled, x, y, progress, opacity, transform, loopStyle, wrap} = ctx;
  const c = el as CounterPrimitive;
  const rawFrom = Number(c.from ?? 0);
  const fromVal = Number.isFinite(rawFrom) ? rawFrom : 0;
  const rawTo = Number(c.to ?? (c as any).value ?? (c as any).number ?? 0);
  const toVal = Number.isFinite(rawTo) ? rawTo : 0;
  const currentVal = Math.round(fromVal + (toVal - fromVal) * progress);
  const fSize = c.fontSize ?? 64;
  const textColor = c.color || accent;

  return wrap(
    <div
      dir="rtl"
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        textAlign: 'center',
        background: 'rgba(11, 15, 25, 0.75)',
        border: `1.5px solid ${accent}44`,
        borderRadius: 24,
        padding: '16px 32px',
        backdropFilter: 'blur(12px)',
        boxShadow: '0 16px 32px rgba(0,0,0,0.4)',
      }}
    >
      <div
        dir="ltr"
        style={{
          fontFamily: 'monospace, system-ui',
          fontSize: fSize,
          fontWeight: 800,
          color: textColor,
          textShadow: `0 0 20px ${textColor}66`,
          display: 'flex',
          alignItems: 'baseline',
          gap: 8,
        }}
      >
        {c.prefix && <span style={{ fontSize: fSize * 0.6 }}>{c.prefix}</span>}
        <span>{(toVal >= 1000 && toVal <= 2100 && !c.unit) ? String(currentVal) : currentVal.toLocaleString('en-US')}</span>
        {c.unit && <span style={{ fontSize: fSize * 0.55, opacity: 0.9 }}>{c.unit}</span>}
      </div>
      {c.label && (
        <span
          style={{
            fontSize: Math.max(20, fSize * 0.38),
            color: '#e2e8f0',
            fontWeight: 600,
            marginTop: 6,
          }}
        >
          {c.label}
        </span>
      )}
    </div>
  );
};

export const renderGauge = (ctx: GenCtx): React.ReactNode => {
  const {el, frame, fps, accent, settled, x, y, progress, opacity, transform, loopStyle, wrap} = ctx;
  const g = el as GaugePrimitive;
  const currentPct = Math.round(g.value * progress);
  const barW = g.width ?? 480;
  const color = g.color || accent;
  const track = g.trackColor || 'rgba(255,255,255,0.12)';

  if (g.kind === 'ring') {
    const radius = 64;
    const circ = 2 * Math.PI * radius;
    const dashOffset = circ - (circ * currentPct) / 100;
    return wrap(
      <div
        style={{
          position: 'relative',
          width: 160,
          height: 160,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <svg width={160} height={160} style={{ transform: 'rotate(-90deg)' }}>
          <circle cx={80} cy={80} r={radius} stroke={track} strokeWidth={12} fill="none" />
          <circle
            cx={80}
            cy={80}
            r={radius}
            stroke={color}
            strokeWidth={12}
            fill="none"
            strokeLinecap="round"
            strokeDasharray={circ}
            strokeDashoffset={dashOffset}
            style={{ filter: `drop-shadow(0 0 10px ${color}88)` }}
          />
        </svg>
        <div
          dir="ltr"
          style={{
            position: 'absolute',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
          }}
        >
          <span style={{ fontSize: 32, fontWeight: 800, color: '#ffffff' }}>{currentPct}%</span>
          {g.label && <span style={{ fontSize: 14, color: '#94a3b8' }}>{g.label}</span>}
        </div>
      </div>
    );
  }

  // Linear bar
  return wrap(
    <div
      dir="rtl"
      style={{
        width: barW,
        display: 'flex',
        flexDirection: 'column',
        gap: 8,
        background: 'rgba(15, 23, 42, 0.8)',
        padding: '16px 22px',
        borderRadius: 20,
        border: '1px solid rgba(255,255,255,0.12)',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: 22, fontWeight: 700, color: '#f1f5f9' }}>{g.label || ''}</span>
        <span dir="ltr" style={{ fontSize: 22, fontWeight: 800, color }}>
          {currentPct}
          {g.unit || '%'}
        </span>
      </div>
      <div
        style={{
          width: '100%',
          height: 16,
          background: track,
          borderRadius: 999,
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            width: `${currentPct}%`,
            height: '100%',
            background: `linear-gradient(90deg, ${color}88, ${color})`,
            borderRadius: 999,
            boxShadow: `0 0 12px ${color}88`,
          }}
        />
      </div>
    </div>
  );
};

export const renderConnector = (ctx: GenCtx): React.ReactNode => {
  const {el, frame, fps, accent, settled, x, y, progress, opacity, transform, loopStyle, wrap} = ctx;
  const conn = el as any;
  const color = conn.color || accent;
  const strokeW = conn.strokeWidth ?? 3;
  const isDashed = Boolean(conn.dashed || conn.style === 'dashed');

  const fromArr = Array.isArray(conn.from) && conn.from.length >= 2 ? conn.from : null;
  const toArr = Array.isArray(conn.to) && conn.to.length >= 2 ? conn.to : null;

  const x1: number = fromArr ? Number(fromArr[0]) : Number(conn.fromX ?? conn.x ?? 300);
  const y1: number = fromArr ? Number(fromArr[1]) : Number(conn.fromY ?? 1000);
  const x2: number = toArr ? Number(toArr[0]) : Number(conn.toX ?? 780);
  const y2: number = toArr ? Number(toArr[1]) : Number(conn.toY ?? 800);
  const curX2 = x1 + (x2 - x1) * progress;
  const curY2 = y1 + (y2 - y1) * progress;
  const midX = (x1 + x2) / 2;
  const midY = (y1 + y2) / 2;

  return (
    <svg
      width={1080}
      height={1920}
      style={{
        position: 'absolute',
        inset: 0,
        pointerEvents: 'none',
        zIndex: el.zIndex ?? 7,
        overflow: 'visible',
      }}
    >
      <line
        x1={x1}
        y1={y1}
        x2={curX2}
        y2={curY2}
        stroke={color}
        strokeWidth={strokeW}
        strokeDasharray={isDashed ? '8 6' : undefined}
        strokeLinecap="round"
      />
      {conn.label && progress > 0.6 && (
        <foreignObject
          x={midX - 90}
          y={midY - 24}
          width={180}
          height={48}
          style={{ overflow: 'visible' }}
        >
          <div
            dir="rtl"
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              background: 'rgba(15, 23, 42, 0.92)',
              border: `1.5px solid ${color}88`,
              borderRadius: 999,
              padding: '4px 14px',
              color: '#ffffff',
              fontSize: 16,
              fontWeight: 600,
              whiteSpace: 'nowrap',
            }}
          >
            {conn.label}
          </div>
        </foreignObject>
      )}
    </svg>
  );
};
