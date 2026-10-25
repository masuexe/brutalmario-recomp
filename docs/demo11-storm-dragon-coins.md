# Room 122 Dragon Coin vertical-column fix

The native host now removes all five Dragon Coins without leaving a column of
garbage tiles. This is a runtime correction; no ROM, layout, graphics asset,
sprite, exit, completion rule or music selection changed. The cumulative ROM
remains the unpromoted `demo11-fix-batch-p` candidate.

## Cause and compatibility boundary

The same ROM and input reproduce the column on the old native build, including
pure interpreter execution, but not on default Snes9x. After a pickup, enabled
HDMA channels target the VRAM data ports with the address increment left by
the ordinary tile update. The native PPU accepted those visible-field writes,
producing a vertical column that remains until the area is redrawn.

A diagnostic reference run with
`snes9x_block_invalid_vram_access=disabled` reproduces the native corruption:
the entire 16 KiB tilemap range matches the old native host after pickup.
Default Snes9x rejects those invalid writes. These controls distinguish a PPU
access-policy defect from a graphics transplant or AOT translation defect.

The project PPU patch now rejects HDMA writes to `$2118/$2119` unless forced
blank is active. H-blank during visible scanout does not permit VRAM writes.
Rejected bytes still advance the VRAM pointer according to VMAIN. The HDMA
source cursor continues normally. Other HDMA destinations are unaffected.

CPU and ordinary DMA uploads retain the existing permissive compatibility
policy: accepted Carol scripts use it for graphics changes outside blanking.
This deliberately does not claim universal cycle-accurate VRAM access rules.
The LOVE ANIMAL fireball/sign regression on the rebuilt cumulative candidate
still sets `$14AF=1` and all six graphics slices match their WRAM sources.

## Reproduction and identities

| Item | SHA-256 |
| --- | --- |
| ROM, unchanged | `48891cf75b570e4118f8646f7f216d50505d047edc40341b3d0dccdc8cc3022c` |
| Old native binary | `d8879d7e5d41692d40f1a08b501fad7156469916142d78a62a8817924113a6cb` |
| Rebuilt native binary | `a00a993d366b0cf5ba5cc7498e9df0c5d639d1bb13015825b56ac420e47f1875` |
| Tracked pickup script | `27b88190dc4bfe1dc3c3b1e97a6161ad5da5053db2c8f9b2ba8eb3c9d7a904f9` |
| Reference Snes9x core | `39aff6a57c370035486e1b5ca3d33b99ac31ed5e809a883984bce9be51aecf7c` |

The reference frontend/core use the existing pinned checkout. Capture receipts
record the frontend/native binary, ROM, script and runtime patch identities.
The old binary and its original build receipt are preserved in
`local/backups/storm-coin-pre-fix/`; historical captures/receipts are intact.
The demoOnly1 executable and receipt were also backed up before rebuilding it
for the host regression tests. Other historical builds retain their identities
and need rebuilding before use with the updated runtime manifest.

```sh
python3 tools/m1.py native --target demo11-fix-batch-p \
  --script recomp/inputs/demo11-storm-dragon-coins.script --capture NEW_NAME
python3 tools/qualify_demo11_storm_coins.py
python3 tools/check_demo11_line.py
```

The script uses a practice map-node override, player teleports and damage
immunity to exercise five real pickup collisions. It never writes coin
counters, Map16, VRAM, goal flags or SRAM. This qualifies pickups, not an
unassisted traversal, exit or save/reload.

## Automated evidence

`storm-coins-ref-r2` is the fresh reference. The preserved old binary runs the
same tracked script in `storm-coins-before-r2`. Its tilemap differs from the
reference by 194, 386, 644, 902 and 1,052 bytes after successive pickups.

`storm-coins-fixed-native`, `storm-coins-fixed-optimized` and
`storm-coins-fixed-interpreter` each finish at frame 2,898. In all three:

- Both real coin counters increase from 0 to 5; the fifth pickup grants a life.
- Both 0x3600-byte Map16 planes match the reference at every pickup sample.
- All 16 KiB of tilemap VRAM (`$4000..$7FFF`, byte offsets) match the reference
  at the immediate and delayed samples after every pickup: zero differences.
- Title, file-menu and opening-message framebuffers match the old native build
  byte for byte. The interpreter run reports zero AOT bridge entries.

The qualifier verifies receipts, dump sizes, completion logs and the negative
control; its report is `local/reports/demo11-storm-coins.json`. The ROM-free
`ppu_hdma_vram_test.c` fails against the preserved old PPU source and passes
with the fix, covering both data ports, address increments, forced blank and
legacy CPU/DMA uploads. The existing mosaic, raster, palette and latch tests
also pass. The whole-ROM byte audit remains unchanged.

Final checks: **122/122** unit tests and **45/45** integrated line checks pass.
Logs are `local/reports/storm-coin-unittests-final.log` and
`local/reports/storm-coin-line-check-final.log`. The batch-P byte audit still
reports 386,151 changed bytes inside 495,263 reviewed bytes and zero unexpected
bytes; those are the pre-existing content recipes, not changes from this fix.

## Storm mosaic acceptance

The user subsequently confirmed that the effect appears later and matches
original Demo 1-1. Investigation is closed at their request; parity with
cheap_demo is not established or required. Earlier brightness/edge metrics
did not prove mosaic: inspected historical samples have MOSAIC `$03` (1x1).
They must not be reused as evidence of a thunder-triggered mosaic effect.
