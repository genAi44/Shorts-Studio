"""تجميع المشاهد: ضم الفيديو بلا إعادة ترميز، وضم الصوت، ثم دمجهما."""
import os
import subprocess


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("ffmpeg فشل: " + (r.stderr or "")[-600:])


def to_wav(src, dst, dur):
    """صوت أحادي 44.1k بطول مطابق تماماً لطول المشهد (صمت في النهاية عند الحاجة)."""
    tmp = dst + ".part.wav"
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-ar", "44100", "-ac", "1",
         "-af", "apad", "-t", f"{dur:.4f}", "-c:a", "pcm_s16le", tmp])
    os.replace(tmp, dst)


def concat(paths, out):
    lst = out + ".txt"
    with open(lst, "w", encoding="utf-8") as f:
        for p in paths:
            f.write("file '" + os.path.abspath(p).replace("'", "'\\''") + "'\n")
    tmp = out + ".part" + os.path.splitext(out)[1]
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", tmp])
    os.replace(tmp, out)


def loudnorm(path, target_lufs=-14.0, true_peak=-1.5):
    """تطبيع جهارة التعليق الصوتي لمعيار المنصّات القصيرة (≈ -14 LUFS) مع حدّ أقصى للذروة.

    يحافظ على نفس المدة وعدد العينات (44.1k أحادي) حتى لا يختل تزامن الكابشن.
    """
    tmp = path + ".norm.wav"
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", path,
         "-af", f"highpass=f=70,loudnorm=I={target_lufs}:TP={true_peak}:LRA=11",
         "-ar", "44100", "-ac", "1", "-c:a", "pcm_s16le", tmp])
    os.replace(tmp, path)


def mux(video, audio, out, quality="standard"):
    """
    دمج الفيديو مع الصوت مع تحسين جودة الترميز.
    
    مستويات الجودة:
    - 'draft': CRF 28، veryfast - للمعاينة السريعة
    - 'standard': CRF 23، veryfast - الجودة الافتراضية المتوازنة  
    - 'high': CRF 20، medium - جودة أعلى
    - 'cinematic': CRF 18، slow - أفضل جودة سينمائية
    """
    quality_settings = {
        "draft": {"crf": 28, "preset": "veryfast"},
        "standard": {"crf": 23, "preset": "veryfast"},
        "high": {"crf": 20, "preset": "medium"},
        "cinematic": {"crf": 18, "preset": "slow"},
    }
    settings = quality_settings.get(quality, quality_settings["standard"])
    
    tmp = out + ".part.mp4"
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", video, "-i", audio, "-map", "0:v", "-map", "1:a",
         "-c:v", "libx264", "-crf", str(settings["crf"]), "-preset", settings["preset"],
         "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart",
         "-pix_fmt", "yuv420p", tmp])
    os.replace(tmp, out)
