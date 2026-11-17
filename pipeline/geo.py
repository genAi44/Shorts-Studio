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


# ══════════════════════════════════════════════════════════════════════
# GeoEngine — محرك البحث الذكي في geodata.db
# ══════════════════════════════════════════════════════════════════════
class GeoEngine:
    """
    محرك البحث الجغرافي الشامل.
    يدعم البحث متعدد المراحل بكل لغات العالم (عربي، إنجليزي، فرنسي، وغيرها)،
    وحساب الأطر الذكية للخرائط، والبحث القريب، ومعلومات الدول والعواصم.
    """

    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH):
        self.db_path = Path(db_path)
        self._db: Optional[sqlite3.Connection] = None
        self._cache: Dict[str, Optional[GeoPlace]] = {}
        self._country_map: Dict[str, Dict[str, str]] = {}
        if self.db_path.exists():
            self._init_db()

    def _init_db(self):
        self._db = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        cur = self._db.cursor()
        try:
            for row in cur.execute("SELECT iso2, iso3, name_en, name_ar FROM countries").fetchall():
                iso2 = row["iso2"]
                self._country_map[iso2] = {
                    "iso2": iso2,
                    "iso3": row["iso3"] or iso2,
                    "name_en": row["name_en"] or "",
                    "name_ar": row["name_ar"] or "",
                }
        except Exception:
            pass

    def _ensure_db(self) -> bool:
        if self._db is None and self.db_path.exists():
            self._init_db()
        return self._db is not None

    def _row_to_place(self, row: sqlite3.Row, confidence: float = 1.0) -> GeoPlace:
        iso2 = row["country_iso2"] or ""
        cinfo = self._country_map.get(iso2, {})
        keys = row.keys()
        return GeoPlace(
            geoname_id=row["geoname_id"],
            name_en=row["name_en"],
            name_ar=row["name_ar"] if "name_ar" in keys else None,
            name_local=row["name_local"] if "name_local" in keys else None,
            name_ascii=row["name_ascii"] if "name_ascii" in keys else None,
            lat=float(row["lat"]),
            lon=float(row["lon"]),
            country_iso2=iso2,
            country_iso3=cinfo.get("iso3") or iso2,
            country_en=cinfo.get("name_en") or iso2,
            country_ar=cinfo.get("name_ar"),
            admin1_code=row["admin1_code"] if "admin1_code" in keys else None,
            admin1_name_en=row["admin1_name_en"] if "admin1_name_en" in keys else None,
            admin1_name_ar=row["admin1_name_ar"] if "admin1_name_ar" in keys else None,
            admin2_code=row["admin2_code"] if "admin2_code" in keys else None,
            admin2_name_en=row["admin2_name_en"] if "admin2_name_en" in keys else None,
            feature_class=row["feature_class"] if "feature_class" in keys else None,
            feature_code=row["feature_code"] if "feature_code" in keys else None,
            population=int(row["population"] or 0) if "population" in keys else 0,
            elevation=row["elevation"] if "elevation" in keys else None,
            dem=row["dem"] if "dem" in keys else None,
            timezone=row["timezone"] if "timezone" in keys else None,
            is_capital=bool(row["is_capital"]) if "is_capital" in keys else False,
            is_admin_capital=bool(row["is_admin_capital"]) if "is_admin_capital" in keys else False,
            is_historical=bool(row["is_historical"]) if "is_historical" in keys else False,
            source=row["source"] if "source" in keys else "geonames",
            wikidata_id=row["wikidata_id"] if "wikidata_id" in keys else None,
            confidence=confidence,
        )

    def _row_to_country(self, row: sqlite3.Row) -> GeoCountry:
        keys = row.keys()
        return GeoCountry(
            iso2=row["iso2"],
            iso3=row["iso3"] or row["iso2"],
            name_en=row["name_en"],
            name_local=row["name_local"] if "name_local" in keys else None,
            name_ar=row["name_ar"] if "name_ar" in keys else None,
            capital_name_en=row["capital_name_en"] if "capital_name_en" in keys else None,
            capital_geoname_id=row["capital_geoname_id"] if "capital_geoname_id" in keys else None,
            bbox_west=row["bbox_west"] if "bbox_west" in keys else row["bbox_w"] if "bbox_w" in keys else None,
            bbox_south=row["bbox_south"] if "bbox_south" in keys else row["bbox_s"] if "bbox_s" in keys else None,
            bbox_east=row["bbox_east"] if "bbox_east" in keys else row["bbox_e"] if "bbox_e" in keys else None,
            bbox_north=row["bbox_north"] if "bbox_north" in keys else row["bbox_n"] if "bbox_n" in keys else None,
            centroid_lat=row["centroid_lat"] if "centroid_lat" in keys else None,
            centroid_lon=row["centroid_lon"] if "centroid_lon" in keys else None,
            region=row["region"] if "region" in keys else None,
            subregion=row["subregion"] if "subregion" in keys else None,
            continent=row["continent"] if "continent" in keys else None,
            population=int(row["population"] or 0) if "population" in keys else 0,
            area_km2=row["area_km2"] if "area_km2" in keys else None,
            currency_code=row["currency_code"] if "currency_code" in keys else None,
            phone_prefix=row["phone_prefix"] if "phone_prefix" in keys else None,
            languages=row["languages"] if "languages" in keys else None,
            tld=row["tld"] if "tld" in keys else None,
            neighbours=row["neighbours"] if "neighbours" in keys else None,
            geojson_110m=row["geojson_110m"] if "geojson_110m" in keys else None,
            geojson_50m=row["geojson_50m"] if "geojson_50m" in keys else None,
            geojson_10m=row["geojson_10m"] if "geojson_10m" in keys else None,
        )

    # ── مراحل البحث الخمسة ───────────────────────────────────────────
    def _match_exact_ar(
        self,
        q: str,
        iso2: Optional[str],
        feature_codes: Optional[List[str]] = None,
        min_pop: int = 0
    ) -> Optional[GeoPlace]:
        cur = self._db.cursor()
        sql = "SELECT * FROM places WHERE name_ar = ?"
        params: List[Any] = [q]
        if iso2:
            sql += " AND country_iso2 = ?"
            params.append(iso2.upper())
        if feature_codes:
            sql += f" AND feature_code IN ({','.join('?' for _ in feature_codes)})"
            params.extend(feature_codes)
        if min_pop > 0:
            sql += " AND (population >= ? OR is_capital = 1 OR is_historical = 1)"
            params.append(min_pop)
        sql += " ORDER BY is_capital DESC, population DESC LIMIT 1"
        row = cur.execute(sql, params).fetchone()
        return self._row_to_place(row, confidence=1.0) if row else None

    def _match_altname(
        self,
        q: str,
        lang: Optional[str],
        iso2: Optional[str],
        feature_codes: Optional[List[str]] = None,
        min_pop: int = 0
    ) -> Optional[GeoPlace]:
        cur = self._db.cursor()
        sql = """
            SELECT p.* FROM alt_names a
            JOIN places p ON a.geoname_id = p.geoname_id
            WHERE a.name = ?
        """
        params: List[Any] = [q]
        if lang:
            sql += " AND a.lang = ?"
            params.append(lang)
        if iso2:
            sql += " AND p.country_iso2 = ?"
            params.append(iso2.upper())
        if feature_codes:
            sql += f" AND p.feature_code IN ({','.join('?' for _ in feature_codes)})"
            params.extend(feature_codes)
        if min_pop > 0:
            sql += " AND (p.population >= ? OR p.is_capital = 1 OR p.is_historical = 1)"
            params.append(min_pop)
        sql += " ORDER BY a.is_preferred DESC, p.is_capital DESC, p.population DESC LIMIT 1"
        row = cur.execute(sql, params).fetchone()
        return self._row_to_place(row, confidence=0.95) if row else None

    def _match_exact_en(
        self,
        q: str,
        iso2: Optional[str],
        feature_codes: Optional[List[str]] = None,
        min_pop: int = 0
    ) -> Optional[GeoPlace]:
        cur = self._db.cursor()
        sql = "SELECT * FROM places WHERE (name_en = ? COLLATE NOCASE OR name_ascii = ? COLLATE NOCASE OR name_local = ? COLLATE NOCASE)"
        params: List[Any] = [q, q, q]
        if iso2:
            sql += " AND country_iso2 = ?"
            params.append(iso2.upper())
        if feature_codes:
            sql += f" AND feature_code IN ({','.join('?' for _ in feature_codes)})"
            params.extend(feature_codes)
        if min_pop > 0:
            sql += " AND (population >= ? OR is_capital = 1 OR is_historical = 1)"
            params.append(min_pop)
        sql += " ORDER BY is_capital DESC, population DESC LIMIT 1"
        row = cur.execute(sql, params).fetchone()
        return self._row_to_place(row, confidence=0.9) if row else None

    def _match_fts(
        self,
        q: str,
        iso2: Optional[str],
        feature_codes: Optional[List[str]] = None,
        min_pop: int = 0
    ) -> Optional[GeoPlace]:
        cur = self._db.cursor()
        clean_q = re.sub(r"[^\w\s]", " ", q).strip()
        if not clean_q:
            return None
        sql = """
            SELECT p.* FROM places_fts f
            JOIN places p ON f.geoname_id = p.geoname_id
            WHERE places_fts MATCH ?
        """
        params: List[Any] = [f'"{clean_q}"']
        if iso2:
            sql += " AND p.country_iso2 = ?"
            params.append(iso2.upper())
        if feature_codes:
            sql += f" AND p.feature_code IN ({','.join('?' for _ in feature_codes)})"
            params.extend(feature_codes)
        if min_pop > 0:
            sql += " AND (p.population >= ? OR p.is_capital = 1 OR p.is_historical = 1)"
            params.append(min_pop)
        sql += " ORDER BY rank, p.is_capital DESC, p.population DESC LIMIT 1"
        try:
            row = cur.execute(sql, params).fetchone()
            return self._row_to_place(row, confidence=0.85) if row else None
        except Exception:
            return None

    def _fallback_nominatim(self, q: str, iso2: Optional[str]) -> Optional[GeoPlace]:
        try:
            params: Dict[str, Any] = {"q": q, "format": "json", "limit": 1}
            if iso2:
                params["countrycodes"] = iso2.lower()
            resp = requests.get(
                "https://nominatim.openstreetmap.org/search",
                params=params,
                headers={"User-Agent": "ShortsStudioBot/1.0 (GIS; contact@example.com)"},
                timeout=5,
            )
            if resp.status_code == 200:
                data = resp.json()
                if data:
                    item = data[0]
                    return GeoPlace(
                        geoname_id=int(item.get("osm_id", -9999)),
                        name_en=item.get("name") or q,
                        name_ar=q if re.search(r"[\u0600-\u06FF]", q) else None,
                        name_local=item.get("display_name"),
                        lat=float(item["lat"]),
                        lon=float(item["lon"]),
                        country_iso2=iso2 or "",
                        country_iso3=iso2 or "",
                        country_en=iso2 or "",
                        source="nominatim",
                        confidence=0.75,
                    )
        except Exception:
            pass
        return None

    # ── الواجهة البرمجية العامة لمحرك الجغرافيا ────────────────────────
    def resolve(
        self,
        query: str,
        country_iso2: Optional[str] = None,
        lang: Optional[str] = None,
        feature_codes: Optional[List[str]] = None,
        min_pop: int = 0,
        allow_network: bool = False
    ) -> Optional[GeoPlace]:
        """
        بحث متعدد المراحل يدعم كل لغات العالم:
        1. مطابقة تامة في alt_names (أي لغة أو اللغة المحددة)
        2. مطابقة تامة في name_ar
        3. مطابقة تامة في name_en / name_ascii / name_local
        4. FTS5 fuzzy (يتجاهل التشكيل والهجاء المختلف)
        5. Nominatim API كاحتياطي شبكي
        """
        q = query.strip()
        if not q:
            return None
        cache_key = f"{q}|{country_iso2 or ''}|{lang or ''}|{min_pop}|{allow_network}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        if not self._ensure_db():
            res = self._fallback_nominatim(q, country_iso2) if allow_network else None
            self._cache[cache_key] = res
            return res

        result = (
            self._match_exact_ar(q, country_iso2, feature_codes, min_pop) or
            self._match_altname(q, lang, country_iso2, feature_codes, min_pop) or
            self._match_altname(q, "ar", country_iso2, feature_codes, min_pop) or
            self._match_exact_en(q, country_iso2, feature_codes, min_pop) or
            self._match_fts(q, country_iso2, feature_codes, min_pop)
        )

        if not result and re.search(r"[\u0600-\u06FF]", q):
            # محاولة البحث مع تطبيع الهمزات (إ / أ / آ -> ا)
            norm_q = re.sub(r"[إأآ]", "ا", q)
            if norm_q != q:
                result = (
                    self._match_exact_ar(norm_q, country_iso2, feature_codes, min_pop) or
                    self._match_altname(norm_q, "ar", country_iso2, feature_codes, min_pop) or
                    self._match_fts(norm_q, country_iso2, feature_codes, min_pop)
                )

        if not result and allow_network:
            result = self._fallback_nominatim(q, country_iso2)

        self._cache[cache_key] = result
        return result

    def resolve_all(
        self,
        queries: List[str],
        country_iso2: Optional[str] = None
    ) -> List[GeoPlace]:
        """يحل قائمة أسماء دفعة واحدة بكفاءة (مثال: ['فاس', 'مراكش', 'سلا', 'مكناس'])."""
        results: List[GeoPlace] = []
        for q in queries:
            p = self.resolve(q, country_iso2=country_iso2)
            if p:
                results.append(p)
        return results

    def get_country(self, iso2_or_iso3: str) -> Optional[GeoCountry]:
        """
        جلب بيانات دولة كاملة.
        يقبل: 'MA' أو 'MAR' أو 'Morocco' أو 'المغرب'
        """
        if not self._ensure_db():
            return None
        q = iso2_or_iso3.strip()
        cur = self._db.cursor()
        sql = """
            SELECT * FROM countries
            WHERE iso2 = ? COLLATE NOCASE
               OR iso3 = ? COLLATE NOCASE
               OR name_en = ? COLLATE NOCASE
               OR name_local = ? COLLATE NOCASE
               OR name_ar = ?
            LIMIT 1
        """
        row = cur.execute(sql, [q, q, q, q, q]).fetchone()
        return self._row_to_country(row) if row else None

    def get_capital(self, country_iso2: str) -> Optional[GeoPlace]:
        """عاصمة دولة مباشرة."""
        if not self._ensure_db():
            return None
        cur = self._db.cursor()
        sql = "SELECT * FROM places WHERE country_iso2 = ? AND is_capital = 1 ORDER BY population DESC LIMIT 1"
        row = cur.execute(sql, [country_iso2.strip().upper()]).fetchone()
        return self._row_to_place(row) if row else None

    def get_all_capitals(self) -> List[GeoPlace]:
        """كل عواصم دول العالم (195+)."""
        if not self._ensure_db():
            return []
        cur = self._db.cursor()
        sql = "SELECT * FROM places WHERE is_capital = 1 ORDER BY name_en"
        rows = cur.execute(sql).fetchall()
        return [self._row_to_place(r) for r in rows]

    def get_cities_in_country(
        self,
        country_iso2: str,
        min_pop: int = 100000,
        limit: int = 50
    ) -> List[GeoPlace]:
        """أكبر مدن دولة معينة مرتبة بالسكان."""
        if not self._ensure_db():
            return []
        cur = self._db.cursor()
        sql = """
            SELECT * FROM places
            WHERE country_iso2 = ? AND population >= ?
            ORDER BY population DESC
            LIMIT ?
        """
        rows = cur.execute(sql, [country_iso2.strip().upper(), min_pop, limit]).fetchall()
        return [self._row_to_place(r) for r in rows]

    def get_smart_bbox(
        self,
        places: List[GeoPlace],
        canvas_w: int = 1080,
        canvas_h: int = 1920,
        headline_zone_px: int = 280,
        padding_ratio: float = 0.25
    ) -> MapBBox:
        """
        bbox ذكي يضمن:
        - كل الأماكن ظاهرة
        - لا دبابيس في HEADLINE_ZONE (أعلى 280px)
        - padding يتكيف مع حجم الدولة
        - يُنزّل الخريطة إذا المدن شمالية
        """
        if not places:
            return MapBBox(west=-180, east=180, south=-90, north=90, center_lat=0, center_lon=0)

        lats = [p.lat for p in places]
        lons = [p.lon for p in places]

        span_lat = max(max(lats) - min(lats), 0.5)
        span_lon = max(max(lons) - min(lons), 0.5)

        pad_lat = max(span_lat * padding_ratio, 0.4)
        pad_lon = max(span_lon * padding_ratio, 0.4)

        raw_bbox = BBox(
            west=min(lons) - pad_lon,
            east=max(lons) + pad_lon,
            south=min(lats) - pad_lat,
            north=max(lats) + pad_lat
        )

        headline_ratio = headline_zone_px / canvas_h
        lat_range = max(raw_bbox.north - raw_bbox.south, 1.2)
        north_headroom = lat_range * headline_ratio * 1.6

        return MapBBox(
            west=raw_bbox.west,
            east=raw_bbox.east,
            south=raw_bbox.south,
            north=raw_bbox.north + north_headroom,
            center_lat=raw_bbox.south + (lat_range / 2),
            center_lon=(raw_bbox.west + raw_bbox.east) / 2,
            headline_safe=True
        )

    def search_nearby(
        self,
        lat: float,
        lon: float,
        radius_km: float = 100,
        limit: int = 10
    ) -> List[GeoPlace]:
        """أماكن قريبة من إحداثيات معينة عبر حساب مسافة Haversine التقريبية."""
        if not self._ensure_db():
            return []
        delta_lat = radius_km / 111.0
        delta_lon = radius_km / max(111.0 * math.cos(math.radians(lat)), 1.0)
        cur = self._db.cursor()
        sql = """
            SELECT * FROM places
            WHERE lat BETWEEN ? AND ?
              AND lon BETWEEN ? AND ?
            LIMIT 200
        """
        rows = cur.execute(sql, [lat - delta_lat, lat + delta_lat, lon - delta_lon, lon + delta_lon]).fetchall()
        places_dist = []
        for r in rows:
            p_lat, p_lon = float(r["lat"]), float(r["lon"])
            # مسافة Haversine
            d_lat = math.radians(p_lat - lat)
            d_lon = math.radians(p_lon - lon)
            a = math.sin(d_lat / 2) ** 2 + math.cos(math.radians(lat)) * math.cos(math.radians(p_lat)) * math.sin(d_lon / 2) ** 2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            dist_km = 6371.0 * c
            if dist_km <= radius_km:
                places_dist.append((dist_km, r))

        places_dist.sort(key=lambda x: x[0])
        return [self._row_to_place(r) for _, r in places_dist[:limit]]


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


