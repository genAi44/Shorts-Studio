"""Split from `pipeline/direct.py` (re-exported there); see that module."""
from . import areamap
from .geo import detect_city_in_text
from .icons import pick_icons_for_beat
import re
from .direct import ICONS, _SPEC_SCHEMA, _add_camera, _num, _s, _words  # noqa: E402


def _normalize_beat_area_map(b, bigtext, fallback_text, geo, kind, out, sentence):
    return areamap.beat_from_raw(b) or bigtext()


def _normalize_beat_map_pin(b, bigtext, fallback_text, geo, kind, out, sentence):
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


def _normalize_beat_timeline_card(b, bigtext, fallback_text, geo, kind, out, sentence):
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


def _normalize_beat_stat_ring_v2(b, bigtext, fallback_text, geo, kind, out, sentence):
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


def _normalize_beat_elevation_profile(b, bigtext, fallback_text, geo, kind, out, sentence):
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


def _normalize_beat_custom_scene(b, bigtext, fallback_text, geo, kind, out, sentence):
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


def _normalize_beat_cinematic_dramatic(b, bigtext, fallback_text, geo, kind, out, sentence):
    spec_in = dict(b.get("scene_spec")) if isinstance(b.get("scene_spec"), dict) else {}
    spec_in.setdefault("cinematic", kind)
    o = {"kind": kind, "title": _words(b.get("title") or fallback_text, 6), "scene_spec": spec_in}
    if b.get("subtitle") or b.get("sub"):
        o["subtitle"] = _words(b.get("subtitle") or b.get("sub"), 7)
    return _add_camera(o, b)


def _normalize_beat_generative_canvas(b, bigtext, fallback_text, geo, kind, out, sentence):
    try:
        from .generative_visuals import validate_generative_canvas_spec
        o = validate_generative_canvas_spec(b)
        return _add_camera(o, b)
    except Exception:
        return bigtext()


def _normalize_beat_versus_battle(b, bigtext, fallback_text, geo, kind, out, sentence):
    allowed_story_fields = set((_SPEC_SCHEMA.get("beats", {}).get(kind, {}).get("fields") or {}).keys()) | set(_SPEC_SCHEMA.get("common_fields", {}).keys())
    o = {k: v for k, v in b.items() if k in allowed_story_fields}
    o["kind"] = kind
    o["title"] = _words(b.get("title") or fallback_text, 6)
    return _add_camera(o, b)


def _normalize_beat_line_chart(b, bigtext, fallback_text, geo, kind, out, sentence):
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


def _normalize_beat_pie_chart(b, bigtext, fallback_text, geo, kind, out, sentence):
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


def _normalize_beat_bigtext(b, bigtext, fallback_text, geo, kind, out, sentence):
    return bigtext()


def _normalize_beat_photo(b, bigtext, fallback_text, geo, kind, out, sentence):
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


def _normalize_beat_map(b, bigtext, fallback_text, geo, kind, out, sentence):
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


def _normalize_beat_stat(b, bigtext, fallback_text, geo, kind, out, sentence):
    if not _s(b.get("number")):
        return bigtext()
    out.update({"number": _s(b.get("number"), 16), "label": _words(b.get("label"), 8)})
    if b.get("layout") in ("ring", "bar", "plain", "stack"):
        out["layout"] = b["layout"]
    return _add_camera(out, b)


def _normalize_beat_bars(b, bigtext, fallback_text, geo, kind, out, sentence):
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


def _normalize_beat_timeline(b, bigtext, fallback_text, geo, kind, out, sentence):
    items = [{"year": _s(it.get("year"), 12), "label": _words(it.get("label"), 6)} for it in (b.get("items") or [])[:5]
             if isinstance(it, dict) and _s(it.get("year"))]
    if len(items) < 2:
        return bigtext()
    out["items"] = items
    return _add_camera(out, b)


def _normalize_beat_versus(b, bigtext, fallback_text, geo, kind, out, sentence):
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


def _normalize_beat_list(b, bigtext, fallback_text, geo, kind, out, sentence):
    items = [{"text": _words(it.get("text") if isinstance(it, dict) else it, 6),
              **({"icon": it["icon"]} if isinstance(it, dict) and it.get("icon") in ICONS else {})}
             for it in (b.get("items") or [])[:5]]
    items = [i for i in items if i["text"]]
    if len(items) < 2:
        return bigtext()
    out["items"] = items
    return _add_camera(out, b)


def _normalize_beat_icons(b, bigtext, fallback_text, geo, kind, out, sentence):
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


def _normalize_beat_split(b, bigtext, fallback_text, geo, kind, out, sentence):
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


def _normalize_beat_ticker(b, bigtext, fallback_text, geo, kind, out, sentence):
    items = [{"text": _words(it.get("text") if isinstance(it, dict) else it, 7),
              **({"icon": it["icon"]} if isinstance(it, dict) and it.get("icon") in ICONS else {})}
             for it in (b.get("items") or [])[:8]]
    items = [i for i in items if i["text"]]
    if not items:
        return bigtext()
    out["items"] = items
    return _add_camera(out, b)


def _normalize_beat_cardstack(b, bigtext, fallback_text, geo, kind, out, sentence):
    items = [{"text": _words(it.get("text") if isinstance(it, dict) else it, 7),
              **({"icon": it["icon"]} if isinstance(it, dict) and it.get("icon") in ICONS else {}),
              **({"value": _s(it.get("value"), 10)} if isinstance(it, dict) and it.get("value") else {})}
             for it in (b.get("items") or [])[:4]]
    items = [i for i in items if i["text"]]
    if not items:
        return bigtext()
    out["items"] = items
    return _add_camera(out, b)


