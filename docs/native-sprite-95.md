# Native sprite 95 module review

## Product integration update (2026-10-29)

The independent target described below was not present in product r14: its95
record was still a placeholder. The [r15 checkpoint](native-lowmirror-restoration.md)
now integrates the newest official Boss Demo program through
`config/native-content/sprite95-boss-module.json`. Its complete protected block
and record are byte-identical to7hero, which supplies the current behavior replay.
Four fresh r15 room16B samples match the selected95 actor; the r14 control lacks
it. Other actors and the other six rooms are not accepted by those samples.
The older pilot captures below retain their original identities and are not
relabelled as current-product evidence.

R15 is subsequently rejected for an actual C0 loading crash. The95 component
checks remain valid; accepted product r14 still lacks this record.

## Result

The new official donor `7hero` holds a type-1 record for custom sprite slot
`95`. The recipient places that slot in seven rooms but holds the type-0
placeholder record. This document records the review of the record, the
protected program, the dispatch table and one built target. The target now
carries the record and runs the donor program from the free bank `A3`. The
entry of six rooms matches the donor in the slot `95` rows. A course pass and a
clear stay open.

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

The plan keeps the variable name `BM_SEVEN_CODE_PACK` for the pack loader.

## Built target

The target is `demo11-native-sprite95`. Its recipe is
`config/native-content/sprite95-module.json` and its config is
`config/restorations/demo11-native-sprite95.json`. The identity line is
`tools/native_sprite_gap.py`.

| Item | Value |
| --- | --- |
| Target ROM | `1c88ac1188b5fb5eeb543931c09c51cb14f58b3340a6fd83a333e8aa682e0710` |
| Native binary | `9cb14175f313fbdbaca46d9449f85a5dde410c83ee4869d2a3f9a2152cd22aa2` |
| Install site | file offset `1608642` |
| Installed record | `013600003f0399641ae4a339e5a30000` |

The target mounts three packs. The pack variables keep the names
`BM_SEVEN_CODE_PACK`, `BM_NATIVE_SPRITE_PACK` and
`BM_NATIVE_GRAPHICS_PACK`.

## Entry result

The capture `sprite95-16b-matched-native-v1` uses the donor fixture
`type3-room16b-7hero.script`. The donor capture `type3-room16b-7hero-v1`
uses the same fixture.

| Slot | Sprite | Custom | X |
| ---: | ---: | ---: | ---: |
| 6 | `36` | `8C` | 304 |
| 7 | `33` | none | 144 |
| 8 | `33` | none | 112 |
| 9 | `36` | `95` | 16 |

The four rows hold for the donor and for the target. The run log reports
`bank=A3 resolutions=42683 executed_page_instructions=7004`, so the module view
runs.

## Six-room entry table

The table holds the slot `95` actors at the first sample. Each row lists
`(slot, sprite, custom, x)`.

| Room | Donor | Target | Rows equal |
| --- | --- | --- | --- |
| `16B` | `(9,36,95,16)` | `(9,36,95,16)` | yes |
| `16C` | `(8,36,95,175)`, `(9,36,95,112)` | `(8,36,95,172)`, `(9,36,95,112)` | no, 3 px |
| `16D` | `(8,36,95,80)`, `(9,36,95,16)` | `(8,36,95,80)`, `(9,36,95,16)` | yes |
| `16F` | `(9,36,95,16)` | `(9,36,95,16)` | yes |
| `172` | `(6,36,95,192)`, `(7,36,95,64)` | `(6,36,95,192)`, `(7,36,95,64)` | yes |
| `1CC` | `(9,36,95,48)` | `(9,36,95,48)` | yes |

The captures use `sprite95-<room>-donor-v1` and `sprite95-<room>-native-v1`.
The room 16C slot 95 actor starts at mode 0x13 on sample frame 152. It enters
mode 0x14 six frames later than the donor. Both actors start moving from X 191
at the first frame that is 0x14. The actor speed equals negative 0.5 pixels per
frame in both hosts. The six-frame gap times the pixel-per-frame rate predicts
the 3-pixel offset exactly.

Two rooms hold differences in other custom slots. Room `16D` places custom
`34`, whose recipient record points at a different program from the `7hero`
record. Room `172` places standard sprite `00`, whose X differs by five pixels
at the first sample. The review does not cover those slots.

## Walk result

The capture pair `sprite95-16b-walk-donor-v1` and
`sprite95-16b-walk-native-v1` uses one fixture with the entry position poke.

| Sample | Mode | Room | Player X |
| ---: | ---: | ---: | ---: |
| `w0` | `0x14` | `16B` | 16 |
| `w1` | `0x14` | `16B` | 94 |
| `w2` | `0x0B` | `16B` | 94 |
| `w3` to `w8` | `0x0E` | `16B` | 13 |

Both hosts hold the same triple at all nine samples. An earlier pair of
captures reported that the donor reached room `0x16E`. That fixture omitted the
entry position poke, so the two hosts entered different room states. With the
identical fixture the walk behavior matches.

## Reproduction

```
python3 tools/prepare_sprite_module.py
python3 -m unittest tests.test_sprite_module -v
```

The recipe is `config/native-content/sprite95-module.json`. The donor manifest
is `config/7hero-donor.json`. The module receipt is
`local/native-modules/sprite95-v1/preparation-receipt.json`, SHA-256
`2453be33f3d128707e71b79ae416bde4cdb362deea57ed73425e49377dbdb486`. The tests
are `tests/test_sprite_module.py` and pass 5/5.

The qualification tool is `tools/qualify_sprite_gap.py`. Its report is
`local/reports/native-sprite95-final.json`, SHA-256
`b58379ae20656d73849488f1d13a94b29426ff31fba95728af0582585f8e1e01`. The tool
checks the ROM and binary identities, the installed record, the module receipt,
the six-room slot `95` rows and the nine walk states. The suite passes
207/207 tests, and the log is `local/reports/unit-tests-sprite95-parity.log`.

```
python3 tools/m1.py --target demo11-native-sprite95 scaffold
python3 tools/m1.py --target demo11-native-sprite95 generate
python3 tools/m1.py --target demo11-native-sprite95 build
python3 tools/m1.py --target demo11-native-sprite95 native --script recomp/inputs/type3-room16b-7hero.script --capture sprite95-16b-matched-native-v1
python3 tools/qualify_sprite_gap.py
```
