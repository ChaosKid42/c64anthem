#!/usr/bin/env python3
# =====================================================================
#  make_data.py  -  generates the binary data for anthem.asm
#
#  Picture : multicolor bitmap 320x200 (federal president + 3rd verse)
#  Music   : German national anthem, melody by Joseph Haydn (1797),
#            E-flat major, 4/4, quarter = 85 bpm. Structure of the
#            3rd verse: first part (bars 1-4) twice, second part
#            (bars 5-12), its closing lines twice; final note with
#            a fermata.
#
#  Produces:  bitmap.bin   8000 bytes  multicolor bitmap ($2000)
#             screen.bin   1024 bytes  screen RAM      ($1000, 1000+24)
#             colors.bin   1024 bytes  color RAM       ($1400, 1000+24)
#             music.bin     380 bytes  music data
#             freq.bin       98 bytes  SID frequency table (MIDI 36..84)
#             image_320x200.png       preview of the rendered picture
#
#  Usage:     python3 make_data.py [image.png] [--outdir DIR]
#             Without an image a simple flag background is drawn.
#
#  Dependencies: numpy, pillow
# =====================================================================
import argparse
import os

import numpy as np
from PIL import Image

# ---------------------------------------------------------------------
# 1) Small 3x5 font, glyphs are scaled 2x in x direction
# ---------------------------------------------------------------------
FONT = {
 'A':"010,101,111,101,101", 'B':"110,101,110,101,110", 'C':"011,100,100,100,011",
 'D':"110,101,101,101,110", 'E':"111,100,110,100,111", 'F':"111,100,110,100,100",
 'G':"011,100,101,101,011", 'H':"101,101,111,101,101", 'I':"111,010,010,010,111",
 'J':"001,001,001,101,010", 'K':"101,101,110,101,101", 'L':"100,100,100,100,111",
 'M':"101,111,111,101,101", 'N':"111,101,101,101,101", 'O':"010,101,101,101,010",
 'P':"110,101,110,100,100", 'Q':"010,101,101,110,011", 'R':"110,101,110,101,101",
 'S':"011,100,010,001,110", 'T':"111,010,010,010,010", 'U':"101,101,101,101,011",
 'V':"101,101,101,101,010", 'W':"101,101,111,111,101", 'X':"101,101,010,101,101",
 'Y':"101,101,010,010,010", 'Z':"111,001,010,100,111",
 '0':"111,101,101,101,111", '1':"010,110,010,010,111", '2':"110,001,010,100,111",
 '3':"111,001,011,001,111", '4':"101,101,111,001,001", '5':"111,100,110,001,110",
 '6':"011,100,111,101,111", '7':"111,001,010,010,010", '8':"111,101,111,101,111",
 '9':"111,101,111,001,110",
 ' ':"000,000,000,000,000", '!':"010,010,010,000,010", ',':"000,000,000,010,100",
 '.':"000,000,000,000,010", '-':"000,000,111,000,000", ':':"000,010,000,010,000",
}
UML = {'\u00c4':'A', '\u00d6':'O', '\u00dc':'U'}      # A-umlaut, O-umlaut, U-umlaut

WHITE = (236, 240, 245)
GOLD  = (250, 205, 110)
GREY  = (170, 175, 185)

def _plot(a, x, y, c):
    if 0 <= y < a.shape[0] and 0 <= x < a.shape[1]:
        a[y, x] = c

def draw_text(a, x, y, text, colour):
    """3x5 font, 2 pixels wide per font pixel, 8 pixel advance."""
    cx = x
    for ch in text:
        dots = False
        if ch in UML:
            ch, dots = UML[ch], True
        rows = FONT[ch].split(',')
        if dots:                                   # umlaut dots one row higher
            for gx, b in enumerate("101"):
                if b == '1':
                    _plot(a, cx + gx * 2, y - 1, colour)
        for ry, row in enumerate(rows):
            for gx, b in enumerate(row):
                if b == '1':
                    for px in range(2):
                        _plot(a, cx + gx * 2 + px, y + ry, colour)
        cx += 8

def text_width(t):
    return len(t) * 8 - 2

# ---------------------------------------------------------------------
# 2) Assemble the 320x200 screen image
# ---------------------------------------------------------------------
LYRICS = ["EINIGKEIT UND RECHT UND FREIHEIT",
          "F\u00dcR DAS DEUTSCHE VATERLAND!",
          "DANACH LASST UNS ALLE STREBEN",
          "BR\u00dcDERLICH MIT HERZ UND HAND!",
          "EINIGKEIT UND RECHT UND FREIHEIT",
          "SIND DES GL\u00dcCKES UNTERPFAND.",
          "BL\u00dcH IM GLANZE DIESES GL\u00dcCKES,",
          "BL\u00dcHE, DEUTSCHES VATERLAND!"]
