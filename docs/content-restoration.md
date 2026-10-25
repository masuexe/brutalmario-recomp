# Content restoration and regression workflow

The user has accepted the 68-variant Demo 1-1 checkpoint and clarified the
long-term objective: retain Demo 1-1 or demoOnly1 as the engine/baseline and
restore unplayable content from other supplied versions where a complete,
playable donor exists. The user chose to compare the existing local versions
first. Official chronology and a latest complete release are not established.

## Priorities

### Current objective (2026-10-22)

Continue from the accepted demoOnly1-based cumulative restoration, currently
`world1-next-course` (descending from `star-world-forest`). Restore playable
World 1 routes and broken courses, then
selectively recover Demo 1-1 additions after identifying their object, sprite,
block, ASM and audio dependencies. Preserve accepted Star World content and
working recipient map routes/events in separate, reproducible descendant
targets. Automatically qualify and commit/push successful checkpoints; request
human playtesting only for essential questions that automation cannot resolve.
Sound is available again; earlier listening deferral is no longer a current
environment constraint. The full cross-version recovery remains incomplete.

This supersedes the earlier work priority of finishing the nine-star hub.

The current cumulative checkpoint is
[`world1-next-course`](world1-next-course-restoration.md), which includes the
[`room106 graphics recovery`](world1-room106-restoration.md). The user accepted
1-2 gameplay and room106 gameplay; room106 music remains incorrect and was
explicitly deferred. Automatic coverage now includes the assisted 1-2
room010 -> room04A -> room161 clear and onward room106 entry, plus
[room106's chase-Yoshi clear and real death/re-entry](world1-room106-flow.md).
The [room120 cave regression](world1-room120-regression.md) now covers natural
entry, five Dragon Coin pickups, normal clear and recipient File A persistence. Its
normal exit selects room138. The new isolated
[`world1-room138-audio` candidate](world1-room138-restoration.md) repairs its
missing-song Mario Start stall and preserves the original sample dependency;
entry, movement, assisted whole-course progression with a real tape clear,
onward castle entry, File A persistence, and real death/re-entry are
automatically checked on reference, native and cheap_demo. Room138's secret
exit and audible output stay open. Full onward connectivity and
selective Demo 1-1 recovery remain incomplete.

Content recovery now takes priority over increasing the AOT variant count.
The existing interpreter fallback lets investigation proceed without first
recompiling every routine. AOT work should address a demonstrated execution,
compatibility or performance need encountered during restoration, rather than
becoming a prerequisite for content work.

Keep the accepted Demo 1-1 and demoOnly1 ROMs, configurations, saves and
regression captures separate from restoration candidates. A pilot should use
an isolated target and reproducible content manifest. demoOnly1 is the first
recipient candidate to investigate because boss, shop and map flows have
already been exercised there; Demo 1-1 remains an engine/reference candidate.
This is a starting hypothesis, not a proven cross-version compatibility choice.
The first migration pilot should determine the recipient before a broad merge.

## Reduced manual checkpoints

The current cumulative recipient is the accepted `star-world-forest` target
on demoOnly1. Demo 1-1 remains separate and may supply selected additional
content. The [World 1 route audit](world1-route-audit.md) reproduces its
three-cell route restriction; preserve the recipient's map routes when
investigating Demo 1-1 content migration. Actual normal-exit route integration
remains pending.

The user authorizes automatic commits and pushes for completed checkpoints
once their required checks pass. Report the commit and verification results;
unresolved failures must remain explicit rather than being marked accepted.

The user has now authorized a continuous restoration loop: automatically
qualify, commit/push and advance through the remaining Star World courses.
New content alone does not require a user playtest. Ask for a targeted human
check only when essential behavior cannot be resolved automatically. Keep
automatic qualification distinct from user-reported acceptance.

Sound became available again with the accepted Sky Star playtest; the user
reports its heard audio is normal. Earlier unitemized listening checks remain
in the [audio queue](audio-acceptance-queue.md), without blocking progress.

Routine AOT transformations no longer require a separate user playtest or a
"continue" response after every function/batch. When applicable differential,
full-route, dense-transition, interpreter-floor, selected state/clock and PCM
checks pass, record the change as **automatically qualified** and continue
within the authorized scope. Preserve the last manually accepted baseline and
record every candidate's identity. Do not call automated qualification a new
manual acceptance.

Combine routine changes into milestone smoke checks. Request targeted human
validation for an essential unresolved experience question, a shared-runtime
change with an evidence gap, or an unexplained mismatch that automatic probes
cannot resolve. Audible output remains distinct
from generated PCM. A new opcode alone is not a reason for an extra manual
gate if the qualified behavior and integration are covered automatically.

The user need not complete a combined playthrough for each restored level.
The recent word-push ordering and post-SEP index
truncation defects were caught by automated probes before user playtesting;
this supports using those probes as the routine gate, not assuming future
changes cannot fail.

## Initial local version comparison

`config/content-versions.json` pins all nine supplied standalone IPS files,
the base body and their +512 patch-coordinate candidate outputs. The first
`tools/audit_content_versions.py --prepare-local-roms` run reproduced all nine
4 MiB candidates under `local/content-versions/`, without changing either
accepted target or any original input. The two baseline candidates match the
existing prepared ROMs byte for byte. Donor alignment is structurally plausible
but gameplay qualification remains pending.

| Version | Role in the first comparison | Existing evidence and limitation |
| --- | --- | --- |
| Demo 1-1 | Frozen recipient/reference candidate | One ordinary level is manually exercised; no Boss in this version. |
| demoOnly1 | First recipient candidate to investigate | Bounded ordinary-level, Boss, shop and map checks have passed; other content is not qualified. |
| demo6 / demo7 | Historical ordinary-level donor candidates | Local patches exist; completeness, chronology and per-level playability remain unverified. |
| cheap_demo | Ordinary/special-content donor candidate | Notes describe unfinished content and older-emulator dependencies; Bowser Castle is unfinished. |
| 7hero | Targeted Bowser Castle/Boss donor candidate | Notes describe a Boss test, blocked door and custom-sprite failures after overworld transitions. |
| mazo | Targeted final-dungeon midboss donor candidate | Notes describe unfinished difficulty balancing; not a complete-game donor claim. |
| demo8 | Separate unofficial composite donor candidate | Notes claim most stages playable, but exclude Bowser Castle and Athletic Special and mention replacement courses and known bugs. |
| ow | Overworld reference only | Its notes explicitly say it has no course data; exclude it as a level donor. |

Those readme statements are supplied documentation, not new gameplay results.
In particular, demo8's claim of broad playability does not establish that it
contains the intended original version of each course or supersedes all other
sources. The already exercised demoOnly1 Athletic Special content must not be
replaced merely because another archive has a larger version number.

For orientation only, whole-image differences from demoOnly1 are:

| Version | Different bytes at the same offset | Identical 32 KiB banks / 128 |
| --- | ---: | ---: |
| Demo 1-1 | 848,021 | 59 |
| 7hero | 1,579,442 | 36 |
| cheap_demo | 2,343,075 | 3 |
| mazo | 2,236,240 | 3 |
| ow | 2,200,259 | 3 |
| demo6 | 2,735,094 | 0 |
| demo7 | 2,721,922 | 0 |
| demo8 | 2,509,239 | 1 |

These are layout comparisons, not completeness or compatibility scores.
Relocating identical data can produce large byte differences. The baseline
SRAM header exponent is 5; the other candidates use 1, another reason to keep
saves/version state isolated. No room mapping, dependency closure or gameplay
has been inferred from these global measurements.

## Distinguish the failure before restoring a room

Build a room/course matrix with separate observations for the unmodified
recipient, the unmodified donor and the native restoration candidate. Record
ROM/core identity, overworld entrance, room and exit chain, observed failure,
reference captures and confidence. Matching room numbers alone do not prove
two courses correspond.

A Mario Start hang or scrambled geometry can indicate absent/unfinished data,
incorrect entrance or resource selection, dependencies from another engine
version, or a runtime compatibility defect. It is not enough to classify all
such slots as deleted courses. Donor notes explicitly document core-specific
failures; failure in the modern Snes9x reference alone does not prove content
is absent. Preserve the user's ZSNES 1.51 historical reference and label any
new reference-core limitation instead of substituting it for a donor verdict.

If the same recipient ROM fails in its reference environment, classify the
original defect before modifying native execution. If a donor room is complete
but the native version differs, isolate that execution or loader difference.
If no supplied donor has a complete room, mark it missing/reconstruction work
rather than claiming a faithful recovery from unavailable data.

## Migrate a dependency-complete pilot

Prefer an enterable but damaged ordinary course for the first pilot when a
complete donor and a clear room mapping are available. Its live initialization,
geometry, collision and object state provide useful comparison points. Entry
alone does not imply that its dependencies are simple or mostly intact.

Give Mario Start hangs a short initial diagnosis as well. A shared loader or
initialization defect affecting several otherwise complete courses takes
priority over an individual transplant. An absent or unfinished original room
does not become the first repair target solely because it hangs at entry.
Verified donor completeness and a bounded dependency set determine priority;
visible severity is a secondary signal.

The first pilot should be one complete ordinary course whose donor can be
verified, with a clear recipient slot and few special dependencies. Qualify
all its connected subrooms, entrances, exits, completion and return to the map.
Do not start by bulk-copying every pointer or assembling all Boss releases.

A migration manifest should identify each component and its source/version:
layout and exits; graphics, palettes and tile/collision definitions; sprites
and blocks plus their ID remapping; level scripts and hard-coded addresses;
music/animation/HDMA where used; and completion/DK/save integration. The source
packages already assign sprite ID $0F to different actors (nova versus
starship), so identical numeric IDs cannot be assumed to mean identical
resources or behavior. Complete source-to-ROM correspondence remains unproven.

Restore the recipient's course with its required data and code adaptations.
Preserve existing recipient behavior outside that dependency set. Keep original
IPS files separate; applying historical patches on top of each other is not
a migration recipe. Use a reproducible isolated ROM/asset change first, verify
it in a suitable reference environment, then regenerate native code against
that candidate's actual identity. This avoids replacing the runtime's resource
loaders before one end-to-end migration has demonstrated the needed format.

For intentional content changes, old scene hashes are no longer the expected
result for the modified room. Compare that room against the verified donor
behavior and the documented adaptations, and retain the old regression routes
for unaffected content. Review expected differences explicitly before recording
new baselines; do not accept every changed capture by updating hashes.

A pilot is complete when it loads, displays coherent geometry/graphics, has
correct collisions and objects, traverses every included pipe/door, supports
death/re-entry, exits to the correct map state, preserves the intended DK and
completion behavior, and has the expected sound. Automate repeatable routes;
ask the user for one consolidated playthrough at that milestone. This is the
next substantive acceptance target, rather than another AOT count increment.

## Reproduction and current boundary

```sh
python3 tools/audit_content_versions.py --prepare-local-roms
python3 -m unittest discover -s tests -p test_prepare_rom.py -v
```

The three existing ROM-preparation tests pass. All nine candidates verify their
pinned patch and output hashes; the two baseline copies match the accepted
target files. Repeating preparation verifies existing copies and refuses to
overwrite conflicting ROMs. Metadata reports live in
`local/reports/content-versions.json`; original inputs remain untouched.

The initial identity/readme/layout comparison is complete. The user selected
the lower-left course in the nine-star hub as the first pilot. Its entrance is
demoOnly1 map 6 / `$0128,$01E8`, room `$005` in an uncleared save. A bounded
[Star World candidate](star-world-1-restoration.md) now restores three missing
graphics streams from cheap_demo, using IDs referenced only by that room.
Opening/death/re-entry, normal goal, keyhole and resulting World 1 warp have
automated evidence. This is an actual isolated ROM/native build. The user
reports testing broadly matches the original. The first specific concern,
[LOVE ANIMAL fireball respawning](star-world-1-animal.md), was reproduced in
both versions and closed by the user as explained original behavior; no
gameplay patch was requested. Other unspecified issues remain unclassified.
Individual full-course and sound coverage was not specified. Other courses
and donor versions remain unqualified.

The [first-course closeout and nine-star survey](star-hub-survey.md) found no
loaded Dragon Coin placement in the first course's four examined rooms in either
version; pickup is not applicable to that path, rather than a fabricated pass.
Actual normal-clear progress survives saving, native cold restart and console
reset/File A reload. This uncovered and fixed a missing native hardware-reset
callback. The 20 unchanged-entry scene samples remain byte-identical; all 92
tests pass. Nonzero Dragon Coin persistence is still unqualified by this course.

All nine uncleared hub entrances now have bounded original/native/donor
observations. The [upper-left cave candidate](star-world-upper-left-restoration.md)
(`$004`, map 6 / `$0128,$0168`) now builds cumulatively on the lower-left
repair. It restores missing ExGFX `$144` and custom sprite `$7A`, whose absent
water/platform behavior was found after the graphics-only prototype. All 99
project tests pass. Five real DK pickups, their nonzero saved bit, normal
clear, console reset/File A reload, water interactions, both examined cave
pipes and death/re-entry pass bounded native/reference checks. The 28 shared
lower-left/shop/Boss-door scene samples retain identical full WRAM and raw
framebuffers. The user subsequently accepted this restoration milestone,
confirming normal custom-sprite loading and removal of the original damaged
regions. The report does not separately itemize full traversal or sound;
acceptance does not expand those coverage claims. This cumulative target is
now the accepted restoration baseline. Routine diagnostics need no additional
manual gate.

The [Snow Star lower-right candidate](star-world-lower-right-restoration.md)
(`$008`, map 6 / `$01C8,$01E8`) now builds on that accepted baseline.
The MARIO START stall is an SPC upload waiting on the missing `$54` music
pointer; restoring ExGFX `$1B3` alone does not fix it. The candidate adapts
the donor's actual song to the recipient driver, adds the graphics and
restores shared missing ice Ptooie `$57`. Existing penguins, Santa, slots,
layout and exit rules are retained.

Five actual DK pickups, a real end-wall transfer to `$026`, timed slot jumps,
normal goal, key/keyhole secret, Warp Star, death/re-entry and normal-clear/DK
save/reload pass automated checks. Donor slot/goal and secret probes succeed,
while their different completion flags remain documented. All 105 tests and
191 selected local assertions pass, and 36 accepted route scene samples
remain byte-identical. Native song memory matches the adapted payload and
native/reference audio stays non-silent. The user subsequently tested both
normal and key exits without issues and authorized continuing. Snow Star is
now the accepted cumulative gameplay baseline, `star-world-lower-right`.
Audio was not separately itemized and remains in the listening queue.

The [upper-right candidate](star-world-upper-right-restoration.md) (`$002`,
map 6 / `$01C8,$0168`) now restores missing song `$5D` from the second entry
of a cheap_demo four-song group. Only the music pointer and its new RATS
block change; graphics, layout, sprites, exits and runtime remain intact.
Entry, real upward pipe/normal goal, five Dragon Coin pickups and reset/save/re-entry,
and death pass in both hosts. All 108 tests and 242 selected assertions pass;
60 earlier full-WRAM/raw-framebuffer samples remain identical. Automated
audio data checks pass, with human listening deferred. The user confirmed
normal entry and SMB3 brick behavior, then explicitly waived a complete manual
run because of the course length. They accepted this stage using those
observations plus the automated route/save checks. `star-world-upper-right`
is now the accepted cumulative baseline; full manual traversal and listening
remain unconfirmed. Continue with the middle-right loading stall (`$009`,
map 6 / `$0198,$01A8`) under the existing automated-checkpoint workflow.

The [middle-right dependency investigation](star-world-middle-right-investigation.md)
isolates missing ExGFX `$190/$193` and a null `$2E` music pointer.
Graphics-only still stalls; an explicitly temporary existing-song substitution
reaches active play but corrupts 4,863 low Map16 bytes; combining both keeps
the sampled buffer intact. The in-progress candidate restores the real `$2E` intro/loop song, those two
graphics streams, custom sprites `$17/$28`, and the same graphics on screen-2
destination `$09B`. Reference entry and a diagnostic `$09B` load keep low
Map16 intact, and the rocket renders. A ridden left-page climb now reaches
the rocket finish at Mario Y `$02B0`, walks into the screen-2 door, and
touches the `$09B` goal tape. The guest returns to the overworld with
translevel `$09` flagged `$8C` in WRAM and SRAM, and that flag survives
reset and File A load. The same samples match on the recreated native build, and the launcher
accepts this ROM. A time-over in both hosts drops one life, returns to the
hub, and allows a fresh entry. The two upper Dragon Coins are on opposite sides
of a wall and do not both fit one climb. The secret exit remains open.
The user subsequently tested Sky Star without finding problems and reported
that sound is available again and its audio is normal. The
[middle-right restoration report](star-world-middle-right-restoration.md)
records stage acceptance and the new cumulative baseline. Secret completion
and all-five-Dragon-Coin coverage remain unconfirmed.

The center star (`$00A`, room `$079`) has no reachable victory store. Its
phase-2 boss program never writes the level-end timer, and the donor sprite
block is unchanged. That undefined ending is preserved as an accepted exception
rather than patched; see [the center report](star-world-center-restoration.md).
This does not upgrade any other unconfirmed item listed above.
The [center damage regression](center-damage-regression.md) records a
rolled-back recipe edit that made powered Mario die instead of shrinking;
the [cannon comparison](center-cannon-flight.md) reproduces the directional-input
distinction in ZSNES 1.51 and qualifies a controlled DK flight on both hosts.
The [current cumulative center candidate](star-world-center-restoration.md)
also includes all eight qualified surrounding courses. Its Boss ending is
an accepted exception: the donor's unfinished ending is preserved as-is, no
clear condition was authored, and no document may claim a center clear.

The upper-inner cave (`$007`, map 6 / `$0178,$0188`) is the next cumulative candidate on the Sky
Star ROM. Its recipe restores the six missing ExGFX streams and custom
sprites `$15`, `$45`, and `$50`. `star-world-upper-inner-goal.script` rides
the coaster, stomps the Koopas, and touches the goal tape. Both hosts return
to the hub in mode `$0E` with `$13CE=1` and translevel `$07` flagged `$81`
in WRAM and both SRAM copies; File A reload keeps `$81`. Two frame-counter
pokes after the map tile poke keep native on the same phase as reference.
Death and DK coverage are not part of this checkpoint. The stage is
automatically qualified.

Middle-left (`$003`, map 6 / `$0158,$01A8`) had the same empty layer-1
problem. `star-world-middle-left` installs the donor object stream on the
cave ROM. `star-world-middle-left-goal.script` swims the water course and
jumps into the goal tape at X `$0CA0`. Both hosts return to the hub in
mode `$0E` at `$010E,$012E` with `$13CE=1` and translevel `$03` flagged
`$8C` in WRAM. Both SRAM copies store `$8C` (`$0003` and `$01B0`), and
File A reload keeps `$8C` with 4 lives. The overworld life total before
reload is 5 on reference and 8 on native; the saved clear matches. Death
and DK coverage are not part of this checkpoint. The stage is
automatically qualified. A new manual gate is not required.

The subsequent [middle-left identity investigation](star-world-middle-left-identity.md)
confirms that cheap_demo room `$003` duplicates World 1 water room `$120`:
terrain and all 34 sprite placements match after normalizing record order.
Its existing qualification therefore covers the copied donor water course,
not a distinct original forest course. demo6/demo7 retain different forest
data with 14 sprite records. The subsequent
[independent Forest Star candidate](star-world-forest-restoration.md) uses
demo8's retained forest data and is separately qualified for parrot flight,
projectile/enemy collision, both saved exits, Warp Star transfer and
death/reentry on reference and native hosts. It is launched as
`--restoration star-world-forest`; the water and center targets stay available.
Its music uses the existing recipient arrangement and has not received a new
manual listening acceptance.

The [lower-inner restoration](star-world-lower-inner-restoration.md) now
restores the missing warp-star actors and 100-coin controller in `$117`.
The geometry and sprite placements already match cheap_demo. Actual-input
movement passes the former wall; a separate player/camera-assisted pickup
fixture triggers the existing 100-coin exit and retains flag `$8F` in both
SRAM copies after reset and File A load on both hosts. All 239 previous
native WRAM/framebuffer samples remain exact. An unassisted complete route,
DK coverage and death/re-entry are not qualified by this checkpoint.

The subsequent [lower-inner music correction](lower-inner-music.md) uses
existing recipient songs `$60` (course/expiry) and `$79` (caps). Donor
`$21/$22` are local selections within an uploaded four-song bank, so global
song numbers and matching backgrounds were insufficient evidence. On
2026-10-21 the user confirmed that the corrected music is completely normal,
closing the scoped listening check.

## Demo 1-1 rebase (2026-10-23)

The user chose to change the restoration base from demoOnly1 to Demo 1-1 rather than
reverse-engineer Demo 1-1's custom sprite mechanism. The newer 1-1 and castle are
native on that base, so the World 1-1 layout migration attempt (which stalled because
the newer course needs its own sprite behaviour) became unnecessary.

New chain: `demo11-base` -> `demo11-room106` -> `demo11-room010-gfx` ->
`demo11-room010-music` -> `demo11-room138-audio` -> `demo11-room0cb-gfx` (head,
`9155c1eb…`). Recoveries ported: room 106 graphics `1A2`, room 010 graphics
`151`/`102`, room 010 song `2F`, room 138 private song `7E` with its sample-bank
selector, and the shared graphics `12A`. Custom sprites `8D` and `0B` are **not**
ported; Demo 1-1 supplies working equivalents.

Verification is consolidated in `tools/check_demo11_line.py`, which currently reports
**10/10**:

- the five recoveries, each with its own pinned qualifier;
- World 1 route parity (eight demoOnly1-era routes replayed on both hosts);
- six original engine flows (boss death and phases, repeated death, shop, boss door,
  Lemmy mask);
- a whole-line byte audit: 8,214 changed bytes against the pinned Demo 1-1 input, all
  inside the chain's 15,878 declared region bytes, zero unexpected;
- a reachability audit: only the intended differing rooms (`0C5` intro, `0C7` map,
  `105` newer 1-1, `10E` newer castle) were ever entered, and any future capture that
  enters another differing room fails acceptance;
- World 1-1 goal and clear: the newer course places its goal on the far-right end
  platform (`x≈0x16DC`, `y=0x140`); touching it produces map state `0x8A` and event
  `0x01` on both hosts, the same overworld event the demoOnly1 line produced.

Deferred: the user's playtest and listening acceptance (checklist in
[demo11-playtest.md](demo11-playtest.md)); and the scripted room 010 pipe route, which
fails on this base because version-level tables differ (room data is identical), and
therefore needs a real playthrough to decide. The former map-cursor gap is closed:

