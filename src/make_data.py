#!/usr/bin/env python3
# =====================================================================
#  make_data.py  -  generates the binary data for anthem.asm
#
#  Picture : 320x200 bitmap, multicolor portrait + high-resolution
#            text of the 3rd verse in the C64 character set
#  Music   : German national anthem, melody by Joseph Haydn (1797),
#            E-flat major, 4/4, quarter = 85 bpm. Structure of the
#            3rd verse: first part (bars 1-4) twice, second part
#            (bars 5-12), its closing lines twice; final note with
#            a fermata.
#
#             bitmap.bin   8000 bytes  bitmap ($2000)
#             screen.bin   1024 bytes  screen RAM      ($1000, 1000+24)
#             colors.bin   1024 bytes  color RAM       ($1400, 1000+24)
#             music.bin     380 bytes  music data
#             freq.bin       98 bytes  SID frequency table (MIDI 36..84)
#             image_320x200.png       preview of the rendered picture
#
#  Usage:     python3 make_data.py [image] [--crop L,T,R,B] [--outdir DIR]
#             Without an image a simple flag background is drawn.
#
#  Dependencies: numpy, pillow
# =====================================================================
import argparse
import os

import numpy as np
from PIL import Image

# ---------------------------------------------------------------------
# 1) C64 character ROM glyphs (uppercase/graphics set, 901225-01).
#    Only the characters used by the screen text are included.  Each
#    glyph is 8 rows of 8 bits, MSB = leftmost pixel.
# ---------------------------------------------------------------------
FONT = {
    'A': (24, 60, 102, 126, 102, 102, 102, 0),
    'B': (124, 102, 102, 124, 102, 102, 124, 0),
    'C': (60, 102, 96, 96, 96, 102, 60, 0),
    'D': (120, 108, 102, 102, 102, 108, 120, 0),
    'E': (126, 96, 96, 120, 96, 96, 126, 0),
    'F': (126, 96, 96, 120, 96, 96, 96, 0),
    'G': (60, 102, 96, 110, 102, 102, 60, 0),
    'H': (102, 102, 102, 126, 102, 102, 102, 0),
    'I': (60, 24, 24, 24, 24, 24, 60, 0),
    'J': (30, 12, 12, 12, 12, 108, 56, 0),
    'K': (102, 108, 120, 112, 120, 108, 102, 0),
    'L': (96, 96, 96, 96, 96, 96, 126, 0),
    'M': (99, 119, 127, 107, 99, 99, 99, 0),
    'N': (102, 118, 126, 126, 110, 102, 102, 0),
    'O': (60, 102, 102, 102, 102, 102, 60, 0),
    'P': (124, 102, 102, 124, 96, 96, 96, 0),
    'Q': (60, 102, 102, 102, 102, 60, 14, 0),
    'R': (124, 102, 102, 124, 120, 108, 102, 0),
    'S': (60, 102, 96, 60, 6, 102, 60, 0),
    'T': (126, 24, 24, 24, 24, 24, 24, 0),
    'U': (102, 102, 102, 102, 102, 102, 60, 0),
    'V': (102, 102, 102, 102, 102, 60, 24, 0),
    'W': (99, 99, 99, 107, 127, 119, 99, 0),
    'X': (102, 102, 60, 24, 60, 102, 102, 0),
    'Y': (102, 102, 102, 60, 24, 24, 24, 0),
    'Z': (126, 6, 12, 24, 48, 96, 126, 0),
    # Umlauts: the C64 character ROM has no umlauts. These follow the
    # German umlaut definitions from the C64-Wiki "Zeichen" article:
    # two-pixel dots on the top row, letter body compressed and shifted
    # down to make room for them.
    '\u00c4': (195, 24, 102, 126, 102, 102, 102, 0),    # Ä
    '\u00d6': (102, 60, 102, 102, 102, 102, 60, 0),     # Ö
    '\u00dc': (102, 0, 102, 102, 102, 102, 60, 0),      # Ü
    '0': (60, 102, 110, 118, 102, 102, 60, 0),
    '1': (24, 24, 56, 24, 24, 24, 126, 0),
    '2': (60, 102, 6, 12, 48, 96, 126, 0),
    '3': (60, 102, 6, 28, 6, 102, 60, 0),
    '4': (6, 14, 30, 102, 127, 6, 6, 0),
    '5': (126, 96, 124, 6, 6, 102, 60, 0),
    '6': (60, 102, 96, 124, 102, 102, 60, 0),
    '7': (126, 102, 12, 24, 24, 24, 24, 0),
    '8': (60, 102, 102, 60, 102, 102, 60, 0),
    '9': (60, 102, 102, 62, 6, 102, 60, 0),
    ' ': (0, 0, 0, 0, 0, 0, 0, 0),
    '!': (24, 24, 24, 24, 0, 0, 24, 0),
    ',': (0, 0, 0, 0, 0, 24, 24, 48),
    '.': (0, 0, 0, 0, 0, 24, 24, 0),
    '-': (0, 0, 0, 126, 0, 0, 0, 0),
    ':': (0, 0, 24, 0, 0, 24, 0, 0),
    '?': (60, 102, 6, 12, 24, 0, 24, 0),
    "'": (6, 12, 24, 0, 0, 0, 0, 0),
}

