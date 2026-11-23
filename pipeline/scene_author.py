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
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple

from .config import FPS, ROOT, record_fallback

REMOTION = ROOT / "remotion"
AUTHORED_SRC = REMOTION / "src" / "authored"
KIT_DOC = ROOT / "docs" / "SCENE_KIT.md"
CACHE_DIR = ROOT / "data" / "authored_cache"
KIT_VERSION = 1
MAX_RETRIES = 2
TEST_FRAME_FRACTIONS = (0.15, 0.5, 0.9)
FLAT_STD = 6.0

SYSTEM = """You are the art director AND the motion-graphics engineer of an Arabic educational Shorts studio (1080x1920).
You design ONE scene as real code: a single TSX file that default-exports a React component. Follow the kit documentation
below exactly. Output ONLY the TSX source (no markdown fences, no commentary).

Design brief: the scene must express THIS sentence and its entities visually, with art direction: one hero element, clear
Arabic typographic hierarchy, layered (semi-transparent) decoration, staggered entrances, something always gently moving.
Never a plain card or a bare emoji. Use the entities' real data (numbers, years, names); do not invent facts.
If data.map_overlay exists, the places must be shown on the map with <MapLayer overlay={data.map_overlay} /> (you may add
supporting elements, but do not cover the map or the caption zone). Keep the video's ground visible (no opaque full-canvas fill).

{kit}
"""


# ------------------------------------------------------------------ prompts

def _kit_text() -> str:
    return KIT_DOC.read_text(encoding="utf-8") if KIT_DOC.exists() else ""