# ══════════════════════════════════════════════════════════════════════
# دوال التوافق ومطابقة النصوص الحية عبر محرك البحث الجغرافي
# ══════════════════════════════════════════════════════════════════════
# كلمات شائعة وأرقام واختصارات زمنية يجب ألا تعامل كأسماء مدن
_CITY_STOP_WORDS = {
    "في", "من", "إلى", "الى", "على", "عن", "مع", "أن", "إن", "قد", "كان", "كانت", "يكون",
    "أو", "ثم", "بل", "لا", "لن", "لم", "ما", "هذا", "هذه", "تلك", "ذلك", "هنا",
    "هناك", "سر", "السر", "بداية", "نهاية", "نقطة", "يوم", "اليوم", "يوما", "يوماً", "أيام", "الأيام",
    "ساعة", "لحظة", "ثانية", "دقيقة", "عام", "سنة", "قرن", "القرن", "قارة", "قارات", "القارات",
    "وجه", "الأرض", "اللقب", "المنافسة", "تتنافس", "ساحرة", "تأسر", "القلوب",
    "حرب", "الحرب", "ملك", "سلطان", "مدينة", "المدينة", "مدينتين", "المدينتين", "مدن", "المدن",
    "عاصمة", "العاصمة", "عاصمتين", "العاصمتين", "عاصمتان", "عواصم", "العواصم", "دولة", "الدولة",
    "دول", "الدول", "بلد", "البلد", "بلاد", "البلاد", "بلدان", "شعب", "الشعب", "شعوب",
    "عالم", "العالم", "مركز", "المركز", "الحكم", "حكم", "الأولى", "الثانية", "الثالثة",
    "شمال", "الشمال", "جنوب", "الجنوب", "شرق", "الشرق", "غرب", "الغرب", "وسط", "الوسط",
    "بحري", "البحري", "سقوط", "تحرير", "إنزال", "إحصائيات", "ضحايا", "مليون", "مليار",
    "قلب", "القلب", "جزيرة", "الجزيرة", "جزر", "الجزر", "ساحل", "الساحل", "جبل", "الجبل",
    "جبال", "الجبال", "نهر", "النهر", "بحر", "البحر", "محيط", "المحيط", "وادي", "الوادي",
    "صحراء", "الصحراء", "غابة", "الغابة", "قمة", "القمة", "أعلى", "الأعلى", "أدنى",
    "سلطة", "السلطة", "حكومة", "الحكومة", "برلمان", "البرلمان", "رئيس", "الرئيس",
    "قضاء", "القضاء", "دستور", "الدستور", "دستوري", "دستورية", "تاريخي", "تاريخية",
    "ثورة", "الثورة", "ثورات", "الثورات", "تاج", "التاج", "إسباني", "الإسباني",
    "استقلال", "الاستقلال", "تاريخ", "التاريخ", "حقيقة", "الحقيقة", "مفاجأة", "المفاجأة",
    "غريب", "الغريب", "عجيب", "العجيب", "تعلم", "هل", "أكبر", "أصغر", "أغنى", "أفقر",
    "أول", "أولى", "ثاني", "ثانية", "ثالث", "ثالثة", "آخر", "جديد", "الجديد", "قديم", "القديم",
    "القديمة", "الحديثة",
    # الأعداد والأرقام بالعربية لمنع تطابق مثل "ألفين" مع مدينة Alvin الأمريكية أو "الخمس" مع الخمس الليبية
    "صفر", "واحد", "واحدة", "الواحد", "الواحدة", "اثنين", "اثنان", "الاثنين", "الاثنان", "اثنتين", "اثنتان", "الاثنتين", "الاثنتان", "اثني", "اثنتي",
    "ثلاث", "ثلاثة", "الثلاث", "الثلاثة", "أربع", "أربعة", "الأربع", "الأربعة", "خمس", "خمسة", "الخمس", "الخمسة", "ست", "ستة", "الست", "الستة", "سبع", "سبعة", "السبع", "السبعة",
    "ثمان", "ثماني", "ثمانية", "الثمان", "الثماني", "الثمانية", "تسع", "تسعة", "التسع", "التسعة", "عشر", "عشرة", "العشر", "العشرة",
    "عشرين", "عشرون", "العشرين", "العشرون", "ثلاثين", "ثلاثون", "الثلاثين", "الثلاثون", "أربعين", "أربعون", "الأربعين", "الأربعون", "خمسين", "خمسون", "الخمسين", "الخمسون",
    "ستين", "ستون", "سبعين", "سبعون", "ثمانين", "ثمانون", "تسعين", "تسعون",
    "مئة", "مائة", "المئة", "المائة", "مئتين", "مائتين", "مئات", "ثلاثمئة", "أربعمئة", "خمسمئة",
    "ستمئة", "سبعمئة", "ثمانمئة", "تسعمئة", "ألف", "ألفين", "ألفان", "آلاف", "الألف", "الآلاف",
    "مليون", "مليونين", "ملايين", "المليون", "الملايين", "مليار", "مليارات",
    "الأكبر", "الأصغر", "الأعلى", "الأدنى", "الأشهر", "الأقدم", "الأحدث", "الأهم", "الأقوى", "الأغنى", "الأفقر", "الأصلية", "الأصلي",
    "كيف", "لماذا", "متى", "أين", "كم", "كل", "جميع", "بعض", "أكثر", "أقل", "نحو",
    "حتى", "بين", "بينما", "فوق", "تحت", "أمام", "خلف", "حول", "دون", "غير", "سوى", "فقط",
    "الذي", "التي", "الذين", "اللواتي", "اللائي", "إذا", "لو", "لولا", "لعل", "ليت",
    "أمريكا", "الجنوبية", "الشمالية", "أوروبا", "آسيا", "أفريقيا", "إفريقيا", "أستراليا",
    "العربي", "العربية", "الإسلامي", "الإسلامية", "الدور", "الإداري", "الثقل", "الحضاري",
    "السياسي", "الاقتصادي", "التشريعي", "التنفيذي", "التنفيذية", "القضائي", "القضائية",
    "الرسمية", "الفعلي", "رسمياً", "فعلياً", "رسميتين", "بدلا", "ثواني", "الثواني",
    "القادمة", "ستكتشف", "المثير", "شهدت", "ضد", "تجمع", "تملك", "يمتلك", "تمتلك",
    "تقع", "يقع", "تعد", "يعد", "أقر", "بقاء", "شؤون", "تدير", "تظل", "يبقى", "تبقى",
    "كامل", "بالكامل", "انقسام", "الانقسام", "صراع", "الصراع", "مقر", "المقر",
    # اختصارات تاريخية وزمنية تمنع الخلط مع أسماء مدن مثل 'قم' الإيرانية أو 'صور' أو 'العين'
    "قم", "ق م", "م", "هـ", "ميلادي", "هجري", "قبل", "بعد", "فترة", "عصور",
    "عين", "العين", "صور", "الصور", "بيان", "البيان", "سلام", "السلام", "أمل", "الأمل",
    "نور", "النور", "فجر", "الفجر", "نصر", "النصر", "عهد", "العهد", "مجد", "المجد",
    "دول", "دولا", "دولة", "الدول", "الدولة", "جيش", "جيشا", "جيشها", "جيوش", "جيوشا",
    "شعب", "شعبا", "شعوب", "شعوبا", "شعوبها", "عالم", "العالم", "أمان", "أمانا", "امان",
    "عام", "سنة", "سنويا", "ممر", "فوق", "تحت", "بين", "تدر", "أعلى", "اكبر", "أكبر",
    "تعيش", "بدون", "قوات", "مسلحة", "تعتمد", "تحميها", "لاتينية", "اللاتينية", "الوسطى",
    "أمريكا", "امريكا", "اروبا", "أوروبا", "آسيا", "افريقيا", "أفريقيا",
}


