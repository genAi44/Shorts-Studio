"""المخرج البصري: لكل جملة منطوقة مشهد حركي (beat) يُرسم بالكود في Remotion."""

import copy

import json

import re

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from .config import ROOT, record_fallback
from .icons import pick_icons_for_beat, _has_whole_word
from . import areamap

_SPEC_SCHEMA_PATH = ROOT / "spec_schema.json"
_SPEC_SCHEMA: Dict[str, Any] = json.loads(_SPEC_SCHEMA_PATH.read_text(encoding="utf-8")) if _SPEC_SCHEMA_PATH.exists() else {"common_fields": {}, "beats": {}}


def validate_beat(beat: Dict[str, Any]) -> Dict[str, Any]:
    """Validates a beat dictionary strictly against `spec_schema.json`.
    Any unknown field or type mismatch raises a ValueError instead of silently dropping.
    """
    if not isinstance(beat, dict):
        raise ValueError(f"Beat must be a dict, got {type(beat).__name__}")
    kind = beat.get("kind")
    beats_schema = _SPEC_SCHEMA.get("beats", {})
    if not kind or kind not in beats_schema:
        raise ValueError(f"Invalid or unknown beat kind: {kind!r}")

    b_def = beats_schema[kind]
    common_fields = _SPEC_SCHEMA.get("common_fields", {})
    allowed_fields = {**common_fields, **b_def.get("fields", {})}

    # 1. Check required fields
    for req in b_def.get("required", []):
        if req not in beat or beat[req] is None:
            raise ValueError(f"Missing required field '{req}' for beat kind '{kind}'")

    # 2. Check for any undeclared field & validate field types
    for k, val in beat.items():
        if k not in allowed_fields:
            raise ValueError(f"Field '{k}' is not declared in spec_schema.json for beat kind '{kind}'")
        if val is None:
            continue
        expected_type = allowed_fields[k]
        if expected_type == "string" and not isinstance(val, str):
            raise ValueError(f"Field '{k}' in beat kind '{kind}' must be string, got {type(val).__name__}")
        elif expected_type == "number" and (not isinstance(val, (int, float)) or isinstance(val, bool)):
            raise ValueError(f"Field '{k}' in beat kind '{kind}' must be number, got {type(val).__name__}")
        elif expected_type == "boolean" and not isinstance(val, bool):
            raise ValueError(f"Field '{k}' in beat kind '{kind}' must be boolean, got {type(val).__name__}")
        elif expected_type == "array" and not isinstance(val, list):
            raise ValueError(f"Field '{k}' in beat kind '{kind}' must be array, got {type(val).__name__}")
        elif expected_type == "object" and not isinstance(val, dict):
            raise ValueError(f"Field '{k}' in beat kind '{kind}' must be object, got {type(val).__name__}")

    return beat


_PLAYBOOK_PATH = Path(__file__).parent / "playbook.md"

_PLAYBOOK = ""

try:

    _PLAYBOOK = _PLAYBOOK_PATH.read_text(encoding="utf-8")

except Exception:

    pass

ICONS = ["pin", "building", "mountain", "clock", "coin", "person", "people", "book", "atom", "bulb", "globe", "flag",
         "arrow-up", "arrow-down", "arrow-left", "arrow-right", "star", "heart", "lock", "key", "chart", "water", "fire",
         "leaf", "shield", "scale", "crown", "rocket", "brain", "phone", "sun", "moon", "check", "cross", "plane", "home",
         "warning", "question", "bolt", "eye"]

KINDS = [
    "custom_scene",
    "generative_canvas",
    "area_map", "map_pin", "timeline_card", "stat_ring_v2", "elevation_profile",
    "versus_battle", "animated_route", "balance_meter", "deep_time_slider",
    "stack_pyramid",     "macro_zoom_globe", "subsurface_mine", "dot_matrix_population",
    "money_waterfall", "frontline_clash",
    "line_chart", "pie_chart", "map", "stat", "bigtext", "bars", "timeline", "versus", "list", "icons", "canvas", "photo", "split", "ticker", "cardstack",
    "city_skyline", "architecture", "mystery_scene", "year_counter", "person_card", "authored",
    # أنماط مشاهد سينمائية جديدة لتنويع الحركة والإضاءة
    "cinematic_dramatic", "architectural_blueprint", "celestial_constellation",
    "kinetic_wave_field", "radial_light_cathedral", "topographic_contour",
]

COLORS = ["accent", "accent2", "text", "hl0", "hl1", "hl2", "hl3"]

ENTERS = ["rise", "drop", "pop", "left", "right", "fade"]

