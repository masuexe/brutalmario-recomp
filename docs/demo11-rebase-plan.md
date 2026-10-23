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

## Progress: room 010 music ported, gameplay reached (2026-10-23)

`demo11-room010-music` ports the missing song `2F` upload group from demo8 onto the
already-ported graphics. The payload is fully deterministic (same donor group, same
`source_base` 0x6000 and `destination_base` 0x5400), so the adapted 795-byte payload
hashes the same as on the demoOnly1 line; only the allocation (`0x19D000`) and the
sound slot are new. Candidate
`a72f0d363a7ec01d304b12ed245efcf7e5d3aec1cb2f4e7185f8c63ce5ef04aa`, 715 changed bytes.

### Behaviour now matches the donor

| Target | mode at entry | song |
| --- | --- | --- |
| demo11-base (no fixes) | `0x12` - stuck in Mario Start | `2F` |
| demo11-room010-gfx | `0x12` | `2F` |
| **demo11-room010-music (reference)** | **`0x14` gameplay** | `2F` |
| **demo11-room010-music (native)** | **`0x14`** | `2F` |
| demo8 donor | `0x14` | `24` |

Rendered frames (converted locally to `local/frames/room010-*.png`):

- Unfixed base: a black screen reading `MARIO START !`.
- Donor and both restored hosts: the same grass course with hills, a question block,
  Koopa and Mario - visually the same layout.
- The only visible difference from the donor is the status bar text (`MARIO LV1`
  versus `MARIO`), which is the versions' own HUD, not a restoration artefact.

Measured over the playfield (rows 48-223, 180,224 bytes):

| Comparison | Differing bytes | Share |
| --- | --- | --- |
| donor vs reference | 1,461 | **0.81 %** |
| donor vs native | 35,358 | 19.62 % |
| donor vs unfixed base | 117,618 | 65.26 % |

The reference frame is within 1 % of the donor, which together with the pin-equal
decompressed graphics confirms the 151/102 rendering. The native host differs from
the reference by 18.92 %, a known host-rendering difference (HDMA gradient and sprite
timing), so the qualifier deliberately compares only the reference frame with the
donor and records native pixel parity as not verified.

`tools/qualify_demo11_room010_music.py` pins the payload, the empty slot, the
protected payload, the pointer and the changed-byte footprint, requires mode `0x14`
and song `2F` on both hosts, requires the reference playfield within 2 % of the donor,
and requires the unfixed base to still show the Mario Start stall. Report:
`local/reports/demo11-room010-music-qualification.json`.

Still missing for a full course pass: custom sprite `8D` (the route needs its
ability). Audible acceptance stays with the user.

## Progress: custom sprite 8D is not needed on Demo 1-1 (2026-10-23)

The demoOnly1 line restores custom sprite `8D` because room 010's route needs its
ability. Demo 1-1 stores different data at the same record slot (`28c974f0…` instead
of the default `0000ffffffffffff218001218001ffff`), so the id resolves differently
there. Rather than reverse-engineer that table, the decisive test was behavioural:
run the 8D-dependent route unconverted on the Demo 1-1 line (`demo11-room010-music`,
which already has the graphics and music ports).

| Host | Result |
| --- | --- |
| reference | **route passed**: gameplay `0x14`, room `0x010`, all four ability samples |
| native | **route passed** |

Positions agree within one pixel between hosts: spawn `(0x10,0x14E)/(0x10,0x14F)`,
walk `(0x4F,0x160)` both, flight `(0x10,0x13D)/(0x10,0x13E)`, land `(0x74,0x160)`
both.

So Demo 1-1 already provides whatever ability room 010's route exercises, and
**porting custom sprite 8D is unnecessary** - the largest expected cost of the rebase
disappears. The route's own `until` conditions (`mode 0x14`, room `0x010`, `$71`
returning to 0) all satisfied, and `m1` reported the capture passed on both hosts.

That trims the remaining recovery list to:

| Remaining | Affects | Why |
| --- | --- | --- |
| song `21` transplant | room138 | slot absent in both builds |
| custom sprite `0B` | room138 | demoOnly1 restores it; check whether Demo 1-1 needs to |
| graphics `12A` | room0CB | absent in both builds |

