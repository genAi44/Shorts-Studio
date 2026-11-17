"""استدعاء نماذج الذكاء الاصطناعي بنظام المزوّدين الموحد مع التبديل التلقائي (Fallback).
يدعم FreeLLMAPI و DeepSeek و Gemini و OpenAI-compatible مع التخصيص الكامل لكل دور.
"""
import base64
import json
import logging
import re
from typing import Any, List, Optional

import requests

from .config import cfg
from .llm_providers import (
    LLMError,
    LLMResponse,
    LLMUsage,
    extract_json,
    sanitize_text as _sanitize,
)
from .llm_router import get_router

logger = logging.getLogger("pipeline.llm")


def call_llm_json(
    role: str,
    system: str,
    user: str,
    temperature: Optional[float] = None,
    session_id: Optional[str] = None,
    timeout: int = 120,
) -> Any:
    """استدعاء موحد لأي دور (script, director, style, factcheck, chat_edit) مع التحويل الاحتياطي."""
    router = get_router()
    resp = router.dispatch(
        role=role,
        system=system,
        user=user,
        temperature=temperature,
        json_mode=True,
        session_id=session_id,
        timeout=timeout,
    )
    return resp.content


def _parse_with_repair(raw: str, repair_fn, max_retries: int = 2) -> Any:
    """يحاول تحليل JSON؛ عند الفشل يطلب من النموذج إصلاحه."""
    for attempt in range(max_retries + 1):
        try:
            return extract_json(raw)
        except LLMError:
            if attempt == max_retries:
                raise
            raw = repair_fn(raw)


def _post(url: str, headers: dict, payload: dict, timeout: int = 120) -> dict:
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=timeout)
    except requests.RequestException as e:
        raise LLMError(_sanitize(f"تعذّر الاتصال: {e}"))
    if r.status_code >= 300:
        raise LLMError(_sanitize(f"خطأ {r.status_code} من الخدمة: {r.text[:300]}"), status_code=r.status_code)
    try:
        return r.json()
    except Exception:
        raise LLMError("ردّ غير مفهوم من الخدمة.")


def deepseek_json(system: str, user: str, temperature: float = 0.8, session_id: Optional[str] = None) -> Any:
    """دالة التوافقية السابقة لـ DeepSeek؛ تستخدم الموجه الذكي مع Fallback."""
    try:
        return call_llm_json("director", system, user, temperature=temperature, session_id=session_id)
    except Exception as e:
        logger.warning("فشل الموجه الذكي لدور director، تجربة استدعاء DeepSeek المباشر: %s", e)

    key = cfg("DEEPSEEK_API_KEY")
    if not key:
        raise LLMError("مفتاح DEEPSEEK_API_KEY غير مضبوط في ملف .env", provider="deepseek")
    base = cfg("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")
    url = base + "/chat/completions"
    hdrs = {"Authorization": "Bearer " + key, "Content-Type": "application/json"}
    model = cfg("DEEPSEEK_MODEL", "deepseek-chat")
    data = _post(url, hdrs, {
        "model": model,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "response_format": {"type": "json_object"},
        "temperature": temperature,
    })
    try:
        raw = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        raise LLMError("ردّ DeepSeek بلا محتوى.", provider="deepseek")

    def repair(bad):
        r = _post(url, hdrs, {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
                {"role": "assistant", "content": bad},
                {"role": "user", "content": "الرد ليس JSON صالحاً. أعده كـ JSON فقط بلا نص إضافي."},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.0,
        })
        try:
            return r["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            raise LLMError("ردّ DeepSeek بلا محتوى في الإصلاح.", provider="deepseek")

    return _parse_with_repair(raw, repair)


def gemini_json(system: str, user: str, grounding: Optional[bool] = None, temperature: float = 0.2, session_id: Optional[str] = None) -> Any:
    """دالة التوافقية السابقة لـ Gemini؛ تستخدم الموجه الذكي مع Fallback."""
    key = cfg("GEMINI_API_KEY")
    grounding_val = grounding if grounding is not None else (cfg("GEMINI_GROUNDING", "1") not in ("0", "false", "no"))

    if not grounding_val or not key:
        try:
            return call_llm_json("script", system, user, temperature=temperature, session_id=session_id)
        except Exception as e:
            logger.warning("فشل الموجه الذكي لدور script، تجربة استدعاء Gemini المباشر: %s", e)

    if not key:
        return call_llm_json("script", system, user, temperature=temperature, session_id=session_id)

    model = cfg("GEMINI_MODEL", "gemini-2.5-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    headers = {"x-goog-api-key": key, "Content-Type": "application/json"}
    base_body = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
    }

    def call(use_ground):
        p = json.loads(json.dumps(base_body))
        if use_ground:
            p["tools"] = [{"google_search": {}}]
            p["generationConfig"] = {"temperature": temperature}
        else:
            p["generationConfig"] = {"temperature": temperature, "responseMimeType": "application/json"}
        return _post(url, headers, p, timeout=150)

    try:
        data = call(grounding_val)
    except LLMError:
        if not grounding_val:
            raise
        data = call(False)
    try:
        parts = data["candidates"][0]["content"]["parts"]
        raw = "".join(p.get("text", "") for p in parts)
    except (KeyError, IndexError):
        raise LLMError("ردّ Gemini بلا محتوى (ربما حجبه فلتر الأمان).", provider="gemini")

    def repair(bad):
        p = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [
                {"role": "user", "parts": [{"text": user}]},
                {"role": "model", "parts": [{"text": bad}]},
                {"role": "user", "parts": [{"text": "الرد ليس JSON صالحاً. أعده كـ JSON فقط."}]},
            ],
            "generationConfig": {"temperature": 0.0, "responseMimeType": "application/json"},
        }
        r = _post(url, headers, p, timeout=150)
        try:
            return "".join(x.get("text", "") for x in r["candidates"][0]["content"]["parts"])
        except (KeyError, IndexError):
            raise LLMError("ردّ Gemini بلا محتوى في الإصلاح.", provider="gemini")

    return _parse_with_repair(raw, repair)


