"""Central Layout Contract (`pipeline/layout.py`).

Shared 9:16 (1080x1920) vertical canvas layout zones and coordinates.
Must remain 100% identical to `remotion/src/layout.ts`.
"""

CANVAS_WIDTH = 1080
CANVAS_HEIGHT = 1920

SAFE_TOP = 72
SAFE_BOTTOM = 1780

HEADLINE_ZONE = {
    "top": 140,
    "bottom": 280,
    "center_y": 210,
    "left": 80,
    "right": 80,
}

BEAT_ZONE = {
    "top": 280,
    "bottom": 1380,
    "center_y": 860,
    "left": 80,
    "right": 80,
    "title_top": 240,
    "sub_title_top": 220,
    "chart_title_top": 420,
    "corner_top": 240,
    "corner_bottom": 1220,
    "peak_y": 420,
    "sea_y": 1480,
    "list_top_with_headline": 440,
    "list_top_no_headline": 340,
    "zero": 0,
    "pin_offset": 20,
    "magnifier_bottom": 8,
}

CAPTION_ZONE = {
    "top": 1420,
    "bottom": 1760,
    "center_y": 1550,
    "left": 40,
    "right": 40,
}
