"""Offline Visual Assets & Motion Tools for Shorts Studio (`pipeline/visual_tools.py`).

Provides deterministic offline search, validation, transition picking, QA visual review,
credit tracking (`credits.json`), and natural-language chat edit routing for:
- Icons (`search_icons`)
- Emoji (`search_emoji`)
- Flags (`resolve_flag`)
- Lottie (`search_lottie`)
- Animated Charts & Counters (`draw_chart`)
- Scene Transitions (`pick_transitions`)
- Typography & Layout Components (`build_typography_component`)
"""
from __future__ import annotations
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from .geo import AR_ISO3

ROOT = Path(__file__).resolve().parent.parent
PKG_ASSETS = ROOT / "packages" / "assets"


VALID_CHART_TYPES = {"bar", "line", "pie", "donut", "counter", "progress_ring", "timeline"}
VALID_CHART_ANIMS = {"spring", "grow", "draw", "stagger"}


def draw_chart(spec: Dict[str, Any]) -> Dict[str, Any]:
    """Tool `draw_chart({ type, data, style, animation, durationInFrames })`:
    Validates chart configuration and returns a normalized visual element `{ kind: 'chart', spec }`.
    """
    if not isinstance(spec, dict):
        raise ValueError("draw_chart expects a dictionary spec.")
    ctype = str(spec.get("type", "bar")).strip().lower()
    if ctype not in VALID_CHART_TYPES:
        raise ValueError(f"Unsupported chart type '{ctype}'. Must be one of {sorted(VALID_CHART_TYPES)}.")

    raw_data = spec.get("data")
    if not isinstance(raw_data, list) or len(raw_data) == 0:
        raise ValueError("draw_chart requires a non-empty 'data' array.")

    norm_data = []
    for idx, d in enumerate(raw_data[:12]):
        if not isinstance(d, dict):
            raise ValueError(f"data[{idx}] must be an object with 'label' and 'value'.")
        label = str(d.get("label", f"#{idx + 1}")).strip()
        try:
            val = float(d.get("value", 0))
        except (TypeError, ValueError):
            raise ValueError(f"data[{idx}].value must be numeric.")
        item: Dict[str, Any] = {"label": label, "value": val}
        if d.get("color"):
            item["color"] = str(d["color"])
        if d.get("year"):
            item["year"] = str(d["year"])
        norm_data.append(item)

    raw_style = spec.get("style") if isinstance(spec.get("style"), dict) else {}
    norm_style = {
        "title": str(raw_style.get("title", "")).strip() or undefined_none(raw_style.get("title")),
        "unit": str(raw_style.get("unit", "")).strip(),
        "rtl": bool(raw_style.get("rtl", True)),
        "arabicNumerals": bool(raw_style.get("arabicNumerals", True)),
        "width": max(200, min(1080, int(raw_style.get("width", 900)))),
        "height": max(160, min(1400, int(raw_style.get("height", 620)))),
    }
    if not norm_style["title"]:
        norm_style.pop("title", None)

    anim = str(spec.get("animation", "spring")).strip().lower()
    if anim not in VALID_CHART_ANIMS:
        anim = "spring"

    dur = max(15, min(600, int(spec.get("durationInFrames", 90))))

    return {
        "kind": "chart",
        "spec": {
            "type": ctype,
            "data": norm_data,
            "style": norm_style,
            "animation": anim,
            "durationInFrames": dur,
        },
    }


def undefined_none(v: Any) -> None:
    return None


