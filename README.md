# Anthem — "Das Lied der Deutschen" (3rd verse) for the Commodore 64

A small C64 demo that shows a multicolor bitmap of the Federal President
together with the text of the third verse of the German national anthem,
and plays a three-voice SID arrangement of Joseph Haydn's melody. The
screen text is rendered with the original C64 character ROM font.

The program is written in ACME assembly and built with Ninja.

## Requirements

| Tool | Purpose |
|------|---------|
| [Ninja](https://ninja-build.org/) | build system |
| [ACME](https://sourceforge.net/projects/acme-crossass/) | 6502 cross assembler |
| Python 3 with `numpy` and `pillow` | generates the binary data |
| [VICE](https://vice-emu.sourceforge.io/) (`c1541`, `x64`) | disk image tool and emulator |

## Build

```sh
ninja          # builds build/anthem.prg and build/anthem.d64
ninja run      # builds and starts the program in VICE
ninja clean    # removes the build directory
```

## Run

```sh
ninja run      # build and start build/anthem.prg in x64sc
```

Or open the disk image manually:

```sh
x64 build/anthem.d64
```

Or inside VICE:

```
LOAD"ANTHEM",8,1
RUN
```

## Project structure

```
.
├── build.ninja                build description
├── src/
│   ├── anthem.asm             6502 source (ACME syntax)
│   └── make_data.py           generates the binary data
├── res/
│   ├── steinmeier.jpg         portrait of the Federal President
│   └── anthem_image_c64.png   reference preview of the picture
└── build/                     generated output (git-ignored)
```

## How it works

`make_data.py` crops the portrait to a 320x112 banner, converts the
320x200 screen to a Koala-style multicolor bitmap and writes the bitmap,
screen and color data. The header, title, lyrics and footer are drawn
directly into the Koala data using glyphs from the C64 character ROM, so
the text stays crisp. The script also generates the SID frequency table
and the music data.

`anthem.asm` sets up the VIC-II for a multicolor bitmap, copies screen and
color data into place, initializes the SID and installs a raster IRQ that
plays the music.

The build produces:

- `build/anthem.prg` — CBM program file with load address `$0801`
- `build/anthem.d64` — 35-track disk image containing `ANTHEM`

## Using a different picture

The build uses `res/steinmeier.jpg`. To try another image, run the script
manually (it writes the generated data into `build/`):

```sh
python3 src/make_data.py path/to/photo.png --crop L,T,R,B --outdir build
```

Without an image a simple black-red-gold flag background is drawn. The
crop box is optional; without it the photo is center-cropped to the banner
aspect ratio. `res/anthem_image_c64.png` is only a reference preview; it
is not used as build input.

## Credits

- Portrait: Olaf Kosinsky, *2015-12 Frank-Walter Steinmeier SPD
  Bundesparteitag*, CC BY-SA 3.0 de, via Wikimedia Commons.
- Melody: Joseph Haydn (1797).
- Text: third verse of *Das Lied der Deutschen* by Hoffmann von
  Fallersleben.
- Font: glyphs from the C64 character ROM (Commodore).
