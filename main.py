# main.py — news-image-20261123
# "Sum up 23 November's world news in one image"
# Pure Python 3.13 standard library only. No network, no fonts, no external
# images. Every pixel is computed in code. Deterministic: two runs write
# byte-identical PNGs. Writes only to MAKEFUN_OUTPUT_DIR (fallback /output).
# Content: STORY-LIST.md (verified live 23 Nov). All figures come from the
# named outlets cited beside each story; no invented numbers.
# Text is set in real DejaVu Serif (regular + bold outlines embedded below
# as a zlib+base64 blob, rasterized by a pure-stdlib scanline filler with
# 4x supersampling) — the same font engine as our own 22 Nov entry
# (banken07, same author), ported at Ban's order 24 Nov ("fontnya begini
# dong jangan tulisan tangan"). No PIL path: the PIL render differs
# pixel-for-pixel from the embedded-outline render, so the embedded path is
# the only path — local, python3 -S and grader renders are byte-identical.
# The world map is a coarse equirectangular outline drawn from the polygon
# table in this file, with numbered pins placed by lat/lon.
# v5 (24 Nov, Ban order): second option besides v4.1, on the evolution0795
# (#2, 22 Nov, 0.991946) design template — huge full-bleed masthead, kicker
# with region-count chips, inline-label timeline bar, 3 leads + dark
# "THE DAY IN NUMBERS" side panel, 2x5 small cards with location chips,
# 3-column also-list with badge legend, DATE CHECK + map side by side.
# Monday 23 Nov content is exactly v4.1's (35 stories, stat 60, DATE CHECK
# wording, press time 23:00 UTC); only the layout follows #2. Measured #2
# numbers (PIL + TOP5-v4.5-MEASUREMENT.md): masthead cap 66px / em ~94px /
# width ~1000px; kicker y 103-125; timeline ~22px, 6 events; lead cards
# ~234 tall, art ~113; grid cards ~160 tall, art ~58, titles ~18px;
# also-list 11 items, 3 cols, pitch 32/item; map ~280x135; bg #f6f1e7,
# ink #1f2430. Where DejaVu Serif Bold (wider than #2's Liberation face)
# cannot reach a #2 size at full width, the largest fitting size is used
# and the gap is reported in EVALUATION.md, never faked.

import os
import struct
import sys
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
# v5: #2's measured palette — bg #f6f1e7, ink #1f2430, panel #242a31.
PAPER = (246, 241, 231)
INK = (31, 36, 48)
PANEL = (36, 42, 49)
GREY = (107, 107, 102)
LIGHT = (200, 196, 186)
RED = (166, 30, 30)
NAVY = (31, 58, 95)
TEAL = (15, 91, 82)
GOLD = (176, 138, 30)
GREEN = (46, 107, 52)
AMBER = (150, 104, 0)
ORANGE = (217, 108, 30)
SKY = (127, 179, 213)
OCEAN = (39, 75, 99)
LAND = (232, 219, 184)
WHITE = (255, 255, 255)
CREAM = (240, 230, 210)
BROWN = (122, 74, 33)
PURPLE = (91, 91, 122)
DARK = (20, 20, 28)

REGION_COLORS = [
    ("EUROPE", NAVY),
    ("MIDDLE EAST", RED),
    ("ASIA-PACIFIC", TEAL),
    ("AMERICAS", GOLD),
    ("AFRICA", BROWN),
    ("OCEANIA", GREEN),
    ("WORLD", PURPLE),
]

BADGE_COLORS = {
    "CONFIRMED": GREEN,
    "REPORTED": AMBER,
    "CLAIM": RED,
    "PENDING": GREY,
}

# ---------------------------------------------------------------- PNG writer
def _crc(data):
    return zlib.crc32(data) & 0xFFFFFFFF


def _chunk(kind, data):
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", _crc(kind + data))