Then the World 1 requalification (courses, saves, death handling) can start.

## Progress: room 138 audio ported and the course clears (2026-10-23)

`demo11-room138-audio` combines the two demoOnly1 audio steps because every pin is
identical on the new base:

| Item | Demo 1-1 |
| --- | --- |
| Room 138 header record at `5CFBE5` | `40 60 22` (music byte `0x22` -> global `21`, absent) |
| Sample-bank selector site `0FCF7E` | `00` |
| Private song slot `0FE17A` | `000000` (absent) |
| Level streams L1/L2 | identical pointers `5CEBE5`/`5CFBEF` and identical bytes |

So the payload is the same deterministic 1,147-byte adaptation of donor private song
`7E`; only the allocation (`0x1A0000`) is new. Candidate
`be5ff1d230a3bfefb072b6acf83e52a9599819daa913482cee72be6a1d6ac2bf`, 1,068 changed
bytes.

### Entry behaviour

| Host | mode | music |
| --- | --- | --- |
| demo11-base | `0x12` Mario Start stall | `0x21` (missing) |
| demo-only-1 (unrestored) | `0x12` | `0x21` |
| **demo11-room138-audio** | **`0x14` gameplay** | **`0x7E`** |

### The clear/save route passes on both hosts

`recomp/inputs/world1-room138-clear-save.script` completes on reference and native:

| Sample | reference | native |
| --- | --- | --- |
| goal tape touched (`$1493`) | `0xF0` | `0xF0` |
| goal position | `(0x11D9, 0x110)` | `(0x11D8, 0x110)` |
| map return after goal | mode `0x0E` | mode `0x0E` |
| uncleared castle | room `0x10E` | room `0x10E` |
| course reload / settled | room `0x138`, gameplay | same |

### Custom sprite 0B is not ported

Demo 1-1 spawns its own `0x0B` sprite during the route (slot 4, status `0x08`) and the
course clears, so the definition is functionally present on the new base. Visual
fidelity of that object therefore remains a playtest question, not an automatic one.

`tools/qualify_demo11_room138_audio.py` pins the payload, slot, patches and footprint,
requires the base to keep stalling on song `0x21`, requires gameplay with song `0x7E`,
and requires the clear/save route on both hosts. Report:
`local/reports/demo11-room138-audio-qualification.json`.

## Progress: room 0CB shared graphics 12A ported - recovery list complete (2026-10-23)

`demo11-room0cb-gfx` ports the shared extended graphics `12A`. On the new base the id
is selected by **five** rooms, not four: `000`, `007`, `0CB`, `100`, `116` - room `007`
is the extra one, so installing the stream also fixes that room's rendering.

| Item | Value |
| --- | --- |
| Donor stream (cheap_demo `12A`) | pointer `28DAEF`, 661 compressed bytes |
| Base slot | empty (`FFFFFF`) |
| Allocation | file `0x109000`, 669 bytes |
| Candidate ROM | `9155c1eb291c784c3804c277cbd29bca3c734772e85862a1c6bfb47537fb1499` |
| Changed bytes | 503 |

### Verification

Structural: the slot was empty, the relocated stream decompresses to the donor image,
the room list selecting `12A` is exactly `[0, 7, 203, 256, 278]`, and every changed
byte lies inside the allocation or the slot.

Regression on the new head (room 0CB cannot be entered yet, so its rendered
appearance stays unverified):

| Check | Ancestor | New head |
| --- | --- | --- |
| room 138 goal `$1493` | `F0` at `(0x11D9,0x110)` | identical |
| room 138 map return | mode `0x0E` at `(0x46,0x12E)` | identical |
| room 010 ability landing | `(0x74,0x160)` | identical |

WRAM `0x100`-`0x1FF` is byte-identical in both regressions, so the shared graphics
installation changes nothing else that these routes exercise.

### The recovery list is complete

