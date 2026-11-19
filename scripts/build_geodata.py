#!/usr/bin/env python3
"""
scripts/build_geodata.py
بناء قاعدة بيانات جغرافية عالمية شاملة تلقائياً من مصادر مفتوحة رسمية:
1. GeoNames: مدن العالم (+70,000)، معلومات 252 دولة، تقسيمات إدارية، والأسماء البديلة بكل اللغات.
2. Natural Earth: حدود الدول (GeoJSON بدقة 110m, 50m, 10m)، سواحل، بحيرات، وأنهار.
3. Wikidata SPARQL: المدن والعواصم التاريخية، الحضارات القديمة، طريق الحرير، واليونسكو.
"""

from __future__ import annotations
import argparse
from dataclasses import dataclass
from datetime import datetime
import io
import json
from pathlib import Path
import re
import sqlite3
import sys
import time
from typing import Any, Dict, List, Optional, Set
import zipfile

import requests
import shapefile
from tqdm import tqdm

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)

# ══════════════════════════════════════════════════════════════════════
# STEP 1 — مصادر البيانات الرسمية
# ══════════════════════════════════════════════════════════════════════
SOURCES: Dict[str, Dict[str, Any]] = {
    # ── GeoNames ──────────────────────────────────────
    "geonames_15k": {
        "url": "https://download.geonames.org/export/dump/cities15000.zip",
        "desc": "مدن +15,000 ساكن (~25,000 مكان)",
        "default": False,
    },
    "geonames_5k": {
        "url": "https://download.geonames.org/export/dump/cities5000.zip",
        "desc": "مدن +5,000 ساكن (~55,000 مكان)",
        "default": True,
    },
    "geonames_1k": {
        "url": "https://download.geonames.org/export/dump/cities1000.zip",
        "desc": "مدن +1,000 ساكن (~140,000 مكان)",
        "default": False,
    },
    "geonames_all": {
        "url": "https://download.geonames.org/export/dump/allCountries.zip",
        "desc": "كل الأماكن الجغرافية (~12 مليون سجل)",
        "default": False,
    },
    # الأسماء البديلة بكل لغات العالم (عربي، فرنسي، صيني...)
    "geonames_altnames": {
        "url": "https://download.geonames.org/export/dump/alternateNamesV2.zip",
        "desc": "أسماء بديلة بكل اللغات (~16 مليون سجل)",
        "default": True,
    },
    # معلومات الدول (عواصم + ISO2 + ISO3 + bbox + لغات)
    "geonames_countries": {
        "url": "https://download.geonames.org/export/dump/countryInfo.txt",
        "desc": "بيانات 252 دولة",
        "default": True,
    },
    # تقسيمات إدارية (مناطق + ولايات + محافظات)
    "geonames_admin1": {
        "url": "https://download.geonames.org/export/dump/admin1CodesASCII.txt",
        "desc": "المناطق الإدارية المستوى الأول",
        "default": True,
    },
    "geonames_admin2": {
        "url": "https://download.geonames.org/export/dump/admin2Codes.txt",
        "desc": "المناطق الإدارية المستوى الثاني",
        "default": True,
    },
    # ── Natural Earth ──────────────────────────────────
    "ne_countries_110m": {
        "url": "https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip",
        "desc": "حدود الدول — دقة منخفضة (للعرض البعيد)",
        "default": True,
    },
    "ne_countries_50m": {
        "url": "https://naciscdn.org/naturalearth/50m/cultural/ne_50m_admin_0_countries.zip",
        "desc": "حدود الدول — دقة متوسطة (للفيديو) ← موصى به",
        "default": True,
    },
    "ne_countries_10m": {
        "url": "https://naciscdn.org/naturalearth/10m/cultural/ne_10m_admin_0_countries.zip",
        "desc": "حدود الدول — دقة عالية (للتفاصيل)",
        "default": False,
    },
    "ne_places_10m": {
        "url": "https://naciscdn.org/naturalearth/10m/cultural/ne_10m_populated_places.zip",
        "desc": "مدن Natural Earth تفصيلية",
        "default": False,
    },
    "ne_places_50m": {
        "url": "https://naciscdn.org/naturalearth/50m/cultural/ne_50m_populated_places.zip",
        "desc": "مدن Natural Earth متوسطة",
        "default": True,
    },
    "ne_coastline_50m": {
        "url": "https://naciscdn.org/naturalearth/50m/physical/ne_50m_coastline.zip",
        "desc": "خطوط السواحل",
        "default": True,
    },
    "ne_lakes_50m": {
        "url": "https://naciscdn.org/naturalearth/50m/physical/ne_50m_lakes.zip",
        "desc": "البحيرات الكبرى",
        "default": True,
    },
    "ne_rivers_50m": {
        "url": "https://naciscdn.org/naturalearth/50m/physical/ne_50m_rivers_lake_centerlines.zip",
        "desc": "الأنهار الرئيسية",
        "default": True,
    },
}

