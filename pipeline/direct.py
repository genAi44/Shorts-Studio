"""المخرج البصري: لكل جملة منطوقة مشهد حركي (beat) يُرسم بالكود في Remotion."""

import copy

import json

import re

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from .config import ROOT, record_fallback
from .icons import pick_icons_for_beat, get_icon_path, _has_whole_word

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
    "generative_canvas",
    "map_pin", "timeline_card", "stat_ring_v2", "elevation_profile",
    "versus_battle", "animated_route", "balance_meter", "deep_time_slider",
    "stack_pyramid", "macro_zoom_globe", "subsurface_mine", "dot_matrix_population",
    "money_waterfall", "frontline_clash",
    "line_chart", "pie_chart", "map", "stat", "bigtext", "bars", "timeline", "versus", "list", "icons", "canvas", "photo", "split", "ticker", "cardstack",
    "city_skyline", "architecture", "mystery_scene",
]

COLORS = ["accent", "accent2", "text", "hl0", "hl1", "hl2", "hl3"]

ENTERS = ["rise", "drop", "pop", "left", "right", "fade"]

CAMERAS = ["push-in", "zoom-in", "zoom-out", "pan-left", "pan-right", "tilt-up", "tilt-down", "parallax", "handheld", "pan", "static"]

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
        return o

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
    (r"مدينة|مدن|عاصمة|قصور|قصر|قلعة|حصن", "ancient historical fortress castle architecture", "historical architecture building", "modern cars watermark"),
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
    detected_city, city_data = detect_city_in_text(sentence)
    if not clean_pt and detected_city:
        clean_pt = detected_city
        cou_iso = cou_iso or city_data.get("iso", "")

    # تحويل رمز الدولة إلى اسم إنجليزي حقيقي لتفادي مطابقات خاطئة مثل MAR -> Casa del Mar
    country_en = ISO3_TO_COUNTRY_EN.get(cou_iso.upper(), "") if cou_iso else ""

    if clean_pt or country_en:
        city_info = WORLD_CITIES.get(clean_pt)
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
            "alt_queries": alts
        }
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

    # مشهد الحلقة المفتوحة (open_loop) مشهد توتر وتشويق (Tension Beat)
    if scene.get("role") == "open_loop":
        return {
            "kind": "canvas",
            "title": "ترقّب",
            "camera": "zoom-in",
            "elements": [
                {"type": "icon", "name": "question", "x": 540, "y": 680, "size": 240, "color": "accent", "enter": "pop", "loop": "pulse"},
                {"type": "text", "text": _words(sentence, 6), "x": 540, "y": 1000, "size": 74, "color": "text", "enter": "rise"}
            ]
        }
    ty = v.get("type")
    pts = v.get("points") or []
    cs = v.get("countries") or []
    cou_iso = cs[0] if cs else ""
    pt_name = pts[0].get("name", "") if pts else ""

    # فحص ما إذا كانت الجملة أو المشهد يذكر مدينة أو عاصمة معروفة (سلا، فاس، مراكش، إلخ)
    detected_city, city_data = detect_city_in_text(sentence)
    if not detected_city:
        detected_city, city_data = detect_city_in_text(scene.get("on_screen", ""))

    # إذا كانت الجملة تذكر مدينة أو عاصمة صراحة والمشهد ليس خاتمة أو ترقب، فالأولوية المطلقة لخريطة المدينة
    if detected_city and city_data and scene.get("role") not in ("open_loop", "cta", "loop"):
        return {
            "kind": "map",
            "title": scene.get("on_screen", "") or detected_city,
            "countries": [city_data["iso"]],
            "highlight": [city_data["iso"]],
            "points": [{"name": detected_city, "lat": city_data["lat"], "lon": city_data["lon"], "dot": True}],
            "camera": "zoom-in"
        }

    if i == 0 and ty == "map":
        map_pts = list(pts)
        if not map_pts and detected_city and city_data:
            map_pts = [{"name": detected_city, "lat": city_data["lat"], "lon": city_data["lon"], "dot": True}]
        return {"kind": "map", "title": scene.get("on_screen", ""), "countries": cs,
                "highlight": v.get("highlight") or cs, "points": map_pts}

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

    # إذا ورد ترتيب أو قائمة أو مراكز أولى (أغنى، أكبر، أفضل، المراكز)
    _RANK_KW = re.compile(r"أغنى|أكبر|أفضل|أعلى|أقوى|المراكز|ترتيب|قائمة|ranking|top", re.I)
    if _RANK_KW.search(sentence) and not (cou_iso or pt_name):
        nums = re.findall(r"\d[\d,.]*", sentence)
        return {
            "kind": "bars",
            "title": _words(sentence, 5),
            "items": [
                {"label": "المرتبة الأولى", "value": 100, "display": nums[0] if nums else "١"},
                {"label": "المرتبة الثانية", "value": 85, "display": nums[1] if len(nums) > 1 else "٢"},
                {"label": "المرتبة الثالثة", "value": 70, "display": nums[2] if len(nums) > 2 else "٣"},
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

    """مقاطع المشهد: من script (إن وُجدت ولها نفس عدد الجمل) وإلا بدائل آمنة."""
    sents = sentences(scene.get("narration", ""))
    raw = scene.get("beats") if isinstance(scene.get("beats"), list) else []
    out = []
    for i, s in enumerate(sents):
        b = raw[i] if i < len(raw) else fallback_beat(scene, i, s)
        out.append(normalize_beat(b, s, geo))
    return out

# ------------------------------------------------------------------ المخرج (DeepSeek)

DIRECTOR_SYSTEM = """أنت مخرج فني ومحلل بيانات لفيديوهات Shorts عربية بالموشن غرافيك. لكل جملة منطوقة ترسم مشهداً حركياً يوضّح معناها لحظة نطقها.

## إطار التفكير البصري (يجب تطبيقه على كل جملة قبل اختيار النوع)

**الخطوة ١: تحليل نوع المعلومة**
- رقم واحد صادم (إحصاء، ارتفاع، تاريخ)؟
- أرقام متعددة قابلة للمقارنة (نسب، كميات)؟
- سلسلة زمنية (أرقام عبر سنوات متعاقبة ≥3)؟
- توزيع نسبي (نسب مئوية تجمع ~100%)؟
- مقارنة طرفين (أكثر/أقل من، بينما، مقابل)؟
- تسلسل خطوات أو عملية؟
- مكان أو علاقة مكانية؟
- ارتفاع جغرافي/طبوغرافي؟
- مفهوم مجرد أو قصة؟

**الخطوة ٢: هل التصور يضيف فهماً حقيقياً؟**
- إذا كان النص وحده يوصل المعنى بوضوح → bigtext أو icons أو cardstack
- إذا كان التصور يجعل الفهم أسرع أو أعمق → اختر التصور المناسب

**الخطوة ٣: خريطة الاختيار الذكي**
| نوع المعلومة | النوع الأمثل |
|---|---|

| رسم حر/عملية/شبكة/تفاعل/قوة/فكرة ديناميكية | generative_canvas |
| صراع طرفين/مقارنة بطولية أو تنافسية | versus_battle |
| هرمية/طبقات/ترتيب تصاعدي أو تنازلي | stack_pyramid |
| ميزان/تأرجح قوى أو نسبتين متقابلتين | balance_meter |
| مسار تنقل/رحلة بين محطات أو مدن | animated_route |
| خط زمني/عصور ومحطات تاريخية | deep_time_slider أو timeline_card |
| ارتفاع جبل/قمة/عمق بحري بالمتر | elevation_profile |
| رقم واحد بطل متوهج | stat_ring_v2 |
| مقارنة أرقام أو كميات | bars |
| صورة حقيقية لمعلم أو شخص أو كائن | photo |
| خريطة إقليمية ودبابيس | map_pin أو map |
| رسم بياني لسلسلة زمنية متعاقبة | line_chart |
| رسم بياني لنسب مئوية | pie_chart |
| عبارة افتتاحية خاطفة قوية | bigtext (مرة واحدة فقط كحد أقصى) |
| مدينة / أفق حضري | city_skyline |
| مبنى تاريخي / معماري | architecture |
| سؤال / غموض / لغز | mystery_scene |

**الخطوة ٤: تحقق صحة البيانات**
- لا تخترع أرقاماً أو نسباً لم ترد في الجملة أو في facts
- إذا لم تكن البيانات صريحة → استخدم generative_canvas أو photo أو versus_battle أو stack_pyramid

**خلاصة**: اختر النوع البصري الحي الأغنى الذي يجعل المشاهد ينبهر بالرسم والحركة.

---

ستستلم المشاهد وجمل كل مشهد، وتعيد لكل جملة مقطعاً (beat) واحداً بالترتيب، وبعدد الجمل بالضبط.

حقل camera (اختياري، لأي نوع مقطع):
- "push-in": تكبير تدريجي 100%→107% — للتأكيد والـ hook.
- "pan": انزلاق أفقي — للقوائم والتسلسل.
- "parallax": طبقات بسرعات مختلفة — للصور والخرائط.
- "zoom-in", "zoom-out", "tilt-up", "tilt-down", "static".

أنواع المقاطع (kind) وحقولها:

- "map": للأماكن والعواصم والمدن والحدود الجغرافية. إلزامي كلما ذكرت الجملة مدينة أو عاصمة أو دولة أو توسعاً جغرافياً:
  {"kind":"map","title":"فاس: العاصمة الثانية","countries":["MAR"],"highlight":["MAR"],"points":[{"name":"فاس","lat":34.033,"lon":-5.0}],"camera":"zoom-in"}

- "generative_canvas": لوحة رسم حر إبداعية بالـ SVG والعناصر المتحركة. استخدمه بكثرة لتمثيل العمليات والتفاعلات والشبكات والأنظمة:
  {"kind":"generative_canvas","title":"شبكة التفاعل والتجارة","grid":"dots","elements":[{"type":"shape","shape":"circle","x":540,"y":850,"w":180,"h":180,"fill":"#f59e0b","motion":"pop"},{"type":"badge","text":"المركز الرئيسي","x":540,"y":850,"icon":"sparkles"},{"type":"badge","text":"الميناء","x":280,"y":650,"icon":"ship"},{"type":"connector","fromX":280,"fromY":650,"toX":540,"toY":850,"color":"#f59e0b","style":"dashed","animated":true}],"camera":"zoom-in"}
  العناصر المتاحة:
  - badge: {"type":"badge","text":"..","x":540,"y":800,"icon":"sparkles|star|shield|fire|coin|crown","color":"#.."}
  - shape: {"type":"shape","shape":"circle|rect|pill|ring","x":..,"y":..,"w":..,"h":..,"fill":"#..","motion":"pop|rise|drop"}
  - counter: {"type":"counter","value":100,"prefix":"","suffix":"%","label":"..","x":..,"y":..}
  - gauge: {"type":"gauge","value":75,"label":"..","x":..,"y":..}
  - connector: {"type":"connector","fromX":..,"fromY":..,"toX":..,"toY":..,"color":"#..","style":"solid|dashed","animated":true}
  توزيع العناصر: وزّع العناصر عمودياً على كامل الشاشة (y من 420 إلى 1500) ولا تكتلها في نطاق y ضيق. مثال توزيع: قمة (y=450)، وسط (y=850-950)، قاع (y=1350-1480).

- "versus_battle": صراع ومقارنة حماسية بين طرفين أو قوتين مع شارة VS:
  {"kind":"versus_battle","title":"صراع النفوذ","left":{"title":"الطرف الأول","subtitle":"وصف موجز أو رقم","badge":"أفضلية"},"right":{"title":"الطرف الثاني","subtitle":"وصف موجز أو رقم","badge":"تحدي"},"camera":"zoom-in"}

- "stack_pyramid": هرم أو طبقات متتالية من القمة للقاعدة:
  {"kind":"stack_pyramid","title":"الهرم الطبقي","tiers":[{"label":"القمة والقيادة","value":"5%"},{"label":"الطبقة الوسطى","value":"25%"},{"label":"القاعدة الشعبية","value":"70%"}],"camera":"tilt-up"}

- "balance_meter": ميزان متحرك يتأرجح بين وزنين أو قوتين:
  {"kind":"balance_meter","title":"ميزان القوى","leftLabel":"القوة الأولى","leftWeight":65,"rightLabel":"القوة الثانية","rightWeight":35,"unit":"%","camera":"push-in"}

- "animated_route": مسار رحلة أو انتقال بين محطات:
  {"kind":"animated_route","title":"مسار الحملة","stops":[{"name":"نقطة البداية"},{"name":"محطة العبور"},{"name":"المقر النهائي"}],"camera":"pan-left"}

- "deep_time_slider": خط زمني يمر عبر العصور والمحطات التاريخية:
  {"kind":"deep_time_slider","title":"المحطات التاريخية","eras":[{"name":"البداية","year":"١٥٠٠ م"},{"name":"الذروة","year":"١٧٥٠ م"},{"name":"الحاضر","year":"٢٠٢٤ م"}],"camera":"pan-left"}

- "map_pin": خريطة إقليمية مع دبابيس وأسماء مدن تسقط بالحركة النابضة:
  {"kind":"map_pin","title":"مسار انتقال العواصم","region":"egypt","points":[{"name":"القاهرة","x":540,"y":780},{"name":"الإسكندرية","x":420,"y":560}]}

- "timeline_card": خط زمني عربي مع بطاقات محطات تاريخية:
  {"kind":"timeline_card","title":"تطور العواصم عبر الزمن","items":[{"year":"٦٤١ م","label":"تأسيس الفسطاط","icon":"icons/history/castle.svg"},{"year":"٩٦٩ م","label":"بناء القاهرة","icon":"icons/building/mosque.svg"}]}

- "stat_ring_v2": حلقة إحصائية ثلاثية الأبعاد تحتوي أيقونة بطل في مركزها والرقم يتصاعد بتوهج ذهبي:
  {"kind":"stat_ring_v2","number":"1,000","label":"عام من التاريخ","icon":"icons/time/hourglass.svg","camera":"zoom-in"}

- "elevation_profile": تصور بصري متحرك لارتفاع جبل أو قمة أو بناية فوق سطح البحر:
  {"kind":"elevation_profile","title":"جبل إيفرست","height":"8,849","unit":"م","sea_label":"سطح البحر","camera":"push-in"}

- "bars": مقارنة أرقام حقيقية بأعمدة ملونة:
  {"kind":"bars","title":"مقارنة الأرقام","items":[{"label":"الطرف أ","value":85,"display":"85K"},{"label":"الطرف ب","value":42,"display":"42K"}],"camera":"push-in"}

- "line_chart": رسم بياني خطي متحرك للبيانات الزمنية (≥3 نقاط):
  {"kind":"line_chart","title":"نمو عدد السكان","points":[{"label":"1800","value":1.0},{"label":"1900","value":1.6},{"label":"2000","value":6.1}],"y_label":"مليار","camera":"push-in"}

- "pie_chart": مخطط دائري للبيانات النسبية التي تجمع 100%:
  {"kind":"pie_chart","title":"توزيع الحصص","items":[{"label":"النفط","value":40},{"label":"الغاز","value":35},{"label":"أخرى","value":25}],"camera":"zoom-in"}

- "photo": للجمل التي تذكر شخصاً، معلماً، أثراً، مدينة، أو كائناً حقيقياً قابلاً للتصوير:
  {"kind":"photo","query":"pyramids of giza cairo egypt","text":"أهرامات الجيزة الخالدة","camera":"parallax","must_show":"pyramids","avoid":"watermark text collage"}


قواعد صارمة:
- مدينة أو أفق حضري → city_skyline. مبنى تاريخي أو معماري → architecture. سؤال أو لغز → mystery_scene. استعمل photo فقط لما لا يمكن تمثيله بالرسوم المتجهة. لا تزد نسبة photo عن 15-25% من المقاطع.
- ممنوع بتاتاً استخدام نوع "icons" (الدوائر القديمة بنجوم مكررة ملغاة تماماً).
- الأعلام (visuals): إذا أضفت علماً في حقل visuals فيجب أن يكون علم الدولة التي يتحدث عنها هذا المقطع تحديداً. إذا تناول المقطع دولاً متعددة أو منطقة عامة (آسيا، أوروبا...) فلا تضع أي علم. لا تكرر نفس العلم في مقاطع متتالية لدول مختلفة.
- الأرقام في الصوت والصورة: عند استخدام stat_ring_v2 أو bars مع رقم دقيق، اكتب في السرد الصوتي (title/subtitle) صيغة تقريبية ("أكثر من 36 مليون") والرقم الدقيق يبقى فقط في حقل number للتصور البصري. لا تكرر الرقم الكامل في العنوان والسرد والشارة معاً.
- مشهد البداية (Hook - أول جملة): يجب أن يكون مشهداً سينمائياً بطلاً يخطف الأبصار فوراً (Hero Visual)! استخدم نوع "photo" مع استعلام إنجليزي فائق الدقة أو "generative_canvas" بتكوين فني غني. يُمنع منعاً باتاً عرض شاشة سوداء فارغة بنص فقط (bigtext مجرد).
- ممنوع تكرار "bigtext" نهائياً، ويُمنع استخدامه لأكثر من مرة واحدة فقط وبشرط وجود مغزى قوي! بقية المشاهد يجب أن تكون بصرية سينمائية (generative_canvas, photo, versus_battle, stack_pyramid, balance_meter, bars, stat_ring_v2).
- الصور الواقعية (photo): استخدمها بسخاء في 40% إلى 50% من المقاطع كلما ذكرت الجملة حضارة، معلماً، أثراً، معبداً، كارثة طبيعية، مدينة، أسلحة، نقوداً، أو حدثاً تاريخياً. اكتب دائماً query بالإنجليزية دقيقاً ومحدداً مع 2 alt_queries واضحة.
- أعطِ أولوية قصوى لـ "generative_canvas" عندما تصف الجملة عملية تفاعلية أو نظاماً أو شبكة أو حركة مفاهيمية.
- في versus_battle: إذا لم تكن هناك أرقام صريحة، لا تضع أرقاماً عشوائية أبداً، بل ركز على title و subtitle و badge لكلا الطرفين.
- في balance_meter: استخدم دائماً leftLabel و rightLabel و leftWeight و rightWeight.
- في stack_pyramid: استخدم دائماً مصفوفة tiers من القمة للقاعدة.
- تنويع صارم: لا مقطعان متتاليان من نفس النوع أبداً.
- ممنوع تكرار نمط map→stat_ring_v2→bars أكثر من مرة واحدة في الفيديو كله. كل منطقة جغرافية يجب أن تُعرض بأسلوب مختلف: versus_battle أو generative_canvas أو photo أو balance_meter أو stack_pyramid.
- مشهد CTA (نهاية الفيديو): يجب أن يحتوي على عنصر بصري قوي (generative_canvas بشبكة نجوم أو عناصر متحركة، أو photo مناسب)، وليس شاشة سوداء أو progress bar فارغة. أضف شارات نص تحفيزية واضحة.
- لا تخترع أرقاماً أو حقائق: كل رقم أو تاريخ أو اسم يجب أن يرد صراحة في السرد أو facts.
- أعد JSON فقط:
{"scenes":[{"id":"hook","beats":[{...}]},{"id":"lead","beats":[{...}]},{"id":"body1","beats":[{...}]},{"id":"open_loop1","beats":[{...}]},{"id":"body2","beats":[{...}]},{"id":"open_loop2","beats":[{...}]},{"id":"body3","beats":[{...}]},{"id":"cta","beats":[{...}]}]}"""

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

- استعمل photo فقط لما لا تستطيع city_skyline أو architecture أو mystery_scene أو icon_scene أو map تمثيله (وجه شخص حقيقي، حدث تاريخي لا يُختزل في رمز). لا تزد عن 15-25% من المقاطع، ولا مقطعين متتاليين منه."""

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
                    target["beats"][0] = map_cand
        targets.append(target)

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

            # منع تكرار نفس النوع مرتين متتاليتين (مع استثناء الخرائط التي تعرض مدناً أو نقاطاً جغرافية مختلفة)
            is_diff_map = False
            if cur_kind == "map" and prev_kind == "map":
                curr_pt = (b.get("points") or [{}])[0].get("name")
                prev_pt = (prev_beat.get("points") or [{}])[0].get("name") if prev_beat else None
                if curr_pt and prev_pt and curr_pt != prev_pt:
                    is_diff_map = True

            is_repeat = ((cur_kind == prev_kind and not is_diff_map) or
                         (cur_kind in ("stat", "stat_ring_v2") and prev_kind in ("stat", "stat_ring_v2")))
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
                elif cur_kind in ("photo", "stat", "stat_ring_v2", "icon_scene", "generative_canvas"):
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
        transitions = visual_tools.pick_transitions(len(PART_IDS), seed=42)
        for idx, pid in enumerate(PART_IDS):
            if pid in s and isinstance(s[pid], dict):
                sc_obj = {**s[pid], "id": pid, "role": PARTS_BY_ID[pid]["role"]}
                # إثراء المشهد بعنصر بصري تراكبي ذكي وموجز (علم الدولة، أيقونة معبرة، أو لوتي في الـ hook)
                s[pid]["visuals"] = visual_tools.enrich_scene_visuals(sc_obj, scene_index=idx, preferred_icon_set="lucide")
                s[pid]["transition"] = transitions[idx]
    except Exception:
        pass
    s['body'] = [s.get('body1', {}), s.get('body2', {}), s.get('body3', {})]
    s['loop'] = s.get('cta', {})
    return s

def auto_beats(script, geo=None):

    """مقاطع آمنة بلا نموذج (من الـ visual الحالي)."""
    return apply_beats(script, {}, geo)
