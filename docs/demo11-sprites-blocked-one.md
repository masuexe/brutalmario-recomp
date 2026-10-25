# Blocked placed custom sprites, batch one

Date: 2026-10-26. Twelve placed custom sprites still used the default record,
and their bank windows held graphics assets. This batch ports them and moves
thirteen graphics assets with reviewed pointer patches.

## Batch

- Base: `demo11-sprites-free-two`
- Target: `demo11-sprites-blocked-one`
- Sprites: `0x1E`, `0x1F`, `0x21`, `0x42`, `0x52`, `0x62`, `0x6F`, `0x72`, `0x87`, `0x8C`, `0x8E` and `0x8F`
- Graphics relocations: 13
- ROM: `c4799ec8bed568646aec16426824d2516694bd7a39346fe9e4dfbf226745cd8f`
- Native binary: `4bdbf5c013236776d89274ea6c6dfe3d63a761959839b5b1d4a133705d8510a2`

## Evidence

Room fixtures enter rooms `0x8F`, `0x95`, `0xB0` and `0x1D`.
Each room frame changes, and each HUD region stays identical. Room `0x66`
and room `0x65` stay unchanged, because their sprite spawns later or off
screen in the capture window.

Each relocated asset must decode to the same pixels before and after the move.
A later sprite block can use part of an old location. The qualifier checks every
nonzero byte in an old location against the installed sprite block.

- `tools/qualify_demo11_sprites_blocked_one.py` passes.
- Whole-line audit: 989,772 changed bytes, zero unexpected.
- Suite **72/72**; space budget passes.

## Limits

- The fixtures use a room-exit poke, not ordinary traversal.
- 47 placed custom sprite candidates still need reviewed relocations.
