import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline import geo_overlay, media, visual_intelligence


class TestVisualIntelligenceV2(unittest.TestCase):
    def test_historical_event_location_and_scene_plan(self):
        script = {
            "title": "سقوط برلين 1945",
            "hook": {"narration": "في عام 1945 شهدت برلين نهاية الحرب العالمية الثانية.", "on_screen": "برلين 1945"},
            "lead": {"narration": "تحولت المدينة إلى ساحة معركة كبرى في أوروبا.", "on_screen": "ساحة معركة"},
            "body1": {"narration": "استمرت معركة ستالينغراد قبل ذلك وغيرت مسار الحرب.", "on_screen": "ستالينغراد 1942"},
            "open_loop1": {"narration": "لكن كيف انقسمت المدينة بعدها؟", "on_screen": "لغز التقسيم"},
            "body2": {"narration": "تم تقسيم العاصمة إلى أربعة قطاعات عام 1945.", "on_screen": "4 قطاعات"},
            "open_loop2": {"narration": "وماذا حدث في نورماندي؟", "on_screen": "نورماندي"},
            "body3": {"narration": "أنزلت قوات الحلفاء في نورماندي عام 1944.", "on_screen": "نورماندي 1944"},
            "cta": {"narration": "شاركنا رأيك في التعليقات.", "on_screen": "شاركنا"},
        }
        plan = visual_intelligence.build_deterministic_visual_plan(script)
        self.assertTrue(plan["global_era"]["is_historical"])
        scenes_by_id = {s["id"]: s for s in plan["scenes"]}

        # Scene 2 ("تحولت المدينة...") must inherit Berlin from context memory
        lead_locs = [loc["name_ar"] for loc in scenes_by_id["lead"]["explicit_and_inherited_locations"]]
        self.assertTrue(any("برلين" in n for n in lead_locs))

        # Scene plan fields must exist
        sp = scenes_by_id["body1"]["scene_plan"]
        for key in ("what_narration_says", "info_to_clarify", "required_media_or_map", "elements_to_show", "motion_and_camera", "sfx_cue", "transition_to_next"):
            self.assertIn(key, sp)
            self.assertTrue(sp[key])

    def test_geo_overlay_historical_battle_and_zoom_hierarchy(self):
        sc = {
            "id": "body1",
            "role": "body",
            "narration": "وقعت معركة حطين عام 1187 في فلسطين.",
            "on_screen": "معركة حطين",
            "_vi": {"is_historical": True},
        }
        overlay = geo_overlay.build_scene_map_overlay(sc, [], 120)
        self.assertIsNotNone(overlay)
        self.assertTrue(overlay["enabled"])
        self.assertEqual(overlay["map_style"], "historical")
        self.assertEqual(overlay["zoom_hierarchy"], ["world", "continent", "country", "city"])
        self.assertTrue(any("حطين" in wp["name_ar"] for wp in overlay["waypoints"]))

    def test_media_resolve_uses_vi_scene_metadata(self):
        m = media.Media(str(ROOT / "cache" / "test_vi_media"), log=lambda *a: None)
        vi_sc = {
            "media_query_en": "Berlin Brandenburg Gate 1945",
            "must_show": "Berlin 1945 ruins",
            "avoid": "modern skyscrapers",
            "is_historical": True,
        }
        with patch("pipeline.media.find", return_value=[]) as mock_find:
            res = m.resolve({"kind": "photo", "query": ""}, "برلين عام 1945", vi_scene=vi_sc)
            mock_find.assert_called()
            called_query = mock_find.call_args_list[0][0][0]
            self.assertEqual(called_query, "Berlin Brandenburg Gate 1945")
            self.assertNotEqual(res.get("kind"), "photo")  # degraded cleanly when no candidates


if __name__ == "__main__":
    unittest.main()
