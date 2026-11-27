"""The beat director may not turn every scene into custom_scene (an LLM drawing): photo/map/area_map render natively."""
import pipeline.direct as direct  # noqa: F401  (import order: direct_apply is a split module of direct)
from pipeline.direct_apply import MAX_CUSTOM_RUN, variety_reasons

IDS = ["hook", "lead", "body1", "open_loop1", "body2", "open_loop2", "body3", "cta"]
C, P, M = [{"kind": "custom_scene"}], [{"kind": "photo"}], [{"kind": "map"}]


def test_all_custom_scene_is_rejected():
    reasons = variety_reasons({i: C for i in IDS}, IDS)
    assert len(reasons) == 1 and "photo or map" in reasons[0]


def test_short_custom_runs_pass():
    plan = {"hook": C, "lead": C, "body1": P, "open_loop1": C, "body2": C, "open_loop2": M, "body3": C, "cta": C}
    assert MAX_CUSTOM_RUN == 2 and variety_reasons(plan, IDS) == []


def test_prompt_no_longer_forces_custom_scene():
    s = direct.director_system(True)
    kind_rule = s.split("4. kind:")[1][:900]
    assert "mandatory" not in kind_rule and '"photo"' in kind_rule and '"map"' in kind_rule and "Variety rule" in kind_rule


def _t(sid, role, kind, concept="", narration="جملة عن قناة بنما في أمريكا الوسطى."):
    return {"id": sid, "role": role, "narration": narration, "on_screen": "", "beats": [{"kind": kind, "concept": concept}]}


def test_upgrade_photos_breaks_the_longest_drawn_run_with_distinct_queries():
    from pipeline.direct_apply import _has_long_drawn_run, _upgrade_photos
    roles = ["hook", "body", "body", "open_loop", "body", "open_loop", "body", "cta"]
    kinds = ["photo", "custom_scene", "photo", "custom_scene", "map", "custom_scene", "custom_scene", "custom_scene"]
    concepts = ["", "lock gates", "", "mountain ridge", "", "workers digging under rain", "cargo ship rising inside Gatun lock chamber", "globe"]
    targets = [_t(f"s{i}", r, k, c) for i, (r, k, c) in enumerate(zip(roles, kinds, concepts))]
    targets[0]["beats"][0]["query"] = "Panama landmark architecture"
    targets[2]["beats"][0]["query"] = "Panama Canal locks"
    assert _has_long_drawn_run(targets)
    _upgrade_photos(None, {"title": "قناة بنما"}, targets)
    assert not _has_long_drawn_run(targets)                       # the open_loop2-body3-cta run is broken
    assert targets[6]["beats"][0]["kind"] == "photo"              # body3 (inside the run), not the first body scene
    assert targets[6]["beats"][0]["query"] == "cargo ship rising inside Gatun lock chamber"  # from its own concept
    qs = [t["beats"][0].get("query") for t in targets if t["beats"][0]["kind"] == "photo"]
    assert len(qs) == len(set(q.lower() for q in qs))             # never the same photo twice
