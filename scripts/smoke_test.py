"""
Visual Smoke Test — Renders tests/fixtures/test_spec.json at frames [1, 15, 45, 90, 150, 210]
with `npx remotion still` and verifies:
  1. No pixel column is >95% the same color (catches flat-color flash)
  2. Text is not touching the frame edges (samples top/bottom 10px rows for white/black pixels)
Prints PASS or FAIL with the frame number.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
REMOTION_DIR = ROOT / "remotion"
SPEC_PATH = ROOT / "tests" / "fixtures" / "test_spec.json"
FRAMES = [1, 15, 45, 90, 150, 210]


def check_frame_image(img_path: Path, frame_num: int) -> tuple[bool, str]:
    img = Image.open(img_path).convert("RGB")
    width, height = img.size
    pixels = img.load()

    # 1. Check that no pixel column is >95% the same color (catches flat-color flash)
    threshold_col = int(height * 0.95)
    for x in range(width):
        col_counts: Counter[tuple[int, int, int]] = Counter()
        for y in range(height):
            col_counts[pixels[x, y]] += 1
        most_common_color, count = col_counts.most_common(1)[0]
        if count > threshold_col:
            pct = (count / height) * 100.0
            return (
                False,
                f"column x={x} is {pct:.1f}% identical color {most_common_color} (>95% limit)",
            )

    # 2. Sample top/bottom 10px rows for white/black pixels (text touching frame edges)
    edge_ys = list(range(0, 10)) + list(range(height - 10, height))
    white_black_count = 0
    total_edge_pixels = len(edge_ys) * width
    for y in edge_ys:
        for x in range(width):
            r, g, b = pixels[x, y]
            is_white = r >= 250 and g >= 250 and b >= 250
            is_black = r <= 5 and g <= 5 and b <= 5
            if is_white or is_black:
                white_black_count += 1

    # Allow 0 white/black text pixels touching the top/bottom 10px edge strip
    if white_black_count > 0:
        return (
            False,
            f"detected {white_black_count}/{total_edge_pixels} pure white/black pixels in top/bottom 10px rows",
        )

    return True, "ok"


def main() -> int:
    if not SPEC_PATH.exists():
        print(f"FAIL: missing test fixture {SPEC_PATH}")
        return 1

    npx_cmd = "npx.cmd" if os.name == "nt" else "npx"
    if not shutil.which(npx_cmd):
        print(f"FAIL: {npx_cmd} not found in PATH")
        return 1

    out_dir = Path(tempfile.mkdtemp(prefix="shorts_smoke_"))
    all_passed = True

    try:
        for frame in FRAMES:
            out_png = out_dir / f"frame_{frame}.png"
            cmd = [
                npx_cmd,
                "remotion",
                "still",
                "src/index.ts",
                "Short",
                str(out_png),
                f"--props={SPEC_PATH}",
                f"--frame={frame}",
                "--quiet",
            ]
            proc = subprocess.run(
                cmd,
                cwd=str(REMOTION_DIR),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            if proc.returncode != 0 or not out_png.exists():
                err = (proc.stderr or proc.stdout or "").strip()
                print(f"FAIL frame {frame}: remotion still failed ({err})")
                all_passed = False
                continue

            ok, detail = check_frame_image(out_png, frame)
            if ok:
                print(f"PASS frame {frame}")
            else:
                print(f"FAIL frame {frame}: {detail}")
                all_passed = False
    finally:
        shutil.rmtree(out_dir, ignore_errors=True)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

