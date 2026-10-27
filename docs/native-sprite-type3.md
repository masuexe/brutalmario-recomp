# Native type-3 SpriteTool records C0, C1 and C2

## Result

The newest official donors place three type-3 records in slots `C0`, `C1` and
`C2`. The recipient keeps the same room placements but the slots hold type-0
placeholders. This document records the static review and one bounded entry
check. It does not install the records and it does not claim behavior.

## Records

The `7hero` and `boss` images hold byte-identical records and byte-identical
protected blocks.

| Slot | Field | Value |
| --- | --- | --- |
| `C0` | Record | `03ffffffffffffffe68613ea8613ffff` |
| `C0` | Init | `13:86E6` |
| `C0` | Block | 205 bytes, SHA-256 `11db36ef4b3f6ca9d4b848173072cba0e4c08a87c776e75fd9376a9154dee92e` |
| `C1` | Record | `03ffffffffffffff17ae131bae13ffff` |
| `C1` | Init | `13:AE17` |
| `C1` | Block | 213 bytes, SHA-256 `a1b87ca2135ad18140195aa885a239eb36300815cd886ff9abee5baa2ddf6ac3` |
| `C2` | Record | `03ffffffffffffff30dd1534dd15ffff` |
| `C2` | Init | `15:DD30` |
| `C2` | Block | 295 bytes, SHA-256 `fa8c0ac51be70e188ebaf324802fd2ab9d4deec60674f6f9a3a411ec8549c509` |

Each record starts with type `03`. Bytes 1 to 7 stay `FF`. Bytes 8 to 10 hold
the init pointer and bytes 11 to 13 hold the main pointer. Bytes 14 and 15 stay
`FF`.

## Block layout

Each protected block starts with a `STAR` header. The body holds the label
`MDKINIT` and the label `MAIN`. The init field points at the `MAIN` label.
The main field points 4 bytes later, at a stub.

The stub pushes the data bank, pushes the program bank, pulls the data bank and
calls the module body. The module body returns with `RTS`. The stub then pulls
the data bank and returns with `RTL`.

The body of slot `C0` reads `$17AB` as a countdown. It exits while the
countdown is not `38`, `30`, `28` or `20`. It then compares the actor box
with the player box. If the boxes overlap, it calls `01:A9DE` and sets
`$14C8` to `08`.

## Room placements

| Slot | Donor rooms | Recipient rooms | Recipient record |
| --- | --- | --- | --- |
| `C0` | `16B` twice | `16B` twice | `0000ffffffffffff218001218001ffff` |
| `C1` | `16B` four times | `16B` four times | `0000ffffffffffff218001218001ffff` |
| `C2` | `170` once | `170` once | `0000ffffffffffff218001218001ffff` |

The level data, the sprite lists and the graphics records for rooms `16B` and
`170` are byte-identical between the donor and the recipient. The only
difference is the record type in each slot.

## Entry check

The fixture enters room `16B` and room `170` through a labelled pipe action.

| Image | Room | Actors at the first sample |
| --- | --- | --- |
| donor `7hero` | `16B` | three sprite-`00` slots and two sprite-`33` slots |
| recipient | `16B` | two sprite-`00` slots, two sprite-`33` slots and one custom `8C` |
| donor `7hero` | `170` | no actors |
| recipient | `170` | sprite `BC` and sprite `2F` |

Neither image materializes a `C0`, `C1` or `C2` actor in room `16B` or
room `170` under this fixture. The room placement alone does not spawn the
records. The type byte at `$1AB1C` reads `00` for every active actor in both
images.

The room dependency table shows the cause. Room `16B` also places slot `95`.
The recipient holds a type-0 placeholder for `95`, while `7hero` holds a
5,144-byte type-1 program. See [the gap inventory](native-sprite-gaps.md).

## Type admission

The recipient constructor at `31:8177` reads the record type at `$7FAB1C`.
When the type byte is not zero it jumps to a second path at `31:81D1`. That
path copies bytes 1 to 7 directly into RAM and copies bytes 10 to 13 into
`$7FAB28` and `$7FAB34`. It does not read the init and main pointers.

The donor constructor at `10:B059` reads the same type byte. When the type byte
is not zero it copies bytes 1 to 9 and bytes 10 to 13 as three words.

The two constructors therefore disagree on the layout that follows the type
byte. A record transplant must also carry the constructor contract.

## Reproduction

```
python3 tools/audit_sprite_type3.py
```

The report is `local/reports/native-sprite-type3.json`, SHA-256
`7e35f68ac13d5d65552b8b8843cb2521adb950569c05e837ce2cdb9ca3faa950`. The tests
are `tests/test_sprite_type3.py` and pass 5/5. The full suite passes 192/192
tests. The log is `local/reports/unit-tests-type3.log`. The captures are
`red-c0c2-room16b-donor-v1`, `red-c0c2-room170-donor-v1`,
`type3-room16b-native-v1` and `type3-room170-native-v1`.
