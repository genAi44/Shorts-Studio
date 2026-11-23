# Scene kit (what the art director may use)

An **authored scene** is ONE self-contained TSX file, default-exporting a React component `(props: SceneProps) => JSX`.
It may import only `react`, `remotion` and `../kit`. Everything is driven by the frame number; nothing else is allowed.

```tsx
import React from 'react';
import {AbsoluteFill} from 'remotion';
import {Abs, ArText, Card, Counter, LAYOUT, useKit, enter, useSpr, SceneProps} from '../kit';

export default function Scene({dur, data}: SceneProps) {
  const k = useKit();
  const p = useSpr(0.1, 'snappy');
  return (
    <AbsoluteFill>
      <Abs x={90} y={LAYOUT.beat.center_y - 220} w={900} style={enter(p, 'rise', 60)}>
        <Card style={{padding: 40}}>
          <ArText size={64}>{data.sentence}</ArText>
          <Counter to={1453} size={150} delay={0.3} />
        </Card>
      </Abs>
    </AbsoluteFill>
  );
}
```

## Mistakes that got scenes rejected (read this first)
1. `useState` / `useEffect` / any state or effect hook: NEVER. Everything is computed from the frame (`useKit().frame`, `useSpr`, `useProgress`).
   If a child needs its own animation, make a small component and call `useSpr` inside it.
2. Inventing API: there is no `LAYOUT.beat.center_x` (use `LAYOUT.cx`), no `useKit().theme`, `Bar` takes `w`/`h` not `width`/`height`,
   `ArText` has no `words` prop and its children must be ONE string, `enter()` returns a style object (do not read `.x` from numbers).
3. Import every name you use, including the type `SceneProps`: `import {SceneProps, LAYOUT, ...} from '../kit';`.
4. Output only code: the first line must be an `import`. No reasoning text before or after.
5. Text must be >= 24 px (hero text 56-150 px) and stay inside `LAYOUT.beat`; do not place text where it overlaps other text.

## Design direction (read before you compose)
Good short-form scenes share a few habits. Apply them; do not imitate any specific video.
1. **One hero idea per screen.** One hero object/graphic + one short line. Leave generous empty space; never fill the beat zone.
2. **Text is part of the layout**, not a caption: put it next to the hero. Inside one line, make the KEY word big, heavy and in the
   accent colour and the rest small and light (`KeyLine`): a 2.5-3x size contrast reads as design, equal sizes read as a form.
3. **Two colours.** Ground + text + ONE accent (`c('accent')`) with alphas of it. Do not introduce other hues.
4. **Build up, do not swap.** Items appear one by one on the same canvas and stay (`Stack`, `Hub`, `Steps`): the viewer sees the idea assemble.
5. **No boxes around everything.** Prefer a bare shape, a circle, a ribbon or a pinned card over a card-in-a-card.
6. **A continuous element behind the content** (`Ribbon`) gives scenes the same visual family; keep it at low alpha.
7. **One metaphor per scene**: hub (sources), rising steps (progress/stages), list that grows (consequences), pinned card (a fact).
8. Stagger by 0.1-0.35 s; the key word enters first or on the spoken word (`data.words` has the times).

## Layout recipes (ready-made, in `../kit`)
| recipe | use it for | props |
|---|---|---|
| `KeyLine` | the headline of nearly every scene | `keyword` (big accent word/phrase), `lead?` (small line above), `tail?` (small line below), `size=120`, `delay`, `maxWidth` |
| `Hub` | something with 2-7 sources/parts/causes | `items=[{icon?: 'lucide:x', label?}]`, `center` (node: an `Icon` ~130 px), `cy`, `radius=300`, `delay` |
| `Steps` | stages, progress, ranking (first item is on the right) | `items: string[]` (2-5 short labels), `w=900`, `bottom`, `maxH=540` |
| `Stack` | consequences, features, a numbered list | `items=[{text, icon?}]` (2-6 rows, 150 px apart), `top`, `step=0.5` |
| `Pinned` | one fact/number on a card hanging from a string | `x,y,w,h,rotate`, children = `Counter` / `ArText` / `Icon` (no photos) |
| `Ribbon` | background decoration behind everything | `variant` 0 / 1 / 2 |

