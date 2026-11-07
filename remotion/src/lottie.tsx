import React, {useMemo} from 'react';
import {Lottie, LottieAnimationData} from '@remotion/lottie';
import {spring, useCurrentFrame, useVideoConfig} from 'remotion';
import lottieDataBundle from './generated/lottieData.json';

export interface LottieVisualProps {
  name: string;
  size?: number;
  loop?: boolean;
  playbackRate?: number;
  style?: React.CSSProperties;
}

const BUNDLE: Record<string, {meta: any; data: LottieAnimationData}> = lottieDataBundle as any;

export const resolveLottieData = (nameOrQuery: string): {id: string; data: LottieAnimationData; meta: any} => {
  const q = (nameOrQuery || 'checkmark').trim().toLowerCase();
  if (BUNDLE[q]) {
    return {id: q, data: BUNDLE[q].data, meta: BUNDLE[q].meta};
  }
  for (const [id, entry] of Object.entries(BUNDLE)) {
    const tags: string[] = entry.meta?.tags || [];
    if (
      id.includes(q) ||
      q.includes(id) ||
      tags.some((t) => t.toLowerCase() === q || q.includes(t.toLowerCase()))
    ) {
      return {id, data: entry.data, meta: entry.meta};
    }
  }
  const fallbackKey = Object.keys(BUNDLE)[0] || 'checkmark';
  return {id: fallbackKey, data: BUNDLE[fallbackKey].data, meta: BUNDLE[fallbackKey].meta};
};

export const LottieVisual: React.FC<LottieVisualProps> = ({
  name,
  size = 180,
  loop = true,
  playbackRate = 1,
  style,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const resolved = useMemo(() => resolveLottieData(name), [name]);
  const enter = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 160, mass: 0.75},
  });

  return (
    <div
      data-lottie-id={resolved.id}
      style={{
        width: size,
        height: size,
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        opacity: Math.min(1, enter * 1.5),
        transform: `scale(${(0.8 + 0.2 * enter).toFixed(3)})`,
        ...style,
      }}
    >
      <Lottie
        animationData={resolved.data}
        loop={loop}
        playbackRate={playbackRate}
        style={{width: '100%', height: '100%'}}
      />
    </div>
  );
};

