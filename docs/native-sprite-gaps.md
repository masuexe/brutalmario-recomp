# Native custom sprite gap inventory

## Result

The recipient places 163 custom sprite slots across its rooms. Fifty-four of
those slots hold the type-0 placeholder record instead of a program. The 54
slots cover 78 rooms and 94 placements. This document records the inventory and
the donor availability. It does not install a record and it does not claim
behavior.

## Categories

| Category | Slots | Rooms | Note |
| --- | ---: | ---: | --- |
| Type-1 record in a donor | 40 | 61 | The newest donor with the slot supplies a program |
| Type-3 record only | 3 | 2 | Slots `C0`, `C1` and `C2` |
| No donor record | 11 | 16 | Slots `96`, `97`, `99`, `A1`, `A2`, `A5`, `A6`, `E8`, `E9`, `EA`, `F5` |

The type-1 group has the largest coverage. Thirty-three slots exist only in
`cheap-demo`. Three exist in both `cheap-demo` and `7hero`. Two exist only in
`7hero` and two only in `mazo`.

The eleven slots without a donor record need a source review before any
recovery. The three type-3 slots need the constructor contract from
[the type-3 review](native-sprite-type3.md).

## Largest gaps by room count

| Slot | Rooms | Donor types |
| --- | ---: | --- |
| `95` | 7 | `7hero` type 1 |
| `92` | 6 | `cheap-demo` type 1 |
| `10` | 5 | `cheap-demo` type 1 |
| `12` | 5 | `cheap-demo` type 1 |
| `55` | 5 | `cheap-demo` type 1 |
| `11` | 4 | `cheap-demo` type 1 |
| `13` | 3 | `cheap-demo` type 1 |
| `99` | 3 | none |

Slot `95` is the newest-donor case. `cheap-demo` and `mazo` hold the
placeholder, and `7hero` holds a type-1 record with a 5,144-byte protected
block.

## Room 16B

Room `16B` places slots `8C`, `95`, `C0` and `C1`. The recipient record for
`8C` exists. The other three are placeholders. A donor capture of room `16B`
shows four actors whose custom bytes read `8C`, `95`, `33` and `95`. The
recipient capture of the same fixture shows three actors, and the `95` slots
carry unrelated sprite ids.

The room `16B` donor behavior therefore depends on slots that the recipient
does not carry. A room entry check cannot pass until those slots carry a
program.

## Reproduction

```
python3 tools/audit_sprite_gaps.py
```

The report is `local/reports/native-sprite-gaps.json`, SHA-256
`954c6828d4d71f7415c3e8760c3068b37ff5fbacb69104d1842a5f8bb0e20f55`. The tests
are `tests/test_sprite_gaps.py` and pass 5/5. The full suite passes 197/197
tests. The log is `local/reports/unit-tests-gaps.log`.
