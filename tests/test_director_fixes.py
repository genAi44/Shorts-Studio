import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline import direct, visual_tools
from geodb_marker import needs_geodb


class TestDirectorFixes(unittest.TestCase):
    def test_resolve_flag_no_false_egypt(self):
        # Empty or unknown query must NOT return Egypt (EG)
        res_empty = visual_tools.resolve_flag("")
        self.assertIsNone(res_empty["code"])
        self.assertFalse(res_empty["found"])

        res_unknown = visual_tools.resolve_flag("مدينة غير موجودة إطلاقاً")
        self.assertIsNone(res_unknown["code"])
        self.assertFalse(res_unknown["found"])

        # Real queries must still work
        res_eg = visual_tools.resolve_flag("مصر")
        self.assertEqual(res_eg["code"], "EG")
        self.assertTrue(res_eg["found"])

        res_qa = visual_tools.resolve_flag("قطر")
        self.assertEqual(res_qa["code"], "QA")
        self.assertTrue(res_qa["found"])

    def test_fallback_beat_versus(self):
        scene = {"role": "body", "on_screen": "مقارنة"}
        beat = direct.fallback_beat(scene, 1, "حجم الاقتصاد الكلي مقابل ثراء شعب الدولة")
        self.assertEqual(beat["kind"], "versus_battle")

    def test_fallback_beat_rankings_bars(self):
        scene = {"role": "body", "on_screen": "أغنى 5 دول"}
        beat = direct.fallback_beat(scene, 1, "سنكشف لك أغنى خمس دول في العالم")
        self.assertEqual(beat["kind"], "bars")
        self.assertTrue(len(beat["items"]) >= 3)

    def test_fallback_beat_specialized_generative(self):
        scene = {"role": "body", "on_screen": "قطر"}
        beat = direct.fallback_beat(scene, 1, "مستفيدة من ثرواتها الهائلة من الغاز الطبيعي")
        self.assertEqual(beat["kind"], "generative_canvas")
        self.assertTrue(len(beat["elements"]) >= 3)

    def test_apply_beats_no_star_icons(self):
        script = {
            "title": "ثروات العالم",
            "hook": {"narration": "هل تعلم عن هذا السر؟", "on_screen": "بداية", "beats": []},
            "body1": {"narration": "الجملة الأولى التوضيحية للموضوع العام.", "on_screen": "نقطة 1", "beats": []},
            "cta": {"narration": "اشترك للمزيد وشاركنا رأيك في التعليقات.", "on_screen": "شاركنا", "beats": []},
        }
        res = direct.apply_beats(script, {})
        for pid in ("hook", "body1", "cta"):
            for b in res.get(pid, {}).get("beats", []):
                # Ensure no icons beat with star fallback
                if b.get("kind") == "icons":
                    items = b.get("items") or []
                    self.assertFalse(any(it.get("icon") == "star" for it in items))

    def test_hook_hero_visual_not_empty_bigtext(self):
        script = {
            "title": "حضارات مفقودة",
            "hook": {"narration": "حضارات مفقودة اختفت عبر التاريخ.", "beats": [{"kind": "bigtext", "text": "حضارات مفقودة"}]},
            "body1": {"narration": "معابد عظيمة بنيت في الغابات.", "beats": []},
            "cta": {"narration": "تابعنا للمزيد.", "beats": []},
        }
        res = direct.apply_beats(script, {})
        hook_beats = res.get("hook", {}).get("beats", [])
        self.assertTrue(len(hook_beats) > 0)
        # First beat in hook must be a rich photo or generative canvas, NEVER bare bigtext
        self.assertIn(hook_beats[0]["kind"], ("photo", "generative_canvas"))

    def test_generative_procedural_scene_no_fake_kpis(self):
        from pipeline.generative_visuals import compose_procedural_scene
        for text in [
            "المخازن الغذائية وهلع السكان بسبب المجاعة",
            "حضارات قديمة ومعابد مدفونة في الرمال",
            "طوفان هائل وفيضانات أغرقت المدينة كاملة",
            "انهيار كامل وسقوط الإمبراطورية",
            "مفهوم عام ونقاش تاريخي معمق",
        ]:
            scene = compose_procedural_scene(text)
            self.assertEqual(scene["kind"], "generative_canvas")
            scene_str = str(scene)
            self.assertNotIn("مؤشر التفاعل", scene_str)
            self.assertNotIn("نسبة الإنجاز", scene_str)
            self.assertNotIn("رؤية استراتيجية", scene_str)

    def test_photo_to_text_returns_generative_canvas(self):
        b = {"kind": "photo", "query": "ancient ruins", "text": "معابد قديمة غارقة"}
        fallback = direct.photo_to_text(b)
        self.assertEqual(fallback["kind"], "generative_canvas")

    def test_word_count_limits_flexible_above_and_strict_under(self):
        from pipeline import scriptspec as sp
        # Script with 149 words: Hook 17 words, CTA 18 words, fits within ~57 seconds
        script_149 = {
            "title": "حضارات مفقودة عبر التاريخ الغامض",
            "tags": ["تاريخ", "حضارات", "أسرار"],
            "facts": [{"claim": "حقيقة 1", "source": "المصدر"}],
            "hook": {"narration": "هل تساءلت يوماً لماذا اختفت أعظم إمبراطوريات العالم القديم فجأة دون أن تترك خلفها أي أثر واضح للعلماء؟", "on_screen": "لغز الاختفاء", "visual": {"type": "text", "text": "اختفاء مفاجئ"}}, # 17 words
            "lead": {"narration": "في هذا المقطع القصير سنكشف لك ثلاثة أسرار صادمة حول مدن عظيمة ابتلعتها رمال الصحراء والغابات الكثيفة لقرون طويلة.", "on_screen": "كشف الأسرار", "visual": {"type": "text", "text": "مدن مدفونة"}}, # 19 words
            "body1": {"narration": "الحقيقة الأولى تكمن في حضارة المايا التي شيدت أهرامات هائلة في قلب الأدغال، لكن الجفاف الحاد دمر زراعتهم وقضى على مصادر طعامهم.", "on_screen": "جفاف المايا", "visual": {"type": "text", "text": "أهرامات الأدغال"}}, # 23 words
            "open_loop1": {"narration": "لكن المثير للدهشة، هل كان الجفاف وحده هو المسؤول عن سقوط تلك الإمبراطورية الكبرى؟", "on_screen": "لغز السقوط", "visual": {"type": "text", "text": "سر السقوط"}}, # 14 words
            "body2": {"narration": "الوثائق المكتشفة أثبتت نشوب حروب دموية وصراعات طاحنة بين المدن المتنافسة على الموارد القليلة المتبقية مما عجل بانهيار الهيكل الاجتماعي بالكامل.", "on_screen": "صراع الموارد", "visual": {"type": "text", "text": "صراع داخلي"}}, # 20 words
            "open_loop2": {"narration": "وما الذي حدث للكنوز الذهبية الضخمة التي كانت تملأ قصور ملوكهم حتى اختفت تماماً؟", "on_screen": "الكنوز المفقودة", "visual": {"type": "text", "text": "أين الكنوز؟"}}, # 14 words
            "body3": {"narration": "الفيضانات الجارفة طمرت المعابد وقصور الذهب تحت أمتار من الطمي الكثيف ليتحول المجد التليد إلى أطلال صامتة تنتظر من يعيد اكتشافها.", "on_screen": "طوفان الطمي", "visual": {"type": "text", "text": "أطلال صامتة"}}, # 22 words
            "cta": {"narration": "شاركنا رأيك في التعليقات هل يمكن لحضارتنا الحالية أن تواجه نفس هذا المصير الغامض في المستقبل البعيد أم لا:", "on_screen": "شارك برأيك", "visual": {"type": "text", "text": "شاركنا رأيك"}}, # 18 words
        }
        tw = sp.total_words(script_149)
        self.assertTrue(145 <= tw <= 152)
        errors = sp.script_errors(script_149)
        # MUST NOT have any errors (no non-conforming ⛔)
        self.assertEqual(errors, [])

        # But a script UNDER minimum words (< 95) MUST produce an error
        script_under = {
            "title": "قصير جداً",
            "hook": {"narration": "هل تعلم عن هذا الشيء؟", "visual": {"type": "text", "text": "سؤال"}},
            "lead": {"narration": "سنخبرك الآن بالسر.", "visual": {"type": "text", "text": "سر"}},
            "body1": {"narration": "هذه معلومة قصيرة.", "visual": {"type": "text", "text": "نقطة"}},
            "open_loop1": {"narration": "ولكن ماذا حدث بعد ذلك؟", "visual": {"type": "text", "text": "ترقب"}},
            "body2": {"narration": "حدثت أشياء غريبة.", "visual": {"type": "text", "text": "غرابة"}},
            "open_loop2": {"narration": "وهل انتهى الأمر؟", "visual": {"type": "text", "text": "تساؤل"}},
            "body3": {"narration": "وانتهت القصة هنا.", "visual": {"type": "text", "text": "نهاية"}},
            "cta": {"narration": "اشترك الآن بالقناة للمزيد:", "visual": {"type": "text", "text": "اشتراك"}},
        }
        tw_under = sp.total_words(script_under)
        self.assertTrue(tw_under < 95)
        errors_under = sp.script_errors(script_under)
        self.assertTrue(any("أقل من الحد الأدنى" in e for e in errors_under))

    @needs_geodb
    def test_auto_enrichment_of_scene_visuals_not_empty(self):
        script = {
            "title": "مصر وتاريخ الأهرامات",
            "hook": {"narration": "هل زرت مصر وشاهدت أهرامات الجيزة الخالدة؟", "visual": {"type": "text", "text": "أهرامات الجيزة"}},
            "body1": {"narration": "الفراعنة شيدوا معابد مهيبة ومعالم تاريخية لا نظير لها في العالم.", "visual": {"type": "text", "text": "معابد مهيبة"}},
            "cta": {"narration": "اشترك بالقناة وشاركنا رأيك في التعليقات الآن:", "visual": {"type": "text", "text": "شاركنا"}},
        }
        res = direct.apply_beats(script, {})
        hook_vis = res.get("hook", {}).get("visuals", [])
        # Visuals rectangle MUST NOT be empty []
        self.assertTrue(len(hook_vis) > 0)
        self.assertIn(hook_vis[0].get("kind"), ("flag", "icon", "lottie", "emoji"))
        # Egypt mentioned in Hook -> flag of EG should be picked
        self.assertEqual(hook_vis[0].get("kind"), "flag")
        self.assertEqual(hook_vis[0].get("spec", {}).get("code"), "EG")

    def test_sanitize_spec_preserves_iconify_and_question_icons(self):
        from pipeline import icons as _icons
        spec = {
            "scenes": [
                {
                    "id": "open_loop1",
                    "beats": [
                        {
                            "kind": "canvas",
                            "elements": [
                                {"type": "icon", "name": "question"},
                                {"type": "icon", "name": "lucide:landmark"},
                                {"type": "icon", "name": "lucide:building"},
                            ],
                        }
                    ],
                }
            ]
        }
        sanitized = _icons.sanitize_spec_assets(spec)
        els = sanitized["scenes"][0]["beats"][0]["elements"]
        self.assertEqual(els[0]["name"], "question")
        self.assertEqual(els[1]["name"], "lucide:landmark")
        self.assertEqual(els[2]["name"], "lucide:building")

    def test_no_midword_truncation_in_procedural_scene(self):
        from pipeline.generative_visuals import compose_generative_canvas
        sent = "الجنوبية عاصمتين رسميّتين بدلاً من عاصمة واحدة؟"
        res = compose_generative_canvas(sent, context="لغز العاصمتين")
        self.assertEqual(res["title"], "لغز العاصمتين")
        for el in res["elements"]:
            if el.get("type") == "badge":
                # Must never end with partial word "عاص" or "واحد"
                self.assertFalse(el["text"].endswith("عاص"))
                self.assertFalse(el["text"].endswith("واحد"))

    def test_reject_hallucinated_war_elevation_profile_and_preserve_map(self):
        from pipeline import geo as _geo
        g = _geo.get_geo()
        sent = "اندلعت حرب أهلية دامية طاحنة عام ألف وثمانمئة وتسعة وتسعين جعلت لاباز المركز الاقتصادي."
        bad_beat = {
            "kind": "elevation_profile",
            "title": "حرب 1899",
            "capital": "حرب 1899",
            "height": "1,600",
            "unit": "كيلومتر",
        }
        norm = direct.normalize_beat(bad_beat, sent, g)
        self.assertNotEqual(norm["kind"], "elevation_profile")

        script = {
            "title": "لماذا تملك بوليفيا عاصمتين؟",
            "body2": {
                "narration": sent,
                "on_screen": "صعود لاباز",
                "visual": {
                    "type": "map",
                    "countries": ["BOL"],
                    "highlight": ["BOL"],
                    "points": [{"name": "لاباز", "lat": -16.5, "lon": -68.15}],
                },
            },
        }
        applied = direct.apply_beats(script, {"scenes": [{"id": "body2", "beats": [bad_beat]}]}, g)
        self.assertEqual(applied["body2"]["beats"][0]["kind"], "map")

    def test_fix1_central_layout_contract(self):
        from pipeline import layout as py_layout
        from scripts.check_layout import run_check
        self.assertEqual(py_layout.SAFE_TOP, 72)
        self.assertEqual(py_layout.SAFE_BOTTOM, 1780)
        self.assertEqual(py_layout.HEADLINE_ZONE["top"], 140)
        self.assertEqual(py_layout.BEAT_ZONE["top"], 280)
        self.assertEqual(py_layout.CAPTION_ZONE["top"], 1420)
        self.assertTrue(run_check())

    def test_fix2_explicit_fallbacks_and_debug_mode(self):
        import os
        from pipeline import config as cfg
        cfg.clear_warnings()
        beat = {"kind": "bigtext", "text": "تجربة"}
        res = cfg.record_fallback("unit_test_reason", "beat_42", beat)
        self.assertTrue(res.get("_fallback"))
        self.assertTrue(beat.get("_fallback"))
        self.assertTrue(any("WARNING: falling back [unit_test_reason] beat=[beat_42]" in w for w in cfg.get_last_warnings()))

        prev_debug = os.environ.get("DEBUG")
        try:
            os.environ["DEBUG"] = "1"
            with self.assertRaises(cfg.FallbackError):
                cfg.record_fallback("strict_debug_failure", "beat_99", {})
        finally:
            if prev_debug is None:
                os.environ.pop("DEBUG", None)
            else:
                os.environ["DEBUG"] = prev_debug

    def test_fix3_single_schema_validation(self):
        valid_beat = {"id": "b1", "kind": "stat", "number": "95%", "label": "دقة", "layout": "ring", "_fallback": True}
        self.assertEqual(direct.validate_beat(valid_beat)["kind"], "stat")

        invalid_field_beat = {"kind": "stat", "number": "95%", "unknown_python_field": 123}
        with self.assertRaises(ValueError):
            direct.validate_beat(invalid_field_beat)

    def test_fix4_whole_word_arabic_and_closed_icon_categories(self):
        from unittest.mock import patch
        from pipeline import icons as _icons
        self.assertEqual(len(_icons.CLOSED_ICON_CATEGORIES), 20)
        # Whole-word check: "تقل" must NOT match "علم" or "قرن"
        self.assertFalse(_icons._has_whole_word("تقل المسافة بين المدينتين", "علم"))
        self.assertTrue(_icons._has_whole_word("هذا علم الفلك الحديث", "علم"))

        # LLM icon picker selects from the closed 20-word list
        with patch("pipeline.llm.call_llm_json", return_value={"category": "coin"}):
            picked = _icons.pick_icon_category_llm("نمو الاقتصاد العالمي والبنوك", use_llm=True)
            self.assertEqual(picked, "coin")

    def test_fix5_beat_rules_and_llm_retry_guard(self):
        from pipeline import geo as _geo
        g = _geo.get_geo()
        script = {
            "title": "تحول اقتصادي",
            "body1": {"narration": "في عام 1899 حدث تحول اقتصادي كبير.", "on_screen": "عام التحول"},
        }
        bad_plan = {"scenes": [{"id": "body1", "beats": [{"kind": "map", "countries": [], "points": []}]}]}
        retried_calls = []

        def fake_retry(failed_reasons):
            retried_calls.extend(failed_reasons)
            return {"scenes": [{"id": "body1", "beats": [{"kind": "stat", "number": 1899, "label": "عام التحول"}]}]}

        applied = direct.apply_beats(script, bad_plan, g, llm_retry_fn=fake_retry)
        self.assertEqual(len(retried_calls), 1)
        self.assertEqual(applied["body1"]["beats"][0]["kind"], "stat")


    @needs_geodb
    def test_city_detection_and_map_enforcement(self):
        from pipeline import geo as _geo
        g = _geo.get_geo()
        # فحص كشف المدن
        city, info = _geo.detect_city_in_text("كانت سلا مركز الحكم الأولى للدولة المغربية")
        self.assertEqual(city, "سلا")
        self.assertEqual(info["iso"], "MAR")
        self.assertAlmostEqual(info["lat"], 34.05, places=1)

        # فحص إجبار الخريطة عند ذكر عاصمة/مدينة حتى لو اختار الـ LLM نوعاً آخر
        script = {
            "title": "عواصم المغرب",
            "body1": {"narration": "كانت سلا مركز الحكم الأولى للدولة المغربية.", "on_screen": "سلا: العاصمة الأولى"},
            "body2": {"narration": "أصبحت مراكش عاصمة دينية وعلمية مرموقة.", "on_screen": "مراكش: العاصمة الثالثة"}
        }
        plan = {
            "scenes": [
                {"id": "body1", "beats": [{"kind": "stat", "number": "319", "label": "سنة التأسيس"}]},
                {"id": "body2", "beats": [{"kind": "generative_canvas", "title": "مراكش"}]}
            ]
        }
        applied = direct.apply_beats(script, plan, g)
        self.assertEqual(applied["body1"]["beats"][0]["kind"], "map")
        self.assertEqual(applied["body1"]["beats"][0]["countries"], ["MAR"])
        self.assertEqual(applied["body1"]["beats"][0]["points"][0]["name"], "سلا")

        self.assertEqual(applied["body2"]["beats"][0]["kind"], "map")
        self.assertEqual(applied["body2"]["beats"][0]["countries"], ["MAR"])
        self.assertEqual(applied["body2"]["beats"][0]["points"][0]["name"], "مراكش")

    @needs_geodb
    def test_photo_query_country_translation_no_raw_iso(self):
        # التأكد من عدم استخدام رموز ISO الثلاثية الخام (مثل MAR) التي تطابق كاليفورنيا
        pb = direct.detect_photo_beat("مراكش عاصمة تاريخية", pt_name="مراكش", cou_iso="MAR")
        self.assertIsNotNone(pb)
        self.assertIn("Morocco", pb["query"])
        self.assertNotIn("MAR ", pb["query"])
        self.assertIn("Marrakech", pb["query"])

    @needs_geodb
    def test_hook_map_enrichment_multiple_capitals(self):
        from pipeline import geo as _geo
        g = _geo.get_geo()
        script = {
            "title": "لماذا للمغرب أربع عواصم إمبراطورية؟",
            "hook": {"narration": "لماذا يمتلك المغرب أربع عواصم إمبراطورية موزعة بينها؟", "on_screen": "أربع عواصم إمبراطورية"},
            "body1": {"narration": "كانت سلا العاصمة الأولى.", "on_screen": "سلا"},
            "body2": {"narration": "أصبحت فاس العاصمة الثانية.", "on_screen": "فاس"},
            "body3": {"narration": "أصبحت مراكش العاصمة الثالثة.", "on_screen": "مراكش"}
        }
        plan = {
            "scenes": [
                {"id": "hook", "beats": [{"kind": "map", "countries": ["MAR"], "points": []}]},
                {"id": "body1", "beats": [{"kind": "map", "countries": ["MAR"], "points": [{"name": "سلا"}]}]},
            ]
        }
        applied = direct.apply_beats(script, plan, g)
        hook_pts = applied["hook"]["beats"][0].get("points", [])
        self.assertGreaterEqual(len(hook_pts), 3)
        pt_names = [p["name"] for p in hook_pts]
        self.assertIn("سلا", pt_names)
        self.assertIn("فاس", pt_names)
        self.assertIn("مراكش", pt_names)


if __name__ == "__main__":
    unittest.main()


