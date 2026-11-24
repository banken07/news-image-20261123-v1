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
# v7 (24 Nov, Ban order — date fix + 7 review points): a live audit
# (DATE-AUDIT.md) found 5 pictured cards were Sunday stories, so the
# pictured set was rebuilt from clean-Monday stories (Ahmadi, EU
# sanctions, Vanuatu, Belgium airports, Estonia warning); the 5 demoted
# stories moved to the also-list with (Sun) tags; DATE CHECK now names
# all 15 Earlier items; stat 258 -> 74 Ahmadi; timeline times yellow;
# map pins inset + de-clustered; also-list 10px; "#" in the stat discs.
# Same 35 stories, same region counts, same layout as v6.2.
# v8 (24 Nov, Ban order — top-3 structure, 28 stories, Left-out box):
# main list holds ONLY Monday stories (first-reported or developing Mon
# 23 Nov UTC): 13 pictured unchanged + 15 also-list (7 kept + 8 new
# Monday stories from V8-NEW-STORIES.md). The 15 non-Monday stories
# leave the also-list for a new box titled exactly "Left out because
# they happened on an earlier day", grouped by day with dates. Every
# also-list row carries a source + status badge (CONFIRMED/REPORTED/
# CLAIM, same legend as the pictured cards). DATE CHECK's first line is
# the strict rule + "Wires read to 23:00 UTC". Kicker "28 STORIES",
# region counts EUROPE 6 / MIDDLE EAST 6 / WORLD 6 / ASIA-PACIFIC 4 /
# AMERICAS 3 / OCEANIA 2 / AFRICA 1. Structure follows the 22 Nov top-3
# (rank 1 also-list rows carry region+source; rank 2 DATE CHECK holds
# the rule + left-out list; rank 3 two-column also-list) — layout only,
# never their wording.
# v12 (24 Nov, Ban order — 4 fixes on v11, preview only, do NOT submit):
# MAP: pin 4 SEOUL is GONE — story 4 is Wall St (USA), so the Seoul
# pin carried a wrong number (a Kospi-angle leftover from v7); no pin
# for story 4, per the brief. The four 1px clearances are widened to
# >=4px by moving neighbours, not just the labels: pin 12 nudges
# (dy2 -18 -> -22) and pin 10 up 1px (dy2 -6 -> -7) so ANTALYA's
# label (dy -6 -> -4) clears the Brussels pin by 4px and the
# BRUSSELS label by 4px, and the BRUSSELS label clears pin 12 by
# 4.4px (pin 12's disc top sits exactly on the map's top edge); pin 2
# (Benghazi) down 2px (dy2 10 -> 12) so ANTALYA clears it by 4px; BAHRAIN label drops
# (dy 10 -> 16) and steps out (gap 6 -> 10) to clear pin 2 by 5px and
# the BENGHAZI label by 4px; CIKANDE label up (dy -4 -> -6) to clear
# the Vanuatu pin by 4px; VANUATU label down (dy 2 -> 5) to clear the
# Cikande pin by 4px and WELLINGTON (dy 6 -> 8) by 6px; Moscow pin
# down 2px (dy2 -10 -> -12) so the KYIV label clears it by 5px.
# STATS: "DEAD IN DYMER" -> "DYMER TOLL" (story 3 never states 11
# deaths in the image; the label now matches the headline wording).
# DATE CHECK: left-out rows pitch 13 -> 15px, name-to-day gap one
# space -> explicit 6px. ALSO-LIST: pitch 30 -> 31px, desc 10 ->
# 10.5px at +15 (was +14); footer Sources 9 -> 9.5px. No rasterizer
# change: glyphs already render at 4x supersampling + alpha blend, so
# the legibility gain is leading + size, as briefed.

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
YELLOW = (255, 210, 63)
SKY = (127, 179, 213)
OCEAN = (39, 75, 99)
LAND = (232, 219, 184)
WHITE = (255, 255, 255)
CREAM = (240, 230, 210)
BROWN = (122, 74, 33)
PURPLE = (91, 91, 122)
DARK = (20, 20, 28)

# v9: region colours SAMPLED from the 22 Nov #2 edition's kicker chips
# (median of each chip's solid interior, 1024x1024 reference):
# EUROPE #184a87, MIDDLE EAST #a82820, ASIA #b85018, AFRICA #287838,
# AMERICAS #684088, OCEANIA #087878, WORLD #404048. One colour per
# region, used consistently in the kicker chips, the card category
# labels, and the map pins. (Note: #2's own category labels sampled
# GREY — Ban's brief explicitly orders them region-coloured instead.)
REG_BLUE = (24, 74, 135)
REG_RED = (168, 40, 32)
REG_ORANGE = (184, 80, 24)
REG_GREEN = (40, 120, 56)
REG_PURPLE = (104, 64, 136)
REG_TEAL = (8, 120, 120)
REG_GREY = (64, 64, 72)
# v9 stat-number colours: #2's panel numbers sampled as soft pastels on
# dark navy — 186 gold, 14 salmon, 98.37% light blue, 720/9 light
# green, 24 lavender; 6th stat (we have 6) gets pink, same family.
STAT_GOLD = (232, 192, 112)
STAT_SALMON = (216, 144, 128)
STAT_SKY = (144, 176, 224)
STAT_MINT = (144, 208, 160)
STAT_LAV = (200, 176, 224)
STAT_PINK = (240, 160, 168)
# v9 UTC-bar time colours: #2's times sampled as soft pastels on black
# (light blue, lavender, gold, pink, green); brightened slightly for
# contrast on the black bar.
TIME_BLUE = (140, 176, 228)
TIME_LAV = (178, 137, 203)
TIME_GOLD = (238, 201, 95)
TIME_PINK = (223, 164, 168)
TIME_GREEN = (159, 200, 166)
# v10: COP31's 14:48 is the IPS first-filing time (see V10-SOURCES.md
# §1b) — a distinct pastel orange so it reads as its own event.
TIME_ORANGE = (240, 170, 110)

REGION_COLORS = [
    ("EUROPE", REG_BLUE),
    ("MIDDLE EAST", REG_RED),
    ("ASIA-PACIFIC", REG_ORANGE),
    ("AMERICAS", REG_PURPLE),
    ("AFRICA", REG_GREEN),
    ("OCEANIA", REG_TEAL),
    ("WORLD", REG_GREY),
]

