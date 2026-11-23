"""Picture verification: Gemini -> FreeLLMAPI fallback chain, and the PHOTO_VERIFY switch (off = the gate is disabled)."""
import os
import sys
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("NO_NETWORK", "1")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PIL import Image  # noqa: E402

from pipeline import llm, media  # noqa: E402

CANDS = [
    {"url": "http://ex/1.jpg", "title": "Brasilia Cathedral", "desc": "cathedral Brasilia Brazil", "src": "Pexels"},
    {"url": "http://ex/2.jpg", "title": "Brasilia skyline", "desc": "Brasilia Brazil", "src": "Wikipedia"},
]
IM = Image.new("RGB", (800, 600), (100, 120, 140))


def _pick(**env):
    with patch.dict(os.environ, {"GEMINI_API_KEY": "k", "FREELLMAPI_API_KEY": "k", **env}), patch.object(media, "fetch_image", return_value=IM):
        return media.pick([dict(c) for c in CANDS], "Brasilia landmark", "برازيليا", lambda *_: None, must_show="Brasilia")


def test_gemini_429_falls_back_to_freellmapi_vision():
    with patch("pipeline.llm.gemini_vision_json", side_effect=RuntimeError("429 Quota")), \
         patch("pipeline.llm.freellmapi_vision_json", return_value={"pick": 0, "score": 9, "reason": "cathedral of Brasilia"}) as free:
        picked, score, reason = _pick()
    assert free.called and picked is not None and score == 9 and "cathedral" in reason


def test_gemini_only_mode_never_calls_freellmapi():
    with patch("pipeline.llm.gemini_vision_json", side_effect=RuntimeError("429")), \
         patch("pipeline.llm.freellmapi_vision_json", return_value={"pick": 0, "score": 9, "reason": "x"}) as free:
        _pick(PHOTO_VERIFY="gemini")
    assert not free.called


def test_off_disables_the_gate_and_accepts_the_best_heuristic_candidate():
    with patch("pipeline.llm.gemini_vision_json") as g, patch("pipeline.llm.freellmapi_vision_json") as f:
        picked, score, _ = _pick(PHOTO_VERIFY="off")
    assert not g.called and not f.called and picked is not None and score > 0


def test_vision_providers_follow_the_switch():
    with patch.dict(os.environ, {"GEMINI_API_KEY": "k", "FREELLMAPI_API_KEY": "k"}):
        with patch.dict(os.environ, {"PHOTO_VERIFY": "auto"}):
            assert llm.vision_providers() == ["gemini", "freellmapi"]
        with patch.dict(os.environ, {"PHOTO_VERIFY": "freellmapi"}):
            assert llm.vision_providers() == ["freellmapi"]
        with patch.dict(os.environ, {"PHOTO_VERIFY": "off"}):
            assert llm.vision_providers() == []
