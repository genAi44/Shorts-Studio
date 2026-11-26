"""Area maps: when the narration states the AREA/SIZE of a place, show that place's outline with the area.

Flow: the director LLM extracts a structured `area` claim per sentence (place, type, value, unit, optional
compare). Nothing here parses Arabic prose: places are resolved by ISO3 / English name / normalised Arabic
name against bundled offline data (data/world.geojson + data/area_places.json), and the claimed number is
checked against the data (>10% off -> visible warning). The validator side (`missing_reasons` / `enforce`)
rejects a sentence that has a claim but no `area_map` beat.
"""
from __future__ import annotations

import json
import logging
import math
from typing import Any, Dict, List, Optional

import numpy as np

from .config import LAST_WARNINGS, ROOT, record_fallback

_log = logging.getLogger("shorts_studio")

LAYOUTS = ("top", "bottom", "overlay")
# (box center y, box height) of the map area per layout; all inside BEAT_ZONE 280..1380
BOX = {"top": (1010, 600), "bottom": (740, 600), "overlay": (810, 740)}
UNITS = {"km2": 1.0, "mi2": 2.589988110336, "ha": 0.01, "m2": 1e-6}
TOL = 0.10  # narration vs data tolerance
EARTH_KM = 6371.0088
_AR_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
_AR_FOLD = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ى": "ي", "ة": "ه", "ؤ": "و", "ئ": "ي"})
_TYPES = ("country", "city", "continent", "ocean", "sea", "lake", "island", "region")


# ------------------------------------------------------------------ text/number helpers (no regex)
def norm_ar(s: Any) -> str:
    s = "".join(ch for ch in str(s or "") if not (0x064B <= ord(ch) <= 0x065F or ch in "ـٰ"))
    s = s.translate(_AR_FOLD).strip().casefold()
    return " ".join(w[2:] if w.startswith("ال") and len(w) > 3 else w for w in s.split())


def _num(v: Any) -> Optional[float]:
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        x = float(v)
    else:
        s = str(v or "").translate(_AR_DIGITS).replace("٬", "").replace(",", "").replace("٫", ".").strip()
        try:
            x = float(s)
        except ValueError:
            return None
    return x if math.isfinite(x) and x > 0 else None


def _has_arabic_digits(s: Any) -> bool:
    return any("٠" <= ch <= "٩" or "۰" <= ch <= "۹" for ch in str(s or ""))


def _warn(msg: str) -> None:
    msg = f"WARNING: area-map {msg}"
    if msg not in LAST_WARNINGS:
        LAST_WARNINGS.append(msg)
        _log.warning(msg)


# ------------------------------------------------------------------ geometry on the sphere
def _ring_area(r) -> float:
    a = np.asarray(r, float)
    x, y = np.radians(a[:, 0]), np.radians(a[:, 1])
    d = (np.roll(x, -1) - x + np.pi) % (2 * np.pi) - np.pi  # antimeridian-safe step
    return abs(float(np.sum(d * (2 + np.sin(y) + np.sin(np.roll(y, -1)))))) * EARTH_KM ** 2 / 2


def _poly_area(poly) -> float:
    return _ring_area(poly[0]) - sum(_ring_area(h) for h in poly[1:])


def _disc(lat: float, lon: float, area_km2: float, n: int = 64) -> List[list]:
    r = math.sqrt(area_km2 / math.pi)
    kx = 111.32 * max(math.cos(math.radians(lat)), 0.05)
    return [[[lon + r / kx * math.cos(t), lat + r / 110.574 * math.sin(t)] for t in np.linspace(0, 2 * math.pi, n, endpoint=False)]]


def _clip(ring, lim: float, keep_le: bool):
    inside = (lambda p: p[0] <= lim) if keep_le else (lambda p: p[0] >= lim)
    out = []
    for i, a in enumerate(ring):
        b = ring[(i + 1) % len(ring)]
        ia, ib = inside(a), inside(b)
        if ia:
            out.append(a)
        if ia != ib:
            t = (lim - a[0]) / (b[0] - a[0])
            out.append([lim, a[1] + t * (b[1] - a[1])])
    return out


def _russia(polys, side: str):
    out = []
    for poly in polys:
        xs = [p[0] for p in poly[0]]
        if max(xs) < -100:  # Chukotka beyond the antimeridian
            if side == "east":
                out.append(poly)
            continue
        ring = _clip(poly[0], 60.0, side == "west")
        if len(ring) >= 3:
            out.append([ring])
    return out


# ------------------------------------------------------------------ registry
_REG: Optional[Dict[str, Any]] = None


