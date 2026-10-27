# Native sprite 95 module review

## Result

The new official donor `7hero` holds a type-1 record for custom sprite slot
`95`. The recipient places that slot in seven rooms but holds the type-0
placeholder record. This document records the static review of the record, the
protected program and the dispatch table. It does not install the record and it
does not claim behavior.

## Record

| Item | Value |
| --- | --- |
| Slot | `95` |
| Donor record | `013600003f0399641ae42039e5200000` |
| Init | `20: E41A` |
| Main | `20: E539` |
| Rooms | `16B`, `16C`, `16D`, `16E`, `16F`, `172`, `1CC` |
| Recipient record | `0000ffffffffffff218001218001ffff` |

The donor program lives in one protected block. The block starts at `20:E40B`, is
5,144 bytes long and has SHA-256
`20980e341c2877b32e286cb7053450ffcb54f1ee74f55f79f7a0b0b1236a6454`.

## Program review

The audit holds 52 local entry states and 2,086 instruction variants. It finds
17 outside calls, no source-bank long call and no unreviewed indirect jump.

The program dispatches through one inline table at `20:E541`. The table holds
17 entries of the form `20 lo hi`. Each entry is a JSR to a target inside the
block. The table SHA-256 is
`a4e01ed44f0046775283803db8e2b90d1794eca05c7069978cf7fd1f0094b73c`. The
dispatcher at `20:E587` holds `6c 00 00`, which is `JMP ($0000)`.

The dispatcher reads a state word at `$1504`, scales it by three and loads the
entry address from the table into `$00` and `$01`. It then jumps through
`$0000`. The table therefore must carry the same relocatable targets as the
program.

The outside calls are `00F5B7`, `01801A`, `018022`, `01802A`, `0187A7`,
`019138`, `01A7DC`, `01ACF9`, `01B44F`, `01B7B3`, `02A9DE`, `07F7D2`,
`27FB02`, `28FCC0` and `2E8DF0`. Fourteen of them are byte-identical in the
recipient. Call `0187A7` is the SpriteTool constructor hook, which points to
`10:B059` in the donor and to `31:8177` in the recipient. The call therefore
enters the recipient constructor, which is the intended target.

## Planned mapping

The plan maps the block to the free bank `A3` at `A3:E40B`. The plan then
changes the record init and main fields to `A3:E41A` and `A3:E539`. The
adapted record is `013600003f0399641ae4a339e5a30000`, and the install site is
file offset `1608642` in the recipient.

The plan keeps the variable name `BM_SEVEN_CODE_PACK` for the pack loader. The
runtime mapping and the graphics review for rooms `16B` to `1CC` stay open.

## Reproduction

```
python3 tools/prepare_sprite_module.py
python3 -m unittest tests.test_sprite_module -v
```

The recipe is `config/native-content/sprite95-module.json`. The donor manifest
is `config/7hero-donor.json`. The module receipt is
`local/native-modules/sprite95-v1/preparation-receipt.json`, SHA-256
`2453be33f3d128707e71b79ae416bde4cdb362deea57ed73425e49377dbdb486`. The tests
are `tests/test_sprite_module.py` and pass 5/5. The full suite passes 202/202
tests. The log is `local/reports/unit-tests-sprite95.log`.
