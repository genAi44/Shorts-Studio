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


def test_ensure_visuals_inserts_logged_marked_shot_and_hides_the_beat_under_it():
    clear_warnings()
    ent = {"type": "time", "scale": "year", "text": "1453", "value": 1453, "label_ar": "سقوط القسطنطينية", "span": [2, 2]}
    words = [{"t": "في", "s": 0.1, "e": 0.4}, {"t": "عام", "s": 0.5, "e": 0.8}, {"t": "1453", "s": 0.9, "e": 1.4}]
    base = [{"kind": "bigtext", "from": 0, "dur": 150}]
    out = E.ensure_visuals(base, [[ent]], words, 150)
    shot = [b for b in out if b["kind"] == "year_counter"]
    assert len(shot) == 1 and shot[0]["_fallback"] and shot[0]["year"] == 1453
    assert out[0]["hide"], "the beat under the inserted shot must be hidden"
    assert any("year_counter" in w for w in get_last_warnings())
    # already covered -> nothing inserted, nothing logged
    clear_warnings()
    planned = [{"kind": "year_counter", "from": 0, "dur": 150, "year": 1453}]
    assert E.ensure_visuals(planned, [[ent]], words, 150) == planned and not get_last_warnings()


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
        out = E.ensure_visuals([{"kind": "bigtext", "from": 0, "dur": 90}], [[ent]], [{"t": "أحمر", "s": 0.1, "e": 0.5}], 90)
        assert any(b["kind"] == "stat" and b["_fallback"] for b in out)
    finally:
        del E.ENTITY_REGISTRY["color"]


def test_injected_extractor_is_validated_locally():
    script = {"hook": {"id": "hook", "role": "hook", "narration": "القاهرة هي عاصمة مصر."}}
    fake = lambda payload: {"scenes": [{"id": "hook", "sentences": [{"i": 0, "entities": [
        {"type": "place", "scale": "capital", "text": "القاهرة", "name_ar": "القاهرة", "name_en": "Cairo", "iso2": "EG"},
        {"type": "place", "scale": "city", "text": "باريس", "name_ar": "باريس", "name_en": "Paris"}]}]}]}
    out = E.extract_script(script, extractor=fake)
    names = [e["name_ar"] for per in out.get("hook", []) for e in per]
    assert "القاهرة" in names and "باريس" not in names     # Paris is not a span of the sentence: dropped
    assert all(e["verified"] in ("geonames", "natural-earth") for per in out["hook"] for e in per)


def test_overlay_handles_every_scale():
    spec = _spec()
    by_id = {sc["id"]: sc["map_overlay"] for sc in spec["scenes"] if sc.get("map_overlay")}
    assert max(w["zoom"] for w in by_id["village"]["waypoints"]) >= 2.6        # tiny place: lens territory
    assert by_id["globe"]["waypoints"][0]["kind"] == "globe"
    assert any(f["shape"] == "area" for f in by_id["ocean"]["features"])
    assert any(f["shape"] == "river" and f["d"] for f in by_id["river"]["features"])
    assert len(by_id["route"]["waypoints"]) == 3
    assert by_id["conflict"]["waypoints"][1]["arrow"] == "attack"
