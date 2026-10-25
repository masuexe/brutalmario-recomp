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

## Stall root causes

The 61 remaining stalls split into two dependency groups:

| Group | Count | Evidence |
| --- | ---: | --- |
| No missing extended graphics | 42 | Each requests a null music slot |
| Missing extended graphics | 19 | 59 distinct null graphics IDs |

Many stalled rooms select several null extended graphics IDs. Room `0x173`
selects seven: `1AB`, `201`, `202`, `286`, `287`, `288` and `289`.
The [graphics candidate A](demo11-course-gfx-a.md) ports them from 7hero.

The graphics install alone does not fix room `0x173`. Its last request is song
`1A`, and slot `1A` stays null. The room still stalls at mode `12`.

Room `0x173` layer-1 data matches 7hero room `0x173` and demoOnly1 room
`0x173` exactly. Both new-family builds leave the room unplayable, so the
legacy donors are the only resource source.

The [music batch A and fix batch B candidates](demo11-course-batch-a.md) now
fix three stalled translevels: `01E` and `043` with music only, and `038`
with music and graphics. Their captures reach gameplay on reference and native.

The [music batch C and fix batch D candidates](demo11-course-batch-c.md) add
songs `55`-`57` and five more graphics IDs. They fix `04B`, `0A5`, `00E`,
`01F` and `06D`.

The [graphics fix batches E and F](demo11-course-batch-e.md) add sixteen more
graphics IDs. They fix `080`, `081` and `068`.

The [music batch G](demo11-course-batch-g.md) uses raw legacy group slices for
songs with unreviewed commands. It fixes `02B`, `02F` and `06C`.

The [graphics fix batches H and I](demo11-course-batch-h.md) port sixteen more
graphics IDs. They fix `027`, `03A`, `040`, `051` and `066`, and reach
gameplay on `018` and `01B`.

## Chain-end survey

The full survey also ran on the candidate chain end (`demo11-fix-batch-i`).

| Result | Head | Chain end |
| --- | ---: | ---: |
| Playable `14` | 70 | 97 |
| Mario Start stall `12` | 78 | 51 |
| Mode `0E` (returns to map) | 34 | 31 |
| Death or other modes | 10 | 13 |

The chain improves 22 reviewed translevels and removes 27 stalls in total. The
51 remaining stalls need the low ids (`02`, `03`, `05`, `06`, `1A`),
song `6D`, or graphics that are not ported yet.

The [music batch J and graphics batches K1-M](demo11-course-batch-j.md) add
five more legacy songs and 21 graphics IDs. They fix `00D`, `01A`, `02C`,
`034`, `03C`, `048`, `04E`, `055`, `056`, `062`, `06F` and
`070`.

The [music batch N and graphics batches O1/O2](demo11-course-batch-n.md)
resolve the low-id blocker. The engine plays its own built-in song for those
ids; a valid payload only satisfies the upload handshake. All 39 remaining
chain stalls now reach gameplay.

Report: `local/reports/demo11-course-survey-chain-i.json`.

## Final chain survey

The full survey ran on the final chain end (`demo11-fix-batch-o2`).

| Result | Head | Chain end |
| --- | ---: | ---: |
| Playable `14` | 70 | 147 |
| Mario Start stall `12` | 78 | 0 |
| Mode `0E` (returns to map) | 34 | 31 |
| Death or other | 10 | 14 |

All 78 stalls are fixed. The 45 non-playable entries that remain are not
stalls: 31 return to the map, 10 die or use a death mode, 3 are in a reload
fade and 1 has an unexpected mode.

Every non-playable entry is explained:

| Class | Count | Detail |
| --- | ---: | --- |
| No-input death | 43 | Mode `14` at entry 240, lives drop 4 to 3, then map, death or reload mode |
| Normal map return | 2 | Translevels `077` and `07B` load room `0C5` (Yoshi's House), which returns to the map by design |

No stall and no unreachable room remain in the range. The chain end also passes
the whole-line byte audit: 39 recipes reproduced, 382,653 changed bytes inside
494,184 reviewed bytes, zero unexpected bytes.

Report: `local/reports/demo11-course-survey-chain-o.json`.

## Full-range completion (0x001-0x0FF)

The tail range ran on the chain end after the main range.

| Range | Playable | Stalls | No-input deaths | Map returns |
| --- | ---: | ---: | ---: | ---: |
| `001`-`0C0` | 147 | 0 | 43 | 2 |
| `0C1`-`0FF` | 60 | 0 | 3 | 0 |
| **Total** | **207** | **0** | **46** | **2** |

All 255 translevels load. No stall remains in the full range. The 48
non-playable entries are the 46 no-input deaths and the two Yoshi's House
returns.

The survey tool now rejects a range outside `0x000`-`0x0FF`, because the
map node level byte is eight bits wide.

Report: `local/reports/demo11-course-survey-tail.json`.

`tools/qualify_demo11_full_range.py` checks both reports, the capture
receipts and the result classes. The suite now reports **43/43**.

## Remaining graphics references

The chain end still leaves some extended graphics slots empty. The base Demo
1-1 ROM has 190 unique empty slots across 111 room headers, so empty slots are
normal in this game. The chain end has 90 unique empty slots across 55 room
headers.

All those rooms load and reach gameplay. The engine uses its fallback graphics.
Visual correctness for those rooms is not claimed.

The graphics batches J-M, N and O explain the reduction from 190 to 90.

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

The [song 0x57 candidate](demo11-music-57.md) now installs the reviewed
donor song and removes the stall. Translevel `001` reaches gameplay on the
candidate and matches native on the sampled fields. The candidate is not the
head yet.

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