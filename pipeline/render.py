"""رسم المشاهد (PIL + numpy) مدفوعاً بالكامل بالستايل. كل مشهد ملف mp4 مستقل."""
import math
import os
import re
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFont, features

from .config import FONT, FPS, H, W
from .style import FONTS

DATA = FONT.parent
SC = 2  # supersampling للأقنعة
_HAS_RAQM = bool(features.check("raqm"))

# Pure-Python Arabic contextual shaper (Presentation Forms-B) + RTL reorderer when libraqm is unavailable
_AR_FORMS = {
    "\u0621": ("\uFE80", "\uFE80", "\uFE80", "\uFE80", False),
    "\u0622": ("\uFE81", "\uFE82", "\uFE81", "\uFE82", False),
    "\u0623": ("\uFE83", "\uFE84", "\uFE83", "\uFE84", False),
    "\u0624": ("\uFE85", "\uFE86", "\uFE85", "\uFE86", False),
    "\u0625": ("\uFE87", "\uFE88", "\uFE87", "\uFE88", False),
    "\u0626": ("\uFE89", "\uFE8A", "\uFE8B", "\uFE8C", True),
    "\u0627": ("\uFE8D", "\uFE8E", "\uFE8D", "\uFE8E", False),
    "\u0628": ("\uFE8F", "\uFE90", "\uFE91", "\uFE92", True),
    "\u0629": ("\uFE93", "\uFE94", "\uFE93", "\uFE94", False),
    "\u062A": ("\uFE95", "\uFE96", "\uFE97", "\uFE98", True),
    "\u062B": ("\uFE99", "\uFE9A", "\uFE9B", "\uFE9C", True),
    "\u062C": ("\uFE9D", "\uFE9E", "\uFE9F", "\uFEA0", True),
    "\u062D": ("\uFEA1", "\uFEA2", "\uFEA3", "\uFEA4", True),
    "\u062E": ("\uFEA5", "\uFEA6", "\uFEA7", "\uFEA8", True),
    "\u062F": ("\uFEA9", "\uFEAA", "\uFEA9", "\uFEAA", False),
    "\u0630": ("\uFEAB", "\uFEAC", "\uFEAB", "\uFEAC", False),
    "\u0631": ("\uFEAD", "\uFEAE", "\uFEAD", "\uFEAE", False),
    "\u0632": ("\uFEAF", "\uFEB0", "\uFEAF", "\uFEB0", False),
    "\u0633": ("\uFEB1", "\uFEB2", "\uFEB3", "\uFEB4", True),
    "\u0634": ("\uFEB5", "\uFEB6", "\uFEB7", "\uFEB8", True),
    "\u0635": ("\uFEB9", "\uFEBA", "\uFEBB", "\uFEBC", True),
    "\u0636": ("\uFEBD", "\uFEBE", "\uFEBF", "\uFEC0", True),
    "\u0637": ("\uFEC1", "\uFEC2", "\uFEC3", "\uFEC4", True),
    "\u0638": ("\uFEC5", "\uFEC6", "\uFEC7", "\uFEC8", True),
    "\u0639": ("\uFEC9", "\uFECA", "\uFECB", "\uFECC", True),
    "\u063A": ("\uFECD", "\uFECE", "\uFECF", "\uFED0", True),
    "\u0641": ("\uFED1", "\uFED2", "\uFED3", "\uFED4", True),
    "\u0642": ("\uFED5", "\uFED6", "\uFED7", "\uFED8", True),
    "\u0643": ("\uFED9", "\uFEDA", "\uFEDB", "\uFEDC", True),
    "\u0644": ("\uFEDD", "\uFEDE", "\uFEDF", "\uFEE0", True),
    "\u0645": ("\uFEE1", "\uFEE2", "\uFEE3", "\uFEE4", True),
    "\u0646": ("\uFEE5", "\uFEE6", "\uFEE7", "\uFEE8", True),
    "\u0647": ("\uFEE9", "\uFEEA", "\uFEEB", "\uFEEC", True),
    "\u0648": ("\uFEED", "\uFEEE", "\uFEED", "\uFEEE", False),
    "\u0649": ("\uFEEF", "\uFEF0", "\uFEEF", "\uFEF0", False),
    "\u064A": ("\uFEF1", "\uFEF2", "\uFEF3", "\uFEF4", True),
}
_LAM_ALEF = {
    "\u0622": ("\uFEF5", "\uFEF6"),
    "\u0623": ("\uFEF7", "\uFEF8"),
    "\u0625": ("\uFEF9", "\uFEFA"),
    "\u0627": ("\uFEFB", "\uFEFC"),
}
_HARAKAT = set("\u064B\u064C\u064D\u064E\u064F\u0650\u0651\u0652\u0653\u0654\u0655\u0670\u0640")


