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
    "sea_y": 1340,
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

# Inset map ("HUD") shown over LLM-generated scenes: bottom band, above the caption zone.
HUD_MAP_ZONE = {"top": 995, "left": 240, "width": 600, "svg_height": 330}

# Map stage placements (wide card) used when a map is the main subject.
MAP_STAGE_ZONE = {"full_top": 200, "split_top": 710, "width": 984, "full_svg_height": 980, "bleed_width": 1080, "bleed_svg_height": 1000, "bleed_head_top": 96, "split_head_top": 40, "split_foot_bottom": 24, "bleed_foot_bottom": 110, "split_svg_height": 620}

# LLM scenes are top-heavy: compress above the HUD map, or shift down/enlarge slightly when there is no map (percent / px / ratio x100).
SCENE_FIT = {"compress_pct": 82, "plain_shift_px": 100, "plain_scale_pct": 105, "origin_y_pct": 6}

# Content box that generative-canvas elements are scaled up to fill.
CANVAS_FIT_BOX = {"w": 920, "h": 900, "cx": 540, "cy": 860, "max_pct": 190}

# Beats start their entrance this many frames BEFORE their cut, so the first frame of a scene is never empty.
BEAT_LEAD_FRAMES = 6

# Magnifier lens for tiny places (map viewBox units, 840x520): margin from the visible corner, radius, zoom (x100) at which it appears,
# and the cap (x100) for the main map while the lens shows the close-up.
MAP_LENS = {"margin": 14, "r": 100, "min_zoom_pct": 220, "main_cap_pct": 155}
