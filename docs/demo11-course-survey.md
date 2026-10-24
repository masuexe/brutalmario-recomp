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

## Full-range result (translevels 001-0C0)

192 probes ran on the reference host:

| Result | Count | Meaning |
| --- | ---: | --- |
| Playable `14` | 70 | Level reached gameplay |
| Mario Start stall `12` | 78 | A music slot is null |
| Mode `0E` | 34 | Returned to the map; likely unused or empty rooms |
| Mode `0D` | 7 | Death or invalid entry |
| Mode `17` | 2 | Unexpected state |
| Mode `0B` | 1 | Unexpected state |

All 42 stalls sampled before the range widened requested a null music slot. The
unique stalled songs are `02`, `03`, `05`, `06`, `21`, `2C`, `36`,
`3B`, `3C`, `3E`, `3F`, `42`, `43`, `44`, `45`, `46`, `47`,
`53`, `55`, `56`, `57` and `5B`. Six have verified new-family mappings,
two are legacy-exclusive and the rest are unmapped.

The first fix candidate is
`[demo11-course-music-retarget](demo11-course-music-retarget.md)`. It retargets
17 rooms to existing new-family slots and lets seven sampled levels reach
gameplay. It is a candidate, not the current head.

## Candidate full-range result

The candidate survey reran all 192 probes with the same method:

| Result | Head | Candidate |
| --- | ---: | ---: |
| Playable `14` | 70 | 77 |
| Mario Start stall `12` | 78 | 61 |
| Mode `0E` | 34 | 41 |
| Mode `0D` / `0C` | 7 | 9 |
| Mode `17` | 2 | 3 |
| Mode `0B` | 1 | 1 |

Seven translevels change from stall to gameplay: `015`, `021`, `03C`,
`048`, `04E`, `054` and `056`. The other retargeted levels now return to
the map or die, so they need separate work.

61 stalls remain. They request 20 unique songs: `02` blocks 32 of them, and
`05` blocks 3. The rest are one or two levels each. Song `02` is the first
target for the donor song restoration.

## First broken course: translevel 001

Translevel `001` stops at mode `12` (Mario Start). The reference capture shows
the last music request `$57`. The recipient song table entry at
`$0F:E000 + $57*3` is `00 00 00`, so the uploader waits for a null pointer.
This is the same failure shape as the Snow Star song fix.

The music mapping names slot `$57` **KingBonbie VS MechaBonbie** from
Super Momotarou Dentetsu DX, used in the **Rescue Yoshi** level. Every other
supplied version has a non-null pointer `A1 94 D2` for this slot: cheap-demo,
demo6, demo7, demo8, 7hero, mazo, ow and the three ra versions. Demo 1-1 and
demoOnly1 have the null slot.

Next step: port slot `$57` with the reviewed music recipe workflow
(`tools/restore_star_world_1.py`, `adapt_music`), like the room 010 and room
138 music recoveries. The donor song data must be located in the donor's
upload group layout first.

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