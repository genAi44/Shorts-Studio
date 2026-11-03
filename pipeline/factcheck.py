"""Validates city→country→continent triples before script assembly.
Prevents geographic misclassification (e.g. Cairo ≠ Asian city).
"""
from __future__ import annotations
import re
from typing import Optional

# City → (country, continent, lat, lon)
CITY_DB: dict[str, tuple[str, str, float, float]] = {
    # Africa
    "cairo": ("egypt", "africa", 30.0444, 31.2357),
    "القاهرة": ("egypt", "africa", 30.0444, 31.2357),
    "cairo city": ("egypt", "africa", 30.0444, 31.2357),
    "alexandria": ("egypt", "africa", 31.2001, 29.9187),
    "الإسكندرية": ("egypt", "africa", 31.2001, 29.9187),
    "nairobi": ("kenya", "africa", -1.286, 36.818),
    "lagos": ("nigeria", "africa", 6.455, 3.384),
    "accra": ("ghana", "africa", 5.603, -0.187),
    "addis ababa": ("ethiopia", "africa", 9.025, 38.747),
    "أديس أبابا": ("ethiopia", "africa", 9.025, 38.747),
    "cape town": ("south africa", "africa", -33.925, 18.424),
    "johannesburg": ("south africa", "africa", -26.205, 28.050),
    "khartoum": ("sudan", "africa", 15.558, 32.533),
    "الخرطوم": ("sudan", "africa", 15.558, 32.533),
    "tripoli": ("libya", "africa", 32.902, 13.180),
    "طرابلس": ("libya", "africa", 32.902, 13.180),
    "tunis": ("tunisia", "africa", 36.819, 10.165),
    "تونس": ("tunisia", "africa", 36.819, 10.165),
    "algiers": ("algeria", "africa", 36.737, 3.086),
    "الجزائر": ("algeria", "africa", 36.737, 3.086),
    "rabat": ("morocco", "africa", 34.020, -6.843),
    "الرباط": ("morocco", "africa", 34.020, -6.843),
    "casablanca": ("morocco", "africa", 33.573, -7.589),
    "الدار البيضاء": ("morocco", "africa", 33.573, -7.589),
    "mogadishu": ("somalia", "africa", 2.046, 45.318),
    "مقديشو": ("somalia", "africa", 2.046, 45.318),
    # Middle East / Asia
    "riyadh": ("saudi arabia", "asia", 24.687, 46.722),
    "الرياض": ("saudi arabia", "asia", 24.687, 46.722),
    "jeddah": ("saudi arabia", "asia", 21.485, 39.192),
    "جدة": ("saudi arabia", "asia", 21.485, 39.192),
    "mecca": ("saudi arabia", "asia", 21.390, 39.857),
    "مكة": ("saudi arabia", "asia", 21.390, 39.857),
    "medina": ("saudi arabia", "asia", 24.470, 39.610),
    "المدينة": ("saudi arabia", "asia", 24.470, 39.610),
    "dubai": ("uae", "asia", 25.204, 55.270),
    "دبي": ("uae", "asia", 25.204, 55.270),
    "abu dhabi": ("uae", "asia", 24.453, 54.377),
    "أبوظبي": ("uae", "asia", 24.453, 54.377),
    "baghdad": ("iraq", "asia", 33.341, 44.401),
    "بغداد": ("iraq", "asia", 33.341, 44.401),
    "damascus": ("syria", "asia", 33.510, 36.291),
    "دمشق": ("syria", "asia", 33.510, 36.291),
    "amman": ("jordan", "asia", 31.955, 35.945),
    "عمّان": ("jordan", "asia", 31.955, 35.945),
    "beirut": ("lebanon", "asia", 33.889, 35.495),
    "بيروت": ("lebanon", "asia", 33.889, 35.495),
    "doha": ("qatar", "asia", 25.286, 51.531),
    "الدوحة": ("qatar", "asia", 25.286, 51.531),
    "kuwait city": ("kuwait", "asia", 29.368, 47.978),
    "الكويت": ("kuwait", "asia", 29.368, 47.978),
    "muscat": ("oman", "asia", 23.613, 58.593),
    "مسقط": ("oman", "asia", 23.613, 58.593),
    "manama": ("bahrain", "asia", 26.218, 50.586),
    "المنامة": ("bahrain", "asia", 26.218, 50.586),
    "sanaa": ("yemen", "asia", 15.369, 44.191),
    "صنعاء": ("yemen", "asia", 15.369, 44.191),
    "tehran": ("iran", "asia", 35.689, 51.389),
    "طهران": ("iran", "asia", 35.689, 51.389),
    "istanbul": ("turkey", "asia", 41.013, 28.950),
    "إسطنبول": ("turkey", "asia", 41.013, 28.950),
    "ankara": ("turkey", "asia", 39.920, 32.854),
    "أنقرة": ("turkey", "asia", 39.920, 32.854),
    "tokyo": ("japan", "asia", 35.689, 139.692),
    "طوكيو": ("japan", "asia", 35.689, 139.692),
    "beijing": ("china", "asia", 39.905, 116.391),
    "بكين": ("china", "asia", 39.905, 116.391),
    "new delhi": ("india", "asia", 28.614, 77.209),
    "نيودلهي": ("india", "asia", 28.614, 77.209),
    # Europe
    "london": ("uk", "europe", 51.507, -0.127),
    "لندن": ("uk", "europe", 51.507, -0.127),
    "paris": ("france", "europe", 48.857, 2.352),
    "باريس": ("france", "europe", 48.857, 2.352),
    "berlin": ("germany", "europe", 52.520, 13.405),
    "برلين": ("germany", "europe", 52.520, 13.405),
    "rome": ("italy", "europe", 41.902, 12.496),
    "روما": ("italy", "europe", 41.902, 12.496),
    "madrid": ("spain", "europe", 40.417, -3.704),
    "مدريد": ("spain", "europe", 40.417, -3.704),
    # Americas
    "new york": ("usa", "americas", 40.713, -74.006),
    "نيويورك": ("usa", "americas", 40.713, -74.006),
    "washington": ("usa", "americas", 38.907, -77.036),
    "واشنطن": ("usa", "americas", 38.907, -77.036),
    "mexico city": ("mexico", "americas", 19.433, -99.133),
    "مكسيكو": ("mexico", "americas", 19.433, -99.133),
    "são paulo": ("brazil", "americas", -23.550, -46.633),
    "buenos aires": ("argentina", "americas", -34.603, -58.382),
    # Oceania
    "sydney": ("australia", "oceania", -33.868, 151.209),
    "canberra": ("australia", "oceania", -35.282, 149.129),
    "auckland": ("new zealand", "oceania", -36.848, 174.763),
}

