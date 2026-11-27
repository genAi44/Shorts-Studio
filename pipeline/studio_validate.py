"""Split from `pipeline/studio.py` (re-exported there): the shot validator and spoken-number matching."""
import hashlib
import json
import re
import shutil
import time
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
from .config import FPS, cfg, record_fallback

from .studio import DEVICES, DEVICE_BUDGET, MAX_SAME_DEVICE, MAX_SAME_ICON, MECHANISMS, REPEATABLE  # noqa: E402


# ------------------------------------------------------------------ validator (before any code)

_TASHKEEL = re.compile(r"[ً-ْـ]")
_PUNCT = re.compile(r"[^\w؀-ۿ]")


def norm_word(w: str) -> str:
    return _PUNCT.sub("", _TASHKEEL.sub("", str(w or ""))).replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")


def find_word(words: List[Dict[str, Any]], anchor: Any) -> Optional[Dict[str, Any]]:
    a = norm_word(anchor)
    if not a:
        return None
    for w in words:
        if norm_word(w["t"]) == a:
            return w
    for w in words:
        n = norm_word(w["t"])
        if len(a) >= 3 and len(n) >= 3 and (a in n or n in a):
            return w
    return None


@lru_cache(maxsize=1)
def _icon_names() -> frozenset:
    """Icons the renderer can actually draw: the curated bundle (remotion/src/generated/iconifyBundle.json, ~280 icons).
    Any other name silently renders as a star (icons.tsx fallback), so it is rejected here."""
    p = Path(__file__).resolve().parent.parent / "remotion" / "src" / "generated" / "iconifyBundle.json"
    d = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    return frozenset(f"{s}:{n}" for s, v in (d.get("sets") or {}).items() for n in v)


def icon_ok(name: Any) -> bool:
    return isinstance(name, str) and name.strip().lower() in _icon_names()


def _nwords(s: Any) -> int:
    return len(str(s or "").split())


_UNITS = {"واحد": 1, "واحده": 1, "احد": 1, "احدى": 1, "اثنان": 2, "اثنين": 2, "اثنتان": 2, "اثنتين": 2, "اثنا": 2, "اثني": 2,
          "اثنتا": 2, "اثنتي": 2, "ثلاث": 3, "ثلاثه": 3,
          "اربع": 4, "اربعه": 4, "خمس": 5, "خمسه": 5, "ست": 6, "سته": 6, "سبع": 7, "سبعه": 7, "ثمان": 8, "ثماني": 8, "ثمانيه": 8,
          "تسع": 9, "تسعه": 9, "عشر": 10, "عشره": 10}
_TENS = {"عشرون": 20, "ثلاثون": 30, "اربعون": 40, "خمسون": 50, "ستون": 60, "سبعون": 70, "ثمانون": 80, "تسعون": 90}
_TENS.update({k[:-2] + "ين": v for k, v in list(_TENS.items())})
_HUNDREDS = {"مئه": 100, "مائه": 100, "مئتان": 200, "مئتين": 200, "مائتان": 200, "مائتين": 200}
_HUNDREDS.update({u + h: v * 100 for u, v in (("ثلاث", 3), ("اربع", 4), ("خمس", 5), ("ست", 6), ("سبع", 7), ("ثمان", 8), ("تسع", 9))
                  for h in ("مئه", "مائه")})
_SCALES = {"الف": 1000, "الاف": 1000, "مليون": 10 ** 6, "ملايين": 10 ** 6, "مليار": 10 ** 9, "مليارات": 10 ** 9}
_DUALS = {"الفان": 2000, "الفين": 2000, "مليونان": 2 * 10 ** 6, "مليونين": 2 * 10 ** 6}


_AR_PUNCT = "،؛؟٪"
_DECIMAL = {"فاصل", "فاصله"}


def _num_token(tok: str) -> Optional[Tuple[str, int]]:
    t = norm_word(tok).replace("ة", "ه").strip(_AR_PUNCT)  # norm_word keeps U+060C..: the Arabic comma is in that range
    cands = [t]
    if t.startswith("و") and len(t) > 2:
        cands.append(t[1:])
    for c in list(cands):  # attached prepositions: "بألفين", "لعشرين", "كمئة"
        if c[:1] in ("ب", "ل", "ك") and len(c) > 3:
            cands.append(c[1:])
    for cand in cands:
        for kind, table in (("unit", _UNITS), ("unit", _TENS), ("hundred", _HUNDREDS), ("scale", _SCALES), ("unit", _DUALS)):
            if cand in table:
                return kind, table[cand]
    return None