# v9: badge colours follow #2's legend — CONFIRMED green, CLAIM gold,
# REPORTED orange, PENDING grey (was CLAIM red, REPORTED amber).
BADGE_COLORS = {
    "CONFIRMED": GREEN,
    "REPORTED": ORANGE,
    "CLAIM": GOLD,
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
             track=0.0, serif=False, font=None, xscale=1.0):
        """Draw text; (x, y) is the baseline point (left/centre/right by
        align). Real serif glyphs from the embedded outlines; bold selects
        the bold face. `serif` is accepted for compatibility and ignored:
        all text is serif now. Slant shears the outlines (fake italic).
        `font` overrides the face id. `xscale` horizontally condenses
        the text (1.0 = natural); only the masthead uses it."""
        s = norm(s)
        w = text_width(s, size, bold, track, font, xscale)
        if align == "c":
            x -= w / 2.0
        elif align == "r":
            x -= w
        fid = font or ("B" if bold else "R")
        for ch in s:
            if ch == " ":
                x += _advance(" ", size, bold, font, xscale) + track
                continue
            bm = _glyph_bitmap(fid, ch, size, slant, xscale)
            if bm is not None:
                self._blit_text(x, y, bm, c)
            x += _advance(ch, size, bold, font, xscale) + track

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
# v6: the face is Liberation Serif (regular + bold), extracted on the
# build machine with fontTools (~/workspace/makefun/news-image-20261123/
# extract_lib.py) and embedded below as a zlib-compressed blob (base64).
# Same record format as the 22 Nov DejaVu blob it replaces (fid, code,
# advance, bbox, x,y,on contours); the dead "L" face (17 DejaVu glyphs
# spelling the 22 Nov masthead) was dropped — nothing in this entry
# ever selected it. At runtime the program rasterizes the outlines with
# a pure-stdlib scanline filler + 4x supersampling, so the entry needs
# no font files and no third-party library. No PIL path is used (the
# embedded outlines are the only path — local, python3 -S and grader
# renders must all be byte-identical); verify renders with `python3 -S`.
# The masthead is drawn with xscale 0.845: #2's masthead measures
# condensed (~0.84x Liberation Bold at the same cap height — 1000px
# wide at a 67px cap, where natural Liberation Bold would be ~1200px),
# so the condense reproduces #2's rendered masthead geometry.
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


def _advance(ch, size, bold, font=None, xscale=1.0):
    fid = font or ("B" if bold else "R")
    entry = FONTS[fid].get(ch)
    if entry is None:
        return 0.0
    return entry[0] * size / UPM * xscale


def text_width(text, size, bold=False, track=0.0, font=None, xscale=1.0):
    text = norm(text)
    return sum(_advance(c, size, bold, font, xscale) + track for c in text)


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


def _flatten_contour(contour, scale, slant, xscale=1.0):
    """TrueType quadratic outline -> polyline in supersampled screen
    coords (y down, origin at the pen position on the baseline).
    xscale horizontally condenses the outline (1.0 = natural width);
    only the masthead uses it, to reproduce #2's condensed masthead."""
    s = scale * SS
    pts = [((x * xscale + slant * y) * s, -y * s, on) for (x, y, on) in contour]
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


def _rasterize(font_id, ch, size, slant, xscale=1.0):
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
    polys = [_flatten_contour(c, scale, slant, xscale) for c in contours]
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


def _glyph_bitmap(font_id, ch, size, slant, xscale=1.0):
    key = (font_id, ch, size, slant, xscale)
    bm = _GLYPH_CACHE.get(key)
    if bm is None:
        # Embedded outlines only: the PIL path renders different pixels
        # (22 Nov file: PIL 251,468 B vs embedded 175,531 B), so it is
        # deliberately not used — local, python3 -S and grader renders
        # must all be byte-identical.
        bm = _rasterize(font_id, ch, size, slant, xscale)
        _GLYPH_CACHE[key] = bm
    return bm



# ---------------------------------------------------------------- text adapters
# draw_text takes (x, y) = top-left of the INK box (not the baseline):
# the baseline is computed from the actual glyph bboxes, so tops are exact
# for caps, lowercase and mixed text alike.

def _ink_top(s, size, bold=False, slant=0.0, font=None, xscale=1.0):
    """Pixels from the top of the ink box to the baseline (negative)."""
    top = None
    fid = font or ("B" if bold else "R")
    for ch in norm(s):
        if ch == " ":
            continue
        bm = _glyph_bitmap(fid, ch, size, slant, xscale)
        if bm is None:
            continue
        if top is None or bm[4] < top:
            top = bm[4]
    if top is None:
        top = -int(round(0.655 * size))
    return top


def draw_text(cv, x, y, s, size, color, bold=False, align="l", slant=0.0,
              track=0.0, xscale=1.0):
    """Draw text; (x, y) is the top-left of the ink box."""
    baseline = y - _ink_top(s, size, bold, slant, xscale=xscale)
    cv.text(x, baseline, s, size, color, bold=bold, align=align,
            slant=slant, track=track, xscale=xscale)


def draw_text_c(cv, cx, y, s, size, color, bold=False, slant=0.0, track=0.0,
                xscale=1.0):
    draw_text(cv, cx, y, s, size, color, bold=bold, align="c",
              slant=slant, track=track, xscale=xscale)


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
# v7: pins follow the new pictured set (renumbered). Tuple:
# (story, lon, lat, label or None, label side, label dy, pin dx, pin dy,
#  label gap). dx/dy nudge a pin in screen px where the coarse map would
# stack two discs — every pair is now >=13px apart (measured, see
# EVALUATION.md). label gap (v10) pushes a label a few px further from
# its pin so a thin leader line can connect them (see draw_map); SEOUL
# still has gap 0 (it would run past the map's right edge). v11: KYIV
# gets gap 4 (Ban order — leader line for Kyiv) and the Qom pin nudges
# +6px east (dx 24 -> 30) so the KYIV label clears its disc by 2px.
# (KYIV is boxed in by pins 5/13, so the gap stays small.)
# v12: pin 4 (SEOUL) REMOVED — story 4 is Wall St (USA); the Seoul
# pin was a Kospi-angle leftover carrying a wrong number. Neighbour
# moves (see the v12 header comment): pin 12 further NW, pin 10 up
# 1px, pin 2 down 2px, Moscow pin down 2px; ANTALYA dy -4, BAHRAIN
# dy 16 + gap 10, CIKANDE dy -6, VANUATU dy 5, WELLINGTON dy 8.
# v13 (Ban: MORE breathing room — worst clearance 4.0 -> >= 6.0):
# Europe/Med cluster spread by moving pins AND labels together:
# pin 10 east+up (dx -6 -> +2, dy2 -7 -> -9) and pin 12 east
# (dx -16 -> -12) so the two Brussels discs stay >= 6px apart; pin 2 down (dy2 12 -> 16)
# v14 (Ban: do NOT just regenerate the same image — make the fixes
# VISIBLY obvious at 1x, not just probe-measurable): every label
# pushed decisively outward into open space with longer leader
# lines; worst clearances 6.0px -> >=10px (probe /tmp/v14_geom.py).
# Europe/Med, paired pin+label moves: BRUSSELS gap 16 -> 26 (far
# west into the Atlantic; clears pin 12 by 14.6px); ANTALYA gap
# 6 -> 32, dy -2 -> +2 (south-west into the Med; clears pin 2 by
# 10.3px, BRUSSELS label by 12px); BENGHAZI pin south-west (dx -13
# -> -20, dy2 16 -> 20) + label dy 13 -> 20 (clears BAHRAIN label
# by 18px); KYIV gap 8 -> 9, dy 12 -> 11 (its 27px label only fits
# the corridor once Qom moves east — see below); Qom pin east dx
# 38 -> 46 (schematic map, precedent set v11/v12; KYIV label now
# clears it by 15px); BAHRAIN pin south dy2 8 -> 12 + label dy
# 22 -> 30, gap 10 -> 9 (clears pin 2 by 11.7px); Moscow pin up
# dy2 -14 -> -15 (KYIV label clears it by 11px). Pacific: CIKANDE
# pin north dy2 0 -> -8 + label gap 6 -> 12 (clears own pin by
# 13px, Vanuatu pin by 15px); VANUATU label gap 6 -> 10, dy 8 -> 3
# (clears Cikande pin by 10.0px, WELLINGTON label by 11px, own pin
# by 11.1px); WELLINGTON gap 6 -> 10 (clears own pin by 12.9px).
# No Seoul pin (story 4 is Wall St). All pin numbers still match
# their story numbers.
MAP_PINS = [
    (1, 31.0, 37.5, "ANTALYA", -1, 2, -3, 3, 32),
    (2, 18.0, 33.0, "BENGHAZI", -1, 20, -20, 20, 6),
    (3, 30.5, 50.5, "KYIV", 1, 11, -2, -8, 9),
    (5, 50.9, 34.6, None, 1, 0, 46, -5),
    (6, 52.5, 27.5, "BAHRAIN", -1, 30, 18, 12, 9),
    (7, -122.0, 37.4, None, 1, 0, 0, 0),
    (8, 106.5, -7.0, "CIKANDE", 1, -9, 0, -8, 12),
    (9, 174.5, -41.0, "WELLINGTON", -1, 11, 0, 0, 10),
    (10, 4.35, 50.85, "BRUSSELS", -1, 0, 2, -9, 26),
    (11, 167.0, -16.0, "VANUATU", -1, 3, -10, 3, 10),
    (12, 4.35, 50.85, None, 1, 0, -12, -22),
    (13, 37.6, 55.75, None, 1, 0, 14, -15),
]


