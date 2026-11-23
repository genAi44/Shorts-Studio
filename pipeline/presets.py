"""Ready-made art directions ("style presets") in styles/<slug>/: a style.json that fits the style schema (style.normalize) and a
STYLE.md guide (essence / what it is not / materials / rhythm / director rules) that is handed to the visual director and to the
scene author, so the look is a way of working and not only a set of colours.

The structure of the guides is inspired by Lemo-Opuscar (github.com/lemomo-ai/lemo-opuscar, docs CC BY-NC 4.0); the text and the
values here are our own."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import ROOT

STYLES_DIR = ROOT / "styles"


def _dirs() -> List[Path]:
    if not STYLES_DIR.is_dir():
        return []
    return sorted(p for p in STYLES_DIR.iterdir() if (p / "style.json").is_file())


def list_presets() -> List[Dict[str, Any]]:
    out = []
    for d in _dirs():
        try:
            meta = json.loads((d / "style.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        out.append({"slug": d.name, "name": meta.get("name", d.name), "en": meta.get("en", ""), "line": meta.get("line", ""), "uses": meta.get("uses", [])})
    return out


def has_preset(slug: Optional[str]) -> bool:
    return bool(slug) and (STYLES_DIR / str(slug) / "style.json").is_file() and "/" not in str(slug) and ".." not in str(slug)


def load_style(slug: str) -> Dict[str, Any]:
    """The normalized style dict of a preset, tagged with its slug (KeyError when it does not exist)."""
    from .style import normalize
    if not has_preset(slug):
        raise KeyError(slug)
    meta = json.loads((STYLES_DIR / slug / "style.json").read_text(encoding="utf-8"))
    st = normalize(meta["style"])
    st["preset"] = slug
    return st


def guide(slug: Optional[str]) -> str:
    """The STYLE.md text of a preset ('' when there is none)."""
    if not has_preset(slug):
        return ""
    p = STYLES_DIR / str(slug) / "STYLE.md"
    return p.read_text(encoding="utf-8") if p.is_file() else ""
