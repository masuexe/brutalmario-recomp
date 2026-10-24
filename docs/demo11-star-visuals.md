# Demo 1-1 Star World visual recoveries

Date: 2026-10-24. The user accepted the lower-inner cap-expiry/music correction,
then reported the lower-left secret room's colors, missing sky fuel gauge and
right-hand flame corner, and missing Snow Star Santa.

Current automatically qualified cumulative target: `demo11-star-visuals-flame`.
ROM SHA-256:
`9f4add87fc2fe4efe2ebc96bc4509853f082656bb418c6ba26c170ef8f2768d1`.
Native binary SHA-256:
`4fdb2fd360458e7095bf33e20294dd87178d0dd3a088f1a4cdc1d1fe476effa9`.
The accepted cap-music parent remains intact. These visual repairs have new
bounded automated evidence; they do not imply a new user acceptance.

```sh
# Sky Star, including the fuel gauge and complete flame:
python3 tools/play_demo_only1.py --restoration demo11-star-visuals-flame --show-location
# Lower-left course, whose screen-09 pipe enters the secret room:
python3 tools/play_demo_only1.py --restoration demo11-star-visuals-flame --level star-world-1 --show-location
# Snow Star, including its slot-game Santa reward:
python3 tools/play_demo_only1.py --restoration demo11-star-visuals-flame --level star-world-lower-right --show-location
```

Each command creates an isolated practice save. Existing ROMs, builds, game
processes, user saves and captures remain intact.

## Secret-room colors: different artwork, unchanged palette

Room `$054`'s custom palette pointer, all 514 source bytes, and the loaded
palette buffer already match the qualified demoOnly1 predecessor. Its selected
ExGFX `$B2` does **not** match: Demo 1-1 supplies different artwork under that
number, producing the darker appearance despite identical colors in palette RAM.

The resource recipe copies cheap_demo's 3,052-byte stream at `$56:BE42`, decoding
to 4,096 bytes with SHA-256
`dfc3cf5a4867d28aaa21929dd7e9c92da9c7b5777771f1b234364bedfa57937b`.
That image equals the previously qualified demoOnly1 artwork. A private RATS
block at `$3E:9000` and unused ID `$FF8` serve only room `$054`; its graphics
word at `$14:B78C` changes from `$00B2` to `$0FF8`. The shared `$B2` resource,
palette, room layout, sprites, collisions and exits remain intact.

The builder now resolves the verified small ExGFX table at `$0F:F600` as well
as the existing large table. Its standard-file resolver is bounded to `$00..$31`;
unsupported source IDs are rejected. A focused regression test covers the
source-table formats and unsupported IDs. Destination allocation and room-use
guards remain unchanged.

## Fuel gauge: scoped guest-side NMI upload

The rocket already fills `$7F:FFE0..FFEF` with the FUEL label and fuel cells,
and decrements fuel during real flight. Demo 1-1's status-bar upload routine
at `$10:8294` omits the custom row that demoOnly1 uploads. Populating the RAM
buffer alone therefore leaves the gauge absent.

A 69-byte RATS-protected shim at `$3E:A008` first calls the original recipient
routine unchanged, then uploads those sixteen cells to VRAM word `$5028` only
when room `$009` is actively playing (mode `$14`). It preserves A/P around its
checks and uses the same DMA register sequence as the earlier display path.
The NMI call at `$00:8DE1` points to this shim. Other rooms retain the recipient
upload path; the donor's global status-bar behavior is not transplanted.

Both hosts show real fuel decreasing from 11 to 10, with the visible tilemap
cells equal to the updated guest buffer. The normal flight/door/tape route
also clears through `$09B`, saves `$09=$8C` in both SRAM copies and retains it
after console reset/File A reload on both hosts.

## Flame corner: source OAM gap, not a missing graphics stream

The user clarified that the **right corner** of the flame was missing. The
source renderer draws fourteen body tiles and advances Y to the next free OAM
entry. Four redundant `INY` instructions then skip one entry before the two
flame tiles. Its existing finalizer marks only sixteen entries as 16×16; the
second flame falls outside that range and retains an 8×8 size flag.

The baseline reproduces this exactly: its visible flame entries at `$0394/$0398`
have size flags `2/0`. Replacing only the four `INY` bytes at `$38:B5E0` with
`NOP`s places them at `$0390/$0394`, both with size flag `2`. Fourteen body
tiles plus two flame tiles now fit the existing sixteen-entry finalization.
Sixteen consecutive samples on both hosts exercise both `$8C/$AC` and
`$8E/$AE` animation pairs, with both pieces consistently 16×16.

