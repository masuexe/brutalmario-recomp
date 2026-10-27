# Native full sprite gap target review

## Result

The recipient holds 54 custom sprite slots with the type-0 placeholder record.
Forty of those slots hold a type-1 record in an official donor. This target
carries 35 of them at once. Each record keeps its type-1
layout and each code block keeps its low 16 address bits.

Four sampled rooms match the donor: `083`, `087`, `142` and `155`.

## Records

The target carries the slots `10` to `14`, `0F`, `19`, `22`, `3B`, `55`, `92`,
`A0`, `9D`, `93`, `7E`, `79`, `76`, `66`, `5D`, `4A`, `3F`, `3D`, `3C`, `38`,
`36`, `32`, `31`, `2D`, `23`, `20`, `1C`, `9B`, `9C`, `2C` and `7F`.

Thirty-one blocks come from `cheap-demo` and two from `mazo`.

Slot `2C` writes to one address in the module bank. A write to ROM has no
effect, so the recipe records that operand in `ignored_operands` and needs no
data.

Slot `7F` reads two bytes with `LDA $BEA8,X` and `LDA $BEA9,X`, where
`X = $1933 * 2`. The index stayed `0` in the donor capture of room `0A5`, so
the code reads one 16-bit table entry.

The recipe now holds a `data_appendix` of 128 bytes from `24:BEA8`. The pack
grows to 1,641 bytes and the two operands point to the appendix at `A8DA`.
The target runs the module: `bank=B4 resolutions=81489` in room `0A5`. The two
persistent actors match the donor in both samples. The donor creates one more
actor in the later sample.

The instruction `PEA $804C` is not a data address. It passes the custom sprite
id `0x4C` to the SpriteTool spawn entry `00:C0FB` with the flag `0x8000`. The
analyzer no longer treats a `PEA` or `PER` operand as an address.

## Packs

The target mounts 37 packs: one code block for each record, the sprite 9E code
block and the graphics block. The code banks are `A4`, `A6` to `AF`, `B0` to
`B5`, `B7` to `BF`, `C0` to `C9` and `C4`.

## Built target

| Item | Value |
| --- | --- |
| Target ROM | `78c4647d9d47026d7fd3316c2efda31bb3ec71d7d21e951274b9acb658414cc0` |
| Binary | `BrutalMarioDemo11NativeFullSpriteGapsSNESRecomp` |

## Room result

| Room | Slots | Samples matched |
| --- | --- | ---: |
| `00D` | `92` | 2 of 2 |
| `05D` | `3F` | 2 of 2 |
| `083` | `A0` | 1 of 1 |
| `087` | `20` | 1 of 1 |
| `08B` | `32` | 2 of 2 |
| `0AF` | `55` | 2 of 2 |
| `142` | `3C` | 2 of 2 |
| `147` | `4A` | 2 of 2 |
| `155` | `11`, `12`, `31` | 4 of 4 |
| `15D` | `2D` | 2 of 2 |
| `160` | `23` | 2 of 2 |

Each row lists `(slot, sprite, custom, x, y)`. The first sample matches in
every room, and the later samples match where the fixture keeps the player
still.

The run reports no `BRK` and 37 module views.

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
the extra records and packs leave an unchanged route as it was. Each point
records the hash of both dumps. The report is
`local/reports/native-sprite-full-regression.json`, SHA-256
`4c0f8d59ecf304f85be7b5d318134cc8607457992f402aebb85c483e1e86559b`.

## Frozen rooms

Six rooms freeze at the room entry on the native target. The game mode holds
`0x12` and the frame counter `$13` and `$14` stops. The donor reaches mode
`0x14` and its frame counter keeps counting. The actors stand still in both
captures, so an actor compare there does not measure the module.

A control run shows the cause. The tool `tools/qualify_emu_freeze.py` runs the
same entry script on the reference emulator with the unmodified Demo 1-1 ROM.
Every one of the five tested rooms freezes there in the same way.

| Room | Mode | Frame counter | Frozen |
| --- | --- | ---: | --- |
| `085` | `0x12` | 62981 | yes |
| `0A2` | `0x12` | 62981 | yes |
| `0BA` | `0x12` | 62981 | yes |
| `0BB` | `0x12` | 62981 | yes |
| `0F3` | `0x12` | 62981 | yes |

The teleport fixture therefore causes the freeze. The native runtime and the
gap records are not the cause. A map-based entry is necessary to qualify these
rooms. The report is `local/reports/native-sprite-emu-freeze.json`, SHA-256
`18edf8719d7f90fbd5fcfbce5cc684554a34317f59104918bfa737ede603b134`.

| Room | Donor mode | Target mode | Target frame at `r1` | at `r2` |
| --- | --- | ---: | ---: | ---: |
| `085` | `0x14` | `0x12` | 63492 | 63492 |
| `091` | `0x14` | `0x12` | 63492 | 63492 |
| `0A2` | `0x14` | `0x12` | 63492 | 63492 |
| `0BA` | `0x14` | `0x12` | 63492 | 63492 |
| `0BB` | `0x14` | `0x12` | 63492 | 63492 |
| `0F3` | `0x14` | `0x12` | 63492 | 63492 |

