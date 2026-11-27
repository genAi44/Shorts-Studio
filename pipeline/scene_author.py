"""Art director as a code author: every scene can be real React/TSX written by the LLM against a documented kit.

Flow per scene (see docs/SCENE_KIT.md):
    prompt(sentence, entities, theme, layout, kit docs) -> TSX
    -> static gate   (node remotion/scripts/check-scene.mjs: AST allowlist + tsc)
    -> sandbox render of 3 frames of the real composition (child process, timeout, DOM audit)
    -> automated checks (not blank, no overflow/overlap, nothing in the caption zone, Arabic RTL, readable size)
    -> accepted: cached by content hash (data/authored_cache) and saved as a file in the job folder (outputs/<job>/scenes/)
    on failure: the errors go back to the LLM (MAX_RETRIES), then the built-in beats are kept and a warning is recorded.

LLM code is never executed outside that gate. The same files serve preview and final render (sync_to_remotion).
"""
from __future__ import annotations

import contextlib
import hashlib
import json
import os
import re
import shutil
import re
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple

from .config import FPS, ROOT, record_fallback

REMOTION = ROOT / "remotion"
MIN_CONTENT_H = 420  # px of vertical extent of everything a scene draws (beat zone is 1100)
AUTHORED_SRC = REMOTION / "src" / "authored"
KIT_DOC = ROOT / "docs" / "SCENE_KIT.md"
CACHE_DIR = ROOT / "data" / "authored_cache"
KIT_VERSION = 3  # 3: designer thinks and writes in English (2: storyboard + hero SVG + TSX)
MAX_RETRIES = 4
TEST_FRAME_FRACTIONS = (0.15, 0.5, 0.9)
FLAT_STD = 6.0
STATE_LEAD_FRAMES = 2       # a visual state enters this many frames before its trigger word (anticipation)
HERO_MIN_COVER = 0.06       # rendered SVG content must cover >= 6% of its viewBox
HERO_MIN_PX = 160           # and be at least this big on the 1080x1920 canvas (both sides)

# The designer's visual description of a scene: 13 fields (A elements, B visual states, C composition & layout, + the hero).
STORYBOARD_FIELDS = (
    "scene_id",           # 1  the scene (system-owned, overwritten)
    "visual_concept",     # 2  how the picture expresses the director's main concept
    "hero_element",       # 3  id of the one hero element (an `elements` id)
    "elements",           # 4  A: [{id, draw, role, layer: "svg"|"text"}] everything that must be drawn and why
    "visual_states",      # 5  B: [{state, elements, appearance, positions, condition, trigger_word}]
    "composition",        # 6  C: overall composition
    "positions",          # 7  C: {element_id: where it sits}
    "relative_sizes",     # 8  C: {element_id: size relative to the canvas / hero}
    "alignment",          # 9  C: alignment rules
    "layering",           # 10 C: back-to-front order of element ids
    "spatial_relations",  # 11 C: how elements relate in space
    "visual_hierarchy",   # 12 C: what the eye reads 1st, 2nd, 3rd
    "layout_changes",     # 13 C: how the layout changes from state to state
)