HEADER = "BUNDESPR\u00c4SIDENT FRANK-WALTER STEINMEIER"

def flag_background():
    """Fallback background if no photo is available."""
    a = np.zeros((200, 320, 3), np.float64)
    for y in range(200):                           # black-red-gold
        if y < 60:      a[y] = (28, 28, 32)
        elif y < 120:   a[y] = (150, 30, 30)
        else:           a[y] = (200, 160, 40)
    return a

def build_picture(img_path=None):
    if img_path and os.path.exists(img_path):
        canvas = np.zeros((200, 320, 3), np.float64)
        src = Image.open(img_path).convert("RGB").resize((320, 179), Image.LANCZOS)
        canvas[:179] = np.array(src, np.float64)
    else:
        canvas = flag_background()

    # Darken: title strip at the top, gradient band at the bottom for the lyrics
    for y in range(200):
        f = 1.0
        if y <= 13:
            f = 0.30
        if y >= 90:
            f = min(f, 1.0 - 0.88 * ((y - 90) / 110.0) ** 1.15)
        canvas[y] *= f

    draw_text(canvas, 4, 2, HEADER, GOLD)
    draw_text(canvas, (320 - text_width("3. STROPHE")) // 2, 110, "3. STROPHE", GOLD)
    y = 126
    for line in LYRICS:
        draw_text(canvas, (320 - text_width(line)) // 2, y, line, WHITE)
        y += 9
    draw_text(canvas, (320 - text_width("MELODIE: JOSEPH HAYDN 1797")) // 2, 193,
              "MELODIE: JOSEPH HAYDN 1797", GREY)
    return np.clip(canvas, 0, 255).astype(np.uint8)

# ---------------------------------------------------------------------
# 3) Convert to a multicolor bitmap (Koala format)
#    per 8x8 character cell: 32 multicolor pixels, background = color 0,
#    plus 3 colors from the 16 C64 colors (best match)
# ---------------------------------------------------------------------
PAL = np.array([(0,0,0), (255,255,255), (104,55,43), (112,164,178),
                (111,61,134), (88,141,67), (53,40,121), (184,199,111),
                (111,79,64), (67,57,0), (154,103,89), (68,68,68),
                (108,108,108), (154,210,132), (108,94,181), (149,149,149)],
               dtype=np.int32)

def to_koala(img):
    import itertools
    mc    = np.asarray(img, float).reshape(200, 160, 2, 3).mean(2)
    cells = mc.reshape(25, 8, 40, 4, 3)
    bmp = np.zeros(8000, np.uint8)
    scr = np.zeros(1000, np.uint8)
    col = np.zeros(1000, np.uint8)
    for cy in range(25):
        for cx in range(40):
            px  = cells[cy, :, cx, :, :].reshape(32, 3)
            d   = ((px[:, None, :] - PAL[None, :, :]) ** 2).sum(2)   # 32x16
            cnt = np.bincount(d.argmin(1), minlength=16)
            cand = [int(c) for c in np.argsort(-cnt)[:6] if c != 0]  # never color 0
            while len(cand) < 3:
                cand.append(int(np.argsort(-cnt)[len(cand)]))
            cand = list(dict.fromkeys(cand))
            best = min(((d[:, [0] + list(c)].min(1).sum(),
                         [0] + list(c),
                         d[:, [0] + list(c)].argmin(1))
                        for c in itertools.combinations(cand, 3)),
                       key=lambda t: t[0])
            _, cols, assign = best
            for r in range(8):
                byte = 0
                for p in range(4):
                    byte = (byte << 2) | int(assign[r * 4 + p])
                bmp[cy * 320 + cx * 8 + r] = byte
            scr[cy * 40 + cx] = (cols[1] << 4) | cols[2]
            col[cy * 40 + cx] = cols[3]
    return bmp, scr, col

# ---------------------------------------------------------------------
# 4) Music: note1, note2, note3, duration (1/50 s); 255 = end/loop
#
#    Melody: E-flat major, 4/4, quarter = 85 bpm -> one quarter = 35
#    frames (50 Hz). Structure of the 3rd verse:
#      first part   bars 1-4   "Unity and justice and freedom /
#                               for the German fatherland!"        (2x)
#      second part  bars 5-8   "Unity and justice and freedom /
#                               are the pledge of happiness."
#                   bars 9-12  "Bloom in the splendor of this happiness,
#                               bloom, German fatherland!"         (2x)
#    The notes follow the Haydn melody (E-flat major) exactly.
# ---------------------------------------------------------------------
Q = 35              # quarter note (frames at 50 Hz)

CHORDS = {'Eb': (39, 58),     # bass 39 = Eb2, pad 58 = Bb3
          'Bb': (46, 62),     # 46 = Bb2,     62 = D4
          'Ab': (44, 60)}     # 44 = Ab2,     60 = C4

# Bar by bar: ([(MIDI note, length in quarters), ...], harmony)
BARS = [
    # --- first part (bars 1-4) -------------------------------------
    ([(63,1.5),(65,0.5),(67,1),(65,1)],                    'Eb'),  # U-ni-ty and
    ([(68,1),(67,1),(65,0.5),(62,0.5),(63,1)],             'Eb'),  # jus-tice and free-dom
    ([(72,1),(70,1),(68,1),(67,1)],                        'Ab'),  # for the Ger-man
    ([(65,1),(67,0.5),(63,0.5),(70,2)],                    'Eb'),  # fa-ther-land
    # --- second part, first half (bars 5-8) ------------------------
    ([(65,1),(67,1),(65,0.5),(62,0.5),(58,1)],             'Bb'),  # U-ni-ty and
    ([(68,1),(67,1),(65,0.5),(62,0.5),(58,1)],             'Bb'),  # jus-tice and free-dom
    ([(70,1),(68,1),(67,1.5),(67,0.5)],                    'Eb'),  # are the pledge of
    ([(69,1),(69,0.5),(70,0.5),(70,2)],                    'Bb'),  # hap-pi-ness
    # --- second part, second half (bars 9-12) ----------------------
    ([(75,1.5),(74,0.5),(74,0.5),(72,0.5),(70,1)],         'Eb'),  # bloom in the splen-dor
    ([(72,1.5),(70,0.5),(70,0.5),(68,0.5),(67,1)],         'Ab'),  # of this hap-pi-ness
    ([(65,1.5),(67,0.25),(68,0.25),(70,0.5),(72,0.5),
      (68,0.5),(65,0.5)],                                  'Bb'),  # blos-som, Ger-man
    ([(63,1),(67,0.5),(65,0.5),(63,2)],                    'Eb'),  # fa-ther-land
]

# First part 2x, second part first half, second part second half 2x
STRUCTURE = [0,1,2,3, 0,1,2,3, 4,5,6,7, 8,9,10,11, 8,9,10,11]

def build_music():
    ev = []
    for b in STRUCTURE:
        notes, ch = BARS[b]
        bass, pad = CHORDS[ch]
        for nt, beats in notes:
            ev += [nt, bass, pad, max(1, int(round(beats * Q)))]
    ev[-1] = 100                        # fermata on the final note
    ev += [255, 0, 0, 0]                # end marker
    return ev

# ---------------------------------------------------------------------
# 5) SID frequency table PAL: reg = f * 16777216 / 985248
# ---------------------------------------------------------------------
def build_freq():
    t = []
    for n in range(36, 85):                 # MIDI 36 (C2) .. 84 (C6)
        f = 440.0 * 2 ** ((n - 69) / 12.0)
        reg = int(round(f * 16777216 / 985248.0))
        t += [reg & 0xff, reg >> 8]
    return t

# ---------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(
        description="Generate the binary data for anthem.asm.")
    ap.add_argument("image", nargs="?", default=None,
                    help="optional background image "
                         "(default: simple flag background)")
    ap.add_argument("-o", "--outdir", default="build",
                    help="output directory (default: build)")
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    canvas = build_picture(args.image)
    bmp, scr, col = to_koala(canvas)

    out = {
        "bitmap.bin": list(bmp),
        "screen.bin": list(scr) + [0] * 24,
        "colors.bin": list(col) + [0] * 24,
        "music.bin":  build_music(),
        "freq.bin":   build_freq(),
    }
    for name, data in out.items():
        path = os.path.join(args.outdir, name)
        with open(path, "wb") as f:
            f.write(bytes(data))
        print("%-11s %5d bytes" % (name, len(data)))
    Image.fromarray(canvas).save(os.path.join(args.outdir, "image_320x200.png"))

if __name__ == "__main__":
    main()
