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


def mux(video, audio, out):
    tmp = out + ".part.mp4"
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", video, "-i", audio, "-map", "0:v", "-map", "1:a",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", tmp])
    os.replace(tmp, out)
