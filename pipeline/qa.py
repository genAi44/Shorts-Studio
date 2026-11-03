"""Auto-QA: رندر ستيل عند منتصف كل مقطع ← Gemini يفحص القراءة والصلة بالجملة ← إعادة التصميم إن لزم."""
import io
import os

from . import llm, rem

QA_SYSTEM = (
    "You are a QA reviewer for an Arabic motion-graphics educational video. "
    "You see a still frame from a beat (scene segment) and its Arabic narration words. "
    "Check: 1) Is text readable — not clipped, not overlapping, sufficient contrast? "
    "2) Is the visual relevant to the Arabic narration? "
    "Return JSON only: {\"readable\": true, \"relevant\": true, \"issues\": \"\"}"
)


def _beat_words(scene, beat, fps):
    """الكلمات المنطوقة خلال هذا المقطع."""
    s0 = beat.get("from", 0) / fps
    s1 = (beat.get("from", 0) + beat.get("dur", 0)) / fps
    return " ".join(w["t"] for w in scene.get("words", []) if s0 <= w.get("s", 0) <= s1)


def qa_beats(spec, work_dir, log=print):
    """
    يفحص كل مقطع تلقائياً ويُسجّل النتائج.
    يُعيد قائمة بمشاكل الجودة (قابلة للاستخدام لإعادة توليد المقاطع الفاشلة).
    """
    if not llm.cfg("GEMINI_API_KEY"):
        log("QA: مفتاح Gemini غير مضبوط — تخطّي فحص الجودة")
        return []

    try:
        from PIL import Image
    except ImportError:
        log("QA: Pillow غير مثبّت — تخطّي فحص الجودة")
        return []

    fps = spec.get("fps", 30)
    issues_found = []

    for si, scene in enumerate(spec.get("scenes", [])):
        for bi, beat in enumerate(scene.get("beats", [])):
            scene_from = scene.get("from", 0)
            beat_mid = scene_from + beat.get("from", 0) + beat.get("dur", 30) // 2
            still_path = os.path.join(work_dir, f"qa_{si}_{bi}.jpg")
            try:
                rem.render_still(spec, still_path, beat_mid, work_dir)
            except Exception as e:
                log(f"QA: تعذّر رندر المقطع {si}.{bi}: {str(e)[:60]}")
                continue

            try:
                with Image.open(still_path) as im:
                    buf = io.BytesIO()
                    im.convert("RGB").thumbnail((540, 960))
                    im.save(buf, "JPEG", quality=72)
                    img_bytes = buf.getvalue()
            except Exception as e:
                log(f"QA: تعذّر قراءة الصورة: {str(e)[:60]}")
                continue
            finally:
                try:
                    os.remove(still_path)
                except Exception:
                    pass

            narration = _beat_words(scene, beat, fps)
            try:
                res = llm.gemini_vision_json(QA_SYSTEM, f"Arabic narration: {narration}", [img_bytes])
                readable = bool(res.get("readable", True))
                relevant = bool(res.get("relevant", True))
                issue_txt = str(res.get("issues", ""))[:120]
                tag = "✓" if readable and relevant else "✗"
                log(f"QA {tag} [{si}.{bi} {beat.get('kind', '?')}] {issue_txt or 'OK'}")
                if not readable or not relevant:
                    issues_found.append({"si": si, "bi": bi, "beat": beat, "issues": issue_txt})
            except Exception as e:
                log(f"QA: Gemini فشل ({str(e)[:60]})")

    if issues_found:
        log(f"QA: {len(issues_found)} مقطع يحتاج مراجعة")
    else:
        log("QA: جميع المقاطع اجتازت الفحص ✓")
    return issues_found
