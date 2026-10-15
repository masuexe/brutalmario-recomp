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

### Comparison with the user's working base

The user subsequently supplied `../roms/Super Mario World (U).smc` and reported
that direct IPS patching works with this file but not the `[!]` file. Local
byte comparison confirms the distinction is a **512-byte copier header**, not
a different game revision:

| Local file | File size | Copier header | Game-body SHA-256 |
| --- | ---: | ---: | --- |
| `Super Mario World (U) [!].smc` | 524,288 | None | `0838e531fe22c077528febe14cb3ff7c492f1f5fa8de354192bdff7137c27f5b` |
| `Super Mario World (U).smc` | 524,800 | 512 bytes | `0838e531fe22c077528febe14cb3ff7c492f1f5fa8de354192bdff7137c27f5b` |

The complete headered file has SHA-256
`d70c9c7716ad12c674fc7dd744736aa48d4d7b4237f58066be620fda26024872`.
Removing its first 512 bytes gives a byte-identical copy of the pinned base.
Applying `1-1.ips` directly to this headered file and then removing its copier
header produces a byte-identical copy of the **existing research target**,
SHA-256 `314496f67caf53d1d74873333de366a07a2b2446d7bbb5f27eeeb9aa69894f32`.

The preparation script already adds the required prefix before applying the
patch to the headerless pinned base. Therefore the user's observation does
not invalidate existing captures, runtime findings, or generated code. Neither
original input was modified. The comparison was performed in memory; metadata
is recorded in `local/reports/base-rom-comparison.json`.

For manual patching, use the supplied headered file, or explicitly add a
512-byte prefix to the headerless file first. A patcher that automatically
handles copier headers may behave differently. These results establish the
alignment for **Demo 1-1**; other IPS versions still require individual review.

## IPS offsets

All nine standalone IPS files pass structural parsing and match their archived copies by hash. Each has an exclusive write extent of `0x400200`, with no explicit final-size field. IPS contains no base-ROM digest; valid structure does not establish playability.

Demo 1-1 writes ROM/SRAM size fields at IPS offset `0x81D7`. Standard headerless LoROM places those fields at `0x7FD7`, a difference of 512 bytes. In-memory comparison:

| Operation | Resulting body size | ROM / SRAM size exponents at $7FC0 |
| --- | ---: | --- |
| Apply directly to headerless base | 4,194,816 | 9 / 1 (unchanged stock values) |
| Add 512-byte prefix, apply IPS, remove prefix | 4,194,304 | 12 / 5 (4 MiB / 32 KiB) |

This supports headered IPS coordinates for Demo 1-1. Direct application can retain the original title and checksum/complement relationship while putting modifications at incorrect offsets. Those checks alone do not detect the problem.

The correctly aligned headerless Demo 1-1 has SHA-256 `314496f67caf53d1d74873333de366a07a2b2446d7bbb5f27eeeb9aa69894f32` and CRC32 `08ad808b`. It was initially previewed in memory; M1 subsequently saved it with `tools/prepare_rom.py` and booted it in both reference and native hosts. Its header retains the stock checksum a0da while its actual body sum is 1d59. Record this discrepancy without silently repairing the original patch to satisfy a probe.

The other eight patches also have separate in-memory previews with both prefix conventions in the local JSON. Their base and header assumptions still need individual review; a shared write extent is insufficient proof.

## Bundled compatibility notes: not reproduced locally

- `cheap_demo/cheap_demo.txt` says bsnes, Snes9x 1.51 and later, and some other cores cannot run it. It recommends older uosnesw or snesgt and describes freezes and unfinished content. This does not identify the underlying hardware dependency.
- `cheap_demo/7hero.txt` describes custom sprites failing after overworld-map transitions, possible Snes9x 1.51 freezes, and unfinished doors/checkpoints.
- `demo8/demo8.txt` identifies an unofficial edit and records graphics, music, and overworld-display problems.
- No separate Demo 1-1 compatibility notes were found. Cheap Demo claims must not be generalized to Demo 1-1.

## Reference baseline status

The user identifies **ZSNES 1.51** as their known-working environment. This is user-reported evidence; no ZSNES executable has been obtained or run in this workspace. It remains the intended historical behavior baseline, especially for content that modern cores cannot run.

For an independent automated comparison, M1 built Snes9x 1.63 at commit `1bcc369e89f08243e0a462882fb1f3e42e51de3a`. It can display the title and file menu, dismiss the opening message with A, and enter level $105. Opening text appears garbled; whether that is original/incomplete content or a compatibility problem is not established. Reaching one level does not contradict the older packages' documented compatibility problems or establish boss compatibility.

The initial shared-input reference/native run produced eight scene dumps and
a captured reference WAV; its title and file-menu pictures matched after
common 5-bit color quantization, while later scenes differed. Subsequent
[PPU fixes](ppu-fixes.md) and a [timing fix](timing.md) have separate validation
and remaining issues. Audio fidelity is still unqualified. See [m1.md](m1.md)
for the original experiment and links to the follow-up findings.
