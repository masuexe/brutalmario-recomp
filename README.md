# Brutal Mario Recomp

A faithful native PC port of carol's Brutal Mario / Super Kitiku Mario. Make Demo 1-1 independently playable first, then investigate content missing from that version. **M1 is in progress:** a local Linux native prototype boots Demo 1-1, enters a level, and runs a scripted 6,104-frame session. Fidelity, Windows execution, and custom-boss qualification remain incomplete.

User inputs remain in the sibling `patches/`, `references/`, and `roms/` directories. Inventory tools only read them. The M1 tools prepare a verified ROM copy and execute locally built tools; all downloaded sources, derived ROMs/code, executables, and captures stay under gitignored `local/`.

Reproduce the inventory with Python 3.12 (tested; no third-party packages):

```sh
mkdir -p local/reports
python3 tools/inventory.py ../patches ../references ../roms > local/reports/inventory.json
python3 tools/analyze_m0.py > local/reports/analysis.json
python3 -m unittest discover -s tests -v
```

The second tool uses the supplied directory layout and a verified base-ROM SHA-256. Review those assumptions when changing inputs. It previews two IPS header conventions in memory without saving a target ROM.

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
- [User-reported manual playtests](docs/playtesting.md)
- [Audio baseline and capture reproduction](docs/audio.md)
- [Star-music timing probe](docs/star-audio.md)
- [demoOnly1 boss route and fast native pre-boss entry](docs/boss-entry.md)
- [demoOnly1 death black-screen fix](docs/death-black-screen.md)

Original archives, patches, third-party sources, and ROMs are not included in the repository. Historical versions are not automatically merged.
