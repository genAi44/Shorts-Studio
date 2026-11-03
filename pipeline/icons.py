"""Auto Icon Picker for Shorts Studio beats.
Uses fast keyword matching (no LLM call) on beat text and query to select relevant
SVG icons from the local bundle in remotion/public/icons/.
"""
from __future__ import annotations
import os
from pathlib import Path
from typing import List, Dict

ROOT = Path(__file__).resolve().parent.parent
ICONS_DIR = ROOT / "remotion" / "public" / "icons"

# Automatically index all actual icons on disk: filename -> path relative to remotion/public/
_AVAILABLE_ICONS: Dict[str, str] = {}
if ICONS_DIR.exists():
    for root, _, files in os.walk(ICONS_DIR):
        for f in files:
            if f.endswith(".svg"):
                rel = os.path.relpath(os.path.join(root, f), ROOT / "remotion" / "public").replace("\\", "/")
                _AVAILABLE_ICONS[f.lower()] = rel
                base_name = f.lower().replace(".svg", "")
                _AVAILABLE_ICONS[base_name] = rel

# Common aliases mapping English terms or LLM hallucinations to exact bundle paths
ICON_ALIASES: Dict[str, str] = {
    "building": "icons/building/city.svg",
    "government": "icons/building/parliament.svg",
    "politics": "icons/building/parliament.svg",
    "balance": "icons/chart/scale.svg",
    "justice": "icons/chart/scale.svg",
    "law": "icons/chart/scale.svg",
    "bar-chart": "icons/chart/chart-bar.svg",
    "barchart": "icons/chart/chart-bar.svg",
    "chart-bar": "icons/chart/chart-bar.svg",
    "chart": "icons/chart/chart-line.svg",
    "map": "icons/map/location.svg",
    "map_pin": "icons/map/pin.svg",
    "pin": "icons/map/pin.svg",
    "globe": "icons/world/globe-2.svg",
    "globe-2": "icons/world/globe-2.svg",
    "world": "icons/world/world-globe.svg",
    "earth": "icons/world/world-globe.svg",
    # Lucide semantic icons
    "population": "icons/person/users.svg",
    "crowd": "icons/person/users.svg",
    "users": "icons/person/users.svg",
    "user-round": "icons/person/user-round.svg",
    "landmark": "icons/building/landmark.svg",
    "capital-icon": "icons/building/landmark.svg",
    "building-2": "icons/building/building-2.svg",
    "trophy": "icons/crown/trophy.svg",
    "medal": "icons/crown/medal.svg",
    "ranking": "icons/number/ranking.svg",
    "list-ordered": "icons/number/ranking.svg",
    "map-pin-2": "icons/map/map-pin-2.svg",
    "trending-up": "icons/arrow/trending-up.svg",
    "zap": "icons/science/zap.svg",
    "mosque": "icons/monument/mosque.svg",
    "pyramid": "icons/history/pyramid.svg",
    "castle": "icons/history/castle.svg",
    "monument": "icons/history/monument.svg",
    "clock": "icons/time/clock.svg",
    "timeline": "icons/time/timeline.svg",
    "money": "icons/coin/coins.svg",
    "gold": "icons/coin/gold-bars.svg",
    "gold_bars": "icons/coin/gold-bars.svg",
    "gold-bars": "icons/coin/gold-bars.svg",
    "arrow": "icons/arrow/arrow-right.svg",
    "globe": "icons/world/world-globe.svg",
    "earth": "icons/world/world-globe.svg",
    "world-globe": "icons/world/world-globe.svg",
    "crown": "icons/crown/crown-gold.svg",
    "sword": "icons/history/sword.svg",
    "shield": "icons/history/shield.svg",
    "star": "icons/star/star.svg",
    "flame": "icons/fire/flame.svg",
    "fire": "icons/fire/flame.svg",
    "atom": "icons/science/atom.svg",
    "bulb": "icons/science/bulb.svg",
    "lightbulb": "icons/science/bulb.svg",
    "person": "icons/person/profile.svg",
    "people": "icons/person/people.svg",
    "warning": "icons/arrow/target.svg",
    "check": "icons/star/badge.svg",
}

def _clean_key(name: str) -> str:
    s = name.lower().replace("\\", "/").strip()
    if s.endswith(".svg"):
        s = s[:-4]
    if "/" in s:
        s = s.split("/")[-1]
    return s

