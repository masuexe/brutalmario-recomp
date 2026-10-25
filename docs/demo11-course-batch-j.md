# Demo 1-1 music batch J and graphics batches K1-M

Date: 2026-10-26. These are candidate checkpoints. They are not the current
head.

## Music batch J

Raw group slices from cheap-demo, on top of fix batch I.

| Song | Group |
| --- | --- |
| `36` | `$2A:A008` slot 2 |
| `3B` | `$2A:E008` slot 3 |
| `3E` | `$2B:8008` slot 2 |
| `42` | `$3F:8008` slot 2 |
| `43` | `$3F:8008` slot 3 |

| Item | Value |
| --- | --- |
| Target | `demo11-music-batch-j` |
| Base | `demo11-fix-batch-i` |
| ROM SHA-256 | `60422232d4c9125a5426e4e7c34b6739dc0a1e9a6fbb6d88ef56a8dbae101dd9` |

## Graphics batches

All graphics come from 7hero.

| Batch | IDs | Rooms | Size | ROM |
| --- | --- | --- | ---: | --- |
| K1 | `261`, `260`, `262`, `1E8`, `1B6`, `120`, `1A4` | `0x0D`, `0x108`, `0x131`, `0x13E` | 18374 | `dee49001788fbf4c55b7bc7dbba9eb5f2405e4095079a6784af4ab94a0c78b11` |
| K2 | `22D`, `230`, `22F` | `0x110` | 7766 | `510fed8a8d9236787fcefcb6102f869675dcb19214f0f0a19416e024016d368d` |
| L | `1B1`, `1AD`, `1BE`, `222`, `223`, `103` | `0x1A`, `0x118`, `0x124`, `0x12A` | 13611 | `7abd2d3ac5c245531116409c764f60e93dac75dc526e57b49a6df258bda771a8` |
| M | `23E`, `23D`, `23F`, `23B`, `240` | `0x14B`, `0x14C` | 14436 | `f4e81c34e3d93a4bdb0123e0411cd99ba9107cedf9c3897c1e4533b5fad93f6c` |

Fix batch M native binary SHA-256:
`92cc42fc1c3309fc2cfb2895abafd7cae1703f462cc14552214945f7b667a7a5`.

## Verification

`tools/qualify_demo11_batches_jklm.py` checks the chain identities, the raw
music payloads, the graphics data, the captures and the native build.

| Translevel | Base | Fix batch M |
| --- | --- | --- |
| `00D` | stall `12` | gameplay `14` |
| `01A` | stall `12` | gameplay `14` |
| `02C` | stall `12` | gameplay `14` |
| `034` | stall `12` | gameplay `14` |
| `03C` | stall `12` | gameplay `14` |
| `048` | stall `12` | gameplay `14` |
| `04E` | stall `12` | gameplay `14` |
| `055` | return to map `0E` | gameplay `14` |
| `056` | stall `12` | gameplay `14` |
| `062` | stall `12` | gameplay `14` |
| `06F` | stall `12` | gameplay `14` |
| `070` | stall `12` | gameplay `14` |

All twelve stay in gameplay at entry 240 and 600. The reference and native
captures match on mode, room, lives and translevel.

The suite now reports **41/41**.

## Causality check

Music batch J alone unblocks all twelve levels. Reference captures of the music
batch J candidate reach gameplay at entry 240 for every one of them:
`00D`, `01A`, `02C`, `034`, `03C`, `048`, `04E`, `055`, `056`,
`062`, `06F` and `070`.

The graphics batches K1, K2, L and M update the graphics of those rooms. They
are not required for entry. This is an important scope correction: the music
batches fix the stalls; the graphics batches are visual work.

Captures: `local/captures/d11-musiconly-*`.

## Limits

- Entry and short gameplay are the claims.
- The graphics edits are visual only. An audible or visual comparison against
  the original is not claimed.
- The candidate chain is not accepted as the head.