def _normalize_beat_authored(b, bigtext, fallback_text, geo, kind, out, sentence):
    if not b.get("scene_id"):
        return bigtext()
    return _add_camera({"kind": "authored", "scene_id": str(b["scene_id"]), "data": b.get("data") if isinstance(b.get("data"), dict) else {}}, b)


def _normalize_beat_year_counter(b, bigtext, fallback_text, geo, kind, out, sentence):
    y = _num(b.get("year"), -5000, 2100, None)
    if y is None:
        return bigtext()
    o = {"kind": "year_counter", "year": int(y), "title": _words(b.get("title"), 5), "label": _words(b.get("label") or fallback_text, 6),
         "era": _s(b.get("era") or "year", 12)}
    ty = _num(b.get("to_year"), -5000, 2100, None)
    if ty is not None:
        o["to_year"] = int(ty)
    return _add_camera(o, b)


def _normalize_beat_person_card(b, bigtext, fallback_text, geo, kind, out, sentence):
    nm = _words(b.get("name") or b.get("title"), 5)
    if not nm:
        return bigtext()
    o = {"kind": "person_card", "name": nm, "years": _s(b.get("years"), 16), "role": _words(b.get("role"), 6), "query": _s(b.get("query"), 60)}
    if b.get("img"):
        o["img"] = b["img"]
    return _add_camera(o, b)


def _normalize_beat_city_skyline(b, bigtext, fallback_text, geo, kind, out, sentence):
    o = {"kind": "city_skyline", "title": _words(b.get("title") or fallback_text, 5)}
    if b.get("subtitle") or b.get("sub"):
        o["subtitle"] = _words(b.get("subtitle") or b.get("sub"), 6)
    if isinstance(b.get("seed"), (int, float)):
        o["seed"] = int(b["seed"])
    return _add_camera(o, b)


def _normalize_beat_architecture(b, bigtext, fallback_text, geo, kind, out, sentence):
    o = {"kind": "architecture", "title": _words(b.get("title") or fallback_text, 5)}
    if b.get("subtitle") or b.get("sub"):
        o["subtitle"] = _words(b.get("subtitle") or b.get("sub"), 6)
    if b.get("era"):
        o["era"] = _words(b.get("era"), 5)
    if isinstance(b.get("seed"), (int, float)):
        o["seed"] = int(b["seed"])
    return _add_camera(o, b)


def _normalize_beat_mystery_scene(b, bigtext, fallback_text, geo, kind, out, sentence):
    q = b.get("question") or b.get("text") or fallback_text
    o = {"kind": "mystery_scene", "question": _words(q, 10)}
    if b.get("subtitle") or b.get("sub"):
        o["subtitle"] = _words(b.get("subtitle") or b.get("sub"), 6)
    if isinstance(b.get("variant"), int):
        o["variant"] = b["variant"] % 3
    if isinstance(b.get("seed"), (int, float)):
        o["seed"] = int(b["seed"])
    return _add_camera(o, b)


_NORMALIZE_KIND = {
    'area_map': _normalize_beat_area_map,
    'map_pin': _normalize_beat_map_pin,
    'timeline_card': _normalize_beat_timeline_card,
    'stat_ring_v2': _normalize_beat_stat_ring_v2,
    'elevation_profile': _normalize_beat_elevation_profile,
    'custom_scene': _normalize_beat_custom_scene,
    'cinematic_dramatic': _normalize_beat_cinematic_dramatic,
    'architectural_blueprint': _normalize_beat_cinematic_dramatic,
    'celestial_constellation': _normalize_beat_cinematic_dramatic,
    'kinetic_wave_field': _normalize_beat_cinematic_dramatic,
    'radial_light_cathedral': _normalize_beat_cinematic_dramatic,
    'topographic_contour': _normalize_beat_cinematic_dramatic,
    'generative_canvas': _normalize_beat_generative_canvas,
    'versus_battle': _normalize_beat_versus_battle,
    'animated_route': _normalize_beat_versus_battle,
    'balance_meter': _normalize_beat_versus_battle,
    'deep_time_slider': _normalize_beat_versus_battle,
    'stack_pyramid': _normalize_beat_versus_battle,
    'macro_zoom_globe': _normalize_beat_versus_battle,
    'subsurface_mine': _normalize_beat_versus_battle,
    'dot_matrix_population': _normalize_beat_versus_battle,
    'money_waterfall': _normalize_beat_versus_battle,
    'frontline_clash': _normalize_beat_versus_battle,
    'line_chart': _normalize_beat_line_chart,
    'pie_chart': _normalize_beat_pie_chart,
    'bigtext': _normalize_beat_bigtext,
    'photo': _normalize_beat_photo,
    'map': _normalize_beat_map,
    'stat': _normalize_beat_stat,
    'bars': _normalize_beat_bars,
    'timeline': _normalize_beat_timeline,
    'versus': _normalize_beat_versus,
    'list': _normalize_beat_list,
    'icons': _normalize_beat_icons,
    'split': _normalize_beat_split,
    'ticker': _normalize_beat_ticker,
    'cardstack': _normalize_beat_cardstack,
    'authored': _normalize_beat_authored,
    'year_counter': _normalize_beat_year_counter,
    'person_card': _normalize_beat_person_card,
    'city_skyline': _normalize_beat_city_skyline,
    'architecture': _normalize_beat_architecture,
    'mystery_scene': _normalize_beat_mystery_scene,
}
