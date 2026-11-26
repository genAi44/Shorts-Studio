import React from 'react';
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { evolvePath } from '@remotion/paths';
import { Icon } from './icons';
import { Emoji } from './emoji';
import { Flag } from './flag';
import { LottieVisual } from './lottie';
import { useTheme, rgba } from './theme';
import { BEAT_ZONE, CANVAS_FIT_BOX } from './layout';
import { useFont } from './hooks';
import { DYNAMIC_SCENE_REGISTRY } from './generated/DynamicScenes';
import {renderBadge, renderConnector, renderCounter, renderGauge, renderPath, renderShape} from './generativePrimitives';
export {renderBadge, renderConnector, renderCounter, renderGauge, renderPath, renderShape} from './generativePrimitives';
export {CanvasMoodBackground, CustomSvgIllustrationLayer} from './generativeLayers';
export {GenerativeCanvasBeat, computeFit} from './generativeCanvasBeat';

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
export type GenCtx = {
  el: GenerativeElement; frame: number; fps: number; accent: string; settled?: boolean;
  x: number; y: number; progress: number; opacity: number; transform: string; loopStyle: React.CSSProperties;
  wrap: (content: React.ReactNode, extraStyle?: React.CSSProperties) => React.ReactElement;
};

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

  const ctx: GenCtx = {el, frame, fps, accent, settled, x, y, progress, opacity, transform, loopStyle, wrap};
  switch (el.type) {
    case 'shape':
      return renderShape(ctx);

    case 'path':
      return renderPath(ctx);

    case 'badge':
      return renderBadge(ctx);

    case 'counter':
      return renderCounter(ctx);

    case 'gauge':
      return renderGauge(ctx);

    case 'connector':
      return renderConnector(ctx);

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
