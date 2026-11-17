---
name: transitions-and-effects
description: Scene transitions (@remotion/transitions: fade, slide, wipe, flip, clock-wipe), geometric shapes (@remotion/shapes), organic noise (@remotion/noise), motion blur (@remotion/motion-blur), and sound effects (@remotion/sfx).
---

# Transitions, Shapes, Noise & Effects (`transitions-and-effects`)

All `@remotion/*` packages are pinned to exact version `4.0.539`.

## Rules
1. **Vary transitions per scene boundary**: Always use `pick_transitions(scene_count, seed)` (or `pickSceneTransitions` in TS) so transitions vary across scene boundaries (`slide`, `wipe`, `clock-wipe`, `fade`, `flip`) and **never repeat the same transition back-to-back**.
2. **Organic motion with `@remotion/noise`**: Use `noise2D(seed, x, y)` for subtle floating background geometry (`<NoiseShapesLayer />`), never random `Math.random()` per frame.
3. **Subtle `@remotion/sfx`**: Pair scene transitions with low-volume (`0.25–0.30`) bundled sound effects (`whoosh`, `whip`, `pageTurn`, `uiSwitch`, `ding`) when audio cues are enabled.

---

## Worked Examples

### 1. Picking Non-Repeating Scene Transitions

```python
from pipeline.visual_tools import pick_transitions

transitions = pick_transitions(scene_count=8, seed=42)
# -> [
#   {"type": "none", "durationInFrames": 12, "sfx": "none"},
#   {"type": "clock-wipe", "direction": "from-left", "durationInFrames": 14, "sfx": "whip"},
#   {"type": "slide", "direction": "from-bottom", "durationInFrames": 14, "sfx": "pageTurn"},
#   ...
# ]
```

### 2. Using `<TransitionSeries>` in Remotion

```tsx
import {TransitionSeries, linearTiming, getTransitionPresentation} from './transitions';

<TransitionSeries>
  <TransitionSeries.Sequence durationInFrames={85}>
    <SceneA />
  </TransitionSeries.Sequence>
  <TransitionSeries.Transition
    presentation={getTransitionPresentation({type: 'wipe', direction: 'from-right', durationInFrames: 15, sfx: 'whoosh'})}
    timing={linearTiming({durationInFrames: 15})}
  />
  <TransitionSeries.Sequence durationInFrames={80}>
    <SceneB />
  </TransitionSeries.Sequence>
</TransitionSeries>
```

