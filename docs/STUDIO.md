# Studio mode: direction before code

`STUDIO_MODE=1` replaces "one LLM writes a scene's code from a sentence" with a production chain. Off by default; the
legacy paths (built-in beats, `AUTHORED_SCENES=1`) are untouched and remain the fallback.

```
script + words ─► Creative Director ─► treatment ──────────┐
                  (1 LLM call)         message, visual world, │
                                       per scene: intent,     │
                                       function, energy, link │
style + preset ─► Visual Director  ─► design system ─────────┤      production.json (the bible)
                  (deterministic)      theme, type scale,     │
                                       motif, motion, the     │
                                       transition grammar,    │
                                       the preset's "not"     │
each scene, in order ─► Scene Designer ─► shot spec ─► validator ──► Engineer (compiler) ─► gates ─► accepted
                        (1 LLM call,      device +     (rules,       kit recipes, timing       │
                        sees prev shot)   texts +      no code)      from anchor words         │
                                          anchor words   ▲                                     │
                                                         └──── repair: render problems ◄──────┘ (max 2)
                                                        then: AUTHORED_SCENES path or built-in beats
```

## The stages
| stage | file / function | input | output |
|---|---|---|---|
| Creative Director | `studio.treatment` | title, facts, narration per scene | `message, world, motif, climax, breath, scenes[{intent, function, energy, link}]` |
| Visual Director | `studio.design_system` | style (+ preset STYLE.md), treatment | theme colours, type scale, Ribbon motif (one variant for the whole video), motion rules, transition grammar, "not" list |
| Scene Designer | `studio.design_shot` | scene words + entities, its direction, the video's world, **the previous shot**, devices used, the drawable icons | shot spec (below) |
| Validator | `studio.validate_shot` | shot spec | rule violations, sent back to the designer (max 3 designs) |
| Engineer | `studio.compile_shot` | shot spec | one TSX file against `../kit`, **no LLM** |
| Gates | `scene_author.static_check` + `sandbox_render` | TSX | tsc + allowlist, 3 rendered frames: blank, sparse, overlap, edges, safe zones, RTL, tiny text |

## Shot spec
```json
{"device": "hub", "why": "...", "keyword": "أسباب الفتح", "keyword_at": "فتح", "lead": "...", "tail": "...",
 "hero_icon": "lucide:swords", "items": [{"text": "المدافع", "icon": "lucide:bomb", "at": "بجيش"}],
 "number": {"value": 1453, "year": true, "label": "...", "at": "1453"}, "sides": [...]}
```
Devices: `statement, number, pinned, hub, steps, stack, versus, map`. Each has a fixed, gate-tested layout; the
designer chooses *what* and *when*, never pixel positions.

## Mechanisms (learned from the `remotion` project: the picture IS the explanation)
`remotion/src/mechanisms.tsx`, exported by the kit. Each one draws a physical thing that changes state on a spoken word
(`mech.change_at`), so the motion alone tells what happens (the "no-text test", written by the designer as `behavior`):
| device | draws | for |
|---|---|---|
| `level` | a tank whose level drops / rises / overflows, old level kept as a dashed ghost | levels, capacity, overload |
| `flow` | one stream split into 2-4 branches by share, the branch the sentence is about highlighted | where something goes |
| `filter` | a grid of N things of which all but k fade away | selection, survival, choice |
| `tally` | two columns of countable icons in proportion | quantities compared |
| `shrink` | an area shrinking / growing with true area (sqrt scale), old outline dashed | surfaces, territory, share |
The designer is told to prefer a mechanism and to draw the video's `core_metaphor` / recurring `objects` (chosen by the
creative director); the generic devices are the fallback. Numbers inside a mechanism follow the truth rule.
**Hero gate:** the main drawing carries `[data-hero]`; at mid-scene it must be >= 520 px wide (`HERO_MIN_W`), and it counts
as content for the sparse check. The generic heroes grew to match (icon ring 540, number ring 560, pinned card 540).
Not taken from it: free-form LLM TSX (its own stress test failed 6/10 scenes), decorative telemetry text, tiny labels.

## Rules the validator enforces (before any code)
- A scene with a map must use `map`; `map` only with a map.
- Every device at most once per video (`map` unlimited, `statement` twice): a device is a look, twice reads as a template.
- keyword 1-4 words, lead/tail ≤ 7, all on-screen text ≤ 12 words, never a copy of the narration.
- Every number, in the number slot **or inside any on-screen text**, is spoken in the sentence (digits or Arabic words:
  `studio.word_numbers` reads "عشرون ألف ومئتان وواحد وأربعون" as 20241) or is a verified entity value (truth rule).
- Icon budget: a hero icon is the hero once per video, any icon at most twice per video, the two sides of
  `versus` differ.
- No line twice on screen (a tail repeating an item), and no number written in a label when a counter already rolls it.
- Every `at` is a spoken word (it is the sync anchor).
- Every icon is in the **renderer's bundle** (`remotion/src/generated/iconifyBundle.json`, ~280 icons).

