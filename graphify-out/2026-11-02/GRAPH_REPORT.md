# Graph Report - shorts-studio  (2026-11-02)

## Corpus Check
- 82 files · ~808,503 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 100 file(s) not represented in the graph (top: .ttf 72, .bin 25, .example 1)

## Summary
- 481 nodes · 1319 edges · 16 communities (14 shown, 2 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 24 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- beats.tsx
- media.py
- app.py
- rem.py
- package.json
- direct.py
- render.py
- Shorts Studio (استوديو Shorts)
- Film grain texture PNG - master source in remotion/public, grayscale noise for SVG feTurbulence-style visual grading
- Short.tsx
- render.mjs
- compilerOptions
- sfx.py
- build_playbook.py
- setup.ps1

## God Nodes (most connected - your core abstractions)
1. `useTheme()` - 54 edges
2. `rgba()` - 43 edges
3. `useSpring()` - 29 edges
4. `cfg()` - 25 edges
5. `enterStyle()` - 23 edges
6. `useFont()` - 22 edges
7. `produce()` - 21 edges
8. `normalize()` - 18 edges
9. `preview()` - 17 edges
10. `BeatView()` - 17 edges

## Surprising Connections (you probably didn't know these)
- `Film grain texture PNG - grayscale noise overlay for video visual depth effect` --semantically_similar_to--> `Film grain texture PNG - master source in remotion/public, grayscale noise for SVG feTurbulence-style visual grading`  [INFERRED] [semantically similar]
  outputs/20261102-002051-23ed9/public/grain.png → remotion/public/grain.png
- `Film grain texture PNG - grayscale noise overlay (render output 2)` --semantically_similar_to--> `Film grain texture PNG - master source in remotion/public, grayscale noise for SVG feTurbulence-style visual grading`  [INFERRED] [semantically similar]
  outputs/20261102-002727-04799/public/grain.png → remotion/public/grain.png
- `Film grain texture PNG - grayscale noise overlay (render output 3)` --semantically_similar_to--> `Film grain texture PNG - master source in remotion/public, grayscale noise for SVG feTurbulence-style visual grading`  [INFERRED] [semantically similar]
  outputs/20261102-003108-2acfc/public/grain.png → remotion/public/grain.png
- `make_beats()` --calls--> `director_system()`  [EXTRACTED]
  app.py → pipeline/direct.py
- `Motion Playbook — timing, easing, camera, beat sequencing` --conceptually_related_to--> `Scene vocabulary: map, stat, bigtext, bars, timeline, versus, list, icons, canvas, photo, text`  [INFERRED]
  pipeline/playbook.md → README.md

## Import Cycles
- None detected.

## Communities (16 total, 2 thin omitted)

### Community 0 - "beats.tsx"
Cohesion: 0.11
Nodes (77): react, remotion, BarRow(), BarsBeat(), BeatShell(), BeatView(), BigTextBeat(), CanvasBeat() (+69 more)

### Community 1 - "media.py"
Cohesion: 0.07
Nodes (34): status(), cfg(), flag(), deepseek_json(), repair(), extract_json(), gemini_json(), call() (+26 more)

### Community 2 - "app.py"
Cohesion: 0.08
Nodes (29): body(), err(), factcheck(), index(), job(), make_beats(), make_script(), make_style() (+21 more)

### Community 3 - "rem.py"
Cohesion: 0.06
Nodes (37): work(), concat(), mux(), run(), to_wav(), _beat_words(), qa_beats(), available() (+29 more)

### Community 4 - "package.json"
Cohesion: 0.08
Nodes (25): react-dom, @remotion/cli, @remotion/fonts, @remotion/media, @remotion/paths, @remotion/shapes, @remotion/transitions, @types/react (+17 more)

### Community 5 - "direct.py"
Cohesion: 0.10
Nodes (21): _add_camera(), apply_beats(), auto_beats(), beats_for_scene(), director_prompt(), director_system(), fallback_beat(), normalize_beat() (+13 more)

### Community 6 - "render.py"
Cohesion: 0.10
Nodes (15): Background, ease(), load_font(), lum(), MapLayer, draw(), proj_arr(), sect() (+7 more)

### Community 7 - "Shorts Studio (استوديو Shorts)"
Cohesion: 0.10
Nodes (18): Credits: Lamas in the sunset San Pedro de Atacama Chile — CC BY-SA 2.5 Wikimedia, Credits: Pyu ancient city graveyard + Damascus Umayyad Mosque — CC BY-SA 4.0 / CC BY 2.0, FFmpeg concat list: 6 voiceover segments (w_0–w_5.wav) run 002051, FFmpeg concat list: 6 voiceover segments (w_0–w_5.wav) run 002727, FFmpeg concat list: 6 voiceover segments (w_0–w_5.wav) run 003108, Motion Playbook — timing, easing, camera, beat sequencing, DeepSeek — script writing & visual director model, ElevenLabs — Arabic voiceover and word-level timestamps (+10 more)

### Community 8 - "Film grain texture PNG - master source in remotion/public, grayscale noise for SVG feTurbulence-style visual grading"
Cohesion: 0.50
Nodes (4): Film grain texture PNG - grayscale noise overlay for video visual depth effect, Film grain texture PNG - grayscale noise overlay (render output 2), Film grain texture PNG - grayscale noise overlay (render output 3), Film grain texture PNG - master source in remotion/public, grayscale noise for SVG feTurbulence-style visual grading

### Community 9 - "Short.tsx"
Cohesion: 0.15
Nodes (22): demoSpec, Background(), Deco(), Finish(), mixc(), SceneWipe(), Waves(), RemotionRoot() (+14 more)

### Community 10 - "render.mjs"
Cohesion: 0.19
Nodes (7): here, inputProps, log(), spec, here, inputProps, spec

### Community 11 - "compilerOptions"
Cohesion: 0.15
Nodes (12): compilerOptions, esModuleInterop, jsx, lib, module, moduleResolution, noEmit, noImplicitAny (+4 more)

### Community 12 - "sfx.py"
Cohesion: 0.35
Nodes (5): ensure_sfx(), _pop(), _tick(), _whoosh(), _write()

### Community 14 - "setup.ps1"
Cohesion: 0.83
Nodes (3): Install-IfMissing(), Refresh-Path(), Test-Tool()

## Knowledge Gaps
- **20 isolated node(s):** `@remotion/cli`, `@remotion/paths`, `@remotion/shapes`, `@remotion/transitions`, `react-dom` (+15 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 131 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `produce()` connect `rem.py` to `media.py`, `app.py`?**
  _High betweenness centrality (0.019) - this node is a cross-community bridge._
- **What connects `@remotion/cli`, `@remotion/paths`, `@remotion/shapes` to the rest of the system?**
  _20 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `beats.tsx` be split into smaller, more focused modules?**
  _Cohesion score 0.10986804360298336 - nodes in this community are weakly interconnected._
- **Why does `cfg()` connect `media.py` to `app.py`, `rem.py`?**
  _High betweenness centrality (0.016) - this node is a cross-community bridge._
- **Should `media.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07288135593220339 - nodes in this community are weakly interconnected._
- **Should `app.py` be split into smaller, more focused modules?**
  _Cohesion score 0.0803633822501747 - nodes in this community are weakly interconnected._
- **Should `rem.py` be split into smaller, more focused modules?**
  _Cohesion score 0.0590990990990991 - nodes in this community are weakly interconnected._