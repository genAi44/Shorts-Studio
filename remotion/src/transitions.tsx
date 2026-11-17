import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {Audio} from '@remotion/media';
import {linearTiming, TransitionSeries} from '@remotion/transitions';
import {fade} from '@remotion/transitions/fade';
import {slide} from '@remotion/transitions/slide';
import {wipe} from '@remotion/transitions/wipe';
import {flip} from '@remotion/transitions/flip';
import {clockWipe} from '@remotion/transitions/clock-wipe';
import {Circle, Polygon, Rect, Star} from '@remotion/shapes';
import {noise2D} from '@remotion/noise';
import {Trail} from '@remotion/motion-blur';
import {ding, pageTurn, uiSwitch, whip, whoosh} from '@remotion/sfx';
import type {SceneTransitionSpec} from './schema';

export {TransitionSeries, linearTiming, Trail, Circle, Polygon, Rect, Star, noise2D};

export const SFX_MAP: Record<string, string | null> = {
  none: null,
  whoosh,
  whip,
  pageTurn,
  switch: uiSwitch,
  uiSwitch,
  ding,
};

/**
 * Storyboard Agent Transition Picker:
 * Assigns a varied sequence of transitions across scene boundaries so no single transition
 * is overused or repeated back-to-back.
 */
export const pickSceneTransitions = (
  sceneCount: number,
  seed = 42,
  sceneRoles: Array<string> = []
): SceneTransitionSpec[] => {
  // Cinematographic transition pool - each type serves a narrative purpose
  const pool: Array<SceneTransitionSpec['type']> = [
    'slide',        // directional, purposeful movement
    'wipe',         // geographical/narrative boundary
    'clock-wipe',   // dramatic revelation
    'fade',         // tonal shift, time passage
    'flip',         // perspective change, contrast
  ];
  const directions: Array<NonNullable<SceneTransitionSpec['direction']>> = [
    'from-right',
    'from-left',
    'from-bottom',
    'from-top',
  ];
  const sfxCycle: Array<SceneTransitionSpec['sfx']> = [
    'whoosh',
    'whip',
    'pageTurn',
    'switch',
  ];

  const out: SceneTransitionSpec[] = [];
  let prevType: SceneTransitionSpec['type'] = 'none';
  let prevDirection: string = 'from-right';

  for (let i = 0; i < sceneCount; i++) {
    if (i === 0) {
      out.push({type: 'none', durationInFrames: 12, sfx: 'none'});
      continue;
    }
    
    const role = sceneRoles[i] || 'body';
    
    // Role-based cinematographic transition selection
    let preferredIndices: number[] = [];
    
    if (role === 'hook') {
      // Hook transitions: dramatic, attention-grabbing
      preferredIndices = [2, 4, 1]; // clock-wipe, flip, wipe
    } else if (role === 'open_loop') {
      // Open loop: suspenseful, lingering
      preferredIndices = [3, 2, 0]; // fade, clock-wipe, slide
    } else if (role === 'cta') {
      // CTA: resolution, closure
      preferredIndices = [3, 1, 0]; // fade, wipe, slide
    } else if (role === 'lead') {
      // Lead: establishing, setting context
      preferredIndices = [0, 1, 3]; // slide, wipe, fade
    } else {
      // Body: varied but smooth
      preferredIndices = [0, 1, 4, 3, 2];
    }
    
    // Select from preferred indices, falling back if needed
    let chosenType: SceneTransitionSpec['type'] = 'slide';
    let typeIdx = -1;
    
    for (const prefIdx of preferredIndices) {
      const candidateIdx = prefIdx % pool.length;
      if (pool[candidateIdx] !== prevType) {
        chosenType = pool[candidateIdx];
        typeIdx = candidateIdx;
        break;
      }
    }
    
    // If all preferred types match previous, pick any other
    if (typeIdx === -1) {
      for (let j = 0; j < pool.length; j++) {
        if (pool[j] !== prevType) {
          chosenType = pool[j];
          typeIdx = j;
          break;
        }
      }
    }
    
    prevType = chosenType;
    
    // Direction selection: avoid repeat direction for 2+ scenes
    let chosenDir = directions[(seed + i) % directions.length];
    if (chosenDir === prevDirection && i > 1) {
      chosenDir = directions[(directions.length + (seed + i + 1) % directions.length) % directions.length];
    }
    prevDirection = chosenDir;
    
    // Duration varies by role for pacing
    let dur = 14;
    if (role === 'hook') dur = 18;
    else if (role === 'open_loop') dur = 16;
    else if (role === 'cta') dur = 12;
    
    out.push({
      type: chosenType,
      direction: chosenDir,
      durationInFrames: dur,
      sfx: sfxCycle[(seed + i) % sfxCycle.length],
    });
  }
  return out;
};

