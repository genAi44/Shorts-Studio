"""Split from `pipeline/icons.py` (re-exported there); see that module."""
from __future__ import annotations
from typing import List, Dict, Optional
from .config import cfg, record_fallback
from .icons import _find_icon, _has_whole_word  # noqa: E402


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
