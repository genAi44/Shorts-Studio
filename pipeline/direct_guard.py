"""Split from `pipeline/direct.py` (re-exported there); see that module."""
from typing import Any, Dict
from . import areamap
from .geo import detect_city_in_text
import re
from .config import record_fallback
from .direct import _num, fallback_beat, normalize_beat, sentences, validate_beat  # noqa: E402


# ------------------------------------------------------------------ Beat Type Guard (`BEAT_RULES`)
_ELEV_GUARD_RE = re.compile(
    r"ارتفاع|قمة|جبل|سلسلة جبال|فوق سطح البحر|عمق|هضبة|أنديز|إيفرست|أمتار|متر|elevation|mountain|peak|altitude|sea level",
    re.I,
)


_WAR_CONFLICT_RE = re.compile(r"حرب|معركة|نزاع|ثورة|تمرد", re.I)


def _pred_elevation_profile(b: dict, sentence: str = "", geo=None) -> bool:
    h_str = str(b.get("height") or "").strip()
    if not re.search(r"\d", h_str):
        return False
    combined = f"{sentence} {b.get('title', '')} {b.get('unit', '')}"
    if not _ELEV_GUARD_RE.search(combined):
        return False
    if _WAR_CONFLICT_RE.search(str(b.get("title") or "")):
        return False
    return True


def _real_point(p: Any) -> bool:
    """A point is real if it has numeric lat/lon in range or its name resolves to a known city."""
    if not isinstance(p, dict):
        return False
    try:
        if -90 <= float(p.get("lat")) <= 90 and -180 <= float(p.get("lon")) <= 180:
            return True
    except (TypeError, ValueError):
        pass
    name = str(p.get("name") or "").strip()
    return bool(name) and bool(detect_city_in_text(name)[0])


def _pred_map(b: dict, sentence: str = "", geo=None) -> bool:
    """A map needs a real place: a valid country code, or a point with coordinates / a known city."""
    pts = b.get("points") or []
    cs = [str(c).upper() for c in (b.get("countries") or []) if isinstance(c, str)]
    hl = [str(c).upper() for c in (b.get("highlight") or cs) if isinstance(c, str)]
    if geo is not None:
        cs = [c for c in cs if geo.has(c)]
        hl = [c for c in hl if geo.has(c)]
    return any(_real_point(p) for p in pts) or bool(cs) or bool(hl)


def _pred_map_pin(b: dict, sentence: str = "", geo=None) -> bool:
    pts = b.get("points") or []
    return isinstance(pts, list) and any(_real_point(p) for p in pts)


def _pred_stat(b: dict, sentence: str = "", geo=None) -> bool:
    return bool(re.search(r"\d", str(b.get("number") or "")))


def _pred_items_numeric(b: dict, sentence: str = "", geo=None) -> bool:
    items = b.get("items") or []
    return isinstance(items, list) and len(items) >= 2 and all(isinstance(x, dict) and x.get("value") is not None for x in items[:2])


def _pred_line_chart(b: dict, sentence: str = "", geo=None) -> bool:
    pts = b.get("points") or []
    return isinstance(pts, list) and len(pts) >= 2


def _pred_timeline(b: dict, sentence: str = "", geo=None) -> bool:
    items = b.get("items") or []
    return isinstance(items, list) and len(items) >= 1 and any(isinstance(x, dict) and bool(str(x.get("year") or "").strip()) for x in items)


def _pred_versus(b: dict, sentence: str = "", geo=None) -> bool:
    l = b.get("left")
    r = b.get("right")
    return isinstance(l, dict) and isinstance(r, dict) and bool(str(l.get("title") or "").strip()) and bool(str(r.get("title") or "").strip())


def _pred_photo(b: dict, sentence: str = "", geo=None) -> bool:
    q = re.sub(r"[^\w\s\-',.]", " ", str(b.get("query") or "")).strip()
    return len(q) >= 3


def _pred_items_nonempty(b: dict, sentence: str = "", geo=None) -> bool:
    items = b.get("items") or []
    return isinstance(items, list) and len(items) >= 1