Layout rule: `KeyLine` goes in `y = LAYOUT.beat.top + 10` (width 900, centred with `display:flex; justifyContent:center`), the
recipe body below it (`Hub` `cy = LAYOUT.beat.center_y + 120`, `Stack` `top = LAYOUT.beat.top + 220`, `Steps` default). Recipes may be
combined or used as inspiration for your own composition (inline SVG shapes + `useSpr` staggers).

```tsx
import React from 'react';
import {AbsoluteFill} from 'remotion';
import {Abs, Hub, Icon, KeyLine, LAYOUT, Ribbon, SceneProps, useKit} from '../kit';

export default function Scene({data}: SceneProps) {
  const k = useKit();
  return (
    <AbsoluteFill>
      <Ribbon variant={0} />
      <Abs x={90} y={LAYOUT.beat.top + 10} w={900} style={{display: 'flex', justifyContent: 'center'}}>
        <KeyLine lead="مصدر الدخل" keyword="خمسة روافد" size={110} />
      </Abs>
      <Hub cy={LAYOUT.beat.center_y + 120} radius={300}
           center={<Icon name="lucide:wallet" size={130} color={k.c('accent')} />}
           items={[{icon: 'lucide:fuel', label: 'النفط'}, {icon: 'lucide:landmark', label: 'الاستثمار'}, {icon: 'lucide:ship', label: 'الموانئ'}]} />
    </AbsoluteFill>
  );
}
```
Working examples of each recipe: `tests/fixtures/recipes/*.tsx`.

## Props
`dur` = scene length in frames. `data` = `{sentence, sentences[], role, entities[], words[{t,s,e}], map_overlay|null, theme}`:
`words` are the spoken words with start/end seconds (sync accents to them), `entities` are the verified entities of the
sentence (`type`, `scale`, `name_ar`, numbers, years, `lat/lon`), `map_overlay` is the ready map spec for places.

## Kit (`../kit`)
| name | what |
|---|---|
| `useKit()` | `{frame, fps, t, sec(s), dark, c(name, alpha), shadow, card, cardBorder, font, fontWeight}`; `c` names: `text, accent, accent2, ground, ground2, hl0, hl1, hl2` |
| `LAYOUT` | `W=1080, H=1920, safeTop, safeBottom, headline{top,bottom,center_y,left,right}, beat{top:280,bottom:1380,center_y:860,left:80,right:80,...}, caption{top:1420,...}` |
| `Abs` | absolutely positioned box `{x,y,w?,h?,style}` (px on the canvas) |
| `Card` | theme card (dark glass on dark grounds, white card on light grounds) |
| `ArText` | **all Arabic text**: `dir=rtl`, word-by-word entrance, `size, weight, color, align, delay, reveal('words'|'fade'|'none'), maxWidth` |
| `Counter` | rolling number `{to, from, delay, dur, size, suffix, decimals}` |
| `Ring`, `Bar` | progress ring / bar `{value 0..1, ...}` |
| `Icon` | Iconify icon `{name:'lucide:landmark', size, color}` (bundled sets lucide / ph / tabler) |
| `MapLayer` | the vector map engine, only when `data.map_overlay` exists. It draws its own card with its own labels at a FIXED place: `mode="split-bottom"` card at y 710..1415 (put your elements in y 280..690, keep them out of the card), `mode="full-stage"` card at y 200..1280 (put NOTHING over it), `mode="hud"` small card at y 995..1420. Prefer `split-bottom` with a hero title/number above it |
| `useSpr(delaySec, preset)` | spring 0..1 (`smooth`, `snappy`, `bouncy`) |
| `enter(p, kind, dist)` | entrance style = opacity + translate + scale (3 properties): `rise, drop, pop, left, right, fade` |
| `useProgress(startSec, durSec)` | 0..1 with a bezier ease |
| `useIdle(amp, period, phase)` | gentle floating offset |
| `ease` | bezier curves: `out, inOut, in, back` (for `interpolate(..., {easing})`) |
| `interpolate`, `Pop` | remotion interpolate / staggered entrance wrapper |
| `KeyLine`, `Hub`, `Steps`, `Stack`, `Pinned`, `Ribbon` | layout recipes (see "Layout recipes" above) |

