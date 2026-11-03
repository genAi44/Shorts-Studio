"""استدعاء DeepSeek (الإخراج الفني والستايل) وGemini (كتابة السكربت، تدقيق الحقائق، والتعبئة)."""
import json
import re

import requests

from .config import cfg


class LLMError(Exception):
    pass


def _sanitize(text):
    if not isinstance(text, str):
        text = str(text)
    for k in ("GEMINI_API_KEY", "DEEPSEEK_API_KEY", "ELEVENLABS_API_KEY", "PEXELS_API_KEY"):
        val = cfg(k)
        if val and len(val) >= 4:
            text = text.replace(val, "[REDACTED]")
    return text


def extract_json(text):
    text = (text or "").strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.I)
    try:
        return json.loads(text)
    except Exception:
        a, b = text.find("{"), text.rfind("}")
        if a >= 0 and b > a:
            try:
                return json.loads(text[a:b + 1])
            except Exception:
                pass
    raise LLMError("لم يعد النموذج JSON صالحاً. أعد المحاولة.")


def _parse_with_repair(raw, repair_fn, max_retries=2):
    """يحاول تحليل JSON؛ عند الفشل يطلب من النموذج إصلاحه (حتى max_retries مرة)."""
    for attempt in range(max_retries + 1):
        try:
            return extract_json(raw)
        except LLMError:
            if attempt == max_retries:
                raise
            raw = repair_fn(raw)


def _post(url, headers, payload, timeout=120):
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=timeout)
    except requests.RequestException as e:
        raise LLMError(_sanitize(f"تعذّر الاتصال: {e}"))
    if r.status_code >= 300:
        raise LLMError(_sanitize(f"خطأ {r.status_code} من الخدمة: {r.text[:300]}"))
    try:
        return r.json()
    except Exception:
        raise LLMError("ردّ غير مفهوم من الخدمة.")


def deepseek_json(system, user, temperature=0.8):
    key = cfg("DEEPSEEK_API_KEY")
    if not key:
        raise LLMError("مفتاح DEEPSEEK_API_KEY غير مضبوط في ملف .env")
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
        raise LLMError("ردّ DeepSeek بلا محتوى.")

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
            raise LLMError("ردّ DeepSeek بلا محتوى في الإصلاح.")

    return _parse_with_repair(raw, repair)


def gemini_json(system, user, grounding=None, temperature=0.2):
    key = cfg("GEMINI_API_KEY")
    if not key:
        raise LLMError("مفتاح GEMINI_API_KEY غير مضبوط في ملف .env")
    if grounding is None:
        grounding = cfg("GEMINI_GROUNDING", "1") not in ("0", "false", "no")
    model = cfg("GEMINI_MODEL", "gemini-2.5-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    headers = {"x-goog-api-key": key, "Content-Type": "application/json"}
    base = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
    }

    def call(use_ground):
        p = json.loads(json.dumps(base))
        if use_ground:
            p["tools"] = [{"google_search": {}}]
            p["generationConfig"] = {"temperature": temperature}
        else:
            p["generationConfig"] = {"temperature": temperature, "responseMimeType": "application/json"}
        return _post(url, headers, p, timeout=150)

    try:
        data = call(grounding)
    except LLMError:
        if not grounding:
            raise
        data = call(False)  # بعض النماذج/الحسابات لا تدعم البحث المرتبط
    try:
        parts = data["candidates"][0]["content"]["parts"]
        raw = "".join(p.get("text", "") for p in parts)
    except (KeyError, IndexError):
        raise LLMError("ردّ Gemini بلا محتوى (ربما حجبه فلتر الأمان).")

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
            raise LLMError("ردّ Gemini بلا محتوى في الإصلاح.")

    return _parse_with_repair(raw, repair)


def gemini_vision_json(system, user, images):
    """images: قائمة (bytes JPEG). تُرسل مرقّمة بالترتيب ويُطلب JSON."""
    import base64
    key = cfg("GEMINI_API_KEY")
    if not key:
        raise LLMError("مفتاح GEMINI_API_KEY غير مضبوط في ملف .env")
    model = cfg("GEMINI_MODEL", "gemini-2.5-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    parts = [{"text": user}]
    for i, im in enumerate(images):
        parts.append({"text": f"Image {i}:"})
        parts.append({"inlineData": {"mimeType": "image/jpeg", "data": base64.b64encode(im).decode()}})
    data = _post(url, {"x-goog-api-key": key, "Content-Type": "application/json"},
                 {"systemInstruction": {"parts": [{"text": system}]}, "contents": [{"role": "user", "parts": parts}],
                  "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"}}, timeout=150)
    try:
        raw = "".join(p.get("text", "") for p in data["candidates"][0]["content"]["parts"])
    except (KeyError, IndexError):
        raise LLMError("ردّ Gemini بلا محتوى.")

    def repair(bad):
        fix = _post(url, {"x-goog-api-key": key, "Content-Type": "application/json"},
                    {"systemInstruction": {"parts": [{"text": system}]},
                     "contents": [{"role": "user", "parts": parts},
                                  {"role": "model", "parts": [{"text": bad}]},
                                  {"role": "user", "parts": [{"text": "الرد ليس JSON صالحاً. أعده كـ JSON فقط."}]}],
                     "generationConfig": {"temperature": 0.0, "responseMimeType": "application/json"}},
                    timeout=150)
        try:
            return "".join(p.get("text", "") for p in fix["candidates"][0]["content"]["parts"])
        except (KeyError, IndexError):
            raise LLMError("ردّ Gemini بلا محتوى في الإصلاح.")

    return _parse_with_repair(raw, repair)
