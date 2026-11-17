import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.geo import detect_city_in_text
from pipeline.geo_overlay import extract_timed_geo_mentions
from pipeline.scriptspec import normalize
from pipeline.search import _search_wikipedia


class TestPhase4GeoAndScript(unittest.TestCase):
    def test_yawman_does_not_match_yuma(self):
        text = "هل تساءلت يومًا ما هي أجمل مدينة على وجه الأرض؟ خمس مدن تتنافس على اللقب!"
        city, info = detect_city_in_text(text)
        self.assertIsNone(city)
        self.assertIsNone(info)

        mentions = extract_timed_geo_mentions(text, "", [], 180)
        self.assertEqual(mentions, [])

    def test_normalize_strips_stray_cyrillic_and_cjk(self):
        raw = {
            "title": "كيوتو",
            "hook": {"narration": "هل تعلم ما هي أجمل مدينة؟", "on_screen": "أجمل مدينة"},
            "body2": {"narration": "تضم أكثر من ألف وستةсот معبد بوذي", "on_screen": "1600 معبد"},
        }
        norm = normalize(raw)
        self.assertNotIn("сот", norm["body2"]["narration"])
        self.assertIn("وستة", norm["body2"]["narration"])

    @patch("pipeline.search._query_wiki_endpoint", return_value=[])
    def test_arabic_wiki_query_does_not_fallback_to_en_wikipedia(self, mock_query):
        res = _search_wikipedia("أجمل مدن العالم", max_results=3)
        self.assertEqual(res, [])
        self.assertEqual(mock_query.call_count, 1)
        self.assertEqual(mock_query.call_args.kwargs.get("lang"), "ar")


if __name__ == "__main__":
    unittest.main()
