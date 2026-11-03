"""المخرج البصري: لكل جملة منطوقة مشهد حركي (beat) يُرسم بالكود في Remotion."""

import copy

import json

import re

from pathlib import Path
from .icons import pick_icons_for_beat, get_icon_path

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

KINDS = ["icon_scene", "map_pin", "timeline_card", "stat_ring_v2", "elevation_profile", "line_chart", "pie_chart", "map", "stat", "bigtext", "bars", "timeline", "versus", "list", "icons", "canvas", "photo", "split", "ticker", "cardstack"]

COLORS = ["accent", "accent2", "text", "hl0", "hl1", "hl2", "hl3"]

ENTERS = ["rise", "drop", "pop", "left", "right", "fade"]

CAMERAS = ["push-in", "zoom-in", "zoom-out", "pan-left", "pan-right", "tilt-up", "tilt-down", "parallax", "handheld", "pan", "static"]

TERM = re.compile(r”[.!؟?؛:…،,-]+$”)

STRIP = “»«\”’)(“”’’”

# Arabic keyword → short icon name from ICONS list
_KW_ICONS = [
    ([“توسع”, “انتشار”, “خريطة”, “جغرافي”, “إقليم”, “حدود”, “ملاحة”, “بحار”], “globe”),
    ([“حرب”, “قتال”, “معركة”, “جيش”, “عسكر”, “انتصار”, “هزيمة”, “غزو”, “سلاح”], “shield”),
    ([“ملك”, “إمبراطور”, “حاكم”, “سلطة”, “حكم”, “سياسة”, “قرار”, “أمير”, “خليفة”], “crown”),
    ([“اقتصاد”, “مال”, “ثروة”, “تجارة”, “خزينة”, “فقر”, “غنى”, “ذهب”, “نقود”], “coin”),
    ([“علم”, “اكتشاف”, “بحث”, “تقنية”, “تطور”, “ابتكار”, “فيزياء”, “كيمياء”], “atom”),
    ([“مدينة”, “بناء”, “معمار”, “حصن”, “برج”, “أثر”, “معبد”, “قصر”], “building”),
    ([“وقت”, “زمن”, “سنة”, “قرن”, “عصر”, “مرحلة”, “فترة”, “تاريخ”, “عهد”], “clock”),
    ([“شعب”, “مجتمع”, “ناس”, “سكان”, “جماهير”, “أمة”, “قبيلة”, “جماعة”], “people”),
    ([“كتاب”, “علم”, “معرفة”, “ثقافة”, “فكر”, “أدب”, “فلسفة”, “كتابة”], “book”),
    ([“دين”, “عبادة”, “روح”, “إيمان”, “مقدس”, “كنيسة”, “مسجد”, “معبد”], “star”),
    ([“طبيعة”, “بيئة”, “نهر”, “جبل”, “بحر”, “غابة”, “صحراء”, “أرض”], “mountain”),
    ([“تراجع”, “انهيار”, “سقوط”, “أزمة”, “انهار”, “فشل”, “خسارة”, “ضعف”], “arrow-down”),
    ([“نمو”, “صعود”, “ارتفاع”, “نجاح”, “تقدم”, “ازدهار”, “توسع”, “قوة”], “arrow-up”),
    ([“عالم”, “دولة”, “أمم”, “دبلوماسية”, “سفير”, “معاهدة”, “تحالف”], “globe”),
    ([“نار”, “حرق”, “دمار”, “هجوم”, “قصف”, “انفجار”], “fire”),
    ([“شريعة”, “قانون”, “عدل”, “قضاء”, “ميزان”, “حقوق”, “دستور”], “scale”),
    ([“تكنولوجيا”, “ثورة”, “صناعة”, “طاقة”, “برق”, “كهرباء”], “bolt”),
    ([“قلب”, “حب”, “شعور”, “وجدان”, “إنسانية”, “رحمة”], “heart”),
    ([“مفتاح”, “سر”, “اكتشاف”, “حل”, “لغز”, “باب”, “فتح”], “key”),
    ([“مخ”, “فكر”, “ذكاء”, “عقل”, “خطط”, “استراتيجية”], “brain”),
]

def _pick_icon_for_sentence(sent: str) -> str:
    “””Pick a contextually appropriate short icon name based on Arabic sentence keywords.”””
    for keywords, icon in _KW_ICONS:
        if any(kw in sent for kw in keywords):
            return icon
    fallback = [“globe”, “crown”, “shield”, “clock”, “building”, “people”, “chart”, “star”, “key”, “fire”, “brain”, “scale”]
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

    return re.sub(r"\s+", " ", str(v if v is not None else "")).strip()[:n]

def _words(v, maxw):

    return " ".join(_s(v, 120).split()[:maxw])

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
    kind = b.get("kind") if b.get("kind") in KINDS else "bigtext"
    out = {"kind": kind, "title": _words(b.get("title"), 7)}
    fallback_text = _words(b.get("text") or b.get("title") or " ".join(sentence.split()[:4]), 6).strip(".!؟?،:؛ ")
    def bigtext():
        o = {"kind": "bigtext", "title": "", "text": fallback_text or "…"}
        if b.get("sub"):
            o["sub"] = _words(b.get("sub"), 8)
        if b.get("layout") in ("center", "stack", "diag", "left"):
            o["layout"] = b["layout"]
        return o
    if kind == "icon_scene":
        picked = pick_icons_for_beat(sentence, b.get("text", "") or b.get("title", ""), n=4)
        hero = b.get("hero_icon") or (picked[0] if picked else "icons/monument/monument.svg")
        o = {
            "kind": "icon_scene",
            "title": _words(b.get("title") or b.get("text") or fallback_text, 7),
            "hero_icon": hero,
            "center_label": _words(b.get("center_label") or b.get("label") or "المركز", 3),
        }
        if b.get("sub"):
            o["sub"] = _words(b.get("sub"), 8)
        badges = b.get("badges") or b.get("items")
        if badges and isinstance(badges, list):
            o["badges"] = [
                {
                    "icon": bg.get("icon") or (picked[i % len(picked)] if picked else "icons/history/pyramid.svg"),
                    "label": _words(bg.get("label") or bg.get("text"), 3),
                    "x": bg.get("x"),
                    "y": bg.get("y")
                }
                for i, bg in enumerate(badges[:4]) if isinstance(bg, dict)
            ]
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
        if not _s(b.get("height")):
            return bigtext()
        o = {
            "kind": "elevation_profile",
            "title": _words(b.get("title") or b.get("peak_name") or fallback_text, 6),
            "height": _s(b.get("height"), 16),
            "unit": _s(b.get("unit") or "م", 8),
            "sea_label": _s(b.get("sea_label") or "سطح البحر", 20),
        }
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
        o = {"kind": "photo", "title": out["title"], "query": q, "text": _words(b.get("text"), 6).strip(".!؟?،:؛ "),
             "cutout": b.get("cutout") is True}
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
                items.append({"label": _words(it.get("label"), 4), "value": float(it.get("value")),
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
        items = [{"icon": it.get("icon") if it.get("icon") in ICONS else "star", "label": _words(it.get("label"), 3)}
                 for it in (b.get("items") or [])[:4] if isinstance(it, dict)]
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

def photo_to_text(b):

    """صورة تعذّر إيجادها ← icon_scene بأيقونات مرتبطة بالنص بدلاً من بطاقة نصية مجردة."""
    text = b.get("text") or b.get("title") or b.get("query") or "…"
    picked = pick_icons_for_beat(text, query=b.get("query", ""), n=3)
    fallback_icon = "icons/history/monument.svg"
    return {
        "kind": "icon_scene",
        "title": " ".join(text.split()[:5]).strip(".!؟?،:؛ "),
        "sub": " ".join(text.split()[5:10]).strip(".!؟?،:؛ ") if len(text.split()) > 5 else "",
        "hero_icon": picked[0] if picked else fallback_icon,
        "center_label": b.get("title", "")[:12] or " ".join(text.split()[:3]),
        "badges": [
            {"icon": picked[1] if len(picked) > 1 else fallback_icon, "label": ""},
            {"icon": picked[2] if len(picked) > 2 else fallback_icon, "label": ""},
        ],
        "camera": b.get("camera", "push-in"),
    }

# ------------------------------------------------------------------ بدائل بلا نموذج

# خريطة ترجمات سريعة للمدن والمعالم العربية الشائعة لضمان أفضل نتائج صور

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
    if i == 0 and ty == "map":
        return {"kind": "map", "title": scene.get("on_screen", ""), "countries": cs,
                "highlight": v.get("highlight") or cs, "points": pts}
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
            items = [{"label": lbl.strip()[:20], "value": float(val)} for lbl, val in pct_labels[:5]]
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
    # إذا ارتبط المشهد بمعلم أو مدينة أو بلد -> صورة حقيقية مرخصة
    if pt_name or cou_iso:
        clean_pt = re.sub(r"\(.*?\)", "", pt_name).strip()
        q = CITY_EN.get(pt_name) or CITY_EN.get(clean_pt)
        if not q:
            q = f"{clean_pt} {cou_iso} landmark historical".strip() if clean_pt else f"{cou_iso} landmark architecture"
        return {
            "kind": "photo",
            "query": q,
            "text": _words(sentence, 5),
            "camera": "parallax",
            "must_show": clean_pt or "historical building",
            "avoid": "watermark text collage",
            "alt_queries": [f"{clean_pt} landmark", f"{cou_iso} historical place"]
        }
    if i == 0 and ty == "stat":
        return {"kind": "stat", "title": scene.get("on_screen", ""), "number": v.get("number", ""), "label": v.get("label", "")}
    if i == 0 and ty == "text":
        return {"kind": "bigtext", "title": "", "text": v.get("text") or scene.get("on_screen", "")}
    picked = pick_icons_for_beat(sentence, n=3)
    return {
        "kind": "icon_scene",
        "title": " ".join(sentence.split()[:4]).strip(".!؟?،:؛ "),
        "sub": " ".join(sentence.split()[4:10]).strip(".!؟?،:؛ ") if len(sentence.split()) > 4 else "",
        "hero_icon": picked[0] if picked else "icons/monument/monument.svg",
        "center_label": "محور الحدث",
        "camera": "push-in",
    }

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
- إذا كان النص وحده يوصل المعنى بوضوح → icon_scene أو bigtext
- إذا كان التصور يجعل الفهم أسرع أو أعمق → اختر التصور المناسب

**الخطوة ٣: خريطة الاختيار الذكي**
| نوع المعلومة | النوع الأمثل |
|---|---|
| رقم واحد + أيقونة | stat_ring_v2 |
| عدة أرقام مقارنة | bars |
| سلسلة زمنية ≥3 نقاط (سنة+قيمة) | line_chart |
| توزيع نسبي (نسب مئوية) | pie_chart |
| مقارنة طرفين واضحة | versus |
| تسلسل زمني بمحطات | timeline_card |
| مكان/خريطة | map |
| ارتفاع جبل/بناية | elevation_profile |
| خطوات/عملية | list أو cardstack |
| شيء مرئي حقيقي | photo |
| رمز مفاهيمي/استعارة | icon_scene |
| علاقات/أسهم/بنية | canvas |
| عبارة قوية مجردة | bigtext |

**الخطوة ٤: تحقق صحة البيانات**
- لا تخترع أرقاماً أو نسباً لم ترد في الجملة أو في facts
- إذا لم تكن البيانات صريحة → استخدم نوعاً لا يتطلب أرقاماً

**خلاصة**: اختر النوع الذي يجعل المعلومة أوضح وأسرع فهماً، لا الأكثر بصرياً.

---

ستستلم المشاهد وجمل كل مشهد، وتعيد لكل جملة مقطعاً (beat) واحداً بالترتيب، وبعدد الجمل بالضبط.

حقل camera (اختياري، لأي نوع مقطع):

- "push-in": تكبير تدريجي 100%→107% — للتأكيد والـ hook.

- "pan": انزلاق أفقي — للقوائم والتسلسل.

- "parallax": طبقات بسرعات مختلفة — للصور والخرائط.

- "static": بلا حركة كاميرا (افتراضي).

أضفه عندما يخدم حركة الكاميرا معنى الجملة. مثال: {"kind":"stat","number":"3650","camera":"push-in"}

أنواع المقاطع (kind) وحقولها:

- "icon_scene": تكوين سينمائي ثلاثي الأبعاد مستوحى من الطراز الذهبي (أيقونة بطل كبيرة، نصوص عربية عريضة متوهجة، 2-4 أيقونات فرعية طافية حولها مع أسهم رابطة متحركة، وشرارات نارية). استعمله كمشهد إيضاحي متكامل غني بالرموز بدلاً من البطاقات المسطحة:
  {"kind":"icon_scene","title":"لماذا تغيرت عاصمة مصر؟","hero_icon":"icons/building/mosque.svg","center_label":"القاهرة","badges":[{"icon":"icons/history/pyramid.svg","label":"منف"},{"icon":"icons/monument/lighthouse.svg","label":"الإسكندرية"}],"camera":"push-in"}

- "map_pin": خريطة إقليمية مع دبابيس وأسماء مدن تسقط بالحركة النابضة وأسهم متصلة:
  {"kind":"map_pin","title":"مسار انتقال العواصم","region":"egypt","points":[{"name":"القاهرة","x":540,"y":780},{"name":"الإسكندرية","x":420,"y":560}]}

- "timeline_card": خط زمني عربي أفقي/عمودي مرسوم بانسيابية متحركة مع بطاقات محطات تاريخية وأيقونات:
  {"kind":"timeline_card","title":"تطور العواصم عبر الزمن","items":[{"year":"٦٤١ م","label":"تأسيس الفسطاط","icon":"icons/history/castle.svg"},{"year":"٩٦٩ م","label":"بناء القاهرة","icon":"icons/building/mosque.svg"}]}

- "stat_ring_v2": حلقة إحصائية محسّنة ثلاثية الأبعاد تحتوي أيقونة بطل في مركزها والرقم يتصاعد بتوهج ذهبي:
  {"kind":"stat_ring_v2","number":"1,000","label":"عام من التاريخ","icon":"icons/time/hourglass.svg"}

- "elevation_profile": تصور بصري متحرك لارتفاع جبل أو قمة أو بناية فوق سطح البحر — يرسم صورة جبل SVG تنكشف من الأسفل، مع خط أفقي يمثل سطح البحر، ومؤشر ارتفاع متحرك يتصاعد حتى القمة، وعداد الارتفاع يتصاعد رقمياً. استخدمه دائماً عند ذكر ارتفاع جبل أو بناية أو قمة بالمتر:
  {"kind":"elevation_profile","title":"جبل إيفرست","height":"8,849","unit":"م","sea_label":"سطح البحر","camera":"push-in"}

- "line_chart": رسم بياني خطي متحرك للبيانات الزمنية أو الاتجاهات (≥3 نقاط). استخدمه عند وجود سلسلة قيم عبر سنوات أو فترات متعاقبة (نمو السكان، ارتفاع درجات الحرارة، تطور الناتج المحلي، إلخ):
  {"kind":"line_chart","title":"نمو عدد السكان","points":[{"label":"1800","value":1.0},{"label":"1900","value":1.6},{"label":"2000","value":6.1},{"label":"2024","value":8.1}],"y_label":"مليار","camera":"push-in"}

- "pie_chart": مخطط دائري (donut) للبيانات النسبية التي تجمع 100% (أو تقارب ذلك). استخدمه عند وجود توزيع نسبي (حصص سوقية، تركيبة ميزانية، توزيع جغرافي، إلخ). القيم كنسب مئوية:
  {"kind":"pie_chart","title":"مصادر الطاقة العالمية","items":[{"label":"النفط","value":33},{"label":"الغاز","value":24},{"label":"الفحم","value":27},{"label":"متجددة","value":16}],"camera":"zoom-in"}

فئات الأيقونات المتاحة للاختيار:
[history, monument, map, person, science, number, arrow, fire, star, building, chart, time, world, book, sword, crown, coin, ship, tree]
فضل دائماً استخدام icon_scene أو map_pin أو stat_ring_v2 أو timeline_card على النصوص المجردة (bigtext).


- "map": للجمل التي تذكر مكاناً. {"kind":"map","title":"...","countries":["BOL"],"highlight":["BOL"],"points":[{"name":"سوكري","lat":-19.02,"lon":-65.26}]} الدول برموز ISO3 كبيرة، والإحداثيات حقيقية.

- "stat": رقم واحد يُعدّ تصاعدياً. {"kind":"stat","title":"...","number":"3,650","label":"متراً فوق سطح البحر"}

- "bigtext": عبارة كبيرة (≤6 كلمات). {"kind":"bigtext","text":"...","sub":"سطر صغير اختياري","layout":"center|stack|diag|left"}

- "bars": مقارنة أرقام حقيقية وردت في الجملة. {"kind":"bars","title":"...","items":[{"label":"...","value":12,"display":"12%"}]} (2 إلى 6)

- "timeline": تسلسل تواريخ. {"kind":"timeline","title":"...","items":[{"year":"1899","label":"..."}]} (2 إلى 5)

- "versus": مقارنة طرفين. {"kind":"versus","title":"...","left":{"title":"...","value":"..","sub":"..","icon":"scale"},"right":{...}} (الطرف الأول يظهر يميناً)

- "list": نقاط قصيرة. {"kind":"list","title":"...","items":[{"text":"...","icon":"check"}]} (2 إلى 5)

- "icons": أيقونات مع تسميات. {"kind":"icons","title":"...","items":[{"icon":"building","label":"..."}]} (1 إلى 4)

- "canvas": مشهد حر ترسمه أنت بعناصر مرتبة بالإحداثيات (لوحة 1080×1920؛ المنطقة الآمنة y من 450 إلى 1300). العناصر:

  {"type":"text","text":"..","x":540,"y":800,"size":90,"color":"accent","enter":"pop","delay":0.2,"loop":"float"}
  {"type":"icon","name":"rocket","x":540,"y":700,"size":220,"color":"accent2","enter":"rise","delay":0}
  {"type":"shape","shape":"circle|rect|ring|tri|star","x":..,"y":..,"size":160,"w":..,"h":..,"color":"hl1","enter":"pop"}
  {"type":"arrow","x":800,"y":900,"x2":300,"y2":900,"color":"text","stroke":12,"delay":0.5}   {"type":"line", ...نفس الحقول}
  الألوان: accent, accent2, text, hl0..hl3. enter: rise, drop, pop, left, right, fade. loop اختياري: float, pulse, spin. delay بالثواني (0 إلى 3) لتوقيت ظهور العنصر أثناء نطق الجملة.

الأيقونات المتاحة فقط: """ + ", ".join(ICONS) + """

- "split": مقارنة طرفين بلوحتين عموديتين. {"kind":"split","title":"...","left":{"title":"...","icon":"building","value":"2.4M","sub":"سطر فرعي"},"right":{"title":"...","icon":"water","value":"8.9M"}}

- "ticker": شريط أخبار متحرك. {"kind":"ticker","title":"...","items":[{"text":"حقيقة قصيرة","icon":"star"}]} (3 إلى 8 عناصر)

- "cardstack": بطاقات مكدّسة تظهر تباعاً. {"kind":"cardstack","title":"...","items":[{"text":"نقطة قصيرة","icon":"check","value":"95%"}]} (2 إلى 4 بطاقات)

قواعد:

- كل مقطع يرسم معنى جملته هي، لا الفيديو عموماً. استعمل canvas عندما تصف الجملة علاقة أو عملية أو فكرة تحتاج رسماً خاصاً (أسهم بين مفاهيم، عناصر متحركة...).

- استعمل photo كلما ذكرت الجملة شيئاً حقيقياً قابلاً للتصوير (معلم، أثر، شخص، مكان، أداة، وثيقة).

- تنويع صارم: لا مقطعان متتاليان من نفس النوع أبداً. ممنوع تكرار نفس تخطيط الأرقام stat (ring أو bar أو plain أو stack) مرتين في الفيديو؛ وممنوع تكرار تخطيط bigtext (center|stack|diag|left) مرتين في الفيديو.

- لا تخترع أرقاماً أو حقائق: كل رقم أو تاريخ أو اسم يجب أن يرد صراحة في السرد أو في facts الموثقة بمصادرها؛ يحظر استخدام أو اختراع أي حقيقة لم يتم التحقق منها وتوثيقها بمصدر.

- title اختياري: عنوان قصير (≤4 كلمات) يظهر أعلى الشاشة. النصوص عربية وموجزة جداً.

- لا تخرج عن حدود الحقول. أعد JSON فقط:

{"scenes":[{"id":"hook","beats":[{...}]},{"id":"lead","beats":[{...}]},{"id":"body1","beats":[{...}]},{"id":"open_loop1","beats":[{...}]},{"id":"body2","beats":[{...}]},{"id":"open_loop2","beats":[{...}]},{"id":"body3","beats":[{...}]},{"id":"cta","beats":[{...}]}]}"""

PHOTO_RULES = """

صور حقيقية (kind = "photo"): يبحث التطبيق عن صورة مرخّصة من الإنترنت (Wikimedia Commons وPexels) ويعرضها بمعالجة مونتاج احترافية.

{"kind":"photo","query":"english search words","text":"عبارة عربية قصيرة ≤6 كلمات","cutout":false,"number":"35,000","must_show":"the main subject","avoid":"watermark text collage","alt_queries":["broader query","even broader"],"camera":"parallax"}

- query بالإنجليزية فقط، 2-6 كلمات، محدد وقابل للتصوير مع اسم كيان + بلد + سنة إن وجدت. مثال: "Casa de la Libertad Sucre Bolivia 1825", "human brain anatomy", "Berlin Wall fall 1989".

- alt_queries: قائمة من استعلامين احتياطيين أوسع تدريجياً (من الأكثر تحديداً إلى الأعم). مثال: ["Sucre Bolivia colonial architecture", "Bolivia colonial city"].

- must_show: وصف قصير بالإنجليزية لما يجب أن تُظهره الصورة بالضبط. مثال: "white colonial building facade".

- avoid: ما يجب استبعاده. مثال: "watermark text collage portrait person".

- cutout=true فقط لجسم مفرد واضح (عضو، حيوان، أداة، مركبة، مبنى منفرد). للمشاهد والمدن والأحداث استعمل false.

- number اختياري: رقم من الجملة يُعدّ تصاعدياً تحت الصورة.

- camera: "parallax" للمناظر والمدن، "push-in" للوجوه والمباني، "static" للأحداث التاريخية.

- استعمل photo عندما تذكر الجملة شيئاً حقيقياً قابلاً للتصوير. لا تزد عن نصف المقاطع، ولا مقطعين متتاليين منه."""

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

def apply_beats(script, result, geo=None):

    """يدمج ناتج المخرج في السكربت بعد تنظيفه مع ضمان تنوع التخطيطات وعدم التكرار."""
    from .scriptspec import scenes_of
    s = copy.deepcopy(script)
    got = {x.get("id"): x.get("beats") for x in (result.get("scenes") or []) if isinstance(x, dict)}
    targets = []
    for sc in scenes_of(s):
        target = s.get(sc["id"])
        if not target:
            continue
        raw = got.get(sc["id"])
        sents = sentences(sc["narration"])
        raw = raw if isinstance(raw, list) else []
        target["beats"] = [normalize_beat(raw[i] if i < len(raw) else fallback_beat(sc, i, sents[i]), sents[i], geo)
                           for i in range(len(sents))]
        targets.append(target)
    # فحص ما بعدي: تنويع المقاطع، منع تكرار الخرائط أو أي نوع مرتين متتاليتين، وتنويع الكاميرا
    stat_choices = ["ring", "bar", "stack", "plain"]
    bigtext_choices = ["center", "stack", "diag", "left"]
    cam_choices = ["zoom-in", "pan-left", "zoom-out", "tilt-up", "parallax", "pan-right", "handheld"]
    used_stat_layouts = set()
    used_bigtext_layouts = set()
    prev_kind = None
    prev_cam = None
    cam_counter = 0
    for target in targets:
        sents = sentences(target.get("narration", ""))
        beats = target.get("beats", [])
        for bi, b in enumerate(beats):
            cur_kind = b.get("kind")
            sent = sents[bi] if bi < len(sents) else ""
            # منع تكرار نفس النوع مرتين متتاليتين
            if cur_kind == prev_kind:
                if cur_kind == "map":
                    pts = b.get("points") or []
                    pt_name = pts[0].get("name", "") if pts else ""
                    cou = (b.get("countries") or [""])[0]
                    q = f"{pt_name} {cou} landmark historical".strip() if pt_name else f"{cou} history architecture".strip()
                    if not q:
                        q = "historical monument architecture"
                    b = {
                        "kind": "photo",
                        "query": q,
                        "text": _words(sent or pt_name, 5),
                        "camera": "parallax",
                        "must_show": pt_name or "historical building",
                        "avoid": "watermark text collage",
                        "alt_queries": [f"{pt_name} city", f"{cou} landmark"]
                    }
                    beats[bi] = b
                    cur_kind = "photo"
                elif cur_kind == "photo":
                    b = {"kind": "bigtext", "title": "", "text": _words(sent, 5), "layout": "stack", "camera": "zoom-out"}
                    beats[bi] = b
                    cur_kind = "bigtext"
                elif cur_kind == "bigtext":
                    nums = re.findall(r"\d+[\d,.]*", sent)
                    if nums:
                        b = {"kind": "stat", "title": "", "number": nums[0], "label": _words(sent, 6), "layout": "ring", "camera": "zoom-in"}
                        beats[bi] = b
                        cur_kind = "stat"
                    else:
                        picked = pick_icons_for_beat(sent, sent, n=4)
                        hero = picked[0] if picked else "icons/history/monument.svg"
                        b = {
                            "kind": "icon_scene",
                            "title": _words(sent, 6),
                            "hero_icon": hero,
                            "center_label": _words(sent, 2),
                            "camera": "zoom-in",
                            "badges": [{"icon": picked[i], "label": "", "x": None, "y": None}
                                       for i in range(1, min(4, len(picked)))] if len(picked) > 1 else []
                        }
                        beats[bi] = b
                        cur_kind = "icon_scene"
            prev_kind = cur_kind
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
    s['body'] = [s.get('body1', {}), s.get('body2', {}), s.get('body3', {})]
    s['loop'] = s.get('cta', {})
    return s

def auto_beats(script, geo=None):

    """مقاطع آمنة بلا نموذج (من الـ visual الحالي)."""
    return apply_beats(script, {}, geo)
