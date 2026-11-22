# Asset & Package Licenses (`docs/LICENSES.md`)

All visual assets, icon sets, emoji graphics, flags, fonts, Lottie animations, and libraries bundled in `packages/assets/` and `remotion/` have been verified for offline bundling and personal/studio use.

---

## 1. Offline Icon Collections (`packages/assets/icons/` & `@iconify-json/*`)

| Collection / Package | Prefix | Version | License | Attribution Required? | Source URL |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Lucide Icons** (`@iconify-json/lucide`) | `lucide` | `1.2.x` | **ISC License** | No (copyright notice retained in package/docs) | https://github.com/lucide-icons/lucide |
| **Phosphor Icons** (`@iconify-json/ph`) | `ph` | `1.2.x` | **MIT License** | No | https://github.com/phosphor-icons/core |
| **Tabler Icons** (`@iconify-json/tabler`) | `tabler` | `1.2.x` | **MIT License** | No | https://github.com/tabler/tabler-icons |
| **Iconify Utils** (`@iconify/utils`) | — | `2.x` / `3.x` | **MIT License** | No | https://github.com/iconify/iconify |

---

## 2. Offline Emoji Graphics (`packages/assets/emoji/`)

| Collection | Format | License | Attribution Required? | Source URL |
| :--- | :--- | :--- | :--- | :--- |
| **Google Noto Color Emoji** (Primary Default) | SVG / PNG | **Apache License 2.0** | No for graphics; Apache-2.0 notice included here | https://github.com/googlefonts/noto-emoji |
| **Twemoji (`@jdecked/twemoji`)** (Optional Fallback) | SVG | **CC-BY 4.0** (Graphics) / **MIT** (Code) | **Yes** — automatically recorded in `credits.json` whenever a `twemoji` asset is used | https://github.com/jdecked/twemoji |
| **Noto Animated Emoji** (Optional) | Lottie / JSON | **CC-BY 4.0** | **Yes** — automatically recorded in `credits.json` when used | https://googlefonts.github.io/noto-emoji-animation/ |

> **Policy**: OpenMoji (CC BY-SA 4.0 ShareAlike) is intentionally excluded so rendered outputs are not encumbered by ShareAlike copyleft requirements.

---

## 3. Offline Country Flags (`packages/assets/flags/`)

| Collection / Package | Ratios | License | Attribution Required? | Source URL |
| :--- | :--- | :--- | :--- | :--- |
| **`flag-icons` (Lipis)** | `4x3` (rect) & `1x1` (round/square) | **MIT License** | No | https://github.com/lipis/flag-icons |
| **Google Noto `region-flags`** | SVG | **Public Domain (CC0 / PD)** | No | https://github.com/googlefonts/noto-emoji/tree/main/third_party/region-flags |

---

## 4. Curated Offline Lottie Library (`packages/assets/lottie/`)

Every Lottie animation in `packages/assets/lottie/` is stored with its full metadata, source URL, author, and license in [`packages/assets/lottie/manifest.json`](../packages/assets/lottie/manifest.json).

| Asset ID | File | Category | License | Attribution Required? |
| :--- | :--- | :--- | :--- | :--- |
| `checkmark` | `packages/assets/lottie/checkmark.json` | `check` | **CC0 1.0 Public Domain / MIT** | No |
| `arrow-right` | `packages/assets/lottie/arrow-right.json` | `arrows` | **CC0 1.0 Public Domain / MIT** | No |
| `arrow-up` | `packages/assets/lottie/arrow-up.json` | `arrows` | **CC0 1.0 Public Domain / MIT** | No |
| `loader-ring` | `packages/assets/lottie/loader-ring.json` | `loaders` | **CC0 1.0 Public Domain / MIT** | No |
| `confetti-burst` | `packages/assets/lottie/confetti-burst.json` | `confetti` | **CC0 1.0 Public Domain / MIT** | No |
| `sparkles-gold` | `packages/assets/lottie/sparkles-gold.json` | `sparkles` | **CC0 1.0 Public Domain / MIT** | No |
| `transition-sweep` | `packages/assets/lottie/transition-sweep.json` | `transitions` | **CC0 1.0 Public Domain / MIT** | No |
| `pulse-target` | `packages/assets/lottie/pulse-target.json` | `highlights` | **CC0 1.0 Public Domain / MIT** | No |

---

## 5. Charts, Math, Maps & Fonts

| Package / Asset | License | Notes |
| :--- | :--- | :--- |
| `d3-scale`, `d3-shape`, `d3-array`, `d3-geo` | **ISC License** | Pure SVG calculation only |
| `world-atlas`, `topojson-client` | **ISC License** | Natural Earth public domain map vectors |
| `data/world.geojson` (+ `world-atlas`) | **Public Domain** (Natural Earth 10m `admin_0_countries`) | Country outlines for the vector map engine; no network at render time |
| `zod` | **MIT License** | Schema validation |
| `@remotion/google-fonts` & Bundled Arabic/English Fonts (`Cairo`, `Noto Kufi Arabic`, `Tajawal`, `Amiri`, `Changa`, `El Messiri`, `Reem Kufi`, `Markazi Text`, `Lalezar`, `Inter`, `Montserrat`) | **SIL Open Font License 1.1 (OFL-1.1)** | Bundled locally in `data/` and `remotion/public/fonts/` |
| `remotion` & `@remotion/*` (`4.0.539`) | **Remotion License** (Free for individuals and companies ≤ 3 people; see https://www.remotion.dev/license) | Pinned to exact version `4.0.539` |

