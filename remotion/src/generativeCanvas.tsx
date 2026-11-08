import React from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {evolvePath} from '@remotion/paths';
import {Icon} from './icons';
import {Emoji} from './emoji';
import {Flag} from './flag';
import {LottieVisual} from './lottie';
import {useTheme, rgba} from './theme';
import {useFont} from './hooks';

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
        config: {damping: 14, stiffness: 120, mass: 0.8},
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
        loopStyle = {transform: `translateY(${Math.sin(t * 2.5) * 10}px)`};
        break;
      case 'pulse':
        loopStyle = {transform: `scale(${1 + Math.sin(t * 3.5) * 0.05})`};
        break;
      case 'spin':
        loopStyle = {transform: `rotate(${(t * 45) % 360}deg)`};
        break;
      case 'breathe':
        loopStyle = {opacity: 0.82 + Math.sin(t * 2) * 0.18};
        break;
      case 'shake':
        loopStyle = {transform: `translateX(${Math.sin(t * 18) * 4}px)`};
        break;
      case 'glow':
        loopStyle = {filter: `drop-shadow(0 0 ${12 + Math.sin(t * 3) * 8}px currentColor)`};
        break;
      case 'none':
      default:
        break;
    }
  }

  return {progress, opacity, transform, loopStyle};
};

// ------------------------------------------------------------------ Generative Element Renderer
export const GenerativeElementView: React.FC<{
  el: GenerativeElement;
  frame: number;
  fps: number;
  accent: string;
  settled?: boolean;
}> = ({el, frame, fps, accent, settled = false}) => {
  const rawX = Number(el.x ?? 540);
  const rawY = Number(el.y ?? 960);
  const x = Number.isFinite(rawX) ? Math.max(200, Math.min(880, rawX)) : 540;
  const y = Number.isFinite(rawY) ? Math.max(360, Math.min(1550, rawY)) : 960;
  const motionPreset = (el.motion as MotionPreset) || 'pop';
  const loopPreset = (el.loop as LoopPreset) || 'none';
  const {progress, opacity, transform, loopStyle} = usePrimitiveMotion(
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
      <div style={{opacity, transform}}>
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
          <svg width={w} height={h} viewBox="0 0 100 100" style={{overflow: 'visible'}}>
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
          <svg width={w} height={h} viewBox="0 0 100 120" style={{overflow: 'visible'}}>
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
          <svg width={w} height={h} viewBox="0 0 24 24" style={{overflow: 'visible'}}>
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
      let evolved = {strokeDasharray: 'none', strokeDashoffset: 0};
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
          <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center'}}>
            <span style={{fontSize: fSize, fontWeight: 700, lineHeight: 1.3}}>{b.text}</span>
            {b.sub && <span style={{fontSize: fSize * 0.75, opacity: 0.75}}>{b.sub}</span>}
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
            {c.prefix && <span style={{fontSize: fSize * 0.6}}>{c.prefix}</span>}
            <span>{currentVal.toLocaleString('en-US')}</span>
            {c.unit && <span style={{fontSize: fSize * 0.55, opacity: 0.9}}>{c.unit}</span>}
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
            <svg width={160} height={160} style={{transform: 'rotate(-90deg)'}}>
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
                style={{filter: `drop-shadow(0 0 10px ${color}88)`}}
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
              <span style={{fontSize: 32, fontWeight: 800, color: '#ffffff'}}>{currentPct}%</span>
              {g.label && <span style={{fontSize: 14, color: '#94a3b8'}}>{g.label}</span>}
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
          <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
            <span style={{fontSize: 22, fontWeight: 700, color: '#f1f5f9'}}>{g.label || ''}</span>
            <span dir="ltr" style={{fontSize: 22, fontWeight: 800, color}}>
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
              style={{overflow: 'visible'}}
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

// ------------------------------------------------------------------ Background Grid / Mood Component
const CanvasMoodBackground: React.FC<{mode?: boolean | 'dots' | 'lines' | 'radar'; accent: string}> = ({
  mode,
  accent,
}) => {
  if (!mode) return null;

  if (mode === 'radar') {
    return (
      <svg
        width={1080}
        height={1920}
        style={{position: 'absolute', inset: 0, pointerEvents: 'none', opacity: 0.18}}
      >
        <circle cx={540} cy={960} r={180} stroke={accent} strokeWidth={1.5} fill="none" />
        <circle cx={540} cy={960} r={360} stroke={accent} strokeWidth={1.5} fill="none" strokeDasharray="6 6" />
        <circle cx={540} cy={960} r={540} stroke={accent} strokeWidth={1.5} fill="none" />
        <line x1={540} y1={200} x2={540} y2={1720} stroke={accent} strokeWidth={1} strokeDasharray="4 4" />
        <line x1={80} y1={960} x2={1000} y2={960} stroke={accent} strokeWidth={1} strokeDasharray="4 4" />
      </svg>
    );
  }

  if (mode === 'lines') {
    return (
      <div
        style={{
          position: 'absolute',
          inset: 0,
          opacity: 0.12,
          backgroundImage: `linear-gradient(${accent}33 1px, transparent 1px), linear-gradient(90deg, ${accent}33 1px, transparent 1px)`,
          backgroundSize: '80px 80px',
          pointerEvents: 'none',
        }}
      />
    );
  }

  // Dots mode
  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        opacity: 0.16,
        backgroundImage: `radial-gradient(${accent} 1.5px, transparent 1.5px)`,
        backgroundSize: '48px 48px',
        pointerEvents: 'none',
      }}
    />
  );
};

// ------------------------------------------------------------------ Generative Canvas Beat Main
export const GenerativeCanvasBeat: React.FC<{beat: any}> = ({beat}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const th = useTheme();
  const font = useFont();

  const defaultAccent = th?.p?.accent ? rgba(th.p.accent) : '#f59e0b';
  const spec: GenerativeCanvasSpec = {
    title: beat.title || '',
    subtitle: beat.subtitle || '',
    background: beat.background,
    accent: beat.accent || defaultAccent,
    grid: beat.grid ?? 'dots',
    elements: beat.elements || [],
  };

  const accentColor = spec.accent || defaultAccent;

  return (
    <AbsoluteFill
      style={{
        background:
          spec.background || 'radial-gradient(circle at 50% 45%, #111827 0%, #030712 100%)',
        overflow: 'hidden',
      }}
    >
      <CanvasMoodBackground mode={spec.grid} accent={accentColor} />

      {/* Header title if specified */}
      {spec.title && (
        <div
          dir="rtl"
          style={{
            position: 'absolute',
            top: 240,
            left: '50%',
            transform: 'translateX(-50%)',
            textAlign: 'center',
            zIndex: 30,
            width: 900,
          }}
        >
          <div
            style={{
              ...font,
              fontSize: 52,
              fontWeight: 800,
              color: '#ffffff',
              textShadow: '0 4px 20px rgba(0,0,0,0.8)',
              lineHeight: 1.25,
            }}
          >
            {spec.title}
          </div>
          {spec.subtitle && (
            <div
              style={{
                fontSize: 26,
                color: accentColor,
                fontWeight: 600,
                marginTop: 8,
              }}
            >
              {spec.subtitle}
            </div>
          )}
        </div>
      )}

      {/* Render all generative elements */}
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
    </AbsoluteFill>
  );
};
