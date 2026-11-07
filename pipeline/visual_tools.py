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

_ICONS_CACHE: Optional[Dict[str, Any]] = None
_EMOJI_CACHE: Optional[Dict[str, Any]] = None
_FLAGS_CACHE: Optional[Dict[str, Any]] = None
_LOTTIE_CACHE: Optional[Dict[str, Any]] = None


def _load_icons_bundle() -> Dict[str, Any]:
    global _ICONS_CACHE
    if _ICONS_CACHE is None:
        p = PKG_ASSETS / "icons" / "catalog.json"
        _ICONS_CACHE = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"catalog": [], "sets": {}}
    return _ICONS_CACHE


def _load_emoji_catalog() -> Dict[str, Any]:
    global _EMOJI_CACHE
    if _EMOJI_CACHE is None:
        p = PKG_ASSETS / "emoji" / "catalog.json"
        _EMOJI_CACHE = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"items": []}
    return _EMOJI_CACHE


def _load_flags_catalog() -> Dict[str, Any]:
    global _FLAGS_CACHE
    if _FLAGS_CACHE is None:
        p = PKG_ASSETS / "flags" / "countries.json"
        _FLAGS_CACHE = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"iso3ToIso2": {}, "countries": []}
    return _FLAGS_CACHE


def _load_lottie_manifest() -> Dict[str, Any]:
    global _LOTTIE_CACHE
    if _LOTTIE_CACHE is None:
        p = PKG_ASSETS / "lottie" / "manifest.json"
        _LOTTIE_CACHE = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"items": []}
    return _LOTTIE_CACHE


SEMANTIC_ICON_MAP: Dict[str, List[str]] = {
    "pyramid": ["lucide:pyramid", "lucide:landmark", "tabler:building-monument"],
    "هرم": ["lucide:pyramid", "lucide:landmark"],
    "أهرامات": ["lucide:pyramid", "lucide:landmark"],
    "اهرامات": ["lucide:pyramid", "lucide:landmark"],
    "capital": ["lucide:landmark", "lucide:building-2", "tabler:map-pin-filled"],
    "عاصمة": ["lucide:landmark", "lucide:building-2", "lucide:crown"],
    "عاصمتين": ["lucide:landmark", "lucide:scale", "lucide:map-pin"],
    "parliament": ["lucide:landmark", "ph:bank", "ph:columns"],
    "برلمان": ["lucide:landmark", "ph:bank"],
    "حكومة": ["lucide:landmark", "lucide:building-2"],
    "دستور": ["lucide:scroll-text", "lucide:scale", "ph:scroll"],
    "قانون": ["lucide:scale", "lucide:gavel", "lucide:scroll-text"],
    "عدالة": ["lucide:scale", "lucide:gavel"],
    "قضاء": ["lucide:scale", "lucide:landmark"],
    "war": ["lucide:swords", "lucide:shield", "ph:sword"],
    "حرب": ["lucide:swords", "lucide:shield", "ph:sword"],
    "معركة": ["lucide:swords", "ph:sword"],
    "صراع": ["lucide:swords", "lucide:flame"],
    "تمرد": ["lucide:flame", "lucide:swords"],
    "جيش": ["lucide:shield", "lucide:swords"],
    "money": ["lucide:coins", "lucide:banknote", "ph:treasure-chest"],
    "مال": ["lucide:coins", "lucide:banknote"],
    "أموال": ["lucide:coins", "lucide:banknote"],
    "ذهب": ["lucide:coins", "lucide:gem", "ph:treasure-chest"],
    "اقتصاد": ["lucide:trending-up", "lucide:coins", "lucide:bar-chart-3"],
    "نمو": ["lucide:trending-up", "lucide:arrow-up-right"],
    "map": ["lucide:map", "lucide:globe", "lucide:map-pin"],
    "خريطة": ["lucide:map", "lucide:globe", "lucide:map-pin"],
    "عالم": ["lucide:globe", "tabler:world", "ph:globe-hemisphere-east"],
    "جبل": ["lucide:mountain", "lucide:compass"],
    "بحر": ["lucide:waves", "lucide:anchor", "lucide:ship"],
    "مضيق": ["lucide:waves", "lucide:anchor"],
    "مسجد": ["ph:mosque", "tabler:building-mosque"],
    "جامع": ["ph:mosque", "tabler:building-mosque"],
    "سكان": ["lucide:users", "lucide:user-round"],
    "شعب": ["lucide:users", "lucide:user-round"],
    "زمن": ["lucide:hourglass", "lucide:clock", "tabler:timeline"],
    "تاريخ": ["lucide:scroll-text", "lucide:hourglass", "lucide:landmark"],
    "سنة": ["lucide:calendar", "lucide:clock"],
    "عام": ["lucide:calendar", "lucide:hourglass"],
    "فكرة": ["lucide:lightbulb", "lucide:sparkles"],
    "سر": ["lucide:key", "lucide:lightbulb", "lucide:help-circle"],
    "لغز": ["lucide:help-circle", "lucide:key"],
    "كأس": ["lucide:trophy", "lucide:medal", "tabler:award"],
    "بطولة": ["lucide:trophy", "lucide:medal"],
}


