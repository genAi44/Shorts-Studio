// AUTO-GENERATED FROM spec_schema.json BY scripts/generate_schema.py — DO NOT EDIT MANUALLY
import {z} from 'zod';

// 1. Icon Visual Spec
export const IconAnimationPresetSchema = z.enum(['none', 'draw', 'pop', 'float', 'pulse', 'rotate']);
export type IconAnimationPreset = z.infer<typeof IconAnimationPresetSchema>;

export const IconVisualSpecSchema = z.object({
  name: z.string().min(1),
  size: z.number().min(16).max(512).default(96),
  color: z.string().optional(),
  strokeWidth: z.number().min(0.5).max(8).default(2.2),
  animation: IconAnimationPresetSchema.default('pop'),
  label: z.string().optional(),
});
export type IconVisualSpec = z.infer<typeof IconVisualSpecSchema>;

// 2. Emoji Visual Spec
export const EmojiAnimationPresetSchema = z.enum(['none', 'bounce', 'pop', 'shake', 'spin']);
export type EmojiAnimationPreset = z.infer<typeof EmojiAnimationPresetSchema>;

export const EmojiVisualSpecSchema = z.object({
  char: z.string().min(1),
  size: z.number().min(16).max(512).default(96),
  animation: EmojiAnimationPresetSchema.default('pop'),
  label: z.string().optional(),
});
export type EmojiVisualSpec = z.infer<typeof EmojiVisualSpecSchema>;

// 3. Flag Visual Spec
export const FlagShapeSchema = z.enum(['rect', 'round']);
export type FlagShape = z.infer<typeof FlagShapeSchema>;

export const FlagVisualSpecSchema = z.object({
  code: z.string().min(2),
  shape: FlagShapeSchema.default('rect'),
  size: z.number().min(20).max(512).default(96),
  animation: z.enum(['none', 'pop', 'float', 'wave']).default('pop'),
  label: z.string().optional(),
});
export type FlagVisualSpec = z.infer<typeof FlagVisualSpecSchema>;

// 4. Lottie Visual Spec
export const LottieVisualSpecSchema = z.object({
  name: z.string().min(1),
  size: z.number().min(24).max(800).default(180),
  loop: z.boolean().default(true),
  playbackRate: z.number().min(0.1).max(4).default(1),
  label: z.string().optional(),
});
export type LottieVisualSpec = z.infer<typeof LottieVisualSpecSchema>;

// 5. Animated Charts & Counters (`draw_chart` tool schema)
export const ChartDataPointSchema = z.object({
  label: z.string(),
  value: z.number(),
  color: z.string().optional(),
  sub: z.string().optional(),
  year: z.string().optional(),
});
export type ChartDataPoint = z.infer<typeof ChartDataPointSchema>;

export const ChartStyleSchema = z.object({
  title: z.string().optional(),
  subtitle: z.string().optional(),
  unit: z.string().optional(),
  rtl: z.boolean().default(true),
  arabicNumerals: z.boolean().default(false),
  accentColor: z.string().optional(),
  secondaryColor: z.string().optional(),
  donutInnerRadiusRatio: z.number().min(0).max(0.85).default(0.55),
  width: z.number().min(200).max(1080).default(900),
  height: z.number().min(160).max(1400).default(640),
});
export type ChartStyle = z.infer<typeof ChartStyleSchema>;

export const DrawChartSchema = z.object({
  type: z.enum(['bar', 'line', 'pie', 'donut', 'counter', 'progress_ring', 'timeline']),
  data: z.array(ChartDataPointSchema).min(1).max(12),
  style: ChartStyleSchema.default({}),
  animation: z.enum(['spring', 'grow', 'draw', 'stagger']).default('spring'),
  durationInFrames: z.number().int().min(15).max(600).default(90),
});
export type DrawChartInput = z.infer<typeof DrawChartSchema>;

