---
name: animated-charts
description: Pure SVG animated charts and counters (<BarChart />, <LineChart />, <PieDonutChart />, <NumberCounter />, <ProgressRing />, <Timeline />) powered by D3 scales/shapes and Remotion frames with RTL and Arabic numerals support.
---

# Animated Charts & Counters (`animated-charts`)

Charts are rendered in **pure SVG** using `d3-scale`, `d3-shape`, and `d3-array` driven exclusively by Remotion frames (`useCurrentFrame`, `spring`, `@remotion/paths`). Never use DOM-mutating `d3-selection` inside React/Remotion.

## Rules
1. **Validate every chart via `draw_chart`**: Always validate chart specs with `draw_chart({ type, data, style, animation, durationInFrames })` (`DrawChartSchema` in Zod).
2. **RTL & Arabic-Indic Numerals**: Set `style.rtl = true` and `style.arabicNumerals = true` (`٠١٢٣٤٥٦٧٨٩`) for Arabic Shorts when appropriate.
3. **Readable data density**: Keep `data` between 2 and 6 items on a 9:16 vertical screen so labels never overlap.

---

## Worked Examples

### 1. Validating & Creating a Chart via `draw_chart`

```python
from pipeline.visual_tools import draw_chart

chart_visual = draw_chart({
    "type": "bar",
    "data": [
        {"label": "لاباز", "value": 3650},
        {"label": "سوكري", "value": 2790},
        {"label": "كيتو", "value": 2850}
    ],
    "style": {
        "title": "ارتفاع العواصم فوق سطح البحر (متر)",
        "unit": "م",
        "rtl": True,
        "arabicNumerals": True,
        "width": 900,
        "height": 600
    },
    "animation": "spring",
    "durationInFrames": 90
})
```

### 2. Rendering Directly in Remotion (`remotion/src/charts.tsx`)

```tsx
import {BarChart, LineChart, PieDonutChart, NumberCounter, ProgressRing, Timeline} from './charts';

<BarChart
  data={[
    {label: 'مصر', value: 114},
    {label: 'السعودية', value: 36},
    {label: 'المغرب', value: 38},
  ]}
  style={{title: 'عدد السكان (مليون نسمة)', rtl: true, arabicNumerals: true, unit: 'م'}}
/>

<NumberCounter value={3650} label="متراً فوق سطح البحر" unit="م" arabicNumerals={true} rtl={true} />
<ProgressRing value={86} label="نسبة التحضر" arabicNumerals={true} />
```

