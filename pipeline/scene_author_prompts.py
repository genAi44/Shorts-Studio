"""Split from `pipeline/scene_author.py` (re-exported there); see that module."""
from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
from .config import FPS
import json
import re
from .scene_author import KIT_DOC, STATE_LEAD_FRAMES, STORYBOARD_FIELDS, SYSTEM  # noqa: E402


def _kit_text() -> str:
    return KIT_DOC.read_text(encoding="utf-8") if KIT_DOC.exists() else ""


_HINTS = (
    ("edge", "touches/overflows the canvas edge", "Give every text container an explicit width (<= 920) and centre it: left = LAYOUT.cx - width/2. Pass maxWidth to ArText. Never use right:/negative offsets."),
    ("overlap", "overlapping text", "Stack elements vertically with explicit y values at least 1.4 x the font size apart, computed from one list, and keep cards from covering each other's text. If the two overlapping texts share the same box, the same words are drawn twice (an outline/shadow copy, a duplicated list item, or two layers at the same x/y): draw every string exactly once and use textShadow or colour for emphasis. A keyword longer than ~12 characters at size >= 100 wraps and collides: use size <= 90 or put it in a separate Abs with its own y."),
    ("zone", "safe zones", "Every text must lie between LAYOUT.beat.top and LAYOUT.beat.bottom - 40 (and out of the map card when you use MapLayer)."),
    ("rtl", "right-to-left", "Render every Arabic string with <ArText> (it sets dir=rtl); never put Arabic directly in a div/span/svg text."),
    ("tiny", "too small", "Raise font sizes: body text >= 30 px, labels >= 26 px."),
    ("blank", "blank", "Draw visible content: at least a hero element and one ArText from frame 20 on."),
    ("name", "TS2304", "Every component/helper you use must be imported from '../kit' in the first import line (Ribbon, KeyLine, Hub, Steps, Stack, Pinned, Abs, ArText, Icon, Counter ...): add the missing name to that import."),
    ("css", "TS2353", "A style object has a property that is not real CSS (e.g. 'justify'): use exact camelCase CSS names - justifyContent, alignItems, flexDirection, textAlign, gap. Check every key you wrote in style={{...}}."),
    ("hero", "is not one of the elements' ids", "hero_element must be copied exactly from one elements[].id (the main SVG group's id); do not invent a new name."),
    ("anim", "is forbidden in the SVG", "Remove every <animate>, <animateTransform>, <animateMotion> and <set> from the SVG: it must be static. Put appearing parts in <g data-state=\"N\"> (the kit reveals them on the trigger word) and do any other motion in the TSX with spring/interpolate on a wrapper."),
    ("cssanim", "CSS animation/transition is not frame-deterministic", "Delete every transition/animation style key; drive opacity/transform from useCurrentFrame() with spring() or interpolate()."),
    ("spr", "\"smooth\" | \"snappy\" | \"bouncy\"", "useSpr presets are only 'smooth', 'snappy', 'bouncy'. 'pop' is an enter() kind, not a spring: useSpr(d, 'bouncy') then enter(p, 'pop')."),
    ("svgid","has layer 'svg' but the SVG has no element", "Give each storyboard element with layer 'svg' the SAME id in the SVG (id=\"x\" on its shape or <g>), or set its layer to 'tsx' if the scene file draws it (text, Counter, Icon, Ribbon, MapLayer)."),
    ("state", "group in the SVG", "Wrap the SVG shapes that appear in visual state N in <g data-state=\"N\">...</g> (state 1 needs no group), or drop that state from visual_states."),
    ("trigger", "must be copied from the narration", "trigger_word must be one word copied exactly from data.sentence, and later states must use words that come later in the sentence."),
    ("recipe", "TS2322", "A prop has the wrong type: check the recipe's exact signature in the kit doc (Steps items are strings; Stack/Hub items are objects; Hub center is a React node)."),
)


def hints_for(errors: List[str]) -> List[str]:
    out = []
    for _, needle, hint in _HINTS:
        if any(needle in e for e in errors):
            out.append(hint)
    return out


