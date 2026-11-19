/**
 * CameraRig — Cinematic 2.5D camera system for Remotion.
 * v2: spring per-axis, rotation, punch-in, parallax 5 depths, motion-blur Trail.
 */
import React from 'react';
import {AbsoluteFill, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {Trail} from '@remotion/motion-blur';

// ─── spring presets ───────────────────────────────────────────────────────────
const SPRINGS = {
  smooth:  {mass: 1,   damping: 28, stiffness: 120},
  snappy:  {mass: 1,   damping: 18, stiffness: 220},
  heavy:   {mass: 1.4, damping: 32, stiffness: 90},
  bouncy:  {mass: 0.8, damping: 12, stiffness: 180},
  pop:     {mass: 0.6, damping: 10, stiffness: 300},
} as const;
type Preset = keyof typeof SPRINGS;

// ─── Impact shake ─────────────────────────────────────────────────────────────
export const useCameraShake = (
  triggerFrame: number,
  dur = 12,
  intensity = 1,
) => {
  const frame = useCurrentFrame();
  const t = frame - triggerFrame;
  if (t < 0 || t >= dur) return {x: 0, y: 0, rot: 0};
  const decay = 1 - t / dur;
  return {
    x:   Math.sin(t * 2.1) * 8  * intensity * decay,
    y:   Math.cos(t * 1.7) * 5  * intensity * decay,
    rot: Math.sin(t * 1.5) * 0.6 * intensity * decay,
  };
};

// ─── Punch-in hook ────────────────────────────────────────────────────────────
/** Triggers a sharp zoom-in spring at `triggerFrame`, returns scale 1→target. */
export const usePunchIn = (
  triggerFrame: number,
  targetScale = 1.18,
  preset: Preset = 'pop',
) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const cfg = SPRINGS[preset];
  const prog = spring({frame: frame - triggerFrame, fps, config: cfg});
  if (frame < triggerFrame) return 1;
  return 1 + (targetScale - 1) * prog;
};

// ─── Parallax layer (5 depths) ────────────────────────────────────────────────
export const ParallaxLayer: React.FC<{
  depth?: 0 | 1 | 2 | 3 | 4;  // 0=slowest bg, 4=fastest fg
  children: React.ReactNode;
  style?: React.CSSProperties;
}> = ({depth = 2, children, style}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const prog = frame / Math.max(1, durationInFrames - 1);
  // speed multipliers for 5 depth levels
  const sp = ([0.12, 0.28, 0.50, 0.72, 1.0] as const)[depth];
  const range = 32;
  return (
    <AbsoluteFill
      style={{
        transform: `translate(${(-range / 2 + range * prog) * sp}px, ${(-range * 0.3 / 2 + range * 0.3 * prog) * sp}px)`,
        ...style,
      }}
    >
      {children}
    </AbsoluteFill>
  );
};

// ─── CameraRig ────────────────────────────────────────────────────────────────
export type CameraMode =
  | 'ken-burns'
  | 'static'
  | 'push-in'
  | 'pull-out'
  | 'pan-horizontal'
  | 'pan-vertical'
  | 'zoom-punch'
  | 'handheld'
  | 'drift-left'
  | 'drift-right'
  | 'float-up';

/**
 * CameraRig: wraps content in cinematic camera movements with spring physics.
 * Each axis (scale, tx, ty, rot) has an independent spring so motion feels organic.
 *
 * Usage:
 *   <CameraRig mode="push-in" motionBlur>
 *     <ParallaxLayer depth={0}>{bg}</ParallaxLayer>
 *     <ParallaxLayer depth={2}>{cards}</ParallaxLayer>
 *     <ParallaxLayer depth={4}>{text}</ParallaxLayer>
 *   </CameraRig>
 */
