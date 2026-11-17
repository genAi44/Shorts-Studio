---
name: icons-emoji-flags
description: Offline Iconify icons (<Icon />), bundled SVG emoji (<Emoji />), and country flags (<Flag />) with search tools and Remotion frame-driven animations. Use when selecting or rendering icons, emojis, or country flags in scenes or beats.
---

# Icons, Emoji & Flags (`icons-emoji-flags`)

Everything renders **100% offline** from `packages/assets/` (mirrored to `remotion/public/` and `remotion/src/generated/`). Never invent icon names or render raw OS text emoji.

## Rules
1. **Always call search tools** (`search_icons`, `search_emoji`, `resolve_flag`) before adding an asset. Never guess or hallucinate an icon identifier.
2. **Consistent icon style per video**: Lock to one Iconify prefix per video (`lucide`, `ph`, or `tabler`).
3. **Never render emoji as text**: Always use `<Emoji char="🏛️" />` or `{ kind: "emoji", spec: { char: "🏛️" } }` which loads the bundled Noto Color Emoji Apache-2.0 SVG.
4. **No emoji spam**: At most **1 emoji per scene**.
5. **Reuse country resolver for flags**: `<Flag code="EG" shape="rect|round" />` accepts ISO2 (`"EG"`), ISO3 (`"EGY"`, `"BOL"`), Arabic (`"مصر"`, `"بوليفيا"`), or English (`"Egypt"`, `"Bolivia"`).

---

## Worked Examples

### 1. Searching & Adding an Icon (`search_icons` + `<Icon />`)

```python
from pipeline.visual_tools import search_icons

matches = search_icons("هرم", set_name="lucide", limit=3)
# -> [{"id": "lucide:pyramid", "set": "lucide", "name": "pyramid", "license": "ISC", ...}]
```

```tsx
import {Icon} from './icons';

// Remotion frame-driven animation presets: 'draw' | 'pop' | 'float' | 'pulse' | 'rotate'
<Icon name="lucide:landmark" size={96} color="#f5c542" strokeWidth={2.2} animation="draw" />
```

### 2. Searching & Adding a Bundled Emoji (`search_emoji` + `<Emoji />`)

```python
from pipeline.visual_tools import search_emoji

em = search_emoji("معلم تاريخي", limit=1)[0]
# -> {"char": "🏛️", "code": "1f3db", "file": "emoji/1f3db.svg", "license": "Apache-2.0"}
```

```tsx
import {Emoji} from './emoji';

// Presets: 'bounce' | 'pop' | 'shake' | 'spin'
<Emoji char="🏛️" size={96} animation="bounce" />
```

### 3. Resolving & Rendering a Flag (`resolve_flag` + `<Flag />`)

```python
from pipeline.visual_tools import resolve_flag

fl = resolve_flag("بوليفيا", shape="round")
# -> {"code": "BO", "iso2": "bo", "shape": "round", "file": "flags/1x1/bo.svg"}
```

```tsx
import {Flag} from './flag';

<Flag code="EG" shape="rect" size={96} animation="pop" />
<Flag code="بوليفيا" shape="round" size={96} animation="float" />
```

### 4. Scene Schema Integration (`visuals`)

```json
{
  "visuals": [
    {
      "kind": "icon",
      "placement": "badge-row",
      "spec": { "name": "lucide:landmark", "size": 92, "color": "#f5c542", "strokeWidth": 2.2, "animation": "draw" }
    },
    {
      "kind": "flag",
      "placement": "badge-row",
      "spec": { "code": "BO", "shape": "rect", "size": 88, "animation": "pop" }
    }
  ]
}
```

