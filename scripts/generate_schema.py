"""Build Script (`scripts/generate_schema.py`).

Generates `remotion/src/schema.ts` from `spec_schema.json` at the project root
so Python (`validate_beat`) and TypeScript (`remotion/src/schema.ts`) share a
single source of truth for every beat kind, field, and type.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC_SCHEMA_PATH = ROOT / "spec_schema.json"
TS_OUT_PATH = ROOT / "remotion" / "src" / "schema.ts"

ZOD_MAP = {
    "string": "z.string()",
    "number": "z.number()",
    "boolean": "z.boolean()",
    "array": "z.array(z.any())",
    "object": "z.record(z.string(), z.any())",
    "any": "z.any()",
}


def generate_schema_ts() -> str:
    schema = json.loads(SPEC_SCHEMA_PATH.read_text(encoding="utf-8"))
    common_fields: dict[str, str] = schema.get("common_fields", {})
    beats: dict[str, dict] = schema.get("beats", {})

    lines = [
        "// AUTO-GENERATED FROM spec_schema.json BY scripts/generate_schema.py — DO NOT EDIT MANUALLY",
        "import {z} from 'zod';",
        "",
        "// 1. Icon Visual Spec",
        "export const IconAnimationPresetSchema = z.enum(['none', 'draw', 'pop', 'float', 'pulse', 'rotate']);",
        "export type IconAnimationPreset = z.infer<typeof IconAnimationPresetSchema>;",
        "",
        "export const IconVisualSpecSchema = z.object({",
        "  name: z.string().min(1),",
        "  size: z.number().min(16).max(512).default(96),",
        "  color: z.string().optional(),",
        "  strokeWidth: z.number().min(0.5).max(8).default(2.2),",
        "  animation: IconAnimationPresetSchema.default('pop'),",
        "  label: z.string().optional(),",
        "});",
        "export type IconVisualSpec = z.infer<typeof IconVisualSpecSchema>;",
        "",
        "// 2. Emoji Visual Spec",
        "export const EmojiAnimationPresetSchema = z.enum(['none', 'bounce', 'pop', 'shake', 'spin']);",
        "export type EmojiAnimationPreset = z.infer<typeof EmojiAnimationPresetSchema>;",
        "",
        "export const EmojiVisualSpecSchema = z.object({",
        "  char: z.string().min(1),",
        "  size: z.number().min(16).max(512).default(96),",
        "  animation: EmojiAnimationPresetSchema.default('pop'),",
        "  label: z.string().optional(),",
        "});",
        "export type EmojiVisualSpec = z.infer<typeof EmojiVisualSpecSchema>;",
        "",
        "// 3. Flag Visual Spec",
        "export const FlagShapeSchema = z.enum(['rect', 'round']);",
        "export type FlagShape = z.infer<typeof FlagShapeSchema>;",
        "",
        "export const FlagVisualSpecSchema = z.object({",
        "  code: z.string().min(2),",
        "  shape: FlagShapeSchema.default('rect'),",
        "  size: z.number().min(20).max(512).default(96),",
        "  animation: z.enum(['none', 'pop', 'float', 'wave']).default('pop'),",
        "  label: z.string().optional(),",
        "});",
        "export type FlagVisualSpec = z.infer<typeof FlagVisualSpecSchema>;",
        "",
        "// 4. Lottie Visual Spec",
        "export const LottieVisualSpecSchema = z.object({",
        "  name: z.string().min(1),",
        "  size: z.number().min(24).max(800).default(180),",
        "  loop: z.boolean().default(true),",
        "  playbackRate: z.number().min(0.1).max(4).default(1),",
        "  label: z.string().optional(),",
        "});",
        "export type LottieVisualSpec = z.infer<typeof LottieVisualSpecSchema>;",
        "",
        "// 5. Animated Charts & Counters (`draw_chart` tool schema)",
        "export const ChartDataPointSchema = z.object({",
        "  label: z.string(),",
        "  value: z.number(),",
        "  color: z.string().optional(),",
        "  sub: z.string().optional(),",
        "  year: z.string().optional(),",
        "});",
        "export type ChartDataPoint = z.infer<typeof ChartDataPointSchema>;",
        "",
        "export const ChartStyleSchema = z.object({",
        "  title: z.string().optional(),",
        "  subtitle: z.string().optional(),",
        "  unit: z.string().optional(),",
        "  rtl: z.boolean().default(true),",
        "  arabicNumerals: z.boolean().default(false),",
        "  accentColor: z.string().optional(),",
        "  secondaryColor: z.string().optional(),",
        "  donutInnerRadiusRatio: z.number().min(0).max(0.85).default(0.55),",
        "  width: z.number().min(200).max(1080).default(900),",
        "  height: z.number().min(160).max(1400).default(640),",
        "});",
        "export type ChartStyle = z.infer<typeof ChartStyleSchema>;",
        "",
        "export const DrawChartSchema = z.object({",
        "  type: z.enum(['bar', 'line', 'pie', 'donut', 'counter', 'progress_ring', 'timeline']),",
        "  data: z.array(ChartDataPointSchema).min(1).max(12),",
        "  style: ChartStyleSchema.default({}),",
        "  animation: z.enum(['spring', 'grow', 'draw', 'stagger']).default('spring'),",
        "  durationInFrames: z.number().int().min(15).max(600).default(90),",
        "});",
        "export type DrawChartInput = z.infer<typeof DrawChartSchema>;",
        "",
        "// 6. Reusable Typography & Layout Components",
        "export const TypographyComponentSpecSchema = z.object({",
        "  component: z.enum([",
        "    'lower_third',",
        "    'title_card',",
        "    'quote_card',",
        "    'bullet_list',",
        "    'stat_callout',",
        "    'caption_style',",
        "    'animated_headline',",
        "  ]),",
        "  title: z.string().optional(),",
        "  subtitle: z.string().optional(),",
        "  quote: z.string().optional(),",
        "  author: z.string().optional(),",
        "  items: z.array(z.string()).optional(),",
        "  value: z.string().optional(),",
        "  unit: z.string().optional(),",
        "  captionMode: z.enum(['word-highlight', 'karaoke', 'pop']).optional(),",
        "  fontPairing: z.enum(['cairo_inter', 'kufi_montserrat', 'tajawal_inter', 'amiri_classic']).default('cairo_inter'),",
        "  rtl: z.boolean().default(true),",
        "  arabicNumerals: z.boolean().default(false),",
        "});",
        "export type TypographyComponentSpec = z.infer<typeof TypographyComponentSpecSchema>;",
        "",
        "// 7. Unified Scene/Beat Visual Element (`visuals: [{ kind, spec }]`)",
        "export const VisualPlacementSchema = z.enum([",
        "  'center',",
        "  'top-right',",
        "  'top-left',",
        "  'bottom-right',",
        "  'bottom-left',",
        "  'badge-row',",
        "  'hero',",
        "]);",
        "export type VisualPlacement = z.infer<typeof VisualPlacementSchema>;",
        "",
        "export const VisualElementSchema = z.discriminatedUnion('kind', [",
        "  z.object({",
        "    kind: z.literal('icon'),",
        "    spec: IconVisualSpecSchema,",
        "    placement: VisualPlacementSchema.optional(),",
        "    x: z.number().optional(),",
        "    y: z.number().optional(),",
        "  }),",
        "  z.object({",
        "    kind: z.literal('emoji'),",
        "    spec: EmojiVisualSpecSchema,",
        "    placement: VisualPlacementSchema.optional(),",
        "    x: z.number().optional(),",
        "    y: z.number().optional(),",
        "  }),",
        "  z.object({",
        "    kind: z.literal('flag'),",
        "    spec: FlagVisualSpecSchema,",
        "    placement: VisualPlacementSchema.optional(),",
        "    x: z.number().optional(),",
        "    y: z.number().optional(),",
        "  }),",
        "  z.object({",
        "    kind: z.literal('lottie'),",
        "    spec: LottieVisualSpecSchema,",
        "    placement: VisualPlacementSchema.optional(),",
        "    x: z.number().optional(),",
        "    y: z.number().optional(),",
        "  }),",
        "  z.object({",
        "    kind: z.literal('chart'),",
        "    spec: DrawChartSchema,",
        "    placement: VisualPlacementSchema.optional(),",
        "    x: z.number().optional(),",
        "    y: z.number().optional(),",
        "  }),",
        "  z.object({",
        "    kind: z.literal('component'),",
        "    spec: TypographyComponentSpecSchema,",
        "    placement: VisualPlacementSchema.optional(),",
        "    x: z.number().optional(),",
        "    y: z.number().optional(),",
        "  }),",
        "]);",
        "export type VisualElement = z.infer<typeof VisualElementSchema>;",
        "",
        "// 8. Generative Canvas & Motion Primitives Spec",
        "export const GenerativeElementSchema = z.object({",
        "  id: z.string().optional(),",
        "  type: z.enum([",
        "    'shape',",
        "    'path',",
        "    'badge',",
        "    'counter',",
        "    'gauge',",
        "    'connector',",
        "    'text',",
        "    'icon',",
        "    'emoji',",
        "    'flag',",
        "    'lottie',",
        "  ]),",
        "  x: z.number().min(0).max(1080).optional(),",
        "  y: z.number().min(0).max(1920).optional(),",
        "  delay: z.number().min(0).max(600).optional(),",
        "  duration: z.number().min(0).max(600).optional(),",
        "  motion: z.enum(['pop', 'rise', 'drop', 'fade', 'scale', 'draw', 'slide_right', 'slide_left', 'none']).optional(),",
        "  loop: z.enum(['float', 'pulse', 'spin', 'glow', 'breathe', 'shake', 'none']).optional(),",
        "  opacity: z.number().min(0).max(1).optional(),",
        "  zIndex: z.number().optional(),",
        "}).passthrough();",
        "",
        "export const GenerativeCanvasBeatSchema = z.object({",
        "  kind: z.literal('generative_canvas'),",
        "  title: z.string().optional(),",
        "  subtitle: z.string().optional(),",
        "  background: z.string().optional(),",
        "  accent: z.string().optional(),",
        "  grid: z.union([z.boolean(), z.enum(['dots', 'lines', 'radar'])]).optional(),",
        "  elements: z.array(GenerativeElementSchema).default([]),",
        "}).passthrough();",
        "",
        "// 9. Scene Transition Spec",
        "export const SceneTransitionSpecSchema = z.object({",
        "  type: z.enum(['fade', 'slide', 'wipe', 'flip', 'clock-wipe', 'none']).default('fade'),",
        "  direction: z.enum(['from-right', 'from-left', 'from-top', 'from-bottom']).optional(),",
        "  durationInFrames: z.number().int().min(6).max(45).default(14),",
        "  sfx: z.enum(['none', 'whoosh', 'whip', 'pageTurn', 'switch', 'ding']).default('none'),",
        "});",
        "export type SceneTransitionSpec = z.infer<typeof SceneTransitionSpecSchema>;",
        "",
        "// 10. Unified Beat Schemas Generated from spec_schema.json",
    ]

    kind_literals = ", ".join(f"'{k}'" for k in beats.keys())
    lines.append(f"export const BeatKindSchema = z.enum([{kind_literals}]);")
    lines.append("export type BeatKind = z.infer<typeof BeatKindSchema>;")
    lines.append("")

    lines.append("export const CommonBeatFieldsSchema = z.object({")
    for fname, ftype in common_fields.items():
        if fname == "kind":
            continue
        z_expr = ZOD_MAP.get(ftype, "z.any()")
        lines.append(f"  {fname}: {z_expr}.optional(),")
    lines.append("});")
    lines.append("")

    union_members: list[str] = []
    for bkind, bdef in beats.items():
        req_set = set(bdef.get("required", []))
        fields_map: dict[str, str] = bdef.get("fields", {})
        schema_var = f"Beat_{bkind}_Schema"
        lines.append(f"export const {schema_var} = CommonBeatFieldsSchema.extend({{")
        lines.append(f"  kind: z.literal('{bkind}'),")
        for fname, ftype in fields_map.items():
            z_expr = ZOD_MAP.get(ftype, "z.any()")
            if fname not in req_set:
                z_expr += ".optional()"
            lines.append(f"  {fname}: {z_expr},")
        lines.append("}).strict();")
        union_members.append(schema_var)

    lines.append("")
    lines.append("export const StrictBeatSchema = z.discriminatedUnion('kind', [")
    for m in union_members:
        lines.append(f"  {m},")
    lines.append("]);")
    lines.append("export type GeneratedBeatSpec = z.infer<typeof StrictBeatSchema>;")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    ts_code = generate_schema_ts()
    TS_OUT_PATH.write_text(ts_code, encoding="utf-8")
    print(f"Generated {TS_OUT_PATH.relative_to(ROOT)} from {SPEC_SCHEMA_PATH.name} successfully.")
