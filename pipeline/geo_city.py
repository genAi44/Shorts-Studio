"""Split from `pipeline/geo.py` (re-exported there); see that module."""
from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
import re
from .geo import AR_ISO3, get_engine  # noqa: E402


# ══════════════════════════════════════════════════════════════════════
# دوال التوافق ومطابقة النصوص الحية عبر محرك البحث الجغرافي
# ══════════════════════════════════════════════════════════════════════
# كلمات شائعة وأرقام واختصارات زمنية يجب ألا تعامل كأسماء مدن
_CITY_STOP_WORDS = {
    "في", "من", "إلى", "الى", "على", "عن", "مع", "أن", "إن", "قد", "كان", "كانت", "يكون",
    "أو", "ثم", "بل", "لا", "لن", "لم", "ما", "هذا", "هذه", "تلك", "ذلك", "هنا",
    "هناك", "سر", "السر", "بداية", "نهاية", "نقطة", "يوم", "اليوم", "يوما", "يوماً", "أيام", "الأيام",
    "ساعة", "لحظة", "ثانية", "دقيقة", "عام", "سنة", "قرن", "القرن", "قارة", "قارات", "القارات",
    "وجه", "الأرض", "اللقب", "المنافسة", "تتنافس", "ساحرة", "تأسر", "القلوب",
    "حرب", "الحرب", "ملك", "سلطان", "مدينة", "المدينة", "مدينتين", "المدينتين", "مدن", "المدن",
    "عاصمة", "العاصمة", "عاصمتين", "العاصمتين", "عاصمتان", "عواصم", "العواصم", "دولة", "الدولة",
    "دول", "الدول", "بلد", "البلد", "بلاد", "البلاد", "بلدان", "شعب", "الشعب", "شعوب",
    "عالم", "العالم", "مركز", "المركز", "الحكم", "حكم", "الأولى", "الثانية", "الثالثة",
    "شمال", "الشمال", "جنوب", "الجنوب", "شرق", "الشرق", "غرب", "الغرب", "وسط", "الوسط",
    "بحري", "البحري", "سقوط", "تحرير", "إنزال", "إحصائيات", "ضحايا", "مليون", "مليار",
    "قلب", "القلب", "جزيرة", "الجزيرة", "جزر", "الجزر", "ساحل", "الساحل", "جبل", "الجبل",
    "جبال", "الجبال", "نهر", "النهر", "بحر", "البحر", "محيط", "المحيط", "وادي", "الوادي",
    "صحراء", "الصحراء", "غابة", "الغابة", "قمة", "القمة", "أعلى", "الأعلى", "أدنى",
    "سلطة", "السلطة", "حكومة", "الحكومة", "برلمان", "البرلمان", "رئيس", "الرئيس",
    "قضاء", "القضاء", "دستور", "الدستور", "دستوري", "دستورية", "تاريخي", "تاريخية",
    "ثورة", "الثورة", "ثورات", "الثورات", "تاج", "التاج", "إسباني", "الإسباني",
    "استقلال", "الاستقلال", "تاريخ", "التاريخ", "حقيقة", "الحقيقة", "مفاجأة", "المفاجأة",
    "غريب", "الغريب", "عجيب", "العجيب", "تعلم", "هل", "أكبر", "أصغر", "أغنى", "أفقر",
    "أول", "أولى", "ثاني", "ثانية", "ثالث", "ثالثة", "آخر", "جديد", "الجديد", "قديم", "القديم",
    "القديمة", "الحديثة",
    # الأعداد والأرقام بالعربية لمنع تطابق مثل "ألفين" مع مدينة Alvin الأمريكية أو "الخمس" مع الخمس الليبية
    "صفر", "واحد", "واحدة", "الواحد", "الواحدة", "اثنين", "اثنان", "الاثنين", "الاثنان", "اثنتين", "اثنتان", "الاثنتين", "الاثنتان", "اثني", "اثنتي",
    "ثلاث", "ثلاثة", "الثلاث", "الثلاثة", "أربع", "أربعة", "الأربع", "الأربعة", "خمس", "خمسة", "الخمس", "الخمسة", "ست", "ستة", "الست", "الستة", "سبع", "سبعة", "السبع", "السبعة",
    "ثمان", "ثماني", "ثمانية", "الثمان", "الثماني", "الثمانية", "تسع", "تسعة", "التسع", "التسعة", "عشر", "عشرة", "العشر", "العشرة",
    "عشرين", "عشرون", "العشرين", "العشرون", "ثلاثين", "ثلاثون", "الثلاثين", "الثلاثون", "أربعين", "أربعون", "الأربعين", "الأربعون", "خمسين", "خمسون", "الخمسين", "الخمسون",
    "ستين", "ستون", "سبعين", "سبعون", "ثمانين", "ثمانون", "تسعين", "تسعون",
    "مئة", "مائة", "المئة", "المائة", "مئتين", "مائتين", "مئات", "ثلاثمئة", "أربعمئة", "خمسمئة",
    "ستمئة", "سبعمئة", "ثمانمئة", "تسعمئة", "ألف", "ألفين", "ألفان", "آلاف", "الألف", "الآلاف",
    "مليون", "مليونين", "ملايين", "المليون", "الملايين", "مليار", "مليارات",
    "الأكبر", "الأصغر", "الأعلى", "الأدنى", "الأشهر", "الأقدم", "الأحدث", "الأهم", "الأقوى", "الأغنى", "الأفقر", "الأصلية", "الأصلي",
    "كيف", "لماذا", "متى", "أين", "كم", "كل", "جميع", "بعض", "أكثر", "أقل", "نحو",
    "حتى", "بين", "بينما", "فوق", "تحت", "أمام", "خلف", "حول", "دون", "غير", "سوى", "فقط",
    "الذي", "التي", "الذين", "اللواتي", "اللائي", "إذا", "لو", "لولا", "لعل", "ليت",
    "أمريكا", "الجنوبية", "الشمالية", "أوروبا", "آسيا", "أفريقيا", "إفريقيا", "أستراليا",
    "العربي", "العربية", "الإسلامي", "الإسلامية", "الدور", "الإداري", "الثقل", "الحضاري",
    "السياسي", "الاقتصادي", "التشريعي", "التنفيذي", "التنفيذية", "القضائي", "القضائية",
    "الرسمية", "الفعلي", "رسمياً", "فعلياً", "رسميتين", "بدلا", "ثواني", "الثواني",
    "القادمة", "ستكتشف", "المثير", "شهدت", "ضد", "تجمع", "تملك", "يمتلك", "تمتلك",
    "تقع", "يقع", "تعد", "يعد", "أقر", "بقاء", "شؤون", "تدير", "تظل", "يبقى", "تبقى",
    "كامل", "بالكامل", "انقسام", "الانقسام", "صراع", "الصراع", "مقر", "المقر",
    # اختصارات تاريخية وزمنية تمنع الخلط مع أسماء مدن مثل 'قم' الإيرانية أو 'صور' أو 'العين'
    "قم", "ق م", "م", "هـ", "ميلادي", "هجري", "قبل", "بعد", "فترة", "عصور",
    "عين", "العين", "صور", "الصور", "بيان", "البيان", "سلام", "السلام", "أمل", "الأمل",
    "نور", "النور", "فجر", "الفجر", "نصر", "النصر", "عهد", "العهد", "مجد", "المجد",
    "دول", "دولا", "دولة", "الدول", "الدولة", "جيش", "جيشا", "جيشها", "جيوش", "جيوشا",
    "شعب", "شعبا", "شعوب", "شعوبا", "شعوبها", "عالم", "العالم", "أمان", "أمانا", "امان",
    "عام", "سنة", "سنويا", "ممر", "فوق", "تحت", "بين", "تدر", "أعلى", "اكبر", "أكبر",
    "تعيش", "بدون", "قوات", "مسلحة", "تعتمد", "تحميها", "لاتينية", "اللاتينية", "الوسطى",
    "أمريكا", "امريكا", "اروبا", "أوروبا", "آسيا", "افريقيا", "أفريقيا",
}