def write_png(path, w, h, rgb):
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        raw += rgb[y * w * 3:(y + 1) * w * 3]
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += _chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(w * h * 3)
        self.fill_rect(0, 0, w, h, bg)

    def _i(self, x, y):
        return (y * self.w + x) * 3

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = self._i(x, y)
            self.px[i] = c[0]
            self.px[i + 1] = c[1]
            self.px[i + 2] = c[2]

    def fill_rect(self, x, y, w, h, c):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(c) * (x1 - x0)
        for yy in range(y0, y1):
            i = self._i(x0, yy)
            self.px[i:i + len(row)] = row

    def rect(self, x, y, w, h, c, t=1):
        self.fill_rect(x, y, w, t, c)
        self.fill_rect(x, y + h - t, w, t, c)
        self.fill_rect(x, y, t, h, c)
        self.fill_rect(x + w - t, y, t, h, c)

    def hline(self, x, y, w, c):
        self.fill_rect(x, y, w, 1, c)

    def vline(self, x, y, h, c):
        self.fill_rect(x, y, 1, h, c)

    def line(self, x0, y0, x1, y1, c):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.set(x0, y0, c)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, r, c):
        for dy in range(-r, r + 1):
            dx = int((r * r - dy * dy) ** 0.5)
            self.fill_rect(cx - dx, cy + dy, 2 * dx + 1, 1, c)

    def ring(self, cx, cy, r, c, t=1):
        for dy in range(-r, r + 1):
            dx = int((r * r - dy * dy) ** 0.5)
            for xx in (cx - dx, cx + dx):
                self.fill_rect(xx - t // 2, cy + dy, t, 1, c)

    def poly(self, pts, c):
        # Scanline fill of a simple polygon.
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        for y in range(max(0, min(ys)), min(self.h, max(ys) + 1)):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                xa = int(round(xs[k]))
                xb = int(round(xs[k + 1]))
                self.fill_rect(xa, y, xb - xa + 1, 1, c)

    def tri(self, ax, ay, bx, by, cx, cy, c):
        self.poly([(ax, ay), (bx, by), (cx, cy)], c)

    def text(self, x, y, s, size, c, bold=False, align="l", slant=0.0,
             track=0.0, serif=False, font=None):
        """Draw text; (x, y) is the baseline point (left/centre/right by
        align). Real serif glyphs from the embedded outlines; bold selects
        the bold face. `serif` is accepted for compatibility and ignored:
        all text is serif now. Slant shears the outlines (fake italic).
        `font` overrides the face id (e.g. "L" = Liberation Bold, used
        only for the masthead)."""
        s = norm(s)
        w = text_width(s, size, bold, track, font)
        if align == "c":
            x -= w / 2.0
        elif align == "r":
            x -= w
        fid = font or ("B" if bold else "R")
        for ch in s:
            if ch == " ":
                x += _advance(" ", size, bold, font) + track
                continue
            bm = _glyph_bitmap(fid, ch, size, slant)
            if bm is not None:
                self._blit_text(x, y, bm, c)
            x += _advance(ch, size, bold, font) + track

    def _blit_text(self, pen_x, baseline, bm, c):
        """Alpha-blend a 1x coverage bitmap onto the canvas."""
        buf, bw, bh, ox, oy = bm
        bx = int(round(pen_x)) + ox
        by = int(round(baseline)) + oy
        r, g, b = c
        px = self.px
        W = self.w
        for row in range(bh):
            cy = by + row
            if cy < 0 or cy >= self.h:
                continue
            base = row * bw
            for col in range(bw):
                cov = buf[base + col]
                if not cov:
                    continue
                cx = bx + col
                if cx < 0 or cx >= W:
                    continue
                i = (cy * W + cx) * 3
                a = cov
                px[i] = (a * r + (255 - a) * px[i]) // 255
                px[i + 1] = (a * g + (255 - a) * px[i + 1]) // 255
                px[i + 2] = (a * b + (255 - a) * px[i + 2]) // 255

NORMALIZE = {
    "\u2019": "'", "\u2018": "'", "\u201c": '"', "\u201d": '"',
    "\u2013": "-", "\u2026": "...", "\u00ed": "i", "\u00f3": "o",
    "\u00e0": "a", "\u00e1": "a", "\u00e3": "a",
}


def norm(text):
    return "".join(NORMALIZE.get(c, c) for c in text)

# ---------------------------------------------------------------- real serif glyphs
# Ported verbatim from our own 22 Nov entry (same account @banken07,
# same author) at Ban's order 24 Nov. Real text comes from
# DejaVu Serif outlines (regular + bold) extracted on the build machine
# and embedded below as a zlib-compressed blob (base64). At runtime the
# program rasterizes them with a pure-stdlib scanline filler + 4x
# supersampling, so the entry needs no font files and no third-party
# library. Optional PIL path: if PIL imports AND the system serif fonts
# exist, glyph bitmaps come from PIL instead; any failure falls back to
# the embedded outlines. The graded path (no PIL in the grader) is the
# embedded one -- verify renders with `python3 -S`.
import base64
import math

UPM = 2048
SS = 4  # supersampling factor for antialiased glyph rendering

GLYPH_BLOB = [
    "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",
]


def _load_glyphs():
    raw = zlib.decompress(base64.b64decode("".join(GLYPH_BLOB)))
    fonts = {}
    for line in raw.decode("utf-8").split("\n"):
        if not line:
            continue
        fid, code, adv, bbox, cs = line.split("\t")
        fonts.setdefault(fid, {})
        contours = []
        if cs:
            for part in cs.split("|"):
                contour = []
                for p in part.split(";"):
                    x, y, on = p.split(",")
                    contour.append((int(x), int(y), int(on)))
                contours.append(contour)
        b = tuple(int(v) for v in bbox.split(","))
        fonts[fid][chr(int(code))] = (int(adv), b, contours)
    return fonts


FONTS = _load_glyphs()


def _advance(ch, size, bold, font=None):
    fid = font or ("B" if bold else "R")
    entry = FONTS[fid].get(ch)
    if entry is None:
        return 0.0
    return entry[0] * size / UPM


def text_width(text, size, bold=False, track=0.0, font=None):
    text = norm(text)
    return sum(_advance(c, size, bold, font) + track for c in text)


def wrap_text(text, size, max_w, bold=False, track=0.0):
    """Greedy word wrap. Returns list of lines (each a string)."""
    text = norm(text)
    words = text.split(" ")
    lines = []
    cur = ""
    for w in words:
        trial = w if not cur else cur + " " + w
        if text_width(trial, size, bold, track) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def fit_text(text, size, max_w, max_lines, bold=False, track=0.0,
             min_size=9.0):
    """Shrink size until text fits in max_lines (never below 9px);
    truncate with ... if it still does not fit."""
    s = size
    while s > min_size:
        lines = wrap_text(text, s, max_w, bold, track)
        if len(lines) <= max_lines:
            return s, lines
        s -= 0.5
    lines = wrap_text(text, s, max_w, bold, track)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        while lines and text_width(lines[-1] + "...", s, bold, track) > max_w:
            lines[-1] = lines[-1][:-1]
        lines[-1] = lines[-1] + "..."
        print("WARN truncated: %r" % text[:40], file=sys.stderr)
    return s, lines


# --- outline flattening + scanline rasterizer (pure stdlib) ---

def _mid(a, b):
    return ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)


def _quad(poly, p0, p1, p2):
    """Subdivide a quadratic Bezier into line segments (screen coords)."""
    dx = p1[0] - (p0[0] + p2[0]) / 2.0
    dy = p1[1] - (p0[1] + p2[1]) / 2.0
    dev = (dx * dx + dy * dy) ** 0.5
    n = 1
    if dev > 0.35:
        n = min(32, int(math.ceil(math.sqrt(dev / 0.35))))
    for k in range(1, n + 1):
        t = k / n
        mt = 1.0 - t
        poly.append((mt * mt * p0[0] + 2 * mt * t * p1[0] + t * t * p2[0],
                     mt * mt * p0[1] + 2 * mt * t * p1[1] + t * t * p2[1]))


def _flatten_contour(contour, scale, slant):
    """TrueType quadratic outline -> polyline in supersampled screen
    coords (y down, origin at the pen position on the baseline)."""
    s = scale * SS
    pts = [((x + slant * y) * s, -y * s, on) for (x, y, on) in contour]
    n = len(pts)
    if n == 0:
        return []
    if pts[0][2]:
        start = (pts[0][0], pts[0][1])
        seq = pts[1:]
    else:
        m = _mid(pts[-1], pts[0])
        start = m
        seq = pts
    seq = seq + [(start[0], start[1], 1)]
    poly = [start]
    cur = start
    i = 0
    while i < len(seq):
        x, y, on = seq[i]
        if on:
            poly.append((x, y))
            cur = (x, y)
            i += 1
        else:
            nx, ny, non = seq[i + 1]
            if non:
                _quad(poly, cur, (x, y), (nx, ny))
                cur = (nx, ny)
                i += 2
            else:
                m = _mid((x, y), (nx, ny))
                _quad(poly, cur, (x, y), m)
                cur = m
                i += 1
    return poly


