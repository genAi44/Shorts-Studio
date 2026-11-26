"""Studio mode (STUDIO_MODE=1): direction before code.

  Creative Director  -> treatment       (one call: message, visual world, per-scene intent / function / link)
  Visual Director    -> design system   (deterministic, from the video's style + preset: palette, type scale, motif,
                                         motion language, transition grammar, the preset's "not" list)
  Scene Designer     -> shot spec       (one call per scene, sees the previous shot: a device from a fixed catalogue,
                                         short texts, anchor words). Validated BEFORE any code (validate_shot).
  Animation Engineer -> TSX             (compile_shot: deterministic, kit recipes only, timing from the anchor words)
  Gates              -> scene_author's static check + 3-frame sandbox render; failures go back to the Scene Designer
                        with the problems (repair loop), then to the legacy path.

Everything a stage decided is written to outputs/<job>/production.json (the production bible).
"""
import hashlib
import json
import re
import shutil
import time
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from .config import FPS, cfg, record_fallback

COMPILER_VERSION = 5
CAMERA_PUSH = 1.06  # protocol 5.5: push-in 100 % -> 106 % across a scene
CAMERA_BOB = 6      # px of idle float, so a finished build never sits still
MAX_DESIGN_TRIES = 3          # first design + 2 retries on validator errors
MAX_REPAIRS = 2               # redesigns after a failed render gate
MECHANISMS = ("level", "flow", "filter", "tally", "shrink", "timeline")  # the drawing IS the explanation (remotion/src/mechanisms.tsx)
DEVICES = MECHANISMS + ("statement", "number", "pinned", "hub", "steps", "stack", "versus", "map")
REPEATABLE = {"map"}          # the only device that may follow itself (the map is the continuity)
MAX_SAME_DEVICE = 1           # a device is a look: twice in one video reads as a template
DEVICE_BUDGET = {"statement": 2, **{m: 2 for m in MECHANISMS}}  # a mechanism may return (the same sea, later): continuity
HERO_MIN_W = 520  # px: the [data-hero] drawing must be at least this wide at mid-scene (render gate)
MAX_SAME_ICON = 2
FUNCTIONS = ("claim", "contrast", "quantity", "sequence", "cause", "place", "person", "question")
LINKS = ("continue", "contrast", "deeper", "next_step")


# ------------------------------------------------------------------ LLM access

def _ask(system: str, user: str, temperature: float) -> Any:
    from . import llm
    r = llm.call_llm_json("director", system, user, temperature=temperature, timeout=150)
    if isinstance(r, str):
        r = json.loads(r[r.find("{"): r.rfind("}") + 1])
    return r


# ------------------------------------------------------------------ 1. Creative Director

TREATMENT_SYSTEM = """You are the creative director of an Arabic educational Shorts studio (vertical 1080x1920, ~60 s).
Before anyone designs a frame, you decide what the video MEANS and how it is told visually. Make decisions, not
suggestions. Do not choose colours or fonts (the art director owns those).

For the whole video: the one-sentence message, ONE visual world that every scene lives in (e.g. "an atlas being drawn
in front of us", "a ledger filling up", "a museum label wall") and its recurring motif, the scene of the climax
(strongest contrast) and the one breathing scene before it.
Also the CORE VISUAL METAPHOR: the one physical thing the explanation is drawn with (the sea whose level drops, the
river that is split, the jar shelf that empties), and 1-4 recurring OBJECTS that come back from scene to scene so the
scenes read as one story (Arabic nouns).
For every scene: its intent (what the viewer must understand or feel), its rhetorical function
(claim | contrast | quantity | sequence | cause | place | person | question), its energy 1-5 (hook high, build rising,
breath low, climax 5) and how it links to the PREVIOUS scene (continue | contrast | deeper | next_step).

Return JSON only:
{"message":"...","world":"...","motif":"...","core_metaphor":"...","objects":["..."],"climax":"scene id","breath":"scene id",
 "scenes":[{"id":"hook","intent":"...","function":"question","energy":5,"link":"continue"}]}"""


def treatment(script: Dict[str, Any], scenes: List[Dict[str, Any]], ask=_ask) -> Dict[str, Any]:
    items = [{"id": s["id"], "role": s.get("role"), "narration": " ".join(w["t"] for w in s.get("words") or [])} for s in scenes]
    user = json.dumps({"title": script.get("title"), "facts": script.get("facts", [])[:12], "scenes": items}, ensure_ascii=False)
    try:
        t = ask(TREATMENT_SYSTEM, user, 0.6)
    except Exception as e:  # noqa: BLE001 - a neutral treatment keeps the pipeline going, loudly
        record_fallback(f"studio treatment failed ({str(e)[:80]}): neutral treatment", beat_id="studio")
        t = {}
    return normalize_treatment(t, scenes)


def normalize_treatment(t: Any, scenes: List[Dict[str, Any]]) -> Dict[str, Any]:
    t = t if isinstance(t, dict) else {}
    by = {s.get("id"): s for s in t.get("scenes") or [] if isinstance(s, dict)}
    out = []
    for i, sc in enumerate(scenes):
        s = by.get(sc["id"], {})
        fn = s.get("function") if s.get("function") in FUNCTIONS else ("question" if sc.get("role") in ("hook", "open_loop") else "claim")
        link = s.get("link") if s.get("link") in LINKS else ("continue" if i else "continue")
        try:
            energy = max(1, min(5, int(s.get("energy", 3))))
        except (TypeError, ValueError):
            energy = 3
        out.append({"id": sc["id"], "intent": str(s.get("intent") or "")[:200], "function": fn, "energy": energy, "link": link})
    objs = [str(o)[:40] for o in t.get("objects") or [] if str(o).strip()][:4] if isinstance(t.get("objects"), list) else []
    return {"message": str(t.get("message") or "")[:240], "world": str(t.get("world") or "")[:200], "motif": str(t.get("motif") or "")[:120],
            "core_metaphor": str(t.get("core_metaphor") or "")[:200], "objects": objs,
            "climax": t.get("climax"), "breath": t.get("breath"), "scenes": out}


# ------------------------------------------------------------------ 2. Visual Director (deterministic)

# narrative link -> transition (types exist in remotion/src/transitions.tsx; <= 12 frames; next step enters from the
# left because Arabic reads right to left)
TRANSITION_GRAMMAR = {
    "continue": {"type": "fade", "durationInFrames": 8, "sfx": "none"},
    "contrast": {"type": "flip", "durationInFrames": 10, "sfx": "whip"},
    "deeper": {"type": "clock-wipe", "durationInFrames": 12, "sfx": "whoosh"},
    "next_step": {"type": "slide", "direction": "from-left", "durationInFrames": 10, "sfx": "whoosh"},
}
SWAP = {"fade": "wipe", "flip": "wipe", "clock-wipe": "fade", "slide": "wipe", "wipe": "fade"}


def design_system(style: Dict[str, Any], treatment_: Dict[str, Any]) -> Dict[str, Any]:
    from .style import theme_from_style
    theme = theme_from_style(style)
    guide = theme.pop("art_guide", "")
    nots = [ln.strip("-• ").strip() for ln in guide.splitlines() if ln.strip().startswith(("ليس", "- لا", "- ممنوع", "Not", "- Not"))]
    seed = int(style.get("seed", 42) or 42)
    return {
        "theme": theme,
        "type_scale": {"hero": 120, "hero_long": 92, "lead": 46, "label": 34},  # KeyLine derives lead/tail from the hero size
        "motif": {"ribbon_variant": seed % 3, "world": treatment_.get("world"), "motif": treatment_.get("motif"),
                  "core_metaphor": treatment_.get("core_metaphor"), "objects": treatment_.get("objects") or []},
        "motion": {"anticipation_s": 0.1, "entrance": "spring", "stagger_s": [0.25, 1.2], "hold_last_s": 0.4},
        "transitions": TRANSITION_GRAMMAR,
        "not": nots[:8],
        "preset_guide": guide,
    }


def transitions_for(links: List[str]) -> List[Dict[str, Any]]:
    """One transition per scene from its narrative link; never the same type more than twice in a row."""
    out: List[Dict[str, Any]] = []
    for i, link in enumerate(links):
        if i == 0:
            out.append({"type": "none", "durationInFrames": 8, "sfx": "none"})
            continue
        t = dict(TRANSITION_GRAMMAR.get(link, TRANSITION_GRAMMAR["continue"]))
        if len(out) >= 2 and out[-1]["type"] == out[-2]["type"] == t["type"]:
            t["type"] = SWAP[t["type"]]
        out.append(t)
    return out


