# Native Seven Koopalings ending boundary

## Cumulative integration update (2026-10-29)

The [Seven product integration](native-seven-product-integration.md) discovers
that this qualified feature was missing from the cumulative candidate. It now
carries the pinned newest Boss controller/resources and child into an isolated
current descendant, with fresh source actor, font, ending and life-award checks.
Earlier evidence below retains its exact identities and bounded acceptance;
no earned complete victory or saved clear is inferred from ending fixtures.

## Result and acceptance

The user chose to keep the official Boss Demo T-shaped test room as the ending.
The user stated that a life loss requires a rightward walk to the pit. Waiting in
the room does not lose a life. The current native target is
`demo11-native-seven-ending-1up`. It descends from the earlier ending targets.
The recipient's room `174` stays unchanged. The ending uses reserved room
`17B`.

The current checkpoint qualifies these items:

- The injected defeat boundary.
- The original ending-room layout.
- The ordinary rightward pit death and the one-life loss.
- The map return and the English font restoration.
- The hidden 1-up checkpoints in the test room.

The hidden checkpoints spawn a real green mushroom in both hosts. The mushroom
awards one life at the same sample index in both hosts. The pit death then
consumes that life. A separate assisted combat route reaches joined-part tiers
`0` through `6` with actual attacks. Neither route proves an earned fight
victory. No check writes completion flags.

## Adaptations

Four isolated descendants keep all earlier targets and receipts.

1. `demo11-native-seven-ending-stop` changes the mapped master program's
   defeat music immediate at `A2:8384` from `FF` to `80`. The official Boss
   instruction at `22:8383` is `LDA #$FF; STA $1DFB`. The modern driver treats
   `FF` as a custom-song upload request. That request stalled in both hosts.
   The modern `80` command stops music without an upload. A CPU boundary test
   covers the actual dispatch. The ROM and the four other packs stay unchanged.
2. `demo11-native-seven-ending-test` changes the room `0FF` screen exit from
   `174` to `17B`. It also changes the room `17B` background pointer from
   `FFD900` to `FFDE54`. Three ROM bytes change. The existing `17B` template
   already has the official Boss `174` layout, an empty sprite stream, the
   secondary headers, the graphics selection and the palette selection. The
   master font wrapper also queues English font restoration for player action
   `06` (the ending pipe transfer). It already did so for action `09`
   (death). The expanded wrapper fits its allocation and four empty bytes.
3. `demo11-native-seven-ending-tiles` supplies a room-local FG2 graphics clone
   as unused ExGFX `FFC` at immutable `A6:EA7D`. The official Boss blanks the
   graphics definitions of Map16 `6F` and `70`. The recipient keeps pole
   graphics there. The clone blanks only their eight 8x8 character patterns
   (`A4` to `A7` and `B4` to `B7`) in recipient GFX `17`. Room `17B`
   alone selects it. Shared Map16 definitions, helpers, layout IDs and
   collisions stay unchanged. The record selects `15,19,FFC,14,02,13,01,00`.
   The bounded literal LC_LZ2 stream adds 4,105 bytes to the A6 pack. The pack
   stays in the same 32 KiB bank.
4. `demo11-native-seven-ending-1up` restores the hidden checkpoint processing
   in room `17B`. The recipient returns early at `$00:F294`. The official code
   compares the checkpoint index with `$1421`. It then continues at
   `$00:F2A8` or stops. The target replaces five recipient bytes with
   `JML $A2:F100` and a NOP. A 37-byte shim checks room `17B` and the high
   room byte. It saves A and P. Outside room `17B` it returns and the recipient
   early return stays. Inside room `17B` it continues at `$00:F299` or
   `$00:F2A8`. The fourth ordered checkpoint calls the retained shared spawn
   helper. That helper creates sprite `78`, not a direct life increment.

The room and graphics namespace checks stay as recorded. They walk all 512
foreground object streams, the secondary entrances and the decoded current
overworld level map. No prior incoming exit or map assignment selects `17B`.
No current room selects `FFC`.

Pinned official data:

| Data | Identity |
| --- | --- |
| Boss `174` foreground | `6AF93A`, 99 bytes, SHA-256 `bd97f2ae808e6acb8349b2189ae463be9f546e6758cfeb80c3fa45b83a787c9a` |
| Recipient `17B` foreground | `068000`, identical 99 bytes |
| Boss empty sprite stream | `6AF9A5`, `00FF`. Recipient `07E76D` is identical. |
| Hills background | `0CDE54`, 261-byte LC_RLE1, SHA-256 `a2f736af63defb21fd267926e4cf476647f374a3e7357b6744a5c41c40f02143` |
| Boss blank Map16 definitions | `0D8378`, 16 bytes, `F810` repeated eight times |

