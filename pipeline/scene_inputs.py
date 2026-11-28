"""What the designer receives from upstream: the director's binding decision, and whether a scene keeps a native visual."""
import shutil
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


def director_decision(scene: Dict[str, Any]) -> List[Dict[str, Any]]:
    """The beat director's decision for this scene (step 3 of the app), handed to the designer as binding input."""
    out = []
    for b in scene.get("beats") or []:
        if isinstance(b, dict) and (b.get("concept") or b.get("title") or b.get("photo_subject")):
            out.append({k: b[k] for k in ("kind", "title", "concept", "camera", "photo_subject") if b.get(k)})
    return out


NATIVE_KINDS = ("map", "map_pin", "area_map")


def has_native_visual(scene: Dict[str, Any]) -> bool:
    """A scene whose director beats show a real map or a found licensed photo: those render with the native
    components, an authored TSX scene would replace them with a drawing (seen: 0 photos on screen from 9 found)."""
    beats = [b for b in scene.get("beats") or [] if isinstance(b, dict)]
    # ALL beats native: a scene mixing a photo with drawn beats is authored (its drawn beats would otherwise render with the
    # old built-in component, in a palette that clashes with the authored scenes - seen in a real run)
    return bool(beats) and all(b.get("kind") in NATIVE_KINDS or (b.get("kind") == "photo" and b.get("img")) for b in beats)


def attach_photos(ctxs: Dict[str, Dict[str, Any]], photo: Optional[Callable[[str, str], Optional[Dict[str, Any]]]],
                  job_dir: str, log: Callable[[str], None] = print) -> List[Path]:
    """For every scene to author whose director decision names a photo_subject: fetch a licensed photo (background removed
    when possible) and hand it to the designer as data.photo = {src, cut, subject}. The file is also copied into
    remotion/public so the sandbox render (the 3-frame gate) sees it. Returns the copied files (removed after authoring)."""
    from .scene_author import REMOTION
    copied: List[Path] = []
    if photo is None:
        return copied
    for sid, ctx in ctxs.items():
        subj = next((d.get("photo_subject") for d in ctx.get("director_decision") or [] if d.get("photo_subject")), "")
        if not subj:
            continue
        try:
            res = photo(str(subj), ctx.get("sentence", "")) or {}
        except Exception as e:  # noqa: BLE001 - the scene is still authored, without a photo
            log(f"scene authoring: photo for '{sid}' unavailable ({e})")
            continue
        src = str(res.get("img") or "")
        if not src:
            continue
        ctx["photo"] = {"src": src, "cut": bool(res.get("cut")), "subject": str(subj)}
        dst = REMOTION / "public" / src
        if not dst.exists():
            try:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(Path(job_dir) / "public" / src, dst)
                copied.append(dst)
            except OSError:
                pass
        log(f"scene authoring: '{sid}' hero photo '{subj}' ({'cut-out' if ctx['photo']['cut'] else 'framed'})")
    return copied


PHOTO_RULES = """

PHOTO HERO (when data.photo exists): the scene is built around a REAL photo of data.photo.subject (licensed, usually cut out).
  Show it with <HeroPhoto> big (w 600..900) as the hero - like a magazine cut-out: one real object/person/place, huge, with depth.
  Your hero SVG then becomes the supporting layer AROUND the photo (arrows pointing at parts of it, an outline or a path drawn across
  it, a highlight ring, a small diagram beside it), and the 2-4 word key line sits above or beside it. Never cover the photo's centre.
"""


GSAP_RULES = """

TSX + HTML + CSS + GSAP (MANDATORY - the gate rejects a scene without useGsapTimeline): the scene file is TSX. Use the kit components for what they do best
(HeroPhoto, MapLayer, ArText for EVERY Arabic string, Counter, HeroSvg, Icon) and build everything else as your own HTML / SVG elements
with CSS, animated by ONE GSAP timeline:
  import {useGsapTimeline, ...} from '../kit';
  const scope = useGsapTimeline<HTMLDivElement>(({timeline: tl, selector: q}) => {
    tl.from(q('.card'), {y: 90, opacity: 0, duration: 0.6, ease: 'back.out(1.6)'}, 0.2);          // position = seconds from scene start
    tl.fromTo(q('.route'), {strokeDashoffset: 1}, {strokeDashoffset: 0, duration: 2.4, ease: 'power2.inOut'}, 0.8);
    tl.to(q('.ship'), {x: 420, rotation: 4, duration: 3, ease: 'sine.inOut'}, 1.2);
  });
  return <AbsoluteFill><style>{`.card{position:absolute;left:140px;top:420px;width:800px;...}`}</style><div ref={scope} ...>...</div></AbsoluteFill>;
  - Every GSAP position is in SECONDS, synced to the word timings (data.words: an element starts 0.1 s before its word).
  - Use the timeline for rich motion: paths drawing (pathLength={1} + strokeDasharray={1} + strokeDashoffset), objects travelling along
    the frame with overshoot, staggered groups (stagger: 0.08), scale-throughs, counters, a slow drift of the whole group.
  - FORBIDDEN (the gate rejects them): tl.play / resume / restart / reverse, gsap.ticker, delayedCall, callbacks (onUpdate, onComplete,
    onStart, .call), registerPlugin, setTimeout / setInterval / requestAnimationFrame, Date, Math.random, CSS animation / transition /
    @keyframes / url() in <style> or style objects. Only core GSAP (no plugins).
  - Arabic text stays in ArText (never split into letters); GSAP may move/fade the element that wraps an ArText.
"""


def scene_requirements(code: str, ctx: Dict[str, Any]) -> List[str]:
    """What every authored scene must contain: its own elements animated by ONE GSAP timeline (useGsapTimeline), and the real
    photo when the pipeline found one (HeroPhoto)."""
    if "useGsapTimeline" not in code:
        return ["the scene's own elements must be animated with ONE GSAP timeline: const scope = useGsapTimeline<HTMLDivElement>"
                "(({timeline: tl, selector: q}) => { tl.from(q('.x'), {...}, 0.4); ... }) on the root div (import it from '../kit'); "
                "positions in seconds synced to the word timings - rich motion: paths drawing, objects travelling, staggered groups"]
    if ctx.get("photo") and "HeroPhoto" not in code:
        return [f"data.photo is ready (a real photo of '{ctx['photo']['subject']}'): the scene must show it with <HeroPhoto data={{data}} "
                "x=.. y=.. w=.. h=.. /> (import it from '../kit'), big (w >= 600), and build the explanation around it"]
    return []
