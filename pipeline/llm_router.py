"""نظام التوجيه والتحويل التلقائي (LLM Router & Fallback Manager).
يدير تعيين النماذج والمزوّدين لكل دور (Script, Director, Style, Factcheck, Chat Edit)
مع دعم التحويل الاحتياطي الذكي (Fallback)، الجلسات الثابتة (Sticky Sessions)، وتسجيل الإحصائيات.
"""
import copy
import json
import logging
from pathlib import Path
import time
from typing import Any, Dict, List, Optional

from .config import ROOT, cfg
from .llm_providers import (
    LLMError,
    LLMResponse,
    get_all_providers,
    get_provider,
    sanitize_text,
)

logger = logging.getLogger("llm_router")

ROLES = ["script", "director", "style", "factcheck", "chat_edit", "illustrator"]
CONFIG_FILE = ROOT / "pipeline" / "llm_config.json"


DEFAULT_ROLES_CONFIG: Dict[str, Dict[str, Any]] = {
    "script": {
        "provider": cfg("SCRIPT_PROVIDER", "freellmapi"),
        "model": cfg("SCRIPT_MODEL", "auto"),
        "fallback_chain": ["freellmapi", "gemini", "deepseek"],
        "temperature": 0.4,
    },
    "director": {
        "provider": cfg("DIRECTOR_PROVIDER", "freellmapi"),
        "model": cfg("DIRECTOR_MODEL", "auto"),
        "fallback_chain": ["freellmapi", "deepseek", "gemini"],
        "temperature": 0.7,
    },
    "style": {
        "provider": cfg("STYLE_PROVIDER", "freellmapi"),
        "model": cfg("STYLE_MODEL", "auto"),
        "fallback_chain": ["freellmapi", "deepseek", "gemini"],
        "temperature": 0.8,
    },
    "factcheck": {
        "provider": cfg("FACTCHECK_PROVIDER", "gemini"),
        "model": cfg("FACTCHECK_MODEL", "gemini-2.5-flash"),
        "fallback_chain": ["gemini", "freellmapi", "deepseek"],
        "temperature": 0.2,
    },
    # studio illustrator: writes the bespoke SVG drawing of each scene (code quality matters: a fixed, strong model)
    "illustrator": {
        "provider": cfg("ILLUSTRATOR_PROVIDER", "deepseek"),
        "model": cfg("ILLUSTRATOR_MODEL", "deepseek-chat"),
        "fallback_chain": ["deepseek", "gemini", "freellmapi"],
        "temperature": 0.6,
    },
    "chat_edit": {
        "provider": cfg("CHAT_EDIT_PROVIDER", "freellmapi"),
        "model": cfg("CHAT_EDIT_MODEL", "auto"),
        "fallback_chain": ["freellmapi", "deepseek", "gemini"],
        "temperature": 0.5,
    },
}


