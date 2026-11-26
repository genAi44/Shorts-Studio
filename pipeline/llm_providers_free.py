"""Split from `pipeline/llm_providers.py` (re-exported there); see that module."""
from typing import Any, Dict, List, Optional
from .config import cfg
import requests
import time
from .llm_providers import BaseLLMProvider, LLMError, LLMResponse, LLMUsage, extract_json, logger, sanitize_text  # noqa: E402


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
