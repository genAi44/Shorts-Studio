"""Split from `pipeline/entities.py` (re-exported there); see that module."""
from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
import json
import os
from .config import record_fallback
import threading
import time
from .entities import ENTITY_REGISTRY, NOMINATIM_CACHE, find_span  # noqa: E402


_OCEANS: Dict[str, Tuple[str, float, float, float, float]] = {  # name_ar -> (name_en, lat, lon, half_h_deg, half_w_deg)
    "المحيط الأطلسي": ("Atlantic Ocean", 5.0, -30.0, 45.0, 28.0),
    "المحيط الهادئ": ("Pacific Ocean", 0.0, -150.0, 50.0, 45.0),
    "المحيط الهندي": ("Indian Ocean", -15.0, 78.0, 35.0, 35.0),
    "المحيط المتجمد الشمالي": ("Arctic Ocean", 82.0, 0.0, 10.0, 90.0),
    "المحيط الجنوبي": ("Southern Ocean", -65.0, 0.0, 12.0, 90.0),
    "البحر الأبيض المتوسط": ("Mediterranean Sea", 35.0, 18.0, 6.0, 20.0),
    "البحر الأحمر": ("Red Sea", 20.0, 38.5, 9.0, 4.0),
    "الخليج العربي": ("Persian Gulf", 27.0, 51.5, 3.0, 4.0),
    "بحر العرب": ("Arabian Sea", 15.0, 65.0, 8.0, 10.0),
}


_RATE = threading.Lock()


_LAST_NOMINATIM = [0.0]


