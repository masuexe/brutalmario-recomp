# Native mazo 9B entry and module view

## Result

The target `demo11-native-mazo-9b` descends from `demo11-native-sprite9e`. It
installs the official mazo 9B record and runs the protected program from an
immutable A2 view. The recipient already supplies the room 190 level data and
the sprite list. This target needs no graphics pack.

The checkpoint qualifies these items:

- The room 190 entry in mode `14`.
- The three persistent 9B parts in slots `6`, `7` and `9`.
- The persistent part positions at the donor values.
- The settled state at `fight600`.
- The map return in mode `0E`.
- 830 byte-identical regression comparisons.

## Adaptation

The record install changes one 16-byte sprite table slot. The recipient slot
holds the type-0 placeholder `0000ffffffffffff218001218001ffff`. The installed
record is `012800003fa39944bdefa2efefa20000`. The init and main banks change
from `1E` to `A2`. The file offset is `0x188C22`.

The protected program starts at file offset `0xF6FAE`. That offset maps to
`1E:EFAE`. The program is 3,399 bytes. Its SHA-256 is
`1668041b55de0a639ebc37d7742b0a378d22d005a1e6eecadccb95278d4b61af`. The
module needs no call patch. The audit finds no source-bank long reference. All
61 absolute operands stay inside the block. The module calls 11 outside shared
helpers.

The recipe is `config/native-content/mazo-9b-module.json`. The target mounts
three packs:

| Pack | Bank | Address | Size |
| --- | --- | ---: | ---: |
| `mazo-9b-code.bin` | `A2` | `A2EFAE` | 3,399 |
| `sprite9e.bin` | `A5` | `A595CD` | 1,291 |
| `star1-ffd.bin` | `B6` | `B68008` | 3,001 |

The pack starts at bank offset `0x6FAE`. The runtime checks that the pack ends
inside the bank window. The record init and main addresses resolve inside the
pack.

## Verification

The donor capture is `local/captures/mazo-9b-entry-v2-donor`. It uses the mazo
ROM SHA-256
`94092a0fdbf9d92e8f638b7defba41b7c93e70ea0ea56d976a032e6eac6b73e1` and the
tracked script `recomp/inputs/mazo-9b-donor-fixture.script`. The native capture
is `local/captures/mazo-9b-entry-v3-native`. It uses the tracked script
`recomp/inputs/mazo-9b-native-fixture.script`.

Both hosts enter room 190 in mode `14`. At `fight150` the three persistent
parts have the same positions: slot `6` at `(96,208)`, slot `7` at
`(120,120)` and slot `9` at `(128,8)`. At `fight600` both hosts hold
exactly those three parts at those positions. At `fight1200` both hosts return
to mode `0E`.

The A2 view reports 17,534,396 resolutions and 2,738,710 executed page
instructions. The runtime rejects no pack.

The room 190 script also spawns transient 9B actors in slots `0` to `5`. Both
hosts spawn them in the same order. Their positions and their sample timing
differ. The report records 58 sample and slot observations of this difference.
The module calls the shared helper `01:ACF9` at seven sites. The report does not
claim that the helper causes the difference.

Seven unchanged native routes compare against fresh parent captures. The parent
is `demo11-native-sprite9e`. The routes are Star 1 entry, the Boss route, the
sprite `9E` lift route and custom `6A` rooms `0D8`, `0E2`, `0E3` and
`0E4`. The comparison has 830 byte-identical files.

The module receipt is
`local/native-modules/demo11-native-mazo-9b-final/preparation-receipt.json`,
SHA-256 `a7a754466dc63057fbc9b00f23f398e0b2368dd390341a04c7cb62728c0485d9`.
The target ROM SHA-256 is
`8ab6bd4f5cbfe149aeeb759818ff2eab4d8b6102da698ab86ef1a5e1d375b244`.
The native binary SHA-256 is
`06d034b69915219829bdadee63de24c01401e72aa0e8ae92bf76364ff539d0fd`.
The generated header SHA-256 is
`a5825cd9fd782f02ad0c493a199491fcf68fb0647006bcff30294997caae10c1`.
The qualification report is `local/reports/native-mazo-9b-final.json`,
SHA-256 `4e666d89ff1be8e42413c388ad704f163573bb41186cdd56921f3dc3f5558963`.
An independent rerun reproduces this report byte for byte.

The module tests pass 8/8. The full suite passes 184/184 tests. The log is
`local/reports/unit-tests-mazo-fork.log`.

## Room 190 Mode7 rendering check

The donor frame `mazo-9b-entry-v1-donor/fight180` shows the sunset Mode7
scene, the flying ship and the green and red sphere. The current product r14
renders the same scene in `mazo-9b-r14-check-v1/fight180`. The earlier module
target `demo11-native-mazo-9b` lacks the `1E5` Mode7 background patch and shows
vertical stripe garbage in `mazo-9b-entry-v1-native/fight180`. The layer 1
pointer `5BB3DA` and the five sampled header tables are equal for both hosts.
The fault belongs to that older module target, not the current product. A room
190 traversal check must use r14 or a later target that keeps the `1E5` patch.
The assisted entry still dies at `(32,-72)` on the old target.

Room 190 is an interactive Mode7 field on r14. The translevel `0B4` entry
capture `mazo-190-tl-v1` keeps mode `14` and room `190`. The player world
position stays at `(32,-64)`, but directional input moves the field. In
`mazo-190-ship-v1`, right input moves the sphere to the right edge. Up input
moves it to the top right, and a long left input empties the view. The four
flying actors and the green and red sphere therefore move through a camera
scroll, not through `$94`. The sphere touch route stays open. The next check
traces the scroll and the vehicle actor, not the player coordinate.