// 6. Reusable Typography & Layout Components
export const TypographyComponentSpecSchema = z.object({
  component: z.enum([
    'lower_third',
    'title_card',
    'quote_card',
    'bullet_list',
    'stat_callout',
    'caption_style',
    'animated_headline',
  ]),
  title: z.string().optional(),
  subtitle: z.string().optional(),
  quote: z.string().optional(),
  author: z.string().optional(),
  items: z.array(z.string()).optional(),
  value: z.string().optional(),
  unit: z.string().optional(),
  captionMode: z.enum(['word-highlight', 'karaoke', 'pop']).optional(),
  fontPairing: z.enum(['cairo_inter', 'kufi_montserrat', 'tajawal_inter', 'amiri_classic']).default('cairo_inter'),
  rtl: z.boolean().default(true),
  arabicNumerals: z.boolean().default(false),
});
export type TypographyComponentSpec = z.infer<typeof TypographyComponentSpecSchema>;

// 7. Unified Scene/Beat Visual Element (`visuals: [{ kind, spec }]`)
export const VisualPlacementSchema = z.enum([
  'center',
  'top-right',
  'top-left',
  'bottom-right',
  'bottom-left',
  'badge-row',
  'hero',
]);
export type VisualPlacement = z.infer<typeof VisualPlacementSchema>;

export const VisualElementSchema = z.discriminatedUnion('kind', [
  z.object({
    kind: z.literal('icon'),
    spec: IconVisualSpecSchema,
    placement: VisualPlacementSchema.optional(),
    x: z.number().optional(),
    y: z.number().optional(),
    from: z.number().optional(),
    to: z.number().optional(),
  }),
  z.object({
    kind: z.literal('emoji'),
    spec: EmojiVisualSpecSchema,
    placement: VisualPlacementSchema.optional(),
    x: z.number().optional(),
    y: z.number().optional(),
    from: z.number().optional(),
    to: z.number().optional(),
  }),
  z.object({
    kind: z.literal('flag'),
    spec: FlagVisualSpecSchema,
    placement: VisualPlacementSchema.optional(),
    x: z.number().optional(),
    y: z.number().optional(),
    from: z.number().optional(),
    to: z.number().optional(),
  }),
  z.object({
    kind: z.literal('lottie'),
    spec: LottieVisualSpecSchema,
    placement: VisualPlacementSchema.optional(),
    x: z.number().optional(),
    y: z.number().optional(),
    from: z.number().optional(),
    to: z.number().optional(),
  }),
  z.object({
    kind: z.literal('chart'),
    spec: DrawChartSchema,
    placement: VisualPlacementSchema.optional(),
    x: z.number().optional(),
    y: z.number().optional(),
    from: z.number().optional(),
    to: z.number().optional(),
  }),
  z.object({
    kind: z.literal('component'),
    spec: TypographyComponentSpecSchema,
    placement: VisualPlacementSchema.optional(),
    x: z.number().optional(),
    y: z.number().optional(),
    from: z.number().optional(),
    to: z.number().optional(),
  }),
]);
export type VisualElement = z.infer<typeof VisualElementSchema>;

// 8. Generative Canvas & Motion Primitives Spec
export const GenerativeElementSchema = z.object({
  id: z.string().optional(),
  type: z.enum([
    'shape',
    'path',
    'badge',
    'counter',
    'gauge',
    'connector',
    'text',
    'icon',
    'emoji',
    'flag',
    'lottie',
  ]),
  x: z.number().min(0).max(1080).optional(),
  y: z.number().min(0).max(1920).optional(),
  delay: z.number().min(0).max(600).optional(),
  duration: z.number().min(0).max(600).optional(),
  motion: z.enum(['pop', 'rise', 'drop', 'fade', 'scale', 'draw', 'slide_right', 'slide_left', 'none']).optional(),
  loop: z.enum(['float', 'pulse', 'spin', 'glow', 'breathe', 'shake', 'none']).optional(),
  opacity: z.number().min(0).max(1).optional(),
  zIndex: z.number().optional(),
}).passthrough();

export const GenerativeCanvasBeatSchema = z.object({
  kind: z.literal('generative_canvas'),
  title: z.string().optional(),
  subtitle: z.string().optional(),
  background: z.string().optional(),
  accent: z.string().optional(),
  grid: z.union([z.boolean(), z.enum(['dots', 'lines', 'radar'])]).optional(),
  elements: z.array(GenerativeElementSchema).default([]),
}).passthrough();

