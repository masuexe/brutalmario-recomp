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

## Screen counts: Demo 1-1's World 1 courses are larger

The first layer1 byte encodes the horizontal screen count as `(byte & 0x1F) + 1`,
the same convention the earlier room documents use (room 105 -> 20, room 138 ->
19). Applying it to the differing rooms gives:

| Room | Demo 1-1 screens | demoOnly1 screens |
| --- | ---: | ---: |
| `00C` | 25 | 12 |
| `011` | 6 | 10 |
| `025` | 5 | 1 |
| `04F` | 12 | 2 |
| `056` | 10 | 7 |
| `0C5` | 2 | 1 |
| `102` | 2 | 11 |
| **`105` (1-1)** | **24** | **20** |
| **`10E` (castle)** | **23** | **13** |
| `168` | 5 | 4 |
| `179` | 1 | 3 |

The two World 1 rooms that matter for the current recipient are therefore
**larger in Demo 1-1**: 1-1 gains four screens and the castle gains ten, which is
the strongest evidence yet that Demo 1-1 carries additional course content rather
than only relocation.

Caveat: room 105 gains four screens while its measured layer1 data grows by only
11 bytes, so the extra screens are sparsely populated; the castle gains ten
screens together with 1,601 bytes. That asymmetry is a hint about authoring order
and should be checked before treating either as finished content.

## Recommended first pilot

**Room `105` (World 1-1)**, not the castle: it is the course the user actually
plays first, its difference is smaller and better understood (same layer1 prefix
style, four extra sparse screens, 15 extra placed sprites), and its dependency set
is already the subject of existing qualifications. The castle is the larger prize
but a ten-screen extension with new graphics ids is a much bigger closure.

## Classification: rewrites, one relocation, and one missing level

Similarity of the two layer1 streams was measured with an order-preserving diff
(`difflib` matching blocks) over the 22 differing rooms, and every substantially
different room was then cross-matched against all other rooms to catch relocated
content.

| Room | Demo 1-1 bytes | demoOnly1 bytes | In-order match | Class |
| --- | ---: | ---: | ---: | --- |
| `005` | 8,996 | 8,996 | 100.0% | near-identical |
| `02A` | 866 | 866 | 100.0% | near-identical |
| `176` | 5,885 | 5,885 | 100.0% | near-identical |
| `17A` | 98 | 98 | 100.0% | near-identical |
| `19B` | 5 | 5 | 100.0% | near-identical |
| `1C7` | 5 | 5 | 100.0% | near-identical |
| `0C7` | 5,707 | 5,686 | 99.6% | near-identical |
| `182` | 178 | 178 | 99.4% | near-identical |
| `174` | 827 | 827 | 99.3% | near-identical |
| `126` | 963 | 953 | 97.9% | near-identical |
| `08F` | 323 | 316 | 97.8% | near-identical |
| `10E` (castle) | 13,777 | 12,176 | 35.5% | **rewritten** |
| `0C5` | 23 | 545 | 30.4% | rewritten |
| `00C` | 23 | 6,704 | 26.1% | rewritten |
| `102` | 54 | 243 | 25.9% | rewritten |
| `105` (1-1) | 7,101 | 7,090 | 12.3% | **rewritten** |
| `056` | 353 | 184 | 8.2% | rewritten |
| `011` | 376 | 252 | 5.1% | rewritten |
| `179` | 281 | 98 | 2.5% | rewritten |
| `025` | 996 | 1,566 | 2.6% | rewritten |
| `168` | 3,286 | 17 | 0.2% | **missing in demoOnly1** |
| `04F` / `00C` | 6,704 | 6,704 | 100% cross-match | **relocated pair** |

### What the numbers mean

- **Only one relocation exists**: Demo 1-1's room `04F` is demoOnly1's room `00C`
  byte for byte. Every other difference is content authored independently in each
  version.
- **1-1 and the castle are rewrites, not extensions.** Their layouts diverge from
  the first object, so replacing the recipient's 1-1 or castle with Demo 1-1's
  version would substitute a *different course*, not recover lost content. That is
  a product decision, not a restoration step.
- **Room `168` is the one genuine missing level**: demoOnly1 holds a 17-byte stub
  and 2 sprites where Demo 1-1 has a 3,286-byte, 5-screen level with 47 sprites.
- The eleven near-identical rooms differ by small, local edits - the kind a
  version bump produces.

### Consequence for the migration plan

"Selective recovery of Demo 1-1 additions" should mean importing content that
demoOnly1 does **not** have (room `168`, the graphics resources already imported,
the five music slots), not overwriting demoOnly1's own course versions with Demo
1-1 rewrites. Replacing 1-1's layout would discard the version the current World 1
qualifications were built on.

Open question before importing room `168`: whether any recipient map node actually
selects level `168`. If nothing references it, the import would be inert content.

## Reachability check for the missing level 168 (2026-10-23)

Level `168` has translevel `0x8C` (`0x168 - 0xDC`). The recipient's World 1 map page
table (loaded at `$7ED000`, indexed by the documented 16x16 page formula) does not
contain `0x8C`, so no World 1 node selects that level.

Attempts to sample the other submaps failed: teleporting with `poke 1f11` for
submaps 1-4 produces byte-identical map RAM (`C800-D000` hash `3fb1ecc7`, page table
hash `2f1aac6a`) to the initial map0 state, both when poked after the map loads and
when poked from a fresh session. The practice teleport therefore cannot switch
submaps, so the remaining submaps cannot be sampled this way.

This matters because it bounds what the migration can achieve: without a map node,
importing level `168` would add content that nothing in the recipient reaches.

## Strategic conclusion

Demo 1-1's additional content is tied to Demo 1-1's overworld. The recipient's own
map and content set are internally consistent, so 'selective recovery' without map
integration can only import inert resources. Any further step needs an explicit
decision about migrating map nodes and routes, which is a much larger and riskier
change than resource recovery and would alter the overworld the World 1
qualifications were built on.

Open, deliberately not attempted: importing level `168`, importing the five
Demo 1-1-only music slots without a selecting room, and any overworld migration.
