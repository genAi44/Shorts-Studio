"""TSX + HTML + CSS + GSAP scenes: the static gate accepts a paused, frame-seeked GSAP timeline and rejects anything that runs on
GSAP's own clock or the wall clock (play, callbacks, setTimeout) and CSS animation in <style>."""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
REM = ROOT / "remotion"
needs_node = pytest.mark.skipif(not (REM / "node_modules" / "typescript").exists() or shutil.which("node") is None,
                                reason="needs node + remotion/node_modules")


def _check(name: str) -> dict:
    src = ROOT / "tests" / "fixtures" / "gsap" / f"{name}.tsx"
    dst = REM / "src" / "authored" / f"_gate_{name}.tsx"     # the gate type-checks against ../kit from src/authored
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(src, dst)
    try:
        r = subprocess.run(["node", "scripts/check-scene.mjs", str(dst)], cwd=REM, capture_output=True, text=True, encoding="utf-8", timeout=180)
        return json.loads(r.stdout.strip().splitlines()[-1])
    finally:
        dst.unlink(missing_ok=True)


@needs_node
def test_a_frame_seeked_gsap_scene_passes():
    d = _check("good")
    assert d["ok"], d


@needs_node
def test_clock_driven_gsap_and_css_animation_are_rejected():
    v = " ".join(_check("bad")["violations"])
    for needle in ("onComplete", ".play", "setTimeout", "<style> may not use animation"):
        assert needle in v, (needle, v)
