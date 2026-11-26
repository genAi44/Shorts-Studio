"""Split from `pipeline/geo.py` (re-exported there); see that module."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from pathlib import Path
import math
import re
import requests
import sqlite3
from .geo import BBox, DEFAULT_DB_PATH, GeoCountry, GeoPlace, MapBBox  # noqa: E402


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
