"""المخرج البصري: لكل جملة منطوقة مشهد حركي (beat) يُرسم بالكود في Remotion."""

import copy

import json

import re

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from .config import ROOT, record_fallback
from .icons import pick_icons_for_beat, _has_whole_word

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
    "map_pin", "timeline_card", "stat_ring_v2", "elevation_profile",
    "versus_battle", "animated_route", "balance_meter", "deep_time_slider",
    "stack_pyramid",     "macro_zoom_globe", "subsurface_mine", "dot_matrix_population",
    "money_waterfall", "frontline_clash",
    "line_chart", "pie_chart", "map", "stat", "bigtext", "bars", "timeline", "versus", "list", "icons", "canvas", "photo", "split", "ticker", "cardstack",
    "city_skyline", "architecture", "mystery_scene",
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
    for k in ("scene_spec", "narration_cues", "svg_layers", "environment", "secondary_accent", "tsx_id", "concept"):
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
        # إذا كانت الجملة تشير لكائن حقيقي ملموس، فضّل صورة بطلة
        photo_beat = detect_photo_beat(sentence)
        if photo_beat:
            return photo_beat
        o = {"kind": "bigtext", "title": "", "text": fallback_text or "…"}
        if b.get("sub"):
            o["sub"] = _words(b.get("sub"), 8)
        if b.get("layout") in ("center", "stack", "diag", "left"):
            o["layout"] = b["layout"]
        return _add_camera(o, b)

    if kind == "map_pin":
        region = b.get("region") or "egypt"
        pts = []
        for p in (b.get("points") or [])[:5]:
            if isinstance(p, dict):
                pts.append({
                    "name": _s(p.get("name"), 24),
                    "x": p.get("x", 540),
                    "y": p.get("y", 870),
                    "icon": p.get("icon") or "icons/map/map_pin.svg"
                })
        o = {
            "kind": "map_pin",
            "title": _words(b.get("title") or fallback_text, 7),
            "region": region,
            "points": pts
        }
        return _add_camera(o, b)

    if kind == "timeline_card":
        items = []
        for it in (b.get("items") or [])[:4]:
            if isinstance(it, dict):
                items.append({
                    "year": _s(it.get("year"), 12),
                    "label": _words(it.get("label") or it.get("text"), 6),
                    "icon": it.get("icon") or "icons/time/history_clock.svg"
                })
        o = {
            "kind": "timeline_card",
            "title": _words(b.get("title") or fallback_text, 7),
            "items": items
        }
        return _add_camera(o, b)

    if kind == "stat_ring_v2":
        if not _s(b.get("number")):
            return bigtext()
        picked = pick_icons_for_beat(sentence, b.get("label", ""), n=1)
        o = {
            "kind": "stat_ring_v2",
            "title": _words(b.get("title"), 7),
            "number": _s(b.get("number"), 16),
            "label": _words(b.get("label"), 8),
            "icon": b.get("icon") or (picked[0] if picked else "icons/coin/gold_bars.svg")
        }
        return _add_camera(o, b)

    if kind == "elevation_profile":
        _ELEV_VALID = re.compile(r"ارتفاع|قمة|جبل|سلسلة جبال|فوق سطح البحر|عمق|هضبة|أنديز|إيفرست|أمتار|متر|elevation|mountain|peak|altitude|sea level", re.I)
        combined_elev = f"{sentence} {b.get('title', '')} {b.get('unit', '')}"
        if not _s(b.get("height")) or not _ELEV_VALID.search(combined_elev) or re.search(r"حرب|معركة|نزاع|ثورة|تمرد", str(b.get("title") or "")):
            return bigtext()
        raw_unit = _s(b.get("unit") or "م", 8)
        if "كيلو" in raw_unit or raw_unit.lower() == "km":
            raw_unit = "م"
        o = {
            "kind": "elevation_profile",
            "title": _words(b.get("title") or b.get("peak_name") or fallback_text, 5),
            "capital": _words(b.get("capital") or b.get("title") or fallback_text, 4),
            "height": _s(b.get("height"), 16),
            "unit": raw_unit,
            "sea_label": _s(b.get("sea_label") or "مستوى سطح البحر", 20),
            "country": _s(b.get("country") or "", 6),
        }
        return _add_camera(o, b)

    if kind == "custom_scene":
        if isinstance(b.get("elements"), list) and b.get("elements"):
            try:
                from .generative_visuals import validate_generative_canvas_spec
                o = validate_generative_canvas_spec(b)
                o["kind"] = "custom_scene"
                if isinstance(b.get("scene_spec"), dict):
                    o["scene_spec"] = b["scene_spec"]
                if b.get("approach"):
                    o["approach"] = _s(b["approach"], 40)
                return _add_camera(o, b)
            except Exception:
                pass
        o = {
            "kind": "custom_scene",
            "title": _words(b.get("title") or fallback_text, 6),
            "scene_spec": b.get("scene_spec") if isinstance(b.get("scene_spec"), dict) else {"approach": _s(b.get("approach") or "", 40)},
        }
        if b.get("approach"):
            o["approach"] = _s(b["approach"], 40)
        if b.get("subtitle"):
            o["subtitle"] = _words(b["subtitle"], 7)
        return _add_camera(o, b)

    if kind == "generative_canvas":
        try:
            from .generative_visuals import validate_generative_canvas_spec
            o = validate_generative_canvas_spec(b)
            return _add_camera(o, b)
        except Exception:
            return bigtext()

    if kind in (
        "versus_battle", "animated_route", "balance_meter", "deep_time_slider",
        "stack_pyramid", "macro_zoom_globe", "subsurface_mine", "dot_matrix_population",
        "money_waterfall", "frontline_clash"
    ):
        allowed_story_fields = set((_SPEC_SCHEMA.get("beats", {}).get(kind, {}).get("fields") or {}).keys()) | set(_SPEC_SCHEMA.get("common_fields", {}).keys())
        o = {k: v for k, v in b.items() if k in allowed_story_fields}
        o["kind"] = kind
        o["title"] = _words(b.get("title") or fallback_text, 6)
        return _add_camera(o, b)

    if kind == "line_chart":
        pts = []
        for pt in (b.get("points") or [])[:8]:
            if not isinstance(pt, dict):
                continue
            try:
                pts.append({"label": _s(pt.get("label") or pt.get("x") or "", 12),
                             "value": float(pt.get("value") or pt.get("y") or 0)})
            except Exception:
                pass
        if len(pts) < 2:
            return bigtext()
        o = {
            "kind": "line_chart",
            "title": _words(b.get("title") or fallback_text, 7),
            "points": pts,
            "y_label": _s(b.get("y_label") or b.get("unit") or "", 16),
        }
        return _add_camera(o, b)

    if kind == "pie_chart":
        items = []
        total_v = 0.0
        for it in (b.get("items") or [])[:6]:
            if not isinstance(it, dict):
                continue
            try:
                v = float(it.get("value") or 0)
                items.append({"label": _s(it.get("label") or "", 20), "value": v})
                total_v += v
            except Exception:
                pass
        if len(items) < 2:
            return bigtext()
        # normalize to 100 if values look like raw counts not percents
        if total_v > 0 and abs(total_v - 100) > 5:
            items = [{"label": it["label"], "value": round(it["value"] / total_v * 100, 1)} for it in items]
        o = {
            "kind": "pie_chart",
            "title": _words(b.get("title") or fallback_text, 7),
            "items": items,
        }
        return _add_camera(o, b)

    if kind == "bigtext":
        return bigtext()
    if kind == "photo":
        q = re.sub(r"[^\w\s\-',.]", " ", _s(b.get("query"), 100)).strip()
        if fallback_text:
            det_c, det_d = detect_city_in_text(fallback_text)
            if det_d and det_d.get("en"):
                c_en = det_d["en"]
                cou_en = det_d.get("country", "")
                if c_en.lower() not in q.lower():
                    q = f"{c_en} {cou_en} landmark historical architecture".strip()
                    b = dict(b)
                    b["must_show"] = f"{c_en} {cou_en} landmark"
                    b["alt_queries"] = [f"{c_en} cityscape", f"{cou_en} landmark"]
        if len(q) < 3:
            return bigtext()
        _NO_CUTOUT_KW = re.compile(
            r"\b(city|capital|building|architecture|landscape|map|globe|world|street|plaza|palace|temple|ruins|fortress|castle|church|mosque|mountain|river|ocean|sea|war|battle|crowd|aerial|view|skyline|sucre|paz|bolivia|cairo|baghdad|damascus|jerusalem)\b",
            re.I,
        )
        allow_cutout = (b.get("cutout") is True) and not bool(_NO_CUTOUT_KW.search(f"{q} {b.get('must_show', '')}"))
        o = {"kind": "photo", "title": out["title"], "query": q, "text": _words(b.get("text"), 6).strip(".!؟?،:؛ "),
             "cutout": allow_cutout}
        if _s(b.get("number")):
            o["number"] = _s(b.get("number"), 16)
        if _s(b.get("must_show")):
            o["must_show"] = _s(b.get("must_show"), 80)
        if _s(b.get("avoid")):
            o["avoid"] = _s(b.get("avoid"), 80)
        alts = [re.sub(r"[^\w\s\-',.]", " ", _s(a, 100)).strip() for a in (b.get("alt_queries") or []) if isinstance(a, str)]
        alts = [a for a in alts if len(a) >= 3][:2]
        if alts:
            o["alt_queries"] = alts
        return _add_camera(o, b)
    if kind == "map":
        cs = [str(c).upper() for c in (b.get("countries") or []) if isinstance(c, str)]
        hl = [str(c).upper() for c in (b.get("highlight") or cs) if isinstance(c, str)]
        if geo is not None:
            cs = [c for c in cs if geo.has(c)]
            hl = [c for c in hl if geo.has(c)]
        pts = []
        for p in (b.get("points") or [])[:6]:
            try:
                la, lo = float(p["lat"]), float(p["lon"])
                if -90 <= la <= 90 and -180 <= lo <= 180:
                    pts.append({"name": _s(p.get("name"), 24), "lat": la, "lon": lo, "dot": p.get("dot") is not False})
            except Exception:
                pass
        if not cs and not hl and not pts:
            return bigtext()
        out.update({"countries": cs[:6], "highlight": hl[:4], "points": pts})
        return _add_camera(out, b)
    if kind == "stat":
        if not _s(b.get("number")):
            return bigtext()
        out.update({"number": _s(b.get("number"), 16), "label": _words(b.get("label"), 8)})
        if b.get("layout") in ("ring", "bar", "plain", "stack"):
            out["layout"] = b["layout"]
        return _add_camera(out, b)
    if kind == "bars":
        items = []
        for it in (b.get("items") or [])[:6]:
            try:
                lbl = _words(it.get("label"), 4)
                if not lbl:
                    continue
                items.append({"label": lbl, "value": float(it.get("value")),
                              **({"display": _s(it.get("display"), 12)} if it.get("display") else {})})
            except Exception:
                pass
        if len(items) < 2:
            return bigtext()
        out["items"] = items
        return _add_camera(out, b)
    if kind == "timeline":
        items = [{"year": _s(it.get("year"), 12), "label": _words(it.get("label"), 6)} for it in (b.get("items") or [])[:5]
                 if isinstance(it, dict) and _s(it.get("year"))]
        if len(items) < 2:
            return bigtext()
        out["items"] = items
        return _add_camera(out, b)
    if kind == "versus":
        def side(x):
            x = x if isinstance(x, dict) else {}
            o = {"title": _words(x.get("title"), 4)}
            if x.get("value"):
                o["value"] = _s(x.get("value"), 10)
            if x.get("sub"):
                o["sub"] = _words(x.get("sub"), 6)
            if x.get("icon") in ICONS:
                o["icon"] = x["icon"]
            return o
        l, r = side(b.get("left")), side(b.get("right"))
        if not l["title"] or not r["title"]:
            return bigtext()
        out.update({"left": l, "right": r})
        return _add_camera(out, b)
    if kind == "list":
        items = [{"text": _words(it.get("text") if isinstance(it, dict) else it, 6),
                  **({"icon": it["icon"]} if isinstance(it, dict) and it.get("icon") in ICONS else {})}
                 for it in (b.get("items") or [])[:5]]
        items = [i for i in items if i["text"]]
        if len(items) < 2:
            return bigtext()
        out["items"] = items
        return _add_camera(out, b)
    if kind == "icons":
        alt_icons = ["globe", "star", "crown", "shield", "building", "chart", "compass", "book"]
        used_short = set()
        items = []
        for idx, it in enumerate((b.get("items") or [])[:4]):
            if not isinstance(it, dict):
                continue
            ic = it.get("icon") if it.get("icon") in ICONS else "star"
            if ic in used_short:
                for cand in alt_icons:
                    if cand in ICONS and cand not in used_short:
                        ic = cand
                        break
            used_short.add(ic)
            lbl = _words(it.get("label") or it.get("text"), 3)
            if lbl:
                items.append({"icon": ic, "label": lbl})
        if not items:
            return bigtext()
        out["items"] = items
        return _add_camera(out, b)
    if kind == "split":
        def split_side(x):
            x = x if isinstance(x, dict) else {}
            o = {"title": _words(x.get("title"), 5)}
            if x.get("value"):
                o["value"] = _s(x.get("value"), 10)
            if x.get("sub"):
                o["sub"] = _words(x.get("sub"), 5)
            if x.get("icon") in ICONS:
                o["icon"] = x["icon"]
            return o
        l, r = split_side(b.get("left")), split_side(b.get("right"))
        if not l["title"] or not r["title"]:
            return bigtext()
        out.update({"left": l, "right": r})
        return _add_camera(out, b)
    if kind == "ticker":
        items = [{"text": _words(it.get("text") if isinstance(it, dict) else it, 7),
                  **({"icon": it["icon"]} if isinstance(it, dict) and it.get("icon") in ICONS else {})}
                 for it in (b.get("items") or [])[:8]]
        items = [i for i in items if i["text"]]
        if not items:
            return bigtext()
        out["items"] = items
        return _add_camera(out, b)
    if kind == "cardstack":
        items = [{"text": _words(it.get("text") if isinstance(it, dict) else it, 7),
                  **({"icon": it["icon"]} if isinstance(it, dict) and it.get("icon") in ICONS else {}),
                  **({"value": _s(it.get("value"), 10)} if isinstance(it, dict) and it.get("value") else {})}
                 for it in (b.get("items") or [])[:4]]
        items = [i for i in items if i["text"]]
        if not items:
            return bigtext()
        out["items"] = items
        return _add_camera(out, b)
    if kind == "city_skyline":
        o = {"kind": "city_skyline", "title": _words(b.get("title") or fallback_text, 5)}
        if b.get("subtitle") or b.get("sub"):
            o["subtitle"] = _words(b.get("subtitle") or b.get("sub"), 6)
        if isinstance(b.get("seed"), (int, float)):
            o["seed"] = int(b["seed"])
        return _add_camera(o, b)
    if kind == "architecture":
        o = {"kind": "architecture", "title": _words(b.get("title") or fallback_text, 5)}
        if b.get("subtitle") or b.get("sub"):
            o["subtitle"] = _words(b.get("subtitle") or b.get("sub"), 6)
        if b.get("era"):
            o["era"] = _words(b.get("era"), 5)
        if isinstance(b.get("seed"), (int, float)):
            o["seed"] = int(b["seed"])
        return _add_camera(o, b)
    if kind == "mystery_scene":
        q = b.get("question") or b.get("text") or fallback_text
        o = {"kind": "mystery_scene", "question": _words(q, 10)}
        if b.get("subtitle") or b.get("sub"):
            o["subtitle"] = _words(b.get("subtitle") or b.get("sub"), 6)
        if isinstance(b.get("variant"), int):
            o["variant"] = b["variant"] % 3
        if isinstance(b.get("seed"), (int, float)):
            o["seed"] = int(b["seed"])
        return _add_camera(o, b)
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

