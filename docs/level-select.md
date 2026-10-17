# demoOnly1 map teleport and practice selector

Date: 2026-10-17. The [demoOnly1 launcher](../tools/play_demo_only1.py) supports
**any map position** through map ID and pixel coordinates, plus named shortcuts
and an interactive menu. Each destination starts a fresh practice session
with separate saves. The World 1 castle preset is available for investigating
Larry without first unlocking its map path.

## World 1 castle

From the project directory:

```sh
python3 tools/play_demo_only1.py --level world1-castle
```

With the existing air-swimming practice option:

```sh
python3 tools/play_demo_only1.py --level world1-castle --air-swim
```

The corrected preset hands control back at **map 0, X=`$0018`, Y=`$01B8`**,
the lower-left castle beside the user's animated-skull landmark. Use the normal
level-entry button. This starts loading `$010`, but currently stalls at MARIO
START in both native and Snes9x reference runs, even without completion flags.
Larry has not been reached; original ZSNES behavior remains unknown.

The previous map 1 / `$0058,$0088` preset was misidentified and was confirmed by
the user to enter a World 6 level. Its earlier `$101` entry/return results do
not qualify World 1 or Larry. See [completion-cheat.md](completion-cheat.md)
for the correction and investigation status.

## Any map position

```sh
python3 tools/play_demo_only1.py --teleport 0 0x18 0x1b8
python3 tools/play_demo_only1.py --teleport 5 0x178 0x128 --air-swim
python3 tools/play_demo_only1.py --teleport 6 0x178 0x1a8
```

The arguments are **MAP X Y**. Map IDs range from 0 to 6; coordinates range
from 0 to 511 (`0x1ff`) on each axis. Decimal, `0x` hexadecimal and quoted
`'$58'` hexadecimal values are accepted. X/Y are pixel positions in the
engine's overworld coordinate space, rather than tile indices or the visible
window's coordinates. Typical node centers end in hexadecimal `8`.

The examples locate the World 1 castle, Baby Yoshi Hill on Special, and the
previously observed Star World arrival position. Other coordinates are allowed
for exploration. A location on empty terrain need not contain a level entrance.
The destination is written once; the player can move normally after handoff.

To choose from a terminal menu:

```sh
python3 tools/play_demo_only1.py --select-level
python3 tools/play_demo_only1.py --select-level --air-swim
```

The menu offers Athletic Special, Baby Yoshi Hill, World 1 castle (loading investigation),
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

The corrected World 1 castle preset is available for loading investigation.
It selects `$010` but stalls in mode `$12` in native and reference runs. The
previous `$101` node was a World 6 location and retains its separate garbled
interior observation. Neither result verifies Larry or an original-version
castle hang.
Milky Way Wishes and End of Special Zone have no named shortcut. On 2026-10-16,
the user confirmed that both also hang at MARIO START in the original demoOnly1.
Reference probes of those nodes likewise remain in loading mode `$12` after
extended waits. This records an original-version limitation. Arbitrary map
teleport remains available for exploring any coordinates, including those nodes.

## Validation and local evidence

The initial teleport selector passed user testing. The user identified the
incorrect castle label; the corrected coordinates and completion option are
recorded in [completion-cheat.md](completion-cheat.md). The complete suite now
passes 41 tests. Native and reference checks cover map handoff, ordinary-level
entry/return, Warp Star round trips with completion flags, and the corrected
castle's unresolved loading stall.

Earlier evidence under `local/captures/level-select-*` includes Athletic Special,
Baby Yoshi Hill, custom Star World coordinates and the old World 6 node. The
old castle-entry comparisons describe `$101`, not World 1. Ordinary save,
backup-save, configuration and binding hashes were preserved in real launcher
smoke runs. No full-state, whole-ROM or Larry-battle acceptance is claimed.