# ------------------------------------------------------------------ 3. Scene Designer

SHOT_SYSTEM = """You are the scene designer of an Arabic educational Shorts studio (1080x1920). You design ONE scene as a
shot spec: you think visually and spatially, then pick a DEVICE from the catalogue and fill its slots. You do not write
code: an engineer compiles your spec exactly, and a validator rejects any spec that breaks the rules below.

THINK FIRST: "what physical thing does this sentence describe, and what does it DO?" (a level drops, a stream is
split, many become few, an area shrinks). The no-text test: with every word removed, the motion alone must still tell
what happens. Write that in "behavior". Prefer a MECHANISM; the generic devices are the fallback when nothing physical
changes. Draw the video's core_metaphor / recurring objects when the sentence is about them.

MECHANISMS (a big drawing that changes state on the "change_at" word; slot "mech"):
- level: a tank/sea whose level moves. mech {"from":0.9,"to":0.4,"from_label":"...","to_label":"...","change_at":"word"}
  from/to = fill 0..1.2 (above 1 = overflow). Labels <= 4 words (e.g. the year or state at each level).
- flow: one stream split into 2-4 branches. mech {"source":"...","branches":[{"label":"...","share":93,"icon":"lucide:x"}],
  "keep":1,"change_at":"word"}; share in % only when spoken, or when it is 100 minus the other spoken shares (93 spoken
  -> 7 allowed); else omit (equal widths); keep = index of the branch the sentence is about.
- filter: many become few (or none: to 0). mech {"from":24,"to":6,"icon":"lucide:x","from_label":"...","to_label":"...","change_at":"word"}
- tally: two quantities drawn as countable icons. mech {"sides":[{"label":"...","value":24,"icon":"lucide:x"},{...}]}
- shrink: an area that shrinks or grows (true area). mech {"from":950,"to":600,"unit":"كم²","from_label":"...",
  "to_label":"...","change_at":"word"}
- timeline: 2-5 dated events on an axis; a marker travels to each one on its word, earlier ones recede.
  mech {"events":[{"year":1453,"label":"...","at":"word"}]} years ascending, label <= 4 words.
Numbers inside a mechanism (filter/tally/shrink values, flow shares, timeline years) are shown on screen: spoken or
entity values only.
"mech_at" = the word on which the drawing enters.

DEVICES (generic fallback):
- statement: one hero icon (big, in a ring) + the key line. For a claim or a question with no number/list.
- number: one big rolling number in a ring + the key line. The sentence states one number or year.
- pinned: a card pinned on a string holding a number (or a hero icon) + a short label. One striking fact.
- hub: a centre icon with 2-6 satellites (icon + label). Sources, causes, parts of one thing.
- steps: 2-5 rising steps (labels). Stages, growth, ranking, "from X to Y".
- stack: 2-5 rows that build up (text + icon). Consequences, features, a dated list.
- versus: two sides (icon + label + optional number). Comparison, before/after, contrast.
- map: the vector map of the scene's places, big (always when the scene has a map, unless map_already_shown: then
  the places were already seen and a mechanism may explain the sentence instead) + the key line + optionally one
  number. The map is the hero: no hero icon.

TEXT: keyword = the KEY idea in 1-4 words (big, accent colour); lead / tail = optional small lines (<= 7 words each).
DIRECTION: a bare number does not say which way things go; read story_so_far and video_message ("33 metres by 2050"
in a story about a drying sea is a DROP). Never write a direction (rises / falls / grows / shrinks) the story contradicts.
On-screen text is the punchline, NOT a copy of the narration (the narration is already captioned). Arabic.
TIMING: every slot that appears has "at": a word copied EXACTLY from the scene's spoken words; it appears on that word.
ICONS: ONLY names from "available_icons" in the brief (any other name renders as a star).
Choose icons whose meaning matches (never a lightbulb for heritage, a star for corruption, a rising chart for a decline).
NUMBERS: only numbers that are spoken in the sentence or listed in its entities; "year": true for a year.
CONTINUITY: one visual world for the whole video; every device at most ONCE per video (map unlimited, statement and
each mechanism twice, never twice in a row):
see devices_used_so_far. Every on-screen line says something different (a tail never repeats an item).

Return JSON only:
{"device":"hub","why":"one line: why this device proves the sentence","behavior":"what the drawing does (mechanisms)",
 "keyword":"...","keyword_at":"word","lead":"...","tail":"...",
 "hero_icon":"lucide:x","hero_at":"word",
 "number":{"value":1453,"year":true,"suffix":"","label":"...","at":"word"},
 "items":[{"text":"...","icon":"lucide:x","at":"word"}],
 "sides":[{"label":"...","icon":"lucide:x","value":null,"at":"word"},{"label":"...","icon":"lucide:x","value":null,"at":"word"}],
 "mech":{},"mech_at":"word"}
Omit slots the device does not use."""


def shot_brief(ctx: Dict[str, Any], tscene: Dict[str, Any], ds: Dict[str, Any], prev: Optional[Dict[str, Any]], used: Dict[str, int],
               story: Optional[Dict[str, Any]] = None) -> str:
    brief = {
        "video_message": (story or {}).get("message"),
        "story_so_far": (story or {}).get("before", []),
        "scene": {"id": ctx["id"], "role": ctx.get("role"), "seconds": round(ctx["dur"] / FPS, 1), "sentence": ctx["sentence"],
                  "spoken_words": [w["t"] for w in ctx["words"]], "entities": ctx.get("entities", []),
                  "has_map": bool(ctx.get("map_overlay")), "map_already_shown": bool(ctx.get("map_seen"))},
        "direction": {k: tscene.get(k) for k in ("intent", "function", "energy", "link")},
        "video": {"world": ds["motif"].get("world"), "motif": ds["motif"].get("motif"), "core_metaphor": ds["motif"].get("core_metaphor"),
                  "objects": ds["motif"].get("objects") or [], "not": ds.get("not", [])},
        "previous_shot": {k: prev.get(k) for k in ("device", "keyword")} if prev else None,
        "devices_used_so_far": {k: v for k, v in used.items() if ":" not in k},
        "hero_icons_used": [k[5:] for k in used if k.startswith("hero:")],
        "icons_used_so_far": {k[5:]: v for k, v in used.items() if k.startswith("icon:")},
        "available_icons": sorted(_icon_names()),
    }
    return json.dumps(brief, ensure_ascii=False)


