# AGENTS.md

Guidance for AI coding agents working in this repository.

## Project

C64 demo written in ACME assembly. `src/make_data.py` generates the binary
assets, `src/anthem.asm` is assembled into a CBM program file, and the
result is packed into a D64 disk image.

## Layout

- `src/` — source files (`.asm`, `.py`). Never put generated files here.
- `res/` — input resources: `steinmeier.jpg` (portrait) and
  `anthem_image_c64.png` (reference preview, not a build input).
- `build/` — generated output only. Never edit it by hand; it is git-ignored.
- `build.ninja` — the build description (kept at the project root so that
  plain `ninja` works).

## Build

```sh
ninja          # build build/anthem.prg and build/anthem.d64
ninja clean    # remove build/
```

All build outputs must go to `build/`. Do not commit anything from `build/`.

## Toolchain

The tools are installed system-wide (no local toolchain setup needed):

| Tool | Version | Notes |
|------|---------|-------|
| ACME | 0.97 ("Zem") | `acme` |
| VICE | 3.10 | `x64sc` (GTK), `x64` (SDL), `c1541` |
| Python 3 | — | needs `numpy` and `pillow` |
| Ninja | — | `ninja` |

- The sandbox has no X server, so the VICE GUI cannot open a display
  (`x64sc`/`x64` fail with "cannot open display"). Run headless with
  `x64sc -console -autostart build/anthem.prg -warp -limit 500`.
  `xvfb-run`/`Xvfb` also fail because the sandbox blocks socket creation.
- `c1541` prints `OPENCBM: opening dynamic library libopencbm.so failed!`
  but still writes the D64 correctly (it falls back to its internal D64
  driver), so this warning is harmless.
- ACME has no `--list` option; use `-l <file>` for a symbol list or
  `--vicelabels <file>` for VICE-format labels.

## Conventions

- Assembly uses ACME syntax; comments and labels are in English.
- `make_data.py` writes into the directory given by `--outdir` (default
  `build`). Keep it that way so the build stays self-contained.
- The assembler is run from inside `build/`, so the `!bin` directives
  resolve the generated `.bin` files there and `!to "anthem.prg", cbm`
  writes the program together with its load address.
- Do not assemble the final program with `acme -o`: `-o` overrides `!to`
  and drops the CBM load address, producing a headerless binary.
- Keep the generated data deterministic so incremental builds stay stable.
- Screen text is drawn into the bitmap data in high-resolution format
  (8 pixels per byte) with glyphs from the C64 character ROM, embedded in
  `make_data.py` (`FONT`). The photo is stored in multicolor format
  (4 fat pixels per byte); `anthem.asm` switches between the two modes
  with a raster split. The ROM has no umlauts; `normalize()`
  transliterates Ä/Ö/Ü to A/O/U.
- On PAL the first visible raster line is 51, so screen row `y` starts at
  raster line `51 + 8*y`. The raster split in `anthem.asm` uses line 59
  (photo, `y=8`) and line 171 (text, `y=120`); the music IRQ is at line
  251 (bottom border).
- The C64 bitmap is cell-major: cell `(cx, cy)`, row `r` lives at
  `bmp[cy*320 + cx*8 + r]`, with screen/color at `cy*40 + cx`.
- The text band is solid black and the photo occupies `y=8..119`, so the
  text stays readable.
- The Ninja variable for the output directory is `outdir`, not `builddir`.
  Ninja 1.13 stores `.ninja_log` inside `$builddir`, which would break
  `ninja clean`.
