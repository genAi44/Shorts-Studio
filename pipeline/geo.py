"""
pipeline/geo.py
محرك الجغرافيا الشامل:
1. GeoEngine: محرك البحث الذكي في قاعدة البيانات الرسمية geodata.db عبر FTS5 و Wikidata والأسماء البديلة بكل اللغات.
2. Geo: إدارة حدود الدول (GeoJSON) وحساب أطر العرض وإسقاطات الكاميرا للرندرة.
"""

from __future__ import annotations
from dataclasses import dataclass
import json
import math
from pathlib import Path
import re
import sqlite3
import threading
from typing import Any, Dict, List, Optional, Tuple

import requests

from .config import GEO, ROOT

_lock = threading.Lock()
_geo = None
_engine = None

DEFAULT_DB_PATH = ROOT / "data" / "geodata.db"


@dataclass
class GeoPlace:
    geoname_id: int
    name_en: str
    name_ar: Optional[str] = None
    name_local: Optional[str] = None
    name_ascii: Optional[str] = None
    lat: float = 0.0
    lon: float = 0.0
    country_iso2: str = ""
    country_iso3: Optional[str] = None
    country_en: Optional[str] = None
    country_ar: Optional[str] = None
    admin1_code: Optional[str] = None
    admin1_name_en: Optional[str] = None
    admin1_name_ar: Optional[str] = None
    admin2_code: Optional[str] = None
    admin2_name_en: Optional[str] = None
    feature_class: Optional[str] = None
    feature_code: Optional[str] = None
    population: int = 0
    elevation: Optional[int] = None
    dem: Optional[int] = None
    timezone: Optional[str] = None
    is_capital: bool = False
    is_admin_capital: bool = False
    is_historical: bool = False
    source: str = "geonames"
    wikidata_id: Optional[str] = None
    confidence: float = 1.0


@dataclass
class GeoCountry:
    iso2: str
    iso3: str
    name_en: str
    name_local: Optional[str] = None
    name_ar: Optional[str] = None
    capital_name_en: Optional[str] = None
    capital_geoname_id: Optional[int] = None
    bbox_west: Optional[float] = None
    bbox_south: Optional[float] = None
    bbox_east: Optional[float] = None
    bbox_north: Optional[float] = None
    centroid_lat: Optional[float] = None
    centroid_lon: Optional[float] = None
    region: Optional[str] = None
    subregion: Optional[str] = None
    continent: Optional[str] = None
    population: int = 0
    area_km2: Optional[float] = None
    currency_code: Optional[str] = None
    phone_prefix: Optional[str] = None
    languages: Optional[str] = None
    tld: Optional[str] = None
    neighbours: Optional[str] = None
    geojson_110m: Optional[str] = None
    geojson_50m: Optional[str] = None
    geojson_10m: Optional[str] = None


@dataclass
class BBox:
    west: float
    south: float
    east: float
    north: float


@dataclass
class MapBBox:
    west: float
    east: float
    south: float
    north: float
    center_lat: float
    center_lon: float
    headline_safe: bool = True


def get_engine() -> GeoEngine:
    global _engine
    with _lock:
        if _engine is None:
            _engine = GeoEngine()
        return _engine


# ══════════════════════════════════════════════════════════════════════
# Geo — إدارة إسقاطات الخرائط لرندرة الفيديو (Remotion Engine)
# ══════════════════════════════════════════════════════════════════════
# أطر العرض الجغرافية المعتمدة للدول ذات الجزر المتعددة أو الأقاليم البعيدة لضمان ظهور كامل أراضي الدولة دون اقتصاص
_MAINLAND_BBOX_OVERRIDES: Dict[str, Tuple[float, float, float, float]] = {
    "FRA": (-5.2, 41.3, 9.6, 51.1),      # فرنسا القارية + كورسيكا
    "USA": (-125.0, 24.5, -66.9, 49.4),  # الولايات المتحدة القارية المتصلة (من المحيط للأطلسي مع واشنطن)
    "JPN": (129.5, 31.0, 145.8, 45.6),   # أرخبيل اليابان الكامل (هوكايدو، هونشو، شيكوكو، كيوشو)
    "EGY": (24.7, 22.0, 36.9, 31.7),     # مصر كاملة مع شبه جزيرة سيناء وساحل البحر الأحمر
    "BRA": (-74.0, -33.8, -34.8, 5.3),   # البرازيل كاملة
    "GBR": (-8.2, 49.9, 1.8, 58.7),      # المملكة المتحدة كاملة
    "ESP": (-9.3, 36.0, 4.3, 43.8),      # إسبانيا القارية + جزر البليار
    "PRT": (-9.5, 36.9, -6.2, 42.2),     # البرتغال القارية
    "ITA": (6.6, 36.6, 18.5, 47.1),      # إيطاليا + صقلية + سردينيا
    "NLD": (3.3, 50.7, 7.2, 53.5),       # هولندا الأوروبية
    "DNK": (8.0, 54.5, 12.7, 57.8),      # الدنمارك
    "GRC": (19.4, 34.8, 28.3, 41.8),     # اليونان + كريت
    "TUR": (26.0, 35.8, 44.8, 42.1),     # تركيا بشقيها الآسيوي والأوروبي
    "IDN": (95.0, -11.0, 141.0, 6.0),    # إندونيسيا
    "PHL": (117.0, 5.5, 126.6, 18.6),    # الفلبين
    "MYS": (100.0, 1.2, 119.3, 7.4),     # ماليزيا
    "RUS": (27.0, 41.2, 180.0, 77.7),    # روسيا
}


