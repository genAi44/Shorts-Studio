# Motion and scene direction playbook - Remotion Official Motion Playbook
# Based on the 13 official Remotion guidelines and skills (remotion-dev/skills v4.0.541)

## 1. Animation and timing rules (remotion-best-practices & remotion-create)
- Animation is a pure function of the frame (deterministic `useCurrentFrame()`).
- Vertical video size: 1080x1920 at 30 frames per second (fps=30).
- No dead static frames; motion continues throughout the beat (no stillness longer than 1.0 second).
- Rhythmic timing:
  - Fast beats (Hook / Punch): 0.8-1.5 seconds.
  - Narration and explanation beats: 1.5-3.0 seconds.
  - Focus and reflection points: 3.0-4.0 seconds.
- Elements always exit faster than they enter (0.22 s exit / 0.38 s entrance).
- Stagger: offset 3-6 frames between the elements of one scene for natural depth and visual flow.

## 2. Motion physics and easing (remotion-markup)
- Sudden appearances, cards and badges: use `spring({damping: 200, mass: 0.8})` to prevent overshoot.
- Lively flowing motion (Scale & Pop): `spring({damping: 22, mass: 0.5})`.
- Smooth entrance: `Easing.bezier(0.16, 1, 0.3, 1)`.
- Fast exit: `Easing.bezier(0.7, 0, 0.84, 0)`.
- Use the modern transform properties `scale`, `translate`, `rotate` directly inside style instead of complex CSS transform strings.
- Respect the keep-out zones: keep the top title zone and the bottom caption zone clear.

## 3. Media and sound effects (remotion-multimedia & remotion-render)
- Real photos: cinematic camera treatment (Ken Burns pan/zoom) with saturated natural colours and high contrast (no dull grey filters).
- Sound effects (SFX): used sparingly and only at decisive moments or impacts; never repeat the same effect (such as a whoosh) in every scene.
- Offline-render compatibility: all assets and fonts are loaded locally for complete stability.

## 4. Maps and geographic routes (remotion-maps)
- Use animated map pins (`map_pin`) and interactive routes (`animated_route`).
- Connected routes with soft curves and smooth transitions between cities and locations.
- Avoid consecutive maps without a rich scene break between them.

## 5. Text and interactive captions (remotion-captions)
- Word-by-word synchronisation with high precision.
- A glow and a distinct colour on the active word to hold the viewer's attention.
- Avoid placing any random visual elements that cover the captions or overlap them.

## 6. Cinematic camera motion
- `zoom-in` / `push-in`: gradual cinematic lens approach (100%->112%) - the default for the hook, realistic photos and prominent facts.
- `zoom-out`: wide panoramic reveal (114%->100%) - excellent for maps, hierarchy charts and networks.
- `pan-left` / `pan-right`: cinematic horizontal glide - for side-by-side comparisons (versus), routes and timelines.
- `tilt-up` / `tilt-down`: vertical sweep - for towering historical buildings, peaks and pyramids.
- `parallax`: multi-speed 3D motion layers for photos and maps.
- Varying the camera move between each beat and the next is mandatory (never repeat the same camera move).

## 7. Interactive scene structures and narrative templates (remotion-interactivity & remotion-saas)
- `generative_canvas`: top priority when representing concepts, interactive processes, networks and motion flows using shapes, badges, animated links and counters.
- `versus_battle`: an epic comparison between two sides or two clashing forces with a central VS badge.
- `stack_pyramid`: a layered pyramid or an ascending hierarchy from the top to the base.
- `balance_meter`: a physical scale that swings between two values or two weights.
- `animated_route`: a transfer path or journey between several stops with an animated progress line.
- `deep_time_slider`: a timeline for historical milestones and successive eras.
- `elevation_profile`: an animated vertical section of the height of a peak or mountain in metres above sea level.
- `stat_ring_v2`: a 3D statistics ring with a golden number and a hero icon in the centre.
- `bars`: bar charts for comparing quantities or percentages.
- `photo`: high-resolution real photos with no dull grey filter and an elegant modern glass frame.
- `map_pin` / `map`: regional maps and precise pins for locations and cities.

## 8. Strict quality rules
- The `icons` kind is forbidden entirely (circles containing repeated stars are banned).
- Never repeat `bigtext` or rely on it as an easy substitute; it is allowed at most once, in the opening (Hook), if needed.
- Strict variety: never two consecutive beats of the same kind anywhere in the video.
- Never introduce or invent numbers or facts that are not explicitly in facts and the script.

<!-- built and checked against the official Remotion skills: remotion-best-practices, remotion-markup, remotion-maps, remotion-captions, remotion-interactivity, remotion-multimedia, remotion-create, remotion-render, remotion-studio, remotion-saas, remotion-docs, remotion-upgrade, remotion-license -->