def word_numbers(text: str) -> set:
    """Numbers written in Arabic words ("عشرون ألف ومئتان وواحد وأربعون" -> 20241, "سبعة عشر مليون" -> 17000000)."""
    out, total, cur, seen, whole = set(), 0, 0, False, None

    def flush():
        nonlocal total, cur, seen, whole
        if seen:
            n = total + cur
            if whole is not None:  # "اثني عشر فاصل ستة" -> 12.6
                out.add(whole)
                n = whole + n / 10 ** len(str(n))
            out.add(round(n, 6) if isinstance(n, float) else n)
        total, cur, seen, whole = 0, 0, False, None

    for tok in str(text or "").split() + ["."]:
        if norm_word(tok).replace("ة", "ه").strip(_AR_PUNCT) in _DECIMAL and seen and whole is None:
            whole, total, cur, seen = total + cur, 0, 0, False
            continue
        nt = _num_token(tok)
        if nt is None:
            if whole is not None and not seen:  # "فاصل" with no digits after it: keep the whole part
                total, cur, seen, whole = whole, 0, True, None
            flush()
            continue
        kind, v = nt
        seen = True
        if kind == "scale":
            total += max(cur, 1) * v
            cur = 0
        elif kind == "hundred" and v == 100 and 0 < cur < 10:  # "ثلاث مئة"
            cur *= 100
        else:
            cur += v
        if tok.rstrip()[-1:] in "،,.؛:":  # a comma ends the number (after this word)
            flush()
    return out


_PERCENT = re.compile(r"[%٪]|بالمئ|بالمائ|في المئ|في المائ")


def _spoken(v: float, ctx: Dict[str, Any]) -> bool:
    from .direct import _number_in_text
    return _number_in_text(int(v) if float(v).is_integer() else v, ctx["sentence"]) or v in word_numbers(ctx["sentence"])


def number_ok(value: Any, ctx: Dict[str, Any]) -> bool:
    from .direct import _number_in_text
    if value is None:
        return False
    try:
        v = float(value)
    except (TypeError, ValueError):
        return False
    if _spoken(v, ctx):
        return True
    # derived from the sentence's own logic (Rule 1.4): the rest of a spoken percentage (93 % -> 7), and the 100 % whole
    if _PERCENT.search(ctx["sentence"]) and 0 < v <= 100 and (v == 100 or _spoken(100 - v, ctx)):
        return True
    for e in ctx.get("entities", []):  # verified entity values (numbers written in words are resolved there)
        for k in ("value", "year", "to", "from", "born", "died"):
            try:
                if e.get(k) is not None and float(e[k]) == v:
                    return True
            except (TypeError, ValueError):
                continue
    return False


_DIGITS = re.compile(r"\d[\d,]*(?:\.\d+)?")
_AR_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩٫٬", "0123456789.,")
ITEM_LIMITS = {"hub": (2, 6, 3), "steps": (2, 5, 3), "stack": (2, 5, 5)}


def shot_icons(shot: Optional[Dict[str, Any]]) -> List[str]:
    if not isinstance(shot, dict):
        return []
    m = shot.get("mech") if isinstance(shot.get("mech"), dict) else {}
    out = [shot.get("hero_icon"), m.get("icon")] + [b.get("icon") for b in m.get("branches") or [] if isinstance(b, dict)] \
        + [x.get("icon") for x in m.get("sides") or [] if isinstance(x, dict)] + [it.get("icon") for it in shot.get("items") or [] if isinstance(it, dict)]         + [sd.get("icon") for sd in shot.get("sides") or [] if isinstance(sd, dict)]
    return [i for i in dict.fromkeys(out) if i]


def count_use(used: Dict[str, int], shot: Dict[str, Any], sign: int = 1) -> None:
    """Device and icon budget of the video (the validator reads it)."""
    hero = ["hero:" + shot["hero_icon"]] if shot.get("hero_icon") else []
    for key in [shot["device"]] + ["icon:" + i for i in shot_icons(shot)] + hero:
        used[key] = used.get(key, 0) + sign