SYSTEM = """You are the DESIGNER of an Arabic-language educational Shorts studio (1080x1920): the art director AND the motion-graphics engineer.

{contract}

In this scene file: every identifier, function name, variable name and comment is English; the only Arabic in the TSX are the strings drawn on
screen through ArText, copied from data.sentence / data.sentences or an entity's name_ar (never translated, never invented). The storyboard, element ids,
"draw" / "role" / "appearance" descriptions and SVG ids are English; only "trigger_word" is copied verbatim (Arabic) from the narration.

The DIRECTOR has already decided this scene. data.director_decision is BINDING: its "concept" is the picture to draw (the subject,
composition and motion it describes) and its "title" is the on-screen headline idea - realise THAT idea, never replace it with another one.
data.director_plan adds the story context (objective, facts to get across, links to the previous/next scene, transition trigger, continuity).
Your job is to turn the director's decision into a picture. Follow the kit documentation below exactly.

REPLY FORMAT (exactly three blocks, in this order, nothing else, no markdown fences):
<storyboard>
{JSON visual description with exactly these 13 fields:
 "scene_id", "visual_concept",
 "elements": [{"id": "...", "draw": "what exactly is drawn", "role": "why it is there", "layer": "svg" | "tsx"}],
   (layer "svg" = drawn INSIDE your <hero_svg> with that exact id; layer "tsx" = drawn by the scene file: ArText, Counter, Icon,
    Ribbon, MapLayer, cards... Keep "svg" elements few - the 2-5 shapes/groups of the illustration - and give each its id.)
 "hero_element": COPY one "id" from the elements list above (never a new name; usually your main SVG group),
 "visual_states": [{"state": 1, "elements": ["ids visible in this state"], "appearance": "how each element looks",
                    "positions": "where they are", "condition": "what changes into this state", "trigger_word": "a word of the narration"}],
 "composition", "positions": {"id": "where"}, "relative_sizes": {"id": "size vs canvas/hero"}, "alignment",
 "layering": ["back-most id", "...", "front-most id"], "spatial_relations", "visual_hierarchy", "layout_changes"}
</storyboard>
<hero_svg>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 W H"> ... the scene's main graphic ... </svg>
</hero_svg>
<tsx>
the scene file (first line an import)
</tsx>

Storyboard rules: write the SVG first in your head, then list its ids as the "svg" elements (same spelling). State 1 is the opening picture (its trigger_word may be ""); every later state's trigger_word is copied from the
narration (data.sentence) and the states follow the narration's order. Every element with layer "svg" is drawn in the SVG with
id="<its id>"; every element of state N >= 2 that appears only from that state is inside <g data-state="N">...</g> (the kit reveals
that group when its trigger word is spoken). Prefer 1-3 states; a state that only changes TSX text still needs its <g data-state="N">
around the SVG part that changes with it (e.g. a highlight ring). The SVG is a real illustration of the visual concept (shapes, paths, the hero object),
never empty, never a placeholder: >= 3 painted shapes, viewBox required, colours from the theme. The SVG is STATIC: no <animate>,
<animateTransform>, <animateMotion>, <set>, no CSS animation/transition (the kit reveals each <g data-state> on its word; any extra motion
goes in the TSX with spring/interpolate). Also no <script>, <style>, <image>, <foreignObject>, external links or event handlers; no text
inside the SVG (all Arabic text goes through ArText in the TSX). In the TSX never use style transition/animation either.
The TSX must draw the SVG with <HeroSvg data={data} x=.. y=.. w=.. h=.. /> placed according to your storyboard.

TIMING IS READ-ONLY: data.words carries word timings computed by the timing engine. Read them if you need to, but never invent,
estimate, compute, copy or change timings, and never put any timing (seconds, frames, durations, start/end) in the storyboard or the
SVG. To make something change at a moment, name the word (trigger_word); the system resolves it. Captions are built by the system:
never draw captions or subtitles.

Design brief: the scene must express THIS sentence and its entities visually, with art direction: one hero element, clear
Arabic typographic hierarchy, layered (semi-transparent) decoration, staggered entrances, something always gently moving.
Never a plain card or a bare emoji. Use the entities' real data (numbers, years, names); do not invent facts.
If data.map_overlay exists, the places must be shown on the map with <MapLayer overlay={data.map_overlay} /> (you may add
supporting elements, but do not cover the map or the caption zone). The map engine already DRAWS what the sentence names: countries,
cities, rivers, mountain ranges (a ridge drawn frame by frame) and, when a line divides a country (the Urals: Europe | Asia), the country
cut in two coloured halves with labels. Never re-draw those yourself and never replace them by a text card. Keep the video's ground visible (no opaque full-canvas fill).

{kit}
"""


# ------------------------------------------------------------------ prompts


# ------------------------------------------------------------------ context, ids, cache