## Layout notes (Engineer)
The map device uses the wide `split-bottom` stage: the map is the hero, no hero icon competes with it; an optional
number sits between the key line and the map. A counter is invisible until its anchor word (no `0` on screen before the
number is spoken). Numbers up to 5 characters sit in a ring; longer ones get the full width with an underline, sized to fit. Arabic units
never go into `Counter` (it is not RTL) but become the label line under the number.

## Timing (Engineer)
A slot enters 0.1 s before its anchor word (anticipation, never later). The hero element enters by 25 % of the scene at
the latest: a late anchor would leave the scene empty, which the sparse gate rejects. Stack rows use the measured gap
between their anchors as the stagger.

## Transitions
From the story link, not from a random seed: `continue → fade 8f`, `contrast → flip 10f`, `deeper → clock-wipe 12f`,
`next_step → slide from-left 10f` (Arabic reads right to left). Never the same type 3 times in a row; all ≤ 12 frames.

## Findings while building it
- **Icons:** `Icon` falls back to a **star** for any name outside the 280-icon bundle. That explains the "star for
  corruption / internal conflicts" frames in FRAME_REVIEW.md. The studio validates against the bundle and gives the
  designer the list; the legacy paths still do not.
- **Worktrees:** `data/geodata.db` (127 MB) is git-ignored. Without it `build_spec` crashes and 43 tests fail.

## Not done (and why)
- **Vision critic in the repair loop:** the free vision router is not reproducible (docs/CRITIC.md). The loop uses the
  deterministic render gates; `CRITIC=1` still grades the final video.
- **Retiring the overlapping legacy generators** (`storyteller.py` LLM TSX, `generative_visuals.py`): only after
  STUDIO_MODE is measured better on the same topics, which needs the calibrated critic.
- **Preview (`/api/preview`)** does not run the studio (it would cost one LLM call per scene per preview).

## End-to-end result (script of `outputs/20261123-215737-0ed0d`, Russia; estimated word timing, silent audio)
| run | studio scenes | fallback reason |
|---|---|---|
| 1 | 6/8 | body1: designer insisted on 17,080,242 (written in words, the old parser read 17,000,000); cta: the free router returned nothing 3 times |
| 2 (word numbers) | 8/8 | one repair: body3 overflowed the edge at render time and was redesigned as steps |
| 3 (icon budget) | 7/8 | body2: designer kept writing a 6-word list item (rejected by the validator) |
| 4 (camera) | 8/8 | — |

Deterministic critic, original vs run 4: no sparse scene (min detail 0.039 vs 0.005 for the original open_loop1);
the longest still span is 1.4 s in body3 (stack finished building), every other scene ≤ 1.2 s. The original kept
moving thanks to drifting particles; the studio scenes rely on the camera push-in + bob, which is gentler.
Weak spots that are the model's, not the pipeline's: icon choice within the 280-icon bundle (e.g. `%` for a continent)
and generic `versus` labels. A stronger, fixed director model is the next lever (llm_config.json `director` role).

## New video: «لماذا يختفي البحر الميت؟» (atlas, real ElevenLabs voice, `outputs/20261124-060058-d6dc8-studio`)
Full app path (facts search → script → director → `produce` with `STUDIO_MODE=1 CRITIC=1`): 8/8 studio scenes, 0 fallback,
deterministic critic clean (no sparse, no static, no repeat). Looking at the frames found what the critic did not:
| defect | fix |
|---|---|
| map tiny in the HUD band, a hero icon competing with it | map device on `split-bottom`, no hero icon |
| a ring showing `0` until the number is spoken | counter hidden until its anchor |
| body3 tail = its third row | validator: no line twice |
| cta empty for the first third (hero word at 50 %) | hero cap 35 % → 25 % |
| `stack` twice, white rows read as a template | each device once per video |
Re-render of the same script (`-v2`): devices map, number, map, statement, versus, pinned, steps, statement (7 looks, was
5). Left after v2: the versus labels repeated their counter values (`٦٠٠ كم²` above `600`): now a validator rule, not yet
re-rendered. The free vision critic still fails 6/8 scenes with different reasons each run: it is not a signal yet.

### v3: with mechanisms (same script and voice)
Core metaphor chosen by the creative director: «حوض ماء زجاجي عليه علامات منسوب… كلما انقطع عنه الصنبور هبط سطح الماء
وترك حلقة جافة». Devices: map, number, map, statement, **shrink** (the sea from 950 to 600 km²), **level** (the tank drops on
«يهبط»), versus, statement. 8/8 accepted. Fixed after v3: shrink showed decimals mid-change (926.2), and two scenes shared the
same hero icon (now once per video). lead/body1 (93 % / 7 %) would suit `flow`, but 7 is not spoken in lead and body1 has
a map (map is mandatory there).