def validate_shot(shot: Any, ctx: Dict[str, Any], prev: Optional[Dict[str, Any]], used: Dict[str, int]) -> List[str]:
    if not isinstance(shot, dict):
        return ["the reply is not a JSON object"]
    errs: List[str] = []
    dev = shot.get("device")
    words = ctx["words"]
    spoken = ", ".join(w["t"] for w in words[:40])
    if dev not in DEVICES:
        return [f"device must be one of {', '.join(DEVICES)}"]
    has_map = bool(ctx.get("map_overlay"))
    if has_map and dev != "map" and not ctx.get("map_seen"):
        errs.append("this scene has a map (its places must be shown): device must be 'map'")
    if dev == "map" and not has_map:
        errs.append("device 'map' is only for scenes that have a map")
    if prev and dev == prev.get("device") and dev not in REPEATABLE:
        errs.append(f"the previous scene already uses '{dev}': choose another device")
    if dev not in REPEATABLE and used.get(dev, 0) >= DEVICE_BUDGET.get(dev, MAX_SAME_DEVICE):
        errs.append(f"'{dev}' was already used {used[dev]} times in this video: choose another device")
    prev_icons = set(shot_icons(prev))
    for ic in shot_icons(shot):
        if ic == shot.get("hero_icon") and used.get("hero:" + str(ic), 0) >= 1:
            errs.append(f"hero_icon '{ic}' was already the hero of an earlier scene: a hero is used once per video, pick another")
        elif ic == shot.get("hero_icon") and ic in prev_icons:
            errs.append(f"hero_icon '{ic}' was used by the previous scene: pick a different icon")
        if used.get("icon:" + str(ic), 0) >= MAX_SAME_ICON:
            errs.append(f"icon '{ic}' was already used {used['icon:' + str(ic)]} times in this video: pick a different icon")
    if dev == "versus" and len({sd.get("icon") for sd in shot.get("sides") or [] if isinstance(sd, dict)}) < 2:
        errs.append("the two sides of 'versus' need two different icons")
    kw = str(shot.get("keyword") or "").strip()
    if not kw or _nwords(kw) > 4:
        errs.append("keyword must be 1-4 words")
    for k in ("lead", "tail"):
        if _nwords(shot.get(k)) > 7:
            errs.append(f"{k} must be at most 7 words")
    if _nwords(kw) + _nwords(shot.get("lead")) + _nwords(shot.get("tail")) > 12:
        errs.append("too much text on screen (keyword + lead + tail > 12 words): the caption already carries the narration")
    if norm_word(" ".join([str(shot.get("lead") or ""), kw, str(shot.get("tail") or "")])) == norm_word(ctx["sentence"]):
        errs.append("the on-screen text copies the narration: write the punchline instead")

    mech = shot.get("mech") if isinstance(shot.get("mech"), dict) else {}
    mech_texts = [mech.get(k) for k in ("from_label", "to_label", "source", "unit")] \
        + [b.get("label") for b in mech.get("branches") or [] if isinstance(b, dict)] \
        + [sd.get("label") for sd in mech.get("sides") or [] if isinstance(sd, dict)] \
        + [ev.get("label") for ev in mech.get("events") or [] if isinstance(ev, dict)]
    texts = mech_texts + [kw, shot.get("lead"), shot.get("tail")] + [it.get("text") for it in shot.get("items") or [] if isinstance(it, dict)]         + [sd.get("label") for sd in shot.get("sides") or [] if isinstance(sd, dict)]         + [(shot.get("number") or {}).get("label") if isinstance(shot.get("number"), dict) else None]
    seen = set()
    for txt in texts:  # the same line twice on screen (tail repeating an item) is wasted space
        t = norm_word(str(txt or ""))
        if t and t in seen:
            errs.append(f"the text '{txt}' appears twice on screen: every slot must say something different")
        seen.add(t)
    counted = {str(v.get("value")).replace(".0", "") for v in [shot.get("number")] + list(shot.get("sides") or []) + list(mech.get("sides") or [])
               if isinstance(v, dict) and v.get("value") is not None}
    if dev in ("filter", "shrink"):
        counted |= {str(mech.get(k)).replace(".0", "") for k in ("from", "to") if mech.get(k) is not None}
    counted |= {str(ev.get("year")).replace(".0", "") for ev in mech.get("events") or [] if isinstance(ev, dict) and ev.get("year") is not None}
    counted |= {str(b.get("share")).replace(".0", "") for b in mech.get("branches") or [] if isinstance(b, dict) and b.get("share") is not None}
    for txt in texts:  # a number already rolling in a counter is not written again next to it
        for m in _DIGITS.findall(str(txt or "").translate(_AR_DIGITS)):
            if m.replace(",", "") in counted:
                errs.append(f"'{m}' in '{txt}' is already shown by the counter: remove it from the text")
    derived = {str(b.get("share")).replace(".0", "") for b in mech.get("branches") or []
               if isinstance(b, dict) and b.get("share") is not None and _complement(b, [x for x in mech.get("branches") or [] if isinstance(x, dict)], ctx)}
    for txt in texts:  # truth rule for numbers written inside any on-screen text, not only the number slot
        for m in _DIGITS.findall(str(txt or "").translate(_AR_DIGITS)):
            n = m.replace(",", "")
            if n and n not in derived and not number_ok(n, ctx):
                errs.append(f"'{m}' in the on-screen text '{txt}' is not spoken in the sentence nor in its entities: remove it")

    def need_at(label: str, at: Any):
        if not find_word(words, at):
            errs.append(f"{label}: '{at}' is not one of the spoken words; copy one exactly from: {spoken}")

    if shot.get("keyword_at"):
        need_at("keyword_at", shot.get("keyword_at"))
    if dev in ("statement", "pinned", "map") and shot.get("hero_icon") is not None or dev == "statement":
        if not icon_ok(shot.get("hero_icon")):
            errs.append(f"hero_icon '{shot.get('hero_icon')}' is not in available_icons")
    num = shot.get("number") if isinstance(shot.get("number"), dict) else None
    if dev == "number" and not num:
        errs.append("device 'number' needs a number")
    if dev == "pinned" and not num and not shot.get("hero_icon"):
        errs.append("device 'pinned' needs a number or a hero_icon")
    if num:
        if not number_ok(num.get("value"), ctx):
            errs.append(f"number {num.get('value')} is not spoken in the sentence nor in its entities: use a spoken number or drop it")
        need_at("number.at", num.get("at"))
        if _nwords(num.get("label")) > 5:
            errs.append("number.label must be at most 5 words")
    if dev in ITEM_LIMITS:
        lo, hi, maxw = ITEM_LIMITS[dev]
        items = [it for it in shot.get("items") or [] if isinstance(it, dict)]
        if not lo <= len(items) <= hi:
            errs.append(f"'{dev}' needs {lo}-{hi} items")
        for i, it in enumerate(items):
            if not str(it.get("text") or "").strip() or _nwords(it.get("text")) > maxw:
                errs.append(f"item {i + 1}: text must be 1-{maxw} words")
            if dev != "steps" and not icon_ok(it.get("icon")):
                errs.append(f"item {i + 1}: icon '{it.get('icon')}' is not in available_icons")
            if it.get("at"):
                need_at(f"item {i + 1}.at", it.get("at"))
    if dev in MECHANISMS:
        errs += _mech_errors(dev, mech, ctx, need_at)
        if not str(shot.get("behavior") or "").strip():
            errs.append("'behavior' is required for a mechanism: what the drawing does (the no-text test)")
        if shot.get("mech_at"):
            need_at("mech_at", shot.get("mech_at"))
    if dev == "versus":
        sides = [s for s in shot.get("sides") or [] if isinstance(s, dict)]
        if len(sides) != 2:
            errs.append("'versus' needs exactly 2 sides")
        for i, s in enumerate(sides[:2]):
            if not str(s.get("label") or "").strip() or _nwords(s.get("label")) > 3:
                errs.append(f"side {i + 1}: label must be 1-3 words")
            if not icon_ok(s.get("icon")):
                errs.append(f"side {i + 1}: icon '{s.get('icon')}' is not in available_icons")
            if s.get("value") is not None and not number_ok(s.get("value"), ctx):
                errs.append(f"side {i + 1}: value {s.get('value')} is not spoken in the sentence nor in its entities")
            if s.get("at"):
                need_at(f"side {i + 1}.at", s.get("at"))
    return list(dict.fromkeys(errs))