| Recovery | Target | Status |
| --- | --- | --- |
| room 106 graphics `1A2` | `demo11-room106` | qualified (terrain 0 diff, 4,738 before) |
| room 010 graphics `151`/`102` | `demo11-room010-gfx` | construction-level |
| room 010 song `2F` | `demo11-room010-music` | qualified (mode `0x14`, playfield 0.81 % of donor) |
| room 138 private song `7E` | `demo11-room138-audio` | qualified (clear/save passes on both hosts) |
| room 0CB graphics `12A` | `demo11-room0cb-gfx` | qualified (structural + regression) |
| room 010 sprite `8D` | - | not needed on this base |
| room 138 sprite `0B` | - | not needed on this base |

New head: **`demo11-room0cb-gfx`** (`9155c1eb`). The next phase is the World 1
requalification on this line, then the user playtest and audition.

## World 1 requalification on the Demo 1-1 line (2026-10-23)

Head `demo11-room0cb-gfx` (`9155c1eb`). Twelve existing World 1 routes were run on the
reference host; the existing scripts were written for the demoOnly1 line, so this
measures transfer, not fresh coverage.

| Route | Result |
| --- | --- |
| room 106 entry | pass |
| room 106 clear | pass |
| room 106 death | pass |
| room 010 death | pass |
| room 010 subroom | pass |
| room 120 coins/save | pass |
| room 138 death | pass |
| room 138 natural entry | pass |
| room 138 clear/save | pass (from the audio qualification) |
| room 010 full two-pipes route | **fails at the first pipe** |
| 1-1 first-goal route | **fails: written for the old layout** |
| 1-1 house return | **fails: depends on the old 1-1 route** |

### The two-pipes failure is Demo 1-1's own behaviour

On the new head the assisted route reaches the screen-8 pipe (`x=0x0898`, camera
`0x0800`), presses Up, and nothing happens: the player stays in room `0x010` and
settles on the ground. The same failure appears on the **minimal**
`demo11-room010-music` target (same `y=0x00E5` at `first_pipe`, no transition), so it
predates the later ports and is not a restoration regression.

The room's data cannot explain it either: both builds have identical room 010 L1
(961 bytes, pointer `64C308`), L2, sprite list, level header (`$64C6C5 = 40 60 30`),
and identical Map16 buffers at the pipe screen. What does differ is version-level
table content - for example the secondary-exit tables `$05:F800` and `$05:FA00`
differ in 7 and 3 entries respectively - so a route scripted for demoOnly1 does not
transfer to the newer build. This is content difference, not a port defect.

### 1-1 is native and healthy

Entry on the new head places Mario at `(0x40, 0x160)` and walking moves him to
`(0x69, 0x160)`, matching the Demo 1-1 baseline exactly. The old goal route is
obsolete because it was tuned to demoOnly1's older layout (its goal tape sat where the
new layout has none).

### Practice entrances added

`demo11-world1-1`, `demo11-world1-2` and `demo11-world1-138` let the Demo 1-1 line be
played from the launcher; 22 entrances total, 120 tests pass.

### Next

Human playtest and audition on the new line: 1-1 native layout, 1-2 entry and pipes,
room 138 custom object appearance, and the restored songs (`2F` for 1-2, private `7E`
for room 138).

### Native parity for the eight transferable routes

All eight passing routes were then replayed on the **native recomp host** and compared
with the reference host: 198 sampled tags across the routes.

| Route | Samples | Mode/room sequence |
| --- | ---: | --- |
| room 106 entry | 10 | identical |
| room 106 clear | 31 | identical |
| room 106 death | 11 | identical |
| room 010 death | 11 | identical |
| room 010 subroom | 8 | identical |
| room 120 coins/save | 59 | identical |
| room 138 death | 10 | identical |
| room 138 natural entry | 58 | identical |

Level mode and room agree at every sampled tag, and the final goal-tape, map-state,
event and submap bytes agree on all eight routes. Player positions drift on the long
assisted routes because input timing differs between hosts, so positions are excluded
from the parity claim deliberately. Report:
`local/reports/demo11-world1-route-parity.json`; tool:
`tools/qualify_demo11_world1_routes.py`.

### 1-1 goal scripting hit a sprite-identity wall (2026-10-23)

Attempts to script a goal contact on the Demo 1-1 line did not succeed, and the
reason is now clear: the sprite numbers seen at runtime do not match the room's
static sprite list.

