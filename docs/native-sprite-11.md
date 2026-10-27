# Native sprite 11 module review

## Result

The official `cheap-demo` holds a type-1 record for custom sprite slot `11`.
The recipient places that slot in four rooms but holds the type-0 placeholder
record. This document records the review of the record, the protected program
and one built target. The target carries the record and runs the donor program
from the free bank `AA`. Room `158` entry matches the donor.

## Record

| Item | Value |
| --- | --- |
| Slot | `11` |
| Donor record | `01360000f8a22d454bb01a06b11a0000` |
| Init | `1A: B04B` |
| Main | `1A: B106` |
| Rooms | `155`, `156`, `158`, `159` |
| Recipient record | `0000ffffffffffff218001218001ffff` |

The donor program lives in one protected block. The block starts at `1A:B03C`,
is 5,032 bytes long and has SHA-256
`cb09373c41521be34c7812e49dccad8a66b267470f8f5d73198144e977e27804`.

## Program review

The audit holds 54 local entry states and 2,037 instruction variants. It finds
15 outside calls, no unreviewed indirect jump and no source-bank long call.

## Mapping

The block moves to the free bank `AA` and keeps its low address bits:
`AA:B03C`. The record init and main fields become `AA:B04B` and `AA:B106`. The
adapted record is `01360000f8a22d454bb0aa06b1aa0000`, and the install site is
file offset `1606530` in the recipient.

## Built target

The target is `demo11-native-sprite11`. Its recipe is
`config/native-content/sprite11-module.json` and its config is
`config/restorations/demo11-native-sprite11.json`.

| Item | Value |
| --- | --- |
| Target ROM | `61b3155b5ddab405a90232251020191995e7fbf436eb54434a1567d430024ba9` |
| Install site | file offset `1606530` |
| Installed record | `01360000f8a22d454bb0aa06b1aa0000` |

The target mounts three packs. The pack variables keep the names
`BM_SEVEN_CODE_PACK`, `BM_NATIVE_SPRITE_PACK` and
`BM_NATIVE_GRAPHICS_PACK`.

## Entry result

Both hosts run the fixture `sprite11-room158-shared.script`. The donor capture
is `sprite11-158-donor-v1` and the target capture is
`sprite11-158-native-v1`. Each row lists `(slot, sprite, custom, x, y)`.

| Sample | Donor | Target | Rows equal |
| --- | --- | --- | --- |
| `r1` | `(8,36,17,280,352)`, `(9,36,17,152,352)` | same | yes |
| `r2` | same | same | yes |
| `r3` | same | same | yes |

Rooms `156` and `158` also place slot `10`, which this target does not carry,
so their full actor list cannot match. The slot `11` rows match.

The run reports `bank=AA resolutions=511856 executed_page_instructions=82703`
and no `BRK`.

## Reproduction

```
python3 tools/m1.py --target demo11-native-sprite11 scaffold
python3 tools/m1.py --target demo11-native-sprite11 generate
python3 tools/m1.py --target demo11-native-sprite11 build
python3 tools/m1.py --target demo11-native-sprite11 native --script recomp/inputs/sprite11-room158-shared.script --capture sprite11-158-native-v1
python3 tools/qualify_sprite11_gap.py
```

The donor manifest is `config/cheap-demo-donor.json`. The qualification tool is
`tools/qualify_sprite11_gap.py`. Its report is
`local/reports/native-sprite11-final.json`, SHA-256
`711a6c1312945d080d94195bd5038b0824c2810489a5378b5023704f25a582a2`.

## Limits

This document claims the static review, the built target and entry parity for
room `158`. It does not claim the other three rooms, movement, a course pass or
a clear. The sprite graphics review stays open.

The tests are `tests/test_sprite_11.py` and pass 5/5. The full suite passes
239/239 tests. The log is `local/reports/unit-tests-sprite11.log`.
