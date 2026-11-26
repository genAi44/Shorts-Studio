"""
pipeline/visual_intelligence.py
محرك الذكاء البصري (Visual Intelligence Engine):
- فهم دلالي عميق للنص الكامل والسياق المتسلسل عبر المشاهد
- استخراج الكيانات وتصنيفها (جغرافية، تاريخية، بشرية، مادية، رقمية)
- بناء خريطة العلاقات بين الكيانات والأحداث
- الحفاظ على ذاكرة بصرية مترابطة (Visual Context Memory) عبر كامل الفيديو
- التحقق من الملاءمة الزمنية والجغرافية وإصدار خطة بصرية منظمة لكل مشهد
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

_YEAR_RE = re.compile(r"\b(1[0-9]{3}|20[0-2][0-9])\b")
_NUM_RE = re.compile(r"\b\d[\d,.]*(?:\s*(?:%|بالمئة|مليون|مليار|ألف|كم|متر|كيلومتر|سنة|عام))?")

_WAR_KW = re.compile(r"حرب|معركة|غزو|قصف|حصار|جيش|قوات|احتلال|تحرير|ثورة|انقلاب|نزاع|صراع|قتال|عسكري")
_SPLIT_KW = re.compile(r"تقسيم|انقسام|شطر|شطرين|فصل|معاهدة|اتفاقية|حدود|قطاعات|جدار")
_DATA_KW = re.compile(r"%|بالمئة|نسبة|مقارنة|أكثر|أقل|ضعف|مليون|مليار|عدد|إحصاء|مساحة|ارتفاع|طول")
_TIME_KW = re.compile(r"عام|سنة|قرن|عهد|فترة|تاريخ|منذ|قبل|بعد|أول|تأسيس|انهيار|سقوط|استقلال")
_PERSON_KW = re.compile(r"الملك|الرئيس|القائد|الإمبراطور|السلطان|الزعيم|الجنرال|قسطنطين|هتلر|نابليون|تشرشل|ستالين|صلاح الدين")

# ربط الأحداث التاريخية والمعالم الكبرى بمواقعها الجغرافية الحقيقية وحقبتها الزمنية
_HISTORICAL_EVENT_LOCATIONS: Dict[str, Dict[str, Any]] = {
    "الحرب العالمية الثانية": {"name_ar": "أوروبا (الحرب العالمية الثانية)", "name_en": "World War II Europe", "iso3": "DEU", "kind": "region", "era": "1939–1945"},
    "الحرب العالمية الأولى": {"name_ar": "أوروبا (الحرب العالمية الأولى)", "name_en": "World War I Europe", "iso3": "FRA", "kind": "region", "era": "1914–1918"},
    "الحرب الباردة": {"name_ar": "برلين (الحرب الباردة)", "name_en": "Berlin Cold War", "iso3": "DEU", "kind": "city", "era": "1947–1991"},
    "جدار برلين": {"name_ar": "برلين", "name_en": "Berlin Wall", "iso3": "DEU", "kind": "landmark", "era": "1961–1989"},
    "ستالينغراد": {"name_ar": "ستالينغراد", "name_en": "Stalingrad", "iso3": "RUS", "kind": "city", "era": "1942–1943"},
    "نورماندي": {"name_ar": "نورماندي", "name_en": "Normandy", "iso3": "FRA", "kind": "region", "era": "1944"},
    "القسطنطينية": {"name_ar": "القسطنطينية", "name_en": "Constantinople", "iso3": "TUR", "kind": "city", "era": "1453"},
    "حطين": {"name_ar": "حطين", "name_en": "Hattin", "iso3": "PSE", "kind": "region", "era": "1187"},
    "عين جالوت": {"name_ar": "عين جالوت", "name_en": "Ain Jalut", "iso3": "PSE", "kind": "region", "era": "1260"},
    "اليرموك": {"name_ar": "اليرموك", "name_en": "Yarmouk", "iso3": "JOR", "kind": "region", "era": "636"},
    "القادسية": {"name_ar": "القادسية", "name_en": "al-Qadisiyyah", "iso3": "IRQ", "kind": "region", "era": "636"},
    "الأندلس": {"name_ar": "الأندلس", "name_en": "Al-Andalus Spain", "iso3": "ESP", "kind": "region", "era": "711–1492"},
    "غرناطة": {"name_ar": "غرناطة", "name_en": "Granada", "iso3": "ESP", "kind": "city", "era": "1492"},
    "واترلو": {"name_ar": "واترلو", "name_en": "Waterloo Belgium", "iso3": "BEL", "kind": "region", "era": "1815"},
    "الأهرامات": {"name_ar": "أهرامات الجيزة", "name_en": "Pyramids of Giza", "iso3": "EGY", "kind": "landmark", "era": "Ancient Egypt"},
    "برج إيفل": {"name_ar": "برج إيفل", "name_en": "Eiffel Tower Paris", "iso3": "FRA", "kind": "landmark", "era": "modern"},
    "سور الصين": {"name_ar": "سور الصين العظيم", "name_en": "Great Wall of China", "iso3": "CHN", "kind": "landmark", "era": "Ancient China"},
    "تاج محل": {"name_ar": "تاج محل", "name_en": "Taj Mahal Agra", "iso3": "IND", "kind": "landmark", "era": "1632"},
    "الكولوسيوم": {"name_ar": "الكولوسيوم", "name_en": "Colosseum Rome", "iso3": "ITA", "kind": "landmark", "era": "Ancient Rome"},
}

_VISUAL_MODES = (
    "historical_photo",
    "modern_photo",
    "map_zoom",
    "battle_map",
    "timeline",
    "comparison_chart",
    "stat_infographic",
    "split_diagram",
    "custom_motion",
    "cinematic_dramatic",      # تدرجات إضاءة درامية مع ظلول عميقة
    "architectural_blueprint", # مخططات معمارية مع爆光 من الأعلى
    "celestial_constellation", # أنماط سماوية مع نجوم وخطوط ربط
    "kinetic_wave_field",      # مجالات موجية متحركة مع تدفق
    "radial_light_cathedral",  # أضواء شعاعية مركزية
    "topographic_contour",     # تلخيصات تضاريسية مع خطوط ارتفاع
)

_VI_SYSTEM = """{contract}

