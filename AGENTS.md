# AGENTS.md

Guidance for AI coding agents working in this repository.

## Project

C64 demo written in ACME assembly. `src/make_data.py` generates the binary
assets, `src/anthem.asm` is assembled into a CBM program file, and the
result is packed into a D64 disk image.

## Layout

- `src/` — source files (`.asm`, `.py`). Never put generated files here.
- `res/` — input resources (images, ...).
- `build/` — generated output only. Never edit it by hand; it is git-ignored.
- `build.ninja` — the build description (kept at the project root so that
  plain `ninja` works).

## Build

```sh
ninja          # build build/anthem.prg and build/anthem.d64
ninja clean    # remove build/
```

All build outputs must go to `build/`. Do not commit anything from `build/`.

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
- The Ninja variable for the output directory is `outdir`, not `builddir`.
  Ninja 1.13 stores `.ninja_log` inside `$builddir`, which would break
  `ninja clean`.
