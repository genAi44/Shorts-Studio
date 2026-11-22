"""يولّد مكتبة SFX محلية (whoosh/pop/tick/impact/riser/ding + ambient bed) بلا ملفات خارجية.

تُكتب الملفات في `<pub>/sfx/*.wav` وتُستخدم من Remotion عبر staticFile (بدون اعتماد على الشبكة).
"""
import os
import wave

import numpy as np

SR = 44100
SFX_VERSION = "4"
_RNG = np.random.default_rng(7)


def _write(path, samples, channels=1):
    x = np.asarray(samples, dtype=np.float64)
    peak = float(np.max(np.abs(x))) if x.size else 0.0
    if peak > 0.98:
        x = x * (0.98 / peak)
    pcm = (np.clip(x, -1.0, 1.0) * 32767).astype("<i2")
    with wave.open(path, "w") as w:
        w.setnchannels(channels)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def _t(dur):
    return np.arange(int(SR * dur)) / SR


def _fade(x, fin=0.004, fout=0.02):
    n_in, n_out = int(SR * fin), int(SR * fout)
    if n_in:
        x[:n_in] *= np.linspace(0, 1, n_in)
    if n_out:
        x[-n_out:] *= np.linspace(1, 0, n_out)
    return x


def _lowpass(x, alpha):
    """مرشح تمرير منخفض أحادي القطب بمعامل متغيّر عبر الزمن (alpha مصفوفة أو رقم)."""
    a = np.broadcast_to(np.asarray(alpha, dtype=np.float64), x.shape)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(x.size):
        acc += a[i] * (x[i] - acc)
        y[i] = acc
    return y


def _whoosh(dur=0.42, amp=0.55):
    """ضجيج مُرشّح بمرشح يتحرك صعوداً ثم هبوطاً — إحساس هواء/حركة كاميرا."""
    t = _t(dur)
    noise = _RNG.standard_normal(t.size)
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 1.6
    sweep = 0.03 + 0.32 * np.sin(np.pi * t / dur) ** 2
    band = _lowpass(noise, sweep) - _lowpass(noise, sweep * 0.18)
    return _fade(band * env * amp * 3.2)


def _pop(dur=0.11, amp=0.6):
    """نقرة ناعمة لظهور البطاقات: نغمة تهبط بسرعة + نقرة قصيرة."""
    t = _t(dur)
    f = 520 * np.exp(-t * 28) + 180
    phase = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(phase) * np.exp(-t / 0.035)
    click = _RNG.standard_normal(t.size) * np.exp(-t / 0.002) * 0.25
    return _fade((body + click) * amp, fin=0.001)


def _tick(dur=0.05, amp=0.4):
    """تكة قصيرة للعدّادات والدبابيس."""
    t = _t(dur)
    s = np.sin(2 * np.pi * 1850 * t) * np.exp(-t / 0.006)
    s += 0.4 * np.sin(2 * np.pi * 3700 * t) * np.exp(-t / 0.003)
    return _fade(s * amp, fin=0.0005, fout=0.01)


def _impact(dur=0.9, amp=0.8):
    """ضربة سينمائية منخفضة (sub boom) لبداية الـ hook والكشف الكبير."""
    t = _t(dur)
    f = 95 * np.exp(-t * 4.5) + 38
    phase = 2 * np.pi * np.cumsum(f) / SR
    boom = np.sin(phase) * np.exp(-t / 0.32)
    hit = _lowpass(_RNG.standard_normal(t.size), 0.08) * np.exp(-t / 0.04) * 1.6
    return _fade((boom + hit) * amp, fin=0.001, fout=0.15)


def _riser(dur=0.9, amp=0.45):
    """صعود قصير قبل الكشف (open loops)."""
    t = _t(dur)
    prog = t / dur
    f = 220 + 900 * prog ** 2
    phase = 2 * np.pi * np.cumsum(f) / SR
    tone = np.sin(phase) * 0.35 + np.sin(phase * 1.5) * 0.15
    noise = _lowpass(_RNG.standard_normal(t.size), 0.02 + 0.25 * prog) * 0.9
    env = prog ** 2.2
    return _fade((tone + noise) * env * amp, fin=0.01, fout=0.03)


def _ding(dur=0.9, amp=0.35):
    """جرس ناعم للـ CTA."""
    t = _t(dur)
    s = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t / d)
            for f, a, d in ((1318.5, 1.0, 0.35), (1975.5, 0.45, 0.22), (2637.0, 0.25, 0.12)))
    return _fade(s * amp, fin=0.001, fout=0.08)


