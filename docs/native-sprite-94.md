# Native sprite 94 module review

## Cumulative integration (2026-10-30)

The [current cumulative recovery](native-sprite-product-reconciliation.md)
installs the newest official Boss program, byte-identical to this7hero source,
in bank8D. Nine fresh samples match both actors’19 fields and slots, including
the moving actor’s phase0/1 cycle. Full-room and exit acceptance remains open;
the earlier independent captures below retain their original identities.

## Result

The official `7hero` holds a type-1 record for custom sprite slot `94`. The
recipient places that slot in room `0EF` but holds the type-0 placeholder
record. This document records the review of the record, the protected program
and one built target. The target carries the record and runs the donor program
from the free bank `A6`. Room `0EF` entry matches the donor.

## Record

| Item | Value |
| --- | --- |
| Slot | `94` |
| Donor record | `013600073f8319645cb31771b3170000` |
| Init | `17: B35C` |
| Main | `17: B371` |
| Rooms | `0EF` |
| Recipient record | `0000ffffffffffff218001218001ffff` |

The donor program lives in one protected block. The block starts at `17:B34D`,
is 2,096 bytes long and has SHA-256
`4ced2fe700c642d539ba511418d1c7e35c811cb04d2e77b01d1faa08006c7693`.

## Program review

The audit holds 25 local entry states and 898 instruction variants. It finds
14 outside calls and no unreviewed indirect jump. The program holds no inline
dispatch table.

## Mapping

The block moves to the free bank `A6` and keeps its low address bits:
`A6:B34D`. The record init and main fields become `A6:B35C` and `A6:B371`. The
adapted record is `013600073f8319645cb3a671b3a60000`, and the install site is
file offset `1608626` in the recipient.

## Built target

The target is `demo11-native-sprite94`. Its recipe is
`config/native-content/sprite94-module.json` and its config is
`config/restorations/demo11-native-sprite94.json`.

| Item | Value |
| --- | --- |
| Target ROM | `5d0e759231117a468bcd75d0eff776dc49405d58f5afe90095d2d0999a13de26` |
| Install site | file offset `1608626` |
| Installed record | `013600073f8319645cb3a671b3a60000` |

The target mounts three packs. The pack variables keep the names
`BM_SEVEN_CODE_PACK`, `BM_NATIVE_SPRITE_PACK` and
`BM_NATIVE_GRAPHICS_PACK`.

## Entry result

Both hosts run the fixture `sprite94-room0ef-native.script`. The donor capture
is `sprite94-0ef-donor-v1` and the target capture is
`sprite94-0ef-native-v1`.

| Sample | Donor | Target | Rows equal |
| --- | --- | --- | --- |
| `r1` | `(8,36,94,176,224)`, `(9,36,94,112,229)` | `(8,36,94,176,224)`, `(9,36,94,112,222)` | no, Y 7 px |
| `r2` | `(8,36,94,176,224)`, `(9,36,94,112,320)` | same | yes |
| `r3` | same as `r2` | same | yes |

Each row lists `(slot, sprite, custom, x, y)`. The first sample holds a
7-pixel Y difference in slot 9. The later samples match the donor exactly.
The run reports `bank=A6 resolutions=1007960
executed_page_instructions=169640` and no `BRK`.

## Reproduction

```
python3 tools/m1.py --target demo11-native-sprite94 scaffold
python3 tools/m1.py --target demo11-native-sprite94 generate
python3 tools/m1.py --target demo11-native-sprite94 build
python3 tools/m1.py --target demo11-native-sprite94 native --script recomp/inputs/sprite94-room0ef-native.script --capture sprite94-0ef-native-v1
python3 tools/qualify_sprite94_gap.py
```

The donor manifest is `config/7hero-donor.json`. The qualification tool is
`tools/qualify_sprite94_gap.py`. Its report is
`local/reports/native-sprite94-final.json`, SHA-256
`7d00bbd5ef877b510f0c10fefdadbfa7fe43c365550664b15d0d9dba48660505`.

## Limits

This document claims the static review, the built target and entry parity for
room `0EF`. It does not claim movement, a course pass or a clear. The sprite
graphics review stays open.

The tests are `tests/test_sprite_94.py` and pass 5/5. The full suite passes
218/218 tests. The log is `local/reports/unit-tests-sprite94.log`.
