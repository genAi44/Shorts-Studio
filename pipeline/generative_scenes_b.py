"""Split from `pipeline/generative_visuals.py` (re-exported there); see that module."""
from __future__ import annotations
import re
from .generative_visuals import _words  # noqa: E402


def _scene_inflation():
    """Branch of `compose_procedural_scene`."""
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


def _scene_civilization(context, topic):
    """Branch of `compose_procedural_scene`."""
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


def _scene_flood(context, topic):
    """Branch of `compose_procedural_scene`."""
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


def _scene_crops(context, topic):
    """Branch of `compose_procedural_scene`."""
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


def _scene_collapse(context, topic):
    """Branch of `compose_procedural_scene`."""
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