def photo_to_text(b, sentence="", beat_id="photo"):
    """صورة تعذّر إيجادها ← لوحة رسم تعبيرية غنية بدلاً من شاشة سوداء مجردة."""
    text = sentence or b.get("text") or b.get("title") or "…"
    uid = str(b.get("id") or b.get("title") or beat_id)
    ent_iso3 = str(b.get("entity_iso3") or "").upper()
    if ent_iso3:
        try:
            from .geo import get_geo
            if get_geo().has(ent_iso3):
                return {
                    "kind": "map",
                    "countries": [ent_iso3],
                    "highlight": [ent_iso3],
                    "title": b.get("entity_name_ar") or b.get("title") or "",
                    "text": _words(text, 5),
                    "camera": b.get("camera") or "push-in",
                }
        except Exception:
            pass
    try:
        from .generative_visuals import compose_generative_canvas
        canvas = compose_generative_canvas(
            text,
            context=b.get("title") or "",
            is_fallback=True,
            fallback_reason="photo_to_text",
            beat_id=uid,
        )
        if b.get("camera"):
            canvas["camera"] = b["camera"]
        return canvas
    except Exception as exc:
        from .config import FallbackError
        if isinstance(exc, FallbackError):
            raise
        fb = {
            "kind": "bigtext",
            "title": "",
            "text": " ".join(text.split()[:5]).strip(".!؟?،:؛ "),
            "sub": " ".join(text.split()[5:10]).strip(".!؟?،:؛ ") if len(text.split()) > 5 else "",
            "layout": "center",
            "camera": b.get("camera", "push-in"),
            "_fallback": True,
        }
        record_fallback("photo_to_text_bigtext", beat_id=uid, beat=fb)
        return fb

