/**
 * CameraRig — Cinematic 2.5D camera system for Remotion.
 * Provides Ken Burns, parallax layering, and impact shakes
 * without touching BeatShell's existing camera modes.
 */
import React from 'react';
import {AbsoluteFill, useCurrentFrame, useVideoConfig} from 'remotion';

// --- Impact shake (for dramatic stat reveals / number pops) ---
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
    x: Math.sin(t * 2.1) * 8 * intensity * decay,
    y: Math.cos(t * 1.7) * 5 * intensity * decay,
    rot: Math.sin(t * 1.5) * 0.6 * intensity * decay,
  };
};

// --- Parallax layer (depth 0 = slow background, 2 = fast foreground) ---
export const ParallaxLayer: React.FC<{
  depth?: 0 | 1 | 2;
  children: React.ReactNode;
  style?: React.CSSProperties;
}> = ({depth = 1, children, style}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const prog = frame / Math.max(1, durationInFrames - 1);
  const sp = ([0.25, 0.55, 1.0] as const)[depth];
  return (
    <AbsoluteFill
      style={{
        transform: `translate(${(-14 + 28 * prog) * sp}px, ${(-6 + 12 * prog) * sp}px)`,
        ...style,
      }}
    >
      {children}
    </AbsoluteFill>
  );
};

/**
 * CameraRig: wraps content in cinematic camera movements
 * Includes: ken-burns, push-in, pull-out, pan-horizontal, pan-vertical,
 * zoom-punch (dramatic zoom on revelation), handheld (subtle organic motion)
 *
 * Usage:
 *   <CameraRig mode="ken-burns">
 *     <ParallaxLayer depth={0}>{bgMap}</ParallaxLayer>
 *     <ParallaxLayer depth={1}>{cards}</ParallaxLayer>
 *     <ParallaxLayer depth={2}>{text}</ParallaxLayer>
 *   </CameraRig>
 */
export const CameraRig: React.FC<{
  mode?: 'ken-burns' | 'static' | 'push-in' | 'pull-out' | 'pan-horizontal' | 'pan-vertical' | 'zoom-punch' | 'handheld';
  /** frame offset (from beat frame 0) to trigger a punch shake */
  shakeFrame?: number;
  shakeIntensity?: number;
  /** Easing curve for the camera movement */
  easing?: 'ease-out' | 'ease-in' | 'ease-in-out' | 'linear';
  children: React.ReactNode;
  style?: React.CSSProperties;
}> = ({mode = 'ken-burns', shakeFrame = -99, shakeIntensity = 1, easing = 'ease-out', children, style}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const sh = useCameraShake(shakeFrame, 12, shakeIntensity);
  const prog = frame / Math.max(1, durationInFrames - 1);

  // Easing functions
  const easeOut = (t: number) => 1 - Math.pow(1 - t, 3);
  const easeIn = (t: number) => t * t * t;
  const easeInOut = (t: number) => t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
  const linear = (t: number) => t;
  
  const applyEasing = (t: number) => {
    switch (easing) {
      case 'ease-in': return easeIn(t);
      case 'ease-in-out': return easeInOut(t);
      case 'linear': return linear(t);
      default: return easeOut(t);
    }
  };

  let scale = 1;
  let tx = sh.x;
  let ty = sh.y;
  const easedProg = applyEasing(prog);

  switch (mode) {
    case 'ken-burns':
      scale = 1 + 0.08 * easedProg;
      tx += -20 + 40 * easedProg;
      break;
    case 'push-in':
      scale = 1 + 0.12 * easedProg;
      break;
    case 'pull-out':
      scale = 1.12 - 0.12 * easedProg;
      break;
    case 'pan-horizontal':
      tx = -40 + 80 * easedProg;
      break;
    case 'pan-vertical':
      ty = -30 + 60 * easedProg;
      break;
    case 'zoom-punch':
      // Dramatic zoom that accelerates toward the end
      const punchProg = Math.pow(prog, 1.5);
      scale = 1 + 0.20 * punchProg;
      tx = -15 + 30 * punchProg;
      break;
    case 'handheld':
      // Subtle organic handheld motion (only when not settled)
      if (prog > 0.1 && prog < 0.9) {
        const shakeAmount = 2.5 * Math.sin(frame * 0.7) * (1 - Math.abs(prog - 0.5) * 2);
        tx += Math.sin(frame * 0.53) * shakeAmount;
        ty += Math.cos(frame * 0.47) * shakeAmount * 0.7;
      }
      break;
    default:
      break;
  }

  return (
    <AbsoluteFill
      style={{
        transform: `scale(${scale}) translate(${tx}px, ${ty}px) rotate(${sh.rot}deg)`,
        ...style,
      }}
    >
      {children}
    </AbsoluteFill>
  );
};

/**
 * Zoom-to-city SVG wrapper.
 * Applies an animated scale that starts wide (zoomOut) and eases in to 1.0.
 * Usage: wrap the <svg> inside MapBeat with this when you want a fly-in feel.
 */
export const SvgZoomIn: React.FC<{
  originX: number;
  originY: number;
  fromScale?: number;
  dur?: number;   // frames
  children: React.ReactNode;
}> = ({originX, children, originY, fromScale = 0.45, dur = 40}) => {
  const frame = useCurrentFrame();
  // ease-out cubic
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
