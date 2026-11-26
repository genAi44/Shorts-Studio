"""Split from `pipeline/render.py` (re-exported there); see that module."""
from .config import H, W
from PIL import Image, ImageDraw
import math
import numpy as np
from .render import SC, _dtext, _tlen, lum, mix  # noqa: E402


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
            w = _tlen(font, name)
            d.rounded_rectangle([x - w / 2 - 22, ty - 40, x + w / 2 + 22, ty + 40], radius=22, fill=pal["c1"] + (int(200 * k),))
            _dtext(d, (x, ty), name, font=font, fill=pal["text"] + (int(255 * k),), anchor="mm")