def pick_transitions(scene_count: int, seed: int = 42) -> List[Dict[str, Any]]:
    """Transition picker for the Storyboard Agent per scene boundary.
    Rule: vary transitions across scene boundaries and never repeat the same transition back-to-back.
    """
    pool = ["slide", "wipe", "clock-wipe", "fade", "flip"]
    directions = ["from-right", "from-left", "from-bottom", "from-top"]
    sfx_cycle = ["whoosh", "whip", "pageTurn", "switch"]
    out: List[Dict[str, Any]] = []
    prev_type = "none"

    for i in range(scene_count):
        if i == 0:
            out.append({"type": "none", "durationInFrames": 12, "sfx": "none"})
            continue
        idx = (seed + i * 3) % len(pool)
        if pool[idx] == prev_type:
            idx = (idx + 1) % len(pool)
        chosen = pool[idx]
        prev_type = chosen
        out.append({
            "type": chosen,
            "direction": directions[(seed + i) % len(directions)],
            "durationInFrames": 14,
            "sfx": sfx_cycle[(seed + i) % len(sfx_cycle)],
        })
    return out


def normalize_visual_element(el: Dict[str, Any], preferred_icon_set: str = "lucide") -> Optional[Dict[str, Any]]:
    """Normalizes and validates a single visual element `{ kind, spec, placement?, x?, y? }`."""
    if not isinstance(el, dict):
        return None
    kind = str(el.get("kind", "")).strip().lower()
    spec = el.get("spec") if isinstance(el.get("spec"), dict) else {}
    placement = el.get("placement")

    if kind == "icon":
        raw_name = str(spec.get("name") or el.get("name") or "landmark").strip()
        matches = search_icons(raw_name, set_name=preferred_icon_set, limit=1)
        if not matches:
            matches = search_icons(raw_name, limit=1)
        icon_id = matches[0]["id"] if matches else f"{preferred_icon_set}:landmark"
        anim = str(spec.get("animation", "pop")).lower()
        if anim not in ("none", "draw", "pop", "float", "pulse", "rotate"):
            anim = "pop"
        out = {
            "kind": "icon",
            "spec": {
                "name": icon_id,
                "size": max(24, min(320, int(spec.get("size", 92)))),
                "color": str(spec.get("color", "#f5c542")),
                "strokeWidth": float(spec.get("strokeWidth", 2.2)),
                "animation": anim,
            },
        }
    elif kind == "emoji":
        raw_char = str(spec.get("char") or el.get("char") or "🏛️").strip()
        matches = search_emoji(raw_char, limit=1)
        chosen_char = matches[0]["char"] if matches else "⭐"
        anim = str(spec.get("animation", "pop")).lower()
        if anim not in ("none", "bounce", "pop", "shake", "spin"):
            anim = "pop"
        out = {
            "kind": "emoji",
            "spec": {
                "char": chosen_char,
                "size": max(24, min(320, int(spec.get("size", 88)))),
                "animation": anim,
            },
        }
    elif kind == "flag":
        raw_code = str(spec.get("code") or el.get("code") or "").strip()
        shape = "round" if spec.get("shape") == "round" else "rect"
        resolved = resolve_flag(raw_code, shape=shape)
        if not resolved.get("found") or not resolved.get("code"):
            return None  # never fall back to a default country's flag
        out = {
            "kind": "flag",
            "spec": {
                "code": resolved["code"],
                "shape": shape,
                "size": max(24, min(320, int(spec.get("size", 88)))),
                "animation": str(spec.get("animation", "pop")) if spec.get("animation") in ("none", "pop", "float", "wave") else "pop",
            },
        }
    elif kind == "lottie":
        raw_name = str(spec.get("name") or el.get("name") or "checkmark").strip()
        matches = search_lottie(raw_name, limit=1)
        chosen_id = matches[0]["id"] if matches else "checkmark"
        out = {
            "kind": "lottie",
            "spec": {
                "name": chosen_id,
                "size": max(32, min(600, int(spec.get("size", 150)))),
                "loop": bool(spec.get("loop", True)),
                "playbackRate": float(spec.get("playbackRate", 1.0)),
            },
        }
    elif kind == "chart":
        try:
            out = draw_chart(spec)
        except Exception:
            return None
    elif kind == "component":
        comp_type = str(spec.get("component", "lower_third")).strip()
        if comp_type not in (
            "lower_third",
            "title_card",
            "quote_card",
            "bullet_list",
            "stat_callout",
            "caption_style",
            "animated_headline",
        ):
            comp_type = "lower_third"
        out = {
            "kind": "component",
            "spec": {
                "component": comp_type,
                "title": str(spec.get("title", "")),
                "subtitle": str(spec.get("subtitle", "")),
                "quote": str(spec.get("quote", "")),
                "author": str(spec.get("author", "")),
                "items": [str(x) for x in (spec.get("items") or [])][:6],
                "value": str(spec.get("value", "")),
                "unit": str(spec.get("unit", "")),
                "fontPairing": str(spec.get("fontPairing", "cairo_inter")),
                "rtl": bool(spec.get("rtl", True)),
                "arabicNumerals": bool(spec.get("arabicNumerals", True)),
            },
        }
    else:
        return None

    if placement in ("center", "top-right", "top-left", "bottom-right", "bottom-left", "badge-row", "hero"):
        out["placement"] = placement
    # Optional timed window (frames, scene-local) — used by entity-synced flags
    if isinstance(el.get("from"), (int, float)) and isinstance(el.get("to"), (int, float)) and el["to"] > el["from"]:
        out["from"] = max(0, int(el["from"]))
        out["to"] = int(el["to"])
    if isinstance(el.get("x"), (int, float)) and isinstance(el.get("y"), (int, float)):
        # Enforce 9:16 safe margins
        out["x"] = max(90, min(990, int(el["x"])))
        out["y"] = max(220, min(1380, int(el["y"])))
    return out


