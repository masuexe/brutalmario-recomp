# PPU transition fixes

Date: 2026-10-15. Fixes the reported vertical-stripe mosaic effect and alternating corrupted background behind `MARIO START!`. The existing native executable has been rebuilt at `local/build/demo-1-1/BrutalMarioDemo11SNESRecomp`.

Follow-up: complete live-register restoration exposed a regression in the
driver's render-only HDMA ownership, suppressing the file-menu background.
The [HDMA state fix](menu-background.md) moves those transfers to the live
beam while preserving this raster restoration and the MARIO START fix.
Measurements below describe the original transition-fix checkpoint.

The later [shop selection fix](shop-cursor.md) additionally preserves and
replays CGRAM palette/port state for scanline color changes. The later
[counter-read fix](loading-timing.md) corrects the PPU2 bus and counter byte
selectors; its snapshot extension and timing results are documented separately.

## Reproduction and causes

The interactive configuration uses `NewRenderer = 1`. The original automated M1 route selected `NewRenderer=0`, so it did not cover the optimized renderer's mosaic cache.

1. **Mosaic became vertical stripes.** The optimized renderer built `mosaicModulo` only in `ppu_runLine(ppu, 0)`. The beam-aligned frame driver renders visible lines 1 through 224 without that pre-render call. When mosaic was enabled, the zero-initialized vertical lookup sampled row zero for every scanline. Moving cache refresh to every scanline entry also handles raster writes that change mosaic size within a field.
2. **`MARIO START!` flashed an obsolete background.** Raster scanout reconstructs a completed field. The old `ppu_rasterRenderEnd` only replayed writes from the new field, leaving stale register values behind when that journal had no corresponding entry. A late write on line 224 may already be live guest state without being applied to the preceding visible scanout. This rolled the main/subscreen masks back on alternating frames: the affected run switched between `TM/TS = 0x10/0x04` and `0x15/0x02`. Saving the complete live display-register file and write latches at RenderBegin, and restoring them at RenderEnd, preserves the guest state independently of replay coverage.

The second problem exists independently of the mosaic cache. Fixing only the cache changed the obsolete background from stripes into colored blocks, while the alternating-frame corruption remained.

## Implementation

- [Runtime patch](../patches/runtime/0001-fix-mosaic-and-raster-restore.patch): per-scanline mosaic cache refresh and complete post-raster register/latch restoration.
- [Patch manifest](../config/runtime-patches.json): SHA-256 pins for upstream source, patch, and resulting source.
- [Runtime override builder](../tools/runtime_patches.py): materializes patched `ppu.c` under ignored `local/runtime/`, checks all hashes, and selects that source in the experiment's CMake target. The pinned upstream checkout remains clean.
- [M1 runner](../tools/m1.py): includes runtime patch identity in captures, checks the executable's build receipt, and supports explicit renderer and input-script selection.

The ROM, IPS, recompiled CPU functions, gameplay logic, interactive settings, and user saves are not edited. The source changes affect PPU rendering and restoration of its live state.

## Validation

Both synthetic tests reproduce failures against the pinned unmodified PPU and pass with the patched runtime:

- `tests/ppu_mosaic_test.c`: analytic 2D tile patterns, both renderers, 2bpp/4bpp, mosaic sizes 1 through 16, visible-only scanout, mid-field size changes, and disabling mosaic.
- `tests/ppu_raster_restore_test.c`: late line-224 screen writes, new fields without writes, repeated idle-field replay, complete display-register preservation, scroll/Mode 7 write latches, and OAM port preservation.

All **11 project tests** pass. The pinned upstream raster-journal and HD Mode 7 tests also pass when compiled against the patched PPU.

The optimized renderer also completed the full 6,104-frame M1 smoke route in about 36 seconds, including level entry, movement, jumps, death, and return to the overworld. All eight sampled full-WRAM images match the initial native baseline exactly, and the compiled-entry/interpreted-opcode counters are unchanged. The final presentation capture also shows square mosaic blocks and a clean black start-screen background.

Game-level captures reproduce the user's optimized-renderer path. In 80 consecutive observations, guest WRAM is identical before and after the raster-state fix. The 42-frame `MARIO START!` interval (frames 2155 through 2196) now has a stable black background and text. Every frame matches the Snes9x reference's stable start screen after RGB5 normalization; the mosaic-only version alternated between the correct screen and stale colored background.

Local evidence:

```text
local/captures/transitions-before/        original optimized-renderer presentation
local/captures/transitions-after/         mosaic-only intermediate presentation
local/captures/transition-dense/          intermediate consecutive frame observations
local/captures/transitions-reference/     reference start-screen snapshot
local/captures/transitions-fixed/         both fixes, consecutive observations
local/captures/transitions-present-fixed/ both fixes, final presentation captures
local/reports/transition-fix-validation.json
```

This validates these transition defects, not complete game fidelity. Broader timing/audio differences and custom-boss acceptance from M1 remain open. The historical ZSNES 1.51 baseline remains user-reported.

## Repeat the checks

```sh
python3 -m unittest discover -s tests -v
python3 tools/m1.py build
python3 tools/m1.py native --renderer optimized \
  --script recomp/inputs/transition-flicker.script \
  --capture transition-check-new
```

Use a new capture name each time. The script reaches the first course and captures every guest frame through the start-screen interval. Existing interactive configurations are not rewritten by the renderer override.