def _pred_elements_nonempty(b: dict, sentence: str = "", geo=None) -> bool:
    els = b.get("elements") or []
    return isinstance(els, list) and len(els) >= 1


def _pred_area_map(b: dict, sentence: str = "", geo=None) -> bool:
    return areamap.valid_claim(b)


def _pred_always_true(b: dict, sentence: str = "", geo=None) -> bool:
    return isinstance(b, dict) and bool(b.get("kind"))


BEAT_RULES: Dict[str, Dict[str, Any]] = {
    "authored": {"predicate": lambda b, s="", g=None: bool(b.get("scene_id")), "reason": "authored beat requires a scene_id"},
    "year_counter": {"predicate": lambda b, s="", g=None: _num(b.get("year"), -5000, 2100, None) is not None, "reason": "year_counter requires a real year number"},
    "person_card": {"predicate": lambda b, s="", g=None: bool(str(b.get("name") or b.get("title") or "").strip()), "reason": "person_card requires the person's name"},
    "city_skyline": {"predicate": lambda b, s="", g=None: bool(str(b.get("title") or "").strip()), "reason": "city_skyline requires a title naming the city"},
    "architecture": {"predicate": lambda b, s="", g=None: bool(str(b.get("title") or "").strip()), "reason": "architecture requires a title naming the building"},
    "mystery_scene": {"predicate": lambda b, s="", g=None: bool(str(b.get("question") or b.get("text") or "").strip()), "reason": "mystery_scene requires a question"},
    "area_map": {
        "predicate": _pred_area_map,
        "reason": "area_map requires an `area` object with a place and a value (or a compare ratio)",
    },
    "elevation_profile": {
        "predicate": _pred_elevation_profile,
        "reason": "elevation_profile requires numeric altitude data and geographic elevation context",
    },
    "map": {
        "predicate": _pred_map,
        "reason": "map requires a valid place name or country code in the beat",
    },
    "map_pin": {
        "predicate": _pred_map_pin,
        "reason": "map_pin requires at least one point with a place name",
    },
    "stat": {
        "predicate": _pred_stat,
        "reason": "stat requires numeric data in 'number'",
    },
    "stat_ring_v2": {
        "predicate": _pred_stat,
        "reason": "stat_ring_v2 requires numeric data in 'number'",
    },
    "bars": {
        "predicate": _pred_items_numeric,
        "reason": "bars requires at least 2 numeric items",
    },
    "pie_chart": {
        "predicate": _pred_items_numeric,
        "reason": "pie_chart requires at least 2 numeric items",
    },
    "line_chart": {
        "predicate": _pred_line_chart,
        "reason": "line_chart requires at least 2 data points",
    },
    "timeline": {
        "predicate": _pred_timeline,
        "reason": "timeline requires dated items",
    },
    "timeline_card": {
        "predicate": _pred_timeline,
        "reason": "timeline_card requires dated items",
    },
    "versus": {
        "predicate": _pred_versus,
        "reason": "versus requires both left and right titles",
    },
    "split": {
        "predicate": _pred_versus,
        "reason": "split requires both left and right titles",
    },
    "photo": {
        "predicate": _pred_photo,
        "reason": "photo requires a valid English search query",
    },
    "list": {
        "predicate": _pred_items_nonempty,
        "reason": "list requires non-empty items",
    },
    "icons": {
        "predicate": _pred_items_nonempty,
        "reason": "icons requires non-empty items",
    },
    "ticker": {
        "predicate": _pred_items_nonempty,
        "reason": "ticker requires non-empty items",
    },
    "cardstack": {
        "predicate": _pred_items_nonempty,
        "reason": "cardstack requires non-empty items",
    },
    "canvas": {
        "predicate": _pred_elements_nonempty,
        "reason": "canvas requires non-empty elements",
    },
    "generative_canvas": {
        "predicate": _pred_elements_nonempty,
        "reason": "generative_canvas requires non-empty elements",
    },
    "custom_scene": {
        "predicate": _pred_always_true,
        "reason": "invalid custom_scene",
    },
    "bigtext": {"predicate": _pred_always_true, "reason": "invalid bigtext"},
    "versus_battle": {"predicate": _pred_always_true, "reason": "invalid versus_battle"},
    "animated_route": {"predicate": _pred_always_true, "reason": "invalid animated_route"},
    "balance_meter": {"predicate": _pred_always_true, "reason": "invalid balance_meter"},
    "deep_time_slider": {"predicate": _pred_always_true, "reason": "invalid deep_time_slider"},
    "stack_pyramid": {"predicate": _pred_always_true, "reason": "invalid stack_pyramid"},
    "macro_zoom_globe": {"predicate": _pred_always_true, "reason": "invalid macro_zoom_globe"},
    "subsurface_mine": {"predicate": _pred_always_true, "reason": "invalid subsurface_mine"},
    "dot_matrix_population": {"predicate": _pred_always_true, "reason": "invalid dot_matrix_population"},
    "money_waterfall": {"predicate": _pred_always_true, "reason": "invalid money_waterfall"},
    "frontline_clash": {"predicate": _pred_always_true, "reason": "invalid frontline_clash"},
    # أنماط مشاهد سينمائية جديدة
    "cinematic_dramatic": {"predicate": _pred_elements_nonempty, "reason": "cinematic_dramatic requires elements"},
    "architectural_blueprint": {"predicate": _pred_elements_nonempty, "reason": "architectural_blueprint requires elements"},
    "celestial_constellation": {"predicate": _pred_elements_nonempty, "reason": "celestial_constellation requires elements"},
    "kinetic_wave_field": {"predicate": _pred_elements_nonempty, "reason": "kinetic_wave_field requires elements"},
    "radial_light_cathedral": {"predicate": _pred_elements_nonempty, "reason": "radial_light_cathedral requires elements"},
    "topographic_contour": {"predicate": _pred_elements_nonempty, "reason": "topographic_contour requires elements"},
}


