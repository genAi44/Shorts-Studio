# QA report — Playwright MCP run (2026-11-23)

Scope: the web app (`app.py` + `static/index.html`), driven for real with the Playwright MCP (`browser_run_code_unsafe`, snapshots,
evaluate, route interception) on **desktop 1280x800, tablet 768x1024 (touch), mobile 390x844 (touch, DPR 2)**.
Scenarios: `qa/playwright/*.tpl.js` (run with `__DEVICE__` / `__TAG__` replaced; the `run3-*.js` files are the generated ones).
Videos: `test-results/videos/<run>/<device>/*.webm` (git-ignored). Screenshots: `test-results/shots/<run>/`.

## How the videos were "watched"
I cannot play a video. Every recording was sampled with ffmpeg into 18-frame contact sheets (`video_sheet_<device>.jpg`) plus
per-step screenshots, and those images were inspected. Frame-level motion between samples was not reviewed.

## What was tested (all three viewports + an error-injection run)
load and status chips · LLM health / routing log / role settings · empty idea · sample script · title/description/tags editing ·
condition check · director (no model) · visual library · 3 style presets · random style · invalid style JSON · frame preview ·
production controls · render progress and result (**network-mocked: no paid ElevenLabs call**) · keyboard Tab order and focus ring ·
server 500 / network failure on script, director, preview, render · render success without a url · fact check (real Gemini, free tier) ·
horizontal overflow, touch-target size, unnamed fields, console errors, failed requests on every step.

Not tested: a real end-to-end render with ElevenLabs (paid; covered in earlier sessions), the DeepSeek director and the style
art-director model calls (paid/rate-limited), and drag/resize interactions the page does not have.

## Problems found (run 1, before the fixes) and what was done
| # | Problem | Evidence | Fix |
|---|---|---|---|
| 1 | Two previews at once overwrote one shared file (`outputs/_prev/preview.jpg`); also shared generated TSX | code + two concurrent requests: 16 s vs 87 s | per-request folder, one preview at a time, folder removed afterwards |
| 2 | Visual library returned unresolved flags → `<img src="/assets/">` 404 | network log 404 on all 3 devices | server filters them, client guards |
| 3 | Invalid style JSON: only a red border, no message; the red border stayed after choosing a valid preset | screenshot `08-bad-json`, `09-preview` | message + border reset |
| 4 | 40 form fields without an accessible name (10 LLM role selects, idea, title, …) | DOM audit | names derived from the visible label, also for dynamic content |
| 5 | Touch targets: header buttons 32 px high, checkbox 13 px | DOM audit on tablet/mobile | `pointer: coarse` ≥ 40–44 px, checkbox 20 px |
| 6 | Connection check used a blocking `alert()` | code | inline result line |
| 7 | Empty idea sent a request and got a 400 | network log | client-side check |
| 8 | Render finished without a url → broken `<video src="undefined">` | `/undefined` 404 | guard + message |
| 9 | Preview of a "free" photo style with no photo showed a dark blob behind the title | screenshot `09-preview` | placeholder made faint |

## Results after the fixes (run 3, new videos)
desktop 19/19 steps · tablet 19/19 · mobile 19/19 · error run 10/10. No page errors, no unexpected 4xx/5xx (the remaining 4xx/5xx
are the injected faults and the mocked video url), 0 unnamed fields, no horizontal overflow, touch targets fine
(only the 20 px checkbox, whose label is the real hit area), preview 11–12 s.

## Not fixed / worth knowing
* **A render running at the same time as a preview can still clash** on `remotion/src/generated/DynamicScenes.tsx` and `src/authored/` (shared files). Previews are serialised against each other only.
* The frame preview takes 10–80 s depending on the LLM TSX path (a failed tsc check triggers an LLM repair with a 65 s timeout); the page shows only "جارٍ الرسم…".
* Fact check took 12–46 s on the free Gemini tier with no progress indicator.
* `+ مقطع` (add part) exists in the HTML but is hidden (`display:none`): a dead control.
* Header buttons are 32 px high on desktop (fine for a mouse).

## Process note
`pytest-playwright` empties `test-results/` at every pytest start. It deleted the first-run videos and screenshots (run 1 and 2) during
this session. `pytest.ini` now passes `-p no:playwright`; the run-1 findings above come from the step logs captured at the time.