The user playtested 1-1, 1-2 (full natural clear) and room 138 on 2026-10-24, and
custom sprites `8D`/`0B` were then ported, advancing the chain through
`demo11-sprite8d` -> `demo11-sprite0b` (11/11). The subsequent
[World 1 route repair](world1-overworld-route-repair.md) restores the three
route-enable cells around the 1-1 map node that original Demo 1-1 zeroes; the
real clear event now walks the player to the 1-2 node and the normal entry
button opens room `$010` on both hosts. Head is `demo11-world1-route`
(`5265a7bd…`), acceptance 12/12 at that point; the user playtested and
confirmed the map route is fixed on 2026-10-24. The subsequent
[room106 music fix](world1-room106-music-investigation.md) steers the
room106 course's level-default request (node `(0x58,0x1D8)`, internal room
`$0106`) to native slot `0x33`, chosen by the user through a generated
audition library, while the room120 course (node `(0x88,0x1F8)`) keeps its
user-confirmed original `0x49` music; head is now `demo11-room106-music`
(`22229d65…`), acceptance **13/13**.

The demoOnly1 line remains available and untouched; `docs/rollback.md` documents both
rollback routes and the pre-rebase snapshot. The full rebase plan, with the evidence
and risk list, is [demo11-rebase-plan.md](demo11-rebase-plan.md).

