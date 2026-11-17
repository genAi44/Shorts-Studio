import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame} from 'remotion';
import {Icon} from './icons';
import {Emoji} from './emoji';
import {Flag} from './flag';
import {LottieVisual} from './lottie';
import {ChartVisual} from './charts';
import {TypographyVisual} from './typography';
import {BEAT_ZONE, SAFE_TOP} from './layout';
import type {VisualElement, VisualPlacement} from './schema';

const placementStyle = (placement?: VisualPlacement, x?: number, y?: number): React.CSSProperties => {
  if (typeof x === 'number' && typeof y === 'number') {
    return {
      position: 'absolute',
      left: x,
      top: y,
      transform: 'translate(-50%, -50%)',
    };
  }
  // Safe margins for 9:16 (1080x1920) from central layout contract
  switch (placement) {
    case 'top-right':
      return {position: 'absolute', top: BEAT_ZONE.corner_top, right: 96};
    case 'top-left':
      return {position: 'absolute', top: BEAT_ZONE.corner_top, left: 96};
    case 'bottom-right':
      return {position: 'absolute', top: BEAT_ZONE.corner_bottom, right: 96};
    case 'bottom-left':
      return {position: 'absolute', top: BEAT_ZONE.corner_bottom, left: 96};
    case 'center':
    case 'hero':
    default:
      return {
        position: 'absolute',
        left: '50%',
        top: BEAT_ZONE.center_y,
        transform: 'translate(-50%, -50%)',
      };
  }
};

export const SingleVisualElement: React.FC<{item: VisualElement; index?: number}> = ({
  item,
  index = 0,
}) => {
  // Timed elements (entity-synced flags) start their entrance animation when they appear
  const delayFrames = (typeof item.from === 'number' ? item.from : 0) + index * 5;
  switch (item.kind) {
    case 'icon':
      return (
        <Icon
          name={item.spec.name}
          size={item.spec.size}
          color={item.spec.color || '#f5c542'}
          strokeWidth={item.spec.strokeWidth}
          animation={item.spec.animation}
          delayFrames={delayFrames}
        />
      );
    case 'emoji':
      return (
        <Emoji
          char={item.spec.char}
          size={item.spec.size}
          animation={item.spec.animation}
          delayFrames={delayFrames}
        />
      );
    case 'flag':
      if (!item.spec.code) return null;
      return (
        <Flag
          code={item.spec.code}
          shape={item.spec.shape}
          size={item.spec.size}
          animation={item.spec.animation}
          delayFrames={delayFrames}
        />
      );
    case 'lottie':
      return (
        <LottieVisual
          name={item.spec.name}
          size={item.spec.size}
          loop={item.spec.loop}
          playbackRate={item.spec.playbackRate}
        />
      );
    case 'chart':
      return <ChartVisual spec={item.spec} />;
    case 'component':
      return <TypographyVisual spec={item.spec} />;
    default:
      return null;
  }
};

const FADE_FRAMES = 6;

/** Opacity of a timed element (from/to in scene-local frames); 1 for untimed elements. */
const timedOpacity = (v: VisualElement, frame: number): number => {
  if (typeof v.from !== 'number' || typeof v.to !== 'number') return 1;
  if (frame < v.from || frame >= v.to) return 0;
  const fadeIn = v.from === 0 ? 1 : interpolate(frame, [v.from, v.from + FADE_FRAMES], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const fadeOut = interpolate(frame, [v.to - FADE_FRAMES, v.to], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return Math.min(fadeIn, fadeOut);
};

/**
 * Renders `visuals` attached to a Scene or Beat.
 * Timed elements (`from`/`to`, e.g. entity-synced flags) are shown only inside their window,
 * so the flag always matches the country currently being spoken about.
 * Enforces the `motion-design-quality` rule: max 3 visible elements at a time.
 */
export const SceneVisualsLayer: React.FC<{visuals?: VisualElement[]}> = ({visuals}) => {
  const frame = useCurrentFrame();
  if (!visuals || visuals.length === 0) return null;
  const bounded = visuals
    .filter((v) => {
      if (!v || !v.spec) return false;
      if (v.kind === 'flag' && !v.spec.code) return false;
      if (v.kind === 'icon' && !v.spec.name) return false;
      return timedOpacity(v, frame) > 0;
    })
    .slice(0, 3);
  if (bounded.length === 0) return null;

  const badgeItems = bounded.filter((v) => v.placement === 'badge-row' || (!v.placement && v.kind !== 'chart' && v.kind !== 'component'));
  const positionedItems = bounded.filter((v) => !badgeItems.includes(v));

  return (
    <AbsoluteFill style={{pointerEvents: 'none', zIndex: 16}}>
      {positionedItems.map((item, idx) => (
        <div key={`pos_${idx}`} data-slot={(item as any).slot || 'STAGE_B'} style={{...placementStyle(item.placement, item.x, item.y), opacity: timedOpacity(item, frame)}}>
          <SingleVisualElement item={item} index={idx} />
        </div>
      ))}
      {badgeItems.length > 0 && (
        <div
          data-slot="HEADER"
          style={{
            position: 'absolute',
            top: SAFE_TOP,
            left: '50%',
            transform: 'translateX(-50%)',
            display: 'flex',
            justifyContent: 'center',
            gap: 16,
            alignItems: 'center',
            pointerEvents: 'none',
          }}
        >
          {badgeItems.map((item, idx) => (
            <div
              key={`badge_${item.kind}_${item.from ?? 'x'}_${idx}`}
              style={{
                opacity: timedOpacity(item, frame),
                padding: '6px 14px',
                borderRadius: 999,
                background: 'rgba(11, 18, 32, 0.72)',
                border: '1px solid rgba(245, 197, 66, 0.28)',
                boxShadow: '0 8px 24px rgba(0,0,0,0.35)',
                backdropFilter: 'blur(10px)',
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <SingleVisualElement item={item} index={idx} />
            </div>
          ))}
        </div>
      )}
    </AbsoluteFill>
  );
};

