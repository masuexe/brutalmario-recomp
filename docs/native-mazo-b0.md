# Native mazo B0 corridor plan

## Result

The mazo `B0` corridor actor has a static module review and a built target.
One imported corridor room enters gameplay. Rooms `00D` and `10C` still fail
to load. This document records the measured data and the open failure. It does
not qualify full corridor playability.

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

The module tests pass 11/11.

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

The donor rooms `00D` and `10C` use legacy music `31` in the level header.
The modern family has no row for that track, so the copied header uses music
`02`. Rooms `191` and `192` keep music `02`.

The pack is `mazo-b0-corridor.bin`, 288 bytes, SHA-256
`4d90fc094324a035745d9c26d26af49299ff1e771cbf13a85c3744ed788af94d`.
The recipe is `config/native-content/mazo-b0-corridor.json`. The integration
plan has 45 patches. The projected ROM SHA-256 is
`5711ea39a84c02416efb427dd0f1bbd085f944c1412446636c10baaf28e53511`.
The receipt is
`local/native-modules/mazo-b0-corridor-v1/preparation-receipt.json`, SHA-256
`0140e6306f79c78f936e88237d69500e78bfd1a50b54e968c6f501801e5f95b2`. The tool
is `tools/prepare_mazo_b0_corridor.py`.

## Target and entry

The target is `demo11-native-mazo-b0`. Its recipe is
`config/native-content/mazo-b0.json`. The target mounts four packs:

| Pack | Bank | Address | Size |
| --- | --- | ---: | ---: |
| `mazo-b0-code.bin` | `A2` | `A28989` | 419 |
| `sprite9e.bin` | `A5` | `A595CD` | 1,291 |
| `star1-ffd.bin` | `B6` | `B68008` | 3,001 |
| `mazo-b0-corridor.bin` | `A7` | `A78000` | 288 |

The target ROM SHA-256 is
`5711ea39a84c02416efb427dd0f1bbd085f944c1412446636c10baaf28e53511`. The
native binary SHA-256 is
`272b0edd2fc956e523377976b58ab9109b1d4512a7fecd10a6f56c6dcc27b94c`.

The room `191` entry works. The capture is
`local/captures/mazo-b0-room191-v1-native`. It loads mode `14` in room
`0x191`. Custom actor `A9` is active in slot `7` at `(192,368)`. Standard
sprites `77` occupy slots `8` and `9`. The A7 data pack resolves 1,166 reads
and the A2 module view executes.

The room `183` entry fails. The capture is
`local/captures/mazo-b0-room183-v3-native`. The host enters a bad state with
mode `34` and room `0x3400`. The actor slots hold garbage. The failure stays
open. The donor rooms `00D` and `10C` have level header bytes `c0 70`.
Room `191` has `40 30`.

## Next steps

1. Diagnose the rooms `00D` and `10C` load failure. Test the level bytes with
   an empty sprite list first. Then compare the header mode bytes and the
   layer 2 handling.
2. Qualify the room `191` graphics, camera and actor behavior against the
   donor capture.
3. Record the relocated exits of room `00D`. They stay outside this bounded
   entry check.
4. Never overwrite the recipient `B0` slot.

## Reproduction

```
python3 -c "import sys; sys.path.insert(0, 'tools'); import prepare_mazo_module as p; from pathlib import Path; p.prepare(Path('local/native-modules/mazo-b0-v1').resolve(), Path('config/native-content/mazo-b0-module.json').resolve())"
python3 tools/prepare_mazo_b0_corridor.py --write-recipe
python3 tools/prepare_mazo_b0_corridor.py
python3 tools/native_seven.py
python3 -c "import sys; sys.path.insert(0, 'tools'); import native_mazo as n; n.prepare('demo11-native-mazo-b0')"
python3 tools/m1.py --target demo11-native-mazo-b0 scaffold
python3 tools/m1.py --target demo11-native-mazo-b0 generate
python3 tools/m1.py --target demo11-native-mazo-b0 build
python3 tools/m1.py --target demo11-native-mazo-b0 native --script recomp/inputs/mazo-b0-room191.script --capture YOUR_FRESH_NAME
python3 -m unittest discover -s tests -p test_mazo_module.py -v
```