class LLMRouter:
    def __init__(self, config_path: Optional[Any] = None):
        self._config_file = Path(config_path) if config_path else CONFIG_FILE
        self._roles_config: Dict[str, Dict[str, Any]] = copy.deepcopy(DEFAULT_ROLES_CONFIG)
        self._execution_logs: List[Dict[str, Any]] = []
        self._active_sessions: Dict[str, Dict[str, Any]] = {}
        self._load_config()

    def _load_config(self):
        if self._config_file.exists():
            try:
                data = json.loads(self._config_file.read_text(encoding="utf-8"))
                for role, conf in data.items():
                    if role in self._roles_config and isinstance(conf, dict):
                        self._roles_config[role].update(conf)
            except Exception as e:
                logger.warning("تعذّر قراءة ملف إعدادات النماذج %s: %s", self._config_file, e)

    def save_config(self):
        try:
            self._config_file.write_text(json.dumps(self._roles_config, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            logger.error("تعذّر حفظ إعدادات النماذج: %s", e)

    def get_role_config(self, role: str) -> Dict[str, Any]:
        return copy.deepcopy(self._roles_config.get(role, self._roles_config["script"]))

    def get_all_role_configs(self) -> Dict[str, Dict[str, Any]]:
        return copy.deepcopy(self._roles_config)

    def update_role_config(self, role: str, provider: str, model: Optional[str] = None, fallback_chain: Optional[List[str]] = None):
        if role not in self._roles_config:
            raise LLMError(f"الدور '{role}' غير معروف. الأدوار المدعومة: {ROLES}")
        all_provs = get_all_providers()
        if provider not in all_provs:
            raise LLMError(f"المزوّد '{provider}' غير مدعوم.")

        # إذا كان المزوّد هو FreeLLMAPI، يتم تفعيل Auto Mode دائماً
        if provider == "freellmapi":
            model = "auto"

        self._roles_config[role]["provider"] = provider
        if model:
            self._roles_config[role]["model"] = model
        if fallback_chain:
            self._roles_config[role]["fallback_chain"] = [p for p in fallback_chain if p in all_provs]
        self.save_config()

    def get_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        return list(reversed(self._execution_logs[-limit:]))

    def get_recent_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self.get_logs(limit=limit)

    def get_or_create_session(self, session_id: str) -> Dict[str, Any]:
        if session_id not in self._active_sessions:
            self._active_sessions[session_id] = {
                "id": session_id,
                "created_at": time.time(),
                "last_active": time.time(),
                "calls_count": 0,
            }
        else:
            self._active_sessions[session_id]["last_active"] = time.time()
        return self._active_sessions[session_id]

    def _record_log(
        self,
        role: str,
        requested_provider: str,
        requested_model: str,
        actual_provider: str,
        actual_model: str,
        routed_via: Optional[str],
        tokens: Dict[str, int],
        latency_ms: int,
        status: str,
        fallback_used: bool,
        error: Optional[str] = None,
        session_id: Optional[str] = None,
    ):
        entry = {
            "id": len(self._execution_logs) + 1,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "role": role,
            "requested_provider": requested_provider,
            "requested_model": requested_model,
            "actual_provider": actual_provider,
            "actual_model": actual_model,
            "routed_via": routed_via,
            "prompt_tokens": tokens.get("prompt_tokens", 0),
            "completion_tokens": tokens.get("completion_tokens", 0),
            "total_tokens": tokens.get("total_tokens", 0),
            "latency_ms": latency_ms,
            "status": status,
            "fallback_used": fallback_used,
            "error": error,
            "session_id": session_id,
        }
        self._execution_logs.append(entry)
        if len(self._execution_logs) > 200:
            self._execution_logs = self._execution_logs[-150:]

    def get_capabilities(self) -> Dict[str, Dict[str, Any]]:
        """قدرات المزوّدين المسجلين (Auto Mode، JSON، Vision)."""
        caps = {}
        for pid, prov in get_all_providers().items():
            caps[pid] = {
                "auto_mode": getattr(prov, "supports_auto_mode", False),
                "json_mode": True,
                "vision": (pid == "gemini"),
                "configured": prov.is_configured(),
            }
        return caps

    def dispatch(
        self,
        role: str,
        system: str = "",
        user: str = "",
        messages: Optional[List[Dict[str, str]]] = None,
        temperature: Optional[float] = None,
        json_mode: bool = True,
        session_id: Optional[str] = None,
        timeout: int = 120,
    ) -> LLMResponse:
        """إرسال الطلب إلى المزوّد المعين للدور المحدد، مع التبديل التلقائي الاحتياطي (Fallback) عند الفشل."""
        if messages is not None and not user:
            for m in messages:
                if m.get("role") == "system" and not system:
                    system = m.get("content", "")
                elif m.get("role") == "user":
                    user = m.get("content", "")
        conf = self.get_role_config(role)
        primary_provider_id = conf.get("provider", "freellmapi")
        primary_model = conf.get("model", "auto")
        temp = temperature if temperature is not None else conf.get("temperature", 0.7)
        fallback_chain = conf.get("fallback_chain", ["freellmapi", "gemini", "deepseek"])

        # ترتيب المزوّدين للبدء بالمزوّد الأساسي ثم الاحتياطيين
        providers_to_try = [primary_provider_id] + [p for p in fallback_chain if p != primary_provider_id]

        messages = [{"role": "user", "content": user}]
        attempt_errors = []

        if session_id:
            self.get_or_create_session(session_id)["calls_count"] += 1

        for idx, prov_id in enumerate(providers_to_try):
            try:
                provider = get_provider(prov_id)
            except Exception as e:
                attempt_errors.append(f"{prov_id}: {e}")
                continue

            if not provider.is_configured():
                attempt_errors.append(f"{prov_id}: غير مضبوط (مفتاح API ناقص)")
                continue

            # اختيار النموذج للمزوّد الحالي
            target_model = primary_model if prov_id == primary_provider_id else None
            if prov_id == "freellmapi":
                target_model = "auto"

            t0 = time.time()
            try:
                resp = provider.complete(
                    messages=messages,
                    system=system,
                    model=target_model,
                    temperature=temp,
                    json_mode=json_mode,
                    session_id=session_id,
                    timeout=timeout,
                )
                latency = int((time.time() - t0) * 1000)
                fallback_used = prov_id != primary_provider_id

                self._record_log(
                    role=role,
                    requested_provider=primary_provider_id,
                    requested_model=primary_model,
                    actual_provider=prov_id,
                    actual_model=resp.model,
                    routed_via=resp.usage.routed_via,
                    tokens={
                        "prompt_tokens": resp.usage.prompt_tokens,
                        "completion_tokens": resp.usage.completion_tokens,
                        "total_tokens": resp.usage.total_tokens,
                    },
                    latency_ms=latency,
                    status="success",
                    fallback_used=fallback_used,
                    session_id=session_id,
                )
                return resp

            except LLMError as le:
                latency = int((time.time() - t0) * 1000)
                err_msg = str(le)
                logger.warning(
                    "[LLM Fallback] الدور '%s' فشل لدى المزوّد '%s' (النموذج: %s): %s",
                    role,
                    prov_id,
                    target_model,
                    err_msg,
                )
                attempt_errors.append(f"{prov_id} ({le.status_code or 'error'}): {err_msg}")
                self._record_log(
                    role=role,
                    requested_provider=primary_provider_id,
                    requested_model=primary_model,
                    actual_provider=prov_id,
                    actual_model=target_model or "",
                    routed_via=None,
                    tokens={},
                    latency_ms=latency,
                    status="failed",
                    fallback_used=prov_id != primary_provider_id,
                    error=err_msg,
                    session_id=session_id,
                )
            except Exception as ge:
                latency = int((time.time() - t0) * 1000)
                err_msg = sanitize_text(str(ge))
                logger.error("[LLM Exception] خطأ غير متوقع لدى المزوّد '%s': %s", prov_id, err_msg)
                attempt_errors.append(f"{prov_id}: {err_msg}")
                self._record_log(
                    role=role,
                    requested_provider=primary_provider_id,
                    requested_model=primary_model,
                    actual_provider=prov_id,
                    actual_model=target_model or "",
                    routed_via=None,
                    tokens={},
                    latency_ms=latency,
                    status="error",
                    fallback_used=prov_id != primary_provider_id,
                    error=err_msg,
                    session_id=session_id,
                )

        # إذا فشلت جميع المحاولات
        summary_err = " | ".join(attempt_errors)
        raise LLMError(
            f"فشلت جميع محاولات المزوّدين للدور '{role}'. التفاصيل: {summary_err}",
            provider=primary_provider_id,
        )


_ROUTER: Optional[LLMRouter] = None


def get_router() -> LLMRouter:
    global _ROUTER
    if _ROUTER is None:
        _ROUTER = LLMRouter()
    return _ROUTER