Actor slot 7 is the green and red sphere. Directional input moves that slot:
up changes `y 120` to `8`, left changes `x 120` to `8`, and right changes `x`
to `136`. Slot 9 stays at `(128,8)`. In `mazo-190-exact-v1`, slot 7 reaches
`(128,8)` and overlaps slot 9, but the room and mode do not change. In
`mazo-190-shiphit-v1`, slot 7 also overlaps moving ship slot 5 without a room
change. The room layer 1 stream holds only a 13-byte header, and the layer 2
pointer is the empty sentinel `FFDE54` on both hosts. Room 190 is a special
Mode7 scene, not a tile level. The target object and the transition condition
stay open. The official donor capture `mazo-9b-entry-v2-donor` shows the same
persistent parts at `fight150` and `fight600` and also returns to mode `0E` at
`fight1200`. The direct entry therefore matches the official source window. No
clear or boss transition appears on either host in that window.

Course context differs. The official donor room 190 holds `$13BF=30`, the 10C
course, while the direct native translevel `0B4` entry holds `$13BF=B4`. The
native pipe fixture holds `$13BF=6A`. A forced `$13BF=30` on the direct entry
(`mazo-190-ctx-v1`) gives the same map-return window, so the identity does not
trigger the room change. The 10C course context and the internal room change
stay open.

A map-entry test changed the word at file offsets `961B8` and `20E1B8` for
translevel `030` from `010C` to `0190` in the reference host. The map 6
override still loaded room `10C`. The two matched tables are not the loader for
this entry, so the map node swap needs a different table. The `0EF600` table
holds three-byte pointers, and its first `0x100` entries hold no `10C` or `190`
level word. That table is not a direct level-number map for this node either.

The Super Mario World overworld format gives the cause. The original game does
not store translevels in a table. It assigns them as level tiles appear in the
Layer 1 data. A Lunar Magic edit keeps the high byte in the Layer 1 tile row. A map node swap therefore needs an edit of that level tile or its order,
not a translevel index patch. The next step finds the Layer 1 tile position of
the node and changes its level value. A map capture at the practice position holds
`30` at `7ED000+1F0`. A forced `B4` there changes that byte, but the later A press
enters room `005`. The poked map position is not the level tile, and the
practice `D7E2` override is a separate path.

The 9B program has no `STA 010B`, `STA 010C` or `STA 13BF` write and no
immediate `190` or `1BE`. In `mazo-190-buttons-v1`, slot 7 sits at `(128,8)`
and A, B and Start input leave the room and mode unchanged. The room acts as a
closed Mode7 cutscene on both hosts.

A long hold repeats the check in `mazo-190-long-v1`. Room `190` stays in mode
`14` for about 960 frames, then changes to mode `0D`, then mode `0E` with room
`190`. Lives drop from `4` to `3`. The room is a timed cutscene that returns to
the map and is not a softlock.

The user supplied a map screenshot for the node. The `10C` tile sits at map
tiles X `20..21`, Y `1D..1F`, and its green label is `30`. Map table reads at
`(Y*32+X)` for those tiles return zero in captured submaps 2 to 5. The submap
identity is still needed before a Layer 1 tile edit. Product map frames at ids
`0`, `2`, `3`, `4`, `5` and `6` show an island, a cave mine, a fire castle, a
bridge castle, an ice field and Star Road. None matches the annotated
screenshot, so the screenshot is probably an editor view or a different submap.

The room 10C top actor is custom sprite `64` at `(144,64)`. Its record points to
bank `3E` code at `3E859F` and `3E85C5`. A bounded scan of that code finds no
immediate room `190` constant and no `19B8`, `19D8` or `13BF` write. A player
placement on the actor leaves the room and mode unchanged. The 10C to 190 event
is not a direct path in this sprite code.

## Limits

The entry window ends at the first map return. It does not prove attack damage,
a fight clear, an ending, a save state or completion writes. The
[attack-window check](native-mazo-attack-window.md) records the transient intro
actor difference. The transient intro
actor behavior stays open. The `B0` corridor recovery stays separate because it
conflicts with the ForestStar `B0` actor. The runtime keeps the variable name
`BM_SEVEN_CODE_PACK` for compatibility with the existing pack loader.

## Reproduction

```
python3 tools/prepare_mazo_module.py
python3 -c "import sys; sys.path.insert(0, 'tools'); import native_seven; native_seven.prepare('demo11-native-mazo-9b')"
python3 tools/m1.py --target demo11-native-mazo-9b scaffold
python3 tools/m1.py --target demo11-native-mazo-9b generate
python3 tools/m1.py --target demo11-native-mazo-9b build
python3 tools/m1.py --target demo11-native-mazo-9b native --script recomp/inputs/mazo-9b-native-fixture.script --capture YOUR_FRESH_ENTRY_NAME
python3 tools/qualify_mazo_9b.py --prefix YOUR_FRESH_PREFIX --parent-prefix YOUR_PARENT_PREFIX --output local/reports/YOUR_FRESH_REPORT.json
```

For the parent regressions, run each tracked regression script with
`--target demo11-native-sprite9e` and with
`--target demo11-native-mazo-9b`. Use fresh capture names for both. The
qualifier checks both capture receipts and then compares every dump file.