def search_icons(
    query: str,
    set_name: Optional[str] = None,
    limit: int = 5,
    llm_fallback: bool = False,
) -> List[Dict[str, Any]]:
    """Tool `search_icons({ query, set? })`:
    Returns the best matching offline Iconify icons by name/tags (and semantic meaning),
    so agents never invent icon names.
    """
    q = (query or "").strip().lower()
    tokens = [t for t in re.split(r"[\s,_\-/]+", q) if t]
    bundle = _load_icons_bundle()
    catalog: List[Dict[str, Any]] = bundle.get("catalog", [])
    if set_name in ("lucide", "ph", "tabler"):
        catalog = [c for c in catalog if c.get("set") == set_name]

    synonym_hits = set()
    for kw, ids in SEMANTIC_ICON_MAP.items():
        if kw == q or (len(kw) >= 3 and re.search(rf"(?:^|\s|ال){re.escape(kw)}(?:$|\s|[،.؟!])", q)):
            synonym_hits.update(ids)
        for tk in tokens:
            if len(tk) >= 3 and (tk == kw or tk == f"ال{kw}"):
                synonym_hits.update(ids)

    scored: List[Dict[str, Any]] = []
    for item in catalog:
        score = 0
        item_id = item["id"].lower()
        item_name = item["name"].lower()
        tags = [str(t).lower() for t in item.get("tags", [])]
        ar_list = [str(a) for a in item.get("ar", [])]

        if item_id == q or item_name == q:
            score += 120
        if item["id"] in synonym_hits:
            score += 85
        if q and len(q) >= 2 and item_name in q or (q in item_name and len(q) >= 2):
            score += 55
        for ar in ar_list:
            if ar == q:
                score += 95
            elif q and len(ar) >= 3 and re.search(rf"(?:^|\s|ال){re.escape(ar)}(?:$|\s|[،.؟!])", q):
                score += 65
        for tag in tags:
            if tag == q:
                score += 75
            elif any(tk == tag or (len(tk) >= 3 and (tk in tag or tag in tk)) for tk in tokens):
                score += 35

        scored.append({
            "id": item["id"],
            "set": item["set"],
            "name": item["name"],
            "score": score,
            "tags": item.get("tags", []),
            "ar": ar_list,
            "license": item.get("license", "MIT"),
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    positive = [s for s in scored if s["score"] > 0]
    if positive:
        return positive[:limit]

    # Optional LLM semantic fallback when no tag matches and an API key is configured
    if llm_fallback and q:
        try:
            from . import llm
            if llm.has_deepseek() or llm.has_gemini():
                sample_ids = [c["id"] for c in catalog[:60]]
                prompt = f"Pick the single best icon ID for query '{query}' from this exact list: {sample_ids}. Return JSON: {{\"id\": \"...\"}}"
                res, _ = llm.call_json("You are an icon matcher. Return JSON only.", prompt, prefer="deepseek")
                picked_id = res.get("id")
                for s in scored:
                    if s["id"] == picked_id:
                        s["score"] = 50
                        return [s] + [x for x in scored if x["id"] != picked_id][: max(0, limit - 1)]
        except Exception:
            pass

    return scored[:limit]


def search_emoji(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Tool `search_emoji({ query })` with localized Arabic & English names."""
    q = (query or "").strip()
    q_low = q.lower()
    tokens = [t for t in re.split(r"[\s,_\-/]+", q_low) if t]
    items = _load_emoji_catalog().get("items", [])

    scored = []
    for em in items:
        score = 0
        if em["char"] == q or em["code"] == q_low:
            score += 150
        if q_low and q_low in em["name"].lower():
            score += 85
        if q and (q in em["name_ar"] or em["name_ar"] in q):
            score += 95
        for tag in em.get("tags", []):
            tl = str(tag).lower()
            if tl == q_low:
                score += 80
            elif q_low and (tl in q_low or q_low in tl):
                score += 45
            elif any(len(tk) >= 3 and (tk in tl or tl in tk) for tk in tokens):
                score += 30
        scored.append({**em, "score": score})

    scored.sort(key=lambda x: x["score"], reverse=True)
    positive = [s for s in scored if s["score"] > 0]
    return (positive if positive else scored)[:limit]


def resolve_flag(query: str, shape: str = "rect") -> Dict[str, Any]:
    """Resolves Arabic/English country names or ISO2/ISO3 codes (reusing `pipeline/geo.py` AR_ISO3)."""
    raw = (query or "").strip()
    sh = "round" if shape == "round" else "rect"
    ratio = "1x1" if sh == "round" else "4x3"
    if not raw:
        return {
            "code": None,
            "iso2": None,
            "shape": sh,
            "file": "",
            "found": False,
            "license": "MIT (flag-icons)",
            "attributionRequired": False,
        }
    upper = raw.upper()
    lower = raw.lower()
    cat = _load_flags_catalog()
    iso3_map: Dict[str, str] = cat.get("iso3ToIso2", {})
    countries: List[Dict[str, Any]] = cat.get("countries", [])

    iso2 = None
    if re.match(r"^[A-Z]{2}$", upper):
        iso2 = lower
    elif re.match(r"^[A-Z]{3}$", upper) and upper in iso3_map:
        iso2 = iso3_map[upper].lower()

    if not iso2:
        # Check pipeline.geo AR_ISO3
        for ar_name, iso3_code in AR_ISO3.items():
            if ar_name == raw or (len(raw) >= 3 and (ar_name in raw or raw in ar_name)):
                if iso3_code in iso3_map:
                    iso2 = iso3_map[iso3_code].lower()
                    break

    if not iso2:
        for c in countries:
            if c["iso2"].upper() == upper or c["iso3"].upper() == upper:
                iso2 = c["iso2"].lower()
                break
            if any(a == raw or (len(raw) >= 3 and (a in raw or raw in a)) for a in c.get("ar", [])):
                iso2 = c["iso2"].lower()
                break
            if any(e == lower or (len(lower) >= 3 and (e in lower or lower in e)) for e in c.get("en", [])):
                iso2 = c["iso2"].lower()
                break

    if not iso2:
        return {
            "code": None,
            "iso2": None,
            "shape": sh,
            "file": "",
            "found": False,
            "license": "MIT (flag-icons)",
            "attributionRequired": False,
        }

    return {
        "code": iso2.upper(),
        "iso2": iso2,
        "shape": sh,
        "file": f"flags/{ratio}/{iso2}.svg",
        "found": True,
        "license": "MIT (flag-icons)",
        "attributionRequired": False,
    }


def search_lottie(query: str, limit: int = 4) -> List[Dict[str, Any]]:
    """Tool `search_lottie({ query })` over `packages/assets/lottie/manifest.json`."""
    q = (query or "").strip()
    q_low = q.lower()
    items = _load_lottie_manifest().get("items", [])
    scored = []
    for it in items:
        score = 0
        if it["id"].lower() == q_low or it["category"].lower() == q_low:
            score += 110
        if q_low and q_low in it["name"].lower():
            score += 75
        if q and q in it.get("name_ar", ""):
            score += 85
        for tag in it.get("tags", []):
            tl = str(tag).lower()
            if tl == q_low:
                score += 80
            elif q_low and (tl in q_low or q_low in tl):
                score += 45
        scored.append({**it, "score": score})

    scored.sort(key=lambda x: x["score"], reverse=True)
    positive = [s for s in scored if s["score"] > 0]
    return (positive if positive else scored)[:limit]


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
        raw_code = str(spec.get("code") or el.get("code") or "EG").strip()
        shape = "round" if spec.get("shape") == "round" else "rect"
        resolved = resolve_flag(raw_code, shape=shape)
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
    existing = scene.get("visuals")
    if isinstance(existing, list) and existing:
        norm = []
        emoji_count = 0
        for el in existing:
            n_el = normalize_visual_element(el, preferred_icon_set=preferred_icon_set)
            if not n_el:
                continue
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
    vis = scene.get("visual") if isinstance(scene.get("visual"), dict) else {}
    out: List[Dict[str, Any]] = []

    # 1. Check if a country is mentioned or in map visual -> add <Flag /> ONLY if validated
    countries = (vis.get("countries") or []) + (vis.get("highlight") or [])
    flag_added = False
    if countries:
        fl = resolve_flag(str(countries[0]), shape="round" if scene_index % 2 else "rect")
        if fl.get("found") and fl.get("code"):
            out.append({
                "kind": "flag",
                "placement": "badge-row",
                "spec": {"code": fl["code"], "shape": fl["shape"], "size": 84, "animation": "pop"},
            })
            flag_added = True
    else:
        for ar_name, iso3 in AR_ISO3.items():
            if ar_name in text:
                fl = resolve_flag(iso3, shape="rect")
                if fl.get("found") and fl.get("code"):
                    out.append({
                        "kind": "flag",
                        "placement": "badge-row",
                        "spec": {"code": fl["code"], "shape": "rect", "size": 84, "animation": "pop"},
                    })
                    flag_added = True
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


def qa_visual_review(spec: Dict[str, Any]) -> List[Dict[str, str]]:
    """QA Agent's visual review:
    Checks for visual clutter (>3 visuals per scene), mixed icon sets, emoji spam (>1 emoji per scene),
    unsafe 9:16 margins, and overlapping coordinates.
    """
    issues: List[Dict[str, str]] = []
    scenes = spec.get("scenes", []) if isinstance(spec, dict) else []
    icon_sets_seen = set()

    for sc in scenes:
        sid = sc.get("id", "scene")
        visuals = sc.get("visuals") or []
        if len(visuals) > 3:
            issues.append({
                "level": "warn",
                "where": sid,
                "msg": f"المشهد '{sid}' يحتوي على {len(visuals)} عناصر بصرية (الحد الأقصى الموصى به 3 لمنع الازدحام البصري).",
            })
        emoji_cnt = sum(1 for v in visuals if isinstance(v, dict) and v.get("kind") == "emoji")
        if emoji_cnt > 1:
            issues.append({
                "level": "warn",
                "where": sid,
                "msg": f"المشهد '{sid}' يحتوي على {emoji_cnt} رموز تعبيرية (ممنوع الإكثار من الإيموجي).",
            })
        coords = []
        for v in visuals:
            if not isinstance(v, dict):
                continue
            if v.get("kind") == "icon":
                name = str(v.get("spec", {}).get("name", ""))
                if ":" in name:
                    icon_sets_seen.add(name.split(":")[0])
            x, y = v.get("x"), v.get("y")
            if isinstance(x, (int, float)) and isinstance(y, (int, float)):
                if x < 70 or x > 1010 or y < 160 or y > 1480:
                    issues.append({
                        "level": "warn",
                        "where": sid,
                        "msg": f"عنصر بصري في '{sid}' خارج الهوامش الآمنة لـ 9:16 ({x}, {y}).",
                    })
                for ox, oy in coords:
                    if abs(x - ox) < 70 and abs(y - oy) < 70:
                        issues.append({
                            "level": "warn",
                            "where": sid,
                            "msg": f"تداخل بصري محتمل بين عنصرين في المشهد '{sid}' عند ({x}, {y}).",
                        })
                coords.append((x, y))

    if len(icon_sets_seen) > 1:
        issues.append({
            "level": "warn",
            "where": "all",
            "msg": f"تعددت مجموعات الأيقونات في نفس الفيديو ({sorted(icon_sets_seen)})؛ يُفضّل توحيد أسلوب الأيقونات.",
        })

    return issues


def record_asset_credits(spec: Dict[str, Any], job_dir: Optional[str] = None) -> Dict[str, Any]:
    """Scans `spec` for all visual assets used and records per-asset attribution in `credits.json`."""
    root_credits_path = ROOT / "credits.json"
    base_credits = (
        json.loads(root_credits_path.read_text(encoding="utf-8"))
        if root_credits_path.exists()
        else {"project": "shorts-studio", "collections": {}, "usedAssets": []}
    )

    used_assets: List[Dict[str, Any]] = []
    emoji_cat = {e["char"]: e for e in _load_emoji_catalog().get("items", [])}
    lottie_cat = {m["id"]: m for m in _load_lottie_manifest().get("items", [])}

    for sc in spec.get("scenes", []) if isinstance(spec, dict) else []:
        for v in sc.get("visuals") or []:
            if not isinstance(v, dict):
                continue
            kind = v.get("kind")
            vspec = v.get("spec") or {}
            if kind == "icon":
                name = str(vspec.get("name", "lucide:landmark"))
                prefix = name.split(":")[0] if ":" in name else "lucide"
                used_assets.append({
                    "kind": "icon",
                    "id": name,
                    "collection": prefix,
                    "license": "ISC" if prefix == "lucide" else "MIT",
                    "attributionRequired": False,
                })
            elif kind == "emoji":
                ch = str(vspec.get("char", ""))
                em = emoji_cat.get(ch, {})
                col = em.get("collection", "noto-emoji")
                attr = col == "twemoji" or bool(em.get("attributionRequired", False))
                used_assets.append({
                    "kind": "emoji",
                    "id": ch,
                    "collection": col,
                    "license": "CC-BY 4.0" if col == "twemoji" else "Apache-2.0",
                    "attributionRequired": attr,
                    "credit": (
                        "Twemoji graphics by Twitter, Inc and contributors (CC-BY 4.0)"
                        if col == "twemoji"
                        else "Google Noto Color Emoji (Apache-2.0)"
                    ),
                })
            elif kind == "flag":
                code = str(vspec.get("code", "EG"))
                used_assets.append({
                    "kind": "flag",
                    "id": code,
                    "collection": "flag-icons",
                    "license": "MIT",
                    "attributionRequired": False,
                })
            elif kind == "lottie":
                lid = str(vspec.get("name", "checkmark"))
                lm = lottie_cat.get(lid, {})
                used_assets.append({
                    "kind": "lottie",
                    "id": lid,
                    "collection": "lottie-local",
                    "license": lm.get("license", "CC0-1.0"),
                    "sourceUrl": lm.get("sourceUrl", "packages/assets/lottie/manifest.json"),
                    "attributionRequired": bool(lm.get("attributionRequired", False)),
                })

    dedup = {}
    for ua in used_assets:
        dedup[f"{ua['kind']}:{ua['id']}"] = ua
    final_list = list(dedup.values())

    base_credits["usedAssets"] = final_list
    root_credits_path.write_text(json.dumps(base_credits, ensure_ascii=False, indent=2), encoding="utf-8")
    if job_dir and os.path.isdir(job_dir):
        Path(job_dir, "credits.json").write_text(
            json.dumps(base_credits, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    return base_credits


def apply_chat_visual_edit(
    script: Dict[str, Any],
    instruction: str,
    scene_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Handles chat edits like:
    - 'change the icon to a pyramid' / 'غير الأيقونة إلى هرم'
    - 'use a bar chart here' / 'استخدم مخطط أعمدة هنا'
    - 'add flag of Egypt' / 'أضف علم مصر'
    - 'add emoji crown' / 'أضف إيموجي تاج'
    - 'add lottie confetti' / 'أضف لوتي احتفال'
    using the exact same offline tools (`search_icons`, `draw_chart`, `resolve_flag`, `search_emoji`, `search_lottie`).
    """
    import copy
    from .scriptspec import PART_IDS, normalize

    s = normalize(copy.deepcopy(script))
    target_id = scene_id if scene_id in PART_IDS else "hook"
    instr = (instruction or "").strip()
    instr_low = instr.lower()

    part = s.get(target_id, {})
    visuals: List[Dict[str, Any]] = list(part.get("visuals") or [])
    action_taken = ""

    # 0. Check for Elevation / Mountain + Sea + Capital + Counter requests ("ارتفاع", "جبل", "بحر", "elevation")
    if any(k in instr_low for k in ("elevation", "altitude", "ارتفاع", "جبل", "سطح البحر")):
        nums = re.findall(r"\d[\d,]*", instr)
        vis_num = (part.get("visual") or {}).get("number") if isinstance(part.get("visual"), dict) else None
        height_str = nums[0] if nums else (str(vis_num) if vis_num else "3,650")
        elev_beat = {
            "kind": "elevation_profile",
            "title": part.get("on_screen") or "لاباز — أعلى عاصمة إدارية",
            "capital": part.get("on_screen") or "العاصمة لاباز",
            "height": height_str,
            "unit": "م",
            "sea_label": "مستوى سطح البحر",
        }
        beats = list(part.get("beats") or [])
        part["beats"] = [elev_beat] + beats[1:] if beats else [elev_beat]
        action_taken = f"elevation_profile({height_str}m)"

    elif any(k in instr_low for k in ("versus", "battle", "مقارنة القوى", "سباق المقارنة", "مقارنة")):
        beat_obj = {
            "kind": "versus_battle",
            "title": part.get("on_screen") or "مقارنة القوى المباشرة",
            "left": {"name": "الطرف الأول", "value": 85, "unit": "مليار $", "code": "EG"},
            "right": {"name": "الطرف الثاني", "value": 120, "unit": "مليار $", "code": "SA"},
        }
        beats = list(part.get("beats") or [])
        part["beats"] = [beat_obj] + beats[1:] if beats else [beat_obj]
        action_taken = "versus_battle"

    elif any(k in instr_low for k in ("route", "journey", "مسار", "انتقال", "رحلة", "طريق")):
        beat_obj = {
            "kind": "animated_route",
            "title": part.get("on_screen") or "مسار الانتقال الجغرافي",
            "from_city": "سوكري",
            "to_city": "لاباز",
            "distance_km": 560,
        }
        beats = list(part.get("beats") or [])
        part["beats"] = [beat_obj] + beats[1:] if beats else [beat_obj]
        action_taken = "animated_route"

    elif any(k in instr_low for k in ("balance", "gauge", "ميزان", "كفة", "استفتاء")):
        beat_obj = {
            "kind": "balance_meter",
            "title": part.get("on_screen") or "ميزان القوى والسيطرة",
            "label_a": "الحكومة المركزية",
            "label_b": "نخب الشمال",
            "pct": 68,
        }
        beats = list(part.get("beats") or [])
        part["beats"] = [beat_obj] + beats[1:] if beats else [beat_obj]
        action_taken = "balance_meter"

    elif any(k in instr_low for k in ("century", "year", "time", "قرون", "زمن", "سنوات", "تاريخ عبر الزمن")):
        beat_obj = {
            "kind": "deep_time_slider",
            "title": part.get("on_screen") or "قفزة عبر القرون والتاريخ",
            "start_year": 1825,
            "end_year": 2009,
            "event_label": "إقرار الدستور المزدوج والتسوية النهائية",
        }
        beats = list(part.get("beats") or [])
        part["beats"] = [beat_obj] + beats[1:] if beats else [beat_obj]
        action_taken = "deep_time_slider"

    elif any(k in instr_low for k in ("stack_pyramid", "طبقات", "هرم السلطة", "تشريح السلطة")):
        beat_obj = {
            "kind": "stack_pyramid",
            "title": part.get("on_screen") or "هيكل السلطة الدستورية",
            "layers": [
                {"name": "الرئاسة والحكومة (لاباز)", "width": 360, "color": "#f5c542"},
                {"name": "البرلمان والوزارات المركزية", "width": 560, "color": "#38bdf8"},
                {"name": "القضاء الأعلى والدستور (سوكري)", "width": 780, "color": "#34d399"},
            ],
        }
        beats = list(part.get("beats") or [])
        part["beats"] = [beat_obj] + beats[1:] if beats else [beat_obj]
        action_taken = "stack_pyramid"

    elif any(k in instr_low for k in ("macro", "globe", "zoom", "العالم إلى الدولة", "تلسكوبي", "كوكب")):
        beat_obj = {
            "kind": "macro_zoom_globe",
            "title": part.get("on_screen") or "في قلب قارة أمريكا الجنوبية",
            "country": "بوليفيا",
            "code": "BO",
        }
        beats = list(part.get("beats") or [])
        part["beats"] = [beat_obj] + beats[1:] if beats else [beat_obj]
        action_taken = "macro_zoom_globe"

    elif any(k in instr_low for k in ("mine", "subsurface", "باطن الأرض", "مناجم", "تعدين", "فضة", "ذهب تحت الأرض")):
        beat_obj = {
            "kind": "subsurface_mine",
            "title": part.get("on_screen") or "كنوز باطن الأرض والفضة",
            "depth_m": 1200,
            "resource": "مناجم الفضة التاريخية",
        }
        beats = list(part.get("beats") or [])
        part["beats"] = [beat_obj] + beats[1:] if beats else [beat_obj]
        action_taken = "subsurface_mine"

    elif any(k in instr_low for k in ("population", "matrix", "سكان", "كثافة سكانية", "مصفوفة")):
        beat_obj = {
            "kind": "dot_matrix_population",
            "title": part.get("on_screen") or "التوزيع السكاني والديموغرافي",
            "total_label": "١٢ مليون نسمة",
            "highlight_pct": 70,
        }
        beats = list(part.get("beats") or [])
        part["beats"] = [beat_obj] + beats[1:] if beats else [beat_obj]
        action_taken = "dot_matrix_population"

    elif any(k in instr_low for k in ("waterfall", "budget", "ميزانية", "تدفق الأموال", "أموال الدولة")):
        beat_obj = {
            "kind": "money_waterfall",
            "title": part.get("on_screen") or "مسار التدفقات المالية والميزانية",
            "total": "١٠٠ مليار $",
            "streams": [
                {"name": "تطوير البنية والمدن", "pct": "٤٥%", "color": "#f5c542"},
                {"name": "الخدمات والصحة", "pct": "٣٠%", "color": "#38bdf8"},
                {"name": "الاحتياطي السيادي", "pct": "٢٥%", "color": "#34d399"},
            ],
        }
        beats = list(part.get("beats") or [])
        part["beats"] = [beat_obj] + beats[1:] if beats else [beat_obj]
        action_taken = "money_waterfall"

    elif any(k in instr_low for k in ("frontline", "war", "حرب", "جبهة", "معركة", "اشتباك", "نزاع مسلح")):
        beat_obj = {
            "kind": "frontline_clash",
            "title": part.get("on_screen") or "اشتعال خطوط المواجهة والنزاع",
            "side_a": "قوات الحكومة",
            "side_b": "الفيدراليون (الشمال)",
        }
        beats = list(part.get("beats") or [])
        part["beats"] = [beat_obj] + beats[1:] if beats else [beat_obj]
        action_taken = "frontline_clash"

    elif any(k in instr_low for k in ("generative", "custom", "بركان", "انفجار", "حصار", "شبكة عصبية", "تضخم", "توليد", "ليغو", "رسم توضيحي", "رسم حر")):
        from .generative_visuals import compose_generative_canvas
        gen_beat = compose_generative_canvas(instr, context=part.get("text") or part.get("on_screen"))
        beats = list(part.get("beats") or [])
        part["beats"] = [gen_beat] + beats[1:] if beats else [gen_beat]
        action_taken = f"generative_canvas({gen_beat.get('title')})"

    # 1. Check for Chart requests ("bar chart", "line chart", "pie chart", "donut", "مخطط أعمدة", "مخطط خطي", "مخطط دائري")
    elif any(k in instr_low for k in ("chart", "bar", "line", "pie", "donut", "مخطط", "أعمدة", "بياني", "دائري")):
        ctype = "bar"
        if "line" in instr_low or "خطي" in instr_low:
            ctype = "line"
        elif "pie" in instr_low or "donut" in instr_low or "دائري" in instr_low:
            ctype = "donut"
        elif "timeline" in instr_low or "زمني" in instr_low:
            ctype = "timeline"

        chart_el = draw_chart({
            "type": ctype,
            "data": [
                {"label": part.get("on_screen") or "المؤشر الأول", "value": 85},
                {"label": "المؤشر الثاني", "value": 62},
                {"label": "المؤشر الثالث", "value": 44},
            ],
            "style": {
                "title": part.get("on_screen") or "مقارنة البيانات",
                "rtl": True,
                "arabicNumerals": True,
            },
        })
        chart_el["placement"] = "center"
        visuals = [v for v in visuals if v.get("kind") != "chart"]
        visuals.insert(0, chart_el)
        # Also update the scene's primary beat so the chart renders prominently
        beats = list(part.get("beats") or [])
        chart_beat = {
            "kind": "chart",
            "title": part.get("on_screen") or "مقارنة البيانات",
            "spec": chart_el["spec"],
        }
        if beats:
            beats[0] = chart_beat
        else:
            beats = [chart_beat]
        part["beats"] = beats
        action_taken = f"draw_chart({ctype})"

    # 2. Check for Flag requests ("flag", "علم")
    elif "flag" in instr_low or "علم" in instr_low:
        q = re.sub(r"(?i)(change|add|use|the|flag|of|to|here|أضف|غير|استخدم|علم|إلى|هنا)", " ", instr).strip()
        fl = resolve_flag(q or instr)
        flag_el = {
            "kind": "flag",
            "placement": "badge-row",
            "spec": {"code": fl["code"], "shape": "rect", "size": 92, "animation": "pop"},
        }
        visuals = [v for v in visuals if v.get("kind") != "flag"]
        visuals.append(flag_el)
        action_taken = f"resolve_flag({fl['code']})"

    # 3. Check for Emoji requests ("emoji", "إيموجي", "رمز تعبيري")
    elif "emoji" in instr_low or "إيموجي" in instr_low or "ايموجي" in instr_low:
        q = re.sub(r"(?i)(change|add|use|the|emoji|to|here|أضف|غير|استخدم|إيموجي|ايموجي|إلى|هنا)", " ", instr).strip()
        matches = search_emoji(q or instr, limit=1)
        chosen = matches[0]
        em_el = {
            "kind": "emoji",
            "placement": "badge-row",
            "spec": {"char": chosen["char"], "size": 92, "animation": "pop"},
        }
        visuals = [v for v in visuals if v.get("kind") != "emoji"]
        visuals.append(em_el)
        action_taken = f"search_emoji({chosen['char']})"

    # 4. Check for Lottie requests ("lottie", "لوتي", "confetti", "sparkles", "checkmark")
    elif any(k in instr_low for k in ("lottie", "لوتي", "confetti", "sparkle", "loader", "checkmark")):
        q = re.sub(r"(?i)(change|add|use|the|lottie|to|here|أضف|غير|استخدم|لوتي|إلى|هنا)", " ", instr).strip()
        matches = search_lottie(q or instr, limit=1)
        chosen = matches[0]
        lot_el = {
            "kind": "lottie",
            "placement": "badge-row",
            "spec": {"name": chosen["id"], "size": 140, "loop": True, "playbackRate": 1.0},
        }
        visuals = [v for v in visuals if v.get("kind") != "lottie"]
        visuals.append(lot_el)
        action_taken = f"search_lottie({chosen['id']})"

    # 5. Default / Icon requests ("change the icon to a pyramid", "غير الأيقونة إلى هرم")
    else:
        q = re.sub(
            r"(?i)(change|set|replace|add|use|the|icon|to|a|an|here|in|this|scene|أضف|غير|استبدل|الأيقونة|أيقونة|ايقونة|إلى|الى|هنا)",
            " ",
            instr,
        ).strip()
        matches = search_icons(q or instr, limit=1, llm_fallback=True)
        chosen = matches[0]
        icon_el = {
            "kind": "icon",
            "placement": "badge-row",
            "spec": {
                "name": chosen["id"],
                "size": 96,
                "color": "#f5c542",
                "strokeWidth": 2.2,
                "animation": "draw",
            },
        }
        replaced = False
        for idx, v in enumerate(visuals):
            if v.get("kind") == "icon":
                visuals[idx] = icon_el
                replaced = True
                break
        if not replaced:
            visuals.append(icon_el)
        action_taken = f"search_icons({chosen['id']})"

    part["visuals"] = visuals[:3]
    s[target_id] = part
    return {"script": s, "scene": target_id, "action": action_taken, "visuals": part["visuals"]}
