"""يولّد ملفات SFX صغيرة (whoosh/pop/tick) بـ wave بلا مكتبات خارجية."""
import math
import os
import struct
import wave

SR = 44100


def _write(path, samples):
    with wave.open(path, 'w') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        data = struct.pack(f'<{len(samples)}h', *[max(-32767, min(32767, int(s))) for s in samples])
        w.writeframes(data)


def _whoosh(dur=0.18, amp=0.45):
    n = int(SR * dur)
    return [amp * 32767 * (1 - t / n) * math.sin(2 * math.pi * (600 + 2600 * t / n) * t / SR)
            for t in range(n)]


def _pop(dur=0.06, amp=0.6):
    n = int(SR * dur)
    return [amp * 32767 * math.exp(-t / (SR * 0.012)) * math.sin(2 * math.pi * 240 * t / SR)
            for t in range(n)]


def _tick(dur=0.035, amp=0.38):
    n = int(SR * dur)
    return [amp * 32767 * math.exp(-t / (SR * 0.007)) * math.sin(2 * math.pi * 1200 * t / SR)
            for t in range(n)]


def ensure_sfx(pub_dir):
    """يتأكد من وجود sfx/*.wav في pub_dir؛ يولّدها إذا لم تكن موجودة. آمن للاستدعاء المتكرر."""
    sfx_dir = os.path.join(pub_dir, 'sfx')
    os.makedirs(sfx_dir, exist_ok=True)
    for name, fn in [('whoosh', _whoosh), ('pop', _pop), ('tick', _tick)]:
        p = os.path.join(sfx_dir, f'{name}.wav')
        if not os.path.exists(p):
            _write(p, fn())
    return sfx_dir