def gemini_vision_json(system: str, user: str, images: List[bytes]) -> Any:
    """استدعاء الرؤية الحاسوبية لاختيار الصور (Gemini Vision)."""
    key = cfg("GEMINI_API_KEY")
    if not key:
        raise LLMError("مفتاح GEMINI_API_KEY غير مضبوط في ملف .env لاختيار الصور بالرؤية الحاسوبية", provider="gemini")
    model = cfg("GEMINI_MODEL", "gemini-2.5-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    parts: List[Dict[str, Any]] = [{"text": user}]
    for i, im in enumerate(images):
        parts.append({"text": f"Image {i}:"})
        parts.append({"inlineData": {"mimeType": "image/jpeg", "data": base64.b64encode(im).decode()}})
    data = _post(
        url,
        {"x-goog-api-key": key, "Content-Type": "application/json"},
        {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": parts}],
            "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"},
        },
        timeout=150,
    )
    try:
        raw = "".join(p.get("text", "") for p in data["candidates"][0]["content"]["parts"])
    except (KeyError, IndexError):
        raise LLMError("ردّ Gemini Vision بلا محتوى.", provider="gemini")

    def repair(bad):
        fix = _post(
            url,
            {"x-goog-api-key": key, "Content-Type": "application/json"},
            {
                "systemInstruction": {"parts": [{"text": system}]},
                "contents": [
                    {"role": "user", "parts": parts},
                    {"role": "model", "parts": [{"text": bad}]},
                    {"role": "user", "parts": [{"text": "الرد ليس JSON صالحاً. أعده كـ JSON فقط."}]},
                ],
                "generationConfig": {"temperature": 0.0, "responseMimeType": "application/json"},
            },
            timeout=150,
        )
        try:
            return "".join(p.get("text", "") for p in fix["candidates"][0]["content"]["parts"])
        except (KeyError, IndexError):
            raise LLMError("ردّ Gemini Vision بلا محتوى في الإصلاح.", provider="gemini")

    return _parse_with_repair(raw, repair)


def write_script_with_facts(topic: str, facts_text: str, style: Optional[Any] = None) -> dict:
    """كتابة سكربت فيديو قصير معتمد كلياً على الحقائق الموثقة المجلوبة من الويب دون هلوسة."""
    from . import scriptspec as sp

    system = (
        "You are writing a script for an engaging, highly informative Arabic Shorts video.\n"
        "Strict rules:\n"
        "1. When the topic asks for a specific count (e.g. '5 دول', '5 عواصم', 'أفضل 5'), you MUST mention ALL 5 items across the 3 body sections. Distribute them cleanly:\n"
        "   - In BODY 1: cover items 1 and 2.\n"
        "   - In BODY 2: cover items 3 and 4.\n"
        "   - In BODY 3: cover item 5 (the ultimate climax/answer).\n"
        "   Never stop at only 2 or 3 items when 5 were requested!\n"
        "2. For each capital/country, explicitly mention both the City Name and the Country Name.\n"
        "3. Use ONLY the facts provided below and verified, authentic facts. Do not invent fake numbers or dates.\n"
        "4. Write in concise, punchy Arabic phrases optimized for vertical fast-paced video.\n\n"
        + sp.SYSTEM
    )

    user_message = f"الحقائق الموثقة من الويب (Facts):\n{facts_text}\n\nفكرة وموضوع الفيديو (Topic):\n{topic}"
    if style:
        style_name = style.get("name", "") if isinstance(style, dict) else str(style)
        if style_name:
            user_message += f"\nالأسلوب والنمط المعتمد: {style_name}"

    raw = call_llm_json("script", system, user_message, temperature=0.7)
    script = sp.normalize(raw)

    # التحقق من سلامة الأجزاء وإصلاحها إن لزم
    try:
        from .geo import get_geo
        geo = get_geo()
        errors = sp.script_errors(script, geo)
        if errors:
            repair_prompt = (
                f"الحقائق الموثقة (Facts):\n{facts_text}\n\n"
                "السكربت يحتوي على بعض الملاحظات الهيكلية:\n"
                + "\n".join(f"- {e}" for e in errors)
                + f"\n\nالسكربت الحالي:\n{sp.dumps(script)}\n"
                "أعد JSON فقط بالمفاتيح الثمانية الصالحة مع الالتزام التام بالحقائق المرفقة."
            )
            fixed_raw = call_llm_json("script", system, repair_prompt, temperature=0.2)
            script = sp.normalize(fixed_raw)
    except Exception as e:
        logger.debug("تخطي إعادة التحقق من الأخطاء: %s", e)

    return script

