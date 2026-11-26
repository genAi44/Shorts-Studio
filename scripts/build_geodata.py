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
sys.path.insert(0, str(Path(__file__).resolve().parent))  # sibling split modules
from geodata_loaders import WikidataFetcher, build_fts_index, enrich_countries_geojson, load_admin_regions, load_altnames, load_countries_geonames, load_historical_places, load_physical_features, load_places_geonames  # noqa: E402
from geodata_tables import BuildLogger, BuildReport, CachedDownloader, SCHEMA, SOURCES, WIKIDATA_QUERIES  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)


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
