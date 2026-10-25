# CC lobby custom sprite set

Date: 2026-10-26. The CC lobby rooms place five more custom sprites that
still used the default record: `0x67`, `0x68`, `0x6A`, `0x71` and
`0x5B`. Their bank windows held graphics assets. This batch ports the
sprites and relocates nine graphics assets with reviewed pointer patches.

## Batch

- Base: `demo11-sprites-cc-lobby`
- Target: `demo11-sprites-cc-lobby-full`
- ROM: `3ef5817beffc26b5c11cb51d0c810839478db9bf4234a59c6cf27f9c25fdeff0`
- Native binary: `688e23563f11f963d2abfb311729cda6b5706f73c8a611a343ca261f43c5b952`

| Sprite | Rooms |
| --- | --- |
| `0x67` | `0xCD`, `0xD6`, `0xD7`, `0xD8`, `0xD9`, `0xDA`, `0xDB`, `0xDC`, `0xDD`, `0xDE`, `0xDF`, `0xE1`, `0xE5`, `0xE6`, `0xE7` |
| `0x68` | `0xD3`, `0xD4` |
| `0x6A` | `0xD8`, `0xE2`, `0xE3`, `0xE4` |
| `0x71` | `0x3A`, `0x55`, `0x99`, `0xC4` |
| `0x5B` | `0xC1` |

## Graphics relocations

Each relocation moves one graphics asset to a free bank run. The batch patches
the pointer slot and zeroes the old location. A later sprite block can use part
of an old location. The qualifier checks each nonzero byte in an old location
against the installed sprite block. Each relocated asset must decode to the
same pixels before and after the move.

## Evidence

Room-exit fixtures enter rooms `0xCD`, `0xD3`, `0xD8`, `0xC4` and
`0xC1`. The room frames change after the batch. The HUD region stays
identical. Room `0xCD` uses game mode `0x12`; its frame does not change
in the captured window. The other four rooms change in the gameplay field.

- `tools/qualify_demo11_sprites_cc_lobby_full.py` passes.
- Whole-line audit: 922,380 changed bytes, zero unexpected.
- Suite **66/66**; space budget passes.

## Limits

- The fixtures use a room-exit poke. They qualify room entry, not a complete
  traversal or a boss fight.
- The user must playtest the CC lobby rooms.
- The sprite tile graphics gap stays open.
