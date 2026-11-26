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

# Re-exported so `pipeline.llm_providers.<name>` keeps working.
from .llm_providers_more import (  # noqa: E402,F401
    DeepSeekProvider,
    GeminiProvider,
    OpenAICompatibleProvider,
)

# Re-exported so `pipeline.llm_providers.<name>` keeps working.
from .llm_providers_free import (  # noqa: E402,F401
    FreeLLMAPIProvider,
)