def build_prompts(ctx: Dict[str, Any], errors: Optional[List[str]] = None, previous: Optional[str] = None) -> Tuple[str, str]:
    slim = {k: v for k, v in ctx.items() if k != "map_overlay"}
    guide = (ctx.get("theme") or {}).get("art_guide", "")
    if guide:
        slim["theme"] = {k: v for k, v in ctx["theme"].items() if k != "art_guide"}
    slim["has_map_overlay"] = bool(ctx.get("map_overlay"))
    if ctx.get("map_overlay"):
        ov = ctx["map_overlay"]
        slim["map_places"] = ([{"name_en": w.get("name_en") or "", "name_ar": w.get("name_ar")} for w in ov.get("waypoints", [])]
                              + [{"name_en": f.get("name_en") or "", "name_ar": f.get("label")} for f in ov.get("features", [])])
    user = ("Scene data (this is exactly `data` in your component, except map_overlay which is injected; director_plan is the director's "
            "read-only plan for this scene, words are read-only timings):\n"
            + json.dumps(slim, ensure_ascii=False)
            + f"\n\nScene length: {ctx['dur']} frames at {FPS} fps. Write the storyboard, the hero SVG and the scene.")
    if errors and previous:
        hints = hints_for(errors)
        user += ("\n\nYour previous attempt was REJECTED. Fix every problem and return the complete corrected reply (all three blocks).\n"
                 "Problems:\n- " + "\n- ".join(errors[:14])
                 + ("\n\nHow to fix:\n- " + "\n- ".join(hints) if hints else "") + "\n\nPrevious reply:\n" + previous)
    from .director_plan import LANGUAGE_CONTRACT
    from .skills import DESIGNER_SKILLS, skills_block
    system = SYSTEM.replace("{contract}", LANGUAGE_CONTRACT).replace("{kit}", _kit_text()) + skills_block(DESIGNER_SKILLS)
    if guide:
        system += "\n\nART DIRECTION OF THIS VIDEO (a style guide: follow its essence, its 'not' list and its director rules; it overrides generic taste):\n" + guide
    return system, user


def extract_code(text: str) -> str:
    t = (text or "").strip()
    if "```" in t:
        parts = t.split("```")
        body = max(parts[1::2], key=len) if len(parts) > 2 else parts[-1]
        t = body.split("\n", 1)[1] if body.lstrip().lower().startswith(("tsx", "typescript", "ts", "jsx")) and "\n" in body else body
    lines = t.splitlines()
    starts = [i for i, ln in enumerate(lines) if ln.startswith("import ")]
    if not starts:
        return "\n".join(lines).strip() + "\n"
    # drop reasoning before the code; a model that "thinks aloud" may emit the file twice: an import group that follows
    # code (> 12 lines after the previous import) starts a new copy, keep the last copy that has the default export
    groups = [starts[0]] + [b for a, b in zip(starts, starts[1:]) if b - a > 12]
    first = groups[0]
    for g in groups:
        if any(ln.startswith("export default") or ln.startswith("export default") for ln in lines[g:]):
            first = g
    return "\n".join(lines[first:]).strip() + "\n"


def parse_steps(text: str) -> Tuple[Optional[Dict[str, Any]], str]:
    """Steps 1-2 of the designer reply: <extract>{JSON}</extract> and <brief>English visual brief</brief>."""
    t = text or ""
    ex = None
    m = re.search(r"<extract>(.*?)</extract>", t, re.S)
    if m:
        from .llm_providers import extract_json
        try:
            ex = extract_json(m.group(1))
        except Exception:  # noqa: BLE001 - reported by step_errors
            ex = None
    m = re.search(r"<brief>(.*?)</brief>", t, re.S)
    return (ex if isinstance(ex, dict) else None), (m.group(1).strip() if m else "")


STEP_FIELDS = ("subject", "one_idea", "entities", "numbers")


def step_errors(ex: Optional[Dict[str, Any]], brief: str, ctx: Dict[str, Any]) -> List[str]:
    """Step 1 must extract only what the narration says; step 2 must be a real English brief."""
    from .direct import _number_in_text
    errs: List[str] = []
    if not isinstance(ex, dict):
        errs.append('step 1 is missing: start the reply with <extract>{"subject": ..., "one_idea": ..., "entities": [...], "numbers": [...]}</extract>')
    else:
        errs += [f"step 1 <extract> field '{f}' is missing" for f in STEP_FIELDS if f not in ex]
        for n in ex.get("numbers") or []:
            if not _number_in_text(n, ctx.get("sentence", "")) and not re.search(r"[؀-ۿ]", str(n)):
                errs.append(f"step 1 extracted the number {n!r}, which is not spoken in the sentence: extract only spoken numbers")
    latin = re.findall(r"[A-Za-z]+", brief)
    if len(latin) < 15:
        errs.append("step 2 is missing or too short: write <brief>...</brief>, an English visual brief of at least 15 words "
                    "(what the viewer sees, the composition and the motion), translating the sentence's meaning and the director's concept")
    return errs


def parse_reply(text: str) -> Tuple[Optional[Dict[str, Any]], Optional[str], str]:
    """Designer reply -> (storyboard dict | None, hero svg | None, tsx code). Missing parts come back as None / ''."""
    t = text or ""
    sb = None
    m = re.search(r"<storyboard>(.*?)</storyboard>", t, re.S)
    if m:
        from .llm_providers import extract_json
        try:
            sb = extract_json(m.group(1))
        except Exception:  # noqa: BLE001 - reported as an invalid storyboard
            sb = None
    m = re.search(r"<hero_svg>(.*?)</hero_svg>", t, re.S)
    svg = None
    if m:
        body = m.group(1).replace("```svg", "").replace("```xml", "").replace("```", "")
        sm = re.search(r"<svg\b.*</svg>", body, re.S)
        svg = sm.group(0).strip() if sm else body.strip()
    m = re.search(r"<tsx>(.*?)(?:</tsx>|$)", t, re.S)
    rest = m.group(1) if m else re.sub(r"<storyboard>.*?</storyboard>|<hero_svg>.*?</hero_svg>", "", t, flags=re.S)
    return (sb if isinstance(sb, dict) else None), svg, extract_code(rest) if rest.strip() else ""


