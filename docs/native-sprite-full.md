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
| `083` | `A0` | 1 of 1 |
| `087` | `20` | 1 of 1 |
| `142` | `3C` | 2 of 2 |
| `155` | `11`, `12`, `31` | 4 of 4 |

Each row lists `(slot, sprite, custom, x, y)`. The first sample matches in
every room, and the later samples match where the fixture keeps the player
still.

The run reports no `BRK` and 35 module views.

## Open behaviour

Rooms `151` and `190` hold slots `9C` and `9B`. The target carries both records
and both programs start, but the donor behaviour does not follow yet.

| Room | Slot | Donor actors | Target actors | Rows equal |
| --- | --- | ---: | ---: | --- |
| `151` | `9C` | 3 | 1 | no |
| `190` | `9B` | 5 | 1 | no |

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
`9784f32eec785fe68ff4c55eaacaf26104c3066832ea1cbb968b3c778c3cff6a`.

## Limits

This document claims the static review, the built target and entry parity for
four sampled rooms. It does not claim the other rooms, movement, a course pass
or a clear. The sprite graphics review stays open.

The tests are `tests/test_sprite_full.py` and pass 5/5. The full suite passes
261/261 tests. The log is `local/reports/unit-tests-full2.log`.