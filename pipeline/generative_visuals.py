"""Generative Motion Primitives & LLM Canvas Composer (`pipeline/generative_visuals.py`).

Enables the LLM to generate custom animated motion-graphic scenes from scratch
by composing declarative primitives (shapes, paths, badges, counters, gauges,
connectors, icons, emoji, flags) without writing raw JSX or risking runtime crashes.
Works 100% offline with robust fallback procedural generators for any concept.
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from .config import record_fallback

GENERATIVE_VISUAL_GRAMMAR = """
You are the Lead Motion Graphics Director. Instead of using rigid pre-made templates,
you compose custom animated scenes from scratch using declarative motion primitives.

Canvas Coordinate System:
- Aspect ratio: 9:16 Vertical (1080 x 1920)
- Safe content zone: X: 80..1000 (Center: 540), Y: 320..1420 (Center: 960)
- The bottom area (Y > 1460) is reserved for captions.

Available Primitives:
1. "shape":
   - shape: "rect" | "circle" | "ring" | "triangle" | "pill" | "star" | "shield"
   - x, y, w, h, fill, stroke, strokeWidth, r (radius)
   - motion: "pop" | "rise" | "drop" | "fade" | "scale"
   - loop: "pulse" | "float" | "spin" | "glow" | "breathe" | "shake"
2. "path":
   - curve: "bezier" | "wave" | "mountain" | "arc" | "zigzag"
   - from: [x, y], to: [x, y], control: [x, y]
   - stroke, strokeWidth, strokeDasharray
   - motion: "draw" (animated stroke evolution)
3. "badge":
   - text, sub, icon (e.g. "lucide:flame"), emoji (e.g. "⚠️"), flag (ISO2), bg, borderColor, textColor, size ("sm"|"md"|"lg")
   - motion: "pop" | "drop" | "rise"
4. "counter":
   - from, to, unit, prefix, label, color, fontSize
   - motion: "pop" | "rise"
5. "gauge":
   - value (0..100), label, unit, kind ("linear" | "ring"), width, color
   - motion: "rise" | "pop"
6. "connector":
   - from: [x, y], to: [x, y], label, dashed, color
7. "icon":
   - name (e.g. "lucide:rocket", "ph:sword"), size, color, strokeWidth
8. "text":
   - text, size, color, weight, align, bgChip

