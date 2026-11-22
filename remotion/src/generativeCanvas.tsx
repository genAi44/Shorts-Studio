import React from 'react';
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { evolvePath } from '@remotion/paths';
import { Icon } from './icons';
import { Emoji } from './emoji';
import { Flag } from './flag';
import { LottieVisual } from './lottie';
import { useTheme, rgba } from './theme';
import { useFont } from './hooks';
import { DYNAMIC_SCENE_REGISTRY } from './generated/DynamicScenes';

export type MotionPreset =
  | 'pop'
  | 'rise'
  | 'drop'
  | 'fade'
  | 'scale'
  | 'draw'
  | 'slide_right'
  | 'slide_left'
  | 'none';

export type LoopPreset = 'float' | 'pulse' | 'spin' | 'glow' | 'breathe' | 'shake' | 'none';

export interface BasePrimitive {
  id?: string;
  type: string;
  x?: number; // 0..1080 default 540
  y?: number; // 0..1920 default 960
  delay?: number; // in frames (or seconds * fps)
  duration?: number;
  motion?: MotionPreset;
  loop?: LoopPreset;
  opacity?: number;
  zIndex?: number;
}

export interface ShapePrimitive extends BasePrimitive {
  type: 'shape';
  shape: 'rect' | 'circle' | 'ring' | 'triangle' | 'pill' | 'star' | 'cylinder' | 'shield';
  w?: number;
  h?: number;
  r?: number; // corner radius
  fill?: string;
  stroke?: string;
  strokeWidth?: number;
}

export interface PathPrimitive extends BasePrimitive {
  type: 'path';
  d?: string; // custom SVG path d
  curve?: 'bezier' | 'wave' | 'mountain' | 'arc' | 'zigzag';
  from?: [number, number];
  to?: [number, number];
  control?: [number, number];
  stroke?: string;
  strokeWidth?: number;
  strokeDasharray?: string;
  arrowHead?: boolean;
}

export interface BadgePrimitive extends BasePrimitive {
  type: 'badge';
  text: string;
  sub?: string;
  icon?: string;
  emoji?: string;
  flag?: string;
  bg?: string;
  textColor?: string;
  borderColor?: string;
  size?: 'sm' | 'md' | 'lg';
}

export interface CounterPrimitive extends BasePrimitive {
  type: 'counter';
  from?: number;
  to: number;
  unit?: string;
  prefix?: string;
  label?: string;
  color?: string;
  fontSize?: number;
}

export interface GaugePrimitive extends BasePrimitive {
  type: 'gauge';
  value: number; // 0..100
  label?: string;
  unit?: string;
  kind?: 'linear' | 'ring';
  width?: number;
  color?: string;
  trackColor?: string;
}

export interface ConnectorPrimitive extends BasePrimitive {
  type: 'connector';
  from?: [number, number];
  to?: [number, number];
  fromX?: number;
  fromY?: number;
  toX?: number;
  toY?: number;
  style?: 'solid' | 'dashed';
  animated?: boolean;
  label?: string;
  dashed?: boolean;
  color?: string;
  strokeWidth?: number;
}

export interface TextPrimitive extends BasePrimitive {
  type: 'text';
  text: string;
  size?: number;
  weight?: number;
  color?: string;
  align?: 'center' | 'right' | 'left';
  maxWidth?: number;
  bgChip?: boolean;
}

export interface IconPrimitive extends BasePrimitive {
  type: 'icon';
  name: string;
  size?: number;
  color?: string;
  strokeWidth?: number;
}

export interface EmojiPrimitive extends BasePrimitive {
  type: 'emoji';
  char: string;
  size?: number;
}

export interface FlagPrimitive extends BasePrimitive {
  type: 'flag';
  code: string;
  shape?: 'rect' | 'round';
  size?: number;
}

export interface LottiePrimitive extends BasePrimitive {
  type: 'lottie';
  name: string;
  size?: number;
}

