"""Tests for Smart Geographic Map Overlay detection, timing alignment, and Remotion spec generation."""
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.geo import get_geo
from pipeline.geo_overlay import build_scene_map_overlay, extract_timed_geo_mentions


class TestSmartGeoOverlay(unittest.TestCase):
    def test_detects_countries_capitals_and_cities_automatically(self):
        narration = "تقع دولة الفاتيكان بالكامل داخل مدينة روما عاصمة إيطاليا."
        words = [
            {"t": "تقع", "s": 0.0, "e": 0.4},
            {"t": "دولة", "s": 0.4, "e": 0.8},
            {"t": "الفاتيكان", "s": 0.8, "e": 1.5},
            {"t": "بالكامل", "s": 1.5, "e": 2.0},
            {"t": "داخل", "s": 2.0, "e": 2.4},
            {"t": "مدينة", "s": 2.4, "e": 2.8},
            {"t": "روما", "s": 2.8, "e": 3.4},
            {"t": "عاصمة", "s": 3.4, "e": 3.9},
            {"t": "إيطاليا", "s": 3.9, "e": 4.6},
        ]
        mentions = extract_timed_geo_mentions(narration, "", words, dur_frames=150)
        names = [m["name_ar"] for m in mentions]
        self.assertIn("الفاتيكان", names)
        self.assertIn("روما", names)
        self.assertIn("إيطاليا", names)

        # Verify chronological ordering matches spoken timestamps
        self.assertEqual(names[0], "الفاتيكان")
        self.assertEqual(names[1], "روما")
        self.assertEqual(names[2], "إيطاليا")

        # Verify kinds
        rome = next(m for m in mentions if m["name_ar"] == "روما")
        self.assertEqual(rome["kind"], "capital")
        self.assertEqual(rome["kind_label"], "عاصمة")
        self.assertAlmostEqual(rome["lat"], 41.9, delta=0.5)
        self.assertAlmostEqual(rome["lon"], 12.5, delta=0.5)

    def test_multi_location_overlay_and_word_sync(self):
        sc = {
            "id": "body1",
            "role": "body",
            "narration": "تتقاسم سوكري ولاباز مقاليد الحكم في بوليفيا منذ عام 1899.",
            "on_screen": "سوكري ولاباز",
        }
        words = [
            {"t": "تتقاسم", "s": 0.0, "e": 0.6},
            {"t": "سوكري", "s": 0.6, "e": 1.3},
            {"t": "ولاباز", "s": 1.3, "e": 2.1},
            {"t": "مقاليد", "s": 2.1, "e": 2.7},
            {"t": "الحكم", "s": 2.7, "e": 3.2},
            {"t": "في", "s": 3.2, "e": 3.5},
            {"t": "بوليفيا", "s": 3.5, "e": 4.3},
        ]
        geo = get_geo()
        overlay = build_scene_map_overlay(sc, words, dur_frames=150, geo=geo, scene_idx=2)
        self.assertIsNotNone(overlay)
        self.assertTrue(overlay["enabled"])
        self.assertGreaterEqual(len(overlay["waypoints"]), 2)
        self.assertTrue(len(overlay["countries"]) >= 1)
        self.assertEqual(overlay["countries"][0]["iso3"], "BOL")

        wp_names = [w["name_ar"] for w in overlay["waypoints"]]
        self.assertIn("سوكري", wp_names)
        self.assertIn("لاباز", wp_names)

        # Check trigger_frame progression
        triggers = [w["trigger_frame"] for w in overlay["waypoints"]]
        self.assertEqual(triggers, sorted(triggers))

    def test_no_random_overlay_when_no_location_mentioned(self):
        sc = {
            "id": "body2",
            "role": "body",
            "narration": "ينص الدستور في المادة السادسة على فصل السلطات الثلاث بشكل متوازن.",
            "on_screen": "فصل السلطات",
        }
        words = [{"t": w, "s": i * 0.5, "e": (i + 1) * 0.5} for i, w in enumerate(sc["narration"].split())]
        overlay = build_scene_map_overlay(sc, words, dur_frames=150, scene_idx=3)
        self.assertIsNone(overlay)

    def test_five_countries_and_capitals_world_tour_detection(self):
        pairs = [
            ("تقع باريس عاصمة فرنسا على ضفاف نهر السين.", "فرنسا", "باريس", "FRA"),
            ("تعد طوكيو عاصمة اليابان من أكبر الحواضر في العالم.", "اليابان", "طوكيو", "JPN"),
            ("تزدهر القاهرة عاصمة مصر بتاريخها العريق على نهر النيل.", "مصر", "القاهرة", "EGY"),
            ("صممت برازيليا لتكون عاصمة البرازيل الحديثة في قلب البلاد.", "البرازيل", "برازيليا", "BRA"),
            ("تضم واشنطن العاصمة مقر الحكم الفيدرالي في الولايات المتحدة.", "الولايات المتحدة", "واشنطن العاصمة", "USA"),
        ]
        geo = get_geo()
        for idx, (narration, country_ar, capital_ar, iso3) in enumerate(pairs):
            words = [{"t": w, "s": i * 0.45, "e": (i + 1) * 0.45} for i, w in enumerate(narration.split())]
            overlay = build_scene_map_overlay(
                {"id": f"sc_{idx}", "role": "body", "narration": narration, "on_screen": f"{country_ar} - {capital_ar}"},
                words,
                dur_frames=150,
                geo=geo,
                scene_idx=idx,
            )
            self.assertIsNotNone(overlay, f"Missing overlay for {country_ar} - {capital_ar}")
            wp_names = [w["name_ar"] for w in overlay["waypoints"]]
            self.assertIn(country_ar, wp_names)
            self.assertIn(capital_ar, wp_names)
            c_isos = [c["iso3"] for c in overlay["countries"]]
            self.assertIn(iso3, c_isos)
            # Verify 1:1 viewport and top HUD placement (never bottom-left)
            self.assertEqual(overlay["viewport"], {"w": 840, "h": 520})
            self.assertIn(overlay["placement"], ("top-left", "top-right"))
            # Verify pin coordinates stay locked on the capital and never jump to the country centroid
            cap_wp = next(w for w in overlay["waypoints"] if w["name_ar"] == capital_ar)
            cnt_wp = next(w for w in overlay["waypoints"] if w["name_ar"] == country_ar)
            self.assertEqual((cap_wp["x"], cap_wp["y"]), (cnt_wp["x"], cnt_wp["y"]))

    def test_sanitizer_strips_vertical_writing_mode_and_negative_flip_scale(self):
        from pipeline.storyteller import _sanitize_llm_tsx

        raw = """
        export const DynamicScene_test: React.FC<{frame?: number; fps?: number; dur?: number}> = (props) => {
          const currentFrame = useCurrentFrame();
          const {fps: videoFps} = useVideoConfig();
          const frame = props.frame ?? currentFrame;
          const flipAngle = 180;
          return (
            <AbsoluteFill>
              <svg width={1080} height={1920}>
                <text x={100} y={200} writingMode="tb">طوكيو</text>
                <g transform={`scale(1, ${Math.cos(flipAngle * Math.PI / 180)})`}>
                  <text x={200} y={300}>1960</text>
                </g>
              </svg>
            </AbsoluteFill>
          );
        };
        """
        cleaned = _sanitize_llm_tsx(raw, "DynamicScene_test")
        self.assertIsNotNone(cleaned)
        self.assertNotIn('writingMode="tb"', cleaned)
        self.assertIn("Math.abs(Math.cos(", cleaned)

    def test_remotion_typescript_compiles_with_map_overlay(self):
        rem_dir = ROOT / "remotion"
        tsc_bin = rem_dir / "node_modules" / ".bin" / ("tsc.cmd" if sys.platform.startswith("win") else "tsc")
        if tsc_bin.exists():
            res = subprocess.run(
                [str(tsc_bin), "--noEmit"],
                cwd=str(rem_dir),
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(res.returncode, 0, f"TypeScript compilation failed:\n{res.stdout}\n{res.stderr}")


if __name__ == "__main__":
    unittest.main()



def test_wide_countries_are_not_zoomed_into_a_crop():
    import os
    os.environ.setdefault("NO_NETWORK", "1")
    from pipeline import geo_overlay as go
    from pipeline.geo import get_geo
    g = get_geo()
    for iso in ("RUS", "USA", "CHN"):
        v = g.view_for([iso], [])
        assert go._fills_width(g, iso, v["S"], v["K"]), iso
    v = g.view_for(["BHR"], [])
    assert not go._fills_width(g, "BHR", v["S"], v["K"])