def _shape_arabic(text: str) -> str:
    if _HAS_RAQM or not text or not re.search(r"[\u0600-\u06FF]", str(text)):
        return str(text)
    # Strip tashkeel for clean Presentation Forms-B shaping
    chars = [c for c in str(text) if c not in _HARAKAT]
    out = []
    i = 0
    n = len(chars)
    while i < n:
        ch = chars[i]
        if ch not in _AR_FORMS:
            out.append(ch)
            i += 1
            continue
        prev_c = chars[i - 1] if i > 0 else ""
        prev_joins = bool(prev_c in _AR_FORMS and _AR_FORMS[prev_c][4])
        # Check Lam-Alef ligature
        if ch == "\u0644" and i + 1 < n and chars[i + 1] in _LAM_ALEF:
            iso_lig, fin_lig = _LAM_ALEF[chars[i + 1]]
            out.append(fin_lig if prev_joins else iso_lig)
            i += 2
            continue
        next_c = chars[i + 1] if i + 1 < n else ""
        next_joins = bool(_AR_FORMS[ch][4] and next_c in _AR_FORMS)
        iso, fin, ini, med, _ = _AR_FORMS[ch]
        if prev_joins and next_joins:
            out.append(med)
        elif prev_joins:
            out.append(fin)
        elif next_joins:
            out.append(ini)
        else:
            out.append(iso)
        i += 1
    shaped = "".join(out)
    # Reorder tokens RTL while keeping ASCII/number runs LTR
    tokens = re.findall(r"[A-Za-z0-9_.,:%+\-/]+|[^\sA-Za-z0-9_.,:%+\-/]+|\s+", shaped)
    visual_tokens = []
    for tok in reversed(tokens):
        if re.match(r"^[A-Za-z0-9_.,:%+\-/]+$", tok) or tok.isspace():
            visual_tokens.append(tok)
        else:
            visual_tokens.append(tok[::-1])
    return "".join(visual_tokens)


def _tlen(font, s: str) -> float:
    if _HAS_RAQM:
        return font.getlength(s, language="ar")
    return font.getlength(_shape_arabic(s))


def _dtext(draw, xy, s: str, **kw):
    if _HAS_RAQM:
        kw["language"] = "ar"
        draw.text(xy, s, **kw)
    else:
        kw.pop("language", None)
        draw.text(xy, _shape_arabic(s), **kw)

# ---------------------------------------------------------------- أدوات
_fonts = {}


def load_font(name, size, weight):
    k = (name, size, weight)
    if k in _fonts:
        return _fonts[k]
    file, var, _ = FONTS[name]
    f = ImageFont.truetype(str(DATA / file), size)
    if var:
        try:
            vals = []
            for a in f.get_variation_axes():
                nm = a["name"].decode() if isinstance(a["name"], bytes) else a["name"]
                vals.append(max(a["minimum"], min(a["maximum"], weight)) if "eight" in nm else a["default"])
            f.set_variation_by_axes(vals)
        except Exception:
            pass
    _fonts[k] = f
    return f


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def lum(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def on(c):
    """لون نص مقروء فوق الخلفية c."""
    return (22, 18, 14) if lum(c) > 150 else (255, 255, 255)


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def paste_rgba(ov, layer, x, y):
    lw, lh = layer.size
    x, y = int(x), int(y)
    sx, sy = max(0, -x), max(0, -y)
    ex, ey = min(lw, W - x), min(lh, H - y)
    if ex <= sx or ey <= sy:
        return
    ov.alpha_composite(layer.crop((sx, sy, ex, ey)), (x + sx, y + sy))


def wrap_lines(text, font, maxw):
    lines, cur = [], []
    for w in text.split():
        if cur and _tlen(font, " ".join(cur + [w])) > maxw:
            lines.append(" ".join(cur))
            cur = [w]
        else:
            cur.append(w)
    if cur:
        lines.append(" ".join(cur))
    return lines


def parse_num(s):
    m = re.search(r"\d[\d,\.]*", s)
    if not m:
        return None
    raw = m.group(0).rstrip(".,")
    clean = raw.replace(",", "")
    try:
        val = float(clean)
    except ValueError:
        return None
    dec = len(clean.split(".")[1]) if "." in clean else 0
    return s[:m.start()], val, dec, "," in raw, s[m.start() + len(raw):]

# Re-exported so `pipeline.render.<name>` keeps working.
from .render_layers import (  # noqa: E402,F401
    Background,
    MapLayer,
)

# Re-exported so `pipeline.render.<name>` keeps working.
from .render_scene_renderer import (  # noqa: E402,F401
    SceneRenderer,
    preview_frame,
    render_scene,
)