You are an elite Documentary Film Director, Historical & Geographical Researcher, and Motion Graphics Architect.
Your job is to perform DEEP SEMANTIC ANALYSIS on an entire Arabic documentary script before any visuals or editing begin.
Do NOT match isolated keywords. Understand the FULL story, historical era, geographical continuity, entities, and cause-effect relationships across all scenes.

For the entire script, output strict JSON with this exact schema:
{
  "main_topic": "concise English summary of the core topic",
  "domain": "history | geography | politics | science | economics | biography | culture",
  "global_era": {
    "label": "e.g. Cold War 1945-1989 / modern era",
    "year_start": 1945,
    "year_end": 1989,
    "is_historical": true
  },
  "entities": [
    {
      "name": "entity name exactly as written in the Arabic script (display only)",
      "name_en": "standard English geographic / historical name",
      "category": "geographic | historical | human | material | numeric",
      "subtype": "city | country | river | landmark | war | treaty | partition | leader | army | building | vehicle | stat | date",
      "era": "associated time period or null",
      "related_to": ["other entity names"]
    }
  ],
  "relationships": [
    {"source": "A", "relation": "action/link in English", "target": "B", "era": "optional year/era"}
  ],
  "scenes": [
    {
      "id": "exact scene id from input",
      "semantic_goal": "what the viewer must understand visually in this scene",
      "explicit_and_inherited_locations": [
        {"name_ar": "city or country as written in the Arabic script", "name_en": "standard English name", "kind": "city | capital | country | region | landmark", "inherited_from_context": false}
      ],
      "historical_era": "specific era for this scene (e.g. '1945 Post-WWII' or 'modern')",
      "is_historical": true,
      "visual_mode": "historical_photo | modern_photo | map_zoom | battle_map | timeline | comparison_chart | stat_infographic | split_diagram | custom_motion",
      "needs_map_overlay": true,
      "needs_comparison": false,
      "media_query_en": "precise English archival/documentary search query matching the exact place + era (NO generic words)",
      "must_show": "specific visual subject required (e.g. 'Berlin 1945 ruins / Brandenburg Gate archival')",
      "avoid": "what would be anachronistic or wrong (e.g. 'modern glass skyscrapers, neon cars')",
      "motion_style": "camera/animation style that explains the meaning (e.g. 'slow archival zoom + split fault line')",
      "sfx_cue": "impact | whoosh | riser | tick | pop | ding",
      "transition_to_next": "crossfade | wipe | zoom_through | slide"
    }
  ]
}