// 9. Scene Transition Spec
export const SceneTransitionSpecSchema = z.object({
  type: z.enum(['fade', 'slide', 'wipe', 'flip', 'clock-wipe', 'none']).default('fade'),
  direction: z.enum(['from-right', 'from-left', 'from-top', 'from-bottom']).optional(),
  durationInFrames: z.number().int().min(6).max(45).default(14),
  sfx: z.enum(['none', 'whoosh', 'whip', 'pageTurn', 'switch', 'ding']).default('none'),
});
export type SceneTransitionSpec = z.infer<typeof SceneTransitionSpecSchema>;

// 10. Unified Beat Schemas Generated from spec_schema.json
export const BeatKindSchema = z.enum(['generative_canvas', 'custom_scene', 'map', 'map_pin', 'photo', 'stat', 'stat_ring_v2', 'bigtext', 'bars', 'timeline', 'timeline_card', 'versus', 'split', 'list', 'icons', 'canvas', 'ticker', 'cardstack', 'elevation_profile', 'line_chart', 'pie_chart', 'versus_battle', 'animated_route', 'balance_meter', 'deep_time_slider', 'stack_pyramid', 'macro_zoom_globe', 'subsurface_mine', 'dot_matrix_population', 'money_waterfall', 'frontline_clash', 'chart', 'typography', 'visuals', 'city_skyline', 'architecture', 'mystery_scene', 'architectural_blueprint', 'celestial_constellation', 'cinematic_dramatic', 'kinetic_wave_field', 'radial_light_cathedral', 'topographic_contour', 'year_counter', 'person_card']);
export type BeatKind = z.infer<typeof BeatKindSchema>;

export const CommonBeatFieldsSchema = z.object({
  id: z.string().optional(),
  from: z.number().optional(),
  dur: z.number().optional(),
  title: z.string().optional(),
  subtitle: z.string().optional(),
  camera: z.string().optional(),
  settled: z.boolean().optional(),
  cues: z.array(z.any()).optional(),
  visuals: z.array(z.any()).optional(),
  scene_spec: z.record(z.string(), z.any()).optional(),
  svg_layers: z.array(z.any()).optional(),
  environment: z.string().optional(),
  narration_cues: z.array(z.any()).optional(),
  tsx_id: z.string().optional(),
  concept: z.string().optional(),
  narration: z.string().optional(),
  video_title: z.string().optional(),
  facts_summary: z.string().optional(),
  video_countries: z.array(z.any()).optional(),
  video_cities: z.array(z.any()).optional(),
  accent: z.string().optional(),
  secondary_accent: z.string().optional(),
  countries: z.array(z.any()).optional(),
  highlight: z.array(z.any()).optional(),
  points: z.array(z.any()).optional(),
  _fallback: z.boolean().optional(),
  hide: z.array(z.any()).optional(),
  _entity: z.string().optional(),
  img: z.string().optional(),
});