The subsequent [castle sprite-06 repair](world1-castle-investigation.md) corrects the
castle survey - the "missing F0 sprite" was a runtime-table misreading; F0 spawns and
renders natively at level x `$360` - and restores the actually missing lineage-shared
custom sprite `06` at the castle opening (`x=$B0`) from cheap_demo's block (byte-identical
in demo8), the same record-port pattern as `8D`/`0B`. Head is now
`demo11-castle-sprite06` (`4328e78c...`), acceptance **14/14**. The user clarified the
newer castle is most likely author-unfinished: restore-as-much-as-possible is the goal,
and course completion/boss integration is explicitly not required. The far-right door
(x `$10EA`) is recorded as an unentered observation.

The
[castle sprite 06 port](world1-castle-audit.md) and the room106-music head
followed; the user then directed work to the Star World convergence: the
[Star World lower-left graphics recovery](star-world-1-restoration.md) shape
(renumbered ids FFD/FFE/FFF) now ports onto the Demo 1-1 line as
`demo11-star1-gfx`, with both hosts entering room `$005` and rendering the
terrain (acceptance **15/15**). The remaining Star World graphics follow as one shared-pointer batch
(`demo11-star-gfx-batch`, acceptance **16/16**): sixteen streams covering
upper-left/snow/sky/center/upper-inner/lower-inner, with upper-left (room
`$004`) verified rendering on both hosts. The follow-up music recovery
(`demo11-star-music`) ports the accepted song 54 and 2E sequences: snow and
sky pass the Mario Start loader with audible tracks on both hosts (the
practice save carries clear flags, so those nodes play the Warp Star branch
after load), upper-inner and lower-inner load with their native song slots,
and the center node behaves the same way. The first sprite-slot audit incorrectly treated default records as populated;
the later sprite recovery and allocation correction below supersede that finding. Remaining open:
per-course traversal, enemies, platforms and clear behaviour - the same
per-course qualification depth the demoOnly1 line applied.


