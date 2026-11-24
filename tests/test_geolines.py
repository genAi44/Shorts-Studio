"""Offline reference lines (ranges / boundaries) drawn on the map, and a country cut along a dividing line."""
import os
import sys
from pathlib import Path

os.environ.setdefault("NO_NETWORK", "1")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pytest  # noqa: E402

from pipeline import entities, geo_overlay as go, geolines, tts  # noqa: E402
from pipeline.geo import get_geo  # noqa: E402


def test_names_resolve_in_arabic_and_english():
    for name in ("جبال الأورال", "الاورال", "الأورال", "جبال الاورال"):
        assert geolines.find(name)["id"] == "urals", name
    assert geolines.find("", "Ural Mountains")["id"] == "urals"
    assert geolines.find("الحد بين أوروبا وآسيا")["id"] == "europe_asia_border"
    assert geolines.find("خط الاستواء")["kind"] == "reference"
    assert geolines.find("نهر النيل") is None and geolines.find("") is None


@pytest.mark.parametrize("line", geolines._lines(), ids=lambda l: l["id"])
def test_every_line_is_well_formed(line):
    assert line["name_ar"] and line["name_en"] and len(line["points"]) >= 2
    for lon, lat in line["points"]:
        assert -180 <= lon <= 180 and -90 <= lat <= 90
    if geolines.divides(line):
        assert line["divides"]["west_label"] and line["divides"]["east_label"]


def test_a_ring_is_cut_along_the_line():
    ring = [[50, 50], [70, 50], [70, 60], [50, 60]]
    west, east = geolines.split_polygon(ring, [[60, 70], [60, 40]])
    assert max(p[0] for p in west) <= 60.0001 and min(p[0] for p in east) >= 59.9999
    # a slanted line: the cut follows it
    west2, _ = geolines.split_polygon(ring, [[55, 40], [65, 70]])
    assert any(abs(p[0] - geolines.lon_at([[55, 40], [65, 70]], p[1])) < 1e-6 for p in west2 if p[1] in (50, 60) or True)
    # nothing on one side: that side is empty
    w3, e3 = geolines.split_polygon(ring, [[90, 70], [90, 40]])
    assert w3 and not e3


def test_the_urals_are_drawn_and_cut_russia_in_two():
    sent = "تقسمها جبال الأورال إلى قارتين"
    ent = entities.validate_entity({"type": "terrain", "scale": "mountain", "text": "جبال الأورال", "name_ar": "جبال الأورال", "name_en": "Ural Mountains"}, sent)
    assert ent and ent["verified"] == "local-lines" and ent["line_id"] == "urals" and ent["divides"]["countries"] == ["RUS"]
    t = tts.estimate_timing(sent)
    words = [{"t": a, "s": b, "e": c} for a, b, c in t["words"]]
    ov = go.build_scene_map_overlay({"role": "body", "narration": sent}, words, 150, get_geo(), 0, None, None, go.mention_from_entity(ent, words))
    rng = [f for f in ov["features"] if f["shape"] == "range"]
    assert rng and rng[0]["d"].startswith("M") and len(rng[0]["pts"]) >= 5       # the ridge is a path with glyph positions
    sp = ov["split"]
    assert sp and sp["iso3"] == "RUS" and sp["west_label"] == "أوروبا" and sp["east_label"] == "آسيا"
    assert sp["west_d"] and sp["east_d"] and sp["line_d"].startswith("M")
    assert sp["west_xy"][0] < sp["east_xy"][0]                                    # Europe is on the left, Asia on the right
    assert "RUS" in [c["iso3"] for c in ov["countries"]]


def test_a_range_that_divides_nothing_does_not_split():
    ent = entities.validate_entity({"type": "terrain", "scale": "mountain", "text": "جبال الهيمالايا", "name_ar": "جبال الهيمالايا", "name_en": "Himalayas"}, "تمتد جبال الهيمالايا شمال الهند")
    assert ent and ent["line_id"] == "himalaya" and "divides" not in ent
    t = tts.estimate_timing("تمتد جبال الهيمالايا شمال الهند")
    words = [{"t": a, "s": b, "e": c} for a, b, c in t["words"]]
    ov = go.build_scene_map_overlay({"role": "body", "narration": "x"}, words, 150, get_geo(), 0, None, None, go.mention_from_entity(ent, words))
    assert ov["split"] is None and any(f["shape"] == "range" for f in ov["features"])
