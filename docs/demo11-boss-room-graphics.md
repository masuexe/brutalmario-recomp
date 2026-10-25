# Boss room graphics and sprite 2B

Date: 2026-10-26. The user reported that the middle boss room of level
`0x15F` entered, but its graphics were black bars and the custom sprite
had no code. The user also reported that room `0x49` (behind the big door of
level `0x109`) shows the custom sprite with a wrong palette and a damaged
level.

## Root causes

1. The earlier global graphics batches checked only the level-index rooms. 95
   other rooms with a valid header still had empty extended graphics slots.
   Room `0x0BC` missed seven IDs: `1C5`, `1C4`, `215`, `216`, `217`,
   `218` and `1D2`. Room `0x49` missed `160`, `16E` and `16F`.
2. Room `0x0BC` places custom sprite `0x2B` (record with extra byte,
   parameter `0x3D`) and the target record was the default record.
   Room `0x49` places custom sprite `0x48`, which the earlier batch
   installed, but the room graphics were still missing.

## Recovery

1. `demo11-boss-room-sprites`: relocate the three graphics blocks that
   occupy the sprite `0x2B` window in bank `0x39` (`0x14C`, `0x14D`, `0x14E`),
   port sprite `0x2B` from cheap-demo, and free window `0x4C9D` in bank 
   `0x39` for the 7983-byte sprite block.
2. `demo11-gfx-boss1` through `demo11-gfx-boss76`: install the 159
   remaining extended graphics IDs (143 from cheap-demo, 16 from 7hero).

The relocation pointer must point to the block data (`block + 8`), not to the
RATS header. A first attempt pointed eight bytes early and changed the
rendering of levels `038`, `042` and `047`. The final chain
renders those three levels byte-identically to the base chain.

Chain end: `demo11-gfx-boss76`
- ROM: `d6e78605b9d69c9534d2584134291c3b1c8c6d31ac744bf16e1ec534e25a325e`
- Native binary: `63ddcb2f4a793ca20c2f2208892ef2c9dfe20d889d6982bf8e69970c65bd6381`
- Whole-line audit: 886,768 changed bytes, zero unexpected.
- Suite: **58/58**.
- Space: 357,950 free bytes; the reviewed floor is now 300,000.

## Evidence

- Scripted door sweep of level `0x083`: step 40 reaches mode `0x14` in
  room `0xBC` with a bright frame (mean 93.3 out of 255). The frame shows the
  boss room tiles and the boss object.
- Room `0x49` now has `0x160`, `0x16E` and `0x16F` installed. A debug fixture
  loads room `0x49` through the level `0x109` entry and reports music
  `0x6B`. The user must confirm the palette and the level in ordinary play.

## Limits

- The scripted route cannot reach the big door of level `0x109`. The room
  `0x49` fix needs the user playtest.
- Entry frames qualify rendering and load, not a complete boss fight.