def guard_beat(b: Any, scene: dict, beat_index: int, sentence: str, geo=None) -> dict:
    """Checks `b` against `BEAT_RULES`. If the predicate fails, replaces with safe category fallback and logs warning."""
    beat_id = f"{scene.get('id', 'scene')}:{beat_index}"
    if not isinstance(b, dict) or b.get("kind") not in BEAT_RULES:
        fb = normalize_beat(fallback_beat(scene, beat_index, sentence), sentence, geo)
        record_fallback(f"unknown_or_missing_beat_kind:{b.get('kind') if isinstance(b, dict) else type(b).__name__}", beat_id=beat_id, beat=fb)
        return validate_beat(fb)

    kind = b["kind"]
    rule = BEAT_RULES[kind]
    if not rule["predicate"](b, sentence, geo):
        fb = normalize_beat(fallback_beat(scene, beat_index, sentence), sentence, geo)
        record_fallback(rule["reason"], beat_id=beat_id, beat=fb)
        return validate_beat(fb)

    normed = normalize_beat(b, sentence, geo)
    return validate_beat(normed)


def beats_for_scene(scene, geo=None):

    """مقاطع المشهد: إذا كان المقطع مخصصاً بالكود الأصلي (tsx_id) لكل المشهد، يُحفظ كمقطع واحد متكامل؛ وإلا حسب الجمل."""
    raw = scene.get("beats") if isinstance(scene.get("beats"), list) else []
    if len(raw) == 1 and isinstance(raw[0], dict) and raw[0].get("tsx_id"):
        full_narr = scene.get("narration", "")
        b0 = dict(raw[0])
        normed = normalize_beat(b0, full_narr, geo)
        for k in ("tsx_id", "narration", "video_title", "facts_summary", "video_countries", "video_cities", "scene_spec", "narration_cues", "concept", "accent", "secondary_accent"):
            if k in b0 and k not in normed:
                normed[k] = b0[k]
        return [normed]
    sents = sentences(scene.get("narration", ""))
    out = []
    for i, s in enumerate(sents):
        b = raw[i] if i < len(raw) else fallback_beat(scene, i, s)
        out.append(normalize_beat(b, s, geo))
    return out