def _num(v: Any) -> Optional[float]:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _complement(b: Dict[str, Any], br: List[Dict[str, Any]], ctx: Dict[str, Any]) -> bool:
    """A share that is exactly 100 minus all the other shares, which are themselves spoken: derived, not invented."""
    others = [x for x in br if x is not b]
    vals = [_num(x.get("share")) for x in others]
    if not others or None in vals or not all(number_ok(x.get("share"), ctx) for x in others):
        return False
    v = _num(b.get("share"))
    return v is not None and abs(100 - sum(vals) - v) < 0.01


def _mech_errors(dev: str, m: Dict[str, Any], ctx: Dict[str, Any], need_at) -> List[str]:
    """Slot rules of the five mechanisms (shapes only; the truth rule for their numbers also runs on all texts)."""
    e: List[str] = []
    if not m:
        return [f"'{dev}' needs a 'mech' object (see the catalogue)"]
    if m.get("change_at"):
        need_at("mech.change_at", m.get("change_at"))
    for k in ("from_label", "to_label"):
        if _nwords(m.get(k)) > 4:
            e.append(f"mech.{k} must be at most 4 words")
    if dev == "level":
        a, b = _num(m.get("from")), _num(m.get("to"))
        if a is None or b is None or not (0 <= a <= 1.2 and 0 <= b <= 1.2) or abs(a - b) < 0.05:
            e.append("level: mech.from and mech.to are fills between 0 and 1.2 that differ by at least 0.05")
    elif dev == "flow":
        br = [b for b in m.get("branches") or [] if isinstance(b, dict)]
        if not 2 <= len(br) <= 4:
            e.append("flow needs 2-4 branches")
        if not str(m.get("source") or "").strip() or _nwords(m.get("source")) > 4:
            e.append("flow: mech.source is 1-4 words")
        for i, b in enumerate(br):
            if not str(b.get("label") or "").strip() or _nwords(b.get("label")) > 3:
                e.append(f"flow branch {i + 1}: label is 1-3 words")
            if b.get("icon") and not icon_ok(b.get("icon")):
                e.append(f"flow branch {i + 1}: icon '{b.get('icon')}' is not in available_icons")
            if b.get("share") is not None and not number_ok(b.get("share"), ctx) and not _complement(b, br, ctx):
                e.append(f"flow branch {i + 1}: share {b.get('share')} is not spoken in the sentence nor in its entities "
                         "(a share is allowed when it is 100 minus the other, spoken, shares): omit it")
        kp = m.get("keep")
        if kp is not None and not (isinstance(kp, int) and 0 <= kp < len(br)):
            e.append("flow: mech.keep is the index (0-based) of one branch")
    elif dev in ("filter", "shrink"):
        a, b = _num(m.get("from")), _num(m.get("to"))
        lo = 0 if dev == "filter" else 1e-9  # a filter may end with none left ("you buy nothing")
        if a is None or b is None or a <= 0 or b < lo or a == b or (dev == "filter" and b >= a):
            e.append(f"{dev}: mech.from and mech.to are " + ("numbers with 0 <= to < from" if dev == "filter" else "two positive numbers that differ"))
        for k in ("from", "to"):
            if m.get(k) is not None and not (k == "to" and dev == "filter" and _num(m.get(k)) == 0) and not number_ok(m.get(k), ctx):
                e.append(f"{dev}: mech.{k} = {m.get(k)} is not spoken in the sentence nor in its entities")
        if dev == "filter" and m.get("icon") and not icon_ok(m.get("icon")):
            e.append(f"filter: icon '{m.get('icon')}' is not in available_icons")
        if dev == "shrink" and _nwords(m.get("unit")) > 2:
            e.append("shrink: mech.unit is at most 2 words")
    elif dev == "timeline":
        ev = [x for x in m.get("events") or [] if isinstance(x, dict)]
        if not 2 <= len(ev) <= 5:
            e.append("timeline needs 2-5 events")
        ys = [_num(x.get("year")) for x in ev]
        for i, x in enumerate(ev):
            if ys[i] is None or not number_ok(x.get("year"), ctx):
                e.append(f"timeline event {i + 1}: year {x.get('year')} is not spoken in the sentence nor in its entities")
            if not str(x.get("label") or "").strip() or _nwords(x.get("label")) > 4:
                e.append(f"timeline event {i + 1}: label is 1-4 words")
            if x.get("at"):
                need_at(f"timeline event {i + 1}.at", x.get("at"))
        if None not in ys and any(b <= a for a, b in zip(ys, ys[1:])):
            e.append("timeline: events must be in strictly ascending years (two events in one year is not a timeline: use another device)")
    elif dev == "tally":
        sd = [x for x in m.get("sides") or [] if isinstance(x, dict)]
        if len(sd) != 2:
            e.append("tally needs exactly 2 sides")
        vals = [_num(x.get("value")) for x in sd]
        for i, x in enumerate(sd[:2]):
            if vals[i] is None or vals[i] <= 0 or not number_ok(x.get("value"), ctx):
                e.append(f"tally side {i + 1}: value must be a positive number spoken in the sentence or its entities")
            if not icon_ok(x.get("icon")):
                e.append(f"tally side {i + 1}: icon '{x.get('icon')}' is not in available_icons")
            if not str(x.get("label") or "").strip() or _nwords(x.get("label")) > 3:
                e.append(f"tally side {i + 1}: label is 1-3 words")
        if len(vals) == 2 and None not in vals and min(vals) > 0 and max(vals) / min(vals) > 30:
            e.append("tally: the two values differ more than 30x (one side would be a single icon): use shrink or number")
    return e
