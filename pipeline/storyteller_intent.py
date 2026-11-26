"""Split from `pipeline/storyteller.py` (re-exported there); see that module."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from .geo import detect_city_in_text
import re
from .storyteller import _clean_text, _words  # noqa: E402


def _extract_phrases(narration: str) -> List[str]:
    """Splits Arabic/English narration into meaningful semantic phrases for synchronization."""
    text = _clean_text(narration)
    if not text:
        return []
    parts = [p.strip() for p in re.split(r"[،,؛;:.!؟?\-]+", text) if p.strip()]
    phrases: List[str] = []
    for p in parts:
        w = p.split()
        if len(w) <= 6:
            phrases.append(p)
        else:
            for idx in range(0, len(w), 5):
                chunk = " ".join(w[idx : idx + 5]).strip()
                if chunk:
                    phrases.append(chunk)
    return phrases[:5] if phrases else [_words(text, 5)]


_AR_WORD_NUMBERS = {
    "\u0635\u0641\u0631": 0, "\u0648\u0627\u062d\u062f": 1, "\u0627\u062b\u0646\u064a\u0646": 2, "\u0627\u062b\u0646\u0627\u0646": 2, "\u062b\u0644\u0627\u062b\u0629": 3, "\u0623\u0631\u0628\u0639\u0629": 4, "\u0623\u0631\u0628\u0639": 4,
    "\u062e\u0645\u0633\u0629": 5, "\u062e\u0645\u0633": 5, "\u0633\u062a\u0629": 6, "\u0633\u062a": 6, "\u0633\u0628\u0639\u0629": 7, "\u0633\u0628\u0639": 7, "\u062b\u0645\u0627\u0646\u064a\u0629": 8,
    "\u062b\u0645\u0627\u0646": 8, "\u062a\u0633\u0639\u0629": 9, "\u062a\u0633\u0639": 9, "\u0639\u0634\u0631\u0629": 10, "\u0639\u0634\u0631": 10, "\u0623\u062d\u062f \u0639\u0634\u0631": 11, "\u0627\u062b\u0646\u0627 \u0639\u0634\u0631": 12,
    "\u062e\u0645\u0633\u0629 \u0639\u0634\u0631": 15, "\u0633\u062a\u0629 \u0639\u0634\u0631": 16, "\u0633\u0628\u0639\u0629 \u0639\u0634\u0631": 17, "\u062b\u0645\u0627\u0646\u064a\u0629 \u0639\u0634\u0631": 18, "\u062a\u0633\u0639\u0629 \u0639\u0634\u0631": 19,
    "\u0639\u0634\u0631\u0648\u0646": 20, "\u0639\u0634\u0631\u064a\u0646": 20, "\u062b\u0644\u0627\u062b\u0648\u0646": 30, "\u062b\u0644\u0627\u062b\u064a\u0646": 30, "\u062e\u0645\u0633\u0648\u0646": 50, "\u062e\u0645\u0633\u064a\u0646": 50,
    "\u0645\u0626\u0629": 100, "\u0645\u0627\u0626\u0629": 100, "\u0623\u0644\u0641": 1_000, "\u0623\u0644\u0641\u064a\u0646": 2_000, "\u0645\u0644\u064a\u0648\u0646": 1_000_000,
    "\u0645\u0644\u064a\u0627\u0631": 1_000_000_000,
}


_AR_MULTIPLIERS = {"\u0645\u0644\u064a\u0648\u0646": 1_000_000, "\u0645\u0644\u064a\u0627\u0631": 1_000_000_000, "\u0623\u0644\u0641": 1_000, "\u0645\u0626\u0629": 100, "\u0645\u0627\u0626\u0629": 100}


def _parse_arabic_word_number(text: str) -> Optional[float]:
    """Try to parse a simple Arabic word-form number like '\u0633\u0628\u0639\u0629 \u0639\u0634\u0631 \u0645\u0644\u064a\u0648\u0646'."""
    t = text.strip()
    for multi_word, val in sorted(_AR_WORD_NUMBERS.items(), key=lambda x: -len(x[0])):
        if multi_word in t:
            base = val
            for mult_word, mult_val in _AR_MULTIPLIERS.items():
                if mult_word in t and mult_word != multi_word:
                    return base * mult_val
            return float(base)
    return None


def _extract_numbers(text: str) -> List[Dict[str, Any]]:
    """Extracts numbers (digit or Arabic word-form) and their surrounding context label from text."""
    results: List[Dict[str, Any]] = []
    # First pass: Arabic word-numbers (e.g. "\u0633\u0628\u0639\u0629 \u0639\u0634\u0631 \u0645\u0644\u064a\u0648\u0646")
    for phrase, val in sorted(_AR_WORD_NUMBERS.items(), key=lambda x: -len(x[0])):
        if phrase in text:
            after = text[text.index(phrase) + len(phrase):].strip().split()[:3]
            label = " ".join(after) if after else phrase
            results.append({"display": phrase, "value": float(val), "label": _words(label, 3) or "\u0642\u064a\u0645\u0629"})
    for m in re.finditer(r"(\d[\d,.\u0660-\u0669]*)", text):
        raw_num = m.group(1)
        arabic_map = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
        norm_str = raw_num.translate(arabic_map).replace(",", "")
        try:
            val = float(norm_str)
        except ValueError:
            val = 0.0
        # Grab 3 words after the number as unit/label
        after = text[m.end() :].strip().split()[:3]
        before = text[: m.start()].strip().split()[-3:]
        label = " ".join(after) if after else " ".join(before)
        results.append({
            "display": raw_num,
            "value": val,
            "label": _words(label, 3) or "قيمة موثقة",
        })
    return results


def classify_narration_intent(narration: str, role: str = "body") -> Dict[str, Any]:
    """Distinguishes narration types and extracts key entities without restricting to templates."""
    t = _clean_text(narration)
    nums = _extract_numbers(t)
    city_name, city_info = detect_city_in_text(t)

    # Identify multiple cities if mentioned
    phrases = _extract_phrases(t)
    cities_found: List[Dict[str, Any]] = []
    seen_cities = set()
    for ph in [t] + phrases:
        cn, ci = detect_city_in_text(ph)
        if cn and ci and cn not in seen_cities:
            seen_cities.add(cn)
            cities_found.append({"name": cn, **ci})

    has_question = ("؟" in t or "?" in t) or any(
        w in t.split() for w in ["لماذا", "كيف", "متى", "أين", "هل", "ما", "ماذا"]
    )
    has_comparison = any(
        w in t for w in ["مقابل", "بينما", "تليها", "يليها", "أكبر من", "أصغر من", "صراع", "مقارنة", "تفوق", "منافسة"]
    )
    has_cause_effect = any(
        w in t for w in ["بسبب", "نتيجة", "أدى", "يؤدي", "تؤدي", "دفع", "لذلك", "فجأة", "تحول", "جعلت", "مضاعفة"]
    )
    has_history = any(
        w in t for w in ["عام", "سنة", "قرن", "تاريخ", "تأسست", "الحرب", "الإمبراطورية", "القديمة", "العصور", "ملك", "دستور"]
    )
    has_process = any(
        w in t for w in ["مراحل", "خطوات", "تنتقل", "تدفق", "منظومة المراحل", "خطوة بخطوة"]
    )
    # ponytail: removed "شبكة","نظام","مسار","رحلة" — too broad, caused network-diagram false positives on geo content
    has_population = any(
        w in t for w in ["سكان", "نسمة", "مليون", "تعداد", "شعب", "بشر", "مدن", "مدينة", "عاصمة"]
    )

    has_urban = any(
        w in t for w in ["أبراج", "حاضرة", "عمران", "عمرانية", "ناطحات", "أفق", "مزدحمة"]
    )

    if role == "hook" or (has_question and role in ("open_loop", "hook")):
        primary_intent = "question_and_discovery"
        visual_approach = "exploded_isometric_core"
    elif has_comparison and (len(nums) >= 2 or len(cities_found) >= 2 or "مقابل" in t or "بينما" in t):
        primary_intent = "comparative_analysis"
        visual_approach = "equilibrium_duel_stage"
    elif has_cause_effect:
        primary_intent = "cause_and_consequence"
        visual_approach = "exploded_isometric_core"
    elif has_urban or (city_info and has_population and nums):
        primary_intent = "urban_metropolis"
        visual_approach = "metropolis_skyline"
    elif city_info:
        primary_intent = "geographic_spatial_story"
        visual_approach = "orbital_cartography"
    elif has_history:
        primary_intent = "historical_chronicle"
        visual_approach = "chronicle_conduit"
    elif len(nums) >= 2:
        primary_intent = "multi_metric_statistics"
        visual_approach = "equilibrium_duel_stage"
    elif len(nums) == 1:
        primary_intent = "hero_statistic_revelation"
        visual_approach = "metropolis_skyline" if has_population else "exploded_isometric_core"
    elif has_process:
        primary_intent = "process_and_transformation"
        visual_approach = "exploded_isometric_core"
    elif role == "cta":
        primary_intent = "interactive_audience_challenge"
        visual_approach = "exploded_isometric_core"
    else:
        primary_intent = "conceptual_explanation"
        visual_approach = "exploded_isometric_core"

    return {
        "primary_intent": primary_intent,
        "visual_approach": visual_approach,
        "has_question": has_question,
        "has_comparison": has_comparison,
        "has_cause_effect": has_cause_effect,
        "has_history": has_history,
        "has_process": has_process,
        "has_population": has_population,
        "numbers": nums,
        "primary_city": city_info,
        "primary_city_name": city_name,
        "cities": cities_found,
        "phrases": phrases,
    }


def _pick_unique(options: List[Any], used: set, seed: int, key_fn=lambda x: x) -> Any:
    for offset in range(len(options)):
        cand = options[(seed + offset) % len(options)]
        k = key_fn(cand)
        if k not in used:
            used.add(k)
            return cand
    cand = options[seed % len(options)]
    used.add(key_fn(cand))
    return cand