def detect_city_in_text(text: str) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """
    يكتشف ما إذا كان النص يذكر مدينة أو عاصمة ويبحث عنها فوراً في geodata.db.
    يعيد (اسم_المدينة_بالعربية, قاموس_المعلومات_الجغرافية).
    """
    if not text:
        return None, None
    engine = get_engine()
    _STOP_WORDS = _CITY_STOP_WORDS

    # استخراج الكلمات والتراكيب المحتملة (1 إلى 2 كلمة)
    raw_words = [re.sub(r"[^\w]", "", w) for w in text.split()]
    raw_words = [w for w in raw_words if w and len(w) >= 2]

    cands: List[str] = []
    for i in range(len(raw_words) - 1):
        w1, w2 = raw_words[i], raw_words[i + 1]
        bigram = f"{w1} {w2}"
        if bigram == "المدينة المنورة":
            cands.append(bigram)
        elif w1 not in _STOP_WORDS and w2 not in _STOP_WORDS:
            cands.append(bigram)
    for w in raw_words:
        if w not in _STOP_WORDS:
            cands.append(w)
            if len(w) >= 5 and w[0] in ("و", "ب", "ل", "ف") and w[1:] not in _STOP_WORDS:
                cands.append(w[1:])

    if not hasattr(detect_city_in_text, "_cand_cache"):
        detect_city_in_text._cand_cache = {}
    cand_cache = detect_city_in_text._cand_cache

    matched_candidates: List[Tuple[Tuple[int, int, int, int], str, Dict[str, Any]]] = []

    for cand in cands:
        if cand in cand_cache:
            cached_info = cand_cache[cand]
            if cached_info is not None:
                rank_key = (
                    int(bool(cached_info.get("is_capital"))),
                    int(cached_info.get("feature_code") == "PPLC"),
                    int(bool(cached_info.get("is_historical"))),
                    int(cached_info.get("population") or 0),
                )
                matched_candidates.append((rank_key, cand, cached_info))
            continue

        if cand in AR_ISO3:
            cand_cache[cand] = None
            continue

        is_ar = bool(re.search(r"[\u0600-\u06FF]", cand))
        if is_ar:
            place = (
                engine._match_exact_ar(cand, None) or
                engine._match_altname(cand, "ar", None)
            )
        else:
            place = engine._match_exact_en(cand, None)

        if place and (
            place.is_capital
            or place.is_historical
            or place.feature_code == "PPLC"
            or (place.feature_code in ("PPLA", "PPLA2", "PPLG") and (place.population or 0) >= 50000)
            or (place.feature_code in ("PPL", "PPLX", "ADM1") and (place.population or 0) >= 100000)
        ):
            city_name = place.name_ar or place.name_en
            info = {
                "name": city_name,
                "en": place.name_en,
                "iso": place.country_iso3 or place.country_iso2,
                "iso2": place.country_iso2,
                "lat": place.lat,
                "lon": place.lon,
                "country": place.country_en or place.country_iso2,
                "is_capital": place.is_capital,
                "is_historical": place.is_historical,
                "feature_code": place.feature_code,
                "population": place.population or 0,
            }
            cand_cache[cand] = info
            rank_key = (
                int(bool(place.is_capital)),
                int(place.feature_code == "PPLC"),
                int(bool(place.is_historical)),
                int(place.population or 0),
            )
            matched_candidates.append((rank_key, cand, info))
        else:
            cand_cache[cand] = None

    if matched_candidates:
        matched_candidates.sort(key=lambda item: item[0], reverse=True)
        _, best_cand, best_info = matched_candidates[0]
        return best_cand, best_info

    return None, None


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
