# Forest room exit inventory

Date: 2026-10-30. Target: `demo11-native-product-r14`. This note lists the
bounded screen exits of the ten Forest rooms. It does not qualify a route, a
clear or a save.

## Method

`tools/inspect_level_exits.py` reads each Layer 1 stream inside its RATS header
bounds. It reports screen exits, five-byte exits and screen jumps. For a screen
exit the destination is the low byte plus the high bit in flag bit 0. Flag bit 1
marks a secondary exit.

`tests/test_level_exits.py` pins six live-verified boundaries. The r13 and r14
tables are identical for these rooms.

## Table

| Room | Screen exits | Notes |
| --- | --- | --- |
| `113` | none | Goal tape `(4624,144)` carries the clear |
| `111` | `11 -> 02E` | live bridge crossing accepted |
| `015` | `4 -> 044`, `2 -> 044`, `5 -> 015`, `1 -> 013` (secondary) | shack and switch accepted |
| `123` | `4 -> 042`, `0 -> 123` | lost-forest maze accepted |
| `11F` | `2 -> 039`, `3 -> 182` | both live verified |
| `114` | `17 -> 114` (secondary) | same-room reload, live verified |
| `11C` | `9 -> 041`, `10 -> 11C` (secondary) | castle entrances |
| `11B` | `11 -> 053` | hidden branch |
| `11E` | `19 -> 037` | hidden branch. The goal sprite sits below the kill boundary |
| `129` | `3 -> 03E`, `1 -> 045`, `2 -> 03F` (secondary) | hidden mansion |

Each room also holds one or more screen jumps. The table lists primary behavior
only. A live probe must confirm a secondary exit before a route uses it.

## Probe scope

A live probe starts at the first screen of the room. It can confirm only the
exit on that screen. A later screen needs an entry from its left neighbor. The
probes for 11C screen 10 and 129 screens 2 and 3 returned the first-screen
destination, so they do not confirm their own rows. Those rows stay static only.

## Live-verified additions (2026-10-30)

Assisted screen-exit fixtures confirm three more destinations on r14. Each
capture keeps mode 14, four lives and the flag at `05`. No clear or save occurs.

| Entry | Screen | Destination | Capture |
| --- | --- | --- | --- |
| `11B` | 11 | `053` | `forest-11b-exit-v1` |
| `11C` | 9 | `041` | `forest-11c-exit-v1` |
| `11E` | 19 | `037` | `forest-11e-exit-v1` |
| `129` | 1 | `045` | `forest-129-y1-v2` |
| `129` | 3 | `03E` | `forest-129-y3-v2` |

Room `129` uses vertical screens. A held Y position reaches its exits: Y `180`
gives room `045`, and Y `280` or `380` gives room `03E`. Both captures keep four
lives. The `03F` secondary row stays static only.

Room `11C` is horizontal. An X probe for screen 10 enters the pit. A Y probe
loads room `000`. Screen 10 stays static only.

Scripts are `recomp/inputs/forest-11b-screen11.script`,
`recomp/inputs/forest-11c-screen09.script` and
`recomp/inputs/forest-11e-screen19.script`.

## Product exit scan (2026-10-31)

A full scan of rooms `000..1FF` in the product finds one external exit to
`129`: room `03E` screen 1. It finds self-secondary exits for room `114`
screen 17 and room `11C` screen 10. No other room points to `114`, `11C`,
`11E` or `129`. An assisted `03E` attempt teleports the player to `(521,352)`.
The floor there is a pit, and the player falls to `y 687` without a transition.
The external neighbor fixture stays open. A later jump attempt at the same
point also fails: the player starts at `(521,352)`, a left jump falls to
`y 455`, then `y 543` and `y 1068`, and the room stays `03E`.

A vertical probe drops the player at X `120` from Y `0`. The player lands at
Y `288`, then walks right to X `354` and stops at a wall. The room stays `03E`.
The screen 1 exit needs a different route or object.

A later pipe probe on the r15 candidate places the player at X `0x40`, `0x80`
and `0xC0` near Y `0x140`, then presses Down and Up. Every sample stays in
room `129` with mode `0E`, so no pipe or door reaches screen 2 or 3.

A fresh product probe (`forest129-keyhole-v1`) enters from the actual node at
`(01B8,01B8)`. The player starts at `(96,224)`. Down input does not move. Right
input reaches `(354,720)`. Down input then does not move. Room `129` and
`$141A=0` stay unchanged, so the secondary03F exit is not a simple boundary.

A second position probe targets the live custom `78` actor at `(432,240)` and
the custom `2F` actor at `(128,448)`. The player moves to `(431,416)`, then
`(128,400)`, then falls to `(128,907)`. Room `129` and `$141A=0` stay
unchanged. The sprite IDs show a 1-Up mushroom (`78`) and a portable
springboard (`2F`), not a keyhole or key. The secondary exit therefore needs a
different object, not the key/keyhole path.

A static scan of the secondary entrance tables finds two records for room `129`:
index `0x45` with flag `58` and index `0x129` with flag `6B`. Both have the
secondary bit set. These are the next input candidates for the screen2/3 entry. The screen
bits still need decoding. A forced `$1B93=1` before translevel `45` entry does
not select a secondary start. The game still loads room `121`, and the byte is
zero at the first live sample. The route needs an actual secondary exit or pipe.