## Verification boundaries

The tracked `seven-ending-{native,donor}-fixture.script` inputs label the map
and pipe entry fixtures, the temporary damage protection and the injected final
tier and damage threshold. The fixture disables protection before the test-room
walk. The script then uses ordinary Right inputs. It does not teleport Mario to
the pit.

Both images enter their T rooms at `(16,352)`. Ten successive rightward samples
match coordinates. They end at `(744,456)` with player action `09`. That is a
real pit death. Both hosts then return to map mode `0E` with one fewer life than
at the start of death. Native VRAM contains the retained recipient's 2,048-byte
English font in the test room and after the map return.

The mushroom captures use the tracked
`seven-ending-mushroom-{donor,native}.script` inputs. That script adds a
rightward walk with single-frame dumps. Both hosts first show sprite `78` in
state `8` at sample `17`. Both hosts first show the extra life at sample
`28`. The donor life count moves from 19 to 20 and back to 19. The native life
count moves from 4 to 5 and back to 4. The map return therefore spends the
awarded life. Both hosts spawn the sprite at slot 11 with X `0x0260` and Y
`0x0160` from the same fixture.

Sprite `78` has a different property byte in each image. The value comes from
the image sprite database at `$07F4C7` plus the sprite id. The official Boss
image stores `C2` and the recipient stores `D2` at `$167A` slot 11. The
native host keeps the recipient value. The boundary test pins both values and
normalizes only that reviewed byte before the comparison.

The ending-route music cues agree by meaning. The fight request is donor `0x23`
(legacy) and native `AC`. Both hosts hold `$0DDA = 0x02` in the ending rooms
and `0xFF` on the pit death. The child program's `$1EC7CD` request `0x1E`
maps to the modern stop/transition special case. No sampled cue shows a version
mismatch.

Neither host writes saved progress across the ending path. Saved level status,
overworld events, switches, the completion counter, DK bits, midway masks and
`$7FEBE` stay unchanged from the fight to the map return. Ten level-status
bytes differ between the images before the fight. They are version-local
starting progress, not ending writes. The report records this check. Standard
save completion is therefore not a missing write in this path. An earned defeat
is still not proven.

A newer assisted probe reaches tier 6 with two remaining parts. A 20-sample
attack-type sweep leaves both damage fields unchanged. The base part sits below
the forced player point, so the Up attacks pass above it. See the
[fight analysis](native-seven-fight-analysis.md).

The loaded foreground tilemap matches the official room after normalization of
the reviewed eight blank pole subtiles (two loaded copies). All eleven character
patterns selected by the source foreground match. The adapted pole patterns are
zero pixels. The foreground Map16 IDs and collision planes also match. This is
not whole-frame equality. HUD and font, background animation phase and map
context are version-specific.

The assisted combat input generator `tools/seven_fight_route.py` uses 400
cycles of ordinary Up+B and Up+A attacks with explicit temporary immunity. It
never writes boss HP, damage totals, phase or completion state. Both hosts
sample all seven joined-part tiers. Their unseeded timings and accumulated damage
differ. This is progression evidence, not synchronized fight parity. The user
stated that the design intends random defensive learning and attack-specific
immunity. See [the learning check](native-seven-learning.md).

Seven unchanged native routes compare all WRAM, VRAM, palette, OAM, SRAM,
framebuffer and event register dumps against their pinned historical controls.
The routes are Star 1 entry, the existing Boss route, the sprite `9E` lift route
and recipient custom `6A` rooms `0D8`, `0E2`, `0E3` and `0E4`. There are
830 byte-identical file comparisons. Their practice, map and entry fixtures keep
their original scope.

Unit coverage includes the actual modern music dispatch and the exact recipe
changes. It also rejects unreviewed patches and reproduces the T-room output.
It covers bounded graphics decoding, the hidden checkpoint continuation and
spawn, and the real font wrapper, scheduler and DMA for player actions `0` to
`9`. Only actions `6` and `9` queue English font restoration. The final unit
suite passes 176/176 tests. The log is
`local/reports/unit-tests-seven-ending-1up-final.log`.

## Identities and evidence

