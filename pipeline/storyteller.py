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


def _extract_phrases(narration: str) -> List[str]:
    """Splits Arabic/English narration into meaningful semantic phrases for synchronization."""
    text = _clean_text(narration)
    if not text:
        return []
    parts = [p.strip() for p in re.split(r"[،,؛;:.!؟?\-]+", text) if p.strip()]
    phrases: List[str] = []
    for p in parts:
        w = p.split()
        if len(w) <= 6:
            phrases.append(p)
        else:
            for idx in range(0, len(w), 5):
                chunk = " ".join(w[idx : idx + 5]).strip()
                if chunk:
                    phrases.append(chunk)
    return phrases[:5] if phrases else [_words(text, 5)]


_AR_WORD_NUMBERS = {
    "\u0635\u0641\u0631": 0, "\u0648\u0627\u062d\u062f": 1, "\u0627\u062b\u0646\u064a\u0646": 2, "\u0627\u062b\u0646\u0627\u0646": 2, "\u062b\u0644\u0627\u062b\u0629": 3, "\u0623\u0631\u0628\u0639\u0629": 4, "\u0623\u0631\u0628\u0639": 4,
    "\u062e\u0645\u0633\u0629": 5, "\u062e\u0645\u0633": 5, "\u0633\u062a\u0629": 6, "\u0633\u062a": 6, "\u0633\u0628\u0639\u0629": 7, "\u0633\u0628\u0639": 7, "\u062b\u0645\u0627\u0646\u064a\u0629": 8,
    "\u062b\u0645\u0627\u0646": 8, "\u062a\u0633\u0639\u0629": 9, "\u062a\u0633\u0639": 9, "\u0639\u0634\u0631\u0629": 10, "\u0639\u0634\u0631": 10, "\u0623\u062d\u062f \u0639\u0634\u0631": 11, "\u0627\u062b\u0646\u0627 \u0639\u0634\u0631": 12,
    "\u062e\u0645\u0633\u0629 \u0639\u0634\u0631": 15, "\u0633\u062a\u0629 \u0639\u0634\u0631": 16, "\u0633\u0628\u0639\u0629 \u0639\u0634\u0631": 17, "\u062b\u0645\u0627\u0646\u064a\u0629 \u0639\u0634\u0631": 18, "\u062a\u0633\u0639\u0629 \u0639\u0634\u0631": 19,
    "\u0639\u0634\u0631\u0648\u0646": 20, "\u0639\u0634\u0631\u064a\u0646": 20, "\u062b\u0644\u0627\u062b\u0648\u0646": 30, "\u062b\u0644\u0627\u062b\u064a\u0646": 30, "\u062e\u0645\u0633\u0648\u0646": 50, "\u062e\u0645\u0633\u064a\u0646": 50,
    "\u0645\u0626\u0629": 100, "\u0645\u0627\u0626\u0629": 100, "\u0623\u0644\u0641": 1_000, "\u0623\u0644\u0641\u064a\u0646": 2_000, "\u0645\u0644\u064a\u0648\u0646": 1_000_000,
    "\u0645\u0644\u064a\u0627\u0631": 1_000_000_000,
}
_AR_MULTIPLIERS = {"\u0645\u0644\u064a\u0648\u0646": 1_000_000, "\u0645\u0644\u064a\u0627\u0631": 1_000_000_000, "\u0623\u0644\u0641": 1_000, "\u0645\u0626\u0629": 100, "\u0645\u0627\u0626\u0629": 100}


def _parse_arabic_word_number(text: str) -> Optional[float]:
    """Try to parse a simple Arabic word-form number like '\u0633\u0628\u0639\u0629 \u0639\u0634\u0631 \u0645\u0644\u064a\u0648\u0646'."""
    t = text.strip()
    for multi_word, val in sorted(_AR_WORD_NUMBERS.items(), key=lambda x: -len(x[0])):
        if multi_word in t:
            base = val
            for mult_word, mult_val in _AR_MULTIPLIERS.items():
                if mult_word in t and mult_word != multi_word:
                    return base * mult_val
            return float(base)
    return None


def _extract_numbers(text: str) -> List[Dict[str, Any]]:
    """Extracts numbers (digit or Arabic word-form) and their surrounding context label from text."""
    results: List[Dict[str, Any]] = []
    # First pass: Arabic word-numbers (e.g. "\u0633\u0628\u0639\u0629 \u0639\u0634\u0631 \u0645\u0644\u064a\u0648\u0646")
    for phrase, val in sorted(_AR_WORD_NUMBERS.items(), key=lambda x: -len(x[0])):
        if phrase in text:
            after = text[text.index(phrase) + len(phrase):].strip().split()[:3]
            label = " ".join(after) if after else phrase
            results.append({"display": phrase, "value": float(val), "label": _words(label, 3) or "\u0642\u064a\u0645\u0629"})
    for m in re.finditer(r"(\d[\d,.\u0660-\u0669]*)", text):
        raw_num = m.group(1)
        arabic_map = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
        norm_str = raw_num.translate(arabic_map).replace(",", "")
        try:
            val = float(norm_str)
        except ValueError:
            val = 0.0
        # Grab 3 words after the number as unit/label
        after = text[m.end() :].strip().split()[:3]
        before = text[: m.start()].strip().split()[-3:]
        label = " ".join(after) if after else " ".join(before)
        results.append({
            "display": raw_num,
            "value": val,
            "label": _words(label, 3) or "قيمة موثقة",
        })
    return results


# ---------------------------------------------------------------------------
# 1. UNDERSTAND BEFORE DESIGNING: Narrative & Segment Context Analyzer
# ---------------------------------------------------------------------------

def classify_narration_intent(narration: str, role: str = "body") -> Dict[str, Any]:
    """Distinguishes narration types and extracts key entities without restricting to templates."""
    t = _clean_text(narration)
    nums = _extract_numbers(t)
    city_name, city_info = detect_city_in_text(t)

    # Identify multiple cities if mentioned
    phrases = _extract_phrases(t)
    cities_found: List[Dict[str, Any]] = []
    seen_cities = set()
    for ph in [t] + phrases:
        cn, ci = detect_city_in_text(ph)
        if cn and ci and cn not in seen_cities:
            seen_cities.add(cn)
            cities_found.append({"name": cn, **ci})

    has_question = ("؟" in t or "?" in t) or any(
        w in t.split() for w in ["لماذا", "كيف", "متى", "أين", "هل", "ما", "ماذا"]
    )
    has_comparison = any(
        w in t for w in ["مقابل", "بينما", "تليها", "يليها", "أكبر من", "أصغر من", "صراع", "مقارنة", "تفوق", "منافسة"]
    )
    has_cause_effect = any(
        w in t for w in ["بسبب", "نتيجة", "أدى", "يؤدي", "تؤدي", "دفع", "لذلك", "فجأة", "تحول", "جعلت", "مضاعفة"]
    )
    has_history = any(
        w in t for w in ["عام", "سنة", "قرن", "تاريخ", "تأسست", "الحرب", "الإمبراطورية", "القديمة", "العصور", "ملك", "دستور"]
    )
    has_process = any(
        w in t for w in ["مراحل", "خطوات", "تنتقل", "تدفق", "منظومة المراحل", "خطوة بخطوة"]
    )
    # ponytail: removed "شبكة","نظام","مسار","رحلة" — too broad, caused network-diagram false positives on geo content
    has_population = any(
        w in t for w in ["سكان", "نسمة", "مليون", "تعداد", "شعب", "بشر", "مدن", "مدينة", "عاصمة"]
    )

    has_urban = any(
        w in t for w in ["أبراج", "حاضرة", "عمران", "عمرانية", "ناطحات", "أفق", "مزدحمة"]
    )

    if role == "hook" or (has_question and role in ("open_loop", "hook")):
        primary_intent = "question_and_discovery"
        visual_approach = "exploded_isometric_core"
    elif has_comparison and (len(nums) >= 2 or len(cities_found) >= 2 or "مقابل" in t or "بينما" in t):
        primary_intent = "comparative_analysis"
        visual_approach = "equilibrium_duel_stage"
    elif has_cause_effect:
        primary_intent = "cause_and_consequence"
        visual_approach = "exploded_isometric_core"
    elif has_urban or (city_info and has_population and nums):
        primary_intent = "urban_metropolis"
        visual_approach = "metropolis_skyline"
    elif city_info:
        primary_intent = "geographic_spatial_story"
        visual_approach = "orbital_cartography"
    elif has_history:
        primary_intent = "historical_chronicle"
        visual_approach = "chronicle_conduit"
    elif len(nums) >= 2:
        primary_intent = "multi_metric_statistics"
        visual_approach = "equilibrium_duel_stage"
    elif len(nums) == 1:
        primary_intent = "hero_statistic_revelation"
        visual_approach = "metropolis_skyline" if has_population else "exploded_isometric_core"
    elif has_process:
        primary_intent = "process_and_transformation"
        visual_approach = "exploded_isometric_core"
    elif role == "cta":
        primary_intent = "interactive_audience_challenge"
        visual_approach = "exploded_isometric_core"
    else:
        primary_intent = "conceptual_explanation"
        visual_approach = "exploded_isometric_core"

    return {
        "primary_intent": primary_intent,
        "visual_approach": visual_approach,
        "has_question": has_question,
        "has_comparison": has_comparison,
        "has_cause_effect": has_cause_effect,
        "has_history": has_history,
        "has_process": has_process,
        "has_population": has_population,
        "numbers": nums,
        "primary_city": city_info,
        "primary_city_name": city_name,
        "cities": cities_found,
        "phrases": phrases,
    }


# ---------------------------------------------------------------------------
# 2 & 3. INVENT ORIGINAL VISUAL CONCEPT & CREATE 6-PART SCENE SPECIFICATION
# ---------------------------------------------------------------------------

def _pick_unique(options: List[Any], used: set, seed: int, key_fn=lambda x: x) -> Any:
    for offset in range(len(options)):
        cand = options[(seed + offset) % len(options)]
        k = key_fn(cand)
        if k not in used:
            used.add(k)
            return cand
    cand = options[seed % len(options)]
    used.add(key_fn(cand))
    return cand


