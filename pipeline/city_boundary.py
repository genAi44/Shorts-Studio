"""Real city boundaries (city limits) from OpenStreetMap, through Nominatim (free, 1 request/second, cached on disk).

The map engine only knew countries and city points, so a scene about a city's borders showed a pin or a made-up drawing.
OSM data is ODbL: every map that draws one of these boundaries shows ATTRIBUTION.
"""
import json
import os
import time
from typing import Any, Dict, List, Optional, Tuple

from .config import ROOT

CACHE = ROOT / "data" / "city_boundaries.json"
ATTRIBUTION = "© OpenStreetMap contributors"
MAX_POINTS = 600          # simplified polygon size kept per city (Nominatim simplifies with polygon_threshold)
_LAST = [0.0]


def _cache() -> Dict[str, Any]:
    try:
        return json.loads(CACHE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _usable(geom: Any) -> bool:
    return isinstance(geom, dict) and geom.get("type") in ("Polygon", "MultiPolygon") and bool(geom.get("coordinates"))


def _thin(geom: Dict[str, Any]) -> Dict[str, Any]:
    """Keep at most MAX_POINTS points per ring (the map shows a city a few hundred pixels wide)."""
    def ring(r: List[List[float]]) -> List[List[float]]:
        step = max(1, len(r) // MAX_POINTS)
        out = [[round(p[0], 5), round(p[1], 5)] for p in r[::step]]
        return out + [out[0]] if out and out[-1] != out[0] else out
    if geom["type"] == "Polygon":
        return {"type": "Polygon", "coordinates": [ring(r) for r in geom["coordinates"]]}
    return {"type": "MultiPolygon", "coordinates": [[ring(r) for r in poly] for poly in geom["coordinates"]]}


def fetch(name_en: str, iso2: str = "") -> Optional[Dict[str, Any]]:
    """GeoJSON Polygon/MultiPolygon of the city's administrative boundary, or None (unknown, a point only, offline)."""
    name_en = (name_en or "").split(",")[0].strip()
    if not name_en:
        return None
    key = f"{name_en}|{iso2.lower()}"
    cache = _cache()
    if key in cache:
        return cache[key] or None
    if os.environ.get("NO_NETWORK") == "1" or os.environ.get("PYTEST_CURRENT_TEST"):
        return None
    import requests
    wait = 1.05 - (time.time() - _LAST[0])
    if wait > 0:
        time.sleep(wait)
    _LAST[0] = time.time()
    geom = None
    try:
        params: Dict[str, Any] = {"q": name_en, "format": "json", "limit": 3, "polygon_geojson": 1, "polygon_threshold": 0.0005,
                                  "accept-language": "en"}
        if iso2:
            params["countrycodes"] = iso2.lower()
        r = requests.get("https://nominatim.openstreetmap.org/search", params=params, timeout=10,
                         headers={"User-Agent": "ShortsStudio/1.0 (educational video generator)"})
        for hit in (r.json() if r.status_code == 200 else []):
            # a city / town administrative boundary, not a building or a street that shares the name
            if hit.get("class") in ("boundary", "place") and _usable(hit.get("geojson")):
                geom = _thin(hit["geojson"])
                break
    except Exception:  # noqa: BLE001 - no boundary: the map shows the city pin as before
        geom = None
    cache[key] = geom or {}
    try:
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        CACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass
    return geom


def rings(geom: Dict[str, Any]) -> List[List[List[float]]]:
    """Outer + inner rings of a Polygon/MultiPolygon as lon/lat lists."""
    if geom["type"] == "Polygon":
        return list(geom["coordinates"])
    return [r for poly in geom["coordinates"] for r in poly]


def extent(geom: Dict[str, Any]) -> Tuple[float, float, float, float]:
    """(lon0, lat0, lon1, lat1) of the boundary."""
    pts = [p for r in rings(geom) for p in r]
    return (min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts))


def attach(mentions: List[Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
    """Give every city mention that has a real boundary a `city` feature (drawn by the map engine). Returns {index: geom}."""
    out: Dict[int, Dict[str, Any]] = {}
    for i, m in enumerate(mentions):
        if m.get("kind") in ("city", "capital", "district") and not m.get("feature"):
            g = fetch(str(m.get("name_en") or ""), str(m.get("iso2") or ""))
            if g:
                out[i] = g
                m["feature"] = {"shape": "city", "geom": g}
    return out


def corners(geoms: Dict[int, Dict[str, Any]]) -> List[Dict[str, float]]:
    """Two corner points per boundary, for the camera to frame them."""
    pts: List[Dict[str, float]] = []
    for g in geoms.values():
        x0, y0, x1, y1 = extent(g)
        pts += [{"lon": x0, "lat": y0}, {"lon": x1, "lat": y1}]
    return pts
