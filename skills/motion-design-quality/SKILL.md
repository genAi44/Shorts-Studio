---
name: motion-design-quality
description: Visual QA and motion design rules for 9:16 vertical Shorts: max 2-3 visual elements per scene, consistent icon style per video, no emoji spam, readable contrast, and safe 9:16 margins.
---

# Motion Design Quality & QA Rules (`motion-design-quality`)

Every storyboard and rendered scene is validated against these strict visual quality rules (`qa_visual_review` in `pipeline/visual_tools.py`).

## Core Rules

1. **Limit to 2–3 Visual Elements per Scene**:
   - Never place more than 3 visual elements (`scene.visuals`) in a single scene.
   - If a full-bleed chart (`kind: "chart"`) or map (`kind: "map_pin"`) is active in the center, keep supporting elements in the top `badge-row` (`y = 230`) so they never collide with the central focal point.

2. **Consistent Icon Style per Video**:
   - Pick **one** Iconify collection (`lucide`, `ph`, or `tabler`) for the entire video and lock all `search_icons` queries in that video to that prefix. Never mix thin line icons (`lucide`) with filled/duotone icons from another set in the same video.

3. **No Emoji Spam**:
   - Maximum **1 `<Emoji />` per scene**.
   - Always render emoji from the bundled SVG catalog (`packages/assets/emoji/`), never as raw text.

4. **Readable Contrast & Arabic Shaping**:
   - Maintain WCAG AA/AAA contrast (`>= 4.5:1`) for all text and labels against dark navy/charcoal cards (`rgba(11, 18, 32, 0.90)`).
   - Never animate Arabic text per-character; animate **per-word** only.
   - Ensure SVG icons inside dark badges use high-contrast gold (`#f5c542`) or white (`#f8fafc`).

5. **Safe Margins for 9:16 Vertical Video (`1080×1920`)**:
   - **Horizontal Safe Zone**: `x ∈ [90, 990]` (90px left/right padding to avoid platform UI buttons).
   - **Top Headline Zone**: `y ∈ [180, 320]`.
   - **Primary Visual / Chart Canvas Zone**: `y ∈ [340, 1380]`.
   - **Bottom Caption Zone**: `y ∈ [1440, 1760]` (reserved for synchronized captions).

---

## Running Visual QA Check

```python
from pipeline.visual_tools import qa_visual_review

issues = qa_visual_review(spec)
for issue in issues:
    print(issue["level"], issue["where"], issue["msg"])
```

