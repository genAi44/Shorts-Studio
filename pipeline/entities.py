"""Entity -> visual system (single source of truth).

RULE: every entity named in the narration must get a visual that suits its type, in the scene of that sentence.
Geography is the strongest case: any place (village .. globe) gets a map.

Adding an entity type = ONE entry in ENTITY_REGISTRY (see docs/ENTITIES.md):
    id, label, llm_hint (what the extractor should look for), channel ("overlay" = map overlay, "beat" = a beat of
    one of `kinds`), required, and a `fallback` builder that returns a visible beat when the director did not draw it.

Detection is structural, never regex on Arabic: ONE llm call extracts typed entities per sentence (JSON), then every
entity is validated locally (Natural Earth / GeoNames in data/geodata.db; unknown places -> Nominatim with a visible
warning and a disk cache). Text is only ever cut on whole-word (whitespace token) boundaries.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from .config import ROOT, record_fallback

log = logging.getLogger("pipeline.entities")

CACHE_PATH = ROOT / "data" / "entity_cache.json"
NOMINATIM_CACHE = ROOT / "data" / "nominatim_cache.json"
SCHEMA_VERSION = 1

PUNCT = "،؛؟?!.,:;()[]{}\"'«»-–—…"

# ------------------------------------------------------------------ word-boundary helpers (no regex)


def tokens(text: str) -> List[str]:
    return str(text or "").split()


def bare(tok: str) -> str:
    return tok.strip(PUNCT)


# Arabic proclitics glued to the first word of a phrase: "وأوروبا" = و + أوروبا, "بآسيا" = ب + آسيا, "للعراق" = لـ + العراق
_CLITICS = ("و", "ف", "ب", "ل", "ك", "وب", "ول", "فب", "فل", "وك")   # never "ال": «كويت» is not a word of «الكويت»
_HAMZA = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ى": "ي", "ة": "ه"})


def _norm(tok: str) -> str:
    return "".join(ch for ch in tok if not "ً" <= ch <= "ْ" and ch != "ـ").translate(_HAMZA)


def _same_word(sent_tok: str, target: str, allow_clitic: bool) -> bool:
    a, b = _norm(sent_tok), _norm(target)
    if a == b:
        return True
    if not allow_clitic or len(b) < 3:
        return False
    if a.endswith(b) and a[:-len(b)] in _CLITICS:           # و + أوروبا, ب + آسيا, وال + أورال ...
        return True
    return b.startswith("ال") and a.startswith(("لل", "ولل", "فلل")) and a.endswith(b[2:]) and a[:-len(b[2:])] in ("لل", "ولل", "فلل")


def find_span(sentence: str, text: str) -> Optional[Tuple[int, int]]:
    """(first_token, last_token) of `text` inside `sentence`, matched on whole tokens only (a glued Arabic proclitic such as
    و / ب / ل / ال on the FIRST word is accepted; the span still covers whole whitespace tokens); None if absent."""
    st = [bare(t) for t in tokens(sentence)]
    tt = [bare(t) for t in tokens(text) if bare(t)]
    if not tt:
        return None
    for i in range(len(st) - len(tt) + 1):
        if st[i:i + len(tt)] == tt:
            return i, i + len(tt) - 1
    for i in range(len(st) - len(tt) + 1):                  # second chance: diacritics / hamza forms / one glued proclitic
        if all(_same_word(st[i + k], tt[k], allow_clitic=(k == 0)) for k in range(len(tt))):
            return i, i + len(tt) - 1
    return None


def cut_words(text: str, max_words: int) -> str:
    """Shorten on word boundaries only."""
    return " ".join(tokens(text)[:max_words])


# ------------------------------------------------------------------ registry


@dataclass
class EntityType:
    id: str
    label: str
    llm_hint: str
    channel: str                     # "overlay" (map overlay satisfies it) or "beat"
    kinds: Tuple[str, ...] = ()      # beat kinds that satisfy it (channel == "beat")
    required: bool = True
    fallback: Optional[Callable[[Dict[str, Any], str], Dict[str, Any]]] = None
    scales: Tuple[str, ...] = ()     # sub-types (place scales, terrain kinds, ...)


def _fb_year(e: Dict[str, Any], sentence: str) -> Dict[str, Any]:
    return {"kind": "year_counter", "title": "", "year": e.get("value"),
            "to_year": e.get("to"), "era": e.get("kind") or "year", "label": cut_words(e.get("label_ar") or sentence, 6)}


def _fb_quantity(e: Dict[str, Any], sentence: str) -> Dict[str, Any]:
    cmp_ = [c for c in (e.get("compare") or []) if isinstance(c, dict) and c.get("value") is not None][:4]
    if cmp_:
        items = [{"label": cut_words(e.get("label_ar") or "", 3), "value": float(e["value"])}] + \
                [{"label": cut_words(str(c.get("label") or ""), 3), "value": float(c["value"])} for c in cmp_]
        return {"kind": "bars", "title": cut_words(e.get("label_ar") or sentence, 5), "items": items}
    return {"kind": "stat", "title": "", "number": f"{e.get('value'):,}" if isinstance(e.get("value"), (int, float)) else str(e.get("value")),
            "label": cut_words((e.get("label_ar") or "") + " " + (e.get("unit") or ""), 6), "layout": "ring"}


def _fb_person(e: Dict[str, Any], sentence: str) -> Dict[str, Any]:
    return {"kind": "person_card", "name": cut_words(e.get("name_ar") or "", 5), "years": _years(e),
            "role": cut_words(e.get("role_ar") or "", 6), "query": e.get("name_en") or ""}


_NATURE_ICON = {"animal": "lucide:paw-print", "plant": "lucide:leaf", "element": "lucide:atom", "organ": "lucide:heart-pulse",
                "phenomenon": "lucide:cloud-lightning"}


def _fb_nature(e: Dict[str, Any], sentence: str) -> Dict[str, Any]:
    """Licensed photo when one resolves; otherwise the card shows a procedural Iconify icon (never placeholder text)."""
    icon = _NATURE_ICON.get(str(e.get("scale") or ""), "lucide:sparkles")
    try:
        from .visual_tools import search_icons
        name = str(e.get("name_en") or "").strip().lower()
        hit = search_icons(name, set_name="lucide", limit=1) if name else []
        if hit and name in str(hit[0]["id"]).lower():  # a fuzzy hit (Lion -> star) is worse than the scale's default icon
            icon = hit[0]["id"]
    except Exception:  # noqa: BLE001
        pass
    return {"kind": "photo", "query": e.get("name_en") or e.get("name_ar") or "", "text": cut_words(e.get("name_ar") or "", 4),
            "must_show": e.get("name_en") or "", "icon": icon}


def _fb_flag(e: Dict[str, Any], sentence: str) -> Dict[str, Any]:
    return {"kind": "icons", "title": cut_words(e.get("name_ar") or "", 3), "items": [{"icon": "flag", "label": cut_words(e.get("name_ar") or "", 2)}]}


def _years(e: Dict[str, Any]) -> str:
    b, d = e.get("born"), e.get("died")
    return f"{b}–{d}" if b and d else str(b or d or "")


ENTITY_REGISTRY: Dict[str, EntityType] = {r.id: r for r in [
    EntityType("place", "مكان جغرافي", "any place: village, town, city, capital, region, country, continent, ocean/sea, or the whole Earth (scale)",
               channel="overlay", scales=("village", "town", "city", "capital", "region", "country", "continent", "ocean", "globe")),
    EntityType("terrain", "تضاريس", "river, mountain range, desert, lake, strait, island, or a named geographic line such as the equator or the Europe-Asia boundary (subtype)", channel="overlay",
               scales=("river", "mountain", "desert", "lake", "strait", "island", "boundary")),
    EntityType("conflict", "حدود/حرب/معركة", "war, battle, border or treaty (sides a and b, year)", channel="overlay"),
    EntityType("route", "طريق/رحلة", "trade route, expedition or journey with ordered stops (lat/lon each)", channel="overlay"),
    EntityType("time", "سنة/قرن/حقبة", "a year, century or era (value = year number; to = end year for a span)", channel="beat",
               kinds=("year_counter", "timeline", "timeline_card", "deep_time_slider"), fallback=_fb_year),
    EntityType("quantity", "رقم/قياس", "a measurement: area, population, height, distance, money, percent (value, unit, compare[])", channel="beat",
               kinds=("stat", "stat_ring_v2", "bars", "pie_chart", "line_chart", "money_waterfall", "dot_matrix_population",
                      "elevation_profile", "balance_meter"), fallback=_fb_quantity),
    EntityType("person", "شخصية تاريخية", "a historical person (name_ar, name_en, born, died, role_ar)", channel="beat",
               kinds=("person_card", "photo"), fallback=_fb_person),
    EntityType("nature", "حيوان/نبات/عنصر/عضو/ظاهرة", "animal, plant, chemical element, body organ or natural phenomenon", channel="beat",
               kinds=("photo", "icons"), fallback=_fb_nature, scales=("animal", "plant", "element", "organ", "phenomenon")),
    EntityType("empire", "إمبراطورية/دولة تاريخية", "a historical empire or state (from/to years, centre lat/lon)", channel="overlay"),
    EntityType("flag", "علم", "derived automatically from every country-scale place; never extracted", channel="overlay", required=False),
]}


def register(entity_type: EntityType) -> None:
    ENTITY_REGISTRY[entity_type.id] = entity_type


# ------------------------------------------------------------------ extraction (one structural llm call)

EXTRACT_SYSTEM = """You extract visual entities from Arabic narration for a video system. Return JSON only:
{"scenes":[{"id":"<scene id>","sentences":[{"i":0,"entities":[ ... ]}]}]}  (same scenes and sentence order as the input, empty list if none).
Entity shapes (text = the exact words as written in the sentence, whole words only, copy them verbatim):
 {"type":"place","scale":"village|town|city|capital|region|country|continent|ocean|globe","text":"..","name_ar":"..","name_en":"..","iso2":"..","lat":0,"lon":0}
 {"type":"terrain","scale":"river|mountain|desert|lake|strait|island|boundary","text":"..","name_ar":"..","name_en":"..","lat":0,"lon":0,"iso2":".."}  (a named mountain range is scale "mountain"; the equator / tropics / prime meridian / the Europe-Asia boundary are scale "boundary")
 {"type":"conflict","text":"..","name_ar":"..","a":{"name_ar":"..","lat":0,"lon":0},"b":{"name_ar":"..","lat":0,"lon":0},"year":0}
 {"type":"route","text":"..","name_ar":"..","stops":[{"name_ar":"..","lat":0,"lon":0}]}
 {"type":"time","scale":"year|century|era","text":"..","value":1453,"to":null,"label_ar":".."}
 {"type":"quantity","scale":"area|population|height|distance|money|percent","text":"..","value":0,"unit":"..","label_ar":"..","compare":[{"label":"..","value":0}]}
 {"type":"person","text":"..","name_ar":"..","name_en":"..","born":0,"died":0,"role_ar":".."}
 {"type":"nature","scale":"animal|plant|element|organ|phenomenon","text":"..","name_ar":"..","name_en":"..","lat":0,"lon":0}
 {"type":"empire","text":"..","name_ar":"..","name_en":"..","from":0,"to":0,"lat":0,"lon":0}
