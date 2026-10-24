# Legacy donor music layout

Date: 2026-10-26. This note records the legacy-family music layout that the
Demo 1-1 restoration uses. The findings come from static analysis and from the
reviewed song restorations.

## Two music families

| Family | Versions | Music storage |
| --- | --- | --- |
| New | `demo-1-1`, `demo-only-1`, and the restoration line | Single-song payloads in a 3-byte pointer table at `$0F:E000` |
| Legacy | `cheap-demo`, `demo6`, `demo7`, `demo8`, `7hero`, `mazo`, `ow`, `ra-*` | Four-song upload groups in fixed ROM blocks |

The new-family table entries are bank, high byte and low byte. A null entry
stalls the SPC upload, so the game stops at Mario Start.

## Legacy group storage

A legacy ROM holds 21 groups with a stride of 0x2000 bytes:

| Groups | Addresses |
| --- | --- |
| 10 | `$29:8008` to `$2B:A008` |
| 7 | `$3E:B008` to `$3F:E008` |
| 4 | `$44:8008` to `$44:E008` |

Each group has this layout:

| Offset | Content |
| --- | --- |
| 0 | Count, two bytes |
| 2 | Source base, two bytes, normally `0x6800` |
| 4 + 8*k | Sequence header for slot k, four slots |
| Count + 8 | Group end, including a trailer |

The song data area starts at source base + 64. Group total size is
count + 8, normally 6136 bytes.

## Extraction recipe

`tools/derive_legacy_song.py` walks the reachable command graph with the same
rules as `restore_star_world_1.py` `adapt_music`. It prints the reviewed
config fields and the payload identity.

Validated cases:

| Group | Slot | Result |
| --- | --- | --- |
| `$44:A008` | 0 | Song size 700, payload SHA `bc134773...`; matches the reviewed Snow Star song 0x54 config exactly |
| `$29:8008` | 1 | Matches the reviewed room 138 song 0x7E config exactly |
| `$44:A008` | 3 | Payload SHA `1d293f8e...`; matches the installed song 0x57 payload exactly |

These cases validate the group layout and the slot order.

## Open point: song id to group and slot

The legacy family does not use the new-family table at `$0F:E000`. The bytes
at that address are identical across all legacy versions, so they are shared
data, not a pointer table. The mapping from a song id to a group and a slot is
not resolved yet.

- The SNES side sends only the song id to APU port 2. See the request handler
  at file offset 0x179 and the upload activation routine at `$34:9B00`.
- The activation routine reads a DMA descriptor table at `$7F:FB00`. The
  writer of that table is not resolved yet.
- The legacy group order is not a simple id order. Group `$44:A008` starts at
  song 0x54, and group `$29:8008` has song 0x7E in slot 1.

## Donor probing limit

The recipient map 6 overworld tile override does not work on `cheap-demo`. A
25-translevel probe all entered room `0x14B`, so the donor map layout and the
tile address differ. The donor survey must locate the donor map tile address
before it can select courses by level number.

## Next steps

1. Capture APU RAM on a donor level that plays a target song, with
   `SNESREF_APURAM_TRACE_FILE`. The uploaded group bytes appear at APU RAM
   `0x6800`; match them in the ROM to identify the group.
2. Use the DSP register trace to select the slot. Compare the donor trace with
   the four candidate payloads.
3. Resolve the id to group and slot table. Then restore the remaining songs.
