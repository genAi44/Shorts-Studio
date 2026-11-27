"""Part 6: renders are compared with the reference band (motion / frozen frames / brightness)."""
from pipeline.quality_bar import compare


def test_the_weak_render_fails_and_a_reference_like_render_passes():
    weak = compare({"motion": 1.05, "still_pct": 53.8, "luma": 22.5})
    assert not weak["passed"] and len(weak["issues"]) == 3
    assert compare({"motion": 8.8, "still_pct": 9.0, "luma": 185.0})["passed"]
