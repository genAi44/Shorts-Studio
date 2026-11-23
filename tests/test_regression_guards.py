"""
tests/test_regression_guards.py
قائمة التحقق التلقائية لمنع تكرار جميع الأخطاء المرصودة عبر دورات التطوير (Cycles 1-11).
أي تعديل مستقبلي يكسر أياً من هذه القواعد سيفشل هنا فوراً قبل الرندر.
"""
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent


class TestRegressionGuards(unittest.TestCase):
    def test_01_sanitize_fixes_non_monotonic_interpolate_and_foreign_object_outside_svg(self):
        from pipeline.storyteller import _sanitize_llm_tsx

        raw = """
        export const DynamicScene_test_1: React.FC<{frame?: number; fps?: number; dur?: number}> = (props) => {
          const currentFrame = useCurrentFrame();
          const {fps: videoFps} = useVideoConfig();
          const frame = props.frame ?? currentFrame;
          const fps = props.fps ?? videoFps;
          const dur = Math.max(1, props.dur ?? 150);
          const p = Math.min(1, Math.max(0, frame / dur));
          const ph3 = interpolate(p, [0.68, 0.78, 1.0, 1.0], [0, 1, 1, 1], {clamp: true});
          return (
            <AbsoluteFill style={{pointerEvents: 'none', overflow: 'hidden', background: '#050b16'}}>
              <svg width={1080} height={1920} viewBox="0 0 1080 1920">
                <rect x={60} y={260} width={400} height={120} fill="#111" />
              </svg>
              <foreignObject x={60} y={260} width={400} height={120} style={{opacity: ph3}}>
                <div>اختبار</div>
              </foreignObject>
            </AbsoluteFill>
          );
        };
        """
        cleaned = _sanitize_llm_tsx(raw, "DynamicScene_test_1")
        self.assertIsNotNone(cleaned)
        self.assertNotIn("[0.68, 0.78, 1.0, 1.0]", cleaned)
        self.assertNotIn("[0.68, 0.78, 1, 1]", cleaned)
        self.assertNotIn("clamp: true", cleaned)
        # </svg> must appear AFTER <foreignObject>
        self.assertLess(cleaned.find("<foreignObject"), cleaned.rfind("</svg>"))

    def test_02_llm_prompt_forbids_rolling_historical_years(self):
        from pipeline.storyteller import _LLM_TSX_SYSTEM

        self.assertIn("NEVER animate or roll historical years", _LLM_TSX_SYSTEM)
        self.assertIn("1465..1920", _LLM_TSX_SYSTEM)

    def test_03_no_fake_ranking_placeholder_bars(self):
        from pipeline.direct import fallback_beat

        sc = {"id": "b1", "role": "body", "on_screen": "أكبر سور"}
        b = fallback_beat(sc, 0, "أكبر مشروع هندسي في تاريخ الصين القديم.")
        if b.get("kind") == "bars":
            labels = [it.get("label", "") for it in (b.get("items") or [])]
            self.assertNotIn("المرتبة الأولى", labels)

    def test_04_detect_photo_beat_prioritizes_landmarks_over_generic_regex(self):
        from pipeline.direct import detect_photo_beat

        pb_wall = detect_photo_beat("هل تعلم أن بناء سور الصين العظيم استغرق أكثر من ألفي عام؟")
        self.assertIsNotNone(pb_wall)
        self.assertIn("Great Wall of China", pb_wall["query"])
        self.assertNotIn("flood", pb_wall["query"].lower())

        pb_petra = detect_photo_beat("بُنيت مدينة البتراء وسط الصحراء.")
        self.assertIsNotNone(pb_petra)
        self.assertIn("Petra", pb_petra["query"])

    def test_05_photo_and_map_beats_keep_no_tsx_id(self):
        from pipeline.direct import apply_beats
        from pipeline.geo import get_geo

        script = {
            "title": "لماذا بُني سور الصين العظيم؟",
            "hook": {"id": "hook", "role": "hook", "narration": "سور الصين العظيم أطول سور في التاريخ."},
            "body1": {"id": "body1", "role": "body", "narration": "حماية الصين من الغزوات الشمالية."},
            "cta": {"id": "cta", "role": "cta", "narration": "شاركنا رأيك في التعليقات."},
        }
        director_out = {
            "scenes": [
                {"id": "hook", "beats": [{"kind": "photo", "query": "Great Wall of China"}]},
                {"id": "body1", "beats": [{"kind": "map", "countries": ["CHN"]}]},
                {"id": "cta", "beats": [{"kind": "generative_canvas", "concept": "cta"}]},
            ]
        }
        res = apply_beats(script, director_out, geo=get_geo())
        self.assertIsNone(res["hook"]["beats"][0].get("tsx_id"))
        self.assertIsNone(res["body1"]["beats"][0].get("tsx_id"))

    def test_06_geo_disambiguation_and_stopwords(self):
        from pipeline.geo_overlay import extract_timed_geo_mentions

        m1 = extract_timed_geo_mentions("في قلب أمريكا الجنوبية", "", [], 150)
        self.assertTrue(any(m["name_ar"] == "أمريكا الجنوبية" for m in m1))
        self.assertFalse(any(m["name_ar"] == "الولايات المتحدة" for m in m1))

        m2 = extract_timed_geo_mentions("بعد العبور نحو الأندلس", "", [], 150)
        self.assertFalse(any(m["name_ar"] == "العبور" for m in m2))
        self.assertTrue(any(m["name_ar"] == "الأندلس" for m in m2))

        m3 = extract_timed_geo_mentions("هل تستطيع دولاً أخرى تكرار تجربة سنغافورة؟", "", [], 150)
        self.assertFalse(any(m["name_ar"] == "دولا" for m in m3))
        self.assertTrue(any(m["name_ar"] == "سنغافورة" for m in m3))

        m4 = extract_timed_geo_mentions("اكتشف العلماء منحدر حلزوني خفي ودراسة حديثة في أهرامات الجيزة", "", [], 150)
        names4 = {m["name_ar"] for m in m4}
        self.assertNotIn("خفي", names4)
        self.assertNotIn("حديثة", names4)
        self.assertTrue(any("الجيزة" in n or "مصر" in n for n in names4))

    def test_09_enrich_scene_visuals_does_not_match_substring_country_like_handasa_to_india(self):
        from pipeline.visual_tools import enrich_scene_visuals

        sc = {"id": "b1", "role": "body", "narration": "عبقرية هندسية مذهلة في أهرامات الجيزة.", "on_screen": "هندسة الأهرامات"}
        els = enrich_scene_visuals(sc, scene_index=0)
        flags = [e["spec"]["code"] for e in els if e.get("kind") == "flag"]
        self.assertNotIn("in", flags)

    def test_07_media_pick_429_fallback_prefers_matching_keywords(self):
        from pipeline import media

        cands = [
            {"url": "http://ex/1.jpg", "title": "Middle Eastern Mosque", "desc": "stone dome", "src": "Pexels"},
            {"url": "http://ex/2.jpg", "title": "Great Wall of China", "desc": "Great Wall mountains China", "src": "Wikipedia"},
        ]
        im = Image.new("RGB", (800, 600), (100, 120, 140))
        with patch.object(media, "fetch_image", return_value=im), \
             patch("pipeline.llm.gemini_vision_json", side_effect=RuntimeError("429 Quota")):
            picked, score, _ = media.pick(cands, "Great Wall of China landmark", "سور الصين العظيم", lambda *_: None, must_show="Great Wall of China")
        self.assertIsNotNone(picked)
        self.assertEqual(picked["url"], "http://ex/2.jpg")

    def test_08_remotion_short_and_map_overlay_structural_invariants(self):
        short_tsx = (ROOT / "remotion" / "src" / "Short.tsx").read_text(encoding="utf-8")
        map_tsx = (ROOT / "remotion" / "src" / "mapOverlay.tsx").read_text(encoding="utf-8")

        # Legacy MapBeat must be skipped when MapOverlayLayer renders full-stage
        self.assertIn("!(isLegacyFullMap && hasMapOverlay)", short_tsx)
        self.assertIn("mode={mapMode}", short_tsx)
        # Audio headroom cap to prevent 0.0 dB clipping
        self.assertIn("volume={0.78}", short_tsx)
        # MapOverlayLayer must support all 3 modes and continent footer
        self.assertIn("'full-stage'", map_tsx)
        self.assertIn("'split-bottom'", map_tsx)
        self.assertIn("القارة:", map_tsx)

    def test_10_active_beat_tsx_check_and_audio_headroom(self):
        short_tsx = Path("remotion/src/Short.tsx").read_text(encoding="utf-8")
        self.assertIn("Boolean(activeBeat?.tsx_id)", short_tsx)
        self.assertIn("volume={0.78}", short_tsx)

        sfx_tsx = Path("remotion/src/sfx.tsx").read_text(encoding="utf-8")
        self.assertIn("add('impact', start, 0.24)", sfx_tsx)

    def test_11_storyteller_phase_crossfade_and_no_empty_dashed_box(self):
        st = Path("pipeline/storyteller.py").read_text(encoding="utf-8")
        self.assertIn("NEVER draw empty dashed placeholder boxes", st)
        self.assertIn("NEVER leave two cards overlapping in the same slot", st)

    def test_12_geo_detect_city_rejects_common_arabic_words_and_tiny_barbados_greenland(self):
        from pipeline.geo import detect_city_in_text

        self.assertEqual(detect_city_in_text("دولاً لا تملك جيشاً واحداً،"), (None, None))
        self.assertEqual(detect_city_in_text("وتحميها عضويتها وموقعها الاستراتيجي فوق ممر غرينلاند،"), (None, None))

    def test_13_media_rejects_flags_and_unrelated_429_fallback(self):
        from pipeline import media

        cands = [
            {"url": "https://upload.wikimedia.org/wikipedia/commons/a/a4/Flag_of_the_United_States.svg", "thumb": "https://upload.wikimedia.org/wikipedia/commons/a/a4/Flag_of_the_United_States.svg", "title": "Flag of the United States", "source": "Wikipedia"},
            {"url": "http://ex/unrelated.jpg", "thumb": "http://ex/unrelated.jpg", "title": "Random Cat Portrait", "source": "Pexels"},
        ]
        im = Image.new("RGB", (800, 600), (100, 120, 140))
        with patch.object(media, "fetch_image", return_value=im), \
             patch("pipeline.llm.gemini_vision_json", side_effect=RuntimeError("429 Quota")):
            picked, score, _ = media.pick(cands, "Panama Canal shipping", "تعتمد على قناة بنما", lambda *_: None, must_show="Panama Canal")
        self.assertIsNone(picked)
        self.assertEqual(score, 0)

    def test_14_enrich_scene_visuals_fixes_mismatched_flag_code(self):
        from pipeline.visual_tools import enrich_scene_visuals

        scene = {
            "id": "body2",
            "role": "body",
            "narration": "ثانياً، بنما في أمريكا الوسطى",
            "visual": {"type": "map", "countries": ["PAN"], "highlight": ["PAN"]},
            "visuals": [{"kind": "flag", "placement": "badge-row", "spec": {"code": "JP", "shape": "rect", "size": 84}}],
        }
        res = enrich_scene_visuals(scene, scene_index=4)
        self.assertEqual(res[0]["kind"], "flag")
        self.assertEqual(res[0]["spec"]["code"], "PA")

    def test_15_storyteller_clamps_foreign_object_bounds(self):
        from pipeline.storyteller import _sanitize_llm_tsx

        raw = """export const DynamicScene_test: React.FC<{frame?: number; fps?: number; dur?: number}> = (props) => {
  const frame = props.frame ?? useCurrentFrame();
  return (
    <AbsoluteFill>
      <svg width={1080} height={1920} viewBox="0 0 1080 1920">
        <foreignObject x={60} y={12} width={960} height={120}><div dir="rtl" lang="ar">عنوان</div></foreignObject>
        <foreignObject x={60} y={1390} width={960} height={140}><div dir="rtl" lang="ar">تذييل</div></foreignObject>
      </svg>
    </AbsoluteFill>
  );
};"""
        cleaned = _sanitize_llm_tsx(raw, "DynamicScene_test")
        self.assertIsNotNone(cleaned)
        self.assertIn("y={105}", cleaned)
        self.assertIn("y={1315}", cleaned)

    def test_16_scriptspec_catches_promised_five_items_stopping_at_three(self):
        from pipeline.scriptspec import validate

        script = {
            "title": "5 دول بلا جيوش!",
            "hook": {"narration": "هل تتخيل دولاً بلا جيش؟", "on_screen": "دول بلا جيش"},
            "lead": {"narration": "ستكتشف 5 دول لا تملك جيشاً.", "on_screen": "5 دول"},
            "body1": {"narration": "أولاً، كوستاريكا في أمريكا الوسطى.", "on_screen": "كوستاريكا"},
            "open_loop1": {"narration": "وماذا عن دولة أخرى؟", "on_screen": "دولة أخرى"},
            "body2": {"narration": "ثانياً، بنما في أمريكا الوسطى.", "on_screen": "بنما"},
            "open_loop2": {"narration": "وهل هناك عضو في الناتو؟", "on_screen": "عضو ناتو"},
            "body3": {"narration": "ثالثاً، آيسلندا في شمال الأطلسي.", "on_screen": "آيسلندا"},
            "cta": {"narration": "اكتب رأيك في التعليقات:", "on_screen": "شاركنا"},
        }
        errs = [i for i in validate(script) if i["level"] == "error" and i["where"] == "body"]
        self.assertTrue(errs)

    def test_17_photo_tsx_respects_split_bottom_for_arch_tilt_circle(self):
        photo_tsx = (ROOT / "remotion" / "src" / "photo.tsx").read_text(encoding="utf-8")
        short_tsx = (ROOT / "remotion" / "src" / "Short.tsx").read_text(encoding="utf-8")
        map_tsx = (ROOT / "remotion" / "src" / "mapOverlay.tsx").read_text(encoding="utf-8")
        self.assertIn("splitBottom ? 920 : (hasNum ? 820 : 920)", photo_tsx)
        self.assertIn("splitBottom ? 900 : (hasNum ? 800 : 900)", photo_tsx)
        self.assertNotIn("<AccentShapes", photo_tsx)
        self.assertIn("<Background spec={spec} />", short_tsx)
        self.assertNotIn("{!anyCustomTsx && <Background", short_tsx)
        self.assertIn("effectiveMode === 'split-bottom' ? MAP_STAGE_ZONE.split_svg_height", map_tsx)
        self.assertIn("split_svg_height: 620", (ROOT / "remotion" / "src" / "layout.ts").read_text(encoding="utf-8"))

    def test_18_direct_detect_photo_beat_prefers_sentence_country_over_scene_country(self):
        from pipeline.direct import detect_photo_beat

        b = detect_photo_beat("تليها بنما المجاورة التي تحولت إلى مركز لوجستي", pt_name="سان خوسيه", cou_iso="CRI")
        self.assertIsNotNone(b)
        self.assertIn("panama", b["query"].lower())
        self.assertNotIn("costa rica", b["query"].lower())

    def test_19_media_rejects_map_with_historical_places(self):
        from pipeline.media import NON_PHOTO_RE

        self.assertIsNotNone(NON_PHOTO_RE.search("Mauritius_Map_With_Historical_Places.png"))
        self.assertIsNotNone(NON_PHOTO_RE.search("Mauritius Map With Historical Places"))
        self.assertIsNone(NON_PHOTO_RE.search("Maple_Tree_Park_Tokyo.jpg"))

    def test_20_short_tsx_suppresses_duplicate_flag_when_map_overlay_active(self):
        short_tsx = (ROOT / "remotion" / "src" / "Short.tsx").read_text(encoding="utf-8")
        self.assertIn("v.kind !== 'flag'", short_tsx)


if __name__ == "__main__":
    unittest.main()


def test_every_sfx_cue_used_by_remotion_has_a_builder():
    import re
    from pipeline.sfx import SFX_BUILDERS
    src = (ROOT / "remotion" / "src" / "sfx.tsx").read_text(encoding="utf-8")
    m = re.search(r"type SfxName = ([^;]+);", src)
    names = set(re.findall(r"'(\w+)'", m.group(1)))
    assert names <= set(SFX_BUILDERS), names - set(SFX_BUILDERS)


def test_color_interpolate_is_rewritten():
    from pipeline.storyteller import _fix_color_interpolate as f
    out = f("interpolate(p, [0, 1], ['#c0c0c0', '#ffd700'], {x: 1}); interpolate(p, [0, 1], [0, 1])")
    assert out.startswith("interpolateColors(") and "; interpolate(p, [0, 1], [0, 1])" in out


def test_arabic_text_count_distinguishes_bare_scene():
    from pipeline.storyteller import _arabic_texts as at
    assert len(at("<AbsoluteFill><svg><rect/></svg></AbsoluteFill>")) == 0
    assert len(at("<div>عنوان المشهد</div><div>بطاقة أولى</div><div>بطاقة ثانية</div>")) == 3