Return ONLY valid JSON matching:
{
  "kind": "generative_canvas",
  "title": "عنوان المشهد التوضيحي",
  "subtitle": "شرح فرعي مختصر",
  "accent": "#hexColor",
  "grid": "dots" | "lines" | "radar",
  "elements": [ ... ]
}
"""


def _clean_str(s: Any) -> str:
    return re.sub(r"\s+", " ", str(s or "")).strip()


def _words(s: Any, max_words: int = 5, start_word: int = 0) -> str:
    """Truncates text strictly on whole word boundaries, never slicing mid-word."""
    cleaned = _clean_str(s).strip(".!؟?،:؛- ")
    if not cleaned:
        return ""
    toks = cleaned.split()
    sliced = toks[start_word : start_word + max_words]
    return " ".join(sliced).strip(".!؟?،:؛- ")


def _has_any_whole_word(text: str, words: List[str]) -> bool:
    """Matches whole words in Arabic or English using Unicode non-word boundaries (not substring)."""
    if not text:
        return False
    low = text.lower()
    for w in words:
        w_clean = w.strip().lower()
        if not w_clean:
            continue
        pattern = rf"(?<![\w\u0600-\u06FF])(?:[وفبكل]?(?:ال)?)?{re.escape(w_clean)}(?:ات|ون|ين|ان|ة|ه|ها|هم)?(?![\w\u0600-\u06FF])"
        if re.search(pattern, low):
            return True
    return False



def validate_generative_canvas_spec(spec: Dict[str, Any]) -> Dict[str, Any]:
    """Ensures spec is safe, bounds-checked, and conforms to vertical 9:16 format."""
    out = dict(spec)
    out["kind"] = "generative_canvas"
    out["title"] = _words(out.get("title"), 6)
    out["subtitle"] = _words(out.get("subtitle"), 7)
    if out["subtitle"] == out["title"]:
        out["subtitle"] = ""
    out["accent"] = out.get("accent") or "#f59e0b"
    grid = out.get("grid")
    if grid not in (True, False, "dots", "lines", "radar"):
        out["grid"] = "dots"

    raw_elements = out.get("elements") or []
    cleaned_elements: List[Dict[str, Any]] = []

    for i, el in enumerate(raw_elements[:16]):  # max 16 primitives to keep rendering swift
        if not isinstance(el, dict):
            continue
        e = dict(el)
        e_type = e.get("type", "shape")
        e["type"] = e_type
        # Coordinate sanity bounds
        e["x"] = max(40, min(1040, int(e.get("x", 540))))
        e["y"] = max(100, min(1750, int(e.get("y", 960))))
        e["delay"] = max(0, min(300, int(e.get("delay", i * 4))))
        e["motion"] = e.get("motion", "pop")
        e["loop"] = e.get("loop", "none")
        if e_type == "badge":
            e["text"] = _words(e.get("text"), 6)
            if e.get("sub"):
                e["sub"] = _words(e.get("sub"), 6)
            if not e["text"]:
                continue
        elif e_type == "text":
            e["text"] = _words(e.get("text"), 8)
            if not e["text"]:
                continue
        elif e_type == "counter":
            raw_to = e.get("to") if e.get("to") is not None else (e.get("value") if e.get("value") is not None else e.get("number"))
            try:
                num_str = re.sub(r"[^\d.\-]", "", str(raw_to)) if raw_to is not None else ""
                to_val = float(num_str) if num_str else None
            except Exception:
                to_val = None
            if to_val is None:
                lbl = _words(e.get("label") or e.get("text"), 6)
                if not lbl:
                    continue
                e["type"] = "badge"
                e["text"] = lbl
            else:
                e["to"] = int(to_val) if to_val.is_integer() else to_val
                e["from"] = int(e.get("from", 0)) if isinstance(e.get("from", 0), (int, float)) else 0
        elif e_type == "connector":
            fx = e.get("fromX", 300)
            fy = e.get("fromY", 1000)
            tx = e.get("toX", 780)
            ty = e.get("toY", 800)
            from_pt = e.get("from")
            if isinstance(from_pt, (list, tuple)) and len(from_pt) >= 2:
                fx, fy = from_pt[0], from_pt[1]
            to_pt = e.get("to")
            if isinstance(to_pt, (list, tuple)) and len(to_pt) >= 2:
                tx, ty = to_pt[0], to_pt[1]
            e["from"] = [int(fx), int(fy)]
            e["to"] = [int(tx), int(ty)]
            e["fromX"] = int(fx)
            e["fromY"] = int(fy)
            e["toX"] = int(tx)
            e["toY"] = int(ty)
            if e.get("style") == "dashed":
                e["dashed"] = True
        elif e_type == "path":
            from_pt = e.get("from")
            if not isinstance(from_pt, (list, tuple)) or len(from_pt) < 2:
                e["from"] = [180, 1100]
            to_pt = e.get("to")
            if not isinstance(to_pt, (list, tuple)) or len(to_pt) < 2:
                e["to"] = [900, 600]
        cleaned_elements.append(e)

    out["elements"] = cleaned_elements
    return out


def compose_procedural_scene(topic: str, context: Optional[str] = None) -> Dict[str, Any]:
    """Procedurally generates an intricate scene from primitives based on semantic keywords."""
    t = f"{topic} {context or ''}".lower()

    # 1. بركان / حرارة / صهارة
    if _has_any_whole_word(t, ["بركان", "حمم", "صهارة", "انفجار", "لافا", "volcano", "lava", "eruption", "magma"]):
        return {
            "kind": "generative_canvas",
            "title": "انفجار بركاني مفاجئ وتدفق الحمم",
            "subtitle": "تحليل النشاط البركاني والانبعاثات الحرارية",
            "accent": "#ef4444",
            "grid": "dots",
            "elements": [
                {
                    "type": "shape",
                    "shape": "triangle",
                    "x": 540,
                    "y": 1120,
                    "w": 720,
                    "h: ": 480,
                    "w": 720,
                    "h": 480,
                    "fill": "#1c1917",
                    "stroke": "#78350f",
                    "strokeWidth": 4,
                    "motion": "rise",
                    "delay": 0,
                },
                {
                    "type": "path",
                    "curve": "mountain",
                    "from": [180, 1340],
                    "to": [900, 1340],
                    "stroke": "#f97316",
                    "strokeWidth": 6,
                    "motion": "draw",
                    "delay": 4,
                },
                {
                    "type": "shape",
                    "shape": "circle",
                    "x": 540,
                    "y": 880,
                    "w": 96,
                    "h": 96,
                    "fill": "#ef4444",
                    "stroke": "#fca5a5",
                    "strokeWidth": 3,
                    "motion": "pop",
                    "loop": "pulse",
                    "delay": 8,
                },
                {
                    "type": "counter",
                    "x": 540,
                    "y": 620,
                    "from": 200,
                    "to": 1250,
                    "unit": "°م",
                    "label": "حرارة الحمم البركانية المنصهرة",
                    "color": "#ef4444",
                    "fontSize": 72,
                    "motion": "pop",
                    "delay": 12,
                },
                {
                    "type": "badge",
                    "x": 540,
                    "y": 420,
                    "text": "حالة طوارئ جيولوجية قصوى",
                    "icon": "lucide:flame",
                    "size": "lg",
                    "bg": "rgba(69, 10, 10, 0.95)",
                    "borderColor": "#ef4444",
                    "textColor": "#fef2f2",
                    "motion": "drop",
                    "delay": 16,
                },
                {
                    "type": "gauge",
                    "x": 540,
                    "y": 1420,
                    "value": 88,
                    "label": "كثافة سحب الرماد البركاني",
                    "unit": "%",
                    "color": "#f97316",
                    "width": 740,
                    "motion": "rise",
                    "delay": 20,
                },
            ],
        }

    # 2. حصار بحري / مضيق / سفن / ممرات مائية
    if _has_any_whole_word(t, ["بحر", "بحري", "مضيق", "حصار", "سفينة", "سفن", "ملاحة", "قناة", "قراصنة", "naval", "blockade", "strait", "ship", "maritime"]):
        return {
            "kind": "generative_canvas",
            "title": "إغلاق الممرات البحرية ونقاط الاختناق",
            "subtitle": "شلل حركة الملاحة الدولية في المضيق",
            "accent": "#0ea5e9",
            "grid": "lines",
            "elements": [
                {
                    "type": "path",
                    "curve": "wave",
                    "from": [100, 1020],
                    "to": [980, 1020],
                    "stroke": "#0284c7",
                    "strokeWidth": 8,
                    "motion": "draw",
                    "delay": 0,
                },
                {
                    "type": "shape",
                    "shape": "rect",
                    "x": 220,
                    "y": 1020,
                    "w": 180,
                    "h": 360,
                    "r": 24,
                    "fill": "rgba(30, 41, 59, 0.9)",
                    "stroke": "#475569",
                    "strokeWidth": 2,
                    "motion": "slide_right",
                    "delay": 4,
                },
                {
                    "type": "shape",
                    "shape": "rect",
                    "x": 860,
                    "y": 1020,
                    "w": 180,
                    "h": 360,
                    "r": 24,
                    "fill": "rgba(30, 41, 59, 0.9)",
                    "stroke": "#475569",
                    "strokeWidth": 2,
                    "motion": "slide_left",
                    "delay": 4,
                },
                {
                    "type": "connector",
                    "from": [310, 1020],
                    "to": [770, 1020],
                    "label": "منطقة الحظر العسكري",
                    "dashed": True,
                    "color": "#ef4444",
                    "strokeWidth": 4,
                    "delay": 10,
                },
                {
                    "type": "icon",
                    "name": "lucide:anchor",
                    "x": 540,
                    "y": 920,
                    "size": 130,
                    "color": "#38bdf8",
                    "motion": "pop",
                    "loop": "float",
                    "delay": 14,
                },
                {
                    "type": "counter",
                    "x": 540,
                    "y": 640,
                    "from": 0,
                    "to": 4200,
                    "unit": "سفينة / شهر",
                    "label": "حجم التجارة البحرية المهددة",
                    "color": "#38bdf8",
                    "fontSize": 64,
                    "motion": "pop",
                    "delay": 18,
                },
                {
                    "type": "badge",
                    "x": 540,
                    "y": 420,
                    "text": "إغلاق الممر المائي الاستراتيجي",
                    "icon": "lucide:alert-triangle",
                    "size": "lg",
                    "bg": "rgba(15, 23, 42, 0.95)",
                    "borderColor": "#0ea5e9",
                    "textColor": "#ffffff",
                    "motion": "drop",
                    "delay": 22,
                },
            ],
        }

    # 3. ذكاء اصطناعي / شبكة عصبية / حوسبة / بيانات
    if _has_any_whole_word(t, ["ذكاء", "اصطناعي", "عصبية", "بيانات", "حوسبة", "تكنولوجيا", "خوارزمية", "روبوت", "ai", "neural", "computing", "tech"]):
        return {
            "kind": "generative_canvas",
            "title": "ثورة الذكاء الاصطناعي الفائق",
            "subtitle": "معالجة بلايين المعاملات في أجزاء من الثانية",
            "accent": "#8b5cf6",
            "grid": "radar",
            "elements": [
                {
                    "type": "shape",
                    "shape": "circle",
                    "x": 540,
                    "y": 960,
                    "w": 180,
                    "h": 180,
                    "fill": "rgba(139, 92, 246, 0.15)",
                    "stroke": "#a78bfa",
                    "strokeWidth": 3,
                    "motion": "pop",
                    "loop": "pulse",
                    "delay": 0,
                },
                {
                    "type": "icon",
                    "name": "lucide:brain",
                    "x": 540,
                    "y": 960,
                    "size": 110,
                    "color": "#c084fc",
                    "motion": "pop",
                    "delay": 4,
                },
                {
                    "type": "connector",
                    "from": [540, 960],
                    "to": [240, 780],
                    "label": "التعلم العميق",
                    "color": "#a78bfa",
                    "dashed": True,
                    "delay": 8,
                },
                {
                    "type": "connector",
                    "from": [540, 960],
                    "to": [840, 780],
                    "label": "الشبكات التوليدية",
                    "color": "#a78bfa",
                    "dashed": True,
                    "delay": 10,
                },
                {
                    "type": "connector",
                    "from": [540, 960],
                    "to": [540, 1260],
                    "label": "البيانات الضخمة",
                    "color": "#a78bfa",
                    "dashed": True,
                    "delay": 12,
                },
                {
                    "type": "counter",
                    "x": 540,
                    "y": 580,
                    "from": 10,
                    "to": 175,
                    "unit": "تريليون عملية",
                    "label": "قدرة المعالجة الحسابية",
                    "color": "#c084fc",
                    "fontSize": 64,
                    "motion": "pop",
                    "delay": 16,
                },
                {
                    "type": "gauge",
                    "x": 540,
                    "y": 1420,
                    "value": 99,
                    "label": "دقة التنبؤ والتحليل الذاتي",
                    "unit": "%",
                    "color": "#8b5cf6",
                    "width": 720,
                    "motion": "rise",
                    "delay": 20,
                },
            ],
        }

    # 4. تضخم / صعود الأسعار / صاروخ اقتصادي
    if _has_any_whole_word(t, ["تضخم", "أسعار", "غلاء", "عملة", "اقتصادي", "صاروخ", "inflation", "rocket", "prices", "economy"]):
        return {
            "kind": "generative_canvas",
            "title": "انفجار معدلات التضخم والأسعار",
            "subtitle": "قفزة غير مسبوقة في كلفة المعيشة",
            "accent": "#f59e0b",
            "grid": "lines",
            "elements": [
                {
                    "type": "path",
                    "curve": "zigzag",
                    "from": [180, 1300],
                    "to": [880, 760],
                    "stroke": "#ef4444",
                    "strokeWidth": 8,
                    "motion": "draw",
                    "delay": 0,
                },
                {
                    "type": "icon",
                    "name": "lucide:rocket",
                    "x": 880,
                    "y": 760,
                    "size": 110,
                    "color": "#f59e0b",
                    "motion": "pop",
                    "loop": "shake",
                    "delay": 8,
                },
                {
                    "type": "counter",
                    "x": 540,
                    "y": 560,
                    "from": 4,
                    "to": 148,
                    "unit": "%",
                    "prefix": "+",
                    "label": "المعدل السنوي لارتفاع الأسعار",
                    "color": "#ef4444",
                    "fontSize": 78,
                    "motion": "pop",
                    "delay": 12,
                },
                {
                    "type": "badge",
                    "x": 540,
                    "y": 380,
                    "text": "تآكل القوة الشرائية للأجور",
                    "icon": "lucide:trending-up",
                    "size": "lg",
                    "bg": "rgba(40, 10, 10, 0.95)",
                    "borderColor": "#ef4444",
                    "textColor": "#fee2e2",
                    "motion": "drop",
                    "delay": 16,
                },
                {
                    "type": "gauge",
                    "x": 540,
                    "y": 1420,
                    "value": 74,
                    "label": "نسبة الأسر المتأثرة مباشرة بالأزمة",
                    "unit": "%",
                    "color": "#f59e0b",
                    "width": 720,
                    "motion": "rise",
                    "delay": 20,
                },
            ],
        }

    # 5. حضارات قديمة / إمبراطوريات / آثار / معابد / أهرامات
    if _has_any_whole_word(t, ["حضارة", "حضارات", "إمبراطورية", "أثر", "آثار", "معبد", "أهرام", "أهرامات", "كنز", "كنوز", "فراعنة", "فرعون", "بابل", "آشور", "سومر", "مايا", "إنكا", "رومان", "إغريق", "civilization", "empire", "ancient", "ruin", "temple"]):
        nums = re.findall(r"\d+[\d,.]*", topic)
        title_txt = _words(context, 5) or _words(topic, 5) or "الأسرار التاريخية"
        badge_top = _words(topic, 5) if _words(topic, 5) != title_txt else (_words(topic, 5, 5) or "معالم خالدة عبر العصور")
        elements = [
            {
                "type": "shape",
                "shape": "ring",
                "x": 540,
                "y": 860,
                "w": 460,
                "stroke": "#f59e0b",
                "strokeWidth": 3,
                "fill": "rgba(245, 158, 11, 0.05)",
                "motion": "pop",
                "loop": "pulse",
                "delay": 0,
            },
            {
                "type": "icon",
                "name": "lucide:landmark",
                "x": 540,
                "y": 860,
                "size": 140,
                "color": "#f59e0b",
                "motion": "pop",
                "delay": 5,
            },
            {
                "type": "badge",
                "x": 540,
                "y": 560,
                "text": badge_top or "إرث تاريخي عريق",
                "icon": "lucide:history",
                "size": "lg",
                "bg": "rgba(15, 23, 42, 0.95)",
                "borderColor": "#f59e0b",
                "textColor": "#fef3c7",
                "motion": "drop",
                "delay": 10,
            },
        ]
        if nums:
            elements.append({
                "type": "counter",
                "x": 540,
                "y": 1240,
                "from": 0,
                "to": float(nums[0].replace(",", "")),
                "unit": "عام" if len(nums[0]) >= 3 else "",
                "label": "الامتداد الزمني والتاريخي",
                "color": "#f59e0b",
                "fontSize": 68,
                "motion": "pop",
                "delay": 15,
            })
        else:
            elements.append({
                "type": "badge",
                "x": 540,
                "y": 1180,
                "text": _words(topic, 6, 5) or "محطة فاصلة في التاريخ",
                "icon": "lucide:hourglass",
                "size": "md",
                "bg": "rgba(245, 158, 11, 0.15)",
                "borderColor": "#f59e0b",
                "textColor": "#fef3c7",
                "motion": "rise",
                "delay": 15,
            })
        return {
            "kind": "generative_canvas",
            "title": title_txt,
            "subtitle": _words(context, 6) if context and _words(context, 6) != title_txt else "",
            "accent": "#f59e0b",
            "grid": "radar",
            "elements": elements,
        }

    # 6. فيضانات / مياه / غرق / سيول / أمطار
    if _has_any_whole_word(t, ["فيضان", "فيضانات", "غرق", "طوفان", "أمطار", "مياه", "أنهار", "سدود", "flood", "water", "rain", "deluge", "river"]):
        title_txt = _words(context, 5) or _words(topic, 5) or "تدفق المياه والفيضانات"
        return {
            "kind": "generative_canvas",
            "title": title_txt,
            "subtitle": "",
            "accent": "#0ea5e9",
            "grid": "lines",
            "elements": [
                {
                    "type": "path",
                    "curve": "wave",
                    "from": [140, 1000],
                    "to": [940, 1000],
                    "stroke": "#0ea5e9",
                    "strokeWidth": 8,
                    "motion": "draw",
                    "delay": 0,
                },
                {
                    "type": "icon",
                    "name": "lucide:waves",
                    "x": 540,
                    "y": 800,
                    "size": 130,
                    "color": "#38bdf8",
                    "motion": "pop",
                    "loop": "pulse",
                    "delay": 5,
                },
                {
                    "type": "badge",
                    "x": 540,
                    "y": 520,
                    "text": _words(topic, 5) or "طوفان جارف دمّر مصادر الحياة",
                    "icon": "lucide:droplets",
                    "size": "lg",
                    "bg": "rgba(8, 20, 36, 0.95)",
                    "borderColor": "#0ea5e9",
                    "textColor": "#e0f2fe",
                    "motion": "drop",
                    "delay": 10,
                },
                {
                    "type": "gauge",
                    "x": 540,
                    "y": 1320,
                    "value": 92,
                    "label": "منسوب تدفق السيول الجارفة",
                    "unit": "%",
                    "color": "#38bdf8",
                    "width": 720,
                    "motion": "rise",
                    "delay": 16,
                },
            ],
        }

    # 7. محاصيل / غذاء / زراعة / مخازن / قمح / جوع
    if _has_any_whole_word(t, ["محاصيل", "غذاء", "زراعة", "مخازن", "قمح", "جوع", "مجاعة", "إنتاجية", "طعام", "غذائية", "crops", "agriculture", "food", "famine", "grain", "storage"]):
        nums = re.findall(r"\d+[\d,.]*", topic)
        val = float(nums[0].replace(",", "")) if nums else 35
        return {
            "kind": "generative_canvas",
            "title": _words(context, 5) or _words(topic, 5) or "أزمة الإمداد الغذائي",
            "subtitle": "",
            "accent": "#eab308",
            "grid": "dots",
            "elements": [
                {
                    "type": "shape",
                    "shape": "rect",
                    "x": 540,
                    "y": 920,
                    "w": 760,
                    "h": 460,
                    "r": 28,
                    "fill": "rgba(15, 23, 42, 0.85)",
                    "stroke": "#eab308",
                    "strokeWidth": 2.5,
                    "motion": "pop",
                    "delay": 0,
                },
                {
                    "type": "icon",
                    "name": "lucide:sprout",
                    "x": 540,
                    "y": 780,
                    "size": 120,
                    "color": "#eab308",
                    "motion": "pop",
                    "loop": "pulse",
                    "delay": 5,
                },
                {
                    "type": "badge",
                    "x": 540,
                    "y": 480,
                    "text": _words(topic, 5) or "تراجع إنتاجية المحاصيل الحيوية",
                    "icon": "lucide:alert-triangle",
                    "size": "lg",
                    "bg": "rgba(30, 20, 10, 0.95)",
                    "borderColor": "#eab308",
                    "textColor": "#fef9c3",
                    "motion": "drop",
                    "delay": 10,
                },
                {
                    "type": "counter",
                    "x": 540,
                    "y": 1040,
                    "from": 0,
                    "to": val,
                    "prefix": "-" if "%" in topic or "خفض" in topic or "نقص" in topic else "",
                    "unit": "%" if "%" in topic or val <= 100 else "",
                    "label": "نسبة العجز في المحاصيل والمخزون",
                    "color": "#ef4444" if ("خفض" in topic or "نقص" in topic) else "#eab308",
                    "fontSize": 72,
                    "motion": "pop",
                    "delay": 15,
                },
            ],
        }

    # 8. دمار / انهيار كامل / سقوط / موت / نهاية الحضارة
    if _has_any_whole_word(t, ["دمار", "انهيار", "سقوط", "هلاك", "موت", "نهاية", "فناء", "زوال", "collapse", "fall", "destruction", "extinction"]):
        return {
            "kind": "generative_canvas",
            "title": _words(context, 5) or _words(topic, 5) or "الانهيار والاندثار الكامل",
            "subtitle": "",
            "accent": "#ef4444",
            "grid": "radar",
            "elements": [
                {
                    "type": "shape",
                    "shape": "circle",
                    "x": 540,
                    "y": 860,
                    "w": 380,
                    "h": 380,
                    "fill": "rgba(239, 68, 68, 0.08)",
                    "stroke": "#ef4444",
                    "strokeWidth": 3,
                    "motion": "pop",
                    "loop": "pulse",
                    "delay": 0,
                },
                {
                    "type": "icon",
                    "name": "lucide:skull",
                    "x": 540,
                    "y": 860,
                    "size": 130,
                    "color": "#ef4444",
                    "motion": "pop",
                    "delay": 5,
                },
                {
                    "type": "badge",
                    "x": 540,
                    "y": 560,
                    "text": _words(topic, 5) or "نهاية مأساوية وانهيار شامل",
                    "icon": "lucide:alert-octagon",
                    "size": "lg",
                    "bg": "rgba(40, 10, 10, 0.95)",
                    "borderColor": "#ef4444",
                    "textColor": "#fee2e2",
                    "motion": "drop",
                    "delay": 10,
                },
                {
                    "type": "badge",
                    "x": 540,
                    "y": 1200,
                    "text": _words(topic, 6, 5) or "نقطة تحول حاسمة",
                    "icon": "lucide:flame",
                    "size": "md",
                    "bg": "rgba(239, 68, 68, 0.15)",
                    "borderColor": "#ef4444",
                    "textColor": "#fca5a5",
                    "motion": "rise",
                    "delay": 15,
                },
            ],
        }

    # 9. سياق عام ذكي ومحدد (Clean Semantic Spotlight)
    nums = re.findall(r"\d+[\d,.]*", topic)
    icon_name = "lucide:sparkles"
    if _has_any_whole_word(t, ["سؤال", "لماذا", "كيف", "لغز", "سر", "بحث", "تعليقات", "شارك", "اكتب"]):
        icon_name = "lucide:help-circle"
    elif _has_any_whole_word(t, ["شعب", "بشر", "سكان", "مجتمع", "قبيلة"]):
        icon_name = "lucide:users"
    elif _has_any_whole_word(t, ["ملك", "حكم", "سلطة", "دولة", "سيادة", "دستور"]):
        icon_name = "lucide:crown"
    elif _has_any_whole_word(t, ["مدينة", "عاصمة", "عاصمتين", "بناء", "معمار"]):
        icon_name = "lucide:landmark"

    title_txt = _words(context, 5) or _words(topic, 5) or "تحليل المشهد"
    first_chunk = _words(topic, 5)
    second_chunk = _words(topic, 5, 5)
    top_badge_txt = first_chunk if first_chunk and first_chunk != title_txt else (second_chunk or title_txt)
    bottom_badge_txt = second_chunk if second_chunk and second_chunk != top_badge_txt else (_words(topic, 5, 10) or "خلاصة المشهد")

    elements = [
        {
            "type": "shape",
            "shape": "ring",
            "x": 540,
            "y": 880,
            "w": 420,
            "stroke": "#38bdf8",
            "strokeWidth": 2.5,
            "fill": "rgba(56, 189, 248, 0.05)",
            "motion": "pop",
            "loop": "pulse",
            "delay": 0,
        },
        {
            "type": "icon",
            "name": icon_name,
            "x": 540,
            "y": 880,
            "size": 130,
            "color": "#38bdf8",
            "motion": "pop",
            "delay": 5,
        },
        {
            "type": "badge",
            "x": 540,
            "y": 560,
            "text": top_badge_txt,
            "icon": icon_name,
            "size": "lg",
            "bg": "rgba(15, 23, 42, 0.95)",
            "borderColor": "#38bdf8",
            "textColor": "#ffffff",
            "motion": "drop",
            "delay": 10,
        },
    ]

    if nums:
        elements.append({
            "type": "counter",
            "x": 540,
            "y": 1240,
            "from": 0,
            "to": float(nums[0].replace(",", "")),
            "unit": "%" if "%" in topic else "",
            "label": bottom_badge_txt,
            "color": "#38bdf8",
            "fontSize": 68,
            "motion": "pop",
            "delay": 15,
        })
    else:
        elements.append({
            "type": "badge",
            "x": 540,
            "y": 1180,
            "text": bottom_badge_txt,
            "icon": "lucide:sparkles",
            "size": "md",
            "bg": "rgba(56, 189, 248, 0.14)",
            "borderColor": "#38bdf8",
            "textColor": "#bae6fd",
            "motion": "rise",
            "delay": 15,
        })

    return {
        "kind": "generative_canvas",
        "title": title_txt,
        "subtitle": "",
        "accent": "#38bdf8",
        "grid": "dots",
        "elements": elements,
    }


def compose_generative_canvas(
    prompt_or_sentence: str,
    context: Optional[str] = None,
    is_fallback: bool = False,
    fallback_reason: str = "",
    beat_id: str = "generative_canvas",
) -> Dict[str, Any]:
    """Generates a complete GenerativeCanvas beat.

    If `is_fallback` is True, logs an explicit fallback warning, marks `_fallback: True`,
    and raises in DEBUG=1 mode.
    """
    raw_spec = compose_procedural_scene(prompt_or_sentence, context)
    validated = validate_generative_canvas_spec(raw_spec)
    if is_fallback:
        record_fallback(fallback_reason or "generative_canvas_fallback", beat_id=beat_id, beat=validated)
    return validated
