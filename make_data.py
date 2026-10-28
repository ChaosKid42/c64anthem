#!/usr/bin/env python3
# =====================================================================
#  make_data.py  -  erzeugt die Binardaten fuer hymne.asm
#
#  Bild   : Multicolor-Bitmap 320x200 (Bundespraesident + 3. Strophe)
#  Musik  : Deutsche Nationalhymne, Melodie nach Joseph Haydn (1797),
#           Es-Dur, 4/4, Viertel = 85 bpm.  Aufbau der 3. Strophe:
#           Stollen (T. 1-4) zweimal, Abgesang (T. 5-12), dessen
#           Schlusszeilen zweimal; Schlussnote mit Fermate.
#
#  Erzeugt:  bitmap.bin   8000 Bytes  Multicolor-Bitmap ($2000)
#            screen.bin   1024 Bytes  Screen-RAM      ($1000, 1000+24)
#            colors.bin   1024 Bytes  Farb-RAM        ($1400, 1000+24)
#            music.bin     380 Bytes  Musikdaten
#            freq.bin       98 Bytes  SID-Frequenztabelle (MIDI 36..84)
#
#  Aufruf:   python3 make_data.py [bild.png]
#            ohne Argument wird data/gen-755.png benutzt; fehlt die Datei,
#            wird ein einfacher Flaggen-Hintergrund gezeichnet.
#
#  Abhaengigkeiten: numpy, pillow
# =====================================================================
import sys, os
import numpy as np
from PIL import Image

# ---------------------------------------------------------------------
# 1) Kleine 3x5-Schrift, Glyphen werden in x-Richtung 2-fach skaliert
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
UML = {'\u00c4':'A', '\u00d6':'O', '\u00dc':'U'}      # A-Uml, O-Uml, U-Uml

WHITE = (236, 240, 245)
GOLD  = (250, 205, 110)
GREY  = (170, 175, 185)

def _plot(a, x, y, c):
    if 0 <= y < a.shape[0] and 0 <= x < a.shape[1]:
        a[y, x] = c

def draw_text(a, x, y, text, colour):
    """3x5-Schrift, 2 Pixel breit je Fontpixel, 8 Pixel Vorschub."""
    cx = x
    for ch in text:
        dots = False
        if ch in UML:
            ch, dots = UML[ch], True
        rows = FONT[ch].split(',')
        if dots:                                   # Umlautpunkte eine Zeile hoeher
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
# 2) Bildschirmbild 320x200 zusammenbauen
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
    """Ersatzhintergrund, falls kein Foto vorhanden ist."""
    a = np.zeros((200, 320, 3), np.float64)
    for y in range(200):                           # Schwarz-Rot-Gold
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

    # Abdunkeln: Titelstreifen oben, Verlaufsband unten fuer den Liedtext
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
# 3) Umwandlung in ein Multicolor-Bitmap (Koala-Format)
#    je 8x8-Zeichenzelle: 32 Multicolor-Pixel, Hintergrund = Farbe 0,
#    dazu 3 Farben aus den 16 C64-Farben (beste Naeherung)
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
            cand = [int(c) for c in np.argsort(-cnt)[:6] if c != 0]  # nie Farbe 0
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
# 4) Musik: Note1, Note2, Note3, Dauer (1/50 s); 255 = Ende/Schleife
#
#    Melodie: Es-Dur, 4/4, Viertel = 85 bpm  ->  eine Viertel = 35 Frames
#    (50 Hz).  Aufbau der 3. Strophe:
#      Stollen   T1-4   "Einigkeit und Recht und Freiheit /
#                        fuer das deutsche Vaterland!"      (2x)
#      Abgesang  T5-8   "Einigkeit und Recht und Freiheit /
#                        sind des Glueckes Unterpfand."
#                T9-12  "Blueh im Glanze dieses Glueckes, /
#                        bluehe, deutsches Vaterland!"       (2x)
#    Die Noten folgen der Haydn-Melodie (Es-Dur) exakt.
# ---------------------------------------------------------------------
Q = 35              # Viertelnote (Frames bei 50 Hz)

CHORDS = {'Eb': (39, 58),     # Bass 39 = Es2, Flaeche 58 = B3
          'Bb': (46, 62),     # 46 = B2,      62 = D4
          'Ab': (44, 60)}     # 44 = As2,     60 = C4

# Takt fuer Takt: ([(MIDI-Note, Laenge in Vierteln), ...], Harmonie)
BARS = [
    # --- Stollen (T1-T4) -------------------------------------------
    ([(63,1.5),(65,0.5),(67,1),(65,1)],                    'Eb'),  # Ei-nig-keit und
    ([(68,1),(67,1),(65,0.5),(62,0.5),(63,1)],             'Eb'),  # Recht und Frei-heit
    ([(72,1),(70,1),(68,1),(67,1)],                        'Ab'),  # fuer das deut-sche
    ([(65,1),(67,0.5),(63,0.5),(70,2)],                    'Eb'),  # Va-ter-land
    # --- Abgesang, 1. Haelfte (T5-T8) ------------------------------
    ([(65,1),(67,1),(65,0.5),(62,0.5),(58,1)],             'Bb'),  # Ei-nig-keit und
    ([(68,1),(67,1),(65,0.5),(62,0.5),(58,1)],             'Bb'),  # Recht und Frei-heit
    ([(70,1),(68,1),(67,1.5),(67,0.5)],                    'Eb'),  # sind des Glue-ckes
    ([(69,1),(69,0.5),(70,0.5),(70,2)],                    'Bb'),  # Un-ter-pfand
    # --- Abgesang, 2. Haelfte (T9-T12) -----------------------------
    ([(75,1.5),(74,0.5),(74,0.5),(72,0.5),(70,1)],         'Eb'),  # Blueh im Glan-ze
    ([(72,1.5),(70,0.5),(70,0.5),(68,0.5),(67,1)],         'Ab'),  # die-ses Glue-ckes
    ([(65,1.5),(67,0.25),(68,0.25),(70,0.5),(72,0.5),
      (68,0.5),(65,0.5)],                                  'Bb'),  # blue-he, deut-sches
    ([(63,1),(67,0.5),(65,0.5),(63,2)],                    'Eb'),  # Va-ter-land
]

# Stollen 2x, Abgesang 1. Haelfte, Abgesang 2. Haelfte 2x
STRUCTURE = [0,1,2,3, 0,1,2,3, 4,5,6,7, 8,9,10,11, 8,9,10,11]

def build_music():
    ev = []
    for b in STRUCTURE:
        notes, ch = BARS[b]
        bass, pad = CHORDS[ch]
        for nt, beats in notes:
            ev += [nt, bass, pad, max(1, int(round(beats * Q)))]
    ev[-1] = 100                        # Fermate auf der Schlussnote
    ev += [255, 0, 0, 0]                # Endmarke
    return ev

# ---------------------------------------------------------------------
# 5) SID-Frequenztabelle PAL: reg = f * 16777216 / 985248
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
    img = sys.argv[1] if len(sys.argv) > 1 else "data/gen-755.png"
    canvas = build_picture(img)
    bmp, scr, col = to_koala(canvas)

    out = {
        "bitmap.bin": list(bmp),
        "screen.bin": list(scr) + [0] * 24,
        "colors.bin": list(col) + [0] * 24,
        "music.bin":  build_music(),
        "freq.bin":   build_freq(),
    }
    for name, data in out.items():
        open(name, "wb").write(bytes(data))
        print("%-11s %5d Bytes" % (name, len(data)))
    Image.fromarray(canvas).save("bild_320x200.png")

if __name__ == "__main__":
    main()