# ══════════════════════════════════════════════════════════════════════
# STEP 2 — بنية قاعدة البيانات (SQLite Schema)
# ══════════════════════════════════════════════════════════════════════
SCHEMA = """
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;

-- جدول الدول (252 دولة + إقليم)
CREATE TABLE IF NOT EXISTS countries (
    iso2              TEXT PRIMARY KEY,
    iso3              TEXT UNIQUE,
    iso_numeric       TEXT,
    name_en           TEXT NOT NULL,
    name_local        TEXT,
    name_ar           TEXT,
    capital_name_en   TEXT,
    capital_geoname_id INTEGER,
    bbox_west         REAL,
    bbox_south        REAL,
    bbox_east         REAL,
    bbox_north        REAL,
    centroid_lat      REAL,
    centroid_lon      REAL,
    region            TEXT,
    subregion         TEXT,
    continent         TEXT,
    population        INTEGER DEFAULT 0,
    area_km2          REAL,
    currency_code     TEXT,
    phone_prefix      TEXT,
    languages         TEXT,
    tld               TEXT,
    neighbours        TEXT,
    geojson_110m      TEXT,
    geojson_50m       TEXT,
    geojson_10m       TEXT,
    source            TEXT DEFAULT 'geonames',
    last_updated      TEXT
);

-- جدول الأماكن (مدن + قرى + مواقع تاريخية)
CREATE TABLE IF NOT EXISTS places (
    geoname_id        INTEGER PRIMARY KEY,
    name_en           TEXT NOT NULL,
    name_ascii        TEXT,
    name_ar           TEXT,
    name_local        TEXT,
    lat               REAL NOT NULL,
    lon               REAL NOT NULL,
    feature_class     TEXT,
    feature_code      TEXT,
    country_iso2      TEXT REFERENCES countries(iso2),
    admin1_code       TEXT,
    admin2_code       TEXT,
    admin3_code       TEXT,
    admin1_name_en    TEXT,
    admin2_name_en    TEXT,
    population        INTEGER DEFAULT 0,
    elevation         INTEGER,
    dem               INTEGER,
    timezone          TEXT,
    is_capital        INTEGER DEFAULT 0,
    is_admin_capital  INTEGER DEFAULT 0,
    is_historical     INTEGER DEFAULT 0,
    is_deleted        INTEGER DEFAULT 0,
    source            TEXT DEFAULT 'geonames',
    wikidata_id       TEXT,
    confidence        REAL DEFAULT 1.0,
    last_updated      TEXT
);

-- جدول الأسماء البديلة (كل اللغات)
CREATE TABLE IF NOT EXISTS alt_names (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    geoname_id        INTEGER NOT NULL REFERENCES places(geoname_id),
    lang              TEXT,
    name              TEXT NOT NULL,
    is_preferred      INTEGER DEFAULT 0,
    is_short          INTEGER DEFAULT 0,
    is_colloquial     INTEGER DEFAULT 0,
    is_historic       INTEGER DEFAULT 0
);

-- جدول المناطق الإدارية
CREATE TABLE IF NOT EXISTS admin_regions (
    code              TEXT PRIMARY KEY,
    country_iso2      TEXT REFERENCES countries(iso2),
    level             INTEGER,
    name_en           TEXT NOT NULL,
    name_local        TEXT,
    geoname_id        INTEGER
);

-- جدول المعالم الجغرافية الطبيعية
CREATE TABLE IF NOT EXISTS geo_features (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    type              TEXT NOT NULL,
    name_en           TEXT,
    name_ar           TEXT,
    geojson           TEXT,
    bbox_west         REAL,
    bbox_south        REAL,
    bbox_east         REAL,
    bbox_north        REAL,
    source            TEXT
);

-- الفهارس
CREATE INDEX IF NOT EXISTS idx_places_country      ON places(country_iso2);
CREATE INDEX IF NOT EXISTS idx_places_latlon       ON places(lat, lon);
CREATE INDEX IF NOT EXISTS idx_places_feature      ON places(feature_code);
CREATE INDEX IF NOT EXISTS idx_places_population   ON places(population DESC);
CREATE INDEX IF NOT EXISTS idx_places_capital      ON places(is_capital) WHERE is_capital = 1;
CREATE INDEX IF NOT EXISTS idx_places_name_ar      ON places(name_ar);
CREATE INDEX IF NOT EXISTS idx_places_name_en      ON places(name_en);
CREATE INDEX IF NOT EXISTS idx_altnames_lang_name  ON alt_names(lang, name);
CREATE INDEX IF NOT EXISTS idx_altnames_place      ON alt_names(geoname_id);
"""

# ══════════════════════════════════════════════════════════════════════
# STEP 3 — Wikidata SPARQL للمدن التاريخية والحضارات
# ══════════════════════════════════════════════════════════════════════
WIKIDATA_QUERIES: Dict[str, str] = {
    # المواقع التاريخية والحضارات البارزة المحددة بالاسم (بابل، نينوى، أور، قرطبة، تدمر، قرطاجة، البتراء)
    "notable_ancient_civilizations": """
        SELECT DISTINCT ?place ?placeLabel ?coord ?countryLabel ?iso2 WHERE {
          VALUES ?place { wd:Q5684 wd:Q3860 wd:Q131367 wd:Q5783 wd:Q83354 wd:Q180111 wd:Q1757 }
          ?place wdt:P625 ?coord .
          OPTIONAL { ?place wdt:P17 ?country . ?country wdt:P297 ?iso2 . }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "ar,en" . }
        }
    """,
    # المدن التاريخية العربية والإسلامية الكبرى
    "historical_arab_cities": """
        SELECT DISTINCT ?place ?placeLabel ?coord ?countryLabel ?iso2 WHERE {
          VALUES ?type { wd:Q515 wd:Q839954 wd:Q486972 wd:Q123705 wd:Q3024240 }
          ?place wdt:P31 ?type .
          ?place wdt:P625 ?coord .
          ?place wdt:P17 ?country .
          ?country wdt:P297 ?iso2 .
          VALUES ?iso2 { "MA" "DZ" "TN" "LY" "EG" "SA" "IQ" "SY" "JO" "PS" "YE" "OM" "AE" "QA" "KW" "BH" "SD" "MR" "ES" "TR" "IR" }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "ar,en,fr" . }
        }
        LIMIT 1000
    """,
    # الحضارات القديمة والمواقع الأثرية
    "ancient_civilizations": """
        SELECT DISTINCT ?place ?placeLabel ?coord ?countryLabel ?iso2 WHERE {
          VALUES ?type { wd:Q839954 wd:Q486972 }
          ?place wdt:P31 ?type .
          ?place wdt:P625 ?coord .
          OPTIONAL { ?place wdt:P17 ?country . ?country wdt:P297 ?iso2 . }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "ar,en,fr" . }
        }
        LIMIT 1000
    """,
    # العواصم التاريخية الكبرى
    "all_historical_capitals": """
        SELECT DISTINCT ?capital ?capitalLabel ?coord ?countryLabel ?iso2 WHERE {
          ?country wdt:P36 ?capital .
          ?capital wdt:P625 ?coord .
          ?country wdt:P297 ?iso2 .
          SERVICE wikibase:label { bd:serviceParam wikibase:language "ar,en,fr,es,de" . }
        }
        LIMIT 500
    """,
}


