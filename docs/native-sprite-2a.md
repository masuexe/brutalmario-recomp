# Native sprite 2A module review

## Result

The official `7hero` holds a type-1 record for custom sprite slot `2A`. The
recipient places that slot in room `0FF` but holds the type-0 placeholder
record. This document records the review of the record, the protected program
and one built target. The target carries the record and runs the donor program
from the free bank `A9`. Room `0FF` entry matches the donor.

## Record

| Item | Value |
| --- | --- |
| Slot | `2A` |
| Donor record | `0136000035a299440f80228d80220000` |
| Init | `22: 800F` |
| Main | `22: 808D` |
| Rooms | `0FF` |
| Recipient record | `0000ffffffffffff218001218001ffff` |

The donor program lives in one protected block. The block starts at `22:8000`,
is 28,478 bytes long and has SHA-256
`d070d644b5da61d4150e58f4d6603a0ccbe5d0c37b19e7a00c8ffc2d9bb1d757`.

## Program review

The audit holds 4 local entry states before dispatch and 17 outside calls. The
program holds three inline dispatch tables.

| Table | Entries | Dispatcher |
| --- | ---: | --- |
| `22:8095` | 35 | `22:8115` |
| `22:8118` | 23 | `22:81C8` |
| `22:BB7B` | 21 | `22:BBF7` |

Each dispatcher holds `6c 00 00`, which is `JMP ($0000)`. The program also
holds 39 source-bank long calls. Every such call keeps its low 16 bits and
changes its bank byte from `22` to `A9`.

The outside calls are `00F5B7`, `01801A`, `018022`, `01802A`, `0187A7`,
`019138`, `01A7DC`, `01AB99`, `01ACF9`, `01B7B3`, `0285BA`, `02A9DE`, `07F7D2`,
`0FF780`, `10D8D0`, `27FB02` and `28FCC0`.

## Mapping

The block moves to the free bank `A9` and keeps its low address bits:
`A9:8000`. The record init and main fields become `A9:800F` and `A9:808D`. The
adapted record is `0136000035a299440f80a98d80a90000`, and the install site is
file offset `1606930` in the recipient.

The adapted code SHA-256 is
`3bb788a19acd416344ba474c1dcfab278d053878e082562728dd7ae0739e70c9`. It
differs from the donor copy in the 39 bank bytes only.

## Built target

The target is `demo11-native-sprite2a`. Its recipe is
`config/native-content/sprite2a-module.json` and its config is
`config/restorations/demo11-native-sprite2a.json`.

| Item | Value |
| --- | --- |
| Target ROM | `89a8aa220320a1fec0726149ac1c04dd7c84faf5d159bb57e7b1da96e84c0e0c` |
| Install site | file offset `1606930` |
| Installed record | `0136000035a299440f80a98d80a90000` |

The target mounts three packs. The pack variables keep the names
`BM_SEVEN_CODE_PACK`, `BM_NATIVE_SPRITE_PACK` and
`BM_NATIVE_GRAPHICS_PACK`.

## Entry result

Both hosts run the fixture `sprite2a-room0ff-native.script`. The donor capture
is `sprite2a-0ff-donor-v1` and the target capture is
`sprite2a-0ff-native-v1`. Each row lists `(slot, sprite, custom, x, y)`.

| Sample | Donor | Target | Rows equal |
| --- | --- | --- | --- |
| `r1` | `(8,36,42,192,352)`, `(9,36,42,96,312)` | same | yes |
| `r2` | `(8,...,352)`, `(9,...,322)` | `(9,...,323)` | no, Y 1 px |
| `r3` | `(8,...,352)`, `(9,...,319)` | `(9,...,318)` | no, Y 1 px |

The run reports `bank=A9 resolutions=2903535 executed_page_instructions=479816`
and no `BRK`.

## Reproduction

```
python3 tools/m1.py --target demo11-native-sprite2a scaffold
python3 tools/m1.py --target demo11-native-sprite2a generate
python3 tools/m1.py --target demo11-native-sprite2a build
python3 tools/m1.py --target demo11-native-sprite2a native --script recomp/inputs/sprite2a-room0ff-native.script --capture sprite2a-0ff-native-v1
python3 tools/qualify_sprite2a_gap.py
```

The donor manifest is `config/7hero-donor.json`. The qualification tool is
`tools/qualify_sprite2a_gap.py`. Its report is
`local/reports/native-sprite2a-final.json`, SHA-256
`87cf37fee4971d00badd187a6a79af829285244de972a30bc911a2a12056ce0a`.

## Limits

This document claims the static review, the built target and entry parity for
room `0FF`. It does not claim movement, a course pass or a clear. The sprite
graphics review stays open.

The tests are `tests/test_sprite_2a.py` and pass 5/5. The full suite passes
233/233 tests. The log is `local/reports/unit-tests-sprite2a.log`.
