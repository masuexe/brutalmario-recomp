# Mario the Pyromaniac room 11E route inventory

Date: 2026-10-30. Target: `demo11-native-product-r14`. This note records
parsed content and four bounded probes. It does not qualify a route, a clear or
a save.

## Parsed content

| Item | Value |
| --- | --- |
| Map node | index `38B`, `01B8 / 0188`, translevel `42` |
| Goal tape `7B` | `(2656,480)` |
| Key sprites | none |
| Screen exit | screen `19` to room `037` |
| Other sprite ids | `13`, `1D`, `3E`, `75`, `80`, `09`, `0D`, `0E`, `0F` |

## Probes

Each probe uses the map-node fixture, damage immunity and a held position. The
probes write no completion, event or save state.

| Probe | Start | Result |
| --- | --- | --- |
| Drop | `(2656,200)` | lands at Y `224`, lives 4 |
| Right walk | from `2656,224` | Y `224` at `2722`, `2798`, `2808` |
| Left walk | from `2656,224` | Y `224` to `2401`, then Y `272` at `2388` |
| Lower frame | hold `(2656,380)` and `(2656,460)` | lower band with a bridge and yellow markers |

The goal at Y `480` lies one screen below the upper floor. No probe touches the
goal. The completion flag stays at `05` and the life count stays at 4.

## Kill boundary

A deeper walk goes left to `2313,272`, then right to `2554,305`. The next step
falls into the pit. The player reaches action `09` at Y `454` and then Y `822`.
The kill boundary is near Y `454`. The goal sprite at Y `480` sits below that
boundary. A normal route therefore cannot touch it.

## Next work

Treat the Y `480` goal sprite as an author exception until a walkthrough or a
video shows a route. Check the step at `2401` and the rooms on both sides for a
lower entrance. Do not claim a clear or a save for this room.
