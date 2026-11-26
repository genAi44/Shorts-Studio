"""Split from `pipeline/geo_overlay.py` (re-exported there); see that module."""
from __future__ import annotations
from .geo import AR_ISO3, _CITY_STOP_WORDS, detect_city_in_text, get_engine, get_geo
from typing import Any, Dict, List, Tuple
from .config import FPS
import numpy as np
import re
from .geo_overlay import _AMBIGUOUS_COUNTRY_WORDS, _COUNTRY_CONTEXT_PREV, _CURATED_CITIES_AR, _CURATED_CONTINENTS_AR, _CURATED_COUNTRIES_AR, _CURATED_LANDMARKS_AR, _PUNCT_RE, _TASHKEEL_RE  # noqa: E402


_COMMON_NOUN_CITY_STOPWORDS = {
    "العبور", "عبور", "السلام", "سلام", "النصر", "نصر", "الفتح", "فتح",
    "التحرير", "تحرير", "الثورة", "ثورة", "الشروق", "شروق", "الأمل", "أمل",
    "الرحاب", "البدر", "الفيصل", "المدينة", "مدينة", "العاصمة", "عاصمة",
    "المحيط", "البحر", "النهر", "الشمال", "الجنوب", "الشرق", "الغرب", "الوسط",
    "الخليج", "الجمهورية", "المملكة", "الدولة", "الإسلامية", "المسلمين",
    "دولا", "دولاً", "دول", "أخرى", "عالمي", "مركز", "ميناء", "جزيرة",
    "خفي", "خفية", "حديثة", "حديثا", "حديثاً", "قديم", "قديمة", "عظيم", "عظيمة",
    "كبير", "كبيرة", "صغير", "صغيرة", "جديد", "جديدة", "أبيض", "أسود", "أحمر",
}


def _norm_token(s: str) -> str:
    if not s:
        return ""
    s = _TASHKEEL_RE.sub("", str(s))
    s = _PUNCT_RE.sub("", s)
    return s.strip()


def _format_gps(lat: float, lon: float) -> str:
    ns = "N" if lat >= 0 else "S"
    ew = "E" if lon >= 0 else "W"
    return f"{abs(lat):.1f}°{ns} {abs(lon):.1f}°{ew}"


def _d_svg(xy: np.ndarray, min_d: float = 1.6, close: bool = True) -> str:
    out, last = [], None
    for x, y in xy:
        if last is None or (x - last[0]) ** 2 + (y - last[1]) ** 2 >= min_d ** 2:
            out.append((float(x), float(y)))
            last = (float(x), float(y))
    if len(out) < 3:
        return ""
    return "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in out) + ("Z" if close else "")


def _find_word_timestamp(
    mention_token: str,
    words: List[Dict[str, Any]],
    scene_dur_sec: float,
    fallback_ratio: float = 0.15,
) -> Tuple[float, float, int]:
    """Finds the exact (start_sec, end_sec, word_index) where `mention_token` is spoken in `words`."""
    norm_target = _norm_token(mention_token)
    if not norm_target or not words:
        t_start = round(scene_dur_sec * fallback_ratio, 3)
        return t_start, min(scene_dur_sec, t_start + 1.8), 0

    target_parts = [p for p in norm_target.split() if p]
    first_part = target_parts[0] if target_parts else norm_target

    for idx, w in enumerate(words):
        wt = _norm_token(w.get("t", ""))
        if not wt:
            continue
        # Match exact or with single-letter Arabic prefix (و، ب، ل، ف، ك)
        if (
            wt == first_part
            or (len(wt) >= 4 and wt[0] in ("و", "ب", "ل", "ف", "ك") and wt[1:] == first_part)
            or (len(first_part) >= 4 and first_part in wt)
        ):
            s_sec = float(w.get("s", 0.0))
            e_sec = float(w.get("e", s_sec + 0.6))
            if len(target_parts) > 1 and idx + 1 < len(words):
                e_sec = float(words[idx + 1].get("e", e_sec))
            return s_sec, e_sec, idx

    t_start = round(scene_dur_sec * fallback_ratio, 3)
    return t_start, min(scene_dur_sec, t_start + 1.8), 0