def _find_icon(name: str) -> str:
    clean = _clean_key(name)
    if clean in ICON_ALIASES:
        target = ICON_ALIASES[clean]
        if (ROOT / "remotion" / "public" / target).exists():
            return target

    # Check direct filename match in available
    if clean in _AVAILABLE_ICONS:
        return _AVAILABLE_ICONS[clean]
    if f"{clean}.svg" in _AVAILABLE_ICONS:
        return _AVAILABLE_ICONS[f"{clean}.svg"]

    # Partial match on filename
    for k, v in _AVAILABLE_ICONS.items():
        if clean in k or k in clean:
            return v

    return "icons/history/monument.svg"

def resolve_icon(icon_path: str) -> str:
    """Ensures any icon path requested by director/LLM exists on disk in remotion/public/."""
    if not icon_path:
        return "icons/history/monument.svg"
    clean = icon_path.strip().replace("\\", "/")
    if clean.startswith("public/"):
        clean = clean[7:]
    if clean.startswith("/"):
        clean = clean[1:]

    # If it directly exists on disk in remotion/public
    if (ROOT / "remotion" / "public" / clean).exists():
        return clean

    # Resolve through alias or fuzzy match
    resolved = _find_icon(clean)
    if (ROOT / "remotion" / "public" / resolved).exists():
        return resolved

    return "icons/history/monument.svg"

def sanitize_spec_assets(spec: dict) -> dict:
    """Walks the entire Remotion spec and validates/sanitizes all icon and map paths."""
    if not isinstance(spec, dict):
        return spec

    # Check maps in public
    maps_dir = ROOT / "remotion" / "public" / "maps"
    available_maps = {f.stem.lower() for f in maps_dir.glob("*.svg")} if maps_dir.exists() else set()

    for scene in spec.get("scenes", []):
        for beat in scene.get("beats", []):
            # 1. Map beats & region
            if beat.get("kind") in ("map_pin", "map"):
                r = (beat.get("region") or "").lower()
                if r and r not in available_maps:
                    # For Arab/Middle-East regions use middle_east; for everything else use world
                    arab_regions = {"arab", "arabia", "middle_east", "gcc", "levant", "egypt", "saudi", "iraq", "syria", "jordan", "uae", "gulf"}
                    is_arab = any(a in r for a in arab_regions)
                    if is_arab and "middle_east" in available_maps:
                        beat["region"] = "middle_east"
                    elif "world" in available_maps:
                        beat["region"] = "world"

            # 2. Hero icon & main icon
            if "hero_icon" in beat:
                beat["hero_icon"] = resolve_icon(beat["hero_icon"])
            if "icon" in beat:
                beat["icon"] = resolve_icon(beat["icon"])

            # 3. Badges array
            if "badges" in beat and isinstance(beat["badges"], list):
                for b in beat["badges"]:
                    if isinstance(b, dict) and "icon" in b:
                        b["icon"] = resolve_icon(b["icon"])

            # 4. Items array
            if "items" in beat and isinstance(beat["items"], list):
                for it in beat["items"]:
                    if isinstance(it, dict) and "icon" in it:
                        it["icon"] = resolve_icon(it["icon"])

            # 5. Points array (in map_pin)
            if "points" in beat and isinstance(beat["points"], list):
                for pt in beat["points"]:
                    if isinstance(pt, dict) and "icon" in pt:
                        pt["icon"] = resolve_icon(pt["icon"])

            # 6. Canvas elements
            if "elements" in beat and isinstance(beat["elements"], list):
                for el in beat["elements"]:
                    if isinstance(el, dict) and el.get("type") == "icon" and "name" in el:
                        # el["name"] is often an icon identifier
                        resolved = resolve_icon(el["name"])
                        el["name"] = _clean_key(resolved)

    return spec

