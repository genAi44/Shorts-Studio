# Official Documentation & Sources (`docs/LINKS.md`)

All links below were verified against official documentation and package registries (2026-11-05 / 2026-11-06).
Every `remotion` and `@remotion/*` package in [`remotion/package.json`](../remotion/package.json) is pinned to the **exact** version `"4.0.539"` (no `^` or `~`).

---

## 1. Remotion Core & Official Packages (`4.0.539`)

- ✓ **Components Overview**: https://www.remotion.dev/docs/components
- ✓ **API & Packages Overview**: https://www.remotion.dev/docs/api
- ✓ **Official Remotion Agent Skills (`remotion-markup`)**: https://github.com/remotion-dev/skills
  - *Note*: The `remotion-markup` skill documents `<TransitionSeries>`, `@remotion/shapes`, `@remotion/lottie`, `@remotion/noise`, `@remotion/paths`, and recommends CSS/SVG filter + `<Trail>` (`@remotion/motion-blur`) or HTML-in-canvas effects (`glow`, `vignette`, `lightLeak`) depending on scene complexity. In Remotion `4.0.539`, `@remotion/transitions`, `@remotion/shapes`, `@remotion/paths`, `@remotion/lottie`, `@remotion/noise`, `@remotion/motion-blur`, `@remotion/google-fonts`, and `@remotion/sfx` are stable and verified.

### Verified Package Documentation URLs
- ✓ **`remotion`**: https://www.remotion.dev/docs/
- ✓ **`@remotion/cli`**: https://www.remotion.dev/docs/cli
- ✓ **`@remotion/media`**: https://www.remotion.dev/docs/media
- ✓ **`@remotion/fonts`**: https://www.remotion.dev/docs/fonts
- ✓ **`@remotion/google-fonts`**: https://www.remotion.dev/docs/google-fonts
- ✓ **`@remotion/transitions`**: https://www.remotion.dev/docs/transitions
  - Presentations: `fade` (`/fade`), `slide` (`/slide`), `wipe` (`/wipe`), `flip` (`/flip`), `clockWipe` (`/clock-wipe`)
- ✓ **`@remotion/shapes`**: https://www.remotion.dev/docs/shapes
  - Components/Generators: `<Rect>`, `<Circle>`, `<Triangle>`, `<Star>`, `<Polygon>`, `<Ellipse>`, `<Heart>`, `<Pie>`, `makeRect`, `makeCircle`, `makeTriangle`, `makeStar`, `makePolygon`
- ✓ **`@remotion/paths`**: https://www.remotion.dev/docs/paths
  - Utilities: `evolvePath`, `getLength`, `getPointAtLength`, `getTangentAtLength`, `interpolatePath`, `extendViewBox`
- ✓ **`@remotion/lottie`**: https://www.remotion.dev/docs/lottie
  - Component: `<Lottie animationData={...} loop={...} playbackRate={...} direction="forward" />`
- ✓ **`@remotion/noise`**: https://www.remotion.dev/docs/noise
  - Utilities: `noise2D(seed, x, y)`, `noise3D(seed, x, y, z)`, `noise4D(seed, x, y, z, w)`
- ✓ **`@remotion/motion-blur`**: https://www.remotion.dev/docs/motion-blur
  - Components: `<Trail layers={...} lagInFrames={...} trailOpacity={...}>`, `<CameraMotionBlur shutterAngle={...} samples={...}>`
- ✓ **`@remotion/sfx`**: https://www.remotion.dev/docs/sfx
  - Bundled sound effects: `whoosh`, `whip`, `pageTurn`, `switch`, `mouseClick`, `shutterModern`, `shutterOld`, `ding`, `bruh`, `vineBoom`, `windowsXpError`
- ✓ **`@remotion/layout-utils`**: https://www.remotion.dev/docs/layout-utils
  - Utilities: `measureText`, `fillTextBox`, `fitText`, `fitTextOnNLines`
- ✓ **`@remotion/animation-utils`**: https://www.remotion.dev/docs/animation-utils
  - Utilities: `makeTransform`, `interpolateStyles`, `translate`, `scale`, `rotate`, `skew`
