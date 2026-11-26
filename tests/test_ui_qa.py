"""Found by the Playwright QA run: concurrent previews overwrote one shared file; the visual-library returned unresolved flags
(a broken <img src="/assets/">); the page has unnamed fields."""
import json
import os
import sys
import threading
import time
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("NO_NETWORK", "1")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import app as appmod  # noqa: E402
from pipeline import rem  # noqa: E402


def _script():
    return {"hook": {"narration": "القاهرة هي عاصمة مصر", "on_screen": "x", "visual": {"type": "text", "text": "x"}}}


def test_concurrent_previews_get_their_own_frame_and_clean_up(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTHORED_SCENES", "0")  # a local .env with AUTHORED_SCENES=1 would send the fake spec into the authoring path
    seen_dirs, results = [], {}

    def fake_render_still(spec, out, fr, work):
        seen_dirs.append(work)
        time.sleep(0.3)                                  # long enough for the two requests to overlap
        Path(out).write_bytes(b"\xff\xd8JPEG-of-" + Path(work).name.encode())

    fake_spec = {"scenes": [{"id": "hook", "from": 0, "dur": 90, "beats": [{"from": 0}]}]}
    with patch.object(appmod, "OUT", tmp_path), patch.object(rem, "available", return_value=True), \
         patch.object(rem, "build_spec", return_value=fake_spec), patch.object(rem, "render_still", side_effect=fake_render_still), \
         patch.object(appmod, "pick_engine", return_value="remotion"):
        c = appmod.app.test_client()

        def go(k):
            r = c.post("/api/preview", json={"script": _script(), "style": {}, "scene": 0, "beat": 0})
            results[k] = (r.status_code, r.data)

        ts = [threading.Thread(target=go, args=(k,)) for k in (1, 2)]
        [t.start() for t in ts]
        [t.join(20) for t in ts]
    assert results[1][0] == results[2][0] == 200
    assert len(set(seen_dirs)) == 2                       # each request rendered in its own folder
    assert results[1][1] != results[2][1]                 # and got its own frame back
    assert not any(p.is_dir() for p in (tmp_path / "_prev").glob("*"))   # temp folders removed


def test_visual_library_never_returns_unresolved_flags():
    c = appmod.app.test_client()
    for q in ("map", "xyz-no-such-thing", ""):
        r = c.post("/api/visual-library", json={"query": q}).get_json()
        assert all(f.get("found") and f.get("file") for f in r["flags"]), q


def test_every_form_field_gets_an_accessible_name_script():
    html = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
    assert "function nameFields" in html and "aria-label" in html      # the page names unlabeled fields at load and on change
    assert "input[type=checkbox] { width: 20px" in html and "@media (pointer: coarse)" in html