def design_shot(ctx, tscene, ds, prev, used, ask=_ask, errors: Optional[List[str]] = None, previous_spec=None,
                story: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    user = shot_brief(ctx, tscene, ds, prev, used, story)
    if errors:
        user += ("\n\nYour previous spec was REJECTED. Fix every problem and return the complete corrected spec.\nProblems:\n- "
                 + "\n- ".join(errors[:12]) + "\nPrevious spec:\n" + json.dumps(previous_spec, ensure_ascii=False))
    system = SHOT_SYSTEM + (("\n\nART DIRECTION OF THIS VIDEO (follow its essence and its 'not' list):\n" + ds["preset_guide"]) if ds.get("preset_guide") else "")
    try:
        r = ask(system, user, 0.7 if not errors else 0.4)
    except Exception as e:  # noqa: BLE001
        record_fallback(f"studio shot design failed for {ctx['id']} ({str(e)[:80]})", beat_id=ctx["id"])
        return None
    return r if isinstance(r, dict) else None


# ------------------------------------------------------------------ validator (before any code)

_TASHKEEL = re.compile(r"[ً-ْـ]")
_PUNCT = re.compile(r"[^\w؀-ۿ]")


def norm_word(w: str) -> str:
    return _PUNCT.sub("", _TASHKEEL.sub("", str(w or ""))).replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")


def find_word(words: List[Dict[str, Any]], anchor: Any) -> Optional[Dict[str, Any]]:
    a = norm_word(anchor)
    if not a:
        return None
    for w in words:
        if norm_word(w["t"]) == a:
            return w
    for w in words:
        n = norm_word(w["t"])
        if len(a) >= 3 and len(n) >= 3 and (a in n or n in a):
            return w
    return None


@lru_cache(maxsize=1)
def _icon_names() -> frozenset:
    """Icons the renderer can actually draw: the curated bundle (remotion/src/generated/iconifyBundle.json, ~280 icons).
    Any other name silently renders as a star (icons.tsx fallback), so it is rejected here."""
    p = Path(__file__).resolve().parent.parent / "remotion" / "src" / "generated" / "iconifyBundle.json"
    d = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    return frozenset(f"{s}:{n}" for s, v in (d.get("sets") or {}).items() for n in v)


def icon_ok(name: Any) -> bool:
    return isinstance(name, str) and name.strip().lower() in _icon_names()


def _nwords(s: Any) -> int:
    return len(str(s or "").split())


_UNITS = {"واحد": 1, "واحده": 1, "احد": 1, "احدى": 1, "اثنان": 2, "اثنين": 2, "اثنتان": 2, "اثنتين": 2, "اثنا": 2, "اثني": 2,
          "اثنتا": 2, "اثنتي": 2, "ثلاث": 3, "ثلاثه": 3,
          "اربع": 4, "اربعه": 4, "خمس": 5, "خمسه": 5, "ست": 6, "سته": 6, "سبع": 7, "سبعه": 7, "ثمان": 8, "ثماني": 8, "ثمانيه": 8,
          "تسع": 9, "تسعه": 9, "عشر": 10, "عشره": 10}
_TENS = {"عشرون": 20, "ثلاثون": 30, "اربعون": 40, "خمسون": 50, "ستون": 60, "سبعون": 70, "ثمانون": 80, "تسعون": 90}
_TENS.update({k[:-2] + "ين": v for k, v in list(_TENS.items())})
_HUNDREDS = {"مئه": 100, "مائه": 100, "مئتان": 200, "مئتين": 200, "مائتان": 200, "مائتين": 200}
_HUNDREDS.update({u + h: v * 100 for u, v in (("ثلاث", 3), ("اربع", 4), ("خمس", 5), ("ست", 6), ("سبع", 7), ("ثمان", 8), ("تسع", 9))
                  for h in ("مئه", "مائه")})
_SCALES = {"الف": 1000, "الاف": 1000, "مليون": 10 ** 6, "ملايين": 10 ** 6, "مليار": 10 ** 9, "مليارات": 10 ** 9}
_DUALS = {"الفان": 2000, "الفين": 2000, "مليونان": 2 * 10 ** 6, "مليونين": 2 * 10 ** 6}


_AR_PUNCT = "،؛؟٪"
_DECIMAL = {"فاصل", "فاصله"}


def _num_token(tok: str) -> Optional[Tuple[str, int]]:
    t = norm_word(tok).replace("ة", "ه").strip(_AR_PUNCT)  # norm_word keeps U+060C..: the Arabic comma is in that range
    cands = [t]
    if t.startswith("و") and len(t) > 2:
        cands.append(t[1:])
    for c in list(cands):  # attached prepositions: "بألفين", "لعشرين", "كمئة"
        if c[:1] in ("ب", "ل", "ك") and len(c) > 3:
            cands.append(c[1:])
    for cand in cands:
        for kind, table in (("unit", _UNITS), ("unit", _TENS), ("hundred", _HUNDREDS), ("scale", _SCALES), ("unit", _DUALS)):
            if cand in table:
                return kind, table[cand]
    return None


def word_numbers(text: str) -> set:
    """Numbers written in Arabic words ("عشرون ألف ومئتان وواحد وأربعون" -> 20241, "سبعة عشر مليون" -> 17000000)."""
    out, total, cur, seen, whole = set(), 0, 0, False, None

    def flush():
        nonlocal total, cur, seen, whole
        if seen:
            n = total + cur
            if whole is not None:  # "اثني عشر فاصل ستة" -> 12.6
                out.add(whole)
                n = whole + n / 10 ** len(str(n))
            out.add(round(n, 6) if isinstance(n, float) else n)
        total, cur, seen, whole = 0, 0, False, None

    for tok in str(text or "").split() + ["."]:
        if norm_word(tok).replace("ة", "ه").strip(_AR_PUNCT) in _DECIMAL and seen and whole is None:
            whole, total, cur, seen = total + cur, 0, 0, False
            continue
        nt = _num_token(tok)
        if nt is None:
            if whole is not None and not seen:  # "فاصل" with no digits after it: keep the whole part
                total, cur, seen, whole = whole, 0, True, None
            flush()
            continue
        kind, v = nt
        seen = True
        if kind == "scale":
            total += max(cur, 1) * v
            cur = 0
        elif kind == "hundred" and v == 100 and 0 < cur < 10:  # "ثلاث مئة"
            cur *= 100
        else:
            cur += v
        if tok.rstrip()[-1:] in "،,.؛:":  # a comma ends the number (after this word)
            flush()
    return out


_PERCENT = re.compile(r"[%٪]|بالمئ|بالمائ|في المئ|في المائ")


def _spoken(v: float, ctx: Dict[str, Any]) -> bool:
    from .direct import _number_in_text
    return _number_in_text(int(v) if float(v).is_integer() else v, ctx["sentence"]) or v in word_numbers(ctx["sentence"])


def number_ok(value: Any, ctx: Dict[str, Any]) -> bool:
    from .direct import _number_in_text
    if value is None:
        return False
    try:
        v = float(value)
    except (TypeError, ValueError):
        return False
    if _spoken(v, ctx):
        return True
    # derived from the sentence's own logic (Rule 1.4): the rest of a spoken percentage (93 % -> 7), and the 100 % whole
    if _PERCENT.search(ctx["sentence"]) and 0 < v <= 100 and (v == 100 or _spoken(100 - v, ctx)):
        return True
    for e in ctx.get("entities", []):  # verified entity values (numbers written in words are resolved there)
        for k in ("value", "year", "to", "from", "born", "died"):
            try:
                if e.get(k) is not None and float(e[k]) == v:
                    return True
            except (TypeError, ValueError):
                continue
    return False


_DIGITS = re.compile(r"\d[\d,]*(?:\.\d+)?")
_AR_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩٫٬", "0123456789.,")
ITEM_LIMITS = {"hub": (2, 6, 3), "steps": (2, 5, 3), "stack": (2, 5, 5)}


def shot_icons(shot: Optional[Dict[str, Any]]) -> List[str]:
    if not isinstance(shot, dict):
        return []
    m = shot.get("mech") if isinstance(shot.get("mech"), dict) else {}
    out = [shot.get("hero_icon"), m.get("icon")] + [b.get("icon") for b in m.get("branches") or [] if isinstance(b, dict)] \
        + [x.get("icon") for x in m.get("sides") or [] if isinstance(x, dict)] + [it.get("icon") for it in shot.get("items") or [] if isinstance(it, dict)]         + [sd.get("icon") for sd in shot.get("sides") or [] if isinstance(sd, dict)]
    return [i for i in dict.fromkeys(out) if i]


def count_use(used: Dict[str, int], shot: Dict[str, Any], sign: int = 1) -> None:
    """Device and icon budget of the video (the validator reads it)."""
    hero = ["hero:" + shot["hero_icon"]] if shot.get("hero_icon") else []
    for key in [shot["device"]] + ["icon:" + i for i in shot_icons(shot)] + hero:
        used[key] = used.get(key, 0) + sign


def validate_shot(shot: Any, ctx: Dict[str, Any], prev: Optional[Dict[str, Any]], used: Dict[str, int]) -> List[str]:
    if not isinstance(shot, dict):
        return ["the reply is not a JSON object"]
    errs: List[str] = []
    dev = shot.get("device")
    words = ctx["words"]
    spoken = ", ".join(w["t"] for w in words[:40])
    if dev not in DEVICES:
        return [f"device must be one of {', '.join(DEVICES)}"]
    has_map = bool(ctx.get("map_overlay"))
    if has_map and dev != "map" and not ctx.get("map_seen"):
        errs.append("this scene has a map (its places must be shown): device must be 'map'")
    if dev == "map" and not has_map:
        errs.append("device 'map' is only for scenes that have a map")
    if prev and dev == prev.get("device") and dev not in REPEATABLE:
        errs.append(f"the previous scene already uses '{dev}': choose another device")
    if dev not in REPEATABLE and used.get(dev, 0) >= DEVICE_BUDGET.get(dev, MAX_SAME_DEVICE):
        errs.append(f"'{dev}' was already used {used[dev]} times in this video: choose another device")
    prev_icons = set(shot_icons(prev))
    for ic in shot_icons(shot):
        if ic == shot.get("hero_icon") and used.get("hero:" + str(ic), 0) >= 1:
            errs.append(f"hero_icon '{ic}' was already the hero of an earlier scene: a hero is used once per video, pick another")
        elif ic == shot.get("hero_icon") and ic in prev_icons:
            errs.append(f"hero_icon '{ic}' was used by the previous scene: pick a different icon")
        if used.get("icon:" + str(ic), 0) >= MAX_SAME_ICON:
            errs.append(f"icon '{ic}' was already used {used['icon:' + str(ic)]} times in this video: pick a different icon")
    if dev == "versus" and len({sd.get("icon") for sd in shot.get("sides") or [] if isinstance(sd, dict)}) < 2:
        errs.append("the two sides of 'versus' need two different icons")
    kw = str(shot.get("keyword") or "").strip()
    if not kw or _nwords(kw) > 4:
        errs.append("keyword must be 1-4 words")
    for k in ("lead", "tail"):
        if _nwords(shot.get(k)) > 7:
            errs.append(f"{k} must be at most 7 words")
    if _nwords(kw) + _nwords(shot.get("lead")) + _nwords(shot.get("tail")) > 12:
        errs.append("too much text on screen (keyword + lead + tail > 12 words): the caption already carries the narration")
    if norm_word(" ".join([str(shot.get("lead") or ""), kw, str(shot.get("tail") or "")])) == norm_word(ctx["sentence"]):
        errs.append("the on-screen text copies the narration: write the punchline instead")

    mech = shot.get("mech") if isinstance(shot.get("mech"), dict) else {}
    mech_texts = [mech.get(k) for k in ("from_label", "to_label", "source", "unit")] \
        + [b.get("label") for b in mech.get("branches") or [] if isinstance(b, dict)] \
        + [sd.get("label") for sd in mech.get("sides") or [] if isinstance(sd, dict)] \
        + [ev.get("label") for ev in mech.get("events") or [] if isinstance(ev, dict)]
    texts = mech_texts + [kw, shot.get("lead"), shot.get("tail")] + [it.get("text") for it in shot.get("items") or [] if isinstance(it, dict)]         + [sd.get("label") for sd in shot.get("sides") or [] if isinstance(sd, dict)]         + [(shot.get("number") or {}).get("label") if isinstance(shot.get("number"), dict) else None]
    seen = set()
    for txt in texts:  # the same line twice on screen (tail repeating an item) is wasted space
        t = norm_word(str(txt or ""))
        if t and t in seen:
            errs.append(f"the text '{txt}' appears twice on screen: every slot must say something different")
        seen.add(t)
    counted = {str(v.get("value")).replace(".0", "") for v in [shot.get("number")] + list(shot.get("sides") or []) + list(mech.get("sides") or [])
               if isinstance(v, dict) and v.get("value") is not None}
    if dev in ("filter", "shrink"):
        counted |= {str(mech.get(k)).replace(".0", "") for k in ("from", "to") if mech.get(k) is not None}
    counted |= {str(ev.get("year")).replace(".0", "") for ev in mech.get("events") or [] if isinstance(ev, dict) and ev.get("year") is not None}
    counted |= {str(b.get("share")).replace(".0", "") for b in mech.get("branches") or [] if isinstance(b, dict) and b.get("share") is not None}
    for txt in texts:  # a number already rolling in a counter is not written again next to it
        for m in _DIGITS.findall(str(txt or "").translate(_AR_DIGITS)):
            if m.replace(",", "") in counted:
                errs.append(f"'{m}' in '{txt}' is already shown by the counter: remove it from the text")
    derived = {str(b.get("share")).replace(".0", "") for b in mech.get("branches") or []
               if isinstance(b, dict) and b.get("share") is not None and _complement(b, [x for x in mech.get("branches") or [] if isinstance(x, dict)], ctx)}
    for txt in texts:  # truth rule for numbers written inside any on-screen text, not only the number slot
        for m in _DIGITS.findall(str(txt or "").translate(_AR_DIGITS)):
            n = m.replace(",", "")
            if n and n not in derived and not number_ok(n, ctx):
                errs.append(f"'{m}' in the on-screen text '{txt}' is not spoken in the sentence nor in its entities: remove it")

    def need_at(label: str, at: Any):
        if not find_word(words, at):
            errs.append(f"{label}: '{at}' is not one of the spoken words; copy one exactly from: {spoken}")

    if shot.get("keyword_at"):
        need_at("keyword_at", shot.get("keyword_at"))
    if dev in ("statement", "pinned", "map") and shot.get("hero_icon") is not None or dev == "statement":
        if not icon_ok(shot.get("hero_icon")):
            errs.append(f"hero_icon '{shot.get('hero_icon')}' is not in available_icons")
    num = shot.get("number") if isinstance(shot.get("number"), dict) else None
    if dev == "number" and not num:
        errs.append("device 'number' needs a number")
    if dev == "pinned" and not num and not shot.get("hero_icon"):
        errs.append("device 'pinned' needs a number or a hero_icon")
    if num:
        if not number_ok(num.get("value"), ctx):
            errs.append(f"number {num.get('value')} is not spoken in the sentence nor in its entities: use a spoken number or drop it")
        need_at("number.at", num.get("at"))
        if _nwords(num.get("label")) > 5:
            errs.append("number.label must be at most 5 words")
    if dev in ITEM_LIMITS:
        lo, hi, maxw = ITEM_LIMITS[dev]
        items = [it for it in shot.get("items") or [] if isinstance(it, dict)]
        if not lo <= len(items) <= hi:
            errs.append(f"'{dev}' needs {lo}-{hi} items")
        for i, it in enumerate(items):
            if not str(it.get("text") or "").strip() or _nwords(it.get("text")) > maxw:
                errs.append(f"item {i + 1}: text must be 1-{maxw} words")
            if dev != "steps" and not icon_ok(it.get("icon")):
                errs.append(f"item {i + 1}: icon '{it.get('icon')}' is not in available_icons")
            if it.get("at"):
                need_at(f"item {i + 1}.at", it.get("at"))
    if dev in MECHANISMS:
        errs += _mech_errors(dev, mech, ctx, need_at)
        if not str(shot.get("behavior") or "").strip():
            errs.append("'behavior' is required for a mechanism: what the drawing does (the no-text test)")
        if shot.get("mech_at"):
            need_at("mech_at", shot.get("mech_at"))
    if dev == "versus":
        sides = [s for s in shot.get("sides") or [] if isinstance(s, dict)]
        if len(sides) != 2:
            errs.append("'versus' needs exactly 2 sides")
        for i, s in enumerate(sides[:2]):
            if not str(s.get("label") or "").strip() or _nwords(s.get("label")) > 3:
                errs.append(f"side {i + 1}: label must be 1-3 words")
            if not icon_ok(s.get("icon")):
                errs.append(f"side {i + 1}: icon '{s.get('icon')}' is not in available_icons")
            if s.get("value") is not None and not number_ok(s.get("value"), ctx):
                errs.append(f"side {i + 1}: value {s.get('value')} is not spoken in the sentence nor in its entities")
            if s.get("at"):
                need_at(f"side {i + 1}.at", s.get("at"))
    return list(dict.fromkeys(errs))


def _num(v: Any) -> Optional[float]:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _complement(b: Dict[str, Any], br: List[Dict[str, Any]], ctx: Dict[str, Any]) -> bool:
    """A share that is exactly 100 minus all the other shares, which are themselves spoken: derived, not invented."""
    others = [x for x in br if x is not b]
    vals = [_num(x.get("share")) for x in others]
    if not others or None in vals or not all(number_ok(x.get("share"), ctx) for x in others):
        return False
    v = _num(b.get("share"))
    return v is not None and abs(100 - sum(vals) - v) < 0.01


def _mech_errors(dev: str, m: Dict[str, Any], ctx: Dict[str, Any], need_at) -> List[str]:
    """Slot rules of the five mechanisms (shapes only; the truth rule for their numbers also runs on all texts)."""
    e: List[str] = []
    if not m:
        return [f"'{dev}' needs a 'mech' object (see the catalogue)"]
    if m.get("change_at"):
        need_at("mech.change_at", m.get("change_at"))
    for k in ("from_label", "to_label"):
        if _nwords(m.get(k)) > 4:
            e.append(f"mech.{k} must be at most 4 words")
    if dev == "level":
        a, b = _num(m.get("from")), _num(m.get("to"))
        if a is None or b is None or not (0 <= a <= 1.2 and 0 <= b <= 1.2) or abs(a - b) < 0.05:
            e.append("level: mech.from and mech.to are fills between 0 and 1.2 that differ by at least 0.05")
    elif dev == "flow":
        br = [b for b in m.get("branches") or [] if isinstance(b, dict)]
        if not 2 <= len(br) <= 4:
            e.append("flow needs 2-4 branches")
        if not str(m.get("source") or "").strip() or _nwords(m.get("source")) > 4:
            e.append("flow: mech.source is 1-4 words")
        for i, b in enumerate(br):
            if not str(b.get("label") or "").strip() or _nwords(b.get("label")) > 3:
                e.append(f"flow branch {i + 1}: label is 1-3 words")
            if b.get("icon") and not icon_ok(b.get("icon")):
                e.append(f"flow branch {i + 1}: icon '{b.get('icon')}' is not in available_icons")
            if b.get("share") is not None and not number_ok(b.get("share"), ctx) and not _complement(b, br, ctx):
                e.append(f"flow branch {i + 1}: share {b.get('share')} is not spoken in the sentence nor in its entities "
                         "(a share is allowed when it is 100 minus the other, spoken, shares): omit it")
        kp = m.get("keep")
        if kp is not None and not (isinstance(kp, int) and 0 <= kp < len(br)):
            e.append("flow: mech.keep is the index (0-based) of one branch")
    elif dev in ("filter", "shrink"):
        a, b = _num(m.get("from")), _num(m.get("to"))
        lo = 0 if dev == "filter" else 1e-9  # a filter may end with none left ("you buy nothing")
        if a is None or b is None or a <= 0 or b < lo or a == b or (dev == "filter" and b >= a):
            e.append(f"{dev}: mech.from and mech.to are " + ("numbers with 0 <= to < from" if dev == "filter" else "two positive numbers that differ"))
        for k in ("from", "to"):
            if m.get(k) is not None and not (k == "to" and dev == "filter" and _num(m.get(k)) == 0) and not number_ok(m.get(k), ctx):
                e.append(f"{dev}: mech.{k} = {m.get(k)} is not spoken in the sentence nor in its entities")
        if dev == "filter" and m.get("icon") and not icon_ok(m.get("icon")):
            e.append(f"filter: icon '{m.get('icon')}' is not in available_icons")
        if dev == "shrink" and _nwords(m.get("unit")) > 2:
            e.append("shrink: mech.unit is at most 2 words")
    elif dev == "timeline":
        ev = [x for x in m.get("events") or [] if isinstance(x, dict)]
        if not 2 <= len(ev) <= 5:
            e.append("timeline needs 2-5 events")
        ys = [_num(x.get("year")) for x in ev]
        for i, x in enumerate(ev):
            if ys[i] is None or not number_ok(x.get("year"), ctx):
                e.append(f"timeline event {i + 1}: year {x.get('year')} is not spoken in the sentence nor in its entities")
            if not str(x.get("label") or "").strip() or _nwords(x.get("label")) > 4:
                e.append(f"timeline event {i + 1}: label is 1-4 words")
            if x.get("at"):
                need_at(f"timeline event {i + 1}.at", x.get("at"))
        if None not in ys and any(b <= a for a, b in zip(ys, ys[1:])):
            e.append("timeline: events must be in strictly ascending years (two events in one year is not a timeline: use another device)")
    elif dev == "tally":
        sd = [x for x in m.get("sides") or [] if isinstance(x, dict)]
        if len(sd) != 2:
            e.append("tally needs exactly 2 sides")
        vals = [_num(x.get("value")) for x in sd]
        for i, x in enumerate(sd[:2]):
            if vals[i] is None or vals[i] <= 0 or not number_ok(x.get("value"), ctx):
                e.append(f"tally side {i + 1}: value must be a positive number spoken in the sentence or its entities")
            if not icon_ok(x.get("icon")):
                e.append(f"tally side {i + 1}: icon '{x.get('icon')}' is not in available_icons")
            if not str(x.get("label") or "").strip() or _nwords(x.get("label")) > 3:
                e.append(f"tally side {i + 1}: label is 1-3 words")
        if len(vals) == 2 and None not in vals and min(vals) > 0 and max(vals) / min(vals) > 30:
            e.append("tally: the two values differ more than 30x (one side would be a single icon): use shrink or number")
    return e


# ------------------------------------------------------------------ 4. Animation Engineer (deterministic compiler)

def _js(v: Any) -> str:
    return json.dumps(v, ensure_ascii=False)


HERO_CAP = 0.25  # the hero is on screen by 25 % of the scene at the latest (an empty first half fails the sparse gate)
_CAP: Dict[str, float] = {"s": 1e9}


def _at(words: List[Dict[str, Any]], anchor: Any, default: float, lead: float = 0.1, hero: bool = True) -> float:
    """Seconds into the scene at which a slot appears: just before its word (anticipation), never later; a hero slot
    whose word comes late enters earlier (by HERO_CAP of the scene)."""
    w = find_word(words, anchor) if anchor else None
    t = max(0.0, float(w["s"]) - lead) if w else default
    return round(min(t, _CAP["s"]) if hero else t, 2)


def _keyline(shot: Dict[str, Any], words, y: str, size_hint: int = 0) -> str:
    kw = str(shot.get("keyword") or "").strip()
    size = size_hint or (120 if len(kw) <= 12 else 92)
    delay = max(0.0, _at(words, shot.get("keyword_at"), 0.0) - 0.12)  # KeyLine shows the keyword 0.12 s after its delay
    attrs = f"keyword={{{_js(kw)}}} size={{{size}}} delay={{{delay}}}"
    for k in ("lead", "tail"):
        if str(shot.get(k) or "").strip():
            attrs += f" {k}={{{_js(str(shot[k]).strip())}}}"
    return f"""      <Abs x={{90}} y={{{y}}} w={{900}} style={{{{display: 'flex', justifyContent: 'center'}}}}>
        <KeyLine {attrs} />
      </Abs>"""


def _unit_label(num: Dict[str, Any]) -> str:
    """The line under a number: its label, else its Arabic unit (Counter itself only takes Latin units like % or km²)."""
    label = str(num.get("label") or "").strip()
    suf = str(num.get("suffix") or "").strip()
    return label or (suf if re.search(r"[؀-ۿ]", suf) else "")


def _label_line(num: Dict[str, Any], words) -> str:
    lab = _unit_label(num)
    return (f"\n        <ArText size={{44}} weight={{700}} delay={{{_at(words, num.get('at'), 0.3) + 0.4}}} maxWidth={{900}}>{{{_js(lab)}}}</ArText>"
            if lab else "")


def _counter(num: Dict[str, Any], words, size: int, color: str = "") -> str:
    v = float(num["value"])
    year = bool(num.get("year")) or (v.is_integer() and 100 <= v <= 2100 and not num.get("suffix"))
    dec = 0 if v.is_integer() else min(2, len(str(v).split(".")[1]))
    attrs = f"to={{{int(v) if v.is_integer() else v}}} size={{{size}}} delay={{{_at(words, num.get('at'), 0.3)}}} decimals={{{dec}}}"
    if year:
        attrs += " year"
    if num.get("suffix") and not re.search(r"[؀-ۿ]", str(num["suffix"])):  # Arabic units go to the label (ArText)
        attrs += f" suffix={{{_js(' ' + str(num['suffix']))}}}"
    if color:
        attrs += f" color={{{_js(color)}}}"
    f0 = round(_at(words, num.get('at'), 0.3) * FPS)
    attrs += f" style={{{{opacity: interpolate(k.frame, [{max(0, f0 - 4)}, {f0 + 2}], [0, 1], {{extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}})}}}}"
    return f"<Counter {attrs} />"


HEADER = """import React from 'react';
import {AbsoluteFill} from 'remotion';
import {Abs, ArText, Counter, Filter, Flow, Hub, Icon, KeyLine, LAYOUT, Level, MapLayer, Pinned, Ribbon, Ring, SceneProps, Shrink, Stack, Steps, Tally, Timeline, interpolate, useIdle, useKit, useSpr, enter} from '../kit';
"""

HERO_ICON = """
const HeroIcon: React.FC<{name: string; delay: number; y: number}> = ({name, delay, y}) => {
  const k = useKit();
  const p = useSpr(delay, 'bouncy');
  const bob = useIdle(8, 3.2, 0);
  return (
    <Abs x={LAYOUT.cx - 270} y={y + bob} w={540} h={540} style={{...enter(p, 'pop', 0), display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
      <div data-hero="icon" style={{position: 'absolute', inset: 0, borderRadius: 270, border: `8px solid ${k.c('accent', 0.85)}`, background: k.c('accent', 0.08)}} />
      <div style={{position: 'absolute', inset: -36, borderRadius: 306, border: `2px solid ${k.c('accent', 0.25)}`}} />
      <Icon name={name} size={300} color={k.c('accent')} />
    </Abs>
  );
};
"""

SIDE = """
const Side: React.FC<{x: number; label: string; icon: string; delay: number; children?: React.ReactNode}> = ({x, label, icon, delay, children}) => {
  const k = useKit();
  const p = useSpr(delay, 'snappy');
  return (
    <Abs x={x} y={LAYOUT.beat.top + 330} w={400} style={{...enter(p, 'rise', 60), display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 22}}>
      <div style={{width: 230, height: 230, borderRadius: 115, border: `5px solid ${k.c('accent', 0.8)}`, display: 'flex', alignItems: 'center', justifyContent: 'center', background: k.c('accent', 0.07)}}>
        <Icon name={icon} size={130} color={k.c('accent')} />
      </div>
      <ArText size={50} weight={800} maxWidth={390} reveal="none">{label}</ArText>
      {children}
    </Abs>
  );
};
"""


def compile_shot(shot: Dict[str, Any], ctx: Dict[str, Any], ds: Dict[str, Any]) -> str:
    """Shot spec -> one TSX scene against ../kit. Positions are fixed per device (tested against the gates), timing comes
    from the anchor words. No creative decision is made here."""
    words, dev = ctx["words"], shot["device"]
    _CAP["s"] = HERO_CAP * ctx["dur"] / FPS
    ribbon = f"      <Ribbon variant={{{int(ds['motif']['ribbon_variant'])}}} />"
    top = "LAYOUT.beat.top + 10"
    helpers, body = "", []
    if dev in MECHANISMS:
        m = shot["mech"]
        dur_s = ctx["dur"] / FPS
        enter_s = _at(words, shot.get("mech_at") or shot.get("keyword_at"), 0.2)
        ch = _at(words, m.get("change_at"), enter_s + 0.7, hero=False) if m.get("change_at") else enter_s + 0.7
        ch = round(min(max(ch, enter_s + 0.4), max(enter_s + 0.4, dur_s - 2.0)), 2)  # the change finishes inside the scene
        t = lambda k: _js(str(m.get(k) or "").strip())
        if dev == "level":
            el = f"<Level from={{{float(m['from'])}}} to={{{float(m['to'])}}} fromLabel={{{t('from_label')}}} toLabel={{{t('to_label')}}} delay={{{enter_s}}} change={{{ch}}} />"
        elif dev == "flow":
            br = [{"label": str(b["label"]).strip(), **({"share": float(b["share"])} if b.get("share") is not None else {}),
                   **({"icon": b["icon"]} if b.get("icon") and icon_ok(b.get("icon")) else {})} for b in m["branches"][:4]]
            el = f"<Flow source={{{t('source')}}} branches={{{_js(br)}}} keep={{{int(m['keep']) if isinstance(m.get('keep'), int) else -1}}} delay={{{enter_s}}} change={{{ch}}} />"
        elif dev == "filter":
            ic = f" icon={{{_js(m['icon'])}}}" if m.get("icon") and icon_ok(m.get("icon")) else ""
            el = f"<Filter from={{{float(m['from'])}}} to={{{float(m['to'])}}}{ic} fromLabel={{{t('from_label')}}} toLabel={{{t('to_label')}}} delay={{{enter_s}}} change={{{ch}}} />"
        elif dev == "tally":
            sd = [{"label": str(x["label"]).strip(), "value": float(x["value"]), "icon": x["icon"]} for x in m["sides"][:2]]
            el = f"<Tally sides={{{_js(sd)}}} delay={{{enter_s}}} change={{{ch}}} />"
        elif dev == "timeline":
            evs = [{"year": int(_num(x["year"])), "label": str(x["label"]).strip()} for x in m["events"][:5]]
            times, last = [], enter_s
            for i, x in enumerate(m["events"][:5]):  # each event on its word; never before the previous one; inside the scene
                tt = _at(words, x.get("at"), last + 0.8, hero=(i == 0)) if x.get("at") else last + (0.4 if i == 0 else 0.8)
                tt = round(min(max(tt, last + (0 if i == 0 else 0.5)), dur_s - 0.8), 2)
                times.append(tt)
                last = tt
            el = f"<Timeline events={{{_js(evs)}}} times={{{_js(times)}}} delay={{{enter_s}}} />"
        else:
            el = f"<Shrink from={{{float(m['from'])}}} to={{{float(m['to'])}}} unit={{{t('unit')}}} fromLabel={{{t('from_label')}}} toLabel={{{t('to_label')}}} delay={{{enter_s}}} change={{{ch}}} />"
        body = [_keyline(shot, words, top, 92), "      " + el]
    elif dev == "statement":
        helpers = HERO_ICON
        body = [f"      <HeroIcon name={{{_js(shot['hero_icon'])}}} delay={{{_at(words, shot.get('hero_at'), 0.0)}}} y={{LAYOUT.beat.top + 50}} />",
                _keyline(shot, words, "LAYOUT.beat.top + 660", 0)]
    elif dev == "number":
        shown = len(f"{float(shot['number']['value']):,.0f}")
        if shown <= 5:  # fits the ring
            hero = f"""      <Abs x={{LAYOUT.cx - 280}} y={{LAYOUT.beat.top + 320}} w={{560}} h={{560}}>
        <Ring value={{1}} size={{560}} delay={{{_at(words, shot['number'].get('at'), 0.3)}}}>{_counter(shot['number'], words, 170)}</Ring>
      </Abs>"""
        else:  # a long number gets the full width and an underline instead of the ring; its label sits right under it
            size = min(150, int(900 / (0.62 * shown)))
            hero = f"""      <Abs x={{90}} y={{LAYOUT.beat.top + 470}} w={{900}} style={{{{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 24}}}}>
        {_counter(shot['number'], words, size)}
        <div style={{{{width: 520, height: 10, borderRadius: 5, background: k.c('accent', 0.85)}}}} />{_label_line(shot['number'], words)}
      </Abs>"""
        body = [_keyline(shot, words, top, 96), hero]
        if shown <= 5 and _unit_label(shot["number"]):
            body.append(f"""      <Abs x={{90}} y={{LAYOUT.beat.top + 910}} w={{900}} style={{{{display: 'flex', justifyContent: 'center'}}}}>
        <ArText size={{44}} weight={{700}} delay={{{_at(words, shot['number'].get('at'), 0.3) + 0.4}}} maxWidth={{900}}>{{{_js(_unit_label(shot['number']))}}}</ArText>
      </Abs>""")
    elif dev == "pinned":
        num = shot.get("number") if isinstance(shot.get("number"), dict) else None
        inner = _counter(num, words, 110, "#141210") if num else f"<Icon name={{{_js(shot['hero_icon'])}}} size={{260}} color=\"#141210\" />"
        label = _unit_label(num) if num else ""
        lab = f"\n            <ArText size={{38}} weight={{700}} color=\"#141210\" maxWidth={{380}} reveal=\"fade\">{{{_js(label)}}}</ArText>" if label else ""
        delay = _at(words, (num or {}).get("at") or shot.get("hero_at"), 0.2)
        body = [_keyline(shot, words, top, 96),
                f"""      <Pinned x={{LAYOUT.cx - 270}} y={{LAYOUT.beat.top + 340}} w={{540}} h={{540}} rotate={{-2}} delay={{{delay}}}>
        <div style={{{{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 56}}}}>
            {inner}{lab}
        </div>
      </Pinned>"""]
    elif dev == "hub":
        items = [{"icon": it["icon"], "label": str(it["text"]).strip()} for it in shot["items"]][:6]
        first = _at(words, shot["items"][0].get("at"), 0.4) - 0.35
        body = [_keyline(shot, words, top, 92),
                f"""      <Hub cy={{LAYOUT.beat.center_y + 110}} radius={{250}} delay={{{round(max(0.0, first), 2)}}} items={{{_js(items)}}}
           center={{<Icon name={_js(shot.get('hero_icon') if icon_ok(shot.get('hero_icon')) and shot.get('hero_icon') else items[0]['icon'])} size={{130}} color={{k.c('accent')}} />}} />"""]
    elif dev == "steps":
        labels = [str(it["text"]).strip() for it in shot["items"]][:5]
        body = [_keyline(shot, words, top, 92),
                f"      <Steps items={{{_js(labels)}}} delay={{{_at(words, shot['items'][0].get('at'), 0.3)}}} />"]
    elif dev == "stack":
        items = [{"text": str(it["text"]).strip(), "icon": it["icon"]} for it in shot["items"]][:5]
        ats = [_at(words, it.get("at"), -1, hero=(i == 0)) for i, it in enumerate(shot["items"][:5])]
        known = [a for a in ats if a >= 0]
        step = round(min(1.2, max(0.25, (known[-1] - known[0]) / (len(known) - 1))), 2) if len(known) >= 2 else 0.5
        body = [_keyline(shot, words, top, 92),
                f"      <Stack top={{LAYOUT.beat.top + 300}} step={{{step}}} delay={{{known[0] if known else 0.3}}} items={{{_js(items)}}} focus />"]
    elif dev == "versus":
        helpers = SIDE
        sides = shot["sides"][:2]
        xs = ("LAYOUT.cx + 40", "LAYOUT.cx - 440")  # first side on the right (Arabic)
        body = [_keyline(shot, words, top, 92)]
        for x, s in zip(xs, sides):
            d = _at(words, s.get("at"), 0.3)
            kid = _counter({"value": s["value"], "at": s.get("at")}, words, 90) if s.get("value") is not None else ""
            body.append(f"      <Side x={{{x}}} label={{{_js(str(s['label']).strip())}}} icon={{{_js(s['icon'])}}} delay={{{d}}}>{kid}</Side>")
        body.append("""      <Abs x={LAYOUT.cx - 3} y={LAYOUT.beat.top + 340} w={6} h={420} style={{background: k.c('accent', 0.35), borderRadius: 3}} />""")
    elif dev == "map":
        body = ["      <MapLayer overlay={data.map_overlay} mode=\"split-bottom\" />", _keyline(shot, words, top, 92)]
        num = shot.get("number") if isinstance(shot.get("number"), dict) else None
        if num:
            lab = _unit_label(num)
            lab_el = (f"<ArText size={{40}} weight={{700}} delay={{{_at(words, num.get('at'), 0.3) + 0.4}}} maxWidth={{420}}>{{{_js(lab)}}}</ArText>" if lab else "")
            body.append(f"""      <Abs x={{90}} y={{LAYOUT.beat.top + 270}} w={{900}} style={{{{display: 'flex', flexDirection: 'row-reverse', alignItems: 'center', justifyContent: 'center', gap: 28}}}}>
        {_counter(num, words, min(110, int(700 / (0.62 * len(f"{float(num['value']):,.0f}")))))}{lab_el}
      </Abs>""")
    return (HEADER + helpers + f"""
// studio shot ({dev}): {str(shot.get('why') or '').replace(chr(10), ' ')[:160]}
export default function Scene({{dur, data}}: SceneProps) {{
  const k = useKit();
  // virtual camera: slow push-in + gentle bob on the content; the ribbon stays outside it (slower layer = parallax)
  const cam = interpolate(k.frame, [0, Math.max(1, dur)], [1, {CAMERA_PUSH}], {{extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}});
  const bob = useIdle({CAMERA_BOB}, 4.5, 0);
  return (
    <AbsoluteFill>
{ribbon}
      <AbsoluteFill style={{{{transform: `translateY(${{bob}}px) scale(${{cam}})`, transformOrigin: '50% 45%'}}}}>
{chr(10).join(body)}
      </AbsoluteFill>
    </AbsoluteFill>
  );
}}
""")


# ------------------------------------------------------------------ orchestration (production bible + gates + repair)

def _name(shot: Dict[str, Any], ctx: Dict[str, Any], ds: Dict[str, Any]) -> str:
    from .scene_author import _gate_sig
    payload = json.dumps({"v": COMPILER_VERSION, "gate": _gate_sig(), "shot": shot, "words": ctx["words"], "dur": ctx["dur"],
                          "theme": ds["theme"], "ribbon": ds["motif"]["ribbon_variant"],
                          "ov": hashlib.sha1(json.dumps(ctx.get("map_overlay"), sort_keys=True).encode()).hexdigest()},
                         sort_keys=True, ensure_ascii=False)
    return "s_st" + hashlib.sha1(payload.encode("utf-8")).hexdigest()[:11]


def _design_valid(ctx, tscene, ds, prev, used, ask, extra_errors=None, last=None, story=None) -> Tuple[Optional[Dict[str, Any]], List[str], int]:
    errs, shot, tries = list(extra_errors or []), last, 0
    for _ in range(MAX_DESIGN_TRIES):
        tries += 1
        shot = design_shot(ctx, tscene, ds, prev, used, ask, errs or None, shot, story)
        errs = validate_shot(shot, ctx, prev, used) if shot is not None else ["the designer returned nothing"]
        if not errs:
            return shot, [], tries
    return None, errs, tries


def map_places(ov: Any) -> frozenset:
    """The places a map overlay shows (Arabic names of its waypoints)."""
    if not isinstance(ov, dict):
        return frozenset()
    return frozenset(str(w.get("name_ar") or w.get("name_en") or "") for w in ov.get("waypoints") or [] if isinstance(w, dict)) - {""}


def story_for(ctxs: List[Dict[str, Any]], t: Optional[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """What each scene's illustrator must know beyond its own sentence: the earlier sentences (a bare number gets its
    direction from the story: '33 m by 2050' in a drying sea is a drop), the video message, the scene's intent."""
    t = t or {}
    intents = {s.get("id"): s.get("intent") for s in t.get("scenes") or [] if isinstance(s, dict)}
    out, before = {}, []
    for c in ctxs:
        out[c["id"]] = {"message": t.get("message"), "before": list(before[-6:]), "intent": intents.get(c["id"])}
        before.append(c["sentence"])
    return out


def illustrate_all(ctxs, shots, ds, style, job: Path, scenes_dir: Path, bible: Dict[str, Any], log, write=None,
                   treatment_: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
    """Bespoke SVG hero per scene by the illustrator model, through the real render gates, max 2 repairs each.
    The first showing of a map keeps the map device (geography is drawn from data, not imagined). Returns sid -> name."""
    from concurrent.futures import ThreadPoolExecutor
    from . import illustrator as il
    from . import scene_author as sa
    todo = {c["id"]: c for c in ctxs if (shots.get(c["id"]) or {}).get("device") != "map"}
    story = story_for(ctxs, treatment_)
    names = {sid: il.name_for(c, shots.get(sid), ds) for sid, c in todo.items()}
    accepted: Dict[str, str] = {}
    for sid in list(todo):
        hit = sa.CACHE_DIR / f"{names[sid]}.tsx"
        if hit.exists():
            shutil.copyfile(hit, scenes_dir / f"{names[sid]}.tsx")
            accepted[sid] = names[sid]
            bible["shots"].setdefault(sid, {})["illustration"] = {"status": "cache"}
            todo.pop(sid)
    codes: Dict[str, str] = {}
    problems: Dict[str, List[str]] = {}
    for rnd in range(MAX_REPAIRS + 1):
        if not todo:
            break
        with ThreadPoolExecutor(max_workers=4) as ex:
            futs = {sid: ex.submit(il.draw, c, shots.get(sid), ds, "_" + re.sub(r"\W", "", sid), problems.get(sid), codes.get(sid), write, story[sid])
                    for sid, c in todo.items()}
            res = {sid: f.result() for sid, f in futs.items()}
        now: Dict[str, List[str]] = {}
        ready = {}
        for sid, hero in res.items():
            rec = bible["shots"].setdefault(sid, {}).setdefault("illustration", {"calls": 0})
            rec["calls"] = rec.get("calls", 0) + 1
            if not hero:
                now[sid] = ["the reply had no `const Hero` component (return only the code)"]
                continue
            codes[sid] = hero
            rec["plan"] = il.plan_of(hero)
            path = scenes_dir / f"{names[sid]}.tsx"
            path.write_text(il.scene_code(hero, shots.get(sid), todo[sid], ds), encoding="utf-8")
            errs = sa.static_check(path)
            if errs:
                now[sid] = [f"the code failed the type/safety check: {e}" for e in errs[:5]]
                continue
            ready[names[sid]] = {"ctx": dict(todo[sid], hero_min_ink=il.HERO_MIN_INK, hero_min_w=il.HERO_MIN_SIDE,
                                             allowed_numbers=il.allowed_numbers(todo[sid]))}
        pr: Dict[str, List[str]] = {}
        if ready:
            with sa.sync_to_remotion(str(scenes_dir), only=set(ready)):
                pr = sa.sandbox_render(ready, style, job / "scenes_check")
        for sid in list(res):
            nm = names[sid]
            if sid not in now and pr.get(nm):
                now[sid] = pr[nm]
            rec = bible["shots"][sid]["illustration"]
            if now.get(sid):
                rec.setdefault("problems", []).append(now[sid][:6])
                (scenes_dir / f"{nm}.tsx").unlink(missing_ok=True)
                log(f"studio: illustration {sid} rejected ({now[sid][0][:90]})")
            else:
                accepted[sid] = nm
                rec["status"] = "accepted"
                shutil.copyfile(scenes_dir / f"{nm}.tsx", sa.CACHE_DIR / f"{nm}.tsx")
                log(f"studio: illustrated {sid}: {rec.get('plan', '')[:90]}")
                todo.pop(sid)
        problems = now
    for sid in todo:
        bible["shots"][sid]["illustration"]["status"] = "fallback_to_device"
    return accepted


def direct_spec(spec: Dict[str, Any], script: Dict[str, Any], job_dir: str, log: Callable[[str], None] = print, ask=_ask,
                gates: bool = True, illustrate_write=None) -> Dict[str, Any]:
    """Replace each scene's beats by a compiled studio shot. Scenes that cannot pass keep their beats (legacy path) and
    are listed in production.json -> fallback. Mutates and returns the spec."""
    from . import scene_author as sa
    from .style import theme_from_style
    job = Path(job_dir).resolve()
    scenes_dir = job / "scenes"
    scenes_dir.mkdir(parents=True, exist_ok=True)
    sa.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    theme = theme_from_style(spec["style"])
    ctxs = [sa.scene_context(s, theme) for s in spec["scenes"]]

    t = treatment(script, spec["scenes"], ask)
    ds = design_system(spec["style"], t)
    for s, tr in zip(spec["scenes"], transitions_for([x["link"] for x in t["scenes"]])):
        s["transition"] = tr
    bible: Dict[str, Any] = {"started": time.strftime("%Y-%m-%d %H:%M:%S"), "treatment": t,
                             "design_system": {k: v for k, v in ds.items() if k != "preset_guide"}, "shots": {}, "fallback": []}
    log(f"studio: treatment '{t['world'][:60]}', motif ribbon {ds['motif']['ribbon_variant']}")

    seen_places: set = set()
    for c in ctxs:  # the same places on a map twice is a repeat: the second scene may explain instead of re-showing
        pl = map_places(c.get("map_overlay"))
        c["map_seen"] = bool(pl) and pl <= seen_places
        seen_places |= pl

    shots: Dict[str, Dict[str, Any]] = {}
    used: Dict[str, int] = {}
    prev = None
    stories = story_for(ctxs, t)
    for ctx, tscene in zip(ctxs, t["scenes"]):  # sequential: each scene sees the previous shot (continuity)
        shot, errs, tries = _design_valid(ctx, tscene, ds, prev, used, ask, story=stories[ctx["id"]])
        rec = {"tries": tries, "errors": errs, "status": "designed" if shot else "invalid", "shot": shot}
        bible["shots"][ctx["id"]] = rec
        if shot:
            shots[ctx["id"]] = shot
            count_use(used, shot)
            prev = shot
        log(f"studio: {ctx['id']} -> {shot['device'] if shot else 'INVALID'} ({tries} design call(s))")

    by_id = {c["id"]: c for c in ctxs}
    accepted: Dict[str, str] = {}
    illustrated: Dict[str, str] = {}
    if gates and cfg("STUDIO_ILLUSTRATE", "1") == "1":  # bespoke drawings first; the compiled devices are the fallback
        illustrated = illustrate_all(ctxs, shots, ds, spec["style"], job, scenes_dir, bible, log, write=illustrate_write, treatment_=t)
        accepted.update(illustrated)
    pending = {sid: s for sid, s in shots.items() if sid not in illustrated}
    for rnd in range(MAX_REPAIRS + 1):
        if not pending:
            break
        names = {sid: _name(s, by_id[sid], ds) for sid, s in pending.items()}
        todo = {}
        for sid, nm in names.items():
            path = scenes_dir / f"{nm}.tsx"
            hit = sa.CACHE_DIR / f"{nm}.tsx"
            if hit.exists():
                shutil.copyfile(hit, path)
                accepted[sid] = nm
                bible["shots"][sid]["status"] = "cache"
                continue
            path.write_text(compile_shot(pending[sid], by_id[sid], ds), encoding="utf-8")
            todo[sid] = nm
        problems: Dict[str, List[str]] = {}
        if gates and todo:
            for sid, nm in todo.items():
                errs = sa.static_check(scenes_dir / f"{nm}.tsx")
                if errs:
                    problems[sid] = [f"compiled code failed the static check (engineer bug): {e}" for e in errs[:3]]
            ready = {nm: {"ctx": dict(by_id[sid], hero_min_w=HERO_MIN_W)} for sid, nm in todo.items() if sid not in problems}
            if ready:
                with sa.sync_to_remotion(str(scenes_dir), only=set(ready)):
                    pr = sa.sandbox_render(ready, spec["style"], job / "scenes_check")
                for sid, nm in todo.items():
                    if pr.get(nm):
                        problems[sid] = pr[nm]
        for sid, nm in todo.items():
            if problems.get(sid):
                (scenes_dir / f"{nm}.tsx").unlink(missing_ok=True)
                bible["shots"][sid].setdefault("render_problems", []).append(problems[sid][:6])
            else:
                accepted[sid] = nm
                bible["shots"][sid]["status"] = "accepted"
                if gates:
                    shutil.copyfile(scenes_dir / f"{nm}.tsx", sa.CACHE_DIR / f"{nm}.tsx")
        pending = {}
        if rnd == MAX_REPAIRS:
            break
        for sid, probs in problems.items():  # repair: back to the Scene Designer with what the render showed
            i = [c["id"] for c in ctxs].index(sid)
            prev_shot = shots.get(ctxs[i - 1]["id"]) if i else None
            used_wo = dict(used)
            count_use(used_wo, shots[sid], -1)
            log(f"studio: repairing {sid} ({probs[0][:80]})")
            new, errs, tries = _design_valid(by_id[sid], t["scenes"][i], ds, prev_shot, used_wo, ask,
                                             ["the rendered frames failed: " + p for p in probs[:6]], shots[sid], stories[sid])
            bible["shots"][sid]["tries"] += tries
            if new:
                used = dict(used_wo)
                count_use(used, new)
                shots[sid] = pending[sid] = new
                bible["shots"][sid]["shot"] = new

    for s in spec["scenes"]:
        nm = accepted.get(s["id"])
        if not nm:
            bible["fallback"].append(s["id"])
            bible["shots"].setdefault(s["id"], {})["status"] = "fallback"
            record_fallback(f"studio: scene '{s['id']}' kept its built-in beats", beat_id=s["id"])
            continue
        ctx = by_id[s["id"]]
        s["authored"] = {"scene_id": nm, "status": "studio", "device": "illustration" if s["id"] in illustrated else shots[s["id"]]["device"]}
        s["beats"] = [{"kind": "authored", "scene_id": nm, "from": 0, "dur": s["dur"], "data": {k: v for k, v in ctx.items() if k != "id"},
                       "settled": s.get("role") == "hook"}]
        s["map_overlay"] = None  # the shot draws the map itself through MapLayer(data.map_overlay)
    spec["authored_dir"] = str(scenes_dir)
    bible["summary"] = {"scenes": len(ctxs), "accepted": len(accepted), "fallback": len(bible["fallback"]),
                        "devices": ["illustration" if c["id"] in illustrated else shots.get(c["id"], {}).get("device") for c in ctxs],
                        "illustrated": len(illustrated)}
    (job / "production.json").write_text(json.dumps(bible, ensure_ascii=False, indent=1), encoding="utf-8")
    log(f"studio: {bible['summary']}")
    return spec