def _nominatim_cache() -> Dict[str, Any]:
    try:
        return json.loads(NOMINATIM_CACHE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def geocode_online(query: str, iso2: str = "") -> Optional[Dict[str, Any]]:
    """Nominatim (free), 1 request/second, results cached on disk. Callers add the visible warning."""
    key = f"{query}|{iso2}"
    cache = _nominatim_cache()
    if key in cache:
        return cache[key] or None
    if os.environ.get("NO_NETWORK") == "1":
        return None
    import requests
    with _RATE:
        wait = 1.05 - (time.time() - _LAST_NOMINATIM[0])
        if wait > 0:
            time.sleep(wait)
        _LAST_NOMINATIM[0] = time.time()
        try:
            params: Dict[str, Any] = {"q": query, "format": "json", "limit": 1}
            if iso2:
                params["countrycodes"] = iso2.lower()
            r = requests.get("https://nominatim.openstreetmap.org/search", params=params, timeout=6,
                             headers={"User-Agent": "ShortsStudio/1.0 (educational video generator)"})
            data = r.json() if r.status_code == 200 else []
        except Exception:  # noqa: BLE001
            data = []
    res = {"lat": float(data[0]["lat"]), "lon": float(data[0]["lon"]), "name_en": data[0].get("display_name", "")[:60]} if data else None
    cache[key] = res or {}
    try:
        NOMINATIM_CACHE.parent.mkdir(parents=True, exist_ok=True)
        NOMINATIM_CACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass
    return res


def _km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    import math
    p = math.pi / 180
    a = math.sin((lat2 - lat1) * p / 2) ** 2 + math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin((lon2 - lon1) * p / 2) ** 2
    return 12742 * math.asin(min(1, math.sqrt(a)))


def _num(v: Any) -> Optional[float]:
    try:
        f = float(v)
        return f if f == f else None
    except (TypeError, ValueError):
        return None


_CONTINENT_CODE = {"Africa": "AF", "Asia": "AS", "Europe": "EU", "North America": "NA", "South America": "SA", "Oceania": "OC", "Antarctica": "AN"}


def _continent_members(name_en: str) -> List[str]:
    """Every country of the continent (Natural Earth continent code in the countries table), so the whole continent is lit."""
    import sqlite3
    code = _CONTINENT_CODE.get(name_en)
    if not code:
        return []
    try:
        from .geo import DEFAULT_DB_PATH
        con = sqlite3.connect(str(DEFAULT_DB_PATH))
        rows = con.execute("SELECT iso3 FROM countries WHERE continent=? AND iso3 IS NOT NULL", (code,)).fetchall()
        con.close()
        return [r[0] for r in rows]
    except Exception:  # noqa: BLE001
        return []


def _resolve_place(e: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    from .geo import get_engine
    scale = str(e.get("scale") or "")
    name_ar, name_en = str(e.get("name_ar") or ""), str(e.get("name_en") or "")
    iso2 = str(e.get("iso2") or "").upper()
    out = {"type": "place", "scale": scale, "name_ar": name_ar, "name_en": name_en, "text": e.get("text") or name_ar}
    if scale == "globe":
        out.update(lat=20.0, lon=10.0, verified="builtin")
        return out
    if scale == "ocean":
        hit = _OCEANS.get(name_ar)
        if hit:
            out.update(name_en=hit[0], lat=hit[1], lon=hit[2], half_h=hit[3], half_w=hit[4], verified="builtin")
            return out
        lat, lon = _num(e.get("lat")), _num(e.get("lon"))
        if lat is None or lon is None:
            return None
        out.update(lat=lat, lon=lon, half_h=10.0, half_w=14.0, verified="llm-coordinates")
        return out
    if scale == "continent":
        from .geo_overlay import _CURATED_CONTINENTS_AR
        hit = _CURATED_CONTINENTS_AR.get(name_ar)
        if not hit:
            return None
        out.update(lat=hit["lat"], lon=hit["lon"], name_en=hit["name_en"], iso3=hit["iso3"],
                   continent_isos=_continent_members(hit["name_en"]) or list(hit.get("continent_isos") or []), verified="natural-earth")
        return out
    engine = get_engine()
    if scale == "country":
        c = engine.get_country(iso2) if iso2 else None
        if c is None:
            p = engine.resolve(name_ar or name_en, feature_codes=["PCLI"])
            c = engine.get_country(p.country_iso2) if p else None
        if c is None:
            return None
        out.update(iso2=c.iso2.lower(), iso3=c.iso3, name_ar=name_ar or c.name_ar or "", name_en=c.name_en,
                   lat=c.centroid_lat or 0.0, lon=c.centroid_lon or 0.0, verified="natural-earth")
        return out
    # village / town / city / capital / region
    p = None
    for q in (name_ar, name_en):
        if q:
            p = engine.resolve(q, country_iso2=iso2 or None)
            if p:
                break
    lat, lon = _num(e.get("lat")), _num(e.get("lon"))
    if p:
        if lat is not None and lon is not None and _km(lat, lon, p.lat, p.lon) > 400:
            # the model and the dictionary disagree: trust the dictionary, say so
            record_fallback(f"place '{name_ar or name_en}': model coordinates {_km(lat, lon, p.lat, p.lon):.0f} km from the dictionary entry; dictionary used", beat_id="geo")
        out.update(lat=p.lat, lon=p.lon, iso2=(p.country_iso2 or "").lower(), iso3=p.country_iso3 or "", name_en=p.name_en,
                   country_ar=p.country_ar or "", scale="capital" if p.is_capital else scale, verified="geonames")
        return out
    q = name_en or name_ar
    res = geocode_online(q, iso2.lower()) if q else None
    if res:
        record_fallback(f"place '{name_ar or name_en}' not in the local dictionary: geocoded online (Nominatim), verify it", beat_id="geo")
        out.update(lat=res["lat"], lon=res["lon"], verified="nominatim")
        return out
    if scale == "region" and lat is not None and lon is not None:
        # a named region without a polygon in the data (e.g. a peninsula): marked area from the model's coordinates, said out loud
        record_fallback(f"region '{name_ar or name_en}' is not in the data: drawn as an approximate marked area from model coordinates", beat_id="geo")
        out.update(lat=lat, lon=lon, verified="llm-coordinates", approx=True)
        return out
    return None


def _resolve_terrain(e: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    import sqlite3
    scale = str(e.get("scale") or "")
    out = {"type": "terrain", "scale": scale, "name_ar": str(e.get("name_ar") or ""), "name_en": str(e.get("name_en") or ""),
           "text": e.get("text") or e.get("name_ar") or ""}
    lat, lon = _num(e.get("lat")), _num(e.get("lon"))
    if scale in ("mountain", "boundary", "range", "line"):   # offline reference lines: the range / line is drawn, not just marked
        from . import geolines
        ln = geolines.find(out["name_ar"], out["name_en"]) or geolines.find(str(e.get("text") or ""), "")
        if ln:
            pts = ln["points"]
            mid = pts[len(pts) // 2]
            out.update(geojson=geolines.as_geojson(ln), lat=mid[1], lon=mid[0], verified="local-lines", approx=True,
                       line_id=ln["id"], line_kind=ln.get("kind", "range"), name_ar=out["name_ar"] or ln["name_ar"], name_en=out["name_en"] or ln["name_en"])
            if geolines.divides(ln):
                out["divides"] = geolines.divides(ln)
            return out
    if scale in ("river", "lake") and (out["name_en"] or out["name_ar"]):
        try:
            from .geo import DEFAULT_DB_PATH
            generic = {"river", "lake", "nile river"}
            en_words = [w for w in out["name_en"].split() if w.lower() not in ("river", "lake")]
            cands = [c for c in (out["name_en"], " ".join(en_words), out["name_ar"]) if c]
            con = sqlite3.connect(str(DEFAULT_DB_PATH))
            row = None
            for cand in dict.fromkeys(cands):
                row = con.execute("SELECT geojson, bbox_west, bbox_south, bbox_east, bbox_north FROM geo_features WHERE type=? AND (lower(name_en)=lower(?) OR name_ar=?) ORDER BY (bbox_east-bbox_west)*(bbox_north-bbox_south) DESC LIMIT 1",
                                  (scale, cand, cand)).fetchone()
                if row:
                    break
            con.close()
            del generic
            if row:
                out.update(geojson=row[0], lat=(row[2] + row[4]) / 2, lon=(row[1] + row[3]) / 2, verified="natural-earth")
                out["lat"], out["lon"] = (row[2] + row[4]) / 2, (row[1] + row[3]) / 2
                return out
        except Exception:  # noqa: BLE001
            pass
    if lat is None or lon is None:
        return None
    record_fallback(f"{scale} '{out['name_ar'] or out['name_en']}' not in Natural Earth data: drawn as an approximate marked area from model coordinates", beat_id="terrain")
    out.update(lat=lat, lon=lon, verified="llm-coordinates", approx=True)
    return out


def validate_entity(e: Dict[str, Any], sentence: str, geo: Any = None) -> Optional[Dict[str, Any]]:
    """Local verification. Returns the cleaned entity (with `span`) or None (dropped, with a visible warning)."""
    t = str(e.get("type") or "")
    et = ENTITY_REGISTRY.get(t)
    if not et or t == "flag":
        return None
    span = find_span(sentence, str(e.get("text") or ""))
    if span is None and e.get("name_ar"):
        span = find_span(sentence, str(e.get("name_ar")))
    if span is None:
        record_fallback(f"entity '{e.get('text') or e.get('name_ar')}' ({t}) is not a whole-word span of its sentence: ignored", beat_id="entities")
        return None
    out: Optional[Dict[str, Any]]
    if t == "place":
        out = _resolve_place(e)
    elif t == "terrain":
        out = _resolve_terrain(e)
    elif t == "time":
        v = _num(e.get("value"))
        out = {**e, "value": int(v)} if v is not None else None
    elif t == "quantity":
        v = _num(e.get("value"))
        out = {**e, "value": v} if v is not None else None
    elif t == "conflict":
        out = dict(e) if isinstance(e.get("a"), dict) and isinstance(e.get("b"), dict) else None
    elif t == "route":
        stops = [s for s in (e.get("stops") or []) if isinstance(s, dict) and _num(s.get("lat")) is not None and _num(s.get("lon")) is not None]
        out = {**e, "stops": stops} if len(stops) >= 2 else None
    elif t == "empire":
        out = dict(e) if _num(e.get("lat")) is not None and _num(e.get("lon")) is not None else None
    else:  # person, nature
        out = dict(e) if (e.get("name_ar") or e.get("name_en")) else None
    if out is None:
        record_fallback(f"entity '{e.get('text') or e.get('name_ar')}' ({t}) could not be verified locally: dropped", beat_id="entities")
        return None
    out["type"], out["span"] = t, list(span)
    return out
