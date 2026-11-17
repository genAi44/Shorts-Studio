"""نظام مزوّدي نماذج الذكاء الاصطناعي (LLM Providers System).
يوفر بنية موحدة ومرنة لإدارة والتواصل مع مختلف المزوّدين (FreeLLMAPI, DeepSeek, Gemini, OpenAI).
"""
import json
import logging
import re
import time
from typing import Any, Dict, List, Optional

import requests

from .config import cfg

logger = logging.getLogger("llm_providers")


class LLMError(Exception):
    """خطأ عام في استدعاءات نماذج الذكاء الاصطناعي مع تصنيف كود الحالة."""
    def __init__(self, message: str, status_code: Optional[int] = None, provider: str = "", model: str = ""):
        super().__init__(message)
        self.status_code = status_code
        self.provider = provider
        self.model = model


class LLMUsage:
    def __init__(
        self,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_tokens: int = 0,
        latency_ms: int = 0,
        routed_via: Optional[str] = None,
        cost_usd: Optional[float] = None,
        provider: str = "",
        model: str = "",
    ):
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = total_tokens or (prompt_tokens + completion_tokens)
        self.latency_ms = latency_ms
        self.routed_via = routed_via
        self.cost_usd = cost_usd
        self.provider = provider
        self.model = model

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "latency_ms": self.latency_ms,
            "routed_via": self.routed_via,
            "cost_usd": self.cost_usd,
            "provider": self.provider,
            "model": self.model,
        }


class LLMResponse:
    def __init__(
        self,
        content: Any,
        raw_text: str,
        provider: str,
        model: str,
        usage: LLMUsage,
        session_id: Optional[str] = None,
        routed_via: Optional[str] = None,
    ):
        self.content = content
        self.raw_text = raw_text
        self.provider = provider
        self.model = model
        self.usage = usage
        self.session_id = session_id
        self.routed_via = routed_via or (usage.routed_via if usage else None)


def sanitize_text(text: Any) -> str:
    """إخفاء المفاتيح السرية من النصوص وسجلات الأخطاء."""
    s = str(text) if text is not None else ""
    for k in (
        "GEMINI_API_KEY", "DEEPSEEK_API_KEY", "ELEVENLABS_API_KEY",
        "PEXELS_API_KEY", "FREELLMAPI_API_KEY", "OPENAI_API_KEY"
    ):
        val = cfg(k)
        if val and len(val) >= 4:
            s = s.replace(val, "[REDACTED]")
    return s


def extract_json(text: str) -> Any:
    """استخراج كائن JSON من النص وتنظيف وسوم الماركداون والتفكير والفواصل الزائدة."""
    t = (text or "").strip()
    t = re.sub(r"<think>.*?</think>", "", t, flags=re.S | re.I).strip()
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", t, flags=re.I).strip()

    def _try_parse(candidate: str) -> Any:
        try:
            return json.loads(candidate)
        except Exception:
            cleaned = re.sub(r",\s*([}\]])", r"\1", candidate)
            return json.loads(cleaned)

    try:
        return _try_parse(t)
    except Exception:
        a, b = t.find("{"), t.rfind("}")
        if a >= 0 and b > a:
            try:
                return _try_parse(t[a:b + 1])
            except Exception:
                pass
        arr_a, arr_b = t.find("["), t.rfind("]")
        if arr_a >= 0 and arr_b > arr_a:
            try:
                return _try_parse(t[arr_a:arr_b + 1])
            except Exception:
                pass
    raise LLMError("لم يعد النموذج JSON صالحاً.", provider="extractor")


class BaseLLMProvider:
    id: str = "base"
    name: str = "Base Provider"
    supports_auto_mode: bool = False

    def is_configured(self) -> bool:
        raise NotImplementedError

    def health_check(self) -> Dict[str, Any]:
        raise NotImplementedError

    def list_models(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def auto_mode_info(self) -> Optional[Dict[str, Any]]:
        return None

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
        raise NotImplementedError

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        system: str = "",
        model: Optional[str] = None,
        temperature: float = 0.7,
        json_mode: bool = True,
        session_id: Optional[str] = None,
        timeout: int = 120,
    ) -> LLMResponse:
        return self.complete(
            messages=messages,
            system=system,
            model=model,
            temperature=temperature,
            json_mode=json_mode,
            session_id=session_id,
            timeout=timeout,
        )

    def validate_capability(self, model: str, capability: str) -> bool:
        """التحقق من دعم النموذج لقدرات معينة مثل json أو tools أو vision."""
        return True