def _lonlat(x, y, w, h, lon, lat):
    # v7: inset the geo rect by 8px left/right, 4px top/bottom so edge
    # pins (Wellington, lon 174.5) sit inside the map with margin.
    px = x + 8 + int((lon + 180.0) / 360.0 * (w - 16))
    py = y + 4 + int((85.0 - lat) / 145.0 * (h - 8))
    return px, py


def draw_map(cv, x, y, w, h):
    cv.fill_rect(x, y, w, h, OCEAN)
    for poly in LAND_POLYS:
        pts = [_lonlat(x, y, w, h, lon, lat) for lon, lat in poly]
        cv.poly(pts, LAND)
    for num, lon, lat, label, side, *rest in MAP_PINS:
        dy = rest[0] if len(rest) > 0 else 0
        dx = rest[1] if len(rest) > 1 else 0
        dy2 = rest[2] if len(rest) > 2 else 0
        gap = rest[3] if len(rest) > 3 else 0
        px, py = _lonlat(x, y, w, h, lon, lat)
        px += dx
        py += dy2
        # v9: pins coloured by the story's region (same palette as the
        # kicker chips and card categories), white ring + white number.
        cv.disc(px, py, 6, dict(REGION_COLORS)[REGION_OF[num]])
        cv.ring(px, py, 6, WHITE, 1)
        s = str(num)
        draw_text(cv, px - int(text_w(s, 9, bold=True)) // 2, py - 3, s, 9, WHITE, bold=True)
        if label:
            tw = int(text_w(label, 9, bold=True))
            # v10: the label sits `gap` px further from its pin (Ban:
            # tidy the Brussels/Antalya/Kyiv and Wellington/Vanuatu
            # labels with leader lines). v11: KYIV has gap 4 (leader
            # line drawn; Qom pin nudged east so the label clears it).
            # v12: the SEOUL pin is gone (story 4 is Wall St), so no
            # label runs past the map's right edge any more.
            lx = px + 9 + gap if side > 0 else px - 9 - tw - gap
            ly = py - 3 + dy
            # thin leader line (garis penunjuk) from the pin disc to
            # the label rect — only where the gap exceeds the disc edge
            # by >2px; drawn before the label rect so the rect covers
            # the line end.
            rx0, ry0, rx1, ry1 = lx - 2, ly - 2, lx + tw + 2, ly + 9
            nx = min(max(px, rx0), rx1)
            ny = min(max(py, ry0), ry1)
            ddx, ddy = nx - px, ny - py
            dd = (ddx * ddx + ddy * ddy) ** 0.5
            if dd > 8:
                ux, uy = ddx / dd, ddy / dd
                cv.line(int(px + 7 * ux), int(py + 7 * uy),
                        int(nx), int(ny), INK)
            cv.fill_rect(lx - 2, ly - 2, tw + 4, 11, PAPER)
            draw_text(cv, lx, ly, label, 9, INK, bold=True)


# ---------------------------------------------------------------- self-made flags
# v9: simplified country flags drawn from scratch in the flat-vector
# style (2-3 shapes each, 16x11px + 1px border). Never copied from #2's
# flag drawings — these are my own simplifications of the real flags.
FLAG_BLUE = (30, 80, 160)
FLAG_RED = (200, 30, 30)
FLAG_GREEN = (0, 130, 60)
FLAG_SAFFRON = (255, 153, 51)
FLAG_NAVY = (30, 30, 120)
FLAG_GOLD = (255, 210, 63)
FLAG_BORDER = (90, 90, 90)


def draw_flag(cv, x, y, code):
    """Draw a simplified 16x11 flag for `code` at (x, y)."""
    w, h = 16, 11
    if code == "RU":  # white-blue-red horizontal
        cv.fill_rect(x, y, w, 4, WHITE)
        cv.fill_rect(x, y + 4, w, 3, FLAG_BLUE)
        cv.fill_rect(x, y + 7, w, 4, FLAG_RED)
    elif code == "MX":  # green-white-red vertical
        cv.fill_rect(x, y, 5, h, FLAG_GREEN)
        cv.fill_rect(x + 5, y, 6, h, WHITE)
        cv.fill_rect(x + 11, y, 5, h, FLAG_RED)
    elif code == "EU":  # blue + ring of yellow dots
        cv.fill_rect(x, y, w, h, REG_BLUE)
        import math as _m
        for k in range(5):
            a = _m.radians(90 + k * 72)
            cv.disc(x + 8 + int(3 * _m.cos(a)), y + 5 + int(3 * _m.sin(a)),
                    1, FLAG_GOLD)
    elif code == "CD":  # blue + red diagonal + yellow disc
        cv.fill_rect(x, y, w, h, (0, 90, 180))
        for d in (-1, 0, 1):
            cv.line(x + d, y + h - 1, x + w - 1 + d, y, FLAG_RED)
        cv.disc(x + 8, y + 5, 2, FLAG_GOLD)
    elif code == "PS":  # black-white-green + red triangle at hoist
        cv.fill_rect(x, y, w, 4, (20, 20, 20))
        cv.fill_rect(x, y + 4, w, 3, WHITE)
        cv.fill_rect(x, y + 7, w, 4, FLAG_GREEN)
        cv.poly([(x, y), (x + 6, y + 5), (x, y + h - 1)], FLAG_RED)
    elif code == "UN":  # light blue + white disc
        cv.fill_rect(x, y, w, h, (110, 170, 215))
        cv.disc(x + 8, y + 5, 3, WHITE)
    elif code == "KR":  # white + red/blue taegeuk (two offset discs)
        cv.fill_rect(x, y, w, h, WHITE)
        cv.disc(x + 7, y + 4, 2, FLAG_RED)
        cv.disc(x + 9, y + 6, 2, (30, 60, 160))
    elif code == "IN":  # saffron-white-green + navy disc
        cv.fill_rect(x, y, w, 4, FLAG_SAFFRON)
        cv.fill_rect(x, y + 4, w, 3, WHITE)
        cv.fill_rect(x, y + 7, w, 4, (19, 136, 8))
        cv.disc(x + 8, y + 5, 1, FLAG_NAVY)
    elif code == "ID":  # red over white
        cv.fill_rect(x, y, w, 5, FLAG_RED)
        cv.fill_rect(x, y + 5, w, 6, WHITE)
    elif code == "US":  # stripes + blue canton
        for i in range(4):
            cv.fill_rect(x, y + i * 3, w, 2 if i < 3 else 2,
                         FLAG_RED if i % 2 == 0 else WHITE)
        cv.fill_rect(x, y, 7, 6, (30, 50, 120))
        cv.disc(x + 2, y + 2, 1, WHITE)
        cv.disc(x + 5, y + 4, 1, WHITE)
    elif code == "IR":  # green-white-red horizontal
        cv.fill_rect(x, y, w, 4, FLAG_GREEN)
        cv.fill_rect(x, y + 4, w, 3, WHITE)
        cv.fill_rect(x, y + 7, w, 4, FLAG_RED)
    else:
        cv.fill_rect(x, y, w, h, GREY)
    cv.rect(x, y, w, h, FLAG_BORDER, 1)


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
        # v10: redrawn to read at a glance — darker teal hall, 2 rows
        # of bright windows, a big ruled document with a BOLD red X
        # (the rejected pact), a long table with delegate silhouettes
        # at the sides. (v9's version was a small crossed-out doc that
        # read as a generic building.)
        cv.fill_rect(x, y, w, h, (0, 96, 96))
        for row in range(2):
            for col in range(6):
                cv.fill_rect(X(12 + col * 50), y + 8 + row * 12,
                             int(34 * w / 322), 8, CREAM)
        # long conference table + delegate silhouettes at the sides
        cv.fill_rect(x + 8, y + h - 24, w - 16, 10, (60, 45, 30))
        for sx in (16, 40, w - 54, w - 30):
            cv.fill_rect(x + sx, y + h - 36, 14, 12, (35, 35, 35))
        # big white document, ruled lines, bold red X (3 strokes each way)
        dw, dh = 84, 42
        dx0 = x + w // 2 - dw // 2
        dy0 = y + 32
        cv.fill_rect(dx0, dy0, dw, dh, WHITE)
        for rl in range(3):
            cv.fill_rect(dx0 + 9, dy0 + 9 + rl * 8, dw - 18, 2, GREY)
        for off in (-1, 0, 1):
            cv.line(dx0 + 7 + off, dy0 + 5, dx0 + dw - 7 + off, dy0 + dh - 5, RED)
            cv.line(dx0 + 7 + off, dy0 + dh - 5, dx0 + dw - 7 + off, dy0 + 5, RED)
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
        for sx, sy in ((152, 8), (172, 12), (162, 20)):
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
    elif kind == "ahmadi":
        # v7: microphone on a stand, dark background (non-graphic).
        cv.fill_rect(x, y, w, h, DARK)
        cx = x + w // 2
        cv.disc(cx, y + 16, 9, LIGHT)
        cv.hline(cx - 8, y + 12, 16, GREY)
        cv.hline(cx - 8, y + 16, 16, GREY)
        cv.hline(cx - 8, y + 20, 16, GREY)
        cv.vline(cx, y + 26, h - 32, GREY)
        cv.fill_rect(cx - 12, y + h - 6, 24, 4, GREY)
        cv.disc(x + 22, y + 40, 3, GOLD)
        cv.disc(x + w - 22, y + 20, 3, GOLD)
    elif kind == "eusanctions":
        # v7: EU circle of stars (right, clear of the location chip and
        # the badge) + bank building (left, below the chip).
        cv.fill_rect(x, y, w, h, NAVY)
        import math
        for k in range(12):
            a = math.radians(k * 30)
            _star(cv, x + 165 + int(12 * math.cos(a)),
                  y + 18 + int(12 * math.sin(a)), 2, GOLD)
        cv.tri(x + 6, y + 36, x + 104, y + 36, x + 55, y + 24, GREY)
        cv.fill_rect(x + 10, y + 36, 90, h - 36, LIGHT)
        for ccx in (20, 45, 70):
            cv.fill_rect(x + ccx, y + 40, 6, h - 46, WHITE)
        cv.fill_rect(x + 10, y + h - 6, 90, 4, WHITE)
    elif kind == "vanuatu":
        # v7: island + seismic wave rings above it.
        cv.fill_rect(x, y, w, h, OCEAN)
        for r in (5, 10, 15):
            cv.ring(x + 95, y + 20, r, WHITE, 1)
        cv.poly([(x + 20, y + h), (x + 40, y + 30), (x + 70, y + 22),
                 (x + 110, y + 28), (x + 150, y + 40), (x + 170, y + h)],
                GREEN)
        cv.hline(x + 30, y + h - 8, 50, WHITE)
        cv.hline(x + 110, y + h - 6, 50, WHITE)
    elif kind == "belgium":
        # v7: control tower (left, top below the location chip) +
        # grounded plane (centre, clear of the badge).
        cv.fill_rect(x, y, w, h, SKY)
        cv.fill_rect(x, y + h - 6, w, 4, (60, 60, 60))
        cv.fill_rect(x + 19, y + 22, 20, 10, DARK)
        cv.fill_rect(x + 24, y + 32, 10, h - 38, GREY)
        cv.fill_rect(x + 60, y + 42, 60, 8, WHITE)
        cv.tri(x + 60, y + 42, x + 60, y + 30, x + 70, y + 42, WHITE)
        cv.fill_rect(x + 82, y + 32, 10, 20, WHITE)
    elif kind == "estonia":
        # v7: border post (left, striped) + Estonian flag (right).
        cv.fill_rect(x, y, w, h, SKY)
        cv.fill_rect(x, y + 44, w, h - 44, GREEN)
        cv.fill_rect(x + 40, y + 24, 8, 28, WHITE)
        cv.fill_rect(x + 40, y + 30, 8, 6, RED)
        cv.fill_rect(x + 40, y + 40, 8, 6, RED)
        cv.vline(x + 140, y + 12, 34, DARK)
        cv.fill_rect(x + 140, y + 12, 30, 7, (0, 114, 206))
        cv.fill_rect(x + 140, y + 19, 30, 7, DARK)
        cv.fill_rect(x + 140, y + 26, 30, 7, WHITE)


# ---------------------------------------------------------------- content
# v4: same 35 stories, same figures, same sources as v3.1 (STORY-LIST.md).
# Only the CASING changed to match the 22 Nov reference typography:
# masthead/subhead/decks/also-list/DATE CHECK in sentence case, heads and
# labels in caps. Wording is otherwise identical.
MASTHEAD = "Monday 23 November 2026"
SUBHEAD = "COP31 collapses \u2014 no deal \u00b7 Merkury sunk off Libya \u00b7 Dymer toll rises to 11"
TOPLINE = "THE WORLD IN ONE DAY \u00b7 26 STORIES \u00b7 7 REGIONS \u00b7 PRESS TIME 23:00 UTC \u00b7 EVERY STORY DATED MONDAY 23 NOVEMBER 2026"

# Timeline: verified times only (see STORY-LIST.md, V10-SOURCES.md §1).
# (minutes from 00:00 UTC, label, label above the bar?, time-word
# colour). v10: "Morning" is now the definite "05:23" (Dymer toll 11:
# Tkachenko Telegram 07:23 Kyiv local = 05:23 UTC, corroborated by the
# Reuters wire timestamped 06:24 UTC already carrying "kills 11"); the
# same chronology confirms the 01:28 UTC rescue. COP31 gets "14:48" —
# the IPS first-filing time (14:48:44 UTC Sun); HONEST CAVEAT: no exact
# plenary hour was established (Guardian "Sunday afternoon", AP "ended
# Sunday night"), so 14:48 is the first-report time, NOT the plenary
# time — do not present it as the plenary hour.
# v9: black bar, bright per-event time colours sampled from #2's UTC bar
# (light blue, lavender, gold, pink, green pastels on black).
# v11: the list is CHRONOLOGICAL by UTC hour (Ban order) — the bar
# draws one even slot per entry in list order, so list order IS the
# left-to-right order: 01:28, 02:40, 05:23, 14:48, 21:00, 23:00.
TIMELINE = [
    (88, "01:28 Dymer rescue", False, TIME_BLUE),
    (160, "02:40 Vanuatu", True, TIME_LAV),
    (323, "05:23 Dymer toll 11", False, TIME_GOLD),
    (888, "14:48 COP31 collapses", True, TIME_ORANGE),
    (1260, "21:00 S&P +4.7%", True, TIME_PINK),
    (1380, "23:00 Press time", False, TIME_GREEN),
]

# v9: each stat number gets its own colour (sampled from #2's panel:
# gold, salmon, light blue, light green, lavender, + pink for the 6th).
STATS = [
    ("60", "BANKS IN EU SANCTIONS PLAN", STAT_GOLD),
    ("74", "LASHES FOR SINGER AHMADI", STAT_SALMON),
    ("+4.7%", "S&P 500 RISE ON MONDAY (AP)", STAT_SKY),
    ("11", "DYMER TOLL", STAT_MINT),
    ("24", "DEAD IN CIKANDE FIRE", STAT_LAV),
    ("720/9", "INDIA TOTAL IN WELLINGTON", STAT_PINK),
]

LEADS = [
    {"n": 1, "badge": "CONFIRMED", "scene": "cop31",
     "head": "COP31 COLLAPSES: NO DEAL",
     "deck": "Pact rejected; Guterres 'deeply disappointed'.",
     "src": "UN NEWS \u00b7 BBC \u00b7 CNN"},
    {"n": 2, "badge": "REPORTED", "scene": "merkury",
     "head": "MERKURY SINKS OFF LIBYA",
     "deck": "Zelensky: 7 sea drones hit; Ka-27 destroyed.",
     "src": "AP \u00b7 CNN \u00b7 TWZ"},
    {"n": 3, "badge": "CONFIRMED", "scene": "dymer",
     "head": "DYMER TOLL RISES TO 11",
     "deck": "Boy, 7, pulled alive; woman, 79, rescued too.",
     "src": "REUTERS \u00b7 BBC"},
]

SMALL = [
    {"n": 4, "badge": "CONFIRMED", "scene": "markets",
     "head": "WALL ST ROARS BACK",
     # v11 (Ban order): the index level is OUT — "+4.7% (AP)" only.
     "deck": "S&P +4.7% (AP); Nasdaq +6.5%.",
     "src": "AP"},
    {"n": 5, "badge": "CONFIRMED", "scene": "ahmadi",
     "head": "IRAN FLOGS SINGER AHMADI",
     "deck": "74 lashes in Qom; 4 band members too.",
     "src": "REUTERS \u00b7 CNN"},
    {"n": 6, "badge": "REPORTED", "scene": "hormuz",
     "head": "TANKERS ABLAZE AT HORMUZ",
     "deck": "Blockade day 130; tankers keep burning.",
     "src": "AL JAZEERA \u00b7 AP"},
    {"n": 7, "badge": "CONFIRMED", "scene": "nvidia",
     "head": "HUANG BACK AT NVIDIA",
     "deck": "Board reverses; shares +31% Monday.",
     "src": "CNN \u00b7 REUTERS"},
    {"n": 8, "badge": "CONFIRMED", "scene": "cikande",
     "head": "CIKANDE FIRE: 24 DEAD",
     "deck": "Toll confirmed Monday; 30 still missing.",
     "src": "REUTERS"},
    {"n": 9, "badge": "CONFIRMED", "scene": "cricket",
     "head": "1ST TEST ENDS IN A DRAW",
     "deck": "India 720/9 dec; NZ 239/5, Mitchell 49*.",
     "src": "ESPNCRICINFO"},
    {"n": 10, "badge": "PENDING", "scene": "eusanctions",
     "head": "EU PROPOSES 22ND RUSSIA SANCTIONS",
     "deck": "60 banks off SWIFT; needs all 27.",
     "src": "AP \u00b7 EC"},
    {"n": 11, "badge": "CONFIRMED", "scene": "vanuatu",
     "head": "VANUATU SHAKEN BY M6.5 QUAKE",
     "deck": "M6.5 at 02:40 UTC; no tsunami threat.",
     "src": "USGS"},
    {"n": 12, "badge": "CONFIRMED", "scene": "belgium",
     "head": "BELGIUM AIRPORTS SHUT BY STRIKE",
     "deck": "Flights grounded; about 59,500 affected.",
     "src": "SKEYES \u00b7 BRUSSELS AIRPORT"},
    {"n": 13, "badge": "CONFIRMED", "scene": "estonia",
     "head": "RUSSIA WARNS ESTONIA OVER BORDER",
     "deck": "Moscow: closure 'verge of open war'.",
     "src": "REUTERS"},
]

ALSO = [
    # v9: 13 items, ALL Monday (first-reported or developing Mon 23 Nov
    # UTC) — v8's 15 minus Marquez (thin Developing) and Cucuta drones
    # (weakest news weight). Each row: (number, bold title, 1-line grey
    # description, source, self-made flag code). No badge chips on rows
    # (per #2's system; the badge legend stays in the header).
    (14, "Sparta II towed out", "Arrived St Petersburg on Monday", "Reuters", "RU"),
    # v10: renamed to the Monday news (Reuters headline, opened live:
    # "US extradition order exists for arrested Mexican drug lord 'El
    # Chapo Isidro'"). The capture was Fri night; the Monday story is
    # the extradition order. Description follows the Reuters wording.
    (15, "US extradition order for El Chapo", "Harfuch: order exists; captured over weekend", "Reuters", "MX"),
    (16, "BepiColombo in orbit", "ESA reports safe-mode anomaly Monday", "ESA", "EU"),
    (17, "DR Congo: Ebola fighting", "Fighting near hospital; staff sheltered", "UN News", "CD"),
    (18, "Gaza contamination", "Oxfam: >99% of Gaza contaminated", "Oxfam", "PS"),
    (19, "Gaza: 3 dead incl UNRWA", "UNRWA worker killed near Jabalia", "Reuters", "UN"),
    # v10: description reworded to the confirmed core — the "60 days"
    # line was in the German-media report per V8 but NOT in the visible
    # excerpt of the opened Reuters article (see V10-SOURCES.md §5).
    (20, "Russia readies nuclear satellite", "NATO: Russia plans nuclear-armed launch this year", "Reuters", "RU"),
    (21, "Seoul reshuffles cabinet", "First woman nominated as spy chief", "Reuters", "KR"),
    (22, "India gives Nepal $1.62bn package", "$1.62bn package announced Monday", "Reuters", "IN"),
    # v11 (Ban order): name the country in the description.
    (23, "Prabowo names two VP candidates", "Two ministers named as VP candidates in Indonesia", "Reuters", "ID"),
    (24, "US blacklists Megaspeed", "US bars AI chip sales to Singapore firm", "WSJ", "US"),
    (25, "US sanctions 30 Iran entities", "30 entities in shadow-banking network", "Treasury", "IR"),
    (26, "Guterres calls for AI safety pact", "Calls for multilateral AI safety talks", "UN News", "UN"),
]

# v9: the 15 non-Monday stories for the DATE CHECK 3-column left-out
# list — flat (name, red date), reading order Sun -> Sat -> Fri ->
# Thu 19 Nov -> Mon 16 Nov, 5 per column. Same items as v8.
LEFTOUT = [
    ("Democrats", "Sun"), ("Houthis", "Sun"), ("Sudan", "Sun"),
    ("Liverpool", "Sun"), ("Alcaraz", "Sun"), ("Netanyahu", "Sun"),
    ("Istanbul", "Sun"), ("South Sudan", "Sat"), ("Bolsonaro", "Sat"),
    ("West Bank", "Sat"), ("Boca", "Sat 14 Nov"), ("Poland plot", "Fri"),
    ("Riemann", "Fri"), ("Trump/Putin", "Thu 19 Nov"),
    ("Nepal", "Mon 16 Nov"),
]

# v9: DATE CHECK — first line is the strict rule + wire-read time; the
# "not in this image" clause and the Kospi/Hang Seng intraday note are
# DROPPED (per #2's system — the left-out list carries the dating
# honesty now). The rule is drawn bold (see build()).
DATECHECK_RULE = ("RULE: Every story in this image happened, or was first reported, "
    "on Monday 23 November 2026 (UTC). Wires read to 23:00 UTC.")


# ---------------------------------------------------------------- layout (v5)
# v5 data: location chips + category lines for the 13 pictured cards
# (like #2's "1 ANTALYA, TÜRKIYE" chips and "WORLD · CLIMATE" lines),
# region counts for the kicker chips (verified in the cancelled v5 brief,
# total 35), and the story number each stat comes from (like #2's small
# circled numbers in its stat panel: 60->10 EU sanctions, 74->5 Ahmadi,
# +4.7%->4 markets, 11->3 Dymer, 24->8 Cikande, 720/9->9 cricket).
LOCATIONS = {
    1: "ANTALYA, TURKIYE", 2: "BENGHAZI, LIBYA", 3: "DYMER, UKRAINE",
    4: "WALL ST, USA", 5: "QOM, IRAN", 6: "STRAIT OF HORMUZ",
    7: "SANTA CLARA, USA", 8: "CIKANDE, INDONESIA", 9: "WELLINGTON, NZ",
    10: "BRUSSELS, BELGIUM", 11: "VANUATU",
    12: "BRUSSELS, BELGIUM", 13: "MOSCOW, RUSSIA",
}
CATEGORIES = {
    1: "WORLD · CLIMATE", 2: "MIDDLE EAST · WAR", 3: "EUROPE · WAR",
    4: "WORLD · MARKETS", 5: "MIDDLE EAST · RIGHTS", 6: "MIDDLE EAST · WAR",
    7: "AMERICAS · MARKETS", 8: "ASIA-PACIFIC · DISASTER",
    9: "OCEANIA · CRICKET", 10: "EUROPE · SANCTIONS", 11: "OCEANIA · QUAKE",
    12: "EUROPE · TRAVEL", 13: "EUROPE · DIPLOMACY",
}
REGION_COUNTS = [("EUROPE", 5), ("MIDDLE EAST", 6), ("WORLD", 6),
                 ("ASIA-PACIFIC", 4), ("AMERICAS", 2), ("OCEANIA", 2),
                 ("AFRICA", 1)]
STAT_STORIES = [10, 5, 4, 3, 8, 9]

# v9: region of every story (drives the card category colour and the
# map pin colour — one colour per region, used consistently).
REGION_OF = {
    1: "WORLD", 2: "MIDDLE EAST", 3: "EUROPE", 4: "WORLD",
    5: "MIDDLE EAST", 6: "MIDDLE EAST", 7: "AMERICAS",
    8: "ASIA-PACIFIC", 9: "OCEANIA", 10: "EUROPE", 11: "OCEANIA",
    12: "EUROPE", 13: "EUROPE",
    14: "EUROPE", 15: "AMERICAS", 16: "WORLD", 17: "AFRICA",
    18: "MIDDLE EAST", 19: "MIDDLE EAST", 20: "WORLD",
    21: "ASIA-PACIFIC", 22: "ASIA-PACIFIC", 23: "ASIA-PACIFIC",
    24: "WORLD", 25: "MIDDLE EAST", 26: "WORLD",
}

# Zone map (1024px, margins 10) — v9, measured from the render:
#   MASTHEAD 5 (Liberation Bold 101px, xscale 0.845, ~1003px wide,
#     66px cap, full-bleed like #2's 1000px; ink to ~93)
#   KICKER 100-122 (11px text + region-count chips + PRESS TIME right)
#   TIMELINE 128-152 (24px BLACK bar, bright per-event time colours
#     sampled from #2's UTC bar + white labels; v10: 11px type, all six
#     events have definite UTC hours — 14:48 is the IPS first-filing
#     time, not the plenary hour; v11: entries in CHRONOLOGICAL order)
#   LEAD CARDS 158-370 (212; scene 104; cat 10px region colour; head
#     24px 2 lines; deck 12px 1 line; src 9px) | STAT PANEL 158-370
#     (218 wide, dark, header 12px, 6 rows x 31px: 25px number in its
#     own pastel colour + white 8px label, story chip disc r10 "#n")
#   SMALL CARDS 378-518, 526-666 (140; scene 50; cat 9px region colour;
#     head 19px 2 lines (auto-shrink for long heads); deck 11px 1 line;
#     src 9px)
#   ALSO header 674 | ALSO items 696-844 (3 cols x 5 rows, 30px pitch;
#     v9: flag 16x11 + bold 12px title + 10px grey description, source
#     right-aligned 10px; no badge chips on rows) | DATE CHECK (686) +
#     MAP (312x110) 852-988 (136 tall; rule 1 line bold + 3-col left-out
#     with red dates) | FOOTER 994, 1006 (9px)
# "TURKIYE" is spelled without the diaeresis: the glyph set has no Ü
# (same as v4's "Marquez" — the á is not in the set either).
def build():
    cv = Canvas(W, H, PAPER)
    mx = 10
    cw = W - 2 * mx  # 1004

    # masthead: Liberation Serif Bold at 101px (cap 66.1px) with
    # xscale 0.845 — the natural face at cap 66 would be ~1187px wide
    # (too wide for the page); #2's masthead measures condensed
    # (~0.84x at the same cap), so the condense reproduces #2's
    # geometry: ~1003px wide, 66px cap, full-bleed like #2's 1000px.
    draw_text_c(cv, W // 2, 5, MASTHEAD, 101, INK, bold=True, xscale=0.845)

    # kicker: "28 STORIES · 7 REGIONS · ALL FROM THIS ONE DAY" + region
    # chips + "PRESS TIME 23:00 UTC" right (like #2's kicker line).
    ky = 100
    kicker = "26 STORIES \u00b7 7 REGIONS \u00b7 ALL FROM THIS ONE DAY"
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

    # timeline bar: BLACK, 24px (v10: grown from 22px for the bigger
    # 11px type; the 2px come from the lead-card gap, still 6px), bright
    # per-event time colour + white label (v9: #2's system — soft pastel
    # times on black; v10: every event now has a definite UTC hour —
    # 14:48 is the IPS first-filing time, see TIMELINE comment).
    bar_y = 128
    cv.fill_rect(mx, bar_y, cw, 24, DARK)
    draw_text(cv, mx + 6, bar_y + 7, "UTC", 11, WHITE, bold=True)
    slot = (W - mx - 56) // 6
    for i, (mins, label, above, tcol) in enumerate(TIMELINE):
        gx = 56 + i * slot
        # split "TIME rest" into coloured time + white label.
        parts = label.split(" ", 1)
        t, rest = parts[0], parts[1] if len(parts) > 1 else ""
        draw_text(cv, gx, bar_y + 7, t, 11, tcol, bold=True)
        lx = gx + int(text_width(t + " ", 11, bold=True))
        draw_text(cv, lx, bar_y + 7, rest, 11, WHITE, bold=True)

    # helper: location chip (top-left of art) + badge (bottom-right)
    def art_labels(ax, ay, aw, ah, n, badge_label):
        loc = "%d %s" % (n, LOCATIONS[n])
        tw = int(text_width(loc, 9, bold=True))
        cv.fill_rect(ax + 6, ay + 6, tw + 12, 16, INK)
        draw_text(cv, ax + 12, ay + 10, loc, 9, WHITE, bold=True)
        bw = int(text_width(badge_label, 9, bold=True)) + 10
        badge(cv, ax + aw - 6 - bw, ay + ah - 6 - 15, badge_label)

    # 3 lead cards (256 wide) + stat panel (218 wide), 212 tall.
    # v9: head 24px (measured: all 3 fit 2 lines at 24px; 26px breaks
    # COP31 into 3), deck ONE line 12px, category in the region colour.
    ly = 158
    lw = 256
    lh = 212
    for i, st in enumerate(LEADS):
        bx = mx + i * (lw + 6)
        cv.rect(bx, ly, lw, lh, INK, 1)
        scene(cv, bx + 1, ly + 1, lw - 2, 104, st["scene"])
        art_labels(bx + 1, ly + 1, lw - 2, 104, st["n"], st["badge"])
        cat_col = dict(REGION_COLORS)[REGION_OF[st["n"]]]
        draw_text(cv, bx + 8, ly + 110, CATEGORIES[st["n"]], 10, cat_col,
                  bold=True)
        _, nlines = block_fit(cv, bx + 8, ly + 124, st["head"], 24, INK,
                              lw - 16, 2, 28, bold=True)
        block_fit(cv, bx + 8, ly + 184, st["deck"], 12,
                  INK, lw - 16, 1, 15)
        draw_text(cv, bx + 8, ly + lh - 11, st["src"], 9, GREY, bold=True)

    # stat panel: dark "THE DAY IN NUMBERS", 6 rows x 31px. v9: each
    # number in its own pastel colour (sampled from #2's panel) + the
    # story-number disc (#n, kept from v7).
    px = mx + 3 * (lw + 6)
    pw = W - mx - px  # 218
    cv.fill_rect(px, ly, pw, lh, PANEL)
    draw_text_c(cv, px + pw // 2, ly + 8, "THE DAY IN NUMBERS", 12, WHITE,
                bold=True)
    for i, (num, label, ncol) in enumerate(STATS):
        ry = ly + 26 + i * 31
        cv.disc(px + 14, ry + 13, 10, RED)
        draw_text(cv, px + 14, ry + 9, "#%d" % STAT_STORIES[i], 8, WHITE,
                  bold=True, align="c")
        draw_text(cv, px + 30, ry + 2, num, 25, ncol, bold=True)
        lines = wrap(label, pw - 130, 8, bold=True)
        for j, ln in enumerate(lines[:2]):
            draw_text(cv, px + 124, ry + 4 + j * 11, ln, 8, WHITE, bold=True)

    # 10 small cards, 2 rows x 5, 140 tall, scene 50. v9: head 19px
    # (measured: 7 of 10 fit 2 lines; the 3 longest auto-shrink via
    # block_fit, as in #2), deck ONE line 10px, category in the region
    # colour. v10: decks 10px -> 11px (the 4 that overflowed at 11px
    # were shortened, facts kept — see SMALL; #7 shortened too, it sat
    # exactly at the 184px limit), source lines 8px -> 9px.
    sw = 196
    sh = 140
    for row in range(2):
        for col in range(5):
            st = SMALL[row * 5 + col]
            bx = mx + col * (sw + 6)
            by = 378 + row * (sh + 8)
            cv.rect(bx, by, sw, sh, INK, 1)
            scene(cv, bx + 1, by + 1, sw - 2, 50, st["scene"])
            art_labels(bx + 1, by + 1, sw - 2, 50, st["n"], st["badge"])
            cat_col = dict(REGION_COLORS)[REGION_OF[st["n"]]]
            draw_text(cv, bx + 6, by + 56, CATEGORIES[st["n"]], 9, cat_col,
                      bold=True)
            _, nlines = block_fit(cv, bx + 6, by + 68, st["head"], 19, INK,
                                  sw - 12, 2, 22, bold=True)
            block_fit(cv, bx + 6, by + 114, st["deck"], 11,
                      INK, sw - 12, 1, 12)
            draw_text(cv, bx + 6, by + sh - 9, st["src"], 9, GREY, bold=True)

    # also-list header + badge legend (like #2, same line). v14: ay
    # 674 -> 672 so the 33px-pitch items (starting 690) still end
    # before DATE CHECK at 852.
    ay = 672
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

    # also-list: 3 columns x 5 rows, 33px pitch. v9 (#2's system): each
    # row is 3 layers — self-made flag (16x11) + BOLD 12px title with
    # the source right-aligned on the same line, then a 1-line grey
    # 12px description below. No badge chips on rows. Column pitch 338
    # but content width 328 (10px gutter): the source ends at ax+328
    # so it never touches the next column's number. v12: pitch 30 ->
    # 31, desc 10 -> 10.5px at +15 (was +14) for legibility; last
    # desc ends ~843, DATE CHECK starts at 852. v13: pitch 31 -> 32,
    # desc 10.5 -> 11px at +16, items start 696 -> 694; last desc ends
    # ~846-849, DATE CHECK still starts at 852. v14 (Ban: make it
    # VISIBLE at 1x): pitch 32 -> 33, desc 11 -> 12px at +15 (the
    # brief said 11.5, but at 1x side-by-side 11.5 was still
    # indistinguishable from v13's 11 — 12px is the largest size whose
    # last desc still clears DATE CHECK), header 674 -> 672, items
    # start 694 -> 690; last desc ends ~849, DATE CHECK still starts
    # at 852 (3px slack).
    for i, (n, txt, desc, src, flag) in enumerate(ALSO):
        col = i // 5
        row = i % 5
        ax = mx + col * 338
        ay2 = 690 + row * 33
        draw_text(cv, ax, ay2, str(n) + ".", 12, RED, bold=True)
        draw_flag(cv, ax + 28, ay2, flag)
        sw = int(text_width(src, 10))
        draw_text(cv, ax + 328 - sw, ay2 + 1, src, 10, GREY)
        draw_text(cv, ax + 48, ay2, txt, 12, INK, bold=True)
        draw_text(cv, ax + 48, ay2 + 15, desc, 12, GREY)

    # bottom row (v9): DATE CHECK (686) + MAP (312), 136 tall. DATE
    # CHECK: title, then the strict rule in bold (1 line at 10px), then
    # "Left out because they happened on an earlier day" with the 15
    # items in 3 columns x 5 rows, dates in RED. The "not in this image"
    # clause and the intraday note are dropped (per #2's system). v12:
    # left-out rows pitch 13 -> 15px and the name-to-day gap is an
    # explicit 6px (was one space) so no item crowds its neighbour or
    # its red day tag; rows run 912..972, box bottom is 988. v13 (Ban:
    # MORE breathing room): pitch 15 -> 17px, name-to-day gap 6 -> 9px,
    # column pitch 228 -> 234; headroom reclaimed by moving the rule
    # up 2px (dy+28 -> dy+26), rule leading 13 -> 12, post-rule gap
    # 4 -> 2 and the "Left out" header gap 15 -> 13 — rows now run
    # 905..973, glyph bottom ~983, box bottom still 988. v14 (Ban:
    # make it VISIBLE at 1x): pitch 17 -> 20px, name-to-day gap 9 ->
    # 11px; headroom reclaimed by moving the rule up 2px more (dy+26
    # -> dy+24), rule leading 12 -> 11, post-rule gap 2 -> 1 and the
    # "Left out" header gap 13 -> 12, plus the box grows 136 -> 140
    # (bottom 988 -> 992; footer moves down 2px to match) — rows now
    # run 900..980, glyph bottom ~990, box bottom 992.
    dy = 852
    cv.rect(mx, dy, 686, 140, RED, 2)
    draw_text(cv, mx + 8, dy + 8, "DATE CHECK - READ THE DATES", 11, RED,
              bold=True)
    nrule = text_block(cv, mx + 8, dy + 24, DATECHECK_RULE, 10, INK, 670,
                       11, bold=True)
    ly = dy + 24 + nrule * 11 + 1
    draw_text(cv, mx + 8, ly, "Left out because they happened on an earlier day",
              10, INK, bold=True)
    ly += 12
    for i, (name, day) in enumerate(LEFTOUT):
        col = i // 5
        row = i % 5
        lx2 = mx + 8 + col * 234
        ly2 = ly + row * 20
        draw_text(cv, lx2, ly2, name, 10, INK)
        dw = int(text_width(name, 10)) + 11
        draw_text(cv, lx2 + dw, ly2, day, 10, RED, bold=True)
    mx0 = mx + 686 + 6
    draw_text(cv, mx0, dy, "WHERE IT HAPPENED", 11, INK, bold=True)
    draw_text(cv, W - mx - int(text_width("pins = story numbers", 9)), dy,
              "pins = story numbers", 9, GREY)
    draw_map(cv, mx0, dy + 16, 312, 110)

    # footer (2 lines, v12: 9 -> 9.5px for legibility; Sources line
    # measures 639.8px at 9.5, well inside 1004. v13: 9.5 -> 10px,
    # second line 1006 -> 1007 so the two lines breathe at 13px pitch;
    # second line bottom 1017, image is 1024 tall. v14: 10 -> 10.5px,
    # lines 994/1007 -> 996/1009 (DATE CHECK box grew to 992); second
    # line bottom ~1019.5, image is 1024 tall)
    draw_text(cv, mx, 996, "Sources: Reuters \u00b7 BBC \u00b7 AP \u00b7 CNN \u00b7 Al Jazeera \u00b7 AFP \u00b7 UN News \u00b7 ESPNcricinfo \u00b7 France 24 \u00b7 Guardian \u00b7 TWZ \u00b7 CNBC \u00b7 MEE \u00b7 WSJ \u00b7 US Treasury \u00b7 ESA \u00b7 Oxfam", 10.5, GREY)
    draw_text(cv, mx, 1009, "Scenes are drawn illustrations of reported events, not photographs. Wires read to 23:00 UTC.", 10.5, GREY)
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
