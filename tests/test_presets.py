"""Ready-made art directions (styles/<slug>/): schema-valid, guided, wired into the API and the prompts."""
import os
import sys
from pathlib import Path

os.environ.setdefault("NO_NETWORK", "1")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pytest  # noqa: E402

from pipeline import presets, scene_author as sa  # noqa: E402
from pipeline import style as stl  # noqa: E402

SLUGS = ["atlas", "chalkboard", "dossier"]
SECTIONS = ["الجوهر، وما ليس هو", "المواد والرسم", "الإيقاع والإخراج", "تعليمات للمخرج البصري"]


def test_the_presets_are_listed():
    assert [p["slug"] for p in presets.list_presets()] == SLUGS


@pytest.mark.parametrize("slug", SLUGS)
def test_preset_values_survive_normalize(slug):
    import json
    raw = json.loads((ROOT / "styles" / slug / "style.json").read_text(encoding="utf-8"))["style"]
    st = presets.load_style(slug)
    assert st["preset"] == slug
    for sec in ("bg", "headline", "caption", "map", "stat", "text", "deco", "edit"):
        for k, v in raw[sec].items():
            assert st[sec][k] == v, (slug, sec, k)           # nothing was silently replaced by a random value
    assert st["font"] == raw["font"] and st["pace"] == raw["pace"]


@pytest.mark.parametrize("slug", SLUGS)
def test_guide_has_the_sections_and_no_cards_rule(slug):
    g = presets.guide(slug)
    for s in SECTIONS:
        assert s in g, (slug, s)
    assert len(g) > 1200


def test_unknown_or_unsafe_slugs_are_rejected():
    for bad in ("nope", "../pipeline", "", None, "atlas/../x"):
        assert not presets.has_preset(bad)
    assert presets.guide("nope") == ""


def test_normalize_keeps_only_a_real_preset():
    assert stl.normalize({"preset": "atlas"})["preset"] == "atlas"
    assert "preset" not in stl.normalize({"preset": "ghost"})
    assert "preset" not in stl.normalize({})


def test_the_guide_reaches_the_scene_author_system_prompt_not_the_data():
    st = presets.load_style("chalkboard")
    th = stl.theme_from_style(st)
    assert "art_guide" in th
    ctx = {"id": "a", "role": "body", "dur": 90, "sentence": "x", "sentences": ["x"], "entities": [], "words": [], "map_overlay": None, "theme": th}
    system, user = sa.build_prompts(ctx)
    assert "ART DIRECTION OF THIS VIDEO" in system and "سبورة" in system
    assert "art_guide" not in user
    # a different preset changes the cache key of the authored scene
    other = dict(ctx, theme=stl.theme_from_style(presets.load_style("atlas")))
    assert sa.content_hash(sa.scene_context({"id": "a", "words": [], "dur": 90}, th)) != sa.content_hash(sa.scene_context({"id": "a", "words": [], "dur": 90}, other["theme"]))


def test_api_lists_and_applies_a_preset():
    import app as appmod
    c = appmod.app.test_client()
    names = [p["slug"] for p in c.get("/api/presets").get_json()["presets"]]
    assert names == SLUGS
    r = c.post("/api/style", json={"preset": "dossier"}).get_json()
    assert r["by"] == "preset" and r["style"]["preset"] == "dossier" and r["style"]["bg"]["type"] == "grid"
    assert c.post("/api/style", json={"preset": "ghost"}).status_code == 404
