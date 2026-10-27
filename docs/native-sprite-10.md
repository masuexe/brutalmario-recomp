# Native sprite 10 module review

## Result

The official `cheap-demo` holds a type-1 record for custom sprite slot `10`.
The recipient places that slot in five rooms but holds the type-0 placeholder
record. This document records the review of the record, the protected program
and one built target. The target carries the record and runs the donor program
from the free bank `A4`.

## Record

| Item | Value |
| --- | --- |
| Slot | `10` |
| Donor record | `01360080398391002ea61ad1a61a0000` |
| Init | `1A: A62E` |
| Main | `1A: A6D1` |
| Rooms | `12D`, `156`, `157`, `15B`, `15C` |
| Recipient record | `0000ffffffffffff218001218001ffff` |

The donor program lives in one protected block. The block starts at `1A:A61F`,
is 2,589 bytes long and has SHA-256
`47a112ba1ddb0220848b32d2937ee72054a9e59b0acc94a58d6ffa993546d4dc`.

The `7hero`, `mazo` and `boss` donors hold the placeholder record for this
slot. The review uses `cheap-demo` because the repository agreement names it as
the last official demo that holds every custom sprite program.

## Program review

The audit holds 21 local entry states and 963 instruction variants. It finds
eight outside calls and no unreviewed indirect jump. The program holds no
inline dispatch table.

The outside calls are `01801A`, `0187A7`, `01A7DC`, `01B7B3`, `02A9DE`,
`07F7D2`, `27FAF4` and `28FCC0`. The call `0187A7` is the SpriteTool
constructor hook. The other calls enter recipient helpers that are byte
identical to the donor copy.

## Mapping

The block moves to the free bank `A4` and keeps its low address bits:
`A4:A61F`. The program holds bank-local 16-bit jump targets, so the low 16
bits must not change. An earlier plan that used `A4:E61F` moved every
bank-local target and reached `BRK` at `A4:AF45`.

The record init and main fields become `A4:A62E` and `A4:A6D1`. The adapted
record is `01360080398391002ea6a4d1a6a40000`, and the install site is file
offset `1606514` in the recipient.

## Built target

The target is `demo11-native-sprite10`. Its recipe is
`config/native-content/sprite10-module.json` and its config is
`config/restorations/demo11-native-sprite10.json`.

| Item | Value |
| --- | --- |
| Target ROM | `a53da807340a18d2648cc1bfd04d6ab182da719beec0b607a59c0c6925c94830` |
| Install site | file offset `1606514` |
| Installed record | `01360080398391002ea6a4d1a6a40000` |

The target mounts three packs. The pack variables keep the names
`BM_SEVEN_CODE_PACK`, `BM_NATIVE_SPRITE_PACK` and
`BM_NATIVE_GRAPHICS_PACK`.

## Reproduction

```
python3 tools/m1.py --target demo11-native-sprite10 scaffold
python3 tools/m1.py --target demo11-native-sprite10 generate
python3 tools/m1.py --target demo11-native-sprite10 build
```

The donor manifest is `config/cheap-demo-donor.json`. The module receipt is
`local/native-modules/demo11-native-sprite10-final/preparation-receipt.json`,
SHA-256 `1ce754c838d70ad3c563e2a6221b900586565a55ffd15665e570f405d4a524af`.

## Limits

The graphics review stays open. This document claims one built target and one
static module review. It does not claim gameplay, donor parity, a course pass or
a clear.

## Entry qualification

The donor comparison is complete for rooms `12D` and `15B`. The cheap-demo pipe
poke needs `poke 19b8 <room low>` together with `poke 19d8 05` to load a room
above `0x100`. With `19d8 00` to `19d8 04` the game loads the room below
`0x100` instead, which holds no slot `10` sprites.

Rooms `12D` and `15B` match the donor in the later samples. Room `12D` matches
in all three samples. Rooms `156`, `157` and `15C` also place custom slots
`11` to `14`, which the recipient still leaves empty, so those rooms stay open.

The target capture `sprite10-12d-fixed-native-v1` enters room `12D` and
holds four actors with custom id `10` in slots 4 to 7 at X `112`, `108`,
`108` and `108`. The run reports `bank=A4 resolutions=2938112
executed_page_instructions=465523` and no `BRK`.

The capture `sprite10-12d-long-native-v2` keeps the same four actors for 300
frames, moves one of them to X `366`, and exits to room `155` after a
rightward move. The run reports no `BRK`.

Rooms `156` and `15B` also execute the module view
(`bank=A4` page instructions `12272` and `61640`).

This document claims the static review, the built target, donor parity for rooms
`12D` and `15B` and the baseline differential. It does not claim the other
three rooms, movement or a course pass.

| Room | Donor | Target | Rows equal |
| --- | --- | --- | --- |
| `12D` | `(4,36,10,112,208)`, `(5,...,108,370)`, `(6,...,108,210)`, `(7,...,108,290)` | same | yes, all samples |
| `15B` | `(7,36,10,16,368)`, `(9,36,10,240,368)` | same | yes, samples 2 and 3 |
| `156` | needs slot `11` | slot `11` still empty | open |
| `157` | needs slots `12` and `13` | both empty | open |
| `15C` | needs slots `13` and `14` | both empty | open |

## Baseline differential

The baseline target `demo11-native-sprite9e` holds the placeholder record, so
its rooms spawn sprite `00`. The sprite 10 target spawns sprite `36` with
custom id `10` in the same rooms.

| Room | Baseline | Target |
| --- | --- | --- |
| `12D` | slots 4 to 7, sprite `00` | slots 4 to 7, sprite `36`, custom `10` |
| `156` | sprite `00` rows | sprite `36`, custom `10` |
| `15B` | sprite `00` rows | sprite `36`, custom `10` |

The tool is `tools/qualify_sprite10_gap.py`. Its report is
`local/reports/native-sprite10-final.json`, SHA-256
`f7d5be7025df840856d0fbc9db67859e0ef59bf77094cdf3f9018b18f76fe97e`.

The tool checks the ROM and binary identities. It also checks the installed
record, the low-16-bit rule, the module receipt, the two exact rooms and the
module-view counters. The tests are `tests/test_sprite_10.py` and pass 7/7. The
full suite passes 234/234 tests. The log is
`local/reports/unit-tests-sprite10-donor.log`.
