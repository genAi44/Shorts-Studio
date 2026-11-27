"""Split from `pipeline/storyteller.py` (re-exported there); see that module."""
from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
import os
import re
import sys
from .storyteller import _TSX_THEME, _clean_id, _clean_text, _theme_block, logger  # noqa: E402


def _should_use_llm_tsx() -> bool:
    val = os.environ.get("DYNAMIC_TSX_LLM", "").strip().lower()
    if val in ("0", "false", "no", "off"):
        return False
    if val == "force":
        return True
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return False
    main_mod = sys.modules.get("__main__")
    if getattr(main_mod, "__package__", None) == "unittest":
        return False
    return True


_LLM_TSX_SYSTEM = """You are an elite AI Video Architect, Creative Director, Documentary Infographics Designer, and Remotion Motion Graphics Engineer.
Every scene begins with a BLANK VISUAL CANVAS (1080x1920 vertical 9:16).
Your mission is to write 100% original React + Remotion TSX code that visually explains the EXACT historical, geographic, or scientific meaning of the spoken Arabic narration across the full duration of the scene.

TECHNICAL STACK (STRICT):
- Already imported symbols: React, AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig, Easing
- Inline <svg width={1080} height={1920} viewBox="0 0 1080 1920"> with rich, domain-specific SVG illustrations, diagrams, architectural cross-sections, topographic elevation profiles, and historical emblems.
- CRITICAL SVG STRUCTURE RULE: EVERY `<foreignObject x={...} y={...} width={...} height={...}>` MUST be placed INSIDE `<svg width={1080} height={1920} viewBox="0 0 1080 1920">...</svg>`! NEVER close `</svg>` before your `<foreignObject>` cards — `<foreignObject>` outside `<svg>` breaks positioning completely.
- STRICT FACTUAL GROUNDING: Every city, country, year, percentage, count, or number you display MUST come from the Video Title, Verified Facts, or Scene Narration. NEVER invent fake statistics, percentages, or counts (e.g., do NOT make up '96%', '94%', or '12' if not stated in the facts/narration), and NEVER invent unrelated historical cities or dates! Never truncate headlines with '...' or leave any card/banner empty.
- CSS transforms and <foreignObject x={...} y={...} width={...} height={...}> wrapping an inner <div dir="rtl" lang="ar" style={{fontFamily: "'Cairo', 'Noto Kufi Arabic', sans-serif", ...}}> for crisp Arabic typography and structured infographic cards.
- CRITICAL TS RULE FOR <foreignObject>: NEVER put `dir` or `lang` attributes on `<foreignObject>` itself — TypeScript `SVGProps<SVGForeignObjectElement>` rejects them! ALWAYS put `dir="rtl" lang="ar"` on the child `<div>` inside `<foreignObject>`.
- CRITICAL TS RULE FOR `interpolate`: NEVER pass `{clamp: true}`! Always use `{extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}`.

ARABIC TYPOGRAPHY & LEGIBILITY RULES (ZERO GARBLED OR INVERTED TEXT):
- NEVER use SVG `<text>` for Arabic words, and NEVER use `writingMode="tb"` or `writing-mode: vertical-rl`! Vertical text breaks Arabic letter joining and reverses glyph order (producing unreadable broken letters). Always render Arabic strings horizontally inside `<foreignObject><div dir="rtl" lang="ar" style={{fontFamily: "'Cairo', 'Noto Kufi Arabic', sans-serif", ...}}>`.
- NEVER apply negative scale transforms (`scale(-1, 1)` or `scale(1, Math.cos(...))` where `cos` becomes negative) to any group containing text, numbers, or years (e.g., never flip `1960` into mirrored `0691`!). If animating a card flip, use `Math.max(0.15, Math.abs(Math.cos(...)))`.
- High-Contrast Readability: Every text label, subtitle, and number MUST sit inside a high-contrast dark glass card (`background: 'rgba(6, 12, 24, 0.94)'`, `border: '1.5px solid ...'`, `borderRadius: 16`, `color: '#ffffff'` or `'#fde047'`). NEVER place gray text on a dark blue/black background, NEVER let background illustrations bleed through text cards, NEVER let any bar or card extend past `x = 980` (`width <= 920` from `x = 60`), and NEVER use `fontSize < 32px` for any readable card text (phone screens: 26px is unreadable) or linger at `opacity < 0.92` once a card has entered (snap card opacity from 0 -> 1 within 5-6 frames)!
- Wide Numeric Containers & Fast Counter Completion: Large counters (e.g. `14,000,000` or `1,600+`) MUST be inside a `<foreignObject>` at least `560px` wide (`x={260} width={560}`) with `direction: 'ltr'` and `whiteSpace: 'nowrap'` so digits are NEVER clipped. Quantity/percentage counters MUST finish rolling up to their final target value by `progress = 0.45`, and NEVER linger at `0` or `0%` after `p = 0.05` (start from `Math.round(target * 0.4)` -> `target`!). CRITICAL FOR YEARS: NEVER animate or roll historical years (e.g. `1945`, `1961`, `1989`, `2024`) with `interpolate()`! Always render the exact historical year string immediately from frame 0 (e.g. `1989`) with a crisp scale/opacity entrance so the viewer never sees a wrong intermediate year like `1959` or `1931`!

MULTI-PHASE VISUAL STORYTELLING & ANTI-OVERLAP RULES (MANDATORY):
Each scene lasts 5 to 9 seconds (`dur` frames, `p = frame / dur` from `0` to `1`) and covers a complete spoken Arabic sentence with 2–3 clauses (Phase 1: `0.00..0.35`, Phase 2: `0.35..0.70`, Phase 3: `0.70..1.00`):
- Immediate Visibility at Frame 0 (ZERO DEAD AIR): The scene background, Top Headline Banner (`y: 95..230`), AND the primary hero SVG visual stage MUST ALL be visible starting from `frame = 0` (`opacity` starting at `0.85 -> 1.0` within 8 frames)! NEVER hide the main illustration behind `ph2` (`p = 0.30+`) leaving an empty screen for the first 3–4 seconds!
- Phase 1 (`p: 0.0 -> 0.35`): Establish the primary visual subject (iconic SVG illustration, scale, beaker, monument, or diagram) + unified Top Headline Banner (`x: 60..1020, y: 95..230`, main title `fontSize: 52px..60px`, subtitle `fontSize: 32px`, `#fde047`).
- Phase 2 (`p: 0.35 -> 0.70`): Reveal the second layer of evidence/comparison synced to the middle clause (e.g., proportional comparison bars where bar width is strictly `(value / maxValue) * maxBarWidth`, dated historical milestone, or metric counter).
- Phase 3 (`p: 0.70 -> 1.00`): Reveal the final takeaway callout or interactive prompt card. For `cta` / `loop` scenes, include 2–3 concise visual recap chips + animated callout emblem so the ending feels rich and energetic, never just one lone icon.
- ZERO CARD OR ILLUSTRATION COLLISION & ZERO DEAD CANVAS SPACE (MANDATORY):
  * NEVER leave 50%+ of the screen as a flat black/dark void with a tiny icon or small card floating in the middle!
  * ALWAYS render a multi-layered atmospheric SVG backdrop behind your scene: radial spotlight glow (`<radialGradient>`), subtle architectural/topographic depth lines or horizon ground plane, and soft ambient light beams matching the topic mood. NEVER scatter random stray `+`/`×`/`★` stars or confetti particles in empty corners.
  * Scale hero SVG illustrations generously (`width: 500..820px`, `height: 380..540px`) and use full-width structured cards (`x: 60, width: 960` in Slot B/C) so the visual stage (`y: 110..1430`) feels rich (the lowest card/illustration MUST end at `y >= 1250`; never leave the bottom third empty), balanced, and cinematic from top to bottom.
  * NEVER draw Phase 2 bars/cards or Phase 3 takeaway cards on top of a persistent Phase 1 SVG illustration or on top of another card!
  * Use strict non-overlapping vertical slots:
    - Slot A (Top Hero / Metric): `y: 265..590`
    - Slot B (Primary Visual Stage / Comparison): `y: 615..1060`
    - Slot C (Phase 3 Takeaway / Callout): `y: 1085..1435`
  * If Phase 2 or Phase 3 renders a card in the SAME slot or corner as Phase 1, you MUST fade Phase 1 out completely to `opacity: 0` BEFORE Phase 2 enters (e.g. Phase 1 `interpolate(p, [0.42, 0.48], [1, 0], ...)` and Phase 2 `interpolate(p, [0.50, 0.56], [0, 1], ...)`). NEVER leave two cards overlapping in the same slot!
  * NEVER draw empty dashed placeholder boxes (`<rect strokeDasharray=...>` with nothing inside) waiting to be filled — every visible container must hold active content from frame 0 or stay hidden until it enters.
- MULTI-CARD GRID SPACING: When displaying multiple city/country badges (e.g., 3 to 5 capitals), NEVER place them at tight radial/circular angles where bounding boxes overlap! Use a clean 2-column grid (`x = 290` and `x = 790`, rows separated by at least `155px` vertically: `y = 650, 810, 970`) with `width <= 420px` per card.

GEOGRAPHIC & ARCHITECTURAL REALISM (NEVER DO THESE):
- Land monuments (such as the Giza Pyramids, Sphinx, Eiffel Tower, Tokyo Tower, Parliament/Capitol domes) MUST stand firmly on a solid ground, desert plateau, or stone terrace horizon line! If a river (like the Nile or Seine) is shown, draw the river in a distinct lower foreground band below the bank — NEVER draw pyramids or buildings floating in the middle of blue water!
- NEVER draw fake random green oval blobs on a globe to represent continents; use clean latitude/longitude wireframe meridians, orbital rings, and structured emblem cards.
- NEVER draw abstract geometric filler unrelated to the topic.

STRICT CODE & SAFE ZONE RULES:
1. Output ONLY raw TypeScript/JSX for ONE exported component (NO markdown fences, NO import lines, NO export default, NEVER declare `const _GEO_...`).
2. Exact signature:
   export const <TSX_ID>: React.FC<{frame?: number; fps?: number; dur?: number}> = (props) => {
3. MUST call hooks unconditionally on lines 1-2 of the component body BEFORE any conditions:
   const currentFrame = useCurrentFrame();
   const {fps: videoFps} = useVideoConfig();
   const frame = props.frame ?? currentFrame;
   const fps = props.fps ?? videoFps;
   const dur = Math.max(1, props.dur ?? 150);
4. Wrap outer JSX inside <AbsoluteFill style={{pointerEvents: 'none', overflow: 'hidden'}}> with NO `background` on it (the video's own ground shows through; a VIDEO THEME block in the user message gives the colours).
5. NO external assets: NO <img>, NO <image>, NO <canvas>, NO fetch, NO require, NO window, NO document, NO Three.js.
6. Safe layout zones on 1080x1920:
   - Top header/title banner: `x: 60..1020, y: 110..240` (keep `y >= 110` so camera pan/zoom never clips the top edge, and NEVER place any icon, badge, or illustration inside `y: 90..245` overlapping the header text!)
   - Reserved Smart Map Overlay HUD corner (when scene mentions a country/city): `y: 255..605` on the designated HUD side (`left: 48..468` on even scenes, `right: 612..1032` on odd scenes). Keep text cards and bar chart columns out of that corner, and NEVER draw a duplicate background country map!
   - Primary visual & infographic stage: `x: 60..1020, y: 615..1440` (plus the non-HUD side of `y: 260..605`).
   - Bottom Caption Safe Zone: keep `y: 1465..1920` 100% EMPTY (no cards, no text, no numbers, no labels below `y = 1455`) so synchronized subtitles (`y: 1500..1680`) never overlap with scene elements!
7. TypeScript strict correctness: never reference undefined variables, ensure all attributes/styles match React.CSSProperties & SVGProps<T>, escape quotes inside strings."""


