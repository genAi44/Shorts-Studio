"""Split from `pipeline/visual_tools.py` (re-exported there); see that module."""
from __future__ import annotations
from .geo import AR_ISO3
from typing import Any, Dict, List, Optional
import json
import re
from .visual_tools import PKG_ASSETS  # noqa: E402


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
    elif re.match(r"^[A-Z]{3}$", upper):
        _ISO3_TO_ISO2_EXTRA = {
            "PAN": "pa", "CRI": "cr", "ISL": "is", "GRL": "gl", "MUS": "mu", "SLB": "sb",
            "AND": "ad", "LIE": "li", "MCO": "mc", "SMR": "sm", "VAT": "va", "LUX": "lu",
            "MLT": "mt", "CYP": "cy", "IRL": "ie", "NZL": "nz", "AUS": "au", "CAN": "ca",
            "MEX": "mx", "ARG": "ar", "CHL": "cl", "COL": "co", "PER": "pe", "VEN": "ve",
            "ECU": "ec", "URY": "uy", "PRY": "py", "CUB": "cu", "DOM": "do", "HTI": "ht",
            "JAM": "jm", "GTM": "gt", "HND": "hn", "SLV": "sv", "NIC": "ni", "BTN": "bt",
            "MDV": "mv", "WSM": "ws", "DMA": "dm", "GRD": "gd", "LCA": "lc", "VCT": "vc",
            "PLW": "pw", "MHL": "mh", "FSM": "fm", "NRU": "nr", "TUV": "tv", "KIR": "ki",
        }
        if upper in iso3_map:
            iso2 = iso3_map[upper].lower()
        elif upper in _ISO3_TO_ISO2_EXTRA:
            iso2 = _ISO3_TO_ISO2_EXTRA[upper]
        else:
            try:
                from .geo import get_geo
                c_meta = get_geo().c.get(upper) or {}
                if c_meta.get("iso2"):
                    iso2 = str(c_meta["iso2"]).lower()
            except Exception:
                pass

    if not iso2:
        # Check pipeline.geo AR_ISO3 — exact name only (substring matches caused wrong flags)
        for ar_name, iso3_code in AR_ISO3.items():
            if ar_name == raw:
                if iso3_code in iso3_map:
                    iso2 = iso3_map[iso3_code].lower()
                    break

    if not iso2:
        # Exact match first across iso2, iso3, ar, en
        for c in countries:
            if c["iso2"].upper() == upper or c["iso3"].upper() == upper:
                iso2 = c["iso2"].lower()
                break
            if any(a == raw for a in c.get("ar", [])):
                iso2 = c["iso2"].lower()
                break
            if any(e == lower for e in c.get("en", [])):
                iso2 = c["iso2"].lower()
                break

    if not iso2 and not re.match(r"^[A-Z]{2,3}$", upper):
        # Whole-word fallback only (never partial words: 'بنما' ≠ 'بنمائي', 'pan' ≠ 'japan')
        for c in countries:
            if any(
                len(a) >= 3 and re.search(rf"(?:^|[\s،,.\-]){re.escape(a)}(?:$|[\s،,.\-])", raw)
                for a in c.get("ar", [])
            ):
                iso2 = c["iso2"].lower()
                break
            if any(len(e) >= 4 and re.search(rf"\b{re.escape(e)}\b", lower) for e in c.get("en", [])):
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
