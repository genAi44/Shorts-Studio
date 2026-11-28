"""Does a sentence name a place - by its name OR by its nationality adjective ("مدن أمريكية" names the United States)?

Arabic adjectives (nisba) are the name's stem + ي / ية / يون / يين: strip the article and those endings from the words of the
sentence and from the place name, then compare stems. أمريكية -> أمريك = أمريكا -> أمريك; مصرية -> مصر; روسية -> روس = روسيا.
"""
import re
from typing import Iterable, Set

# common names a country is called by in Arabic besides its formal name (formal name -> everyday stem source)
ALIASES = {
    "United States": ["أمريكا", "امريكا"], "الولايات المتحدة": ["أمريكا", "امريكا"],
    "United Kingdom": ["بريطانيا", "إنجلترا", "انجلترا"], "المملكة المتحدة": ["بريطانيا", "إنجلترا", "انجلترا"],
    "Netherlands": ["هولندا"], "Switzerland": ["سويسرا"],
}
_TASHKEEL = re.compile("[ؐ-ًؚ-ٰٟـ]")  # harakat, superscript alef, tatweel (NOT the letters)
_SUFFIXES = ("يون", "يين", "يات", "ية", "يه", "ي", "يا", "ا", "ة", "ه")


def _norm(w: str) -> str:
    w = _TASHKEEL.sub("", w)
    w = re.sub(r"[^\w]", "", w)
    return w.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")


def stem(word: str) -> str:
    w = _norm(word)
    for pre in ("وال", "بال", "لل", "كال", "فال", "ال"):
        if w.startswith(pre) and len(w) - len(pre) >= 3:
            w = w[len(pre):]
            break
    for suf in _SUFFIXES:
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            return w[: -len(suf)]
    return w


def _stems(names: Iterable[str]) -> Set[str]:
    out = set()
    for n in names:
        toks = [t for t in n.split() if t]
        if len(toks) == 1:   # multi-word formal names ("الولايات المتحدة") only match through their aliases or the full name
            out.add(stem(toks[0]))
    return {s for s in out if len(s) >= 3}


def mentions_place(sentence: str, name_ar: str, name_en: str = "") -> bool:
    if not sentence or not (name_ar or name_en):
        return False
    full = _norm(name_ar.replace(" ", "")) if name_ar else ""
    if len(full) >= 3 and full in _norm(sentence.replace(" ", "")):
        return True
    targets = _stems([name_ar] + ALIASES.get(name_ar, []) + ALIASES.get(name_en, []))
    return any(stem(w) in targets for w in sentence.split())
