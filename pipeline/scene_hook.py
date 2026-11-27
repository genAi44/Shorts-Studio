"""The hook gate: the first scene is the thumbnail and the first 2 s (checked on the real render by scene_author)."""
from typing import Any, Dict, List

HOOK_MAX_TEXTS = 3      # the hook: one 2-4 word title + a short label and/or one number
HOOK_MAX_WORDS = 6


def hook_problems(aud: Dict[str, Any], idx: int, flat: bool) -> List[str]:
    """The hook is the thumbnail and the first 2 s: composed from its first frame, one hero, a punch title, nothing else."""
    out: List[str] = []
    hero = aud.get("hero") or {}
    if idx == 0:
        if flat or aud.get("texts", 0) == 0:
            out.append("the hook's first frame is empty: frame 0 must already be the full composition (the title and the hero visible "
                       "from the very first frame - no fade-in from nothing)")
        if not hero.get("box") or hero.get("opacity", 1) < 0.3:
            out.append("the hook's hero is not visible in its first frame: show it from frame 0 (a settle/scale-in of at most 6 frames)")
    if aud.get("texts", 0) > HOOK_MAX_TEXTS:
        out.append(f"the hook shows {aud.get('texts')} texts: keep one 2-4 word title plus at most a short label and one number")
    for txt in aud.get("strings") or []:
        if len(str(txt).split()) > HOOK_MAX_WORDS:
            out.append(f"hook text too long ('{txt}'): the hook title is 2-4 words, no sentences")
            break
    return out
