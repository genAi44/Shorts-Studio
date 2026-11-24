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

from .config import FPS, record_fallback

COMPILER_VERSION = 3
CAMERA_PUSH = 1.06  # protocol 5.5: push-in 100 % -> 106 % across a scene
CAMERA_BOB = 6      # px of idle float, so a finished build never sits still
MAX_DESIGN_TRIES = 3          # first design + 2 retries on validator errors
MAX_REPAIRS = 2               # redesigns after a failed render gate
DEVICES = ("statement", "number", "pinned", "hub", "steps", "stack", "versus", "map")
REPEATABLE = {"map"}          # the only device that may follow itself (the map is the continuity)
MAX_SAME_DEVICE = 1           # a device is a look: twice in one video reads as a template
DEVICE_BUDGET = {"statement": 2}  # the plain fallback device may come back once
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
For every scene: its intent (what the viewer must understand or feel), its rhetorical function
(claim | contrast | quantity | sequence | cause | place | person | question), its energy 1-5 (hook high, build rising,
breath low, climax 5) and how it links to the PREVIOUS scene (continue | contrast | deeper | next_step).

Return JSON only:
{"message":"...","world":"...","motif":"...","climax":"scene id","breath":"scene id",
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
    return {"message": str(t.get("message") or "")[:240], "world": str(t.get("world") or "")[:200], "motif": str(t.get("motif") or "")[:120],
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
        "motif": {"ribbon_variant": seed % 3, "world": treatment_.get("world"), "motif": treatment_.get("motif")},
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

DEVICES (pick the one that PROVES the sentence; ask "what must the viewer see to believe this sentence?"):
- statement: one hero icon (big, in a ring) + the key line. For a claim or a question with no number/list.
- number: one big rolling number in a ring + the key line. The sentence states one number or year.
- pinned: a card pinned on a string holding a number (or a hero icon) + a short label. One striking fact.
- hub: a centre icon with 2-6 satellites (icon + label). Sources, causes, parts of one thing.
- steps: 2-5 rising steps (labels). Stages, growth, ranking, "from X to Y".
- stack: 2-5 rows that build up (text + icon). Consequences, features, a dated list.
- versus: two sides (icon + label + optional number). Comparison, before/after, contrast.
- map: the vector map of the scene's places, big (only and always when the scene has a map) + the key line +
  optionally one number. The map is the hero: no hero icon.

TEXT: keyword = the KEY idea in 1-4 words (big, accent colour); lead / tail = optional small lines (<= 7 words each).
On-screen text is the punchline, NOT a copy of the narration (the narration is already captioned). Arabic.
TIMING: every slot that appears has "at": a word copied EXACTLY from the scene's spoken words; it appears on that word.
ICONS: ONLY names from "available_icons" in the brief (any other name renders as a star).
Choose icons whose meaning matches (never a lightbulb for heritage, a star for corruption, a rising chart for a decline).
NUMBERS: only numbers that are spoken in the sentence or listed in its entities; "year": true for a year.
CONTINUITY: one visual world for the whole video; every device at most ONCE per video (map unlimited, statement twice):
see devices_used_so_far. Every on-screen line says something different (a tail never repeats an item).

Return JSON only:
{"device":"hub","why":"one line: why this device proves the sentence",
 "keyword":"...","keyword_at":"word","lead":"...","tail":"...",
 "hero_icon":"lucide:x","hero_at":"word",
 "number":{"value":1453,"year":true,"suffix":"","label":"...","at":"word"},
 "items":[{"text":"...","icon":"lucide:x","at":"word"}],
 "sides":[{"label":"...","icon":"lucide:x","value":null,"at":"word"},{"label":"...","icon":"lucide:x","value":null,"at":"word"}]}
Omit slots the device does not use."""


def shot_brief(ctx: Dict[str, Any], tscene: Dict[str, Any], ds: Dict[str, Any], prev: Optional[Dict[str, Any]], used: Dict[str, int]) -> str:
    brief = {
        "scene": {"id": ctx["id"], "role": ctx.get("role"), "seconds": round(ctx["dur"] / FPS, 1), "sentence": ctx["sentence"],
                  "spoken_words": [w["t"] for w in ctx["words"]], "entities": ctx.get("entities", []),
                  "has_map": bool(ctx.get("map_overlay"))},
        "direction": {k: tscene.get(k) for k in ("intent", "function", "energy", "link")},
        "video": {"world": ds["motif"].get("world"), "motif": ds["motif"].get("motif"), "not": ds.get("not", [])},
        "previous_shot": {k: prev.get(k) for k in ("device", "keyword")} if prev else None,
        "devices_used_so_far": {k: v for k, v in used.items() if not k.startswith("icon:")},
        "icons_used_so_far": {k[5:]: v for k, v in used.items() if k.startswith("icon:")},
        "available_icons": sorted(_icon_names()),
    }
    return json.dumps(brief, ensure_ascii=False)


def design_shot(ctx, tscene, ds, prev, used, ask=_ask, errors: Optional[List[str]] = None, previous_spec=None) -> Optional[Dict[str, Any]]:
    user = shot_brief(ctx, tscene, ds, prev, used)
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


_UNITS = {"واحد": 1, "واحده": 1, "احد": 1, "احدى": 1, "اثنان": 2, "اثنين": 2, "اثنتان": 2, "اثنتين": 2, "ثلاث": 3, "ثلاثه": 3,
          "اربع": 4, "اربعه": 4, "خمس": 5, "خمسه": 5, "ست": 6, "سته": 6, "سبع": 7, "سبعه": 7, "ثمان": 8, "ثماني": 8, "ثمانيه": 8,
          "تسع": 9, "تسعه": 9, "عشر": 10, "عشره": 10}
_TENS = {"عشرون": 20, "ثلاثون": 30, "اربعون": 40, "خمسون": 50, "ستون": 60, "سبعون": 70, "ثمانون": 80, "تسعون": 90}
_TENS.update({k[:-2] + "ين": v for k, v in list(_TENS.items())})
_HUNDREDS = {"مئه": 100, "مائه": 100, "مئتان": 200, "مئتين": 200, "مائتان": 200, "مائتين": 200}
_HUNDREDS.update({u + h: v * 100 for u, v in (("ثلاث", 3), ("اربع", 4), ("خمس", 5), ("ست", 6), ("سبع", 7), ("ثمان", 8), ("تسع", 9))
                  for h in ("مئه", "مائه")})
_SCALES = {"الف": 1000, "الاف": 1000, "مليون": 10 ** 6, "ملايين": 10 ** 6, "مليار": 10 ** 9, "مليارات": 10 ** 9}
_DUALS = {"الفان": 2000, "الفين": 2000, "مليونان": 2 * 10 ** 6, "مليونين": 2 * 10 ** 6}


def _num_token(tok: str) -> Optional[Tuple[str, int]]:
    t = norm_word(tok).replace("ة", "ه")
    for cand in ((t, t[1:]) if t.startswith("و") and len(t) > 2 else (t,)):
        for kind, table in (("unit", _UNITS), ("unit", _TENS), ("hundred", _HUNDREDS), ("scale", _SCALES), ("unit", _DUALS)):
            if cand in table:
                return kind, table[cand]
    return None


def word_numbers(text: str) -> set:
    """Numbers written in Arabic words ("عشرون ألف ومئتان وواحد وأربعون" -> 20241, "سبعة عشر مليون" -> 17000000)."""
    out, total, cur, seen = set(), 0, 0, False
    for tok in str(text or "").split() + ["."]:
        nt = _num_token(tok)
        if nt is None:
            if seen:
                out.add(total + cur)
            total, cur, seen = 0, 0, False
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
    return out


def number_ok(value: Any, ctx: Dict[str, Any]) -> bool:
    from .direct import _number_in_text
    if value is None:
        return False
    try:
        v = float(value)
    except (TypeError, ValueError):
        return False
    if _number_in_text(int(v) if v.is_integer() else v, ctx["sentence"]) or v in word_numbers(ctx["sentence"]):
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
    out = [shot.get("hero_icon")] + [it.get("icon") for it in shot.get("items") or [] if isinstance(it, dict)]         + [sd.get("icon") for sd in shot.get("sides") or [] if isinstance(sd, dict)]
    return [i for i in dict.fromkeys(out) if i]


def count_use(used: Dict[str, int], shot: Dict[str, Any], sign: int = 1) -> None:
    """Device and icon budget of the video (the validator reads it)."""
    for key in [shot["device"]] + ["icon:" + i for i in shot_icons(shot)]:
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
    if has_map and dev != "map":
        errs.append("this scene has a map (its places must be shown): device must be 'map'")
    if dev == "map" and not has_map:
        errs.append("device 'map' is only for scenes that have a map")
    if prev and dev == prev.get("device") and dev not in REPEATABLE:
        errs.append(f"the previous scene already uses '{dev}': choose another device")
    if dev not in REPEATABLE and used.get(dev, 0) >= DEVICE_BUDGET.get(dev, MAX_SAME_DEVICE):
        errs.append(f"'{dev}' was already used {used[dev]} times in this video: choose another device")
    prev_icons = set(shot_icons(prev))
    for ic in shot_icons(shot):
        if ic == shot.get("hero_icon") and ic in prev_icons:
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

    texts = [kw, shot.get("lead"), shot.get("tail")] + [it.get("text") for it in shot.get("items") or [] if isinstance(it, dict)]         + [sd.get("label") for sd in shot.get("sides") or [] if isinstance(sd, dict)]         + [(shot.get("number") or {}).get("label") if isinstance(shot.get("number"), dict) else None]
    seen = set()
    for txt in texts:  # the same line twice on screen (tail repeating an item) is wasted space
        t = norm_word(str(txt or ""))
        if t and t in seen:
            errs.append(f"the text '{txt}' appears twice on screen: every slot must say something different")
        seen.add(t)
    counted = {str(v.get("value")).replace(".0", "") for v in [shot.get("number")] + list(shot.get("sides") or [])
               if isinstance(v, dict) and v.get("value") is not None}
    for txt in texts:  # a number already rolling in a counter is not written again next to it
        for m in _DIGITS.findall(str(txt or "").translate(_AR_DIGITS)):
            if m.replace(",", "") in counted:
                errs.append(f"'{m}' in '{txt}' is already shown by the counter: remove it from the text")
    for txt in texts:  # truth rule for numbers written inside any on-screen text, not only the number slot
        for m in _DIGITS.findall(str(txt or "").translate(_AR_DIGITS)):
            n = m.replace(",", "")
            if n and not number_ok(n, ctx):
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
import {Abs, ArText, Counter, Hub, Icon, KeyLine, LAYOUT, MapLayer, Pinned, Ribbon, Ring, SceneProps, Stack, Steps, interpolate, useIdle, useKit, useSpr, enter} from '../kit';
"""

HERO_ICON = """
const HeroIcon: React.FC<{name: string; delay: number; y: number}> = ({name, delay, y}) => {
  const k = useKit();
  const p = useSpr(delay, 'bouncy');
  const bob = useIdle(8, 3.2, 0);
  return (
    <Abs x={LAYOUT.cx - 170} y={y + bob} w={340} h={340} style={{...enter(p, 'pop', 0), display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
      <div style={{position: 'absolute', inset: 0, borderRadius: 170, border: `6px solid ${k.c('accent', 0.85)}`, background: k.c('accent', 0.08)}} />
      <div style={{position: 'absolute', inset: -34, borderRadius: 204, border: `2px solid ${k.c('accent', 0.25)}`}} />
      <Icon name={name} size={190} color={k.c('accent')} />
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
    if dev == "statement":
        helpers = HERO_ICON
        body = [f"      <HeroIcon name={{{_js(shot['hero_icon'])}}} delay={{{_at(words, shot.get('hero_at'), 0.0)}}} y={{LAYOUT.beat.top + 60}} />",
                _keyline(shot, words, "LAYOUT.beat.top + 470", 0)]
    elif dev == "number":
        shown = len(f"{float(shot['number']['value']):,.0f}")
        if shown <= 5:  # fits the ring
            hero = f"""      <Abs x={{LAYOUT.cx - 230}} y={{LAYOUT.beat.top + 360}} w={{460}} h={{460}}>
        <Ring value={{1}} size={{460}} delay={{{_at(words, shot['number'].get('at'), 0.3)}}}>{_counter(shot['number'], words, 150)}</Ring>
      </Abs>"""
        else:  # a long number gets the full width and an underline instead of the ring; its label sits right under it
            size = min(150, int(900 / (0.62 * shown)))
            hero = f"""      <Abs x={{90}} y={{LAYOUT.beat.top + 470}} w={{900}} style={{{{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 24}}}}>
        {_counter(shot['number'], words, size)}
        <div style={{{{width: 520, height: 10, borderRadius: 5, background: k.c('accent', 0.85)}}}} />{_label_line(shot['number'], words)}
      </Abs>"""
        body = [_keyline(shot, words, top, 96), hero]
        if shown <= 5 and _unit_label(shot["number"]):
            body.append(f"""      <Abs x={{90}} y={{LAYOUT.beat.top + 860}} w={{900}} style={{{{display: 'flex', justifyContent: 'center'}}}}>
        <ArText size={{44}} weight={{700}} delay={{{_at(words, shot['number'].get('at'), 0.3) + 0.4}}} maxWidth={{900}}>{{{_js(_unit_label(shot['number']))}}}</ArText>
      </Abs>""")
    elif dev == "pinned":
        num = shot.get("number") if isinstance(shot.get("number"), dict) else None
        inner = _counter(num, words, 92, "#141210") if num else f"<Icon name={{{_js(shot['hero_icon'])}}} size={{220}} color=\"#141210\" />"
        label = _unit_label(num) if num else ""
        lab = f"\n            <ArText size={{38}} weight={{700}} color=\"#141210\" maxWidth={{380}} reveal=\"fade\">{{{_js(label)}}}</ArText>" if label else ""
        delay = _at(words, (num or {}).get("at") or shot.get("hero_at"), 0.2)
        body = [_keyline(shot, words, top, 96),
                f"""      <Pinned x={{LAYOUT.cx - 230}} y={{LAYOUT.beat.top + 360}} w={{460}} h={{480}} rotate={{-2}} delay={{{delay}}}>
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
                f"      <Stack top={{LAYOUT.beat.top + 300}} step={{{step}}} delay={{{known[0] if known else 0.3}}} items={{{_js(items)}}} />"]
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


def _design_valid(ctx, tscene, ds, prev, used, ask, extra_errors=None, last=None) -> Tuple[Optional[Dict[str, Any]], List[str], int]:
    errs, shot, tries = list(extra_errors or []), last, 0
    for _ in range(MAX_DESIGN_TRIES):
        tries += 1
        shot = design_shot(ctx, tscene, ds, prev, used, ask, errs or None, shot)
        errs = validate_shot(shot, ctx, prev, used) if shot is not None else ["the designer returned nothing"]
        if not errs:
            return shot, [], tries
    return None, errs, tries


def direct_spec(spec: Dict[str, Any], script: Dict[str, Any], job_dir: str, log: Callable[[str], None] = print, ask=_ask,
                gates: bool = True) -> Dict[str, Any]:
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

    shots: Dict[str, Dict[str, Any]] = {}
    used: Dict[str, int] = {}
    prev = None
    for ctx, tscene in zip(ctxs, t["scenes"]):  # sequential: each scene sees the previous shot (continuity)
        shot, errs, tries = _design_valid(ctx, tscene, ds, prev, used, ask)
        rec = {"tries": tries, "errors": errs, "status": "designed" if shot else "invalid", "shot": shot}
        bible["shots"][ctx["id"]] = rec
        if shot:
            shots[ctx["id"]] = shot
            count_use(used, shot)
            prev = shot
        log(f"studio: {ctx['id']} -> {shot['device'] if shot else 'INVALID'} ({tries} design call(s))")

    by_id = {c["id"]: c for c in ctxs}
    pending = {sid: s for sid, s in shots.items()}
    accepted: Dict[str, str] = {}
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
            ready = {nm: {"ctx": by_id[sid]} for sid, nm in todo.items() if sid not in problems}
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
                                             ["the rendered frames failed: " + p for p in probs[:6]], shots[sid])
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
        s["authored"] = {"scene_id": nm, "status": "studio", "device": shots[s["id"]]["device"]}
        s["beats"] = [{"kind": "authored", "scene_id": nm, "from": 0, "dur": s["dur"], "data": {k: v for k, v in ctx.items() if k != "id"},
                       "settled": s.get("role") == "hook"}]
        s["map_overlay"] = None  # the shot draws the map itself through MapLayer(data.map_overlay)
    spec["authored_dir"] = str(scenes_dir)
    bible["summary"] = {"scenes": len(ctxs), "accepted": len(accepted), "fallback": len(bible["fallback"]),
                        "devices": [shots.get(c["id"], {}).get("device") for c in ctxs]}
    (job / "production.json").write_text(json.dumps(bible, ensure_ascii=False, indent=1), encoding="utf-8")
    log(f"studio: {bible['summary']}")
    return spec
