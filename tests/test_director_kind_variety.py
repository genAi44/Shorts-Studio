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