export const getTransitionPresentation = (
  spec: SceneTransitionSpec,
  width = 1080,
  height = 1920
): any => {
  const dir = spec.direction || 'from-right';
  switch (spec.type) {
    case 'slide':
      return slide({direction: dir});
    case 'wipe':
      return wipe({direction: dir});
    case 'flip':
      return flip({direction: dir});
    case 'clock-wipe':
      return clockWipe({width, height});
    case 'fade':
    default:
      return fade();
  }
};

/**
 * Ambient organic floating geometric shapes driven by `@remotion/shapes` and `@remotion/noise`.
 */
export const NoiseShapesLayer: React.FC<{
  seed?: number;
  color?: string;
  secondaryColor?: string;
}> = ({seed = 7, color = 'rgba(245, 197, 66, 0.22)', secondaryColor = 'rgba(56, 189, 248, 0.18)'}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / (fps * 4);

  const dx1 = noise2D(`x1_${seed}`, t, 0) * 60;
  const dy1 = noise2D(`y1_${seed}`, 0, t) * 60;
  const dx2 = noise2D(`x2_${seed}`, t, 1) * 55;
  const dy2 = noise2D(`y2_${seed}`, 1, t) * 55;
  const rot = (frame / fps) * 18;

  return (
    <AbsoluteFill style={{pointerEvents: 'none', overflow: 'hidden'}}>
      <div
        style={{
          position: 'absolute',
          top: 160 + dy1,
          right: 90 + dx1,
          transform: `rotate(${rot.toFixed(1)}deg)`,
          opacity: 0.55,
        }}
      >
        <Star points={5} innerRadius={22} outerRadius={48} fill="none" stroke={color} strokeWidth={3} />
      </div>
      <div
        style={{
          position: 'absolute',
          bottom: 420 + dy2,
          left: 85 + dx2,
          transform: `rotate(${(-rot * 0.8).toFixed(1)}deg)`,
          opacity: 0.5,
        }}
      >
        <Polygon points={6} radius={44} fill="none" stroke={secondaryColor} strokeWidth={3} />
      </div>
    </AbsoluteFill>
  );
};

/**
 * Scene Boundary Transition Overlay + optional `@remotion/sfx` trigger.
 */
export const SceneTransitionEffect: React.FC<{
  transition?: SceneTransitionSpec;
  index: number;
  enableSfx?: boolean;
}> = ({transition, index, enableSfx = false}) => {
  const frame = useCurrentFrame();
  if (index === 0) return null;
  const dur = transition?.durationInFrames ?? 14;
  const type = transition?.type ?? 'slide';
  const sfxUrl = transition?.sfx ? SFX_MAP[transition.sfx] : null;

  if (frame > dur) return null;
  const p = interpolate(frame, [0, dur], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{pointerEvents: 'none', zIndex: 35}}>
      {enableSfx && sfxUrl ? <Audio src={sfxUrl} volume={0.28} /> : null}
      {type === 'clock-wipe' && (
        <div
          style={{
            position: 'absolute',
            left: '50%',
            top: '50%',
            transform: `translate(-50%, -50%) scale(${interpolate(p, [0, 1], [0.2, 2.4])})`,
            opacity: 1 - p,
          }}
        >
          <Circle radius={420} fill="none" stroke="rgba(245, 197, 66, 0.75)" strokeWidth={24 * (1 - p)} />
        </div>
      )}
    </AbsoluteFill>
  );
};
