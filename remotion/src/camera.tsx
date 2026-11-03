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
 * CameraRig: wraps content in a Ken-Burns slow drift or push-in,
 * plus an optional impact shake triggered at a specific frame.
 *
 * Usage:
 *   <CameraRig mode="ken-burns">
 *     <ParallaxLayer depth={0}>{bgMap}</ParallaxLayer>
 *     <ParallaxLayer depth={1}>{cards}</ParallaxLayer>
 *     <ParallaxLayer depth={2}>{text}</ParallaxLayer>
 *   </CameraRig>
 */
export const CameraRig: React.FC<{
  mode?: 'ken-burns' | 'static' | 'push-in';
  /** frame offset (from beat frame 0) to trigger a punch shake */
  shakeFrame?: number;
  shakeIntensity?: number;
  children: React.ReactNode;
  style?: React.CSSProperties;
}> = ({mode = 'ken-burns', shakeFrame = -99, shakeIntensity = 1, children, style}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const sh = useCameraShake(shakeFrame, 12, shakeIntensity);
  const prog = frame / Math.max(1, durationInFrames - 1);

  let scale = 1;
  let tx = sh.x;
  let ty = sh.y;

  if (mode === 'ken-burns') {
    scale = 1 + 0.08 * prog;
    tx += -20 + 40 * prog;
  } else if (mode === 'push-in') {
    scale = 1 + 0.12 * prog;
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
