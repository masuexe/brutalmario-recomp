# Native sprite 12 module review

## Result

The official `cheap-demo` holds a type-1 record for custom sprite slot `12`.
The recipient places that slot in five rooms but holds the type-0 placeholder
record. This document records the review of the record, the protected program
and one built target. The target carries the record and runs the donor program
from the free bank `AB`. Room `155` slot `12` rows match the donor.

## Record

| Item | Value |
| --- | --- |
| Slot | `12` |
| Donor record | `01361080388101046292168092160000` |
| Init | `16: 9262` |
| Main | `16: 9280` |
| Rooms | `155`, `157`, `159`, `15B`, `15C` |
| Recipient record | `0000ffffffffffff218001218001ffff` |

The donor program lives in one protected block. The block starts at `16:9253`,
is 1,358 bytes long and has SHA-256
`e644151b127d5adbca27671a1cc9242377e6fad07df8e4224ef5be51f2888c34`.

## Program review

The audit holds 17 local entry states and 584 instruction variants. It finds
nine outside calls, no unreviewed indirect jump and no source-bank long call.

The outside calls are `00F5B7`, `01802A`, `0187A7`, `01A7DC`, `01AB99`,
`01B7B3`, `02A9DE`, `07F7D2` and `27FAF4`.

## Mapping

The block moves to the free bank `AB` and keeps its low address bits:
`AB:9253`. The record init and main fields become `AB:9262` and `AB:9280`. The
adapted record is `01361080388101046292ab8092ab0000`, and the install site is
file offset `1606546` in the recipient.

## Built target

The target is `demo11-native-sprite12`. Its recipe is
`config/native-content/sprite12-module.json` and its config is
`config/restorations/demo11-native-sprite12.json`.

| Item | Value |
| --- | --- |
| Target ROM | `fbf844cbaadd7634591b5e1e00417ca7ae95dada75a75e6e4c0aabf06fcae917` |
| Install site | file offset `1606546` |
| Installed record | `01361080388101046292ab8092ab0000` |

The target mounts three packs. The pack variables keep the names
`BM_SEVEN_CODE_PACK`, `BM_NATIVE_SPRITE_PACK` and
`BM_NATIVE_GRAPHICS_PACK`.

## Entry result

Both hosts run the fixture `sprite12-room155-shared.script`. The donor capture
is `sprite12-155-donor-v1` and the target capture is
`sprite12-155-native-v1`. Each row lists `(slot, sprite, custom, x, y)`.

| Sample | Donor slot 12 rows | Target | Rows equal |
| --- | --- | --- | --- |
| `r1` | `(8,36,18,304,304)`, `(9,36,18,176,304)` | same | yes |
| `r2` | same | same | yes |
| `r3` | same | same | yes |
| `r4` | `(8,...)`, `(9,36,18,159,304)` | same | yes |

Every room that places slot `12` also places other gap slots, so a full actor
list cannot match yet. The slot `12` rows match in all four samples.

The run reports `bank=AB resolutions=1250895 executed_page_instructions=210437`
and no `BRK`.

## Reproduction

```
python3 tools/m1.py --target demo11-native-sprite12 scaffold
python3 tools/m1.py --target demo11-native-sprite12 generate
python3 tools/m1.py --target demo11-native-sprite12 build
python3 tools/m1.py --target demo11-native-sprite12 native --script recomp/inputs/sprite12-room155-shared.script --capture sprite12-155-native-v1
python3 tools/qualify_sprite12_gap.py
```

The donor manifest is `config/cheap-demo-donor.json`. The qualification tool is
`tools/qualify_sprite12_gap.py`. Its report is
`local/reports/native-sprite12-final.json`, SHA-256
`4c5a4fd8f0e1f2a4266b2a8d7cb97c4e68fe9a460f12ea6ba339652821439a26`.

## Limits

This document claims the static review, the built target and slot `12` entry
parity. It does not claim a full actor list, movement, a course pass or a
clear. The sprite graphics review stays open.

The tests are `tests/test_sprite_12.py` and pass 5/5. The full suite passes
244/244 tests. The log is `local/reports/unit-tests-sprite12.log`.
