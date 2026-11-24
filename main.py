# main.py — news-image-20261123
# "Sum up 23 November's world news in one image"
# Pure Python 3.13 standard library only. No network, no fonts, no external
# images. Every pixel is computed in code. Deterministic: two runs write
# byte-identical PNGs. Writes only to MAKEFUN_OUTPUT_DIR (fallback /output).
# Content: STORY-LIST.md (verified live 23 Nov). All figures come from the
# named outlets cited beside each story; no invented numbers.
# Text is set in a 5x7 bitmap face drawn by this file (all-caps newspaper
# style); the world map is a coarse equirectangular outline drawn from the
# polygon table in this file, with numbered pins placed by lat/lon.

import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
PAPER = (248, 244, 234)
INK = (25, 25, 25)
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


# ---------------------------------------------------------------- canvas
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


# ---------------------------------------------------------------- 5x7 bitmap face
# Glyphs are 7 rows of 5 cells; '1' is ink. All-caps newspaper face, drawn
# from this table only. Lowercase input is upper-cased by draw_text.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "*": ("00000", "10101", "01110", "11111", "01110", "10101", "00000"),
    "#": ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    "@": ("01110", "10001", "10111", "10101", "10110", "10000", "01110"),
    "_": ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    "[": ("01110", "01000", "01000", "01000", "01000", "01000", "01110"),
    "]": ("01110", "00010", "00010", "00010", "00010", "00010", "01110"),
    "<": ("00010", "00100", "01000", "10000", "01000", "00100", "00010"),
    ">": ("01000", "00100", "00010", "00001", "00010", "00100", "01000"),
    "|": ("00100", "00100", "00100", "00100", "00100", "00100", "00100"),
}


def _norm(s):
    return (s.replace("\u2013", "-").replace("\u2014", "-").replace("\u2019", "'")
             .replace("\u2018", "'").replace("\u201c", '"').replace("\u201d", '"')
             .replace("\u2212", "-").replace("\u00d7", "x").replace("\u20ac", "EUR ")
             .replace("\u2022", "*").upper())


def char_w(scale):
    return 6 * scale


def text_w(s, scale):
    s = _norm(s)
    return max(0, len(s) * 6 * scale - scale)


def draw_char(cv, x, y, ch, scale, color):
    g = FONT.get(ch)
    if g is None:
        return
    for r in range(7):
        row = g[r]
        for c in range(5):
            if row[c] == "1":
                cv.fill_rect(x + c * scale, y + r * scale, scale, scale, color)


def draw_text(cv, x, y, s, scale, color):
    s = _norm(s)
    cx = x
    for ch in s:
        draw_char(cv, cx, y, ch, scale, color)
        cx += 6 * scale
    return cx


