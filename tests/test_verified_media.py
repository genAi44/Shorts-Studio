"""Phase 2 — Verified Geo-Media Engine + Entity Cache regression tests."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from pipeline import direct, media


class TestVerifiedGeoMedia(unittest.TestCase):
    def test_geo_verify_accepts_inside_bbox_and_rejects_outside_bbox(self):
        # Panama City coords (~8.98, -79.52) vs Swiss engraving (~47.37, 8.54)
        pan_cand = {"lat": 8.98, "lon": -79.52, "title": "Panama Canal", "source": "Wikimedia Commons"}
        swiss_cand = {"lat": 47.37, "lon": 8.54, "title": "S. Mauritius (Merian)", "source": "Wikimedia Commons"}

        st_ok, d_ok = media._geo_verify_candidate(pan_cand, "PAN", "Panama")
        st_bad, d_bad = media._geo_verify_candidate(swiss_cand, "MUS", "Mauritius")

        self.assertEqual(st_ok, "verified")
        self.assertGreater(d_ok, 0)
        self.assertEqual(st_bad, "mismatch")
        self.assertLess(d_bad, -50)

    def test_pick_rejects_mismatched_gps_and_weak_fallback_on_429(self):
        swiss_cand = {
            "url": "https://example.com/swiss.jpg",
            "thumb": "https://example.com/swiss_t.jpg",
            "title": "S. Mauritius engraving",
            "source": "Wikimedia Commons",
            "lat": 47.37,
            "lon": 8.54,
        }
        generic_pexels = {
            "url": "https://example.com/generic.jpg",
            "thumb": "https://example.com/generic_t.jpg",
            "title": "Historic stone street",
            "source": "Pexels",
        }
        with patch.object(media, "cfg", return_value="fake-key"), \
             patch.object(media, "fetch_image", side_effect=RuntimeError("429 Too Many Requests")):
            c, score, _ = media.pick(
                [swiss_cand, generic_pexels],
                "Mauritius landmark",
                "موريشيوس جزيرة جميلة",
                entity_iso3="MUS",
                entity_country_en="Mauritius",
            )
            self.assertIsNone(c)
            self.assertEqual(score, 0)

    def test_photo_to_text_falls_back_to_map_when_entity_iso3_present(self):
        fb = direct.photo_to_text(
            {"kind": "photo", "entity_iso3": "PAN", "entity_name_ar": "بنما"},
            sentence="بنما دولة في أمريكا الوسطى",
        )
        self.assertEqual(fb["kind"], "map")
        self.assertEqual(fb["countries"], ["PAN"])

    def test_entity_media_cache_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache_root = Path(tmp) / "cache"
            dest_dir = Path(tmp) / "out"
            img = Image.new("RGB", (64, 64), (10, 20, 30))
            cand = {
                "url": "https://example.com/panama_canal.jpg",
                "thumb": "https://example.com/panama_canal.jpg",
                "title": "Panama Canal",
                "credit": "Test",
                "license": "CC BY",
                "source": "Wikipedia",
                "page": "https://example.com",
            }
            with patch.object(media, "CACHE", cache_root), \
                 patch.object(media, "find", return_value=[cand]), \
                 patch.object(media, "pick", return_value=(cand, 9, "ok")), \
                 patch.object(media, "fetch_image", return_value=img):
                m1 = media.Media(str(dest_dir))
                res1 = m1.resolve({"kind": "photo", "query": "Panama Canal", "entity_iso3": "PAN"}, "قناة بنما")
                self.assertEqual(res1["img"], "media/p1.jpg")
                self.assertTrue((cache_root / "entity_media" / "PAN").exists())

            # Second run when online pick fails -> loads from entity cache!
            with patch.object(media, "CACHE", cache_root), \
                 patch.object(media, "find", return_value=[]), \
                 patch.object(media, "pick", return_value=(None, 0, "429")):
                m2 = media.Media(str(dest_dir))
                res2 = m2.resolve({"kind": "photo", "query": "Panama Canal", "entity_iso3": "PAN"}, "قناة بنما")
                self.assertEqual(res2["img"], "media/p1.jpg")
                self.assertIn("كاش الكيان", m2.reports[-1]["reason"])


if __name__ == "__main__":
    unittest.main()
