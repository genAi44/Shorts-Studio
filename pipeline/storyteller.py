"""AI-Driven Visual Storyteller & Original Scene Generation Engine (`pipeline/storyteller.py`).

Implements the complete 8-stage creative pipeline:
UNDERSTAND THE STORY
→ IMAGINE THE VISUAL
→ DESIGN THE COMPOSITION
→ DESCRIBE THE SCENE (Sections A–F Visual Scene Specification)
→ GENERATE REACT/TSX (`remotion/src/generated/DynamicScenes.tsx` + custom SVG layers)
→ ANIMATE WITH SVG/CSS
→ RENDER WITH REMOTION
→ REVIEW AND IMPROVE (8-Point Quality Evaluator)
"""
from __future__ import annotations

import hashlib
import json
import logging
import math
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .config import ROOT

# Theme of the video being built (set by generate_dynamic_tsx_file). ponytail: module-level because the prompt
# builder runs in a ThreadPoolExecutor (a ContextVar would not propagate); two simultaneous renders could clash.
_TSX_THEME: Optional[Dict[str, Any]] = None


def _theme_block() -> str:
    t = _TSX_THEME
    if not t:
        return ""
    kind = "dark" if t["dark"] else "LIGHT"
    return (
        "\nVIDEO THEME (this wins over any colour instruction in the system rules): "
        f"the video ground is {kind} {t['ground']} (background type `{t['bg_type']}`) and shows through the scene. "
        "The outer <AbsoluteFill> MUST NOT set any background (no gradient, no full-canvas rect/glow): leave it transparent. "
        f"Free-standing text and strokes use {t['text']}; accents {t['accent']} and {t['accent2']}. "
        f"Every card: background `{t['card_bg']}`, border `1.5px solid {t['card_border']}`, text colour {t['card_text']}. "
        "Never use white text directly on a light ground, nor dark text on a dark ground.\n"
    )


def _theme_sig() -> str:
    t = _TSX_THEME
    return json.dumps(t, sort_keys=True) if t else ""


from .geo import AR_ISO3, detect_city_in_text, get_geo

logger = logging.getLogger("pipeline.storyteller")

DYNAMIC_TSX_PATH = ROOT / "remotion" / "src" / "generated" / "DynamicScenes.tsx"


# ---------------------------------------------------------------------------
# Rich Atmospheric Palettes & Visual Approaches (Never Reused in Same Video)
# ---------------------------------------------------------------------------