export const Beat_generative_canvas_Schema = CommonBeatFieldsSchema.extend({
  kind: z.literal('generative_canvas'),
  background: z.string().optional(),
  bg_mood: z.string().optional(),
  accent: z.string().optional(),
  secondary_accent: z.string().optional(),
  grid: z.any().optional(),
  environment: z.string().optional(),
  elements: z.array(z.any()),
  svg_layers: z.array(z.any()).optional(),
  scene_spec: z.record(z.string(), z.any()).optional(),
  narration_cues: z.array(z.any()).optional(),
  tsx_id: z.string().optional(),
}).strict();
export const Beat_custom_scene_Schema = CommonBeatFieldsSchema.extend({
  kind: z.literal('custom_scene'),
  background: z.string().optional(),
  bg_mood: z.string().optional(),
  accent: z.string().optional(),
  secondary_accent: z.string().optional(),
  approach: z.string().optional(),
  environment: z.string().optional(),
  elements: z.array(z.any()).optional(),
  svg_layers: z.array(z.any()).optional(),
  scene_spec: z.record(z.string(), z.any()),
  narration_cues: z.array(z.any()).optional(),
  tsx_id: z.string().optional(),
}).strict();
export const Beat_map_Schema = CommonBeatFieldsSchema.extend({
  kind: z.literal('map'),
  countries: z.array(z.any()).optional(),
  highlight: z.array(z.any()).optional(),
  points: z.array(z.any()).optional(),
  view: z.record(z.string(), z.any()).optional(),
  region: z.string().optional(),
}).strict();
export const Beat_map_pin_Schema = CommonBeatFieldsSchema.extend({
  kind: z.literal('map_pin'),
  region: z.string().optional(),
  points: z.array(z.any()),
  view: z.record(z.string(), z.any()).optional(),
}).strict();
export const Beat_photo_Schema = CommonBeatFieldsSchema.extend({
  kind: z.literal('photo'),
  query: z.string(),
  text: z.string().optional(),
  cutout: z.boolean().optional(),
  number: z.string().optional(),
  must_show: z.string().optional(),
  avoid: z.string().optional(),
  alt_queries: z.array(z.any()).optional(),
  img: z.string().optional(),
  cut: z.boolean().optional(),
}).strict();
export const Beat_stat_Schema = CommonBeatFieldsSchema.extend({
  kind: z.literal('stat'),
  number: z.string(),
  label: z.string().optional(),
  layout: z.string().optional(),
}).strict();
export const Beat_stat_ring_v2_Schema = CommonBeatFieldsSchema.extend({
  kind: z.literal('stat_ring_v2'),
  number: z.string(),
  label: z.string().optional(),
  icon: z.string().optional(),
  hero_icon: z.string().optional(),
}).strict();
export const Beat_bigtext_Schema = CommonBeatFieldsSchema.extend({
  kind: z.literal('bigtext'),
  text: z.string(),
  sub: z.string().optional(),
  layout: z.string().optional(),
}).strict();
export const Beat_bars_Schema = CommonBeatFieldsSchema.extend({
  kind: z.literal('bars'),
  items: z.array(z.any()),
}).strict();
export const Beat_timeline_Schema = CommonBeatFieldsSchema.extend({
  kind: z.literal('timeline'),
  items: z.array(z.any()),
}).strict();
export const Beat_timeline_card_Schema = CommonBeatFieldsSchema.extend({
  kind: z.literal('timeline_card'),
  items: z.array(z.any()),
}).strict();
export const Beat_versus_Schema = CommonBeatFieldsSchema.extend({
  kind: z.literal('versus'),
  left: z.record(z.string(), z.any()),
  right: z.record(z.string(), z.any()),
}).strict();
export const Beat_split_Schema = CommonBeatFieldsSchema.extend({
  kind: z.literal('split'),
  left: z.record(z.string(), z.any()),
  right: z.record(z.string(), z.any()),
}).strict();
export const Beat_list_Schema = CommonBeatFieldsSchema.extend({
  kind: z.literal('list'),
  items: z.array(z.any()),
}).strict();
export const Beat_icons_Schema = CommonBeatFieldsSchema.extend({
  kind: z.literal('icons'),
  items: z.array(z.any()),
  badges: z.array(z.any()).optional(),
  hero_icon: z.string().optional(),
  center_label: z.string().optional(),
  icon: z.string().optional(),
  text: z.string().optional(),
  sub: z.string().optional(),
}).strict();
export const Beat_canvas_Schema = CommonBeatFieldsSchema.extend({
  kind: z.literal('canvas'),
  elements: z.array(z.any()),
}).strict();
export const Beat_ticker_Schema = CommonBeatFieldsSchema.extend({
  kind: z.literal('ticker'),
  items: z.array(z.any()),
}).strict();
export const Beat_cardstack_Schema = CommonBeatFieldsSchema.extend({
  kind: z.literal('cardstack'),
  items: z.array(z.any()),
}).strict();
export const Beat_elevation_profile_Schema = CommonBeatFieldsSchema.extend({
  kind: z.literal('elevation_profile'),
  capital: z.string().optional(),
  height: z.string(),
  unit: z.string().optional(),
  sea_label: z.string().optional(),
  country: z.string().optional(),
  peak_name: z.string().optional(),
}).strict();
export const Beat_line_chart_Schema = CommonBeatFieldsSchema.extend({
  kind: z.literal('line_chart'),
  points: z.array(z.any()),
  y_label: z.string().optional(),
  unit: z.string().optional(),
}).strict();
export const Beat_pie_chart_Schema = CommonBeatFieldsSchema.extend({
  kind: z.literal('pie_chart'),
  items: z.array(z.any()),
}).strict();
export const Beat_versus_battle_Schema = CommonBeatFieldsSchema.extend({
  kind: z.literal('versus_battle'),
  right: z.record(z.string(), z.any()).optional(),
  left: z.record(z.string(), z.any()).optional(),
  result_badge: z.string().optional(),
  sub: z.string().optional(),
}).strict();
export const Beat_animated_route_Schema = CommonBeatFieldsSchema.extend({
  kind: z.literal('animated_route'),
  from_city: z.string().optional(),
  to_city: z.string().optional(),
  distance: z.string().optional(),
  duration_label: z.string().optional(),
  terrain: z.string().optional(),
  sub: z.string().optional(),
  points: z.array(z.any()).optional(),
}).strict();
export const Beat_balance_meter_Schema = CommonBeatFieldsSchema.extend({
  kind: z.literal('balance_meter'),
  right_label: z.string().optional(),
  left_label: z.string().optional(),
  right_weight: z.number().optional(),
  left_weight: z.number().optional(),
  verdict: z.string().optional(),
  sub: z.string().optional(),
  left: z.record(z.string(), z.any()).optional(),
  right: z.record(z.string(), z.any()).optional(),
}).strict();
export const Beat_deep_time_slider_Schema = CommonBeatFieldsSchema.extend({
  kind: z.literal('deep_time_slider'),
  from_year: z.string().optional(),
  to_year: z.string().optional(),
  era_label: z.string().optional(),
  milestone: z.string().optional(),
  span_years: z.string().optional(),
  sub: z.string().optional(),
  items: z.array(z.any()).optional(),
}).strict();
export const Beat_stack_pyramid_Schema = CommonBeatFieldsSchema.extend({
  kind: z.literal('stack_pyramid'),
  tiers: z.array(z.any()).optional(),
  items: z.array(z.any()).optional(),
  sub: z.string().optional(),
}).strict();
export const Beat_macro_zoom_globe_Schema = CommonBeatFieldsSchema.extend({
  kind: z.literal('macro_zoom_globe'),
  region_label: z.string().optional(),
  city_label: z.string().optional(),
  coords: z.string().optional(),
  stat_badge: z.string().optional(),
  sub: z.string().optional(),
  countries: z.array(z.any()).optional(),
  points: z.array(z.any()).optional(),
}).strict();
export const Beat_subsurface_mine_Schema = CommonBeatFieldsSchema.extend({
  kind: z.literal('subsurface_mine'),
  depth: z.string().optional(),
  mineral: z.string().optional(),
  layers: z.array(z.any()).optional(),
  temp: z.string().optional(),
  sub: z.string().optional(),
}).strict();
export const Beat_dot_matrix_population_Schema = CommonBeatFieldsSchema.extend({
  kind: z.literal('dot_matrix_population'),
  total_dots: z.number().optional(),
  highlighted_dots: z.number().optional(),
  ratio_label: z.string().optional(),
  group_a: z.string().optional(),
  group_b: z.string().optional(),
  sub: z.string().optional(),
  number: z.string().optional(),
  label: z.string().optional(),
}).strict();
export const Beat_money_waterfall_Schema = CommonBeatFieldsSchema.extend({
  kind: z.literal('money_waterfall'),
  amount: z.string().optional(),
  direction: z.string().optional(),
  cause: z.string().optional(),
  impact_pct: z.string().optional(),
  sub: z.string().optional(),
  number: z.string().optional(),
  label: z.string().optional(),
}).strict();
export const Beat_frontline_clash_Schema = CommonBeatFieldsSchema.extend({
  kind: z.literal('frontline_clash'),
  side_a: z.string().optional(),
  side_b: z.string().optional(),
  location: z.string().optional(),
  year: z.string().optional(),
  outcome: z.string().optional(),
  sub: z.string().optional(),
  left: z.record(z.string(), z.any()).optional(),
  right: z.record(z.string(), z.any()).optional(),
}).strict();
export const Beat_chart_Schema = CommonBeatFieldsSchema.extend({
  kind: z.literal('chart'),
  spec: z.record(z.string(), z.any()).optional(),
  items: z.array(z.any()).optional(),
}).strict();
export const Beat_typography_Schema = CommonBeatFieldsSchema.extend({
  kind: z.literal('typography'),
  spec: z.record(z.string(), z.any()).optional(),
  text: z.string().optional(),
  sub: z.string().optional(),
}).strict();
export const Beat_visuals_Schema = CommonBeatFieldsSchema.extend({
  kind: z.literal('visuals'),
  visuals: z.array(z.any()),
}).strict();
export const Beat_city_skyline_Schema = CommonBeatFieldsSchema.extend({
  kind: z.literal('city_skyline'),
  title: z.string().optional(),
  subtitle: z.string().optional(),
  text: z.string().optional(),
  seed: z.number().optional(),
}).strict();
export const Beat_architecture_Schema = CommonBeatFieldsSchema.extend({
  kind: z.literal('architecture'),
  title: z.string().optional(),
  subtitle: z.string().optional(),
  era: z.string().optional(),
  seed: z.number().optional(),
}).strict();
export const Beat_mystery_scene_Schema = CommonBeatFieldsSchema.extend({
  kind: z.literal('mystery_scene'),
  question: z.string().optional(),
  text: z.string().optional(),
  subtitle: z.string().optional(),
  variant: z.number().optional(),
  seed: z.number().optional(),
}).strict();
export const Beat_architectural_blueprint_Schema = CommonBeatFieldsSchema.extend({
  kind: z.literal('architectural_blueprint'),
  background: z.string().optional(),
  bg_mood: z.string().optional(),
  accent: z.string().optional(),
  secondary_accent: z.string().optional(),
  approach: z.string().optional(),
  environment: z.string().optional(),
  elements: z.array(z.any()).optional(),
  svg_layers: z.array(z.any()).optional(),
  scene_spec: z.record(z.string(), z.any()).optional(),
  narration_cues: z.array(z.any()).optional(),
  tsx_id: z.string().optional(),
}).strict();
export const Beat_celestial_constellation_Schema = CommonBeatFieldsSchema.extend({
  kind: z.literal('celestial_constellation'),
  background: z.string().optional(),
  bg_mood: z.string().optional(),
  accent: z.string().optional(),
  secondary_accent: z.string().optional(),
  approach: z.string().optional(),
  environment: z.string().optional(),
  elements: z.array(z.any()).optional(),
  svg_layers: z.array(z.any()).optional(),
  scene_spec: z.record(z.string(), z.any()).optional(),
  narration_cues: z.array(z.any()).optional(),
  tsx_id: z.string().optional(),
}).strict();
export const Beat_cinematic_dramatic_Schema = CommonBeatFieldsSchema.extend({
  kind: z.literal('cinematic_dramatic'),
  background: z.string().optional(),
  bg_mood: z.string().optional(),
  accent: z.string().optional(),
  secondary_accent: z.string().optional(),
  approach: z.string().optional(),
  environment: z.string().optional(),
  elements: z.array(z.any()).optional(),
  svg_layers: z.array(z.any()).optional(),
  scene_spec: z.record(z.string(), z.any()).optional(),
  narration_cues: z.array(z.any()).optional(),
  tsx_id: z.string().optional(),
}).strict();
export const Beat_kinetic_wave_field_Schema = CommonBeatFieldsSchema.extend({
  kind: z.literal('kinetic_wave_field'),
  background: z.string().optional(),
  bg_mood: z.string().optional(),
  accent: z.string().optional(),
  secondary_accent: z.string().optional(),
  approach: z.string().optional(),
  environment: z.string().optional(),
  elements: z.array(z.any()).optional(),
  svg_layers: z.array(z.any()).optional(),
  scene_spec: z.record(z.string(), z.any()).optional(),
  narration_cues: z.array(z.any()).optional(),
  tsx_id: z.string().optional(),
}).strict();
export const Beat_radial_light_cathedral_Schema = CommonBeatFieldsSchema.extend({
  kind: z.literal('radial_light_cathedral'),
  background: z.string().optional(),
  bg_mood: z.string().optional(),
  accent: z.string().optional(),
  secondary_accent: z.string().optional(),
  approach: z.string().optional(),
  environment: z.string().optional(),
  elements: z.array(z.any()).optional(),
  svg_layers: z.array(z.any()).optional(),
  scene_spec: z.record(z.string(), z.any()).optional(),
  narration_cues: z.array(z.any()).optional(),
  tsx_id: z.string().optional(),
}).strict();
export const Beat_topographic_contour_Schema = CommonBeatFieldsSchema.extend({
  kind: z.literal('topographic_contour'),
  background: z.string().optional(),
  bg_mood: z.string().optional(),
  accent: z.string().optional(),
  secondary_accent: z.string().optional(),
  approach: z.string().optional(),
  environment: z.string().optional(),
  elements: z.array(z.any()).optional(),
  svg_layers: z.array(z.any()).optional(),
  scene_spec: z.record(z.string(), z.any()).optional(),
  narration_cues: z.array(z.any()).optional(),
  tsx_id: z.string().optional(),
}).strict();
export const Beat_year_counter_Schema = CommonBeatFieldsSchema.extend({
  kind: z.literal('year_counter'),
  year: z.number(),
  to_year: z.number().optional(),
  era: z.string().optional(),
  label: z.string().optional(),
  title: z.string().optional(),
}).strict();
export const Beat_person_card_Schema = CommonBeatFieldsSchema.extend({
  kind: z.literal('person_card'),
  name: z.string(),
  years: z.string().optional(),
  role: z.string().optional(),
  query: z.string().optional(),
  img: z.string().optional(),
  title: z.string().optional(),
}).strict();