# ══════════════════════════════════════════════════════════════════════
# STEP 4 — منطق التحميل والكاش والبناء
# ══════════════════════════════════════════════════════════════════════
@dataclass
class BuildReport:
    countries: int
    places: int
    capitals: int
    admin_capitals: int
    historical: int
    altnames: int
    languages: int
    db_size_mb: float


class BuildLogger:
    def __init__(self, verbose: bool = True):
        self.verbose = verbose

    def step(self, msg: str):
        print(f"\n🚀 {msg}...")

    def info(self, msg: str):
        if self.verbose:
            print(f"  ℹ️ {msg}")

    def warn(self, msg: str):
        print(f"  ⚠️ {msg}")

    def success(self, msg: str):
        print(f"  ✅ {msg}")


class CachedDownloader:
    def __init__(self, cache_dir: str | Path = "data/geo_cache", max_age_days: int = 30):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_age_days = max_age_days
        self.headers = {"User-Agent": "ShortsStudioBot/1.0 (GIS geodata builder; contact@example.com)"}

    def fetch_all(self, source_entries: List[Dict[str, Any]]) -> Dict[str, Path]:
        results: Dict[str, Path] = {}
        for entry in source_entries:
            url = entry["url"]
            filename = url.split("/")[-1]
            cache_path = self.cache_dir / filename
            extracted_dir = self.cache_dir / (filename.replace(".zip", "") + "_dir")

            is_fresh = False
            if cache_path.exists():
                age_days = (datetime.now() - datetime.fromtimestamp(cache_path.stat().st_mtime)).days
                if age_days < self.max_age_days and cache_path.stat().st_size > 1000:
                    is_fresh = True
                    print(f"  ✓ من الكاش: {filename} ({age_days} يوماً)")

            if not is_fresh:
                print(f"  ⬇ تحميل {entry.get('desc', filename)}: {url}")
                resp = requests.get(url, stream=True, timeout=60, headers=self.headers)
                resp.raise_for_status()
                total_size = int(resp.headers.get("content-length", 0))
                with open(cache_path, "wb") as f, tqdm(
                    total=total_size, unit="B", unit_scale=True, desc=f"  {filename}"
                ) as bar:
                    for chunk in resp.iter_content(chunk_size=65536):
                        f.write(chunk)
                        bar.update(len(chunk))

            # فك الضغط (باستثناء alternateNamesV2 للقراءة التتابعية التخفيفية)
            if filename.endswith(".zip") and "alternateNames" not in filename:
                if not extracted_dir.exists() or not any(extracted_dir.iterdir()):
                    extracted_dir.mkdir(parents=True, exist_ok=True)
                    print(f"  📦 فك ضغط {filename}...")
                    with zipfile.ZipFile(cache_path) as z:
                        z.extractall(extracted_dir)
                results[filename] = extracted_dir
            else:
                results[filename] = cache_path

        return results


def load_countries_geonames(countryinfo_path: Path, db: sqlite3.Connection) -> int:
    cur = db.cursor()
    countries: List[Dict[str, Any]] = []
    filepath = countryinfo_path if countryinfo_path.is_file() else countryinfo_path / "countryInfo.txt"

    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) >= 17:
                iso2 = parts[0].strip().upper()
                iso3 = parts[1].strip().upper()
                iso_num = parts[2].strip()
                name_en = parts[4].strip()
                capital = parts[5].strip()
                area = float(parts[6].strip()) if parts[6].strip() else None
                pop = int(parts[7].strip()) if parts[7].strip().isdigit() else 0
                continent = parts[8].strip()
                tld = parts[9].strip()
                cur_code = parts[10].strip()
                phone = parts[12].strip()
                langs = parts[15].strip()
                gid = int(parts[16].strip()) if parts[16].strip().isdigit() else None
                neighbours = parts[17].strip() if len(parts) > 17 else None

                countries.append({
                    "iso2": iso2, "iso3": iso3, "iso_numeric": iso_num,
                    "name_en": name_en, "name_local": name_en, "name_ar": None,
                    "capital_name_en": capital, "capital_geoname_id": gid,
                    "continent": continent, "population": pop, "area_km2": area,
                    "currency_code": cur_code, "phone_prefix": phone,
                    "languages": langs, "tld": tld, "neighbours": neighbours,
                    "last_updated": datetime.now().isoformat()
                })

    cur.executemany("""
        INSERT OR REPLACE INTO countries (
            iso2, iso3, iso_numeric, name_en, name_local, name_ar,
            capital_name_en, capital_geoname_id, continent, population,
            area_km2, currency_code, phone_prefix, languages, tld, neighbours, last_updated
        ) VALUES (
            :iso2, :iso3, :iso_numeric, :name_en, :name_local, :name_ar,
            :capital_name_en, :capital_geoname_id, :continent, :population,
            :area_km2, :currency_code, :phone_prefix, :languages, :tld, :neighbours, :last_updated
        )
    """, countries)
    db.commit()
    return len(countries)


