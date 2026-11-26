"""Split from `pipeline/visual_tools.py` (re-exported there); see that module."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
import re
from .visual_tools import draw_chart, resolve_flag, search_emoji, search_icons, search_lottie  # noqa: E402


def apply_chat_visual_edit(
    script: Dict[str, Any],
    instruction: str,
    scene_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Handles chat edits like:
    - 'change the icon to a pyramid' / 'غير الأيقونة إلى هرم'
    - 'use a bar chart here' / 'استخدم مخطط أعمدة هنا'
    - 'add flag of Egypt' / 'أضف علم مصر'
    - 'add emoji crown' / 'أضف إيموجي تاج'
    - 'add lottie confetti' / 'أضف لوتي احتفال'
    using the exact same offline tools (`search_icons`, `draw_chart`, `resolve_flag`, `search_emoji`, `search_lottie`).
    """
    import copy
    from .scriptspec import PART_IDS, normalize

    s = normalize(copy.deepcopy(script))
    target_id = scene_id if scene_id in PART_IDS else "hook"
    instr = (instruction or "").strip()
    instr_low = instr.lower()

    part = s.get(target_id, {})
    visuals: List[Dict[str, Any]] = list(part.get("visuals") or [])
    action_taken = ""

    # 0. Check for Elevation / Mountain + Sea + Capital + Counter requests ("ارتفاع", "جبل", "بحر", "elevation")
    if any(k in instr_low for k in ("elevation", "altitude", "ارتفاع", "جبل", "سطح البحر")):
        nums = re.findall(r"\d[\d,]*", instr)
        vis_num = (part.get("visual") or {}).get("number") if isinstance(part.get("visual"), dict) else None
        height_str = nums[0] if nums else (str(vis_num) if vis_num else "3,650")
        elev_beat = {
            "kind": "elevation_profile",
            "title": part.get("on_screen") or "لاباز — أعلى عاصمة إدارية",
            "capital": part.get("on_screen") or "العاصمة لاباز",
            "height": height_str,
            "unit": "م",
            "sea_label": "مستوى سطح البحر",
        }
        beats = list(part.get("beats") or [])
        part["beats"] = [elev_beat] + beats[1:] if beats else [elev_beat]
        action_taken = f"elevation_profile({height_str}m)"

    elif any(k in instr_low for k in ("versus", "battle", "مقارنة القوى", "سباق المقارنة", "مقارنة")):
        beat_obj = {
            "kind": "versus_battle",
            "title": part.get("on_screen") or "مقارنة القوى المباشرة",
            "left": {"name": "الطرف الأول", "value": 85, "unit": "مليار $", "code": "EG"},
            "right": {"name": "الطرف الثاني", "value": 120, "unit": "مليار $", "code": "SA"},
        }
        beats = list(part.get("beats") or [])
        part["beats"] = [beat_obj] + beats[1:] if beats else [beat_obj]
        action_taken = "versus_battle"

    elif any(k in instr_low for k in ("route", "journey", "مسار", "انتقال", "رحلة", "طريق")):
        beat_obj = {
            "kind": "animated_route",
            "title": part.get("on_screen") or "مسار الانتقال الجغرافي",
            "from_city": "سوكري",
            "to_city": "لاباز",
            "distance_km": 560,
        }
        beats = list(part.get("beats") or [])
        part["beats"] = [beat_obj] + beats[1:] if beats else [beat_obj]
        action_taken = "animated_route"

    elif any(k in instr_low for k in ("balance", "gauge", "ميزان", "كفة", "استفتاء")):
        beat_obj = {
            "kind": "balance_meter",
            "title": part.get("on_screen") or "ميزان القوى والسيطرة",
            "label_a": "الحكومة المركزية",
            "label_b": "نخب الشمال",
            "pct": 68,
        }
        beats = list(part.get("beats") or [])
        part["beats"] = [beat_obj] + beats[1:] if beats else [beat_obj]
        action_taken = "balance_meter"

    elif any(k in instr_low for k in ("century", "year", "time", "قرون", "زمن", "سنوات", "تاريخ عبر الزمن")):
        beat_obj = {
            "kind": "deep_time_slider",
            "title": part.get("on_screen") or "قفزة عبر القرون والتاريخ",
            "start_year": 1825,
            "end_year": 2009,
            "event_label": "إقرار الدستور المزدوج والتسوية النهائية",
        }
        beats = list(part.get("beats") or [])
        part["beats"] = [beat_obj] + beats[1:] if beats else [beat_obj]
        action_taken = "deep_time_slider"

    elif any(k in instr_low for k in ("stack_pyramid", "طبقات", "هرم السلطة", "تشريح السلطة")):
        beat_obj = {
            "kind": "stack_pyramid",
            "title": part.get("on_screen") or "هيكل السلطة الدستورية",
            "layers": [
                {"name": "الرئاسة والحكومة (لاباز)", "width": 360, "color": "#f5c542"},
                {"name": "البرلمان والوزارات المركزية", "width": 560, "color": "#38bdf8"},
                {"name": "القضاء الأعلى والدستور (سوكري)", "width": 780, "color": "#34d399"},
            ],
        }
        beats = list(part.get("beats") or [])
        part["beats"] = [beat_obj] + beats[1:] if beats else [beat_obj]
        action_taken = "stack_pyramid"

    elif any(k in instr_low for k in ("macro", "globe", "zoom", "العالم إلى الدولة", "تلسكوبي", "كوكب")):
        beat_obj = {
            "kind": "macro_zoom_globe",
            "title": part.get("on_screen") or "في قلب قارة أمريكا الجنوبية",
            "country": "بوليفيا",
            "code": "BO",
        }
        beats = list(part.get("beats") or [])
        part["beats"] = [beat_obj] + beats[1:] if beats else [beat_obj]
        action_taken = "macro_zoom_globe"

    elif any(k in instr_low for k in ("mine", "subsurface", "باطن الأرض", "مناجم", "تعدين", "فضة", "ذهب تحت الأرض")):
        beat_obj = {
            "kind": "subsurface_mine",
            "title": part.get("on_screen") or "كنوز باطن الأرض والفضة",
            "depth_m": 1200,
            "resource": "مناجم الفضة التاريخية",
        }
        beats = list(part.get("beats") or [])
        part["beats"] = [beat_obj] + beats[1:] if beats else [beat_obj]
        action_taken = "subsurface_mine"

    elif any(k in instr_low for k in ("population", "matrix", "سكان", "كثافة سكانية", "مصفوفة")):
        beat_obj = {
            "kind": "dot_matrix_population",
            "title": part.get("on_screen") or "التوزيع السكاني والديموغرافي",
            "total_label": "١٢ مليون نسمة",
            "highlight_pct": 70,
        }
        beats = list(part.get("beats") or [])
        part["beats"] = [beat_obj] + beats[1:] if beats else [beat_obj]
        action_taken = "dot_matrix_population"

    elif any(k in instr_low for k in ("waterfall", "budget", "ميزانية", "تدفق الأموال", "أموال الدولة")):
        beat_obj = {
            "kind": "money_waterfall",
            "title": part.get("on_screen") or "مسار التدفقات المالية والميزانية",
            "total": "١٠٠ مليار $",
            "streams": [
                {"name": "تطوير البنية والمدن", "pct": "٤٥%", "color": "#f5c542"},
                {"name": "الخدمات والصحة", "pct": "٣٠%", "color": "#38bdf8"},
                {"name": "الاحتياطي السيادي", "pct": "٢٥%", "color": "#34d399"},
            ],
        }
        beats = list(part.get("beats") or [])
        part["beats"] = [beat_obj] + beats[1:] if beats else [beat_obj]
        action_taken = "money_waterfall"

    elif any(k in instr_low for k in ("frontline", "war", "حرب", "جبهة", "معركة", "اشتباك", "نزاع مسلح")):
        beat_obj = {
            "kind": "frontline_clash",
            "title": part.get("on_screen") or "اشتعال خطوط المواجهة والنزاع",
            "side_a": "قوات الحكومة",
            "side_b": "الفيدراليون (الشمال)",
        }
        beats = list(part.get("beats") or [])
        part["beats"] = [beat_obj] + beats[1:] if beats else [beat_obj]
        action_taken = "frontline_clash"

    elif any(k in instr_low for k in ("generative", "custom", "بركان", "انفجار", "حصار", "شبكة عصبية", "تضخم", "توليد", "ليغو", "رسم توضيحي", "رسم حر")):
        from .generative_visuals import compose_generative_canvas
        gen_beat = compose_generative_canvas(instr, context=part.get("text") or part.get("on_screen"))
        beats = list(part.get("beats") or [])
        part["beats"] = [gen_beat] + beats[1:] if beats else [gen_beat]
        action_taken = f"generative_canvas({gen_beat.get('title')})"

    # 1. Check for Chart requests ("bar chart", "line chart", "pie chart", "donut", "مخطط أعمدة", "مخطط خطي", "مخطط دائري")
    elif any(k in instr_low for k in ("chart", "bar", "line", "pie", "donut", "مخطط", "أعمدة", "بياني", "دائري")):
        ctype = "bar"
        if "line" in instr_low or "خطي" in instr_low:
            ctype = "line"
        elif "pie" in instr_low or "donut" in instr_low or "دائري" in instr_low:
            ctype = "donut"
        elif "timeline" in instr_low or "زمني" in instr_low:
            ctype = "timeline"

        chart_el = draw_chart({
            "type": ctype,
            "data": [
                {"label": part.get("on_screen") or "المؤشر الأول", "value": 85},
                {"label": "المؤشر الثاني", "value": 62},
                {"label": "المؤشر الثالث", "value": 44},
            ],
            "style": {
                "title": part.get("on_screen") or "مقارنة البيانات",
                "rtl": True,
                "arabicNumerals": True,
            },
        })
        chart_el["placement"] = "center"
        visuals = [v for v in visuals if v.get("kind") != "chart"]
        visuals.insert(0, chart_el)
        # Also update the scene's primary beat so the chart renders prominently
        beats = list(part.get("beats") or [])
        chart_beat = {
            "kind": "chart",
            "title": part.get("on_screen") or "مقارنة البيانات",
            "spec": chart_el["spec"],
        }
        if beats:
            beats[0] = chart_beat
        else:
            beats = [chart_beat]
        part["beats"] = beats
        action_taken = f"draw_chart({ctype})"

    # 2. Check for Flag requests ("flag", "علم")
    elif "flag" in instr_low or "علم" in instr_low:
        q = re.sub(r"(?i)(change|add|use|the|flag|of|to|here|أضف|غير|استخدم|علم|إلى|هنا)", " ", instr).strip()
        fl = resolve_flag(q or instr)
        flag_el = {
            "kind": "flag",
            "placement": "badge-row",
            "spec": {"code": fl["code"], "shape": "rect", "size": 92, "animation": "pop"},
        }
        visuals = [v for v in visuals if v.get("kind") != "flag"]
        visuals.append(flag_el)
        action_taken = f"resolve_flag({fl['code']})"

    # 3. Check for Emoji requests ("emoji", "إيموجي", "رمز تعبيري")
    elif "emoji" in instr_low or "إيموجي" in instr_low or "ايموجي" in instr_low:
        q = re.sub(r"(?i)(change|add|use|the|emoji|to|here|أضف|غير|استخدم|إيموجي|ايموجي|إلى|هنا)", " ", instr).strip()
        matches = search_emoji(q or instr, limit=1)
        chosen = matches[0]
        em_el = {
            "kind": "emoji",
            "placement": "badge-row",
            "spec": {"char": chosen["char"], "size": 92, "animation": "pop"},
        }
        visuals = [v for v in visuals if v.get("kind") != "emoji"]
        visuals.append(em_el)
        action_taken = f"search_emoji({chosen['char']})"

    # 4. Check for Lottie requests ("lottie", "لوتي", "confetti", "sparkles", "checkmark")
    elif any(k in instr_low for k in ("lottie", "لوتي", "confetti", "sparkle", "loader", "checkmark")):
        q = re.sub(r"(?i)(change|add|use|the|lottie|to|here|أضف|غير|استخدم|لوتي|إلى|هنا)", " ", instr).strip()
        matches = search_lottie(q or instr, limit=1)
        chosen = matches[0]
        lot_el = {
            "kind": "lottie",
            "placement": "badge-row",
            "spec": {"name": chosen["id"], "size": 140, "loop": True, "playbackRate": 1.0},
        }
        visuals = [v for v in visuals if v.get("kind") != "lottie"]
        visuals.append(lot_el)
        action_taken = f"search_lottie({chosen['id']})"

    # 5. Default / Icon requests ("change the icon to a pyramid", "غير الأيقونة إلى هرم")
    else:
        q = re.sub(
            r"(?i)(change|set|replace|add|use|the|icon|to|a|an|here|in|this|scene|أضف|غير|استبدل|الأيقونة|أيقونة|ايقونة|إلى|الى|هنا)",
            " ",
            instr,
        ).strip()
        matches = search_icons(q or instr, limit=1, llm_fallback=True)
        chosen = matches[0]
        icon_el = {
            "kind": "icon",
            "placement": "badge-row",
            "spec": {
                "name": chosen["id"],
                "size": 96,
                "color": "#f5c542",
                "strokeWidth": 2.2,
                "animation": "draw",
            },
        }
        replaced = False
        for idx, v in enumerate(visuals):
            if v.get("kind") == "icon":
                visuals[idx] = icon_el
                replaced = True
                break
        if not replaced:
            visuals.append(icon_el)
        action_taken = f"search_icons({chosen['id']})"

    part["visuals"] = visuals[:3]
    s[target_id] = part
    return {"script": s, "scene": target_id, "action": action_taken, "visuals": part["visuals"]}