def scene_context(scene: Dict[str, Any], theme: Dict[str, Any]) -> Dict[str, Any]:
    from .direct import sentences
    words = scene.get("words") or []
    narration = " ".join(str(w.get("t", "")) for w in words)
    ents = [e for per in scene.get("entity_plan") or [] for e in per]
    keep = ("type", "scale", "text", "name_en", "country_en", "name_ar", "value", "unit", "label_ar", "compare", "born", "died", "role_ar", "to", "from", "year", "lat", "lon", "stops", "a", "b")
    return {
        "id": scene.get("id"), "role": scene.get("role"), "dur": int(scene.get("dur", 150)),
        "sentence": narration, "sentences": sentences(narration),
        "entities": [{k: e[k] for k in keep if k in e} for e in ents],
        "words": [{"t": w["t"], "s": round(float(w.get("s", 0)), 2), "e": round(float(w.get("e", 0)), 2)} for w in words][:60],
        "map_overlay": scene.get("map_overlay"), "theme": theme,
        "director_decision": director_decision(scene),
    }


def director_decision(scene: Dict[str, Any]) -> List[Dict[str, Any]]:
    """The beat director's decision for this scene (step 3 of the app), handed to the designer as binding input."""
    out = []
    for b in scene.get("beats") or []:
        if isinstance(b, dict) and (b.get("concept") or b.get("title")):
            out.append({k: b[k] for k in ("kind", "title", "concept", "camera") if b.get(k)})
    return out


def _gate_sig() -> str:
    """Hash of the code a scene is checked and rendered against: a changed map/audit/layout invalidates cached scenes."""
    h = hashlib.sha1()
    for f in ("mapOverlay.tsx", "layoutAudit.tsx", "layout.ts"):
        p = REMOTION / "src" / f
        h.update(p.read_bytes() if p.exists() else b"")
    return h.hexdigest()[:10]


def content_hash(ctx: Dict[str, Any]) -> str:
    ov = json.dumps(ctx.get("map_overlay"), sort_keys=True, ensure_ascii=False)
    payload = json.dumps({"v": KIT_VERSION, "doc": hashlib.sha1(_kit_text().encode("utf-8")).hexdigest(), "gate": _gate_sig(), "sentence": ctx["sentence"],
                          "entities": ctx["entities"], "decision": ctx.get("director_decision") or [], "theme": ctx["theme"], "dur": ctx["dur"], "role": ctx["role"],
                          "overlay": hashlib.sha1(ov.encode("utf-8")).hexdigest()}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]


def scene_name(h: str) -> str:
    return f"s_{h}"


# ------------------------------------------------------------------ gates

