# Rebasing the restoration onto Demo 1-1

Date 2026-10-23. The user decided to change the restoration base to Demo 1-1 instead
of reverse-engineering its custom sprite mechanism. This records the evidence behind
that decision and the plan.

## Why rebasing beats sprite reverse-engineering

Migrating the newer World 1-1 *into* demoOnly1 stalled: the level layout, graphics,
sprite placement and headers can be copied, but the custom sprite behaviour cannot,
and without it the course hard-stalls at `x=0xF92` of 24 screens and cannot be
completed. Demo 1-1's custom sprite storage does not use the 16-byte record table
this project restores from, so it would have to be reverse-engineered with no
guarantee of parity.

Rebasing removes that problem entirely, because Demo 1-1 **natively** has:

| Property | Demo 1-1 |
| --- | --- |
| Newer World 1-1 (`105`) and castle (`10E`) | present |
| Custom sprite behaviour for that layout | present |
| Extended graphics `29E 29F 2A0 2A2` | present |
| Music `69 6A 6B 86 B0` | present |

## What still has to be restored on the new base

Both builds share the same missing dependencies, verified by pointer tables:

| Missing | Affects | Note |
| --- | --- | --- |
| Graphics `1A2` | room106 | absent in both builds |
| Graphics `151`, `102` | room010 (1-2) | absent in both builds |
| Music `2F`, sprite `8D` | room010 | absent in both builds |
| Music `21` (song group) | room138 | slot absent in both builds |
| Graphics `12A` | room0CB | absent in both builds |
| Music `1E` | 100-coin cue | absent in both; engine-special |

So the rebase keeps roughly five recoveries instead of the twelve-target chain, and
none of them needs sprite-mechanism reverse-engineering.

## Plan

1. **Base line.** `demo11-base` roots the new chain and reproduces the pinned Demo 1-1
   input exactly (`314496f6…`). No changes at this target.
2. **Port the recoveries** one at a time as descendants: room106 graphics, room010
   graphics/music/sprite, room138 song/sprite, room0CB graphics.
3. **Re-qualify World 1** on the new line: entry, goal/save, death, the 1-1 -> room106
   -> room120 -> room138 chain, using the existing scripts adapted where the newer
   layout changes the route.
4. **Switch the head** once qualified; archive the demoOnly1 line and its backup.

## Risks and mitigations

- **Saves do not carry over.** The baseline SRAM header exponent differs (5 vs 1), so
  practice sessions and existing saves are not interchangeable. The launcher already
  isolates per-target saves; back up before switching.
- **Every qualification must be re-run.** The existing captures pin demoOnly1-based
  ROMs; none of them transfer.
- **Engine flows need re-verification.** demoOnly1 was chosen originally because
  boss/shop/map flows had been exercised there. Demo 1-1's content is largely
  identical, but those flows must be re-run on the new base before acceptance.
- **A few levels are richer in demoOnly1** (`0C5`, `102`, `025` and small rooms). They
  are outside the World 1 scope; evaluate before any wider switch.
- **Rollback stays available**: `tools/backup_state.py` snapshot
  `local/backups/pre-room105-migration-20261023-051544` plus `docs/rollback.md`.

## Progress: room 106 graphics recovery ported (2026-10-23)

`demo11-room106` is the first recovery on the new base, descended from `demo11-base`.
The port was nearly mechanical because Demo 1-1 needs the same fix and its room data
already matched:

| Check | Result |
| --- | --- |
| Room 106 graphics record on Demo 1-1 | `0180a20019001700140084001300a20100007f00…`, **identical** to demoOnly1's |
| Selected extended graphics | `1A2` at word 6 (record offset 14), same as demoOnly1 |
| Free extended-graphics slots on Demo 1-1 | `F00`-`FFF`, so `FBD` was free |
| Donor `1A2` stream (cheap_demo) | pointer `35F39D`, 3,138 compressed bytes |
| Candidate ROM | `864dc3ef3f06576e55f5d7f1c9f0ae90ee4679ede1d815f2f764996bd06e343c` |
| Changed bytes | 2,590 - the same count as the original demoOnly1 recovery |

Location: allocation file `0x198000`, relocated pointer slot `FBD`, record word 6.

### Verification

`tools/qualify_demo11_room106.py` checks the pinned identities, the empty destination
slot on the base, the record selector, decompression equality, the protected payload,
the changed-byte footprint, the native build identity, and both captures. Terrain is
compared against cheap_demo over **11 screens** in both Map16 buffers:

| Host | settled | walk | jump | landed |
| --- | --- | --- | --- | --- |
| reference | 0 differing bytes | 0 | 0 | 0 |
| native | 0 | 0 | 0 | 0 |

Position deltas are 0 as well, so the recovery is at least as tight as the original
demoOnly1 qualification (which allowed 2 px). Report:
`local/reports/demo11-room106-qualification.json`.

Scope limit: entry and movement only. Complete route, death and save behaviour are not
re-qualified on this base yet, and World 1 as a whole is not qualified on Demo 1-1.

## Progress: room 010 graphics ported as a construction-level descendant (2026-10-23)

`demo11-room010-gfx` ports extended graphics `151` (used twice) and `102` for room
010 onto the Demo 1-1 line. Room 010's record and the additional record at `14B648`
are byte-identical between the builds, and slots `FBB`/`FBC` were free. Candidate
`51558275e653bb380c27cdf1cf0ef77f27e33e107bf96dab8ed78fc42e428291`, 3,338 changed
bytes.

### Methodological correction found while verifying it

Comparing Map16 terrain does **not** detect this graphics defect: the untouched demo11
base, this port and the demo8 donor all load the same tiles (0 differing bytes).
Room 106 is different - its recovery *is* terrain-sensitive, confirmed by capturing
the unfixed base:

| Room 106 capture | mode | player y | terrain diff vs donor |
| --- | --- | --- | --- |
| demo11-base (unfixed) | `0x14` | `0x0442` (falling) | **4,738** bytes |
| demo11-room106 (ported) | `0x14` | `0x0160` (standing) | **0** |

So the room 106 acceptance stands, while room 010's graphics are a rendered-tileset
fix that the terrain metric cannot see.

### What actually blocks room 010 on the new base

With graphics ported, the level still sits in **mode `0x12` (Mario Start)** instead
of reaching gameplay `0x14` - on the base and on this target alike. The donor reaches
`0x14`, and the demoOnly1 line reaches `0x14` only once music `2F` and sprite `8D` are
restored. So the next dependency is **music `2F`**, not the graphics.

`tools/qualify_demo11_room010_gfx.py` therefore checks construction and invariants
rather than claiming a course result: slots were empty, all three selectors point at
the relocated streams, decompression matches the donor images, changed bytes stay
inside the reviewed regions, the port does not change the level mode, and the donor
capture still reaches gameplay. The report records `not_verified`: the rendered
tileset on this base.

Captures (tracked script `recomp/inputs/world1-room010-terrain.script`):
`d11-010-terrain-base`, `-ref`, `-native`, `-donor` in `local/captures/`.