# Lowercase umlauts are folded to the uppercase glyphs above; the
# uppercase letters pass through as-is and are looked up in FONT.
UML = {'\u00e4': '\u00c4', '\u00f6': '\u00d6', '\u00fc': '\u00dc'}

def normalize(text):
    return ''.join(UML[ch] if ch in UML else ch for ch in text)

# ---------------------------------------------------------------------
# 2) Screen layout
# ---------------------------------------------------------------------
SCREEN_W, SCREEN_H = 320, 200
PHOTO_X, PHOTO_Y = 0, 8
PHOTO_W, PHOTO_H = 320, 112

HEADER = normalize("BUNDESPR\u00c4SIDENT FRANK-WALTER STEINMEIER")
TITLE  = "3. STROPHE"
LYRICS = [normalize(line) for line in [
    "EINIGKEIT UND RECHT UND FREIHEIT",
    "F\u00dcR DAS DEUTSCHE VATERLAND!",
    "DANACH LASST UNS ALLE STREBEN",
    "BR\u00dcDERLICH MIT HERZ UND HAND!",
    "EINIGKEIT UND RECHT UND FREIHEIT",
    "SIND DES GL\u00dcCKES UNTERPFAND.",
    "BL\u00dcH IM GLANZE DIESES GL\u00dcCKES,",
    "BL\u00dcHE, DEUTSCHES VATERLAND!",
]]
FOOTER = "MELODIE: JOSEPH HAYDN 1797"

# C64 color indices
BLACK, WHITE, YELLOW, GREY = 0, 1, 7, 12

DEFAULT_IMAGE = "res/steinmeier.jpg"
DEFAULT_CROP  = (160, 133, 800, 357)   # left, top, right, bottom

# ---------------------------------------------------------------------
# 3) Photo
# ---------------------------------------------------------------------
def flag_background():
    """Fallback background if no photo is available."""
    a = np.zeros((PHOTO_H, PHOTO_W, 3), np.float64)
    for y in range(PHOTO_H):                       # black-red-gold
        if y < PHOTO_H // 3:      a[y] = (28, 28, 32)
        elif y < 2 * PHOTO_H // 3: a[y] = (150, 30, 30)
        else:                      a[y] = (200, 160, 40)
    return a

def load_photo(path, crop=None):
    im = Image.open(path).convert("RGB")
    if crop:
        im = im.crop(crop)
    else:
        w, h = im.size
        target = PHOTO_W / PHOTO_H
        if w / h > target:
            cw, ch = int(h * target), h
        else:
            cw, ch = w, int(w / target)
        left, top = (w - cw) // 2, (h - ch) // 2
        im = im.crop((left, top, left + cw, top + ch))
    return im.resize((PHOTO_W, PHOTO_H), Image.Resampling.LANCZOS)

def build_picture(img_path, crop=None):
    canvas = np.zeros((SCREEN_H, SCREEN_W, 3), np.uint8)
    if img_path and os.path.exists(img_path):
        canvas[PHOTO_Y:PHOTO_Y + PHOTO_H] = np.array(load_photo(img_path, crop))
    else:
        canvas[PHOTO_Y:PHOTO_Y + PHOTO_H] = flag_background()
    return canvas

# ---------------------------------------------------------------------
# 4) Convert to a multicolor bitmap (Koala format)
#    per 8x8 character cell: 32 multicolor pixels, background = color 0,
#    plus 3 colors from the 16 C64 colors (best match)
# ---------------------------------------------------------------------
PAL = np.array([(0,0,0), (255,255,255), (104,55,43), (112,164,178),
                (111,61,134), (88,141,67), (53,40,121), (184,199,111),
                (111,79,64), (67,57,0), (154,103,89), (68,68,68),
                (108,108,108), (154,210,132), (108,94,181), (149,149,149)],
               dtype=np.int32)

def to_koala(img, cy0=0):
    """Convert a 320xH image (H a multiple of 8) to multicolor Koala
    data, placing the cells at cell row cy0."""
    import itertools
    h = img.shape[0]
    ncy = h // 8
    mc    = np.asarray(img, float).reshape(h, 160, 2, 3).mean(2)
    cells = mc.reshape(ncy, 8, 40, 4, 3)
    bmp = np.zeros(8000, np.uint8)
    scr = np.zeros(1000, np.uint8)
    col = np.zeros(1000, np.uint8)
    for cy in range(ncy):
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
                bmp[(cy0 + cy) * 320 + cx * 8 + r] = byte
            scr[(cy0 + cy) * 40 + cx] = (cols[1] << 4) | cols[2]
            col[(cy0 + cy) * 40 + cx] = cols[3]
    return bmp, scr, col