def static_check(path: Path) -> List[str]:
    """AST allowlist + tsc, in node (TypeScript compiler API). Returns the list of problems (empty = accepted)."""
    try:
        r = subprocess.run(["node", "scripts/check-scene.mjs", str(Path(path).resolve())], cwd=REMOTION, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
        lines = r.stdout.strip().splitlines()
        if not lines:
            return [f"static check crashed: {(r.stderr or '')[-240:]}"]
        d = json.loads(lines[-1])
        return list(d.get("violations", [])) + list(d.get("diagnostics", []))
    except Exception as e:  # noqa: BLE001
        return [f"static check could not run: {e}"]


def _flat(path: Path) -> bool:
    import numpy as np
    from PIL import Image
    arr = np.asarray(Image.open(path).convert("L"), dtype="float32")
    return float(arr[280:1380, :].std()) < FLAT_STD


def sandbox_render(items: Dict[str, Dict[str, Any]], style: Dict[str, Any], workdir: Path, _retry: bool = False) -> Dict[str, List[str]]:
    """Renders 3 frames of every candidate with the REAL composition (one bundle for the batch) in a child process with a
    timeout, then audits them. items: name -> {"ctx": ctx}. Returns name -> problems."""
    problems: Dict[str, List[str]] = {n: [] for n in items}
    if not items:
        return problems
    workdir.mkdir(parents=True, exist_ok=True)
    scenes, frames, t = [], [], 0
    for name, it in items.items():
        ctx = it["ctx"]
        dur = ctx["dur"]
        scenes.append({"id": name, "role": "body", "from": t, "dur": dur, "words": [{"t": w["t"], "s": w["s"], "e": w["e"]} for w in ctx["words"]],
                       "visuals": [], "beats": [{"kind": "authored", "scene_id": name, "from": 0, "dur": dur, "data": {k: v for k, v in ctx.items() if k != "id"}}],
                       "map_overlay": None})
        frames.append((name, [t + max(2, int(dur * f)) for f in TEST_FRAME_FRACTIONS], dur))
        t += dur
    spec = {"fps": FPS, "width": 1080, "height": 1920, "total": t, "audio": "", "style": style, "scenes": scenes}
    sp = workdir / "check_spec.json"
    sp.write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
    all_frames = [f for _, fs, _ in frames for f in fs]
    out_pat = str(workdir / "chk_%d.jpg")
    try:
        r = subprocess.run(["node", "still.mjs", str(sp), out_pat, ",".join(map(str, all_frames)), str(REMOTION / "public")], cwd=REMOTION,
                           env=dict(os.environ, AUDIT="1"), capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=60 + 25 * len(all_frames))
        if r.returncode != 0:
            # a failed batch must not cost every scene a retry: render the scenes one by one so only the guilty one is blamed
            if len(items) > 1:
                merged: Dict[str, List[str]] = {}
                for n, it in items.items():
                    merged.update(sandbox_render({n: it}, style, workdir))
                return merged
            if not _retry:  # a single scene: one more try before it is reported
                return sandbox_render(items, style, workdir, _retry=True)
            for n in problems:
                problems[n].append("sandbox render failed: " + (r.stderr or r.stdout)[-300:])
            return problems
    except subprocess.TimeoutExpired:
        for n in problems:
            problems[n].append("sandbox render timed out")
        return problems
    for name, fs, dur in frames:
        for idx, f in enumerate(fs):
            img = workdir / f"chk_{f}.jpg"
            aud_f = Path(str(img) + ".audit.json")
            if not img.exists() or not aud_f.exists():
                problems[name].append(f"frame {idx + 1}/3 was not rendered")
                continue
            aud = json.loads(aud_f.read_text(encoding="utf-8"))
            late = idx >= 1  # entrance (first test frame) may cross edges / overlap; later frames may not
            if idx == 1 and (_flat(img) or aud.get("texts", 0) == 0):
                problems[name].append("the scene is blank or has no visible text at mid-scene")
            if idx == 1 and items[name]["ctx"].get("hero_svg") is not None:  # SVG gate, render half: measured in the real render
                hero = aud.get("hero")
                if not hero:
                    problems[name].append("the hero SVG is not rendered at mid-scene (draw it with <HeroSvg data={data} .../> and keep it visible)")
                else:
                    hb = hero.get("box") or [0, 0, 0, 0]
                    if hero.get("opacity", 1) < 0.3:
                        problems[name].append("the hero SVG is (almost) invisible at mid-scene: keep its opacity >= 0.3")
                    if hb[2] - hb[0] < HERO_MIN_PX or hb[3] - hb[1] < HERO_MIN_PX:
                        problems[name].append(f"the hero SVG is too small on screen ({hb[2] - hb[0]}x{hb[3] - hb[1]} px, need >= {HERO_MIN_PX} px each side)")
                    if hero.get("cover", 0) < HERO_MIN_COVER or hero.get("painted", 0) < 3:
                        problems[name].append(f"the rendered hero SVG draws almost nothing (covers {hero.get('cover', 0):.0%} of its viewBox, "
                                              f"{hero.get('painted', 0)} visible shapes): draw a real illustration that fills its viewBox")
            bb = aud.get("bbox")
            hero = aud.get("hero") or {}
            if bb and hero.get("box") and hero.get("opacity", 1) >= 0.3:  # the hero SVG is content too, not only text/icons
                hb = hero["box"]
                bb = [min(bb[0], hb[0]), min(bb[1], hb[1]), max(bb[2], hb[2]), max(bb[3], hb[3])]
            if idx == 1 and bb and (bb[3] - bb[1]) < MIN_CONTENT_H and not any(i.get("type") == "map" for i in aud.get("issues", [])):
                problems[name].append(f"the scene is too sparse: all its content spans only {bb[3] - bb[1]} px of height (need >= {MIN_CONTENT_H}); build a real composition - lead line, hero element, supporting elements, spread over y 280..1380")
            for it in aud.get("issues", []):
                typ, txt = it["type"], f"'{it.get('text', '')}'" + (f" x '{it['other']}'" if it.get("other") else "")
                where = f"@{it.get('box')}"
                if typ == "edge" and late:
                    problems[name].append(f"text touches/overflows the canvas edge: {txt} {where}")
                elif typ == "overlap" and late:
                    problems[name].append(f"overlapping text: {txt} {where}" + (f" with the second text at {it.get('obox')} (move one of them so the boxes do not intersect)" if it.get("obox") else ""))
                elif typ == "map" and late:
                    problems[name].append(f"text sits on the map stage {txt} {where}: the map occupies {it.get('obox')}. Either keep every other element above its top edge (y <= 690) with much less content (no big counter), or switch to <MapLayer mode=\"hud\" /> (small map at y ~995..1420) and use y 280..960 for the content")
                elif typ == "zone":
                    problems[name].append(f"text outside the safe zones (caption zone / above safe top): {txt} {where}")
                elif typ == "rtl":
                    problems[name].append(f"Arabic text not right-to-left (use ArText): {txt}")
                elif typ == "tiny":
                    problems[name].append(f"text too small for a phone ({it.get('fs')}px < 22): {txt}")
    for n in problems:  # de-duplicate, keep order
        problems[n] = list(dict.fromkeys(problems[n]))
    return problems


# ------------------------------------------------------------------ files, sync

@contextlib.contextmanager
def sync_to_remotion(authored_dir: Optional[str], only: Optional[set] = None) -> Iterator[List[Path]]:
    """Copy the job's scene files into remotion/src/authored for the duration of a preview/render (then remove them so
    stale scenes never break the type check of the project). Preview and final render use exactly these files."""
    copied: List[Path] = []
    try:
        if authored_dir and Path(authored_dir).is_dir():
            AUTHORED_SRC.mkdir(parents=True, exist_ok=True)
            for f in Path(authored_dir).glob("s_*.tsx"):
                if only is not None and f.stem not in only:
                    continue  # a rejected candidate must never reach the bundler (one syntax error breaks every scene)
                dst = AUTHORED_SRC / f.name
                shutil.copyfile(f, dst)
                copied.append(dst)
        yield copied
    finally:
        for f in copied:
            with contextlib.suppress(OSError):
                f.unlink()


# ------------------------------------------------------------------ the authoring loop

def _design_data(design: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
    """What the designer adds to the scene's `data`: its storyboard, the SVG, and the frames of its visual states (resolved by the
    system from the existing word timings)."""
    sb = design["storyboard"]
    return {"storyboard": sb, "hero_svg": design["svg"], "hero_states": state_frames(sb, ctx.get("words") or [], int(ctx.get("dur", 150)))}


NATIVE_KINDS = ("map", "map_pin", "area_map")


def has_native_visual(scene: Dict[str, Any]) -> bool:
    """A scene whose director beats show a real map or a found licensed photo: those render with the native
    components, an authored TSX scene would replace them with a drawing (seen: 0 photos on screen from 9 found)."""
    return any(isinstance(b, dict) and (b.get("kind") in NATIVE_KINDS or (b.get("kind") == "photo" and b.get("img")))
               for b in scene.get("beats") or [])


def author_spec(spec: Dict[str, Any], job_dir: str, llm: Optional[Callable[[str, str], Optional[str]]] = None, cache_only: bool = False,
                log: Callable[[str], None] = print, only_ids: Optional[set] = None,
                director_llm: Optional[Callable[[str, str], Any]] = None) -> Dict[str, Any]:
    """Director plan -> designer (storyboard + hero SVG + TSX) -> gates, for every scene; replaces the built-in beats of a scene when
    its authored version passes all gates. Mutates and returns the spec; writes outputs/<job>/director_plan.json,
    scenes/*.tsx + scenes/*.json (storyboard + SVG), scenes/manifest.json and authoring_report.json."""
    from .style import theme_from_style
    llm = llm or llm_write
    theme = theme_from_style(spec["style"])
    job_dir = str(Path(job_dir).resolve())  # node runs with another cwd: always absolute paths
    scenes_dir = Path(job_dir) / "scenes"
    scenes_dir.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    native = {s["id"] for s in spec["scenes"] if has_native_visual(s)}
    for sid in sorted(native):
        log(f"scene authoring: '{sid}' keeps its director visual (real photo / map), not re-authored")
    ctxs = {s["id"]: scene_context(s, theme) for s in spec["scenes"]
            if (only_ids is None or s["id"] in only_ids) and s["id"] not in native}
    names = {sid: scene_name(content_hash(c)) for sid, c in ctxs.items()}  # the director plan is derived from the narration (hashed)
    report: Dict[str, Any] = {"scenes": {}, "started": time.strftime("%Y-%m-%d %H:%M:%S")}
    accepted: Dict[str, str] = {}
    pending: Dict[str, Dict[str, Any]] = {}
    designs: Dict[str, Dict[str, Any]] = {}  # sid -> {"storyboard", "svg"} of the accepted designer reply

    # DIRECTOR: one narrative plan for the whole video, read-only input of the designer (pipeline/director_plan.py)
    from . import director_plan
    plans = director_plan.plan_video(spec, CACHE_DIR, llm=director_llm, cache_only=cache_only, log=log)
    for sid, ctx in ctxs.items():
        ctx["director_plan"] = plans.get(sid) or {}
    (Path(job_dir) / "director_plan.json").write_text(json.dumps(plans, ensure_ascii=False, indent=1), encoding="utf-8")

    for sid, ctx in ctxs.items():  # cache first
        name = names[sid]
        hit = CACHE_DIR / f"{name}.tsx"
        side = CACHE_DIR / f"{name}.json"
        rep = report["scenes"].setdefault(sid, {"name": name, "attempts": 0, "errors": [], "status": "pending"})
        cached = json.loads(side.read_text(encoding="utf-8")) if hit.exists() and side.exists() else None
        if cached and not design_errors(cached.get("storyboard"), cached.get("svg"), hit.read_text(encoding="utf-8"), ctx):
            shutil.copyfile(hit, scenes_dir / f"{name}.tsx")
            accepted[sid] = name
            designs[sid] = cached
            rep["status"] = "cache"
        elif not cache_only:
            pending[sid] = {"ctx": ctx, "errors": None, "code": None}
        else:
            rep["status"] = "not cached"
            record_fallback(f"preview: authored scene for '{sid}' is not cached yet, built-in beats shown (final render will author it)", beat_id=sid)

    for attempt in range(MAX_RETRIES + 1):
        if not pending:
            break
        log(f"scene authoring: attempt {attempt + 1}, {len(pending)} scene(s)")
        def write(sid: str) -> Tuple[str, Optional[str]]:
            sysp, usr = build_prompts(pending[sid]["ctx"], pending[sid]["errors"], pending[sid]["code"])
            return sid, llm(sysp, usr)
        with ThreadPoolExecutor(max_workers=3) as ex:
            written = list(ex.map(write, list(pending)))
        ready: Dict[str, Dict[str, Any]] = {}
        for sid, reply in written:
            rep = report["scenes"][sid]
            rep["attempts"] += 1
            if not reply:
                rep["errors"].append(f"attempt {attempt + 1}: the model returned nothing")
                pending[sid]["errors"], pending[sid]["code"] = ["the model returned nothing"], pending[sid]["code"] or ""
                continue
            ctx = pending[sid]["ctx"]
            sb, svg, code = parse_reply(reply)
            pending[sid]["code"] = reply
            errs = design_errors(sb, svg, code, ctx)  # storyboard contract + SVG gate + the scene draws the SVG
            if errs:
                rep["errors"].append(f"attempt {attempt + 1} design: {errs[:4]}")
                pending[sid]["errors"] = errs
                continue
            path = scenes_dir / f"{names[sid]}.tsx"
            path.write_text(code, encoding="utf-8")
            errs = static_check(path)
            if not errs and ctx.get("map_overlay") and "MapLayer" not in code:
                errs = ["the sentence names places / lines / ranges and data.map_overlay is ready: the scene must show it with <MapLayer overlay={data.map_overlay} /> "
                        "(it draws the country, drawn mountain ranges and dividing lines, and a country cut in two halves with labels); build your composition around it"]
            if errs:
                path.unlink(missing_ok=True)
                rep["errors"].append(f"attempt {attempt + 1} static: {errs[:4]}")
                pending[sid]["errors"] = errs
                continue
            sb["scene_id"] = sid  # system-owned
            designs[sid] = {"storyboard": sb, "svg": svg}
            ready[sid] = {"ctx": {**ctx, **_design_data(designs[sid], ctx)}}
        if ready:
            with sync_to_remotion(str(scenes_dir), only={names[s] for s in ready}):
                probs = sandbox_render({names[s]: v for s, v in ready.items()}, spec["style"], Path(job_dir) / "scenes_check")
            for sid in ready:
                pr = probs.get(names[sid], [])
                if pr:
                    (scenes_dir / f"{names[sid]}.tsx").unlink(missing_ok=True)
                    report["scenes"][sid]["errors"].append(f"attempt {attempt + 1} render: {pr[:4]}")
                    pending[sid]["errors"] = pr
                else:
                    accepted[sid] = names[sid]
                    report["scenes"][sid]["status"] = "accepted"
                    shutil.copyfile(scenes_dir / f"{names[sid]}.tsx", CACHE_DIR / f"{names[sid]}.tsx")
                    (CACHE_DIR / f"{names[sid]}.json").write_text(json.dumps(designs[sid], ensure_ascii=False), encoding="utf-8")
                    pending.pop(sid)

    for sid, p in pending.items():  # exhausted: keep the built-in beats, loudly
        report["scenes"][sid]["status"] = "fallback"
        (scenes_dir / f"{names[sid]}.tsx").unlink(missing_ok=True)
        record_fallback(f"authored scene for '{sid}' rejected after {report['scenes'][sid]['attempts']} attempt(s) ({(p['errors'] or ['?'])[0][:90]}): built-in beats kept", beat_id=sid)

    for s in spec["scenes"]:
        name = accepted.get(s["id"])  # only scenes that were authored / cached
        if not name:
            continue
        ctx = ctxs[s["id"]]
        data = {k: v for k, v in ctx.items() if k != "id"}
        data.update(_design_data(designs[s["id"]], ctx))
        (scenes_dir / f"{name}.json").write_text(json.dumps(designs[s["id"]], ensure_ascii=False, indent=1), encoding="utf-8")
        s["authored"] = {"scene_id": name, "attempts": report["scenes"][s["id"]]["attempts"], "status": report["scenes"][s["id"]]["status"]}
        s["authored_replaced"] = [b.get("kind") for b in s.get("beats", [])]
        s["beats"] = [{"kind": "authored", "scene_id": name, "from": 0, "dur": s["dur"], "data": data,
                       "settled": s.get("role") == "hook"}]
        s["map_overlay"] = None  # the scene draws the map itself through MapLayer(data.map_overlay)
    spec["authored_dir"] = str(scenes_dir)
    n = len(report["scenes"])
    tries = sum(r["attempts"] for r in report["scenes"].values())
    report["summary"] = {"scenes": n, "accepted": len(accepted), "fallback": n - len(accepted), "llm_attempts": tries,
                         "retry_rate": round(max(0, tries - sum(1 for r in report["scenes"].values() if r["attempts"])) / max(1, n), 2)}
    (scenes_dir / "manifest.json").write_text(json.dumps({sid: {"file": f"{nm}.tsx"} for sid, nm in accepted.items()}, ensure_ascii=False, indent=1), encoding="utf-8")
    (Path(job_dir) / "authoring_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    log(f"scene authoring: {report['summary']}")
    return spec

# Re-exported so `pipeline.scene_author.<name>` keeps working.
from .scene_author_prompts import (  # noqa: E402,F401
    _HINTS,
    _kit_text,
    build_prompts,
    design_errors,
    extract_code,
    hints_for,
    llm_write,
    parse_reply,
    state_frames,
    storyboard_errors,
)
