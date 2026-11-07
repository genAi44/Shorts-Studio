import React, {useMemo} from 'react';
import {interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import emojiCatalog from './generated/emojiCatalog.json';
import {SafeImg} from './SafeImg';
import type {EmojiAnimationPreset} from './schema';

export interface EmojiProps {
  char: string;
  size?: number;
  animation?: EmojiAnimationPreset;
  delayFrames?: number;
  style?: React.CSSProperties;
}

type EmojiEntry = {
  char: string;
  code: string;
  name: string;
  name_ar: string;
  tags: string[];
  file: string;
  collection: string;
  license: string;
  attributionRequired: boolean;
};

const ITEMS: EmojiEntry[] = (emojiCatalog as any).items || [];

export const resolveEmojiEntry = (charOrQuery: string): EmojiEntry => {
  const q = (charOrQuery || '⭐').trim();
  const qLower = q.toLowerCase();
  // 1. Direct character match (strip variation selector FE0F comparison)
  const stripVS = (s: string) => s.replace(/\uFE0F/g, '');
  const exact = ITEMS.find((it) => it.char === q || stripVS(it.char) === stripVS(q) || it.code === qLower);
  if (exact) return exact;

  // 2. Match by English/Arabic name or tag
  const byTag = ITEMS.find(
    (it) =>
      it.name.toLowerCase().includes(qLower) ||
      it.name_ar.includes(q) ||
      it.tags.some((t) => t.toLowerCase() === qLower || qLower.includes(t.toLowerCase()))
  );
  if (byTag) return byTag;

  return ITEMS[0];
};

export const Emoji: React.FC<EmojiProps> = ({
  char,
  size = 96,
  animation = 'pop',
  delayFrames = 0,
  style,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const localFrame = Math.max(0, frame - delayFrames);
  const entry = useMemo(() => resolveEmojiEntry(char), [char]);

  let scale = 1;
  let translateY = 0;
  let rotateDeg = 0;
  let opacity = 1;

  if (animation === 'pop') {
    const sp = spring({
      frame: localFrame,
      fps,
      config: {damping: 11, stiffness: 190, mass: 0.65},
    });
    scale = interpolate(sp, [0, 1], [0.2, 1]);
    opacity = Math.min(1, sp * 1.6);
  } else if (animation === 'bounce') {
    const enter = spring({frame: localFrame, fps, config: {damping: 12, stiffness: 170}});
    scale = enter;
    translateY = -Math.abs(Math.sin((localFrame / fps) * Math.PI * 2.2)) * 16 * enter;
    opacity = Math.min(1, enter * 1.5);
  } else if (animation === 'shake') {
    const enter = spring({frame: localFrame, fps, config: {damping: 14, stiffness: 160}});
    scale = enter;
    rotateDeg = Math.sin((localFrame / fps) * Math.PI * 6) * 12 * Math.max(0, 1 - localFrame / (fps * 1.5));
    opacity = Math.min(1, enter * 1.5);
  } else if (animation === 'spin') {
    const enter = spring({frame: localFrame, fps, config: {damping: 14, stiffness: 150}});
    scale = enter;
    rotateDeg = interpolate(enter, [0, 1], [-180, 0]) + (localFrame / fps) * 45;
    opacity = Math.min(1, enter * 1.5);
  }

  const src = staticFile(entry.file);

  return (
    <div
      data-emoji={entry.char}
      data-code={entry.code}
      style={{
        width: size,
        height: size,
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        opacity,
        transform: `translateY(${translateY.toFixed(2)}px) scale(${scale.toFixed(3)}) rotate(${rotateDeg.toFixed(2)}deg)`,
        transformOrigin: 'center center',
        userSelect: 'none',
        ...style,
      }}
    >
      <SafeImg
        src={src}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'contain',
          filter: 'drop-shadow(0 6px 16px rgba(0,0,0,0.38))',
        }}
      />
    </div>
  );
};