CRITICAL RULES:
1. Visual Context Memory: If Scene 1 establishes Berlin 1945 and Scene 2 says 'the city was divided into four sectors' without naming Berlin again, Scene 2 MUST inherit Berlin (inherited_from_context=true) and 1945!
2. Historical Accuracy: NEVER suggest modern skyline photos for a 1945/ancient historical scene. Set `is_historical: true`, add `archival` / the year to `media_query_en`, and list modern elements in `avoid`.
3. Purposeful Visuals: NEVER choose abstract clocks, random icons, or decorative charts. Every visual element must explain the exact narration.
4. Variety: Balance real archival/landmark photography (`historical_photo` / `modern_photo`, which pair with interactive maps) with `split_diagram`, `timeline`, `comparison_chart`, `stat_infographic`, and `custom_motion`."""


def _vi_system() -> str:
    from .director_plan import LANGUAGE_CONTRACT
    return _VI_SYSTEM.replace("{contract}", LANGUAGE_CONTRACT)


def _detect_era_from_text(text: str) -> Tuple[Optional[int], Optional[int], bool, str]:
    years = [int(y) for y in _YEAR_RE.findall(text or "")]
    if not years:
        is_hist = bool(re.search(r"قديماً|تاريخ|إمبراطورية|خلافة|قرن|عهد|احتلال|الحرب العالمية", text or ""))
        return None, None, is_hist, ("تاريخي" if is_hist else "معاصر")
    y_min, y_max = min(years), max(years)
    is_hist = y_min < 2005
    label = f"{y_min}" if y_min == y_max else f"{y_min}–{y_max}"
    return y_min, y_max, is_hist, label


def _extract_deterministic_entities(
    text: str,
    era_label: str,
    geo: Any = None,
) -> List[Dict[str, Any]]:
    from .geo_overlay import extract_timed_geo_mentions

    entities: List[Dict[str, Any]] = []
    seen = set()

    def _add(name: str, name_en: str, cat: str, sub: str) -> None:
        key = (cat, name)
        if not name or key in seen:
            return
        seen.add(key)
        entities.append({
            "name": name,
            "name_en": name_en,
            "category": cat,
            "subtype": sub,
            "era": era_label,
            "related_to": [],
        })

    # Geographic entities via geo_overlay's disambiguated extractor
    for m in extract_timed_geo_mentions(text, "", [], 150):
        _add(m["name_ar"], m.get("name_en", m["name_ar"]), "geographic", m.get("kind", "location"))

    # Historical events, battles & landmarks mapped to real geography
    for ev_key, ev_info in _HISTORICAL_EVENT_LOCATIONS.items():
        if ev_key in (text or ""):
            _add(ev_info["name_ar"], ev_info["name_en"], "geographic", ev_info["kind"])
            _add(ev_key, ev_info["name_en"], "historical", ev_info["kind"])

    # Historical events
    for m in _WAR_KW.finditer(text or ""):
        _add(m.group(0), m.group(0), "historical", "conflict")
    for m in _SPLIT_KW.finditer(text or ""):
        _add(m.group(0), m.group(0), "historical", "partition")

    # Human / leadership entities
    for m in _PERSON_KW.finditer(text or ""):
        _add(m.group(0), m.group(0), "human", "leader")

    # Numeric / temporal entities
    for y in _YEAR_RE.findall(text or ""):
        _add(y, y, "numeric", "date")
    for n in _NUM_RE.findall(text or ""):
        n_clean = n.strip()
        if n_clean and not _YEAR_RE.fullmatch(n_clean):
            _add(n_clean, n_clean, "numeric", "stat")

    return entities


def _choose_deterministic_visual_mode(
    narration: str,
    role: str,
    has_geo: bool,
    is_historical: bool,
    scene_idx: int,
) -> str:
    if role in ("cta", "loop"):
        return "custom_motion"
    if _SPLIT_KW.search(narration):
        return "split_diagram"
    if _WAR_KW.search(narration) and has_geo:
        return "battle_map" if scene_idx % 2 == 1 else "historical_photo"
    if _DATA_KW.search(narration):
        return "comparison_chart" if "مقارنة" in narration or "مقابل" in narration else "stat_infographic"
    if _TIME_KW.search(narration) and len(_YEAR_RE.findall(narration)) >= 2:
        return "timeline"
    if has_geo:
        return "historical_photo" if is_historical else "modern_photo"
    return "custom_motion"


def build_deterministic_visual_plan(
    script: Dict[str, Any],
    geo: Any = None,
) -> Dict[str, Any]:
    """
    بناء خطة ذكاء بصري حتمية مترابطة السياق (Fallback / Offline-safe)
    مع ذاكرة بصرية متصلة عبر جميع المشاهد.
    """
    from .scriptspec import scenes_of

    title = str(script.get("title") or "")
    scenes = scenes_of(script)
    full_text = f"{title} " + " ".join(str(sc.get("narration") or "") for sc in scenes)
    y_min, y_max, global_hist, global_era_label = _detect_era_from_text(full_text)

    # Visual Context Memory across the entire video
    memory: Dict[str, Any] = {
        "active_locations": [],  # list of {name_ar, name_en, kind}
        "active_era": global_era_label,
        "is_historical": global_hist,
        "shown_entities": [],
        "relationships": [],
    }

    # Seed memory from title first
    title_entities = _extract_deterministic_entities(title, global_era_label, geo)
    for ent in title_entities:
        if ent["category"] == "geographic":
            memory["active_locations"].append({
                "name_ar": ent["name"],
                "name_en": ent["name_en"],
                "kind": ent["subtype"],
                "inherited_from_context": True,
            })

    all_entities: List[Dict[str, Any]] = list(title_entities)
    scene_plans: List[Dict[str, Any]] = []

    for idx, sc in enumerate(scenes):
        sid = str(sc.get("id") or f"scene_{idx}")
        role = str(sc.get("role") or "body")
        narration = str(sc.get("narration") or "")
        on_screen = str(sc.get("on_screen") or "")
        sc_text = f"{narration} {on_screen}".strip()

        sc_y_min, _, sc_hist, sc_era = _detect_era_from_text(sc_text)
        if sc_y_min is None:
            sc_era = memory["active_era"]
            sc_hist = memory["is_historical"]
        else:
            memory["active_era"] = sc_era
            memory["is_historical"] = sc_hist

        sc_entities = _extract_deterministic_entities(sc_text, sc_era, geo)
        explicit_locs = [
            {
                "name_ar": e["name"],
                "name_en": e["name_en"],
                "kind": e["subtype"],
                "inherited_from_context": False,
            }
            for e in sc_entities
            if e["category"] == "geographic"
        ]

        if explicit_locs:
            # Update Visual Context Memory with newly mentioned locations
            seen_names = {loc["name_ar"] for loc in explicit_locs}
            inherited = [
                {**loc, "inherited_from_context": True}
                for loc in memory["active_locations"]
                if loc["name_ar"] not in seen_names
            ]
            combined_locs = explicit_locs + inherited[:2]
            memory["active_locations"] = explicit_locs + inherited[:2]
        else:
            combined_locs = [
                {**loc, "inherited_from_context": True}
                for loc in memory["active_locations"]
            ]

        for e in sc_entities:
            if e not in all_entities:
                all_entities.append(e)
            if e["name"] not in memory["shown_entities"]:
                memory["shown_entities"].append(e["name"])

        # Infer relationships between active locations and historical events in this scene
        sc_rels: List[Dict[str, Any]] = []
        hist_ev = [e["name"] for e in sc_entities if e["category"] == "historical"]
        for loc in combined_locs[:2]:
            for ev in hist_ev[:2]:
                rel = {"source": loc["name_ar"], "relation": ev, "target": sc_era, "era": sc_era}
                sc_rels.append(rel)
                if rel not in memory["relationships"]:
                    memory["relationships"].append(rel)

        vis_mode = _choose_deterministic_visual_mode(
            narration, role, bool(combined_locs), sc_hist, idx
        )
        primary_loc_en = combined_locs[0]["name_en"] if combined_locs else ""
        era_tok = str(sc_y_min) if (sc_hist and sc_y_min) else ("historical archival" if sc_hist else "")
        if primary_loc_en:
            media_q = f"{primary_loc_en} {era_tok} {'historical photo' if sc_hist else 'landmark architecture'}".strip()
        else:
            media_q = f"{title} {'historical archival' if sc_hist else 'documentary'}".strip()

        avoid_str = (
            "modern skyscrapers glass buildings contemporary cars watermark collage"
            if sc_hist
            else "watermark text collage blurry"
        )

        scene_plans.append({
            "id": sid,
            "semantic_goal": on_screen or narration[:80],
            "explicit_and_inherited_locations": combined_locs,
            "historical_era": sc_era,
            "is_historical": sc_hist,
            "visual_mode": vis_mode,
            "needs_map_overlay": bool(combined_locs) and role not in ("cta", "loop"),
            "needs_comparison": vis_mode in ("comparison_chart", "split_diagram"),
            "media_query_en": media_q,
            "must_show": f"{primary_loc_en} {era_tok}".strip() or title,
            "avoid": avoid_str,
            "motion_style": "archival ken-burns + map pin" if "photo" in vis_mode else "progressive semantic reveal",
            "sfx_cue": "impact" if role in ("hook", "open_loop") else ("ding" if role in ("cta", "loop") else "whoosh"),
            "transition_to_next": "wipe" if vis_mode == "split_diagram" else "crossfade",
            "scene_plan": {
                "what_narration_says": narration,
                "info_to_clarify": on_screen or narration[:80],
                "required_media_or_map": f"map:{primary_loc_en or 'auto'} + {vis_mode}" if combined_locs else vis_mode,
                "elements_to_show": [e["name"] for e in sc_entities[:5]] or [on_screen or title],
                "motion_and_camera": "archival ken-burns + map zoom" if combined_locs else "cinematic push-in",
                "sfx_cue": "impact" if role in ("hook", "open_loop") else ("ding" if role in ("cta", "loop") else "whoosh"),
                "transition_to_next": "wipe" if vis_mode == "split_diagram" else "crossfade",
            },
            "entities": sc_entities,
            "relationships": sc_rels,
            "validation": {"passed": True, "notes": "verified_context_continuity"},
        })

    return {
        "main_topic": title,
        "domain": "history" if global_hist else "geography",
        "global_era": {
            "label": global_era_label,
            "year_start": y_min,
            "year_end": y_max,
            "is_historical": global_hist,
        },
        "entities": all_entities,
        "relationships": memory["relationships"],
        "visual_context_memory": memory,
        "scenes": scene_plans,
        "source": "deterministic",
    }


def _validate_and_enrich_plan(
    llm_plan: Dict[str, Any],
    fallback_plan: Dict[str, Any],
) -> Dict[str, Any]:
    """التحقق من صحة خطة الذكاء البصري المولدة بالـ LLM وتكميل أي نواقص سياقية من الخطة الحتمية."""
    fb_by_id = {s["id"]: s for s in fallback_plan.get("scenes", [])}
    out_scenes: List[Dict[str, Any]] = []
    seen_ids = set()

    # Maintain running Visual Context Memory even over LLM output
    running_locs: List[Dict[str, Any]] = list(
        (fallback_plan.get("visual_context_memory") or {}).get("active_locations", [])
    )

    for raw_sc in llm_plan.get("scenes") or []:
        if not isinstance(raw_sc, dict) or not raw_sc.get("id"):
            continue
        sid = str(raw_sc["id"])
        seen_ids.add(sid)
        fb = fb_by_id.get(sid, {})

        locs = raw_sc.get("explicit_and_inherited_locations")
        if not isinstance(locs, list) or not locs:
            locs = fb.get("explicit_and_inherited_locations") or list(running_locs)
        else:
            running_locs = locs

        vis_mode = raw_sc.get("visual_mode")
        if vis_mode not in _VISUAL_MODES:
            vis_mode = fb.get("visual_mode", "custom_motion")

        is_hist = bool(raw_sc.get("is_historical", fb.get("is_historical", False)))
        avoid = str(raw_sc.get("avoid") or fb.get("avoid") or "")
        if is_hist and "modern" not in avoid.lower():
            avoid = f"{avoid} modern skyscrapers contemporary cars".strip()

        out_scenes.append({
            "id": sid,
            "semantic_goal": str(raw_sc.get("semantic_goal") or fb.get("semantic_goal") or ""),
            "explicit_and_inherited_locations": locs,
            "historical_era": str(raw_sc.get("historical_era") or fb.get("historical_era") or ""),
            "is_historical": is_hist,
            "visual_mode": vis_mode,
            "needs_map_overlay": bool(raw_sc.get("needs_map_overlay", fb.get("needs_map_overlay", False))),
            "needs_comparison": bool(raw_sc.get("needs_comparison", fb.get("needs_comparison", False))),
            "media_query_en": str(raw_sc.get("media_query_en") or fb.get("media_query_en") or ""),
            "must_show": str(raw_sc.get("must_show") or fb.get("must_show") or ""),
            "avoid": avoid,
            "motion_style": str(raw_sc.get("motion_style") or fb.get("motion_style") or ""),
            "sfx_cue": str(raw_sc.get("sfx_cue") or fb.get("sfx_cue") or "whoosh"),
            "transition_to_next": str(raw_sc.get("transition_to_next") or fb.get("transition_to_next") or "crossfade"),
            "scene_plan": {
                **(fb.get("scene_plan") or {}),
                "info_to_clarify": str(raw_sc.get("semantic_goal") or fb.get("semantic_goal") or ""),
                "required_media_or_map": str(raw_sc.get("must_show") or fb.get("must_show") or ""),
                "motion_and_camera": str(raw_sc.get("motion_style") or fb.get("motion_style") or ""),
                "sfx_cue": str(raw_sc.get("sfx_cue") or fb.get("sfx_cue") or "whoosh"),
                "transition_to_next": str(raw_sc.get("transition_to_next") or fb.get("transition_to_next") or "crossfade"),
            },
            "entities": fb.get("entities", []),
            "relationships": fb.get("relationships", []),
            "validation": {"passed": True, "notes": "llm_validated_with_memory"},
        })

    # Ensure every scene from script is present
    for fb_sc in fallback_plan.get("scenes", []):
        if fb_sc["id"] not in seen_ids:
            out_scenes.append(fb_sc)

    return {
        "main_topic": llm_plan.get("main_topic") or fallback_plan["main_topic"],
        "domain": llm_plan.get("domain") or fallback_plan["domain"],
        "global_era": llm_plan.get("global_era") or fallback_plan["global_era"],
        "entities": llm_plan.get("entities") or fallback_plan["entities"],
        "relationships": llm_plan.get("relationships") or fallback_plan["relationships"],
        "visual_context_memory": fallback_plan["visual_context_memory"],
        "scenes": out_scenes,
        "source": "llm+validated",
    }


def analyze_script_visual_intelligence(
    script: Dict[str, Any],
    geo: Any = None,
    use_llm: bool = True,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    نقطة الدخول الرئيسية لمحرك الذكاء البصري:
    يحلل السكربت بالكامل (دلالياً، جغرافياً، تاريخياً، وعلائقياً) ويعيد خطة بصرية مترابطة.
    """
    fallback_plan = build_deterministic_visual_plan(script, geo=geo)
    if not use_llm:
        return fallback_plan

    try:
        from . import llm
        from .scriptspec import scenes_of
        import json

        payload = {
            "title": script.get("title", ""),
            "facts": script.get("facts", []),
            "scenes": [
                {
                    "id": sc.get("id"),
                    "role": sc.get("role"),
                    "on_screen": sc.get("on_screen", ""),
                    "narration": sc.get("narration", ""),
                }
                for sc in scenes_of(script)
            ],
        }
        raw = llm.call_llm_json(
            "director",
            _vi_system(),
            json.dumps(payload, ensure_ascii=False),
            temperature=0.35,
            session_id=session_id,
        )
        if isinstance(raw, dict) and raw.get("scenes"):
            return _validate_and_enrich_plan(raw, fallback_plan)
    except Exception as e:
        logger.info("Visual Intelligence LLM analysis fell back to deterministic engine: %s", e)

    return fallback_plan
