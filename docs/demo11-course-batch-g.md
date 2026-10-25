# Demo 1-1 music batch G

Date: 2026-10-26. This is a candidate checkpoint. It is not the current head.

## Raw group slices

The command-graph walk in `adapt_music` rejects songs with commands outside the
reviewed subset. The legacy group layout gives a simpler path: keep the donor
source base and copy one sequence header plus the shared data area unchanged.
When the destination base equals the source base, the sequence pointers need no
relocation.

`tools/restore_star_world_1.py` now supports `raw: true` music tracks with
`raw_group_song`.

The method was validated on two known songs:

| Song | Level | Result |
| --- | --- | --- |
| `44` (slot 0) | `043` | gameplay `14` |
| `56` (slot 2) | `04B` | gameplay `14` |

## Installed songs

The candidate descends from fix batch F and installs six raw slices from
cheap-demo.

| Song | Group | Slot | Payload |
| --- | --- | --- | ---: |
| `3C` | `$2B:8008` | 0 | 6136 |
| `3F` | `$2B:8008` | 3 | 6136 |
| `46` | `$3F:A008` | 2 | 6136 |
| `47` | `$3F:A008` | 3 | 6136 |
| `53` | `$44:8008` | 3 | 6136 |
| `5B` | `$44:C008` | 3 | 6136 |

| Item | Value |
| --- | --- |
| Target | `demo11-music-batch-g` |
| Base | `demo11-fix-batch-f` |
| ROM SHA-256 | `04d91e3d206c2b68b34fd9bfaedd402eb0dec74012775d67f9899494d65ca368` |
| Native binary SHA-256 | `aeef124577861ed222ae593efb32195acbd05348fe71b0279fa4686746d37ba2` |

Each song uses an 8192-byte allocation because the raw payload is 6136 bytes.

## Verification

`tools/qualify_demo11_music_batch_g.py` checks the identities, each raw payload
reconstruction, the RATS blocks, the pointer slots, the captures and the native
build.

| Translevel | Head | Batch G |
| --- | --- | --- |
| `02B` | stall `12` | gameplay `14` |
| `02F` | stall `12` | gameplay `14` |
| `06C` | stall `12` | gameplay `14` |

The reference and native captures match on mode, room, lives and translevel.

The suite now reports **39/39**.

## Limits

- The raw form keeps the donor data area, including unused bytes from the other
  three songs in the group. That is harmless for playback.
- The recipient plays the sequence for the installed slot. An audible match is
  not claimed.
- Low ids `02`, `03`, `05`, `06` and `1A` are not in the legacy groups.
- The candidate chain is not accepted as the head.

## Next steps

1. Port the graphics for the remaining stalled rooms.
2. Investigate the low-id source.
3. Re-run the survey on the chain and decide the next head.
