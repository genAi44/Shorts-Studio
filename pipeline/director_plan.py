"""Director stage: narrative planning of the scenes, BEFORE the designer draws anything.

Place in the pipeline (run.produce -> rem.build_spec -> scene_author.author_spec):
    narration + word timings (tts, owned by the system)
    -> plan_video(): ONE LLM call for the whole video with DIRECTOR_SYSTEM (this file, independent of the designer prompt)
    -> validated scene plan (contract below), cached in data/authored_cache/plan_<hash>.json
    -> scene_author (the designer) receives each scene's plan as structured, read-only input.

The director never sees, writes or estimates timings: it gets the narration text only, and its output is rejected if it
contains any timing key. Scene boundaries are the script's scenes (each one has its own synthesized audio), so the director
plans their purpose, order of ideas and the links between them; it does not re-cut the audio.
"""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .config import record_fallback

PLAN_VERSION = 2   # 2: the plan is written in English (cached v1 plans were free-language)

# Shared by every LLM stage that plans or designs scenes (director, visual intelligence, designer): the models think and write in
# English, the video stays Arabic. The narration, its word timings and every on-screen string are never translated.
LANGUAGE_CONTRACT = """LANGUAGE CONTRACT: the narration is Arabic and the final video is entirely Arabic (voice-over, captions, on-screen text).
You think and write EVERYTHING you produce in English: plans, descriptions, reasons, element names, ids, comments and code identifiers.
Never translate, paraphrase or rewrite the Arabic narration. Arabic appears in your output only (a) where a field must be COPIED verbatim
from the narration (a trigger word / phrase), and (b) as the exact strings that will be shown on screen, copied from the narration or from
an entity's name_ar. Place names: use the entity's standard English name (name_en) in your reasoning and keep name_ar for display."""

# Contract: one entry per scene, in the scenes' order. `narration` is attached by the system from the timed words (the
# director does not rewrite it).
PLAN_FIELDS = (
    "scene_id",               # id of the existing scene
    "objective",              # what this scene must achieve in the story
    "main_concept",           # the one idea / message the viewer keeps
    "narrative_description",  # what happens in the scene, narratively
    "key_information",        # list of the facts that must get across (from the narration only)
    "relation_to_previous",   # how it follows the previous scene
    "relation_to_next",       # how it sets up the next scene
    "visual_storytelling",    # suggested visual storytelling approach (map, comparison, process, metaphor, timeline...)
    "transition_trigger",     # word/phrase of THIS scene's narration that hands over to the next scene
    "continuity",             # narrative + visual continuity requirements (recurring motif, colour, element carried over)
)

DIRECTOR_SYSTEM = ("""You are the DIRECTOR of an Arabic-language educational Shorts studio. You plan the story, you do not draw.

"""
                   + LANGUAGE_CONTRACT + """

You receive the video title and its scenes (id, role, narration). For EACH scene, in the same order, decide:
- objective: what the scene must achieve in the story (hook the viewer, set context, prove a claim, contrast, pay off, call to action...).
- main_concept: the ONE idea or message the viewer must keep from this scene.
- narrative_description: what happens in the scene, narratively (2-3 sentences).
- key_information: the list of facts that must get across. Use ONLY facts stated in the narration; never invent numbers, dates or names.
- relation_to_previous / relation_to_next: how the scene follows the previous one and sets up the next one (cause, contrast, zoom-in,
  example, answer to an open question...). The first scene has no previous ("" allowed); the last one loops back to the hook.
- visual_storytelling: the visual storytelling approach that fits this idea (map journey, side-by-side comparison, process steps,
  scale metaphor, timeline, cause-and-effect chain, close-up on one object...). Vary it between neighbouring scenes.
- transition_trigger: the exact word or short phrase, copied VERBATIM (Arabic) from THIS scene's narration, on which the scene hands over to the next one
  (usually its last strong word). "" only for the last scene.
- continuity: what must stay consistent across the cut (a recurring motif, a colour role, an element that carries over, the same place).

Avoid repeating the same idea or information in two scenes. Keep the narrative arc: hook -> build -> one breathing moment -> climax -> loop.

FORBIDDEN (the system owns these): SVG or any drawing, artwork, code, layout coordinates, implementation details, and ANY timing -
no seconds, frames, durations, start/end times, word timings or captions. Refer to moments only by quoting words of the narration.

Reply with JSON only:
{"scenes":[{"scene_id":"...","objective":"...","main_concept":"...","narrative_description":"...","key_information":["..."],
"relation_to_previous":"...","relation_to_next":"...","visual_storytelling":"...","transition_trigger":"...","continuity":"..."}]}""")
from .skills import DIRECTOR_SKILLS, skills_block  # noqa: E402
DIRECTOR_SYSTEM += skills_block(DIRECTOR_SKILLS)