class FreeLLMAPIProvider(BaseLLMProvider):
    id = "freellmapi"
    name = "FreeLLMAPI (Unified Router)"
    supports_auto_mode = True

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = 120,
    ):
        self._cached_models: Optional[List[Dict[str, Any]]] = None
        self._cache_time: float = 0
        self._override_base_url = base_url
        self._override_api_key = api_key
        self._default_timeout = timeout

    @property
    def base_url(self) -> str:
        if self._override_base_url:
            url = self._override_base_url.rstrip("/")
        else:
            url = cfg("FREELLMAPI_BASE_URL", "http://127.0.0.1:31415/v1").rstrip("/")
        if not url.endswith("/v1"):
            url = url + "/v1" if not url.endswith("/v1/") else url.rstrip("/")
        return url

    @property
    def api_key(self) -> str:
        if self._override_api_key is not None:
            return self._override_api_key
        return cfg("FREELLMAPI_API_KEY", "")

    def is_configured(self) -> bool:
        return bool(self.api_key and self.base_url)

    def health_check(self) -> Dict[str, Any]:
        if not self.is_configured():
            return {
                "status": "unconfigured",
                "healthy": False,
                "latency_ms": 0,
                "error": "مفتاح FREELLMAPI_API_KEY أو الرابط غير مضبوط في .env",
                "models_count": 0,
                "auto_mode": False,
            }
        t0 = time.time()
        try:
            url = f"{self.base_url}/models"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            r = requests.get(url, headers=headers, timeout=10)
            latency = int((time.time() - t0) * 1000)
            if r.status_code == 200:
                data = r.json()
                models = data.get("data", [])
                self._cached_models = models
                self._cache_time = time.time()
                return {
                    "status": "healthy",
                    "healthy": True,
                    "latency_ms": latency,
                    "error": None,
                    "models_count": len(models),
                    "auto_mode": True,
                    "verified_model": "auto",
                }
            elif r.status_code == 401:
                return {
                    "status": "unauthorized",
                    "healthy": False,
                    "latency_ms": latency,
                    "error": "مفتاح FreeLLMAPI غير صالح أو منتهي الصلاحية (HTTP 401)",
                    "models_count": 0,
                    "auto_mode": False,
                }
            elif r.status_code == 429:
                return {
                    "status": "rate_limited",
                    "healthy": False,
                    "latency_ms": latency,
                    "error": "تجاوز معدل الطلبات في FreeLLMAPI (HTTP 429 Rate Limit)",
                    "models_count": 0,
                    "auto_mode": False,
                }
            else:
                return {
                    "status": "unhealthy",
                    "healthy": False,
                    "latency_ms": latency,
                    "error": f"خطأ من خادم FreeLLMAPI (HTTP {r.status_code}): {r.text[:120]}",
                    "models_count": 0,
                    "auto_mode": False,
                }
        except requests.exceptions.Timeout:
            return {
                "status": "timeout",
                "healthy": False,
                "latency_ms": int((time.time() - t0) * 1000),
                "error": "انتهت مهلة الاتصال بخادم FreeLLMAPI المحلي (Timeout)",
                "models_count": 0,
                "auto_mode": False,
            }
        except requests.exceptions.RequestException as e:
            return {
                "status": "offline",
                "healthy": False,
                "latency_ms": int((time.time() - t0) * 1000),
                "error": f"تعذر الاتصال بخادم FreeLLMAPI ({e.__class__.__name__})",
                "models_count": 0,
                "auto_mode": False,
            }

    def list_models(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        now = time.time()
        if not force_refresh and self._cached_models and (now - self._cache_time < 300):
            return self._cached_models
        if not self.is_configured():
            return [{"id": "auto", "name": "Auto (Router default)", "available": True}]
        try:
            url = f"{self.base_url}/models"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code == 200:
                models = r.json().get("data", [])
                self._cached_models = models
                self._cache_time = now
                return models
        except Exception as e:
            logger.warning("فشل جلب النماذج من FreeLLMAPI: %s", e)
        return self._cached_models or [{"id": "auto", "name": "Auto (Router default)", "available": True}]

    def auto_mode_info(self) -> Dict[str, Any]:
        models = self.list_models()
        model_ids = [m.get("id") for m in models if isinstance(m, dict)]
        modes = ["auto"]
        if "fusion" in model_ids:
            modes.append("fusion")
        return {
            "enabled": True,
            "status": "نشط (Auto Mode)",
            "selected_model": "auto",
            "verified_model": "auto",
            "default_submode": "balanced",
            "available_modes": modes,
            "supports_balanced": True,
            "supports_smart": "fusion" in modes or "claude-opus-4-5" in model_ids,
            "description": "توجيه تلقائي ذكي لأفضل نموذج متاح مجاناً مع التبديل التلقائي عند الضغط",
        }

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
            raise LLMError("مفتاح FREELLMAPI_API_KEY غير مضبوط في .env", provider=self.id)

        target_model = "auto"
        payload_messages = []
        if system:
            payload_messages.append({"role": "system", "content": system})
        payload_messages.extend(messages)

        payload: Dict[str, Any] = {
            "model": target_model,
            "messages": payload_messages,
            "temperature": temperature,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if session_id:
            headers["X-Session-ID"] = str(session_id)
            headers["x-session-id"] = str(session_id)

        url = f"{self.base_url}/chat/completions"
        t0 = time.time()
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=timeout)
        except requests.exceptions.Timeout:
            raise LLMError(
                f"انتهت مهلة الطلب إلى FreeLLMAPI ({timeout} ثانية)",
                status_code=504,
                provider=self.id,
                model=target_model,
            )
        except requests.exceptions.RequestException as e:
            raise LLMError(
                sanitize_text(f"خطأ اتصال بخادم FreeLLMAPI: {e}"),
                status_code=502,
                provider=self.id,
                model=target_model,
            )

        latency = int((time.time() - t0) * 1000)

        if r.status_code == 401:
            raise LLMError("مفتاح FreeLLMAPI غير صالح (HTTP 401 Unauthorized)", status_code=401, provider=self.id)
        elif r.status_code == 429:
            raise LLMError("تجاوز معدل الطلبات في FreeLLMAPI (HTTP 429 Rate Limit)", status_code=429, provider=self.id)
        elif r.status_code >= 500:
            raise LLMError(
                f"خطأ في خادم FreeLLMAPI أو المزوّد الخلفي (HTTP {r.status_code}): {r.text[:200]}",
                status_code=r.status_code,
                provider=self.id,
            )
        elif r.status_code >= 300:
            raise LLMError(
                sanitize_text(f"خطأ {r.status_code} من FreeLLMAPI: {r.text[:200]}"),
                status_code=r.status_code,
                provider=self.id,
            )

        try:
            data = r.json()
        except Exception:
            raise LLMError("رد غير صالح من FreeLLMAPI (ليس JSON).", provider=self.id)

        routed_via = (
            r.headers.get("x-routed-via")
            or r.headers.get("X-Routed-Via")
            or (data.get("_routed_via", {}).get("model") if isinstance(data.get("_routed_via"), dict) else None)
        )
        if isinstance(data.get("_routed_via"), dict) and not routed_via:
            rv = data["_routed_via"]
            routed_via = f"{rv.get('platform', '')}/{rv.get('model', '')}".strip("/")

        choices = data.get("choices") or []
        if not choices:
            raise LLMError("رد FreeLLMAPI لا يحتوي على أي خيارات أو محتوى.", provider=self.id)

        raw_text = choices[0].get("message", {}).get("content", "")
        usage_data = data.get("usage") or {}
        usage = LLMUsage(
            prompt_tokens=usage_data.get("prompt_tokens", 0),
            completion_tokens=usage_data.get("completion_tokens", 0),
            total_tokens=usage_data.get("total_tokens", 0),
            latency_ms=latency,
            routed_via=routed_via,
            cost_usd=0.0,
            provider=self.id,
            model=data.get("model") or target_model,
        )

        content = extract_json(raw_text) if json_mode else raw_text
        return LLMResponse(
            content=content,
            raw_text=raw_text,
            provider=self.id,
            model=data.get("model") or target_model,
            usage=usage,
            session_id=session_id,
        )


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


_PROVIDERS: Dict[str, BaseLLMProvider] = {}


def get_all_providers() -> Dict[str, BaseLLMProvider]:
    global _PROVIDERS
    if not _PROVIDERS:
        _PROVIDERS = {
            "freellmapi": FreeLLMAPIProvider(),
            "deepseek": DeepSeekProvider(),
            "gemini": GeminiProvider(),
            "openai": OpenAICompatibleProvider(),
        }
    return _PROVIDERS


def get_provider(provider_id: str) -> BaseLLMProvider:
    all_p = get_all_providers()
    if provider_id not in all_p:
        raise LLMError(f"المزوّد '{provider_id}' غير مدعوم أو غير مسجل.", provider=provider_id)
    return all_p[provider_id]