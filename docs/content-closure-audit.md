# Content closure audit

Date: 2026-10-29. Baseline commit: `f65169e`. Product target:
`demo11-native-product-r12`. ROM SHA-256
`d29b121e83a4fa47e0423779feaeb66000f9806a02c89f15eeaf8a4baaf3f552`.

## Result

The tracked record shows no unstarted content block with the size of `7hero`
or `mazo`. It does show a large unfinished acceptance block. Course loading is
complete. Course play is not.

Three findings define the next phase.

1. All 255 translevels load. The full-range survey finds no Mario Start stall.
   A load result is not a play result.
2. Route, exit and save acceptance covers parts of World 1 and all nine Star
   World courses. Worlds 2 to 8 have no such acceptance.
3. The endgame line is open. The record has no earned Seven Koopaling victory
   and no saved completion. It also has no qualified mazo attack and clear.

The product target is a candidate. The record holds no complete playthrough
from a new save.

## Method and limits

This audit reads the tracked documents, `config/world-map.json`,
`config/demo11-level-index.json`, the target config and the test list. It runs
the unit suite. It starts no capture and adds no runtime evidence. A statement
in this audit is only as strong as its cited record.

The unit suite passes 339 tests at `f65169e`. The log is
`local/audit-unit-tests.log`.

## Evidence classes

| Class | Meaning |
| --- | --- |
| Qualified | A receipt covers a route, an exit and a save check, or the user accepted the stage. |
| Partial | A receipt covers entry, one resource or one behavior. The stage is not complete. |
| Load only | The course reaches gameplay in the survey. No play acceptance exists. |
| Missing | A record, a resource or a connection is absent. |
| Original exception | The author did not finish the content. The project keeps the donor state and claims no clear. |

## Loading coverage

The [course survey](demo11-course-survey.md) enters each translevel through a
map 6 tile override. The final survey reports 255 loads and zero stalls. The
non-playable entries are 46 no-input deaths and 2 Yoshi's House returns. The
survey classifies them as load observations, not defects.

The survey count of playable entries changes with each chain end, because
restored sprites start to act. The last recorded counts are 207 playable
entries on `demo11-fix-batch-p` and 231 on `demo11-gfx-boss76`.

The [product survey](demo11-product-survey.md) now covers the current target.
It runs the native host on `demo11-native-product-r12`. All 255 translevels
load, 227 entries are playable and no stall remains. One entry crashes:
translevel `094` (level `170`). The base ROMs load the same level. The
`C2` type-3 record is the recorded cause.

## Course coverage by world

**2026-10-29 qualification:** World membership and course labels in
`config/world-map.json` are provisional. Native r13 visuals contradict the
bridge/fire labels for rooms `121`/`126`; the community directory uses different
version-local IDs. The table below is a summary of the historical catalog,
not a verified per-world inventory. The absence of a complete-game acceptance
record still stands. See [the corrected route inventory](world2-route-inventory.md).

`config/world-map.json` lists the rooms that the walkthrough reference assigns
to each world. The table gives the strongest evidence in the record.

| World | Rooms | Strongest evidence | Missing |
| --- | ---: | --- | --- |
| 1 Grassland | 8 | 1-1 and 1-2 clear, room 106 chase clear, room 120 clear and save, room 138 audio and onward castle entry | Castle clear and boss integration (author unfinished). Room 138 secret exit and audible output. |
| 2 Forest | 9 | Resource and graphics restoration. Loading only. | Route, exit and save acceptance. Boss. |
| 3 Bay | 5 | Resource and graphics restoration. Loading only. | Route, exit and save acceptance. Boss. |
| 4 Cave | 9 | Resource and graphics restoration. Loading only. | Route, exit and save acceptance. Boss. |
| 5 Plateau | 9 | Resource and graphics restoration. Loading only. | Route, exit and save acceptance. Boss. |
| 6 Sky | 10 | Resource and graphics restoration. Loading only. | Route, exit and save acceptance. Boss. |
| 7 Snowfield | 9 | Resource and graphics restoration. Loading only. | Route, exit and save acceptance. Boss. |
| 8 Bowser Valley | 5 | Resource and graphics restoration. Loading only. | Route, exit and save acceptance. Endgame line. |
| Star World | 12 | Nine courses with route acceptance, both exits and save checks. | Center boss ending is an accepted exception. Unassisted traversals and two Dragon Coin sets stay open. |

The [Star World route reports](demo11-star1-route.md) use tracked scripts on
both hosts. The user verified the keyhole secret exits of Sky, Cave, Plains and
Bay in play.

## Entry routes

The survey and the route scripts use a map tile override or a pipe fixture.
The record qualifies real overworld routes only around the World 1 courses and
the star hub. The record holds no real map route for Worlds 2 to 8. A course entry
fixture does not qualify the map route that a player must walk.

## Bosses and special rooms

| Line | Evidence | Missing |
| --- | --- | --- |
| Seven Koopalings (room `0FF`, ending `17B`) | Entry, child actor, font cycle, fight music, ending boundary, hidden 1-up checkpoints | Earned victory and saved completion. Death timer `30` versus `2E`. The two hosts return to different map contexts. |
| mazo 9C (room `151`) | Entry, body samples, attack-window timing, phase music recipe (r12) | Phase music playtest, attack sequence, clear and save. |
| mazo 9B (room `190`) | Entry, actor count, background `1E5`, music override `9E` | Attack, clear and save. |
| Corridor (rooms `183`, `184`, `191`, `192`) | Module entry, invisible markers, orb, foreground, music | Japanese message font. Relocated exits of rooms `00D` and `10C`. |
| Room `0x8F` boss | User accepted the demoOnly1 record and code. | Nothing recorded. |
| HP bars (rooms `0xBC`, `0xCC`, `0x128`, `0x146`, `0xCF`) | Upload shim and captures. | Nothing recorded. |
| World castle bosses (`06E` to `072`) | One manual Lemmy report for World 1. | Per-castle entry, phase, exit and save acceptance for Worlds 2 to 8. |

