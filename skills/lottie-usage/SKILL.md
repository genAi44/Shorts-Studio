---
name: lottie-usage
description: Curated offline Lottie animations (<LottieVisual />) synced to Remotion frames and searched via search_lottie. Use when adding animated checkmarks, arrows, loaders, confetti, sparkles, or radial sweeps.
---

# Offline Lottie Animations (`lottie-usage`)

All Lottie files live locally in `packages/assets/lottie/` with full license metadata in `packages/assets/lottie/manifest.json` (`CC0-1.0` / `MIT`). Never fetch remote Lottie URLs at render time.

## Rules
1. **Always call `search_lottie({ query })`** over `manifest.json` to pick a verified asset ID.
2. **Frame-accurate playback**: `<LottieVisual />` wraps `@remotion/lottie` (`<Lottie />`), which automatically synchronizes playback to `useCurrentFrame()`.
3. **Bounded complexity**: Use at most **1 Lottie element per scene** so 4K renders stay fast and uncluttered.

---

## Available Curated Categories
- `checkmark` (`category: "check"`) — Animated verified checkmark draw-on
- `arrow-right`, `arrow-up` (`category: "arrows"`) — Directional pointer & growth arrows
- `loader-ring` (`category: "loaders"`) — Smooth cycle/progress ring
- `confetti-burst` (`category: "confetti"`) — Celebration burst particles
- `sparkles-gold` (`category: "sparkles"`) — Twinkling golden 4-point stars
- `transition-sweep` (`category: "transitions"`) — Expanding concentric ring reveal
- `pulse-target` (`category: "highlights"`) — Radar/map pin target pulse

---

## Worked Examples

### 1. Searching the Manifest (`search_lottie`)

```python
from pipeline.visual_tools import search_lottie

matches = search_lottie("بريق ذهبي", limit=2)
# -> [{"id": "sparkles-gold", "category": "sparkles", "license": "CC0-1.0", ...}]
```

### 2. Rendering in Remotion (`<LottieVisual />`)

```tsx
import {LottieVisual} from './lottie';

<LottieVisual name="checkmark" size={180} loop={false} playbackRate={1.0} />
```

### 3. Scene Schema Integration (`visuals`)

```json
{
  "visuals": [
    {
      "kind": "lottie",
      "placement": "badge-row",
      "spec": {
        "name": "sparkles-gold",
        "size": 120,
        "loop": true,
        "playbackRate": 1.0
      }
    }
  ]
}
```

