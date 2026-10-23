# Demo 1-1 content inventory against demoOnly1

Date 2026-10-23. First orientation pass for selective Demo 1-1 migration. This is
read-only: it compares **content hashes**, not addresses, because the two builds
relocate their data independently.

Tool: `tools/audit_demo11_additions.py`. Report:
`local/reports/demo11-additions-inventory.json`.

## Method

- Level layer1, layer2 and sprite streams are read through each build's own
  pointer tables and compared by length and SHA-256.
- Room graphics records are read at `14AD08 + room*32` in both builds. Both are
  recipients derived from the same base layout, so the shared offset is valid.
- Music entries are resolved through each build's own `0FE000` table and compared
  as `count(2) + base(2) + data`, not by cutting the stream at `0xFF`.

## Scale

| Table | Differing | Total |
| --- | ---: | ---: |
| Levels with differing content | 22 | 512 |
| Room graphics records | 11 | 512 |
| Music slots | 36 | 256 |

That level count is the important result: the two builds are close enough that a
selective migration is tractable, and most of the whole-image difference is
relocation rather than content.

## Level streams (Demo 1-1 / demoOnly1 lengths)

| Room | Layer 1 | Layer 2 | Sprites |
| --- | --- | --- | --- |
| 005 | 8997 / 8997 | 1 (same) | 182 / 182 |
| 00C | 24 / 6705 | 845 / 37 | 5 / 38 |
| 011 | 377 / 253 | 845 / 4548 | 29 / 44 |
| 025 | 997 / 1567 | 714 / 872 | 23 / 2 |
| 02A | 867 (same) | 872 (same) | 5 / 11 |
| 04F | 6705 / 178 | 37 / 1 | 38 / 5 |
| 056 | 354 / 185 | 12 / 152 | 50 / 5 |
| 08F | 324 / 317 | 872 (same) | 5 (same) |
| 0C5 | 24 / 546 | 5912 / 1 | 5 / 8 |
| 0C7 | 5708 / 5687 | 1 (same) | 83 (same) |
| 102 | 55 / 244 | 6 / 152 | 5 / 26 |
| 105 | 7102 / 7091 | 1 (same) | 134 / 119 |
| 10E | 13778 / 12177 | 4287 (same) | 62 / 29 |
| 126 | 964 / 954 | 1 (same) | 29 (same) |
| 168 | 3287 / 18 | 714 / 1 | 47 / 2 |
| 174 | 828 / 828 | 1 (same) | 92 / 95 |
| 176 | 5886 / 5886 | 1 (same) | 44 (same) |
| 179 | 282 / 99 | 1 / 69 | 5 / 2 |
| 17A | 99 (same) | 4548 / 5912 | 2 (same) |
| 182 | 179 / 179 | 872 (same) | 5 (same) |
| 19B | 6 (same) | 2982 (same) | 5 / 5 |
| 1C7 | 6 (same) | 2982 (same) | 5 / 5 |

Equal lengths with different bytes are real content differences; different lengths
are differences in scope. Either way, this table says nothing about which version
is intended.

## Room graphics records

| Room | Difference |
| --- | --- |
| 056 | demoOnly1 record is the empty default |
| 102 | demoOnly1 record is the empty default |
| 179 | demoOnly1 record is the empty default |
| 0C5 | Demo 1-1 record is the empty default |
| 00C, 011, 025, 04F, 105, 10E, 168 | both set, different extended ids |

The three empty-record rooms are the same missing-dependency shape as the earlier
recoveries: the recipient selects no extra graphics where Demo 1-1 selects real
ids.

## Music

Slots present in Demo 1-1 and absent from demoOnly1: `69`, `6A`, `6B`, `86`, `B0`.

Length-visible differences elsewhere: `8D` (2284 vs 989) and `09` (219 vs 230).
The remaining differing slots share identical lengths and differ only in internal
pointers, which is relocation rather than different music.

## What this establishes, and what it does not

- It establishes which tables differ and by how much.
- It does NOT establish playability, version chronology, or that a longer stream
  is the intended version of that room.
- Room pairs `00C`/`04F` and `0C5`/`17A` look like swapped placements between
  versions rather than additions. A naive copy would move content to the wrong
  room, so these must be understood before anything is copied.

## Candidate pilots, in order

1. **Music slots `69`, `6A`, `6B`, `86`, `B0`** - absent from demoOnly1 and
   self-contained. Worth importing only if a recipient room actually selects
   them; find the selecting rooms first.
2. **Rooms `056`, `102`, `179` graphics** - demoOnly1 holds the empty default
   record while Demo 1-1 selects real ids. Their level streams also differ, so
   the graphics may not fit the recipient layout; check before importing.
3. **Castle room `10E`** - Demo 1-1 carries 1,601 more layer1 bytes and 33 more
   sprites, the largest visible addition in World 1 scope. It needs a full
   dependency closure (its graphics record selects ids demoOnly1 does not use)
   and must not be copied blindly.

Do not migrate by copying whole level streams. Each pilot needs its own dependency
closure and an isolated descendant target.
