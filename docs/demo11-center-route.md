# Demo 1-1 Star World center route and special-warp-star display

Date: 2026-10-24. The user reported a damaged route from the lower-inner node to
the center special warp star. The user also reported that the center star
display stays dark.

Current automatically qualified cumulative target: `demo11-center-route`.
ROM SHA-256:
`917eb515d4c6fd87cdb3d57be748f151773c951d952e3e847cbffb8f9756c1cf`.
Native binary SHA-256:
`21cdc0ef50f3f7398359b1c813c676896a07e794315e3459c1ba5c4bec08abf1`.
Parent: `demo11-star-visuals-flame` (`9f4add87…`).
This repair has bounded automated evidence. It does not imply a new user
acceptance.

```sh
# Starts at the lower-inner node. Walk Up onto the center node:
python3 tools/play_demo_only1.py --restoration demo11-center-route --show-location
```

The launcher creates an isolated practice save. Existing ROMs, builds, game
processes, user saves and captures stay intact.

## Defect

Demo 1-1 stores the Star World map with the center cell empty. The map16 tile at
cell `$7A7` is `$00`. The level assignment at the same cell is `$00`.
DemoOnly1 stores `$5A` and `$0A` at the same places.

The missing special-warp-star tile breaks the route. A real Up input from the
lower-inner node cannot reach the center node. The player deviates to map
position `$017C/$01D0`. A Y press then loads room `$000`.

The same cell also controls the center display. The parent head never starts the
special-warp-star display. Its sampled map interior has 16 colours and 1,891
non-black pixels.

## Repair

The recipe changes three sites and adds one private data block:

| Site | Address | Parent | Candidate |
| --- | --- | --- | --- |
| Center map16 tile | file `0x067F86`, SNES `$0C:FF86` | `$00` | `$5A` |
| Center level assignment | decoded level-map byte `$7A7` | `$00` | `$0A` |
| Level-map loader word | SNES `$04:D803` | `$BEDF` | `$C008` |
| Level-map loader bank | SNES `$04:D808` | `$10` | `$37` |

The level map comes from the compressed stream at SNES `$10:BEDF`. That stream
decodes to 4,096 bytes. The recipe edits one decoded byte and keeps every other
decoded byte. The new stream uses four literal-only LZ2 chunks of 1,024 bytes
and one terminator. This form prevents a changed byte from moving through a
backreference.

The 4,105-byte stream goes into a private `STAR` block at SNES `$37:C000`.
The block header occupies `$37:C000`..`$37:C007`. The stream starts at
`$37:C008`. The loader keeps its instruction bytes. Only its pointer operands
change.

The recipe is
[`demo11-center-route`](../config/restorations/demo11-center-route.json).
It changes 195 bytes relative to the parent; all changes are inside the
declared regions. The whole-line audit rebuilds 20 recipes: 64,137 changed
bytes against Demo 1-1, all within 90,919 declared region bytes, zero
unexpected.

## Evidence

`recomp/inputs/demo11-star-center-route.script` holds the fixture. The fixture
uses map-coordinate pokes to move the player to the lower-inner node. It then
sends a real Up input, samples the center display twice, and presses Y.

| Check | Parent control | Candidate reference | Candidate native | DemoOnly1 control |
| --- | --- | --- | --- | --- |
| Lower node start | `$0178/$01C8` | `$0178/$01C8` | `$0178/$01C8` | `$0178/$01C8` |
| Up movement Y | `$01B2` | `$01AD` | `$01AD` | `$01AD` |
| Center arrival | `$017C/$01D0` | `$0178/$01A8` | `$0178/$01A8` | `$0178/$01A8` |
| Tile under player | `$5D` | `$5A` | `$5A` | `$5A` |
| Center map cell | `00/00` | `5A/0A` | `5A/0A` | `5A/0A` |
| Entry mode | `$14` | `$14` | `$14` | `$14` |
| Entry room | `$000` | `$00A` | `$00A` | `$00A` |
| Entry translevel | `$000` | `$00A` | `$00A` | `$00A` |
| Display colours | 16 | 71 | 71 | 70 |
| Display non-black pixels | 1,891 | 9,901 | 9,901 | 9,863 |
| Animation pixels, two samples | 1,894 | 10,457 | 10,163 | 10,342 |

The candidate starts the center special-warp-star display on both hosts. The
display cycles its colours. Two samples 30 frames apart differ by about 10,000
pixels. The parent control shows only its normal HUD animation.

The demoOnly1 control uses the same fixture on the
[`star-world-forest`](../config/restorations/star-world-forest.json)
predecessor. Its route positions and map-cell bytes match the candidate. Its
loaded center-course frame is byte-identical to the candidate reference frame.
This parity shows that the center course loads with the donor entry, not with a
fabricated state.

Primary captures are `d11-center-ref`, `d11-center-native`,
`d11-center-only1-ref` and `d11-center-parent-ref` under `local/captures`.
Exact receipts and measurements are in
`local/reports/demo11-center-route.json`. The suite log is
`local/reports/demo11-center-route-line.log`.

`tools/qualify_demo11_center_route.py` checks the recipe replay, the four
changed sites, the decoded map edit, the block header, the loader pointer, the
capture identities and every value in the table above. The Demo 1-1 line suite
passes **22/22**. The 33 restoration tests and three preparation tests pass.

## Limits

- The fixture teleports to the lower-inner node. It does not replay an
  unassisted course exit or a full lower-inner clear.
- The test samples the display as two animated frames. The display colour phase
  is not compared pixel by pixel with the donor, because the phase is not a
  game state.
- The center course is the accepted unfinished Giant Starman course. This
  repair does not change its ending, and it claims no center clear, overworld
  return or saved completion result.
- Per-course traversal, DK/death coverage, the sky secret and the broader
  restoration stay open.
- The Star World map title glyphs stay wrong on this line. The parent capture
  and the accepted sky-clear overworld captures show the same text. This repair
  does not change it.

## Reproduce

```sh
python3 tools/restore_star_world_1.py --target demo11-center-route
python3 tools/m1.py scaffold --target demo11-center-route
python3 tools/m1.py generate --target demo11-center-route
python3 tools/m1.py build --target demo11-center-route
python3 tools/m1.py reference --target demo11-center-route \
  --script recomp/inputs/demo11-star-center-route.script --capture fresh-center-ref
python3 tools/m1.py native --target demo11-center-route \
  --script recomp/inputs/demo11-star-center-route.script --capture fresh-center-native
python3 tools/qualify_demo11_center_route.py
python3 tools/check_demo11_line.py
```