def _ambient_bed(dur=16.0, amp=0.34):
    """موسيقى وثائقية هادئة وإيقاعية قابلة للتكرار السلس (120 BPM، 4 كوردات، نبض ناعم، بلا تداخل مع ترددات الصوت)."""
    t = _t(dur)
    out = np.zeros(t.size)

    def f_loop(f):
        return max(1.0 / dur, round(f * dur) / dur)

    # 4-bar chord progression (4s each at 120 BPM = 16s): Am9 -> Fmaj7 -> Cmaj9 -> G6
    chords = [
        (110.0, 220.0, 261.63, 329.63, 392.00),  # Am7
        (87.31, 174.61, 220.00, 261.63, 329.63), # Fmaj7
        (130.81, 196.00, 246.94, 293.66, 329.63),# Cmaj9
        (98.00, 196.00, 246.94, 293.66, 329.63), # G6
    ]
    bar_len = dur / 4.0
    pad = np.zeros(t.size)
    pluck = np.zeros(t.size)

    for idx, freqs in enumerate(chords):
        t0 = idx * bar_len
        t1 = (idx + 1) * bar_len
        # Smooth crossfade window per bar
        in_bar = np.clip((t - t0) / 0.35, 0, 1) * np.clip((t1 - t) / 0.35, 0, 1)
        if idx == 0:
            in_bar += np.clip((t - (dur - 0.35)) / 0.35, 0, 1) * 0.0
        for fi, f in enumerate(freqs):
            ff = f_loop(f)
            w = 0.45 if fi == 0 else (0.28 if fi == 1 else 0.14)
            # Warm harmonic pad (fundamental + soft 2nd harmonic)
            pad += in_bar * w * (np.sin(2 * np.pi * ff * t) + 0.18 * np.sin(4 * np.pi * ff * t))

    # Soft rhythmic sub-pulse at 120 BPM (every 0.5s) + gentle off-beat marimba pluck
    beat_dur = 0.5
    n_beats = int(round(dur / beat_dur))
    for b in range(n_beats):
        bt = b * beat_dur
        dt = (t - bt) % dur
        # Soft muted pulse on every beat (stronger on downbeats)
        pulse_amp = 0.32 if (b % 4 == 0) else 0.18
        pulse_env = np.exp(-dt / 0.09) * (dt < 0.35)
        chord_idx = (b // 8) % 4
        bass_f = f_loop(chords[chord_idx][0] * 0.5)
        out += pulse_amp * pulse_env * np.sin(2 * np.pi * bass_f * t)

        # Gentle melodic arpeggio pluck on every beat
        arp_freqs = chords[chord_idx][2:]
        arp_f = f_loop(arp_freqs[b % len(arp_freqs)] * 2.0)
        arp_env = np.exp(-dt / 0.16) * (dt < 0.45)
        pluck += 0.12 * arp_env * np.sin(2 * np.pi * arp_f * t)

    # Gentle warm air texture (lowpassed so it stays smooth under narration)
    air = _lowpass(_RNG.standard_normal(t.size), 0.015)
    n_xf = int(SR * 1.0)
    air[-n_xf:] = air[-n_xf:] * np.linspace(1, 0, n_xf) + air[:n_xf] * np.linspace(0, 1, n_xf)

    mix = _lowpass(pad * 0.55 + pluck * 0.75 + out + air * 0.35, 0.22)
    return mix / max(1e-9, np.max(np.abs(mix))) * amp


SFX_BUILDERS = {
    "whoosh": _whoosh,
    "pop": _pop,
    "tick": _tick,
    "impact": _impact,
    "riser": _riser,
    "ding": _ding,
    # sfx.tsx emits 'swipe' and 'chime'; without these files the whole render died on a 404
    "swipe": lambda: _whoosh(dur=0.22, amp=0.4),
    "chime": lambda: _ding(dur=0.6, amp=0.3),
    "ambient": _ambient_bed,
}


def ensure_sfx(pub_dir):
    """يتأكد من وجود sfx/*.wav في pub_dir بالإصدار الحالي؛ يولّدها عند الحاجة. آمن للاستدعاء المتكرر."""
    sfx_dir = os.path.join(pub_dir, "sfx")
    os.makedirs(sfx_dir, exist_ok=True)
    ver_file = os.path.join(sfx_dir, ".version")
    current = ""
    if os.path.exists(ver_file):
        try:
            current = open(ver_file, encoding="utf-8").read().strip()
        except OSError:
            current = ""
    stale = current != SFX_VERSION
    for name, fn in SFX_BUILDERS.items():
        p = os.path.join(sfx_dir, f"{name}.wav")
        if stale or not os.path.exists(p):
            _write(p, fn())
    if stale:
        with open(ver_file, "w", encoding="utf-8") as f:
            f.write(SFX_VERSION)
    return sfx_dir