# ------------------------------------------------------------------ shared guards (director + designer)

_TIMING_KEY = re.compile(r"^(s|e|t|t0|t1|start|end|time|times|timing|timings|timestamp|frame|frames|from_frame|to_frame|dur|duration|"
                         r"sec|secs|seconds|ms|offset|words)$|_(time|frame|frames|sec|secs|seconds|ms|start|end|duration)$", re.I)


def timing_keys(obj: Any, path: str = "") -> List[str]:
    """Paths of every key that looks like timing data. LLM stages may reference words, never carry timings."""
    out: List[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{path}.{k}" if path else str(k)
            if _TIMING_KEY.search(str(k)):
                out.append(p)
            out += timing_keys(v, p)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out += timing_keys(v, f"{path}[{i}]")
    return out


_TASHKEEL = re.compile(r"[ً-ْٰـ]")
_PUNCT = re.compile(r"[^\w\s]", re.U)


def norm_word(w: str) -> str:
    w = unicodedata.normalize("NFKC", str(w or ""))
    w = _TASHKEEL.sub("", w)
    w = re.sub("[إأآٱ]", "ا", w).replace("ى", "ي").replace("ة", "ه")
    return _PUNCT.sub("", w).strip().lower()


def _token_match(word: str, trig: str) -> bool:
    # Arabic proclitics (و ب ل ف ك + ال) glue onto the word: "وبرلين" matches "برلين"
    return bool(trig) and (word == trig or (word.endswith(trig) and len(word) - len(trig) <= 3))


def find_word(words: List[str], phrase: str, start: int = 0) -> Optional[int]:
    """Index (>= start) of the first word of `phrase` inside the scene's words, or None. Text only, no timing."""
    toks = [norm_word(t) for t in str(phrase or "").split() if norm_word(t)]
    ws = [norm_word(w) for w in words]
    if not toks:
        return None
    for i in range(max(0, start), len(ws) - len(toks) + 1):
        if all(_token_match(ws[i + j], toks[j]) for j in range(len(toks))):
            return i
    return None


# ------------------------------------------------------------------ prompt, validation, fallback

def scene_items(spec: Dict[str, Any]) -> List[Dict[str, Any]]:
    """What the director sees per scene: id, role, narration (joined from the timed words; text only)."""
    return [{"scene_id": s.get("id"), "role": s.get("role", "body"),
             "narration": " ".join(str(w.get("t", "")) for w in (s.get("words") or []))} for s in spec.get("scenes") or []]


def director_prompt(items: List[Dict[str, Any]], title: str = "") -> str:
    return json.dumps({"title": title, "scenes": items}, ensure_ascii=False)


def normalize_plan(plan: Any) -> Any:
    """Accept the shapes models actually return: a bare list of scenes (a cut-off reply parses to its inner array)
    or {"<anything>": [scenes]}; anything else is returned unchanged for plan_errors to reject."""
    if isinstance(plan, list):
        return {"scenes": plan}
    if isinstance(plan, dict) and not isinstance(plan.get("scenes"), list):
        lists = [v for v in plan.values() if isinstance(v, list) and v and all(isinstance(x, dict) for x in v)]
        if len(lists) == 1:
            return {"scenes": lists[0]}
    return plan


def merge_plans(base: Any, extra: Any, items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Scenes of `extra` replace/fill those of `base` by scene_id; result in the narration's scene order."""
    by_id: Dict[str, Any] = {}
    for pl in (base, extra):
        pl = normalize_plan(pl)
        if isinstance(pl, dict) and isinstance(pl.get("scenes"), list):
            by_id.update({str(x.get("scene_id")): x for x in pl["scenes"] if isinstance(x, dict) and x.get("scene_id")})
    return {"scenes": [by_id[str(i["scene_id"])] for i in items if str(i["scene_id"]) in by_id]}


def _bad_scene_ids(plan: Any, items: List[Dict[str, Any]], errs: List[str]) -> List[str]:
    scenes = [x for x in (plan.get("scenes") or []) if isinstance(x, dict)] if isinstance(plan, dict) else []
    got = {str(x.get("scene_id")) for x in scenes}
    timed = {str(x.get("scene_id")) for x in scenes if timing_keys(x)}
    return [str(i["scene_id"]) for i in items
            if str(i["scene_id"]) not in got or str(i["scene_id"]) in timed or any(e.startswith((f"{i['scene_id']}.", f"{i['scene_id']}:")) for e in errs)]


def plan_errors(plan: Any, items: List[Dict[str, Any]]) -> List[str]:
    """Contract check of the director's output. Empty list = accepted."""
    if not isinstance(plan, dict) or not isinstance(plan.get("scenes"), list):
        return ['the reply must be a JSON object {"scenes": [...]}']
    errs = [f"timing data is forbidden for the director: remove '{p}'" for p in timing_keys(plan)]
    got = [s for s in plan["scenes"] if isinstance(s, dict)]
    ids = [str(s.get("scene_id")) for s in got]
    want = [str(i["scene_id"]) for i in items]
    if ids != want:
        errs.append(f"scene_id list must be exactly {want} in this order (got {ids})")
    by_id = {str(s.get("scene_id")): s for s in got}
    for n, it in enumerate(items):
        s = by_id.get(str(it["scene_id"]))
        if not s:
            continue
        last = n == len(items) - 1
        for f in PLAN_FIELDS[1:]:
            v = s.get(f)
            empty_ok = (f == "relation_to_previous" and n == 0) or (f == "transition_trigger" and last)
            if f == "key_information":
                if not isinstance(v, list) or not [x for x in v if str(x).strip()]:
                    errs.append(f"{it['scene_id']}.key_information must be a non-empty list of facts from the narration")
            elif not isinstance(v, str) or (not v.strip() and not empty_ok):
                errs.append(f"{it['scene_id']}.{f} must be a non-empty string")
        trig = s.get("transition_trigger")
        if isinstance(trig, str) and trig.strip() and find_word(it["narration"].split(), trig) is None:
            errs.append(f"{it['scene_id']}.transition_trigger '{trig}' must be copied from that scene's narration")
        if any(k in s for k in ("svg", "code", "tsx")):
            errs.append(f"{it['scene_id']}: the director must not produce SVG or code")
    return errs


def fallback_scene(it: Dict[str, Any], n: int, total: int, prev: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Deterministic plan for one scene (no LLM): keeps the designer's input contract complete."""
    words = it["narration"].split()
    head = " ".join(words[:7])
    role_obj = {"hook": "hook the viewer with the paradox of the topic", "cta": "close and invite the viewer to react",
                "loop": "loop back to the opening image", "open_loop": "open a question that the next scene answers"}
    return {
        "scene_id": it["scene_id"],
        "objective": role_obj.get(it.get("role"), "explain and prove this sentence visually"),
        "main_concept": head,
        "narrative_description": it["narration"],
        "key_information": [it["narration"]] if it["narration"] else [head or str(it["scene_id"])],
        "relation_to_previous": f"continues from: {prev['main_concept']}" if prev else "",
        "relation_to_next": "loops back to the hook" if n == total - 1 else "sets up the next scene",
        "visual_storytelling": "concrete visual proof of the sentence",
        "transition_trigger": "" if n == total - 1 or not words else words[-1],
        "continuity": "keep the video's colour roles and recurring motif",
    }


def _cache_path(items: List[Dict[str, Any]], title: str, cache_dir: Path) -> Path:
    h = hashlib.sha1(json.dumps({"v": PLAN_VERSION, "sys": DIRECTOR_SYSTEM, "title": title, "items": items},
                                ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()[:12]
    return cache_dir / f"plan_{h}.json"


def llm_plan(system: str, user: str) -> Any:
    from .llm import call_llm_json
    return call_llm_json("director", system, user, temperature=0.6, timeout=150)


def plan_from_decisions(spec: Dict[str, Any], items: List[Dict[str, Any]]) -> Optional[Dict[str, Dict[str, Any]]]:
    """ONE director: when the beat director (app step 3) decided the scenes, the narrative plan is built from those decisions
    instead of a second, independent LLM director re-planning them. None only when no scene carries a decision."""
    by_id = {s.get("id"): s for s in spec.get("scenes") or []}
    decs = {it["scene_id"]: [b for b in (by_id.get(it["scene_id"]) or {}).get("beats") or [] if isinstance(b, dict) and b.get("concept")]
            for it in items}
    if not any(decs.values()):
        return None
    out: Dict[str, Dict[str, Any]] = {}
    prev = None
    for n, it in enumerate(items):
        b = decs[it["scene_id"]]
        s = fallback_scene(it, n, len(items), prev)
        if b:  # a scene without a decision (e.g. a native photo/map scene) keeps the deterministic plan
            concept = " / ".join(dict.fromkeys(str(x["concept"]) for x in b))
            s.update({"main_concept": str(b[0].get("title") or s["main_concept"]), "narrative_description": concept,
                      "visual_storytelling": concept})
        s = {f: s.get(f, "") for f in PLAN_FIELDS}
        s["scene_id"] = str(it["scene_id"])
        s["narration"] = it["narration"]
        out[s["scene_id"]] = s
        prev = s
    return out


def plan_video(spec: Dict[str, Any], cache_dir: Path, llm: Optional[Callable[[str, str], Any]] = None, cache_only: bool = False,
               title: str = "", log: Callable[[str], None] = print) -> Dict[str, Dict[str, Any]]:
    """scene_id -> plan (PLAN_FIELDS + system-owned `narration`). One LLM call (+ one repair call with the contract errors);
    scenes still invalid after that get the deterministic plan and a recorded warning. Never raises."""
    items = scene_items(spec)
    if not items:
        return {}
    decided = plan_from_decisions(spec, items)
    if decided is not None:
        log("director: plan built from the beat director's decisions (no second director call)")
        return decided
    title = title or str(spec.get("title") or "")
    cache_dir.mkdir(parents=True, exist_ok=True)
    cp = _cache_path(items, title, cache_dir)
    plan: Any = None
    status = "cache"
    if cp.exists():
        plan = json.loads(cp.read_text(encoding="utf-8"))
    elif not cache_only:
        llm = llm or llm_plan
        user = director_prompt(items, title)
        status = "llm"
        try:
            plan = merge_plans(llm(DIRECTOR_SYSTEM, user), None, items)
            for attempt in range(2):  # re-ask ONLY the missing/invalid scenes (a short reply is not cut off), merge by scene_id
                errs = plan_errors(plan, items)
                bad = _bad_scene_ids(plan, items, errs)
                if not errs or not bad:
                    break
                log(f"director: {len(bad)} scene(s) missing/invalid {bad}, repair {attempt + 1}/2")
                sub = [i for i in items if str(i["scene_id"]) in bad]
                probs = [e for e in errs[:20] if not e.startswith("scene_id list")]
                fix = llm(DIRECTOR_SYSTEM, director_prompt(sub, title) + "\n\nPlan ONLY these scenes, all of them, in this order: "
                          + ", ".join(bad) + '. Return {"scenes": [...]}.'
                          + ("\nYour previous attempt was REJECTED. Problems:\n- " + "\n- ".join(probs) if probs else ""))
                plan = merge_plans(plan, fix, items)
        except Exception as e:  # noqa: BLE001 - recorded below, the designer still gets a complete plan
            record_fallback(f"director plan llm call failed ({e}): deterministic plan", beat_id="director")
            plan = None
    errs = plan_errors(plan, items) if plan is not None else ["no plan"]
    ok = isinstance(plan, dict) and isinstance(plan.get("scenes"), list) and not timing_keys(plan)  # timings: the whole plan is void
    good = {str(s.get("scene_id")): s for s in plan["scenes"] if isinstance(s, dict)} if ok else {}
    bad_ids = {str(i["scene_id"]) for i in items if any(e.startswith((f"{i['scene_id']}.", f"{i['scene_id']}:")) for e in errs)}
    out: Dict[str, Dict[str, Any]] = {}
    prev = None
    for n, it in enumerate(items):
        sid = str(it["scene_id"])
        s = good.get(sid)
        if s is None or sid in bad_ids:
            if not cache_only:
                record_fallback(f"director plan for '{sid}' invalid or missing ({(errs or ['?'])[0][:90]}): deterministic plan", beat_id=sid)
            s = fallback_scene(it, n, len(items), prev)
        s = {f: s.get(f, "") for f in PLAN_FIELDS}   # only the contract's fields reach the designer (drops any extra key)
        s["scene_id"] = sid
        s["narration"] = it["narration"]          # system-owned, read-only
        out[sid] = s
        prev = s
    if status == "llm" and not errs:  # only a fully valid plan is cached (a fallback must stay visible on the next run)
        cp.write_text(json.dumps({"scenes": [{k: v for k, v in s.items() if k != "narration"} for s in out.values()]},
                                 ensure_ascii=False, indent=1), encoding="utf-8")
    return out