export const CameraRig: React.FC<{
  mode?: CameraMode;
  shakeFrame?: number;
  shakeIntensity?: number;
  springPreset?: Preset;
  /** Trigger a zoom punch at this frame */
  punchFrame?: number;
  punchScale?: number;
  /** Enable @remotion/motion-blur Trail on the rig */
  motionBlur?: boolean;
  /** Number of blur layers (Trail `layers` prop) */
  motionBlurLayers?: number;
  motionBlurOpacity?: number;
  children: React.ReactNode;
  style?: React.CSSProperties;
}> = ({
  mode = 'ken-burns',
  shakeFrame = -99,
  shakeIntensity = 1,
  springPreset = 'smooth',
  punchFrame = -99,
  punchScale = 1.18,
  motionBlur = false,
  motionBlurLayers = 3,
  motionBlurOpacity = 0.6,
  children,
  style,
}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const sh = useCameraShake(shakeFrame, 12, shakeIntensity);
  const prog = frame / Math.max(1, durationInFrames - 1);
  const cfg = SPRINGS[springPreset];

  // per-axis springs from frame 0
  const sp = spring({frame, fps, config: cfg, durationInFrames});
  const punchSp = usePunchIn(punchFrame, punchScale, 'pop');

  let scale = punchSp;
  let tx = sh.x;
  let ty = sh.y;
  let rot = sh.rot;

  switch (mode) {
    case 'ken-burns':
      scale *= 1 + 0.08 * sp;
      tx += (-20 + 40 * sp);
      break;
    case 'push-in':
      scale *= 1 + 0.12 * sp;
      break;
    case 'pull-out':
      scale *= 1.12 - 0.12 * sp;
      break;
    case 'pan-horizontal':
      tx += -40 + 80 * sp;
      break;
    case 'pan-vertical':
      ty += -30 + 60 * sp;
      break;
    case 'drift-left':
      tx += 24 * sp;
      scale *= 1 + 0.04 * sp;
      break;
    case 'drift-right':
      tx += -24 * sp;
      scale *= 1 + 0.04 * sp;
      break;
    case 'float-up':
      ty += 20 * sp;
      scale *= 1 + 0.03 * sp;
      break;
    case 'zoom-punch': {
      const pp = Math.pow(prog, 1.5);
      scale *= 1 + 0.20 * pp;
      tx += -15 + 30 * pp;
      break;
    }
    case 'handheld':
      if (prog > 0.1 && prog < 0.9) {
        const amt = 2.5 * Math.sin(frame * 0.7) * (1 - Math.abs(prog - 0.5) * 2);
        tx += Math.sin(frame * 0.53) * amt;
        ty += Math.cos(frame * 0.47) * amt * 0.7;
        rot += Math.sin(frame * 0.31) * 0.15;
      }
      break;
    default:
      break;
  }

  const inner = (
    <AbsoluteFill
      style={{
        transform: `scale(${scale.toFixed(5)}) translate(${tx.toFixed(2)}px, ${ty.toFixed(2)}px) rotate(${rot.toFixed(3)}deg)`,
        transformOrigin: 'center center',
        ...style,
      }}
    >
      {children}
    </AbsoluteFill>
  );

  if (motionBlur) {
    return (
      <AbsoluteFill>
        <Trail layers={motionBlurLayers} lagInFrames={1} trailOpacity={motionBlurOpacity}>
          {inner}
        </Trail>
      </AbsoluteFill>
    );
  }
  return inner;
};

// ─── SvgZoomIn (kept for map beats) ──────────────────────────────────────────
export const SvgZoomIn: React.FC<{
  originX: number;
  originY: number;
  fromScale?: number;
  dur?: number;
  children: React.ReactNode;
}> = ({originX, originY, children, fromScale = 0.45, dur = 40}) => {
  const frame = useCurrentFrame();
  const t = Math.min(1, frame / dur);
  const eased = 1 - Math.pow(1 - t, 3);
  const sc = fromScale + (1 - fromScale) * eased;
  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        transformOrigin: `${originX}px ${originY}px`,
        scale: String(sc),
      }}
    >
      {children}
    </div>
  );
};