_HINTS = (
    ("edge", "touches/overflows the canvas edge", "Give every text container an explicit width (<= 920) and centre it: left = LAYOUT.cx - width/2. Pass maxWidth to ArText. Never use right:/negative offsets."),
    ("overlap", "overlapping text", "Stack elements vertically with explicit y values at least 1.4 x the font size apart, computed from one list, and keep cards from covering each other's text. If the two overlapping texts share the same box, the same words are drawn twice (an outline/shadow copy, a duplicated list item, or two layers at the same x/y): draw every string exactly once and use textShadow or colour for emphasis. A keyword longer than ~12 characters at size >= 100 wraps and collides: use size <= 90 or put it in a separate Abs with its own y."),
    ("zone", "safe zones", "Every text must lie between LAYOUT.beat.top and LAYOUT.beat.bottom - 40 (and out of the map card when you use MapLayer)."),
    ("rtl", "right-to-left", "Render every Arabic string with <ArText> (it sets dir=rtl); never put Arabic directly in a div/span/svg text."),
    ("tiny", "too small", "Raise font sizes: body text >= 30 px, labels >= 26 px."),
    ("blank", "blank", "Draw visible content: at least a hero element and one ArText from frame 20 on."),
    ("css", "TS2353", "A style object has a property that is not real CSS (e.g. 'justify'): use exact camelCase CSS names - justifyContent, alignItems, flexDirection, textAlign, gap. Check every key you wrote in style={{...}}."),
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
    slim["has_map_overlay"] = bool(ctx.get("map_overlay"))
    if ctx.get("map_overlay"):
        ov = ctx["map_overlay"]
        slim["map_places"] = [w.get("name_ar") for w in ov.get("waypoints", [])] + [f.get("label") for f in ov.get("features", [])]
    user = ("Scene data (this is exactly `data` in your component, except map_overlay which is injected):\n"
            + json.dumps(slim, ensure_ascii=False)
            + f"\n\nScene length: {ctx['dur']} frames at {FPS} fps. Write the scene.")
    if errors and previous:
        hints = hints_for(errors)
        user += ("\n\nYour previous attempt was REJECTED. Fix every problem and return the complete corrected file.\n"
                 "Problems:\n- " + "\n- ".join(errors[:14])
                 + ("\n\nHow to fix:\n- " + "\n- ".join(hints) if hints else "") + "\n\nPrevious code:\n" + previous)
    return SYSTEM.replace("{kit}", _kit_text()), user


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


def llm_write(system: str, user: str) -> Optional[str]:
    from .llm_router import get_router
    try:
        resp = get_router().dispatch(role="director", system=system, user=user, temperature=0.7, json_mode=False, timeout=150)
        return extract_code(resp.content)
    except Exception as e:  # noqa: BLE001 - the caller records the failure
        import logging
        logging.getLogger("pipeline.scene_author").warning("scene authoring llm call failed: %s", e)
        return None


# ------------------------------------------------------------------ context, ids, cache

def scene_context(scene: Dict[str, Any], theme: Dict[str, Any]) -> Dict[str, Any]:
    from .direct import sentences
    words = scene.get("words") or []
    narration = " ".join(str(w.get("t", "")) for w in words)
    ents = [e for per in scene.get("entity_plan") or [] for e in per]
    keep = ("type", "scale", "text", "name_ar", "name_en", "value", "unit", "label_ar", "compare", "born", "died", "role_ar", "to", "from", "year", "lat", "lon", "stops", "a", "b")
    return {
        "id": scene.get("id"), "role": scene.get("role"), "dur": int(scene.get("dur", 150)),
        "sentence": narration, "sentences": sentences(narration),
        "entities": [{k: e[k] for k in keep if k in e} for e in ents],
        "words": [{"t": w["t"], "s": round(float(w.get("s", 0)), 2), "e": round(float(w.get("e", 0)), 2)} for w in words][:60],
        "map_overlay": scene.get("map_overlay"), "theme": theme,
    }


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
                          "entities": ctx["entities"], "theme": ctx["theme"], "dur": ctx["dur"], "role": ctx["role"],
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

def author_spec(spec: Dict[str, Any], job_dir: str, llm: Optional[Callable[[str, str], Optional[str]]] = None, cache_only: bool = False,
                log: Callable[[str], None] = print, only_ids: Optional[set] = None) -> Dict[str, Any]:
    """Replace the built-in beats of every scene by an authored scene when one passes all gates. Mutates and returns the
    spec; writes outputs/<job>/scenes/*.tsx, scenes/manifest.json and authoring_report.json."""
    from .style import theme_from_style
    llm = llm or llm_write
    theme = theme_from_style(spec["style"])
    job_dir = str(Path(job_dir).resolve())  # node runs with another cwd: always absolute paths
    scenes_dir = Path(job_dir) / "scenes"
    scenes_dir.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    ctxs = {s["id"]: scene_context(s, theme) for s in spec["scenes"] if only_ids is None or s["id"] in only_ids}
    names = {sid: scene_name(content_hash(c)) for sid, c in ctxs.items()}
    report: Dict[str, Any] = {"scenes": {}, "started": time.strftime("%Y-%m-%d %H:%M:%S")}
    accepted: Dict[str, str] = {}
    pending: Dict[str, Dict[str, Any]] = {}

    for sid, ctx in ctxs.items():  # cache first
        name = names[sid]
        hit = CACHE_DIR / f"{name}.tsx"
        rep = report["scenes"].setdefault(sid, {"name": name, "attempts": 0, "errors": [], "status": "pending"})
        if hit.exists():
            shutil.copyfile(hit, scenes_dir / f"{name}.tsx")
            accepted[sid] = name
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
        for sid, code in written:
            rep = report["scenes"][sid]
            rep["attempts"] += 1
            if not code:
                rep["errors"].append(f"attempt {attempt + 1}: the model returned nothing")
                pending[sid]["errors"], pending[sid]["code"] = ["the model returned no code"], pending[sid]["code"] or ""
                continue
            path = scenes_dir / f"{names[sid]}.tsx"
            path.write_text(code, encoding="utf-8")
            pending[sid]["code"] = code
            errs = static_check(path)
            if errs:
                path.unlink(missing_ok=True)
                rep["errors"].append(f"attempt {attempt + 1} static: {errs[:4]}")
                pending[sid]["errors"] = errs
                continue
            ready[sid] = {"ctx": pending[sid]["ctx"]}
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
        s["authored"] = {"scene_id": name, "attempts": report["scenes"][s["id"]]["attempts"], "status": report["scenes"][s["id"]]["status"]}
        s["authored_replaced"] = [b.get("kind") for b in s.get("beats", [])]
        s["beats"] = [{"kind": "authored", "scene_id": name, "from": 0, "dur": s["dur"], "data": {k: v for k, v in ctx.items() if k != "id"},
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
