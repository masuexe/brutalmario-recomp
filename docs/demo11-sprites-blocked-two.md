# Blocked placed custom sprites, batch two

Date: 2026-10-26. Ten more blocked custom sprites are ported with ten
reviewed graphics relocations. Two candidates (sprite `0x20` and
sprite `0x1B`) have no reviewed window yet and stay open.

## Batch

- Base: `demo11-sprites-blocked-one`
- Target: `demo11-sprites-blocked-two`
- Sprites: `0x6E`, `0x0E`, `0x5F`, `0x40`, `0x01`, `0x39`, `0x80`, `0x91`, `0x75` and `0x88`
- Graphics relocations: 10
- ROM: `e99b8733cf3b8537666fffd1d728bb263d128ac5f58f580404dd615fe92d2428`
- Native binary: `8f18446477bd84f11b8c8a243e0fdf7c7ca0feeeb6c76f1ef467b415f4500b1d`

## Evidence

Room fixture `0xAC` changes its gameplay field after the batch. The
room owns HUD content through the ported sprite, so the HUD can change there.
Rooms `0xF5`, `0xA6` and `0x94` keep their frame in the
capture window because their sprite is idle or off screen.
The room `0x68` base capture landed in room `0x73`, so the
qualifier does not use it as evidence.

- `tools/qualify_demo11_sprites_blocked_two.py` passes.
- Whole-line audit: 1,011,764 changed bytes, zero unexpected.
- Suite **73/73**; space budget passes.

## Limits

- 37 placed custom sprite candidates still need reviewed relocations.
- The fixtures use a room-exit poke, not ordinary traversal.
