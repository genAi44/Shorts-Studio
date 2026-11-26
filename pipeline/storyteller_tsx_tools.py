"""Split from `pipeline/storyteller.py` (re-exported there); see that module."""
from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
from .config import ROOT
import hashlib
import json
import os
import re
import subprocess
from .storyteller import DYNAMIC_TSX_PATH, _LLM_TSX_SYSTEM, _clean_text, _sanitize_llm_tsx, _theme_sig, logger  # noqa: E402


def _run_tsc_check() -> Tuple[bool, List[int], str]:
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
        err_lines: List[int] = []
        for m in re.finditer(r"DynamicScenes\.tsx\((\d+),", out):
            err_lines.append(int(m.group(1)))
        return False, sorted(set(err_lines)), out
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
            out.update(_extract_verified_llm_blocks(DYNAMIC_TSX_PATH.read_text(encoding="utf-8")))
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