def detect_city_in_text(text: str) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """
    يكتشف ما إذا كان النص يذكر مدينة أو عاصمة ويبحث عنها فوراً في geodata.db.
    يعيد (اسم_المدينة_بالعربية, قاموس_المعلومات_الجغرافية).
    """
    if not text:
        return None, None
    engine = get_engine()
    _STOP_WORDS = _CITY_STOP_WORDS

    # استخراج الكلمات والتراكيب المحتملة (1 إلى 2 كلمة)
    raw_words = [re.sub(r"[^\w]", "", w) for w in text.split()]
    raw_words = [w for w in raw_words if w and len(w) >= 2]

    cands: List[str] = []
    for i in range(len(raw_words) - 1):
        w1, w2 = raw_words[i], raw_words[i + 1]
        bigram = f"{w1} {w2}"
        if bigram == "المدينة المنورة":
            cands.append(bigram)
        elif w1 not in _STOP_WORDS and w2 not in _STOP_WORDS:
            cands.append(bigram)
    for w in raw_words:
        if w not in _STOP_WORDS:
            cands.append(w)
            if len(w) >= 5 and w[0] in ("و", "ب", "ل", "ف") and w[1:] not in _STOP_WORDS:
                cands.append(w[1:])

    if not hasattr(detect_city_in_text, "_cand_cache"):
        detect_city_in_text._cand_cache = {}
    cand_cache = detect_city_in_text._cand_cache

    matched_candidates: List[Tuple[Tuple[int, int, int, int], str, Dict[str, Any]]] = []

    for cand in cands:
        if cand in cand_cache:
            cached_info = cand_cache[cand]
            if cached_info is not None:
                rank_key = (
                    int(bool(cached_info.get("is_capital"))),
                    int(cached_info.get("feature_code") == "PPLC"),
                    int(bool(cached_info.get("is_historical"))),
                    int(cached_info.get("population") or 0),
                )
                matched_candidates.append((rank_key, cand, cached_info))
            continue

        if cand in AR_ISO3:
            cand_cache[cand] = None
            continue

        is_ar = bool(re.search(r"[\u0600-\u06FF]", cand))
        if is_ar:
            place = (
                engine._match_exact_ar(cand, None) or
                engine._match_altname(cand, "ar", None)
            )
        else:
            place = engine._match_exact_en(cand, None)

        # an obscure historical hamlet with no English name and no population ("جديدة" = a Lebanese ruin) is an ordinary
        # Arabic word in a sentence, not a place: it must never steal the sentence from the country that is named in it
        obscure = bool(place) and not place.is_capital and place.feature_code != "PPLC" and not (place.population or 0)             and bool(re.search(r"[؀-ۿ]", place.name_en or ""))
        if place and not obscure and (
            place.is_capital
            or place.is_historical
            or place.feature_code == "PPLC"
            or (place.feature_code in ("PPLA", "PPLA2", "PPLG") and (place.population or 0) >= 50000)
            or (place.feature_code in ("PPL", "PPLX", "ADM1") and (place.population or 0) >= 100000)
        ):
            city_name = place.name_ar or place.name_en
            info = {
                "name": city_name,
                "en": place.name_en,
                "iso": place.country_iso3 or place.country_iso2,
                "iso2": place.country_iso2,
                "lat": place.lat,
                "lon": place.lon,
                "country": place.country_en or place.country_iso2,
                "is_capital": place.is_capital,
                "is_historical": place.is_historical,
                "feature_code": place.feature_code,
                "population": place.population or 0,
            }
            cand_cache[cand] = info
            rank_key = (
                int(bool(place.is_capital)),
                int(place.feature_code == "PPLC"),
                int(bool(place.is_historical)),
                int(place.population or 0),
            )
            matched_candidates.append((rank_key, cand, info))
        else:
            cand_cache[cand] = None

    if matched_candidates:
        matched_candidates.sort(key=lambda item: item[0], reverse=True)
        _, best_cand, best_info = matched_candidates[0]
        return best_cand, best_info

    return None, None
