"""Split from `scripts/build_geodata.py` (re-exported there); see that module."""
from __future__ import annotations
from typing import Any, Dict, List, Optional, Set
from pathlib import Path
from datetime import datetime
import io
import json
import re
import requests
import shapefile
import sqlite3
import time
import zipfile


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
