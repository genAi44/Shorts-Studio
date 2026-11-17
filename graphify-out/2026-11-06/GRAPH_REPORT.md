# Graph Report - shorts-studio  (2026-11-06)

## Corpus Check
- 143 files · ~1,682,067 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 128 file(s) not represented in the graph (top: .bin 97, .ttf 27, .example 1)

## Summary
- 880 nodes · 2290 edges · 47 communities (39 shown, 8 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 23 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `ea21b6b9`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- beats.tsx
- media.py
- run.py
- llm.py
- visualLayer.tsx
- direct.py
- render.py
- Shorts Studio (استوديو Shorts)
- Film grain texture PNG - master source in remotion/public, grayscale noise for SVG feTurbulence-style visual grading
- package.json
- test_visuals.mjs
- compilerOptions
- geo.py
- visual_tools.py
- setup.ps1
- rem.py
- sfx.py
- Official Documentation & Sources (`docs/LINKS.md`)
- app.py
- dependencies
- json
- generativeCanvas.tsx
- schema.ts
- os
- style.py
- tools.ts
- Root.tsx
- TestVisualAssetsLayer
- icons.tsx
- pathlib
- build_playbook.py
- cfg
- Worked Examples
- Offline Lottie Animations (`lottie-usage`)
- Asset & Package Licenses (`docs/LICENSES.md`)
- devDependencies
- Typography & Layout Components (`typography-components`)
- Animated Charts & Counters (`animated-charts`)
- Transitions, Shapes, Noise & Effects (`transitions-and-effects`)
- assets/lottie/manifest.json
- public/lottie/manifest.json
- requests
- charts.tsx
- map_view
- transitions.tsx
- TestDirectorFixes

## God Nodes (most connected - your core abstractions)
1. `useTheme()` - 74 edges
2. `rgba()` - 52 edges
3. `useFont()` - 41 edges
4. `BeatView()` - 37 edges
5. `useSpring()` - 36 edges
6. `ComponentShowcase()` - 32 edges
7. `useProgress()` - 28 edges
8. `Icon()` - 26 edges
9. `cfg()` - 25 edges
10. `enterStyle()` - 24 edges

## Surprising Connections (you probably didn't know these)
- `Rules` --references--> `pickSceneTransitions()`  [INFERRED]
  skills/transitions-and-effects/SKILL.md → remotion/src/transitions.tsx
- `Motion Design Quality & QA Rules (`motion-design-quality`)` --references--> `qa_visual_review()`  [INFERRED]
  skills/motion-design-quality/SKILL.md → pipeline/visual_tools.py
- `status()` --calls--> `has_rembg()`  [EXTRACTED]
  app.py → pipeline/media.py
- `make_beats()` --calls--> `director_system()`  [EXTRACTED]
  app.py → pipeline/direct.py
- `work()` --calls--> `produce()`  [EXTRACTED]
  app.py → pipeline/run.py

## Import Cycles
- None detected.

## Communities (47 total, 8 thin omitted)

### Community 0 - "beats.tsx"
Cohesion: 0.07
Nodes (126): react, remotion, BarRow(), BarsBeat(), BeatShell(), BeatView(), BigTextBeat(), CanvasBeat() (+118 more)

### Community 1 - "media.py"
Cohesion: 0.13
Nodes (14): _clean(), cutout(), fetch_image(), find(), _get(), has_rembg(), _jpeg_bytes(), Media (+6 more)

### Community 2 - "run.py"
Cohesion: 0.17
Nodes (13): preview(), pick_engine(), plan_scenes(), produce(), estimate(), normalize(), normalize_part(), nwords() (+5 more)

### Community 3 - "llm.py"
Cohesion: 0.18
Nodes (14): deepseek_json(), repair(), extract_json(), gemini_json(), call(), repair(), gemini_vision_json(), repair() (+6 more)

### Community 4 - "visualLayer.tsx"
Cohesion: 0.15
Nodes (15): @remotion/lottie, Emoji(), EmojiEntry, EmojiProps, resolveEmojiEntry(), Flag(), GenerativeElementView(), usePrimitiveMotion() (+7 more)

### Community 5 - "direct.py"
Cohesion: 0.07
Nodes (31): _add_camera(), apply_beats(), auto_beats(), beats_for_scene(), director_prompt(), director_system(), fallback_beat(), normalize_beat() (+23 more)

### Community 6 - "render.py"
Cohesion: 0.11
Nodes (16): Background, ease(), load_font(), lum(), MapLayer, draw(), proj_arr(), sect() (+8 more)

### Community 7 - "Shorts Studio (استوديو Shorts)"
Cohesion: 0.14
Nodes (13): Motion Playbook — timing, easing, camera, beat sequencing, DeepSeek — script writing & visual director model, ElevenLabs — Arabic voiceover and word-level timestamps, FFmpeg — audio assembly and concat, Gemini — fact-checking, title/description/tags, image selection, Pexels — photo source (free API key), Python + PIL — fallback simpler render engine, rembg + onnxruntime — optional background removal (~170 MB model) (+5 more)

### Community 9 - "package.json"
Cohesion: 0.08
Nodes (23): d3-array, d3-geo, d3-scale, d3-shape, flag-icons, @iconify-json/lucide, @iconify-json/ph, @iconify-json/tabler (+15 more)

### Community 10 - "test_visuals.mjs"
Cohesion: 0.06
Nodes (25): absoluteOut, absoluteSpec, here, inputProps, log(), modes, REM_DIR, spec (+17 more)

### Community 11 - "compilerOptions"
Cohesion: 0.15
Nodes (12): compilerOptions, esModuleInterop, jsx, lib, module, moduleResolution, noEmit, noImplicitAny (+4 more)

### Community 13 - "visual_tools.py"
Cohesion: 0.07
Nodes (26): visual_library(), _clean_str(), compose_generative_canvas(), compose_procedural_scene(), validate_generative_canvas_spec(), build_spec(), apply_chat_visual_edit(), draw_chart() (+18 more)

### Community 14 - "setup.ps1"
Cohesion: 0.83
Nodes (3): Install-IfMissing(), Refresh-Path(), Test-Tool()

### Community 16 - "rem.py"
Cohesion: 0.32
Nodes (7): available(), find_browser(), make_public(), RemError, render_still(), render_video(), _run()

### Community 17 - "sfx.py"
Cohesion: 0.35
Nodes (5): ensure_sfx(), _pop(), _tick(), _whoosh(), _write()

### Community 18 - "Official Documentation & Sources (`docs/LINKS.md`)"
Cohesion: 0.18
Nodes (9): 1. Remotion Core & Official Packages (`4.0.539`), 2. Icons (Iconify — 100% Offline), 3. Emoji (100% Offline Bundled SVG/PNG), 4. Flags (100% Offline Bundled SVG), 5. Charts, Scales, Geometry & Validation, 6. Lottie Animations (Offline Curated Library), Official Documentation & Sources (`docs/LINKS.md`), Verified Package Documentation URLs (+1 more)

### Community 19 - "app.py"
Cohesion: 0.15
Nodes (18): body(), chat_edit_visual(), err(), factcheck(), index(), job(), make_script(), outputs() (+10 more)

### Community 20 - "dependencies"
Cohesion: 0.07
Nodes (27): dependencies, d3-array, d3-geo, d3-scale, d3-shape, flag-icons, @iconify-json/lucide, @iconify-json/ph (+19 more)

### Community 21 - "json"
Cohesion: 0.17
Nodes (13): build_emoji_library(), build_flags_library(), build_iconify_bundle(), build_lottie_library(), _kf_scalar(), _kf_vec2(), make_lottie_arrow(), make_lottie_checkmark() (+5 more)

### Community 22 - "generativeCanvas.tsx"
Cohesion: 0.18
Nodes (18): BadgePrimitive, BasePrimitive, CanvasMoodBackground(), ConnectorPrimitive, CounterPrimitive, EmojiPrimitive, FlagPrimitive, GaugePrimitive (+10 more)

### Community 23 - "schema.ts"
Cohesion: 0.09
Nodes (21): zod, ChartDataPointSchema, ChartStyleSchema, EmojiAnimationPresetSchema, EmojiVisualSpec, EmojiVisualSpecSchema, FlagShapeSchema, FlagVisualSpec (+13 more)

### Community 24 - "os"
Cohesion: 0.36
Nodes (5): concat(), mux(), run(), to_wav(), generate_all()

### Community 25 - "style.py"
Cohesion: 0.23
Nodes (9): make_style(), art_prompt(), _enum(), _mix(), normalize(), _num(), random_style(), _rgb() (+1 more)

### Community 26 - "tools.ts"
Cohesion: 0.15
Nodes (9): FlagProps, resolveCountryIso2(), DrawChartInput, DrawChartSchema, FlagShape, IconMatch, resolve_flag(), SearchIconsArgs (+1 more)

### Community 27 - "Root.tsx"
Cohesion: 0.21
Nodes (17): demoSpec, ComponentShowcase(), RemotionRoot(), SmokeScene5s(), getTransitionPresentation(), NoiseShapesLayer(), AnimatedHeadline(), BulletListReveal() (+9 more)

### Community 29 - "icons.tsx"
Cohesion: 0.20
Nodes (10): @iconify/utils, @remotion/paths, CachedIconData, extractPathsFromBody(), ICON_CACHE, ICON_PATHS, IconProps, resolveIconData() (+2 more)

### Community 32 - "cfg"
Cohesion: 0.15
Nodes (10): make_beats(), status(), cfg(), flag(), enabled(), estimate_timing(), probe_dur(), synth() (+2 more)

### Community 33 - "Worked Examples"
Cohesion: 0.25
Nodes (7): 1. Searching & Adding an Icon (`search_icons` + `<Icon />`), 2. Searching & Adding a Bundled Emoji (`search_emoji` + `<Emoji />`), 3. Resolving & Rendering a Flag (`resolve_flag` + `<Flag />`), 4. Scene Schema Integration (`visuals`), Icons, Emoji & Flags (`icons-emoji-flags`), Rules, Worked Examples

### Community 34 - "Offline Lottie Animations (`lottie-usage`)"
Cohesion: 0.25
Nodes (7): 1. Searching the Manifest (`search_lottie`), 2. Rendering in Remotion (`<LottieVisual />`), 3. Scene Schema Integration (`visuals`), Available Curated Categories, Offline Lottie Animations (`lottie-usage`), Rules, Worked Examples

### Community 35 - "Asset & Package Licenses (`docs/LICENSES.md`)"
Cohesion: 0.29
Nodes (6): 1. Offline Icon Collections (`packages/assets/icons/` & `@iconify-json/*`), 2. Offline Emoji Graphics (`packages/assets/emoji/`), 3. Offline Country Flags (`packages/assets/flags/`), 4. Curated Offline Lottie Library (`packages/assets/lottie/`), 5. Charts, Math, Maps & Fonts, Asset & Package Licenses (`docs/LICENSES.md`)

### Community 36 - "devDependencies"
Cohesion: 0.29
Nodes (7): devDependencies, @types/d3-array, @types/d3-geo, @types/d3-scale, @types/d3-shape, @types/react, typescript

### Community 37 - "Typography & Layout Components (`typography-components`)"
Cohesion: 0.29
Nodes (6): 1. Per-Word Animated Headline (`<AnimatedHeadline />`), 2. Lower Third, Quote Card, Bullet List & Stat Callout, Curated Font Pairings (`FONT_PAIRINGS`), Mandatory Arabic Typography Rule, Typography & Layout Components (`typography-components`), Worked Examples

### Community 38 - "Animated Charts & Counters (`animated-charts`)"
Cohesion: 0.33
Nodes (5): 1. Validating & Creating a Chart via `draw_chart`, 2. Rendering Directly in Remotion (`remotion/src/charts.tsx`), Animated Charts & Counters (`animated-charts`), Rules, Worked Examples

### Community 39 - "Transitions, Shapes, Noise & Effects (`transitions-and-effects`)"
Cohesion: 0.33
Nodes (5): 1. Picking Non-Repeating Scene Transitions, 2. Using `<TransitionSeries>` in Remotion, Rules, Transitions, Shapes, Noise & Effects (`transitions-and-effects`), Worked Examples

### Community 40 - "assets/lottie/manifest.json"
Cohesion: 0.50
Nodes (3): items, licensePolicy, version

### Community 41 - "public/lottie/manifest.json"
Cohesion: 0.50
Nodes (3): items, licensePolicy, version

### Community 43 - "charts.tsx"
Cohesion: 0.30
Nodes (13): ARABIC_DIGITS, BarChart(), BaseChartProps, ChartVisual(), DEFAULT_PALETTE, formatChartNumber(), LineChart(), NumberCounter() (+5 more)

### Community 44 - "map_view"
Cohesion: 0.60
Nodes (5): _d(), map_view(), country_d(), proj(), sect()

### Community 45 - "transitions.tsx"
Cohesion: 0.25
Nodes (7): @remotion/media, @remotion/motion-blur, @remotion/noise, @remotion/sfx, @remotion/shapes, @remotion/transitions, SFX_MAP

## Knowledge Gaps
- **23 isolated node(s):** `@iconify-json/lucide`, `@iconify-json/ph`, `@iconify-json/tabler`, `@remotion/animation-utils`, `@remotion/cli` (+18 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 321 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `@iconify/utils` connect `icons.tsx` to `package.json`, `test_visuals.mjs`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **What connects `@iconify-json/lucide`, `@iconify-json/ph`, `@iconify-json/tabler` to the rest of the system?**
  _23 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `beats.tsx` be split into smaller, more focused modules?**
  _Cohesion score 0.06646403242147923 - nodes in this community are weakly interconnected._
- **Why does `dependencies` connect `dependencies` to `package.json`?**
  _High betweenness centrality (0.024) - this node is a cross-community bridge._
- **Should `media.py` be split into smaller, more focused modules?**
  _Cohesion score 0.13105413105413105 - nodes in this community are weakly interconnected._
- **Why does `remotion` connect `beats.tsx` to `visualLayer.tsx`, `package.json`, `charts.tsx`, `transitions.tsx`, `generativeCanvas.tsx`, `tools.ts`, `Root.tsx`, `icons.tsx`?**
  _High betweenness centrality (0.020) - this node is a cross-community bridge._
- **Should `direct.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06801346801346801 - nodes in this community are weakly interconnected._