def build_svg_construction_layers(
    approach: str,
    intent_info: Dict[str, Any],
    palette: Dict[str, str],
    phrases: List[str],
    scene_index: int,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Creates bespoke SVG vector layers and coordinated motion elements for the scene."""
    p_col = palette["primary"]
    s_col = palette["secondary"]
    h_col = palette["highlight"]
    surf = palette["surface"]

    nums = intent_info["numbers"]
    cities = intent_info["cities"]
    city_name = intent_info["primary_city_name"] or ""

    svg_layers: List[Dict[str, Any]] = []
    elements: List[Dict[str, Any]] = []

    # 1. Bespoke SVG Vector Illustration Layer tailored to the visual approach
    if approach in ("animated_city_environment", "layered_historical_citadel") or intent_info["has_population"]:
        # Custom SVG Metropolis / Citadel Skyline with illuminated architectural silhouettes & radar halo
        svg_layers.append({
            "kind": "metropolis_skyline",
            "x": 540,
            "y": 900,
            "primary": p_col,
            "secondary": s_col,
            "highlight": h_col,
            "seed": scene_index * 37 + 11,
            "city_label": city_name or (phrases[0] if phrases else ""),
            "population_display": nums[0]["display"] if nums else "",
        })
    elif approach in ("spatial_geographic_diagram", "data_driven_elevation_spire") or cities:
        # Custom SVG Orbital Globe + Spatial Coordinate Rings + Trajectory Arcs
        if cities:
            _lat0, _lon0 = float(cities[0]["lat"]), float(cities[0]["lon"])
            _coords = f"{abs(_lat0):.2f}°{'N' if _lat0 >= 0 else 'S'}, {abs(_lon0):.2f}°{'E' if _lon0 >= 0 else 'W'}"
        else:
            _coords = ""
        svg_layers.append({
            "kind": "orbital_cartography",
            "x": 540,
            "y": 860,
            "primary": p_col,
            "secondary": s_col,
            "highlight": h_col,
            "cities": [c["name"] for c in cities[:4]],
            "coords": _coords,
        })
    elif approach in ("comparative_duel_stage", "visual_metaphor_equilibrium") or intent_info["has_comparison"]:
        # Custom SVG Twin Force Pillars + Dynamic Equilibrium Beam
        _first_ph = phrases[0] if phrases else ""
        _split_pt = max(1, len(_first_ph.split()) // 2)
        svg_layers.append({
            "kind": "equilibrium_duel_stage",
            "x": 540,
            "y": 880,
            "primary": p_col,
            "secondary": s_col,
            "highlight": h_col,
            "left_label": _words(_first_ph, _split_pt) if (len(phrases) == 1 and len(_first_ph.split()) > 2) else _first_ph,
            "right_label": phrases[1] if len(phrases) > 1 else _words(_first_ph, 4, start_word=_split_pt),
        })
    elif approach in ("animated_timeline_expedition", "cause_and_effect_demonstration") or intent_info["has_history"]:
        # Custom SVG Time-Spiral & Cause-Effect Gear/Wave Conduit
        svg_layers.append({
            "kind": "chronicle_conduit",
            "x": 540,
            "y": 890,
            "primary": p_col,
            "secondary": s_col,
            "highlight": h_col,
            "milestones": phrases[:4],
        })
    else:
        # Custom SVG Exploded Isometric Core & Radial Information Nodes
        svg_layers.append({
            "kind": "exploded_isometric_core",
            "x": 540,
            "y": 880,
            "primary": p_col,
            "secondary": s_col,
            "highlight": h_col,
            "nodes": phrases[:4],
        })

    # 2. Coordinated Foreground & Midground Motion Primitives (spread across Y=380..1380)
    # Ambient geometric framing rings & structural paths
    elements.append({
        "id": f"sc_{scene_index}_outer_ring",
        "type": "shape",
        "shape": "ring",
        "x": 540,
        "y": 860,
        "w": 680,
        "stroke": p_col,
        "strokeWidth": 2,
        "fill": "rgba(255,255,255,0.01)",
        "motion": "scale",
        "loop": "spin",
        "delay": 0,
    })
    elements.append({
        "id": f"sc_{scene_index}_inner_shield",
        "type": "shape",
        "shape": "circle" if scene_index % 2 == 0 else "shield",
        "x": 540,
        "y": 860,
        "w": 360,
        "h": 360,
        "stroke": s_col,
        "strokeWidth": 3,
        "fill": surf,
        "motion": "pop",
        "loop": "pulse",
        "delay": 3,
    })

    # Animated trajectory paths connecting upper, center, and lower visual zones
    elements.append({
        "id": f"sc_{scene_index}_curve_top",
        "type": "path",
        "curve": "bezier" if scene_index % 2 == 0 else "arc",
        "from": [180, 500],
        "to": [900, 500],
        "control": [540, 360],
        "stroke": p_col,
        "strokeWidth": 4,
        "motion": "draw",
        "delay": 4,
    })
    elements.append({
        "id": f"sc_{scene_index}_curve_bottom",
        "type": "path",
        "curve": "wave" if scene_index % 3 == 0 else "mountain",
        "from": [140, 1280],
        "to": [940, 1280],
        "control": [540, 1180],
        "stroke": s_col,
        "strokeWidth": 4,
        "motion": "draw",
        "delay": 8,
    })

    # Phrase-synchronized visual cards/badges positioned at distinct vertical & horizontal anchors
    anchors = [
        (540, 460, "drop", "lg"),
        (300, 740, "slide_right", "md"),
        (780, 740, "slide_left", "md"),
        (540, 1140, "rise", "lg"),
    ]
    icons_cycle = [
        "lucide:compass",
        "lucide:landmark",
        "lucide:Layers",
        "lucide:sparkles",
        "lucide:flame",
        "lucide:globe",
        "lucide:crown",
        "lucide:trending-up",
    ]

    for idx, ph in enumerate(phrases[:4]):
        ax, ay, mot, sz = anchors[idx % len(anchors)]
        ic = icons_cycle[(scene_index * 3 + idx) % len(icons_cycle)]
        elements.append({
            "id": f"sc_{scene_index}_phrase_{idx}",
            "type": "badge",
            "x": ax,
            "y": ay,
            "text": _words(ph, 5),
            "sub": cities[idx]["country"] if idx < len(cities) else "",
            "icon": ic,
            "flag": cities[idx]["iso2"].lower() if idx < len(cities) and cities[idx].get("iso2") else undefined_or_str(intent_info, idx),
            "size": sz,
            "bg": surf,
            "borderColor": p_col if idx % 2 == 0 else s_col,
            "textColor": "#ffffff",
            "motion": mot,
            "delay": 6 + idx * 7,
        })
        if idx > 0:
            prev_ax, prev_ay, _, _ = anchors[(idx - 1) % len(anchors)]
            elements.append({
                "id": f"sc_{scene_index}_conn_{idx}",
                "type": "connector",
                "from": [prev_ax, prev_ay],
                "to": [ax, ay],
                "color": h_col,
                "dashed": idx % 2 == 1,
                "delay": 5 + idx * 7,
            })

    # If numbers exist in narration, add real animated counters & gauges
    if nums:
        primary_num = nums[0]
        elements.append({
            "id": f"sc_{scene_index}_hero_counter",
            "type": "counter",
            "x": 540,
            "y": 920,
            "from": 0,
            "to": primary_num["value"],
            "unit": "%" if "%" in primary_num["display"] else "",
            "label": primary_num["label"],
            "color": h_col,
            "fontSize": 76,
            "motion": "pop",
            "delay": 10,
        })
        if len(nums) >= 2:
            v1 = max(1.0, nums[0]["value"])
            v2 = max(1.0, nums[1]["value"])
            ratio = int(round(min(95, max(15, (v1 / (v1 + v2)) * 100))))
            elements.append({
                "id": f"sc_{scene_index}_comp_gauge",
                "type": "gauge",
                "x": 540,
                "y": 1340,
                "value": ratio,
                "label": f"{_words(nums[0]['label'], 2)} vs {_words(nums[1]['label'], 2)}",
                "unit": "%",
                "kind": "linear",
                "width": 660,
                "color": p_col,
                "motion": "rise",
                "delay": 16,
            })
    else:
        # Central hero icon emblem when no raw number is present
        hero_ic = icons_cycle[(scene_index * 5) % len(icons_cycle)]
        elements.append({
            "id": f"sc_{scene_index}_center_icon",
            "type": "icon",
            "name": hero_ic,
            "x": 540,
            "y": 860,
            "size": 124,
            "color": h_col,
            "motion": "pop",
            "loop": "float",
            "delay": 8,
        })

    return svg_layers, elements


def undefined_or_str(intent_info: Dict[str, Any], idx: int) -> Optional[str]:
    if idx == 0 and intent_info.get("primary_city") and intent_info["primary_city"].get("iso2"):
        return str(intent_info["primary_city"]["iso2"]).lower()
    return None


def design_scene_specification(
    scene_id: str,
    role: str,
    narration: str,
    on_screen: str = "",
    scene_index: int = 0,
    total_scenes: int = 8,
    prev_narration: str = "",
    next_narration: str = "",
    video_title: str = "",
    used_palettes: Optional[set] = None,
    used_environments: Optional[set] = None,
    used_approaches: Optional[set] = None,
    used_cameras: Optional[set] = None,
) -> Dict[str, Any]:
    """Creates the complete 6-part Visual Scene Specification (Sections A–F) + SVG layers."""
    if used_palettes is None:
        used_palettes = set()
    if used_environments is None:
        used_environments = set()
    if used_approaches is None:
        used_approaches = set()
    if used_cameras is None:
        used_cameras = set()

    seed = int(hashlib.sha1(f"{video_title}:{scene_id}:{scene_index}:{narration}".encode("utf-8")).hexdigest()[:8], 16)
    intent_info = classify_narration_intent(narration, role=role)

    palette = _pick_unique(SCENE_PALETTES, used_palettes, seed + scene_index, key_fn=lambda p: p["name"])
    env_mode = _pick_unique(ENVIRONMENT_MODES, used_environments, seed + scene_index * 2)
    approach = _pick_unique(VISUAL_APPROACHES, used_approaches, seed + scene_index * 3)
    camera = _pick_unique(CAMERA_CHOREOGRAPHIES, used_cameras, seed + scene_index)

    phrases = intent_info["phrases"]
    svg_layers, elements = build_svg_construction_layers(
        approach=approach,
        intent_info=intent_info,
        palette=palette,
        phrases=phrases,
        scene_index=scene_index,
    )

    # E. Narration Synchronization cues (maps each phrase to time ratio and visual emphasis)
    narration_cues: List[Dict[str, Any]] = []
    n_ph = max(1, len(phrases))
    for p_idx, ph in enumerate(phrases):
        start_r = round(p_idx / n_ph, 2)
        end_r = round((p_idx + 1) / n_ph, 2)
        narration_cues.append({
            "phrase": ph,
            "start_ratio": start_r,
            "end_ratio": end_r,
            "visual_event": f"reveal_node_{p_idx}",
            "emphasis_target": f"sc_{scene_index}_phrase_{p_idx}",
        })

    # Complete 6-section Visual Scene Specification (A–F)
    scene_spec = {
        "visual_concept": {
            "main_idea": f"{approach} illustrating: {_words(on_screen or narration, 7)}",
            "communicates": intent_info["primary_intent"],
            "rationale": (
                f"Translates segment {scene_index + 1}/{total_scenes} ({role}) into an original "
                f"{approach} composition with {env_mode} atmosphere."
            ),
            "approach": approach,
        },
        "composition": {
            "main_subject": on_screen or _words(narration, 5),
            "supporting_elements": [_words(p, 5) for p in phrases[:4]],
            "foreground": "Phrase-synchronized callout badges, animated metric counters, and vector connectors",
            "background": f"Full-bleed 1080x1920 {env_mode} environment in {palette['name']} palette",
            "positioning": "Vertical 3-tier hierarchy across Y=360..1380 within 1080x1920 safe zone",
            "hierarchy": "1. Central SVG focal illustration -> 2. Hero metric/badge -> 3. Phrase-synced nodes",
            "typography_placement": "Top headline zone (Y=220..320), mid-canvas callouts, bottom caption zone (Y=1500+)",
            "color_and_lighting": palette,
        },
        "svg_construction": {
            "illustrations": svg_layers,
            "vector_layers": [env_mode, approach, "foreground_callouts"],
            "labels_and_diagrams": [el.get("text") or el.get("label") for el in elements if el.get("text") or el.get("label")],
            "masks_and_clips": ["radial_vignette_mask", "safe_zone_clip_1080x1920"],
            "relationships": f"Connected flow across {len(phrases)} semantic segments",
        },
        "animation_direction": {
            "entrance": "Spring-physics staggered pop & draw evolution",
            "continuous_movement": f"Ambient {env_mode} drift + orbital ring rotation",
            "transformations": "SVG stroke evolution + 3D perspective depth",
            "camera_movement": camera,
            "visual_reveals": "Sequential phrase-locked node activation",
            "exit": "Smooth scale-and-morph handoff to next scene",
        },
        "narration_sync": {
            "cues": narration_cues,
            "phrase_count": len(narration_cues),
        },
        "transition": {
            "connects_to": f"scene_{scene_index + 1}" if scene_index + 1 < total_scenes else "loop_to_hook",
            "shared_motif": palette["primary"],
            "morph_element": svg_layers[0]["kind"] if svg_layers else "orbital_ring",
            "prev_context": _words(prev_narration, 5),
            "next_context": _words(next_narration, 5),
        },
    }

    bg_css = (
        f"radial-gradient(circle at 50% 38%, {palette['bg_mid']} 0%, "
        f"{palette['bg_top']} 52%, {palette['bg_bottom']} 100%)"
    )

    return {
        "kind": "generative_canvas",
        "title": _words(on_screen or phrases[0] if phrases else video_title, 6),
        "subtitle": _words(phrases[1] if len(phrases) > 1 else "", 6),
        "background": bg_css,
        "bg_mood": palette["name"],
        "accent": palette["primary"],
        "secondary_accent": palette["secondary"],
        "environment": env_mode,
        "grid": "radar" if scene_index % 3 == 0 else ("lines" if scene_index % 3 == 1 else "dots"),
        "camera": camera,
        "svg_layers": svg_layers,
        "elements": elements,
        "narration_cues": narration_cues,
        "scene_spec": scene_spec,
        "tsx_id": f"DynamicScene_{scene_id}_{scene_index}",
    }


# ---------------------------------------------------------------------------
# 7. SCENE QUALITY EVALUATION (8 Mandatory Criteria)
# ---------------------------------------------------------------------------

def evaluate_and_improve_scene(
    beat: Dict[str, Any],
    narration: str,
    scene_index: int = 0,
    previous_signatures: Optional[List[str]] = None,
    prev_signatures: Optional[List[str]] = None,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Evaluates a generated scene beat against the 8 mandatory quality criteria
    and automatically upgrades it if any criterion fails.
    """
    sigs = previous_signatures if previous_signatures is not None else (prev_signatures if prev_signatures is not None else [])
    b = dict(beat)

    # If the beat lacks a full scene_spec or has fewer than 6 elements, enrich via design_scene_specification
    if not b.get("scene_spec") or len(b.get("elements") or []) < 6 or not b.get("svg_layers"):
        designed = design_scene_specification(
            scene_id=str(b.get("id") or f"auto_{scene_index}"),
            role="body",
            narration=narration,
            on_screen=str(b.get("title") or ""),
            scene_index=scene_index,
        )
        for k, v in designed.items():
            if not b.get(k) or k in ("elements", "svg_layers", "scene_spec", "narration_cues", "background", "environment", "accent", "secondary_accent", "camera", "tsx_id"):
                b[k] = v

    elements = list(b.get("elements") or [])
    svg_layers = list(b.get("svg_layers") or [])

    # Criterion 1: Does the visual actually explain the narration?
    has_narration_tie = bool(b.get("title")) or any(el.get("text") or el.get("label") for el in elements)

    # Criterion 2: Is the main idea immediately understandable?
    has_clear_subject = bool(b.get("title")) and (len(svg_layers) > 0 or len(elements) >= 3)

    # Criterion 3: Is the composition visually interesting?
    has_visual_interest = bool(b.get("background")) and bool(b.get("environment")) and len(svg_layers) >= 1

    # Criterion 4: Does it contain enough meaningful visual detail? (Minimum 6 coordinated elements + 1 SVG illustration)
    has_enough_detail = len(elements) >= 6 and len(svg_layers) >= 1

    # Criterion 5: Are the elements coordinated? (Spread across vertical zones, no identical (x,y) collisions for badges)
    badge_coords = [(el.get("x", 540), el.get("y", 960)) for el in elements if el.get("type") == "badge"]
    has_coordinated_layout = len(badge_coords) == len(set(badge_coords))

    # Criterion 6: Is the animation smooth and purposeful?
    has_smooth_animation = bool(b.get("camera")) and any(el.get("motion") for el in elements)

    # Criterion 7: Does it look different from previous scenes?
    sig = f"{b.get('bg_mood')}:{b.get('environment')}:{b.get('accent')}"
    is_distinct = sig not in sigs

    # Criterion 8: Is it visually professional at 1080x1920?
    in_bounds = all(
        60 <= int(el.get("x", 540)) <= 1020 and 220 <= int(el.get("y", 960)) <= 1480
        for el in elements
        if "x" in el and "y" in el
    )

    # Auto-improve if any criterion failed
    if not is_distinct:
        alt_pal = SCENE_PALETTES[(scene_index + len(sigs) + 3) % len(SCENE_PALETTES)]
        alt_env = ENVIRONMENT_MODES[(scene_index + len(sigs) + 2) % len(ENVIRONMENT_MODES)]
        b["accent"] = alt_pal["primary"]
        b["secondary_accent"] = alt_pal["secondary"]
        b["environment"] = alt_env
        b["bg_mood"] = alt_pal["name"]
        b["background"] = (
            f"radial-gradient(circle at 50% 38%, {alt_pal['bg_mid']} 0%, "
            f"{alt_pal['bg_top']} 52%, {alt_pal['bg_bottom']} 100%)"
        )
        sig = f"{b.get('bg_mood')}:{b.get('environment')}:{b.get('accent')}"
        is_distinct = True

    if not has_coordinated_layout:
        safe_slots = [(540, 460), (290, 730), (790, 730), (540, 1150), (540, 1330)]
        b_idx = 0
        for el in elements:
            if el.get("type") == "badge":
                sx, sy = safe_slots[b_idx % len(safe_slots)]
                el["x"], el["y"] = sx, sy
                b_idx += 1
        has_coordinated_layout = True

    if not in_bounds:
        for el in elements:
            if "x" in el:
                el["x"] = max(80, min(1000, int(el["x"])))
            if "y" in el:
                el["y"] = max(260, min(1450, int(el["y"])))
        in_bounds = True

    sigs.append(sig)

    criteria = {
        "1_explains_narration": has_narration_tie,
        "2_immediately_understandable": has_clear_subject,
        "3_visually_interesting": has_visual_interest,
        "4_meaningful_visual_detail": has_enough_detail,
        "5_elements_coordinated": has_coordinated_layout,
        "6_smooth_purposeful_animation": has_smooth_animation,
        "7_distinct_from_previous": is_distinct,
        "8_professional_1080x1920": in_bounds,
    }
    report = {
        "passed": all(criteria.values()),
        "criteria": criteria,
        **criteria,
    }
    return b, report


# ---------------------------------------------------------------------------


from .geo import _CITY_STOP_WORDS

_AR_GEO_STOPWORDS = _CITY_STOP_WORDS | {
    "من", "في", "على", "إلى", "الى", "عن", "مع", "بين", "هل", "ما", "لماذا",
    "كيف", "متى", "أين", "التي", "الذي", "هذا", "هذه", "ذلك", "تلك", "لكن",
    "بينما", "أصبح", "أصبحت", "عام", "سنة", "مدينة", "المدينة", "مدن", "المدن", "مدينتين", "المدينتين",
    "عاصمة", "العاصمة", "عاصمتين", "العاصمتين", "عاصمتان", "عواصم", "العواصم",
    "دولة", "الدولة", "دول", "الدول", "بلد", "البلد", "بلاد", "البلاد",
    "العالم", "قصة", "حرب", "الحرب", "دستور", "الدستور", "دستوري", "دستورية",
    "مقر", "حكومة", "الحكومة", "برلمان", "البرلمان", "اقتصادي", "الاقتصادي", "السياسي",
    "سياسي", "مركز", "المركز", "أعلى", "جبال", "الجبال", "قمة", "القمة", "القرن", "اليوم", "لها",
    "تعلم", "أن", "كان", "كانت", "بعد", "قبل", "أو", "ثم", "حتى", "فقد",
    "أكبر", "أول", "أولى", "ثاني", "واحدة", "رسمياً", "رسميتين", "فعلياً", "الأمر", "السبب",
    "جزيرة", "الجزيرة", "جزر", "الجزر", "سلطة", "السلطة", "تاج", "التاج",
    "ثورة", "الثورة", "ثورات", "الثورات", "إسباني", "الإسباني", "قلب", "القلب",
    "شمال", "الشمال", "جنوب", "الجنوب", "شرق", "الشرق", "غرب", "الغرب", "الجنوبية", "الشمالية",
    "أمريكا", "أوروبا", "آسيا", "أفريقيا", "إفريقيا", "شهدت", "ضد", "تجمع", "تملك",
    "عين", "العين", "صور", "الصور", "بيان", "البيان", "سلام", "السلام", "أمل", "الأمل",
}


def _clean_id(raw_id: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_]", "_", str(raw_id or "Scene_0"))
    if not cleaned or not cleaned[0].isalpha():
        cleaned = "Scene_" + cleaned
    return cleaned


def _clean_text_val(s: Any) -> str:
    return str(s or "").replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ").strip()


def _escape_jsx_child(s: Any) -> str:
    txt = str(s or "").replace("\n", " ").strip()
    return (
        txt.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("{", "&#123;")
        .replace("}", "&#125;")
    )


def _format_coords(lat: float, lon: float) -> str:
    ns = "N" if lat >= 0 else "S"
    ew = "E" if lon >= 0 else "W"
    return f"{abs(lat):.2f}°{ns}, {abs(lon):.2f}°{ew}"


def _split_narration_parts(narration: str, count: int, title: str = "") -> List[str]:
    phrases = [p for p in _extract_phrases(narration) if p]
    if len(phrases) >= count:
        return phrases[:count]
    words = _clean_text(narration).split()
    out: List[str] = []
    if words:
        step = max(1, math.ceil(len(words) / count))
        for i in range(count):
            chunk = " ".join(words[i * step : (i + 1) * step]).strip(".!؟?،:؛- ")
            if chunk:
                out.append(chunk)
    seed_fallback = title or _words(narration, 4) or "مشهد السرد"
    while len(out) < count:
        out.append(seed_fallback)
    return out[:count]


_COUNTRY_REGEX_PATTERNS: Optional[List[Tuple[Any, str]]] = None


def _extract_countries_from_text(text: str) -> List[str]:
    global _COUNTRY_REGEX_PATTERNS
    if not text:
        return []
    if _COUNTRY_REGEX_PATTERNS is None:
        patterns: List[Tuple[Any, str]] = []
        keys = sorted(AR_ISO3.keys(), key=len, reverse=True)
        for k in keys:
            if len(k) < 3:
                continue
            pre = r"(?:^|[\s،؟!.,:؛\-وبلف])" if len(k) >= 4 else r"(?:^|[\s،؟!.,:؛\-])"
            pat = re.compile(pre + re.escape(k) + r"(?:$|[\s،؟!.,:؛\-])", flags=re.IGNORECASE)
            patterns.append((pat, AR_ISO3[k]))
        _COUNTRY_REGEX_PATTERNS = patterns

    found: List[str] = []
    seen = set()
    for pat, iso in _COUNTRY_REGEX_PATTERNS:
        if pat.search(text):
            if iso and iso not in seen:
                seen.add(iso)
                found.append(iso)
                if len(found) >= 3:
                    break
    return found


def _extract_all_cities(text: str) -> List[Dict[str, Any]]:
    """Finds all distinct cities mentioned in narration/title, not just the first match."""
    cleaned = _clean_text(text)
    if not cleaned:
        return []
    found: List[Dict[str, Any]] = []
    seen_coords = set()

    def _add_city(cn: Optional[str], ci: Optional[Dict[str, Any]]):
        if not cn or not ci:
            return
        coord_key = (round(float(ci["lat"]), 1), round(float(ci["lon"]), 1))
        if coord_key in seen_coords:
            return
        seen_coords.add(coord_key)
        found.append({
            "name": ci.get("name") or cn,
            "en": ci.get("en") or cn,
            "iso": ci.get("iso") or "",
            "country": ci.get("country") or "",
            "lat": float(ci["lat"]),
            "lon": float(ci["lon"]),
        })

    cn0, ci0 = detect_city_in_text(cleaned)
    _add_city(cn0, ci0)

    tokens = [re.sub(r"[،؟!.,:؛\"'()«»\-]", "", tok).strip() for tok in cleaned.split()]
    tokens = [t for t in tokens if len(t) >= 3]
    candidates: List[str] = []
    for i, tok in enumerate(tokens):
        if i + 1 < len(tokens):
            candidates.append(f"{tok} {tokens[i + 1]}")
        if tok not in _AR_GEO_STOPWORDS:
            candidates.append(tok)
            if len(tok) >= 4 and tok[0] in ("و", "ب", "ل", "ف"):
                stripped = tok[1:]
                if stripped not in _AR_GEO_STOPWORDS and len(stripped) >= 3:
                    candidates.append(stripped)

    for cand in candidates:
        if len(found) >= 5:
            break
        cn, ci = detect_city_in_text(cand)
        _add_city(cn, ci)

    return found


def _resolve_beat_geo_context(beat: Dict[str, Any]) -> Dict[str, Any]:
    from .rem import map_view

    narration = beat.get("narration") or ""
    on_screen = beat.get("title") or beat.get("on_screen") or ""
    combined_text = f"{on_screen} {narration}".strip()

    explicit_isos = [str(c).upper() for c in (beat.get("countries") or beat.get("highlight") or []) if c]
    detected_cities = _extract_all_cities(combined_text)

    explicit_pts = [
        p for p in (beat.get("points") or [])
        if isinstance(p, dict) and "lat" in p and "lon" in p
    ]
    raw_pts: List[Dict[str, Any]] = []
    seen_pts = set()
    for p in explicit_pts + detected_cities:
        key = (round(float(p["lat"]), 1), round(float(p["lon"]), 1))
        if key in seen_pts:
            continue
        seen_pts.add(key)
        raw_pts.append({
            "name": p.get("name") or p.get("en") or "",
            "lat": float(p["lat"]),
            "lon": float(p["lon"]),
        })

    if not explicit_isos:
        explicit_isos = _extract_countries_from_text(combined_text)
    for c in detected_cities:
        if c.get("iso") and c["iso"] not in explicit_isos:
            explicit_isos.append(c["iso"])

    # Only inherit video-level country if the beat's own narration/title has geographic intent or is the opening hook
    video_isos = [str(c).upper() for c in (beat.get("video_countries") or []) if c]
    video_pts = [
        p for p in (beat.get("video_cities") or [])
        if isinstance(p, dict) and "lat" in p and "lon" in p
    ]
    has_geo_keywords = bool(re.search(
        r"خريطة|موقع|حدود|تقع|مساح|جغرافي|شمال|جنوب|شرق|غرب|قارة|إقليم|عاصمت|دولة داخل|تحيط بها",
        combined_text,
    ))
    is_hook_beat = str(beat.get("tsx_id") or "").startswith("DynamicScene_hook") or beat.get("role") == "hook"
    if not explicit_isos and video_isos and (has_geo_keywords or is_hook_beat):
        explicit_isos = list(video_isos)
    if not raw_pts and video_pts and explicit_isos:
        for vp in video_pts[:4]:
            key = (round(float(vp["lat"]), 1), round(float(vp["lon"]), 1))
            if key not in seen_pts:
                seen_pts.add(key)
                raw_pts.append({
                    "name": vp.get("name") or "",
                    "lat": float(vp["lat"]),
                    "lon": float(vp["lon"]),
                })

    if not explicit_isos and not raw_pts:
        return {"is_geo": False, "ctxPath": "", "countries": [], "points": [], "target": {"x": 540.0, "y": 870.0}}

    try:
        g = get_geo()
        mv = map_view(g, {
            "countries": explicit_isos,
            "highlight": explicit_isos,
            "points": raw_pts,
        })
        countries_out = []
        for hl in mv.get("hl") or []:
            iso = hl.get("iso", "")
            cname = (g.c.get(iso) or {}).get("name") or iso
            countries_out.append({
                "iso": iso,
                "name": cname,
                "d": str(hl.get("d", "")),
                "cx": float(hl.get("cx", 540.0)),
                "cy": float(hl.get("cy", 870.0)),
            })
        pts_out = []
        for idx_p, pt in enumerate(mv.get("pts") or []):
            orig = raw_pts[idx_p] if idx_p < len(raw_pts) else {}
            lat = float(orig.get("lat", 0.0))
            lon = float(orig.get("lon", 0.0))
            pts_out.append({
                "name": pt.get("name") or orig.get("name") or "",
                "lat": lat,
                "lon": lon,
                "coords": _format_coords(lat, lon),
                "x": float(pt.get("x", 540.0)),
                "y": float(pt.get("y", 870.0)),
                "ly": float(pt.get("ly", 955.0)),
            })
        tgt = mv.get("target") or {"x": 540.0, "y": 870.0}
        raw_ctx = str(mv.get("ctx", ""))
        if len(raw_ctx) > 25000 and mv.get("neighbours"):
            acc_ctx: List[str] = []
            acc_len = 0
            for n in mv["neighbours"]:
                nd = str(n.get("d", ""))
                if not nd:
                    continue
                if acc_len + len(nd) > 25000 and acc_ctx:
                    break
                acc_ctx.append(nd)
                acc_len += len(nd)
            if acc_ctx:
                raw_ctx = "".join(acc_ctx)
        elif len(raw_ctx) > 25000:
            raw_ctx = raw_ctx[:25000]
        return {
            "is_geo": bool(countries_out or pts_out),
            "ctxPath": raw_ctx,
            "countries": countries_out,
            "points": pts_out,
            "target": {"x": float(tgt.get("x", 540.0)), "y": float(tgt.get("y", 870.0))},
        }
    except Exception as e:
        logger.debug("Geo context resolution failed: %s", e)
        return {"is_geo": False, "ctxPath": "", "countries": [], "points": [], "target": {"x": 540.0, "y": 870.0}}


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

def _should_use_llm_tsx() -> bool:
    val = os.environ.get("DYNAMIC_TSX_LLM", "").strip().lower()
    if val in ("0", "false", "no", "off"):
        return False
    if val == "force":
        return True
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return False
    main_mod = sys.modules.get("__main__")
    if getattr(main_mod, "__package__", None) == "unittest":
        return False
    return True


_LLM_TSX_SYSTEM = """You are an elite AI Video Architect, Creative Director, Documentary Infographics Designer, and Remotion Motion Graphics Engineer.
Every scene begins with a BLANK VISUAL CANVAS (1080x1920 vertical 9:16).
Your mission is to write 100% original React + Remotion TSX code that visually explains the EXACT historical, geographic, or scientific meaning of the spoken Arabic narration across the full duration of the scene.

TECHNICAL STACK (STRICT):
- Already imported symbols: React, AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig, Easing
- Inline <svg width={1080} height={1920} viewBox="0 0 1080 1920"> with rich, domain-specific SVG illustrations, diagrams, architectural cross-sections, topographic elevation profiles, and historical emblems.
- CRITICAL SVG STRUCTURE RULE: EVERY `<foreignObject x={...} y={...} width={...} height={...}>` MUST be placed INSIDE `<svg width={1080} height={1920} viewBox="0 0 1080 1920">...</svg>`! NEVER close `</svg>` before your `<foreignObject>` cards — `<foreignObject>` outside `<svg>` breaks positioning completely.
- STRICT FACTUAL GROUNDING: Every city, country, year, percentage, count, or number you display MUST come from the Video Title, Verified Facts, or Scene Narration. NEVER invent fake statistics, percentages, or counts (e.g., do NOT make up '96%', '94%', or '12' if not stated in the facts/narration), and NEVER invent unrelated historical cities or dates! Never truncate headlines with '...' or leave any card/banner empty.
- CSS transforms and <foreignObject x={...} y={...} width={...} height={...}> wrapping an inner <div dir="rtl" lang="ar" style={{fontFamily: "'Cairo', 'Noto Kufi Arabic', sans-serif", ...}}> for crisp Arabic typography and structured infographic cards.
- CRITICAL TS RULE FOR <foreignObject>: NEVER put `dir` or `lang` attributes on `<foreignObject>` itself — TypeScript `SVGProps<SVGForeignObjectElement>` rejects them! ALWAYS put `dir="rtl" lang="ar"` on the child `<div>` inside `<foreignObject>`.
- CRITICAL TS RULE FOR `interpolate`: NEVER pass `{clamp: true}`! Always use `{extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}`.

ARABIC TYPOGRAPHY & LEGIBILITY RULES (ZERO GARBLED OR INVERTED TEXT):
- NEVER use SVG `<text>` for Arabic words, and NEVER use `writingMode="tb"` or `writing-mode: vertical-rl`! Vertical text breaks Arabic letter joining and reverses glyph order (producing unreadable broken letters). Always render Arabic strings horizontally inside `<foreignObject><div dir="rtl" lang="ar" style={{fontFamily: "'Cairo', 'Noto Kufi Arabic', sans-serif", ...}}>`.
- NEVER apply negative scale transforms (`scale(-1, 1)` or `scale(1, Math.cos(...))` where `cos` becomes negative) to any group containing text, numbers, or years (e.g., never flip `1960` into mirrored `0691`!). If animating a card flip, use `Math.max(0.15, Math.abs(Math.cos(...)))`.
- High-Contrast Readability: Every text label, subtitle, and number MUST sit inside a high-contrast dark glass card (`background: 'rgba(6, 12, 24, 0.94)'`, `border: '1.5px solid ...'`, `borderRadius: 16`, `color: '#ffffff'` or `'#fde047'`). NEVER place gray text on a dark blue/black background, NEVER let background illustrations bleed through text cards, NEVER let any bar or card extend past `x = 980` (`width <= 920` from `x = 60`), and NEVER use `fontSize < 32px` for any readable card text (phone screens: 26px is unreadable) or linger at `opacity < 0.92` once a card has entered (snap card opacity from 0 -> 1 within 5-6 frames)!
- Wide Numeric Containers & Fast Counter Completion: Large counters (e.g. `14,000,000` or `1,600+`) MUST be inside a `<foreignObject>` at least `560px` wide (`x={260} width={560}`) with `direction: 'ltr'` and `whiteSpace: 'nowrap'` so digits are NEVER clipped. Quantity/percentage counters MUST finish rolling up to their final target value by `progress = 0.45`, and NEVER linger at `0` or `0%` after `p = 0.05` (start from `Math.round(target * 0.4)` -> `target`!). CRITICAL FOR YEARS: NEVER animate or roll historical years (e.g. `1945`, `1961`, `1989`, `2024`) with `interpolate()`! Always render the exact historical year string immediately from frame 0 (e.g. `1989`) with a crisp scale/opacity entrance so the viewer never sees a wrong intermediate year like `1959` or `1931`!

MULTI-PHASE VISUAL STORYTELLING & ANTI-OVERLAP RULES (MANDATORY):
Each scene lasts 5 to 9 seconds (`dur` frames, `p = frame / dur` from `0` to `1`) and covers a complete spoken Arabic sentence with 2–3 clauses (Phase 1: `0.00..0.35`, Phase 2: `0.35..0.70`, Phase 3: `0.70..1.00`):
- Immediate Visibility at Frame 0 (ZERO DEAD AIR): The scene background, Top Headline Banner (`y: 95..230`), AND the primary hero SVG visual stage MUST ALL be visible starting from `frame = 0` (`opacity` starting at `0.85 -> 1.0` within 8 frames)! NEVER hide the main illustration behind `ph2` (`p = 0.30+`) leaving an empty screen for the first 3–4 seconds!
- Phase 1 (`p: 0.0 -> 0.35`): Establish the primary visual subject (iconic SVG illustration, scale, beaker, monument, or diagram) + unified Top Headline Banner (`x: 60..1020, y: 95..230`, main title `fontSize: 52px..60px`, subtitle `fontSize: 32px`, `#fde047`).
- Phase 2 (`p: 0.35 -> 0.70`): Reveal the second layer of evidence/comparison synced to the middle clause (e.g., proportional comparison bars where bar width is strictly `(value / maxValue) * maxBarWidth`, dated historical milestone, or metric counter).
- Phase 3 (`p: 0.70 -> 1.00`): Reveal the final takeaway callout or interactive prompt card. For `cta` / `loop` scenes, include 2–3 concise visual recap chips + animated callout emblem so the ending feels rich and energetic, never just one lone icon.
- ZERO CARD OR ILLUSTRATION COLLISION & ZERO DEAD CANVAS SPACE (MANDATORY):
  * NEVER leave 50%+ of the screen as a flat black/dark void with a tiny icon or small card floating in the middle!
  * ALWAYS render a multi-layered atmospheric SVG backdrop behind your scene: radial spotlight glow (`<radialGradient>`), subtle architectural/topographic depth lines or horizon ground plane, and soft ambient light beams matching the topic mood. NEVER scatter random stray `+`/`×`/`★` stars or confetti particles in empty corners.
  * Scale hero SVG illustrations generously (`width: 500..820px`, `height: 380..540px`) and use full-width structured cards (`x: 60, width: 960` in Slot B/C) so the visual stage (`y: 110..1430`) feels rich (the lowest card/illustration MUST end at `y >= 1250`; never leave the bottom third empty), balanced, and cinematic from top to bottom.
  * NEVER draw Phase 2 bars/cards or Phase 3 takeaway cards on top of a persistent Phase 1 SVG illustration or on top of another card!
  * Use strict non-overlapping vertical slots:
    - Slot A (Top Hero / Metric): `y: 265..590`
    - Slot B (Primary Visual Stage / Comparison): `y: 615..1060`
    - Slot C (Phase 3 Takeaway / Callout): `y: 1085..1435`
  * If Phase 2 or Phase 3 renders a card in the SAME slot or corner as Phase 1, you MUST fade Phase 1 out completely to `opacity: 0` BEFORE Phase 2 enters (e.g. Phase 1 `interpolate(p, [0.42, 0.48], [1, 0], ...)` and Phase 2 `interpolate(p, [0.50, 0.56], [0, 1], ...)`). NEVER leave two cards overlapping in the same slot!
  * NEVER draw empty dashed placeholder boxes (`<rect strokeDasharray=...>` with nothing inside) waiting to be filled — every visible container must hold active content from frame 0 or stay hidden until it enters.
- MULTI-CARD GRID SPACING: When displaying multiple city/country badges (e.g., 3 to 5 capitals), NEVER place them at tight radial/circular angles where bounding boxes overlap! Use a clean 2-column grid (`x = 290` and `x = 790`, rows separated by at least `155px` vertically: `y = 650, 810, 970`) with `width <= 420px` per card.

GEOGRAPHIC & ARCHITECTURAL REALISM (NEVER DO THESE):
- Land monuments (such as the Giza Pyramids, Sphinx, Eiffel Tower, Tokyo Tower, Parliament/Capitol domes) MUST stand firmly on a solid ground, desert plateau, or stone terrace horizon line! If a river (like the Nile or Seine) is shown, draw the river in a distinct lower foreground band below the bank — NEVER draw pyramids or buildings floating in the middle of blue water!
- NEVER draw fake random green oval blobs on a globe to represent continents; use clean latitude/longitude wireframe meridians, orbital rings, and structured emblem cards.
- NEVER draw abstract geometric filler unrelated to the topic.

STRICT CODE & SAFE ZONE RULES:
1. Output ONLY raw TypeScript/JSX for ONE exported component (NO markdown fences, NO import lines, NO export default, NEVER declare `const _GEO_...`).
2. Exact signature:
   export const <TSX_ID>: React.FC<{frame?: number; fps?: number; dur?: number}> = (props) => {
3. MUST call hooks unconditionally on lines 1-2 of the component body BEFORE any conditions:
   const currentFrame = useCurrentFrame();
   const {fps: videoFps} = useVideoConfig();
   const frame = props.frame ?? currentFrame;
   const fps = props.fps ?? videoFps;
   const dur = Math.max(1, props.dur ?? 150);
4. Wrap outer JSX inside <AbsoluteFill style={{pointerEvents: 'none', overflow: 'hidden'}}> with NO `background` on it (the video's own ground shows through; a VIDEO THEME block in the user message gives the colours).
5. NO external assets: NO <img>, NO <image>, NO <canvas>, NO fetch, NO require, NO window, NO document, NO Three.js.
6. Safe layout zones on 1080x1920:
   - Top header/title banner: `x: 60..1020, y: 110..240` (keep `y >= 110` so camera pan/zoom never clips the top edge, and NEVER place any icon, badge, or illustration inside `y: 90..245` overlapping the header text!)
   - Reserved Smart Map Overlay HUD corner (when scene mentions a country/city): `y: 255..605` on the designated HUD side (`left: 48..468` on even scenes, `right: 612..1032` on odd scenes). Keep text cards and bar chart columns out of that corner, and NEVER draw a duplicate background country map!
   - Primary visual & infographic stage: `x: 60..1020, y: 615..1440` (plus the non-HUD side of `y: 260..605`).
   - Bottom Caption Safe Zone: keep `y: 1465..1920` 100% EMPTY (no cards, no text, no numbers, no labels below `y = 1455`) so synchronized subtitles (`y: 1500..1680`) never overlap with scene elements!
7. TypeScript strict correctness: never reference undefined variables, ensure all attributes/styles match React.CSSProperties & SVGProps<T>, escape quotes inside strings."""


def _build_llm_scene_prompts(
    beat: Dict[str, Any],
    scene_index: int,
    total_scenes: int,
    geo_ctx: Dict[str, Any],
    prev_narration: str = "",
    next_narration: str = "",
) -> Tuple[str, str]:
    tsx_id = _clean_id(beat.get("tsx_id") or f"DynamicScene_{scene_index}")
    narration = _clean_text(beat.get("narration") or "")
    title = _clean_text(beat.get("title") or beat.get("on_screen") or "")
    concept = _clean_text(beat.get("concept") or "")
    role = _clean_text(beat.get("id") or beat.get("role") or f"scene_{scene_index}")
    video_title = _clean_text(beat.get("video_title") or "")
    facts_summary = _clean_text(beat.get("facts_summary") or "")
    accent = beat.get("accent") or (_TSX_THEME or {}).get("accent") or "#38bdf8"
    sec = beat.get("secondary_accent") or (_TSX_THEME or {}).get("accent2") or "#f59e0b"

    # Split full scene narration into 2-3 timed semantic clauses so the LLM animates them progressively
    clauses = [c.strip() for c in re.split(r"[،,؛;:.!؟?\-]+", narration) if c.strip()]
    if len(clauses) <= 1 and len(narration.split()) >= 8:
        words = narration.split()
        mid = len(words) // 2
        clauses = [" ".join(words[:mid]), " ".join(words[mid:])]
    elif not clauses:
        clauses = [narration]

    phase_lines = []
    n_cl = len(clauses)
    for ci, cl_txt in enumerate(clauses[:3]):
        p_start = round(ci / min(n_cl, 3), 2)
        p_end = round((ci + 1) / min(n_cl, 3), 2)
        phase_lines.append(f"  - Phase {ci + 1} (progress {p_start:.2f} -> {p_end:.2f}): \"{cl_txt}\"")
    phases_block = "\n".join(phase_lines)

    scene_archetypes = [
        "ARCHETYPE 1 (Historical & Geographic Emblem Stage): Iconic architectural landmark & historical comparison cards with animated timeline/metrics (NO background country map).",
        "ARCHETYPE 2 (Split Comparative Stage): Side-by-side or upper/lower divided comparison stage contrasting two cities, eras, or concepts with custom SVG icons and strictly proportional bars (NO country map).",
        "ARCHETYPE 3 (Architectural & Monument Illustration): Detailed multi-layered custom SVG architectural facade/monument/dome illustration standing on a solid ground plateau with annotated callout cards (NO country map).",
        "ARCHETYPE 4 (Historical Chronicle Timeline): Chronological timeline conduit with dated milestone badges, historical emblems, and progressive wave animation (NO country map).",
        "ARCHETYPE 5 (Spatial / Urban Planning Diagram): Urban plan, elevation profile cross-section, or comparative scale diagram (NO country map).",
        "ARCHETYPE 6 (Institutional / System Flow Diagram): Connected hierarchy diagram showing institutions, laws, or cause-and-effect nodes with animated SVG signal pulses (NO country map).",
        "ARCHETYPE 7 (Data & Scale Infographic): Proportional population/scale comparison visual metaphor and wide animated metric counters (NO country map).",
        "ARCHETYPE 8 (Cinematic Conclusion & Interactive Prompt): Bold emblematic summary visual in `y: 620..940` and non-overlapping call-to-action prompt in `y: 980..1240` (NO country map).",
    ]
    assigned_archetype = scene_archetypes[scene_index % len(scene_archetypes)]
    hud_side = "top-left (x: 48..468, y: 256..600)" if scene_index % 2 == 0 else "top-right (x: 612..1032, y: 256..600)"

    split_hint = ""
    if re.search(r"شطر|تقسيم|انقسام|مدينتين|عاصمتين|حدود|توزيع|فصل|معاهدة", narration):
        split_hint = (
            "- CREATIVE SPLIT/MAP VISUAL: Since this narration describes dividing/splitting two places or powers, "
            "draw a stylized topographic/territory silhouette with TWO glowing location pin markers (e.g. 📍 / target rings), "
            "connected/divided by an animated glowing ZIGZAG split-fault line (`M ... L ...` with `pathLength={1}` and `strokeDashoffset` animating from `1 -> 0`) "
            "so the viewer immediately sees the geographic/political split!\n"
        )

    geo_note = (
        f"\nMANDATORY VISUAL COMPOSITION & MAP HUD COORDINATION FOR SCENE {scene_index + 1}:\n"
        f"- Assigned Visual Composition Mode: {assigned_archetype}\n"
        f"{split_hint}"
        f"- A live interactive `MapOverlayLayer` HUD may render at `{hud_side}` (`y: 256..600`). Keep `{hud_side}` clear of text cards and counters; place upper Slot A cards on the opposite side (`y: 265..590`), Slot B in `y: 615..1060`, and Slot C in `y: 1085..1435` without overlapping.\n"
        f"- Keep `y: 1465..1920` 100% empty for bottom Captions.\n"
    )

    concept_line = f'Director Visual Concept: "{concept}"\n' if concept else ""
    video_ctx_line = f'Full Video Title / Topic: "{video_title}"\n' if video_title else ""
    facts_line = f'Verified Historical/Geographic Facts for this Video: "{facts_summary}"\n' if facts_summary else ""
    vi = beat.get("visual_intelligence") if isinstance(beat.get("visual_intelligence"), dict) else {}
    vi_lines = ""
    if vi:
        vi_parts = []
        if vi.get("semantic_goal"):
            vi_parts.append(f"Semantic Goal: {vi['semantic_goal']}")
        if vi.get("historical_era"):
            vi_parts.append(f"Historical Era: {vi['historical_era']} (is_historical={bool(vi.get('is_historical'))})")
        if vi.get("entities"):
            vi_parts.append(f"Key Entities: {', '.join(str(x) for x in vi['entities'])}")
        if vi.get("relationships"):
            rel_strs = [f"{r.get('source')} -> {r.get('relation')} -> {r.get('target')}" for r in vi["relationships"][:3] if isinstance(r, dict)]
            if rel_strs:
                vi_parts.append(f"Entity Relationships: {' | '.join(rel_strs)}")
        if vi.get("avoid"):
            vi_parts.append(f"Anachronisms/Items to AVOID: {vi['avoid']}")
        if vi_parts:
            vi_lines = "VISUAL INTELLIGENCE DOSSIER:\n- " + "\n- ".join(vi_parts) + "\n"

    user_prompt = (
        f"Design and code Scene {scene_index + 1} of {total_scenes} (`{tsx_id}`) for an Arabic documentary YouTube Short.\n"
        f"{video_ctx_line}"
        f"{facts_line}"
        f"{vi_lines}"
        f"Scene Role: {role}\n"
        f"Full Scene Spoken Narration: \"{narration}\"\n"
        f"On-screen Headline: \"{title}\"\n"
        f"Timed Visual Progression Phases across Scene Duration (`progress = frame / dur`):\n"
        f"{phases_block}\n"
        f"{concept_line}"
        f"Previous Scene Narration: \"{prev_narration}\"\n"
        f"Next Scene Narration: \"{next_narration}\"\n"
        f"Suggested Accent Colors (customize atmosphere to fit the scene's story): primary={accent}, secondary={sec}\n"
        f"{_theme_block()}"
        f"{geo_note}"
        f"\nCreate a rich, concrete, multi-phase visual storytelling composition specifically explaining this scene's narration within the context of \"{video_title}\". "
        f"Include recognizable domain-specific SVG illustrations/diagrams + crisp horizontal Arabic infographic cards/labels via `<foreignObject><div dir=\"rtl\" lang=\"ar\" style={{{{fontFamily: \"'Cairo', 'Noto Kufi Arabic', sans-serif\"}}}}>...</div></foreignObject>`. "
        f"Export exact component symbol `export const {tsx_id}: React.FC<{{frame?: number; fps?: number; dur?: number}}> = (props) => {{ ... }};`."
    )
    return _LLM_TSX_SYSTEM, user_prompt


_AR_LITERAL_RE = re.compile(
    r"""(?:>([^<>{}]*[؀-ۿ][^<>{}]*)<)|(?:['"`]([^'"`\n]*[؀-ۿ][^'"`\n]*)['"`])"""
)


def _arabic_texts(code: str) -> set:
    """Distinct non-empty Arabic text nodes/string literals in a TSX component."""
    return {t.strip() for m in _AR_LITERAL_RE.findall(code) for t in m if t.strip()}


def _sanitize_llm_tsx(raw_code: str, tsx_id: str) -> Optional[str]:
    if not raw_code or not isinstance(raw_code, str):
        return None
    code = raw_code.strip()
    # Strip markdown code fences
    fence_match = re.search(r"```(?:tsx|typescript|ts|jsx|javascript)?\s*\n(.*?)```", code, flags=re.DOTALL | re.IGNORECASE)
    if fence_match:
        code = fence_match.group(1).strip()
    else:
        code = re.sub(r"^```[a-zA-Z]*\s*", "", code)
        code = re.sub(r"\s*```$", "", code).strip()

    # Strip accidental imports or registry exports
    cleaned_lines = []
    for line in code.splitlines():
        st = line.strip()
        if st.startswith("import ") or st.startswith("export default") or "DYNAMIC_SCENE_REGISTRY" in st:
            continue
        cleaned_lines.append(line)
    code = "\n".join(cleaned_lines).strip()

    # Strip hallucinated _GEO_ re-declarations before export const
    m_exp = re.search(r"\bexport\s+const\s+[A-Za-z_]", code)
    if m_exp and "_GEO_" in code[: m_exp.start()]:
        code = code[m_exp.start() :]

    # Normalize component export declaration name to exact tsx_id
    decl_pat = r"export\s+const\s+[A-Za-z_][A-Za-z0-9_]*\s*(?::\s*React\.FC<[^>]+>\s*)?=\s*"
    if re.search(decl_pat, code):
        code = re.sub(
            decl_pat,
            f"export const {tsx_id}: React.FC<{{frame?: number; fps?: number; dur?: number}}> = ",
            code,
            count=1,
        )
    elif re.search(rf"const\s+{re.escape(tsx_id)}\b", code):
        code = re.sub(rf"\bconst\s+{re.escape(tsx_id)}\b", f"export const {tsx_id}", code, count=1)
    elif "useCurrentFrame" in code and re.search(r"\breturn\s*(?:\(|<)", code):
        body = code.strip()
        if body.endswith("};") or body.endswith("}"):
            code = f"export const {tsx_id}: React.FC<{{frame?: number; fps?: number; dur?: number}}> = (props) => {{\n{body}"
        else:
            code = f"export const {tsx_id}: React.FC<{{frame?: number; fps?: number; dur?: number}}> = (props) => {{\n{body}\n}};"
    else:
        return None

    forbidden_substrings = (
        "<img",
        "<image",
        "<canvas",
        "three.js",
        "from 'three'",
        'from "three"',
        "webgl",
        "fetch(",
        "require(",
        "window.",
        "document.",
        "dangerouslysetinnerhtml",
    )
    lower = code.lower()
    if any(tok in lower for tok in forbidden_substrings):
        return None
    # Strip vertical writingMode / writing-mode attributes that disconnect and reverse Arabic letters
    code = re.sub(
        r'\s+writingMode\s*=\s*(?:"[^"]*"|\'[^\']*\'|\{[^}]*\})',
        "",
        code,
    )
    code = re.sub(
        r"writingMode\s*:\s*(?:\"[^\"]*\"|'[^']*')\s*,?",
        "",
        code,
    )
    code = re.sub(
        r"writing-mode\s*:\s*[^;\"']+;?",
        "",
        code,
    )
    # Prevent 3D flip animations from inverting/mirroring text via negative Math.cos inside scale(...)
    code = re.sub(
        r"scale\(\s*1\s*,\s*\$\{\s*Math\.cos\(([^}]+)\)\s*\}\s*\)",
        r"scale(1, ${Math.max(0.12, Math.abs(Math.cos(\1)))})",
        code,
    )
    code = re.sub(
        r"scale\(\s*\$\{\s*Math\.cos\(([^}]+)\)\s*\}\s*,\s*1\s*\)",
        r"scale(${Math.max(0.12, Math.abs(Math.cos(\1)))}, 1)",
        code,
    )
    # React SVGProps<SVGForeignObjectElement> forbids `dir` and `lang` on <foreignObject>;
    # strip them from <foreignObject ...> and inject onto inner <div> if missing.
    code = re.sub(
        r"(<foreignObject\b[^>]*?)\s+(?:dir|lang)\s*=\s*(?:\"[^\"]*\"|'[^']*'|\{[^}]*\})([^>]*>)",
        r"\1\2",
        code,
    )
    # Run twice in case both `dir` and `lang` were on the same <foreignObject>
    code = re.sub(
        r"(<foreignObject\b[^>]*?)\s+(?:dir|lang)\s*=\s*(?:\"[^\"]*\"|'[^']*'|\{[^}]*\})([^>]*>)",
        r"\1\2",
        code,
    )
    code = re.sub(
        r"(<foreignObject\b[^>]*>\s*<div\b)(?![^>]*\bdir\s*=)",
        r'\1 dir="rtl" lang="ar"',
        code,
    )
    # Clamp static numeric <foreignObject y={N} height={H}> within safe vertical bounds [105, 1455]
    def _clamp_fo_bounds(match: re.Match) -> str:
        tag = match.group(0)
        ym = re.search(r"\by=\{(\d+(?:\.\d+)?)\}", tag)
        if not ym:
            return tag
        yv = float(ym.group(1))
        hm = re.search(r"\bheight=\{(\d+(?:\.\d+)?)\}", tag)
        hv = float(hm.group(1)) if hm else 0.0
        new_y = max(105.0, yv)
        if hv > 0 and new_y + hv > 1455.0:
            new_y = max(105.0, 1455.0 - hv)
        if new_y != yv:
            tag = re.sub(r"\by=\{\d+(?:\.\d+)?\}", f"y={{{int(round(new_y))}}}", tag, count=1)
        return tag

    code = re.sub(r"<foreignObject\b[^>]*>", _clamp_fo_bounds, code)
    # Prevent static numeric <foreignObject> boxes without dynamic opacity from overlapping vertically
    _fo_boxes: List[Tuple[int, int, float, float, float, float]] = []
    for m in re.finditer(r"<foreignObject\b[^>]*>", code):
        tag = m.group(0)
        if "opacity" in tag:
            continue
        ym = re.search(r"\by=\{(\d+(?:\.\d+)?)\}", tag)
        hm = re.search(r"\bheight=\{(\d+(?:\.\d+)?)\}", tag)
        if not ym or not hm:
            continue
        xm = re.search(r"\bx=\{(\d+(?:\.\d+)?)\}", tag)
        wm = re.search(r"\bwidth=\{(\d+(?:\.\d+)?)\}", tag)
        xv = float(xm.group(1)) if xm else 0.0
        wv = float(wm.group(1)) if wm else 1080.0
        yv = float(ym.group(1))
        hv = float(hm.group(1))
        _fo_boxes.append((m.start(), m.end(), xv, yv, wv, hv))

    if len(_fo_boxes) > 1:
        # Sort by y ascending and resolve vertical collisions in reverse offset order
        placed_boxes: List[Tuple[float, float, float, float]] = []
        adjustments: Dict[int, float] = {}
        for start, _end, xv, yv, wv, hv in sorted(_fo_boxes, key=lambda b: b[3]):
            new_y = yv
            for px, py, pw, ph in placed_boxes:
                h_overlap = (xv < px + pw) and (px < xv + wv)
                v_overlap = (new_y < py + ph + 16.0) and (py < new_y + hv + 16.0)
                if h_overlap and v_overlap:
                    candidate_y = py + ph + 16.0
                    if candidate_y + hv <= 1455.0:
                        new_y = candidate_y
            placed_boxes.append((xv, new_y, wv, hv))
            if new_y != yv:
                adjustments[start] = new_y
        if adjustments:
            for start, end, _xv, _yv, _wv, _hv in sorted(_fo_boxes, key=lambda b: b[0], reverse=True):
                if start in adjustments:
                    tag = code[start:end]
                    new_tag = re.sub(
                        r"\by=\{\d+(?:\.\d+)?\}",
                        f"y={{{int(round(adjustments[start]))}}}",
                        tag,
                        count=1,
                    )
                    code = code[:start] + new_tag + code[end:]
    # Fix invalid `{ clamp: true }` in Remotion interpolate(...) options
    code = re.sub(
        r"\{\s*clamp\s*:\s*true\s*\}",
        "{extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}",
        code,
    )
    # Ensure numeric literal inputRange arrays in interpolate(...) are strictly monotonically increasing
    def _fix_interpolate_range(m: re.Match) -> str:
        prefix, arr_str = m.group(1), m.group(2)
        parts = [x.strip() for x in arr_str.split(",") if x.strip()]
        try:
            nums = [float(x) for x in parts]
        except ValueError:
            return m.group(0)
        if len(nums) < 2:
            return m.group(0)
        changed = False
        for idx in range(1, len(nums)):
            if nums[idx] <= nums[idx - 1]:
                nums[idx] = round(nums[idx - 1] + 0.001, 4)
                changed = True
        if not changed:
            return m.group(0)
        fixed = ", ".join(str(int(n)) if n.is_integer() else str(n) for n in nums)
        return f"{prefix}[{fixed}]"

    code = re.sub(
        r"(interpolate\s*\([^,]+,\s*)\[([^\[\]]+)\]",
        _fix_interpolate_range,
        code,
    )
    # Fix <foreignObject> accidentally placed after </svg> (outside SVG coordinate space)
    if code.count("<svg") == 1 and code.count("</svg>") == 1 and "<foreignObject" in code:
        svg_close_idx = code.find("</svg>")
        last_fo_idx = code.rfind("<foreignObject")
        abs_close_idx = code.rfind("</AbsoluteFill>")
        if last_fo_idx > svg_close_idx and abs_close_idx > last_fo_idx:
            code = code[:svg_close_idx] + code[svg_close_idx + len("</svg>"):abs_close_idx] + "\n      </svg>\n    " + code[abs_close_idx:]
    if "useCurrentFrame" not in code or ("AbsoluteFill" not in code and "<svg" not in code and "<div" not in code):
        return None
    # Guard React Rules of Hooks: no early `return` before useCurrentFrame/useVideoConfig
    first_hook = min(
        code.find("useCurrentFrame"),
        code.find("useVideoConfig") if "useVideoConfig" in code else len(code),
    )
    if re.search(r"\breturn\s*(?:\(|null|<)", code[:first_hook]):
        return None
    return code


def _synthesize_beat_tsx_via_llm(
    beat: Dict[str, Any],
    scene_index: int,
    total_scenes: int,
    geo_ctx: Dict[str, Any],
    prev_narration: str = "",
    next_narration: str = "",
) -> Optional[str]:
    import time
    from .llm_router import get_router

    tsx_id = _clean_id(beat.get("tsx_id") or f"DynamicScene_{scene_index}")
    sys_prompt, user_prompt = _build_llm_scene_prompts(
        beat, scene_index, total_scenes, geo_ctx, prev_narration, next_narration
    )
    resp = None
    last_err: Optional[Exception] = None
    for attempt in range(2):
        try:
            resp = get_router().dispatch(
                role="director",
                system=sys_prompt,
                user=user_prompt,
                temperature=0.82,
                json_mode=False,
                timeout=90,
            )
            last_err = None
            break
        except Exception as e:
            last_err = e
            if attempt == 0:
                logger.warning("LLM TSX dispatch attempt 1 failed for %s (retrying): %s", tsx_id, e)
                time.sleep(1.5)
    if last_err is not None or resp is None:
        logger.warning("LLM TSX synthesis skipped for scene %d (%s): %s", scene_index, tsx_id, last_err)
        return None
    sanitized = _sanitize_llm_tsx(resp.content, tsx_id)
    # Richness gate: a scene with (almost) no Arabic text (e.g. three bare bars) is an empty frame, not a scene.
    if sanitized is not None and len(_arabic_texts(sanitized)) < 3:
        logger.warning("LLM TSX rejected for scene %d (%s): fewer than 3 Arabic text nodes", scene_index, tsx_id)
        return None
    if sanitized is None:
        logger.warning(
            "LLM TSX rejected by sanitizer for scene %d (%s); raw_len=%d head=%r",
            scene_index,
            tsx_id,
            len(resp.content or ""),
            (resp.content or "")[:160],
        )
    return sanitized


def _run_tsc_check() -> Tuple[bool, List[int], str]:
    tsc_bin = ROOT / "remotion" / "node_modules" / ".bin" / ("tsc.cmd" if os.name == "nt" else "tsc")
    tsconfig = ROOT / "remotion" / "tsconfig.json"
    if not tsc_bin.exists() or not tsconfig.exists():
        return True, [], ""
    try:
        proc = subprocess.run(
            [str(tsc_bin), "-p", str(tsconfig), "--noEmit"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=35,
        )
        if proc.returncode == 0:
            return True, [], ""
        out = (proc.stdout or "") + "\n" + (proc.stderr or "")
        err_lines: List[int] = []
        for m in re.finditer(r"DynamicScenes\.tsx\((\d+),", out):
            err_lines.append(int(m.group(1)))
        return False, sorted(set(err_lines)), out
    except Exception as e:
        logger.warning("tsc check invocation error: %s", e)
        return True, [], ""


def _top_level_args(args: str) -> List[str]:
    parts, depth, cur, q = [], 0, [], ""
    for ch in args:
        if q:
            q = "" if ch == q else q
        elif ch in "'\"`":
            q = ch
        elif ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        elif ch == "," and depth == 0:
            parts.append("".join(cur))
            cur = []
            continue
        cur.append(ch)
    parts.append("".join(cur))
    return parts


def _fix_color_interpolate(code: str) -> str:
    """Remotion's interpolate() throws on color strings ("Non-numeric strings can only be interpolated using
    Easing.step1") and killed the whole render. LLM code does this often: switch such calls to interpolateColors."""
    out, i = [], 0
    pat = re.compile(r"\binterpolate(?:Colors)?\(")
    while True:
        m = pat.search(code, i)
        if not m:
            out.append(code[i:])
            break
        depth, j = 1, m.end()
        while j < len(code) and depth:
            depth += (code[j] == "(") - (code[j] == ")")
            j += 1
        args = code[m.end(): j - 1]
        is_color = m.group(0).startswith("interpolateColors") or re.search(r"""\[\s*['"](?:#|rgb|hsl)""", args) is not None
        out.append(code[i: m.start()])
        if is_color:
            args = ",".join(_top_level_args(args)[:3])  # interpolateColors takes no extrapolate/easing options
        out.append(("interpolateColors(" if is_color else "interpolate(") + args + ")")
        i = j
    return "".join(out)


def _assemble_dynamic_file(header: str, blocks: List[str], registry_entries: List[str]) -> str:
    blocks = [_fix_color_interpolate(b) for b in blocks]
    return (
        header
        + "\n\n".join(blocks)
        + "\n\nexport const DYNAMIC_SCENE_REGISTRY: Record<string, React.FC<{frame?: number; fps?: number; dur?: number}>> = {\n"
        + "\n".join(registry_entries)
        + "\n};\n"
    )


def _repair_beat_tsx_via_llm(
    tsx_id: str,
    broken_code: str,
    tsc_error: str,
    beat: Dict[str, Any],
    geo_ctx: Dict[str, Any],
) -> Optional[str]:
    """Asks the AI architect to fix TypeScript compiler errors in its own generated TSX before ever falling back."""
    try:
        from .llm_router import get_router

        sys_prompt = _LLM_TSX_SYSTEM
        geo_hint = f"Note: `_GEO_{tsx_id}` IS already declared above; do NOT redeclare it." if geo_ctx.get("is_geo") else ""
        user_prompt = (
            f"The TypeScript compiler rejected component `{tsx_id}` with these errors:\n"
            f"{tsc_error[:900]}\n\n"
            f"{geo_hint}\n"
            f"Spoken narration: \"{_clean_text(beat.get('narration') or '')}\"\n"
            f"Fix ALL TypeScript errors and return ONLY the corrected `export const {tsx_id}: React.FC<{{frame?: number; fps?: number; dur?: number}}> = (props) => {{ ... }};` code (preserving the custom SVG illustration, no markdown fences, no imports):\n\n"
            f"{broken_code}"
        )
        resp = get_router().dispatch(
            role="director",
            system=sys_prompt,
            user=user_prompt,
            temperature=0.3,
            json_mode=False,
            timeout=65,
        )
        return _sanitize_llm_tsx(resp.content, tsx_id)
    except Exception as e:
        logger.warning("LLM TSX repair failed for %s: %s", tsx_id, e)
        return None


def _compute_beat_tsx_sig(beat: Dict[str, Any], geo_ctx: Dict[str, Any]) -> str:
    import hashlib
    payload = json.dumps(
        {
            "sig_v": 12,
            "theme": _theme_sig(),
            "tsx_id": beat.get("tsx_id", ""),
            "narration": _clean_text(beat.get("narration") or ""),
            "title": _clean_text(beat.get("title") or beat.get("on_screen") or ""),
            "concept": _clean_text(beat.get("concept") or ""),
            "video_title": _clean_text(beat.get("video_title") or ""),
            "is_geo": bool(geo_ctx.get("is_geo")),
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]


def _extract_verified_llm_blocks(existing_text: str) -> Dict[Tuple[str, str], str]:
    pattern = re.compile(
        r"/\*\s*@llm_verified:([A-Za-z0-9_]+):([a-f0-9]+)\s*\*/\s*\n(.*?)(?=\n/\*\s*@llm_verified:|\nexport const DYNAMIC_SCENE_REGISTRY)",
        flags=re.DOTALL,
    )
    out: Dict[Tuple[str, str], str] = {}
    for m in pattern.finditer(existing_text):
        tsx_id, sig, code = m.group(1), m.group(2), m.group(3).strip()
        if code:
            out[(tsx_id, sig)] = code
    return out


def _load_tsx_cache() -> Dict[Tuple[str, str], str]:
    cache_file = DYNAMIC_TSX_PATH.parent / ".tsx_cache.json"
    out: Dict[Tuple[str, str], str] = {}
    if cache_file.exists():
        try:
            data = json.loads(cache_file.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                for k, v in data.items():
                    if ":" in k and isinstance(v, str) and v.strip():
                        tid, sig = k.split(":", 1)
                        out[(tid, sig)] = v
        except Exception:
            pass
    if DYNAMIC_TSX_PATH.exists():
        try:
            out.update(_extract_verified_llm_blocks(DYNAMIC_TSX_PATH.read_text(encoding="utf-8")))
        except Exception:
            pass
    return out


def _save_tsx_cache(entries: Dict[Tuple[str, str], str]) -> None:
    cache_file = DYNAMIC_TSX_PATH.parent / ".tsx_cache.json"
    try:
        existing = _load_tsx_cache()
        existing.update(entries)
        serializable = {f"{tid}:{sig}": code for (tid, sig), code in list(existing.items())[-120:]}
        cache_file.write_text(json.dumps(serializable, ensure_ascii=False, indent=1), encoding="utf-8")
    except Exception:
        pass


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
