# Native mazo B0 corridor plan

## Result

The mazo `B0` corridor actor has a static module review. The corridor rooms are
not in the recipient. This document records the measured data and the next
steps. It does not qualify playability.

## Module

| Item | Value |
| --- | --- |
| Record | `01400080308300009889139d89130000` |
| Init | `13:8998` |
| Main | `13:899D` |
| Block | `13:8989`, 419 bytes, SHA-256 `b98c2ce2014d4cff3e8fcbb75eec936b8e04446e503f541ce9efdff85b8846e8` |
| Native view candidate | `A2:8989` |

The audit finds 6 entry states and 177 instruction variants. The module has no
dispatch table and no call patch. It has no source-bank long reference. Its 6
absolute operands stay inside the block. The four outside calls are
`01A7DC`, `01ACF9`, `01B7B3` and `0285BA`.

The recipe is `config/native-content/mazo-b0-module.json`. The module receipt
is `local/native-modules/mazo-b0-v1/preparation-receipt.json`, SHA-256
`188fc1bb41bf1a95af89c17889049c007fe110ba4201ab398bac927afa137b5c`.

The module tests pass 10/10. The full suite passes 186/186 tests. The log is
`local/reports/unit-tests-mazo-corridor.log`.

## Corridor data

| Room | L1 bytes | L2 | Sprite list bytes |
| --- | ---: | --- | ---: |
| `00D` | 26 | empty (`FF`) | 8 |
| `10C` | 11 | empty (`FF`) | 8 |
| `191` | 110 | sentinel `FFDE54` | 11 |
| `192` | 104 | sentinel `FFDE54` | 8 |

Each room also has a 32-byte graphics and palette record. The level streams and
the sprite lists total 288 bytes. The records total 128 bytes. One external
bank of 32 KiB has enough room.

The donor L1 streams are raw object streams that end with `FF`. The `FFDE54`
L2 values are empty-layer sentinels. Copy the values, not layers.

The recipient rooms differ. Rooms `00D` and `10C` point at other level and
sprite data. Rooms `191` and `192` point at the empty level `0x068000`. The
recipient has 49 level entries that point at `0x068000`.

## Namespace

The recipient `B0` slot is the ForestStar room `003` actor. Keep that slot.
The donor `B0` program needs a free SpriteTool slot.

A sprite list starts with one header byte. The 3-byte entries follow it and
end with `FF`. A room entry carries the custom id in byte 2 when bit 3 of byte
0 is active. The imported lists change byte 2 from `B0` to `A9`.

The plan uses the free SpriteTool slot `A9`. The slot record is a type-0
placeholder and no recipient room places custom id `A9`.

## Prepared plan

The plan uses four target level slots. Slots `191` and `192` keep their donor
numbers because the recipient entries are empty. Rooms `00D` and `10C` move
to free slots `183` and `184`.

Each target slot is empty level `0x068000`. No room has a screen exit to a
target slot. No target slot byte occurs in the decoded map. The donor room
`00D` has exits to rooms `166`, `162` and `164`. Those rooms are not
imported. Rooms `10C`, `191` and `192` have no primary exit.

The pack is `mazo-b0-corridor.bin`, 288 bytes, SHA-256
`887eee9103f7d8838dfae70839e049f3c43d144e500cef8290749c559a9d7c00`.
The recipe is `config/native-content/mazo-b0-corridor.json`. The integration
plan has 21 patches. The projected ROM SHA-256 is
`405ba709779d8ac14a802a4fbab327e57cfd4fa585f0c22f6b5b59b2b02d5d07`.
The receipt is
`local/native-modules/mazo-b0-corridor-v1/preparation-receipt.json`, SHA-256
`c2e4ad1aa94636ea21068326d0f09203b04d40bd714d3fdfe75c04e4ea9f5fac`. The tool
is `tools/prepare_mazo_b0_corridor.py`.

## Next steps

1. Add a target with the A2 code pack, the A7 data pack, the A5 sprite pack and
   the B6 graphics pack. Extend the mazo runtime to mount the A7 data pack.
2. Capture a fixture entry into the imported rooms. Qualify the actors and the
   room graphics.
3. Record the relocated exits of room `00D`. They stay outside this bounded
   entry check.
4. Never overwrite the recipient `B0` slot.

## Reproduction

```
python3 -c "import sys; sys.path.insert(0, 'tools'); import prepare_mazo_module as p; from pathlib import Path; p.prepare(Path('local/native-modules/mazo-b0-v1').resolve(), Path('config/native-content/mazo-b0-module.json').resolve())"
python3 tools/prepare_mazo_b0_corridor.py --write-recipe
python3 tools/prepare_mazo_b0_corridor.py
python3 -m unittest discover -s tests -p test_mazo_module.py -v
```
