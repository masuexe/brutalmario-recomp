# Native modern sprite integration, slots 99 and A1

Date: 2026-10-30. Parent: `demo11-native-sprite-product-v1`, ROM
`1daaa9411b633fb066b2b94a8970a4f12057b391819ff90b775b89b511b4ab11`.
Candidate: `demo11-native-modern-sprites-v1`, ROM
`bae32d5dc0e02d95d86e856e0ec83264f8be0bdb57796564722ccf7a71e824e6`,
binary `4a6d4530c547f0b6fd04ce9bd5fcc3ef584b6904d3cac92753f2a26f0210682a`.

## Result

This checkpoint installs the two official demoOnly1 programs for sprite slots
`99` and `A1` into the cumulative product. It records the static review, the
build and the first native activation pilots. It does not claim behavior
parity.

The placement census in [the reconciliation report](native-sprite-product-reconciliation.md)
lists ten placeholder slots: `96`, `97`, `99`, `A1`, `A5`, `A6`, `E8`,
`E9`, `EA` and `F5`. This checkpoint covers two of them.

## Selection and records

The source is the pinned official demoOnly1 ROM
`b8d86f894f6c07aeb74794c59adab8f336080285b4781a3e1c921615a2d8216b`, from
`config/demo-only-1-donor.json`. The two recipient slots hold the type-0
placeholder before the change.

| Slot | Source rooms | Record, source to native | Code bytes | Source address | Native address |
| --- | --- | --- | ---: | --- | --- |
| `99` | `174`, `175`, `176` | `01368004e1a23d450ba7134ea7130000` to `01368004e1a23d450ba78b4ea78b0000` | 1,391 | `13A6FC` | `8BA6FC` |
| `A1` | `175`, `176`, `178` | `013600863587b944f688303489300000` to `013600863587b944f6888a34898a0000` | 5,724 | `3088EB` | `8A88EB` |

The two record changes move only the two bank bytes. The code keeps the source
low 16-bit addresses and the low WRAM and I/O mirrors. The adapted payloads are
`4513edf0...d194c9` (`99`) and `c90d5186...c7571f` (`A1`).

## Static review

`tools/prepare_modern_sprite_modules.py` decodes the source programs and
checks each branch and each relocation.

| Item | Slot `99` | Slot `A1` |
| --- | ---: | ---: |
| Local entry states | 14 | 74 |
| Instruction variants | 655 | 2,096 |
| Short dispatch tables | none | 2, eight entries each |
| Source-bank relocations | none | 52 |
| External calls | 5 | 14 |

Every absolute operand, call target and dispatch target stays inside the
program. The review pins the two explicit `DB07` preludes at `13AA4B` and
`13AA51`. It also checks the recipient drawing helper at `28FD6D` and keeps
its two reviewed data-table changes.

Six negative tests reject a wrong parent, a widened `DB07` exception, a
missing relocation, an opcode change, a ninth dispatch target and an
incompatible mirror mapping.

## Cumulative scope

| Item | Parent | Candidate |
| --- | ---: | ---: |
| Recipes | 43 | 44 |
| Mounted packs | 54 | 56 |
| Record and extra patches | 61 | 62 |

The candidate adds one recipe, one A1 pack and one A1 record patch. All 54
parent mappings, the Seven feature, the mazo modules, the type-3 records and
the A2 module stay unchanged. The full unit suite passes 384 tests.

## Runtime activation pilots

The pilots use explicit primary-room, pipe, immunity and player-position
fixtures. They write no actor, HP, switch, progression, completion or save
value. The capture inputs are under `local/captures/modern-pilot-*/input.script`.

| Pilot | Parent | Candidate |
| --- | --- | --- |
| Room `174` | no `99` actor | three `99` actors, X `0/256/257`, Y `256`, status `08` |
| Room `175` | no `99` or `A1` actor | three `99` actors and one `A1` actor |
| Room `176` | no `99` or `A1` actor | one `A1` actor, no `99` actor |
| Room `178` | no `A1` actor | one `A1` actor |

Two checks bound this evidence. All actor positions stay fixed, and the source
entry did not reach the room in the same-profile runs. The source captures hold
only the title, files, intro and node samples. The pilots therefore show
activation, not motion, child generation or behavior parity.

## Limits

- Behavior, motion, child generation and layout parity are open.
- Room `176` shows no `99` actor in the pilot. The fixture may not reach its
  screen. This is open.
- Graphics, audio and a complete room pass are not checked.
- Eight placeholder slots remain: `96`, `97`, `A5`, `A6`, `E8`, `E9`, `EA`
  and `F5`. The project pins the official `ow` donor in `config/ow-donor.json`
  for the slot `97` review. This checkpoint does not use it.
- This checkpoint does not claim whole-game acceptance or product promotion.
  The accepted product stays `demo11-native-product-r14`.

## Next actions

1. Obtain a source-side entry for rooms `174`, `175`, `176` and `178` and
   compare actor rows and motion against the candidate.
2. Review slot `97` against the pinned `ow` donor with the same static
   discipline.
3. Review the remaining slots `96`, `A5`, `A6`, `E8`, `E9`, `EA` and
   `F5` before any install.

## Reproduction

```sh
python3 tools/prepare_modern_sprite_modules.py
python3 tools/m1.py --target demo11-native-modern-sprites-v1 scaffold
python3 tools/m1.py --target demo11-native-modern-sprites-v1 generate
python3 tools/m1.py --target demo11-native-modern-sprites-v1 build
python3 -m unittest tests.test_modern_sprite_modules -v
```

The review record is
`local/restoration/demo11-native-modern-sprites-v1/modern-sprite-review.json`.