Codex decoded the r14 extended loader for the two records. Index `0x45` starts
room `129` at vertical screen `01`, X `00A0`, Y `01B0` with `1B93=0`. Index
`0x129` starts room `129` at vertical screen `0B`, X `0110`, Y `0B30` with
`1B93=3`. Neither record selects screen `2` or `3`. The full exit scan finds one
inbound secondary reference: room `045` screen 0 leads to index `0x45`, which
lands on screen `01`. Screens `2` and `3` therefore have no known normal entry.
Treat them as static-only until a custom object or new exit shows otherwise.

Room `11C` screen9 position `(2432,352)` has no floor under the player. Right
input falls to Y `584`. Right and A jumps also stay at X `2432` and fall to
`811`, then lose a life and return to the map. Screen10 needs a safe landing
platform or a different object.

A screen9 floor scan finds a solid landing at X `2302`, Y `195`. Right and A
input keeps X `2302`, then falls through Y `413` and `636`. A life is lost and
the map returns. The platform has a right wall, so screen10 needs another path.

Codex decoded secondary index `041` as room11C screen09 at X `2336`, Y `320`.
From that landing, right and A input crosses X `2560` and reaches X `2610` at
Y `267` on screen10. The next right jump falls through Y `446` and `669` into
lava. The room stays `11C` and `$141A=0`, so screen10 is reachable but its exit
is still open. Up and down input at X `2610`, Y `267` both fall to Y `442` with
no door or pipe action. The exit needs a different object or position.

A level object scan finds a door (extended object `47`) on screen9 at X `2512`,
Y `144`. The door sits left of the screen10 reach point. A position fixture at the
door and Up input enters room `41` with mode `11`, `$141A=1`, four lives and
player `(16,352)`. The screen9 door is the secondary exit boundary. Natural
reach from the landing at X `2336`, Y `320` remains to be shown. After the
load settles, room `41` shows the castle interior at mode `14`, player
`(16,352)`, with `$141A=1` and four lives. Right input from that entry moves
to Y `664`, then falls to Y `843` and costs a life. The room041 route needs a
precise entry action. Right and A input moves to X `190` on the same floor, then
X `194` at Y `326`. The next steps fall to Y `438` and `662`. A running jump reaches X `194` at
Y `347`, then falls to Y `701`. The gap needs a platform or a different action. Waiting 300 frames at the
edge costs a life. No platform arrives. Right and B input works where A failed.
Six cycles move the player to X `91`, `172`, `273` and `354` without a life loss.
The route crosses the first gap. A further jump from X `354` falls to Y `641`. The X `354` position is a
skull platform over lava. A wait costs a life, and B or right+B input still
falls to Y `470`. The route needs another action. A Y+B run-jump reaches X `307` at Y `301`, above
the skull platform. The next 60-frame press falls to Y `610`. A timed short
jump onto the brick platform is the next action. A short B press at X `307`
does not move the player. Right input falls to Y `531`. The player is stuck at
X `307`, Y `353` in that sample. The working route is to stand on the skull
raft at X `273`, Y `340`. A 120-frame wait moves the player to X `374`, and a
second wait moves to X `464`, with four lives. Two right+B presses then reach
X `506`, Y `328` and X `530`, Y `346` without a life loss. From X `464`, two
left+B presses land on the brick platform at X `358`, Y `288`. Right input to
X `374`, then two right+B jumps, reaches X `436` and X `498` at Y `284`. A third
jump reaches X `517`, Y `341`. The brick route stays alive. At X `519`, a B
jump raises the player to Y `294`. A right input then falls to Y `510`. The ON
block above this position is the next target. Y+B reaches the same Y `294`,
and the ON/OFF state at `1F27` stays zero. The switch needs a different X
position or jump. The pink ON block occupies screen X `108..182`, Y `32..184`
in the X `530` frame. Right+B from X `519` falls to Y `375`, `598` and `830`.
The switch is still not hit. At X `498`, Y `283`, A or B input moves the player
to X `518`, Y `355`. `1F27` stays zero. The X `498` position is already a
falling state, not a jump point. At X `530`, a right tap moves the player to
Y `295`, then B moves to Y `324`. The switch state `1F27` stays zero, so this
position still misses the ON block. A position fixture at X `565`, Y `355` also
leaves `1F27` zero after a B jump to Y `315`. The ON block does not react to a
head hit in these samples. Right input at X `565` moves Y to `315`, then falls
to `451` and `626` without changing X. The X `565` platform is a dead end.

The natural approach reaches X `2510`, Y `320`. A, B and Up input do not raise
the player from Y `320`. A left jump from the screen10 ledge at Y `223` also
falls to Y `446` and `669`. The ledge does not continue left. A room11C sprite scan puts one screen9
sprite at X `224`, Y `48` (ID `09`). No springboard or vine sits near the door.
The natural route needs terrain or another mechanic, not an actor. The door at Y `144` needs another mechanic or a hidden
platform. The test verifies the door boundary, but ordinary traversal remains open.
The same scan finds a second door at screen `20`, X `176`, Y `320`. That door
is far right of the tested route and stays unvisited. A position fixture at
X `5296`, Y `320` falls to Y `437` and then `773`. The second door coordinate
is not yet confirmed.
