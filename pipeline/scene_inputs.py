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