def registry() -> Dict[str, Any]:
    global _REG
    if _REG is not None:
        return _REG
    from .geo import get_geo
    from .geo_overlay import _CURATED_COUNTRIES_AR

    g = get_geo()
    data = json.loads((ROOT / "data" / "area_places.json").read_text(encoding="utf-8"))
    places: Dict[str, dict] = {}
    idx: Dict[tuple, List[dict]] = {}

    def add(p: dict, ar_names=(), en_names=()):
        places[p["id"]] = p
        keys = [("id", p["id"].lower())] + [("en", n.lower()) for n in (p["name_en"], *en_names) if n]
        keys += [("ar", norm_ar(n)) for n in (p.get("name_ar"), *ar_names) if n]
        for k in keys:
            lst = idx.setdefault(k, [])
            if p not in lst:
                lst.append(p)

    for iso, c in g.c.items():
        bb = g.main_bbox(iso)
        add({"id": iso, "type": "country", "iso3": iso, "name_en": c["name"], "name_ar": "",
             "area_km2": data["country_area_km2"].get(iso) or sum(_poly_area(p) for p in c["polys"]), "lat": (bb[1] + bb[3]) / 2, "lon": (bb[0] + bb[2]) / 2,
             "polys": c["polys"], "synthetic": False})
    # Arabic names of countries: curated table (+ explicit fixes from the data file first)
    for ar, iso in data["country_aliases_ar"].items():
        if iso in places:
            idx.setdefault(("ar", norm_ar(ar)), []).append(places[iso])
    for ar, v in _CURATED_COUNTRIES_AR.items():
        p = places.get(v.get("iso3"))
        if p:
            for n in (ar, v.get("name_ar")):
                lst = idx.setdefault(("ar", norm_ar(n)), [])
                if p not in lst:
                    lst.append(p)
            p["name_ar"] = p["name_ar"] or v.get("name_ar", "")
    for cid, c in data["continents"].items():
        polys: List[list] = []
        for iso in c["members"].split():
            if iso in g.c:
                polys += g.c[iso]["polys"]
        if c.get("russia") and "RUS" in g.c:
            polys += _russia(g.c["RUS"]["polys"], c["russia"])
        add({"id": cid, "type": "continent", "name_en": c["name_en"], "name_ar": c["name_ar"], "area_km2": c["area_km2"],
             "lat": c["lat"], "lon": c["lon"], "polys": polys, "synthetic": False}, c.get("aliases_ar", ()))
    for pl in data["places"]:
        if pl.get("rings"):
            polys, syn = [pl["rings"]], False  # outer ring + optional hole (even-odd)
        else:
            polys, syn = [_disc(pl["lat"], pl["lon"], pl["area_km2"])], True
        add({**{k: pl[k] for k in ("id", "type", "name_en", "name_ar", "area_km2", "lat", "lon")}, "iso3": pl.get("iso3", ""),
             "polys": polys, "synthetic": syn}, pl.get("aliases_ar", ()))
    _REG = {"places": places, "idx": idx}
    return _REG


def resolve(a: dict) -> Optional[dict]:
    """Find the bundled place for a claim place dict {place, place_en, iso3, type}. ISO3 first for countries."""
    R = registry()
    typ = a.get("type")
    iso = str(a.get("iso3") or "").upper()
    keys = [("en", str(a.get("place_en") or "").lower()), ("ar", norm_ar(a.get("place")))]
    if iso and typ in (None, "", "country", "region", "city"):
        keys.insert(0, ("id", iso.lower()))
    for k in keys:
        cands = R["idx"].get(k) or []
        if cands:
            return next((p for p in cands if p["type"] == typ), cands[0])
    return None


# ------------------------------------------------------------------ claims
def _place_part(a: dict) -> dict:
    typ = str(a.get("type") or "").lower()
    return {"place": str(a.get("place") or "").strip(), "place_en": str(a.get("place_en") or "").strip(),
            "iso3": str(a.get("iso3") or "").strip().upper(), "type": typ if typ in _TYPES else ""}


def claim_of(raw: Any) -> Optional[dict]:
    """Normalise the director's `area` object, or None when the beat carries no usable area claim."""
    a = raw.get("area") if isinstance(raw, dict) else None
    if not isinstance(a, dict):
        return None
    c = _place_part(a)
    if not (c["place"] or c["place_en"] or c["iso3"]):
        return None
    c["value"] = _num(a.get("value"))
    c["unit"] = a.get("unit") if a.get("unit") in UNITS else "km2"
    c["digits"] = a.get("digits") if a.get("digits") in ("arabic", "latin") else ("arabic" if _has_arabic_digits(a.get("value_text")) else "latin")
    cmp_ = a.get("compare")
    c["compare"] = None
    if isinstance(cmp_, dict) and _num(cmp_.get("ratio")) and (cmp_.get("place") or cmp_.get("place_en") or cmp_.get("iso3")):
        c["compare"] = {**_place_part(cmp_), "ratio": _num(cmp_["ratio"])}
    if c["value"] is None and c["compare"] is None:
        return None
    for k in ("_checked", "res_id", "data_km2", "value_km2", "synthetic"):
        if k in a:
            c[k] = a[k]
    if isinstance(c["compare"], dict) and isinstance(cmp_, dict):
        for k in ("res_id", "data_km2", "data_ratio"):
            if k in cmp_:
                c["compare"][k] = cmp_[k]
    return c


