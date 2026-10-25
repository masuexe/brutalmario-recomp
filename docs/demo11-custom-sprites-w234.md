# Custom sprite port: World 2 to World 4 rooms

Date: 2026-10-26. The user reported that almost every level outside World 1 and
Star World shows one strange falling object when the level uses a custom
sprite. This records the cause and the first port batch.

## Cause found

A sprite record with bit 3 set in the first sprite-list byte marks a custom
sprite placement. The target record for that sprite ID is still the default
record, so the custom code is absent. The game then runs the fallback behaviour
and the object falls.

## Scope

19 level rooms in Worlds 2 to 8 reference a custom sprite ID whose target
record is default. This batch covers the rooms of Worlds 2, 3 and 4:

| Room | Translevel | Missing sprite IDs |
| --- | --- | --- |
| `124` | `048` | `26` |
| `123` | `047` | `08` |
| `125` | `049` | `4C` |
| `11D` | `041` | `3A` (not ported) |
| `127` | `04B` | `0D`, `47` |
| `113` | `037` | `44` |
| `115` | `039` | `05` (not ported) |
| `116` | `03A` | `16`, `18` |

## Batch

Target `demo11-sprites-cheap-demo`, base `demo11-gfx-world8c`, donor
`cheap-demo`. The batch ports 19 sprite IDs. It copies each donor RATS code
block to a free target bank with the same low 16 address bits. It adapts the
bank byte of the init and main pointers in the record. It verifies the six
shared engine dependencies and both versioned dependency hashes.

Candidate ROM:
`8db14be65e84a0ab89de12455825124df4f3491177438d2eaefddfbdfb83e61b`.

Six sprite IDs are not in this batch because no free target bank range keeps
their low 16 address bits: `3A`, `05`, `29`, `04`, `90`, `34`. Their
rooms need the next batch.

## First behaviour evidence

Room `116` (translevel `03A`) changes clearly. The base build shows Mario
standing on flat ground with no other object. The candidate build shows a new
custom object, a red counter, and Mario moves along the level. This proves that
the ported code runs. The intended look needs a user check.

| Base | Candidate |
| --- | --- |
| ![base](local/reports/sprite-w234-03A-before.png) | ![candidate](local/reports/sprite-w234-03A-after.png) |

## Checks

- 17 affected levels load and stay in gameplay in the reference host, except
  translevel `022`, which now returns a death mode after 600 idle frames. The
  behaviour change needs a user check.
- Records, blocks, shared dependencies and room dependencies are verified by
  `tools/qualify_demo11_sprites_w234.py`.
- The native build identity is checked when the build exists.

## The six remaining sprites: allocation analysis

A sprite code block must keep the low 16 bits of its address. The record
only changes the bank byte, and the code uses bank-relative jumps. The
destination therefore needs a free range at one fixed offset inside a bank
below `0x40`.

The six remaining IDs have no such free range in the current chain:

| ID | Offset in bank | Size | Free banks in the base ROM | Blocker in the chain |
| --- | --- | ---: | --- | --- |
| `3A` | `280A` | 1051 | `34 38 39 3C 3F` | star gfx batch, fix batch B, upper inner |
| `05` | `7118` | 1086 | `36 37 38 39 3A 3D 3E 3F` | star gfx batch, world 8a, sprite batch |
| `29` | `1B40` | 2843 | `35 3F` | star gfx batch |
| `90` | `4A7C` | 4133 | `33 34 36 37 38 39 3A 3D 3E 3F` | room 010 gfx, star gfx batch |
| `34` | `6BCC` | 4285 | `36 37 38 39 3A 3D 3E 3F` | star gfx batch, sprite batch |
| `04` | `6DE3` | 821 | `34 36 37 38 39 3A 3D 3E 3F` | fix batch E, star gfx batch |

Three sprite windows overlap each other in banks `34` and `37`:
`26` at `693D`, `08` at `6D08` and `04` at `6DE3`.
The current chain has only two such banks free, so it can hold two of the
three. This is the reason `04` is not in the batch.

