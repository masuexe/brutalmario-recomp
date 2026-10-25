# CC snow projectile sprite 0x5A

Date: 2026-10-26. The user reports that the light blue dragon in room
`0xCC` makes no snowflake. The dragon spawn code in cheap-demo sprite
`0x63` can spawn two custom IDs: `0x56` for the fire projectile
and `0x5A` for the other projectile. The chain record for `0x5A` was
the default record. This batch ports the cheap-demo record for `0x5A`.

## Batch

- Base: `demo11-sprites-fireball`
- Target: `demo11-sprites-snowflake`
- Sprite: `0x5A`, 433 bytes at `$20:265B`
- Rooms that place the ID: `0x1C`
- One graphics asset moved to a free run. The batch patches its pointer slot
  and zeroes the old location.
- ROM: `81d752be8a956fe7b60aa0903ede948447ba0714f6e0ab0166870d84c2af9e1a`
- Native binary: `943ce6951c197bf6ecd6b65cc6d680b5f46dbe00d4442766bf6a577b33efedb6`

## Evidence

The qualifier builds a reviewed fixture. The fixture replaces the first
dragon entry in the room `0xCC` sprite list with sprite `0x5A`.
The capture then shows sprite `0x5A` on screen with four or more X
positions and an active status. The fixture ROM hash is pinned in the
capture receipt.

- `tools/qualify_demo11_sprites_snowflake.py` passes.
- Whole-line audit: 939,558 changed bytes, zero unexpected.
- Suite **70/70**; space budget passes.

## Limits

- The fixture proves that sprite `0x5A` runs and moves. It does not
  prove the dragon attack that spawns it. The user must playtest the light
  blue dragon in room `0xCC`.
- If the snowflake is still missing, the spawn branch is not reached or the
  snowflake uses another asset.