This is an explicit correction of a bug in the supplied rocket drawing code,
which was also present in the earlier demoOnly1 port. No flame artwork,
physics, fuel logic or other actor branch is replaced.

## Santa: missing sprite `$09`, including the slot-game reward

Demo 1-1's `$09` custom record is the default empty record. Room `$026` places
three instances for the slot game; a real winning match uses the same code to
generate Santa, his reindeer and the delivered reward. The missing record
prevents that entire chain from running.

The resource recipe ports cheap_demo's pinned 2,654-byte block from `$14:F25C`
to checked empty `$37:F25C`, keeping its low address. Record `$31:8302` receives
the donor fields with both entry banks adapted. The 512-room dependency scan
finds this slot only in room `$026`; shared routines and version-specific
constructor bytes are pinned. Layouts, placements and slot results are retained.

Both hosts perform actual timed slot jumps, generate the Santa and reindeer
actors (subtypes 0 and 2 with extra bits `$8C`), and show their fly-in. The
existing secret-reward route then produces the real key/keyhole clear,
returning to the map with translevel `$08=$8B`. No slot result, spawned actor,
reward, key-carry state or completion flag is written by the fixtures.

## Recipes, verification and remaining scope

The two immutable steps are:

1. [`demo11-star-visuals`](../config/restorations/demo11-star-visuals.json),
   resource/Santa/fuel recovery, ROM
   `5e7eacb99b530707cc2e68016afb6eaede56ba0e671ca184ff48578b0ee740d6`;
2. [`demo11-star-visuals-flame`](../config/restorations/demo11-star-visuals-flame.json),
   the four-byte OAM correction and current head.

`tools/qualify_demo11_star_visuals.py` checks actual build/ROM/input/host
identities, completed logs and dump sizes. It compares loaded secret-room
palette and VRAM with the exact predecessor, verifies dynamic fuel upload,
both flame animation sizes, Santa generation and the real secret clear,
and the sky normal-clear/save/reload route. The accepted three-cap fixture is
replayed on both hosts after the NMI change: all effects expire, gameplay
continues, and native SPC RAM still contains the correct `$60` payload.

The integrated suite passes **21/21**. The ancestry-derived byte audit rebuilds
all **19** recipes: **63,942** changed bytes against Demo 1-1, all within
**86,802** declared region bytes, zero unexpected. The 33 restoration tests
and three preparation tests pass. Earlier qualifiers remain pinned to their
own frozen targets; this is not a replay of every historical route on this head.

Evidence is under `local/captures/d11-visual-*`, with exact receipts collected
in `local/reports/demo11-star-visuals.json`. Primary final-head captures:
`secret-final-ref` / `secret-native`, `fuel-{ref,native}`, `flame-{ref,native}`,
`santa-arrival-{ref,native}`, `santa-secret-{ref,native}`,
`sky-goal-{ref,native}` and `cap-regression-{ref,native}`, each prefixed
`d11-visual-`. `base-*` and `only1-*` are comparisons; `fixed-*` captures refer
to the intermediate ROM and are not presented as final-head evidence.

Scripts label their map/player shortcuts, damage immunity and pipe-action
fixture. Sky normal completion uses actual flight and tape inputs after the
map shortcut. Secret-room inspection is not a full lower-left secret clear.
Sky secret completion, all DK/death coverage and the broader restoration
remain open. The [center-route follow-up](demo11-center-route.md) now qualifies
the center-node route and special-warp-star display. No new listening
acceptance is requested.

```sh
python3 tools/restore_star_world_1.py --target demo11-star-visuals-flame
python3 tools/m1.py scaffold --target demo11-star-visuals-flame
python3 tools/m1.py generate --target demo11-star-visuals-flame
python3 tools/m1.py build --target demo11-star-visuals-flame
python3 tools/m1.py reference --target demo11-star-visuals-flame \
  --script recomp/inputs/demo11-sky-flame.script --capture fresh-flame-ref
python3 tools/m1.py native --target demo11-star-visuals-flame \
  --script recomp/inputs/demo11-sky-flame.script --capture fresh-flame-native
python3 tools/check_demo11_line.py
```
