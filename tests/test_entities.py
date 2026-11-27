"""Entity -> visual rule: every registered entity named in a sentence must get its visual in that scene."""
import copy
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("NO_NETWORK", "1")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pipeline import entities as E  # noqa: E402
from pipeline.config import clear_warnings, get_last_warnings  # noqa: E402
from geodb_marker import needs_geodb

FIXTURE = ROOT / "tests" / "fixtures" / "entities_spec.json"


def _spec():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_fixture_has_no_entity_gaps_and_covers_every_type():
    spec = _spec()
    assert E.spec_gaps(spec) == []
    seen = {e["type"] for sc in spec["scenes"] for per in sc["entity_plan"] for e in per}
    assert {"place", "terrain", "time", "quantity", "person", "route", "conflict", "nature", "empire"} <= seen
    scales = {e.get("scale") for sc in spec["scenes"] for per in sc["entity_plan"] for e in per if e["type"] == "place"}
    assert {"village", "capital", "country", "continent", "globe", "ocean"} <= scales


def test_sentence_with_entity_but_no_visual_fails():
    """The failing case the rule exists for: remove the visual and the gate reports it."""
    spec = _spec()
    broken = copy.deepcopy(spec)
    for sc in broken["scenes"]:
        if sc["id"] == "year":
            sc["beats"] = [b for b in sc["beats"] if b["kind"] != "year_counter"]   # the year has no timeline visual
        if sc["id"] == "capital":
            sc["map_overlay"] = None                                                  # the capital has no map
    gaps = E.spec_gaps(broken)
    assert any(g.startswith("year:") for g in gaps), gaps
    assert any(g.startswith("capital:") for g in gaps), gaps


def test_plan_errors_go_to_the_director():
    ent = {"type": "person", "text": "ابن سينا", "name_ar": "ابن سينا", "span": [0, 1]}
    errs = E.plan_errors({}, {"body1": [{"kind": "bigtext"}]}, {"body1": [[ent]]})
    assert errs and "person" in errs[0] and "person_card" in errs[0]
    assert E.plan_errors({}, {"body1": [{"kind": "person_card"}]}, {"body1": [[ent]]}) == []


def test_text_is_only_cut_on_whole_words():
    s = "وتليها مدينة الكويت عاصمة دولة الكويت"
    assert E.find_span(s, "الكويت") == (2, 2)
    assert E.find_span(s, "كويت") is None            # a substring is not a word
    assert E.find_span(s, "مدينة الكويت") == (1, 2)
    assert E.cut_words(s, 3) == "وتليها مدينة الكويت"


@needs_geodb
def test_unverifiable_and_non_span_entities_are_dropped_visibly():
    clear_warnings()
    sentence = "قرية سيوة هادئة"
    assert E.validate_entity({"type": "place", "scale": "village", "text": "سيوة", "name_ar": "سيوة", "name_en": "Siwa", "iso2": "EG"}, sentence)
    assert E.validate_entity({"type": "place", "scale": "city", "text": "طوكيو", "name_ar": "طوكيو", "name_en": "Tokyo"}, sentence) is None  # not in the sentence
    assert any("not a whole-word span" in w for w in get_last_warnings())


def test_a_new_entity_type_is_one_registry_entry():
    from pipeline.entities import EntityType
    E.register(EntityType("color", "لون", "a colour", channel="beat", kinds=("stat",),
                          fallback=lambda e, s: {"kind": "stat", "number": "1", "label": "x"}))
    try:
        ent = {"type": "color", "text": "أحمر", "span": [0, 0]}
        assert E.plan_errors({}, {"s": [{"kind": "bigtext"}]}, {"s": [[ent]]})
    finally:
        del E.ENTITY_REGISTRY["color"]


@needs_geodb
def test_injected_extractor_is_validated_locally():
    script = {"hook": {"id": "hook", "role": "hook", "narration": "القاهرة هي عاصمة مصر."}}
    fake = lambda payload: {"scenes": [{"id": "hook", "sentences": [{"i": 0, "entities": [
        {"type": "place", "scale": "capital", "text": "القاهرة", "name_ar": "القاهرة", "name_en": "Cairo", "iso2": "EG"},
        {"type": "place", "scale": "city", "text": "باريس", "name_ar": "باريس", "name_en": "Paris"}]}]}]}
    out = E.extract_script(script, extractor=fake)
    names = [e["name_ar"] for per in out.get("hook", []) for e in per]
    assert "القاهرة" in names and "باريس" not in names     # Paris is not a span of the sentence: dropped
    assert all(e["verified"] in ("geonames", "natural-earth") for per in out["hook"] for e in per)


@needs_geodb
def test_bare_list_sentences_are_read():
    """Real reply shape (short 24, Damascus): "sentences": [[entities of sentence 0], [] ...] instead of {"i","entities"}.
    It used to be dropped silently, so no scene of the video got a map."""
    script = {"body2": {"id": "body2", "role": "body", "narration": "دمشق، عاصمة سوريا، مأهولة منذ القدم. أي أنها الأقدم!"}}
    fake = lambda payload: {"scenes": [{"id": "body2", "sentences": [[
        {"type": "place", "scale": "city", "text": "دمشق", "name_ar": "دمشق", "name_en": "Damascus", "iso2": "SY", "lat": 33.51, "lon": 36.29},
        {"type": "place", "scale": "country", "text": "سوريا", "name_ar": "سوريا", "name_en": "Syria", "iso2": "SY", "lat": 35.0, "lon": 38.0}], []]}]}
    out = E.extract_script(script, extractor=fake)
    names = [e["name_ar"] for per in out["body2"] for e in per]
    assert "دمشق" in names and "سوريا" in names
    assert out["body2"][-1] == []