Rules: lat/lon in decimal degrees (use your knowledge; they are verified later). Never invent entities that are not in the
sentence. Spoken numbers must be converted to digits (value). Do not output flags. Every real place gets an entity."""


def _split_sentences(narration: str) -> List[str]:
    from .direct import sentences
    return sentences(narration)


def _payload(script: Dict[str, Any]) -> Dict[str, Any]:
    from .scriptspec import scenes_of
    return {"scenes": [{"id": sc["id"], "sentences": _split_sentences(sc.get("narration", ""))} for sc in scenes_of(script)]}


def _cache_load() -> Dict[str, Any]:
    try:
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _cache_save(data: Dict[str, Any]) -> None:
    try:
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        CACHE_PATH.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass


def llm_extract(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """The one structural llm call. Returns the raw json or None (the caller records a visible warning)."""
    try:
        from . import llm
        raw = llm.call_llm_json("director", EXTRACT_SYSTEM, json.dumps(payload, ensure_ascii=False), temperature=0.1)
        return raw if isinstance(raw, dict) and isinstance(raw.get("scenes"), list) else None
    except Exception as e:  # noqa: BLE001 - reported below, never silent
        log.warning("entity extraction call failed: %s", e)
        return None


def extract_script(script: Dict[str, Any], extractor: Optional[Callable[[Dict[str, Any]], Optional[Dict[str, Any]]]] = None,
                   geo: Any = None) -> Dict[str, List[List[Dict[str, Any]]]]:
    """{scene_id: [entities_of_sentence_0, entities_of_sentence_1, ...]} - validated, cached, never raises.
    `extractor(payload) -> {"scenes":[{"id","sentences":[{"i","entities":[..]}]}]}` lets tests inject a fixed plan."""
    payload = _payload(script)
    key = hashlib.sha1((json.dumps(payload, ensure_ascii=False, sort_keys=True) + str(SCHEMA_VERSION)).encode("utf-8")).hexdigest()
    cache = _cache_load()
    raw = cache.get(key) if extractor is None else None
    if raw is None:
        raw = (extractor or llm_extract)(payload_for_llm(payload))
        if raw is None:
            record_fallback("entity extraction unavailable: no entity visuals can be enforced (legacy geo detection only)",
                            beat_id="entities")
            return {}
        if extractor is None:
            cache[key] = raw
            _cache_save(cache)
    out: Dict[str, List[List[Dict[str, Any]]]] = {}
    by_scene = {s.get("id"): s for s in (raw.get("scenes") or []) if isinstance(s, dict)}  # the model sometimes returns strings in the list
    for sc in payload["scenes"]:
        sents = sc["sentences"]
        got = by_scene.get(sc["id"], {}).get("sentences") or []
        got = got if isinstance(got, list) else []
        per: List[List[Dict[str, Any]]] = []
        # the model also answers with bare lists ("sentences": [[ent, ..], [], ..]): sentence i = list i
        got = [{"i": j, "entities": g} if isinstance(g, list) else g for j, g in enumerate(got)]
        for i, sentence in enumerate(sents):
            item = next((g for g in got if isinstance(g, dict) and g.get("i") == i), got[i] if i < len(got) and isinstance(got[i], dict) else {})
            ents = [v for v in (validate_entity(e, sentence, geo) for e in (item.get("entities") or []) if isinstance(e, dict)) if v]
            per.append(ents)
        out[sc["id"]] = per
    return out


def payload_for_llm(payload: Dict[str, Any]) -> Dict[str, Any]:
    return payload


# ------------------------------------------------------------------ local validation


# ------------------------------------------------------------------ obligations, validation, enforcement


def unmet(entities_per_sentence: List[List[Dict[str, Any]]], beats: List[Dict[str, Any]],
          overlay_names: Optional[set] = None) -> List[Tuple[int, Dict[str, Any]]]:
    """(sentence_index, entity) pairs whose required visual is missing. overlay-channel entities count as satisfied
    when their name is among `overlay_names` (names the scene's map overlay actually draws)."""
    miss: List[Tuple[int, Dict[str, Any]]] = []
    for i, ents in enumerate(entities_per_sentence):
        kind = beats[i].get("kind") if i < len(beats) and isinstance(beats[i], dict) else None
        for e in ents:
            et = ENTITY_REGISTRY[e["type"]]
            if not et.required:
                continue
            if et.channel == "overlay":
                names = {e.get("name_ar"), e.get("name_en")} - {None, ""}
                if overlay_names is None or not (names & overlay_names):
                    miss.append((i, e))
            elif kind not in et.kinds:
                miss.append((i, e))
    return miss


def plan_errors(script: Dict[str, Any], plan: Dict[str, List[Any]], ents: Dict[str, List[List[Dict[str, Any]]]]) -> List[str]:
    """Errors for the director: sentences whose registered (non-overlay) entity has no suitable beat in its plan.
    Overlay entities (places...) are always drawn by the map overlay builder, so only beat channels are plannable."""
    errs: List[str] = []
    for sid, per in ents.items():
        beats = plan.get(sid) or []
        if not isinstance(beats, list):
            continue
        kinds = [b.get("kind") if isinstance(b, dict) else None for b in beats]
        for i, es in enumerate(per):
            for e in es:
                et = ENTITY_REGISTRY[e["type"]]
                if et.required and et.channel == "beat" and (i >= len(kinds) or kinds[i] not in et.kinds):
                    errs.append(f"{sid}[{i}]: '{e.get('text')}' is a {et.id} entity: the beat must be one of {', '.join(et.kinds)}")
    return errs


def entity_frame(e: Dict[str, Any], words: List[Dict[str, Any]], dur_frames: int) -> int:
    """Frame at which the entity is spoken (matched on whole words in the timed words)."""
    from .geo_overlay import _find_word_timestamp
    s, _e, _i = _find_word_timestamp(str(e.get("text") or e.get("name_ar") or ""), words, max(1.0, dur_frames / 30.0), 0.15)
    return max(0, int(round(s * 30)))


def covered(e: Dict[str, Any], beats: List[Dict[str, Any]], frame: int) -> bool:
    et = ENTITY_REGISTRY[e["type"]]
    return any(isinstance(b, dict) and b.get("kind") in et.kinds and int(b.get("from", 0)) - 12 <= frame < int(b.get("from", 0)) + int(b.get("dur", 0))
               and not any(a <= frame < c for a, c in (b.get("hide") or [])) for b in beats)


INSERT_FRAMES = 66  # an inserted shot lasts ~2.2 s


def ensure_visuals(beats: List[Dict[str, Any]], per_sentence: List[List[Dict[str, Any]]], words: List[Dict[str, Any]],
                   dur_frames: int, photo: Optional[Callable[..., Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
    """For every required beat-channel entity with no suitable beat on screen when it is spoken, INSERT a visible
    fallback shot at that moment (the beat under it is hidden for the shot). Logged, marked `_fallback`, never silent."""
    out = [dict(b) for b in beats]
    for ents in per_sentence:
        for e in ents:
            et = ENTITY_REGISTRY[e["type"]]
            if not (et.required and et.channel == "beat") or et.fallback is None:
                continue
            f = entity_frame(e, words, dur_frames)
            if covered(e, out, f):
                continue
            fb = et.fallback(e, str(e.get("text") or ""))
            if photo is not None and fb["kind"] in ("photo", "person_card"):
                try:  # licensed photo for the inserted shot (same resolver the planned photo beats use)
                    pb = photo({"kind": "photo", "query": fb.get("query") or fb.get("name"), "text": fb.get("text") or fb.get("name"),
                                "must_show": fb.get("must_show") or fb.get("query") or ""}, str(e.get("text") or ""))
                    if isinstance(pb, dict) and pb.get("img"):
                        fb["img"] = pb["img"]
                except Exception as ex:  # noqa: BLE001
                    record_fallback(f"photo for {et.id} '{e.get('text')}' unavailable ({ex}): symbolic visual", beat_id=et.id)
            start = max(0, f - 4)
            dur = min(INSERT_FRAMES, max(24, dur_frames - start))
            for b in out:  # an earlier inserted shot ends where this one starts (no two inserted shots stacked)
                if b.get("_fallback") and int(b.get("from", 0)) < start < int(b.get("from", 0)) + int(b.get("dur", 0)):
                    b["dur"] = start - int(b.get("from", 0))
            fb.update({"from": start, "dur": dur, "_fallback": True, "_entity": et.id})
            for b in out:  # hide whatever is under the inserted shot so texts never stack
                if isinstance(b, dict) and int(b.get("from", 0)) < start + dur and start < int(b.get("from", 0)) + int(b.get("dur", 0)):
                    b["hide"] = list(b.get("hide") or []) + [[start, start + dur]]
            record_fallback(f"{et.id} entity '{e.get('text')}' had no suitable visual when spoken: inserted {fb['kind']} shot", beat_id=f"{et.id}@{f}")
            out.append(fb)
    out.sort(key=lambda b: int(b.get("from", 0)))
    return out


def no_consecutive_repeat(beats: List[Dict[str, Any]]) -> List[str]:
    """Names of beat kinds repeated back to back (the same component must not open two consecutive scenes)."""
    bad = []
    for a, b in zip(beats, beats[1:]):
        if a.get("kind") == b.get("kind") and a.get("kind") not in ("bigtext", "map"):
            bad.append(str(a.get("kind")))
    return bad


# ------------------------------------------------------------------ geo bridge for the map overlay


def geo_mentions(per_sentence: List[List[Dict[str, Any]]], words: List[Dict[str, Any]], sentences: List[str]) -> List[Dict[str, Any]]:
    """Validated place/terrain/route/conflict/empire entities -> overlay mention dicts (timed on the spoken word)."""
    from .geo_overlay import mention_from_entity
    ms: List[Dict[str, Any]] = []
    for i, ents in enumerate(per_sentence):
        for e in ents:
            if ENTITY_REGISTRY[e["type"]].channel != "overlay":
                continue
            ms.extend(mention_from_entity(e, words))
    ms.sort(key=lambda m: m["start_sec"])
    return ms


def extraction_enabled() -> bool:
    """ENTITY_EXTRACT=0 turns the llm extraction off (explicit user choice); unit tests never call the live model."""
    if os.environ.get("ENTITY_EXTRACT", "1").strip().lower() in ("0", "false", "no", "off"):
        return False
    return not os.environ.get("PYTEST_CURRENT_TEST")


def ensure_plan(script: Dict[str, Any], geo: Any = None) -> Dict[str, List[List[Dict[str, Any]]]]:
    """Extract (once, cached) and attach the validated entity plan to the script as `_entities`."""
    plan = script.get("_entities")
    if isinstance(plan, dict) and not any(e for per in plan.values() if isinstance(per, list) for e in per):
        plan = None  # a saved plan with no entity at all (e.g. a reply once misparsed) is re-read; the reply cache makes it free
    if (not isinstance(plan, dict) or not plan) and not extraction_enabled():
        return {}
    if not isinstance(plan, dict) or not plan:
        plan = extract_script(script, geo=geo)
        script["_entities"] = plan
    return plan


def _overlay_names(sc: Dict[str, Any]) -> set:
    ov = sc.get("map_overlay") or {}
    return {w.get("name_ar") for w in ov.get("waypoints", [])} | {f.get("label") for f in ov.get("features", [])}


def spec_gaps(spec: Dict[str, Any]) -> List[str]:
    """The rule, checked on a finished spec: every required entity must have its visual where it is spoken.
    Used by the QA gate and by tests/test_entities.py (which fails when a sentence has an entity but no visual)."""
    gaps: List[str] = []
    for sc in spec.get("scenes") or []:
        names = _overlay_names(sc)
        words = sc.get("words") or []
        for per in sc.get("entity_plan") or []:
            for e in per:
                et = ENTITY_REGISTRY.get(e.get("type"))
                if not et or not et.required:
                    continue
                if et.channel == "overlay":
                    want = {e.get("name_ar"), e.get("name_en")}
                    if e["type"] == "route":
                        want = {s.get("name_ar") for s in e.get("stops", [])}
                    elif e["type"] == "conflict":
                        want = {e["a"].get("name_ar"), e["b"].get("name_ar")}
                    if not ((want - {None, ""}) & names):
                        gaps.append(f"{sc.get('id')}: {et.id} '{e.get('text')}' has no map")
                elif not covered(e, sc.get("beats") or [], entity_frame(e, words, int(sc.get("dur", 150)))):
                    gaps.append(f"{sc.get('id')}: {et.id} '{e.get('text')}' has no {'/'.join(et.kinds)} visual")
    return gaps

# Re-exported so `pipeline.entities.<name>` keeps working.
from .entities_resolve import (  # noqa: E402,F401
    _CONTINENT_CODE,
    _LAST_NOMINATIM,
    _OCEANS,
    _RATE,
    _continent_members,
    _km,
    _nominatim_cache,
    _num,
    _resolve_place,
    _resolve_terrain,
    geocode_online,
    validate_entity,
)