### Safe Star World sprite checkpoint (2026-10-24)

The subsequent `demo11-star-music-2` restores upper-right song `$5D`. The
`demo11-star-sprites` artifact then attempted eleven sprite ports, but review
found seven allocations overwriting occupied recipient data and three entry
pointer pairs outside their moved blocks. Its frozen **18/18** checks did not
cover those defects, and its whole-line audit stopped two targets earlier.
The historical ROM and captures remain intact for diagnosis.

Current cumulative head is **`demo11-star-sprites-safe`**, derived directly
from the intact `demo11-star-music-2` parent. All eleven sprite blocks use
checked empty allocations with unchanged low addresses and adapted entry
banks. The [safe sprite report](demo11-star-sprites-safe.md) records the
correction, identities and evidence. The music and historical sprite recipes
now reproduce their existing ROMs exactly. The ancestry-derived audit also
rebuilds all 16 safe-chain recipes; 58,498 changed bytes against Demo 1-1 lie
inside declared regions, zero unexpected. Integrated checks pass **19/19**.

Both hosts exercise six course entries, the upper-inner real tape clear with
both SRAM copies and reset/File A persistence, and lower-inner actual-input
warp-star progression matching the qualified demoOnly1 predecessor within
8 pixels. This does not qualify all nine courses. The center map node loads
room `$000` on both safe hosts and the intact parent reference; center entry
mapping is the next concrete investigation. Per-sprite interactions, other
full routes, Dragon Coin/death coverage and scoped listening remain open. No new human
acceptance or center clear is claimed.