| Room | Donor mode | Target mode |
| --- | --- | ---: |
| `085` | `0x14` | `0x12` |
| `091` | `0x14` | `0x12` |
| `0A2` | `0x14` | `0x12` |
| `0BA` | `0x14` | `0x12` |
| `0BB` | `0x14` | `0x12` |
| `0F3` | `0x14` | `0x12` |

Entry sweep: for rooms `085`, `0A2`, `0BA`, `0BB` and `0F3`, only `19d8 04`
loads the intended room, and that value freezes the runtime. The values `00`,
`01`, `02` and `05` load room `<room>+0x100` at mode `0x14`.

A manual write of `$0DAE = 0x0F` does not end the freeze, so the palette fade
counter is not the cause.

The baseline target `demo11-native-sprite9e` shows the same stall in rooms
`085` and `0BB`. The gap records therefore do not cause the stall. In room
`0BB` both hosts hold the same actor rows from frames 200 to 240 in mode
`0x12`. The donor then moves, and the target does not.

The qualification tool now rejects a room as exact when the target stays below
mode `0x13`. This rule removed rooms `0BA` and `0F3` from an earlier claim.

Room `0A5` runs a long capture. Both hosts create and remove the third actor in
the same repeating pattern, at a 20-frame offset.

A one-frame capture over one spawn cycle gives the exact offset. A shift of 29
frames aligns 29 of the 32 comparable dumps. The three remaining frames are
`489` to `491`, where the target capture has no data yet. Room `0A5` is
therefore phase-exact.

The same method gives these results.

| Room | Offset | Equal dumps | Residual frames | Result |
| --- | ---: | ---: | --- | --- |
| `091` | -28 | 53 of 53 | none | phase-exact |
| `0A2` | -26 | 55 of 55 | none | phase-exact |
| `0B5` | -29 | 41 of 52 | 189 to 198 | phase-exact outside the load window |
| `190` | 18 | 58 of 63 | 199 to 203 | a 5-frame delay in the setup |
| `151` | -1 | 69 of 80 | 230 to 240 | the target never creates the second actor |

Rooms `091`, `0A2` and `0B5` are phase-exact. Their records and modules work.

Room `190` matches after the setup delay. It still differs in one way: the
donor holds three actors at frame 229 and the target holds one. The target
never creates the two extra actors in the captured window, so room `190` stays
open.

Room `151` matches in every frame before the donor creates a second actor at
frame 230. The target never creates it, so the child step is the only open item
in that room.

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

## Jump review

An earlier review tracked `JSR` and self-bank `JSL` targets. It did not track a
`JMP` that leaves the block. The analyzer now stops at a bank-local `JMP` or
`JSR` target outside the block unless the recipe declares that site in
`external_entries`.

Slot `7F` tail-jumps with `JMP $C0FB` in long mode to `00:C0FB`. The donor and
the recipient hold the same 16 bytes at that address, so both hosts call the
same code. A scan of all 35 recipes finds no undeclared jump.

## Slot 9B branch

The slot `9B` main reads `$1504` and branches on the value: `1` runs one
routine, `2` runs another, and any other value runs a third. The donor holds
`$1504 = 2` and the target holds `$1504 = 0` in room `190`.

A forced write of `$1504 = 2` keeps the value, does not create the missing
actors, and makes the target set `$C2 = 1`. The branch value is therefore not
the only cause.
## Open behaviour

Rooms `151` and `190` hold slots `9C` and `9B`. The target carries both records
and both programs start, but the donor behaviour does not follow yet.

| Room | Slot | Donor actors | Target actors | Rows equal |
| --- | --- | ---: | ---: | --- |
| `001` | `93` | 1 | 0 | no |
| `096` | `76` | 4 | 4 | Y differs |
| `0B5` | `55` | 2 | 2 | phase-exact outside the load window |
| `0B6` | `55` | 4 | 4 | one actor Y differs in the later sample |
| `05B` | `2C` | 2 | 1 | the target actor holds X 16 and Y 0 |
| `0A5` | `7F` | 3 | 3 | phase-exact at a 29-frame offset |
| `162` | `92` | 1 | 1 | start X differs by 49 |
| `164` | `92` | 1 | 1 | start X differs by 164 |
| `0A3` | `7E` | 6 | 6 | positions differ |
| `110` | `0F` | 3 | 3 | one custom id differs |
| `13C` | `3D` | 1 | 1 | first sample differs |
| `14E` | `79` | 1 | 1 | Y differs |
| `151` | `9C` | 2 | 1 | the target never creates the second actor |
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
`1a04206364c2cdbf53fb8abefa7aa743f011dff4ee42fe8059d82a9c938d929e`.

## Limits

This document claims the static review, the built target and entry parity for
four sampled rooms. It does not claim the other rooms, movement, a course pass
or a clear. The sprite graphics review stays open.

The tests are `tests/test_sprite_full.py` and pass 12/12. The full suite passes
268/268 tests. The log is `local/reports/unit-tests-phase4.log`.