def storyboard_errors(sb: Optional[Dict[str, Any]], ctx: Dict[str, Any], svg: Optional[str]) -> List[str]:
    """Contract of the designer's 13-field visual description, and its link to the SVG (states and svg elements exist)."""
    from .director_plan import find_word, timing_keys
    if not isinstance(sb, dict):
        return ["the reply has no valid <storyboard>{...}</storyboard> JSON block"]
    errs = [f"storyboard field '{f}' is missing or empty" for f in STORYBOARD_FIELDS[1:] if not sb.get(f)]
    errs += [f"timing data is forbidden in the storyboard (the timing engine owns it): remove '{p}'" for p in timing_keys(sb)]
    els = sb.get("elements") if isinstance(sb.get("elements"), list) else []
    ids = {str(e.get("id")) for e in els if isinstance(e, dict) and e.get("id")}
    if sb.get("elements") and (not ids or any(not isinstance(e, dict) or not e.get("id") or not e.get("draw") for e in els)):
        errs.append("every storyboard element needs an id and a 'draw' description")
    if sb.get("hero_element") and str(sb.get("hero_element")) not in ids:
        errs.append(f"hero_element '{sb.get('hero_element')}' is not one of the elements' ids")
    svg_txt = svg or ""
    for e in els:
        if isinstance(e, dict) and e.get("id") and str(e.get("layer", "svg")) == "svg" and not re.search(rf'\bid=["\']{re.escape(str(e["id"]))}["\']', svg_txt):
            errs.append(f"element '{e['id']}' has layer 'svg' but the SVG has no element with id=\"{e['id']}\"")
    words = [str(w.get("t", "")) for w in ctx.get("words") or []]
    states = sb.get("visual_states") if isinstance(sb.get("visual_states"), list) else []
    pos = 0
    for st in states:
        if not isinstance(st, dict):
            errs.append("every visual state must be an object")
            continue
        n = st.get("state")
        for f in ("elements", "appearance", "condition"):
            if not st.get(f):
                errs.append(f"visual state {n}: '{f}' is missing")
        unknown = [x for x in (st.get("elements") or []) if str(x) not in ids]
        if unknown:
            errs.append(f"visual state {n} names unknown elements {unknown}")
        if not isinstance(n, int) or n < 1:
            errs.append(f"visual state numbers must be integers >= 1 (got {n!r})")
            continue
        if n == 1:
            continue
        trig = str(st.get("trigger_word") or "")
        i = find_word(words, trig, pos) if trig else None
        if i is None:
            errs.append(f"visual state {n}: trigger_word '{trig}' must be copied from the narration, after the previous state's word")
        else:
            pos = i + 1
        if not re.search(rf'data-state=["\']{n}["\']', svg_txt):
            errs.append(f"visual state {n} has no <g data-state=\"{n}\"> group in the SVG")
    return errs


def state_frames(sb: Dict[str, Any], words: List[Dict[str, Any]], dur: int) -> List[Dict[str, Any]]:
    """System-side: each visual state's trigger word -> the frame it appears, read from the EXISTING word timings (never computed
    by an LLM). State 1 is the opening picture (frame 0)."""
    from .director_plan import find_word
    toks = [str(w.get("t", "")) for w in words]
    out, pos = [], 0
    for st in sorted((s for s in sb.get("visual_states") or [] if isinstance(s, dict) and isinstance(s.get("state"), int)), key=lambda s: s["state"]):
        if st["state"] == 1:
            out.append({"state": 1, "from": 0, "word": ""})
            continue
        i = find_word(toks, str(st.get("trigger_word") or ""), pos)
        if i is None:
            continue
        pos = i + 1
        fr = max(0, min(dur - 1, int(round(float(words[i].get("s", 0)) * FPS)) - STATE_LEAD_FRAMES))
        out.append({"state": st["state"], "from": fr, "word": toks[i]})
    return out


def design_errors(sb: Optional[Dict[str, Any]], svg: Optional[str], code: str, ctx: Dict[str, Any]) -> List[str]:
    """All pre-render designer gates: storyboard contract, SVG gate, the TSX draws the SVG."""
    from .visual_qa import svg_problems
    errs = storyboard_errors(sb, ctx, svg) + svg_problems(svg)
    if not code.strip():
        errs.append("the reply has no <tsx> scene file")
    elif "<HeroSvg" not in code:
        errs.append("the scene must draw the hero SVG with <HeroSvg data={data} x=.. y=.. w=.. h=.. /> (import HeroSvg from '../kit')")
    return errs


def llm_write(system: str, user: str) -> Optional[str]:
    from .llm_router import get_router
    try:
        resp = get_router().dispatch(role="scene_writer", system=system, user=user, json_mode=False, timeout=150)
        return resp.content
    except Exception as e:  # noqa: BLE001 - the caller records the failure
        import logging
        logging.getLogger("pipeline.scene_author").warning("scene authoring llm call failed: %s", e)
        return None
