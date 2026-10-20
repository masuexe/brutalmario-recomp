# Middle-right Star World: dependency isolation

Date: 2026-10-20. The accepted cumulative baseline is now
[`star-world-upper-right`](star-world-upper-right-restoration.md). The user
accepted that stage after checking entry and SMB3 bricks, explicitly waiving
a full manual run. Listening remains deferred during the silent window.

The next course is map 6, X=`$0198`, Y=`$01A8`, translevel `$09`, room
`$009`. The historical original/native survey stalls at MARIO START. This
checkpoint isolates its missing dependencies; it does not produce or accept
a new playable restoration target. The diagnostic ROMs remain under ignored
`local/probes/middle-right/` and do not replace accepted builds or saves.

## Independent missing dependencies

The original graphics selection at `$14:AE28` matches cheap_demo's room
record. It selects ExGFX `$190` and `$193`, whose recipient pointers are both
`$FFFFFF`. The donor provides valid 4,096-byte decoded streams:

| ID | Donor source | Compressed bytes | Diagnostic destination ID |
| --- | --- | ---: | --- |
| `$190` | `$34:844A` | 1,298 | `$FFA` |
| `$193` | `$34:BF08` | 1,569 | `$FF9` |

The graphics-only diagnostic uses the existing checked builder, pins both
streams, checks the destination IDs against all room selections and preserves
the layout/sprite/exit data. New RATS blocks occupy physical
`$1E7000..$1E7B43` (exclusive end). Only room `$009`'s selection words at
record offsets 4 and 10 change; the global missing graphics slots stay empty.

The stalled recipient requests BGM `$2E`; its bank/high/low pointer at
`$0F:E08A` is zero. For diagnosis only, two copies point that slot at the
already restored `$5D` stream, `$3C:E008`. This is an explicit temporary
song substitution, not the final soundtrack repair. No music driver, physics,
enemy, completion or exit code is changed.

All three fresh reference runs use
[`star-world-middle-right-survey.script`](../recomp/inputs/star-world-middle-right-survey.script).
The script transfers an uncleared disposable save to the node, captures mode
`$12` before initialization finishes, and samples after 180 and another 420
guest-frame calls. It does not poke progress, enemy or physics state. Separate
echo compatibility is enabled and invalid-VRAM blocking is disabled, as in
the earlier restoration probes.

| Diagnostic | Mode at both later samples | Low Map16 bytes changed from loading sample | Conclusion |
| --- | --- | ---: | --- |
| Graphics only | `$12` | 0 | Graphics imports alone do not resolve the loading stall. |
| Substitute music only | `$14`, room `$009` | 4,863 | Bypassing the missing stream resolves loading, but missing graphics still corrupt the loaded terrain buffer. |
| Graphics plus substitute music | `$14`, room `$009` | 0 | Both independent entry dependencies are isolated; no buffer corruption in these samples. |

All samples retain the initial four extra lives. Visual inspection confirms
vertical stripes in the music-only run and restored dotted surfaces in the
combined run. This qualifies sampled entry data only; it does not establish
that the entire course, every sprite, exit or secret works.

## Evidence and next implementation boundary

Twenty-five selected local assertions pass, including input/ROM receipt
identities, bounded completion, sampled states, Map16 comparisons and an
audit allowing only reviewed pointer/selection/RATS changes. Evidence is in
`local/reports/middle-right-investigation.json`; captures are
`middle-right-graphics-only`, `middle-right-music-substitute` and
`middle-right-combined-substitute`.

| Diagnostic | ROM SHA-256 |
| --- | --- |
| Graphics only | `05f53d20d6ba23107e63ca93ed5d2190a8dde7e9e70041c259cb0823e684a334` |
| Substitute music only | `92e7eade1a4bc6f7d244b7edcef34a87cb8b2985274fcd174624539532456a08` |
| Combined | `8116dff03d2fd06612c284cdc552abf530320763f64d69e8eb93f1ffa1346297` |

