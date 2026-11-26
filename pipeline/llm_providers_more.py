"""Split from `pipeline/llm_providers.py` (re-exported there); see that module."""
from typing import Any, Dict, List, Optional
from .config import cfg
import requests
import time
from .llm_providers import BaseLLMProvider, LLMError, LLMResponse, LLMUsage, extract_json, sanitize_text  # noqa: E402


class DeepSeekProvider(BaseLLMProvider):
    id = "deepseek"
    name = "DeepSeek AI"
    supports_auto_mode = False

    def __init__(self):
        self._cached_models: Optional[List[Dict[str, Any]]] = None
        self._cache_time: float = 0

    @property
    def base_url(self) -> str:
        return cfg("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")

    @property
    def api_key(self) -> str:
        return cfg("DEEPSEEK_API_KEY", "")

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def health_check(self) -> Dict[str, Any]:
        if not self.is_configured():
            return {
                "status": "unconfigured",
                "healthy": False,
                "latency_ms": 0,
                "error": "مفتاح DEEPSEEK_API_KEY غير مضبوط في .env",
                "models_count": 0,
            }
        t0 = time.time()
        try:
            url = f"{self.base_url}/models"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            r = requests.get(url, headers=headers, timeout=10)
            latency = int((time.time() - t0) * 1000)
            if r.status_code == 200:
                models = r.json().get("data", [])
                self._cached_models = models
                self._cache_time = time.time()
                return {
                    "status": "healthy",
                    "healthy": True,
                    "latency_ms": latency,
                    "error": None,
                    "models_count": len(models),
                }
            return {
                "status": "unhealthy",
                "healthy": False,
                "latency_ms": latency,
                "error": f"HTTP {r.status_code}: {r.text[:120]}",
                "models_count": 0,
            }
        except Exception as e:
            return {
                "status": "offline",
                "healthy": False,
                "latency_ms": int((time.time() - t0) * 1000),
                "error": sanitize_text(str(e)),
                "models_count": 0,
            }

    def list_models(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        now = time.time()
        if not force_refresh and self._cached_models and (now - self._cache_time < 600):
            return self._cached_models
        base_models = [
            {"id": "deepseek-chat", "name": "deepseek-chat (V3 Fast)"},
            {"id": "deepseek-reasoner", "name": "deepseek-reasoner (R1)"},
        ]
        if not self.is_configured():
            return base_models
        try:
            url = f"{self.base_url}/models"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            r = requests.get(url, headers=headers, timeout=12)
            if r.status_code == 200:
                models = r.json().get("data", [])
                seen = {m.get("id") for m in models if isinstance(m, dict)}
                merged = [bm for bm in base_models if bm["id"] not in seen] + models
                self._cached_models = merged
                self._cache_time = now
                return merged
        except Exception:
            pass
        return self._cached_models or base_models

    def complete(
        self,
        messages: List[Dict[str, str]],
        system: str = "",
        model: Optional[str] = None,
        temperature: float = 0.7,
        json_mode: bool = True,
        session_id: Optional[str] = None,
        timeout: int = 120,
    ) -> LLMResponse:
        if not self.is_configured():
            raise LLMError("مفتاح DEEPSEEK_API_KEY غير مضبوط في .env", provider=self.id)

        chosen_model = model or cfg("DEEPSEEK_MODEL", "deepseek-chat")
        payload_messages = []
        if system:
            payload_messages.append({"role": "system", "content": system})
        payload_messages.extend(messages)

        payload: Dict[str, Any] = {
            "model": chosen_model,
            "messages": payload_messages,
            "temperature": temperature,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        url = f"{self.base_url}/chat/completions"
        t0 = time.time()
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=timeout)
        except Exception as e:
            raise LLMError(sanitize_text(f"فشل الاتصال بـ DeepSeek: {e}"), provider=self.id, model=chosen_model)

        latency = int((time.time() - t0) * 1000)
        if r.status_code >= 300:
            raise LLMError(
                sanitize_text(f"خطأ {r.status_code} من DeepSeek: {r.text[:200]}"),
                status_code=r.status_code,
                provider=self.id,
                model=chosen_model,
            )

        data = r.json()
        raw_text = data["choices"][0]["message"]["content"]
        usage_data = data.get("usage") or {}
        usage = LLMUsage(
            prompt_tokens=usage_data.get("prompt_tokens", 0),
            completion_tokens=usage_data.get("completion_tokens", 0),
            total_tokens=usage_data.get("total_tokens", 0),
            latency_ms=latency,
            provider=self.id,
            model=chosen_model,
        )
        content = extract_json(raw_text) if json_mode else raw_text
        return LLMResponse(content=content, raw_text=raw_text, provider=self.id, model=chosen_model, usage=usage, session_id=session_id)


class GeminiProvider(BaseLLMProvider):
    id = "gemini"
    name = "Google Gemini"
    supports_auto_mode = False

    def __init__(self):
        self._cached_models: Optional[List[Dict[str, Any]]] = None
        self._cache_time: float = 0

    @property
    def api_key(self) -> str:
        return cfg("GEMINI_API_KEY", "")

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def health_check(self) -> Dict[str, Any]:
        if not self.is_configured():
            return {
                "status": "unconfigured",
                "healthy": False,
                "latency_ms": 0,
                "error": "مفتاح GEMINI_API_KEY غير مضبوط في .env",
                "models_count": 0,
            }
        t0 = time.time()
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={self.api_key}"
            r = requests.get(url, timeout=10)
            latency = int((time.time() - t0) * 1000)
            if r.status_code == 200:
                raw_models = r.json().get("models", [])
                models = [
                    {"id": m.get("name", "").replace("models/", ""), "name": m.get("displayName", "")}
                    for m in raw_models
                ]
                self._cached_models = models
                self._cache_time = time.time()
                return {
                    "status": "healthy",
                    "healthy": True,
                    "latency_ms": latency,
                    "error": None,
                    "models_count": len(models),
                }
            return {
                "status": "unhealthy",
                "healthy": False,
                "latency_ms": latency,
                "error": f"HTTP {r.status_code}: {r.text[:120]}",
                "models_count": 0,
            }
        except Exception as e:
            return {
                "status": "offline",
                "healthy": False,
                "latency_ms": int((time.time() - t0) * 1000),
                "error": sanitize_text(str(e)),
                "models_count": 0,
            }

    def list_models(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        now = time.time()
        if not force_refresh and self._cached_models and (now - self._cache_time < 600):
            return self._cached_models
        if not self.is_configured():
            return [{"id": "gemini-2.5-flash", "name": "Gemini 2.5 Flash"}]
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={self.api_key}"
            r = requests.get(url, timeout=12)
            if r.status_code == 200:
                raw_models = r.json().get("models", [])
                models = [
                    {
                        "id": m.get("name", "").replace("models/", ""),
                        "name": m.get("displayName", m.get("name", "")),
                        "supportedGenerationMethods": m.get("supportedGenerationMethods", []),
                    }
                    for m in raw_models
                    if "generateContent" in m.get("supportedGenerationMethods", [])
                ]
                self._cached_models = models
                self._cache_time = now
                return models
        except Exception:
            pass
        return self._cached_models or [
            {"id": "gemini-2.5-flash", "name": "Gemini 2.5 Flash"},
            {"id": "gemini-2.5-pro", "name": "Gemini 2.5 Pro"},
        ]

    def complete(
        self,
        messages: List[Dict[str, str]],
        system: str = "",
        model: Optional[str] = None,
        temperature: float = 0.2,
        json_mode: bool = True,
        session_id: Optional[str] = None,
        timeout: int = 150,
    ) -> LLMResponse:
        if not self.is_configured():
            raise LLMError("مفتاح GEMINI_API_KEY غير مضبوط في .env", provider=self.id)

        chosen_model = model or cfg("GEMINI_MODEL", "gemini-2.5-flash")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{chosen_model}:generateContent"
        headers = {"x-goog-api-key": self.api_key, "Content-Type": "application/json"}

        contents = []
        for m in messages:
            role = "model" if m.get("role") == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": m.get("content", "")}]})

        base_payload: Dict[str, Any] = {"contents": contents}
        if system:
            base_payload["systemInstruction"] = {"parts": [{"text": system}]}

        gen_config: Dict[str, Any] = {"temperature": temperature}
        if json_mode:
            gen_config["responseMimeType"] = "application/json"
        base_payload["generationConfig"] = gen_config

        t0 = time.time()
        try:
            r = requests.post(url, headers=headers, json=base_payload, timeout=timeout)
        except Exception as e:
            raise LLMError(sanitize_text(f"فشل الاتصال بـ Gemini: {e}"), provider=self.id, model=chosen_model)

        latency = int((time.time() - t0) * 1000)
        if r.status_code >= 300:
            raise LLMError(
                sanitize_text(f"خطأ {r.status_code} من Gemini: {r.text[:200]}"),
                status_code=r.status_code,
                provider=self.id,
                model=chosen_model,
            )

        data = r.json()
        try:
            parts = data["candidates"][0]["content"]["parts"]
            raw_text = "".join(p.get("text", "") for p in parts)
        except (KeyError, IndexError):
            raise LLMError("رد Gemini بلا محتوى أو حُجب بفلتر الأمان.", provider=self.id, model=chosen_model)

        meta = data.get("usageMetadata") or {}
        usage = LLMUsage(
            prompt_tokens=meta.get("promptTokenCount", 0),
            completion_tokens=meta.get("candidatesTokenCount", 0),
            total_tokens=meta.get("totalTokenCount", 0),
            latency_ms=latency,
            provider=self.id,
            model=chosen_model,
        )
        content = extract_json(raw_text) if json_mode else raw_text
        return LLMResponse(content=content, raw_text=raw_text, provider=self.id, model=chosen_model, usage=usage, session_id=session_id)


class OpenAICompatibleProvider(BaseLLMProvider):
    id = "openai"
    name = "OpenAI-Compatible (Custom)"
    supports_auto_mode = False

    def __init__(self, provider_id: str = "openai", name: str = "OpenAI Compatible", base_url: str = "", api_key: str = ""):
        self.id = provider_id
        self.name = name
        self._custom_base_url = base_url
        self._custom_api_key = api_key
        self._cached_models: Optional[List[Dict[str, Any]]] = None
        self._cache_time: float = 0

    @property
    def base_url(self) -> str:
        return self._custom_base_url or cfg("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")

    @property
    def api_key(self) -> str:
        return self._custom_api_key or cfg("OPENAI_API_KEY", "")

    def is_configured(self) -> bool:
        return bool(self.api_key and self.base_url)

    def health_check(self) -> Dict[str, Any]:
        if not self.is_configured():
            return {
                "status": "unconfigured",
                "healthy": False,
                "latency_ms": 0,
                "error": "المفتاح أو الرابط غير مضبوط في .env",
                "models_count": 0,
            }
        t0 = time.time()
        try:
            url = f"{self.base_url}/models"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            r = requests.get(url, headers=headers, timeout=10)
            latency = int((time.time() - t0) * 1000)
            if r.status_code == 200:
                models = r.json().get("data", [])
                self._cached_models = models
                self._cache_time = time.time()
                return {"status": "healthy", "healthy": True, "latency_ms": latency, "models_count": len(models)}
            return {"status": "unhealthy", "healthy": False, "latency_ms": latency, "error": f"HTTP {r.status_code}"}
        except Exception as e:
            return {"status": "offline", "healthy": False, "latency_ms": int((time.time() - t0) * 1000), "error": str(e)}

    def list_models(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        now = time.time()
        if not force_refresh and self._cached_models and (now - self._cache_time < 600):
            return self._cached_models
        if not self.is_configured():
            return [{"id": "gpt-4o", "name": "gpt-4o"}]
        try:
            url = f"{self.base_url}/models"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            r = requests.get(url, headers=headers, timeout=12)
            if r.status_code == 200:
                models = r.json().get("data", [])
                self._cached_models = models
                self._cache_time = now
                return models
        except Exception:
            pass
        return self._cached_models or [{"id": "gpt-4o", "name": "gpt-4o"}, {"id": "gpt-4o-mini", "name": "gpt-4o-mini"}]

    def complete(
        self,
        messages: List[Dict[str, str]],
        system: str = "",
        model: Optional[str] = None,
        temperature: float = 0.7,
        json_mode: bool = True,
        session_id: Optional[str] = None,
        timeout: int = 120,
    ) -> LLMResponse:
        if not self.is_configured():
            raise LLMError("المفتاح غير مضبوط للمزوّد.", provider=self.id)
        chosen_model = model or "gpt-4o"
        payload_messages = []
        if system:
            payload_messages.append({"role": "system", "content": system})
        payload_messages.extend(messages)
        payload = {"model": chosen_model, "messages": payload_messages, "temperature": temperature}
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        if session_id:
            headers["X-Session-ID"] = str(session_id)
        url = f"{self.base_url}/chat/completions"
        t0 = time.time()
        r = requests.post(url, headers=headers, json=payload, timeout=timeout)
        latency = int((time.time() - t0) * 1000)
        if r.status_code >= 300:
            raise LLMError(f"HTTP {r.status_code}: {r.text[:200]}", status_code=r.status_code, provider=self.id)
        data = r.json()
        raw_text = data["choices"][0]["message"]["content"]
        usage_data = data.get("usage") or {}
        usage = LLMUsage(
            prompt_tokens=usage_data.get("prompt_tokens", 0),
            completion_tokens=usage_data.get("completion_tokens", 0),
            total_tokens=usage_data.get("total_tokens", 0),
            latency_ms=latency,
            provider=self.id,
            model=chosen_model,
        )
        content = extract_json(raw_text) if json_mode else raw_text
        return LLMResponse(content=content, raw_text=raw_text, provider=self.id, model=chosen_model, usage=usage, session_id=session_id)
