# Contributing to Shorts Studio | المساهمة في Shorts Studio

**[English](#english-guide) · [العربية](#arabic-guide)**

---

<a id="english-guide"></a>

## 🇬🇧 English Contribution Guide

### Welcome!

Shorts Studio is built by and for Arabic content creators. **You don't need to write code to contribute.** Some of the most valuable contributions come from people who understand Arabic content, culture, and what makes videos go viral.

---

### Ways to contribute without coding

#### 1. 📝 Suggest topic ideas
Open a [Content Idea issue](https://github.com/genAi44/shorts-studio/issues/new?template=content-idea.md) with a topic suggestion. Great topics:
- Have a surprising fact or counterintuitive twist
- Are 40–55 seconds of material (not too broad, not too narrow)
- Resonate with Arabic-speaking audiences

#### 2. 🌐 Improve Arabic prompts
The AI prompts that guide script generation live in `pipeline/prompts/`. If a generated script sounds unnatural, too formal, or uses the wrong dialect:
1. Fork the repo
2. Edit the relevant `.txt` or `.md` file in `pipeline/prompts/`
3. Open a Pull Request describing the improvement

You don't need to understand Python — the prompt files are plain text.

#### 3. 🧪 Test and report
Run the pipeline on different topics and report what breaks:
- Wrong Arabic grammar or unnatural phrasing → open a [Bug Report](https://github.com/genAi44/shorts-studio/issues/new?template=bug_report.md)
- Factual errors in generated scripts → open a Bug Report with the topic and wrong fact
- Visual scene doesn't match the narration → open a Bug Report

#### 4. 🎨 Design contributions
- Improve the web UI (HTML/CSS in `static/`)
- Create better SVG character assets (see `assets/characters/`)
- Design a demo GIF showing the pipeline in action

#### 5. 📚 Documentation
- Translate the README into other languages
- Write tutorials or blog posts about using Shorts Studio
- Record a demo video

---

### Ways to contribute with code

#### Getting started

```bash
git clone https://github.com/genAi44/shorts-studio.git
cd shorts-studio
pip install -r requirements.txt
cd remotion && npm install && cd ..
cp .env.example .env
# Add your API keys to .env
```

#### Before submitting a PR

- [ ] Test your change end-to-end (run the full pipeline on at least one topic)
- [ ] Don't break the 8-part script structure validation
- [ ] Keep Arabic RTL rendering working
- [ ] One PR per feature/fix — keep it focused

#### Code style
- Python: follow existing style (no formatter enforced yet — just be consistent)
- TypeScript/React: follow the existing Remotion component patterns
- Commit messages: English, present tense ("Add map scene type", not "Added...")

---

### Good first issues

Look for issues labeled [`good first issue`](https://github.com/genAi44/shorts-studio/labels/good%20first%20issue) — these are small, well-defined tasks suitable for first-time contributors.

---

### Code of Conduct

Be respectful. This project serves Arabic content creators worldwide. Contributions in Arabic are as welcome as contributions in English.

---

<a id="arabic-guide"></a>

## 🇸🇦 دليل المساهمة بالعربية

### مرحباً!

Shorts Studio مبني من وإلى صنّاع المحتوى العربي. **لا تحتاج إلى كتابة أكواد للمساهمة.** بعض أكثر المساهمات قيمةً تأتي من أشخاص يفهمون المحتوى العربي والثقافة وما يجعل الفيديوهات تنتشر.

---

### طرق المساهمة بدون برمجة

#### 1. 📝 اقترح أفكار مواضيع
افتح [مشكلة فكرة محتوى](https://github.com/genAi44/shorts-studio/issues/new?template=content-idea.md) باقتراح موضوع. الموضوعات الرائعة:
- تحتوي على حقيقة مفاجئة أو مفارقة غير متوقعة
- تكفي لـ 40-55 ثانية من المحتوى (ليست واسعة جداً ولا ضيقة جداً)
- تلقى صدى لدى الجمهور الناطق بالعربية

#### 2. 🌐 حسّن البرومبتات العربية
البرومبتات التي توجّه توليد السكربت موجودة في `pipeline/prompts/`. إذا بدا السكربت المُولَّد غير طبيعي، رسمياً جداً، أو يستخدم لهجة خاطئة:
1. انشئ نسخة fork من المستودع
2. حرّر الملف `.txt` أو `.md` المناسب في `pipeline/prompts/`
3. افتح Pull Request يصف التحسين

لا تحتاج إلى فهم Python — ملفات البرومبت نصوص عادية.

#### 3. 🧪 اختبر وأبلّغ
شغّل الخط الإنتاجي على مواضيع مختلفة وأبلّغ عما ينكسر:
- قواعد عربية خاطئة أو صياغة غير طبيعية ← افتح [تقرير خطأ](https://github.com/genAi44/shorts-studio/issues/new?template=bug_report.md)
- أخطاء حقائق في السكربتات المُولَّدة ← افتح تقرير خطأ مع الموضوع والحقيقة الخاطئة
- المشهد البصري لا يتطابق مع السرد ← افتح تقرير خطأ

#### 4. 🎨 مساهمات التصميم
- حسّن واجهة الويب (HTML/CSS في `static/`)
- أنشئ أصول شخصيات SVG أفضل (انظر `assets/characters/`)
- صمّم GIF تجريبياً يُظهر الخط الإنتاجي في العمل

#### 5. 📚 التوثيق
- ترجم README إلى لغات أخرى
- اكتب دروسًا أو مقالات حول استخدام Shorts Studio
- سجّل فيديو تجريبياً

---

### مدونة قواعد السلوك

كن محترماً. هذا المشروع يخدم صنّاع المحتوى العربي في جميع أنحاء العالم. المساهمات بالعربية مرحب بها تماماً كالمساهمات بالإنجليزية.
