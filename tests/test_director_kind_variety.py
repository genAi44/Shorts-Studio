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


def test_designer_keeps_director_photo_and_map_scenes():
    from pipeline.scene_author import has_native_visual
    assert has_native_visual({"beats": [{"kind": "photo", "img": "media/p1.jpg"}]})
    assert has_native_visual({"beats": [{"kind": "area_map"}]}) and has_native_visual({"beats": [{"kind": "map"}]})
    assert not has_native_visual({"beats": [{"kind": "photo"}]})          # no image found: the designer may draw it
    assert not has_native_visual({"beats": [{"kind": "generative_canvas", "tsx_id": "DynamicScene_x"}]})
    assert not has_native_visual({"beats": [{"kind": "photo", "img": "media/p4.jpg"}, {"kind": "generative_canvas"}]})  # mixed: authored
    assert has_native_visual({"beats": [{"kind": "map"}, {"kind": "photo", "img": "media/p1.jpg"}]})
