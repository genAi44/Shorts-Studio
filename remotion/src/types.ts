import type {SceneTransitionSpec, VisualElement} from './schema';
import type {MapOverlaySpec} from './mapOverlay';

export type RGB = [number, number, number];
export type Palette = {
  c1: RGB; c2: RGB; accent: RGB; accent2: RGB; text: RGB; ctx: RGB; ctx_edge: RGB; hl: RGB[];
};
export type Style = {
  name: string; seed: number; dark: boolean; font: string; weight: number; palette: Palette;
  bg: {type: string; angle: number; motion: boolean; intensity: number};
  headline: {pos: string; size: number; box: string; enter: string};
  caption: {mode: string; y: number; size: number; hl: string};
  map: {fill: string; edge: number; ctx_alpha: number; marker: string};
  stat: {layout: string};
  text: {layout: string; size: number};
  deco: {frame: string; progress: string};
  pace: number;
  font2: string; weight2: number;
  edit: {photo: string; cutout: string; mixpat: string; shapes: string; ken: string; glow: boolean; blur: boolean; duo: boolean};
};
export type Word = {t: string; s: number; e: number};
export type Beat = {
  kind: string;
  from: number;
  dur: number;
  title?: string;
  settled?: boolean;
  visuals?: VisualElement[];
  [k: string]: any;
};
export type EntitySpan = {
  from: number;
  to: number;
  iso3: string;
  iso2: string;
  kind: string;
  name_ar: string;
  name_en?: string;
  country_ar?: string;
  lat?: number;
  lon?: number;
};
export type SceneSpec = {
  id: string;
  role: 'hook' | 'lead' | 'body' | 'open_loop' | 'cta' | 'loop';
  from: number;
  dur: number;
  words: Word[];
  beats: Beat[];
  visuals?: VisualElement[];
  entities?: EntitySpan[];
  transition?: SceneTransitionSpec;
  map_overlay?: MapOverlaySpec | null;
  visual_mode?: string | null;
  is_historical?: boolean;
  sfx_cue?: string | null;
};
export type Spec = {
  fps: number; width: number; height: number; total: number; audio: string | null; style: Style; scenes: SceneSpec[];
};
export type {SceneTransitionSpec, VisualElement};