- Both the demo11 content ROM and the head ROM carry the **same** room `105` sprite
  list (header `0x10`, 44 records, pointer `46D4D2`), ending in `53 D6 7B`.
- Slow traversals scroll the camera well past that record's screen (cam `0x0EEF`,
  `0x12A4`) while the active sprite slots hold ids `13/14/15/16`, `1E/20`, `25/26/27/28`
  - none of which appear in the static list.
- No slot ever held `0x7B`, and a fast ceiling flight to cam `0x144B` also never
  spawned it.

So this hack resolves level sprite ids into different runtime numbers (its custom
sprite layer), meaning the demoOnly1 route's `until a5 == 7B` goal trigger cannot be
reused by reading the level data statically. Identifying the goal at runtime needs
either a spawn-time trace of the generator or a user playthrough that reaches it.

Recorded as an open verification gap, not a defect: the level itself is unaffected and
1-1 remains native on this base.

#### Follow-up: the runtime sprite source is not the list we can read (2026-10-23)

More probes narrowed the gap but did not close it:

- At gameplay the DP values `$CE/$CF/$D0 = D2 D4 46`, i.e. pointer `0x46D4D2`, and
  `$1692` (sprite memory) is `0x10`, which matches that list's header byte `0x10`.
  So the pointer does point at the list we parsed.
- That list holds 44 three-byte records (`51C00A 013074 011002 … 53D67B`), yet the
  sprites actually placed during play have ids `13/14/15/16` and positions
  `(0xAE9,0x13B)`, `(0xAE0,0x0F0)`, `(0x0A00,0x140)` - ids absent from the list.
- Three coordinate decodings (`[y][x]`, `[x][y]`, and `[x][y]` with 16-pixel y) were
  tested against four live sprites and none matched within 32 px.

Conclusion: this hack remaps both sprite identity and placement between level data
and runtime, and the remapped position does not follow the standard SMW encoding.
Scripted identification of the goal therefore needs a generator-level trace that the
current diagnostic core does not expose, or a user playthrough that reaches the tape.

Deferred, not blocking: the level itself is native and unaffected.

### Engine flows re-verified on the new base

The rebase plan called for re-checking the boss, shop and death flows on the Demo 1-1
line, because demoOnly1 had originally been chosen partly because those flows had
been exercised there. Six original-engine routes were run:

| Route | Host | Result |
| --- | --- | --- |
| boss death (`demo-only-1-boss-death`) | reference | **pass** - boss room `0x100`, death, map return `0x0E` |
| boss probe (`demo-only-1-boss-probe`) | reference | **pass** - damage phases then mode `0x0B`/`0x0C`/`0x0D` death sequence |
| repeat death (`demo-only-1-repeat-death`) | reference | **pass** - three deaths with coins 3/2/1 |
| shop (`demo-only-1-shop`) | reference | **pass** - menu open, browse, exit back to the course |
| boss door (`demo-only-1-boss-door`) | reference | not runnable: script begins with `turbo on`, a native-host-only command |
| Lemmy mask (`demo-only-1-lemmy-mask`) | reference | same `turbo` limitation |

The two `turbo` routes are documented as needing the native host (the reference host
must run them without that line), so they are replayed on the native build instead.

#### Follow-up: the two turbo routes pass on the reference host

Both scripts begin with `turbo on`, a native-host-only command. Running them on the
reference host therefore uses the same tracked script with that one line removed, and
the receipts pin that exact derivation:

| Route | Result |
| --- | --- |
| boss door | **pass** - 3,064 frames, final mode `0x14` in the boss room `0x100` |
| Lemmy mask | **pass** - reaches room `0x08C` in gameplay |

`tools/qualify_demo11_engine_flows.py` rechecks all six routes from the pinned
captures: boss death returns to the map, the damage phases reach the `0x0B`/`0x0C`/
`0x0D` death sequence, repeated death loses coins 3/2/1, the shop opens and exits,
the boss door reaches room `0x100`, and the Lemmy route reaches room `0x08C`. Report:
`local/reports/demo11-engine-flows.json`.

