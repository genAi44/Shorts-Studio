"""رسم المشاهد (PIL + numpy) مدفوعاً بالكامل بالستايل. كل مشهد ملف mp4 مستقل."""
import math
import os
import re
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .config import FONT, FPS, H, W
from .style import FONTS

DATA = FONT.parent
SC = 2  # supersampling للأقنعة

# ---------------------------------------------------------------- أدوات
_fonts = {}


def load_font(name, size, weight):
    k = (name, size, weight)
    if k in _fonts:
        return _fonts[k]
    file, var, _ = FONTS[name]
    f = ImageFont.truetype(str(DATA / file), size)
    if var:
        try:
            vals = []
            for a in f.get_variation_axes():
                nm = a["name"].decode() if isinstance(a["name"], bytes) else a["name"]
                vals.append(max(a["minimum"], min(a["maximum"], weight)) if "eight" in nm else a["default"])
            f.set_variation_by_axes(vals)
        except Exception:
            pass
    _fonts[k] = f
    return f


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def lum(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def on(c):
    """لون نص مقروء فوق الخلفية c."""
    return (22, 18, 14) if lum(c) > 150 else (255, 255, 255)


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def paste_rgba(ov, layer, x, y):
    lw, lh = layer.size
    x, y = int(x), int(y)
    sx, sy = max(0, -x), max(0, -y)
    ex, ey = min(lw, W - x), min(lh, H - y)
    if ex <= sx or ey <= sy:
        return
    ov.alpha_composite(layer.crop((sx, sy, ex, ey)), (x + sx, y + sy))


def wrap_lines(text, font, maxw):
    lines, cur = [], []
    for w in text.split():
        if cur and font.getlength(" ".join(cur + [w]), language="ar") > maxw:
            lines.append(" ".join(cur))
            cur = [w]
        else:
            cur.append(w)
    if cur:
        lines.append(" ".join(cur))
    return lines


def parse_num(s):
    m = re.search(r"\d[\d,\.]*", s)
    if not m:
        return None
    raw = m.group(0).rstrip(".,")
    clean = raw.replace(",", "")
    try:
        val = float(clean)
    except ValueError:
        return None
    dec = len(clean.split(".")[1]) if "." in clean else 0
    return s[:m.start()], val, dec, "," in raw, s[m.start() + len(raw):]


# ---------------------------------------------------------------- الخلفية
class Background:
    def __init__(self, st):
        p, b = st["palette"], st["bg"]
        self.c1, self.c2 = np.array(p["c1"], np.float32), np.array(p["c2"], np.float32)
        self.type, self.inten = b["type"], b["intensity"]
        self.motion = b["motion"] and b["type"] not in ("gradient", "paper")
        ang = math.radians(b["angle"])
        xs = np.arange(W, dtype=np.float32)[None, :]
        ys = np.arange(H, dtype=np.float32)[:, None]
        u = xs * math.cos(ang) + ys * math.sin(ang)
        u = (u - u.min()) / (u.max() - u.min() + 1e-6)
        self.base = (self.c1 + (self.c2 - self.c1) * u[:, :, None]).astype(np.float32)
        dark = lum(p["c1"]) < 128
        self.patcol = np.array(mix(p["text"], p["accent2"], 0.5) if dark else p["accent2"], np.float32)
        self.accent = np.array(p["accent"], np.float32)
        self.accent2 = np.array(p["accent2"], np.float32)
        t = self.type
        self.P = None
        if t in ("grid", "dots", "stripes", "waves"):
            PY, PX = {"grid": (96, 96), "dots": (72, 72), "stripes": (130, 130), "waves": (170, 720)}[t]
            yy, xx = np.mgrid[0:H + PY, 0:W + PX].astype(np.float32)
            if t == "grid":
                m = ((xx % 96 < 3) | (yy % 96 < 3)).astype(np.float32)
            elif t == "dots":
                m = (((xx % 72 - 36) ** 2 + (yy % 72 - 36) ** 2) < 20).astype(np.float32)
            elif t == "stripes":
                m = (((xx + yy) % 130) < 44).astype(np.float32)
            else:
                s = 0.5 + 0.5 * np.sin(2 * np.pi * (yy / 170 + xx / 720))
                m = np.clip((s - 0.82) * 8, 0, 1)
            self.P, self.PY, self.PX = m, PY, PX
        if t == "radial":
            xs2 = (np.arange(W, dtype=np.float32) - 540) / 540
            ys2 = (np.arange(H, dtype=np.float32) - 860) / 860
            self.glow = np.exp(-(xs2[None, :] ** 2 + ys2[:, None] ** 2) * 1.5)[:, :, None]
        if t == "rays":
            lh, lw = H // 4, W // 4
            yy, xx = np.mgrid[0:lh, 0:lw].astype(np.float32)
            self.ang = np.arctan2(yy - lh * 0.45, xx - lw / 2)
            r = np.sqrt((yy - lh * 0.45) ** 2 + (xx - lw / 2) ** 2)
            self.rfade = np.clip(1.15 - r / (lh * 0.9), 0.15, 1)
        if t == "paper":
            rng = np.random.RandomState(st.get("seed", 1) % 100000)
            n = rng.randn(H // 6, W // 6).astype(np.float32)
            n = np.asarray(Image.fromarray(((n * 20) + 128).clip(0, 255).astype(np.uint8)).resize((W, H), Image.BILINEAR), np.float32) - 128
            xs2 = (np.arange(W, dtype=np.float32) - 540) / 540
            ys2 = (np.arange(H, dtype=np.float32) - 960) / 960
            vig = 1 - 0.18 * np.clip(xs2[None, :] ** 2 + ys2[:, None] ** 2, 0, 1.6)
            self.base = (self.base * vig[:, :, None] + n[:, :, None] * 0.22).astype(np.float32)
        self.static = None if self.motion else self._make(0.0)

    def _make(self, t):
        ty, a = self.type, 0.13 * self.inten
        if ty in ("gradient", "paper"):
            return self.base
        if self.P is not None:
            ox = int(t * 26) % self.PX if self.motion else 0
            oy = int(t * 20) % self.PY if self.motion else 0
            m = self.P[oy:oy + H, ox:ox + W] * a
            return self.base + (self.patcol - self.base) * m[:, :, None]
        if ty == "radial":
            k = 0.22 * self.inten * (1 + (0.25 * math.sin(t * 1.3) if self.motion else 0))
            return self.base + self.glow * (self.accent2 * k)
        if ty == "rays":
            ph = t * 0.35 if self.motion else 0
            m = np.clip((np.sin(self.ang * 14 + ph) - 0.5) * 3, 0, 1) * self.rfade * (0.16 * self.inten)
            m = np.asarray(Image.fromarray((m * 255 / 0.2).clip(0, 255).astype(np.uint8)).resize((W, H), Image.BILINEAR), np.float32) / 255 * 0.2
            return self.base + (self.accent - self.base) * m[:, :, None]
        if ty == "aurora":
            lh, lw = H // 8, W // 8
            yy, xx = np.mgrid[0:lh, 0:lw].astype(np.float32)
            f = np.zeros((lh, lw, 3), np.float32)
            for i, col in enumerate((self.accent, self.accent2, self.patcol)):
                cx = lw * (0.5 + 0.38 * math.sin(t * 0.5 + i * 2.1)) if self.motion else lw * (0.2 + 0.3 * i)
                cy = lh * (0.5 + 0.35 * math.cos(t * 0.4 + i * 1.7)) if self.motion else lh * (0.3 + 0.2 * i)
                g = np.exp(-(((xx - cx) / (lw * 0.34)) ** 2 + ((yy - cy) / (lh * 0.2)) ** 2))
                f += g[:, :, None] * col
            f = np.clip(f * 0.5 * self.inten, 0, 255)
            big = np.asarray(Image.fromarray(f.astype(np.uint8)).resize((W, H), Image.BILINEAR), np.float32)
            return self.base * (1 - 0.35 * self.inten) + big * 0.65
        return self.base

    def frame(self, t):
        return self.static if self.static is not None else self._make(t)


# ---------------------------------------------------------------- الخريطة
class MapLayer:
    def __init__(self, geo, vis, st, cy):
        self.st, self.cy = st, cy
        pal = st["palette"]
        self.pal = pal
        self.hl = [str(c).upper() for c in (vis.get("highlight") or vis.get("countries") or [])]
        extra = [str(c).upper() for c in (vis.get("countries") or [])]
        self.pts = [p for p in (vis.get("points") or []) if "lat" in p and "lon" in p]
        v = geo.view_for(list(dict.fromkeys(extra + self.hl)), self.pts)
        S, K, lonc, latc = v["S"], v["K"], v["lonc"], v["latc"]

        def proj(lon, lat):
            return 540 + (lon - lonc) * S * K, cy - (lat - latc) * S

        def proj_arr(a):
            a = np.asarray(a, np.float64)
            return np.stack([540 + (a[:, 0] - lonc) * S * K, cy - (a[:, 1] - latc) * S], 1)

        self.proj = proj
        hw, hh = 560 / (S * K), 1000 / S
        win = (lonc - hw, latc - hh, lonc + hw, latc + hh)

        def sect(b):
            return not (b[2] < win[0] or b[0] > win[2] or b[3] < win[1] or b[1] > win[3])

        def draw(iso, fill_img, edge_img, ew):
            c = geo.c[iso]
            fd, ed = ImageDraw.Draw(fill_img), ImageDraw.Draw(edge_img)
            for poly, bb in zip(c["polys"], c["bbs"]):
                if not sect(bb):
                    continue
                for i, ring in enumerate(poly):
                    pts = [tuple(p) for p in (proj_arr(ring) * SC).tolist()]
                    if len(pts) < 3:
                        continue
                    fd.polygon(pts, fill=255 if i == 0 else 0)
                    if i == 0:
                        ed.line(pts + [pts[0]], fill=255, width=max(int(ew * SC), 1), joint="curve")

        cf, ce = Image.new("L", (W * SC, H * SC), 0), Image.new("L", (W * SC, H * SC), 0)
        for iso in geo.c:
            if iso not in self.hl:
                draw(iso, cf, ce, 2)
        self.cm = np.asarray(cf.resize((W, H), Image.LANCZOS), np.float32)[:, :, None] / 255.0
        self.ce = np.asarray(ce.resize((W, H), Image.LANCZOS), np.float32)[:, :, None] / 255.0
        self.ctx_col = np.array(pal["ctx"], np.float32)
        self.edge_col = np.array(pal["ctx_edge"], np.float32)
        self.alpha = st["map"]["ctx_alpha"]
        self.static_cache = None
        self.hlayers = []
        fill = st["map"]["fill"]
        for iso in self.hl:
            if iso not in geo.c:
                continue
            f, e = Image.new("L", (W * SC, H * SC), 0), Image.new("L", (W * SC, H * SC), 0)
            draw(iso, f, e, st["map"]["edge"])
            f, e = f.resize((W, H), Image.LANCZOS), e.resize((W, H), Image.LANCZOS)
            box = f.getbbox()
            if not box:
                continue
            x0, y0, x1, y1 = box
            x0, y0, x1, y1 = max(x0 - 6, 0), max(y0 - 6, 0), min(x1 + 6, W), min(y1 + 6, H)
            h_, w_ = y1 - y0, x1 - x0
            if fill == "gradient":
                shade = np.linspace(1.18, 0.78, h_, dtype=np.float32)[:, None, None] * np.ones((1, w_, 1), np.float32)
            elif fill == "hatch":
                yy, xx = np.mgrid[y0:y1, x0:x1]
                shade = (1.0 + 0.22 * (((xx + yy) % 26) < 9)).astype(np.float32)[:, :, None] * 0.93
            else:
                shade = np.ones((h_, w_, 1), np.float32)
            self.hlayers.append({"sl": (y0, y1, x0, x1), "M": np.asarray(f, np.float32)[y0:y1, x0:x1, None] / 255.0,
                                 "E": np.asarray(e, np.float32)[y0:y1, x0:x1, None] / 255.0, "shade": shade})
        self.plab = []
        placed = []
        for p in self.pts:
            x, y = proj(float(p["lon"]), float(p["lat"]))
            side = -1
            for _ in range(2):
                ly = y + side * 70
                if all(abs(ly - q[1]) > 64 or abs(x - q[0]) > 320 for q in placed):
                    break
                side = 1
            ly = y + side * 70
            placed.append((x, ly))
            self.plab.append((x, y, ly))

    def base(self, t, ent, bgf, bg_static):
        ca = ent(t, 0.0, 0.5)
        if bg_static and ca >= 1 and self.static_cache is not None:
            out = self.static_cache.copy()
        else:
            k = self.alpha * ca
            out = bgf + (self.ctx_col - bgf) * (self.cm * k)
            out = out + (self.edge_col - out) * (self.ce * (0.8 * k))
            if bg_static and ca >= 1:
                self.static_cache = out.copy()
        edge_hl = np.array(mix(self.pal["text"], (255, 255, 255), 0.5), np.float32)
        for i, L in enumerate(self.hlayers):
            a = ent(t, 0.25 + 0.4 * i, 0.7)
            if a <= 0:
                continue
            y0, y1, x0, x1 = L["sl"]
            col = np.array(self.pal["hl"][i % len(self.pal["hl"])], np.float32) * L["shade"]
            reg = out[y0:y1, x0:x1]
            m = L["M"] * a
            reg[:] = reg * (1 - m) + np.clip(col, 0, 255) * m
            e = L["E"] * 0.9 * a
            reg[:] = reg * (1 - e) + edge_hl * e
        return out

    def marker(self, d, x, y, k, kind, acc, outline):
        r = 13 * k
        a = int(255 * k)
        if kind == "pin":
            d.polygon([(x, y), (x - r * 1.1, y - r * 2.2), (x + r * 1.1, y - r * 2.2)], fill=outline + (a,))
            d.ellipse([x - r * 1.35, y - r * 3.5, x + r * 1.35, y - r * 0.8], fill=outline + (a,))
            d.ellipse([x - r * 0.65, y - r * 2.8, x + r * 0.65, y - r * 1.5], fill=acc + (a,))
        elif kind == "square":
            d.rectangle([x - r - 4, y - r - 4, x + r + 4, y + r + 4], fill=outline + (a,))
            d.rectangle([x - r, y - r, x + r, y + r], fill=acc + (a,))
        elif kind == "diamond":
            d.polygon([(x, y - r * 1.5 - 5), (x + r * 1.5 + 5, y), (x, y + r * 1.5 + 5), (x - r * 1.5 - 5, y)], fill=outline + (a,))
            d.polygon([(x, y - r * 1.5), (x + r * 1.5, y), (x, y + r * 1.5), (x - r * 1.5, y)], fill=acc + (a,))
        else:
            d.ellipse([x - r - 4, y - r - 4, x + r + 4, y + r + 4], fill=outline + (a,))
            d.ellipse([x - r, y - r, x + r, y + r], fill=acc + (a,))

    def overlay(self, ov, t, ent, font):
        d = ImageDraw.Draw(ov)
        pal = self.pal
        kind = self.st["map"]["marker"]
        acc = pal["accent"]
        outline = pal["text"]
        for j, p in enumerate(self.pts):
            x, y, ly = self.plab[j]
            k = ent(t, 1.0 + 0.55 * j, 0.45)
            if k <= 0:
                continue
            dot = p.get("dot", True)
            if dot:
                if kind in ("ring", "square", "diamond") and t > 1.0 + 0.55 * j + 0.45:
                    ph = ((t - 1.45 - 0.55 * j) * 0.9) % 1.0
                    rr = 18 + 46 * ph
                    d.ellipse([x - rr, y - rr, x + rr, y + rr], outline=acc + (int(210 * (1 - ph)),), width=5)
                self.marker(d, x, y, k, kind, acc, outline)
            name = str(p.get("name", ""))
            if not name:
                continue
            ty = (ly if dot else y) + int(10 * (1 - k))
            if kind == "pin" and dot:
                ty = y - 100 + int(10 * (1 - k))
            w = font.getlength(name, language="ar")
            d.rounded_rectangle([x - w / 2 - 22, ty - 40, x + w / 2 + 22, ty + 40], radius=22, fill=pal["c1"] + (int(200 * k),))
            d.text((x, ty), name, font=font, fill=pal["text"] + (int(255 * k),), anchor="mm", language="ar")


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
            wd = font.getlength(it[0], language="ar") * 1.12
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
            w = font.getlength(line, language="ar")
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
                d.text((cx, cyl + 4), line, font=font, fill=self.shadow(), anchor=anc, language="ar")
            d.text((cx, cyl), line, font=font, fill=tc + (255,), anchor=anc, language="ar")
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
        ws = [f.getlength(w[0], language="ar") for f, w in zip(fonts, cur)]
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
                d.text((x, y), w[0], font=f, fill=col + (255,), anchor="rm", language="ar", stroke_width=max(size // 9, 4),
                       stroke_fill=pal["c2"] + (255,))
            else:
                if mode in ("plain", "underline", "box_word") and not (active and hl == "box"):
                    d.text((x, y + 4), w[0], font=f, fill=self.shadow(), anchor="rm", language="ar")
                d.text((x, y), w[0], font=f, fill=col + (255,), anchor="rm", language="ar")
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
            d.text((xy[0], xy[1] + 4), s_, font=f, fill=sh[:3] + (int(sh[3] * al),), anchor=anchor, language="ar")
            d.text(xy, s_, font=f, fill=tuple(col) + (int(255 * al),), anchor=anchor, language="ar")

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
            ws = [f.getlength(w, language="ar") for w in lw]
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
                    d.text((x, y + 5), w, font=f, fill=sh[:3] + (int(sh[3] * k),), anchor="rm", language="ar")
                    d.text((x, y), w, font=f, fill=col + (int(255 * k),), anchor="rm", language="ar")
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
