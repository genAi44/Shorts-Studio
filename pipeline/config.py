"""الإعدادات: تحميل .env يدوياً (بلا مكتبات إضافية) وثوابت الفيديو."""
import os
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
FONT = ROOT / "data" / "NotoKufi.ttf"
GEO = ROOT / "data" / "world.geojson"
SAMPLE = ROOT / "sample" / "demo_bolivia.json"

W, H, FPS = 1080, 1920, 30


def _load_env():
    p = ROOT / ".env"
    if not p.exists():
        return
    for line in p.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v


_load_env()


def cfg(key, default=""):
    return os.environ.get(key, default)


def flag(key):
    return cfg(key, "").strip().lower() in ("1", "true", "yes", "on")


# ------------------------------------------------------------------ Explicit Fallback & Warning Registry
import logging

_logger = logging.getLogger("shorts_studio")
LAST_WARNINGS: list[str] = []


class FallbackError(RuntimeError):
    """Raised when a visual fallback occurs while DEBUG=1 is active."""


def clear_warnings() -> None:
    LAST_WARNINGS.clear()


def get_last_warnings() -> list[str]:
    return list(LAST_WARNINGS)


def record_fallback(reason: str, beat_id: str = "unknown", beat: dict | None = None, log_fn=None) -> dict | None:
    """Explicitly logs a fallback, marks the beat with `_fallback: True`, and raises in DEBUG=1 mode."""
    msg = f"WARNING: falling back [{reason}] beat=[{beat_id}]"
    LAST_WARNINGS.append(msg)
    _logger.warning(msg)
    if callable(log_fn):
        try:
            log_fn(msg)
        except Exception:
            pass
    if isinstance(beat, dict):
        beat["_fallback"] = True
    if flag("DEBUG"):
        raise FallbackError(msg)
    return beat

