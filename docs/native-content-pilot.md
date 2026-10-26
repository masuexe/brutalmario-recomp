# Native external graphics pilot

## Result and scope

`demo11-native-pack-pilot` is an isolated native-only descendant of
`demo11-sprites-orphan-cleanup`. It removes one 3,001-byte compressed graphics
stream from the derived ROM and supplies it through an external file. The
stream is cheap_demo ExGFX `101`, installed as recipient ExGFX `FFD` in room
`005`. The already reviewed recipe is `config/restorations/demo11-star1-gfx.json`.

The lower-left Star World entry/movement fixture and an unchanged Boss corridor,
door and room `0xBC` route match fresh native controls at 42 dump points. This
qualifies external resource delivery and this bank split, not a complete course
or Boss clear, new executable modules, or the full content-restoration goal.

## Addressing and implementation

The descendant clears file `0x1B0008..0x1B0BC0` inclusive. It changes only
the ExGFX `FFD` pointer at file `0x0A2CFF` from `$36:8008` to `$B6:8008`.
The RATS header remains; no claim is made that the legacy ROM allocator can
immediately reclaim the protected block.

The pilot runtime gives raw bank `$B6`'s upper half an independent, immutable
host backing. The `$36` view retains the cleared payload. The pack loader checks
the exact descendant ROM hash, payload length and SHA-256 before simulation.
Missing, corrupt, truncated and oversized packs fail startup. The wrapper and
practice launcher select and verify the pinned pack automatically.

For this first pilot, the loader allocates a contiguous copy of the 4 MiB
derived image and restores the external payload into that view. Only `$B6`
resolves to this view. This preserves existing direct-pointer span semantics
without page-sized buffer overreads. It costs approximately 4 MiB of extra host
memory. It does not enlarge guest WRAM, replace the engine, or reinsert the
payload into the ordinary cartridge backing.

`patches/runtime/0008-native-content-bank.patch` hooks the cartridge resolver,
load and free paths only for this target. Normal CPU reads and `RomPtr` reach
the resolver; interpreter bus reads reach CPU reads; DMA/HDMA use `snes_read`
and cartridge reads. Existing runtime patches and original targets stay intact.
The feature patch and generated header are hash-pinned in build/capture receipts.
Unknown local feature overrides are rejected instead of discarded.

No generated function in either comparison is in bank `$36` or `$B6`. The
qualifier checks that boundary. Synthetic resolver tests cover independent bank
contents, the start/end of the resource, adjacent banks, low addresses, WRAM
exclusion and mount/reload/clear behavior. This is a fixed data-bank mapping,
not a general executable overlay, arbitrary pointer wrapping implementation,
or dynamic mapping/savestate protocol.

## Identities

| Artifact | SHA-256 |
| --- | --- |
| Frozen control ROM | `eccde6612343e9513e6903264f21b80d3a9a02d7f11199100e5907531232ff40` |
| Pilot ROM | `3da980ccd8ad57b9c2bd4628a63e5dd7a0fbe6e7a72b49bee691cb013f1a9865` |
| Pilot native executable | `9e4b31c8f481c1646e70f9c8cd13b3093774f4f7f102b96daca7f30ba47b46cd` |
| External compressed payload | `3a51dd45f2df22d1f2490ca117070a68bfdab33cb03f734ad9e97c59e581a169` |
| Decoded 4,096-byte graphics | `53b3c712f10a30c4f81baa000c4358ea7cebc9c10e3d423d0ed4124f7899fcbf` |
| Star World input | `e0cd732f71184cf48a20208246aedbe6fed6a757de383fc3867e26d972448510` |
| Boss regression input | `650b54556ac2111ad97f388fb22b96f04b4e39d1a558e70bd8de3e67316140bc` |
| Final qualification report | `96a6ec150227dea6a9c3bc659d59ddbce8ed96082618e2ae7ded090825612ac1` |

The official donor ROM hash, native runtime source/patch/result hashes,
manifest, generated header, executable, generated-code analysis and input
identities are recorded in the recipes and local receipts. Original ROMs,
captures, user saves and the frozen native binary were preserved.

## Evidence and reproduction

```sh
python3 tools/native_content.py
python3 tools/m1.py scaffold --target demo11-native-pack-pilot
python3 tools/m1.py generate --target demo11-native-pack-pilot
python3 tools/m1.py build --target demo11-native-pack-pilot
python3 tools/qualify_native_content.py --capture-prefix YOUR_FRESH_PREFIX --run
```

Scaffolding refuses an existing directory; skip it for an already prepared
experiment. Preparation requires the pinned official donor and frozen base
images. `tools/restore_star_world_1.py --target demo11-native-pack-pilot` also
delegates to this preparation. Existing files with conflicting bytes are rejected.

Optional practice launch, with a fresh isolated save:

```sh
python3 tools/play_demo_only1.py --restoration demo11-native-pack-pilot --show-room
```

No new manual playtest is required to accept this bounded automatic result.

Final evidence is under `local/captures/native-pack-v2-{control,external}-{star1,boss}`
and `local/captures/native-pack-v2-reject-{missing,corrupt,truncated,oversized}`.
The report is `local/reports/native-pack-v2-final.json`. Recheck without changing
these captures by supplying a fresh report name:

```sh
python3 tools/qualify_native_content.py --capture-prefix native-pack-v2 --report-name YOUR_FRESH_REPORT
```

All 420 comparisons match: full WRAM, VRAM, CGRAM, OAM, SRAM, raw framebuffers,
APU traces, PPU-write traces, register snapshots and DMA traces at 42 dump points.
The qualifier checks sizes, room/gameplay state, movement, completion logs,
pack-resolution telemetry and receipt identities. The Star World capture logs
6,002 asset-pointer resolutions; the unchanged Boss route logs zero. These are
pointer resolutions, not a byte-read count. Four invalid-pack cases also fail
with the expected diagnostics in the real native executable. APU trace equality
is not a separate audible-output or PCM comparison claim.

The existing whole-line suite remains 78/78. The new native pilot has its own
qualification and is not silently added to those historical ROM checks.
All 140 project unit tests pass, including the five compiled-loader tests and
launcher checks for pack validation and stale feature receipts. Logs are
`local/reports/native-content-unit-tests-final.log` and
`local/reports/native-content-line-check-v1.log`.

## Next boundary

Select a blocked sprite with a verified dependency closure. Determine its
bank-local references, shared calls, concurrent code/data needs and required
low WRAM mirrors before choosing an executable mapping. The data-bank pilot
does not establish a safe module context, interrupt/return protocol, AOT
selection rule or complete Boss port. All requested cross-version recovery
remains open beyond the existing accepted content and this qualified pilot.
