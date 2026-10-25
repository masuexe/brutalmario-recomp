# Custom sprite audit

Date: 2026-10-26. This audit records what the Demo 1-1 line still needs for
custom sprites and why a static rule alone cannot order that work.

## Record format

The line keeps a 16-byte record for each sprite ID at `0x31:8272`, file offset
`0x188272`. The default record is
`0000ffffffffffff218001218001ffff`. A record that differs from the default
points to custom code.

- Bytes 8 to 10 hold a 24-bit file offset to the init entry.
- Bytes 11 to 13 hold a 24-bit file offset to the main entry.
- Both offsets must stay inside one RATS block in the donor ROM.

A custom sprite port therefore needs four parts:

1. the RATS code block,
2. the adapted record,
3. the shared engine dependencies,
4. the sprite graphics and its extra data.

The ports for sprite `8D` (room `010`) and sprite `0B` (room `138`)
implement parts 1 to 3. See `config/restorations/demo11-sprite8d.json` and
`config/restorations/demo11-sprite0b.json`.

Demo 1-1 does not use this table as its native mechanism. The project added the
table and the hook. The rebase plan explains that history:
[demo11-rebase-plan.md](demo11-rebase-plan.md).

## Static candidate rule

A sprite ID is a static candidate when all of these conditions hold:

1. a World room uses the ID,
2. the target record is the default record,
3. a donor record is not the default record,
4. both donor pointers stay inside a RATS block.

Results on the world graphics chain end:

| World | Candidate IDs |
| --- | ---: |
| World 1 | 32 |
| World 2 | 22 |
| World 3 | 13 |
| World 4 | 20 |
| World 5 | 21 |
| World 6 | 25 |
| World 7 | 12 |
| World 8 | 4 |
| Star | 30 |

## Why the rule over-triggers

The candidate set includes low vanilla IDs such as `02`, `04`, `05` and
`07`. The donors redefine many vanilla IDs with their own code. A non-default
donor record therefore does not prove that the level expects custom behaviour.

The first run used every content version as a donor and reported 118 candidates.
Most of them came from `ra-mario-complete`. The run now uses only the legacy
family: `7hero`, `cheap-demo`, `mazo`, `ow`, `demo8`, `demo7` and
`demo6`. The count is 82 unique IDs. It is still above the true defect count.

## Evidence needed next

Use runtime evidence before any port:

- a user report that names the level and the odd object,
- a capture where the sprite state or position differs from the donor level,
- a donor room whose sprite list needs an ID that the target record leaves as
  default.

The static list is an inventory. It is not a defect list.

## Next steps

1. Ask the user for the levels with odd falling objects.
2. For each named level, map the placed sprite IDs to their donor records.
3. Port one sprite at a time with the four required parts and a bounded
   qualifier.
4. Keep the record table heuristic in `tools/world_audit.py` as an inventory
   only.

## Limits

- A non-default donor record does not prove a missing behaviour.
- A missing behaviour does not always show in a reference and native comparison,
  because both hosts run the same ROM.
