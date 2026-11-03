"""الصوت: ElevenLabs مع توقيت الكلمات."""
import base64
import re
import subprocess

import requests

from .config import cfg


class TTSError(Exception):
    pass


def probe_dur(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                        "default=nw=1:nk=1", str(path)], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except Exception:
        raise TTSError("تعذّر قراءة مدة الملف الصوتي.")


def voices():
    key = cfg("ELEVENLABS_API_KEY")
    if not key:
        return []
    try:
        r = requests.get("https://api.elevenlabs.io/v1/voices", headers={"xi-api-key": key}, timeout=30)
        r.raise_for_status()
        return [{"id": v["voice_id"], "name": v.get("name", v["voice_id"])} for v in r.json().get("voices", [])]
    except Exception:
        return []


def synth(text, voice_id, out_base):
    """يعيد {path, dur, words:[(كلمة, بداية, نهاية)]} بالثواني من بداية الملف."""
    text = re.sub(r"\s+", " ", text).strip()
    key = cfg("ELEVENLABS_API_KEY")
    voice_id = voice_id or cfg("ELEVENLABS_VOICE_ID")
    if not key:
        raise TTSError("مفتاح ELEVENLABS_API_KEY غير مضبوط في ملف .env")
    if not voice_id:
        raise TTSError("اختر صوتاً (voice_id) أو اضبط ELEVENLABS_VOICE_ID.")
    settings = {"stability": 0.45, "similarity_boost": 0.8, "style": 0.3, "use_speaker_boost": True}
    if cfg("ELEVENLABS_SPEED"):
        settings["speed"] = float(cfg("ELEVENLABS_SPEED"))
    try:
        r = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/with-timestamps",
            headers={"xi-api-key": key, "Content-Type": "application/json"},
            params={"output_format": "mp3_44100_128"},
            json={"text": text, "model_id": cfg("ELEVENLABS_MODEL", "eleven_multilingual_v2"),
                  "voice_settings": settings},
            timeout=180,
        )
    except requests.RequestException as e:
        raise TTSError(f"تعذّر الاتصال بـ ElevenLabs: {e}")
    if r.status_code >= 300:
        raise TTSError(f"خطأ {r.status_code} من ElevenLabs: {r.text[:300]}")
    j = r.json()
    path = str(out_base) + ".mp3"
    with open(path, "wb") as f:
        f.write(base64.b64decode(j["audio_base64"]))
    al = j.get("alignment") or j.get("normalized_alignment") or {}
    ch = al.get("characters", [])
    st = al.get("character_start_times_seconds", [])
    en = al.get("character_end_times_seconds", [])
    words, cur, s0, e0 = [], "", None, None
    for c, a, b in zip(ch, st, en):
        if c.isspace():
            if cur:
                words.append((cur, s0, e0))
            cur, s0 = "", None
        else:
            if s0 is None:
                s0 = a
            cur += c
            e0 = b
    if cur:
        words.append((cur, s0, e0))
    return {"path": path, "dur": probe_dur(path), "words": words}


def estimate_timing(text):
    """تقدير توقيت الكلمات بمعدّل 2.6 كلمة/ثانية — للمعاينة فقط بلا استدعاء API."""
    words = re.findall(r"\S+", text)
    t, tw = 0.0, []
    for w in words:
        d = 0.22 + 0.045 * len(w)
        tw.append((w, round(t, 3), round(t + d, 3)))
        t += d + 0.04
    return {"dur": max(t, 0.8), "words": tw}
