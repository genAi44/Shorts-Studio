"""Auto Icon Picker for Shorts Studio beats.
Uses fast keyword matching (no LLM call) on beat text and query to select relevant
SVG icons from the local bundle in remotion/public/icons/.
"""
from __future__ import annotations
import os
import re
from pathlib import Path
from typing import List, Dict, Optional

from .config import cfg, record_fallback

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
    "citizen": "icons/person/user-round.svg",
    "senate": "icons/building/parliament.svg",
    "colosseum": "icons/history/temple.svg",
    "aqueduct": "icons/monument/bridge.svg",
    "road": "icons/map/route.svg",
    "broken_wall": "icons/history/ruins.svg",
    "chip": "icons/science/gear.svg",
    "snowflake": "icons/fire/spark.svg",
    "world_map": "icons/map/globe.svg",
    "numbers": "icons/number/ranking.svg",
    "number": "icons/number/hash.svg",
    "bar_chart": "icons/chart/chart-bar.svg",
    "arrow_right": "icons/arrow/arrow-right.svg",
    "arrow_left": "icons/arrow/arrow-left.svg",
    "arrow_up": "icons/arrow/arrow-up.svg",
    "arrow_down": "icons/arrow/arrow-down.svg",
    "warning": "icons/arrow/target.svg",
    "check": "icons/star/badge.svg",
    "question": "icons/science/bulb.svg",
}


def _has_whole_word(text: str, word: str) -> bool:
    """Checks whole-word match in Arabic/English using Unicode non-word boundaries or space splitting."""
    w = word.strip().lower()
    if not w or not text:
        return False
    pattern = rf"(?<![\w\u0600-\u06FF])(?:ال)?{re.escape(w)}(?![\w\u0600-\u06FF])"
    return bool(re.search(pattern, text.lower()))


def _clean_key(name: str) -> str:
    s = name.lower().replace("\\", "/").strip()
    if s.endswith(".svg"):
        s = s.rsplit(".svg", 1)[0]
    if "/" in s:
        s = s.split("/")[-1]
    return s


def _find_icon(name: str, beat_id: str = "unknown", beat: Optional[dict] = None) -> str:
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

    # Whole-word token match on filename parts (no arbitrary substring matching)
    clean_tokens = set(re.split(r"[-_\s]+", clean))
    for k, v in _AVAILABLE_ICONS.items():
        k_tokens = set(re.split(r"[-_\s.]+", k))
        if clean_tokens and (clean_tokens <= k_tokens or k_tokens <= clean_tokens):
            return v

    record_fallback(f"unknown_icon:{name}", beat_id=beat_id, beat=beat)
    # Dynamic fallback: pick from diverse pool instead of always returning monument.svg
    # (monument.svg caused Roman-pillar repetition across unrelated videos)
    diverse_fallbacks = [
        "icons/star/star.svg",
        "icons/map/compass.svg",
        "icons/world/globe-2.svg",
        "icons/chart/chart-bar.svg",
        "icons/crown/trophy.svg",
        "icons/building/landmark.svg",
        "icons/history/monument.svg",
    ]
    beat_text = str((beat or {}).get("text") or (beat or {}).get("narration") or "").lower()
    for kw, icon_name in KEYWORD_MAP.items():
        if kw in beat_text:
            candidate = _find_icon(icon_name, beat_id=beat_id)  # one level only, no recursion
            if candidate and candidate != "icons/history/monument.svg":
                return candidate
    # Rotate through fallback pool using beat_id hash to avoid same icon repeating
    idx = abs(hash(beat_id)) % len(diverse_fallbacks)
    return diverse_fallbacks[idx]


def resolve_icon(icon_path: str, beat_id: str = "unknown", beat: Optional[dict] = None) -> str:
    """Ensures any icon path requested by director/LLM exists on disk in remotion/public/."""
    if not icon_path:
        record_fallback("empty_icon_path", beat_id=beat_id, beat=beat)
        return "icons/world/globe-2.svg"
    clean = icon_path.strip().replace("\\", "/")
    if clean.startswith("public/"):
        clean = " ".join(clean.split())[len("public/"):]
    if clean.startswith("/"):
        clean = clean.lstrip("/")

    # If it directly exists on disk in remotion/public
    if (ROOT / "remotion" / "public" / clean).exists():
        return clean

    # Resolve through alias or token match
    resolved = _find_icon(clean, beat_id=beat_id, beat=beat)
    if (ROOT / "remotion" / "public" / resolved).exists():
        return resolved

    record_fallback(f"missing_icon_file:{icon_path}", beat_id=beat_id, beat=beat)
    return "icons/history/monument.svg"