class Geo:
    def __init__(self, path):
        self.c = {}
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        for feat in d["features"]:
            p = feat["properties"]
            iso = p.get("ISO3166-1-Alpha-3") or p.get("ISO_A3") or ""
            if len(iso) != 3 or not iso.isalpha():
                continue
            g = feat["geometry"]
            polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
            bbs = []
            for poly in polys:
                xs = [pt[0] for pt in poly[0]]
                ys = [pt[1] for pt in poly[0]]
                bbs.append((min(xs), min(ys), max(xs), max(ys)))
            self.c[iso] = {"name": p.get("name", iso), "polys": polys, "bbs": bbs}

    def has(self, iso):
        return iso in self.c

    def main_bbox(self, iso):
        if iso in _MAINLAND_BBOX_OVERRIDES:
            return _MAINLAND_BBOX_OVERRIDES[iso]
        bbs = self.c[iso]["bbs"]
        primary = max(bbs, key=lambda b: (b[2] - b[0]) * (b[3] - b[1]))
        if len(bbs) == 1:
            return primary
        pcx = (primary[0] + primary[2]) / 2.0
        pcy = (primary[1] + primary[3]) / 2.0
        pw = max(primary[2] - primary[0], 4.0)
        ph = max(primary[3] - primary[1], 4.0)
        near = [
            b for b in bbs
            if abs((b[0] + b[2]) / 2.0 - pcx) <= pw * 1.15
            and abs((b[1] + b[3]) / 2.0 - pcy) <= ph * 1.15
        ]
        if not near:
            return primary
        return (
            min(b[0] for b in near),
            min(b[1] for b in near),
            max(b[2] for b in near),
            max(b[3] for b in near),
        )

    def view_for(self, isos, points, bw=1000, bh=860, smax=420, pad=0.1):
        boxes = [self.main_bbox(i) for i in isos if i in self.c]
        boxes += [(p["lon"], p["lat"], p["lon"], p["lat"]) for p in points]
        if not boxes:
            boxes = [(-25, -35, 60, 38)]
        x0 = min(b[0] for b in boxes)
        y0 = min(b[1] for b in boxes)
        x1 = max(b[2] for b in boxes)
        y1 = max(b[3] for b in boxes)
        dx, dy = max(x1 - x0, 1.5), max(y1 - y0, 1.5)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        x0, x1 = cx - dx / 2 * (1 + 2 * pad), cx + dx / 2 * (1 + 2 * pad)
        y0, y1 = cy - dy / 2 * (1 + 2 * pad), cy + dy / 2 * (1 + 2 * pad)
        k = math.cos(math.radians(cy))
        s = min(bw / ((x1 - x0) * k), bh / (y1 - y0), smax)
        return {"lonc": cx, "latc": cy, "K": k, "S": s}


def get_geo():
    global _geo
    with _lock:
        if _geo is None:
            _geo = Geo(GEO)
        return _geo


# قاموس ديناميكي للبلدان والآيزو
class _DynamicCountryMapping(dict):
    def __init__(self, key_type: str = "ar_to_iso3"):
        super().__init__()
        self.key_type = key_type
        self._loaded = False

    def _ensure(self):
        if not self._loaded:
            engine = get_engine()
            if engine._ensure_db():
                try:
                    cur = engine._db.cursor()
                    rows = cur.execute("SELECT iso2, iso3, name_en, name_ar FROM countries").fetchall()
                    for r in rows:
                        i2, i3, n_en, n_ar = r["iso2"], r["iso3"] or r["iso2"], r["name_en"], r["name_ar"]
                        if self.key_type == "ar_to_iso3":
                            if n_ar:
                                self[n_ar] = i3
                            if n_en:
                                self[n_en] = i3
                            self[i2] = i3
                            self[i3] = i3
                        elif self.key_type == "iso3_to_en":
                            self[i3] = n_en
                            self[i2] = n_en
                    self._loaded = True
                except Exception:
                    pass

    def __getitem__(self, item):
        self._ensure()
        return super().__getitem__(item)

    def get(self, item, default=None):
        self._ensure()
        return super().get(item, default)

    def __contains__(self, item):
        self._ensure()
        return super().__contains__(item)

    def __iter__(self):
        self._ensure()
        return super().__iter__()

    def __len__(self):
        self._ensure()
        return super().__len__()

    def items(self):
        self._ensure()
        return super().items()

    def keys(self):
        self._ensure()
        return super().keys()

    def values(self):
        self._ensure()
        return super().values()


AR_ISO3 = _DynamicCountryMapping("ar_to_iso3")
ISO3_TO_COUNTRY_EN = _DynamicCountryMapping("iso3_to_en")


class _DynamicWorldCities(dict):
    """واجهة متوافقة لقاعدة المدن تسحب تلقائياً من geodata.db."""
    def __init__(self):
        super().__init__()

    def __contains__(self, key):
        engine = get_engine()
        return engine.resolve(key) is not None

    def get(self, key, default=None):
        engine = get_engine()
        p = engine.resolve(key)
        if p:
            return {
                "name": p.name_ar or p.name_en,
                "en": p.name_en,
                "iso": p.country_iso3 or p.country_iso2,
                "iso2": p.country_iso2,
                "lat": p.lat,
                "lon": p.lon,
                "country": p.country_en or p.country_iso2,
                "is_capital": p.is_capital,
                "is_historical": p.is_historical,
            }
        return default

    def __getitem__(self, key):
        v = self.get(key)
        if v is None:
            raise KeyError(key)
        return v


WORLD_CITIES = _DynamicWorldCities()

# Re-exported so `pipeline.geo.<name>` keeps working.
from .geo_city import (  # noqa: E402,F401
    _CITY_STOP_WORDS,
    detect_city_in_text,
)

# Re-exported so `pipeline.geo.<name>` keeps working.
from .geo_engine import (  # noqa: E402,F401
    GeoEngine,
)
