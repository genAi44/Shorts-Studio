# Graph Report - shorts-studio  (2026-11-03)

## Corpus Check
- 100 files · ~968,527 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 135 file(s) not represented in the graph (top: .ttf 81, .bin 51, .example 1)

## Summary
- 504 nodes · 1406 edges · 18 communities (15 shown, 3 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 24 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- beats.tsx
- media.py
- app.py
- rem.py
- tts.py
- direct.py
- render.py
- Shorts Studio (استوديو Shorts)
- Film grain texture PNG - master source in remotion/public, grayscale noise for SVG feTurbulence-style visual grading
- package.json
- render.mjs
- compilerOptions
- Geo
- build_playbook.py
- setup.ps1
- llm.py
- sfx.py

## God Nodes (most connected - your core abstractions)
1. `useTheme()` - 57 edges
2. `rgba()` - 43 edges
3. `useSpring()` - 32 edges
4. `cfg()` - 25 edges
5. `useFont()` - 25 edges
6. `enterStyle()` - 24 edges
7. `produce()` - 21 edges
8. `BeatView()` - 21 edges
9. `normalize()` - 18 edges
10. `preview()` - 17 edges

## Surprising Connections (you probably didn't know these)
- `Film grain texture PNG - grayscale noise overlay for video visual depth effect` --semantically_similar_to--> `Film grain texture PNG - master source in remotion/public, grayscale noise for SVG feTurbulence-style visual grading`  [INFERRED] [semantically similar]
  outputs/20261102-002051-23ed9/public/grain.png → remotion/public/grain.png
- `Film grain texture PNG - grayscale noise overlay (render output 2)` --semantically_similar_to--> `Film grain texture PNG - master source in remotion/public, grayscale noise for SVG feTurbulence-style visual grading`  [INFERRED] [semantically similar]
  outputs/20261102-002727-04799/public/grain.png → remotion/public/grain.png
- `Film grain texture PNG - grayscale noise overlay (render output 3)` --semantically_similar_to--> `Film grain texture PNG - master source in remotion/public, grayscale noise for SVG feTurbulence-style visual grading`  [INFERRED] [semantically similar]
  outputs/20261102-003108-2acfc/public/grain.png → remotion/public/grain.png
- `status()` --calls--> `has_rembg()`  [EXTRACTED]
  app.py → pipeline/media.py
- `make_beats()` --calls--> `director_system()`  [EXTRACTED]
  app.py → pipeline/direct.py

## Import Cycles
- None detected.

## Communities (18 total, 3 thin omitted)

### Community 0 - "beats.tsx"
Cohesion: 0.08
Nodes (102): react, remotion, BarRow(), BarsBeat(), BeatShell(), BeatView(), BigTextBeat(), CanvasBeat() (+94 more)

### Community 1 - "media.py"
Cohesion: 0.14
Nodes (14): _clean(), cutout(), fetch_image(), find(), _get(), has_rembg(), _jpeg_bytes(), Media (+6 more)

### Community 2 - "app.py"
Cohesion: 0.08
Nodes (39): body(), err(), factcheck(), index(), job(), make_beats(), make_script(), make_style() (+31 more)

### Community 3 - "rem.py"
Cohesion: 0.06
Nodes (29): concat(), mux(), run(), to_wav(), _beat_words(), qa_beats(), available(), _d() (+21 more)

### Community 4 - "tts.py"
Cohesion: 0.18
Nodes (6): estimate_timing(), probe_dur(), synth(), TTSError, fetch_all(), make_fallback_svg()

### Community 5 - "direct.py"
Cohesion: 0.10
Nodes (24): _add_camera(), apply_beats(), auto_beats(), beats_for_scene(), director_prompt(), director_system(), fallback_beat(), normalize_beat() (+16 more)

### Community 6 - "render.py"
Cohesion: 0.11
Nodes (15): Background, ease(), load_font(), lum(), MapLayer, draw(), proj_arr(), sect() (+7 more)

### Community 7 - "Shorts Studio (استوديو Shorts)"
Cohesion: 0.10
Nodes (18): Credits: Lamas in the sunset San Pedro de Atacama Chile — CC BY-SA 2.5 Wikimedia, Credits: Pyu ancient city graveyard + Damascus Umayyad Mosque — CC BY-SA 4.0 / CC BY 2.0, FFmpeg concat list: 6 voiceover segments (w_0–w_5.wav) run 002051, FFmpeg concat list: 6 voiceover segments (w_0–w_5.wav) run 002727, FFmpeg concat list: 6 voiceover segments (w_0–w_5.wav) run 003108, Motion Playbook — timing, easing, camera, beat sequencing, DeepSeek — script writing & visual director model, ElevenLabs — Arabic voiceover and word-level timestamps (+10 more)

### Community 8 - "Film grain texture PNG - master source in remotion/public, grayscale noise for SVG feTurbulence-style visual grading"
Cohesion: 0.50
Nodes (4): Film grain texture PNG - grayscale noise overlay for video visual depth effect, Film grain texture PNG - grayscale noise overlay (render output 2), Film grain texture PNG - grayscale noise overlay (render output 3), Film grain texture PNG - master source in remotion/public, grayscale noise for SVG feTurbulence-style visual grading

### Community 9 - "package.json"
Cohesion: 0.08
Nodes (25): react-dom, @remotion/cli, @remotion/fonts, @remotion/media, @remotion/paths, @remotion/shapes, @remotion/transitions, @types/react (+17 more)

### Community 10 - "render.mjs"
Cohesion: 0.14
Nodes (11): absoluteOut, absoluteSpec, here, inputProps, log(), spec, absoluteOut, absoluteSpec (+3 more)

### Community 11 - "compilerOptions"
Cohesion: 0.15
Nodes (12): compilerOptions, esModuleInterop, jsx, lib, module, moduleResolution, noEmit, noImplicitAny (+4 more)

### Community 14 - "setup.ps1"
Cohesion: 0.83
Nodes (3): Install-IfMissing(), Refresh-Path(), Test-Tool()

### Community 16 - "llm.py"
Cohesion: 0.27
Nodes (12): deepseek_json(), repair(), extract_json(), gemini_json(), call(), repair(), gemini_vision_json(), repair() (+4 more)

### Community 17 - "sfx.py"
Cohesion: 0.35
Nodes (5): ensure_sfx(), _pop(), _tick(), _whoosh(), _write()

## Knowledge Gaps
- **20 isolated node(s):** `@remotion/cli`, `@remotion/paths`, `@remotion/shapes`, `@remotion/transitions`, `react-dom` (+15 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 143 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `produce()` connect `app.py` to `media.py`, `rem.py`, `tts.py`, `render.py`?**
  _High betweenness centrality (0.019) - this node is a cross-community bridge._
- **What connects `@remotion/cli`, `@remotion/paths`, `@remotion/shapes` to the rest of the system?**
  _20 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `beats.tsx` be split into smaller, more focused modules?**
  _Cohesion score 0.0769121207805156 - nodes in this community are weakly interconnected._
- **Why does `cfg()` connect `app.py` to `llm.py`, `media.py`, `rem.py`, `tts.py`?**
  _High betweenness centrality (0.015) - this node is a cross-community bridge._
- **Should `media.py` be split into smaller, more focused modules?**
  _Cohesion score 0.14333333333333334 - nodes in this community are weakly interconnected._
- **Should `app.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07987711213517665 - nodes in this community are weakly interconnected._
- **Should `rem.py` be split into smaller, more focused modules?**
  _Cohesion score 0.0578386605783866 - nodes in this community are weakly interconnected._