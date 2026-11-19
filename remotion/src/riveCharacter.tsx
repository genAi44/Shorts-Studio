/**
 * riveCharacter.tsx — Rive character animation for Remotion.
 *
 * Uses @remotion/rive (already installed) to play .riv animations
 * frame-accurately. The .riv file name controls which animation plays.
 *
 * Usage:
 *   <RiveCharacter
 *     src={staticFile('characters/hero.riv')}
 *     animation="idle"
 *     width={420}
 *     height={560}
 *     enterFrame={30}
 *   />
 *
 * Place .riv files in remotion/public/characters/.
 * Free characters: rive.app/community (CC-BY or free, check each file's license).
 *
 * Note: state machine inputs require using the ref API — see @remotion/rive docs.
 */
import React from 'react';
import {interpolate, useCurrentFrame} from 'remotion';
import {RemotionRiveCanvas} from '@remotion/rive';

export const RiveCharacter: React.FC<{
  /** Path from staticFile(), e.g. staticFile('characters/hero.riv') */
  src: string;
  /** Name or index of the animation to play */
  animation?: string | number;
  artboard?: string | number;
  fit?: 'contain' | 'cover' | 'fill' | 'fit-width' | 'fit-height' | 'none' | 'scale-down';
  width?: number;
  height?: number;
  style?: React.CSSProperties;
  /** Frame at which the character fades in */
  enterFrame?: number;
  enterDur?: number;
}> = ({
  src,
  animation,
  artboard,
  fit = 'contain',
  width = 400,
  height = 500,
  style,
  enterFrame = 0,
  enterDur = 10,
}) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [enterFrame, enterFrame + enterDur], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  return (
    <div style={{width, height, position: 'relative', opacity, ...style}}>
      <RemotionRiveCanvas
        src={src}
        animation={animation}
        artboard={artboard}
        fit={fit}
        style={{width: '100%', height: '100%'}}
      />
    </div>
  );
};

/**
 * RiveScene — full-screen Rive background scene (ambient loops, environment art).
 */
export const RiveScene: React.FC<{
  src: string;
  animation?: string | number;
  artboard?: string | number;
  opacity?: number;
}> = ({src, animation, artboard, opacity = 1}) => (
  <div style={{position: 'absolute', inset: 0, opacity}}>
    <RemotionRiveCanvas
      src={src}
      animation={animation}
      artboard={artboard}
      fit="cover"
      style={{width: '100%', height: '100%'}}
    />
  </div>
);