# ------------------------------------------------------------------ تحسين غنى المشاهد البصرية
# أنماط المشاهد السينمائية لتنويع الحركة ولون المزاج
CINEMATIC_STYLES = [
    {"name": "cinematic_gold", "bg_grad": "radial-gradient(ellipse at 50% 30%, rgba(212,175,55,0.15) 0%, transparent 60%)", "accent": "#D4AF37", "lighting": "warm"},
    {"name": "cinematic_cool", "bg_grad": "radial-gradient(ellipse at 50% 30%, rgba(56,189,248,0.12) 0%, transparent 60%)", "accent": "#38bdf8", "lighting": "cool"},
    {"name": "cinematic_warm", "bg_grad": "radial-gradient(ellipse at 50% 30%, rgba(251,146,60,0.12) 0%, transparent 60%)", "accent": "#fb923c", "lighting": "warm"},
    {"name": "cinematic_dramatic", "bg_grad": "radial-gradient(ellipse at 50% 40%, rgba(244,63,94,0.10) 0%, transparent 60%)", "accent": "#f43f5e", "lighting": "dramatic"},
    {"name": "cinematic_neon", "bg_grad": "radial-gradient(ellipse at 50% 30%, rgba(168,85,247,0.12) 0%, transparent 60%)", "accent": "#a855f7", "lighting": "neon"},
]

# ------------------------------------------------------------------ بدائل بلا نموذج

# خريطة ترجمات سريعة للمدن والمعالم العربية الشائعة لضمان أفضل نتائج صور
from .geo import WORLD_CITIES, ISO3_TO_COUNTRY_EN, detect_city_in_text

CITY_EN = {
    "منف": "Memphis Egypt ancient capital",
    "طيبة": "Thebes Luxor Egypt temple",
    "طيبة (الأقصر)": "Thebes Luxor Egypt temple",
    "الإسكندرية": "Alexandria Egypt coast ancient",
    "الفسطاط": "Fustat ancient Cairo Egypt",
    "القاهرة": "Cairo Egypt historical citadel",
    "سوكري": "Sucre Bolivia colonial",
    "لاباز": "La Paz Bolivia city mountain",
    "القدس": "Jerusalem old city",
    "بغداد": "Baghdad historical architecture",
    "دمشق": "Damascus old city architecture",
    "مكة": "Mecca city holy",
    "المدينة": "Medina city historical",
    "الرياض": "Riyadh city skyline",
    "العاصمة الإدارية": "New Administrative Capital Egypt",
    "العاصمة الإدارية الجديدة": "New Administrative Capital Egypt"
}
# دمجه مع قاعدة البيانات العالمية
for _k, _v in WORLD_CITIES.items():
    if _k not in CITY_EN:
        CITY_EN[_k] = f"{_v['en']} {_v['country']} landmark historical architecture"

_PHOTO_PATTERNS = [
    (r"حضار|إمبراطور|شعوب|قبائل|قبيلة|سلالة", "ancient lost civilization ruins monument", "ancient stone ruins architecture", "modern tourist watermark"),
    (r"معبد|معابد|أهرام|أثر|آثار|صرح|مقابر", "ancient temple pyramid ruins archaeological site", "ancient temple structure", "watermark text collage"),
    (r"قصور|قصر|قلعة|حصن|أسوار", "ancient historical fortress castle architecture", "historical architecture building", "modern cars watermark"),
    (r"كنز|كنوز|ذهب|فضة|مجوهرات", "ancient golden treasures artifacts discovery", "golden artifacts discovery", "watermark modern text"),
    (r"فيضان|فيضانات|غرق|طوفان|أمطار|مياه|سدود|أنهار", "massive river flood deluge dramatic water disaster", "river flood water deluge", "watermark text"),
    (r"بركان|حمم|صهارة|فوهة", "active volcano lava eruption smoke landscape", "volcano eruption lava", "watermark text"),
    (r"محاصيل|زراعة|مخازن|قمح|طعام|غذاء|مجاعة", "ancient wheat agriculture grain harvest fields", "wheat grain fields harvest", "watermark text"),
    (r"دمار|انهيار|سقوط|موت|فناء|زوال", "ancient ruined city abandoned historical stone", "ruined stone architecture", "watermark modern text"),
    (r"حرب|معركة|جيش|عسكر|فرسان", "ancient historical army warriors fortress battlefield", "historical battle fortress", "watermark text"),
    (r"سفن|بحر|محيط|أسطول|ملاحة", "ancient wooden sailing ship ocean expedition", "wooden sailing ship", "watermark text"),
    (r"فضاء|نجوم|كواكب|مجرة", "deep space stars galaxy universe nebula astronomy", "deep space galaxy", "watermark text"),
    (r"صحراء|رمال|واحة", "vast desert sand dunes dramatic landscape", "desert sand dunes", "watermark text"),
    (r"غابة|طبيعة|أشجار|أدغال", "dense ancient rainforest jungle nature landscape", "rainforest jungle landscape", "watermark text"),
]

def detect_photo_beat(sentence: str, pt_name: str = "", cou_iso: str = "") -> Optional[Dict[str, Any]]:
    clean_pt = re.sub(r"\(.*?\)", "", pt_name).strip() if pt_name else ""
    try:
        from .geo_overlay import extract_timed_geo_mentions
        gm = extract_timed_geo_mentions(sentence, "", [], 150)
        if gm:
            m0 = next((x for x in gm if x.get("kind") in ("landmark", "capital", "city", "country")), gm[0])
            en_n = m0.get("name_en") or m0.get("name_ar") or ""
            if en_n and en_n.lower() == "marrakesh":
                en_n = "Marrakech"
            if en_n.lower() == "marrakesh":
                en_n = "Marrakech"
            m_iso3 = str(m0.get("iso3") or cou_iso or "").upper()
            c_en = ISO3_TO_COUNTRY_EN.get(m_iso3, "") or (ISO3_TO_COUNTRY_EN.get(cou_iso.upper(), "") if cou_iso else "")
            if en_n:
                q_base = f"{en_n} {c_en}".strip() if (c_en and c_en.lower() not in en_n.lower() and m0.get("kind") != "country") else en_n
                return {
                    "kind": "photo",
                    "query": f"{q_base} landmark architecture",
                    "text": _words(sentence, 5),
                    "camera": "parallax",
                    "must_show": q_base,
                    "avoid": "watermark text collage modern cars map flag",
                    "alt_queries": [f"{q_base} city", f"{en_n} landscape"],
                    "entity_iso3": m_iso3,
                    "entity_country_en": c_en,
                    "entity_name_ar": m0.get("name_ar") or "",
                }
    except Exception:
        pass
    detected_city, city_data = detect_city_in_text(sentence)
    if not clean_pt and detected_city:
        clean_pt = detected_city
        cou_iso = cou_iso or city_data.get("iso", "")

    # تحويل رمز الدولة إلى اسم إنجليزي حقيقي لتفادي مطابقات خاطئة مثل MAR -> Casa del Mar
    country_en = ISO3_TO_COUNTRY_EN.get(cou_iso.upper(), "") if cou_iso else ""

    if clean_pt or country_en:
        city_info = city_data or WORLD_CITIES.get(clean_pt)
        city_en = city_info["en"] if city_info else clean_pt
        if city_en and city_en.lower() == "marrakesh":
            city_en = "Marrakech"
        c_name = city_info["country"] if city_info else country_en
        
        if city_en and c_name:
            q = f"{city_en} {c_name} landmark historical architecture"
            must = f"{city_en} {c_name} historic architecture"
            alts = [f"{city_en} landmark", f"{c_name} historical place"]
        elif c_name:
            q = f"{c_name} landmark historical architecture"
            must = f"{c_name} historical architecture"
            alts = [f"{c_name} historical place", f"{c_name} architecture"]
        else:
            q = CITY_EN.get(clean_pt, f"{clean_pt} landmark historical architecture")
            must = clean_pt or "historical building"
            alts = [f"{clean_pt} landmark", f"{clean_pt} historical place"]

        return {
            "kind": "photo",
            "query": q,
            "text": _words(sentence, 5),
            "camera": "parallax",
            "must_show": must,
            "avoid": "watermark text collage modern cars",
            "alt_queries": alts,
            "entity_iso3": (cou_iso or "").upper(),
            "entity_country_en": country_en or c_name or "",
            "entity_name_ar": clean_pt or "",
        }
    try:
        from .geo_overlay import extract_timed_geo_mentions
        gm = extract_timed_geo_mentions(sentence, "", [], 150)
        if gm:
            m0 = next((x for x in gm if x.get("kind") in ("landmark", "capital", "city")), gm[0])
            en_n = m0.get("name_en") or m0.get("name_ar") or ""
            if en_n:
                return {
                    "kind": "photo",
                    "query": f"{en_n} historical landmark architecture",
                    "text": _words(sentence, 5),
                    "camera": "parallax",
                    "must_show": f"{en_n} architecture landmark",
                    "avoid": "watermark text collage modern cars",
                    "alt_queries": [f"{en_n} landmark", f"{en_n} heritage"],
                }
    except Exception:
        pass
    if not re.search(r"إحصائيات|ضحايا|مليون|مليار|نسبة|%|عدد السكان", sentence):
        for pat, query, must_show, avoid in _PHOTO_PATTERNS:
            if re.search(pat, sentence, re.I):
                return {
                    "kind": "photo",
                    "query": query,
                    "text": _words(sentence, 5),
                    "camera": "parallax",
                    "must_show": must_show,
                    "avoid": avoid,
                    "alt_queries": [" ".join(query.split()[:3]), "historical monument architecture"]
                }
    return None