### Demo 1-1 lower-inner cap music follow-up (2026-10-24)

The user reproduced the cap-expiry freeze and reaffirmed course song `$60`
and cap song `$79`. The [lower-inner music descendant](demo11-lower-inner-music.md)
ports the previously accepted selection adaptation onto the safe Demo 1-1
controller at `$3A:8000`. The parent requests absent global `$21` at expiry;
complete WRAM freezes on both hosts. Exactly seven selection bytes now select
`$60` for the course and final expiry and `$79` for all three pickups.

Current cumulative head is **`demo11-lower-inner-music`** (`10f8af33…`).
All three cap effects activate and expire naturally on both corrected hosts,
which keep advancing afterward. Native SPC snapshots match the actual `$79`
and `$60` payloads; those complete uploads are identical to the earlier
user-confirmed demoOnly1 correction. The warp-star route remains qualified
as a segment on both hosts. Whole-line recipe replay now covers 17 targets,
zero unexpected bytes, and integrated checks pass **20/20**. No new human
listening acceptance or full-course clear is inferred. Center entry mapping
and the remaining broader restoration scope stay open.


### Star World visual follow-up (2026-10-24)

The user tested `demo11-lower-inner-music` and reported no issues, accepting
that cap-expiry/music checkpoint. They then requested lower-left secret-room
colors, the sky fuel gauge and flame's right corner, and Snow Star Santa.
The [visual recovery report](demo11-star-visuals.md) records all four fixes.

