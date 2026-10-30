# Native sprite 33 module review

## Cumulative integration (2026-10-30)

The [current cumulative recovery](native-sprite-product-reconciliation.md)
installs the newest official Boss program, byte-identical to this7hero source,
in bank8E. Nine fresh samples match all19 actor fields and slots, including
X208-to133 movement and matching game-driven player movement. Full-room and
exit acceptance remains open; the independent captures below are historical.

## Result

The official `7hero` holds a type-1 record for custom sprite slot `33`. The
recipient places that slot in room `0FE` but holds the type-0 placeholder
record. This document records the review of the record, the protected program
and one built target. The target carries the record and runs the donor program
from the free bank `A7`. Room `0FE` entry matches the donor.

## Record

| Item | Value |
| --- | --- |
| Slot | `33` |
| Donor record | `0136000035a299440dae151dae150000` |
| Init | `15: AE0D` |
| Main | `15: AE1D` |
| Rooms | `0FE` |
| Recipient record | `0000ffffffffffff218001218001ffff` |

The donor program lives in one protected block. The block starts at `15:ADFE`,
is 1,328 bytes long and has SHA-256
`60831043e677facacf4d3c901226973f6d67fe1e5a92a0a9b888083d6d681895`.

## Program review

The audit holds 10 local entry states and 504 instruction variants. It finds
four outside calls and no unreviewed indirect jump. The program holds no inline
dispatch table.

The outside calls are `0187A7`, `01B7B3`, `02A9DE` and `07F7D2`. The call
`0187A7` is the SpriteTool constructor hook.

## Mapping

The block moves to the free bank `A7` and keeps its low address bits:
`A7:ADFE`. The record init and main fields become `A7:AE0D` and `A7:AE1D`. The
adapted record is `0136000035a299440daea71daea70000`, and the install site is
file offset `1607074` in the recipient.

## Built target

The target is `demo11-native-sprite33`. Its recipe is
`config/native-content/sprite33-module.json` and its config is
`config/restorations/demo11-native-sprite33.json`.

| Item | Value |
| --- | --- |
| Target ROM | `3e1d1417436f8b6aca51fa8fc9e7eee8a5f520df5cec3f152d0b9d00d36cd64f` |
| Install site | file offset `1607074` |
| Installed record | `0136000035a299440daea71daea70000` |

The target mounts three packs. The pack variables keep the names
`BM_SEVEN_CODE_PACK`, `BM_NATIVE_SPRITE_PACK` and
`BM_NATIVE_GRAPHICS_PACK`.

## Entry result

Both hosts run the fixture `sprite33-room0fe-native.script`. The donor capture
is `sprite33-0fe-donor-v1` and the target capture is
`sprite33-0fe-native-v1`. Each row lists `(slot, sprite, custom, x, y)`.

| Sample | Donor | Target | Rows equal |
| --- | --- | --- | --- |
| `r1` | `(9,36,51,208,368)` | same | yes |
| `r2` | `(9,36,51,147,368)` | `(9,36,51,139,368)` | no, X 8 px |
| `r3` | `(9,36,51,133,368)` | same | yes |

The run reports `bank=A7 resolutions=159260 executed_page_instructions=26463`
and no `BRK`.

## Reproduction

```
python3 tools/m1.py --target demo11-native-sprite33 scaffold
python3 tools/m1.py --target demo11-native-sprite33 generate
python3 tools/m1.py --target demo11-native-sprite33 build
python3 tools/m1.py --target demo11-native-sprite33 native --script recomp/inputs/sprite33-room0fe-native.script --capture sprite33-0fe-native-v1
python3 tools/qualify_sprite33_gap.py
```

The donor manifest is `config/7hero-donor.json`. The qualification tool is
`tools/qualify_sprite33_gap.py`. Its report is
`local/reports/native-sprite33-final.json`, SHA-256
`a2248f629ed3803cfe740cf48f28d02d28afbfe9a72839717ef50577986e0314`.

## Limits

This document claims the static review, the built target and entry parity for
room `0FE`. It does not claim movement, a course pass or a clear. The sprite
graphics review stays open.

The tests are `tests/test_sprite_33.py` and pass 5/5. The full suite passes
223/223 tests. The log is `local/reports/unit-tests-sprite33.log`.
