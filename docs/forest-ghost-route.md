# Ghost Forest room 114 route inventory

Date: 2026-10-30. Target: `demo11-native-product-r14`. This note records
parsed content and three bounded probes. It does not qualify a route, a clear
or a save.

## Parsed content

| Item | Value |
| --- | --- |
| Map node | index `38E`, `01E8 / 0188`, translevel `38` |
| Goal tape `7B` | `(5232,384)` |
| Key sprites `15` | `(4176,320)`, `(4192,320)`, `(4208,320)` |
| Authored screen exit | screen `17`, flags `07`, low byte `14` |

The screen exit reloads the same room `114` (mode `13` then `14`). The switch
state stays at 0. It is not a course exit.

## Probes

Each probe uses the map-node fixture, damage immunity and a held player
position. The probes write no completion, event or save state.

| Probe | Player start | Result |
| --- | --- | --- |
| Direct | `(5088,368)` | action `09`, death at `(5229,455)`, lives 4 to 3 |
| Near | `(5216,376)` | action `09`, death at `(5229,455)`, lives 4 to 3 |
| Screen 17 then near | `(5216,377)` after reload | action `09`, same death |

All three keep the completion flag at `05`. The tape does not trigger because
the approach crosses a pit. The room needs a platform, a climb or a state
route.

## Floor and vertical extent

A drop test places the player at `(5344,128)` and releases the fixture. The
player falls to Y `176` and stays alive. A left walk from `5344,176` passes
`5277`, `5201`, `5191`, `5052` and `5038` at Y `176` without a fall. The upper floor is
therefore continuous at Y `176`.

The tape at Y `384` lies below the visible frame. The room has a lower section
that the upper floor does not connect. The direct approaches enter the pit
because they start below the upper floor.

## Next work

Find the vertical descent or pipe into the lower section near `(5232,384)`.
Check a shaft, a drop, a climb or the room switch variants. Get walkthrough or
video evidence before another fixture. Do not claim a clear or a save for this
room.