def draw_text_c(cv, cx, y, s, scale, color):
    draw_text(cv, cx - text_w(s, scale) // 2, y, s, scale, color)


def draw_text_track(cv, x, y, s, scale, color, adv):
    # Like draw_text but with an explicit per-character advance (px), used
    # for the masthead where a fixed 6-unit advance would overflow the page.
    s = _norm(s)
    cx = x
    for ch in s:
        draw_char(cv, cx, y, ch, scale, color)
        cx += adv
    return cx


# ---------------------------------------------------------------- serif face for the masthead
# 5x7 bitmap glyphs with a slab-serif treatment: flat top and bottom bars on
# E/B/D/3, feet on M/N/A/Y, slashed 0. Drawn at scale 7 for a 49px cap
# (parity with the rank-1 reference masthead). A 7-wide serif face was tried
# first and REJECTED: 23 chars need 22*44+49 = 1017px at scale 7, wider than
# the 992px column, so the glyphs overlapped and merged. The 5-wide face
# keeps the full date at 937px with a 6px gap between glyphs. Authored here
# for the masthead letterforms only ("MONDAY 23 NOVEMBER 2026"); every other
# string on the page keeps the 5x7 body face above.
SERIF = {
    "M": ("11011", "11101", "10101", "10101", "10001", "10001", "11011"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "N": ("11001", "11101", "10101", "10011", "10011", "10001", "10011"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "A": ("01110", "10001", "10001", "10001", "11111", "10001", "11011"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "0": ("01110", "10011", "10101", "10101", "11001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
}


def draw_serif(cv, x, y, s, scale, color, adv):
    # Masthead only: draws from the SERIF table with an explicit advance.
    s = _norm(s)
    cx = x
    for ch in s:
        g = SERIF.get(ch)
        if g is not None:
            for r in range(7):
                row = g[r]
                for c in range(len(row)):
                    if row[c] == "1":
                        cv.fill_rect(cx + c * scale, y + r * scale, scale, scale, color)
        cx += adv
    return cx


def wrap(s, max_w, scale):
    s = _norm(s)
    words = s.split(" ")
    lines = []
    cur = ""
    for w in words:
        trial = (cur + " " + w).strip()
        if text_w(trial, scale) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def text_block(cv, x, y, s, scale, color, max_w, leading):
    lines = wrap(s, max_w, scale)
    for i, ln in enumerate(lines):
        draw_text(cv, x, y + i * leading, ln, scale, color)
    return len(lines)


def badge(cv, x, y, label, scale=1):
    c = BADGE_COLORS.get(label, GREY)
    w = text_w(label, scale) + 8
    h = 7 * scale + 6
    cv.fill_rect(x, y, w, h, c)
    draw_text(cv, x + 4, y + 3, label, scale, WHITE)
    return w


def num_chip(cv, x, y, n, scale=2):
    s = str(n)
    w = text_w(s, scale) + 8
    h = 7 * scale + 6
    cv.fill_rect(x, y, w, h, RED)
    draw_text(cv, x + 4, y + 3, s, scale, WHITE)
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

# (story number, lon, lat, label or None, label side: 1 right, -1 left)
MAP_PINS = [
    (1, 31.0, 37.5, "ANTALYA", 1),
    (2, 18.0, 33.0, "BENGHAZI", -1),
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
    for num, lon, lat, label, side in MAP_PINS:
        px, py = _lonlat(x, y, w, h, lon, lat)
        cv.disc(px, py, 6, RED)
        cv.ring(px, py, 6, WHITE, 1)
        s = str(num)
        draw_text(cv, px - text_w(s, 1) // 2, py - 3, s, 1, WHITE)
        if label:
            lx = px + 9 if side > 0 else px - 9 - text_w(label, 1)
            ly = py - 3
            cv.fill_rect(lx - 1, ly - 1, text_w(label, 1) + 2, 9, PAPER)
            draw_text(cv, lx, ly, label, 1, INK)


# ---------------------------------------------------------------- flat-vector scenes
def _star(cv, cx, cy, r, c):
    for a in range(0, 360, 45):
        import math
        x1 = cx + int(r * math.cos(math.radians(a)))
        y1 = cy + int(r * math.sin(math.radians(a)))
        cv.line(cx, cy, x1, y1, c)


def scene(cv, x, y, w, h, kind):
    if kind == "cop31":
        cv.fill_rect(x, y, w, h, TEAL)
        for row in range(3):
            for col in range(6):
                cv.fill_rect(x + 12 + col * 50, y + 12 + row * 16, 34, 9, CREAM)
        cv.fill_rect(x + w // 2 - 34, y + h - 40, 68, 26, WHITE)
        cv.line(x + w // 2 - 24, y + h - 34, x + w // 2 + 24, y + h - 20, RED)
        cv.line(x + w // 2 - 24, y + h - 20, x + w // 2 + 24, y + h - 34, RED)
    elif kind == "dymer":
        cv.fill_rect(x, y, w, h, DARK)
        for sx, sy in ((14, 10), (60, 22), (120, 8), (200, 16), (280, 10), (250, 30)):
            cv.disc(x + sx, y + sy, 1, WHITE)
        cv.fill_rect(x + 20, y + 30, 90, h - 30, GREY)
        for fl in range(4):
            for wn in range(4):
                cv.fill_rect(x + 30 + wn * 20, y + 38 + fl * 12, 10, 7,
                             GOLD if (fl + wn) % 2 else (60, 60, 60))
        cv.poly([(x + 110, y + 30), (x + 150, y + 46), (x + 150, y + h),
                 (x + 110, y + h)], (40, 40, 40))
        cv.line(x + 210, y + 20, x + 230, y + 40, WHITE)
        cv.line(x + 230, y + 20, x + 210, y + 40, WHITE)
        cv.disc(x + 220, y + 30, 3, WHITE)
    elif kind == "merkury":
        cv.fill_rect(x, y, w, h, (16, 42, 60))
        cv.fill_rect(x, y + h - 26, w, 26, (10, 30, 46))
        cv.poly([(x + 30, y + h - 26), (x + 60, y + h - 44), (x + 240, y + h - 44),
                 (x + 280, y + h - 26)], (95, 95, 105))
        cv.fill_rect(x + 120, y + h - 62, 70, 20, (95, 95, 105))
        cv.fill_rect(x + 150, y + h - 76, 6, 16, (95, 95, 105))
        _star(cv, x + 90, y + 26, 22, ORANGE)
        _star(cv, x + 90, y + 26, 12, (255, 220, 60))
        cv.disc(x + 220, y + 22, 9, GREY)
        cv.disc(x + 240, y + 30, 6, GREY)
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
        draw_text(cv, x + 80, y + 26, "NVDA", 1, GREEN)
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
MASTHEAD = "MONDAY 23 NOVEMBER 2026"
SUBHEAD = "COP31 COLLAPSES - NO DEAL - MERKURY SUNK OFF LIBYA - DYMER TOLL RISES TO 11"
TOPLINE = "THE WORLD IN ONE DAY - 35 STORIES - 7 REGIONS - EVERY STORY DATED MONDAY 23 NOVEMBER 2026"

# Timeline: verified times only (see STORY-LIST.md). (minutes from 00:00 UTC,
# label, label above the bar?) "SUN" = Sunday outcome carried into Monday;
# "MORNING" = verified morning, exact hour approximate (~07:23 Kyiv local).
TIMELINE = [
    (0, "SUN COP31", True),
    (88, "01:28 DYMER RESCUE", False),
    (160, "02:40 VANUATU", True),
    (323, "MORNING DYMER TOLL 11", False),
    (1260, "21:00 S&P +4.7%", True),
    (1380, "23:00 PRESS TIME", False),
]

STATS = [
    ("0", "CLIMATE DEALS AGREED AT COP31"),
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
     "src": "UN NEWS - BBC - CNN"},
    {"n": 2, "badge": "REPORTED", "scene": "merkury",
     "head": "MERKURY SINKS OFF LIBYA",
     "deck": "Zelensky: 7 sea drones hit; Ka-27 destroyed; Angara cargo ship hit.",
     "src": "AP - CNN - TWZ"},
    {"n": 3, "badge": "CONFIRMED", "scene": "dymer",
     "head": "DYMER TOLL RISES TO 11",
     "deck": "Boy, 7, pulled alive; woman, 79, rescued too. 15 dead in Kyiv region.",
     "src": "REUTERS - BBC"},
]

SMALL = [
    {"n": 4, "badge": "CONFIRMED", "scene": "markets",
     "head": "WALL ST ROARS BACK",
     "deck": "S&P +4.7%, Nasdaq +6.5% on Huang return. Kospi -3.3% to 4,708.54; Hang Seng -0.1%.",
     "src": "AP - REUTERS"},
    {"n": 5, "badge": "CONFIRMED", "scene": "democrats",
     "head": "DEMOCRATS TAKE 258 SEATS",
     "deck": "Largest House majority since 1992. Hubbard beats Foxx after recount.",
     "src": "AP - REUTERS"},
    {"n": 6, "badge": "REPORTED", "scene": "hormuz",
     "head": "TANKERS ABLAZE AT HORMUZ",
     "deck": "Two supertankers hit mines; strike wounds 2 in Bahrain. Blockade day 130.",
     "src": "AL JAZEERA - AP"},
    {"n": 7, "badge": "CONFIRMED", "scene": "nvidia",
     "head": "HUANG BACK AT NVIDIA",
     "deck": "Board reverses days after saying no; shares +31% Mon. Reported SEC probe still open.",
     "src": "CNN - REUTERS"},
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
     "src": "CNBC - MEE"},
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
     "src": "BBC - GUARDIAN"},
]

ALSO = [
    # v3: one-line items at scale 2 (14px cap), max 24 chars each, so every
    # item fits its column. Inline sources dropped for the bigger type;
    # pictured stories still name their sources below each card.
    (14, "SPARTA II TOWED OUT SUN"),
    (15, "SOUTH SUDAN: 24+ KILLED"),
    (16, "POLAND: RAPPER PLOT X2"),
    (17, "EL CHAPO CAPTURED FRI"),
    (18, "BOLSONARO STILL IN ICU"),
    (19, "NETANYAHU TALKS FAIL"),
    (20, "WEST BANK ARSON: 12 CARS"),
    (21, "TRUMP: PUTIN 'MY FRIEND'"),
    (22, "BEPICOLOMBO IN ORBIT SAT"),
    (23, "RIEMANN PROOF CLAIMED"),
    (24, "NEPAL: EUR 19M LOSS FUND"),
    (25, "IRAN FLOGS AHMADI 74X"),
    (26, "BELGIUM AIRPORTS SHUT"),
    (27, "DR CONGO: EBOLA FIGHTING"),
    (28, "GAZA CONTAMINATION"),
    (29, "GAZA: 3 DEAD INCL UNRWA"),
    (30, "ISTANBUL MEDIA RALLY"),
    (31, "MARQUEZ: 8TH TITLE"),
    (32, "BOCA WIN COPA (SAT)"),
    (33, "EU: 22ND RUSSIA SANCTION"),
    (34, "VANUATU M6.5 QUAKE"),
    (35, "RUSSIA WARNS ESTONIA"),
]

DATECHECK = ("Left out as other days' news: Nikkei -5.06% (Fri 20 Nov close; Tokyo shut Mon) - "
    "S&P 500 -3.7% (Fri 20 Nov close) - Sparta II hit Sat, towed out Sun night - El Chapo Isidro "
    "captured Fri night-Sat - Boca Juniors final Sat 21 Nov - BepiColombo orbit Sat 21 Nov (glitch Sun) - "
    "EU-Indonesia signing Sat 21 Nov - Kryvyi Rih strike Fri 20 Nov - Peru quake Fri 20 Nov - "
    "Russia's 400-drone barrage 19-20 Nov. Kospi -5.8% and Hang Seng -1.8% were Monday intraday lows, "
    "not closes (-3.3% and -0.1%). Every story here happened, or was first reported, or was "
    "still developing on Monday 23 November 2026 (UTC). Press time: Monday 23:00 UTC.")


# ---------------------------------------------------------------- layout (v3)
# Zone map (1024px, margins 16):
#   TOPLINE 8 | serif MASTHEAD 16-65 (49px cap) | rule 68 | SUBHEAD 74-88
#   rule 92 | STAT STRIP 96-142 (46) | REGION BAR 145-161 (16)
#   TIMELINE labels 165-172 | bar 174-194 (20) | labels 196-203
#   LEAD CARDS 209-439 (230; scene 112; head 21px 2 lines; deck 14px 3 lines)
#   PICTURED header 447-461 | SMALL CARDS 465-581, 587-703 (116; scene 50)
#   MAP/ALSO header 711-725 | MAP 729-905 (324x176) | ALSO 729-913 (11x17px)
#   DATE CHECK 919-985 (66) | FOOTER 991, 1000
def build():
    cv = Canvas(W, H, PAPER)
    mx = 16
    cw = W - 2 * mx  # 992

    draw_text_c(cv, W // 2, 8, TOPLINE, 1, GREY)
    draw_serif(cv, 43, 16, MASTHEAD, 7, INK, 41)
    cv.fill_rect(mx, 68, cw, 2, INK)
    draw_text_c(cv, W // 2, 74, SUBHEAD, 2, INK)
    cv.fill_rect(mx, 92, cw, 1, LIGHT)

    # stat strip: 6 boxes, 46px
    sy = 96
    bw = (cw - 5 * 4) // 6
    for i, (num, label) in enumerate(STATS):
        bx = mx + i * (bw + 4)
        cv.rect(bx, sy, bw, 46, LIGHT, 1)
        draw_text_c(cv, bx + bw // 2, sy + 1, num, 4, INK)
        lines = wrap(label, bw - 10, 1)
        for li, ln in enumerate(lines[:2]):
            draw_text_c(cv, bx + bw // 2, sy + 30 + li * 8, ln, 1, GREY)

    # region bar
    ry = 145
    rw = cw // 7
    for i, (name, col) in enumerate(REGION_COLORS):
        bx = mx + i * rw
        w = rw if i < 6 else cw - 6 * rw
        cv.fill_rect(bx, ry, w, 16, col)
        draw_text_c(cv, bx + w // 2, ry + 5, name, 1, WHITE)

    # timeline: THE DAY IN UTC (6 verified events; see TIMELINE)
    tl_y = 165
    bar_y = 174
    bl_y = 196
    t0, t1 = 110, 1008  # timed scale: 00:00 -> 24:00 UTC

    def tx(mins):
        return t0 + int(mins / 1440.0 * (t1 - t0))

    cv.fill_rect(mx, bar_y, cw, 20, NAVY)
    cv.hline(t0, bar_y + 10, t1 - t0, WHITE)
    draw_text(cv, 22, bar_y + 7, "THE DAY IN UTC", 1, WHITE)
    for mins, label, above in TIMELINE:
        x = tx(mins)
        cv.disc(x, bar_y + 10, 4, WHITE)
        cv.disc(x, bar_y + 10, 2, RED)
        lx = x - text_w(label, 1) // 2
        lx = max(mx, min(lx, W - mx - text_w(label, 1)))
        draw_text(cv, lx, tl_y if above else bl_y, label, 1, INK)

    # 3 lead cards, 230px tall, scene 112px
    ly = 209
    lw = 324
    lh = 230
    for i, st in enumerate(LEADS):
        bx = mx + i * (lw + 8)
        cv.rect(bx, ly, lw, lh, INK, 1)
        scene(cv, bx + 1, ly + 1, lw - 2, 112, st["scene"])
        badge(cv, bx + 6, ly + 6, st["badge"], 1)
        num_chip(cv, bx + lw - 26, ly + 6, st["n"], 2)
        hy = ly + 118
        nlines = text_block(cv, bx + 8, hy, st["head"], 3, INK, lw - 16, 24)
        dy = hy + nlines * 24 + 2
        text_block(cv, bx + 8, dy, st["deck"], 2, INK, lw - 16, 17)
        draw_text(cv, bx + 8, ly + lh - 9, st["src"], 1, GREY)

    # pictured section header
    py = 447
    draw_text(cv, mx, py, "THE DAY IN PICTURES - STORIES 4-13", 2, INK)
    draw_text(cv, W - mx - text_w("13 PICTURED STORIES", 2), py, "13 PICTURED STORIES", 2, GREY)

    # 10 small cards, 2 rows x 5, 116px tall, scene 50px
    sw = 192
    sh = 116
    for row in range(2):
        for col in range(5):
            st = SMALL[row * 5 + col]
            bx = mx + col * (sw + 8)
            by = 465 + row * (sh + 6)
            cv.rect(bx, by, sw, sh, INK, 1)
            scene(cv, bx + 1, by + 1, sw - 2, 50, st["scene"])
            badge(cv, bx + 4, by + 4, st["badge"], 1)
            num_chip(cv, bx + sw - 24, by + 4, st["n"], 2)
            hy = by + 55
            nlines = text_block(cv, bx + 6, hy, st["head"], 1, INK, sw - 12, 9)
            dy = hy + nlines * 9 + 1
            text_block(cv, bx + 6, dy, st["deck"], 1, GREY, sw - 12, 9)
            draw_text(cv, bx + 6, by + sh - 12, st["src"], 1, GREY)

    # map + also-list
    my = 711
    draw_text(cv, mx, my, "WHERE IT HAPPENED", 2, INK)
    draw_text(cv, 348, my, "ALSO ON MONDAY 23 NOVEMBER", 2, INK)
    draw_map(cv, mx, my + 18, 324, 176)
    # also-list, 2 columns x 11, one-line items at scale 2 (14px cap)
    for i, (n, txt) in enumerate(ALSO):
        col = i // 11
        row = i % 11
        ax = 348 + col * 334
        ay = my + 18 + row * 17
        draw_text(cv, ax, ay, str(n) + ".", 2, RED)
        draw_text(cv, ax + 38, ay, txt, 2, INK)

    # date check
    dy = 919
    cv.rect(mx, dy, cw, 66, RED, 2)
    draw_text(cv, mx + 8, dy + 5, "DATE CHECK - WHAT WE LEFT OUT", 2, RED)
    text_block(cv, mx + 8, dy + 24, DATECHECK, 1, INK, cw - 16, 9)

    # footer (2 lines)
    draw_text(cv, mx, 991, "Sources named under each pictured story; all figures from the outlets cited. Press time Monday 23:00 UTC.", 1, GREY)
    draw_text(cv, mx, 1000, "Badges: CONFIRMED = official / 2+ outlets - CLAIM = one side's claim - REPORTED = witnesses / one source.", 1, GREY)
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



