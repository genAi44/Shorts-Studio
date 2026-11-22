<div align="center">

# 🎬 Shorts Studio

### AI-powered Arabic YouTube Shorts generator — topic in, viral video out.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Node.js 18+](https://img.shields.io/badge/Node.js-18+-green.svg)](https://nodejs.org)
[![Remotion](https://img.shields.io/badge/Remotion-4.x-purple.svg)](https://remotion.dev)
[![Issues Welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![Arabic](https://img.shields.io/badge/language-Arabic-orange.svg)]()

<br/>

> Write one topic. Get a fully-rendered, voiced, animated Arabic Short in minutes.

<br/>

<!-- DEMO GIF PLACEHOLDER — replace with actual screen recording -->
<!-- ![Shorts Studio Demo](docs/demo.gif) -->

**[English](#english) · [العربية](#arabic)**

</div>

---

<a id="english"></a>

## What is Shorts Studio?

Shorts Studio is an end-to-end AI pipeline that transforms a **single Arabic topic** into a production-ready YouTube Short:

| Step | What happens |
|---|---|
| 🧠 **Script** | Gemini + Google Search writes a fact-checked 8-part viral script |
| 🗣️ **Voice** | ElevenLabs generates natural Arabic narration with word-level timestamps |
| 🎨 **Visuals** | DeepSeek art-directs per-sentence motion graphics (maps, stats, timelines) |
| 🎬 **Animation** | Remotion (React) renders every scene as a pure, deterministic function |
| 🎵 **Audio mix** | FFmpeg assembles the final MP4 with ducked music and SFX |

The result: a **40–55 second, 1080×1920 vertical video** with a retention-engineered structure — no manual editing required.

---

## ✨ Features

- 🤖 **Multi-model pipeline** — Gemini (script + fact-check) · DeepSeek (visual direction) · ElevenLabs (TTS)
- 📐 **8-part viral script structure** — HOOK → LEAD → BODY × 3 → OPEN LOOPs → CTA
- 🗺️ **Rich motion graphics** — Animated maps, stat counters, bar charts, timelines, comparison cards
- 🔤 **RTL Arabic captions** — Word-synced karaoke with active-word glow, built for Arabic
- ✅ **Fact-checking built in** — Every on-screen number is sourced before the video renders
- 🖥️ **Local web UI** — Browse, edit scene JSON, re-render individual scenes via Flask
- 🧩 **Modular** — Swap LLM providers, TTS engine, or renderer independently

---

## 🚀 Quick Start

**Prerequisites:** Python 3.10+, Node.js 18+, FFmpeg

```bash
# 1. Clone
git clone https://github.com/genAi44/shorts-studio.git
cd shorts-studio

# 2. Python dependencies
pip install -r requirements.txt

# 3. Remotion renderer
cd remotion && npm install && cd ..

# 4. Configure API keys
cp .env.example .env
# Edit .env — add ELEVENLABS_API_KEY, GEMINI_API_KEY, DEEPSEEK_API_KEY

# 5. Run
./run.sh      # Linux / macOS
run.bat       # Windows
# → open http://localhost:8000
```

> **No API keys?** Click **"حمّل سكربتاً تجريبياً"** (Load test script) in the UI to explore the editor with a preloaded script — no production keys required.

---

## 🏗️ Architecture

```
shorts-studio/
├── app.py              ← Flask web app (UI + API)
├── pipeline/           ← Core AI pipeline
│   ├── storyteller.py  ← Script generation (Gemini + search)
│   ├── tts.py          ← ElevenLabs TTS + word timestamps
│   ├── render.py       ← Scene orchestration
│   ├── factcheck.py    ← Fact verification
│   └── geo.py          ← Animated map engine
├── remotion/           ← React/Remotion renderer
│   └── src/
│       ├── Root.tsx    ← Composition entry
│       └── scenes/     ← Per-scene React components
├── tools/              ← CLI utilities (voiceover, SFX, assets)
└── assets/             ← Shared asset library
```

---

## 🤝 Contributing — No Coding Required!

We welcome contributions from **everyone**:

| Role | How to help |
|---|---|
| 📝 **Content creator** | [Suggest viral topic ideas](https://github.com/genAi44/shorts-studio/issues/new?template=content-idea.md) |
| 🌐 **Translator / editor** | Improve Arabic prompts in `pipeline/prompts/` |
| 🧪 **Tester** | Run the pipeline and report issues |
| 🎨 **Designer** | Improve the web UI or create better SVG assets |
| 👩‍💻 **Developer** | Fix bugs, add features, improve performance |

**[→ Full Contributing Guide](CONTRIBUTING.md)**

---

## 🧩 Entity → visual system

Every entity named in the narration gets a visual of its type in its sentence's scene; every place (village … globe) gets a map.
One registry (`pipeline/entities.py`), one structural llm extraction, local validation, one retry to the director, a visible fallback.
Guide + how to add a type: [`docs/ENTITIES.md`](docs/ENTITIES.md).

```bash
python scripts/build_entity_fixture.py                                   # tests/fixtures/entities_spec.json (one scene per entity type)
SMOKE_FIXTURE=tests/fixtures/entities_spec.json python scripts/smoke_test.py
python -m pytest tests/test_entities.py                                  # fails when a sentence has an entity but no visual
```

Fallbacks are listed in `qa_report.json`, returned as `warnings` by `/api/job/<id>` and shown under the video in the UI.

## 🔬 Visual smoke test

Renders one scene per beat kind (plus map-overlay and LLM-scene cases) and checks every frame automatically.

```bash
cd remotion && npm install && cd ..
python scripts/build_fixture.py        # tests/fixtures/all_beats_spec.json (every beat goes through direct.normalize_beat)
python scripts/smoke_test.py           # frames 1, 15, 45, 90, 149 of every scene (--quick: 15 and 90; --scenes a,b)
```

- **FAIL**: flat frame, text touching the canvas edge, two text boxes overlapping >25%.
  Edge/overlap in the first 30 frames (entrance animations) and text under 22 px are warnings.
- Output in `outputs/smoke/`: `report.json` and `contact_NN.jpg` contact sheets (red = fail, amber = warning).
- The DOM audit is `remotion/src/layoutAudit.tsx`, enabled by `AUDIT=1` in `remotion/still.mjs`.
- Contracts checked in CI-style tests: `python -m pytest tests/test_contracts.py` (schema ⇄ renderer ⇄ director kinds, generated `schema.ts`, layout constants).

## 📋 Requirements

| Dependency | Version | Purpose |
|---|---|---|
| Python | 3.10+ | Pipeline + Flask server |
| Node.js | 18+ | Remotion renderer |
| FFmpeg | any recent | Audio/video assembly |
| ElevenLabs API | — | Arabic TTS |
| Gemini API | — | Script + fact-check |
| DeepSeek API | — | Visual direction |

---

## 📄 License

MIT — free to use, modify, and distribute. See [LICENSE](LICENSE).

---

<a id="arabic"></a>

## 🇸🇦 النسخة العربية

### ما هو Shorts Studio؟

Shorts Studio هو خط إنتاج متكامل يحوّل **موضوعاً عربياً واحداً** إلى فيديو Short جاهز للنشر:

| الخطوة | ما يحدث |
|---|---|
| 🧠 **السكربت** | Gemini + بحث Google يكتب سكربتاً فيروسياً من 8 أجزاء مع التحقق من الحقائق |
| 🗣️ **الصوت** | ElevenLabs تولّد تعليقاً صوتياً عربياً طبيعياً مع توقيت كل كلمة |
| 🎨 **المرئيات** | DeepSeek يصمّم موشن غرافيك لكل جملة (خرائط، إحصاءات، جداول زمنية) |
| 🎬 **الحركة** | Remotion (React) يرسم كل مشهد كدالة حتمية نقية |
| 🎵 **المزج الصوتي** | FFmpeg يجمّع الـ MP4 النهائي مع موسيقى خلفية وتأثيرات صوتية |

النتيجة: فيديو Short عربي **40-55 ثانية، 1080×1920** بهيكل فيروسي — دون أي تحرير يدوي.

### ✨ المزايا

- 🤖 **خط إنتاج متعدد النماذج** — Gemini · DeepSeek · ElevenLabs
- 📐 **هيكل فيروسي من 8 أجزاء** — HOOK → LEAD → BODY × 3 → OPEN LOOPs → CTA
- 🗺️ **موشن غرافيك غني** — خرائط متحركة، عدادات، مخططات، جداول زمنية
- 🔤 **تعليق توضيحي RTL** — كلمة بكلمة، مع توهج الكلمة النشطة
- ✅ **فحص الحقائق مدمج** — كل رقم على الشاشة موثَّق قبل العرض
- 🖥️ **واجهة ويب محلية** — تصفح، حرّر، أعد الرسم عبر Flask

### 🚀 بدء التشغيل السريع

```bash
git clone https://github.com/genAi44/shorts-studio.git
cd shorts-studio
pip install -r requirements.txt
cd remotion && npm install && cd ..
cp .env.example .env   # أضف مفاتيح API
./run.sh               # أو run.bat في ويندوز
# افتح http://localhost:8000
```

### 🤝 المساهمة

نرحب بالجميع — [اقترح موضوعاً](https://github.com/genAi44/shorts-studio/issues/new?template=content-idea.md) · حسّن البرومبتات · اختبر وأبلّغ · صمّم · طوّر

**[← دليل المساهمة الكامل](CONTRIBUTING.md)**

---

<div align="center">

Made with ❤️ for Arabic content creators · صُنع بـ ❤️ لصنّاع المحتوى العربي

⭐ **Star this repo if it helped you!** ⭐

</div>