The accepted base remains
`c96a9f5c5abd01e7749c493f615c8a398365dba2ed9076a33523e3b35ec56c0a`.
No runtime, native build or accepted ROM changes in this investigation. Only
documentation and the bounded survey input are committed; the existing 108
project-test result belongs to the unchanged preceding code checkpoint.

Next, locate and verify the actual donor `$2E` upload and adapt its sequence
and command graph. The current song adapter supports the reviewed single
pattern loops used by `$54/$5D`; a candidate donor group for `$2E` has distinct
intro/loop patterns and needs further verification rather than assuming the
old recipe applies. Then audit sprite dependencies, qualify actual exits,
collectibles, saving and death in both native/reference hosts, and run earlier
route regressions. The temporary `$5D` substitution must not ship as a
restoration. No new user playthrough or listening request is needed for this
diagnostic checkpoint.

## In-progress candidate after the diagnostic

The uncommitted `star-world-middle-right` recipe now uses the real `$2E`
intro/loop upload, ExGFX `$190/$193`, and custom sprites `$17` and `$28`.
It is not an accepted restoration. The native scaffold still matches the
previous ROM and must be recreated before a native run or launcher build.

Room `$009`'s loaded screen-exit table has one destination: screen index 2,
value `$049B`. The exit handler uses only bit 0 of the high byte as the level
high bit, so the destination level is `$09B`. That room's graphics header is
byte-identical and had the same two missing IDs. The recipe pins both room
headers onto `$FFA/$FF9`. Rooms `$097` and `$098` still select the empty
`$190` slot plus other missing IDs; they are not this exit and stay unchanged.

Reference samples after the pin:

| Check | Result |
| --- | --- |
| Room `$009` entry | Active, rocket slot `$28` alive, low Map16 unchanged from layout through graphics and later movement. |
| Screen-2 loader into `$09B` | Reaches room `$09B` with low Map16 unchanged across layout, graphics and the later sample. Goal-tape sprite `$7B` is active. This poke sets the sublevel flag and pipe action; it is not a ridden-rocket clear. |
| Visual samples | Room `$009` shows the fuel gauge and vertical shaft. Room `$09B` shows the goal tape, mushroom and dotted floor without the earlier striped object. A later rocket sample shows Mario riding the star. |

Pause-relocating Mario onto the five `$002D/$002E` tiles does not qualify DK
collection. The rocket overrides that position. Listening stays deferred.

## Ridden climb, not a free walk

Sprite `$28` in translevel `$09` is the rocket. While its fuel counter
`$1594` is nonzero it climbs, copies Mario's X, and holds Mario one pixel
higher each frame. Left and right change Mario's X by one pixel per frame.
Fuel starts at `$0B` and drops once every 256 frames. At zero the rocket
falls. The screen-2 exit `$049B` is selected from Mario's Y high byte, so it
is only reachable at Y high `$02`. The rocket's own height check uses that
same band, but it only changes the rocket mode; it does not load `$09B`.

A straight climb at the spawn X hits a ceiling near Y `$0BB0`. Reference
runs that steer around the bars reach about Y `$03D0` with fuel still left:

| Steer after entry | Result |
| --- | --- |
| Hold right or stay at X `$50`–`$B2` | Stuck near Y `$0BB0`. |
| Left to X `$2D`–`$40` | Passes that bar, then sticks near Y `$08D0`. |
| From X `$30`, slide right to about X `$B9` before Y `$0900` | Passes `$08D0`, then sticks near Y `$06D0`. |
| Slide left through that bar to about X `$3F` | Passes `$06D0` and the later bars, then sticks near Y `$03D0`. |
| Slide to X `$E2` at that height | Also stops near Y `$03D0`. |