CAMERAS = ["push-in", "zoom-in", "zoom-out", "pan-left", "pan-right", "tilt-up", "tilt-down", "parallax", "handheld", "pan", "static", "pull-out", "zoom-punch", "pan-horizontal", "pan-vertical"]

TERM = re.compile('[.!؟?؛:…،,-]+$')

STRIP = '»«"()“”‘’'

# Arabic keyword → short icon name from ICONS list
_KW_ICONS = [
    (["توسع", "انتشار", "خريطة", "جغرافي", "إقليم", "حدود", "ملاحة", "بحار"], "globe"),
    (["حرب", "قتال", "معركة", "جيش", "عسكر", "انتصار", "هزيمة", "غزو", "سلاح"], "shield"),
    (["ملك", "إمبراطور", "حاكم", "سلطة", "حكم", "سياسة", "قرار", "أمير", "خليفة"], "crown"),
    (["اقتصاد", "مال", "ثروة", "تجارة", "خزينة", "فقر", "غنى", "ذهب", "نقود"], "coin"),
    (["علم", "اكتشاف", "بحث", "تقنية", "تطور", "ابتكار", "فيزياء", "كيمياء"], "atom"),
    (["مدينة", "بناء", "معمار", "حصن", "برج", "أثر", "معبد", "قصر"], "building"),
    (["وقت", "زمن", "سنة", "قرن", "عصر", "مرحلة", "فترة", "تاريخ", "عهد"], "clock"),
    (["شعب", "مجتمع", "ناس", "سكان", "جماهير", "أمة", "قبيلة", "جماعة"], "people"),
    (["كتاب", "علم", "معرفة", "ثقافة", "فكر", "أدب", "فلسفة", "كتابة"], "book"),
    (["دين", "عبادة", "روح", "إيمان", "مقدس", "كنيسة", "مسجد", "معبد"], "star"),
    (["طبيعة", "بيئة", "نهر", "جبل", "بحر", "غابة", "صحراء", "أرض"], "mountain"),
    (["تراجع", "انهيار", "سقوط", "أزمة", "انهار", "فشل", "خسارة", "ضعف"], "arrow-down"),
    (["نمو", "صعود", "ارتفاع", "نجاح", "تقدم", "ازدهار", "توسع", "قوة"], "arrow-up"),
    (["عالم", "دولة", "أمم", "دبلوماسية", "سفير", "معاهدة", "تحالف"], "globe"),
    (["نار", "حرق", "دمار", "هجوم", "قصف", "انفجار"], "fire"),
    (["شريعة", "قانون", "عدل", "قضاء", "ميزان", "حقوق", "دستور"], "scale"),
    (["تكنولوجيا", "ثورة", "صناعة", "طاقة", "برق", "كهرباء"], "bolt"),
    (["قلب", "حب", "شعور", "وجدان", "إنسانية", "رحمة"], "heart"),
    (["مفتاح", "سر", "اكتشاف", "حل", "لغز", "باب", "فتح"], "key"),
    (["مخ", "فكر", "ذكاء", "عقل", "خطط", "استراتيجية"], "brain"),
]

def _pick_icon_for_sentence(sent: str) -> str:
    """Pick a contextually appropriate short icon name based on whole-word Arabic sentence keywords."""
    for keywords, icon in _KW_ICONS:
        if any(_has_whole_word(sent, kw) for kw in keywords):
            return icon
    fallback = ["globe", "crown", "shield", "clock", "building", "people", "chart", "star", "key", "fire", "brain", "scale"]
    return fallback[abs(hash(sent)) % len(fallback)]

def sentence_groups(text):

    """مجموعات فهارس الكلمات لكل جملة/مقطع؛ تقسم على علامات الترقيم (بما فيها الفاصلة العربية) وتفكك المقاطع الطويلة لإيقاع مونتاج شورتس ديناميكي."""
    toks = (text or "").split()
    if not toks:
        return []
    groups, cur = [], []
    for i, t in enumerate(toks):
        cur.append(i)
        if TERM.search(t.strip(STRIP)):
            groups.append(cur)
            cur = []
    if cur:
        groups.append(cur)
    merged = []
    for g in groups:
        if merged and len(g) < 3:
            merged[-1] = merged[-1] + g
        elif merged and len(merged[-1]) < 3:
            merged[-1] = merged[-1] + g
        else:
            merged.append(g)
    final_groups = []
    for g in merged:
        if len(g) >= 8:
            mid = len(g) // 2
            final_groups.append(g[:mid])
            final_groups.append(g[mid:])
        else:
            final_groups.append(g)
    return final_groups

def sentences(text):

    toks = (text or "").split()
    return [" ".join(toks[i] for i in g) for g in sentence_groups(text)]

