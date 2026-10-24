# Demo 1-1 course loading survey

Date: 2026-10-26. This is a diagnostic survey of course loading on the accepted
Demo 1-1 line. It does not qualify playability by itself.

## Method

The survey enters each game translevel from the Star World lower-left map 6
node. The node's overworld tile level byte is overwritten with the target
translevel, so the probe does not claim a donor map route. The tile address
comes from the observed map 6 layout:

```
0xD400 + (y >> 4) * 16 + ((x >> 4) & 15) + (x >> 8) * 0x200
```

with X=`0x128`, Y=`0x1E8`. Each capture starts from a fresh save. The
reference host runs the probe, so no native build is needed for this survey.

The probe script:

1. Boots to a fresh save.
2. Teleports to map 6 at the lower-left node.
3. Pokes the node's tile level byte with the target translevel.
4. Enters the node and samples WRAM at 240 and 600 frames.

Tool: `tools/survey_demo11_courses.py`. Report:
`local/reports/demo11-course-survey.json`. Captures:
`local/captures/d11-survey-<TTT>`.

## Reading the result

| Mode | Meaning |
| --- | --- |
| `14` | Level reached gameplay (loaded) |
| `12` | Mario Start stall (a dependency is missing) |
| other | Unexpected load state or failure |

The sample also records the room number, the translevel echo, the player
position and the remaining lives. Room and translevel can differ, because the
recipient maps translevels to rooms through its own table.

## Pilot result (translevels `001`-`008`)

| Translevel | Result | Room | Mode |
| --- | --- | --- | --- |
| `001` | Mario Start stall | `001` | `12` |
| `002` | Playable | `002` | `14` |
| `003` | Playable | `003` | `14` |
| `004` | Playable | `004` | `14` |
| `005` | Playable | `005` | `14` |
| `006` | Playable | `006` | `14` |
| `007` | Playable | `007` | `14` |
| `008` | Playable | `008` | `14` |

The pilot also confirms the override reaches the intended level: the room echo
matches the translevel for these entries. Translevel `001` is the first
candidate for a dependency investigation.

## Next steps

1. Run the survey over the wider translevel range and record the full table.
2. Inspect the Mario Start stalls: compare the room graphics record, music
   pointer and sprite dependencies against the donor versions, as the Star
   World recoveries did.
3. Build a per-world summary and prioritize the broken courses in game order.

## Limits

- The survey uses a fresh uncleared save and a map shortcut. It does not claim
  map-route correctness, course completion, saves or sound.
- Translevels outside the real course list can load unrelated rooms or fail;
  the report is an inventory, not an acceptance.
- The reference host only. Native parity comes later for each accepted course.
