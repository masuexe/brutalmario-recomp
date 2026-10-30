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
| Room `174` | no `99` actor | one `99` actor, X `130`, Y `320`, status `08` |
| Room `175` | no `99` or `A1` actor | three `99` actors, X `143/207/290`, Y `338/306/287`, and one `A1` actor at X `64`, Y `256` |
| Room `176` | no `99` or `A1` actor | one `A1` actor, X `64` to `369`, no `99` actor |
| Room `178` | no `A1` actor | one `A1` actor, X `320`, Y `271` to `146` to `271` |

## Source comparison

The project retains the official demoOnly1 entries as captures
`modern-source-{174,175,176,178}-v1`. The fixture uses the same forced exit
destination and translevel `4A`. `tools/compare_modern_sprite_sources.py`
pairs each native actor with the nearest source actor and classifies each
sample.

| Case | Samples | Result |
| --- | ---: | --- |
| `174/99` | 8 | Near match. Status and velocities equal. Constant offset `(2,4)`. Static on both hosts. |
| `175/99` | 8 | Near match. Status and velocities equal. Offset at most `(11,3)`. Static on both hosts. |
| `175/A1` | 8 | The source moves from `(16,304)` to `(64,256)` in the first 32 frames. Native starts at the settled point. Both hosts agree from frame 32. |
| `176/A1` | 8 | Both hosts move on the same trajectory. Native leads by one or two samples and agrees exactly at frame 256. The native actor ends before frame 512. |
| `178/A1` | 8 | Exact at all eight samples, including the move `Y 271` to `146` and back. |

The `A1` program runs its actual motion and matches the official program in
room `178`. The `99` actors stay static on both hosts, and their small
offsets need a layout check. Child generation, graphics and full rooms remain
open.

## Slot 97 candidate

Target `demo11-native-modern-sprites-v2` descends from v1 and installs the
official `ow` slot `97` record and its 453-byte protected program at
`8CA52A`. The ROM is
`e431d5aa168a4a07b63fca7aa4f7ca9fba08333a3b521a8c5f59553c8be2c2c4`.
The binary is
`ddb06004447d28b3122028f970979524a3d94f484ac359f092a63b1806b2e3e9`.

| Item | Value |
| --- | --- |
| Record | `013600b73503994439a5104ba5100000` to `013600b73503994439a58c4ba58c0000` |
| Code | 453 bytes at `8CA52A`, SHA `b1f39a342a0e42eff47844f1f1b48f29fa4dfcddda5d1bc513a3e903897b92fc` |
| External call | `01B7B3`, 16 bytes identical in `ow` and the recipient |
| Code patches | none |
| Rooms | `1EF` |

Room `1EF` places slot `97` once at `(192,240)` in both images. The
256-byte layout window and the full sprite list are byte-identical. Two rooms
carry screen exits whose high-bit destination byte resolves to level `1EF`:
room `108` (a World 8 course) and room `1EF` itself.

The native pilot loads room `1EF` with one slot `97` actor at `(192,368)`,
status `08`, static across 512 frames. The v1 parent loads the same fixture
with no slot `97` actor.

The documentation describes the `ow` donor as overworld-only with no course
data. Source entry attempts in `ow` did not reach the room. Runtime source parity, motion
and child behaviour stay open.

## Limits

- This checkpoint bounds behavior: `A1` motion matches the source in `178` and follows the source trajectory in `176`. `99` stays static with small offsets. Child generation, graphics and full rooms are open.
- Room `176` shows no `99` actor in the pilot. The fixture may not reach its
  screen. This is open.
- Graphics, audio and a complete room pass are not checked.
- Seven placeholder slots remain: `96`, `A5`, `A6`, `E8`, `E9`, `EA` and
  `F5`. Slot `97` now has a v2 candidate with static and activation evidence.
- This checkpoint does not claim whole-game acceptance or product promotion.
  The accepted product stays `demo11-native-product-r14`.

## Next actions

1. Check the `99` position offsets against the two room layouts.
2. Reach room `1EF` from the room `108` screen exit in the native target and
   record the real route.
3. Review the remaining slots `96`, `A5`, `A6`, `E8`, `E9`, `EA` and
   `F5` before any install.

## Reproduction

```sh
python3 tools/prepare_modern_sprite_modules.py
python3 tools/m1.py --target demo11-native-modern-sprites-v1 scaffold
python3 tools/m1.py --target demo11-native-modern-sprites-v1 generate
python3 tools/m1.py --target demo11-native-modern-sprites-v1 build
python3 -m unittest tests.test_modern_sprite_modules -v

python3 tools/prepare_sprite_module.py \
  --recipe $PWD/config/native-content/sprite97-modern-module.json \
  --output-dir $PWD/local/native-modules/sprite97-modern-v1
python3 -c "import sys; sys.path.insert(0, 'tools'); import native_sprite_gap; native_sprite_gap.prepare('demo11-native-modern-sprites-v2')"
python3 tools/m1.py --target demo11-native-modern-sprites-v2 scaffold
python3 tools/m1.py --target demo11-native-modern-sprites-v2 generate
python3 tools/m1.py --target demo11-native-modern-sprites-v2 build
python3 -m unittest tests.test_modern_sprite_97 -v
```

The review records are
`local/restoration/demo11-native-modern-sprites-v1/modern-sprite-review.json`
and `local/restoration/demo11-native-modern-sprites-v2/input-manifest.json`.
