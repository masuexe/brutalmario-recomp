# Demo 1-1 music batch A and fix batch B

Date: 2026-10-26. These are candidate checkpoints. They are not the current
head.

## Music batch A

The legacy cheap-demo groups map to song ids with the validated formula:

```
song_id = 0x20 + 4 * group_index + slot
```

Group index counts the 16 real groups in address order from `$29:8008`.
`tools/derive_legacy_song.py` derives each song from its group.

| Song | Group | Payload |
| --- | --- | ---: |
| `21` | `$29:8008` slot 1 | 2486 |
| `2C` | `$29:E008` slot 0 | 838 |
| `44` | `$3F:A008` slot 0 | 833 |
| `45` | `$3F:A008` slot 1 | 1804 |
| `4C` | `$3F:E008` slot 0 | 679 |

The candidate installs these five payloads into their null slots. Each payload
gets a 4096-byte allocation, a RATS block and the pointer slot.

| Item | Value |
| --- | --- |
| Target | `demo11-music-batch-a` |
| Base | `demo11-star-bgm` |
| ROM SHA-256 | `07352a92bcc8a7a967b8578ca480cbaaa0b31c1ee7b87020046f52e0faa711fd` |

## Fix batch B

The candidate descends from music batch A and ports nine extended graphics IDs
from 7hero. Rooms `0x01E` and `0x114` select these IDs and the base leaves
every pointer null.

| Item | Value |
| --- | --- |
| Target | `demo11-fix-batch-b` |
| Base | `demo11-music-batch-a` |
| ROM SHA-256 | `04897aaf847d9fb3d0148974ad6702587495ccca14a22348dac5eaebc26396c6` |
| Native binary SHA-256 | `87559c6b49e8fedb6c0fd9dd8bf54ead583e11e4b20a18feb47da37f5c644709` |
| Allocation | file offset `0x1CA710`, 21232 bytes |
| Assets | `1A1`, `19A`, `19B`, `1A2`, `14B`, `14C`, `14D`, `14E`, `150` |

## Verification

`tools/qualify_demo11_music_batch.py` checks both recipe identities, the
derived payload hashes, the installed RATS blocks, the pointer slots, the
donor graphics and the captures.

| Translevel | Head | Music batch A | Fix batch B |
| --- | --- | --- | --- |
| `01E` | stall `12` | gameplay `14` | gameplay `14` |
| `043` | stall `12` | gameplay `14` | gameplay `14` |
| `038` | stall `12` | gameplay then map `0E` | gameplay `14` |

The reference and native captures match on mode, room, lives and translevel at
entry 240 and 600. Positions can drift by a few pixels because the scripts
have no controller input.

The suite now reports **36/36**.

## Limits

- Entry and short gameplay are the claims. Full traversals, completion, saves
  and audible music match are not claimed.
- Many other stalls need more songs or graphics. Song ids below 0x20 have no
  source yet.
- The candidates are not accepted as the head.

## Next steps

1. Continue the music and graphics batches for the remaining stalls.
2. Find a source for the low ids, starting with `02`.
3. Re-run the survey on the candidates and decide the next head.
