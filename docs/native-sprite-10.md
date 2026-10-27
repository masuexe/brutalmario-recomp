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

## Planned mapping

The plan maps the block to the free bank `A4` at `A4:E61F`. The plan then
changes the record init and main fields to `A4:E62E` and `A4:E6D1`. The
adapted record is `01360080398391002ee6a4d1e6a40000`, and the install site is
file offset `1606514` in the recipient.

## Built target

The target is `demo11-native-sprite10`. Its recipe is
`config/native-content/sprite10-module.json` and its config is
`config/restorations/demo11-native-sprite10.json`.

| Item | Value |
| --- | --- |
| Target ROM | `be1acd21694b717edb6b1f87613ff75f86dd4ef96fc0cf8db4a4f90b5ec96f9c` |
| Install site | file offset `1606514` |
| Installed record | `01360080398391002ee6a4d1e6a40000` |

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
SHA-256 `eee86df4140cac3f70c2dd82bae2a7cfc110854d4d91741684c5e4efcd79da0d`.

## Limits

The graphics review stays open. This document claims one built target and one
static module review. It does not claim gameplay, donor parity, a course pass or
a clear.

## Entry qualification

The entry comparison stays open. The donor and the target hold the same room
numbers, but the room numbers are version-local. The `7hero` preamble enters
rooms `16B` and `16C` through a pipe path. The same preamble in `cheap-demo`
reaches room `14D` and then mode `0x0E`, so the probe does not reach rooms
`12D` to `15C`.

The target capture `sprite10-12d-staged-native-v1` shows four actors with
custom id `10` and reports `bank=A4 resolutions=355
executed_page_instructions=54`. The module view therefore runs when a room
places the record. The target also loads room `157` and room `15C` in mode
`0x14`.

A donor fixture for the `cheap-demo` map path stays open. Until that fixture
exists, this document claims the static review, the built target and one
module-view run. It does not claim donor parity.

The tests are `tests/test_sprite_10.py` and pass 4/4. The full suite passes
211/211 tests. The log is `local/reports/unit-tests-sprite10.log`.