Scope limit: reference host only, and this is behaviour transfer of pre-existing
engine routes, not a qualification of restored content.

## One-command acceptance for the Demo 1-1 line

`tools/check_demo11_line.py` runs every acceptance check in sequence and prints a
summary. Verified now:

| Check | Result |
| --- | --- |
| room 106 graphics | pass |
| room 010 graphics (construction) | pass |
| room 010 music | pass |
| room 138 audio | pass |
| room 0CB graphics | pass |
| World 1 route parity | pass |
| engine flows | pass |

Drift guard: every check re-verifies the head ROM `9155c1eb…`, its native binary and
the pinned capture receipts, so any accidental change to the line surfaces as a
failure rather than silently passing.

## Demo 1-1 line status

| Item | Value |
| --- | --- |
| Head target | `demo11-room0cb-gfx` |
| ROM SHA-256 | `9155c1eb291c784c3804c277cbd29bca3c734772e85862a1c6bfb47537fb1499` |
| Chain | `demo11-base` -> `demo11-room106` -> `demo11-room010-gfx` -> `demo11-room010-music` -> `demo11-room138-audio` -> `demo11-room0cb-gfx` |
| Recoveries ported | 1A2, 151/102, song 2F, private song 7E + sample-bank selector, 12A |
| Not needed on this base | custom sprites 8D and 0B (native equivalents) |
| Automated acceptance | 7/7 checks |
| Open items | human playtest and audition; 1-1 scripted goal contact; room 010 pipe route |

### Whole-line byte audit

`tools/audit_demo11_line.py` compares the head ROM with the pinned Demo 1-1 input and
asserts that **every** differing byte lies in a region the chain's recipes declare:
allocations, graphics slots, room-record words, music slots and payloads, code patches
and custom sprite blocks.

| Measure | Value |
| --- | --- |
| Changed bytes vs Demo 1-1 input | 8,214 |
| Declared region bytes | 15,878 |
| Unexpected bytes | **0** |

So the entire rebase touches nothing outside the reviewed recoveries - a single
whole-line integrity guarantee rather than five per-target ones. The audit is now part
of the acceptance driver, which reports **8/8 checks passed**.

### Reachability audit: no unintended World 1 content loss on exercised routes

The two builds differ in 22 level streams, so the rebase is only safe for World 1 if
the rooms its routes reach are identical or intentionally newer. `tools/audit_demo11_
reachability.py` collects the room every capture pinned to the head ROM actually
entered and intersects that with the differing-room list.

| Measure | Value |
| --- | --- |
| Captures pinned to the head | 27 |
| Rooms exercised | 12 |
| Differing rooms exercised | **0C5, 0C7, 105, 10E** |
| Differing rooms never visited | 18 (005, 00C, 011, 025, 02A, 04F, 056, 08F, 102, 126, 168, 174, 176, 179, 17A, 182, 19B, 1C7) |

The four exercised differences are all intended: `0C5` is the intro level, `0C7` is
the overworld map, and `105`/`10E` are the newer 1-1 and castle this rebase was for.
The rooms containing the *older* demoOnly1 versions - including `011`, `025`, `056`,
`102` and `179` - were never entered by any qualified World 1 route, so no tested
path loses content.

Those 18 unvisited differences are the honest risk list: if a pipe or sublevel leads
into one of them, the newer build's version loads instead. That is the same open
question as the room 010 pipe route, and a playthrough closes it.

The audit is wired into the acceptance driver as a drift guard: if a future capture
exercises a differing room outside `{0C5, 0C7, 105, 10E}`, acceptance fails and forces
a review. Driver now reports **9/9 checks passed**.

### 1-1 start-gap probe

Walking right from the fixture spawn with a fixed jump rhythm on the Demo 1-1 line falls
into a gap at about `x=0xDE` (roughly 220 px from the start) and costs a life; the
respawn repeats the same outcome. This is the newer course design asking for its own
mechanics, not a regression: the old layout has a comparable gap slightly further on
(`x≈0xFB`). It also explains why blind scripted traversal cannot reach the goal - the
route needs per-section timing that a fixed press rhythm cannot express.

Recorded in the playtest checklist so the first human playthrough is not surprised by
it.
