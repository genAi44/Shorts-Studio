"""Studio illustrator: a strong code model (role `illustrator`, DeepSeek V3 by default) draws the bespoke SVG hero of
each scene, the way the reference project does (a phone with its notch and dot projector, a face mesh, a jam shelf, a
battery that overflows): the drawing IS the explanation, written for this sentence, not picked from a fixed library.

What stays deterministic around it: the key line (compiled), the stage box, captions, safe zones, timing from the word
timestamps (given to the model in seconds), the render gates (tsc + allowlist, real render, layout audit, ink, the truth
rule on rendered numbers). A drawing that fails twice falls back to the compiled device of the shot (studio.py).
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Dict, List, Optional

from .config import FPS

ILLUSTRATOR_VERSION = 4
STAGE = {"x": 80, "y": 570, "w": 920, "h": 800}  # the drawing's box on the 1080x1920 canvas (under the key line)
HERO_MIN_INK = 0.012  # strong-gradient share inside the box at mid / late scene (an empty or washed-out drawing fails)
HERO_MIN_SIDE = 600  # px: the longest side of what is drawn ([data-hero-ink] bounds) at mid-scene
KIT_NAMES = "AbsoluteFill, interpolate, useKit, useSpr, useProgress, useIdle, clamp01, ease"

SYSTEM = """You are an elite motion-graphics illustrator for Arabic educational Shorts (vertical 1080x1920). For ONE
scene you draw the hero illustration as SVG inside a Remotion React component. The picture must EXPLAIN the sentence.

THINK FIRST (write it as the PLAN comment, 4-8 lines):
1. What is the simplest physical, spatial or familiar-object metaphor that makes this sentence understood at a glance?
   Draw the real thing, recognisably: a phone with its notch and dot projector, a face covered by infrared dots, a jam
   shelf with 24 jars, a battery that overflows, a river split by a dam, a brain with a jammed gear. Never a generic
   icon in a circle, never a dashboard of cards, never a "box with text".
2. What does it DO (behaviour, not state)? Something drops, splits, fills, empties, lights up, breaks, travels, is
   filtered. With all text removed, the motion alone must tell what happens.
