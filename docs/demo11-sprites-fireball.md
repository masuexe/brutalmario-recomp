# CC fire projectile sprite 0x56

Date: 2026-10-26. The user reports that the red dragon in room `0xCC`
breathes fire with sound only and no fireball. A capture of the room shows the
custom sprite `0x56` in the sprite array. Its recipient record was the
default record. The sprite spawned but did nothing.

A cheap-demo capture of the same route shows the same custom IDs: `0x63`,
`0x65` and `0x56`. This batch ports the cheap-demo record for
`0x56`.

## Batch

- Base: `demo11-hp-roomcf`
- Target: `demo11-sprites-fireball`
- Sprite: `0x56`, 2960 bytes at `$21:C4F3`
- Rooms that place the ID: `0xB7`
- Two graphics assets moved to free runs. The batch patches their pointer
  slots and zeroes the old locations.
- ROM: `ee09118e197d956e57e9726a861e79ee9d151f4d7d0129adf80f13e00948a143`
- Native binary: `c0a93be92a66dd5645c7d8bd0d05b50d7ba5804f497827074b3a3db579264cc2`

## Evidence

A room-exit fixture enters room `0xCC`, walks right and records frames.
Before the batch, sprite `0x56` stays at one position. After the batch it
moves across the screen. The frame shows the red fireball.
The fixed path follows the cheap-demo path within twelve pixels for the first
five samples. The HUD region at frame 12 is identical between the two chains.

- `tools/qualify_demo11_sprites_fireball.py` passes.
- Whole-line audit: 936,830 changed bytes, zero unexpected.
- Suite **69/69**; space budget passes.

## Limits

- The blue dragon snowflake is not yet confirmed. It can use the same sprite
  ID and code path. The user must playtest room `0xCC`.
- The fixture uses a room-exit poke, not ordinary traversal.