# Keyword dictionary mapping Arabic and English keywords to specific icon names
KEYWORD_MAP: Dict[str, str] = {
    # History & Antiquity
    "أهرامات": "pyramid",
    "هرم": "pyramid",
    "pyramid": "pyramid",
    "فرعون": "pharaoh",
    "فراعنة": "pharaoh",
    "تاريخ": "scroll",
    "history": "scroll",
    "متحف": "museum",
    "آثار": "ruins",
    "قلعة": "castle",
    "حصن": "castle",
    "سيف": "sword",
    "معركة": "battle",
    "حرب": "shield",
    "تاج": "crown",
    "ملك": "king",

    # Monument & Architecture
    "معلم": "monument",
    "مسلة": "obelisk",
    "منارة": "lighthouse",
    "إسكندرية": "lighthouse",
    "قبة": "dome",
    "مئذنة": "minaret",
    "معبد": "temple",
    "تمثال": "statue",

    # Buildings & Cities
    "عاصمة": "city",
    "capital": "city",
    "مدينة": "city",
    "city": "city",
    "جامع": "mosque",
    "مسجد": "mosque",
    "قصر": "palace",
    "برج": "tower",
    "مبنى": "building",
    "رياض": "city",
    "درعية": "castle",
    "مكة": "mosque",
    "جدة": "port",

    # Maps & Geography
    "خريطة": "map",
    "map": "map",
    "موقع": "map_pin",
    "بوصلة": "compass",
    "نهر": "river",
    "نيل": "river",
    "جبل": "mountain",
    "صحراء": "desert",

    # World & Globe
    "عالم": "globe-2",
    "كوكب": "globe-2",
    "دولي": "globe-2",
    "global": "globe-2",

    # People & Society
    "شعب": "users",
    "سكان": "users",
    "population": "users",
    "قائد": "leader",
    "شخصية": "person",
    "مواطن": "user-round",

    # Rankings & Awards
    "ترتيب": "ranking",
    "ranking": "ranking",
    "مرتبة": "trophy",
    "بطولة": "trophy",
    "جائزة": "medal",
    "ميدالية": "medal",
    "تتويج": "trophy",
    "championship": "trophy",

    # Capital cities & civic
    "عاصمة-أيقونة": "landmark",
    "برلمان": "landmark",
    "متحف-بناء": "landmark",

    # Science & Tech
    "علم": "atom",
    "فلك": "telescope",
    "طاقة": "lightning",

    # Chart & Economy
    "اقتصاد": "chart_up",
    "أموال": "coins",
    "ذهب": "gold_bars",
    "تجارة": "money_bag",

    # Time & Ages
    "زمن": "clock",
    "قرن": "hourglass",
    "سنة": "calendar",

    # Fire & Energy
    "نار": "flame",
    "شرارة": "spark",
}

# Category defaults
CATEGORY_DEFAULTS: Dict[str, str] = {
    "history": "icons/history/monument.svg",
    "monument": "icons/monument/monument.svg",
    "map": "icons/map/map_pin.svg",
    "person": "icons/person/person.svg",
    "science": "icons/science/atom.svg",
    "number": "icons/number/target.svg",
    "arrow": "icons/arrow/arrow-right.svg",
    "fire": "icons/fire/flame.svg",
    "star": "icons/star/star.svg",
    "building": "icons/building/city.svg",
    "chart": "icons/chart/chart_up.svg",
    "time": "icons/time/clock.svg",
    "world": "icons/world/earth.svg",
    "book": "icons/book/book.svg",
    "sword": "icons/sword/sword.svg",
    "crown": "icons/crown/crown.svg",
    "coin": "icons/coin/gold_bars.svg",
    "ship": "icons/ship/ship.svg",
    "tree": "icons/tree/tree.svg",
}

def pick_icons_for_beat(text: str = "", query: str = "", category: str = "", n: int = 3) -> List[str]:
    combined = f"{text} {query}".lower()
    selected: List[str] = []

    # 1. Direct keyword match
    for kw, icon_name in KEYWORD_MAP.items():
        if kw in combined:
            path = _find_icon(icon_name)
            if path and path not in selected:
                selected.append(path)
            if len(selected) >= n:
                return selected

    # 2. Check category requested
    if category and category in CATEGORY_DEFAULTS:
        cpath = _find_icon(CATEGORY_DEFAULTS[category])
        if cpath not in selected:
            selected.append(cpath)

    # 3. Fallback pool
    pool = [
        "icons/history/pyramid.svg",
        "icons/building/city.svg",
        "icons/monument/mosque.svg",
        "icons/history/monument.svg",
        "icons/map/map_pin.svg",
        "icons/star/star.svg",
        "icons/coin/gold_bars.svg",
    ]
    for p in pool:
        if p not in selected:
            selected.append(p)
        if len(selected) >= n:
            break

    return selected[:n]

def get_icon_path(category: str, name: str) -> str:
    return _find_icon(name)
