import React from 'react';
import {BEAT_ZONE, CAPTION_ZONE, SAFE_TOP} from './layout';

export type SlotName = 'HEADER' | 'STAGE_A' | 'STAGE_B' | 'FULL_STAGE' | 'CAPTION';

export const SLOT_RECTS: Record<SlotName, {top: number; left: number; width: number; height: number}> = {
  HEADER: {top: SAFE_TOP, left: 60, width: 960, height: 180},
  STAGE_A: {top: BEAT_ZONE.top, left: 60, width: 960, height: 540},
  STAGE_B: {top: 840, left: 60, width: 960, height: 540},
  FULL_STAGE: {top: BEAT_ZONE.top, left: 40, width: 1000, height: BEAT_ZONE.bottom - BEAT_ZONE.top},
  CAPTION: {top: CAPTION_ZONE.top, left: CAPTION_ZONE.left, width: 1000, height: CAPTION_ZONE.bottom - CAPTION_ZONE.top},
};

/**
 * Wraps a visual element or bespoke TSX scene in a named slot container (`data-slot`)
 * with optional overflow clipping so it cannot spill into the CAPTION zone.
 */
export const SlotContainer: React.FC<{
  slot: SlotName;
  clip?: boolean;
  fullCanvas?: boolean;
  zIndex?: number;
  children: React.ReactNode;
}> = ({slot, clip = false, fullCanvas = false, zIndex, children}) => {
  const r = SLOT_RECTS[slot];
  const style: React.CSSProperties = fullCanvas
    ? {
        position: 'absolute',
        top: 0,
        left: 0,
        width: 1080,
        height: CAPTION_ZONE.top - 20, // strict boundary above captions (y < 1400)
        overflow: clip ? 'hidden' : 'visible',
        zIndex,
      }
    : {
        position: 'absolute',
        top: r.top,
        left: r.left,
        width: r.width,
        height: r.height,
        overflow: clip ? 'hidden' : 'visible',
        zIndex,
      };
  return (
    <div data-slot={slot} style={style}>
      {children}
    </div>
  );
};
