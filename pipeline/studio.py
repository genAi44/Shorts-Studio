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

# split modules (imported last: they read this module's constants)
from .studio_validate import ITEM_LIMITS, _AR_DIGITS, _AR_PUNCT, _DECIMAL, _DIGITS, _DUALS, _HUNDREDS, _PERCENT, _PUNCT, _SCALES, _TASHKEEL, _TENS, _UNITS, _complement, _icon_names, _mech_errors, _num, _num_token, _nwords, _spoken, count_use, find_word, icon_ok, norm_word, number_ok, shot_icons, validate_shot, word_numbers  # noqa: E402,F401
from .studio_compile import HEADER, HERO_CAP, HERO_ICON, SIDE, _CAP, _at, _counter, _js, _keyline, _label_line, _unit_label, compile_shot  # noqa: E402,F401
