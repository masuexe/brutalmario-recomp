# Native full sprite gap target review

## Result

The recipient holds 54 custom sprite slots with the type-0 placeholder record.
Forty of those slots hold a type-1 record in an official donor. This target
carries 33 of them at once. Each record keeps its type-1
layout and each code block keeps its low 16 address bits.

Four sampled rooms match the donor: `083`, `087`, `142` and `155`.

## Records

The target carries the slots `10` to `14`, `0F`, `19`, `22`, `3B`, `55`, `92`,
`A0`, `9D`, `93`, `7E`, `79`, `76`, `66`, `5D`, `4A`, `3F`, `3D`, `3C`, `38`,
`36`, `32`, `31`, `2D`, `23`, `20`, `1C`, `9B` and `9C`.

Thirty-one blocks come from `cheap-demo` and two from `mazo`.

Two further slots, `7F` and `2C`, stay open. Their blocks hold a bank-local
operand that points outside the protected block, so the review needs the
referenced data as well.

## Packs

The target mounts 35 packs: one code block for each record, the sprite 9E code
block and the graphics block. The code banks are `A4`, `A6` to `AF`, `B0` to
`B5`, `B7` to `BF` and `C0` to `C9`.

## Built target

| Item | Value |
| --- | --- |
| Target ROM | `4fd5c0b9d9d30bd46fdb6118eb86b55fe97af23bc95e771b7110d69c2b7d7ce6` |
| Binary | `BrutalMarioDemo11NativeFullSpriteGapsSNESRecomp` |

## Room result

| Room | Slots | Samples matched |
| --- | --- | ---: |
| `05D` | `3F` | 2 of 2 |
| `083` | `A0` | 1 of 1 |
| `087` | `20` | 1 of 1 |
| `08B` | `32` | 2 of 2 |
| `0BA` | `5D` | 2 of 2 |
| `0F3` | `38` | 2 of 2 |
| `142` | `3C` | 2 of 2 |
| `147` | `4A` | 2 of 2 |
| `155` | `11`, `12`, `31` | 4 of 4 |
| `15D` | `2D` | 2 of 2 |
| `160` | `23` | 2 of 2 |

Each row lists `(slot, sprite, custom, x, y)`. The first sample matches in
every room, and the later samples match where the fixture keeps the player
still.

The run reports no `BRK` and 35 module views.

## Unchanged routes

The target adds 35 packs. The tool `tools/qualify_gap_regression.py` shows that
the added packs do not change a route without a gap slot. It runs the same route
script on the baseline target and on this target. Then it compares every dump.

| Route | Equal dumps |
| --- | ---: |
| `demo11-s004-entry` | 1 of 1 |
| `demo11-sky-visuals` | 11 of 11 |
| `demo11-forest-attack` | 20 of 20 |

The tool compares the WRAM dump of each point. The dumps are byte-identical, so
the extra records and packs leave an unchanged route as it was. The report is
`local/reports/native-sprite-full-regression.json`, SHA-256
`bbf085981354d9ff722c48fd45ecd5f1c4988add65037d796a13019764a3648b`.

## Room list differences

A missing actor has two possible causes. The sprite record can be absent, or the
level sprite list can hold no placement. The tool `tools/audit_room_lists.py`
reads the sprite list of every gap room from the donor and from the recipient,
and compares the bytes.

| Result | Rooms |
| --- | ---: |
| Identical lists | 45 |
| Different lists | 4 |

The four rooms are `001`, `075`, `086` and `15E`. Room `001` holds an empty
list in the recipient: 2 bytes against 23 in the donor. A record alone cannot
spawn an actor there. The other three rooms hold different placement data.

The report is `local/reports/native-sprite-full-lists.json`, SHA-256
`028e7bb586ade29b6a18b0d4e8a8cb3963e8f7e61255b4902993a2a29ba425dd`.

## Open behaviour

Rooms `151` and `190` hold slots `9C` and `9B`. The target carries both records
and both programs start, but the donor behaviour does not follow yet.

| Room | Slot | Donor actors | Target actors | Rows equal |
| --- | --- | ---: | ---: | --- |
| `001` | `93` | 1 | 0 | no |
| `085` | `0F` | 3 | 2 | later sample differs |
| `091` | `9D` | 3 | 1 | no |
| `096` | `76` | 4 | 4 | Y differs |
| `0A2` | `36` | 2 | 1 | later sample differs |
| `0A3` | `7E` | 6 | 6 | positions differ |
| `0BB` | `66` | 6 | 6 | the donor actors move, the target actors stay |
| `110` | `0F` | 3 | 3 | one custom id differs |
| `13C` | `3D` | 1 | 1 | first sample differs |
| `14E` | `79` | 1 | 1 | Y differs |
| `151` | `9C` | 3 | 1 | no |
| `190` | `9B` | 5 | 1 | no |

Room `001` has an empty sprite list in the recipient, so the target cannot spawn
its actor. Rooms `091`, `151` and `190` spawn the first actor and then stop: the
module must create the later actors, and the target does not create them. Rooms
`0A3` and `14E` hold the same actor count with a position difference.

The two programs come from `mazo`. They hold many source-bank long calls and
inline dispatch tables. The review needs a second check before this document
can claim their behaviour.

## Reproduction

```
python3 tools/m1.py --target demo11-native-sprite-full scaffold
python3 tools/m1.py --target demo11-native-sprite-full generate
python3 tools/m1.py --target demo11-native-sprite-full build
python3 tools/m1.py --target demo11-native-sprite-full native --script recomp/inputs/room083-shared.script --capture room083-native-v1
python3 tools/qualify_sprite_full_gap.py
```

The qualification tool is `tools/qualify_sprite_full_gap.py`. Its report is
`local/reports/native-sprite-full-final.json`, SHA-256
`e5e32269ceb2306afa4bd968cab754a159181ce9de508cd2c8721265c79c9340`.

## Limits

This document claims the static review, the built target and entry parity for
four sampled rooms. It does not claim the other rooms, movement, a course pass
or a clear. The sprite graphics review stays open.

The tests are `tests/test_sprite_full.py` and pass 6/6. The full suite passes
262/262 tests. The log is `local/reports/unit-tests-rooms11.log`.