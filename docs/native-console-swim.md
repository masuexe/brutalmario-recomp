# Frame-scoped air-swim correction

## Defect and repair (2026-11-02)

The user found that entering `swim` a second time did not restore normal motion.
The old hold loop set level-water byte $85 to 1 every frame; disabling the toggle
only stopped writing. The previously forced 1 could therefore remain active.

Patch 0012 saves the genuine $85 immediately before a gameplay frame, temporarily
applies the override, and restores the underlying value after guest execution.
Outside mode 14 the cheat does not force water. A changed room owns its new
water flag; a guest write clearing water is also preserved. The control and
hold apply at the actual frame boundary, including the run-ahead wrapper.
Normal snapshots/dumps after the frame retain the genuine level-water flag.

Disabling `swim` never directly clears player-in-water byte $75. On the next
simulation frame the game's water logic uses the true level flag and local
water interaction bits. This restores dry-land movement while retaining real
swimming in full-water courses and local water tiles. It also permits leaving
local water normally after the cheat is disabled. Existing water detection is
reused; no new approximation based on player position is introduced.

## Verification

`tests/test_console_swim.py` materializes the pinned runtime patch chain,
compiles the actual `CheatExecute`, `TickCheatHolds` and `FinishCheatHolds`, and
executes the recipient ROM's water decision at $00EA45 through the real 65816
interpreter. The ROM hash must match r14 before the test runs. Execution stops
at the real dry return or the water branch, without simulating the entire PPU,
movement loop or a course. Fixtures explicitly seed interaction bits and WRAM.

After three enabled frames and the second actual `swim` command:

| Underlying environment | $85 after frame | $75 after natural decision |
| --- | ---: | ---: |
| Dry land | 0 | 0 |
| Fully underwater course | 1 | 1 |
| Local water tiles in a dry course | 0 | 1 |
| Subsequently leave those local tiles | 0 | 0 |

The tests additionally check loading mode, new-room water ownership and guest
clearing of the level flag. Eleven targeted tests pass, covering swim, the
retained teleport patch, patch-chain upgrades, product integrity, launch
settings and console installation. A fresh complete suite was not run: the
previous full suite's eight stale demoOnly1 binary-receipt failures remain
explicitly deferred; no old receipt is relabeled as current.

Both platform candidates pass `tools/product.py verify`. Closed-console
startup retains 12 exact parent dump files on each platform. Fresh Linux
queue/room fixtures also exercise enabled air-swim in room 00F and water-room
loading at 120; these are assisted placements, not normal traversal.

## Delivery and identities

Target/ROM remains r14:
`393010107b0398756886cdcc2cc174661a4d49ea51ef6bc3891d31d06d31618b`.

- Linux executable:
  `271ff9053c94e2be33f4a83db4434e496cf3e57b3581bd4635d0e781b7a8b103`.
- Windows executable:
  `909a322331e6b694ec333ea11d0b37120d450ec9b852dcdbacee5d35c5a75f30`.
- Linux archive: `local/release/product-r14-swim-fix-linux-v1.zip`, SHA-256
  `d52f4a1c24587ae09a698cec0b22a1d1e1aedb490fd731fd14d9d7481d5a4980`.
- Windows archive: `local/release/product-r14-swim-fix-windows-v1.zip`, SHA-256
  `4e3142266535c63fc4a248a853daf79caa8f9582c28cd136f36d4c879cda1405`.

The host object is rebuilt with the new pinned patch; other qualified link
objects, including the cached launch-setting resolver, are retained. Evidence,
source materialization, compile/link commands, interpreter-test logs, runtime
receipts and package verification are under `local/diagnostics/swim-fix-v1/`.

The user requested Windows delivery to `D:/tmp`. The fresh folder
`D:/tmp/product-r14-swim-fix-windows-v1` and matching ZIP were copied there with
all file hashes checked. Launch `play.bat` inside the folder. Python 3 is
required. Prior builds, delivery folders and user saves remain intact.

This supersedes swim-toggle claims for earlier console packages. The retained
teleport correction is included; the separate overworld-music ROM repair is
still outside these r14 packages. Whole-game restoration remains open.

The extended room 120 capture reaches mode 14 with player action 0 and both
$85/$75 equal 1 after another 600 frames. The earlier entry samples were still
in pipe action 6, so their $75=0 was not treated as a normal swimming check.