def test_saved_empty_plan_is_read_again(monkeypatch):
    """A script saved with an all-empty plan (the misparsed reply above) is re-extracted; a real plan is kept as is."""
    fresh = {"body2": [[{"name_ar": "دمشق"}]]}
    monkeypatch.setattr(E, "extraction_enabled", lambda: True)
    monkeypatch.setattr(E, "extract_script", lambda script, geo=None: fresh)
    script = {"_entities": {"body2": [[], []], "hook": [[]]}}
    assert E.ensure_plan(script) == fresh and script["_entities"] == fresh
    kept = {"_entities": {"body2": [[{"name_ar": "صور"}]]}}
    assert E.ensure_plan(kept) == {"body2": [[{"name_ar": "صور"}]]}


def test_overlay_handles_every_scale():
    spec = _spec()
    by_id = {sc["id"]: sc["map_overlay"] for sc in spec["scenes"] if sc.get("map_overlay")}
    assert max(w["zoom"] for w in by_id["village"]["waypoints"]) >= 2.6        # tiny place: lens territory
    assert by_id["globe"]["waypoints"][0]["kind"] == "globe"
    assert any(f["shape"] == "area" for f in by_id["ocean"]["features"])
    assert any(f["shape"] == "river" and f["d"] for f in by_id["river"]["features"])
    assert len(by_id["route"]["waypoints"]) == 3
    assert by_id["conflict"]["waypoints"][1]["arrow"] == "attack"


def test_extractor_garbage_never_raises():
    """The model sometimes returns strings inside `scenes` / `sentences`: the plan stays empty instead of crashing."""
    script = {"hook": {"id": "hook", "role": "hook", "narration": "القاهرة هي عاصمة مصر."}}
    for bad in ({"scenes": ["hook", "x"]}, {"scenes": [{"id": "hook", "sentences": "oops"}]}, {"scenes": [{"id": "hook", "sentences": ["a", 3]}]}):
        out = E.extract_script(script, extractor=lambda payload, b=bad: b)
        assert out["hook"] == [[]]


@needs_geodb
def test_ordinary_adjective_is_not_a_historical_place():
    """'جديدة' (new) is also a name-less historical hamlet in Lebanon: it must not hijack «عاصمة جديدة» in a Brazil sentence."""
    from pipeline import geo
    assert geo.detect_city_in_text("في البرازيل، بنوا عاصمة جديدة")[0] is None
    assert geo.detect_city_in_text("نقلت البرازيل عاصمتها إلى برازيليا")[0] == "برازيليا"


def test_arabic_proclitics_do_not_hide_a_named_place():
    """«وأوروبا» / «وآسيا» / «بآسيا» / «للعراق»: the place is named, only a one-letter proclitic is glued to it."""
    from pipeline.entities import find_span
    s = "تفصل جبال الأورال بين أوروبا وآسيا"
    assert find_span(s, "أوروبا") == (4, 4) and find_span(s, "آسيا") == (5, 5) and find_span(s, "الأورال") == (2, 2)
    assert find_span("تقع روسيا بآسيا", "آسيا") == (2, 2)
    assert find_span("سافر للعراق أمس", "العراق") == (1, 1)
    assert find_span("بين أوروبا وآسيا", "بين أوروبا") == (0, 1)       # multi-word: the proclitic is only allowed on the first word
    # still whole words: no cutting inside a word
    assert find_span("عاصمة جديدة", "جدة") is None and find_span("الكويتي", "كويت") is None and find_span("هذا مثال", "ثال") is None


def test_scene_cache_asks_the_model_only_for_changed_scenes(tmp_path, monkeypatch):
    monkeypatch.setattr(E, "CACHE_PATH", tmp_path / "c.json")
    calls = []

    def fake(payload):
        calls.append([s["id"] for s in payload["scenes"]])
        return {"scenes": [{"id": s["id"], "sentences": []} for s in payload["scenes"]]}

    monkeypatch.setattr(E, "llm_extract", fake)
    monkeypatch.setattr(E, "_payload", lambda script: {"scenes": [{"id": k, "sentences": [v]} for k, v in script.items()]})
    script = {"a": "جملة أولى.", "b": "جملة ثانية."}
    E.extract_script(script)
    script["b"] = "جملة ثالثة."
    E.extract_script(script)
    E.extract_script(script)
    assert calls == [["a", "b"], ["b"]]


def test_unverified_landmark_is_dropped_not_invented():
    clear_warnings()
    e = {"type": "place", "scale": "landmark", "text": "قلعة", "name_ar": "قلعة", "name_en": "Nowhere Castle", "iso2": "EG", "lat": 30.0, "lon": 31.0}
    assert E.validate_entity(e, "قلعة قديمة") is None      # offline: no dictionary hit and no Nominatim -> model coordinates are NOT trusted
    assert "district" in E.ENTITY_REGISTRY["place"].scales and "landmark" in E.ENTITY_REGISTRY["place"].scales
