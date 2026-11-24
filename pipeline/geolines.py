"""Offline reference lines (mountain ranges, boundaries, equator ...) and the geometry to cut a country along one of them.

Data: data/geo_lines.json (schematic centre lines, hand-made, drawn as approximate). No network, no API key.
`find()` resolves an Arabic/English name; `split_polygon()` cuts a ring in two along a line (west/east of it), which is how
"the Urals divide Russia into Europe and Asia" is drawn on the map.
"""
from __future__ import annotations

import functools
import json
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .config import ROOT

PATH = ROOT / "data" / "geo_lines.json"
_HAMZA = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ى": "ي", "ة": "ه"})
_LEAD = ("جبال ", "سلسلة ", "سلاسل ", "خط ", "الخط ")


def _norm(s: str) -> str:
    s = "".join(ch for ch in str(s or "") if not "ً" <= ch <= "ْ" and ch != "ـ").translate(_HAMZA).strip().lower()
    for lead in _LEAD:
        if s.startswith(lead) and len(s) > len(lead) + 2:
            s = s[len(lead):]
    if s.startswith("ال") and len(s) > 4:
        s = s[2:]
    return " ".join(s.split())


@functools.lru_cache(maxsize=1)
def _lines() -> List[Dict[str, Any]]:
    try:
        return list(json.loads(PATH.read_text(encoding="utf-8")).get("lines") or [])
    except (OSError, ValueError):
        return []


@functools.lru_cache(maxsize=1)
def _index() -> Dict[str, Dict[str, Any]]:
    idx: Dict[str, Dict[str, Any]] = {}
    for ln in _lines():
        for name in [ln.get("name_ar"), ln.get("name_en"), *(ln.get("aliases") or [])]:
            if name:
                idx.setdefault(_norm(name), ln)
    return idx


def find(name_ar: str = "", name_en: str = "") -> Optional[Dict[str, Any]]:
    """The line called `name_ar` / `name_en` (aliases, hamza and «جبال/خط/ال» insensitive), or None."""
    idx = _index()
    for n in (name_ar, name_en):
        if n and _norm(n) in idx:
            return idx[_norm(n)]
    return None


def as_geojson(line: Dict[str, Any]) -> str:
    return json.dumps({"type": "LineString", "coordinates": line["points"]})


def lon_at(points: Sequence[Sequence[float]], lat: float) -> float:
    """Longitude of the polyline at `lat` (piecewise linear; above / below its ends the end segment is extended)."""
    pts = [(float(x), float(y)) for x, y in points]
    best = None
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        lo, hi = min(y0, y1), max(y0, y1)
        if lo <= lat <= hi and y1 != y0:
            return x0 + (x1 - x0) * (lat - y0) / (y1 - y0)
        if y1 != y0:
            best = best or ((x0, y0), (x1, y1))
    ys = [p[1] for p in pts]
    if lat > max(ys):                                   # north of the line: follow its northern end
        end = max(pts, key=lambda p: p[1])
    else:
        end = min(pts, key=lambda p: p[1])
    return end[0]


def split_polygon(ring: Sequence[Sequence[float]], points: Sequence[Sequence[float]]) -> Tuple[List[List[float]], List[List[float]]]:
    """Cut a ring [[lon, lat], ...] by the polyline: returns (west_ring, east_ring), either may be empty.
    Sutherland-Hodgman against the half-plane lon <= lon_at(lat) (and the opposite one)."""
    def clip(sign: int) -> List[List[float]]:
        out: List[List[float]] = []
        n = len(ring)
        if n < 3:
            return out
        d = [(sign * (float(p[0]) - lon_at(points, float(p[1])))) for p in ring]
        for i in range(n):
            p, q = ring[i], ring[(i + 1) % n]
            dp, dq = d[i], d[(i + 1) % n]
            if dp <= 0:
                out.append([float(p[0]), float(p[1])])
            if (dp < 0 < dq) or (dq < 0 < dp):
                t = dp / (dp - dq)
                out.append([float(p[0]) + t * (float(q[0]) - float(p[0])), float(p[1]) + t * (float(q[1]) - float(p[1]))])
        return out if len(out) >= 3 else []
    return clip(+1), clip(-1)


def divides(line: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    d = line.get("divides")
    return d if isinstance(d, dict) and d.get("countries") else None
