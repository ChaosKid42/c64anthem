# Anthem — "Das Lied der Deutschen" (3rd verse) for the Commodore 64

A small C64 demo that shows a multicolor bitmap of the Federal President
together with the text of the third verse of the German national anthem,
and plays a three-voice SID arrangement of Joseph Haydn's melody.

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
ninja clean    # removes the build directory
```

## Run

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
│   └── anthem_image_c64.png   reference preview of the picture
└── build/                     generated output (git-ignored)
```

## How it works

`make_data.py` renders a 320x200 picture, converts it to a Koala-style
multicolor bitmap and writes the bitmap, screen and color data. It also
generates the SID frequency table and the music data.

`anthem.asm` sets up the VIC-II for a multicolor bitmap, copies screen and
color data into place, initializes the SID and installs a raster IRQ that
plays the music.

The build produces:

- `build/anthem.prg` — CBM program file with load address `$0801`
- `build/anthem.d64` — 35-track disk image containing `ANTHEM`

## Using a different picture

`make_data.py` accepts an optional background image:

```sh
python3 src/make_data.py path/to/photo.png --outdir build
ninja
```

Without an image a simple black-red-gold flag background is drawn.
`res/anthem_image_c64.png` is only a reference preview; it is not used as
build input.
