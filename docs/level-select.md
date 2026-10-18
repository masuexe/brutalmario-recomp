# demoOnly1 map teleport and practice selector

Date: 2026-10-17. The [demoOnly1 launcher](../tools/play_demo_only1.py) supports
**any map position** through map ID and pixel coordinates, plus named shortcuts
and an interactive menu. Each destination starts a fresh practice session
with separate saves.

## Capture the real castle location

On 2026-10-18 the user confirmed that the second World 1 castle preset was
also wrong. They manually found the intended castle and reported that its
**Lemmy boss worked normally**. Correct coordinates and the room ID were not
recorded. The `world1-castle` shortcut has been removed; neither previous guess
is a verified route to this encounter.

From the project directory, start a practice session with location output:

```sh
python3 tools/play_demo_only1.py --select-level --complete-all --show-location
```

For an ordinary saved game, use `python3 tools/play_demo_only1.py --show-location`.
The optional readout appears in the **launching terminal**, not the game window.
It prints changed map coordinates and room IDs, plus a `--teleport MAP X Y`
line while on the overworld. Stop on the intended castle's map node and copy
the final teleport line. After entering, copy the `Room` value as well.
The readout samples guest memory at frame boundaries without writing to it.
It needs the rebuilt demoOnly1 executable; it does not require a debug server.

`OW` is the overworld position, retained while inside a level. `Room` is the
16-bit room ID at `$010B`; `Translevel` is `$13BF`. These level fields can
retain a previous level while on the map; they do not identify the node under
Mario until level entry. Take the map reading while Mario is stationary.
Direct binary launches can enable the same readout with `M1_SHOW_LOCATION=1`.

## Any map position

```sh
python3 tools/play_demo_only1.py --teleport 5 0x178 0x128 --air-swim
python3 tools/play_demo_only1.py --teleport 6 0x178 0x1a8
```

The arguments are **MAP X Y**. Map IDs range from 0 to 6; coordinates range
from 0 to 511 (`0x1ff`) on each axis. Decimal, `0x` hexadecimal and quoted
`'$58'` hexadecimal values are accepted. X/Y are pixel positions in the
engine's overworld coordinate space, rather than tile indices or the visible
window's coordinates. Typical node centers end in hexadecimal `8`.

The examples locate Baby Yoshi Hill on Special and the previously observed
Star World arrival position. Other coordinates are allowed
for exploration. A location on empty terrain need not contain a level entrance.
The destination is written once; the player can move normally after handoff.

To choose from a terminal menu:

```sh
python3 tools/play_demo_only1.py --select-level
python3 tools/play_demo_only1.py --select-level --air-swim
```

The menu offers Athletic Special, Baby Yoshi Hill,
the existing Athletic Special boss-door shortcut, and **Custom map position**.
Choose a number or key. Custom positions accept a line such as `0 0x18 0x1b8`;
enter `q` to cancel. Enter `c` to toggle the optional all-levels/DK completion
cheat, or pass `--complete-all`. Invalid positions are rejected before a session
is created. See [completion-cheat.md](completion-cheat.md) for its tested Warp
Star behavior and exact scope.

Other commands remain available:

```sh
python3 tools/play_demo_only1.py --list-levels
python3 tools/play_demo_only1.py --level athletic-special
python3 tools/play_demo_only1.py --level baby-yoshi-hill
python3 tools/play_demo_only1.py --boss-door --air-swim
python3 tools/play_demo_only1.py --special
python3 tools/play_demo_only1.py
```

The final command uses the ordinary saved game. The boss-door shortcut still
hands control back at the top door in `$177`; press Up to enter the arena.
Baby Yoshi Hill's opening pipe still leads to Vivian's Shop.

## Session isolation and transfer behavior

Every practice launch creates a new directory under
`local/play/demo-only-1/practice/session-*/`. It prints that directory before
launching. The directory holds the generated route, a copy of the ordinary
configuration and the session's saves/states. If the ordinary configuration
is absent, the launcher copies `recomp/m1-config.ini` instead.

The explicit session config prevents the host from anchoring its working
directory back to the executable's ordinary save directory. Existing SRAM
and savestates are not imported. ROM and binary/runtime receipts are verified
before session creation. Listing destinations and cancelling the menu create
no session. Ordinary launch paths retain their previous behavior.

Custom transfers first reach the existing fresh Special-map handoff. They
set both players' map bytes at `$1F11`, positions at `$1F17` and corresponding
grid positions at `$1F1F`, then invoke the normal fade-out mode `$0B`. The
engine runs its own map loader and fade-in, initializing the camera, tile and
level-name display for the selected position. Directly invoking loader mode
`$0C` from an idle map had inverted the fade direction, leaving a black map;
the final implementation uses the normal transition instead.

Athletic Special and Baby Yoshi Hill retain their ordinary map navigation
shortcuts. The boss-door route retains the earlier coordinate/exit shortcut
and its practice scope described in [boss-entry.md](boss-entry.md). Air swimming
retains the existing `$85` forcepoke. Transfers preserve exit destinations. Level-clear/event progress is modified
only when the optional `--complete-all` flag or menu toggle is enabled.
Demo 1-1 remains the separate primary target.

## Exploration status

Both guessed castle coordinates have been withdrawn: map 1 / `$0058,$0088`
loads `$101` (user-confirmed World 6); map 0 / `$0018,$01B8` starts loading
`$010` but is also not the intended castle. The latter node's native/reference
mode `$12` stall remains an observation of that node only. It establishes
neither an intended-castle loading bug nor original ZSNES behavior. The user's
manual Lemmy check passes as a bounded functionality report; the exact route,
clear/death coverage and practice settings were not supplied.

Milky Way Wishes and End of Special Zone have no named shortcut. On 2026-10-16,
the user confirmed that both also hang at MARIO START in the original demoOnly1.
Reference probes of those nodes likewise remain in loading mode `$12` after
extended waits. This records an original-version limitation. Arbitrary map
teleport remains available for exploring any coordinates, including those nodes.

## Validation and local evidence

The initial teleport selector passed user testing. Completion-option evidence
is recorded in [completion-cheat.md](completion-cheat.md). Historical automated
checks cover map handoff, ordinary-level entry/return and Warp Star round trips
with completion flags. Wrong-node castle probes are retained as such.

Earlier evidence under `local/captures/level-select-*` includes Athletic Special,
Baby Yoshi Hill, custom Star World coordinates and the old World 6 node. The
old castle-entry comparisons describe `$101`, not World 1. Ordinary save,
backup-save, configuration and binding hashes were preserved in real launcher
smoke runs. No full-state, whole-ROM or full Lemmy-battle fidelity is claimed.


On 2026-10-18, demoOnly1 was rebuilt with the optional `--show-location`
frame-boundary readout. All 15 launcher tests pass. A deterministic native
Baby Yoshi Hill route prints map 5 / `$0178,$0128` and then room `$126`.
With the readout enabled and disabled, both checkpoints have identical WRAM,
SRAM, VRAM, CGRAM, OAM and raw framebuffer dumps. Local evidence is under
`local/play/demo-only-1/practice/location-console-z1s61pc3/`, including
`comparison.json` and each run's `host.log`. This validates the readout on a
known route; the intended Lemmy entrance remains to be recorded.
