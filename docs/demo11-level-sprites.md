# Remaining level-room custom sprites

Date: 2026-10-26. After the global graphics chain, several level rooms still
missed custom sprite records. This batch ports the six that fit directly from
cheap-demo.

## Batch

- Base: `demo11-gfx-global13`
- Target: `demo11-sprites-level1`, donor cheap-demo
- Sprites: `00`, `02`, `07`, `35`, `3E`, `4B`
- ROM: `8f6ade317c14d872ba2d45ced2ce97a6cbbe3f4538e83b93bda0d1aada46fd66`

The records cover the boss rooms `14B`/`14C`/`14D` (sprite `00`),
level `012`, level `097`, level `087`, level `062` and
level `05E`.

## Dropped: 7hero sprite C2

Sprite `C2` from 7hero is not ported. Its record is
`03ffffffffffffff30dd1534dd15ffff`, a different record layout from the
cheap-demo custom sprite records. A test chain with that record boots level
`094` to a black screen with mode 0 and garbage WRAM. The chain without
`C2` loads level `094` normally (mode `0x14`, room `0x170`).
The record needs its own investigation before a retry.

## Checks

- `tools/qualify_demo11_sprites_level.py`: records, blocks, shared
  dependencies, room dependencies, captures and native build.
- The suite reports **56/56**; the whole-line audit has zero unexpected bytes.

## Limits

- Entry gameplay is the automated claim.
- Eight of the fifteen level-room sprite gaps still need aligned windows.