No Map16 tile is stored at that stop. The
[Sky Star page](https://brutalmario.fandom.com/wiki/Sky_Star) describes this
course: ride the starship upward, dodge walls, and collect fuel blocks.
There is no boss. The normal goal is the screen-2 exit `$049B` (room `$09B`).
A clean left-page climb still stops near Y `$03D0`, short of Y high `$02`,
so that exit is not reached by the routes above.

## Secret fuel and the right-hand page

The rocket's second height check is the secret case: X high `$01` and rocket
Y below `$0450`. The wiki's secret is the same idea. Exhaust the fuel on a
wall, fall, and the plus sprite `$17` at X `$0100`, Y `$0F90` refills
`$1594` to `$0B`. Reference traces show that refill while Mario's Y is
`$0F75`. Eleven fuel units then allow 2,816 frames of one-pixel climb, which
ends at Mario Y `$0475`. The secret check needs Mario below `$0470`, so a
perfect climb from this block is still a few pixels short unless another
plus is collected on the way.

Zigzag reference climbs on the right page, after that refill, do get past
several ceilings:

| Held direction | Clears | Then stops |
| --- | --- | --- |
| Right from X `$0102` | up to about Y `$0DA0` at X `$01D2` | that column |
| Left before Y `$0DA0` | through it, down to about Y `$0B0A` at X `$011D` | the next bar |
| Right again | through Y `$0B80`, down to about Y `$0A02` at X `$01D2` | Y `$08E0` |
| Left, then a short right | through Y `$08E0` to X `$0192`, Y `$08B9` | Y `$07E0` if X stays `$0192` |

Continuing the same zigzag gets through the later bars as well. The best
measured secret sample is a coast at X `$016D`: Mario climbs from Y `$0631`
with fuel 2 to Y `$0541` while the last unit is almost spent. Rocket Y there
is `$0522`, still above the `$0450` secret check. Two more plus sprites are
visible from that corridor, at X `$0050` / Y `$0640` and X `$0090` / Y `$0510`,
but the left side of the corridor is walled at X `$012D`. Moving left to reach
either plus stalls and spends the remaining fuel. A perfect no-hit climb from
the bottom refill alone still ends a few pixels short of the check, and every
real route hits at least one bar. No secret clear is qualified. The normal
exit's save is recorded below.

A later pass removed the long stall on the first right-page crossing. Holding
right for 520 frames after the fall, then left, climbs the X `$012D` wall
with fuel still 9 at Y `$0CFB`. Turning right there before Y `$0C70` reaches
the right edge with no stall samples and fuel 8. The same early-turn pattern
gets to X `$01AD`, Y `$064B`, fuel 2. Stopping in that column bonks
immediately; the open step is only while still moving right. Fuel is then
gone by about Y `$05A0`. The left page at X `$0040` climbs cleanly, with no
wall-hit flag, until the bar at Y `$08D0` (fuel 8 at Y `$096E`). Moving
right of about X `$0060` hits an earlier wall near Y `$0950`.

## Ridden normal exit

Treating the rocket's ceiling check and Mario's own body tiles as solid
finds a left-page line that stays inside the initial 2,816 climb frames.
`recomp/inputs/star-world-middle-right-goal.script` flies that line from the
entrance. It uses the same map shortcut as the entry script and no star
invulnerability. The rocket's finish flag `$C2` becomes 1 at Mario
X `$005A`, Y `$02B0`, still in room `$009`. Walking right along that
platform reaches the door near X `$0142`: action `$71` becomes 5 and the
screen exit loads room `$09B` at X `$0040`, Y `$0120`.

In `$09B`, running right collects the mushroom and stops on the colored
blocks at X `$00F2`. One rightward jump lands at X `$012A`. Continuing right
touches goal-tape sprite `$7B`. The goal timer `$1493` runs, `$13CE` becomes
1, and the guest returns to the overworld in mode `$0E`. Translevel `$09`'s
flag `$1EA2` and both SRAM copies change from `$0C` to `$8C`. Reset, File A
load, and the restored overworld position keep `$8C`.

This is a reference clear of the normal exit only. DK coins, the secret
height check, a death return, and the native build are still unqualified.
The launcher still rejects this ROM until the scaffold is recreated.
