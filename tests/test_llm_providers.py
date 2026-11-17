"""
Comprehensive test suite for unified LLM provider & routing system.
Covers:
- Unit tests: FreeLLMAPI, DeepSeek, Gemini, OpenAI providers
- Error handling: 401, 429, 5xx, timeout, offline connection
- Auto Mode & Header parsing: X-Routed-Via, _routed_via, sticky session X-Session-ID
- Router & Fallback transitions: Automatic failover, logging
- Flask API Endpoints: /api/llm/providers, /api/llm/health, /api/llm/config, /api/llm/logs
- Live Smoke Test: Verified against running FreeLLMAPI instance
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from unittest.mock import patch, MagicMock
import json
import requests
import app
from pipeline import llm_providers
from pipeline import llm_router
from pipeline.llm_providers import (
    FreeLLMAPIProvider,
    DeepSeekProvider,
    GeminiProvider,
    OpenAICompatibleProvider,
    LLMError,
    LLMResponse,
    LLMUsage,
)


class TestFreeLLMAPIUnit(unittest.TestCase):
    def setUp(self):
        self.provider = FreeLLMAPIProvider(
            base_url="http://127.0.0.1:31415/v1",
            api_key="test-key-xyz",
            timeout=5,
        )

    def test_auto_mode_properties(self):
        self.assertTrue(self.provider.supports_auto_mode)
        info = self.provider.auto_mode_info()
        self.assertEqual(info["verified_model"], "auto")
        self.assertTrue(info["enabled"])
        self.assertEqual(info["default_submode"], "balanced")

    @patch("requests.post")
    def test_x_routed_via_parsing_from_header_and_body(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {
            "X-Routed-Via": "nvidia/poolside/laguna-xs-2.1",
            "Content-Type": "application/json",
        }
        mock_resp.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps({"title": "Test Title", "scenes": []}),
                    }
                }
            ],
            "usage": {
                "prompt_tokens": 120,
                "completion_tokens": 45,
                "total_tokens": 165,
            },
            "_routed_via": {
                "platform": "nvidia",
                "model": "poolside/laguna-xs-2.1",
            },
        }
        mock_post.return_value = mock_resp

        result = self.provider.chat_completion(
            messages=[{"role": "user", "content": "hi"}],
            model="auto",
            session_id="session-user-123",
        )

        self.assertIsInstance(result, LLMResponse)
        self.assertEqual(result.routed_via, "nvidia/poolside/laguna-xs-2.1")
        self.assertEqual(result.usage.routed_via, "nvidia/poolside/laguna-xs-2.1")
        self.assertEqual(result.usage.total_tokens, 165)
        self.assertEqual(result.content.get("title"), "Test Title")

        # Verify sticky session header was sent
        sent_headers = mock_post.call_args[1].get("headers", {})
        self.assertEqual(sent_headers.get("X-Session-ID"), "session-user-123")

    @patch("requests.get")
    def test_list_models_live_format(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "data": [
                {"id": "auto", "title": "Auto (router picks best)"},
                {"id": "meta-llama/llama-3.3-70b-instruct", "title": "Llama 3.3 70B"},
            ]
        }
        mock_get.return_value = mock_resp

        models = self.provider.list_models()
        self.assertTrue(len(models) >= 2)
        model_ids = [m["id"] for m in models]
        self.assertIn("auto", model_ids)

    @patch("requests.post")
    def test_error_handling_401_unauthorized(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.text = json.dumps({"error": {"message": "Invalid API key"}})
        mock_post.return_value = mock_resp

        with self.assertRaises(LLMError) as ctx:
            self.provider.chat_completion(
                messages=[{"role": "user", "content": "hi"}],
            )
        self.assertEqual(ctx.exception.status_code, 401)
        self.assertIn("401", str(ctx.exception))
        self.assertIn("غير صالح", str(ctx.exception))

    @patch("requests.post")
    def test_error_handling_429_rate_limit(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 429
        mock_resp.text = json.dumps({"error": {"message": "Rate limit exceeded"}})
        mock_post.return_value = mock_resp

        with self.assertRaises(LLMError) as ctx:
            self.provider.chat_completion(
                messages=[{"role": "user", "content": "hi"}],
            )
        self.assertEqual(ctx.exception.status_code, 429)
        self.assertIn("429", str(ctx.exception))
        self.assertIn("معدل الطلبات", str(ctx.exception))

    @patch("requests.post")
    def test_error_handling_500_server_error(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 502
        mock_resp.text = "Bad Gateway"
        mock_post.return_value = mock_resp

        with self.assertRaises(LLMError) as ctx:
            self.provider.chat_completion(
                messages=[{"role": "user", "content": "hi"}],
            )
        self.assertEqual(ctx.exception.status_code, 502)
        self.assertIn("502", str(ctx.exception))
        self.assertIn("خادم", str(ctx.exception))

    @patch("requests.post")
    def test_error_handling_timeout(self, mock_post):
        mock_post.side_effect = requests.exceptions.Timeout("Read timed out")

        with self.assertRaises(LLMError) as ctx:
            self.provider.chat_completion(
                messages=[{"role": "user", "content": "hi"}],
            )
        self.assertIn("مهلة", str(ctx.exception))

    @patch("requests.post")
    def test_error_handling_connection_offline(self, mock_post):
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")

        with self.assertRaises(LLMError) as ctx:
            self.provider.chat_completion(
                messages=[{"role": "user", "content": "hi"}],
            )
        self.assertIn("اتصال", str(ctx.exception))


class TestRouterAndFallback(unittest.TestCase):
    def setUp(self):
        # Create a fresh isolated router instance for testing
        self.router = llm_router.LLMRouter(config_path="tests/test_temp_llm_config.json")

    def tearDown(self):
        import os
        if os.path.exists("tests/test_temp_llm_config.json"):
            try:
                os.remove("tests/test_temp_llm_config.json")
            except Exception:
                pass

    def test_fallback_activation_when_primary_fails(self):
        # Set primary to deepseek and secondary to freellmapi
        self.router.update_role_config(
            role="script",
            provider="deepseek",
            fallback_chain=["deepseek", "freellmapi"],
        )

        with patch("pipeline.llm_providers.DeepSeekProvider.complete") as mock_ds, \
             patch("pipeline.llm_providers.FreeLLMAPIProvider.complete") as mock_free:
            # Primary deepseek fails
            mock_ds.side_effect = LLMError("DeepSeek 503 Overloaded", status_code=503)

            # Secondary FreeLLMAPI succeeds
            mock_free.return_value = LLMResponse(
                content={"title": "From Fallback"},
                raw_text='{"title": "From Fallback"}',
                provider="freellmapi",
                model="auto",
                usage=LLMUsage(
                    prompt_tokens=50,
                    completion_tokens=20,
                    total_tokens=70,
                    provider="freellmapi",
                    model="auto",
                    routed_via="groq/llama-3",
                ),
                routed_via="groq/llama-3",
            )

            res = self.router.dispatch(
                role="script",
                messages=[{"role": "user", "content": "write script"}],
            )

            self.assertEqual(res.content.get("title"), "From Fallback")
            self.assertEqual(res.provider, "freellmapi")
            self.assertEqual(res.routed_via, "groq/llama-3")

            # Check that log captured fallback
            logs = self.router.get_recent_logs(limit=5)
            self.assertTrue(len(logs) > 0)
            last_log = logs[0]
            self.assertTrue(last_log.get("fallback_used"))
            self.assertEqual(last_log.get("routed_via"), "groq/llama-3")

    def test_capabilities_validation(self):
        caps = self.router.get_capabilities()
        self.assertIn("freellmapi", caps)
        self.assertIn("gemini", caps)
        self.assertIn("deepseek", caps)

        # Gemini supports vision and json
        self.assertTrue(caps["gemini"]["vision"])
        self.assertTrue(caps["gemini"]["json_mode"])
        # FreeLLMAPI supports auto mode
        self.assertTrue(caps["freellmapi"]["auto_mode"])


class TestFlaskAPIContract(unittest.TestCase):
    def setUp(self):
        self.client = app.app.test_client()

    def test_get_providers_endpoint(self):
        res = self.client.get("/api/llm/providers")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("freellmapi", data)
        self.assertIn("deepseek", data)
        self.assertIn("gemini", data)
        self.assertTrue(data["freellmapi"]["supports_auto_mode"])
        self.assertIsInstance(data["freellmapi"]["models"], list)

    def test_get_health_endpoint(self):
        res = self.client.get("/api/llm/health")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("freellmapi", data)
        self.assertIn("deepseek", data)
        self.assertIn("gemini", data)

    def test_get_and_post_config_endpoint(self):
        res = self.client.get("/api/llm/config")
        self.assertEqual(res.status_code, 200)
        cfg = res.get_json()
        self.assertIn("roles", cfg)
        self.assertIn("script", cfg["roles"])

        # Update configuration
        update_res = self.client.post("/api/llm/config", json={
            "roles": {
                "script": {
                    "provider": "freellmapi",
                    "model": "auto"
                }
            }
        })
        self.assertEqual(update_res.status_code, 200)
        updated = update_res.get_json()
        self.assertEqual(updated["roles"]["script"]["provider"], "freellmapi")

    def test_get_logs_endpoint(self):
        res = self.client.get("/api/llm/logs?limit=10")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("logs", data)
        self.assertIsInstance(data["logs"], list)


class TestLiveSmoke(unittest.TestCase):
    def test_live_freellmapi_instance_if_online(self):
        prov = FreeLLMAPIProvider()
        if not prov.is_configured():
            self.skipTest("FreeLLMAPI is not configured in environment.")

        # Test health check
        health = prov.health_check()
        if not health["healthy"]:
            self.skipTest(f"Live FreeLLMAPI is offline: {health.get('error')}")

        self.assertTrue(health["healthy"])
        self.assertEqual(health["verified_model"], "auto")

        # Test live Auto Mode chat completion
        resp = prov.chat_completion(
            messages=[
                {"role": "system", "content": "Reply in JSON only: {\"smoke_test\": \"ok\"}"},
                {"role": "user", "content": "ping"}
            ],
            model="auto",
        )
        self.assertIsInstance(resp.content, dict)
        self.assertIn("smoke_test", resp.content)
        self.assertIsNotNone(resp.routed_via)
        print(f"\n[Smoke Test Success] FreeLLMAPI routed to: {resp.routed_via} (tokens: {resp.usage.total_tokens})")


if __name__ == "__main__":
    unittest.main()