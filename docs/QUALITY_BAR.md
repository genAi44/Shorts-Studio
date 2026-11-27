# Quality bar — what the reference videos do

References: the 9 videos in `C:\Users\<you>\Desktop\references` (motion-design Shorts) and the GeoLoop channel
(`youtube.com/@GeoLoopog/shorts`, geography Shorts). The target is a **mix** of the two.

## Measured band (every render is checked against it — `pipeline/quality_bar.py`)

| metric | references | our weak render (2026-11-27, Panama) |
|---|---|---|
| motion (mean frame difference, 10 fps) | 3.4 – 13.8 | **1.05** |
| frozen frames (diff < 0.6) | 2 – 13 % | **54 %** |
| mean brightness (0–255) | 134 – 217 (one dark reference: 90) | **22** |

Every render writes `outputs/<job>/quality_bar.json` and `contact_sheet.jpg` (a frame every 2 s), and the job log
prints the three numbers. Check any video: `python -m pipeline.quality_bar path/to/short.mp4 [reference_dir]`.

## What the 9 motion-design references share

- **Light, minimal grounds**: off-white / light grey paper, sometimes a grid or one bold palette (lavender, red + black + cream).
  Monochrome plus one accent colour.
- **Typography is the main visual**: one or two huge words, mixed weights and styles (heavy sans + italic serif), the key word
  in the accent colour or a heavier weight, revealed word by word on the voice. No caption bar and a separate headline.
- **One hero object per shot**: a cut-out photo (person, chess piece, briefcase of money, can, coin, TV) or an icon in a
  floating white card, with a soft drop shadow — real depth, lots of negative space, 1–2 elements per frame.
- **Constant motion**: the camera or the objects always move (push-ins, objects flying in with motion blur, curved lines and
  dashed paths drawing between elements, polaroids swinging on a string). A new visual idea every ~1.5–3 s.

## What GeoLoop adds (geography)

- Full-bleed **real satellite imagery** with one **continuous camera move** (zoom out to the continent, fly, zoom in).
- The region is **outlined with a glow on the map itself**; labels are written on the map, no panels or cards.
- **Sticker cut-outs** (characters, flags, stamps) placed directly on the map.
- Simple white word-by-word captions at the bottom.

## What our renders do instead (contact sheet of the weak render)

- Every scene the same layout: small title, big orange title, a small diagram in the middle, caption at the bottom.
- Dark brown/black ground everywhere, small elements, large dead areas, half the frames frozen.
- One visual per scene (~7–10 s) instead of a new idea every 2–3 s.

## Next upgrades this bar points to

1. Motion: something moves in every frame (camera push, parallax, drawing paths), and 2–3 visual changes inside each scene.
2. Grounds: light paper / satellite grounds as style options, not only dark.
3. Typography as the hero: huge mixed-weight key words revealed on the voice instead of title + separate caption.