## Sprite slots

The [gap inventory](native-sprite-gaps.md) counts 54 empty slots in the
recipient rooms.

| Group | Count | State |
| --- | ---: | --- |
| Type-1 record in a donor | 40 | A recipe exists for each slot. The product target mounts the records. |
| Type-3 record only | 3 | `C0` and `C1` run in the r13 product. The constructor contract is open. `C2` is out of the candidate and its restoration stays open. |
| No donor record | 11 | Needs a source review. |

The [type-3 review](native-sprite-type3.md) shows that the donor and recipient
constructors read different record layouts. The records-only install is safe.
The constructor patch crashed and stays an open experiment.

The per-sprite documents also leave a graphics review open for several records.

## Music

| Item | State |
| --- | --- |
| Room `151` phase songs `A5` and `AD` | The r12 recipe exists. Automation cannot damage the boss, so the phase change needs a playtest. |
| Room `106` course music | The user deferred the quality item. |
| Hub map BGM, Star-9 boss cue `98`, other worlds | Recorded open in the [Star BGM checkpoint](demo11-star-bgm.md). |
| Snow and upper-right tracks | Listed as not itemized in the [listening queue](audio-acceptance-queue.md). |

## Graphics

| Item | State |
| --- | --- |
| Japanese message font in rooms `191` and `192` | Open. |
| Empty graphics slots `0x27E` and `0x282` | Open. |
| Per-world visual parity | The [world repair plan](world-repair-plan.md) lists persistent candidates: World 5 room `10F`, Star rooms `004`, `007` and `009`, World 1 room `120`. Later graphics batches may change this list. Re-run `tools/world_parity.py` before scheduling. |

## Product and runtime

The target carries 45 packs, the 36-record sprite gap line, the type-3 records,
the mazo corridor and the Seven line. The r12 ROM equals the r10 ROM. The room
`151` phase music and the room `190` music are native adaptations.

The runtime now has a live cheat channel and a practice console. These tools
help playtests. They do not add acceptance evidence.

The record holds no full-game route from a new save, no ending save and no
post-ending restart check.

## Claims that the record does not support

| Claim | Reason |
| --- | --- |
| "Only music and a few textures remain." | Worlds 2 to 8 have no route, exit or save acceptance. The endgame line is open. |
| "All 255 courses are playable." | The survey proves loading. It does not prove a course clear. |
| "The Seven fight is complete." | No earned victory and no saved completion. |
| "The sprite restoration is complete." | 11 slots have no donor record. 3 type-3 slots have no working constructor. |
| "The game can be finished." | No full route, ending and save evidence exists. |

## Recommended order

1. Rerun the full-range survey on each product candidate. The r12 and r13
   runs are complete. See the [product survey](demo11-product-survey.md).
2. Restore the `C2` type-3 record correctly. Keep it out of the product until
   the constructor work succeeds. Translevel `094` stays in the survey.
3. Qualify the Worlds 2 to 8 routes in world order. Start with World 2. Reuse
   the star route method and add one tracked script for each course.
4. Close the Seven milestone. Prove an earned defeat, the map return and a
   saved completion without a forced fixture.
5. Close mazo. Qualify the attack, the clear and the save. Then playtest the
   room `151` phase music.
6. Inventory the World castle bosses `06E` to `072`. Qualify entry, phase,
   exit and save for each castle.
7. Decide the 11 no-donor sprite slots. Mark each slot as a deprecated
   placeholder or as missing content.
8. Repair the type-3 constructor register state, or keep `C2` out of the
   product.
9. Build one music ledger for each room and each phase. Add the Japanese font
   and the empty graphics slots to the same ledger.
10. Freeze a release candidate. Run one full route from a new save: map
    progression, branch exits, bosses, ending, exit and restart, save reload.

## Evidence index

| Document | Supports |
| --- | --- |
| [Course survey](demo11-course-survey.md) | 255 translevels load. No stalls. |
| [Product survey](demo11-product-survey.md) | Native load survey on r12 and r13. `C2` causes the level `094` crash in r12. |
| [World 2 route inventory](world2-route-inventory.md) | Parsed World 2 exits, goal tapes and the first fixture results. |
| [World repair plan](world-repair-plan.md) | Scene parity triage and detection tools. |
| [Star route reports](demo11-star1-route.md) | Route, exit and save acceptance for each star course. |
| [Seven entry](native-seven-entry.md), [child](native-seven-child.md), [music](native-seven-fight-music.md), [ending](native-seven-ending.md) | Seven program, child actor, music and ending boundary. |
| [mazo 9C](native-mazo-9c.md), [9B](native-mazo-9b.md), [attack window](native-mazo-attack-window.md), [corridor](native-mazo-b0.md) | mazo entry and timing. |
| [Corridor](native-corridor-invisible.md) | Rooms `151`, `190`, `191`, `192` graphics and music. |
| [Sprite gaps](native-sprite-gaps.md), [type-3](native-sprite-type3.md) | Empty slots and donor availability. |
| [Open issues](demo11-open-issues.md) | User-reported defects and dispositions. |
| [Playtesting](playtesting.md) | User acceptances and their scope. |
| [Listening queue](audio-acceptance-queue.md) | Deferred audio checks. |
| [Product target](native-full-product.md) | Pack list, records and merged-target checks. |