### Two ways forward

1. Add a reviewed relocation step. Move the graphics blocks of the star
   graphics batch and the fix batches to other free ranges, then update their
   pointer slots and zero the old ranges. The freed ranges then take the six
   sprite blocks.
2. Rebuild the chain from the base with one global allocator. Reserve the six
   aligned windows first, then place the graphics and music batches.

Option 1 is the smaller change. The base ROM is the only constraint on the
free banks, and it has enough free ranges in banks `38` to `3F`.

## Second batch: five more sprites by relocation

The user played level `0x123` on the first candidate and reported that the
custom wood sprite works normally.

The second batch frees the aligned windows by moving the Star World graphics
blocks out of bank `3F`. The new tool support is `apply_relocations` in
`tools/restore_star_world_1.py`. It copies a reviewed block to a new range,
re-points its reviewed pointer slot, and zeroes the old range. The 16
graphics blocks now live elsewhere, and the Star World rendering is
byte-identical in all 8 sampled frames of translevels `004` and `009`.

The freed windows take five more sprites: `3A`, `05`, `29`, `04` and `90`.
Only sprite `34` remains. Its window in bank `36` is still covered by two
other graphics blocks.

Chain end `demo11-sprite-windows`:

- ROM `9bfbde5dfececdcc202076ba4e1d12a2b933dfb7a1c495fc0c20c806a0d0adad`
- native binary `cdd44455c760dd3979f5d55b362278085ac407c62ea20f7fb69d75b9d60d5b53`
- qualifier `tools/qualify_demo11_sprite_windows.py`; suite **49/49**

Affected levels `041`, `039`, `01E` and `054` load and stay in
gameplay. Level `0x123` still loads after the change.

## Final batch: the last missing sprite

Sprite `34` needs a window in a bank where two graphics blocks of the
fix batch E (graphics `24C` and `24F`, both used by room `15D`) live.
The final batch moves those two blocks to other free ranges and points their
graphics slots to the new addresses. Room `15D` then renders byte-identical
in all 8 sampled frames. The released window in bank `3E` takes sprite `34`.

Chain end `demo11-sprite-final`:

- ROM `bb93ddc05dfbb3d0f1b0fb99fe83239a6fa058669a2706112c4e659b55c737f3`
- native binary `804a2fee1ef3102863fa957aad62cfe2c4917cd6ebc610350ce2223316bf2f6b`
- qualifier `tools/qualify_demo11_sprite_final.py`; suite **51/51**

All 25 missing custom sprites of the World 2 to World 8 level rooms are now
ported: 19 in the first batch, 5 in the window batch and 1 in the final batch.

## Full-range survey on the final chain

The survey on `demo11-sprite-final` reports 255 loads, zero Mario Start
stalls and **216 playable** translevels (graphics chain: 218). Two translevels
changed: `022` and `04E` now return a death mode after 600 idle
frames. The ported custom sprites are active in those levels, so an idle Mario
now dies. This is a behaviour change that the user must confirm.

Qualifier: `tools/qualify_demo11_sprite_final_range.py`; suite **52/52**.
The whole-line audit for `demo11-sprite-final` reproduces the chain with
486,263 changed bytes and zero unexpected bytes.

## Open item: room 11D

The user reports that room `11D` still shows a strange falling object. The
record for sprite `3A` is installed in the chain and the block hash matches,
but dense early frames of the level show no behaviour difference after the
port. A test build that also ports the runtime sprite records `01`, `02` and
`03` shows no difference in room `11D` or four other levels, so those
records appear inert. The falling object needs a user description or a
targeted runtime trace before the next change.

## Status

This is a candidate. The head remains `demo11-fix-batch-p`. The user must
playtest the affected levels and report whether the strange falling object is
gone and whether the new behaviour looks correct.

## Limits

- Entry and short idle gameplay are the only automated claims.
- Six sprite IDs are still missing.
- The port does not prove the whole course works.