def enrich_countries_geojson(ne_countries_shp_dir: Path, db: sqlite3.Connection):
    cur = db.cursor()
    shp_files = list(ne_countries_shp_dir.glob("*.shp"))
    if not shp_files:
        return

    shp_path = shp_files[0]
    res_key = "geojson_50m"
    if "110m" in str(shp_path):
        res_key = "geojson_110m"
    elif "10m" in str(shp_path):
        res_key = "geojson_10m"

    try:
        sf = shapefile.Reader(str(shp_path))
        fields = [f[0] for f in sf.fields[1:]]
        updates = []
        for shape_rec in sf.shapeRecords():
            rec = dict(zip(fields, shape_rec.record))
            iso2 = (rec.get("ISO_A2") or rec.get("ISO_A2_EH") or "").strip().upper()
            iso3 = (rec.get("ISO_A3") or rec.get("ISO_A3_EH") or "").strip().upper()
            name_ar = str(rec.get("NAME_AR") or "").strip() or None
            region = str(rec.get("REGION_UN") or rec.get("CONTINENT") or "").strip() or None
            subregion = str(rec.get("SUBREGION") or rec.get("REGION_WB") or "").strip() or None

            bbox = shape_rec.shape.bbox
            b_w, b_s, b_e, b_n = bbox[0], bbox[1], bbox[2], bbox[3]
            c_lon = round((b_w + b_e) / 2, 4)
            c_lat = round((b_s + b_n) / 2, 4)

            geo_json = None
            try:
                geo_json = json.dumps(shape_rec.shape.__geo_interface__, separators=(",", ":"))
            except Exception:
                pass

            updates.append((
                name_ar, b_w, b_s, b_e, b_n, c_lat, c_lon, region, subregion, geo_json, iso2, iso3
            ))

        sql = f"""
            UPDATE countries SET
                name_ar = COALESCE(?, name_ar),
                bbox_west = ?, bbox_south = ?, bbox_east = ?, bbox_north = ?,
                centroid_lat = ?, centroid_lon = ?,
                region = COALESCE(?, region), subregion = COALESCE(?, subregion),
                {res_key} = ?
            WHERE iso2 = ? OR iso3 = ?
        """
        cur.executemany(sql, updates)
        db.commit()
    except Exception as e:
        print(f"  ⚠️ تحذير أثناء قراءة Shapefile الدول: {e}")


