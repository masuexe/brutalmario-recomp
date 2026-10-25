# CC lobby custom sprite 0x69

Date: 2026-10-26. Rooms `0xD6`, `0xDA`, `0xDB`, `0xE0`,
`0xE2` and `0x155` place custom sprite `0x69` with the
default record. The CC boss sprites `0x63` and `0x65` already use
`demo11-sprites-cc`. This batch ports sprite `0x69` from cheap-demo.

## Batch

- Base: `demo11-hp-room146`
- Target: `demo11-sprites-cc-lobby`
- Sprite: `0x69`, 1227 bytes at `$37:BA1A`
- Rooms: `0xD6`, `0xDA`, `0xDB`, `0xE0`, `0xE2`, `0x155`
- The window is free in banks `0x37` and `0x3A`. The batch uses `0x37` and
  needs no relocation.
- ROM: `34bddb8412945c68e82f78bb642d46c0c41ffa5b27e112e5d6925d62b1fd21df`
- Native binary: `9d10c89196d666c2bcf86dc2713ea1b6c857e9dd1792fb9fba9f9c26e061172e`

## Evidence

A room-exit fixture enters room `0xDA` from the level `0x15F` corridor.
The sprite number list contains `0x69` before and after the batch.
The room frame changes (554 pixels at entry, 1109 pixels later).
The HUD region stays identical. A yellow creature appears next to Mario.

- `tools/qualify_demo11_sprites_cc_lobby.py` passes.
- Whole-line audit: 890,311 changed bytes, zero unexpected.
- Suite **65/65**; space budget passes.

## Limits

- The fixture uses a room-exit poke. It qualifies the room entry, not a
  complete course traversal or a boss fight.
- Sprites `0x5B`, `0x67`, `0x68`, `0x6A` and `0x71` stay open.
  Their windows need reviewed relocations.
