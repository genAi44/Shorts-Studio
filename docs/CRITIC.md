# Critic (Phase 0): grading the finished video

`pipeline/critic.py` grades `outputs/<job>/short.mp4`: not the spec, not the code. It only measures; nothing is repaired.

```
python -m pipeline.critic outputs/<job>                     # -> <job>/critic/report.json + report.html
python -m pipeline.critic --baseline outputs [--no-vision]  # -> outputs/critic_baseline.json
python -m pipeline.critic --calibrate frames docs/FRAME_REVIEW.md --provider freellmapi   # -> qa/critic_calibration_*.json
```
`CRITIC=1` in `.env` runs it after every render (report only, a failure never breaks the render).

## Layer 1: deterministic (ffmpeg + numpy, ~15 s per video, reproducible)
| defect | measure | threshold |
|---|---|---|
| sparse | share of edge pixels in the beat zone (y 280..1380) at mid-scene | < 0.012 → major |
| static | longest run of 10 fps proxy frames with mean abs diff < 0.35 | > 1.2 s minor, > 2.4 s major |
| repeat | dHash (64 bit) of mid-frames, both frames non-sparse | ≤ 6 bits → info (hint only) |
| palette drift | colour histogram distance from the video's median | > 0.55 → minor |
| flashes | full-frame luminance jumps > 40 | > 3 per second |
| monotone rhythm | > 3 consecutive scenes within 15 % of each other | reported |

Checked by hand on `20261123-215737-0ed0d`: it found the hook/body1 repeat (the same Russia map card) and the empty
open_loop1. The std-based "blank" test missed that frame (glows keep the std high), so edge density replaced it.

## Layer 2: vision rubric
Per scene: 6 frames (10/25/40/55/75/90 %) plus the previous scene's last frame and the next scene's first frame, with the
narration. Defects are listed first (with the image index), then 6 scores out of 5. Every defect names its owning stage
(concept / layout / style / motion / code), which is the routing key for the Phase 4 repair loop. One whole-video pass
judges identity, repetition and the visual arc. A scene the model could not see is `NOT REVIEWED`, never passed.

## Calibration (71 hand-labelled frames of FRAME_REVIEW.md; photo-rule labels excluded → 69)
Target: major recall ≥ 0.80, false alarms on clean frames ≤ 0.20, stable from one run to the next.

| run | major recall | any-severity recall | false alarm on clean | note |
|---|---|---|---|---|
| FreeLLMAPI v1 | 0.54 | 0.83 | 0.56 | bug: only the first 4 images were sent (`images[:4]`), at 448 px |
| FreeLLMAPI v2 | 0.42 | 0.71 | 0.25 | all 6 images at 640 px |
| Gemini | — | — | — | key out of quota (429) |

Run-to-run agreement of the two FreeLLMAPI runs on the same frames: 0.40 exact, 0.60 major / not major. The `auto`
router picks a different free model per call, so its verdicts are not reproducible. **Verdict: the deterministic layer
can be trusted now; the vision layer needs a fixed, stronger model before its pass/fail is used as a gate.** Until then,
treat vision defects as hints for a human, not as a score.

## Baseline: 60 past videos, 480 scenes, deterministic layer only (`outputs/critic_baseline.json`)
- **sparse: 11 scenes (2.3 %)**, mostly hook / lead / open_loop / cta. A hand check of all 11: about 8 are really thin
  (a text-only frame, an empty frame, thin outline layouts) and about 3 are faint thin-line UI. Precision is about 70 %.
- **static: 0 scenes.** Median longest still span 0 s, 95th percentile 0.7 s: drifting particles and glows keep every
  frame moving, which is what the protocol asks for. "Nothing develops in the scene" is therefore not a pixel question;
  it belongs to the vision rubric's motion score.
- **repeat: 269 candidate pairs.** A hand check of 4 random pairs found 2 real template repeats (the same shield badge;
  the same map card + gauge) and 2 false ones (a shared dark gradient). An edge-map hash did not separate them better
  (real pairs 61-104 bits, false 59-132), so pixel repeats are hints; layout repetition is judged by the vision pass
  over the whole video.
- palette drift: 2, flashes: 0. Videos that pass the deterministic layer: 83 %. This layer catches the floor (empty or
  broken frames), not quality: the quality signal has to come from a reliable vision model.
