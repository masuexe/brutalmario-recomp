# Native sprite 25 module review

## Cumulative integration (2026-10-30)

The [current cumulative recovery](native-sprite-product-reconciliation.md)
installs the newest official Boss program, byte-identical to this7hero source,
in bank8F. All nine fresh source/native samples match19 actor fields and slots,
including actual Y240-to111 ascent. Earlier independent captures below remain
historical; full room/boss behavior remains open.

## Result

The official `7hero` holds a type-1 record for custom sprite slot `25`. The
recipient places that slot in room `154` but holds the type-0 placeholder
record. This document records the review of the record, the protected program
and one built target. The target carries the record and runs the donor program
from the free bank `A8`. Room `154` entry matches the donor.

## Record

| Item | Value |
| --- | --- |
| Slot | `25` |
| Donor record | `012800073f019944acab2002ac200000` |
| Init | `20: ABAC` |
| Main | `20: AC02` |
| Rooms | `154` |
| Recipient record | `0000ffffffffffff218001218001ffff` |

The donor program lives in one protected block. The block starts at `20:AB9D`,
is 8,801 bytes long and has SHA-256
`3557997cedcd519ecf3e6b04241c4c93ef95512bb70b837adec40874bc836ead`.

## Program review

The audit holds 69 local entry states and 3,040 instruction variants. It finds
15 outside calls and no unreviewed indirect jump. The program holds no inline
dispatch table.

Fourteen of the calls are byte-identical in the recipient. Call `0187A7` is
the SpriteTool constructor hook, which points to `10:B059` in the donor and to
`31:8177` in the recipient.

## Mapping

The block moves to the free bank `A8` and keeps its low address bits:
`A8:AB9D`. The record init and main fields become `A8:ABAC` and `A8:AC02`. The
adapted record is `012800073f019944acaba802aca80000`, and the install site is
file offset `1606850` in the recipient.

## Built target

The target is `demo11-native-sprite25`. Its recipe is
`config/native-content/sprite25-module.json` and its config is
`config/restorations/demo11-native-sprite25.json`.

| Item | Value |
| --- | --- |
| Target ROM | `eab25bfaf6ff72330ec5dc033de09e19c85c4da293c53d4e54ad10f67dd4bd4b` |
| Install site | file offset `1606850` |
| Installed record | `012800073f019944acaba802aca80000` |

The target mounts three packs. The pack variables keep the names
`BM_SEVEN_CODE_PACK`, `BM_NATIVE_SPRITE_PACK` and
`BM_NATIVE_GRAPHICS_PACK`.

## Entry result

Both hosts run the fixture `sprite25-room154-native.script`. The donor capture
is `sprite25-154-donor-v1` and the target capture is
`sprite25-154-native-v1`. Each row lists `(slot, sprite, custom, x, y)`.

| Sample | Donor | Target | Rows equal |
| --- | --- | --- | --- |
| `r1` | `(9,28,25,208,227)` | `(9,28,25,208,232)` | no, Y 5 px |
| `r2` | `(9,28,25,208,202)` | `(9,28,25,208,207)` | no, Y 5 px |
| `r3` | `(9,28,25,208,177)` | `(9,28,25,208,182)` | no, Y 5 px |

Slot, sprite, custom id and X match in every sample. Y holds a constant
5-pixel difference.

The fine captures `sprite25-154-fine-donor-v1` and
`sprite25-154-fine-native-v1` show the cause. The donor enters mode `0x14` at
frame 240 and the target at frame 230, a ten-frame load-phase gap. The actor Y
then differs by one pixel at most, so the fall path and the speed are the same.

The run reports `bank=A8 resolutions=1938756 executed_page_instructions=339513`
and no `BRK`.

## Reproduction

```
python3 tools/m1.py --target demo11-native-sprite25 scaffold
python3 tools/m1.py --target demo11-native-sprite25 generate
python3 tools/m1.py --target demo11-native-sprite25 build
python3 tools/m1.py --target demo11-native-sprite25 native --script recomp/inputs/sprite25-room154-native.script --capture sprite25-154-native-v1
python3 tools/qualify_sprite25_gap.py
```

The donor manifest is `config/7hero-donor.json`. The qualification tool is
`tools/qualify_sprite25_gap.py`. Its report is
`local/reports/native-sprite25-final.json`, SHA-256
`742b802adac791d1c737b2919209c3d162e508a8a215bdbdab07ab056ba44d4a`.

## Limits

This document claims the static review, the built target and entry parity for
room `154`. It does not claim movement, a course pass or a clear. The sprite
graphics review stays open.

The tests are `tests/test_sprite_25.py` and pass 5/5. The full suite passes
228/228 tests. The log is `local/reports/unit-tests-sprite25.log`.
