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
The external neighbor fixture stays open.
