# File-menu background and HDMA state

Date: 2026-10-15. The native file-selection background is restored. Both
renderer choices match the Snes9x file-menu picture on the RGB5 grid. The
opening-message picture also now matches. This is a rendering/state fix;
the remaining one-to-two-tick cross-core timing differences are unchanged.

## Cause

The menu uses BG3 on the main screen (`TM=$04`) and BG1/BG2/OBJ on the
subscreen (`TS=$13`). Its color math depends on window 1 covering the screen.
During the title, HDMA writes `$2126=$00`, `$2127=$ff`. After entering the
menu, HDMA is disabled and those window bounds must remain live.

The beam driver previously disabled HDMA during guest execution and instead
executed the real DMA unit during rendering. The complete-register restoration
added for the [MARIO START flicker fix](ppu-fixes.md) correctly protects live
CPU-written state from raster replay, but also discarded these render-only
HDMA writes. Consequently the menu inherited window bounds `[0,0]` instead
of `[0,255]`, suppressing its subscreen background almost everywhere. Captures
before the complete-register restoration retain `[0,255]`; this was a
regression in that earlier fix, not missing ROM graphics or a new timing bug.

## Fix

The project-owned [beam-driver patch](../patches/runtime/0002-bound-interrupt-execution.patch)
now enables the pinned runtime's existing beam HDMA implementation during
guest execution. CPU and HDMA PPU writes enter the same raster journal.
Rendering replays that history without initializing, priming, or advancing
the real DMA unit a second time. The complete-register restoration remains
in place, preserving the earlier flicker fix.

This also means rendering does not reread HDMA tables after the CPU has
changed their memory, and live HDMA state advances even when scanout is
skipped. No guest instruction, ROM byte, input timing, or user save is edited.
The source and patch hashes are pinned in
[runtime-patches.json](../config/runtime-patches.json). Both target executables
are rebuilt because they share this runtime.

## Validation

- Both native renderer choices match the title and file-menu reference
  pictures: **zero differing RGB5 pixels**. Previously the file-menu sample
  differed at 38,283 pixels.
- The full 6,104-call primary route preserves all eight sampled full WRAM
  images byte for byte against the pre-fix build. Only the file-menu and
  opening-message sampled pictures change; the latter improves from 321
  differing RGB5 pixels to zero. The other six sampled pictures are unchanged.
- All 80 consecutive transition pictures match the pre-fix build exactly
  on the RGB5 grid, including the 42-frame MARIO START interval.
- A full interpreter-only run has zero compiled entries and matches all
  eight compiled-run pictures byte for byte. Sampled stack-page differences
  remain; no complete-state equivalence is claimed.
- The ROM-free `beam_hdma_test.c` uses the real PPU journal and DMA transfer
  implementation with controlled CPU/beam doubles. It verifies persistent
  window state after HDMA disable, no repeated transfer or table reread during
  repeated rendering, continued HDMA state with skipped scanout, and preservation
  of a late CPU screen-enable write. It fails against the pre-fix driver.
- The shared runtime also passes demoOnly1's three-death route: lives decrease
  from five to two and every death returns to overworld mode `$0e`. The fast
  door route still reaches `$177`, and the air-swim probe reaches `$178` with
  swimming active. These are regression checks, not a new full-fight test.
- All **18 project tests pass**. The upstream checkouts remain pinned and
  unmodified; the patch also applies cleanly to a fresh source copy and
  produces the pinned resulting-source hash.

Snes9x 1.63 is the automated comparator. ZSNES 1.51 remains the user-reported
historical baseline and has not been run locally. This fix does not qualify
all HDMA modes, an entire game, or the deferred demoOnly1 victory black screen.

Local evidence is under `local/captures/menu-beam-hdma`, `menu-fix-legacy`,
`menu-fix-full`, `menu-fix-transitions`, `menu-fix-floor`,
`menu-fix-only1-deaths`, and `menu-fix-only1-swim`. Comparison and
negative-test reports are `local/reports/menu-fix-*.json` and
`menu-hdma-negative-test.json`. Captures retain ROM, binary, route, source,
and runtime-patch receipts.

## Reproduction

```sh
python3 tools/m1.py build
python3 tools/m1.py build --target demo-only-1
python3 -m unittest discover -s tests -v
python3 tools/m1.py native --renderer optimized --capture menu-check-new
python3 tools/compare_captures.py \
  local/captures/reference-verified local/captures/menu-check-new
```

Use fresh capture names. Interactive configurations and existing saves are
preserved. The primary executable remains
`local/build/demo-1-1/BrutalMarioDemo11SNESRecomp`.
