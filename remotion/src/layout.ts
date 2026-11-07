/**
 * Central Layout Contract (`remotion/src/layout.ts`).
 *
 * Shared 9:16 (1080x1920) vertical canvas layout zones and coordinates.
 * Must remain 100% identical to `pipeline/layout.py`.
 */

export const CANVAS_WIDTH = 1080;
export const CANVAS_HEIGHT = 1920;

export const SAFE_TOP = 72;
export const SAFE_BOTTOM = 1780;

export const HEADLINE_ZONE = {
  top: 140,
  bottom: 280,
  center_y: 210,
  left: 80,
  right: 80,
} as const;

export const BEAT_ZONE = {
  top: 280,
  bottom: 1380,
  center_y: 860,
  left: 80,
  right: 80,
  title_top: 240,
  sub_title_top: 220,
  chart_title_top: 420,
  corner_top: 240,
  corner_bottom: 1220,
  peak_y: 420,
  sea_y: 1480,
  list_top_with_headline: 440,
  list_top_no_headline: 340,
  zero: 0,
  pin_offset: 20,
  magnifier_bottom: 8,
} as const;

export const CAPTION_ZONE = {
  top: 1420,
  bottom: 1760,
  center_y: 1550,
  left: 40,
  right: 40,
} as const;
