"""Split from `pipeline/render.py` (re-exported there); see that module."""
from .style import FONTS
from .config import FPS, H, W
from PIL import Image, ImageDraw
import math
import numpy as np
import os
import subprocess
from .render import Background, MapLayer, _dtext, _tlen, ease, load_font, on, parse_num, paste_rgba, wrap_lines  # noqa: E402


# ---------------------------------------------------------------- المشهد
class SceneRenderer:
    def __init__(self, geo, sc, dur, words, style, fast=False, settled=False, t0=0.0, total=None):
        self.st = style
        self.pal = style["palette"]
        self.sc, self.dur, self.words = sc, dur, words
        self.t0, self.total = t0, total or dur
        self.k = (0.35 if fast else 1.0) / style["pace"]
        self.settled = settled
        self.vis = sc.get("visual") or {}
        self.type = self.vis.get("type", "text")
        self.dark = style["dark"]
        pos = style["headline"]["pos"]
        self.cy = {"top": 870, "center": 870, "upper": 920, "lower": 650}[pos]
        self.head_y = {"top": 250, "center": 250, "upper": 340, "lower": 1130}[pos]
        self.cap_y = max(style["caption"]["y"], 1380) if pos == "lower" else style["caption"]["y"]
        self.bg = Background(style)
        if self.type == "map":
            self.map = MapLayer(geo, self.vis, style, self.cy)
        self.head = []
        hs = style["headline"]["size"]
        self.head_size = hs
        if sc.get("on_screen") and self.type != "text":
            for size in (hs, int(hs * 0.86), int(hs * 0.72)):
                lines = wrap_lines(sc["on_screen"], self.F(size), 900)
                if len(lines) <= 2:
                    break
            self.head_size, self.head = size, lines
        self.cap_size = style["caption"]["size"]
        self.chunks = self._chunks(words, self.F(self.cap_size), 880, 5 if self.cap_size < 70 else 4, int(self.cap_size * 0.36))

    def F(self, size, dw=0):
        lo, hi = FONTS[self.st["font"]][2]
        return load_font(self.st["font"], int(size), max(lo, min(hi, self.st["weight"] + dw)))

    def ent(self, t, t0, d):
        if self.settled:
            return 1.0
        return ease((t - t0 * self.k) / (d * self.k))

    @staticmethod
    def _chunks(words, font, maxw, maxn, gap):
        out, cur, w = [], [], 0
        for it in words:
            wd = _tlen(font, it[0]) * 1.12
            if cur and (w + wd + gap > maxw or len(cur) >= maxn):
                out.append(cur)
                cur, w = [], 0
            cur.append(it)
            w += wd + gap
        if cur:
            out.append(cur)
        return out

    def shadow(self):
        return (0, 0, 0, 140) if self.dark else (255, 255, 255, 90)

    # ---- العنوان
    def draw_headline(self, ov, t):
        h = self.st["headline"]
        pal = self.pal
        font = self.F(self.head_size)
        right = h["pos"] == "center"
        for i, line in enumerate(self.head):
            p = ease((t - 0.05 - 0.2 * i * self.k) / (0.5 * self.k)) if not self.settled else 1.0
            if p <= 0.01:
                continue
            LH = 240
            layer = Image.new("RGBA", (W, LH), (0, 0, 0, 0))
            d = ImageDraw.Draw(layer)
            w = _tlen(font, line)
            cx, anc = (540, "mm") if not right else (1000, "rm")
            x0, x1 = (cx - w / 2, cx + w / 2) if not right else (cx - w, cx)
            cyl = LH // 2
            box, tc = h["box"], pal["text"]
            if box == "pill":
                d.rounded_rectangle([x0 - 44, cyl - 66, x1 + 44, cyl + 66], radius=66, fill=pal["accent"] + (255,))
                tc = on(pal["accent"])
            elif box == "tag":
                d.rounded_rectangle([x0 - 36, cyl - 62, x1 + 36, cyl + 62], radius=10, fill=pal["accent2"] + (255,))
                tc = on(pal["accent2"])
            elif box == "bar":
                d.rectangle([x1 + 26, cyl - 52, x1 + 40, cyl + 52], fill=pal["accent"] + (255,))
            elif box == "underline":
                d.rectangle([x0, cyl + 62, x1, cyl + 72], fill=pal["accent"] + (255,))
            if box in ("none", "bar", "underline"):
                _dtext(d, (cx, cyl + 4), line, font=font, fill=self.shadow(), anchor=anc)
            _dtext(d, (cx, cyl), line, font=font, fill=tc + (255,), anchor=anc)
            enter, dx, dy = h["enter"], 0, 0
            if enter == "rise":
                dy = (1 - p) * 50
            elif enter == "drop":
                dy = -(1 - p) * 50
            elif enter == "slide":
                dx = (1 - p) * 260
            elif enter == "wipe":
                layer = layer.crop((0, 0, W, LH))
                m = Image.new("L", (W, LH), 0)
                ImageDraw.Draw(m).rectangle([W * (1 - p), 0, W, LH], fill=255)
                layer.putalpha(Image.composite(layer.getchannel("A"), Image.new("L", (W, LH), 0), m))
            elif enter == "pop":
                s = 0.6 + 0.4 * (p + 0.18 * math.sin(p * math.pi))
                layer = layer.resize((max(int(W * s), 1), max(int(LH * s), 1)), Image.BILINEAR)
            if enter in ("rise", "drop", "fade", "slide", "pop"):
                a = layer.getchannel("A").point(lambda v, p=p: int(v * p))
                layer.putalpha(a)
            lw, lh = layer.size
            paste_rgba(ov, layer, (W - lw) / 2 + dx, self.head_y + i * 110 - lh / 2 + dy)

    # ---- الترجمة
    def draw_caption(self, ov, t):
        cur = None
        for ch in self.chunks:
            if ch[0][1] <= t + 0.02:
                cur = ch
        if not cur:
            return
        c = self.st["caption"]
        pal = self.pal
        mode = c["mode"]
        hl = "box" if mode == "box_word" else ("underline" if mode == "underline" else c["hl"])
        if mode == "stroke" and hl == "box":
            hl = "color"
        size = self.cap_size
        gap = int(size * 0.36)
        act = max(i for i, w in enumerate(cur) if w[1] <= t + 0.02)
        fonts = [self.F(size * 1.14 if (hl == "scale" and i == act) else size) for i in range(len(cur))]
        ws = [_tlen(f, w[0]) for f, w in zip(fonts, cur)]
        total = sum(ws) + gap * (len(ws) - 1)
        y = self.cap_y
        d = ImageDraw.Draw(ov)
        hh = int(size * 1.0)
        if mode == "pill":
            d.rounded_rectangle([540 - total / 2 - 38, y - hh, 540 + total / 2 + 38, y + hh], radius=hh // 2 + 8, fill=pal["c1"] + (210,))
        elif mode == "bar":
            d.rectangle([0, y - hh - 6, W, y + hh + 6], fill=pal["c1"] + (222,))
            d.rectangle([0, y - hh - 6, W, y - hh], fill=pal["accent"] + (255,))
        x = 540 + total / 2
        for i, (w, f, wd) in enumerate(zip(cur, fonts, ws)):
            active = i == act
            col = pal["text"]
            if active:
                if hl == "box":
                    d.rounded_rectangle([x - wd - 16, y - hh * 0.8, x + 16, y + hh * 0.8], radius=18, fill=pal["accent"] + (255,))
                    col = on(pal["accent"])
                elif hl == "underline":
                    d.rectangle([x - wd, y + hh * 0.62, x, y + hh * 0.62 + 8], fill=pal["accent"] + (255,))
                    col = pal["accent"] if hl != "underline" or mode != "underline" else pal["text"]
                else:
                    col = pal["accent"]
            if mode == "stroke":
                _dtext(d, (x, y), w[0], font=f, fill=col + (255,), anchor="rm", stroke_width=max(size // 9, 4),
                       stroke_fill=pal["c2"] + (255,))
            else:
                if mode in ("plain", "underline", "box_word") and not (active and hl == "box"):
                    _dtext(d, (x, y + 4), w[0], font=f, fill=self.shadow(), anchor="rm")
                _dtext(d, (x, y), w[0], font=f, fill=col + (255,), anchor="rm")
            x -= wd + gap

    # ---- أرقام
    def draw_stat(self, ov, t):
        v, pal = self.vis, self.pal
        lay = self.st["stat"]["layout"]
        s = str(v.get("number", ""))
        p = ease((t - 0.2 * self.k) / (min(1.6, self.dur * 0.55) * (1 if not self.settled else 0.01)))
        pn = parse_num(s)
        if pn:
            pre, val, dec, commas, suf = pn
            cur = val * p
            show = pre + (f"{cur:,.{dec}f}" if commas else f"{cur:.{dec}f}") + suf
        else:
            show = s
        a = ease(t / (0.4 * self.k)) if not self.settled else 1.0
        d = ImageDraw.Draw(ov)
        cy = self.cy - 60
        lab = str(v.get("label", ""))
        sh = self.shadow()

        def text(xy, s_, f, col, al, anchor="mm"):
            if al <= 0.01:
                return
            _dtext(d, (xy[0], xy[1] + 4), s_, font=f, fill=sh[:3] + (int(sh[3] * al),), anchor=anchor)
            _dtext(d, xy, s_, font=f, fill=tuple(col) + (int(255 * al),), anchor=anchor)

        lines = wrap_lines(lab, self.F(60, -120), 840)[:2]
        if lay == "ring":
            R = 280
            d.ellipse([540 - R, cy - 80 - R, 540 + R, cy - 80 + R], outline=pal["text"] + (int(45 * a),), width=14)
            d.arc([540 - R, cy - 80 - R, 540 + R, cy - 80 + R], -90, -90 + 360 * p, fill=pal["accent"] + (int(255 * a),), width=14)
            text((540, cy - 86), show, self.F(170), pal["accent"], a)
            ly = cy + 315
        elif lay == "bar":
            text((540, cy - 120), show, self.F(210), pal["accent"], a)
            d.rounded_rectangle([140, cy + 60, 940, cy + 92], radius=16, fill=pal["text"] + (int(45 * a),))
            d.rounded_rectangle([140, cy + 60, 140 + 800 * p, cy + 92], radius=16, fill=pal["accent"] + (int(255 * a),))
            ly = cy + 190
        elif lay == "stack":
            for i, line in enumerate(lines):
                text((540, cy - 330 + i * 76), line, self.F(60, -120), pal["accent2"], ease((t - 0.1 * self.k - 0.12 * i) / (0.5 * self.k)) if not self.settled else 1.0)
            text((540, cy - 90), show, self.F(250), pal["text"], a)
            d.rectangle([540 - 220 * p, cy + 70, 540 + 220 * p, cy + 82], fill=pal["accent"] + (255,))
            return
        else:  # plain
            text((540, cy - 50), show, self.F(240), pal["accent"], a)
            d.rectangle([540 - 300 * p, cy + 110, 540 + 300 * p, cy + 122], fill=pal["accent2"] + (255,))
            ly = cy + 215
        for i, line in enumerate(lines):
            k = ease((t - 0.5 * self.k - 0.15 * i) / (0.5 * self.k)) if not self.settled else 1.0
            text((540, ly + i * 80 + int(24 * (1 - k))), line, self.F(60, -120), pal["text"], k)

    # ---- نص كبير
    def _text_block(self, target, t, words, size, layout):
        pal = self.pal
        d = ImageDraw.Draw(target)
        sh = self.shadow()
        n = len(words)
        text = " ".join(words)
        f = self.F(size)
        if layout == "stack":
            lines = [[w] for w in words][:6]
            size = min(size, int(1500 / max(len(lines), 1) / 1.25))
            f = self.F(size)
        else:
            for sz in (size, int(size * 0.82), int(size * 0.68)):
                f = self.F(sz)
                lines = [l.split() for l in wrap_lines(text, f, 880)]
                if len(lines) <= 3:
                    size = sz
                    break
        lh = int(size * 1.28)
        y0 = self.cy - lh * len(lines) / 2 + lh / 2
        idx = 0
        gap = int(size * 0.28)
        for li, lw in enumerate(lines):
            ws = [_tlen(f, w) for w in lw]
            tot = sum(ws) + gap * (len(ws) - 1)
            xr = 540 + tot / 2 if layout in ("center", "stack", "diag") else 960
            for w, wd in zip(lw, ws):
                k = ease((t - (0.12 + 0.26 * idx) * self.k) / (0.35 * self.k)) if not self.settled else 1.0
                if layout == "stack":
                    col = pal["accent"] if idx % 2 == 0 else pal["text"]
                else:
                    col = pal["accent"] if idx == n - 1 else pal["text"]
                if k > 0.01:
                    x = xr - (tot / 2 - wd / 2 + 0) * 0 if layout == "stack" else xr
                    if layout == "stack":
                        x = 540 + wd / 2
                    y = y0 + li * lh + int(34 * (1 - k))
                    _dtext(d, (x, y + 5), w, font=f, fill=sh[:3] + (int(sh[3] * k),), anchor="rm")
                    _dtext(d, (x, y), w, font=f, fill=col + (int(255 * k),), anchor="rm")
                xr -= wd + gap
                idx += 1
        if layout == "left":
            top, bot = y0 - lh / 2, y0 + lh * (len(lines) - 0.5)
            d.rectangle([990, top, 1002, top + (bot - top) * ease(t / (0.6 * self.k) if not self.settled else 1)], fill=pal["accent"] + (255,))

    def draw_text(self, ov, t):
        text = str(self.vis.get("text") or self.sc.get("on_screen") or "")
        words = text.split()
        if not words:
            return
        layout = self.st["text"]["layout"]
        size = self.st["text"]["size"]
        if layout == "diag":
            tmp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            self._text_block(tmp, t, words, size, "diag")
            tmp = tmp.rotate(-7, resample=Image.BICUBIC, center=(540, self.cy))
            ov.alpha_composite(tmp)
        else:
            self._text_block(ov, t, words, size, layout)

    # ---- زخارف
    def draw_deco(self, ov, t):
        dc, pal = self.st["deco"], self.pal
        d = ImageDraw.Draw(ov)
        col = pal["accent"] + (230,)
        fr = dc["frame"]
        if fr == "corners":
            for sx in (50, W - 50):
                for sy in (50, H - 50):
                    dx = 90 if sx < 540 else -90
                    dy = 90 if sy < 540 else -90
                    d.line([(sx, sy + dy), (sx, sy), (sx + dx, sy)], fill=col, width=7)
        elif fr == "border":
            d.rectangle([28, 28, W - 28, H - 28], outline=pal["accent"] + (150,), width=4)
        elif fr == "ticks":
            for yy in range(120, H - 100, 60):
                ln = 34 if (yy // 60) % 4 == 0 else 18
                d.line([(30, yy), (30 + ln, yy)], fill=pal["text"] + (110,), width=3)
                d.line([(W - 30, yy), (W - 30 - ln, yy)], fill=pal["text"] + (110,), width=3)
        pr = dc["progress"]
        f = min(max((self.t0 + t) / self.total, 0), 1)
        if pr == "top":
            d.rectangle([0, 0, W * f, 12], fill=pal["accent"] + (255,))
        elif pr == "bottom":
            d.rectangle([0, H - 12, W * f, H], fill=pal["accent"] + (255,))
        elif pr == "side":
            d.rectangle([W - 12, 0, W, H * f], fill=pal["accent"] + (255,))

    def frame(self, t):
        bgf = self.bg.frame(t)
        if self.type == "map":
            out = self.map.base(t, self.ent, bgf, self.bg.static is not None)
        else:
            out = bgf
        img = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        if self.type == "map":
            self.map.overlay(ov, t, self.ent, self.F(46, -100))
        elif self.type == "stat":
            self.draw_stat(ov, t)
        else:
            self.draw_text(ov, t)
        self.draw_headline(ov, t)
        self.draw_deco(ov, t)
        self.draw_caption(ov, t)
        return Image.alpha_composite(img, ov).convert("RGB")


def render_scene(geo, sc, dur, words, out_path, style, fast=False, settled=False, t0=0.0, total=None, progress=None):
    n = max(int(round(dur * FPS)), 1)
    r = SceneRenderer(geo, sc, dur, words, style, fast=fast, settled=settled, t0=t0, total=total)
    tmp = out_path.replace(".mp4", ".part.mp4")
    p = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
         "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", tmp],
        stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        for i in range(n):
            p.stdin.write(np.asarray(r.frame(i / FPS)).tobytes())
            if progress and i % 30 == 0:
                progress(i / n)
        p.stdin.close()
        err = p.stderr.read().decode("utf-8", "ignore")
        rc = p.wait()
    except BrokenPipeError:
        err = p.stderr.read().decode("utf-8", "ignore")
        rc = p.wait()
    if rc != 0:
        raise RuntimeError("فشل ترميز المشهد: " + err[-500:])
    os.replace(tmp, out_path)
    return n / FPS


def preview_frame(geo, sc, dur, words, style, t, t0=0.0, total=None, fast=False, settled=False):
    return SceneRenderer(geo, sc, dur, words, style, fast=fast, settled=settled, t0=t0, total=total).frame(t)