export const StrictBeatSchema = z.discriminatedUnion('kind', [
  Beat_generative_canvas_Schema,
  Beat_custom_scene_Schema,
  Beat_map_Schema,
  Beat_map_pin_Schema,
  Beat_photo_Schema,
  Beat_stat_Schema,
  Beat_stat_ring_v2_Schema,
  Beat_bigtext_Schema,
  Beat_bars_Schema,
  Beat_timeline_Schema,
  Beat_timeline_card_Schema,
  Beat_versus_Schema,
  Beat_split_Schema,
  Beat_list_Schema,
  Beat_icons_Schema,
  Beat_canvas_Schema,
  Beat_ticker_Schema,
  Beat_cardstack_Schema,
  Beat_elevation_profile_Schema,
  Beat_line_chart_Schema,
  Beat_pie_chart_Schema,
  Beat_versus_battle_Schema,
  Beat_animated_route_Schema,
  Beat_balance_meter_Schema,
  Beat_deep_time_slider_Schema,
  Beat_stack_pyramid_Schema,
  Beat_macro_zoom_globe_Schema,
  Beat_subsurface_mine_Schema,
  Beat_dot_matrix_population_Schema,
  Beat_money_waterfall_Schema,
  Beat_frontline_clash_Schema,
  Beat_chart_Schema,
  Beat_typography_Schema,
  Beat_visuals_Schema,
  Beat_city_skyline_Schema,
  Beat_architecture_Schema,
  Beat_mystery_scene_Schema,
  Beat_architectural_blueprint_Schema,
  Beat_celestial_constellation_Schema,
  Beat_cinematic_dramatic_Schema,
  Beat_kinetic_wave_field_Schema,
  Beat_radial_light_cathedral_Schema,
  Beat_topographic_contour_Schema,
  Beat_year_counter_Schema,
  Beat_person_card_Schema,
]);
export type GeneratedBeatSpec = z.infer<typeof StrictBeatSchema>;