Current cumulative head is **`demo11-star-visuals-flame`** (`9f4add87…`), through
`demo11-star-visuals`. The secret room's palette was already correct; its
version-local `$B2` artwork differed. A private graphic restores its intended
appearance. A room009-only NMI addition displays the existing fuel buffer,
and four removed OAM increments restore the second flame tile's 16x16 size.
The missing `$09` record now supports real slot-game Santa/reindeer generation
and the real keyhole clear on both hosts.

Both flame animations, dynamic fuel depletion, loaded secret-room graphics
and palette, Santa fly-in/secret reward, sky normal clear/save/reload and the
accepted cap-expiry regression pass on reference and native. Integrated checks
pass **21/21**; all 19 recipes reproduce with zero unexpected changed bytes.
The new visual milestone is automatically qualified, not a new user acceptance.
The sky secret, other full-course/Dragon Coin/death coverage and the broader restoration
remain open.


### Demo 1-1 center warp-star route (2026-10-24)

The user reported that the route from the lower-inner node to the center special
warp star is damaged and that the center star display stays dark. The
[center route report](demo11-center-route.md) records the repair.

Current cumulative head is **`demo11-center-route`** (`917eb515…`), through
`demo11-star-visuals-flame`. Demo 1-1 stores the center map cell empty: map16
tile `$00` and level assignment `$00`. The recipe restores the donor pair
`$5A/$0A`, re-encodes the recipient level map as a private literal-only stream,
and moves only the loader pointer. No other decoded map byte changes.

Both hosts reach the center node with real Up input, show the animated
special-warp-star display, and load room `$00A` with translevel `$00A`. A
demoOnly1 control matches the route bytes, and its loaded center-course frame is
byte-identical. Integrated checks pass **22/22**; the byte audit rebuilds 20
recipes with 64,137 changed bytes inside 90,919 declared region bytes, zero
unexpected. The center course keeps its accepted unfinished boss ending. The
assisted course exit, other full-course/Dragon Coin/death coverage, the sky secret and
the broader restoration remain open.


### Demo 1-1 middle-left Forest Star (2026-10-24)

The user accepted the center warp-star checkpoint and asked to restore the map-6
middle-left course to the old build's Forest Star. The
[forest port report](demo11-star-forest.md) records the change.

Current cumulative head is **`demo11-star-forest`** (`4a4928f1…`), through
`demo11-center-route`. Demo 1-1 stores the short terrain stub in room `$003`.
The recipe installs the accepted demoOnly1 forest donor data: room `$003`
Layer 1 and Layer 2, sprite list and palettes, goal room `$04E`, three
isolated ExGFX streams, the parrot/projectile/vine sprite blocks and a
room-scoped private Map16 bank with scoped lookup shims. Recipient sites are
re-derived: the private bank moves to `$41:8000`, the shims to `$49:E908`,
the sprite records to the Demo 1-1 table at `$31:8D72`, and the hooks point
to the new shims. The room settings byte `$05:DE03` returns to the dry value
`$00`.

Reference and native runs qualify entry, live parrot and projectile, both vine
enemies defeated by real shots, the normal goal room `$04E` with save `$8C`,
the secret save `$8E` and portal, and death/re-entry. Fresh demoOnly1-line
captures have identical route values, and the loaded course buffers are
byte-identical. Integrated checks pass **23/23**; the byte audit rebuilds 21
recipes with 105,056 changed bytes inside 139,242 declared region bytes, zero
unexpected. The center Boss ending, the sky secret, other full-course/DK/death
coverage and the broader restoration remain open.


### Demo 1-1 exact map-node BGM dispatch (2026-10-24)

The forest checkpoint's music trace showed the middle-left node playing slot
`0x33` instead of the forest donor track `0x5D`. The accepted room106 music
fix had compared only the 8-bit low byte of map-node X `$1F17`; the middle-left
node at X `$0158` also matched `$58`. The
[dispatch report](demo11-node-music.md) records the correction.

Current cumulative head is **`demo11-node-music`** (`77a4b7a9…`), through
`demo11-star-forest`. A private shim compares the full map-node X word against
`#$0058` and returns to the original dispatch. Only 38 bytes change: the
relocated jump and a 25-byte shim in a checked empty block. The room106 node
keeps its user-auditioned slot `0x33`; the room120 node keeps `0x49`; the
forest node now requests `0x5D` and its native ARAM matches the accepted
demoOnly1-line forest payload.

Both hosts pass the forest entry/movement and both room nodes. Integrated checks
pass **24/24**; the byte audit rebuilds 22 recipes with 105,084 changed bytes
inside 139,275 declared region bytes, zero unexpected. The room106 song choice
is unchanged, and no new listening acceptance is requested. The center Boss
ending, the sky secret, other full-course/Dragon Coin/death coverage and the broader
restoration remain open.


### Demo 1-1 lower-left Star World route acceptance (2026-10-24)

The systematic Star World route acceptance starts with the lower-left course.
The [lower-left route report](demo11-star1-route.md) records it. No ROM changed;
this is a qualification checkpoint on `demo11-node-music` (`77a4b7a9…`).