## Exact signatures (copy these, do not invent others)
```ts
import {SceneProps, LAYOUT, useKit, Abs, Card, ArText, Counter, Ring, Bar, Icon, MapLayer, useSpr, enter, useProgress, useIdle, ease, interpolate, Pop,
        KeyLine, Hub, Steps, Stack, Pinned, Ribbon} from '../kit';
type SceneProps = {dur: number; data: any};
LAYOUT: {cx: 540, cy: 860, W: 1080, H: 1920, safeTop: 72, safeBottom: 1780,
         headline: {top, bottom, center_y, left, right}, beat: {top: 280, bottom: 1380, center_y: 860, left: 80, right: 80},
         caption: {top: 1420, bottom: 1760, ...}}            // there is NO center_x: use LAYOUT.cx
useKit(): {frame, fps, t, sec(s: number): number, dark: boolean, c(name: 'text'|'accent'|'accent2'|'ground'|'ground2'|'hl0'|'hl1'|'hl2', alpha?: number): string,
           shadow: string, card: string, cardBorder: string, font: string, fontWeight: number}      // no .theme, no .layout
useSpr(delaySec: number, preset: 'smooth'|'snappy'|'bouncy'): number            // 0..1, a NUMBER (not an object)
enter(p: number, kind: 'rise'|'drop'|'pop'|'left'|'right'|'fade', dist?: number): React.CSSProperties   // spread it into style
useProgress(startSec: number, durSec: number): number                           // 0..1
<Abs x y w? h? style?>   <Card style?>   <Counter to from? delay? dur? size? color? suffix? decimals? style?/>
<ArText size? weight? color? align? delay? reveal? maxWidth? lineHeight? style?>{string}</ArText>      // children MUST be a string
<Ring value size? stroke? delay? color?>{children}</Ring>   <Bar value w? h? delay? color?/>            // Bar has w/h, not width/height
<Icon name="lucide:landmark" size? color? strokeWidth?/>   <MapLayer overlay={data.map_overlay} mode?/>
```
Use a stagger like `useSpr(0.1 + i * 0.12, 'snappy')` inside a child component (hooks cannot be called in a loop body of the
parent: make one small component per item). Format numbers yourself (`n.toLocaleString('en-US')`) for static text.

## Rules (checked automatically)
- Only spring / bezier easing. At most 3 animated properties per entrance (`enter()` does opacity + translate + scale). Stagger siblings by index.
- No hooks with state or effects (`useState`, `useEffect`...), no timers, no `Date`, no `Math.random`: the frame is the only clock.
- No network, `eval`, `fs`, dynamic import, DOM globals, external URLs, `<img>`, `<style>`, CSS `transition`/`animation`, event handlers.
- Do not paint an opaque full-canvas background: the video's ground (paper / kraft / solid / ink) must show through.
  Layered decoration (shapes, blobs, rings, lines at low alpha) is encouraged.
- All times from `k.sec()` / `fps`; all positions from `LAYOUT`; keep everything inside `LAYOUT.beat` (never in the caption zone,
  never above `safeTop`); minimum text size 24 px; Arabic only through `ArText`.
- Assets: inline SVG, `Icon`, `MapLayer`. Nothing else.

## Pipeline (pipeline/scene_author.py)
sentence + entities + theme + this kit → LLM → static check (AST allowlist + tsc, `remotion/scripts/check-scene.mjs`) →
sandboxed render of 3 frames → automated checks (not blank, no overflow, no overlap, nothing in the caption zone, Arabic RTL,
text ≥ 22 px) → accepted. On failure the errors go back to the LLM (2 retries), then the built-in beats are kept and a warning
is recorded. Accepted scenes are cached by content hash (`data/authored_cache/`) and saved in the job folder
(`outputs/<job>/scenes/*.tsx`): edit one and run `python scripts/rerender_authored.py outputs/<job>`.