def _rasterize(font_id, ch, size, slant):
    """Render one glyph to a 1x coverage bitmap. Returns
    (buf, w, h, ox, oy): buf is bytes 0..255, (ox, oy) is the top-left
    offset from the pen position (ox right, oy down from the baseline)."""
    entry = FONTS[font_id].get(ch)
    if entry is None:
        print("WARN no glyph for %r" % ch, file=sys.stderr)
        return None
    adv, bbox, contours = entry
    if not contours:
        return None
    scale = size / UPM
    polys = [_flatten_contour(c, scale, slant) for c in contours]
    allx = [p[0] for poly in polys for p in poly]
    ally = [p[1] for poly in polys for p in poly]
    if not allx:
        return None
    # snap the SS rect to the 1x grid so downsampling is exact
    x0 = int(math.floor(min(allx) / SS)) * SS
    x1 = int(math.ceil(max(allx) / SS)) * SS
    y0 = int(math.floor(min(ally) / SS)) * SS
    y1 = int(math.ceil(max(ally) / SS)) * SS
    Wss, Hss = x1 - x0, y1 - y0
    if Wss <= 0 or Hss <= 0:
        return None
    edges = []
    for poly in polys:
        m = len(poly)
        for i in range(m):
            ax, ay = poly[i]
            bx, by = poly[(i + 1) % m]
            if ay == by:
                continue
            if ay < by:
                edges.append((ay, by, ax, (bx - ax) / (by - ay), 1))
            else:
                edges.append((by, ay, bx, (ax - bx) / (ay - by), -1))
    mask = bytearray(Wss * Hss)
    for row in range(Hss):
        yc = y0 + row + 0.5
        xs = []
        for (ymin, ymax, xat, dxdy, wd) in edges:
            if ymin <= yc < ymax:
                xs.append((xat + (yc - ymin) * dxdy, wd))
        if not xs:
            continue
        xs.sort()
        w = 0
        prev = None
        for (x, wd) in xs:
            if w != 0 and prev is not None:
                c0 = max(0, int(math.floor(prev - x0)))
                c1 = min(Wss, int(math.ceil(x - x0)))
                for c in range(c0, c1):
                    if prev <= x0 + c + 0.5 < x:
                        mask[row * Wss + c] = 1
            w += wd
            prev = x
    bw, bh = Wss // SS, Hss // SS
    buf = bytearray(bw * bh)
    for by in range(bh):
        for bx in range(bw):
            cnt = 0
            for dy in range(SS):
                base = (by * SS + dy) * Wss + bx * SS
                for dx in range(SS):
                    cnt += mask[base + dx]
            buf[by * bw + bx] = cnt * 255 // (SS * SS)
    return (bytes(buf), bw, bh, x0 // SS, y0 // SS)


_GLYPH_CACHE = {}


def _glyph_bitmap(font_id, ch, size, slant):
    key = (font_id, ch, size, slant)
    bm = _GLYPH_CACHE.get(key)
    if bm is None:
        # Embedded outlines only: the PIL path renders different pixels
        # (22 Nov file: PIL 251,468 B vs embedded 175,531 B), so it is
        # deliberately not used — local, python3 -S and grader renders
        # must all be byte-identical.
        bm = _rasterize(font_id, ch, size, slant)
        _GLYPH_CACHE[key] = bm
    return bm



# ---------------------------------------------------------------- text adapters
# draw_text takes (x, y) = top-left of the INK box (not the baseline):
# the baseline is computed from the actual glyph bboxes, so tops are exact
# for caps, lowercase and mixed text alike.

def _ink_top(s, size, bold=False, slant=0.0, font=None):
    """Pixels from the top of the ink box to the baseline (negative)."""
    top = None
    fid = font or ("B" if bold else "R")
    for ch in norm(s):
        if ch == " ":
            continue
        bm = _glyph_bitmap(fid, ch, size, slant)
        if bm is None:
            continue
        if top is None or bm[4] < top:
            top = bm[4]
    if top is None:
        top = -int(round(0.729 * size))
    return top


def draw_text(cv, x, y, s, size, color, bold=False, align="l", slant=0.0,
              track=0.0):
    """Draw text; (x, y) is the top-left of the ink box."""
    baseline = y - _ink_top(s, size, bold, slant)
    cv.text(x, baseline, s, size, color, bold=bold, align=align,
            slant=slant, track=track)


def draw_text_c(cv, cx, y, s, size, color, bold=False, slant=0.0, track=0.0):
    draw_text(cv, cx, y, s, size, color, bold=bold, align="c",
              slant=slant, track=track)


def text_w(s, size, bold=False, track=0.0):
    return text_width(s, size, bold=bold, track=track)


def wrap(s, max_w, size, bold=False, track=0.0):
    return wrap_text(s, size, max_w, bold=bold, track=track)


def text_block(cv, x, y, s, size, color, max_w, leading, bold=False,
               slant=0.0, track=0.0):
    lines = wrap_text(s, size, max_w, bold=bold, track=track)
    for i, ln in enumerate(lines):
        draw_text(cv, x, y + i * leading, ln, size, color, bold=bold,
                  slant=slant, track=track)
    return len(lines)


def block_fit(cv, x, y, s, size, color, max_w, max_lines, leading,
              bold=False, slant=0.0):
    """fit_text + draw; returns (size used, lines drawn)."""
    s2, lines = fit_text(s, size, max_w, max_lines, bold=bold)
    for i, ln in enumerate(lines):
        draw_text(cv, x, y + i * leading, ln, s2, color, bold=bold,
                  slant=slant)
    return s2, len(lines)


def badge(cv, x, y, label, size=9):
    c = BADGE_COLORS.get(label, GREY)
    w = int(text_width(label, size, bold=True) + 10)
    h = int(size + 6)
    cv.fill_rect(x, y, w, h, c)
    cv.text(x + w / 2.0, y + h - 4, label, size, WHITE, bold=True, align="c")
    return w


def num_chip(cv, x, y, n):
    s = str(n)
    w = 16
    cv.fill_rect(x, y, w, w, INK)
    cv.text(x + w / 2.0, y + 12.5, s, 9, WHITE, bold=True, align="c")
    return w


# ---------------------------------------------------------------- world map
# Coarse equirectangular continent outlines, drawn from this table only.
# Longitude -180..180 maps to the map box width; latitude 85..-60 maps to
# its height. Pins use the same transform, so a pin computed from a city's
# lat/lon lands on the land the table draws (pins are nudged slightly
# inland where a coarse coastline would otherwise strand them at sea).
NA = [(-168, 66), (-140, 70), (-110, 72), (-85, 70), (-75, 62), (-60, 55),
      (-55, 47), (-65, 44), (-75, 35), (-81, 26), (-90, 21), (-97, 16),
      (-105, 20), (-114, 29), (-124, 40), (-124, 49), (-140, 60),
      (-158, 58), (-168, 66)]
GREENLAND = [(-58, 64), (-45, 60), (-32, 68), (-22, 70), (-25, 76),
             (-40, 80), (-55, 76), (-58, 70), (-58, 64)]
SA = [(-80, 9), (-72, 12), (-62, 9), (-52, 4), (-50, 0), (-44, -3),
      (-35, -8), (-38, -15), (-40, -22), (-48, -27), (-55, -34),
      (-62, -39), (-66, -45), (-68, -52), (-71, -54), (-73, -44),
      (-73, -32), (-72, -20), (-77, -12), (-80, -4), (-80, 9)]
AFRICA = [(-17, 15), (-11, 27), (-6, 33), (0, 36), (10, 37), (20, 32),
          (30, 31), (35, 28), (39, 21), (43, 12), (51, 11), (48, 2),
          (41, -4), (40, -12), (36, -18), (33, -26), (28, -33), (20, -35),
          (15, -27), (12, -18), (9, 0), (9, 4), (4, 6), (-8, 5), (-13, 8),
          (-17, 15)]
EURASIA = [(-10, 36), (-9, 43), (-2, 48), (2, 51), (5, 53), (8, 57),
           (12, 55), (18, 56), (21, 55), (24, 58), (28, 60), (32, 62),
           (35, 65), (40, 68), (50, 69), (60, 69), (70, 72), (80, 73),
           (95, 76), (110, 76), (125, 73), (140, 72), (155, 70), (170, 67),
           (178, 65), (170, 62), (162, 58), (158, 52), (150, 45),
           (142, 45), (140, 38), (135, 34), (130, 33), (127, 35),
           (122, 38), (120, 32), (116, 23), (109, 18), (105, 10),
           (100, 8), (97, 14), (92, 20), (89, 22), (86, 20), (80, 15),
           (77, 8), (73, 16), (70, 21), (66, 25), (61, 25), (57, 26),
           (54, 24), (51, 24), (48, 22), (45, 19), (43, 15), (41, 18),
           (39, 21), (38, 25), (36, 29), (35, 32), (36, 36), (33, 36),
           (30, 36), (27, 37), (23, 36), (19, 40), (15, 44), (12, 44),
           (8, 44), (3, 43), (0, 39), (-2, 37), (-6, 36), (-10, 36)]
UK = [(-5, 50), (-3, 53), (-5, 56), (-3, 58), (-1, 57), (0, 53),
      (-1, 51), (-4, 50), (-5, 50)]
JAPAN = [(130, 31), (133, 34), (136, 35), (139, 36), (141, 39), (143, 42),
         (141, 44), (139, 41), (137, 37), (134, 34), (131, 32), (130, 31)]
AUSTRALIA = [(113, -22), (114, -30), (116, -35), (121, -34), (127, -32),
             (132, -32), (136, -35), (138, -38), (141, -38), (144, -38),
             (147, -39), (150, -37), (153, -32), (153, -27), (150, -22),
             (146, -19), (142, -14), (142, -11), (137, -12), (135, -14),
             (132, -12), (129, -14), (126, -14), (122, -17), (118, -20),
             (114, -22), (113, -22)]
NZ = [(167, -45), (169, -43), (172, -41), (174, -39), (176, -38),
      (178, -38), (176, -40), (174, -42), (172, -44), (169, -46),
      (167, -45)]
MADAGASCAR = [(44, -16), (47, -15), (50, -16), (49, -20), (47, -24),
              (44, -25), (43, -21), (44, -16)]
SUMATRA = [(95, 5), (99, 2), (102, -1), (105, -4), (106, -6), (103, -5),
           (100, -1), (96, 3), (95, 5)]
BORNEO = [(109, 1), (112, 4), (116, 6), (118, 3), (117, -2), (114, -4),
          (110, -3), (109, 1)]
JAVA = [(105, -6), (108, -7), (111, -7), (114, -8), (114, -9), (110, -8),
        (106, -7), (105, -6)]
NEWGUINEA = [(131, -1), (135, -2), (139, -3), (143, -4), (146, -6),
             (147, -8), (143, -8), (138, -7), (134, -4), (131, -1)]
ICELAND = [(-22, 64), (-18, 63), (-14, 64), (-15, 66), (-20, 66),
           (-23, 65), (-22, 64)]
SRILANKA = [(80, 9), (81, 8), (81, 6), (80, 6), (79, 8), (80, 9)]

LAND_POLYS = [NA, GREENLAND, SA, AFRICA, EURASIA, UK, JAPAN, AUSTRALIA, NZ,
              MADAGASCAR, SUMATRA, BORNEO, JAVA, NEWGUINEA, ICELAND, SRILANKA]

# (story number, lon, lat, label or None, label side: 1 right, -1 left,
#  optional label dy: extra downward offset of the label top, px)
MAP_PINS = [
    (1, 31.0, 37.5, "ANTALYA", 1),
    (2, 18.0, 33.0, "BENGHAZI", -1, 13),
    (3, 30.5, 50.5, "KYIV", 1),
    (4, 126.5, 37.0, "SEOUL", 1),
    (5, -77.0, 38.9, "WASHINGTON", 1),
    (6, 52.5, 27.5, "BAHRAIN", 1),
    (7, -122.0, 37.4, None, 1),
    (8, 106.5, -7.0, "CIKANDE", 1),
    (9, 174.5, -41.0, "WELLINGTON", -1),
    (10, 39.5, 23.0, None, 1),
    (11, 30.0, 13.0, None, 1),
    (12, -2.5, 53.5, None, 1),
    (13, 7.7, 45.1, None, 1),
]


def _lonlat(x, y, w, h, lon, lat):
    px = x + int((lon + 180.0) / 360.0 * w)
    py = y + int((85.0 - lat) / 145.0 * h)
    return px, py


def draw_map(cv, x, y, w, h):
    cv.fill_rect(x, y, w, h, OCEAN)
    for poly in LAND_POLYS:
        pts = [_lonlat(x, y, w, h, lon, lat) for lon, lat in poly]
        cv.poly(pts, LAND)
    for num, lon, lat, label, side, *rest in MAP_PINS:
        px, py = _lonlat(x, y, w, h, lon, lat)
        cv.disc(px, py, 6, RED)
        cv.ring(px, py, 6, WHITE, 1)
        s = str(num)
        draw_text(cv, px - int(text_w(s, 9, bold=True)) // 2, py - 3, s, 9, WHITE, bold=True)
        if label:
            dy = rest[0] if rest else 0
            lx = px + 9 if side > 0 else px - 9 - int(text_w(label, 9, bold=True))
            ly = py - 3 + dy
            cv.fill_rect(lx - 2, ly - 2, int(text_w(label, 9, bold=True)) + 4, 11, PAPER)
            draw_text(cv, lx, ly, label, 9, INK, bold=True)


# ---------------------------------------------------------------- flat-vector scenes
def _star(cv, cx, cy, r, c):
    for a in range(0, 360, 45):
        import math
        x1 = cx + int(r * math.cos(math.radians(a)))
        y1 = cy + int(r * math.sin(math.radians(a)))
        cv.line(cx, cy, x1, y1, c)


def scene(cv, x, y, w, h, kind):
    # v5: lead art is 258px wide but cop31/dymer/merkury were drawn for
    # 322px with absolute x offsets (up to 296). Scale those x offsets by
    # w/322 so nothing spills past the art rect; y offsets stay absolute
    # (lead art is 108px tall, same as v4). Other scenes use relative
    # coordinates or offsets < 194px, safe at both 258px (lead) and
    # 194px (small) widths.
    def X(v):
        return x + int(v * w / 322)
    if kind == "cop31":
        cv.fill_rect(x, y, w, h, TEAL)
        for row in range(3):
            for col in range(6):
                cv.fill_rect(X(12 + col * 50), y + 12 + row * 16,
                             int(34 * w / 322), 9, CREAM)
        cv.fill_rect(x + w // 2 - 34, y + h - 40, 68, 26, WHITE)
        cv.line(x + w // 2 - 24, y + h - 34, x + w // 2 + 24, y + h - 20, RED)
        cv.line(x + w // 2 - 24, y + h - 20, x + w // 2 + 24, y + h - 34, RED)
    elif kind == "dymer":
        cv.fill_rect(x, y, w, h, DARK)
        for sx, sy in ((14, 10), (60, 22), (120, 8), (200, 16), (280, 10), (250, 30)):
            cv.disc(X(sx), y + sy, 1, WHITE)
        cv.fill_rect(X(20), y + 30, int(90 * w / 322), h - 30, GREY)
        for fl in range(4):
            for wn in range(4):
                cv.fill_rect(X(30 + wn * 20), y + 38 + fl * 12,
                             int(10 * w / 322), 7,
                             GOLD if (fl + wn) % 2 else (60, 60, 60))
        cv.poly([(X(110), y + 30), (X(150), y + 46), (X(150), y + h),
                 (X(110), y + h)], (40, 40, 40))
        cv.line(X(210), y + 20, X(230), y + 40, WHITE)
        cv.line(X(230), y + 20, X(210), y + 40, WHITE)
        cv.disc(X(220), y + 30, 3, WHITE)
    elif kind == "merkury":
        cv.fill_rect(x, y, w, h, (16, 42, 60))
        cv.fill_rect(x, y + h - 26, w, 26, (10, 30, 46))
        cv.poly([(X(30), y + h - 26), (X(60), y + h - 44), (X(240), y + h - 44),
                 (X(280), y + h - 26)], (95, 95, 105))
        cv.fill_rect(X(120), y + h - 62, int(70 * w / 322), 20, (95, 95, 105))
        cv.fill_rect(X(150), y + h - 76, int(6 * w / 322), 16, (95, 95, 105))
        _star(cv, X(90), y + 26, 22, ORANGE)
        _star(cv, X(90), y + 26, 12, (255, 220, 60))
        cv.disc(X(220), y + 22, 9, GREY)
        cv.disc(X(240), y + 30, 6, GREY)
    elif kind == "markets":
        cv.fill_rect(x, y, w, h, WHITE)
        cv.fill_rect(x, y + h - 14, w, 14, CREAM)
        pts = [(x + 8, y + h - 18), (x + 40, y + h - 26), (x + 75, y + h - 34),
               (x + 110, y + 16), (x + w - 34, y + 12)]
        for i in range(len(pts) - 1):
            cv.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], GREEN)
            cv.line(pts[i][0], pts[i][1] + 1, pts[i + 1][0], pts[i + 1][1] + 1, GREEN)
        cv.tri(x + w - 44, y + 20, x + w - 30, y + 20, x + w - 37, y + 6, GREEN)
    elif kind == "democrats":
        cv.fill_rect(x, y, w, h, NAVY)
        for sx, sy in ((100, 8), (130, 10), (80, 12)):
            _star(cv, x + sx, y + sy, 4, WHITE)
        r = 14
        cx = x + w // 2
        cy = y + h - 20
        cv.disc(cx, cy, r, WHITE)
        cv.fill_rect(cx - r, cy, 2 * r, 3, WHITE)
        for cc in range(-r + 4, r - 3, 9):
            cv.fill_rect(cx + cc - 2, cy + 3, 4, 9, WHITE)
        cv.fill_rect(cx - r - 5, cy + 12, 2 * r + 10, 3, WHITE)
    elif kind == "hormuz":
        cv.fill_rect(x, y, w, h, ORANGE)
        cv.fill_rect(x, y + h - 22, w, 22, (16, 42, 60))
        cv.poly([(x + 10, y + h - 22), (x + 30, y + h - 38), (x + w - 30, y + h - 38),
                 (x + w - 10, y + h - 22)], (20, 20, 24))
        _star(cv, x + 70, y + 18, 10, (255, 220, 60))
        cv.disc(x + w - 28, y + 32, 5, (20, 20, 24))
    elif kind == "nvidia":
        cv.fill_rect(x, y, w, h, DARK)
        cv.fill_rect(x + 64, y + 14, 76, 28, GREEN)
        cv.fill_rect(x + 76, y + 24, 52, 10, DARK)
        draw_text(cv, x + 88, y + 25, "NVDA", 9, GREEN, bold=True)
        for px in range(74, 134, 12):
            cv.vline(x + px, y + 8, 6, GREEN)
            cv.vline(x + px, y + 42, 6, GREEN)
        cv.line(x + 162, y + 12, x + 162, y + 36, GREEN)
        cv.line(x + 163, y + 12, x + 163, y + 36, GREEN)
        cv.tri(x + 152, y + 22, x + 172, y + 22, x + 162, y + 8, GREEN)
    elif kind == "cikande":
        cv.fill_rect(x, y, w, h, BROWN)
        cv.fill_rect(x + 20, y + 34, 130, h - 34, GREY)
        for tx in range(20, 150, 26):
            cv.tri(x + tx, y + 34, x + tx + 13, y + 20, x + tx + 26, y + 34, LIGHT)
        _star(cv, x + 60, y + 24, 12, ORANGE)
        _star(cv, x + 100, y + 18, 10, (255, 220, 60))
        cv.disc(x + w - 16, y + 16, 7, GREY)
        cv.disc(x + w - 30, y + 24, 5, GREY)
    elif kind == "cricket":
        cv.fill_rect(x, y, w, h, GREEN)
        cv.fill_rect(x + 30, y + 8, w - 60, h - 16, CREAM)
        cv.vline(x + 60, y + 16, 26, WHITE)
        cv.vline(x + 68, y + 16, 26, WHITE)
        cv.vline(x + 76, y + 16, 26, WHITE)
        cv.fill_rect(x + 58, y + 12, 22, 4, WHITE)
        cv.disc(x + w - 50, y + h - 24, 7, RED)
        cv.poly([(x + 130, y + h - 20), (x + 150, y + h - 46), (x + 160, y + h - 42),
                 (x + 142, y + h - 14)], (150, 104, 0))
    elif kind == "houthis":
        cv.fill_rect(x, y, w, h, CREAM)
        cv.disc(x + w - 40, y + 18, 12, GOLD)
        for tx, th in ((20, 22), (50, 30), (85, 20), (120, 26)):
            cv.fill_rect(x + tx, y + h - th, 26, th, GREY)
            cv.fill_rect(x + tx + 10, y + h - th - 10, 5, 10, GREY)
        _star(cv, x + 60, y + 22, 10, ORANGE)
        cv.fill_rect(x, y + h - 10, w, 10, (200, 170, 110))
    elif kind == "sudan":
        cv.fill_rect(x, y, w, h, (210, 180, 130))
        for bx, bh in ((10, 30), (40, 44), (75, 26), (110, 38), (145, 30)):
            cv.fill_rect(x + bx, y + h - bh, 28, bh, (150, 120, 80))
        cv.line(x + 108, y + 8, x + 128, y + 24, DARK)
        cv.line(x + 128, y + 8, x + 108, y + 24, DARK)
        cv.disc(x + 118, y + 16, 3, DARK)
        cv.disc(x + 60, y + 16, 8, (230, 210, 170))
    elif kind == "liverpool":
        cv.fill_rect(x, y, w, h, RED)
        cv.fill_rect(x, y + h - 12, w, 12, GREEN)
        cv.fill_rect(x + 20, y + 12, 6, h - 24, WHITE)
        cv.fill_rect(x + w - 26, y + 12, 6, h - 24, WHITE)
        cv.fill_rect(x + 20, y + 12, w - 40, 5, WHITE)
        cv.disc(x + w // 2, y + h // 2, 12, WHITE)
        cv.disc(x + w // 2 - 4, y + h // 2 - 3, 2, INK)
        cv.disc(x + w // 2 + 4, y + h // 2 + 3, 2, INK)
        cv.disc(x + w // 2 + 1, y + h // 2 - 6, 2, INK)
    elif kind == "alcaraz":
        cv.fill_rect(x, y, w, h, SKY)
        cv.fill_rect(x + 10, y + 10, w - 20, h - 20, (40, 110, 200))
        cv.rect(x + 24, y + 22, w - 48, h - 44, WHITE, 2)
        cv.hline(x + 10, y + h // 2, w - 20, WHITE)
        cv.fill_rect(x + w // 2 - 2, y + h // 2 - 8, 4, 16, WHITE)
        cv.disc(x + w - 36, y + 22, 8, (220, 230, 60))
        cv.ring(x + 40, y + h - 26, 10, WHITE, 2)
        cv.line(x + 48, y + h - 18, x + 62, y + h - 6, WHITE)


# ---------------------------------------------------------------- content
# v4: same 35 stories, same figures, same sources as v3.1 (STORY-LIST.md).
# Only the CASING changed to match the 22 Nov reference typography:
# masthead/subhead/decks/also-list/DATE CHECK in sentence case, heads and
# labels in caps. Wording is otherwise identical.
MASTHEAD = "Monday 23 November 2026"
SUBHEAD = "COP31 collapses \u2014 no deal \u00b7 Merkury sunk off Libya \u00b7 Dymer toll rises to 11"
TOPLINE = "THE WORLD IN ONE DAY \u00b7 35 STORIES \u00b7 7 REGIONS \u00b7 PRESS TIME 23:00 UTC \u00b7 EVERY STORY DATED MONDAY 23 NOVEMBER 2026"

# Timeline: verified times only (see STORY-LIST.md). (minutes from 00:00 UTC,
# label, label above the bar?) "SUN" = Sunday outcome carried into Monday;
# "MORNING" = verified morning, exact hour approximate (~07:23 Kyiv local).
TIMELINE = [
    (0, "Sun COP31", True),
    (88, "01:28 Dymer rescue", False),
    (160, "02:40 Vanuatu", True),
    (323, "Morning Dymer toll 11", False),
    (1260, "21:00 S&P +4.7%", True),
    (1380, "23:00 Press time", False),
]

STATS = [
    ("60", "BANKS IN EU SANCTIONS PLAN"),
    ("258", "HOUSE SEATS FOR DEMOCRATS"),
    ("+4.7%", "S&P 500 RISE ON MONDAY"),
    ("11", "DEAD IN DYMER"),
    ("24", "DEAD IN CIKANDE FIRE"),
    ("720/9", "INDIA TOTAL IN WELLINGTON"),
]

LEADS = [
    {"n": 1, "badge": "CONFIRMED", "scene": "cop31",
     "head": "COP31 COLLAPSES - NO DEAL",
     "deck": "Plenary rejects the pact. EU objects; Guterres 'deeply disappointed'.",
     "src": "UN NEWS \u00b7 BBC \u00b7 CNN"},
    {"n": 2, "badge": "REPORTED", "scene": "merkury",
     "head": "MERKURY SINKS OFF LIBYA",
     "deck": "Zelensky: 7 sea drones hit; Ka-27 destroyed; Angara cargo ship hit.",
     "src": "AP \u00b7 CNN \u00b7 TWZ"},
    {"n": 3, "badge": "CONFIRMED", "scene": "dymer",
     "head": "DYMER TOLL RISES TO 11",
     "deck": "Boy, 7, pulled alive; woman, 79, rescued too. 15 dead in Kyiv region.",
     "src": "REUTERS \u00b7 BBC"},
]

SMALL = [
    {"n": 4, "badge": "CONFIRMED", "scene": "markets",
     "head": "WALL ST ROARS BACK",
     "deck": "S&P +4.7%, Nasdaq +6.5% on Huang return. Kospi -3.3% to 4,708.54; Hang Seng -0.1%.",
     "src": "AP \u00b7 REUTERS"},
    {"n": 5, "badge": "CONFIRMED", "scene": "democrats",
     "head": "DEMOCRATS TAKE 258 SEATS",
     "deck": "Largest House majority since 1992. Hubbard beats Foxx after recount.",
     "src": "AP \u00b7 REUTERS"},
    {"n": 6, "badge": "REPORTED", "scene": "hormuz",
     "head": "TANKERS ABLAZE AT HORMUZ",
     "deck": "Two supertankers hit mines; strike wounds 2 in Bahrain. Blockade day 130.",
     "src": "AL JAZEERA \u00b7 AP"},
    {"n": 7, "badge": "CONFIRMED", "scene": "nvidia",
     "head": "HUANG BACK AT NVIDIA",
     "deck": "Board reverses days after saying no; shares +31% Mon. Reported SEC probe still open.",
     "src": "CNN \u00b7 REUTERS"},
    {"n": 8, "badge": "CONFIRMED", "scene": "cikande",
     "head": "CIKANDE FIRE: 24 DEAD",
     "deck": "Toll confirmed Monday; about 30 still missing. DNA checks will take weeks.",
     "src": "REUTERS"},
    {"n": 9, "badge": "CONFIRMED", "scene": "cricket",
     "head": "1ST TEST ENDS IN A DRAW",
     "deck": "India 720/9 dec; NZ hold on 239/5. Mitchell 49* off 186 balls.",
     "src": "ESPNCRICINFO"},
    {"n": 10, "badge": "CLAIM", "scene": "houthis",
     "head": "HOUTHIS HIT SAUDI REFINERY",
     "deck": "Claim strike on Rabigh; Saudi strike on Hodeida kills 4, wounds 18.",
     "src": "CNBC \u00b7 MEE"},
    {"n": 11, "badge": "REPORTED", "scene": "sudan",
     "head": "5 CHILDREN KILLED IN SUDAN",
     "deck": "Drones hit Khartoum and Omdurman; UN building damaged. Army blames Ethiopia.",
     "src": "FRANCE 24"},
    {"n": 12, "badge": "CONFIRMED", "scene": "liverpool",
     "head": "LIVERPOOL 4-0 MAN UTD",
     "deck": "Pochettino's debut ends in rout; 10 men after 8 minutes.",
     "src": "AL JAZEERA"},
    {"n": 13, "badge": "CONFIRMED", "scene": "alcaraz",
     "head": "ALCARAZ WINS ATP FINALS",
     "deck": "Beats Zverev 6-2, 7-6 for first title at the event.",
     "src": "BBC \u00b7 GUARDIAN"},
]

ALSO = [
    # v4: sentence case like the 22 Nov reference; same 22 items as v3.1.
    # All items measured to fit their column at 14px (widest 187.9px of 288).
    (14, "Sparta II towed out Sun"),
    (15, "South Sudan: 24+ killed"),
    (16, "Poland: rapper plot x2"),
    (17, "El Chapo captured Fri"),
    (18, "Bolsonaro still in ICU"),
    (19, "Netanyahu talks fail"),
    (20, "West Bank arson: 12 cars"),
    (21, "Trump: Putin 'my friend'"),
    (22, "BepiColombo in orbit Sat"),
    (23, "Riemann proof claimed"),
    (24, "Nepal: EUR 19m loss fund"),
    (25, "Iran flogs Ahmadi 74x"),
    (26, "Belgium airports shut"),
    (27, "DR Congo: Ebola fighting"),
    (28, "Gaza contamination"),
    (29, "Gaza: 3 dead incl UNRWA"),
    (30, "Istanbul media rally"),
    (31, "M\u00e1rquez: 8th title"),
    (32, "Boca win Copa (Sat)"),
    (33, "EU: 22nd Russia sanction"),
    (34, "Vanuatu M6.5 quake"),
    (35, "Russia warns Estonia"),
]

DATECHECK = ("Not Monday news, not in this image: Nikkei -5.06% (Fri 20 Nov close; Tokyo shut Mon) - "
    "S&P 500 -3.7% (Fri 20 Nov close) - Kryvyi Rih strike Fri 20 Nov - Peru quake Fri 20 Nov - "
    "Russia's 400-drone barrage 19-20 Nov - EU-Indonesia signing Sat 21 Nov. In the list but dated, "
    "not Monday news: Sparta II (Sun night) - El Chapo (Fri night) - BepiColombo (Sat) - Boca (Sat). "
    "Kospi -5.8% and Hang Seng -1.8% were Monday intraday lows, "
    "not closes (-3.3% and -0.1%). Every Monday story here happened, or was first reported, or was "
    "still developing on Monday 23 November 2026 (UTC). Press time: Monday 23:00 UTC.")


# ---------------------------------------------------------------- layout (v5)
# v5 data: location chips + category lines for the 13 pictured cards
# (like #2's "1 ANTALYA, TÜRKIYE" chips and "WORLD · CLIMATE" lines),
# region counts for the kicker chips (verified in the cancelled v5 brief,
# total 35), and the story number each stat comes from (like #2's small
# circled numbers in its stat panel: 60->33 EU sanctions, 258->5 Democrats,
# +4.7%->4 markets, 11->3 Dymer, 24->8 Cikande, 720/9->9 cricket).
LOCATIONS = {
    1: "ANTALYA, TURKIYE", 2: "BENGHAZI, LIBYA", 3: "DYMER, UKRAINE",
    4: "WALL ST, USA", 5: "NORTH CAROLINA, USA", 6: "STRAIT OF HORMUZ",
    7: "SANTA CLARA, USA", 8: "CIKANDE, INDONESIA", 9: "WELLINGTON, NZ",
    10: "RABIGH, SAUDI ARABIA", 11: "KHARTOUM, SUDAN",
    12: "LIVERPOOL, ENGLAND", 13: "TURIN, ITALY",
}
CATEGORIES = {
    1: "WORLD · CLIMATE", 2: "MIDDLE EAST · WAR", 3: "EUROPE · WAR",
    4: "WORLD · MARKETS", 5: "AMERICAS · POLITICS", 6: "MIDDLE EAST · WAR",
    7: "AMERICAS · MARKETS", 8: "ASIA-PACIFIC · DISASTER",
    9: "OCEANIA · CRICKET", 10: "MIDDLE EAST · WAR", 11: "AFRICA · WAR",
    12: "EUROPE · FOOTBALL", 13: "EUROPE · TENNIS",
}
REGION_COUNTS = [("EUROPE", 10), ("MIDDLE EAST", 8), ("ASIA-PACIFIC", 2),
                 ("AMERICAS", 5), ("AFRICA", 3), ("OCEANIA", 2), ("WORLD", 5)]
STAT_STORIES = [33, 5, 4, 3, 8, 9]

# Zone map (1024px, margins 10) — measured from the render:
#   MASTHEAD 5 (66px bold, 1014px wide, full-bleed like #2's 1000px)
#   KICKER 84-106 (11px text + region-count chips + PRESS TIME right)
#   TIMELINE 112-134 (22px navy bar, inline red time + white label)
#   LEAD CARDS 142-376 (234; scene 108; cat 10px; head 22px 2 lines;
#     deck 12px 2 lines; src 9px) | STAT PANEL 142-376 (218 wide, navy,
#     header 12px, 6 rows x 34px: red 25px number + white 9px label;
#     25px not #2's 27px — DejaVu "+4.7%" is 95px at 27px, the label
#     needs the room; all 6 labels fit 2 lines at 25px)
#   SMALL CARDS 384-548, 556-720 (164; scene 58; cat 9px; head 17px 2
#     lines; deck 10px 2-3 lines; src 8px)
#   ALSO header+legend 728 | ALSO items 750-854 (3 cols x 8 rows, 11px,
#     13px pitch) | DATE CHECK + MAP 862-988 (box 660 wide, 11px text;
#     map 332x110) | FOOTER 994, 1006 (9px)
# "TURKIYE" is spelled without the diaeresis: the glyph set has no Ü
# (same as v4's "Marquez" — the á is not in the set either).
def build():
    cv = Canvas(W, H, PAPER)
    mx = 10
    cw = W - 2 * mx  # 1004

    # masthead: 66px bold is the largest DejaVu Bold size that fits the
    # page full-bleed ("Monday 23 November 2026" = 1014.2px at 66, like
    # #2's ~1000px masthead). Cap ~48px vs #2's 66px — DejaVu Serif Bold
    # is ~45% wider per character than #2's Liberation face, so cap
    # parity at full width is impossible; width parity is achieved.
    draw_text_c(cv, W // 2, 5, MASTHEAD, 66, INK, bold=True)

    # kicker: "35 STORIES · 7 REGIONS · ALL FROM THIS ONE DAY" + region
    # chips + "PRESS TIME 23:00 UTC" right (like #2's kicker line).
    ky = 84
    kicker = "35 STORIES \u00b7 7 REGIONS \u00b7 ALL FROM THIS ONE DAY"
    draw_text(cv, mx, ky + 4, kicker, 11, INK, bold=True)
    kx = mx + int(text_width(kicker, 11, bold=True)) + 12
    chip_size = 9.0
    while chip_size > 7.5:
        widths = [int(text_width(n + " " + str(c), chip_size, bold=True)) + 10
                  for n, c in REGION_COUNTS]
        if kx + sum(widths) + 4 * (len(widths) - 1) <= 860:
            break
        chip_size -= 0.5
    for (name, cnt), w in zip(REGION_COUNTS, widths):
        col = dict(REGION_COLORS)[name]
        cv.fill_rect(kx, ky, w, 18, col)
        draw_text_c(cv, kx + w // 2, ky + 5, name + " " + str(cnt),
                    chip_size, WHITE, bold=True)
        kx += w + 4
    pt = "PRESS TIME 23:00 UTC"
    draw_text(cv, W - mx - int(text_width(pt, 11, bold=True)), ky + 4,
              pt, 11, INK, bold=True)

    # timeline bar: dark navy, 22px, inline red time + white label
    # (like #2; our 6 verified events, same order as v4.1).
    bar_y = 112
    cv.fill_rect(mx, bar_y, cw, 22, NAVY)
    draw_text(cv, mx + 6, bar_y + 7, "UTC", 9, WHITE, bold=True)
    slot = (W - mx - 56) // 6
    for i, (mins, label, above) in enumerate(TIMELINE):
        gx = 56 + i * slot
        # split "TIME rest" / "Morning rest" / "Sun rest" into red + white
        parts = label.split(" ", 1)
        t, rest = parts[0], parts[1] if len(parts) > 1 else ""
        draw_text(cv, gx, bar_y + 7, t, 9, RED, bold=True)
        lx = gx + int(text_width(t + " ", 9, bold=True))
        draw_text(cv, lx, bar_y + 7, rest, 9, WHITE, bold=True)

    # helper: location chip (top-left of art) + badge (bottom-right)
    def art_labels(ax, ay, aw, ah, n, badge_label):
        loc = "%d %s" % (n, LOCATIONS[n])
        tw = int(text_width(loc, 9, bold=True))
        cv.fill_rect(ax + 6, ay + 6, tw + 12, 16, INK)
        draw_text(cv, ax + 12, ay + 10, loc, 9, WHITE, bold=True)
        bw = int(text_width(badge_label, 9, bold=True)) + 10
        badge(cv, ax + aw - 6 - bw, ay + ah - 6 - 15, badge_label)

    # 3 lead cards (256 wide) + stat panel (218 wide), 234 tall
    ly = 142
    lw = 256
    lh = 234
    for i, st in enumerate(LEADS):
        bx = mx + i * (lw + 6)
        cv.rect(bx, ly, lw, lh, INK, 1)
        scene(cv, bx + 1, ly + 1, lw - 2, 108, st["scene"])
        art_labels(bx + 1, ly + 1, lw - 2, 108, st["n"], st["badge"])
        draw_text(cv, bx + 8, ly + 115, CATEGORIES[st["n"]], 10, RED, bold=True)
        _, nlines = block_fit(cv, bx + 8, ly + 130, st["head"], 22, INK,
                              lw - 16, 2, 25, bold=True)
        block_fit(cv, bx + 8, ly + 130 + nlines * 25 + 2, st["deck"], 12,
                  INK, lw - 16, 2, 15)
        draw_text(cv, bx + 8, ly + lh - 11, st["src"], 9, GREY, bold=True)

    # stat panel: dark "THE DAY IN NUMBERS", 6 rows x 34px
    px = mx + 3 * (lw + 6)
    pw = W - mx - px  # 218
    cv.fill_rect(px, ly, pw, lh, PANEL)
    draw_text_c(cv, px + pw // 2, ly + 8, "THE DAY IN NUMBERS", 12, WHITE,
                bold=True)
    for i, (num, label) in enumerate(STATS):
        ry = ly + 26 + i * 34
        cv.disc(px + 14, ry + 13, 7, RED)
        draw_text(cv, px + 14, ry + 9, str(STAT_STORIES[i]), 9, WHITE,
                  bold=True, align="c")
        draw_text(cv, px + 30, ry + 2, num, 25, RED, bold=True)
        lines = wrap(label, pw - 130, 9, bold=True)
        for j, ln in enumerate(lines[:2]):
            draw_text(cv, px + 124, ry + 4 + j * 11, ln, 9, WHITE, bold=True)

    # 10 small cards, 2 rows x 5, 164 tall, scene 58
    sw = 196
    sh = 164
    for row in range(2):
        for col in range(5):
            st = SMALL[row * 5 + col]
            bx = mx + col * (sw + 6)
            by = 384 + row * (sh + 8)
            cv.rect(bx, by, sw, sh, INK, 1)
            scene(cv, bx + 1, by + 1, sw - 2, 58, st["scene"])
            art_labels(bx + 1, by + 1, sw - 2, 58, st["n"], st["badge"])
            draw_text(cv, bx + 6, by + 64, CATEGORIES[st["n"]], 9, RED,
                      bold=True)
            _, nlines = block_fit(cv, bx + 6, by + 76, st["head"], 17, INK,
                                  sw - 12, 2, 20, bold=True)
            block_fit(cv, bx + 6, by + 76 + nlines * 20 + 2, st["deck"], 10,
                      INK, sw - 12, 3, 12)
            draw_text(cv, bx + 6, by + sh - 9, st["src"], 8, GREY, bold=True)

    # also-list header + badge legend (like #2, same line)
    ay = 728
    draw_text(cv, mx, ay, "ALSO ON MONDAY 23 NOVEMBER", 11, INK, bold=True)
    legend = [("CONFIRMED", "official / 2+ outlets"),
              ("CLAIM", "one side's claim"),
              ("REPORTED", "witnesses / one source"),
              ("PENDING", "not settled yet")]
    segs = []
    for word, desc in legend:
        bw = int(text_width(word, 9, bold=True)) + 10  # badge() width
        segs.append((word, desc, bw,
                     int(text_width(desc, 9))))
    total = sum(bw + 4 + dw for _, _, bw, dw in segs) + 10 * (len(segs) - 1)
    lx = W - mx - total
    for word, desc, bw, dw in segs:
        badge(cv, lx, ay, word)
        lx += bw + 4
        draw_text(cv, lx, ay + 2, desc, 9, GREY)
        lx += dw + 10

    # also-list: 3 columns x 8 rows, 11px, 13px pitch
    for i, (n, txt) in enumerate(ALSO):
        col = i // 8
        row = i % 8
        ax = mx + col * 338
        ay2 = 750 + row * 13
        draw_text(cv, ax, ay2, str(n) + ".", 11, RED, bold=True)
        draw_text(cv, ax + 28, ay2, txt, 11, INK)

    # date check (left) + map (right), side by side like #2
    dy = 862
    cv.rect(mx, dy, 660, 126, RED, 2)
    draw_text(cv, mx + 8, dy + 8, "DATE CHECK - READ THE DATES", 11, RED,
              bold=True)
    text_block(cv, mx + 8, dy + 28, DATECHECK, 11, INK, 644, 15)
    draw_text(cv, 682, dy, "WHERE IT HAPPENED", 11, INK, bold=True)
    draw_text(cv, W - mx - int(text_width("pins = story numbers", 9)), dy,
              "pins = story numbers", 9, GREY)
    draw_map(cv, 682, dy + 16, 332, 110)

    # footer (2 lines)
    draw_text(cv, mx, 994, "Sources: Reuters \u00b7 BBC \u00b7 AP \u00b7 CNN \u00b7 Al Jazeera \u00b7 AFP \u00b7 UN News \u00b7 ESPNcricinfo \u00b7 France 24 \u00b7 Guardian \u00b7 TWZ \u00b7 CNBC \u00b7 MEE", 9, GREY)
    draw_text(cv, mx, 1006, "Scenes are drawn illustrations of reported events, not photographs. Wires read to 23:00 UTC.", 9, GREY)
    return cv


def main():
    out = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out, exist_ok=True)
    cv = build()
    path = os.path.join(out, "entry.png")
    size = write_png(path, W, H, cv.px)
    print("wrote %s (%d bytes)" % (path, size))


if __name__ == "__main__":
    main()