The tracked `star-world-1-*.script` routes pass on reference and native: entry
and ordinary movement, a real fall/death/re-entry, the real normal goal with
save `$89` in WRAM and both SRAM copies plus console-reset reload, the real
keyhole secret exit with save `$8B` and the World 1 Warp Star, and the
`$048`→`$051` side exit. Fresh demoOnly1-line captures match in every semantic
field; only moving positions differ, within animation tolerance.

Integrated checks pass **25/25**; the byte audit is unchanged (22 recipes,
105,084 changed bytes inside 139,275 declared region bytes, zero unexpected).
The sky secret, the remaining Star World course routes, Dragon Coin/death coverage and
the broader restoration remain open.


### Demo 1-1 Star World course BGM (2026-10-25)

The user asked to correct the Star World course music with the Brutal Mario
wiki. The [Star World BGM report](demo11-star-bgm.md) records the finding and
the repair.

The recipient star data came from the legacy demo family and still stored
legacy BGM numbers. The wiki Star Road table gives the songs; the
[music mapping table](music-mapping.md) gives the new-family slot IDs. Six
one-byte level-data music parameters move to the intended slots: Grassland 38,
Bay 49, Cave 51, Plains 32, Sky 58 and Special Warp 7A. Snow already requested
the restored Jingle Bells slot 54, and Valley already requested 60 with its cap
cue 79.

Forest Star keeps the accepted demoOnly1-line substitute. The wiki lists
vanilla BGM 02, but demo 1-1 has no custom upload for it, and a request of 02
stalls the level load.

Both hosts request the intended slot on every course. The native build shows the
intended `$0DDA` in the loaded course, and its APU RAM holds the matching
upload body. Integrated checks pass **26/26**; the byte audit rebuilds 23
recipes with 105,090 changed bytes inside 139,297 declared region bytes, zero
unexpected. The hub map BGM, the Star-9 boss cue 98, other worlds and the
remaining route/death coverage stay open.


### Demo 1-1 upper-left Bay Star route acceptance (2026-10-25)

The [upper-left route report](demo11-star-upper-left-route.md) records the next
qualification checkpoint. No ROM changed; the head stays `demo11-star-bgm`.

The tracked upper-left scripts pass on reference and native: entry and ordinary
controls, the low-Map16 graphics guard, real B presses that swim upward, a real
platform contact that changes the water target from `$0CB0` to `$0C90`, five
real Dragon Coins with the coin-5 saved bit, the screen-8 pipe to the real goal
room `$048` and save flag `$85`, console-reset reload, the alternate-pipe side
exit through `$051`, and a real death/re-entry.

Fresh demoOnly1-line captures match in every semantic field; the native build
matches the reference exactly. Integrated checks pass **27/27**; the byte audit
is unchanged (23 recipes, 105,090 changed bytes inside 139,297 declared region
bytes, zero unexpected).

The Bay keyhole secret exit is user-verified. The user play-tested the
course: all Dragon Coins are collectable, the normal exit is reachable, the key
comes from the upper-right question block at the start, and the keyhole sits
next to the normal-exit pipe. The user considers the Bay Star test passed. With
this, all four remaining Star World secret exits are user-verified: Sky, Cave,
Plains and Bay. Remaining open items are the unassisted traversals, Dragon Coin
and death coverage where missing, the center Boss exception and the broader
restoration.


### Community walkthrough and route references (2026-10-25)

