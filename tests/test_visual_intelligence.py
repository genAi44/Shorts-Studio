import unittest

from pipeline.visual_intelligence import analyze_script_visual_intelligence
from geodb_marker import needs_geodb


class TestVisualIntelligenceEngine(unittest.TestCase):
    def test_context_memory_inherits_city_and_era(self):
        script = {
            "title": "كيف قُسمت برلين بعد عام 1945؟",
            "hook": {"id": "hook", "role": "hook", "narration": "في عام 1945 تغير مصير برلين إلى الأبد."},
            "lead": {"id": "lead", "role": "lead", "narration": "فقد قُسمت المدينة إلى أربعة قطاعات متنازعة."},
            "body1": {"id": "body1", "role": "body", "narration": "وبُني جدار يفصل بين الشرق والغرب."},
            "cta": {"id": "cta", "role": "cta", "narration": "شاركنا رأيك في التعليقات."},
        }
        plan = analyze_script_visual_intelligence(script, use_llm=False)
        self.assertEqual(plan["domain"], "history")
        self.assertTrue(plan["global_era"]["is_historical"])
        self.assertEqual(plan["global_era"]["year_start"], 1945)

        sc_by_id = {s["id"]: s for s in plan["scenes"]}
        lead_locs = sc_by_id["lead"]["explicit_and_inherited_locations"]
        self.assertTrue(any(loc["name_ar"] == "برلين" and loc["inherited_from_context"] for loc in lead_locs))
        self.assertTrue(sc_by_id["lead"]["is_historical"])
        self.assertIn("modern", sc_by_id["lead"]["avoid"])
        self.assertEqual(sc_by_id["body1"]["visual_mode"], "split_diagram")

    @needs_geodb
    def test_mandatory_geo_overlay_covers_continents_and_landmarks(self):
        from pipeline.geo_overlay import extract_timed_geo_mentions

        m_cont = extract_timed_geo_mentions("في قلب أمريكا الجنوبية وأوروبا", "", [], 150)
        names_cont = {m["name_ar"] for m in m_cont}
        self.assertIn("أمريكا الجنوبية", names_cont)
        self.assertIn("أوروبا", names_cont)
        self.assertNotIn("الولايات المتحدة", names_cont)

        m_lm = extract_timed_geo_mentions("حُفرت قناة السويس لتربط البحر الأحمر", "", [], 150)
        names_lm = {m["name_ar"] for m in m_lm}
        self.assertIn("قناة السويس", names_lm)
        self.assertIn("البحر الأحمر", names_lm)

        m_cross = extract_timed_geo_mentions("بعد العبور في معركة وادي لكة نحو الأندلس", "", [], 150)
        names_cross = {m["name_ar"] for m in m_cross}
        self.assertNotIn("العبور", names_cross)
        self.assertIn("الأندلس", names_cross)

        m_plural = extract_timed_geo_mentions("هل تستطيع دولاً أخرى تكرار تجربة سنغافورة؟", "", [], 150)
        names_plural = {m["name_ar"] for m in m_plural}
        self.assertIn("سنغافورة", names_plural)
        self.assertNotIn("دولا", names_plural)


if __name__ == "__main__":
    unittest.main()
