# CC boss room custom sprites

Date: 2026-10-26. Rooms around the CC boss room placed custom sprites `0x63` and
`0x65` with the default record. The HP-bar recipe restored the HUD
display, but the CC room still ran no custom sprite code. This batch ports the
two cheap-demo records and code blocks.

## Batch

- Base: `demo11-hp-bars`
- Target: `demo11-sprites-cc`
- Sprites: `0x63` (1424 bytes, bank `0x3F`), `0x65` (668 bytes, bank `0x3E`)
- Both code blocks fit their reviewed windows directly; no relocation is
  needed.
- Rooms that place the IDs: 
  - `0x63`: `0xCC`, `0xCF`, `0xD0`, `0xD1`
  - `0x65`: `0xCC`, `0xCF`, `0xD0`, `0xD1`, `0xD2`, `0xD5`, `0xD6`, `0xDB`

- ROM: `8d9330deea6ccd50bcbb9bbe466a7aef92f834cb45dfca5de2be10dce782bff4`
- Native binary: `e5e1a3e98804ff48b0c45daccfce4c7500b113c0bf24bb6f2f6b9b6f40058ede`

## Evidence

A CC room-exit fixture enters room `0xCC` from the level `0x15F` corridor.
Before the batch, the custom sprite numbers `0x63` and `0x65` appear once
and then stop (status 0). After the batch they stay active (status 8) and the
room frame shows the additional object next to Mario. The HP HUD region is
byte-identical between the two captures, so the HP-bar recipe is untouched.

- `tools/qualify_demo11_sprites_cc.py` passes.
- Whole-line audit: 888,924 changed bytes, zero unexpected.
- Suite **62/62**; space budget passes.

## Limits

- The fixture uses a room-exit poke. It qualifies the room entry and the sprite
  activation, not a natural boss traversal or a full boss fight.
- The CC boss behaviour and the remaining CC lobby sprite gaps need user
  playtesting.
