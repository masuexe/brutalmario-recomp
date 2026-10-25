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

## Status

This is a candidate. The head remains `demo11-fix-batch-p`. The user must
playtest the affected levels and report whether the strange falling object is
gone and whether the new behaviour looks correct.

## Limits

- Entry and short idle gameplay are the only automated claims.
- Six sprite IDs are still missing.
- The port does not prove the whole course works.