# ------------------------------------------------------------------ تنظيف المقاطع

def _s(v, n=40):
    cleaned = re.sub(r"\s+", " ", str(v if v is not None else "")).strip()
    if len(cleaned) <= n:
        return cleaned
    words_out = []
    cur_len = 0
    for w in cleaned.split():
        if words_out and cur_len + 1 + len(w) > n:
            break
        words_out.append(w)
        cur_len += len(w) + (1 if len(words_out) > 1 else 0)
    return " ".join(words_out) if words_out else cleaned.split()[0]

def _words(v, maxw):
    cleaned = re.sub(r"\s+", " ", str(v if v is not None else "")).strip()
    return " ".join(cleaned.split()[:maxw])

def _num(v, lo, hi, d=0.0):

    try:
        return max(lo, min(hi, float(v)))
    except Exception:
        return d

def _add_camera(out, b):

    cam = b.get("camera")
    if cam in CAMERAS:
        out["camera"] = cam
    for k in ("scene_spec", "narration_cues", "svg_layers", "environment", "secondary_accent", "tsx_id", "concept", "photo_subject"):
        if b.get(k) is not None and k not in out:
            out[k] = b[k]
    return out


def normalize_beat(b, sentence="", geo=None):

    """يقصّ ويصحّح مقطعاً من LLM؛ أي شيء غير صالح يُستبدل بنص كبير آمن."""
    b = b if isinstance(b, dict) else {}
    raw_kind = b.get("kind")
    # Convert any legacy/hallucinated icon_scene into clean icons or bigtext
    if raw_kind == "icon_scene":
        badges = b.get("badges") or b.get("items") or []
        valid_items = []
        for bg in badges[:4]:
            if isinstance(bg, dict) and _words(bg.get("label") or bg.get("text"), 3):
                ic_raw = str(bg.get("icon") or "").split("/")[-1].replace(".svg", "").replace("_", "-")
                ic_clean = ic_raw if ic_raw in ICONS else _pick_icon_for_sentence(bg.get("label") or sentence)
                valid_items.append({"icon": ic_clean, "label": _words(bg.get("label") or bg.get("text"), 3)})
        if len(valid_items) >= 2:
            b = {"kind": "icons", "title": b.get("title") or b.get("text") or "", "items": valid_items, "camera": b.get("camera")}
            raw_kind = "icons"
        else:
            b = {"kind": "bigtext", "text": b.get("title") or b.get("text") or "", "sub": b.get("center_label") or b.get("sub") or "", "camera": b.get("camera")}
            raw_kind = "bigtext"
    kind = raw_kind if raw_kind in KINDS else "bigtext"
    out = {"kind": kind, "title": _words(b.get("title"), 7)}
    fallback_text = _words(b.get("text") or b.get("title") or " ".join(sentence.split()[:4]), 6).strip(".!؟?،:؛ ")
    def bigtext():
        # A beat the director asked for (kind != bigtext) that cannot be drawn: never degrade silently.
        degraded = raw_kind not in (None, "bigtext")
        if degraded:
            why = f"{raw_kind} beat failed its preconditions" if raw_kind in KINDS else f"unknown beat kind {raw_kind!r}"
            record_fallback(why + " -> bigtext/photo", beat_id=str(raw_kind))
        # إذا كانت الجملة تشير لكائن حقيقي ملموس، فضّل صورة بطلة
        photo_beat = detect_photo_beat(sentence)
        if photo_beat:
            if degraded:
                photo_beat["_fallback"] = True
            return photo_beat
        o = {"kind": "bigtext", "title": "", "text": fallback_text or "…"}
        if degraded:
            o["_fallback"] = True
        if b.get("sub"):
            o["sub"] = _words(b.get("sub"), 8)
        if b.get("layout") in ("center", "stack", "diag", "left"):
            o["layout"] = b["layout"]
        return _add_camera(o, b)

    _handler = _NORMALIZE_KIND.get(kind)
    if _handler is not None:
        _res = _handler(b, bigtext, fallback_text, geo, kind, out, sentence)
        if _res is not None:
            return _res
    # canvas
    els = []
    for e in (b.get("elements") or [])[:14]:
        if not isinstance(e, dict):
            continue
        t = e.get("type")
        if t not in ("text", "shape", "icon", "line", "arrow"):
            continue
        el = {"type": t, "x": _num(e.get("x"), 0, 1080, 540), "y": _num(e.get("y"), 300, 1500, 900),
              "color": e.get("color") if e.get("color") in COLORS else "accent",
              "enter": e.get("enter") if e.get("enter") in ENTERS else "rise", "delay": _num(e.get("delay"), 0, 4, 0)}
        if e.get("loop") in ("float", "pulse", "spin"):
            el["loop"] = e["loop"]
        if t == "text":
            el.update({"text": _s(e.get("text"), 40), "size": _num(e.get("size"), 28, 220, 80)})
            if not el["text"]:
                continue
        elif t == "icon":
            icon_name = e.get("name") if e.get("name") in ICONS else None
            if not icon_name or icon_name == "bulb":
                icon_name = _pick_icon_for_sentence(sentence) if sentence else "star"
            el.update({"name": icon_name, "size": _num(e.get("size"), 40, 420, 160)})
        elif t == "shape":
            el.update({"shape": e.get("shape") if e.get("shape") in ("circle", "rect", "ring", "tri", "star") else "circle",
                       "size": _num(e.get("size"), 20, 700, 120), "w": _num(e.get("w"), 10, 1000, 0), "h": _num(e.get("h"), 10, 1000, 0)})
            if not el["w"]:
                el.pop("w")
            if not el["h"]:
                el.pop("h")
        else:
            el.update({"x2": _num(e.get("x2"), 0, 1080, el["x"] + 200), "y2": _num(e.get("y2"), 300, 1500, el["y"]),
                       "stroke": _num(e.get("stroke"), 3, 30, 10)})
        els.append(el)
    if not els:
        return bigtext()
    out["elements"] = els
    return _add_camera(out, b)


