# shorts-studio — project rules

This repo (Python pipeline + `remotion/`) is **not** the vector-only `remotion-studio/` protocol described in `~/Desktop/CLAUDE.md`.
Here, licensed photos (Wikimedia Commons, Wikipedia, Pexels) are **allowed and intended** (`photo` beat, `pipeline/media.py`).

- Rule 1.1 "no raster" does not apply. Still banned: AI-generated images, real-brand logos, unlicensed images (license is recorded per photo).
- Every number shown next to a photo must appear in the scene narration (`direct.py::_number_in_text`).
- A flag badge is shown only when the scene concerns exactly one country (`visual_tools.py`).
- Rule 1.2 (no text-only scenes) still applies (`visual_qa.py`).