def extract_timed_geo_mentions(
    narration: str,
    on_screen: str,
    words: List[Dict[str, Any]],
    dur_frames: int,
) -> List[Dict[str, Any]]:
    """
    Automatically extracts all countries, capitals, and cities mentioned in `narration` (and `on_screen`),
    determines their accurate geographic coordinates and classification (`capital`, `city`, `country`),
    and aligns each mention with the exact spoken word timestamp in `words`.
    """
    combined = f"{narration or ''} {on_screen or ''}".strip()
    if not combined:
        return []

    clean_text = _TASHKEEL_RE.sub("", combined)
    scene_dur_sec = max(1.0, dur_frames / float(FPS))
    engine = get_engine()
    geo = get_geo()

    mentions: List[Dict[str, Any]] = []
    seen_keys = set()

    def _register_mention(
        matched_str: str,
        kind: str,
        name_ar: str,
        name_en: str,
        country_ar: str,
        iso3: str,
        iso2: str,
        lat: float,
        lon: float,
        is_microstate: bool = False,
    ):
        dedup_key = (kind, name_ar, round(lat, 1), round(lon, 1))
        if dedup_key in seen_keys:
            return
        # Avoid registering both a city and a country with the exact same name (e.g. الفاتيكان / تونس / الجزائر)
        for existing in mentions:
            if existing["name_ar"] == name_ar:
                return
        seen_keys.add(dedup_key)

        fallback_r = min(0.75, 0.10 + len(mentions) * 0.28)
        s_sec, e_sec, w_idx = _find_word_timestamp(matched_str, words, scene_dur_sec, fallback_ratio=fallback_r)
        char_pos = clean_text.find(matched_str)
        if char_pos < 0:
            char_pos = 9999

        kind_label = (
            "عاصمة" if kind == "capital"
            else ("مدينة" if kind == "city"
            else ("قارة" if kind == "continent"
            else ("معلم" if kind == "landmark" else "دولة")))
        )
        mentions.append({
            "matched_token": matched_str,
            "kind": kind,
            "kind_label": kind_label,
            "name_ar": name_ar,
            "name_en": name_en,
            "country_ar": country_ar,
            "iso3": (iso3 or "").upper(),
            "iso2": (iso2 or "").lower(),
            "lat": float(lat),
            "lon": float(lon),
            "coords": _format_gps(float(lat), float(lon)),
            "is_microstate": bool(is_microstate),
            "start_sec": round(s_sec, 3),
            "end_sec": round(e_sec, 3),
            "word_index": w_idx,
            "char_pos": char_pos,
        })

    # 1. Check curated cities & capitals first (longest match first)
    for city_key in sorted(_CURATED_CITIES_AR.keys(), key=len, reverse=True):
        pat = re.compile(rf"(?:^|[\s،؟!.,:؛\-وبلفك]){re.escape(city_key)}(?:$|[\s،؟!.,:؛\-])")
        if pat.search(clean_text):
            cinfo = _CURATED_CITIES_AR[city_key]
            # Disambiguate "عمان" (Amman vs Oman) by context
            if city_key == "عمان" and ("سلطنة" in clean_text or "خليج" in clean_text or "مسقط" in clean_text):
                continue
            _register_mention(
                matched_str=city_key,
                kind="capital" if cinfo.get("is_capital") else "city",
                name_ar=cinfo["name_ar"],
                name_en=cinfo["name_en"],
                country_ar=cinfo["country_ar"],
                iso3=cinfo["iso3"],
                iso2=cinfo["iso2"],
                lat=cinfo["lat"],
                lon=cinfo["lon"],
            )

    # 1b. Check curated landmarks, waterways & geo-historical sites
    for lm_key in sorted(_CURATED_LANDMARKS_AR.keys(), key=len, reverse=True):
        pat = re.compile(rf"(?:^|[\s،؟!.,:؛\-وبلفك]){re.escape(lm_key)}(?:$|[\s،؟!.,:؛\-])")
        if pat.search(clean_text):
            linfo = _CURATED_LANDMARKS_AR[lm_key]
            _register_mention(
                matched_str=lm_key,
                kind="landmark",
                name_ar=linfo["name_ar"],
                name_en=linfo["name_en"],
                country_ar=linfo["country_ar"],
                iso3=linfo["iso3"],
                iso2=linfo["iso2"],
                lat=linfo["lat"],
                lon=linfo["lon"],
            )

    # 2. Check curated countries & microstates
    for country_key in sorted(_CURATED_COUNTRIES_AR.keys(), key=len, reverse=True):
        pat = re.compile(rf"(?:^|[\s،؟!.,:؛\-وبلفك]){re.escape(country_key)}(?:$|[\s،؟!.,:؛\-])")
        if pat.search(clean_text):
            # Disambiguate "أمريكا" (USA) vs continent names ("أمريكا الجنوبية / الشمالية / اللاتينية / الوسطى")
            if country_key in ("أمريكا", "امريكا") and re.search(
                r"(?:أمريكا|امريكا)\s+(?:الجنوبية|الشمالية|اللاتينية|الوسطى)",
                clean_text,
            ):
                continue
            cinfo = _CURATED_COUNTRIES_AR[country_key]
            _register_mention(
                matched_str=country_key,
                kind="country",
                name_ar=cinfo["name_ar"],
                name_en=cinfo["name_en"],
                country_ar=cinfo["name_ar"],
                iso3=cinfo["iso3"],
                iso2=cinfo["iso2"],
                lat=cinfo["lat"],
                lon=cinfo["lon"],
                is_microstate=bool(cinfo.get("is_microstate")),
            )

    # 2b. Check continents (if no more specific country/city/landmark already found, or alongside)
    if len(mentions) < 3:
        for cont_key in sorted(_CURATED_CONTINENTS_AR.keys(), key=len, reverse=True):
            pat = re.compile(rf"(?:^|[\s،؟!.,:؛\-وبلفك]){re.escape(cont_key)}(?:$|[\s،؟!.,:؛\-])")
            if pat.search(clean_text):
                cinfo = _CURATED_CONTINENTS_AR[cont_key]
                if cinfo.get("is_region") and mentions:
                    continue  # specific places already named: a region view would shrink them to specks
                _register_mention(
                    matched_str=cont_key,
                    kind="continent",
                    name_ar=cinfo["name_ar"],
                    name_en=cinfo["name_en"],
                    country_ar=cinfo["name_ar"],
                    iso3=cinfo["iso3"],
                    iso2="",
                    lat=cinfo["lat"],
                    lon=cinfo["lon"],
                )
                if mentions:
                    mentions[-1]["continent_isos"] = list(cinfo.get("continent_isos") or [])
                    if cinfo.get("is_region"):
                        mentions[-1]["kind_label"] = "منطقة"

    # 3. Dynamic database scan for any other country in AR_ISO3
    if len(mentions) < 4:
        for ar_name, iso3 in sorted(AR_ISO3.items(), key=lambda x: len(x[0]), reverse=True):
            if len(ar_name) < 3 or not re.search(r"[\u0600-\u06FF]", ar_name):
                continue
            if ar_name in _CITY_STOP_WORDS:
                continue
            if ar_name in _AMBIGUOUS_COUNTRY_WORDS and not re.search(
                rf"(?:{'|'.join(_COUNTRY_CONTEXT_PREV)})\s+{re.escape(ar_name)}(?:$|[\s،؟!.,:؛\-])", clean_text
            ):
                continue  # e.g. "مركز مالي" (financial hub) must not resolve to Mali
            if ar_name in ("أمريكا", "امريكا") and re.search(
                r"(?:أمريكا|امريكا)\s+(?:الجنوبية|الشمالية|اللاتينية|الوسطى)",
                clean_text,
            ):
                continue
            pat = re.compile(rf"(?:^|[\s،؟!.,:؛\-وبلف]){re.escape(ar_name)}(?:$|[\s،؟!.,:؛\-])")
            if pat.search(clean_text) and geo.has(iso3):
                bb = geo.main_bbox(iso3)
                lon_c = (bb[0] + bb[2]) / 2.0
                lat_c = (bb[1] + bb[3]) / 2.0
                c_row = engine.get_country(iso3) if engine else None
                iso2 = (c_row.iso2 if c_row else iso3[:2]).lower()
                en_name = (c_row.name_en if c_row else geo.c[iso3].get("name", iso3))
                _register_mention(
                    matched_str=ar_name,
                    kind="country",
                    name_ar=ar_name,
                    name_en=en_name,
                    country_ar=ar_name,
                    iso3=iso3,
                    iso2=iso2,
                    lat=lat_c,
                    lon=lon_c,
                )
                if len(mentions) >= 4:
                    break

    # 4. Token-level city/capital lookup in geodata.db for any remaining cities
    if len(mentions) < 4:
        raw_tokens = [_norm_token(tok) for tok in clean_text.split()]
        raw_tokens = [t for t in raw_tokens if len(t) >= 3 and t not in _CITY_STOP_WORDS]
        candidates: List[str] = []
        for i in range(len(raw_tokens)):
            if i + 1 < len(raw_tokens):
                candidates.append(f"{raw_tokens[i]} {raw_tokens[i + 1]}")
            candidates.append(raw_tokens[i])
            if len(raw_tokens[i]) >= 5 and raw_tokens[i][0] in ("و", "ب", "ل", "ف"):
                stripped = raw_tokens[i][1:]
                if stripped not in _CITY_STOP_WORDS:
                    candidates.append(stripped)

        for cand in candidates:
            if len(mentions) >= 4:
                break
            norm_cand = _norm_token(cand)
            if norm_cand in _CITY_STOP_WORDS or norm_cand in _COMMON_NOUN_CITY_STOPWORDS:
                continue
            cn, ci = detect_city_in_text(cand)
            if cn and (_norm_token(cn) in _COMMON_NOUN_CITY_STOPWORDS):
                continue
            if cn and ci and "lat" in ci and "lon" in ci:
                pop = int(ci.get("pop") or ci.get("population") or 0)
                is_cap = bool(ci.get("is_capital"))
                has_city_prefix = bool(re.search(rf"مدينة\s+{re.escape(cand)}", clean_text))
                if not is_cap and pop < 500_000 and not has_city_prefix:
                    continue
                iso3 = str(ci.get("iso") or "").upper()
                iso2 = str(ci.get("iso2") or iso3[:2]).lower()
                c_row = engine.get_country(iso3) if (engine and iso3) else None
                country_ar = (c_row.name_ar if (c_row and c_row.name_ar) else str(ci.get("country") or ""))
                _register_mention(
                    matched_str=cand,
                    kind="capital" if ci.get("is_capital") else "city",
                    name_ar=str(ci.get("name") or cn),
                    name_en=str(ci.get("en") or cn),
                    country_ar=country_ar,
                    iso3=iso3,
                    iso2=iso2,
                    lat=float(ci["lat"]),
                    lon=float(ci["lon"]),
                )

    # Sort mentions in chronological spoken order (by start_sec, then char_pos)
    mentions.sort(key=lambda m: (m["start_sec"], m["char_pos"]))
    return mentions[:4]
