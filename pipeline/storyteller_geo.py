"""Split from `pipeline/storyteller.py` (re-exported there); see that module."""
from __future__ import annotations
from .geo import AR_ISO3, detect_city_in_text, get_geo
from typing import Any, Dict, List, Optional, Tuple
from .geo import _CITY_STOP_WORDS
import math
import re
from .storyteller import _clean_text, _extract_phrases, _words, logger  # noqa: E402


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