export type GenerativeElement =
  | ShapePrimitive
  | PathPrimitive
  | BadgePrimitive
  | CounterPrimitive
  | GaugePrimitive
  | ConnectorPrimitive
  | TextPrimitive
  | IconPrimitive
  | EmojiPrimitive
  | FlagPrimitive
  | LottiePrimitive
  | (BasePrimitive & Record<string, any>);

export interface GenerativeCanvasSpec {
  title?: string;
  subtitle?: string;
  background?: string;
  accent?: string;
  grid?: boolean | 'dots' | 'lines' | 'radar';
  elements: GenerativeElement[];
}

// ------------------------------------------------------------------ Motion Engine Hook
const usePrimitiveMotion = (
  frame: number,
  fps: number,
  delay = 0,
  motion: MotionPreset = 'pop',
  loop: LoopPreset = 'none',
  settled = false
) => {
  // Interpret delay consistently as frame offset (or seconds if small float)
  const startFrame = settled ? 0 : Math.max(0, delay > 0 && delay < 3 && !Number.isInteger(delay) ? Math.round(delay * fps) : Math.round(delay));
  const spr = settled
    ? 1
    : spring({
      frame: frame - startFrame,
      fps,
      config: { damping: 14, stiffness: 120, mass: 0.8 },
    });

  const progress = Math.max(0, Math.min(1, spr));
  const t = (frame - startFrame) / fps;

  // Transform styles
  let transform = '';
  let opacity = 1;

  switch (motion) {
    case 'pop':
      transform = `scale(${interpolate(progress, [0, 1], [0.3, 1])})`;
      opacity = interpolate(progress, [0, 0.4, 1], [0, 1, 1]);
      break;
    case 'rise':
      transform = `translateY(${interpolate(progress, [0, 1], [80, 0])}px)`;
      opacity = interpolate(progress, [0, 0.5, 1], [0, 1, 1]);
      break;
    case 'drop':
      transform = `translateY(${interpolate(progress, [0, 1], [-80, 0])}px)`;
      opacity = interpolate(progress, [0, 0.5, 1], [0, 1, 1]);
      break;
    case 'slide_right':
      transform = `translateX(${interpolate(progress, [0, 1], [-120, 0])}px)`;
      opacity = interpolate(progress, [0, 0.5, 1], [0, 1, 1]);
      break;
    case 'slide_left':
      transform = `translateX(${interpolate(progress, [0, 1], [120, 0])}px)`;
      opacity = interpolate(progress, [0, 0.5, 1], [0, 1, 1]);
      break;
    case 'scale':
      transform = `scale(${interpolate(progress, [0, 1], [0.7, 1])})`;
      opacity = interpolate(progress, [0, 0.4, 1], [0, 1, 1]);
      break;
    case 'fade':
      opacity = interpolate(progress, [0, 1], [0, 1]);
      break;
    case 'draw':
      opacity = interpolate(progress, [0, 0.2, 1], [0, 1, 1]);
      break;
    case 'none':
    default:
      opacity = 1;
      transform = '';
      break;
  }

  // Continuous ambient loops
  let loopStyle: React.CSSProperties = {};
  if (t > 0.4) {
    switch (loop) {
      case 'float':
        loopStyle = { transform: `translateY(${Math.sin(t * 2.5) * 10}px)` };
        break;
      case 'pulse':
        loopStyle = { transform: `scale(${1 + Math.sin(t * 3.5) * 0.05})` };
        break;
      case 'spin':
        loopStyle = { transform: `rotate(${(t * 45) % 360}deg)` };
        break;
      case 'breathe':
        loopStyle = { opacity: 0.82 + Math.sin(t * 2) * 0.18 };
        break;
      case 'shake':
        loopStyle = { transform: `translateX(${Math.sin(t * 18) * 4}px)` };
        break;
      case 'glow':
        loopStyle = { filter: `drop-shadow(0 0 ${12 + Math.sin(t * 3) * 8}px currentColor)` };
        break;
      case 'none':
      default:
        break;
    }
  }

  return { progress, opacity, transform, loopStyle };
};

