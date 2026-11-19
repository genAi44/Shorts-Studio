<div align="center">

# 🎬 Shorts Studio | استوديو Shorts

**AI-powered Arabic YouTube Shorts generator — topic in, viral video out.**

**مولّد فيديوهات Shorts العربية بالذكاء الاصطناعي — فكرة واحدة تدخل، فيديو احترافي يخرج.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Node.js 18+](https://img.shields.io/badge/Node.js-18+-green.svg)](https://nodejs.org)
[![Remotion](https://img.shields.io/badge/Remotion-4.x-purple.svg)](https://remotion.dev)
[![Issues Welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![Arabic](https://img.shields.io/badge/language-Arabic%20%7C%20English-orange.svg)]()

<br/>

> **Write a topic. Get a fully-rendered, voiced, animated Arabic Short in minutes.**
>
> اكتب موضوعاً واحداً، واحصل على فيديو Short عربي منطوق ومتحرك بالكامل في دقائق.

<br/>

<!-- DEMO GIF PLACEHOLDER — replace with actual screen recording -->
<!-- ![Shorts Studio Demo](docs/demo.gif) -->

**[English](#english) · [العربية](#arabic)**

</div>

---

<a id="english"></a>

## 🇬🇧 English

### What is Shorts Studio?

Shorts Studio is an end-to-end pipeline that transforms a **single Arabic topic** into a production-ready YouTube Short:

1. 🧠 **Script** — Gemini + Google Search writes a fact-checked 8-part viral script
2. 🗣️ **Voice** — ElevenLabs generates natural Arabic narration with word-level timestamps
3. 🎨 **Visuals** — DeepSeek art-directs per-sentence motion graphics (maps, stats, timelines, characters)
4. 🎬 **Animation** — Remotion (React) renders every scene as a pure, deterministic function
5. 🎵 **Audio mix** — FFmpeg assembles final MP4 with ducked music and SFX

The result: a 40–55 second, 1080×1920, viral-structured Arabic Short — no manual editing required.

---

### ✨ Features

| Feature | Detail |
|---|---|
| 🤖 **Multi-model pipeline** | Gemini (script + fact-check) + DeepSeek (visual direction) + ElevenLabs (TTS) |
| 📐 **8-part viral structure** | HOOK → LEAD → BODY × 3 → OPEN LOOPs → CTA — engineered for watch-time |
| 🗺️ **Rich motion graphics** | Animated maps, stat counters, bar charts, timelines, comparison cards |
| 🔤 **RTL Arabic captions** | Word-synced, karaoke-style with active-word glow — built for Arabic |
| 🎙️ **Natural Arabic voice** | ElevenLabs multilingual v2 with word-level timestamps |
| ✅ **Fact-checking built-in** | Every on-screen number is sourced before the video renders |
| 🖥️ **Local web app** | Flask UI — browse, edit scene JSON, re-render individual scenes |
| 🧩 **Modular** | Swap LLM providers, TTS engine, or renderer independently |

---

### 🚀 Quick Start (5 steps)

**Prerequisites:** Python 3.10+, Node.js 18+, FFmpeg

```bash
# 1. Clone the repo
git clone https://github.com/genAi44/shorts-studio.git
cd shorts-studio

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Install Remotion renderer
cd remotion && npm install && cd ..

# 4. Configure API keys
cp .env.example .env
# Edit .env — add ELEVENLABS_API_KEY, GEMINI_API_KEY, DEEPSEEK_API_KEY

# 5. Run
./run.sh          # Linux / macOS
run.bat           # Windows
# Open http://localhost:8000
```

> **No API keys?** Press "حمّل سكربتاً تجريبياً" (Load test script) in the UI to explore the editor with a preloaded script — no production keys required.

---

### 🏗️ Architecture

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
├── assets/             ← Shared asset library
└── static/             ← Web UI (HTML/CSS/JS)
```

---

### 🌍 How to Contribute (No Coding Required!)

We welcome contributions from **everyone** — not just developers:

| Role | How to help |
|---|---|
| 📝 **Content creator** | Suggest viral topic ideas via [Issues](https://github.com/genAi44/shorts-studio/issues) |
| 🌐 **Translator** | Improve Arabic prompts in `pipeline/prompts/` or translate the UI |
| 🧪 **Tester** | Run the pipeline and report issues with scripts, voice, or visuals |
| 🎨 **Designer** | Improve the web UI or create better SVG assets |
| 👩‍💻 **Developer** | Fix bugs, add features, improve performance |

**[→ Read the full Contributing Guide](CONTRIBUTING.md)**

---

### 📋 Requirements

| Dependency | Version | Purpose |
|---|---|---|
| Python | 3.10+ | Pipeline + Flask server |
| Node.js | 18+ | Remotion renderer |
| FFmpeg | any recent | Audio/video assembly |
| ElevenLabs API | — | Arabic TTS |
| Gemini API | — | Script + fact-check |
| DeepSeek API | — | Visual direction |

---

### 📄 License

MIT — free to use, modify, and distribute. See [LICENSE](LICENSE).

---

<a id="arabic"></a>

## 🇸🇦 العربية

### ما هو Shorts Studio؟

Shorts Studio هو خط إنتاج متكامل يحوّل **موضوعاً عربياً واحداً** إلى فيديو Short جاهز للنشر على يوتيوب:

1. 🧠 **السكربت** — Gemini + بحث Google يكتب سكربتاً فيروسياً من 8 أجزاء مع التحقق من الحقائق
2. 🗣️ **الصوت** — ElevenLabs تولّد تعليقاً صوتياً عربياً طبيعياً مع توقيت كل كلمة
3. 🎨 **المرئيات** — DeepSeek يصمّم موشن غرافيك لكل جملة (خرائط، إحصاءات، جداول زمنية، شخصيات)
4. 🎬 **الحركة** — Remotion (React) يرسم كل مشهد كدالة حتمية نقية
5. 🎵 **المزج الصوتي** — FFmpeg يجمّع الـ MP4 النهائي مع موسيقى خلفية وتأثيرات صوتية

النتيجة: فيديو Short عربي 40-55 ثانية، 1080×1920، بهيكل فيروسي — دون أي تحرير يدوي.

---

### ✨ المزايا

| الميزة | التفاصيل |
|---|---|
| 🤖 **خط إنتاج متعدد النماذج** | Gemini (السكربت + التحقق) + DeepSeek (الإخراج البصري) + ElevenLabs (التحويل للصوت) |
| 📐 **هيكل فيروسي من 8 أجزاء** | HOOK → LEAD → BODY × 3 → OPEN LOOPs → CTA — مهندَس لتعظيم وقت المشاهدة |
| 🗺️ **موشن غرافيك غني** | خرائط متحركة، عدادات إحصائية، مخططات بيانية، جداول زمنية، بطاقات مقارنة |
| 🔤 **تعليق توضيحي عربي RTL** | كلمة بكلمة، أسلوب كاريوكي مع توهج الكلمة النشطة — مبني للعربية |
| 🎙️ **صوت عربي طبيعي** | ElevenLabs متعدد اللغات v2 مع توقيت على مستوى الكلمة |
| ✅ **فحص الحقائق مدمج** | كل رقم على الشاشة موثَّق قبل أن يُعرض الفيديو |
| 🖥️ **تطبيق ويب محلي** | واجهة Flask — تصفح، حرّر JSON المشاهد، أعد رسم المشاهد الفردية |
| 🧩 **معياري** | استبدل موفر LLM أو محرك TTS أو المُصيِّر باستقلالية |

---

### 🚀 بدء التشغيل السريع (5 خطوات)

**المتطلبات:** Python 3.10+، Node.js 18+، FFmpeg

```bash
# 1. استنسخ المستودع
git clone https://github.com/genAi44/shorts-studio.git
cd shorts-studio

# 2. ثبّت تبعيات Python
pip install -r requirements.txt

# 3. ثبّت مُصيِّر Remotion
cd remotion && npm install && cd ..

# 4. اضبط مفاتيح API
cp .env.example .env
# حرّر .env — أضف ELEVENLABS_API_KEY و GEMINI_API_KEY و DEEPSEEK_API_KEY

# 5. شغّل
./run.sh          # Linux / macOS
run.bat           # Windows
# افتح http://localhost:8000
```

> **بلا مفاتيح API؟** اضغط "حمّل سكربتاً تجريبياً" في الواجهة لاستكشاف المحرر بسكربت جاهز — لا يلزم مفاتيح إنتاج.

---

### 🤝 كيف تساهم (بدون برمجة!)

نرحب بمساهمات **الجميع** — ليس فقط المطورين:

| الدور | طريقة المساهمة |
|---|---|
| 📝 **صانع محتوى** | اقترح أفكار مواضيع فيروسية عبر [Issues](https://github.com/genAi44/shorts-studio/issues) |
| 🌐 **مترجم** | حسّن البرومبتات العربية في `pipeline/prompts/` أو ترجم الواجهة |
| 🧪 **مختبر** | شغّل الخط الإنتاجي وأبلّغ عن مشاكل في السكربتات أو الصوت أو المرئيات |
| 🎨 **مصمم** | حسّن واجهة الويب أو أنشئ أصول SVG أفضل |
| 👩‍💻 **مطور** | أصلح الأخطاء، أضف ميزات، حسّن الأداء |

**[← اقرأ دليل المساهمة الكامل](CONTRIBUTING.md)**

---

### 📄 الترخيص

MIT — حر الاستخدام والتعديل والتوزيع. انظر [LICENSE](LICENSE).

---

<div align="center">

Made with ❤️ for Arabic content creators

صُنع بـ ❤️ لصنّاع المحتوى العربي

⭐ **Star this repo if it helped you!** | **أعطِ نجمة إن أفادك!** ⭐

</div>