def fallback_beat(scene, i, sentence):
    v = scene.get("visual") or {}

    # مشهد الحلقة المفتوحة (open_loop) مشهد توتر وتشويق وتساؤل ذكي متكامل بصرياً
    if scene.get("role") == "open_loop":
        from .generative_visuals import compose_generative_canvas
        return compose_generative_canvas(sentence, context=scene.get("on_screen") or "لغز وتساؤل")
    pts = v.get("points") or []
    cs = v.get("countries") or []
    cou_iso = cs[0] if cs else ""
    pt_name = pts[0].get("name", "") if pts else ""

    # فحص ما إذا كانت الجملة أو المشهد يذكر مدينة أو عاصمة معروفة
    detected_city, city_data = detect_city_in_text(sentence)
    if not detected_city:
        detected_city, city_data = detect_city_in_text(scene.get("on_screen", ""))

    # ملاحظة: الخرائط الجغرافية تُعرض الآن كطبقة MapOverlay ذكية متزامنة مع الصوت (pipeline/geo_overlay.py)،
    # لذلك يركز المشهد الأساسي على التكوين البصري والمعماري والتعبيري للجملة دون تكرار خريطة خلفية.

    # مشهد الـ Hook (الخطاف في أول ثوانٍ): يجب أن يكون مشهداً بطلاً جذاباً بصرياً (Hero Visual)
    if scene.get("role") == "hook" or i == 0:
        hero_photo = detect_photo_beat(sentence, pt_name, cou_iso)
        if hero_photo:
            hero_photo["camera"] = "parallax"
            return hero_photo
        from .generative_visuals import compose_generative_canvas
        return compose_generative_canvas(sentence, context=scene.get("on_screen") or v.get("text"))

    # إذا ورد ارتفاع/جبل → مخطط ارتفاع مرئي
    _HEIGHT_KW = re.compile(r"ارتفاع|قمة|جبل|سلسلة جبال|فوق سطح البحر|elevation|mountain|peak|above sea level|meters above|height", re.I)
    if _HEIGHT_KW.search(sentence):
        nums_h = re.findall(r"\d[\d,.]*", sentence)
        heights = []
        for n in nums_h:
            try:
                v = float(n.replace(",", ""))
                if 10 <= v <= 30000:
                    heights.append(n)
            except Exception:
                pass
        if heights:
            return {"kind": "elevation_profile", "title": _words(sentence, 5), "height": heights[0], "unit": "م", "sea_label": "سطح البحر", "camera": "push-in"}
    # نسب مئوية متعددة (≥2) → مخطط دائري
    pcts = re.findall(r"(\d+(?:\.\d+)?)\s*%", sentence)
    pct_labels = re.findall(r"([^\d،,]+?)\s+(\d+(?:\.\d+)?)\s*%", sentence)
    if len(pcts) >= 2:
        if pct_labels and len(pct_labels) >= 2:
            items = [{"label": _words(lbl.strip(), 4), "value": float(val)} for lbl, val in pct_labels[:5]]
        else:
            items = [{"label": f"{v}%", "value": float(v)} for v in pcts[:5]]
        return {"kind": "pie_chart", "title": _words(sentence, 5), "items": items, "camera": "push-in"}
    # سلسلة زمنية: ≥2 أزواج (سنة + قيمة) → line_chart
    year_val_pairs = re.findall(r"((?:19|20)\d{2})[^\d]{0,15}?(\d+(?:[\.,]\d+)?)", sentence)
    if len(year_val_pairs) >= 2:
        points = [{"label": yr, "value": float(val.replace(",", ""))} for yr, val in year_val_pairs[:6]]
        return {"kind": "line_chart", "title": _words(sentence, 5), "points": points, "camera": "push-in"}
    # إذا ورد تاريخ/سنة
    years = re.findall(r"\b(1\d{3}|20\d{2}|[1-9]\d{2})\b", sentence)
    if years:
        return {"kind": "timeline", "title": "", "items": [{"year": years[0], "label": _words(sentence, 5)}]}
    # إذا ورد رقم صريح
    nums = re.findall(r"\d+[\d,.]*", sentence)
    if nums and len(nums[0]) >= 2:
        return {"kind": "stat", "title": "", "number": nums[0], "label": _words(sentence, 5), "layout": "ring"}

    # إذا ورد مقارنة أو صراع أو تفوق طرفين
    _VS_KW = re.compile(r"مقابل|مقارنة|ضد|تنافس|صراع|حجم.*مقابل|تفوق|versus|vs|battle", re.I)
    if _VS_KW.search(sentence):
        tokens = re.split(r"مقابل|ضد|مقارنة", sentence)
        side_a = " ".join(tokens[0].strip().split()[-4:]) if len(tokens) > 1 else "الطرف الأول"
        side_b = _words(tokens[1].strip(), 4) if len(tokens) > 1 else "الطرف الثاني"
        nums = re.findall(r"\d[\d,.]*", sentence)
        v_a = float(nums[0].replace(",", "")) if nums else 100
        v_b = float(nums[1].replace(",", "")) if len(nums) > 1 else 60
        return {
            "kind": "versus_battle",
            "title": _words(sentence, 5),
            "left": {"title": side_a or "الطرف الأول", "subtitle": "", "badge": "طرف ١", "value": v_a},
            "right": {"title": side_b or "الطرف الثاني", "subtitle": "", "badge": "طرف ٢", "value": v_b},
            "camera": "push-in",
        }

    # إذا ورد ترتيب أو قائمة أو مراكز أولى (أغنى، أكبر، أفضل، المراكز) مع أرقام أو أسماء أعداد عربية
    _RANK_KW = re.compile(r"أغنى|أكبر|أفضل|أعلى|أقوى|المراكز|ترتيب|قائمة|ranking|top", re.I)
    _AR_NUM_WORDS = re.compile(r"ثلاث|أربع|خمس|ست|سبع|ثمان|تسع|عشر")
    if _RANK_KW.search(sentence) and not (cou_iso or pt_name):
        nums = re.findall(r"\d[\d,.]*", sentence)
        if len(nums) >= 3:
            return {
                "kind": "bars",
                "title": _words(sentence, 5),
                "items": [
                    {"label": _words(sentence, 2) + " ١", "value": 100, "display": nums[0]},
                    {"label": _words(sentence, 2) + " ٢", "value": 85, "display": nums[1]},
                    {"label": _words(sentence, 2) + " ٣", "value": 70, "display": nums[2]},
                ],
                "camera": "push-in",
            }
        if _AR_NUM_WORDS.search(sentence) or nums:
            return {
                "kind": "bars",
                "title": _words(sentence, 5),
                "items": [
                    {"label": "المركز ١", "value": 100, "display": "1"},
                    {"label": "المركز ٢", "value": 82, "display": "2"},
                    {"label": "المركز ٣", "value": 64, "display": "3"},
                ],
                "camera": "push-in",
            }

    # مفاهيم تخصصية تحتاج مشهد توليدي (بركان، غاز، طاقة، تضخم)
    _GEN_KW = re.compile(r"بركان|حمم|غاز طبيعي|طاقة|حصار|مضيق|ذكاء اصطناعي|بيانات|تضخم|صاروخ|باطن الأرض|ثروات", re.I)
    if _GEN_KW.search(sentence):
        from .generative_visuals import compose_generative_canvas
        return compose_generative_canvas(sentence, context=scene.get("on_screen"))

    # إذا كان المشهد خاتمة (CTA / دعوة للمتابعة والمشاركة): لا تبحث عن صورة عشوائية من الإنترنت (كتلافي خرائط منغوليا/الصين)
    if scene.get("role") in ("cta", "loop") or re.search(r"تابعنا|اشترك|اكتب.*التعليقات|شاركنا برأيك", sentence):
        from .generative_visuals import compose_generative_canvas
        return compose_generative_canvas(sentence, context=scene.get("on_screen") or "شاركنا في التعليقات")

    # إذا ارتبط المشهد بكيان ملموس، أثر، معلم، طبيعة أو بلد -> صورة حقيقية مرخصة
    photo_beat = detect_photo_beat(sentence, pt_name, cou_iso)
    if photo_beat:
        return photo_beat

    # بديل توليدي سياقي غني بدلاً من الشاشة الفارغة
    from .generative_visuals import compose_generative_canvas
    return compose_generative_canvas(sentence, context=scene.get("on_screen") or v.get("text"))


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


