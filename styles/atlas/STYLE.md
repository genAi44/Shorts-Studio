# Old Atlas - style guide

> A page from an old atlas: dark ink on warm paper, hatching on the land, one red pin. The map is the hero and the words serve it.
> For geography and the history of places, why the city was built here, why the capital was moved.
> (The video itself is Arabic: every word shown on screen is Arabic, typeset in the Amiri atlas face.)

## 1. The essence, and what it is not
- **One fixed sheet of paper.** A warm paper colour with a light grain: no glow, no blur, no floating particles.
- **Ink and a single red.** Text is dark brown ink; the accent is a brick red used for ONE thing on the screen (the important name or the pin); a second, rare teal is allowed for small details.
- **The map is drawn with hatching.** The land is hatched with slanted lines and is the only clear element; everything around it is faint. No gradients, no card and no frame around the map.
- **One idea per screen.** One place, or a comparison between two places, never more.

Not: a modern data dashboard (no sparkling counters, no neon), not a school textbook (no coloured boxes), not a map pulled from an app (no multiple coloured pin icons).

## 2. Materials and drawing
- The `paper` background, with no motion. Borders are drawn with a thin ink-coloured line, never with light.
- The `pin` in the accent colour, with the place name under it in the atlas face (Amiri) at a phone-readable size (>= 40 px).
- Photographs are frameless (`free`), fade softly into the paper and are tinted with two colours (`duo`) so they look printed. No card and no boxy shadow.
- Travel paths (moving a capital, a journey) are dashed ink lines that are drawn progressively from one point to the next.

## 3. Writing on screen
- The title is two to four words in heavy Amiri, with an ink line under it drawn from right to left.
- Geographic names are written exactly as they are spoken in the narration; a place name that is not spoken is never written.
- A year or a number appears only once, as plain digits, with no thousands separator for years.

## 4. Rhythm and direction
- A calm rhythm (pace 0.9): the map enters by being drawn, not by jumping, and every scene keeps its pin until the end of the sentence.
- When the place changes, the camera travels over the same map (zoom, then glide) instead of cutting to another scene.
- The reveal scene (the climax): the red pin arrives at its place and everything else fades.
- The closing: back to the full map with no pins except the last one.

## 5. Instructions for the visual director (injected into scene requests)
- Choose `map` or `area_map` for every sentence that contains a place name; never replace it with text.
- No white cards and no coloured boxes; write the name directly on the paper.
- Use one accent colour (brick red) for one word or one pin in the scene.
- Numbers and dates: once, near the map, never in a card.
