# Demo 1-1 graphics batch P

Date: 2026-10-26. This batch closes the graphics references of the restored
content. It is the final candidate chain end.

## Content

| Item | Value |
| --- | --- |
| Target | `demo11-fix-batch-p` |
| Base | `demo11-fix-batch-o2` |
| Donor | 7hero |
| ROM SHA-256 | `48891cf75b570e4118f8646f7f216d50505d047edc40341b3d0dccdc8cc3022c` |
| Native binary SHA-256 | `d8879d7e5d41692d40f1a08b501fad7156469916142d78a62a8817924113a6cb` |

| Graphics ID | Room | Size |
| --- | --- | ---: |
| `226` | `0x129` (translevel `04D`) | 2394 |
| `1AC` | `0x130` (translevel `054`) | 1655 |

## Result

| Translevel | Entry 240 | Entry 600 |
| --- | --- | --- |
| `04D` | gameplay `14` | no-input death |
| `054` | gameplay `14` | gameplay `14` |

Reference and native captures match on mode, room, lives and translevel.

## Graphics references

- Base Demo 1-1 has 190 unique empty extended graphics slots.
- After batch P the chain end has 88 unique empty slots in 53 rooms.
- No room that stalled on the head has an empty slot anymore.
- The 53 remaining rooms are original Demo 1-1 content. Empty slots are normal
  in this game, and the engine uses fallback graphics.

## Verification

`tools/qualify_demo11_batch_p.py` checks the chain identity, the graphics
data, the captures, the native build and the empty-slot property. The suite
reports **44/44**.

The whole-line audit for batch P passes: 40 recipes reproduced, 386,151
changed bytes inside 495,263 reviewed bytes, zero unexpected bytes.