SCENE_PALETTES: List[Dict[str, str]] = [
    {
        "name": "cyber_emerald_horizon",
        "bg_top": "#041f1e",
        "bg_mid": "#062c30",
        "bg_bottom": "#021014",
        "primary": "#10b981",
        "secondary": "#38bdf8",
        "highlight": "#fde047",
        "surface": "rgba(6, 44, 48, 0.86)",
        "lighting": "radial-top-right",
    },
    {
        "name": "imperial_amber_citadel",
        "bg_top": "#23120b",
        "bg_mid": "#1a0f1e",
        "bg_bottom": "#0b0711",
        "primary": "#f59e0b",
        "secondary": "#fb7185",
        "highlight": "#fef08a",
        "surface": "rgba(35, 18, 11, 0.88)",
        "lighting": "spotlight-center",
    },
    {
        "name": "cobalt_orbital_observatory",
        "bg_top": "#0b1938",
        "bg_mid": "#132347",
        "bg_bottom": "#060d1f",
        "primary": "#38bdf8",
        "secondary": "#818cf8",
        "highlight": "#2dd4bf",
        "surface": "rgba(15, 29, 64, 0.86)",
        "lighting": "aurora-diagonal",
    },
    {
        "name": "crimson_chronicle_archive",
        "bg_top": "#2a0a18",
        "bg_mid": "#1c0d26",
        "bg_bottom": "#0c0612",
        "primary": "#f43f5e",
        "secondary": "#f97316",
        "highlight": "#fde68a",
        "surface": "rgba(42, 10, 24, 0.86)",
        "lighting": "warm-horizon",
    },
    {
        "name": "amethyst_quantum_nexus",
        "bg_top": "#1d1038",
        "bg_mid": "#12183b",
        "bg_bottom": "#07091c",
        "primary": "#a855f7",
        "secondary": "#ec4899",
        "highlight": "#38bdf8",
        "surface": "rgba(29, 16, 56, 0.86)",
        "lighting": "nebula-core",
    },
    {
        "name": "teal_mediterranean_atlas",
        "bg_top": "#082836",
        "bg_mid": "#0c3547",
        "bg_bottom": "#04151f",
        "primary": "#06b6d4",
        "secondary": "#34d399",
        "highlight": "#fbbf24",
        "surface": "rgba(12, 53, 71, 0.86)",
        "lighting": "coastal-beam",
    },
    {
        "name": "bronze_antiquity_monument",
        "bg_top": "#261c10",
        "bg_mid": "#1c1917",
        "bg_bottom": "#0c0a09",
        "primary": "#eab308",
        "secondary": "#22d3ee",
        "highlight": "#f97316",
        "surface": "rgba(38, 28, 16, 0.88)",
        "lighting": "sunburst-zenith",
    },
    {
        "name": "indigo_metropolis_skyline",
        "bg_top": "#111836",
        "bg_mid": "#1e1b4b",
        "bg_bottom": "#090a1f",
        "primary": "#60a5fa",
        "secondary": "#c084fc",
        "highlight": "#4ade80",
        "surface": "rgba(30, 27, 75, 0.86)",
        "lighting": "city-glow-bottom",
    },
    {
        "name": "emerald_biosphere_terraces",
        "bg_top": "#072618",
        "bg_mid": "#0f2e22",
        "bg_bottom": "#04140d",
        "primary": "#4ade80",
        "secondary": "#2dd4bf",
        "highlight": "#facc15",
        "surface": "rgba(15, 46, 34, 0.86)",
        "lighting": "canopy-rays",
    },
    {
        "name": "sapphire_deep_ocean_trench",
        "bg_top": "#071e3d",
        "bg_mid": "#0a2a54",
        "bg_bottom": "#030e21",
        "primary": "#22d3ee",
        "secondary": "#3b82f6",
        "highlight": "#f472b6",
        "surface": "rgba(10, 42, 84, 0.86)",
        "lighting": "bioluminescent-depth",
    },
]

ENVIRONMENT_MODES: List[str] = [
    "topographic_contour",
    "isometric_city_grid",
    "orbital_meridian_sphere",
    "architectural_blueprint",
    "celestial_constellation",
    "kinetic_wave_field",
    "radial_light_cathedral",
    "chronicle_strata_layers",
    "hexagonal_data_matrix",
    "horizon_perspective_plane",
]

VISUAL_APPROACHES: List[str] = [
    "animated_city_environment",
    "spatial_geographic_diagram",
    "exploded_structural_diagram",
    "interactive_infographic_monument",
    "cause_and_effect_demonstration",
    "animated_timeline_expedition",
    "visual_metaphor_equilibrium",
    "demographic_crowd_constellation",
    "comparative_duel_stage",
    "kinetic_discovery_core",
    "layered_historical_citadel",
    "data_driven_elevation_spire",
]

CAMERA_CHOREOGRAPHIES: List[str] = [
    "zoom-in",
    "pan-left",
    "push-in",
    "tilt-up",
    "parallax",
    "zoom-out",
    "pan-right",
]


def _clean_text(s: Any) -> str:
    return re.sub(r"\s+", " ", str(s or "")).strip()


def _words(s: Any, max_words: int = 6, start_word: int = 0) -> str:
    cleaned = _clean_text(s).strip(".!؟?،:؛- ")
    if not cleaned:
        return ""
    toks = cleaned.split()
    return " ".join(toks[start_word : start_word + max_words]).strip(".!؟?،:؛- ")


