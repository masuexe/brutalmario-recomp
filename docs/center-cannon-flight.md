# Special Warp Star: cannon flight near the second Dragon Coin

The reported short flight is reproducible when directional input continues
after the cannon's forced-speed interval. Releasing left/right and retaining
B preserves the flight's horizontal momentum and reaches the opposite bank.
This distinction also occurs in unmodified cheap_demo under ZSNES 1.51.
No physics, launch-speed or timer change is justified by this comparison.

## Controlled launch

The upper cannon at `$0708,$0030` launches Mario horizontally with speed
`$60` and a `$40`-frame forced-speed interval. The existing course ASM
enforces that speed while `$7FFFAC` is nonzero. Once it expires, ordinary
air controls resume. Holding right slows Mario toward the ordinary movement
limit; releasing directional input retains the faster airborne momentum.
B changes the falling arc and permits the second DK pickup.

`recomp/inputs/star-world-center-cannon.script` uses paused map/player/camera
fixtures and small camera advances to load the actual cannon. A final
player-position fixture causes a real overlap; the guest sets the launch
speed and duration. It then holds B alone for 160 frames and waits 60.
No cannon, velocity timer, enemy, DK, completion or SRAM state is written.
Velocity is zeroed only before the collision fixture is positioned.

The tested center ROM is
`6db0bb2e6f905a04c03c4ed4b9ebd9674b4a9b5aef7ede533c8f8fc644296d92`.
Native and Snes9x captures are `center-cannon-release-native` and
`center-cannon-release-reference`. Their three relevant samples agree:

| Sample | Mario X,Y | Lives-minus-one | DK count | Action |
| --- | --- | --- | --- | --- |
| Cannon contact | `$0708,$0021` | 4 | 0 | 0 |
| Across the pit | `$0ABF,$0130` | 4 | 1 | 0 |
| Later | `$0B66,$0130` | 4 | 1 | 0 |

This qualifies the controlled cannon flight and actual DK pickup, not an
unassisted approach to the cannon or a complete center-course clear.

## Legacy comparison

The user identified ZSNES 1.51 as the original cheap_demo environment.
An isolated copy of that executable was used; its SHA-256 is
`fcc9c75f44bcfc3a5c7f1b8d8bed6b2cba95ecb80531a57351f006883b47b52e`.
The original executable's settings and saves were not edited.

Both final legacy input movies use **unmodified** cheap_demo, SHA-256
`f4a781042cf384376db60cd83fbcc9a87e110571fcd37496f978d3c70e5e0822`.
They start from the same controlled post-cannon guest WRAM/VRAM fixture in
a disposable ZST container. Its CPU/PPU/APU context comes from an existing
ZSNES vblank state; SRAM is reduced to the donor's 2 KiB size. Consequently
these are bounded cross-emulator movement diagnostics, not cold-start
legacy playthroughs. Direct process-memory samples verify the actual
controller byte during playback.

| ZSNES input after launch | Observed `$15` | Result |
| --- | --- | --- |
| B + Y + right | `$C1` | Horizontal speed decays; Mario falls and enters death action 9 |
| B alone | `$80` | Horizontal momentum persists in the air; Mario reaches the far bank, retains 4 lives-minus-one and collects the Dragon Coin |

The two movie logs contain 161 and 194 matching-input samples respectively.
Windows process samples can straddle a guest frame, so they are not
represented as exact full-frame native/reference comparisons. A separate
cold-start Snes9x donor probe reproduces the same input distinction; its
temporary entrance bypasses affect only setup, not active movement.

Local diagnostic sources and reports are under
`local/diagnostics/zsnes151/` and
`local/reports/center-cannon-zsnes151.json`. Prototypes containing an SRAM
observer were exploratory; the final legacy comparison uses the pristine
donor ROM. The primary native/reference acceptance uses fresh sessions and
imports no savestate.

The [powered-Mario damage fix](center-damage-regression.md) is separate.
Restart the center practice command to obtain that repaired executable,
then release left/right during the cannon flight and retain B for the DK
route. The center boss ending is an accepted exception: the donor's unfinished
ending is preserved as-is and no clear condition was authored.