def load_places_geonames(cities_dir: Path, db: sqlite3.Connection) -> Set[int]:
    cur = db.cursor()
    txt_files = list(cities_dir.glob("cities*.txt")) or list(cities_dir.glob("allCountries.txt"))
    if not txt_files:
        raise FileNotFoundError(f"لم يُعثر على ملف المدن داخل {cities_dir}")

    cities_file = txt_files[0]
    places = []
    geoname_ids: Set[int] = set()
    ar_pattern = re.compile(r"[\u0600-\u06FF]")

    with open(cities_file, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) < 18:
                continue
            gid = int(parts[0])
            name_en = parts[1].strip()
            name_ascii = parts[2].strip() if parts[2] else name_en
            alt_raw = parts[3].strip()
            lat = float(parts[4])
            lon = float(parts[5])
            feat_class = parts[6].strip()
            feat_code = parts[7].strip()
            country_iso2 = parts[8].strip().upper()
            admin1 = parts[10].strip() if len(parts) > 10 else None
            admin2 = parts[11].strip() if len(parts) > 11 else None
            admin3 = parts[12].strip() if len(parts) > 12 else None
            pop = int(parts[14]) if parts[14].isdigit() else 0
            elev = int(parts[15]) if parts[15].isdigit() else None
            dem = int(parts[16]) if parts[16].lstrip("-").isdigit() else None
            tz = parts[17].strip() if len(parts) > 17 else None
            is_cap = 1 if feat_code == "PPLC" else 0
            is_admin_cap = 1 if feat_code in ("PPLA", "PPLA2") else 0

            name_ar = None
            if alt_raw:
                for cand in alt_raw.split(","):
                    cand = cand.strip()
                    if ar_pattern.search(cand):
                        name_ar = cand
                        break

            places.append((
                gid, name_en, name_ascii, name_ar, name_en, lat, lon, feat_class, feat_code,
                country_iso2, admin1, admin2, admin3, None, None, pop, elev, dem, tz,
                is_cap, is_admin_cap, 0, 0, "geonames", None, 1.0, datetime.now().isoformat()
            ))
            geoname_ids.add(gid)

            if len(places) >= 10000:
                cur.executemany("""
                    INSERT OR REPLACE INTO places (
                        geoname_id, name_en, name_ascii, name_ar, name_local, lat, lon, feature_class, feature_code,
                        country_iso2, admin1_code, admin2_code, admin3_code, admin1_name_en, admin2_name_en,
                        population, elevation, dem, timezone, is_capital, is_admin_capital, is_historical, is_deleted,
                        source, wikidata_id, confidence, last_updated
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, places)
                places.clear()

    if places:
        cur.executemany("""
            INSERT OR REPLACE INTO places (
                geoname_id, name_en, name_ascii, name_ar, name_local, lat, lon, feature_class, feature_code,
                country_iso2, admin1_code, admin2_code, admin3_code, admin1_name_en, admin2_name_en,
                population, elevation, dem, timezone, is_capital, is_admin_capital, is_historical, is_deleted,
                source, wikidata_id, confidence, last_updated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, places)
    db.commit()
    return geoname_ids


def load_admin_regions(admin1_path: Path, admin2_path: Path, db: sqlite3.Connection):
    cur = db.cursor()
    records = []

    def _read_admin(filepath: Path, level: int):
        if not filepath.exists():
            return
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                parts = line.strip().split("\t")
                if len(parts) >= 2:
                    code = parts[0].strip()
                    name_en = parts[1].strip()
                    name_local = parts[2].strip() if len(parts) > 2 else name_en
                    gid = int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else None
                    iso2 = code.split(".")[0].upper() if "." in code else ""
                    records.append((code, iso2, level, name_en, name_local, gid))
                    if len(records) >= 5000:
                        cur.executemany("""
                            INSERT OR REPLACE INTO admin_regions (code, country_iso2, level, name_en, name_local, geoname_id)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, records)
                        records.clear()

    _read_admin(admin1_path, level=1)
    _read_admin(admin2_path, level=2)
    if records:
        cur.executemany("""
            INSERT OR REPLACE INTO admin_regions (code, country_iso2, level, name_en, name_local, geoname_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, records)
    db.commit()


def load_altnames(
    altnames_path: Path,
    db: sqlite3.Connection,
    geoname_ids: Set[int],
    langs: Optional[List[str]] = None
) -> int:
    cur = db.cursor()
    alt_records = []
    preferred_ar: Dict[int, str] = {}
    langs_set = set(l.lower() for l in langs) if langs else None
    count = 0

    with zipfile.ZipFile(altnames_path) as z:
        txt_name = "alternateNamesV2.txt" if "alternateNamesV2.txt" in z.namelist() else "alternateNames.txt"
        with z.open(txt_name) as raw_f:
            with io.TextIOWrapper(raw_f, encoding="utf-8", errors="ignore") as f:
                for line in f:
                    p1 = line.find("\t")
                    if p1 == -1:
                        continue
                    p2 = line.find("\t", p1 + 1)
                    if p2 == -1:
                        continue
                    gid_str = line[p1 + 1 : p2]
                    if not gid_str.isdigit():
                        continue
                    gid = int(gid_str)
                    if gid not in geoname_ids:
                        continue

                    parts = line.strip().split("\t")
                    if len(parts) < 4:
                        continue

                    lang = parts[2].strip().lower()
                    if langs_set and lang not in langs_set:
                        continue

                    name = parts[3].strip()
                    if not name:
                        continue

                    is_pref = 1 if len(parts) > 4 and parts[4] == "1" else 0
                    is_short = 1 if len(parts) > 5 and parts[5] == "1" else 0
                    is_colloq = 1 if len(parts) > 6 and parts[6] == "1" else 0
                    is_hist = 1 if len(parts) > 7 and parts[7] == "1" else 0

                    alt_records.append((gid, lang, name, is_pref, is_short, is_colloq, is_hist))
                    count += 1

                    if lang == "ar":
                        if is_pref or gid not in preferred_ar:
                            preferred_ar[gid] = name

                    if len(alt_records) >= 20000:
                        cur.executemany("""
                            INSERT INTO alt_names (geoname_id, lang, name, is_preferred, is_short, is_colloquial, is_historic)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, alt_records)
                        alt_records.clear()

    if alt_records:
        cur.executemany("""
            INSERT INTO alt_names (geoname_id, lang, name, is_preferred, is_short, is_colloquial, is_historic)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, alt_records)

    # تحديث الاسم العربي المعتمد في جدول places
    if preferred_ar:
        updates = [(name, gid) for gid, name in preferred_ar.items()]
        for chunk in range(0, len(updates), 5000):
            cur.executemany("UPDATE places SET name_ar = ? WHERE geoname_id = ?", updates[chunk:chunk + 5000])

    db.commit()
    return count


def load_physical_features(
    coastline_dir: Path,
    lakes_dir: Path,
    rivers_dir: Path,
    db: sqlite3.Connection
):
    cur = db.cursor()
    entries = [
        (coastline_dir, "coastline"),
        (lakes_dir, "lake"),
        (rivers_dir, "river"),
    ]

    for pdir, ftype in entries:
        shp_files = list(pdir.glob("*.shp"))
        if not shp_files:
            continue
        try:
            sf = shapefile.Reader(str(shp_files[0]))
            fields = [f[0] for f in sf.fields[1:]]
            rows = []
            for shape_rec in sf.shapeRecords():
                if not hasattr(shape_rec, "shape") or not hasattr(shape_rec.shape, "bbox") or not shape_rec.shape.bbox:
                    continue
                rec = dict(zip(fields, shape_rec.record))
                name_en = str(rec.get("name") or rec.get("NAME") or rec.get("name_en") or "").strip() or None
                name_ar = str(rec.get("name_ar") or rec.get("NAME_AR") or "").strip() or None
                bbox = shape_rec.shape.bbox
                geojson_str = None
                try:
                    geojson_str = json.dumps(shape_rec.shape.__geo_interface__, separators=(",", ":"))
                except Exception:
                    pass

                rows.append((
                    ftype, name_en, name_ar, geojson_str, bbox[0], bbox[1], bbox[2], bbox[3], "natural_earth"
                ))

            cur.executemany("""
                INSERT INTO geo_features (type, name_en, name_ar, geojson, bbox_west, bbox_south, bbox_east, bbox_north, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, rows)
            db.commit()
        except Exception as e:
            print(f"  ⚠️ تحذير أثناء قراءة {ftype}: {e}")


class WikidataFetcher:
    def __init__(self, endpoint: str = "https://query.wikidata.org/sparql", retry: int = 1, delay: float = 0.5):
        self.endpoint = endpoint
        self.retry = retry
        self.delay = delay
        self.headers = {"User-Agent": "ShortsStudioBot/1.0 (GIS geodata builder; contact@example.com)"}

    def query(self, sparql: str) -> List[Dict[str, Any]]:
        for attempt in range(self.retry):
            try:
                resp = requests.get(
                    self.endpoint,
                    params={"query": sparql, "format": "json"},
                    headers=self.headers,
                    timeout=8
                )
                if resp.status_code == 200:
                    data = resp.json()
                    time.sleep(self.delay)
                    return data.get("results", {}).get("bindings", [])
            except Exception:
                pass
        return []


def load_historical_places(results: List[Dict[str, Any]], db: sqlite3.Connection, source: str = "wikidata") -> int:
    if not results:
        return 0
    cur = db.cursor()
    pt_regex = re.compile(r"Point\s*\(\s*([^\s]+)\s+([^\s\)]+)\s*\)")
    places_rows = []
    alt_rows = []

    # استخدام معرّفات سالبة فريدة للمواقع التاريخية
    cur.execute("SELECT MIN(geoname_id) FROM places")
    min_id = cur.fetchone()[0] or 0
    curr_id = min(min_id, 0) - 1

    for b in results:
        lbl = b.get("placeLabel", {}).get("value") or b.get("capitalLabel", {}).get("value") or ""
        coord = b.get("coord", {}).get("value", "")
        iso2 = b.get("iso2", {}).get("value", "").strip().upper() or None
        place_uri = b.get("place", {}).get("value") or b.get("capital", {}).get("value") or ""
        wiki_id = place_uri.split("/")[-1] if place_uri else None

        if not lbl or not coord:
            continue
        m = pt_regex.search(coord)
        if not m:
            continue
        lon, lat = float(m.group(1)), float(m.group(2))

        curr_id -= 1
        name_ar = lbl if re.search(r"[\u0600-\u06FF]", lbl) else None
        name_en = lbl

        places_rows.append((
            curr_id, name_en, name_en, name_ar, lbl, lat, lon, "P", "PPLH",
            iso2, None, None, None, None, None, 0, None, None, None,
            0, 0, 1, 0, f"wikidata_{source}", wiki_id, 0.95, datetime.now().isoformat()
        ))
        alt_rows.append((curr_id, "ar" if name_ar else "en", lbl, 1, 0, 0, 1))

    if places_rows:
        cur.executemany("""
            INSERT OR IGNORE INTO places (
                geoname_id, name_en, name_ascii, name_ar, name_local, lat, lon, feature_class, feature_code,
                country_iso2, admin1_code, admin2_code, admin3_code, admin1_name_en, admin2_name_en,
                population, elevation, dem, timezone, is_capital, is_admin_capital, is_historical, is_deleted,
                source, wikidata_id, confidence, last_updated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, places_rows)
        cur.executemany("""
            INSERT INTO alt_names (geoname_id, lang, name, is_preferred, is_short, is_colloquial, is_historic)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, alt_rows)
        db.commit()

    return len(places_rows)


def build_fts_index(db: sqlite3.Connection):
    cur = db.cursor()
    cur.execute("DROP TABLE IF EXISTS places_fts;")
    cur.execute("""
        CREATE VIRTUAL TABLE places_fts USING fts5(
            geoname_id UNINDEXED,
            country_iso2 UNINDEXED,
            name_en,
            name_ascii,
            all_names,
            tokenize = 'unicode61 remove_diacritics 1'
        );
    """)

    cur.execute("""
        INSERT INTO places_fts (geoname_id, country_iso2, name_en, name_ascii, all_names)
        SELECT 
            p.geoname_id,
            p.country_iso2,
            p.name_en,
            COALESCE(p.name_ascii, p.name_en),
            COALESCE(p.name_en, '') || ' ' || COALESCE(p.name_ascii, '') || ' ' || COALESCE(p.name_ar, '') || ' ' || COALESCE(GROUP_CONCAT(a.name, ' '), '')
        FROM places p
        LEFT JOIN alt_names a ON p.geoname_id = a.geoname_id
        GROUP BY p.geoname_id;
    """)
    cur.execute("INSERT INTO places_fts(places_fts) VALUES('optimize');")
    db.commit()


# ══════════════════════════════════════════════════════════════════════
# دالة البناء الرئيسية (build_geodatabase)
# ══════════════════════════════════════════════════════════════════════
def build_geodatabase(
    city_source: str = "cities5000",
    map_resolution: str = "50m",
    include_altnames: bool = True,
    include_historical: bool = True,
    include_physical: bool = True,
    cache_dir: str = "data/geo_cache",
    output_db: str = "data/geodata.db",
    force_rebuild: bool = False,
    verbose: bool = True
) -> BuildReport:
    log = BuildLogger(verbose)
    db_path = Path(output_db)

    if db_path.exists() and not force_rebuild:
        log.info(f"قاعدة البيانات {output_db} موجودة بالفعل. جلب التقرير المباشر...")
        conn = sqlite3.connect(str(db_path))
        c = conn.cursor()
        rep = BuildReport(
            countries=c.execute("SELECT COUNT(*) FROM countries").fetchone()[0],
            places=c.execute("SELECT COUNT(*) FROM places").fetchone()[0],
            capitals=c.execute("SELECT COUNT(*) FROM places WHERE is_capital=1").fetchone()[0],
            admin_capitals=c.execute("SELECT COUNT(*) FROM places WHERE is_admin_capital=1").fetchone()[0],
            historical=c.execute("SELECT COUNT(*) FROM places WHERE is_historical=1").fetchone()[0],
            altnames=c.execute("SELECT COUNT(*) FROM alt_names").fetchone()[0],
            languages=c.execute("SELECT COUNT(DISTINCT lang) FROM alt_names").fetchone()[0],
            db_size_mb=db_path.stat().st_size / (1024 * 1024)
        )
        conn.close()
        return rep

    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    # 1. التحميل الذكي بالكاش
    log.step("تحميل المصادر الجغرافية الرسمية")
    downloader = CachedDownloader(cache_dir, max_age_days=30)
    city_key = city_source if city_source.startswith("geonames_") else f"geonames_{city_source.replace('cities', '') if 'cities' in city_source else city_source}"
    if city_key not in SOURCES:
        city_key = "geonames_5k"

    source_entries = [
        SOURCES[city_key],
        SOURCES["geonames_countries"],
        SOURCES["geonames_admin1"],
        SOURCES["geonames_admin2"],
        SOURCES[f"ne_countries_{map_resolution}"],
        SOURCES[f"ne_places_{map_resolution}"],
    ]
    if include_altnames:
        source_entries.append(SOURCES["geonames_altnames"])
    if include_physical:
        source_entries.extend([
            SOURCES["ne_coastline_50m"],
            SOURCES["ne_lakes_50m"],
            SOURCES["ne_rivers_50m"],
        ])

    files = downloader.fetch_all(source_entries)

    # 2. إنشاء قاعدة البيانات وتطبيق الـ Schema
    log.step("إنشاء جداول SQLite وهيكلية GIS")
    conn = sqlite3.connect(str(db_path))
    conn.executescript(SCHEMA)

    # 3. تحميل بيانات الدول
    log.step("تحميل بيانات الدول من GeoNames")
    country_info_file = files.get("countryInfo.txt") or (Path(cache_dir) / "countryInfo.txt")
    c_count = load_countries_geonames(country_info_file, conn)
    log.info(f"تم تحميل {c_count} دولة.")

    log.step(f"إضافة حدود الدول الجغرافية GeoJSON ({map_resolution})")
    ne_shp_dir = files.get(f"ne_{map_resolution}_admin_0_countries.zip") or (Path(cache_dir) / f"ne_{map_resolution}_admin_0_countries_dir")
    enrich_countries_geojson(ne_shp_dir, conn)

    # 4. تحميل الأماكن والمدن
    log.step(f"تحميل الأماكن من GeoNames ({city_key})")
    city_filename = SOURCES[city_key]["url"].split("/")[-1]
    city_dir = files.get(city_filename) or (Path(cache_dir) / (city_filename.replace(".zip", "") + "_dir"))
    geoname_ids = load_places_geonames(city_dir, conn)
    log.info(f"تم إدراج {len(geoname_ids):,} مدينة/مكان.")

    # 5. تحميل المناطق الإدارية
    log.step("تحميل المناطق الإدارية (admin1 + admin2)")
    adm1_file = files.get("admin1CodesASCII.txt") or (Path(cache_dir) / "admin1CodesASCII.txt")
    adm2_file = files.get("admin2Codes.txt") or (Path(cache_dir) / "admin2Codes.txt")
    load_admin_regions(adm1_file, adm2_file, conn)

    # 6. الأسماء البديلة بكل اللغات
    if include_altnames:
        log.step("تحميل الأسماء البديلة للغات العالم (عربي، إنجليزي، فرنسي، وغيرها)")
        alt_zip = files.get("alternateNamesV2.zip") or (Path(cache_dir) / "alternateNamesV2.zip")
        alt_count = load_altnames(alt_zip, conn, geoname_ids, langs=None)
        log.info(f"تم ربط {alt_count:,} اسماً بديلاً.")

    # 7. المعالم الطبيعية
    if include_physical:
        log.step("تحميل المعالم الطبيعية (سواحل، بحيرات، أنهار)")
        c_dir = files.get("ne_50m_coastline.zip") or (Path(cache_dir) / "ne_50m_coastline_dir")
        l_dir = files.get("ne_50m_lakes.zip") or (Path(cache_dir) / "ne_50m_lakes_dir")
        r_dir = files.get("ne_50m_rivers_lake_centerlines.zip") or (Path(cache_dir) / "ne_50m_rivers_lake_centerlines_dir")
        load_physical_features(c_dir, l_dir, r_dir, conn)

    # 8. المدن التاريخية من Wikidata
    if include_historical:
        log.step("جلب المدن التاريخية والحضارات عبر Wikidata SPARQL")
        fetcher = WikidataFetcher()
        for q_name, sparql_code in WIKIDATA_QUERIES.items():
            results = fetcher.query(sparql_code)
            count_hist = load_historical_places(results, conn, source=q_name)
            log.info(f"  Wikidata [{q_name}]: {count_hist} مكان")

    # 9. بناء فهرس FTS5
    log.step("بناء فهرس البحث النصي السريع (FTS5)")
    build_fts_index(conn)

    # 10. إحصاءات ختامية
    c = conn.cursor()
    report = BuildReport(
        countries=c.execute("SELECT COUNT(*) FROM countries").fetchone()[0],
        places=c.execute("SELECT COUNT(*) FROM places").fetchone()[0],
        capitals=c.execute("SELECT COUNT(*) FROM places WHERE is_capital=1").fetchone()[0],
        admin_capitals=c.execute("SELECT COUNT(*) FROM places WHERE is_admin_capital=1").fetchone()[0],
        historical=c.execute("SELECT COUNT(*) FROM places WHERE is_historical=1").fetchone()[0],
        altnames=c.execute("SELECT COUNT(*) FROM alt_names").fetchone()[0],
        languages=c.execute("SELECT COUNT(DISTINCT lang) FROM alt_names").fetchone()[0],
        db_size_mb=db_path.stat().st_size / (1024 * 1024)
    )
    conn.close()

    print("\n" + "═" * 55)
    print("📊 تقرير بناء قاعدة البيانات الجغرافية (geodata.db):")
    print(f"  🌍 الدول المسجلة: {report.countries:,}")
    print(f"  🏙️ الأماكن والمدن: {report.places:,}")
    print(f"  👑 العواصم الرسمية: {report.capitals:,}")
    print(f"  🏛️ العواصم الإقليمية/المحافظات: {report.admin_capitals:,}")
    print(f"  🏺 المواقع والمدن التاريخية: {report.historical:,}")
    print(f"  📖 الأسماء والمرادفات البديلة: {report.altnames:,}")
    print(f"  🌐 اللغات المدعومة: {report.languages:,}")
    print(f"  💾 الحجم الإجمالي للملف: {report.db_size_mb:.1f} MB")
    print("═" * 55 + "\n")
    return report


# ══════════════════════════════════════════════════════════════════════
# STEP 6 — واجهة CLI والاختبار
# ══════════════════════════════════════════════════════════════════════
def run_cli_tests(db_path: str = "data/geodata.db"):
    from pipeline.geo import GeoEngine
    engine = GeoEngine(db_path)
    test_cases = [
        ("فاس", "MA", 34.03, -5.00),
        ("مراكش", "MA", 31.62, -7.98),
        ("سلا", "MA", 34.05, -6.79),
        ("مكناس", "MA", 33.89, -5.54),
        ("الإسكندرية", "EG", 31.20, 29.91),
        ("بابل", "IQ", 32.54, 44.42),
        ("قرطبة", "ES", 37.88, -4.77),
        ("إسطنبول", "TR", 41.00, 28.97),
        ("La Paz", "BO", -16.49, -68.13),
        ("Sucre", "BO", -19.03, -65.26),
    ]

    print("\n" + "═" * 45)
    print("🧪 بدء الاختبارات الجغرافية التلقائية:")
    passed = 0
    for query, country, lat_exp, lon_exp in test_cases:
        result = engine.resolve(query, country_iso2=country)
        if result:
            lat_ok = abs(result.lat - lat_exp) < 0.5
            lon_ok = abs(result.lon - lon_exp) < 0.5
            status = "✅" if (lat_ok and lon_ok) else "⚠️"
            if lat_ok and lon_ok:
                passed += 1
            print(f"{status} {query} ({country}): {result.lat:.2f},{result.lon:.2f} [{result.name_en}]")
        else:
            print(f"❌ {query} ({country}): لم يُعثر عليها")

    print("═" * 45)
    print(f"النتيجة النهائية: {passed}/{len(test_cases)} اختبار ناجح")
    if passed < len(test_cases):
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="بناء قاعدة البيانات الجغرافية geodata.db")
    parser.add_argument("--source", choices=["cities15000", "cities5000", "cities1000", "allCountries"], default="cities5000")
    parser.add_argument("--map", choices=["110m", "50m", "10m"], default="50m")
    parser.add_argument("--no-altnames", action="store_true")
    parser.add_argument("--no-historical", action="store_true")
    parser.add_argument("--no-physical", action="store_true")
    parser.add_argument("--update-altnames-only", action="store_true")
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--test-only", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--cache-dir", default="data/geo_cache")
    parser.add_argument("--output-db", default="data/geodata.db")
    args = parser.parse_args()

    if args.test_only:
        run_cli_tests(args.output_db)
        sys.exit(0)

    if args.update_altnames_only:
        conn = sqlite3.connect(args.output_db)
        cur = conn.cursor()
        cur.execute("SELECT geoname_id FROM places")
        all_gids = set(r[0] for r in cur.fetchall())
        alt_zip = Path(args.cache_dir) / "alternateNamesV2.zip"
        load_altnames(alt_zip, conn, all_gids)
        build_fts_index(conn)
        conn.close()
        print("✅ تم تحديث الأسماء البديلة وفهرس FTS بنجاح.")
        sys.exit(0)

    build_geodatabase(
        city_source=args.source,
        map_resolution=args.map,
        include_altnames=not args.no_altnames,
        include_historical=not args.no_historical,
        include_physical=not args.no_physical,
        cache_dir=args.cache_dir,
        output_db=args.output_db,
        force_rebuild=args.force
    )

    if args.test:
        run_cli_tests(args.output_db)
