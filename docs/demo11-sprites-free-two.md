# Second free-window custom sprite batch

Date: 2026-10-26. A rescan of the latest chain found seven more custom
placements whose record was still the default and whose donor code fits a
free bank window. This batch ports them.

## Batch

- Base: `demo11-sprites-snowflake`
- Target: `demo11-sprites-free-two`
- Sprites: `0x03`, `0x1D`, `0x2F`, `0x41`, `0x59`, `0x84` and `0x85`
- ROM: `01bbcefafd6522481cf5b68a0e5c6fafd42c2461537da72572d35fb5605be905`
- Native binary: `d9e4e3c4b1afb812da050cccb4d25ad35adf74181335493f4123c50f199887e5`

Only sprite `0x59` has a room placement (`0x1C`). The
sampled room frame does not change, because that sprite spawns later than the
capture window. The other six sprites are runtime helpers with no room
placement.

## Evidence

- `tools/qualify_demo11_sprites_free_two.py` passes.
- Whole-line audit: 941,481 changed bytes, zero unexpected.
- Suite **71/71**; space budget passes.

## Limits

- The checks pin records, blocks and shared dependencies. They do not show a
  visible sprite in a room.
- 59 placed custom sprite candidates still need reviewed relocations.