def sanitize_spec_assets(spec: dict) -> dict:
    """Walks the entire Remotion spec and validates/sanitizes all icon and map paths."""
    if not isinstance(spec, dict):
        return spec

    # Check maps in public
    maps_dir = ROOT / "remotion" / "public" / "maps"
    available_maps = {f.stem.lower() for f in maps_dir.glob("*.svg")} if maps_dir.exists() else set()

    for scene in spec.get("scenes", []):
        sc_id = scene.get("id", "scene")
        for bi, beat in enumerate(scene.get("beats", [])):
            beat_id = str(beat.get("id") or f"{sc_id}:{beat.get('kind', 'beat')}:{bi}")
            # 1. Map beats & region
            if beat.get("kind") in ("map_pin", "map"):
                r = (beat.get("region") or "").lower()
                if r and r not in available_maps:
                    record_fallback(f"unknown_map_region:{r}", beat_id=beat_id, beat=beat)
                    arab_regions = {"arab", "arabia", "middle_east", "gcc", "levant", "egypt", "saudi", "iraq", "syria", "jordan", "uae", "gulf"}
                    r_tokens = set(re.split(r"[-_\s]+", r))
                    is_arab = bool(r_tokens & arab_regions)
                    if is_arab and "middle_east" in available_maps:
                        beat["region"] = "middle_east"
                    elif "world" in available_maps:
                        beat["region"] = "world"

            # 2. Hero icon & main icon
            if "hero_icon" in beat:
                beat["hero_icon"] = resolve_icon(beat["hero_icon"], beat_id=beat_id, beat=beat)
            if "icon" in beat:
                beat["icon"] = resolve_icon(beat["icon"], beat_id=beat_id, beat=beat)

            # 3. Badges array — resolve and deduplicate icons within the same beat so hero + badges never repeat the same SVG
            if "badges" in beat and isinstance(beat["badges"], list):
                used_icons = {beat.get("hero_icon")} if beat.get("hero_icon") else set()
                diverse_pool = [
                    "icons/star/star.svg",
                    "icons/map/compass.svg",
                    "icons/science/bulb.svg",
                    "icons/crown/trophy.svg",
                    "icons/chart/trend-up.svg",
                    "icons/history/shield.svg",
                    "icons/world/globe-2.svg",
                    "icons/building/landmark.svg",
                ]
                for b in beat["badges"]:
                    if isinstance(b, dict) and "icon" in b:
                        resolved_ic = resolve_icon(b["icon"], beat_id=beat_id, beat=beat)
                        if resolved_ic in used_icons:
                            for alt_ic in diverse_pool:
                                if alt_ic not in used_icons and (ROOT / "remotion" / "public" / alt_ic).exists():
                                    resolved_ic = alt_ic
                                    break
                        b["icon"] = resolved_ic
                        used_icons.add(resolved_ic)

            # 4. Items array
            if "items" in beat and isinstance(beat["items"], list):
                for it in beat["items"]:
                    if isinstance(it, dict) and "icon" in it:
                        it["icon"] = resolve_icon(it["icon"], beat_id=beat_id, beat=beat)

            # 5. Points array (in map_pin)
            if "points" in beat and isinstance(beat["points"], list):
                for pt in beat["points"]:
                    if isinstance(pt, dict) and "icon" in pt:
                        pt["icon"] = resolve_icon(pt["icon"], beat_id=beat_id, beat=beat)

            # 5b. Network nodes diversity — force unique icons per node so all nodes never look identical
            if "nodes" in beat and isinstance(beat["nodes"], list):
                used_node_icons: set = set()
                _node_pool = [
                    "icons/map/compass.svg", "icons/chart/chart-bar.svg", "icons/star/star.svg",
                    "icons/crown/trophy.svg", "icons/world/globe-2.svg", "icons/building/landmark.svg",
                    "icons/science/atom.svg", "icons/arrow/trending-up.svg", "icons/person/users.svg",
                ]
                for ni, node in enumerate(beat["nodes"]):
                    if not isinstance(node, dict):
                        continue
                    if "icon" in node:
                        node["icon"] = resolve_icon(node["icon"], beat_id=f"{beat_id}:node{ni}", beat=beat)
                    if node.get("icon") in used_node_icons:
                        # Pick next unused icon from diversity pool
                        for alt in _node_pool:
                            if alt not in used_node_icons and (ROOT / "remotion" / "public" / alt).exists():
                                node["icon"] = alt
                                break
                    used_node_icons.add(node.get("icon", ""))

            # 6. Canvas elements
            if "elements" in beat and isinstance(beat["elements"], list):
                for el in beat["elements"]:
                    if isinstance(el, dict) and el.get("type") == "icon" and "name" in el:
                        raw_icon_name = str(el["name"] or "").strip()
                        if ":" in raw_icon_name or raw_icon_name.lower() in (
                            "question", "help", "help-circle", "sparkles", "star", "shield",
                            "fire", "flame", "crown", "coin", "coins", "globe", "clock",
                            "hourglass", "pin", "map-pin", "map", "compass", "book", "scale",
                            "mountain", "wave", "sun", "lock", "user", "users", "trophy",
                            "medal", "eye", "warning", "sword", "swords", "ship", "scroll",
                            "plane", "oil", "wheat", "factory", "anchor", "gavel", "key",
                            "bulb", "lightbulb", "atom", "dna", "chart", "mosque", "monument",
                            "landmark", "building", "city", "rocket", "brain", "heart", "bolt", "zap",
                            "info", "history"
                        ):
                            el["name"] = raw_icon_name
                        else:
                            resolved = resolve_icon(raw_icon_name, beat_id=beat_id, beat=beat)
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