To aid automated route construction and avoid treating intended level puzzles as
emulation defects, community walkthrough resources and stage mechanics are documented
in [walkthrough reference](walkthrough-reference.md). Consult the English Brutal Mario
Wiki (https://brutalmario.fandom.com/) and the Japanese Kitiku Mario Wiki
(https://wikiwiki.jp/kitikumario/) when investigating stage progression, custom gimmicks,
and secret exits.


### Demo 1-1 upper-right Plains Star route acceptance (2026-10-25)

The [upper-right route report](demo11-star-upper-right-route.md) records the
next qualification checkpoint. No ROM changed; the head stays
`demo11-star-bgm`.

The tracked upper-right scripts pass on reference and native: entry and
ordinary controls, the low-Map16 graphics guard, five real Dragon Coins with the
coin-5 saved bit, the real upward pipe to goal room `$048` and save flag
`$86` with console-reset reload, and a real death/re-entry. The reference
requests the wiki-correct Plains Star slot `32`; the old legacy `5D` request
is absent.

Native and reference match on every checked field; only the entry jump phase
differs by 16 pixels. Fresh demoOnly1-line captures match on the route
positions. Integrated checks pass **28/28**; the byte audit is unchanged
(23 recipes, 105,090 changed bytes inside 139,297 declared region bytes, zero
unexpected).

The Plains Star keyhole secret exit is user-verified. The user completed the
hidden-exit verification in play. Automated secret testing stopped at the
user's request. The recorded wiki route is: find the backward-animated brick
near the top right, take its P-Switch, go down, press the switch to convert
the bricks, and fall to the key and keyhole.
Remaining Star World routes, the secret exits, unassisted traversals, the
center Boss exception and the broader restoration stay open.


### Demo 1-1 lower-right Snow Star route acceptance (2026-10-25)

The [lower-right route report](demo11-star-lower-right-route.md) records the
next qualification checkpoint. No ROM changed; the head stays
`demo11-star-bgm`.

The tracked lower-right scripts pass on reference and native: entry and
ordinary controls with the low-Map16 guard, the loaded ice Ptooie (`$57`) and
penguin (`$58`) sprites, five real Dragon Coins with counter and completion-bit checks,
the real end wall into room `$026`, the three-symbol goal-point match and the
real goal sphere, normal clear flag `$8A` with console-reset reload, the real
Santa reward key/keyhole secret with flag `$8B` and the map-0 Warp Star, and a
real death/re-entry.

The reference requests the restored Snow Star slot `54`. Native and reference
match on every route state field, and the demoOnly1 line matches except for
pre-entry menu samples. Integrated checks pass **29/29**; the byte audit is
unchanged (23 recipes, 105,090 changed bytes inside 139,297 declared region
bytes, zero unexpected).

Unassisted full traversal and listening acceptance are not claimed. The
remaining Star World routes, the unassisted traversals, the center Boss
exception and the broader restoration stay open.


### Demo 1-1 lower-inner Valley Star route acceptance (2026-10-25)

The [lower-inner route report](demo11-star-lower-inner-route.md) records the
next qualification checkpoint. No ROM changed; the head stays
`demo11-star-bgm`.

The tracked lower-inner scripts pass on reference and native: a real-input
traversal past the former `$0522` wall and through the warp-star chain, the
real 100-coin controller with coin rollover, the extra life, the ending timer
and `$141C=1`, the overworld return with flag `$1EDD=$8F` and
`SRAM[$3B]/[$1E8]=$8F`, console-reset File A reload, and a real
pit/death/re-entry. The restored custom slots `$30` (caps and 100-coin
controller) and `$37` (warp-star movement) are exercised; the cap music stays
pinned by the separate lower-inner music qualifier.

Native and reference differ only in traversal position phase (at most 3
pixels in X and 2 in Y); goal and death samples match exactly. Fresh
demoOnly1-line captures match every route sample. Integrated checks pass
**30/30**; the byte audit is unchanged (23 recipes, 105,090 changed bytes
inside 139,297 declared region bytes, zero unexpected).

An unassisted 100-coin route is not claimed. The remaining Star World routes,
the own-route traversals, the center Boss exception and the broader
restoration stay open.


### Demo 1-1 upper-inner Cave Star route acceptance (2026-10-25)

The [upper-inner route report](demo11-star-upper-inner-route.md) records the
next qualification checkpoint. No ROM changed; the head stays
`demo11-star-bgm`.

The tracked upper-inner scripts pass on reference and native: entry with the
player X high byte at 1 and 3, the coaster finish with `$13CE=1`,
the normal clear flag `$1EA9=$81` with `SRAM[7]/[$1B4]=$81`, File A reload,
the low-Map16 guard, and real pit/death/re-entry. The reference requests the
wiki-correct Cave Star slot `51`.

The goal and death samples match exactly between hosts. The entry coaster has
a one-frame host phase difference, so the check compares mode, room and player
X high byte there. Fresh demoOnly1-line captures match every route sample.
Integrated checks pass **31/31**; the byte audit is unchanged (23 recipes,
105,090 changed bytes inside 139,297 declared region bytes, zero unexpected).

The secret branch is user-verified. The user play-tested the course and
opened the hidden exit, which unlocked the Warp Star. Automated secret testing
stopped at the user's request. The [secret-layout note](star-world-secret-layouts.md)
records the parsed second goal sprite at X=`$1250` and the low-path stall at
X=`$1026`. The remaining secret branches, unassisted traversals, the center
Boss exception and the broader restoration stay open.


### Demo 1-1 middle-right Sky Star route acceptance (2026-10-25)

The [middle-right route report](demo11-star-middle-right-route.md) records the
next qualification checkpoint. No ROM changed; the head stays
`demo11-star-bgm`.

The tracked middle-right scripts pass on reference and native: entry with the
rocket fuel load `$0B` and the low-Map16 guard, the fuel consumption, the real
rocket finish with coins 4 and fuel 0, the top door and goal room `$09B`, the
normal clear flag `$1EAB=$8C` with `SRAM[9]/[$1B6]=$8C` and File A reload,
and real fall/death/re-entry. The reference requests the wiki-correct Sky Star
slot `58`.

Native and reference match on every route field, and fresh demoOnly1-line
captures match every route sample. Integrated checks pass **32/32**; the byte
audit is unchanged (23 recipes, 105,090 changed bytes inside 139,297 declared
region bytes, zero unexpected).

The normal exit is qualified. The secret exit stays user-verified and
deferred. The remaining secret branches, unassisted traversals, the center
Boss exception and the broader restoration stay open.


### Demo 1-1 course loading survey and music retarget candidate (2026-10-26)

The user chose a full-game course survey for the next phase. The
[survey](demo11-course-survey.md) enters each translevel from the Star World
map 6 node with a bounded overworld tile level override, using a fresh save and
the reference host.

The `001`-`0C0` run found 70 playable entries, 78 Mario Start stalls, 34
empty or returning rooms and 10 unexpected states. Every sampled stall requests
a null music slot, so the SPC upload never completes. The recipient stores the
request as a `40 60 <song+1>` record in the level data.

The [retarget candidate](demo11-course-music-retarget.md) changes 17 rooms to
the verified new-family music ids from `config/music-mapping.json`. Seven
sampled translevels reach gameplay on the candidate while the head stalls. The
candidate is registered, qualified, in the suite, and has a native build. It is
not the current head.

The [song 0x57 candidate](demo11-music-57.md) ports the legacy KingBonbie VS
MechaBonbie song from the reviewed cheap-demo four-song group. Translevel `001`
stalls on the head and reaches gameplay on the candidate. The reference and
native captures match on the sampled fields. An audible match is not claimed.

The suite now reports **35/35**; the head byte audit is unchanged.

The [course graphics candidate A](demo11-course-gfx-a.md) ports seven null
extended graphics IDs from 7hero for room 0x173. The candidate verifies the
data, the pointer slots and the native build, but the room still stalls at
Mario Start because song `1A` is also null. The candidate is a building block.

Stall root causes now split into two groups: 42 stalls have no missing extended
graphics and request null songs; 19 stalls select 59 null extended graphics IDs.
The remaining stalled songs still need donor restoration.