# ------------------------------------------------------------------ بدائل بلا نموذج

# خريطة ترجمات سريعة للمدن والمعالم العربية الشائعة لضمان أفضل نتائج صور
from .geo import WORLD_CITIES, ISO3_TO_COUNTRY_EN, detect_city_in_text


# ------------------------------------------------------------------ المخرج (DeepSeek)

# Re-exported so `pipeline.direct.<name>` keeps working.
from .direct_photo import (  # noqa: E402,F401
    CINEMATIC_STYLES,
    CITY_EN,
    _PHOTO_PATTERNS,
    _number_in_text,
    detect_photo_beat,
    fallback_beat,
    photo_to_text,
)

# Re-exported so `pipeline.direct.<name>` keeps working.
from .direct_guard import (  # noqa: E402,F401
    BEAT_RULES,
    _ELEV_GUARD_RE,
    _WAR_CONFLICT_RE,
    _pred_always_true,
    _pred_area_map,
    _pred_elements_nonempty,
    _pred_elevation_profile,
    _pred_items_nonempty,
    _pred_items_numeric,
    _pred_line_chart,
    _pred_map,
    _pred_map_pin,
    _pred_photo,
    _pred_stat,
    _pred_timeline,
    _pred_versus,
    _real_point,
    beats_for_scene,
    guard_beat,
)

# Re-exported so `pipeline.direct.<name>` keeps working.
from .direct_apply import (  # noqa: E402,F401
    _assign_scene_beats,
    _diversify_beats,
    _enrich_hook_map,
    _merge_visual_plan,
    _retry_failed_plan,
    _storyteller_pass,
    apply_beats,
    auto_beats,
)

# Re-exported so `pipeline.direct.<name>` keeps working.
from .direct_prompts import (  # noqa: E402,F401
    AREA_RULES,
    DIRECTOR_SYSTEM,
    PHOTO_RULES,
    VISUAL_CRAFT,
    director_prompt,
    director_system,
)

# Re-exported so `pipeline.direct.<name>` keeps working.
from .direct_kinds import (  # noqa: E402,F401
    _NORMALIZE_KIND,
    _normalize_beat_architecture,
    _normalize_beat_area_map,
    _normalize_beat_authored,
    _normalize_beat_bars,
    _normalize_beat_bigtext,
    _normalize_beat_cardstack,
    _normalize_beat_cinematic_dramatic,
    _normalize_beat_city_skyline,
    _normalize_beat_custom_scene,
    _normalize_beat_elevation_profile,
    _normalize_beat_generative_canvas,
    _normalize_beat_icons,
    _normalize_beat_line_chart,
    _normalize_beat_list,
    _normalize_beat_map,
    _normalize_beat_map_pin,
    _normalize_beat_mystery_scene,
    _normalize_beat_person_card,
    _normalize_beat_photo,
    _normalize_beat_pie_chart,
    _normalize_beat_split,
    _normalize_beat_stat,
    _normalize_beat_stat_ring_v2,
    _normalize_beat_ticker,
    _normalize_beat_timeline,
    _normalize_beat_timeline_card,
    _normalize_beat_versus,
    _normalize_beat_versus_battle,
    _normalize_beat_year_counter,
)
