# Native full sprite gap target review

## Result

The recipient holds 54 custom sprite slots with the type-0 placeholder record.
Forty of those slots hold a type-1 record in an official donor. This target
carries 31 of them at once from `cheap-demo`. Each record keeps its type-1
layout and each code block keeps its low 16 address bits.

Four sampled rooms match the donor: `083`, `087`, `142` and `155`.

## Records

The target carries the slots `10` to `14`, `0F`, `19`, `22`, `3B`, `55`, `92`,
`A0`, `9D`, `93`, `7E`, `79`, `76`, `66`, `5D`, `4A`, `3F`, `3D`, `3C`, `38`,
`36`, `32`, `31`, `2D`, `23`, `20` and `1C`.

Two further slots, `7F` and `2C`, stay open. Their blocks hold a bank-local
operand that points outside the protected block, so the review needs the
referenced data as well.

## Packs

The target mounts 33 packs: one code block for each record, the sprite 9E code
block and the graphics block. The code banks are `A4`, `A6` to `AF`, `B0` to
`B5`, `B7` to `BF` and `C0` to `C7`.

## Built target

| Item | Value |
| --- | --- |
| Target ROM | `56795e4dc78b2fdc9482dd62fd0e6b2236218e7d744057e3e757a8f73b9423ff` |
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

The run reports no `BRK` and 33 module views.

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
`129cd2e4a30961517d6b5a8b6d6fb1217b3f7252c663204fad8bc35b62be7251`.

## Limits

This document claims the static review, the built target and entry parity for
four sampled rooms. It does not claim the other rooms, movement, a course pass
or a clear. The sprite graphics review stays open.

The tests are `tests/test_sprite_full.py` and pass 5/5. The full suite passes
261/261 tests. The log is `local/reports/unit-tests-full.log`.