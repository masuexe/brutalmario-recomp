# Room 173 custom sprite: the wrong program

## Result

Room `173` places sprite slot `07`. Mario falls with no support and the level
ends. The product image runs an older program for slot `07`.

## Evidence

The room data is the same in both images.

| Item | product r26 | `boss` |
| --- | --- | --- |
| Room `173` level pointer | `68D398` | `68D398` |
| Level block SHA-256 | `9585952b9e745ea2` | `9585952b9e745ea2` |
| Level header | `15 0A 00 40 30 40 70 F2` | same |

The programs differ.

| Image | Slot `07` block | Size |
| --- | --- | --- |
| product r26 | `3D:F556` | 1647 bytes |
| `boss` | `20:94D1` | 5836 bytes |

The product program is the `cheap-demo` one. `cheap-demo` places slot `07` in
room `080` only. Every newer image places it in rooms `080` and `173`.

| Image | Slot `07` rooms |
| --- | --- |
| `cheap-demo` | `080` |
| `boss`, `7hero`, `demo-only-1`, `demo-1-1` | `080`, `173` |

## The difference in the code

| Pattern | product r26 | `boss` |
| --- | --- | --- |
| `LDA $010B` | absent | offset `0x14` |
| `CMP #$73` | absent | offset `0x17` |

The `boss` program tests the room byte. It has a branch for room `173`. The
product program does not test the room at all, so it cannot give room `173`
its own behavior.

## The capture

`recomp/inputs/native-room173-probe.script` forces room `173`.

| Frame | Mode | Actors |
| --- | --- | --- |
| `entry` | `14` | slot `07`, state `00` |
| `f180` | `14` | slot `07`, state `00` |
| `f420` | `0E` | none |

The frame at `f180` shows Mario over open space. The frame at `f420` shows the
overworld map, so the level ended.

## Port plan

The `boss` program needs six code blocks in bank `20`.

| Block | Size |
| --- | --- |
| `20:8001` | 5328 bytes |
| `20:AB9D` | 8801 bytes |
| `20:CDFE` | 5645 bytes |
| `20:E40B` | 5144 bytes |
| `15:8277` | 1832 bytes |
| `29:D9B7` | 3005 bytes |

The block at `20:CDFE` is already ported as sprite 34. The other five are not.

## Warning

Slot `07` also runs in room `080`. Replace the program only after room `080`
is captured as a regression baseline.