- ✓ **`@remotion/animated-emoji`**: https://www.remotion.dev/docs/animated-emoji *(Note: fetches assets or requires local public copy; we use offline bundled Noto Emoji SVGs + Remotion frame-driven spring presets for 100% offline deterministic rendering)*
- ✓ **`@remotion/gif`**: https://www.remotion.dev/docs/gif
- ✓ **`@remotion/light-leaks`**: https://www.remotion.dev/docs/light-leaks
- ✓ **`@remotion/starburst`**: https://www.remotion.dev/docs/starburst
- ✓ **`@remotion/rough-notation`**: https://www.remotion.dev/docs/rough-notation
- ✓ **`@remotion/rive`**: https://www.remotion.dev/docs/rive

---

## 2. Icons (Iconify — 100% Offline)

- ✓ **Icon Data Sources**: https://iconify.design/docs/icons/icon-data.html
- ✓ **Individual Icon-Set Packages (`@iconify-json/{prefix}`)**: https://iconify.design/docs/icons/json.html
- ✓ **All Icons Package (`@iconify/json`) & Helpers**: https://iconify.design/docs/icons/all.html
- ✓ **Iconify Icon Sets Repository**: https://github.com/iconify/icon-sets
- ✓ **Iconify Utils (`getIconData`, `iconToSVG`, `iconToHTML`, `replaceIDs`)**: https://iconify.design/docs/libraries/utils/
- ✓ **Iconify Set Browser & License Inspector**: https://icon-sets.iconify.design/
- **Bundled Offline Sets**:
  - `@iconify-json/lucide` (`1.2.x`, ISC License): https://icon-sets.iconify.design/lucide/
  - `@iconify-json/ph` (Phosphor Icons `1.2.x`, MIT License): https://icon-sets.iconify.design/ph/
  - `@iconify-json/tabler` (Tabler Icons `1.2.x`, MIT License): https://icon-sets.iconify.design/tabler/

---

## 3. Emoji (100% Offline Bundled SVG/PNG)

- ✓ **Google Noto Emoji** (Fonts under SIL OFL 1.1; SVG/PNG graphics under Apache-2.0; flags under Public Domain): https://github.com/googlefonts/noto-emoji
- ✓ **Twemoji Maintained Fork (`@jdecked/twemoji`)** (Graphics under CC-BY 4.0 — attribution recorded in `credits.json` when used; code under MIT): https://github.com/jdecked/twemoji
- ✓ **OpenMoji** (CC BY-SA 4.0 — share-alike; avoided in favor of Apache-2.0 Noto Emoji): https://github.com/hfg-gmuend/openmoji
- ✓ **Google Noto Animated Emoji** (CC BY 4.0): https://googlefonts.github.io/noto-emoji-animation/

---

## 4. Flags (100% Offline Bundled SVG)

- ✓ **`flag-icons` (Lipis SVG Flags — MIT License)**: https://github.com/lipis/flag-icons
- ✓ **Noto `region-flags` (Public Domain alternative)**: https://github.com/googlefonts/noto-emoji/tree/main/third_party/region-flags

---

## 5. Charts, Scales, Geometry & Validation

- ✓ **D3.js Official Documentation**: https://d3js.org/
  - ✓ **`d3-scale` (ISC)**: https://d3js.org/d3-scale
  - ✓ **`d3-shape` (ISC)**: https://d3js.org/d3-shape
  - ✓ **`d3-array` (ISC)**: https://d3js.org/d3-array
  - ✓ **`d3-geo` (ISC)**: https://d3js.org/d3-geo
  - *Usage Rule*: Pure SVG computation (`scaleBand`, `scaleLinear`, `line`, `area`, `pie`, `arc`), never DOM-mutating `d3-selection` inside React/Remotion.
- ✓ **World Atlas TopoJSON (`world-atlas`, ISC)**: https://github.com/topojson/world-atlas
- ✓ **TopoJSON Client (`topojson-client`, ISC)**: https://github.com/topojson/topojson-client
- ✓ **Zod Schema Validation (`zod`, MIT)**: https://zod.dev/

---

## 6. Lottie Animations (Offline Curated Library)

- ✓ **Lottie-Web Format & Runtime (`lottie-web`, MIT)**: https://github.com/airbnb/lottie-web
- ✓ **LottieFiles Free Animations (Lottie Simple License / CC0)**: https://lottiefiles.com/free-animations
- ✓ **Local Manifest**: [`packages/assets/lottie/manifest.json`](../packages/assets/lottie/manifest.json)