// ------------------------------------------------------------------ Generative Element Renderer
export const GenerativeElementView: React.FC<{
  el: GenerativeElement;
  frame: number;
  fps: number;
  accent: string;
  settled?: boolean;
}> = ({ el, frame, fps, accent, settled = false }) => {
  const rawX = Number(el.x ?? 540);
  const rawY = Number(el.y ?? 960);
  const x = Number.isFinite(rawX) ? Math.max(200, Math.min(880, rawX)) : 540;
  const y = Number.isFinite(rawY) ? Math.max(360, Math.min(1550, rawY)) : 960;
  const motionPreset = (el.motion as MotionPreset) || 'pop';
  const loopPreset = (el.loop as LoopPreset) || 'none';
  const { progress, opacity, transform, loopStyle } = usePrimitiveMotion(
    frame,
    fps,
    el.delay ?? 0,
    motionPreset,
    loopPreset,
    settled
  );

  // Wrapper for placement and entrance
  const wrap = (content: React.ReactNode, extraStyle?: React.CSSProperties) => (
    <div
      style={{
        position: 'absolute',
        left: x,
        top: y,
        transform: 'translate(-50%, -50%)',
        zIndex: el.zIndex ?? 10,
        pointerEvents: 'none',
        ...extraStyle,
      }}
    >
      <div style={{ opacity, transform }}>
        <div style={loopStyle}>{content}</div>
      </div>
    </div>
  );

  switch (el.type) {
    case 'shape': {
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
    }

    case 'path': {
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
    }

    case 'badge': {
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
    }

    case 'counter': {
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
    }

    case 'gauge': {
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
    }

    case 'connector': {
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
    }

    case 'text': {
      const txt = el as TextPrimitive;
      const size = txt.size ?? 38;
      const color = txt.color || '#ffffff';
      const weight = txt.weight ?? 700;

      return wrap(
        <div
          dir="rtl"
          style={{
            fontSize: size,
            fontWeight: weight,
            color,
            textAlign: txt.align || 'center',
            maxWidth: txt.maxWidth ?? 880,
            lineHeight: 1.35,
            padding: txt.bgChip ? '12px 28px' : 0,
            background: txt.bgChip ? 'rgba(15, 23, 42, 0.85)' : undefined,
            borderRadius: txt.bgChip ? 18 : undefined,
            border: txt.bgChip ? `1px solid ${accent}44` : undefined,
            textShadow: '0 4px 18px rgba(0,0,0,0.8)',
          }}
        >
          {txt.text}
        </div>
      );
    }

    case 'icon': {
      const ic = el as IconPrimitive;
      return wrap(
        <Icon
          name={ic.name}
          size={ic.size ?? 120}
          color={ic.color || accent}
          strokeWidth={ic.strokeWidth ?? 2.2}
          animation="none"
        />
      );
    }

    case 'emoji': {
      const em = el as EmojiPrimitive;
      return wrap(<Emoji char={em.char} size={em.size ?? 120} animation="none" />);
    }

    case 'flag': {
      const fl = el as FlagPrimitive;
      return wrap(<Flag code={fl.code} shape={fl.shape ?? 'rect'} size={fl.size ?? 130} animation="none" />);
    }

    case 'lottie': {
      const lt = el as LottiePrimitive;
      return wrap(<LottieVisual name={lt.name} size={lt.size ?? 220} loop={true} />);
    }

    default:
      return null;
  }
};

