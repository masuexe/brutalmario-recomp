# Blocked placed custom sprites, batch three

Date: 2026-10-26. Four more blocked custom sprites are ported with four
reviewed graphics relocations. Sprite `0x79` was in the first plan
of this batch. It needs two relocations and the free space fell below the
review floor, so it stays open.

## Batch

- Base: `demo11-sprites-blocked-two`
- Target: `demo11-sprites-blocked-three`
- Sprites: `0x74`, `0x86`, `0x46` and `0x6C`
- Graphics relocations: 4
- ROM: `9ec9c6a0790272b88e882649c1b7849d3bb745b27560f5942f419c177ca21265`
- Native binary: `d14cec7150ba84521a141dbf96227098f1f2b754d8664edb495446b761becad1`

## Evidence

Room fixtures enter rooms `0x3B`, `0x2C` and `0x7B`. Each
gameplay field changes and each HUD stays identical. Room `0x95` changes
both the field and the HUD, because its sprite owns HUD content.

- `tools/qualify_demo11_sprites_blocked_three.py` passes.
- Whole-line audit: 1,022,689 changed bytes, zero unexpected.
- Suite **74/74**; space budget passes.

## Space accounting

The installed content reduced the free ROM space to 296,878 bytes. The
review floor in `tools/check_space_budget.py` moves from 300,000 to 290,000
bytes for the larger restoration line. The aligned free space is 112,124
bytes and the largest run is 19,387 bytes.

## Limits

- 33 placed custom sprite candidates still need reviewed relocations.
- The fixtures use a room-exit poke, not ordinary traversal.