def _build_llm_scene_prompts(
    beat: Dict[str, Any],
    scene_index: int,
    total_scenes: int,
    geo_ctx: Dict[str, Any],
    prev_narration: str = "",
    next_narration: str = "",
) -> Tuple[str, str]:
    tsx_id = _clean_id(beat.get("tsx_id") or f"DynamicScene_{scene_index}")
    narration = _clean_text(beat.get("narration") or "")
    title = _clean_text(beat.get("title") or beat.get("on_screen") or "")
    concept = _clean_text(beat.get("concept") or "")
    role = _clean_text(beat.get("id") or beat.get("role") or f"scene_{scene_index}")
    video_title = _clean_text(beat.get("video_title") or "")
    facts_summary = _clean_text(beat.get("facts_summary") or "")
    accent = beat.get("accent") or (_TSX_THEME or {}).get("accent") or "#38bdf8"
    sec = beat.get("secondary_accent") or (_TSX_THEME or {}).get("accent2") or "#f59e0b"

    # Split full scene narration into 2-3 timed semantic clauses so the LLM animates them progressively
    clauses = [c.strip() for c in re.split(r"[،,؛;:.!؟?\-]+", narration) if c.strip()]
    if len(clauses) <= 1 and len(narration.split()) >= 8:
        words = narration.split()
        mid = len(words) // 2
        clauses = [" ".join(words[:mid]), " ".join(words[mid:])]
    elif not clauses:
        clauses = [narration]

    phase_lines = []
    n_cl = len(clauses)
    for ci, cl_txt in enumerate(clauses[:3]):
        p_start = round(ci / min(n_cl, 3), 2)
        p_end = round((ci + 1) / min(n_cl, 3), 2)
        phase_lines.append(f"  - Phase {ci + 1} (progress {p_start:.2f} -> {p_end:.2f}): \"{cl_txt}\"")
    phases_block = "\n".join(phase_lines)

    scene_archetypes = [
        "ARCHETYPE 1 (Historical & Geographic Emblem Stage): Iconic architectural landmark & historical comparison cards with animated timeline/metrics (NO background country map).",
        "ARCHETYPE 2 (Split Comparative Stage): Side-by-side or upper/lower divided comparison stage contrasting two cities, eras, or concepts with custom SVG icons and strictly proportional bars (NO country map).",
        "ARCHETYPE 3 (Architectural & Monument Illustration): Detailed multi-layered custom SVG architectural facade/monument/dome illustration standing on a solid ground plateau with annotated callout cards (NO country map).",
        "ARCHETYPE 4 (Historical Chronicle Timeline): Chronological timeline conduit with dated milestone badges, historical emblems, and progressive wave animation (NO country map).",
        "ARCHETYPE 5 (Spatial / Urban Planning Diagram): Urban plan, elevation profile cross-section, or comparative scale diagram (NO country map).",
        "ARCHETYPE 6 (Institutional / System Flow Diagram): Connected hierarchy diagram showing institutions, laws, or cause-and-effect nodes with animated SVG signal pulses (NO country map).",
        "ARCHETYPE 7 (Data & Scale Infographic): Proportional population/scale comparison visual metaphor and wide animated metric counters (NO country map).",
        "ARCHETYPE 8 (Cinematic Conclusion & Interactive Prompt): Bold emblematic summary visual in `y: 620..940` and non-overlapping call-to-action prompt in `y: 980..1240` (NO country map).",
    ]
    assigned_archetype = scene_archetypes[scene_index % len(scene_archetypes)]
    hud_side = "top-left (x: 48..468, y: 256..600)" if scene_index % 2 == 0 else "top-right (x: 612..1032, y: 256..600)"

    split_hint = ""
    if re.search(r"شطر|تقسيم|انقسام|مدينتين|عاصمتين|حدود|توزيع|فصل|معاهدة", narration):
        split_hint = (
            "- CREATIVE SPLIT/MAP VISUAL: Since this narration describes dividing/splitting two places or powers, "
            "draw a stylized topographic/territory silhouette with TWO glowing location pin markers (e.g. 📍 / target rings), "
            "connected/divided by an animated glowing ZIGZAG split-fault line (`M ... L ...` with `pathLength={1}` and `strokeDashoffset` animating from `1 -> 0`) "
            "so the viewer immediately sees the geographic/political split!\n"
        )

    geo_note = (
        f"\nMANDATORY VISUAL COMPOSITION & MAP HUD COORDINATION FOR SCENE {scene_index + 1}:\n"
        f"- Assigned Visual Composition Mode: {assigned_archetype}\n"
        f"{split_hint}"
        f"- A live interactive `MapOverlayLayer` HUD may render at `{hud_side}` (`y: 256..600`). Keep `{hud_side}` clear of text cards and counters; place upper Slot A cards on the opposite side (`y: 265..590`), Slot B in `y: 615..1060`, and Slot C in `y: 1085..1435` without overlapping.\n"
        f"- Keep `y: 1465..1920` 100% empty for bottom Captions.\n"
    )

    concept_line = f'Director Visual Concept: "{concept}"\n' if concept else ""
    video_ctx_line = f'Full Video Title / Topic: "{video_title}"\n' if video_title else ""
    facts_line = f'Verified Historical/Geographic Facts for this Video: "{facts_summary}"\n' if facts_summary else ""
    vi = beat.get("visual_intelligence") if isinstance(beat.get("visual_intelligence"), dict) else {}
    vi_lines = ""
    if vi:
        vi_parts = []
        if vi.get("semantic_goal"):
            vi_parts.append(f"Semantic Goal: {vi['semantic_goal']}")
        if vi.get("historical_era"):
            vi_parts.append(f"Historical Era: {vi['historical_era']} (is_historical={bool(vi.get('is_historical'))})")
        if vi.get("entities"):
            vi_parts.append(f"Key Entities: {', '.join(str(x) for x in vi['entities'])}")
        if vi.get("relationships"):
            rel_strs = [f"{r.get('source')} -> {r.get('relation')} -> {r.get('target')}" for r in vi["relationships"][:3] if isinstance(r, dict)]
            if rel_strs:
                vi_parts.append(f"Entity Relationships: {' | '.join(rel_strs)}")
        if vi.get("avoid"):
            vi_parts.append(f"Anachronisms/Items to AVOID: {vi['avoid']}")
        if vi_parts:
            vi_lines = "VISUAL INTELLIGENCE DOSSIER:\n- " + "\n- ".join(vi_parts) + "\n"

    user_prompt = (
        f"Design and code Scene {scene_index + 1} of {total_scenes} (`{tsx_id}`) for an Arabic documentary YouTube Short.\n"
        f"{video_ctx_line}"
        f"{facts_line}"
        f"{vi_lines}"
        f"Scene Role: {role}\n"
        f"Full Scene Spoken Narration: \"{narration}\"\n"
        f"On-screen Headline: \"{title}\"\n"
        f"Timed Visual Progression Phases across Scene Duration (`progress = frame / dur`):\n"
        f"{phases_block}\n"
        f"{concept_line}"
        f"Previous Scene Narration: \"{prev_narration}\"\n"
        f"Next Scene Narration: \"{next_narration}\"\n"
        f"Suggested Accent Colors (customize atmosphere to fit the scene's story): primary={accent}, secondary={sec}\n"
        f"{_theme_block()}"
        f"{geo_note}"
        f"\nCreate a rich, concrete, multi-phase visual storytelling composition specifically explaining this scene's narration within the context of \"{video_title}\". "
        f"Include recognizable domain-specific SVG illustrations/diagrams + crisp horizontal Arabic infographic cards/labels via `<foreignObject><div dir=\"rtl\" lang=\"ar\" style={{{{fontFamily: \"'Cairo', 'Noto Kufi Arabic', sans-serif\"}}}}>...</div></foreignObject>`. "
        f"Export exact component symbol `export const {tsx_id}: React.FC<{{frame?: number; fps?: number; dur?: number}}> = (props) => {{ ... }};`."
    )
    return _LLM_TSX_SYSTEM, user_prompt