3. The beats: which element appears or changes on which spoken word (their times are given in seconds).
4. Continuity: the video's core metaphor and recurring objects (given) come back when the sentence is about them.
5. Direction: read story_so_far and the video message. A bare number does not say which way things go ("33 metres by
   2050" in a story about a sea that is drying up means the level DROPS 33 m, it does not rise). Write the direction of
   every change in the PLAN as "Direction: <what> <rises|drops|grows|shrinks|...> because <the story says ...>", and
   draw exactly that.

DRAWING RULES
- You return ONE component: `const Hero: React.FC<{dur: number}> = ({dur}) => { ... }` that returns SVG children
  (a <g>, <path>, <rect>, <circle>, <text> ...), NOT an <svg> element: it is placed inside
  <svg width={920} height={800} viewBox="0 0 920 800">. Coordinates: x 0..920, y 0..800. Nothing outside.
- BIG: the subject spans at least 700 px of the 920 px width (or 650 px of the height for a tall subject); a render
  check measures the drawn bounds and rejects anything smaller. Centre it around (460, 400).
- RICH, like a polished Kurzgesagt / TED-Ed vector illustration: many shapes per object (body, rim, inner details,
  highlight strokes, a soft shadow ellipse under it, texture lines), linearGradient / radialGradient fills for volume,
  strokes 4-10. Frame 0 of the scene is already a composed, detailed picture (at most a 0.3 s entrance).
- The change on the key word is LARGE and OBVIOUS: a size change of 30 % or more, a clear before/after state, a
  count that visibly empties, a colour that turns. A viewer must see it on a phone at a glance.
- Colours mean something: use the palette hexes given in "palette" (pick the one whose hue fits: water bluish,
  danger the warm accent, neutral objects in ink / ground tones). Never paint water red or fire blue.
- Numbers and labels stay readable to the last frame: draw them LAST (after every shape) and put them where nothing
  moves, grows or sinks later in the scene (never on the path of a falling object, an opening pit, a rising fill).
- At most 3 primary focal elements; earlier elements recede (opacity ~0.4) when a new idea takes the stage.
- Colours ONLY from the theme: k.c('ground' | 'ground2' | 'text' | 'accent' | 'accent2' | 'hl0' | 'hl1' | 'hl2', alpha).
  ground = background colour, text = ink, accent = the strong colour, accent2 = the second colour.
- Text inside the drawing: at most 4 short Arabic labels (1-3 words) or numbers, fontSize >= 36, fontFamily={k.font},
  fontWeight 800, and for Arabic `direction="rtl"` with textAnchor="middle". Numbers: ONLY those in allowed_numbers
  (spoken in the sentence). No sentence text: the caption already shows the narration, the key line is above you.
- Gradient / filter / clipPath / pattern ids end with the given id_suffix (e.g. id={"glow" + SFX}).

MOTION RULES (deterministic: every value is a pure function of the frame)
- `const k = useKit();` gives k.t (seconds), k.frame, k.fps, k.c(...), k.font. Use interpolate(k.t, [a, b], [x, y],
  {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease.out}) for every change; clamp01(x) is available.
- useSpr(delaySeconds, 'snappy' | 'bouncy' | 'smooth') returns 0..1 (a spring); useIdle(amp, period) a gentle
  sine float. Call hooks ONLY at the top of Hero (never in loops, conditions or callbacks); inside .map() use
  interpolate on k.t. No Math.random, no Date, no state, no effects. A seeded pattern: use (i * 37) % 11 style maths.
- An element tied to a word appears 0.1-0.2 s BEFORE that word's start time, never after. Every change is finished
  0.8 s before the scene ends. Something always moves (idle float, pulse, flowing dashes).

OUTPUT: only TypeScript code, no imports (they are provided: React, {KIT}), no markdown fences, no export.
Start with `/* PLAN: ... */`, then any small helper consts / module-level components, then `const Hero`. Keep it
under 220 lines.""".replace("{KIT}", KIT_NAMES)

HEADER = f"""import React from 'react';
import {{AbsoluteFill}} from 'remotion';
import {{Abs, KeyLine, LAYOUT, Ribbon, SceneProps, interpolate, useIdle, useKit, useSpr, useProgress, clamp01, ease}} from '../kit';
"""


def allowed_numbers(ctx: Dict[str, Any]) -> List[str]:
    """Numbers a drawing may show: spoken in the sentence (digits or words), entity values, and the rest of a spoken
    percentage (studio.number_ok decides; this lists the candidates the model may use)."""
    from .studio import _AR_DIGITS, _DIGITS, number_ok, word_numbers
    cands = set()
    for m in _DIGITS.findall(ctx["sentence"].translate(_AR_DIGITS)):
        cands.add(float(m.replace(",", "")))
    cands |= {float(v) for v in word_numbers(ctx["sentence"])}
    for e in ctx.get("entities", []):
        for k in ("value", "year", "to", "from"):
            try:
                cands.add(float(e[k]))
            except (KeyError, TypeError, ValueError):
                pass
    for v in list(cands):
        if 0 < v < 100:
            cands.add(100 - v)
    cands.add(100.0)
    out = []
    for v in sorted(cands):
        if number_ok(v, ctx):
            out.append(str(int(v)) if float(v).is_integer() else str(v))
    return out


def brief(ctx: Dict[str, Any], shot: Optional[Dict[str, Any]], ds: Dict[str, Any], sfx: str,
          story: Optional[Dict[str, Any]] = None) -> str:
    words = [{"word": w["t"], "start_s": round(float(w["s"]), 2)} for w in ctx["words"]]
    story = story or {}
    return json.dumps({
        "video_message": story.get("message"),
        "story_so_far": story.get("before", []),
        "scene_intent": story.get("intent"),
        "sentence": ctx["sentence"],
        "scene_seconds": round(ctx["dur"] / FPS, 2),
        "words_with_times": words,
        "key_line_above_the_drawing": (shot or {}).get("keyword"),
        "designer_idea": {k: (shot or {}).get(k) for k in ("behavior", "why") if (shot or {}).get(k)},
        "video": {"core_metaphor": ds["motif"].get("core_metaphor"), "recurring_objects": ds["motif"].get("objects") or [],
                  "world": ds["motif"].get("world"), "style": ds.get("name") or ds.get("preset"), "avoid": ds.get("not", [])},
        "theme_is_dark": bool(ds.get("dark")),
        "palette": {k: v for k, v in (ds.get("theme") or {}).items() if isinstance(v, str) and v.startswith("#")},
        "allowed_numbers": allowed_numbers(ctx),
        "id_suffix": sfx,
    }, ensure_ascii=False)


def strip_code(text: str) -> str:
    t = (text or "").strip()
    if "```" in t:
        parts = t.split("```")
        body = max(parts[1::2], key=len) if len(parts) > 2 else parts[-1]
        t = body.split("\n", 1)[1] if re.match(r"\s*(tsx|typescript|ts|jsx|javascript)\b", body, re.I) and "\n" in body else body
    lines = [ln for ln in t.splitlines() if not ln.startswith("import ") and not ln.startswith("export default")]
    code = "\n".join(lines)
    code = re.sub(r"^export\s+(const|function)\s", r"\1 ", code, flags=re.M)
    i = code.find("/* PLAN")
    return (code[i:] if i > 0 else code).strip() + "\n"


def plan_of(code: str) -> str:
    m = re.search(r"/\*\s*PLAN:?(.*?)\*/", code, re.S)
    return re.sub(r"\s+", " ", m.group(1)).strip()[:400] if m else ""


def scene_code(hero: str, shot: Optional[Dict[str, Any]], ctx: Dict[str, Any], ds: Dict[str, Any]) -> str:
    """The full scene: compiled key line + the model's Hero inside the fixed stage box, under the studio camera."""
    from .studio import CAMERA_BOB, CAMERA_PUSH, _keyline
    kl = _keyline(shot, ctx["words"], "LAYOUT.beat.top + 10", 92) if shot and str(shot.get("keyword") or "").strip() else ""
    ribbon = f"      <Ribbon variant={{{int(ds['motif']['ribbon_variant'])}}} />"
    return HEADER + "\n" + hero + f"""
export default function Scene({{dur, data}}: SceneProps) {{
  const k = useKit();
  const cam = interpolate(k.frame, [0, Math.max(1, dur)], [1, {CAMERA_PUSH}], {{extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}});
  const bob = useIdle({CAMERA_BOB}, 4.5, 0);
  return (
    <AbsoluteFill>
{ribbon}
      <AbsoluteFill style={{{{transform: `translateY(${{bob}}px) scale(${{cam}})`, transformOrigin: '50% 45%'}}}}>
{kl}
      <Abs x={{{STAGE['x']}}} y={{{STAGE['y']}}} w={{{STAGE['w']}}} h={{{STAGE['h']}}}>
        <svg data-hero="illustration" width={{{STAGE['w']}}} height={{{STAGE['h']}}} viewBox="0 0 {STAGE['w']} {STAGE['h']}" style={{{{overflow: 'visible'}}}}>
          <g data-hero-ink="1"><Hero dur={{dur}} /></g>
        </svg>
      </Abs>
      </AbsoluteFill>
    </AbsoluteFill>
  );
}}
"""


def name_for(ctx: Dict[str, Any], shot: Optional[Dict[str, Any]], ds: Dict[str, Any]) -> str:
    key = json.dumps({"v": ILLUSTRATOR_VERSION, "s": ctx["sentence"], "dur": ctx["dur"], "kw": (shot or {}).get("keyword"),
                      "b": (shot or {}).get("behavior"), "m": ds["motif"].get("core_metaphor"), "theme": ctx.get("theme")},
                     sort_keys=True, ensure_ascii=False)
    return "s_il" + hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]


def draw(ctx: Dict[str, Any], shot: Optional[Dict[str, Any]], ds: Dict[str, Any], sfx: str,
         problems: Optional[List[str]] = None, previous: Optional[str] = None, write=None,
         story: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """One illustrator call -> the Hero code (no imports), or None. `story`: {message, before (earlier sentences), intent}."""
    user = brief(ctx, shot, ds, sfx, story)
    if problems:
        user += ("\n\nYour previous drawing was REJECTED by the render check. Fix every problem, keep what worked, return "
                 "the complete corrected code.\nProblems:\n- " + "\n- ".join(problems[:10]) + "\n\nPrevious code:\n" + (previous or ""))
    text = (write or _write)(SYSTEM, user)
    return strip_code(text) if text and "const Hero" in text else None


def _write(system: str, user: str) -> Optional[str]:
    from .llm_router import get_router
    try:
        return get_router().dispatch(role="illustrator", system=system, user=user, json_mode=False, timeout=240).content
    except Exception as e:  # noqa: BLE001 - the caller falls back to the compiled device
        import logging
        logging.getLogger("pipeline.illustrator").warning("illustrator call failed: %s", e)
        return None