def enrich_scene_visuals(
    scene: Dict[str, Any],
    scene_index: int = 0,
    preferred_icon_set: str = "lucide",
) -> List[Dict[str, Any]]:
    """Storyboard Agent helper: builds 2–3 rich visual elements (`icon`, `emoji`, `flag`, `lottie`)
    for a scene based on its narration, visual type, and role, obeying `motion-design-quality` rules:
    - Limit to 2–3 visual elements per scene
    - Consistent icon set per video (`preferred_icon_set`)
    - No emoji spam (at most 1 emoji per scene)
    """
    vis = scene.get("visual") if isinstance(scene.get("visual"), dict) else {}
    vis_countries = [str(c) for c in ((vis.get("countries") or []) + (vis.get("highlight") or [])) if c]
    expected_flag_codes: List[str] = []
    for vc in vis_countries:
        fl = resolve_flag(vc, shape="rect")
        if fl.get("found") and fl.get("code") and fl["code"] not in expected_flag_codes:
            expected_flag_codes.append(fl["code"])

    existing = scene.get("visuals")
    if isinstance(existing, list) and existing:
        norm = []
        emoji_count = 0
        for el in existing:
            n_el = normalize_visual_element(el, preferred_icon_set=preferred_icon_set)
            if not n_el:
                continue
            if n_el["kind"] == "flag" and len(expected_flag_codes) > 1:
                continue  # multi-country scene: one country's flag would mislabel the rest
            if n_el["kind"] == "flag" and expected_flag_codes:
                cur_code = str((n_el.get("spec") or {}).get("code") or "").upper()
                if cur_code not in expected_flag_codes:
                    fixed_fl = resolve_flag(expected_flag_codes[0], shape=(n_el.get("spec") or {}).get("shape", "rect"))
                    if fixed_fl.get("found") and fixed_fl.get("code"):
                        n_el["spec"] = {**n_el["spec"], "code": fixed_fl["code"]}
            if n_el["kind"] == "emoji":
                if emoji_count >= 1:
                    continue
                emoji_count += 1
            norm.append(n_el)
            if len(norm) >= 3:
                break
        if norm:
            return norm

    text = f"{scene.get('on_screen', '')} {scene.get('narration', '')}"
    out: List[Dict[str, Any]] = []

    # 1. Check if a country is mentioned or in map visual -> add <Flag /> ONLY if validated
    countries = (vis.get("countries") or []) + (vis.get("highlight") or [])
    if len(expected_flag_codes) > 1:
        pass  # multi-country scene: no flag badge
    elif countries:
        fl = resolve_flag(str(countries[0]), shape="round" if scene_index % 2 else "rect")
        if fl.get("found") and fl.get("code"):
            out.append({
                "kind": "flag",
                "placement": "badge-row",
                "spec": {"code": fl["code"], "shape": fl["shape"], "size": 84, "animation": "pop"},
            })
    elif not countries:
        for ar_name, iso3 in sorted(AR_ISO3.items(), key=lambda x: len(x[0]), reverse=True):
            if len(ar_name) < 3:
                continue
            if ar_name in ("أمريكا", "امريكا") and re.search(
                r"(?:أمريكا|امريكا)\s+(?:الجنوبية|الشمالية|اللاتينية|الوسطى)", text
            ):
                continue
            if re.search(rf"(?:^|[\s،؟!.,:؛\-وبلفك]){re.escape(ar_name)}(?:$|[\s،؟!.,:؛\-])", text):
                fl = resolve_flag(iso3, shape="rect")
                if fl.get("found") and fl.get("code"):
                    out.append({
                        "kind": "flag",
                        "placement": "badge-row",
                        "spec": {"code": fl["code"], "shape": "rect", "size": 84, "animation": "pop"},
                    })
                    break

    # 2. Pick 1 matching Iconify icon if text has a meaningful concept and no flag was found
    if len(out) < 1:
        ic_matches = search_icons(text, set_name=preferred_icon_set, limit=1)
        if ic_matches and ic_matches[0].get("score", 0) > 40:
            ic_id = ic_matches[0]["id"]
            anim_cycle = ["draw", "pop", "float", "pulse"]
            out.append({
                "kind": "icon",
                "placement": "badge-row",
                "spec": {
                    "name": ic_id,
                    "size": 84,
                    "color": "#f5c542",
                    "strokeWidth": 2.2,
                    "animation": anim_cycle[scene_index % len(anim_cycle)],
                },
            })

    # 3. If still empty, add either 1 Lottie accent (on hook/cta) or 1 Emoji
    if len(out) < 1:
        role = scene.get("role", "body")
        if role in ("hook", "cta"):
            lottie_q = "sparkles" if role == "hook" else "checkmark"
            lm = search_lottie(lottie_q, limit=1)
            if lm:
                out.append({
                    "kind": "lottie",
                    "placement": "badge-row",
                    "spec": {"name": lm[0]["id"], "size": 90, "loop": True, "playbackRate": 1.0},
                })
        else:
            em = search_emoji(text, limit=1)
            if em and em[0].get("score", 0) > 45:
                out.append({
                    "kind": "emoji",
                    "placement": "badge-row",
                    "spec": {"char": em[0]["char"], "size": 76, "animation": "pop"},
                })

    # If the scene has a full-screen rich beat (photo, map, versus, bars, generative_canvas),
    # limit to max 1 subtle badge to prevent visual clutter; otherwise up to 2.
    beats_kinds = [b.get("kind") for b in (scene.get("beats") or []) if isinstance(b, dict)]
    has_fullscreen_beat = any(k in beats_kinds for k in ("photo", "map", "versus_battle", "bars", "generative_canvas", "elevation_profile", "chart"))
    return out[:1] if has_fullscreen_beat else out[:2]

# Re-exported so `pipeline.visual_tools.<name>` keeps working.
from .visual_tools_search import (  # noqa: E402,F401
    SEMANTIC_ICON_MAP,
    _EMOJI_CACHE,
    _FLAGS_CACHE,
    _ICONS_CACHE,
    _LOTTIE_CACHE,
    _load_emoji_catalog,
    _load_flags_catalog,
    _load_icons_bundle,
    _load_lottie_manifest,
    resolve_flag,
    search_emoji,
    search_icons,
    search_lottie,
)

# Re-exported so `pipeline.visual_tools.<name>` keeps working.
from .visual_tools_edit import (  # noqa: E402,F401
    apply_chat_visual_edit,
)

# Re-exported so `pipeline.visual_tools.<name>` keeps working.
from .visual_tools_qa import (  # noqa: E402,F401
    qa_visual_review,
    record_asset_credits,
)