_AR_LITERAL_RE = re.compile(
    r"""(?:>([^<>{}]*[؀-ۿ][^<>{}]*)<)|(?:['"`]([^'"`\n]*[؀-ۿ][^'"`\n]*)['"`])"""
)


def _arabic_texts(code: str) -> set:
    """Distinct non-empty Arabic text nodes/string literals in a TSX component."""
    return {t.strip() for m in _AR_LITERAL_RE.findall(code) for t in m if t.strip()}


def _sanitize_llm_tsx(raw_code: str, tsx_id: str) -> Optional[str]:
    if not raw_code or not isinstance(raw_code, str):
        return None
    code = raw_code.strip()
    # Strip markdown code fences
    fence_match = re.search(r"```(?:tsx|typescript|ts|jsx|javascript)?\s*\n(.*?)```", code, flags=re.DOTALL | re.IGNORECASE)
    if fence_match:
        code = fence_match.group(1).strip()
    else:
        code = re.sub(r"^```[a-zA-Z]*\s*", "", code)
        code = re.sub(r"\s*```$", "", code).strip()

    # Strip accidental imports or registry exports
    cleaned_lines = []
    for line in code.splitlines():
        st = line.strip()
        if st.startswith("import ") or st.startswith("export default") or "DYNAMIC_SCENE_REGISTRY" in st:
            continue
        cleaned_lines.append(line)
    code = "\n".join(cleaned_lines).strip()

    # Strip hallucinated _GEO_ re-declarations before export const
    m_exp = re.search(r"\bexport\s+const\s+[A-Za-z_]", code)
    if m_exp and "_GEO_" in code[: m_exp.start()]:
        code = code[m_exp.start() :]

    # Normalize component export declaration name to exact tsx_id
    decl_pat = r"export\s+const\s+[A-Za-z_][A-Za-z0-9_]*\s*(?::\s*React\.FC<[^>]+>\s*)?=\s*"
    if re.search(decl_pat, code):
        code = re.sub(
            decl_pat,
            f"export const {tsx_id}: React.FC<{{frame?: number; fps?: number; dur?: number}}> = ",
            code,
            count=1,
        )
    elif re.search(rf"const\s+{re.escape(tsx_id)}\b", code):
        code = re.sub(rf"\bconst\s+{re.escape(tsx_id)}\b", f"export const {tsx_id}", code, count=1)
    elif "useCurrentFrame" in code and re.search(r"\breturn\s*(?:\(|<)", code):
        body = code.strip()
        if body.endswith("};") or body.endswith("}"):
            code = f"export const {tsx_id}: React.FC<{{frame?: number; fps?: number; dur?: number}}> = (props) => {{\n{body}"
        else:
            code = f"export const {tsx_id}: React.FC<{{frame?: number; fps?: number; dur?: number}}> = (props) => {{\n{body}\n}};"
    else:
        return None

    forbidden_substrings = (
        "<img",
        "<image",
        "<canvas",
        "three.js",
        "from 'three'",
        'from "three"',
        "webgl",
        "fetch(",
        "require(",
        "window.",
        "document.",
        "dangerouslysetinnerhtml",
    )
    lower = code.lower()
    if any(tok in lower for tok in forbidden_substrings):
        return None
    # Strip vertical writingMode / writing-mode attributes that disconnect and reverse Arabic letters
    code = re.sub(
        r'\s+writingMode\s*=\s*(?:"[^"]*"|\'[^\']*\'|\{[^}]*\})',
        "",
        code,
    )
    code = re.sub(
        r"writingMode\s*:\s*(?:\"[^\"]*\"|'[^']*')\s*,?",
        "",
        code,
    )
    code = re.sub(
        r"writing-mode\s*:\s*[^;\"']+;?",
        "",
        code,
    )
    # Prevent 3D flip animations from inverting/mirroring text via negative Math.cos inside scale(...)
    code = re.sub(
        r"scale\(\s*1\s*,\s*\$\{\s*Math\.cos\(([^}]+)\)\s*\}\s*\)",
        r"scale(1, ${Math.max(0.12, Math.abs(Math.cos(\1)))})",
        code,
    )
    code = re.sub(
        r"scale\(\s*\$\{\s*Math\.cos\(([^}]+)\)\s*\}\s*,\s*1\s*\)",
        r"scale(${Math.max(0.12, Math.abs(Math.cos(\1)))}, 1)",
        code,
    )
    # React SVGProps<SVGForeignObjectElement> forbids `dir` and `lang` on <foreignObject>;
    # strip them from <foreignObject ...> and inject onto inner <div> if missing.
    code = re.sub(
        r"(<foreignObject\b[^>]*?)\s+(?:dir|lang)\s*=\s*(?:\"[^\"]*\"|'[^']*'|\{[^}]*\})([^>]*>)",
        r"\1\2",
        code,
    )
    # Run twice in case both `dir` and `lang` were on the same <foreignObject>
    code = re.sub(
        r"(<foreignObject\b[^>]*?)\s+(?:dir|lang)\s*=\s*(?:\"[^\"]*\"|'[^']*'|\{[^}]*\})([^>]*>)",
        r"\1\2",
        code,
    )
    code = re.sub(
        r"(<foreignObject\b[^>]*>\s*<div\b)(?![^>]*\bdir\s*=)",
        r'\1 dir="rtl" lang="ar"',
        code,
    )
    # Clamp static numeric <foreignObject y={N} height={H}> within safe vertical bounds [105, 1455]
    def _clamp_fo_bounds(match: re.Match) -> str:
        tag = match.group(0)
        ym = re.search(r"\by=\{(\d+(?:\.\d+)?)\}", tag)
        if not ym:
            return tag
        yv = float(ym.group(1))
        hm = re.search(r"\bheight=\{(\d+(?:\.\d+)?)\}", tag)
        hv = float(hm.group(1)) if hm else 0.0
        new_y = max(105.0, yv)
        if hv > 0 and new_y + hv > 1455.0:
            new_y = max(105.0, 1455.0 - hv)
        if new_y != yv:
            tag = re.sub(r"\by=\{\d+(?:\.\d+)?\}", f"y={{{int(round(new_y))}}}", tag, count=1)
        return tag

    code = re.sub(r"<foreignObject\b[^>]*>", _clamp_fo_bounds, code)
    # Prevent static numeric <foreignObject> boxes without dynamic opacity from overlapping vertically
    _fo_boxes: List[Tuple[int, int, float, float, float, float]] = []
    for m in re.finditer(r"<foreignObject\b[^>]*>", code):
        tag = m.group(0)
        if "opacity" in tag:
            continue
        ym = re.search(r"\by=\{(\d+(?:\.\d+)?)\}", tag)
        hm = re.search(r"\bheight=\{(\d+(?:\.\d+)?)\}", tag)
        if not ym or not hm:
            continue
        xm = re.search(r"\bx=\{(\d+(?:\.\d+)?)\}", tag)
        wm = re.search(r"\bwidth=\{(\d+(?:\.\d+)?)\}", tag)
        xv = float(xm.group(1)) if xm else 0.0
        wv = float(wm.group(1)) if wm else 1080.0
        yv = float(ym.group(1))
        hv = float(hm.group(1))
        _fo_boxes.append((m.start(), m.end(), xv, yv, wv, hv))

    if len(_fo_boxes) > 1:
        # Sort by y ascending and resolve vertical collisions in reverse offset order
        placed_boxes: List[Tuple[float, float, float, float]] = []
        adjustments: Dict[int, float] = {}
        for start, _end, xv, yv, wv, hv in sorted(_fo_boxes, key=lambda b: b[3]):
            new_y = yv
            for px, py, pw, ph in placed_boxes:
                h_overlap = (xv < px + pw) and (px < xv + wv)
                v_overlap = (new_y < py + ph + 16.0) and (py < new_y + hv + 16.0)
                if h_overlap and v_overlap:
                    candidate_y = py + ph + 16.0
                    if candidate_y + hv <= 1455.0:
                        new_y = candidate_y
            placed_boxes.append((xv, new_y, wv, hv))
            if new_y != yv:
                adjustments[start] = new_y
        if adjustments:
            for start, end, _xv, _yv, _wv, _hv in sorted(_fo_boxes, key=lambda b: b[0], reverse=True):
                if start in adjustments:
                    tag = code[start:end]
                    new_tag = re.sub(
                        r"\by=\{\d+(?:\.\d+)?\}",
                        f"y={{{int(round(adjustments[start]))}}}",
                        tag,
                        count=1,
                    )
                    code = code[:start] + new_tag + code[end:]
    # Fix invalid `{ clamp: true }` in Remotion interpolate(...) options
    code = re.sub(
        r"\{\s*clamp\s*:\s*true\s*\}",
        "{extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}",
        code,
    )
    # Ensure numeric literal inputRange arrays in interpolate(...) are strictly monotonically increasing
    def _fix_interpolate_range(m: re.Match) -> str:
        prefix, arr_str = m.group(1), m.group(2)
        parts = [x.strip() for x in arr_str.split(",") if x.strip()]
        try:
            nums = [float(x) for x in parts]
        except ValueError:
            return m.group(0)
        if len(nums) < 2:
            return m.group(0)
        changed = False
        for idx in range(1, len(nums)):
            if nums[idx] <= nums[idx - 1]:
                nums[idx] = round(nums[idx - 1] + 0.001, 4)
                changed = True
        if not changed:
            return m.group(0)
        fixed = ", ".join(str(int(n)) if n.is_integer() else str(n) for n in nums)
        return f"{prefix}[{fixed}]"

    code = re.sub(
        r"(interpolate\s*\([^,]+,\s*)\[([^\[\]]+)\]",
        _fix_interpolate_range,
        code,
    )
    # Fix <foreignObject> accidentally placed after </svg> (outside SVG coordinate space)
    if code.count("<svg") == 1 and code.count("</svg>") == 1 and "<foreignObject" in code:
        svg_close_idx = code.find("</svg>")
        last_fo_idx = code.rfind("<foreignObject")
        abs_close_idx = code.rfind("</AbsoluteFill>")
        if last_fo_idx > svg_close_idx and abs_close_idx > last_fo_idx:
            code = code[:svg_close_idx] + code[svg_close_idx + len("</svg>"):abs_close_idx] + "\n      </svg>\n    " + code[abs_close_idx:]
    if "useCurrentFrame" not in code or ("AbsoluteFill" not in code and "<svg" not in code and "<div" not in code):
        return None
    # Guard React Rules of Hooks: no early `return` before useCurrentFrame/useVideoConfig
    first_hook = min(
        code.find("useCurrentFrame"),
        code.find("useVideoConfig") if "useVideoConfig" in code else len(code),
    )
    if re.search(r"\breturn\s*(?:\(|null|<)", code[:first_hook]):
        return None
    return code


