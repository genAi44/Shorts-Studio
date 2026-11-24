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

## Rules the validator enforces (before any code)
- A scene with a map must use `map`; `map` only with a map.
- No device twice in a row (except `map`), at most 2 uses per video.
- keyword 1-4 words, lead/tail ≤ 7, all on-screen text ≤ 12 words, never a copy of the narration.
- Every number, in the number slot **or inside any on-screen text**, is spoken in the sentence (digits or Arabic words:
  `studio.word_numbers` reads "عشرون ألف ومئتان وواحد وأربعون" as 20241) or is a verified entity value (truth rule).
- Icon budget: the hero icon differs from the previous scene's, any icon at most twice per video, the two sides of
  `versus` differ.
- Every `at` is a spoken word (it is the sync anchor).
- Every icon is in the **renderer's bundle** (`remotion/src/generated/iconifyBundle.json`, ~280 icons).

## Layout notes (Engineer)
Numbers up to 5 characters sit in a ring; longer ones get the full width with an underline, sized to fit. Arabic units
never go into `Counter` (it is not RTL) but become the label line under the number.

## Timing (Engineer)
A slot enters 0.1 s before its anchor word (anticipation, never later). The hero element enters by 35 % of the scene at
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