def _pred_map(b: dict, sentence: str = "", geo=None) -> bool:
    pts = b.get("points") or []
    cs = [str(c).upper() for c in (b.get("countries") or []) if isinstance(c, str)]
    hl = [str(c).upper() for c in (b.get("highlight") or cs) if isinstance(c, str)]
    if geo is not None:
        cs = [c for c in cs if geo.has(c)]
        hl = [c for c in hl if geo.has(c)]
    has_place_name = any(isinstance(p, dict) and bool(str(p.get("name") or "").strip()) for p in pts) or bool(cs) or bool(hl)
    return has_place_name


def _pred_map_pin(b: dict, sentence: str = "", geo=None) -> bool:
    pts = b.get("points") or []
    return isinstance(pts, list) and len(pts) >= 1 and any(isinstance(p, dict) and bool(str(p.get("name") or "").strip()) for p in pts)


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


def _pred_always_true(b: dict, sentence: str = "", geo=None) -> bool:
    return isinstance(b, dict) and bool(b.get("kind"))


BEAT_RULES: Dict[str, Dict[str, Any]] = {
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

# ------------------------------------------------------------------ المخرج (DeepSeek)

DIRECTOR_SYSTEM = """أنت كبير المخرجين الفنيين ومصممي الموشن غرافيك ومهندسي Remotion لفيديوهات Shorts العربية.

## المبدأ الأساسي: لا قوالب مسبقة التصميم. كل مشهد يبدأ من لوحة بيضاء (BLANK CANVAS).

مهمتك: لا تكرر قالباً ولا تختار من مكتبة تصاميم مسبقة.
لكل جملة منطوقة، عليك أن تتخيل المشهد من الصفر وتبتكر فكرة بصرية فريدة تعبّر عن المعنى الدقيق للجملة وكياناتها وأرقامها، وتصمم تكوينها البصري والحركي بالكامل.
يقوم المحرك بكتابة كود Remotion TSX ورسوم SVG المتجهة بالكامل خصيصاً لكل مشهد.

لكل جملة في السكربت، تخيّل من الصفر تصميماً بصرياً فريداً ومختلفاً تماماً عن المشاهد الأخرى، وحدد في المقطع (beat):
1. title: عنوان عربي مكثف ومباشر (3-6 كلمات) من صميم معنى الجملة.
2. concept: وصف بصري تفصيلي إبداعي خاص بهذه الجملة فقط (مثلاً: واجهة المحكمة العليا في سوكري بأعمدة كلاسيكية وختم دستوري متوهج، أو قمم جبال الأنديز المضاءة ليلاً لمدينة لاباز، أو خريطة جغرافية بالحدود الدقيقة، أو مشهد رمزي ملموس من الواقع — ممنوع القوالب أو الأشكال الهندسية الفارغة مثل دوائر ومثلثات عشوائية).
3. camera: حركة الكاميرا السينمائية ("push-in", "zoom-in", "pan-left", "tilt-up", "parallax", "zoom-out").
4. kind: "custom_scene" (إلزامي ليعمل محرك توليد الأكواد الأصلية Remotion TSX).

قواعد صارمة:
- لا تخترع أرقاماً أو تواريخ لم ترد في السكربت أو facts.
- كل مشهد مستقل في تصميمه وألوانه وحركته عن المشاهد الأخرى؛ يُمنع تكرار الفكرة البصرية أو استخدام قوالب ثابتة.
- أعد JSON فقط:
{"scenes":[{"id":"hook","beats":[{"kind":"custom_scene","title":"...","concept":"...","camera":"push-in"}]},{"id":"lead","beats":[{...}]},{"id":"body1","beats":[{...}]},{"id":"open_loop1","beats":[{...}]},{"id":"body2","beats":[{...}]},{"id":"open_loop2","beats":[{...}]},{"id":"body3","beats":[{...}]},{"id":"cta","beats":[{...}]}]}"""

PHOTO_RULES = """

صور حقيقية (kind = "photo"): يبحث التطبيق عن صورة مرخّصة من الإنترنت (Wikimedia Commons وPexels) ويعرضها بمعالجة مونتاج احترافية.

{"kind":"photo","query":"english search words","text":"عبارة عربية قصيرة ≤6 كلمات","cutout":false,"number":"35,000","must_show":"the main subject","avoid":"watermark text collage","alt_queries":["broader query","even broader"],"camera":"parallax"}

- query بالإنجليزية فقط، 2-6 كلمات، محدد وقابل للتصوير مع اسم كيان + بلد + سنة إن وجدت. مثال: "Casa de la Libertad Sucre Bolivia 1825", "human brain anatomy", "Berlin Wall fall 1989".

- alt_queries: قائمة من استعلامين احتياطيين أوسع تدريجياً (من الأكثر تحديداً إلى الأعم). مثال: ["Sucre Bolivia colonial architecture", "Bolivia colonial city"].

- must_show: وصف قصير بالإنجليزية لما يجب أن تُظهره الصورة بالضبط. مثال: "white colonial building facade".

- avoid: ما يجب استبعاده. مثال: "watermark text collage portrait person".

- في مشهد الخاتمة (cta): يُمنع استخدام kind="photo" لمنع جلب صور عشوائية لكلمة "العالم" أو "التعليقات"؛ استخدم "generative_canvas" فقط في الخاتمة.
- cutout=true فقط لجسم مفرد معزول تماماً (أداة، عملة، علم، مركبة). يُمنع منعاً باتاً وضع cutout=true للمدن والمباني والمعالم والخرائط والمناظر الطبيعية.

- number اختياري: رقم من الجملة يُعدّ تصاعدياً تحت الصورة.

- camera: "parallax" للمناظر والمدن، "push-in" للوجوه والمباني، "static" للأحداث التاريخية.

- استعمل photo فقط لما لا تستطيع city_skyline أو architecture أو mystery_scene أو generative_canvas أو map تمثيله (وجه شخص حقيقي، حدث تاريخي لا يُختزل في رمز). لا تزد عن 15-25% من المقاطع، ولا مقطعين متتاليين منه."""

def director_system(photos=True):

    pb = f"\n## دليل الحركة:\n{_PLAYBOOK}\n\n" if _PLAYBOOK else ""
    return pb + DIRECTOR_SYSTEM + (PHOTO_RULES if photos else "")

def director_prompt(script, scenes, mood=""):
    items = []
    for sc in scenes:
        items.append({
            "id": sc["id"],
            "role": sc.get("role", "body"),
            "narration": sc["narration"],
            "sentences": sentences(sc["narration"]),
            "on_screen": sc.get("on_screen", ""),
            "visual_hint": sc.get("visual")
        })
    return json.dumps({"title": script.get("title"), "mood": mood, "facts": script.get("facts", []), "scenes": items},
                      ensure_ascii=False)

def apply_beats(script, result, geo=None, llm_retry_fn: Optional[Callable[[List[str]], dict]] = None):

    """يدمج ناتج المخرج في السكربت بعد فحصه عبر BEAT_RULES (مع إعادة محاولة واحدة كحد أقصى للـ LLM) وتنظيفه."""
    from .scriptspec import scenes_of
    s = copy.deepcopy(script)
    result = result if isinstance(result, dict) else {}
    got = {x.get("id"): x.get("beats") for x in (result.get("scenes") or []) if isinstance(x, dict)}

    # Pre-check LLM beat plan against BEAT_RULES; allow max 1 retry to the LLM before forcing fallbacks
    if got and callable(llm_retry_fn):
        failed_reasons: List[str] = []
        for sc in scenes_of(s):
            raw_list = got.get(sc["id"])
            if not isinstance(raw_list, list):
                continue
            sents = sentences(sc["narration"])
            for i, s_txt in enumerate(sents):
                if i < len(raw_list) and isinstance(raw_list[i], dict):
                    rk = raw_list[i].get("kind")
                    rule = BEAT_RULES.get(rk)
                    if not rule or not rule["predicate"](raw_list[i], s_txt, geo):
                        failed_reasons.append(f"{sc['id']}[{i}] ({rk}): {rule['reason'] if rule else 'unknown kind'}")
        if failed_reasons:
            try:
                retry_res = llm_retry_fn(failed_reasons)
                if isinstance(retry_res, dict) and retry_res.get("scenes"):
                    got = {x.get("id"): x.get("beats") for x in (retry_res.get("scenes") or []) if isinstance(x, dict)}
            except Exception:
                pass

    targets = []
    for sc in scenes_of(s):
        target = s.get(sc["id"])
        if not target:
            continue
        raw = got.get(sc["id"])
        sents = sentences(sc["narration"])
        raw = raw if isinstance(raw, list) else []
        target["beats"] = [
            guard_beat(raw[i], sc, i, sents[i], geo) if i < len(raw) else validate_beat(normalize_beat(fallback_beat(sc, i, sents[i]), sents[i], geo))
            for i in range(len(sents))
        ]
        # إذا كان المشهد يحمل visual.type == "map" أو يذكر مدينة/عاصمة معروفة ولم يضع المخرج خريطة،
        # نضمن وجود مقطع خريطة حقيقي (map) للمدينة أو الدولة في أول جملة من المشهد
        vis = sc.get("visual") if isinstance(sc.get("visual"), dict) else {}
        det_city, det_info = detect_city_in_text(sc.get("on_screen", ""))
        if not det_city:
            det_city, det_info = detect_city_in_text(sc.get("narration", ""))

        has_map_beat = any(b.get("kind") in ("map", "map_pin") for b in target["beats"])
        if not has_map_beat and sc.get("role") in ("body", "lead") and target["beats"]:
            orig_concept = target["beats"][0].get("concept")
            if vis.get("type") == "map" and (vis.get("countries") or vis.get("points")):
                map_cand = normalize_beat({
                    "kind": "map",
                    "title": sc.get("on_screen") or _words(sents[0], 5),
                    "countries": vis.get("countries") or [],
                    "highlight": vis.get("highlight") or vis.get("countries") or [],
                    "points": vis.get("points") or [],
                    "camera": "zoom-in",
                }, sents[0], geo)
                if map_cand.get("kind") == "map":
                    if orig_concept:
                        map_cand["concept"] = orig_concept
                    target["beats"][0] = map_cand
            elif det_city and det_info:
                map_cand = normalize_beat({
                    "kind": "map",
                    "title": sc.get("on_screen") or det_city,
                    "countries": [det_info["iso"]],
                    "highlight": [det_info["iso"]],
                    "points": [{"name": det_city, "lat": det_info["lat"], "lon": det_info["lon"], "dot": True}],
                    "camera": "zoom-in",
                }, sents[0], geo)
                if map_cand.get("kind") == "map":
                    if orig_concept:
                        map_cand["concept"] = orig_concept
                    target["beats"][0] = map_cand
        targets.append(target)

    # دمج خطة محرك الذكاء البصري (Visual Intelligence Engine) لتوحيد السياق التاريخي والجغرافي عبر المشاهد
    try:
        from .visual_intelligence import analyze_script_visual_intelligence
        vi_plan = s.get("_visual_intelligence")
        if not isinstance(vi_plan, dict) or not vi_plan.get("scenes"):
            vi_plan = analyze_script_visual_intelligence(s, geo=geo, use_llm=bool(result))
            s["_visual_intelligence"] = vi_plan
        vi_by_id = {sc_v["id"]: sc_v for sc_v in (vi_plan.get("scenes") or []) if isinstance(sc_v, dict)}
        for t in targets:
            sc_vi = vi_by_id.get(t.get("id"))
            if not sc_vi:
                continue
            t["_vi"] = sc_vi
            for b in (t.get("beats") or []):
                if isinstance(b, dict):
                    b["visual_intelligence"] = {
                        "semantic_goal": sc_vi.get("semantic_goal"),
                        "historical_era": sc_vi.get("historical_era"),
                        "is_historical": sc_vi.get("is_historical"),
                        "visual_mode": sc_vi.get("visual_mode"),
                        "entities": [e.get("name") for e in (sc_vi.get("entities") or [])[:6]],
                        "relationships": sc_vi.get("relationships") or [],
                        "avoid": sc_vi.get("avoid"),
                    }
                    if b.get("kind") == "photo":
                        if not b.get("query") and sc_vi.get("media_query_en"):
                            b["query"] = sc_vi["media_query_en"]
                        if not b.get("must_show") and sc_vi.get("must_show"):
                            b["must_show"] = sc_vi["must_show"]
                        if not b.get("avoid") and sc_vi.get("avoid"):
                            b["avoid"] = sc_vi["avoid"]
                    if b.get("kind") == "photo" and sc_vi.get("media_query_en"):
                        b["query"] = sc_vi["media_query_en"]
                        if sc_vi.get("must_show"):
                            b["must_show"] = sc_vi["must_show"]
                        if sc_vi.get("avoid"):
                            b["avoid"] = sc_vi["avoid"]
    except Exception:
        pass

    # ضمان تنوّع بصري سينمائي: ترقية حتى مشهدين (hook / body) إلى صور حقيقية مرخّصة (photo)
    # لتفعيل تخطيط الشاشة المقسّمة (Photo Top + Panoramic Map Bottom) بدلاً من الاقتصار على رسوم SVG فقط
    photo_count = sum(1 for t in targets for b in (t.get("beats") or []) if b.get("kind") == "photo")
    map_count = sum(1 for t in targets for b in (t.get("beats") or []) if b.get("kind") in ("map", "map_pin"))
    if photo_count < 2:
        for t in targets:
            if photo_count >= 2:
                break
            if t.get("role") not in ("hook", "body") or not t.get("beats"):
                continue
            cur_kind = t["beats"][0].get("kind")
            if cur_kind == "photo":
                continue
            if cur_kind in ("map", "map_pin") and map_count <= 1:
                continue
            first_sent = (sentences(t.get("narration", "")) or [t.get("narration", "")])[0]
            pb = detect_photo_beat(first_sent) or detect_photo_beat(f"{t.get('on_screen', '')} {s.get('title', '')}")
            sc_vi = t.get("_vi") if isinstance(t.get("_vi"), dict) else {}
            if not pb and sc_vi.get("media_query_en"):
                pb = {
                    "kind": "photo",
                    "query": sc_vi["media_query_en"],
                    "text": _words(first_sent, 5),
                    "camera": "parallax",
                    "must_show": sc_vi.get("must_show") or sc_vi["media_query_en"],
                    "avoid": sc_vi.get("avoid") or "watermark text collage",
                    "alt_queries": [sc_vi["media_query_en"]],
                }
            if pb:
                if sc_vi.get("media_query_en"):
                    pb["query"] = sc_vi["media_query_en"]
                if sc_vi.get("must_show"):
                    pb["must_show"] = sc_vi["must_show"]
                if sc_vi.get("avoid"):
                    pb["avoid"] = sc_vi["avoid"]
                pb["text"] = _words(first_sent, 5)
                pb_norm = validate_beat(normalize_beat(pb, first_sent, geo))
                if pb_norm.get("kind") == "photo":
                    t["beats"][0] = pb_norm
                    photo_count += 1

    # إثراء خريطة المشهد الافتتاحي (Hook) بدبابيس جميع المدن/العواصم المذكورة في السكربت إن كانت نقاطها فارغة
    hook_target = s.get("hook")
    if hook_target and hook_target.get("beats"):
        for hb in hook_target["beats"]:
            if hb.get("kind") == "map" and not hb.get("points"):
                all_pts = []
                seen_c = set()
                for other_sc in scenes_of(s):
                    for txt in (other_sc.get("on_screen", ""), other_sc.get("narration", "")):
                        c_name, c_dict = detect_city_in_text(txt)
                        if c_name and c_name not in seen_c and c_dict:
                            seen_c.add(c_name)
                            all_pts.append({"name": c_name, "lat": c_dict["lat"], "lon": c_dict["lon"], "dot": True})
                if all_pts:
                    hb["points"] = all_pts[:6]
    # فحص ما بعدي: تنويع المقاطع، منع تكرار الخرائط أو أي نوع مرتين متتاليتين، وتنويع الكاميرا
    stat_choices = ["ring", "bar", "stack", "plain"]
    bigtext_choices = ["center", "stack", "diag", "left"]
    cam_choices = ["zoom-in", "pan-left", "zoom-out", "tilt-up", "parallax", "pan-right", "handheld"]
    used_stat_layouts = set()
    used_bigtext_layouts = set()
    prev_kind = None
    prev_beat = None
    prev_cam = None
    cam_counter = 0
    for target in targets:
        sents = sentences(target.get("narration", ""))
        beats = target.get("beats", [])
        seen_stat_numbers = set()
        seen_map_cities = set()
        for bi, b in enumerate(beats):
            cur_kind = b.get("kind")
            sent = sents[bi] if bi < len(sents) else ""

            # في مشهد الخاتمة (cta): حوّل أي photo عشوائي إلى generative_canvas نظيف
            if (target.get("role") == "cta" or target == targets[-1]) and cur_kind == "photo":
                from .generative_visuals import compose_generative_canvas
                b = compose_generative_canvas(sent, context=target.get("on_screen") or "شاركنا برأيك")
                beats[bi] = b
                cur_kind = "generative_canvas"

            # منع استخدام icons نهائياً: استبداله بـ stack_pyramid أو generative_canvas
            if cur_kind == "icons":
                items = b.get("items") or []
                if len(items) >= 2:
                    tiers = [{"label": it.get("label", ""), "value": f"{idx+1}"} for idx, it in enumerate(items)]
                    b = {"kind": "stack_pyramid", "title": b.get("title") or _words(sent, 5), "tiers": tiers, "camera": "tilt-up"}
                    beats[bi] = b
                    cur_kind = "stack_pyramid"
                else:
                    from .generative_visuals import compose_generative_canvas
                    b = compose_generative_canvas(sent, context=b.get("title"))
                    beats[bi] = b
                    cur_kind = "generative_canvas"

            # منع تكرار نفس الرقم في مشهد واحد عبر stat_ring_v2 و stat
            if cur_kind in ("stat", "stat_ring_v2"):
                num_key = re.sub(r"[^\d.]", "", str(b.get("number") or ""))
                if num_key and num_key in seen_stat_numbers:
                    from .generative_visuals import compose_generative_canvas
                    b = compose_generative_canvas(sent, context=b.get("title"))
                    beats[bi] = b
                    cur_kind = "generative_canvas"
                elif num_key:
                    seen_stat_numbers.add(num_key)

            # منع تكرار نفس خريطة المدينة أو نفس الصورة للمدينة داخل المشهد الواحد (تثبيت المشهد ومنع الوميض والتشتت)
            if cur_kind == "map":
                curr_city = ((b.get("points") or [{}])[0].get("name") or "").strip()
                if curr_city and curr_city in seen_map_cities:
                    from .generative_visuals import compose_generative_canvas
                    b = compose_generative_canvas(sent, context=b.get("title") or curr_city)
                    beats[bi] = b
                    cur_kind = "generative_canvas"
                elif curr_city:
                    seen_map_cities.add(curr_city)

            # منع تكرار نفس النوع مرتين متتاليتين (مع استثناء الخرائط التي تعرض مدناً أو نقاطاً جغرافية مختلفة)
            is_diff_map = False
            if cur_kind == "map" and prev_kind == "map":
                curr_pt = (b.get("points") or [{}])[0].get("name")
                prev_pt = (prev_beat.get("points") or [{}])[0].get("name") if prev_beat else None
                if curr_pt and prev_pt and curr_pt != prev_pt:
                    is_diff_map = True

            is_repeat = (
                cur_kind not in ("custom_scene", "generative_canvas")
                and ((cur_kind == prev_kind and not is_diff_map)
                     or (cur_kind in ("stat", "stat_ring_v2") and prev_kind in ("stat", "stat_ring_v2")))
            )
            if is_repeat:
                if cur_kind == "map":
                    pts = b.get("points") or []
                    pt_name = pts[0].get("name", "") if pts else ""
                    cou = (b.get("countries") or [""])[0]
                    cou_en = ISO3_TO_COUNTRY_EN.get(cou.upper(), cou)
                    q = f"{pt_name} {cou_en} landmark historical architecture".strip() if pt_name else f"{cou_en} historical architecture".strip()
                    if not q:
                        q = "historical monument architecture"
                    b = {
                        "kind": "photo",
                        "query": q,
                        "text": _words(sent or pt_name, 5),
                        "camera": "parallax",
                        "must_show": pt_name or "historical building",
                        "avoid": "watermark text collage modern cars",
                        "alt_queries": [f"{pt_name} landmark", f"{cou_en} historical place"]
                    }
                    beats[bi] = b
                    cur_kind = "photo"
                elif cur_kind in ("photo", "stat", "stat_ring_v2", "generative_canvas"):
                    photo_b = detect_photo_beat(sent) if prev_kind != "photo" else None
                    if photo_b and cur_kind != "photo":
                        beats[bi] = photo_b
                        cur_kind = "photo"
                    elif cur_kind == "generative_canvas":
                        nums = re.findall(r"\d+[\d,.]*", sent)
                        if nums and prev_kind not in ("stat", "stat_ring_v2"):
                            b = {"kind": "stat_ring_v2", "title": "", "number": nums[0], "label": _words(sent, 6), "camera": "zoom-in"}
                            beats[bi] = b
                            cur_kind = "stat_ring_v2"
                    else:
                        from .generative_visuals import compose_generative_canvas
                        b = compose_generative_canvas(sent, context=b.get("title") or target.get("on_screen"))
                        beats[bi] = b
                        cur_kind = "generative_canvas"
                elif cur_kind == "bigtext":
                    photo_b = detect_photo_beat(sent) if prev_kind != "photo" else None
                    if photo_b:
                        beats[bi] = photo_b
                        cur_kind = "photo"
                    else:
                        nums = re.findall(r"\d+[\d,.]*", sent)
                        if nums:
                            b = {"kind": "stat", "title": "", "number": nums[0], "label": _words(sent, 6), "layout": "ring", "camera": "zoom-in"}
                            beats[bi] = b
                            cur_kind = "stat"
                        else:
                            from .generative_visuals import compose_generative_canvas
                            b = compose_generative_canvas(sent, context=b.get("title"))
                            beats[bi] = b
                            cur_kind = "generative_canvas"

            # ضمان مشهد بطل للـ hook (أول جملة): ممنوع شاشة سوداء فارغة بنص مجرد
            if bi == 0 and target == targets[0] and cur_kind == "bigtext":
                photo_b = detect_photo_beat(sent)
                if photo_b:
                    beats[bi] = photo_b
                    cur_kind = "photo"
                else:
                    from .generative_visuals import compose_generative_canvas
                    b = compose_generative_canvas(sent, context=s.get("title") or b.get("title"))
                    beats[bi] = b
                    cur_kind = "generative_canvas"

            # منع إفراط bigtext في غير الـ hook
            if cur_kind == "bigtext" and (bi > 0 or target != targets[0]):
                photo_b = detect_photo_beat(sent) if prev_kind != "photo" else None
                if photo_b:
                    beats[bi] = photo_b
                    cur_kind = "photo"
                else:
                    nums = re.findall(r"\d+[\d,.]*", sent)
                    if nums:
                        b = {"kind": "stat", "title": "", "number": nums[0], "label": _words(sent, 6), "layout": "ring", "camera": "zoom-in"}
                        beats[bi] = b
                        cur_kind = "stat"
                    else:
                        from .generative_visuals import compose_generative_canvas
                        b = compose_generative_canvas(sent, context=b.get("title"))
                        beats[bi] = b
                        cur_kind = "generative_canvas"

            prev_kind = cur_kind
            prev_beat = b
            # تنويع حركة الكاميرا
            cur_cam = b.get("camera")
            if not cur_cam or cur_cam == prev_cam or cur_cam not in CAMERAS:
                cur_cam = cam_choices[cam_counter % len(cam_choices)]
                cam_counter += 1
                b["camera"] = cur_cam
            prev_cam = cur_cam
            # تنويع تخطيطات stat و bigtext
            if cur_kind == "stat":
                cur_lay = b.get("layout")
                if not cur_lay or cur_lay in used_stat_layouts:
                    avail = [x for x in stat_choices if x not in used_stat_layouts]
                    if not avail:
                        used_stat_layouts.clear()
                        avail = stat_choices
                    cur_lay = avail[0]
                    b["layout"] = cur_lay
                used_stat_layouts.add(cur_lay)
            elif cur_kind == "bigtext":
                cur_lay = b.get("layout", "center")
                if cur_lay in used_bigtext_layouts:
                    avail = [x for x in bigtext_choices if x not in used_bigtext_layouts]
                    if not avail:
                        used_bigtext_layouts.clear()
                        avail = bigtext_choices
                    cur_lay = avail[0]
                    b["layout"] = cur_lay
                used_bigtext_layouts.add(cur_lay)
    try:
        from . import visual_tools
        from .scriptspec import PART_IDS, PARTS_BY_ID
        from .storyteller import (
            _extract_all_cities,
            _extract_countries_from_text,
            design_scene_specification,
            evaluate_and_improve_scene,
            generate_dynamic_tsx_file,
        )

        transitions = visual_tools.pick_transitions(len(PART_IDS), seed=42)
        used_palettes: set = set()
        used_environments: set = set()
        used_approaches: set = set()
        used_cameras: set = set()
        prev_signatures: List[str] = []
        dynamic_tsx_beats: List[Dict[str, Any]] = []
        global_beat_idx = 0

        # استخراج السياق العام للفيديو بالكامل (العنوان + الحقائق الموثقة + الدول والمدن الرئيسية)
        full_video_title = str(s.get("title") or "").strip()
        facts_list: List[str] = []
        for f_item in (s.get("facts") or []):
            if isinstance(f_item, dict) and f_item.get("claim"):
                facts_list.append(str(f_item["claim"]).strip())
            elif isinstance(f_item, str) and f_item.strip():
                facts_list.append(f_item.strip())
        if isinstance(s.get("_facts_data"), dict) and s["_facts_data"].get("facts"):
            raw_facts_str = str(s["_facts_data"]["facts"]).strip()
            for line in raw_facts_str.splitlines():
                cl = line.strip("•-* \t")
                if len(cl) > 12 and cl not in facts_list:
                    facts_list.append(cl)
                if len(facts_list) >= 8:
                    break
        facts_summary = " | ".join(facts_list[:6])

        all_script_text_parts = [full_video_title]
        video_countries: List[str] = []
        video_cities: List[Dict[str, Any]] = []
        seen_vc_coords = set()
        for pid in PART_IDS:
            sc_dict = s.get(pid)
            if isinstance(sc_dict, dict):
                all_script_text_parts.append(str(sc_dict.get("on_screen") or ""))
                all_script_text_parts.append(str(sc_dict.get("narration") or ""))
                vis_d = sc_dict.get("visual") if isinstance(sc_dict.get("visual"), dict) else {}
                for c_iso in (vis_d.get("countries") or vis_d.get("highlight") or []):
                    c_up = str(c_iso).upper().strip()
                    if c_up and c_up not in video_countries:
                        video_countries.append(c_up)
                for pt in (vis_d.get("points") or []):
                    if isinstance(pt, dict) and "lat" in pt and "lon" in pt:
                        ck = (round(float(pt["lat"]), 1), round(float(pt["lon"]), 1))
                        if ck not in seen_vc_coords:
                            seen_vc_coords.add(ck)
                            video_cities.append({
                                "name": str(pt.get("name") or ""),
                                "lat": float(pt["lat"]),
                                "lon": float(pt["lon"]),
                            })
        full_script_text = " ".join(all_script_text_parts)
        for c_iso in _extract_countries_from_text(full_script_text):
            if c_iso not in video_countries:
                video_countries.append(c_iso)
        for c_obj in _extract_all_cities(full_script_text):
            ck = (round(float(c_obj["lat"]), 1), round(float(c_obj["lon"]), 1))
            if ck not in seen_vc_coords:
                seen_vc_coords.add(ck)
                video_cities.append({
                    "name": c_obj["name"],
                    "lat": float(c_obj["lat"]),
                    "lon": float(c_obj["lon"]),
                })
            if c_obj.get("iso") and c_obj["iso"] not in video_countries:
                video_countries.append(c_obj["iso"])

        for idx, pid in enumerate(PART_IDS):
            if pid in s and isinstance(s[pid], dict):
                sc_role = PARTS_BY_ID[pid]["role"]
                sc_obj = {**s[pid], "id": pid, "role": sc_role}
                s[pid]["visuals"] = visual_tools.enrich_scene_visuals(sc_obj, scene_index=idx, preferred_icon_set="lucide")
                s[pid]["transition"] = transitions[idx]

                prev_narr = s.get(PART_IDS[idx - 1], {}).get("narration", "") if idx > 0 else ""
                next_narr = s.get(PART_IDS[idx + 1], {}).get("narration", "") if idx + 1 < len(PART_IDS) else ""
                full_scene_narr = s[pid].get("narration", "")
                sc_beats = s[pid].get("beats") or []

                # دمج مقاطع المشهد الواحد في مقطع بصري متكامل واحد يغطي الجملة كاملة (8 مشاهد = 8 تصاميم متكاملة)
                if len(sc_beats) > 1:
                    primary_beat = dict(sc_beats[0])
                    concepts = [str(b.get("concept") or "").strip() for b in sc_beats if isinstance(b, dict) and b.get("concept")]
                    if concepts:
                        primary_beat["concept"] = " — ".join(dict.fromkeys(c for c in concepts if c))
                    for b_other in sc_beats[1:]:
                        if isinstance(b_other, dict) and b_other.get("kind") == "map" and primary_beat.get("kind") != "map":
                            for mk in ("countries", "highlight", "points"):
                                if b_other.get(mk) and not primary_beat.get(mk):
                                    primary_beat[mk] = b_other[mk]
                    sc_beats = [primary_beat]
                    s[pid]["beats"] = sc_beats

                for b_idx, beat_item in enumerate(sc_beats):
                    if not isinstance(beat_item, dict):
                        continue
                    sent_txt = full_scene_narr
                    was_fallback = beat_item.get("_fallback")
                    designed = design_scene_specification(
                        scene_id=f"{pid}_{b_idx}",
                        role=sc_role,
                        narration=sent_txt,
                        on_screen=beat_item.get("title") or s[pid].get("on_screen", ""),
                        scene_index=global_beat_idx,
                        total_scenes=len(PART_IDS),
                        prev_narration=prev_narr,
                        next_narration=next_narr,
                        video_title=full_video_title,
                        used_palettes=used_palettes,
                        used_environments=used_environments,
                        used_approaches=used_approaches,
                        used_cameras=used_cameras,
                    )
                    if beat_item.get("kind") in ("generative_canvas", "custom_scene"):
                        improved, _ = evaluate_and_improve_scene(designed, sent_txt, global_beat_idx, prev_signatures)
                        used_palettes.add(improved.get("bg_mood") or improved.get("accent"))
                        used_environments.add(improved.get("environment"))
                        if was_fallback:
                            improved["_fallback"] = True
                        if beat_item.get("concept"):
                            improved["concept"] = beat_item["concept"]
                        for gk in ("countries", "highlight", "points"):
                            if beat_item.get(gk):
                                improved[gk] = beat_item[gk]
                        improved["tsx_id"] = f"DynamicScene_{pid}_{b_idx}_{global_beat_idx}"
                        improved["narration"] = sent_txt
                        improved["video_title"] = full_video_title
                        improved["facts_summary"] = facts_summary
                        improved["video_countries"] = video_countries[:3]
                        improved["video_cities"] = video_cities[:5]
                        sc_beats[b_idx] = improved
                        dynamic_tsx_beats.append(improved)
                    else:
                        beat_item["scene_spec"] = designed["scene_spec"]
                        beat_item["narration_cues"] = designed["narration_cues"]
                        if beat_item.get("kind") not in ("photo", "map", "map_pin"):
                            beat_item["tsx_id"] = f"DynamicScene_{pid}_{b_idx}_{global_beat_idx}"
                            beat_item["narration"] = sent_txt
                            beat_item["video_title"] = full_video_title
                            beat_item["facts_summary"] = facts_summary
                            beat_item["video_countries"] = video_countries[:3]
                            beat_item["video_cities"] = video_cities[:5]
                            beat_item["accent"] = designed.get("accent") or "#38bdf8"
                            beat_item["secondary_accent"] = designed.get("secondary_accent") or "#818cf8"
                            dynamic_tsx_beats.append(beat_item)
                        else:
                            beat_item.pop("tsx_id", None)
                    global_beat_idx += 1

        if dynamic_tsx_beats:
            generate_dynamic_tsx_file(dynamic_tsx_beats, use_llm=False)
    except Exception:
        pass
    s['body'] = [s.get('body1', {}), s.get('body2', {}), s.get('body3', {})]
    s['loop'] = s.get('cta', {})
    return s

def auto_beats(script, geo=None):

    """مقاطع آمنة بلا نموذج (من الـ visual الحالي)."""
    return apply_beats(script, {}, geo)