| Item | SHA-256 |
| --- | --- |
| Official Boss ROM | `337fe036f943dafb0df70bdb556e588b785c58ff019b1b00c08f77743e2b3ccd` |
| Final native ROM, 4 MiB | `941f2d0c7ac3ac7ba955d26590778a665e23af1d9cdbbb546d80ec065d0e8a64` |
| Final native binary | `97bf3a9cd2ddf195da5d6a42d345eae9ccfd1686a81bb9affe387fca1ad58ca8` |
| A2 master, 28,965 bytes | `e9061413696935c854f3c20cac6b8fb6e1ae00886d56cb9bdf23629cb2f6c9de` |
| A6 graphics, 31,366 bytes | `43cecea3a2201336d135466e5bb160a91115fd8b6c95223fd1b01ab95cbf7cf7` |

The target inherits the A5 sprite pack (1,291 bytes), the B6 Star 1 graphics
pack (3,001 bytes) and the 9E child pack (3,385 bytes) unchanged. The receipt
is `local/restoration/demo11-native-seven-ending-1up/input-manifest.json`,
SHA-256 `e71264bb8c0e71a4b795683c44b132358d2b53a3a8f04e101e9bb89a182337a6`.
The qualification report is
`local/reports/native-seven-ending-1up-final.json`, SHA-256
`f2759fec2d948af87c8a3724d2d2de25d7c916c94772f21abfcb0a50d4c1db98`.
An independent qualifier rerun reproduces this report byte-for-byte. The earlier
tiles checkpoint report `native-seven-ending-final.json` stays unchanged.

Final evidence locations:

- `local/captures/seven-ending-1up-v1-native`: final native ending and pit.
- `local/captures/seven-ending-visuals-v1-donor`: official Boss ending and pit.
  The qualifier rechecks the source capture script, ROM, frontend and core.
- `local/captures/seven-ending-mushroom-v1-{donor,native}`: hidden 1-up
  checkpoints, spawn, pickup and map return.
- `local/captures/seven-ending-1up-phases-v1-native` and
  `seven-ending-test-phases-v1-donor`: assisted real-damage phase routes.
- `local/captures/seven-ending-1up-v1-{star1,boss,lifts,0d8,0e2,0e3,0e4}`:
  final native regression captures.

Rejected experiments stay under ignored local storage. The
`seven-ending-visuals-*` native trial used a room-conditional shared helper
hook. Extra guest instructions changed frame timing outside the ending room.
Review rejected the trial despite correct local pixels and CPU scope checks. The
`seven-ending-gfx-*` trial used the wrong bypass slot order. Review also
rejected it. Neither is the delivery target. The archive of their original
configs, builders and registration snapshots is at
`local/probes/seven-fight-completion/rejected-{visuals,gfx-order}/`. Their
captures and receipts stay intact. No failed evidence got a new label.

## Remaining work and reproduction

An earned final-tier defeat remains unproven. A manual play attempt on
2026-10-27 showed a playable build. The user could not defeat the boss and
reported no defect. The target restores the hidden checkpoints only
in room `17B`. Other rooms keep the recipient early return. Death timing still
uses the retained recipient timer (`30` versus `2E`), and the two hosts return
to different map contexts. The child's `$1EC7CD` request and other cues were
not observed to change the music outside the mapped `AC` request.

```
python3 tools/native_seven_ending.py
python3 tools/native_seven_ending_test.py
python3 tools/native_seven_ending_tiles.py
python3 tools/native_seven_ending_1up.py
python3 tools/m1.py --target demo11-native-seven-ending-1up scaffold
python3 tools/m1.py --target demo11-native-seven-ending-1up generate
python3 tools/m1.py --target demo11-native-seven-ending-1up build
python3 -m unittest discover -s tests -p test_seven_ending_1up.py -v
python3 tools/qualify_seven_ending.py --target demo11-native-seven-ending-1up --ending seven-ending-1up-v1 --native-phases seven-ending-1up-phases-v1-native --regression seven-ending-1up-v1 --mushroom seven-ending-mushroom-v1-native --mushroom-donor seven-ending-mushroom-v1-donor --output local/reports/YOUR_FRESH_REPORT.json
```

Skip scaffolding an existing experiment. Preparation refuses to overwrite a
receipt or input with different bytes. For fresh evidence, choose fresh capture
names. Run the tracked ending and mushroom scripts on their respective hosts.
Then pass those names to the qualifier. This checkpoint does not promote the
frozen accepted comparison line and does not change user saves.