def _synthesize_beat_tsx_via_llm(
    beat: Dict[str, Any],
    scene_index: int,
    total_scenes: int,
    geo_ctx: Dict[str, Any],
    prev_narration: str = "",
    next_narration: str = "",
) -> Optional[str]:
    import time
    from .llm_router import get_router

    tsx_id = _clean_id(beat.get("tsx_id") or f"DynamicScene_{scene_index}")
    sys_prompt, user_prompt = _build_llm_scene_prompts(
        beat, scene_index, total_scenes, geo_ctx, prev_narration, next_narration
    )
    resp = None
    last_err: Optional[Exception] = None
    for attempt in range(2):
        try:
            resp = get_router().dispatch(
                role="scene_writer",
                system=sys_prompt,
                user=user_prompt,
                temperature=0.82,
                json_mode=False,
                timeout=90,
            )
            last_err = None
            break
        except Exception as e:
            last_err = e
            if attempt == 0:
                logger.warning("LLM TSX dispatch attempt 1 failed for %s (retrying): %s", tsx_id, e)
                time.sleep(1.5)
    if last_err is not None or resp is None:
        logger.warning("LLM TSX synthesis skipped for scene %d (%s): %s", scene_index, tsx_id, last_err)
        return None
    sanitized = _sanitize_llm_tsx(resp.content, tsx_id)
    # Richness gate: a scene with (almost) no Arabic text (e.g. three bare bars) is an empty frame, not a scene.
    if sanitized is not None and len(_arabic_texts(sanitized)) < 3:
        logger.warning("LLM TSX rejected for scene %d (%s): fewer than 3 Arabic text nodes", scene_index, tsx_id)
        return None
    if sanitized is None:
        logger.warning(
            "LLM TSX rejected by sanitizer for scene %d (%s); raw_len=%d head=%r",
            scene_index,
            tsx_id,
            len(resp.content or ""),
            (resp.content or "")[:160],
        )
    return sanitized