# Closed list of exactly 20 icon categories for LLM classification
CLOSED_ICON_CATEGORIES: List[str] = [
    "history", "monument", "map", "person", "science",
    "number", "arrow", "fire", "star", "building",
    "chart", "time", "world", "book", "sword",
    "crown", "coin", "ship", "tree", "question",
]

# Category defaults (20 categories)
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
    "question": "icons/science/bulb.svg",
}


def pick_icon_category_llm(text: str = "", query: str = "", use_llm: bool = False) -> Optional[str]:
    """Uses a single cheap LLM call to pick an icon category from the closed 20-word list."""
    prompt_txt = " ".join(f"{text} {query}".split()[:30]).strip()
    if not prompt_txt:
        return None
    if use_llm or cfg("ICON_LLM_PICKER", "0") == "1":
        try:
            from . import llm
            sys_prompt = (
                "You are an icon classifier. Pickanges ONLY ONE word from this exact closed list of 20 categories:\n"
                + ", ".join(CLOSED_ICON_CATEGORIES)
                + "\nReply with JSON: {\"category\": \"<one_of_the_20_words>\"}"
            )
            res = llm.call_llm_json("director", sys_prompt, prompt_txt, temperature=0.0)
            cat = str((res or {}).get("category") or "").strip().lower()
            if cat in CLOSED_ICON_CATEGORIES:
                return cat
        except Exception:
            pass
    return None


def pick_icons_for_beat(
    text: str = "",
    query: str = "",
    category: str = "",
    n: int = 3,
    use_llm: bool = False,
    beat_id: str = "unknown",
    beat: Optional[dict] = None,
) -> List[str]:
    combined = f"{text} {query}".lower()
    selected: List[str] = []

    # 1. LLM closed-list category picker (if requested/enabled)
    llm_cat = category if category in CATEGORY_DEFAULTS else pick_icon_category_llm(text, query, use_llm=use_llm)
    if llm_cat and llm_cat in CATEGORY_DEFAULTS:
        cpath = _find_icon(CATEGORY_DEFAULTS[llm_cat], beat_id=beat_id, beat=beat)
        if cpath and cpath not in selected:
            selected.append(cpath)
        if len(selected) >= n:
            return selected[:n]

    # 2. Whole-word Arabic/English keyword match (no substring matching)
    for kw, icon_name in KEYWORD_MAP.items():
        if _has_whole_word(combined, kw):
            path = _find_icon(icon_name, beat_id=beat_id, beat=beat)
            if path and path not in selected:
                selected.append(path)
            if len(selected) >= n:
                return selected[:n]

    # 3. Fallback pool
    if not selected:
        record_fallback("no_keyword_icon_match", beat_id=beat_id, beat=beat)
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
