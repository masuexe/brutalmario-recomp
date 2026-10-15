# Initial patching and compatibility analysis

Inspected on 2026-10-15. Local measurements, bundled documentation, and unverified inferences are distinguished below.

## Base ROM

Input: `../roms/Super Mario World (U) [!].smc`.

| Property | Observed value |
| --- | --- |
| File size | 524,288 bytes (512 KiB) |
| SHA-256 | `0838e531fe22c077528febe14cb3ff7c492f1f5fa8de354192bdff7137c27f5b` |
| CRC32 | `b19ed489` |
| Copier header | None; .smc does not imply a header |
| Title / mapping | SUPER MARIOWORLD / LoROM, map byte 0x20 |
| Region / revision | 1 / 0 |
| Checksum / complement | a0da / 5f25; base byte sum also equals a0da |
| RESET | $8000 |

The SHA-256 matches the stock base specified by [SuperMarioWorldRecomp's regen.sh](https://github.com/mstan/SuperMarioWorldRecomp/blob/main/tools/regen.sh). No independent archival database verification has been performed.

## IPS offsets

All nine standalone IPS files pass structural parsing and match their archived copies by hash. Each has an exclusive write extent of `0x400200`, with no explicit final-size field. IPS contains no base-ROM digest; valid structure does not establish playability.

Demo 1-1 writes ROM/SRAM size fields at IPS offset `0x81D7`. Standard headerless LoROM places those fields at `0x7FD7`, a difference of 512 bytes. In-memory comparison:

| Operation | Resulting body size | ROM / SRAM size exponents at $7FC0 |
| --- | ---: | --- |
| Apply directly to headerless base | 4,194,816 | 9 / 1 (unchanged stock values) |
| Add 512-byte prefix, apply IPS, remove prefix | 4,194,304 | 12 / 5 (4 MiB / 32 KiB) |

This supports headered IPS coordinates for Demo 1-1. Direct application can retain the original title and checksum/complement relationship while putting modifications at incorrect offsets. Those checks alone do not detect the problem.

The **candidate** correctly aligned headerless Demo 1-1 has SHA-256 `314496f67caf53d1d74873333de366a07a2b2446d7bbb5f27eeeb9aa69894f32` and CRC32 `08ad808b`. It has only been constructed in memory, not saved or run. Its header retains the stock checksum a0da while its actual body sum is 1d59. Record this discrepancy without silently repairing the original patch to satisfy a probe.

The other eight patches also have separate in-memory previews with both prefix conventions in the local JSON. Their base and header assumptions still need individual review; a shared write extent is insufficient proof.

## Bundled compatibility notes: not reproduced locally

- `cheap_demo/cheap_demo.txt` says bsnes, Snes9x 1.51 and later, and some other cores cannot run it. It recommends older uosnesw or snesgt and describes freezes and unfinished content. This does not identify the underlying hardware dependency.
- `cheap_demo/7hero.txt` describes custom sprites failing after overworld-map transitions, possible Snes9x 1.51 freezes, and unfinished doors/checkpoints.
- `demo8/demo8.txt` identifies an unofficial edit and records graphics, music, and overworld-display problems.
- No separate Demo 1-1 compatibility notes were found. Cheap Demo claims must not be generalized to Demo 1-1.

## Reference baseline still needed

Run the Demo 1-1 candidate in a reference core, recording exact emulator version, ROM hash, inputs, initial SRAM, video/audio, and frame state. If a modern core fails, compare against an older working core and identify the first divergence. A suitable ZSNES version has not been verified. No timing or audio compatibility fixes have been made.
