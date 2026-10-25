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

## Full-range survey

The survey on `demo11-gfx-boss76` reports 255 loads and **231
playable** translevels. Every outer translevel result equals the room 49
chain, so the subroom graphics and sprite `0x2B` do not change the ordinary
course outcomes.

Two translevels change because their previously missing custom sprites now
run:

| Translevel | Before | After |
| --- | --- | --- |
| `070` | boss room `0x14C`, idle | chain `0x14C` -> `0x14D`, gameplay at frame 690 |
| `062` | idle Mario at x=32 | a moving object now carries Mario and he dies |

The `070` transition completes, so it is not a stall. The user must
confirm both changes. The counts above are reproducible from
`tools/qualify_demo11_gfx_boss_range.py`.

## User acceptance: room 49

On 2026-10-26 the user played room `0x49` through the big door of level
`0x109` on `demo11-gfx-boss76`. Music, level layout and the custom
sprite are all normal now. This confirms the empty room graphics slots were
the cause of the earlier wrong palette and damaged level.

## Boss room music: slot A9

The user specified slot `0xA9` as the correct music for room `0xBC`.
The recipe `demo11-boss-room-music-a9` changes the room music object
parameter from `0x1F` (placeholder slot `0x1E`) to `0xAA`, so the loader
requests slot `0xA9`. Slot `0xA9` is present in the ROM.

- ROM: `1a56f3fc8b7188cb1f91cae0e6e2e7f0a4a60139c32c81bfa6b4ba4e6b8a8bdf`
- Native binary: `d0a29d30f5f7f0f7c8d15dd9a3a8af58a723c112348a59d23fb3911a25ddaca0`
- The door sweep capture `bossmusic-a9` samples `$0DDA = A9` in
  Mario Start and in gameplay.
- Suite **60/60**; whole-line audit 886,768 changed bytes, zero unexpected.

## Boss health bar: open

Room `0xBC` places two sprites in the recipient sprite table: IDs
`0x2B` and `0x29`. Both records are custom in the current chain, but
runtime captures show no sprite spawn in room `0xBC` - not at the entry
screen, not on screen 1, and not with a fixture that places a vanilla sprite in
the room list. The boss visuals of the room come from tiles. The boss health bar
belongs to the boss sprite code, so it does not appear while no boss spawns.

The boss spawn path is not restored. Candidate causes: the sprite list index,
a secondary entrance record, or boss content that still needs the later boss
migration. The user must report whether the bar appears after walking to the
boss trigger.

## Boss spawn investigation: 2026-10-26

The room sprite list entry for room `0xBC` is
`00 19 70 2B 3D 70 29 FF`. Under the variable-length record format
(a record with flag bit 3 carries one extra byte) the list places **sprite `0x2B`**
with parameter `0x3D`. The chain installs the cheap-demo record and code block
for sprite `0x2B`, so the data to spawn it exists.

Observed results:

- Runtime captures of room `0xBC` show only the scroll-control pseudo
  sprite `0x01` during Mario Start and no sprite in gameplay.
- Walking right, forcing Mario to screen 1, and idling up to 600 frames do not
  spawn any sprite.
- A fixture that places a vanilla sprite in the room list also spawns nothing.
- A fixture with default records for `0x2B` and `0x29` spawns nothing.
- Pointing room `0x083` at the room `0xBC` list spawns nothing, so the
  sprite index is not the translevel byte alone.

The boss graphics of the room are tiles. The boss health bar is drawn by the
boss sprite code, so it cannot appear while no boss spawns.

Next checks: the room list header semantics (the first byte is `0x00` here),
the secondary entrance record, and whether the intended boss belongs to a newer
demo lineage.

## Limits

- The scripted route cannot reach the big door of level `0x109`. The room
  `0x49` fix needs the user playtest.
- Entry frames qualify rendering and load, not a complete boss fight.
