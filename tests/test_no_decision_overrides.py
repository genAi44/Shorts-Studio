"""Part 2: nothing after the director silently swaps its decision (kind or photo query)."""
import pipeline.direct  # noqa: F401  (import order: direct_apply is a split module of direct)
from pipeline.direct_apply import _merge_visual_plan
from pipeline.direct_apply_passes import _diversify_beats


def test_diversify_never_changes_a_kind():
    targets = [
        {"id": "hook", "role": "hook", "narration": "جملة", "beats": [{"kind": "bigtext", "text": "x"}]},
        {"id": "body1", "role": "body", "narration": "رقم 26 هنا", "beats": [{"kind": "stat", "number": "26"}, {"kind": "stat", "number": "26"}]},
        {"id": "cta", "role": "cta", "narration": "شاركنا", "beats": [{"kind": "photo", "query": "Gatun lock", "number": "999"}]},
    ]
    before = [[b["kind"] for b in t["beats"]] for t in targets]
    _diversify_beats({}, targets)
    assert [[b["kind"] for b in t["beats"]] for t in targets] == before
    assert "number" not in targets[2]["beats"][0]          # truthfulness guard kept: 999 is not spoken


def test_director_photo_query_is_not_overwritten_by_the_scene_query():
    s = {"_visual_intelligence": {"scenes": [{"id": "body1", "media_query_en": "Panama landmark architecture"}]}}
    targets = [{"id": "body1", "beats": [{"kind": "photo", "query": "cargo ship inside Gatun lock chamber"},
                                         {"kind": "photo"}]}]
    _merge_visual_plan(None, {}, s, targets)
    assert targets[0]["beats"][0]["query"] == "cargo ship inside Gatun lock chamber"
    assert targets[0]["beats"][1]["query"] == "Panama landmark architecture"   # filled only when the director gave none
