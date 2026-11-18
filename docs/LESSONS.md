# Lessons Learned — Visual Frame Review

Source: frame-by-frame audit of V1, V2, V3 (71 frames) documented in `docs/FRAME_REVIEW.md`.

---

## L-01: Hardcoded Fallback Icon Causes Cross-Video Repetition

**What happened:** Monument/pillar SVG (`icons/history/monument.svg`) appeared in all 3 unrelated videos.

**Root cause:** `pipeline/icons.py::_find_icon()` returned this path as the final fallback for ANY unknown icon name.

**Fix applied:** Replaced hardcoded fallback with a 7-item diverse pool, selected by `abs(hash(beat_id)) % len(pool)`. Also tries `KEYWORD_MAP` against beat narration before falling back.

**Prevention rule:** No single icon path may be a hardcoded fallback. The fallback pool must have ≥ 5 items.

---

## L-02: Process-Network Template Overuse

**What happened:** 3-node network diagram appeared in 18+ frames across 3 videos, including geographic content about country sizes.

**Root cause 1:** `classify_narration_intent` matched keywords "شبكة", "نظام", "مسار", "رحلة" as `has_process` — these words appear in many non-process contexts.

**Root cause 2:** `generate_scene_tsx` fallback used `generators[scene_index % len]` which deterministically hit `_generate_process_network_tsx` on even scene indices.

**Fix applied:** Removed overly broad keywords from `has_process`. Fallback now uses `safe_generators` list that excludes `_generate_process_network_tsx`.

**Prevention rule:** `has_process` keywords must be unambiguous (steps, phases, flow). Generic system/network words are excluded.

---

## L-03: Edge-Bleed Vertical Progress Bar

**What happened:** A 12px maroon/colored bar appeared at the right (and sometimes left) screen edge across 45+ frames.

**Root cause:** `deco.progress === 'side'` in `remotion/src/layers.tsx` placed a bar at `right: 0`, which is inside the 120px safe zone.

**Fix applied:**
1. Removed `"side"` from options in `pipeline/style.py`
2. For any existing specs with `progress: "side"`, the renderer now draws it at `right: 60, width: 8` (inset)

**Prevention rule:** `deco.progress` options are `["none", "top", "bottom"]` only.

---

## L-04: Text-Only Scenes

**What happened:** 12 frames across V1–V3 showed only text on a colored background — no icons, no graphics.

**Root cause:** Pipeline had no enforcement of Rule 1.2.

**Fix applied:** `pipeline/visual_qa.py::_audit_scene()` check 0b: if all beats have `kind` in `{text, text_reveal, text_only, caption}` and no `elements/icon/nodes`, it's a `text_only_scene` error (score -25).

**Prevention rule:** Every scene spec must have ≥1 non-text visual beat before passing QA.

---

## L-05: Raster Images in Spec (Rule 1.1 Violation)

**What happened:** Photo references appeared in some scene specs despite the vector-only rule.

**Root cause:** No automated scan for raster file extensions in spec JSON.

**Fix applied:** `pipeline/visual_qa.py::_scan_rasters()` recursively finds any value ending in `.jpg/.png/.webp/.gif/.jpeg` and fails the scene with score -30.

**Prevention rule:** Never pass raster paths to scene specs. Use SVG or CSS/SVG gradients only.

---

## L-06: Number Inconsistency Across Counter Animations

**What happened:** Russia's area shown as 17,000,000 → 16,895,998 → 16,874,697 across different scenes of the same video.

**Root cause:** When narration uses Arabic word-numbers ("سبعة عشر مليون"), `_extract_numbers()` returned empty (no digits to parse). The LLM then "looked up" the value from training data, returning slightly different values per scene.

**Fix applied:** `_AR_WORD_NUMBERS` lookup table added. `_extract_numbers()` now parses Arabic word-form numbers before the digit regex pass. "سبعة عشر مليون" → 17,000,000.

**Prevention rule:** Any Arabic text referencing a known quantity must yield a consistent number from `_extract_numbers`. LLM prompt already requires STRICT FACTUAL GROUNDING.

---

## L-07: Geographic Content Without a Map

**What happened:** Scenes about countries/regions showed location pins on a plain background instead of an actual SVG map.

**Root cause:** `has_process` and other classifiers triggered before geographic archetype check; map rendering path was bypassed.

**Fix applied:** Narrowed `has_process` keywords so geo scenes route to metropolis/data-metric generators instead.

**Note for future:** Add explicit geo-archetype detection: if `scene.entities` contains `iso2` codes and narrative is geographic, force a `VectorGeoEngine` map render.

---

## L-08: Same Template Across Consecutive Videos

**What happened:** V2 and V3 (both unrelated topics) used identical Template B — same olive/tan background, same crimson accent, same card style.

**Root cause:** `pipeline/style.py` random template selection has no cross-video memory, so the same template can be drawn repeatedly.

**Prevention rule (not yet implemented):** Store the last-used palette in a project-level config. On next video, bias away from the same template signature.

---

## L-09: Design Repetition Within a Video

**What happened:** Same beat kind (e.g., `generative_canvas` → process_network) appeared 6+ times in a single video.

**Fix applied:** `pipeline/visual_qa.py::_audit_design_repetition()` flags any beat kind (excluding text/caption) appearing > 2 times in the full spec.

**Prevention rule:** Storyboard agent must diversify beat kinds. Max 2 uses of any single visual template per video.

---

## Summary Table

| # | Issue | Severity | Fix Status | File |
|---|-------|----------|------------|------|
| L-01 | Hardcoded monument fallback | Critical | ✅ Fixed | `pipeline/icons.py` |
| L-02 | Process-network overuse | Major | ✅ Fixed | `pipeline/storyteller.py` |
| L-03 | Edge-bleed progress bar | Major | ✅ Fixed | `pipeline/style.py`, `remotion/src/layers.tsx` |
| L-04 | Text-only scenes | Major | ✅ Fixed | `pipeline/visual_qa.py` |
| L-05 | Raster in spec | Critical | ✅ Fixed | `pipeline/visual_qa.py` |
| L-06 | Number inconsistency | Major | ✅ Fixed | `pipeline/storyteller.py` |
| L-07 | Geo without map | Minor | ⚠️ Partial | `pipeline/storyteller.py` |
| L-08 | Same template cross-video | Minor | ⚠️ Pending | `pipeline/style.py` |
| L-09 | Beat kind repetition | Major | ✅ Fixed | `pipeline/visual_qa.py` |
