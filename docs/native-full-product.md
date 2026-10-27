# Native full product target plan

## Result

The qualified content lives in separate targets. A player test needs one
build that carries every qualified pack. This document records the bank map
and the pack list for that build. It does not build the target and it does not
claim playability.

## Content lines

| Line | Banks | Bytes | Note |
| --- | --- | ---: | --- |
| Seven code | `A2` | 28,478 | Immutable code pack |
| Seven graphics | `A6` | 23,165 | Immutable graphics pack |
| Sprite 9E code | `A5` | 1,291 | Shared by both lines |
| Star graphics | `B6` | 3,001 | Shared by both lines |
| Sprite gap code | 34 banks | 1,009 to 12,412 each | One pack for each record |
| Type-3 code | `CB` to `CE` | 40 to 295 each | Four small packs |

The sprite gap banks are `A4`, `A7`, `A8`, `A9`, `AA` to `AF`, `B0` to `B5`,
`B7` to `BF` and `C0` to `C6`, `C8`, `C9`.

## Bank check

The two lines share `A5` and `B6`, and both use the same bytes there. The
Seven line uses `A2` and `A6`, and the gap line leaves both banks free.
Therefore no pack needs a new bank.

## Patch check

Each record patch writes a 16-byte record into the recipient sprite table. The
patches use distinct slots, so they do not collide.

| Patch group | Slots |
| --- | --- |
| Type-1 records | 35 slots |
| Type-3 records | `C0`, `C1`, `C2` |
| Seven entry | the Seven patches from `demo11-native-seven-entry` |

## Build order

1. Start from `demo11-native-sprite9e`.
2. Apply the Seven patches, then the 35 type-1 records, then the three type-3
   records.
3. Mount 41 packs: Seven code and graphics, sprite 9E, star graphics, 34 gap
   code packs and four type-3 packs.
4. Run the unchanged-route regression and the room sample set.

## Limits

This document records a plan. No target exists yet, and this document measures
no pack for this combination. A player test needs the built target and a room
set that the player can reach without a teleport fixture.