# ---------------------------------------------------------------------------


from .geo import _CITY_STOP_WORDS


def generate_scene_tsx(beat: Dict[str, Any], scene_index: int, total_scenes: int = 8) -> str:
    """Fallback TSX stub used when LLM synthesis fails. Returns a valid, renderable component."""
    tsx_id = _clean_id(beat.get("tsx_id") or f"DynamicScene_{scene_index}")
    return (
        f"export const {tsx_id}: React.FC<{{frame?: number; fps?: number; dur?: number}}> = () => (\n"
        f"  <AbsoluteFill style={{{{background: '#0a0a0a'}}}} />\n"
        f");"
    )

# ---------------------------------------------------------------------------
# AI LLM Original TSX Synthesis + TypeScript Compilation Gate
# ---------------------------------------------------------------------------


def generate_dynamic_tsx_file(
    scenes_beats: List[Dict[str, Any]],
    use_llm: Optional[bool] = None,
    only_indices: Optional[set] = None,
    theme: Optional[Dict[str, Any]] = None,
) -> Path:
    """Generates bespoke, original React/TSX components in `remotion/src/generated/DynamicScenes.tsx`
    for every scene beat, synthesizing custom TSX via LLM and verifying with TypeScript `tsc --noEmit`.
    `theme` (style.theme_from_style) makes the scenes follow the video's ground / palette.
    """
    global _TSX_THEME
    _TSX_THEME = theme
    os.makedirs(DYNAMIC_TSX_PATH.parent, exist_ok=True)
    total = len(scenes_beats)
    seen_ids: set = set()
    for idx, beat in enumerate(scenes_beats):
        base_id = _clean_id(beat.get("tsx_id") or f"DynamicScene_{idx}")
        tsx_id = base_id
        if tsx_id in seen_ids:
            tsx_id = _clean_id(f"{base_id}_{idx}")
            suffix = 1
            while tsx_id in seen_ids:
                tsx_id = _clean_id(f"{base_id}_{idx}_{suffix}")
                suffix += 1
        seen_ids.add(tsx_id)
        beat["tsx_id"] = tsx_id

    geo_contexts: List[Dict[str, Any]] = [_resolve_beat_geo_context(b) for b in scenes_beats]
    beat_sigs: List[str] = [_compute_beat_tsx_sig(b, geo_contexts[idx]) for idx, b in enumerate(scenes_beats)]

    geo_const_lines: List[str] = []
    registry_entries: List[str] = []
    for idx, beat in enumerate(scenes_beats):
        tsx_id = beat["tsx_id"]
        registry_entries.append(f"  '{tsx_id}': {tsx_id},")
        if geo_contexts[idx].get("is_geo"):
            geo_payload = json.dumps(geo_contexts[idx], ensure_ascii=False)
            geo_const_lines.append(f"const _GEO_{tsx_id} = {geo_payload};")

    header = (
        "/* AUTO-GENERATED ORIGINAL TSX SCENES BY AI VIDEO ARCHITECT */\n"
        "import React from 'react';\n"
        "import {AbsoluteFill, interpolate, interpolateColors, spring, useCurrentFrame, useVideoConfig, Easing} from 'remotion';\n\n"
        + ("\n".join(geo_const_lines) + "\n\n" if geo_const_lines else "")
    )

    fallback_cache: Dict[int, str] = {}

    def _get_fallback(i: int) -> str:
        if i not in fallback_cache:
            fallback_cache[i] = generate_scene_tsx(scenes_beats[i], i, total)
        return fallback_cache[i]

    raw_blocks: List[Optional[str]] = [None] * total
    is_llm_block: List[bool] = [False] * total

    if use_llm is None:
        use_llm = _should_use_llm_tsx()
    reusable: Dict[Tuple[str, str], str] = _load_tsx_cache() if scenes_beats else {}
    for idx, beat in enumerate(scenes_beats):
        key = (beat["tsx_id"], beat_sigs[idx])
        if key in reusable:
            raw_blocks[idx] = reusable[key]
            is_llm_block[idx] = True

    logger.info("generate_dynamic_tsx_file: total=%d use_llm=%s cached=%d", total, use_llm, sum(1 for x in is_llm_block if x))
    if use_llm and scenes_beats:
        pending_indices: List[int] = []
        for idx, beat in enumerate(scenes_beats):
            if not is_llm_block[idx]:
                if only_indices is None or idx in only_indices:
                    pending_indices.append(idx)

        if pending_indices:
            llm_results: Dict[int, Optional[str]] = {}
            with ThreadPoolExecutor(max_workers=min(4, len(pending_indices))) as pool:
                futs = {}
                for idx in pending_indices:
                    beat = scenes_beats[idx]
                    prev_n = _clean_text(scenes_beats[idx - 1].get("narration", "")) if idx > 0 else ""
                    next_n = _clean_text(scenes_beats[idx + 1].get("narration", "")) if idx + 1 < total else ""
                    fut = pool.submit(_synthesize_beat_tsx_via_llm, beat, idx, total, geo_contexts[idx], prev_n, next_n)
                    futs[fut] = idx
                for fut in as_completed(futs):
                    idx = futs[fut]
                    try:
                        code = fut.result()
                        if code:
                            llm_results[idx] = code
                    except Exception as e:
                        logger.warning("Parallel LLM TSX worker error on beat %d: %s", idx, e)

            for idx, code in llm_results.items():
                if code:
                    raw_blocks[idx] = code
                    is_llm_block[idx] = True

    for idx in range(total):
        if not raw_blocks[idx]:
            raw_blocks[idx] = _get_fallback(idx)

    def _marked_blocks() -> List[str]:
        out_b: List[str] = []
        for idx, blk in enumerate(raw_blocks):
            txt = blk or _get_fallback(idx)
            if is_llm_block[idx]:
                out_b.append(f"/* @llm_verified:{scenes_beats[idx]['tsx_id']}:{beat_sigs[idx]} */\n{txt}")
            else:
                out_b.append(txt)
        return out_b

    marked = _marked_blocks()
    DYNAMIC_TSX_PATH.write_text(_assemble_dynamic_file(header, marked, registry_entries), encoding="utf-8")

    # Verify TypeScript compilation when LLM blocks were inserted; try LLM self-repair before any fallback
    if use_llm and scenes_beats and any(is_llm_block):
        ok, err_lines, tsc_out = _run_tsc_check()
        if not ok:
            logger.warning("DynamicScenes.tsx failed tsc check on lines %s:\n%s\nAttempting LLM repair.", err_lines, tsc_out[:700])
            header_line_count = header.count("\n")
            cur_line = header_line_count + 1
            bad_indices: List[int] = []
            for idx, blk in enumerate(marked):
                blk_lines = blk.count("\n") + 1
                start_l = cur_line
                end_l = cur_line + blk_lines - 1
                cur_line = end_l + 2
                if (any(start_l <= el <= end_l for el in err_lines) or not err_lines) and is_llm_block[idx]:
                    bad_indices.append(idx)

            repaired_any = False
            for idx in bad_indices:
                repaired = _repair_beat_tsx_via_llm(
                    scenes_beats[idx]["tsx_id"],
                    raw_blocks[idx] or "",
                    tsc_out,
                    scenes_beats[idx],
                    geo_contexts[idx],
                )
                if repaired:
                    raw_blocks[idx] = repaired
                    repaired_any = True
                else:
                    raw_blocks[idx] = _get_fallback(idx)
                    is_llm_block[idx] = False
                    repaired_any = True

            if repaired_any:
                marked = _marked_blocks()
                DYNAMIC_TSX_PATH.write_text(_assemble_dynamic_file(header, marked, registry_entries), encoding="utf-8")
                ok2, err2, tsc_out2 = _run_tsc_check()
                if not ok2:
                    logger.warning("Post-repair tsc check still failed on lines %s; isolating failing beats.", err2)
                    cur_line = header.count("\n") + 1
                    for idx, blk in enumerate(marked):
                        blk_lines = blk.count("\n") + 1
                        start_l, end_l = cur_line, cur_line + blk_lines - 1
                        cur_line = end_l + 2
                        if any(start_l <= el <= end_l for el in err2) or not err2:
                            if is_llm_block[idx]:
                                raw_blocks[idx] = _get_fallback(idx)
                                is_llm_block[idx] = False
                    marked = _marked_blocks()
                    DYNAMIC_TSX_PATH.write_text(_assemble_dynamic_file(header, marked, registry_entries), encoding="utf-8")
                    ok3, err3, _ = _run_tsc_check()
                    if not ok3:
                        logger.warning("Final tsc fallback triggered (%s).", err3)
                        DYNAMIC_TSX_PATH.write_text(_assemble_dynamic_file(header, [_get_fallback(i) for i in range(total)], registry_entries), encoding="utf-8")
            else:
                logger.warning("tsc error outside scene blocks:\n%s", tsc_out[:600])

    verified_to_save: Dict[Tuple[str, str], str] = {}
    for idx in range(total):
        if is_llm_block[idx] and raw_blocks[idx]:
            verified_to_save[(scenes_beats[idx]["tsx_id"], beat_sigs[idx])] = raw_blocks[idx]  # type: ignore[index]
    if verified_to_save:
        _save_tsx_cache(verified_to_save)

    llm_count = sum(1 for x in is_llm_block if x)
    logger.info("DynamicScenes.tsx summary: %d/%d bespoke LLM components (fallback=%d)", llm_count, total, total - llm_count)
    return DYNAMIC_TSX_PATH