def _diff(claimed: float, data: float) -> float:
    return abs(claimed - data) / data if data else 1.0


def check_claim(c: dict) -> dict:
    """Resolve the place(s) against bundled data and warn when the narration disagrees (>10%). Idempotent."""
    if c.get("_checked"):
        return c
    c["_checked"] = True
    name = c["place"] or c["place_en"] or c["iso3"]
    p = resolve(c)
    c["res_id"] = p["id"] if p else ""
    c["data_km2"] = round(p["area_km2"], 1) if p else None
    c["synthetic"] = bool(p["synthetic"]) if p else True
    if not p:
        _warn(f"place '{name}' not found in bundled data — showing approximate shape")
    if c["value"] is not None:
        c["value_km2"] = c["value"] * UNITS[c["unit"]]
        if p and _diff(c["value_km2"], p["area_km2"]) > TOL:
            _warn(f"narration says {c['value_km2']:,.0f} km² for '{name}' but data says {p['area_km2']:,.0f} km² "
                  f"({_diff(c['value_km2'], p['area_km2']) * 100:.0f}% off)")
    cmp_ = c["compare"]
    if cmp_:
        q = resolve(cmp_)
        cmp_["res_id"] = q["id"] if q else ""
        if not q:
            _warn(f"comparison place '{cmp_['place'] or cmp_['place_en']}' not found in bundled data")
        if p and q:
            cmp_["data_ratio"] = round(p["area_km2"] / q["area_km2"], 3)
            if _diff(cmp_["ratio"], cmp_["data_ratio"]) > TOL:
                _warn(f"narration says '{name}' is {cmp_['ratio']:g}x the size of '{cmp_['place'] or cmp_['place_en']}' "
                      f"but data says {cmp_['data_ratio']:g}x")
    return c


def valid_claim(b: Any) -> bool:
    return claim_of(b) is not None


def pick_mode(c: dict) -> str:
    reg = registry()["places"]
    p = reg.get(c.get("res_id") or "")
    if c.get("compare") and p and reg.get(c["compare"].get("res_id") or ""):
        return "compare"
    if not p:
        return "disc"
    if p["type"] in ("continent", "ocean") or p["area_km2"] > 8e6:
        return "globe"
    if p["area_km2"] < 10000 or p["type"] == "city":
        return "magnifier"
    return "country"


def beat_from_claim(c: dict, title: str = "", fallback: bool = False) -> dict:
    c = check_claim(c)
    b = {"kind": "area_map", "title": title or c["place"] or c["place_en"], "area": c, "mode": pick_mode(c), "camera": "push-in"}
    if fallback:
        b["_fallback"] = True
    return b


def beat_from_raw(raw: dict) -> Optional[dict]:
    """normalize_beat hook: a (possibly already-built) area_map beat -> clean beat, or None if the claim is unusable."""
    c = claim_of(raw)
    if not c:
        return None
    b = beat_from_claim(c, str(raw.get("title") or ""))
    for k in ("layout", "_fallback", "settled"):
        if raw.get(k):
            b[k] = raw[k]
    if raw.get("camera"):
        b["camera"] = raw["camera"]
    return b


# ------------------------------------------------------------------ validator (director output -> enforced beats)
def missing_reasons(scene_id: str, raw_list: list) -> List[str]:
    """Reasons for the one director retry: a sentence carries an area claim but its beat is not area_map."""
    out = []
    for i, rb in enumerate(raw_list):
        if isinstance(rb, dict) and claim_of(rb) and rb.get("kind") != "area_map":
            c = claim_of(rb)
            out.append(f"{scene_id}[{i}] ({rb.get('kind')}): sentence states the area of '{c['place'] or c['place_en']}' "
                       f"-> kind must be \"area_map\" with the same `area` object")
    return out


def fallback_beat(c: dict, scene_id: str, i: int) -> dict:
    """The director (even after its one retry) gave an area sentence a non-area_map beat: build it from the claim,
    flagged `_fallback` so the render shows a visible "عرض احتياطي" tag."""
    fb = beat_from_claim(c, fallback=True)
    record_fallback("area_map_missing_for_area_sentence", beat_id=f"{scene_id}:{i}", beat=fb)
    return fb


def assign_layouts(targets: list) -> None:
    """Rotate layouts across area_map beats; two adjacent beats never share a layout."""
    prev, k = None, 0
    for t in targets:
        for b in t.get("beats") or []:
            if b.get("kind") != "area_map":
                prev = None
                continue
            lay = b.get("layout") if b.get("layout") in LAYOUTS else LAYOUTS[k % len(LAYOUTS)]
            if lay == prev:
                lay = LAYOUTS[(LAYOUTS.index(lay) + 1) % len(LAYOUTS)]
            b["layout"] = prev = lay
            k += 1

# Re-exported so `pipeline.areamap.<name>` keeps working.
from .areamap_view import (  # noqa: E402,F401
    _bbox,
    _centroid,
    _ctx,
    _d,
    _equi,
    _fit,
    _main,
    _orth,
    _paths,
    build_view,
)
