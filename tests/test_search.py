import json
import os
import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.search import (
    _cache_path,
    _get_cached,
    _set_cached,
    generate_queries,
    search_facts,
    search_query,
)
from pipeline.llm import write_script_with_facts


class TestSearchFacts(unittest.TestCase):
    def test_generate_queries(self):
        queries = generate_queries("عاصمة مصر", n=3)
        self.assertGreaterEqual(len(queries), 2)
        self.assertLessEqual(len(queries), 3)
        self.assertTrue(any("مصر" in q for q in queries))

    def test_cache_mechanism(self):
        query = "اختبار الكاش التجريبي 123"
        fake_results = [{"title": "عنوان", "snippet": "نص", "url": "https://example.com/1"}]
        _set_cached(query, fake_results)

        cached = _get_cached(query, ttl=86400)
        self.assertEqual(cached, fake_results)

        # TTL expired should return None
        expired = _get_cached(query, ttl=-1)
        self.assertIsNone(expired)

    @patch("pipeline.search._get_cached", return_value=None)
    @patch("pipeline.search._set_cached")
    @patch("pipeline.search._search_ddg")
    @patch("pipeline.search._search_serper")
    @patch("pipeline.search._search_wikipedia")
    def test_search_facts_waterfall_and_dedup(self, mock_wiki, mock_serper, mock_ddg, mock_set_cache, mock_get_cache):
        # DDG returns empty
        mock_ddg.return_value = []
        # Serper returns empty
        mock_serper.return_value = []
        # Wiki returns duplicated URLs across queries
        mock_wiki.return_value = [
            {"title": "القاهرة", "snippet": "عاصمة مصر وأكبر مدنها", "url": "https://ar.wikipedia.org/wiki/Cairo"},
            {"title": "القاهرة", "snippet": "عاصمة مصر وأكبر مدنها", "url": "https://ar.wikipedia.org/wiki/Cairo#section"},
        ]

        res = search_facts("عاصمة مصر", n_queries=2)
        self.assertIn("facts", res)
        self.assertIn("sources", res)
        self.assertEqual(len(res["sources"]), 1)  # deduplicated
        self.assertIn("القاهرة", res["facts"])

    @patch("pipeline.search._get_cached", return_value=None)
    @patch("pipeline.search._search_ddg", return_value=[])
    @patch("pipeline.search._search_serper", return_value=[])
    @patch("pipeline.search._search_wikipedia", return_value=[])
    def test_all_backends_fail_does_not_block(self, mock_wiki, mock_serper, mock_ddg, mock_get_cache):
        res = search_facts("سؤال غير موجود إطلاقاً 99999", n_queries=2)
        self.assertEqual(res["facts"], "")
        self.assertEqual(res["sources"], [])
        self.assertEqual(res["count"], 0)

    @patch("pipeline.llm.call_llm_json")
    def test_write_script_with_facts(self, mock_call):
        mock_call.return_value = {
            "title": "عنوان اختباري",
            "hook": {"narration": "سؤال صادم عن التاريخ؟", "on_screen": "سؤال", "visual": {"type": "text"}},
            "lead": {"narration": "سياق مشوق يوضح البداية.", "on_screen": "سياق", "visual": {"type": "text"}},
            "body1": {"narration": "حقيقة أولى من القائمة الموثقة.", "on_screen": "حقيقة 1", "visual": {"type": "text"}},
            "open_loop1": {"narration": "ولكن ما السر غير المتوقع؟", "on_screen": "سر", "visual": {"type": "text"}},
            "body2": {"narration": "حقيقة ثانية من القائمة الموثقة.", "on_screen": "حقيقة 2", "visual": {"type": "text"}},
            "open_loop2": {"narration": "وكيف تجلت النتيجة المذهلة؟", "on_screen": "نتيجة", "visual": {"type": "text"}},
            "body3": {"narration": "حقيقة ثالثة تحسم اللغز كلياً.", "on_screen": "حقيقة 3", "visual": {"type": "text"}},
            "cta": {"narration": "شاركنا برأيك في التعليقات وتابعنا للمزيد.", "on_screen": "شاركنا", "visual": {"type": "text"}},
        }
        facts = "• القاهرة: تأسست عام 969 م على يد جوهر الصقلي (المصدر: https://ar.wikipedia.org/wiki/Cairo)"
        script = write_script_with_facts("تاريخ القاهرة", facts)
        self.assertIn("hook", script)
        self.assertIn("cta", script)
        # Verify system prompt contained the rule
        args, kwargs = mock_call.call_args
        role, system, user = args[0], args[1], args[2]
        self.assertIn("Use ONLY the facts provided below", system)
        self.assertIn(facts, user)


if __name__ == "__main__":
    unittest.main()
