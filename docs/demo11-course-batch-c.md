# Demo 1-1 music batch C and fix batch D

Date: 2026-10-26. These are candidate checkpoints. They are not the current
head.

## Music batch C

The candidate descends from fix batch B and installs the remaining cheap-demo
songs of the `$44:A008` group. Song `54` is already present from the Star
World work.

| Song | Group slot | Payload |
| --- | --- | ---: |
| `55` | `$44:A008` slot 1 | 1995 |
| `56` | `$44:A008` slot 2 | 3626 |
| `57` | `$44:A008` slot 3 | 3934 |

| Item | Value |
| --- | --- |
| Target | `demo11-music-batch-c` |
| Base | `demo11-fix-batch-b` |
| ROM SHA-256 | `39113adc2083ead993011db37e1e66d57bfcf400f126ecf6a50f255f2ec9505a` |

## Fix batch D

The candidate adds five extended graphics IDs from 7hero. Rooms `0x00E`,
`0x01F` and `0x149` select them.

| ID | Compressed size |
| --- | ---: |
| `11C` | 2428 |
| `1A7` | 2931 |
| `203` | 2681 |
| `204` | 2091 |
| `205` | 2856 |

| Item | Value |
| --- | --- |
| Target | `demo11-fix-batch-d` |
| Base | `demo11-music-batch-c` |
| ROM SHA-256 | `f7f88f3b3819672545d52df31788d241d05c7a260bbd61800288f65ec1a92401` |
| Native binary SHA-256 | `23854e24ab4341182507c0f625c755c5169a8caa6f7f6d0a234320e71517300c` |
| Allocation | file offset `0x1D4328`, 13155 bytes |

## Verification

`tools/qualify_demo11_music_batch_cd.py` checks both recipe identities, the
derived payloads, the RATS blocks, the graphics data, the reference captures and
the native captures.

| Translevel | Head | Music batch C | Fix batch D |
| --- | --- | --- | --- |
| `04B` | stall `12` | gameplay `14` | gameplay `14` |
| `0A5` | stall `12` | gameplay `14` | gameplay `14` |
| `00E` | stall `12` | - | gameplay `14` |
| `01F` | stall `12` | - | gameplay `14` |
| `06D` | stall `12` | - | gameplay `14` |
| `001` | stall `12` | gameplay then map | gameplay then map |

Translevel `001` has no controller input in the script, so the player falls
and the level reloads. That is not a regression.

The reference and native captures match on mode, room, lives and translevel.

The suite now reports **37/37**.

## Limits

- Entry and short gameplay are the claims.
- Songs `3C`, `3F`, `46`, `47`, `53` and `5B` still fail the
  derivation. Low ids `02`, `03`, `05`, `06` and `1A` have no source
  yet.
- About 45 further null extended graphics IDs need batches.
- The candidates are not accepted as the head.

## Next steps

1. Continue graphics batches for the remaining rooms.
2. Investigate the failed song derivations and the low ids.
3. Re-run the survey on the candidate chain and decide the next head.
