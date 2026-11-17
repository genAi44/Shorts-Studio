"""Phase 3 — Slot Layout Planner regression tests."""
import unittest

from pipeline.layout_planner import SLOTS, plan_scene_slots


class TestLayoutPlanner(unittest.TestCase):
    def test_beats_overlapping_in_time_are_trimmed_without_overlap(self):
        scene = {
            "id": "body1",
            "beats": [
                {"kind": "photo", "from": 0, "dur": 90},
                {"kind": "photo", "from": 60, "dur": 80},
            ],
        }
        out = plan_scene_slots(scene)
        b0, b1 = out["beats"][0], out["beats"][1]
        self.assertEqual(b0["from"] + b0["dur"], b1["from"])
        self.assertEqual(b0["slot"], "FULL_STAGE")
        self.assertEqual(b1["slot"], "FULL_STAGE")

    def test_split_map_assigns_stage_a_to_non_map_beats(self):
        scene = {
            "id": "body2",
            "map_overlay": {"enabled": True},
            "visual_mode": "",
            "beats": [{"kind": "photo", "from": 0, "dur": 120}],
            "visuals": [{"kind": "flag", "placement": "badge-row", "spec": {"code": "PA"}}],
        }
        out = plan_scene_slots(scene)
        self.assertEqual(out["beats"][0]["slot"], "STAGE_A")
        self.assertEqual(out["visuals"][0]["slot"], "HEADER")
        self.assertTrue(out["slot_plan"]["has_split_map"])

    def test_slots_do_not_overlap_caption_zone(self):
        cap_top = SLOTS["CAPTION"]["top"]
        for name in ("HEADER", "STAGE_A", "STAGE_B", "FULL_STAGE"):
            self.assertLessEqual(SLOTS[name]["top"] + SLOTS[name]["height"], cap_top)


if __name__ == "__main__":
    unittest.main()