# Country → continent
COUNTRY_CONTINENT: dict[str, str] = {
    "egypt": "africa", "nigeria": "africa", "kenya": "africa", "ghana": "africa",
    "ethiopia": "africa", "south africa": "africa", "sudan": "africa",
    "libya": "africa", "tunisia": "africa", "algeria": "africa",
    "morocco": "africa", "somalia": "africa", "tanzania": "africa",
    "uganda": "africa", "angola": "africa", "mozambique": "africa",
    "saudi arabia": "asia", "uae": "asia", "iraq": "asia", "syria": "asia",
    "jordan": "asia", "lebanon": "asia", "qatar": "asia", "kuwait": "asia",
    "oman": "asia", "bahrain": "asia", "yemen": "asia", "iran": "asia",
    "turkey": "asia", "japan": "asia", "china": "asia", "india": "asia",
    "pakistan": "asia", "bangladesh": "asia", "indonesia": "asia",
    "thailand": "asia", "vietnam": "asia", "south korea": "asia",
    "uk": "europe", "france": "europe", "germany": "europe", "italy": "europe",
    "spain": "europe", "netherlands": "europe", "sweden": "europe",
    "norway": "europe", "denmark": "europe", "finland": "europe",
    "usa": "americas", "canada": "americas", "mexico": "americas",
    "brazil": "americas", "argentina": "americas", "colombia": "americas",
    "australia": "oceania", "new zealand": "oceania",
}


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


def lookup_city(city: str) -> Optional[tuple[str, str, float, float]]:
    """Returns (country, continent, lat, lon) or None."""
    return CITY_DB.get(_norm(city))


def validate_continent(city: str, claimed_continent: str) -> tuple[bool, str]:
    """Returns (ok, message). ok=True if claimed matches known."""
    info = lookup_city(city)
    if info is None:
        return True, f"city '{city}' not in DB, skipping"
    country, real_continent, _, _ = info
    claimed = _norm(claimed_continent)
    if claimed != real_continent:
        return False, (
            f"'{city}' is in {real_continent.upper()} (country: {country}), "
            f"not {claimed_continent.upper()}"
        )
    return True, "ok"


def check_script(script: dict) -> list[str]:
    """Scan a script dict for geo errors. Returns list of error strings."""
    errors: list[str] = []
    text = str(script).lower()
    for city, (country, continent, _, _) in CITY_DB.items():
        if _norm(city) not in text:
            continue
        # Look for continent labels near the city mention
        wrong_continents = {
            "africa": ["asia", "europe", "americas"],
            "asia": ["africa", "europe", "americas"],
            "europe": ["africa", "asia", "americas"],
            "americas": ["africa", "asia", "europe"],
        }.get(continent, [])
        for wc in wrong_continents:
            # crude proximity check: both city and wrong continent in same scene text
            scenes = script.get("scenes") or []
            for sc in scenes:
                sc_text = str(sc).lower()
                if _norm(city) in sc_text and wc in sc_text:
                    errors.append(
                        f"Scene '{sc.get('id', '?')}': '{city}' (Africa/{country}) "
                        f"mentioned alongside continent '{wc}'"
                    )
    return errors


def get_city_coords(city: str) -> Optional[tuple[float, float]]:
    """Quick lat/lon lookup for director hints."""
    info = lookup_city(city)
    return (info[2], info[3]) if info else None
