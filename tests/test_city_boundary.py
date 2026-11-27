"""Real city boundaries (OSM city limits): the overlay draws the polygon and frames it, with the ODbL attribution."""
from pipeline import city_boundary
from pipeline.geo_overlay import build_scene_map_overlay

HOUSTON = {"type": "MultiPolygon", "coordinates": [
    [[[-95.8, 29.6], [-95.1, 29.6], [-95.1, 30.1], [-95.8, 30.1], [-95.8, 29.6]]],
    [[[-95.3, 29.9], [-95.2, 29.9], [-95.2, 30.0], [-95.3, 29.9]]],   # an annexed piece away from the core
]}


def test_overlay_draws_the_city_limits_and_frames_them(monkeypatch):
    monkeypatch.setattr(city_boundary, "fetch", lambda name, iso2="": HOUSTON if name == "Houston" else None)
    words = [{"t": t, "s": i * 0.4, "e": i * 0.4 + 0.3} for i, t in enumerate("حدود مدينة هيوستن متعرجة".split())]
    mention = {"matched_token": "هيوستن", "kind": "city", "kind_label": "مدينة", "name_ar": "هيوستن", "name_en": "Houston",
               "country_ar": "الولايات المتحدة", "iso3": "USA", "iso2": "us", "lat": 29.76, "lon": -95.37, "coords": "",
               "is_microstate": False, "start_sec": 0.8, "end_sec": 1.1, "word_index": 2, "char_pos": 2, "scale": "city"}
    ov = build_scene_map_overlay({"id": "body1", "role": "body", "narration": "حدود مدينة هيوستن متعرجة"}, words, 150,
                                 entity_mentions=[mention])
    city = [f for f in ov["features"] if f["shape"] == "city"]
    assert city and city[0]["d"].count("M") == 2                  # both rings of the MultiPolygon are drawn
    assert ov["attribution"] == city_boundary.ATTRIBUTION
    assert ov["waypoints"][0]["zoom"] == 1.0                     # the view frames the boundary: no extra zoom that crops it


def test_no_boundary_keeps_the_old_map(monkeypatch):
    monkeypatch.setattr(city_boundary, "fetch", lambda name, iso2="": None)
    assert city_boundary.attach([{"kind": "city", "name_en": "Nowhere"}]) == {}
    assert city_boundary.extent(HOUSTON) == (-95.8, 29.6, -95.1, 30.1)
