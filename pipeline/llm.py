"""استدعاء نماذج الذكاء الاصطناعي بنظام المزوّدين الموحد مع التبديل التلقائي (Fallback).
يدعم FreeLLMAPI و DeepSeek و Gemini و OpenAI-compatible مع التخصيص الكامل لكل دور.
"""
import base64
import logging
from typing import Any, Dict, List, Optional

import requests

from .config import cfg
from .llm_providers import (
    LLMError,
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


def _shrink_jpeg(data: bytes, max_side: int = 448, quality: int = 70) -> bytes:
    import io
    from PIL import Image
    try:
        im = Image.open(io.BytesIO(data)).convert("RGB")
        im.thumbnail((max_side, max_side))
        out = io.BytesIO()
        im.save(out, "JPEG", quality=quality)
        return out.getvalue()
    except Exception:  # noqa: BLE001 - send the original bytes rather than nothing
        return data


def freellmapi_vision_json(system: str, user: str, images: List[bytes]) -> Any:
    """Vision through FreeLLMAPI (model "auto" routes to a vision-capable free model): the free alternative to Gemini Vision."""
    from .llm_providers import FreeLLMAPIProvider
    prov = FreeLLMAPIProvider()
    if not prov.is_configured():
        raise LLMError("FreeLLMAPI غير مضبوط (FREELLMAPI_API_KEY / FREELLMAPI_BASE_URL)", provider="freellmapi")
    parts: List[Dict[str, Any]] = [{"type": "text", "text": user}]
    # free routed models reject / time out on big multi-image payloads: 4 images, <= 448 px, JPEG q70 is enough to recognise a place
    for i, im in enumerate(images[:4]):
        parts.append({"type": "text", "text": f"Image {i}:"})
        parts.append({"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + base64.b64encode(_shrink_jpeg(im)).decode()}})
    messages = [{"role": "system", "content": system}, {"role": "user", "content": parts}]

    def call(msgs):
        data = _post(f"{prov.base_url}/chat/completions", {"Authorization": f"Bearer {prov.api_key}", "Content-Type": "application/json"},
                     {"model": "auto", "temperature": 0.1, "messages": msgs}, timeout=150)
        try:
            return data["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError):
            raise LLMError("ردّ FreeLLMAPI Vision بلا محتوى.", provider="freellmapi")

    raw = call(messages)
    return _parse_with_repair(raw, lambda bad: call(messages + [{"role": "assistant", "content": bad},
                                                                {"role": "user", "content": "الرد ليس JSON صالحاً. أعده كـ JSON فقط."}]))


def vision_providers() -> List[str]:
    """Providers to try for picture verification, in order. PHOTO_VERIFY = auto (default: Gemini, then FreeLLMAPI) |
    gemini | freellmapi | off (the verification gate is disabled: the best heuristic candidate is accepted)."""
    mode = (cfg("PHOTO_VERIFY", "auto") or "auto").strip().lower()
    if mode == "off":
        return []
    from .llm_providers import FreeLLMAPIProvider
    gem = ["gemini"] if cfg("GEMINI_API_KEY") else []
    free = ["freellmapi"] if FreeLLMAPIProvider().is_configured() else []
    if mode == "gemini":
        return gem
    if mode == "freellmapi":
        return free
    return gem + free


def vision_json(system: str, user: str, images: List[bytes]) -> Any:
    """Picture verification with provider fallback: a 429 from Gemini no longer means 'no photo'."""
    errors = []
    for prov in vision_providers():
        try:
            fn = gemini_vision_json if prov == "gemini" else freellmapi_vision_json
            return fn(system, user, images)
        except Exception as e:  # noqa: BLE001 - try the next provider, the last error is raised
            errors.append(f"{prov}: {str(e)[:80]}")
            logger.warning("vision provider %s failed: %s", prov, e)
    raise LLMError("لا مزوّد رؤية متاح — " + " | ".join(errors) if errors else "التحقق بالرؤية معطّل", provider="vision")


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

