# Brutal Mario Recomp

A native PC port of carol's Brutal Mario / Super Kitiku Mario, with separate original-version baselines and a cross-version content-restoration track. The accepted Demo 1-1 checkpoint has 68 AOT-eligible variants; demoOnly1 has separate bounded Boss, shop and map regressions. **Current restoration:** the accepted cumulative baseline restores the lower-left Star World course and upper-left cave. A new Snow Star candidate restores the lower-right course's missing music, graphics and ice Ptooie, with normal/secret exits and DK saves checked automatically. Consolidated manual Snow Star gameplay/listening acceptance remains pending. Routine AOT work uses automated qualification instead of a manual gate after every batch. Whole-game fidelity and content recovery remain incomplete.

User inputs remain in the sibling `patches/`, `references/`, and `roms/` directories. Inventory tools only read them. The M1 tools prepare a verified ROM copy and execute locally built tools; all downloaded sources, derived ROMs/code, executables, and captures stay under gitignored `local/`.

Reproduce the inventory with Python 3.12 (tested; no third-party packages):

```sh
mkdir -p local/reports
python3 tools/inventory.py ../patches ../references ../roms > local/reports/inventory.json
python3 tools/audit_content_versions.py --prepare-local-roms
python3 -m unittest discover -s tests -v
```

The second tool verifies the supplied base and nine patches against `config/content-versions.json`, compares their image layouts and prepares isolated candidate copies under gitignored `local/content-versions/`. The two original target images remain separate. Donor preparation is not gameplay qualification; see the restoration roadmap for current limits.

- [Content-restoration roadmap and reduced manual checkpoints](docs/content-restoration.md)
- [Snow Star lower-right cumulative candidate](docs/star-world-lower-right-restoration.md)
- [Star World upper-left cave accepted restoration](docs/star-world-upper-left-restoration.md)
- [Star World lower-left course restoration candidate](docs/star-world-1-restoration.md)
- [Versions and input inventory](docs/versions.md)
- [Source analysis](docs/source-analysis.md)
- [Patching and compatibility](docs/compatibility.md)
- [Recompilation feasibility and M1 experiment](docs/recomp-feasibility.md)
- [M1 results and reproduction](docs/m1.md)
- [Mosaic and start-screen rendering fixes](docs/ppu-fixes.md)
- [File-menu background and persistent HDMA state fix](docs/menu-background.md)
- [demoOnly1 shop selection highlight and raster palette fix](docs/shop-cursor.md)
- [Timing investigation and resumable interrupt fix](docs/timing.md)
- [Boot-load timing and the corrected CPU/APU clock ratio](docs/boot-timing.md)
- [Loading boundaries and the PPU counter-read protocol](docs/loading-timing.md)
- [Measured static recompilation coverage](docs/aot-coverage.md)
- [Instruction timing for the pointer-read AOT leaf](docs/aot-timing.md)
- [Indexed table-read AOT expansion](docs/aot-indexed.md)
- [WRAM-store AOT expansion](docs/aot-wram.md)
- [PPU write-event qualification before AOT promotion](docs/aot-mmio-events.md)
- [Palette-port event timing and two-loop AOT expansion](docs/aot-palette.md)
- [Indexed coordinate arithmetic and mixed accumulator widths](docs/aot-coordinate.md)
- [Nested coordinate caller and deadline continuation](docs/aot-caller.md)
- [Indexed sprite-entry loop and nested calls](docs/aot-sprite.md)
- [Sprite-entry append loop and preserved Y](docs/aot-sprite-y.md)
- [Bank-15 coordinate pair and word subtraction](docs/aot-coordinate15.md)
- [Pointer and indexed-phase helper batch](docs/aot-helpers.md)
- [Word buffer-index AOT expansion](docs/aot-buffer-index.md)
- [Buffer-value AOT expansion and word stack order](docs/aot-buffer-read.md)
- [Buffer-match flag AOT expansion and index-width correction](docs/aot-buffer-flags.md)
- [WRAM record writers and nested-call AOT expansion](docs/aot-records.md)
- [User-reported manual playtests](docs/playtesting.md)
- [Audio baseline and capture reproduction](docs/audio.md)
- [Practice audio synchronization and WSLg output workaround](docs/audio-sync.md)
- [Star-music timing probe](docs/star-audio.md)
- [demoOnly1 boss route and fast native pre-boss entry](docs/boss-entry.md)
- [demoOnly1 map teleport, practice selector and location readout](docs/level-select.md)
- [Lemmy castle spotlight seams investigation](docs/lemmy-mask.md)
- [demoOnly1 all-completion and DK-coin practice cheat](docs/completion-cheat.md)
- [Star World save checks, entrance survey and next restoration](docs/star-hub-survey.md)
- [demoOnly1 death black-screen fix](docs/death-black-screen.md)

Original archives, patches, third-party sources, and ROMs are not included in the repository. Historical versions are not automatically merged.
