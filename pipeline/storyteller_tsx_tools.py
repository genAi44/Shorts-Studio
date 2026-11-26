"""Split from `pipeline/storyteller.py` (re-exported there); see that module."""
from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
from .config import ROOT
from pathlib import Path
import hashlib
import json
import os
import re
import subprocess
from .storyteller import DYNAMIC_TSX_PATH, _LLM_TSX_SYSTEM, _clean_text, _sanitize_llm_tsx, _theme_sig, logger  # noqa: E402


def _run_tsc_check() -> Tuple[bool, List[str], str]:
    tsc_bin = ROOT / "remotion" / "node_modules" / ".bin" / ("tsc.cmd" if os.name == "nt" else "tsc")
    tsconfig = ROOT / "remotion" / "tsconfig.json"
    if not tsc_bin.exists() or not tsconfig.exists():
        return True, [], ""
    try:
        proc = subprocess.run(
            [str(tsc_bin), "-p", str(tsconfig), "--noEmit"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=35,
        )
        if proc.returncode == 0:
            return True, [], ""
        out = (proc.stdout or "") + "\n" + (proc.stderr or "")
        # one file per scene: report failing scene ids ("DynamicScenes" = an error in the index file)
        err_ids = set(re.findall(r"generated[\\/]scenes[\\/]([A-Za-z0-9_]+)\.tsx\(\d+,", out))
        if re.search(r"DynamicScenes\.tsx\(\d+,", out):
            err_ids.add("DynamicScenes")
        return False, sorted(err_ids), out
    except Exception as e:
        logger.warning("tsc check invocation error: %s", e)
        return True, [], ""


def _top_level_args(args: str) -> List[str]:
    parts, depth, cur, q = [], 0, [], ""
    for ch in args:
        if q:
            q = "" if ch == q else q
        elif ch in "'\"`":
            q = ch
        elif ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        elif ch == "," and depth == 0:
            parts.append("".join(cur))
            cur = []
            continue
        cur.append(ch)
    parts.append("".join(cur))
    return parts


def _fix_color_interpolate(code: str) -> str:
    """Remotion's interpolate() throws on color strings ("Non-numeric strings can only be interpolated using
    Easing.step1") and killed the whole render. LLM code does this often: switch such calls to interpolateColors."""
    out, i = [], 0
    pat = re.compile(r"\binterpolate(?:Colors)?\(")
    while True:
        m = pat.search(code, i)
        if not m:
            out.append(code[i:])
            break
        depth, j = 1, m.end()
        while j < len(code) and depth:
            depth += (code[j] == "(") - (code[j] == ")")
            j += 1
        args = code[m.end(): j - 1]
        is_color = m.group(0).startswith("interpolateColors") or re.search(r"""\[\s*['"](?:#|rgb|hsl)""", args) is not None
        out.append(code[i: m.start()])
        if is_color:
            args = ",".join(_top_level_args(args)[:3])  # interpolateColors takes no extrapolate/easing options
        out.append(("interpolateColors(" if is_color else "interpolate(") + args + ")")
        i = j
    return "".join(out)


SCENES_DIR = DYNAMIC_TSX_PATH.parent / "scenes"
_SCENE_HEADER = (
    "/* AUTO-GENERATED ORIGINAL TSX SCENE BY AI VIDEO ARCHITECT */\n"
    "import React from 'react';\n"
    "import {AbsoluteFill, interpolate, interpolateColors, spring, useCurrentFrame, useVideoConfig, Easing} from 'remotion';\n\n"
)
_SCENE_MARK = "// ---- scene ----\n"
_FC = "React.FC<{frame?: number; fps?: number; dur?: number}>"


def _write_dynamic_files(blocks: List[str], tsx_ids: List[str], geo_consts: Dict[str, str]) -> None:
    """One file per scene in generated/scenes/ (each stays small) + DynamicScenes.tsx as the registry index."""
    SCENES_DIR.mkdir(parents=True, exist_ok=True)
    for old in SCENES_DIR.glob("*.tsx"):
        if old.stem not in tsx_ids:
            old.unlink()
    for tid, blk in zip(tsx_ids, blocks):
        geo = geo_consts.get(tid, "")
        (SCENES_DIR / f"{tid}.tsx").write_text(
            _SCENE_HEADER + (geo + "\n\n" if geo else "") + _SCENE_MARK + _fix_color_interpolate(blk) + "\n",
            encoding="utf-8",
        )
    DYNAMIC_TSX_PATH.write_text(
        "/* AUTO-GENERATED INDEX OF THE TSX SCENES IN ./scenes/ */\n"
        "import React from 'react';\n"
        + "".join(f"import {{{tid}}} from './scenes/{tid}';\n" for tid in tsx_ids)
        + f"\nexport const DYNAMIC_SCENE_REGISTRY: Record<string, {_FC}> = {{\n"
        + "".join(f"  '{tid}': {tid},\n" for tid in tsx_ids)
        + "};\n",
        encoding="utf-8",
    )


def _scene_ids_in_index() -> List[str]:
    if not DYNAMIC_TSX_PATH.exists():
        return []
    return re.findall(r"^import \{(\w+)\} from './scenes/", DYNAMIC_TSX_PATH.read_text(encoding="utf-8"), re.M)


def read_scene_block(tsx_id: str) -> str:
    """Code of one generated scene (verification marker + component), '' if the file is missing."""
    f = SCENES_DIR / f"{tsx_id}.tsx"
    if not f.exists():
        return ""
    return f.read_text(encoding="utf-8").split(_SCENE_MARK, 1)[-1].rstrip("\n")


def _verified_blocks_on_disk() -> Dict[Tuple[str, str], str]:
    """LLM-verified scenes of the generated files, parsed one scene file at a time (so a verified
    block can no longer swallow the fallback scene written after it, as in the single-file layout)."""
    out: Dict[Tuple[str, str], str] = {}
    for tid in _scene_ids_in_index():
        out.update(_extract_verified_llm_blocks(read_scene_block(tid) + "\nexport const DYNAMIC_SCENE_REGISTRY"))
    return out


def snapshot_dynamic_scenes() -> Dict[str, str]:
    """Copy of the generated index + scene files, for callers that must leave them untouched."""
    files = [DYNAMIC_TSX_PATH] + (sorted(SCENES_DIR.glob("*.tsx")) if SCENES_DIR.exists() else [])
    return {str(f): f.read_text(encoding="utf-8") for f in files if f.exists()}


def restore_dynamic_scenes(snap: Dict[str, str]) -> None:
    if SCENES_DIR.exists():
        for f in SCENES_DIR.glob("*.tsx"):
            if str(f) not in snap:
                f.unlink()
    for path, text in snap.items():
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(text, encoding="utf-8")


def _assemble_dynamic_file(header: str, blocks: List[str], registry_entries: List[str]) -> str:
    blocks = [_fix_color_interpolate(b) for b in blocks]
    return (
        header
        + "\n\n".join(blocks)
        + "\n\nexport const DYNAMIC_SCENE_REGISTRY: Record<string, React.FC<{frame?: number; fps?: number; dur?: number}>> = {\n"
        + "\n".join(registry_entries)
        + "\n};\n"
    )


def _repair_beat_tsx_via_llm(
    tsx_id: str,
    broken_code: str,
    tsc_error: str,
    beat: Dict[str, Any],
    geo_ctx: Dict[str, Any],
) -> Optional[str]:
    """Asks the AI architect to fix TypeScript compiler errors in its own generated TSX before ever falling back."""
    try:
        from .llm_router import get_router

        sys_prompt = _LLM_TSX_SYSTEM
        geo_hint = f"Note: `_GEO_{tsx_id}` IS already declared above; do NOT redeclare it." if geo_ctx.get("is_geo") else ""
        user_prompt = (
            f"The TypeScript compiler rejected component `{tsx_id}` with these errors:\n"
            f"{tsc_error[:900]}\n\n"
            f"{geo_hint}\n"
            f"Spoken narration: \"{_clean_text(beat.get('narration') or '')}\"\n"
            f"Fix ALL TypeScript errors and return ONLY the corrected `export const {tsx_id}: React.FC<{{frame?: number; fps?: number; dur?: number}}> = (props) => {{ ... }};` code (preserving the custom SVG illustration, no markdown fences, no imports):\n\n"
            f"{broken_code}"
        )
        resp = get_router().dispatch(
            role="director",
            system=sys_prompt,
            user=user_prompt,
            temperature=0.3,
            json_mode=False,
            timeout=65,
        )
        return _sanitize_llm_tsx(resp.content, tsx_id)
    except Exception as e:
        logger.warning("LLM TSX repair failed for %s: %s", tsx_id, e)
        return None


def _compute_beat_tsx_sig(beat: Dict[str, Any], geo_ctx: Dict[str, Any]) -> str:
    import hashlib
    payload = json.dumps(
        {
            "sig_v": 12,
            "theme": _theme_sig(),
            "tsx_id": beat.get("tsx_id", ""),
            "narration": _clean_text(beat.get("narration") or ""),
            "title": _clean_text(beat.get("title") or beat.get("on_screen") or ""),
            "concept": _clean_text(beat.get("concept") or ""),
            "video_title": _clean_text(beat.get("video_title") or ""),
            "is_geo": bool(geo_ctx.get("is_geo")),
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]


def _extract_verified_llm_blocks(existing_text: str) -> Dict[Tuple[str, str], str]:
    pattern = re.compile(
        r"/\*\s*@llm_verified:([A-Za-z0-9_]+):([a-f0-9]+)\s*\*/\s*\n(.*?)(?=\n/\*\s*@llm_verified:|\nexport const DYNAMIC_SCENE_REGISTRY)",
        flags=re.DOTALL,
    )
    out: Dict[Tuple[str, str], str] = {}
    for m in pattern.finditer(existing_text):
        tsx_id, sig, code = m.group(1), m.group(2), m.group(3).strip()
        if code:
            out[(tsx_id, sig)] = code
    return out


def _load_tsx_cache() -> Dict[Tuple[str, str], str]:
    cache_file = DYNAMIC_TSX_PATH.parent / ".tsx_cache.json"
    out: Dict[Tuple[str, str], str] = {}
    if cache_file.exists():
        try:
            data = json.loads(cache_file.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                for k, v in data.items():
                    if ":" in k and isinstance(v, str) and v.strip():
                        tid, sig = k.split(":", 1)
                        out[(tid, sig)] = v
        except Exception:
            pass
    if DYNAMIC_TSX_PATH.exists():
        try:
            out.update(_verified_blocks_on_disk())
        except Exception:
            pass
    return out


def _save_tsx_cache(entries: Dict[Tuple[str, str], str]) -> None:
    cache_file = DYNAMIC_TSX_PATH.parent / ".tsx_cache.json"
    try:
        existing = _load_tsx_cache()
        existing.update(entries)
        serializable = {f"{tid}:{sig}": code for (tid, sig), code in list(existing.items())[-120:]}
        cache_file.write_text(json.dumps(serializable, ensure_ascii=False, indent=1), encoding="utf-8")
    except Exception:
        pass
