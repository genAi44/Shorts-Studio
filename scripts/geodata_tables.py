"""Split from `scripts/build_geodata.py` (re-exported there); see that module."""
from __future__ import annotations
from typing import Any, Dict, List
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
import requests
from tqdm import tqdm
import zipfile


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
