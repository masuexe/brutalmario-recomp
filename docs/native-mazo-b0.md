# Native mazo B0 corridor plan

## Result

The mazo `B0` corridor actor has a static module review and a built target.
The four imported corridor rooms load. Rooms `191` and `192` enter gameplay
and match the donor actor set. Rooms `183` and `184` are transition steps that
load and then fade to room `190`. The donor image shows the same transition
from rooms `00D` and `10C`. This document records the measured data and the
bounded entry. It does not qualify full corridor playability.

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

The module tests pass 11/11. The full suite passes 187/187 tests. The log is
`local/reports/unit-tests-mazo-b0-entry.log`.

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

The plan has a level table policy. Rooms `00D` and `10C` keep the recipient
level tables. The donor table values crash the level load. Rooms `191` and
`192` copy the donor values. These two rooms load with the copied values.

The pack is `mazo-b0-corridor.bin`, 288 bytes, SHA-256
`4d90fc094324a035745d9c26d26af49299ff1e771cbf13a85c3744ed788af94d`.
The recipe is `config/native-content/mazo-b0-corridor.json`. The integration
plan has 33 patches. The projected ROM SHA-256 is
`67e5b578ff0efac53e732ed008dc0a5b740a96b05c815e15803268185c2d1875`.
The receipt is
`local/native-modules/mazo-b0-corridor-v1/preparation-receipt.json`, SHA-256
`1ae24236421222be44342a29dd03ab0fe98817b8670a3b1107790a267ffa9808`. The tool
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
`67e5b578ff0efac53e732ed008dc0a5b740a96b05c815e15803268185c2d1875`. The
native binary SHA-256 is
`20d44ee859dabadbc518866beba71144123e2cf60389b7a1cfff34d70fe08f49`.

The room `191` entry works. The capture is
`local/captures/mazo-b0-room191-v2-native`. It loads mode `14` in room
`0x191`. Custom actor `A9` is active in slot `7` at `(192,368)`. Standard
sprites `77` occupy slots `8` and `9`. The A7 data pack resolves 1,166 reads
and the A2 module view executes.

The room `183` entry is a transition step. The fine capture is
`local/captures/mazo-b0-room183-fine-v1`. At frame 180 it loads mode `15` in
room `0x183`. Two custom actors `A9` occupy slots `8` and `9` at `(272,48)`
and `(32,64)`. At frame 190 the mode is `17` in room `0x190`. At frame 230
the mode is `20` in room `0x190`. The capture has no gameplay frame in room
`0x183`.

The room `184` entry matches room `183`. The capture is
`local/captures/mazo-b0-room184-v1-native`.

## Entry qualification

`tools/qualify_mazo_b0.py` checks the target identities, the graphics
records, the entry mode and room, the custom `A9` actor set and the donor
actor set. The report is `local/reports/native-mazo-b0-final.json`, SHA-256
`a0c3f93defb0b2acc0c8c9ba8019ec9e5a5a7e9cf83acbf092083d43ca21bf36`.

| Room | Slot | Entry mode | Actors | Cap |
| --- | --- | ---: | --- | --- |
| `00D` | `183` | `15` | two custom `A9` | Load step. Both images fade to `190`. |
| `10C` | `184` | `15` | two custom `A9` | Load step. Both images fade to `190`. |
| `191` | `191` | `14` | three, donor parity | None. |
| `192` | `192` | `14` | two, donor parity | None. |

The donor captures are `mazo-b0-donor191-v1` and `mazo-b0-donor192-v1`. The
donor actor sets match the native actor sets. The custom id changes from `B0`
to `A9`.

The donor transition captures are `mazo-b0-donor00d-fine-v1` and
`mazo-b0-donor10c-fine-v1`. At frame 160 the donor is in mode `17` in room
`0x00D` or room `0x10C`. At frame 180 the donor is in room `0x190`. The native
rooms `183` and `184` do the same.

The room `183` frame at mode `15` shows a load step. The frame is not a
gameplay frame. The room `183` and room `184` captures do not qualify
graphics. The donor pipe chain through rooms `00D` and `10C` stays unverified.

## Next steps

1. Record the relocated exits of room `00D`. They stay outside this bounded
   entry check.
2. Record the corridor camera, palette and sprite behavior in rooms `191` and
   `192` against the donor captures.
3. Never overwrite the recipient `B0` slot.

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
python3 tools/qualify_mazo_b0.py
python3 -m unittest discover -s tests -p test_mazo_module.py -v
```
