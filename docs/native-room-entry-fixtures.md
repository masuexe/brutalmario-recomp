# Room entry fixtures: the poke order

## Result

The order of the writes controls whether a forced room entry loads. A wrong
order leaves the room in mode `12` or keeps the previous room.

## Working order

```
poke 19b8 <room low>
poke 19d8 <subroom>
poke 94 80004001
poke 88 0000
poke 71 06
wait 60
poke 19b8 <room low>
poke 19d8 <subroom>
wait 300
```

The `$19B8` write comes first and repeats after the other writes. The second
write replaces the value that the engine copies over during the transition.

For a room below `0x100`, use `19d8 04`. For a room at `0x100` or above, use
`19d8 01`.

## Evidence

Room `080` stayed in mode `12` with the earlier order. It reaches mode `14`
with this order.

## Wait for the room, do not wait a fixed time

A fixed wait is not reliable. Room loads take between 100 and 2000 frames.
Use two `until` steps instead.

```
poke 19b8 <room low>
poke 19d8 <subroom>
poke 94 80004001
poke 88 0000
poke 71 06
wait 60
poke 19b8 <room low>
poke 19d8 <subroom>
until 010b == <room low> 2500
until 0100 == 14 1200
dump r<room>
```

## One capture holds six or seven rooms

After about seven forced room changes, the next `until 010b` times out. The
game stops accepting the forced change.

| Batch | Rooms | Result |
| --- | --- | --- |
| `100` | `100` to `105` | 6 of 6 load |
| `106` | `106` to `10B` | `106` loads, then the limit stops the run |
| `140` | `140` to `145` | 6 of 6 load |
| `148` | `148` to `14E` | 7 of 7 load |
| `150` | `150` | `151` times out in sequence, but loads alone |
| `158` | `158`, `159` | `15A` times out in sequence, but loads alone |

Rooms `151`, `15A` and `107` load correctly in a single-room probe. A timeout
in a batch is a limit of the fixture, not a defect in the room.

## Room `080` baseline for slot `07`

`recomp/inputs/native-room080-r28.script`, capture `r28-room080-base`.

| Frame | Mode | Song | Slot `07` actors |
| --- | --- | --- | --- |
| `f0300` | `14` | `19` | three actors at state `08` |
| `f0600` | `14` | `19` | three actors at state `08` |
| `f1200` | `14` | `19` | three actors at state `08` |
| `f1800` | `14` | `19` | three actors at state `08` |

Room `080` works with the current slot `07` program. Keep this result as the
regression reference for the slot `07` port.

## Room `173` status

`recomp/inputs/native-room173-r28.script`, capture `r28-room173`.

| Frame | Room | Mode | Song | Slot `07` actors |
| --- | --- | --- | --- | --- |
| `f0300` | `173` | `14` | `FF` | one actor at state `08` |
| `f0600` | `173` | `0E` | `00` | none |

Room `173` loads and then loses the level at frame `600`. The cause is the
slot `07` program, which has no room test and no state `2` handler.

See `docs/native-room173-sprite.md` for the program difference.