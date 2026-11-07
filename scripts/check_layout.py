"""CI Layout Contract Check (`scripts/check_layout.py`).

1. Verifies `pipeline/layout.py` and `remotion/src/layout.ts` have identical
   SAFE_TOP, SAFE_BOTTOM, HEADLINE_ZONE, BEAT_ZONE, CAPTION_ZONE constants.
2. Greps `Short.tsx`, `beats.tsx`, and `visualLayer.tsx` for hardcoded numeric
   `top:` or `bottom:` pixel values and fails with non-zero exit code if found.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pipeline import layout as py_layout  # noqa: E402

TARGET_TSX_FILES = [
    ROOT / "remotion" / "src" / "Short.tsx",
    ROOT / "remotion" / "src" / "beats.tsx",
    ROOT / "remotion" / "src" / "visualLayer.tsx",
]

HARDCODED_TOP_BOTTOM_RE = re.compile(r"\b(top|bottom)\s*:\s*-?\d+(?:\.\d+)?\b")


def check_layout_sync() -> list[str]:
    errors: list[str] = []
    ts_path = ROOT / "remotion" / "src" / "layout.ts"
    if not ts_path.exists():
        return ["Missing remotion/src/layout.ts"]
    ts_text = ts_path.read_text(encoding="utf-8")

    for const_name in ("SAFE_TOP", "SAFE_BOTTOM"):
        py_val = getattr(py_layout, const_name, None)
        m = re.search(rf"export\s+const\s+{const_name}\s*=\s*(\d+)", ts_text)
        if not m or int(m.group(1)) != py_val:
            errors.append(f"Mismatch for {const_name}: py={py_val}, ts={m.group(1) if m else None}")

    for zone_name in ("HEADLINE_ZONE", "BEAT_ZONE", "CAPTION_ZONE"):
        py_zone = getattr(py_layout, zone_name, {})
        m = re.search(rf"export\s+const\s+{zone_name}\s*=\s*\{{([^}}]+)\}}", ts_text, re.S)
        if not m:
            errors.append(f"Missing {zone_name} in remotion/src/layout.ts")
            continue
        body = m.group(1)
        ts_zone = {k: int(v) for k, v in re.findall(r"(\w+)\s*:\s*(-?\d+)", body)}
        if ts_zone != py_zone:
            errors.append(f"Zone mismatch for {zone_name}: py={py_zone} vs ts={ts_zone}")

    return errors


def check_hardcoded_px() -> list[str]:
    violations: list[str] = []
    for fpath in TARGET_TSX_FILES:
        if not fpath.exists():
            violations.append(f"Missing target file: {fpath}")
            continue
        content = fpath.read_text(encoding="utf-8")
        if "from './layout'" not in content and 'from "./layout"' not in content:
            violations.append(f"{fpath.name}: missing import from './layout'")
        for lineno, line in enumerate(content.splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*"):
                continue
            for match in HARDCODED_TOP_BOTTOM_RE.finditer(line):
                violations.append(f"{fpath.name}:{lineno}: hardcoded {match.group(0)} in `{stripped}`")
    return violations


def run_check() -> bool:
    errors = check_layout_sync() + check_hardcoded_px()
    if errors:
        for e in errors:
            print(f"FAIL [layout]: {e}", file=sys.stderr)
        return False
    print("PASS [layout]: Central layout contract verified; 0 hardcoded top/bottom values found.")
    return True


if __name__ == "__main__":
    sys.exit(0 if run_check() else 1)
