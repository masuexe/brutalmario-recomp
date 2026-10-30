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

## Next work

Find the intended approach to `(5232,384)`. Check a moving platform, a climb
or the room switch variants. Get walkthrough or video evidence before another
fixture. Do not claim a clear or a save for this room.
