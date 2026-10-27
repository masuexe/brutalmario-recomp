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

## Built target

The target is `demo11-native-product`. Its config is
`config/restorations/demo11-native-product.json`.

| Item | Value |
| --- | --- |
| ROM | `052d4ddf6add8e60eb9a1b6c2be5db1f53f79db8f188e93ab0fdbc5163732a88` |
| Binary | `BrutalMarioDemo11NativeProductSNESRecomp` |
| Packs | 39 |
| Type-1 records | 35 |
| Seven patches | the full `seven-module.json` patch list |

The pack banks run from `A2` to `C9`. The Seven code pack uses `A2`, the Seven
graphics pack uses `A6`, and the gap packs take the rest.

Slot `2A` holds the Seven program in bank `A2`. A separate single-slot gap
target holds the same program in bank `A9`, so the merged target uses the Seven
record and leaves that copy out.

| Check | Result |
| --- | --- |
| `BRK` count on route `demo11-s004-entry` | 0 |
| Route `demo11-s004-entry` dump | equal to the baseline |
| Unchanged-route regression | 32 of 32 dumps equal |

The tests are `tests/test_product_target.py` and pass 5/5. The full suite passes
278/278 tests. The log is `local/reports/unit-tests-product.log`. The regression
report is `local/reports/native-sprite-full-regression-product.json`, SHA-256
`76bb4a146897918b7eadcb1b7a06c95078f3394ed83cb81021057af952207f13`.

## Limits

This document records a plan. No target exists yet, and this document measures
no pack for this combination. A player test needs the built target and a room
set that the player can reach without a teleport fixture.