// ------------------------------------------------------------------ Atmospheric Environment & Custom SVG Construction Layers
const CanvasMoodBackground: React.FC<{
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
const CustomSvgIllustrationLayer: React.FC<{
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

// ------------------------------------------------------------------ Generative Canvas Beat Main
// Templates place small fixed-size primitives around the canvas centre, leaving most of the 9:16 frame dark.
// Measure the content bbox (rough per-type size estimates) and scale it up to fill the beat zone.
const FIT_BOX = {w: 920, h: 900, cx: 540, cy: 860, max: 1.9};
export const computeFit = (els: any[]): {k: number; cx: number; cy: number} => {
  let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
  for (const el of els) {
    const rx = Number(el.x ?? 540), ry = Number(el.y ?? 960);
    if (!Number.isFinite(rx) || !Number.isFinite(ry)) continue;
    const x = Math.max(200, Math.min(880, rx)), y = Math.max(360, Math.min(1550, ry));
    let w = 0, h = 0;
    switch (el.type) {
      case 'badge': { const fs = el.size === 'lg' ? 30 : el.size === 'sm' ? 22 : 26; w = String(el.text || '').length * fs * 0.6 + 110; h = fs * (el.sub ? 3.2 : 2.4); break; }
      case 'icon': case 'emoji': w = h = el.size ?? 120; break;
      case 'flag': w = el.size ?? 130; h = w * 0.75; break;
      case 'lottie': w = h = el.size ?? 220; break;
      case 'counter': { const fs = el.fontSize ?? 64; w = (String(el.to ?? '').length + 3) * fs * 0.6; h = fs * 2; break; }
      case 'gauge': w = el.kind === 'ring' ? 160 : (el.width ?? 400); h = el.kind === 'ring' ? 160 : 80; break;
      case 'text': { const fs = el.size ?? 38; w = Math.min(el.maxWidth ?? 800, String(el.text || '').length * fs * 0.55); h = fs * 1.5; break; }
      default: continue; // shapes/paths/connectors are decor: they scale with the group but don't size it
    }
    x0 = Math.min(x0, x - w / 2); x1 = Math.max(x1, x + w / 2);
    y0 = Math.min(y0, y - h / 2); y1 = Math.max(y1, y + h / 2);
  }
  if (!Number.isFinite(x0)) return {k: 1, cx: FIT_BOX.cx, cy: FIT_BOX.cy};
  const k = Math.max(1, Math.min(FIT_BOX.max, FIT_BOX.w / Math.max(1, x1 - x0), FIT_BOX.h / Math.max(1, y1 - y0)));
  return {k, cx: (x0 + x1) / 2, cy: (y0 + y1) / 2};
};

export const GenerativeCanvasBeat: React.FC<{ beat: any }> = ({ beat }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const th = useTheme();
  const font = useFont();

  const defaultAccent = th?.p?.accent ? rgba(th.p.accent) : '#f59e0b';
  const defaultSec = th?.p?.accent2 ? rgba(th.p.accent2) : '#38bdf8';

  const sceneSpec = (beat.scene_spec && typeof beat.scene_spec === 'object') ? beat.scene_spec : {};
  const cinematicMode = sceneSpec.cinematic || (beat.kind === 'custom_scene' ? '' : '');
  const cinematicLighting = sceneSpec.lighting || '';

  const spec: GenerativeCanvasSpec = {
    title: beat.title || '',
    subtitle: beat.subtitle || '',
    background: beat.background,
    accent: beat.accent || defaultAccent,
    grid: beat.grid ?? 'dots',
    elements: beat.elements || [],
  };

  const fit = React.useMemo(() => computeFit(spec.elements as any[]), [spec.elements]);
  const accentColor = spec.accent || defaultAccent;
  const secondaryAccent = beat.secondary_accent || defaultSec;
  const cinematicIntensity = cinematicMode ? 1 : 0;
  const DynamicTsxComp = beat.tsx_id ? DYNAMIC_SCENE_REGISTRY[beat.tsx_id] : undefined;

  return (
    <AbsoluteFill
      style={{
        background:
          spec.background ||
          `radial-gradient(circle at 50% 38%, #132347 0%, #0b1938 55%, #050b1a 100%)`,
        overflow: 'hidden',
      }}
    >
      <CanvasMoodBackground
        mode={spec.grid}
        environment={beat.environment}
        accent={accentColor}
        secondaryAccent={secondaryAccent}
        frame={frame}
        fps={fps}
      />

      {/* Custom SVG Vector Illustrations from Scene Specification (Section C) */}
      <CustomSvgIllustrationLayer
        layers={beat.svg_layers}
        frame={frame}
        fps={fps}
        accent={accentColor}
        secondaryAccent={secondaryAccent}
      />

      {/* Executable React/TSX Component generated specifically for this segment */}
      {DynamicTsxComp ? (
        <DynamicTsxComp frame={frame} fps={fps} dur={beat.dur || 90} />
      ) : null}

      {/* Header title if specified */}
      {spec.title && (
        <div
          dir="rtl"
          style={{
            position: 'absolute',
            top: 235,
            left: '50%',
            transform: 'translateX(-50%)',
            textAlign: 'center',
            zIndex: 30,
            width: 920,
          }}
        >
          <div
            style={{
              ...font,
              fontSize: 52,
              fontWeight: 800,
              color: '#ffffff',
              textShadow: `0 4px 24px rgba(0,0,0,0.85), 0 0 28px ${accentColor}55`,
              lineHeight: 1.25,
            }}
          >
            {spec.title}
          </div>
          {spec.subtitle && (
            <div
              style={{
                fontSize: 27,
                color: accentColor,
                fontWeight: 700,
                marginTop: 8,
                textShadow: '0 2px 12px rgba(0,0,0,0.8)',
              }}
            >
              {spec.subtitle}
            </div>
          )}
        </div>
      )}

      {/* Render all generative elements */}
      <div style={{position: 'absolute', inset: 0, transformOrigin: `${fit.cx}px ${fit.cy}px`, transform: `translate(${FIT_BOX.cx - fit.cx}px, ${FIT_BOX.cy - fit.cy}px) scale(${fit.k.toFixed(3)})`}}>
      {spec.elements.map((el, idx) => (
        <GenerativeElementView
          key={el.id || `gen_el_${idx}`}
          el={el}
          frame={frame}
          fps={fps}
          accent={accentColor}
          settled={Boolean(beat.settled)}
        />
      ))}
      </div>

      {/* Cinematic lighting + vignette + grain layer driven from scene_spec.cinematic / lighting */}
      {cinematicIntensity > 0 && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            pointerEvents: 'none',
            background:
              cinematicLighting === 'dramatic'
                ? 'radial-gradient(ellipse 80% 60% at 50% 42%, rgba(244,63,94,0.34) 0%, rgba(0,0,0,0.55) 70%)'
                : cinematicLighting === 'deep-space'
                ? 'radial-gradient(ellipse 80% 60% at 50% 42%, rgba(56,189,248,0.22) 0%, rgba(8,12,30,0.7) 78%)'
                : cinematicLighting === 'radial-core'
                ? 'radial-gradient(ellipse 90% 70% at 50% 38%, rgba(251,191,36,0.32) 0%, rgba(12,8,30,0.68) 90%)'
                : cinematicLighting === 'cool-flow'
                ? 'radial-gradient(ellipse 80% 60% at 50% 42%, rgba(56,189,248,0.26) 0%, rgba(6,20,38,0.66) 80%)'
                : cinematicLighting === 'earth-tones'
                ? 'radial-gradient(ellipse 80% 60% at 50% 42%, rgba(180,120,60,0.28) 0%, rgba(20,14,8,0.72) 82%)'
                : cinematicLighting === 'soft-top'
                ? 'radial-gradient(ellipse 90% 50% at 50% 18%, rgba(233,244,255,0.28) 0%, rgba(8,12,22,0.66) 82%)'
                : 'radial-gradient(ellipse 80% 60% at 50% 38%, rgba(212,175,55,0.26) 0%, rgba(6,8,18,0.7) 82%)',
            boxShadow: 'inset 0 0 140px rgba(0,0,0,0.72)',
            mixBlendMode: 'multiply',
            opacity: 0.9 + 0.1 * Math.sin(frame / 3),
          }}
        />
      )}

    </AbsoluteFill>
  );
};