# Re-exported so `pipeline.storyteller.<name>` keeps working.
from .storyteller_intent import (  # noqa: E402,F401
    _AR_MULTIPLIERS,
    _AR_WORD_NUMBERS,
    _extract_numbers,
    _extract_phrases,
    _parse_arabic_word_number,
    _pick_unique,
    classify_narration_intent,
)

# Re-exported so `pipeline.storyteller.<name>` keeps working.
from .storyteller_geo import (  # noqa: E402,F401
    _AR_GEO_STOPWORDS,
    _COUNTRY_REGEX_PATTERNS,
    _clean_id,
    _clean_text_val,
    _escape_jsx_child,
    _extract_all_cities,
    _extract_countries_from_text,
    _format_coords,
    _resolve_beat_geo_context,
    _split_narration_parts,
)

# Re-exported so `pipeline.storyteller.<name>` keeps working.
from .storyteller_llm import (  # noqa: E402,F401
    _AR_LITERAL_RE,
    _LLM_TSX_SYSTEM,
    _arabic_texts,
    _build_llm_scene_prompts,
    _sanitize_llm_tsx,
    _should_use_llm_tsx,
    _synthesize_beat_tsx_via_llm,
)

# Re-exported so `pipeline.storyteller.<name>` keeps working.
from .storyteller_tsx_tools import (  # noqa: E402,F401
    _assemble_dynamic_file,
    _compute_beat_tsx_sig,
    _extract_verified_llm_blocks,
    _fix_color_interpolate,
    _load_tsx_cache,
    _repair_beat_tsx_via_llm,
    _run_tsc_check,
    _save_tsx_cache,
    _top_level_args,
)

# Re-exported so `pipeline.storyteller.<name>` keeps working.
from .storyteller_svg import (  # noqa: E402,F401
    build_svg_construction_layers,
    undefined_or_str,
)

# Re-exported so `pipeline.storyteller.<name>` keeps working.
from .storyteller_spec import (  # noqa: E402,F401
    design_scene_specification,
    evaluate_and_improve_scene,
)