# ---------------------------------------------------------------------
# 5) Text rendering directly into the bitmap data
#
#    The photo is stored in multicolor format (4 fat pixels per byte),
#    but the text is stored in high-resolution format (8 pixels per
#    byte, one bit each) so the C64 character ROM glyphs are drawn at
#    their native 8x8 size with no scaling.  The VIC-II is switched
#    between the two modes with a raster split (see anthem.asm).  In
#    high-res mode screen RAM holds (foreground << 4) | background.
# ---------------------------------------------------------------------
def draw_text(bmp, scr, col, x, y, text, fg):
    cx, cy = x // 8, y // 8
    dy = y % 8
    for ch in text:
        glyph = FONT[ch]
        for r in range(8 - dy):
            bmp[cy * 320 + cx * 8 + r + dy] = glyph[r]
        scr[cy * 40 + cx] = (fg << 4) | BLACK
        col[cy * 40 + cx] = BLACK
        cx += 1

def koala_to_image(bmp, scr, col):
    """Decode the bitmap data back to a 320x200 RGB preview."""
    img = np.zeros((SCREEN_H, SCREEN_W, 3), np.uint8)
    cy0, cy1 = PHOTO_Y // 8, (PHOTO_Y + PHOTO_H) // 8
    for cy in range(25):
        for cx in range(40):
            s = int(scr[cy * 40 + cx])
            if cy0 <= cy < cy1:
                # multicolor (photo)
                colors = [PAL[0], PAL[s >> 4], PAL[s & 0x0f],
                          PAL[col[cy * 40 + cx]]]
                for r in range(8):
                    byte = int(bmp[cy * 320 + cx * 8 + r])
                    for p in range(4):
                        c = colors[(byte >> (6 - 2 * p)) & 3]
                        x, y = cx * 8 + p * 2, cy * 8 + r
                        img[y, x] = c
                        img[y, x + 1] = c
            else:
                # high-res (text)
                fg, bg = PAL[s >> 4], PAL[s & 0x0f]
                for r in range(8):
                    byte = int(bmp[cy * 320 + cx * 8 + r])
                    for p in range(8):
                        c = fg if (byte >> (7 - p)) & 1 else bg
                        img[cy * 8 + r, cx * 8 + p] = c
    return img

def draw_screen_text(bmp, scr, col):
    draw_text(bmp, scr, col, 0, 0, HEADER, YELLOW)
    draw_text(bmp, scr, col, (SCREEN_W - len(TITLE) * 8) // 2, 120, TITLE, YELLOW)
    y = 128
    for line in LYRICS:
        draw_text(bmp, scr, col, (SCREEN_W - len(line) * 8) // 2, y, line, WHITE)
        y += 8
    draw_text(bmp, scr, col, (SCREEN_W - len(FOOTER) * 8) // 2, 192, FOOTER, GREY)

# ---------------------------------------------------------------------
# 6) Music: note1, note2, note3, duration (1/50 s); 255 = end/loop
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
            ev += [nt, bass, pad, max(1, round(beats * Q))]
    ev[-1] = 100                        # fermata on the final note
    ev += [255, 0, 0, 0]                # end marker
    return ev

# ---------------------------------------------------------------------
# 7) SID frequency table PAL: reg = f * 16777216 / 985248
# ---------------------------------------------------------------------
def build_freq():
    t = []
    for n in range(36, 85):                 # MIDI 36 (C2) .. 84 (C6)
        f = 440.0 * 2 ** ((n - 69) / 12.0)
        reg = round(f * 16777216 / 985248.0)
        t += [reg & 0xff, reg >> 8]
    return t

# ---------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(
        description="Generate the binary data for anthem.asm.")
    ap.add_argument("image", nargs="?", default=DEFAULT_IMAGE,
                    help=f"background image (default: {DEFAULT_IMAGE})")
    ap.add_argument("--crop", default=None,
                    help="crop box left,top,right,bottom (default: tuned "
                         "for the bundled photo, otherwise centered)")
    ap.add_argument("-o", "--outdir", default="build",
                    help="output directory (default: build)")
    args = ap.parse_args()

    if args.crop:
        crop = tuple(int(v) for v in args.crop.split(","))
    elif os.path.basename(args.image) == os.path.basename(DEFAULT_IMAGE):
        crop = DEFAULT_CROP
    else:
        crop = None

    os.makedirs(args.outdir, exist_ok=True)
    canvas = build_picture(args.image, crop)
    photo = canvas[PHOTO_Y:PHOTO_Y + PHOTO_H]
    bmp, scr, col = to_koala(photo, cy0=PHOTO_Y // 8)
    draw_screen_text(bmp, scr, col)

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
        print(f"{name:<11} {len(data):>5} bytes")
    preview = koala_to_image(bmp, scr, col)
    Image.fromarray(preview).save(os.path.join(args.outdir, "image_320x200.png"))

if __name__ == "__main__":
    main()
