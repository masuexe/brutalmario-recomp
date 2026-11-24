# Brutal Mario Recomp

A native PC port of carol's Brutal Mario / Super Kitiku Mario, with separate original-version baselines and a cross-version content-restoration track. The active Public Beta target is **`demo11-native-product-r52`** (all 71 native content packs, bilingual EN/JA runtime localization, Demo 7 English Overworld names, native SNESRecomp mod runtime, and opt-in 16:9 widescreen with Map16 BG1 margin prefill).

## Quick Start: Run & Debug (`demo11-native-product-r52`)

### 1. Interactive play (normal window)

```sh
# Standard play (8:7 square pixels default, isolated saves under local/play/demo11-native-product-r52/)
python3 tools/play_native_target.py

# Launch with 16:9 widescreen enabled and/or language override (en | ja | auto)
BM_WIDESCREEN=1 python3 tools/play_native_target.py --lang en

# Start with all levels unlocked (or warp straight to Special Zone)
python3 tools/play_native_target.py --complete-all
python3 tools/play_native_target.py --special-zone

# Interactive launch directly from the build directory (uses local/build/<target>/)
python3 tools/launch_native.py
```

### 2. Practice & debug cheats

```sh
# Warp directly to any room (0x000..0x1FF), with optional invincibility / air swim
python3 tools/play_native_cheats.py --room 0x105 --invincible
python3 tools/play_native_cheats.py --room 0x0FF --invincible --swim
```

**In-game shortcuts:**
- **`Esc` / `O`**: Open **GAME SETTINGS** (live hot-toggle `Language` `1/2/3`, `Widescreen 16:9` `4/W`, `Sprite Limit` `5`, `Pixel Aspect` `6` for `8:7` 1:1 square pixels vs `4:3` CRT 7:6 pixels, and view installed/active `Mods`).
- **`~` (backquote)**: Open **Practice Cheat Console** (`invincible`, `swim`, `xy X Y`, `lives N`, `music HEX`, `map M X Y`, `teleport ROOM`, `lang en|ja|auto|toggle`, `widescreen on|off|toggle`, `aspect 8:7|4:3|1:1|toggle`, `mods`, `complete`, `help`).

### 3. Useful debug environment variables

| Variable | Effect |
| --- | --- |
| `BM_WIDESCREEN=1` / `0` | Force 16:9 widescreen on (`400x224`) or off (`256x224`) |
| `BM_WIDESCREEN_EXTRA=72` | Override per-side widescreen pixel margin (default `72`) |
| `BM_WS_PREFILL=0` | Disable Map16 BG1 margin prefill for A/B debugging |
| `BM_LANG=en\|ja\|auto` | Override runtime localization language |
| `BM_MOD_OVERRIDES_DIR=<dir>` | Override non-executable `BM_*` packs from a local directory |

### 4. Build, test, and package

```sh
export PATH="/home/harp/.local/bin:$PATH"

# Rebuild current product target (incremental Ninja build)
python3 tools/m1.py --target demo11-native-product-r52 build

# Run targeted widescreen + mod runtime E2E tests
python3 -m unittest tests.test_product_r52_widescreen_and_mods -v

# Run full unit test suite
python3 -m unittest discover -s tests -p "test_*.py" -v

# Build Windows binary + Linux/Windows ROM-free Public Beta ZIPs
python3 tools/package_public_beta.py --target demo11-native-product-r52 --force-rebuild-windows
```

---

## Inventory and Documentation

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
- [World 1 route audit and integration limits](docs/world1-route-audit.md)
- [World 1 room 106 graphics recovery candidate](docs/world1-room106-restoration.md)
- [Independent Forest Star candidate, mechanics and both exits](docs/star-world-forest-restoration.md)
- [Cumulative nine-star candidate and center completion boundary](docs/star-world-center-restoration.md)
- [Lower-inner warp stars and the qualified 100-coin exit](docs/star-world-lower-inner-restoration.md)
- [Lower-inner course/cap music mapping and listening check](docs/lower-inner-music.md)
- [Center damage regression](docs/center-damage-regression.md)
- [Special Warp Star cannon controls and ZSNES 1.51 comparison](docs/center-cannon-flight.md)
- [Sky Star middle-right accepted stage and handoff policy](docs/star-world-middle-right-restoration.md)
- [Star World upper-right accepted restoration](docs/star-world-upper-right-restoration.md)
- [Star World middle-right dependency investigation](docs/star-world-middle-right-investigation.md)
- [Snow Star lower-right accepted gameplay baseline](docs/star-world-lower-right-restoration.md)
- [Deferred listening checks](docs/audio-acceptance-queue.md)
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
- [Demo 1-1 music extraction](docs/demo11-music-extraction.md)
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

The delivery target is the native PC game. The requested cross-version content
does not have to fit in one SFC image or remain playable in an emulator. See the
[native content expansion plan](docs/native-content-expansion.md) for the next
architecture milestone and its verification boundaries.
