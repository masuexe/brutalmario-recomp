# Content restoration and regression workflow

The user has accepted the 68-variant Demo 1-1 checkpoint and clarified the
long-term objective: retain Demo 1-1 or demoOnly1 as the engine/baseline and
restore unplayable content from other supplied versions where a complete,
playable donor exists. The user chose to compare the existing local versions
first.

The official demo chronology (from oldest to newest) is established as:
`demo6 -> demo6.5 -> demo7 -> cheap_demo -> ow -> mazo -> 7hero -> boss -> demoonly1 -> 1-1`.
When code or data is missing, agents prioritize referencing the newest available code,
and only reference code from these official demos. Note that `cheap_demo` is the last
version that contains all custom sprite code.

## Priorities

### Current direction: native PC delivery

The user's latest decision is that the completed game only needs to run on PC.
An emulator-compatible merged ROM is not a deliverable. Recover the requested
Demo 1-1, demoOnly1, cheap_demo, 7hero, boss and mazo content through the native
host, without requiring it all to fit in one cartridge image. Preserve the
official-source, version-selection and reproducibility rules above.

The [native content expansion plan](native-content-expansion.md) supersedes
the earlier expansion recommendations to keep reclaiming cartridge space or
require reference-host compatibility. The immediate next milestone is an
isolated external-content pilot, followed by a currently blocked custom sprite.
The [native graphics pilot](native-content-pilot.md) now qualifies the first
resource-delivery step: a 3,001-byte graphics stream is absent from its derived
ROM and supplied by an independently mapped external pack. Entry/movement and
an unchanged Boss route match fresh native controls at 42 dump points; four
invalid-pack startups fail as expected. The subsequent
[external sprite-code pilot](native-sprite9e.md) now runs custom sprite `9E`
from a fixed independent bank, with donor-matched lift behavior, native real
death/re-entry, 420 unchanged comparisons and five rejected invalid-pack
startups. This qualifies one immutable code mapping; complete Boss integration
and general executable-module support remain open.
The [Boss inventory](native-boss-inventory.md) now pins the supplied official
Boss Demo and selects its Seven Koopalings program as the first fight candidate.
At that inventory checkpoint, eight bounded donor entry checks passed and
native installation was still open.
The [native Seven Koopalings opening](native-seven-entry.md) now executes the
selected program from immutable A2/A6 packs while preserving A5/B6. Eight
opening samples, fight-local Japanese font bytes, 590 unchanged comparisons,
five rejected startups and 157 unit tests pass. Demo 1-1's English font
overwriting the older Japanese glyphs is a release difference, adapted locally.
The [native Seven child checkpoint](native-seven-child.md) now names the newest
official dynamic child `6A` as custom `E0` and keeps the recipient `6A` actor. It
also restores the English font after a death and reloads the Japanese font on a
fight entry. Six event-aligned child samples, 830 unchanged comparisons, native
death/re-entry and 162 unit tests pass.
The [fight-music checkpoint](native-seven-fight-music.md) now pins the room
`0FF` request to modern slot `AC` (Last Battle). The user listening check
identified the composition. Other fight cues, later fight phases, the ending
and saved completion remain open.
The [hurt-learning boundary test](native-seven-learning.md) now checks 258
paired source/native cases. The user confirmed that random defensive learning
and attack-specific resistance are intended mechanics.
The [ending-boundary checkpoint](native-seven-ending.md) now adapts the modern
stop-music command. It keeps the user-selected official T test room in reserved
room `17B` and restores the English font on exit. It also restores the hidden
1-up checkpoints in that room. A real green mushroom spawns and awards one life
at the same sample index in both hosts. An explicit defeat fixture qualifies the
ending, ordinary rightward pit death and map return. A separate assisted attack
route reaches tiers `0..6`. Seven existing native routes retain 830
byte-identical file comparisons. An earned complete victory and saved completion
remain open.
The [mazo 9C entry checkpoint](native-mazo-9c.md) installs the official mazo 9C
record and runs its protected program from an immutable A2 view. Room `151`
already exists in the recipient with matching level data, sprite list and
graphics. Two active 9C actors appear at the donor slots and positions, and 830
regression comparisons stay byte-identical. The attack behavior, room `190` 9B
module, `B0` corridors and a clear remain open.
The [mazo 9B entry checkpoint](native-mazo-9b.md) installs the official 9B
record and runs its protected program from an immutable A2 view. Room `190`
already exists in the recipient with matching level data and sprite list. The
entry holds three persistent 9B parts at the donor positions, and the settled
state matches at `fight600`. Transient intro actors differ. The [attack-window check](native-mazo-attack-window.md)
records the room 151 wave motion and the later cycle timing. The
[B0 corridor plan](native-mazo-b0.md) records the 419-byte module review, the
corridor data pack and the built target. The four corridor rooms load
with the custom `A9` actor. Rooms `191` and `192` enter gameplay and match the
donor actors. Rooms `00D` and `10C` are transition steps to room `190`. The donor image shows the same transition from rooms `00D` and `10C` to room
`190`. The attack, the relocated exits and a clear remain open.
The [type-3 sprite review](native-sprite-type3.md) pins the newer `C0`, `C1`
and `C2` records, their protected blocks and their room placements. It also
records that the donor and the recipient constructors read different layouts
after the type byte. Record installation stays open.
The [custom sprite gap inventory](native-sprite-gaps.md) now counts the slots
that recipient rooms place but the recipient table leaves empty. Fifty-four
slots cover 78 rooms. Forty of them have a type-1 program in a donor, three have
only a type-3 program, and eleven have no donor record. Record installation
stays open. The [sprite 95 module review](native-sprite-95.md) pins the newest
donor record for the largest gap, its protected block and its 17-entry dispatch
table. The runtime mapping stays open.
The existing `demo11-sprites-orphan-cleanup` chain remains the frozen comparison
checkpoint; this direction change does not promote the candidate or qualify
new content. Full restoration remains open.

Reference emulation remains useful for original donor behavior and unchanged
content, but native-only integration is qualified in the PC host. Compatibility
with an emulator must not block that work. MSU-1 is optional, not a prerequisite.

### Earlier World 1 objective (2026-10-22)

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

The [music batch A and fix batch B candidates](demo11-course-batch-a.md) install
five cheap-demo songs with the validated mapping and nine 7hero graphics. Three
stalled translevels now reach and keep gameplay on reference and native:
`01E` and `043` with music only, and `038` with music and graphics.

The [music batch C and fix batch D candidates](demo11-course-batch-c.md) add
songs `55`-`57` and five more graphics IDs. They fix `04B`, `0A5`, `00E`,
`01F` and `06D`.

The [graphics fix batches E and F](demo11-course-batch-e.md) add sixteen more
graphics IDs for rooms `0x15C`, `0x15D` and `0x144`. They fix `080`, `081` and
`068`.

The [music batch G](demo11-course-batch-g.md) installs six legacy songs as raw
group slices. This path skips the command-graph walk, so songs with unreviewed
commands are installable. It fixes `02B`, `02F` and `06C`.

The [graphics fix batches H and I](demo11-course-batch-h.md) port sixteen more
graphics IDs for the remaining graphics-only stalls. They fix `027`, `03A`,
`040`, `051` and `066`, and they let `018` and `01B` reach gameplay.

The [music batch J and graphics batches K1-M](demo11-course-batch-j.md) add five
more legacy songs as raw slices and 21 more graphics IDs. They fix twelve
stalled translevels: `00D`, `01A`, `02C`, `034`, `03C`, `048`, `04E`, `055`,
`056`, `062`, `06F` and `070`.

The [music batch N and graphics batches O1/O2](demo11-course-batch-n.md)
resolve the low-id blocker. Audio comparison shows the engine plays its own
built-in song for those ids; the payload only satisfies the upload handshake.
All 39 remaining chain stalls now reach gameplay.

The final chain survey reports 207 playable entries and **zero stalls** across
all 255 translevels (head: 70 playable and 78 stalls). The remaining 48 entries
are 46 no-input deaths and 2 Yoshi's House returns. The
[full-range survey qualifier](demo11-course-survey.md) checks both survey
reports.

The [graphics batch P](demo11-course-batch-p.md) ports the last two extended
graphics IDs that the restored rooms reference. No room that stalled on the head
has an empty graphics slot anymore. The whole-line audit passes with zero
unexpected bytes. The suite reports **44/44**; the candidates are not accepted
as the head.

The [head promotion plan](demo11-head-promotion.md) promotes
`demo11-fix-batch-p` after the user playtest.



### Room 122 Dragon Coin runtime correction

The [Dragon Coin fix](demo11-storm-dragon-coins.md) resolves the persistent
vertical garbage column after pickups on `demo11-fix-batch-p`. The ROM is
unchanged. The PPU rejects visible-field HDMA VRAM writes outside forced
blank while preserving the accepted permissive CPU/general-DMA upload policy.
Five real assisted pickups, the fifth-coin extra life, both Map16 planes and
all 16 KiB of tilemap VRAM match default Snes9x in both renderers and pure
interpreter mode. The preserved old binary reproduces the corruption using
the same tracked input. Startup pictures and the LOVE ANIMAL legacy graphics
upload regression pass. The integrated suite reports **45/45**; the whole-ROM
byte audit still has zero unexpected bytes.

The user confirmed that the storm mosaic appears later and matches original
Demo 1-1, then closed that investigation. cheap_demo parity is not claimed.
Earlier image metrics did not prove mosaic and have been superseded.

### Head promotion

The [head promotion](demo11-head-promotion.md) moved the line head from
`demo11-star-bgm` to **`demo11-fix-batch-p`** (ROM `48891cf7...`, native binary
`a00a993d...`). The head audit reproduces 41 recipes and reports 386,151 changed
bytes inside 495,263 reviewed bytes with zero unexpected bytes. The suite
reports **45/45**. The full-range survey reports 207 playable entries and zero
stalls across all 255 translevels. The Dragon Coin column runtime fix is part
of the promoted state. Broader restoration work remains open.


### World-by-world graphics batches

The [world graphics batches](demo11-gfx-worlds.md) port 37 extended graphics
IDs from 7hero in nine bounded batches. The batches follow the world order.
After the chain, no room in Worlds 2 to 8 has an empty extended graphics
slot. Eight translevels now stay in gameplay: `047`, `041`, `037`, `016`,
`031`, `022`, `020` and `04C`. Five playable translevels show the new tile
sets. The suite reports **46/46**. The chain-end audit passes with zero
unexpected bytes. The chain end is `demo11-gfx-world8c` (ROM
`03704a35...`, native binary `b729ba48...`); the head stays at
`demo11-fix-batch-p`.

The full-range survey on the graphics chain end reports 255 loads, zero
stalls and 218 playable translevels (head: 207). Qualifier:
`tools/qualify_demo11_gfx_full_range.py`.

### Custom sprite port, World 2 to World 4

The [custom sprite port](demo11-custom-sprites-w234.md) fixes the cause of
the strange falling object in the later worlds. A custom sprite placement
sets bit 3 in the first sprite-list byte. The target record for that sprite
was still the default record, so the custom code was absent.
The batch ports 19 sprite records from cheap-demo onto
`demo11-gfx-world8c`. Candidate ROM
`8db14be6...`, native binary `61f4b869...`.
Six sprite IDs need the next batch because no free bank range keeps their
low 16 address bits. The suite reports **48/48**. This is a candidate that
waits for a user playtest.

The [second sprite batch](demo11-custom-sprites-w234.md) moves the Star World
graphics blocks to free aligned banks for five more sprites. The user
confirmed that the custom wood sprite works in level `0x123`. The chain
end is `demo11-sprite-windows` (ROM `9bfbde5d...`, native
`cdd44455...`). The suite reports **49/49**. One sprite (`34`) remains.
The [space plan](demo11-space-expansion.md) records the measured cartridge
budget and the options for later boss content.

The [final sprite batch](demo11-custom-sprites-w234.md) moves two graphics
blocks and ports the last missing custom sprite. All 25 missing custom sprites
of the World 2 to World 8 level rooms are now ported. Chain end
`demo11-sprite-final` (ROM `bb93ddc0...`, native `804a2fee...`).
The suite reports **51/51** and includes a space budget guard.

The final sprite chain survey reports 255 loads, zero stalls and 216 playable
translevels. Translevels `022` and `04E` now return a death mode after
600 idle frames because the ported custom sprites are active; the user must
confirm this behaviour change. The whole-line audit reproduces the chain with
zero unexpected bytes and the suite reports **52/52**. The
[expansion research](demo11-expansion-research.md) records the community
answers for content beyond 4 MB.

The [global graphics batches](demo11-gfx-global.md) close the 53 remaining
empty extended graphics slots of the level rooms. Vertical-line corruption and
start falls disappear in the affected rooms. The full-range survey on
`demo11-gfx-global13` reports 255 loads, zero stalls and **233 playable**
translevels (previous chain: 216). Translevel `069` changed its idle
behaviour and needs a user check. The chain-end audit has zero unexpected
bytes and the suite reports **54/54**. The user confirmed that room `11D` is
fine on `demo11-sprite-final`.

The user confirmed that room `0x116` (translevel `03A`) completes normally on
`demo11-sprite-final`. The custom object with the red counter behaves as
intended.

The user confirmed levels `0x109` and `0x15F` on the global graphics
chain. The middle boss room of `0x15F` stayed black because its room
`0x0BC` requested the null legacy music slot `0x2D`. The
[boss music retarget](demo11-boss-music-fix.md) moves that one parameter to the
working slot `0x1E`, so the room now loads. The user deferred music
quality work. The [level sprite batch](demo11-level-sprites.md) ports six more
custom sprite records and drops the 7hero C2 record, which crashes level `094`.
Chain end `demo11-boss-music-retarget` (ROM `69ea041f...`, native
`a2d42daf...`). The suite reports **56/56** and the audit has zero
unexpected bytes.

The user clarified that the level `0x145` object without tiles is the
scroll-control sprite, so the level is normal and no defect remains. The user also reports
that the big door of level `0x109` leads to room `0x49`, whose custom
sprite probably has no code. The [room 049 sprite batch](demo11-room49-sprite.md)
ports record `0x48` from cheap-demo; the runtime effect needs a user playtest
through the door. Chain end `demo11-sprite-room49` (ROM `ce129957...`,
native `2e357a96...`). The suite reports **57/57**; the audit has zero
unexpected bytes.

The [boss room graphics batch](demo11-boss-room-graphics.md) covers the 95
remaining rooms with empty extended graphics slots (159 IDs) and ports custom
sprite `0x2B` for room `0x0BC`. The middle boss room of level
`0x15F` now loads with correct tiles. The batch also fills the room `0x49`
graphics (`0x160`, `0x16E`, `0x16F`), which the user reported as a wrong
palette and a damaged level. Chain end `demo11-gfx-boss76` (ROM `d6e78605...`,
native `63ddcb2f...`). The suite reports **58/58** and the audit has zero
unexpected bytes. The space floor is now 300,000 free bytes.

The full-range survey on `demo11-gfx-boss76` reports 231 playable
translevels and no outer behavior change. Two translevels change because their
missing custom sprites now run: `070` moves from boss room `0x14C` to
`0x14D` (the transition completes), and `062` now has a moving object
that carries Mario to a death. The user must confirm both. The suite reports
**59/59**.

The user confirmed room `0x49` on `demo11-gfx-boss76`: music,
level layout and the custom sprite are normal. This accepts the subroom
graphics recovery for that room.

The user specified slot `0xA9` as the correct music for room `0xBC`. The
`demo11-boss-room-music-a9` recipe sets the one-byte room music parameter,
and the capture confirms `$0DDA = A9`. The room still has no boss health bar:
the room places sprites `0x2B` and `0x29`, but runtime captures show no
sprite spawn. The boss spawn path stays open. Chain end
`demo11-boss-room-music-a9` (ROM `1a56f3fc...`, native `d0a29d30...`).
The suite reports **60/60**.

The user reports that the room `0xBC` boss attacks work in ordinary play,
while headless captures on the same chain do not spawn the boss. cheap-demo
shows the health bar immediately, and its room list bytes and records equal the
chain. A runtime state difference is the remaining suspect. The user should
provide the save or savestate of a working fight, or confirm the exact entry
path.


### Boss and Mario HP display repair

The user reports missing HP bars in rooms `0xBC` and `0xCC`.
The [HP upload investigation](demo11-hp-bars.md) supersedes the earlier claim that the boss does not spawn.
That claim came from probes which misread `$161A,x` as a sprite number and rejected its valid zero index.
The actual boss runs, and both rooms fill their HP character buffers.
Demo 1-1 omits the legacy HUD upload for these characters.

The isolated `demo11-hp-bars` descendant appends the upload only in active rooms `0xBC` and `0xCC`.
It retains the existing recipient HUD and the accepted room009 fuel upload.
Reference, native and interpreter captures show both displays.
A vanilla Koopa contact fixture exercises real Mario damage and the subsequent HP display update.
Ordinary corridor HUD controls, startup pictures and the fuel regression also pass.
The integrated suite passes 61/61 checks, and all 122 unit tests pass.
The candidate byte audit reports zero unexpected changes.
The head remains `demo11-fix-batch-p`; this checkpoint does not promote the restoration chain or qualify a full boss fight.

The [CC sprite batch](demo11-cc-sprites.md) ports custom sprites `0x63` and `0x65`
from cheap-demo onto `demo11-hp-bars`. Room `0xCC` now keeps both
custom sprites active while the HP HUD region stays byte-identical. Chain end
`demo11-sprites-cc` (ROM `8d9330de...`, native `e5e1a3e9...`).
Suite **62/62**; audit zero unexpected.

The [room 0x128 HP bar recipe](demo11-hp-room128.md) extends the accepted
HP shim to room `0x128`. The room already filled the legacy `$7F:FFE0`
row and set `$7F:FFDF`; only the HUD upload was missing. The fixed
capture changes the HUD row and leaves the gameplay field byte-identical.
Chain end `demo11-hp-room128` (ROM `d41eda4d...`, native
`f3975d6f...`). Suite **63/63**; audit zero unexpected.

The [room 0x146 HP bar recipe](demo11-hp-room146.md) adds the last captured
missing HP row. A capture scan found only rooms `0x009`, `0x0BC`, `0x0CC`,
`0x128` and `0x146` that fill the legacy row. Room `0x009` already
displays its row through the accepted fuel shim. Room `0x146` now displays
its row; the gameplay field stays byte-identical. Chain end
`demo11-hp-room146` (ROM `616074b4...`). Suite **64/64**.

The [CC lobby sprite batch](demo11-cc-lobby-sprites.md) ports custom sprite
`0x69` from cheap-demo. Rooms `0xD6`, `0xDA`, `0xDB`, `0xE0`,
`0xE2` and `0x155` now run the custom code. The room frame changes
and the HUD stays identical. Chain end `demo11-sprites-cc-lobby`
(ROM `34bddb84...`). Suite **65/65**; audit zero unexpected.

The [CC lobby sprite set](demo11-cc-lobby-sprites-full.md) ports the remaining
lobby sprites `0x67`, `0x68`, `0x6A`, `0x71` and `0x5B` with nine
reviewed graphics relocations. Room frames change and the HUD stays identical.
Chain end `demo11-sprites-cc-lobby-full` (ROM `3ef5817b...`).
Suite **66/66**; audit zero unexpected.

The [remaining free sprite batch](demo11-sprites-remaining-free.md) ports
fifteen free-window sprites: `0x1A`, `0x27`, `0x3D`, `0x4F`, `0x51`, `0x53`,
`0x5C`, `0x6B`, `0x6D`, `0x70`, `0x73`, `0x77`, `0x7B`, `0x7D`
and `0x8B`. Chain end `demo11-sprites-remaining-free` (ROM
`fa986111...`). Suite **67/67**; audit zero unexpected.

The [room 0xCF HP bar recipe](demo11-hp-roomcf.md) extends the HP shim to
room `0xCF`. The room already filled the legacy row and set the flag;
only the HUD upload was missing. Chain end `demo11-hp-roomcf`
(ROM `925b004a...`). Suite **68/68**; audit zero unexpected.

The [fire projectile batch](demo11-sprites-fireball.md) ports custom sprite
`0x56` with two graphics relocations. Room `0xCC` now shows the red
fireball and its path matches cheap-demo. Chain end
`demo11-sprites-fireball` (ROM `ee09118e...`). Suite **69/69**;
audit zero unexpected.

The [snow projectile batch](demo11-sprites-snowflake.md) ports custom sprite
`0x5A` with one graphics relocation. The dragon spawn code can spawn
it beside the fire projectile. Chain end `demo11-sprites-snowflake`
(ROM `81d752be...`). Suite **70/70**; audit zero unexpected.

The [second free sprite batch](demo11-sprites-free-two.md) ports seven more
custom records: `0x03`, `0x1D`, `0x2F`, `0x41`, `0x59`, `0x84` and `0x85`.
Chain end `demo11-sprites-free-two` (ROM `01bbcefa...`). Suite
**71/71**; audit zero unexpected.

The [blocked sprite batch one](demo11-sprites-blocked-one.md) ports twelve
placed custom sprites with thirteen reviewed graphics relocations. Rooms
`0x8F`, `0x95`, `0xB0` and `0x1D` change and keep an identical HUD.
Chain end `demo11-sprites-blocked-one` (ROM `c4799ec8...`). Suite
**72/72**; audit zero unexpected.

The [blocked sprite batch two](demo11-sprites-blocked-two.md) ports ten more
custom sprites with ten reviewed graphics relocations. Room `0xAC` changes
its gameplay field. Chain end `demo11-sprites-blocked-two` (ROM
`e99b8733...`). Suite **73/73**; audit zero unexpected.

The [blocked sprite batch three](demo11-sprites-blocked-three.md) ports four
custom sprites with four relocations. Rooms `0x3B`, `0x2C` and `0x7B`
change and keep an identical HUD. The free-space review floor moves from
300,000 to 290,000 bytes. Chain end `demo11-sprites-blocked-three`
(ROM `9ec9c6a0...`). Suite **74/74**; audit zero unexpected.

The [blocked sprite batch four](demo11-sprites-blocked-four.md) ports sprites
`0x1B` and `0x0C` and adds sprite-block rebanking to the planner.
Chain end `demo11-sprites-blocked-four` (ROM `7f20e474...`). Suite
**75/75**; audit zero unexpected. The free-space review floor is now 150,000 bytes.

The [native record restores](demo11-native-record-restores.md) revert two
wrong cheap-demo ports: sprite `0x42` in room `0x8F` and sprite
`0x3D` in room `0x13C`. Demo 1-1 and demoOnly1 keep the default
records for these IDs. Room `0x8F` now matches the pristine demo 1-1 frame.
The full-range survey finds 231 playable translevels. Chain end
`demo11-sprites-native-records` (ROM `63389cab...`). Suite **76/76**.

The [demoOnly1 room 0x8F boss port](demo11-room8f-boss-port.md) installs the
new boss record and code block. The demoOnly1 record table is at file
`0x8308A` and the block is at file `0x13C862`. Two graphics
assets move to free the bank window. Room `0x8F` now matches the
demoOnly1 frame. Chain end `demo11-sprites-room8f-boss`
(ROM `23f8ab7f...`). Suite **77/77**.

The user accepted the [demoOnly1 room 0x8F boss port](demo11-room8f-boss-port.md).
The boss drops coins after the defeat and a world conquest rate screen follows.
The user states that this is the author intent.

The [orphan sprite block cleanup](demo11-orphan-sprite-cleanup.md) removes
the two code blocks of the restored records `0x42` and `0x3D`.
Two room frames stay byte-identical. Chain end `demo11-sprites-orphan-cleanup`
(ROM `eccde661...`). Suite **78/78**.


### Room 190 background recovery (2026-10-28)

The [r3 background repair](native-corridor-background.md) restores official mazo
extended graphics `1E5` on a separate product-r2 descendant. The vertical stripes
disappear. Both the Mode 7 map and character lanes match the live donor at
16,384 bytes each; native/interpreter VRAM and framebuffer agree. The older
handoff confused the map and character byte lanes. The user reports r2 is
playable apart from its background. The Japanese message font in rooms 191/192
and broader restoration remain open.


### Room 191 invisible markers (2026-10-29)

The user accepted the r3 background. The [room 191 marker adaptation](native-corridor-invisible.md)
adds room-private transparent foreground and control-sprite patterns in r5,
retaining actor logic and collision data. Five samples agree between native
and interpreter graphics; room 190 retains five byte-identical dump files.
The 313-test suite passes. The Japanese message font and broader restoration
remain open.

### Room 191 orb correction (2026-10-29)

The user found that r5 also hid the rightmost question orb. The
[r6 correction](native-corridor-invisible.md#r6-correction-retain-the-question-orb)
restores the complete original SP4 page, retaining only the private transparent
foreground patterns. Five samples require original orb graphics, an active orb
actor, visible orb pixels and transparent garbage rectangles. Native/interpreter
graphics agree; room 190's five complete dumps remain identical to r3. The r5
claim that its orb patterns were disposable placeholders is superseded.

### Room192 foreground extension

The user accepted r6. The [r7 room192 extension](native-corridor-invisible.md#room-192-extension-r7)
reuses its private foreground clone while preserving original sprite graphics.
Five native/interpreter samples and unchanged actor states pass; rooms191/190
retain 30 identical dump files. The Japanese message font remains open.

## Content closure audit (2026-10-29)

The [content closure audit](content-closure-audit.md) reviews the tracked record
at `f65169e` against the product target `demo11-native-product-r12`. It finds
no unstarted content block with the size of `7hero` or `mazo`. It records
three open gaps. Worlds 2 to 8 have no route, exit or save acceptance. The
Seven line has no earned victory and no saved completion. The mazo attack and
clear have no qualification. The audit also lists the open sprite, music and
graphics items and the claims that the record does not support. The unit suite
passes 339 tests.

## Product-line load survey (2026-10-29)

The [product survey](demo11-product-survey.md) runs the full-range course probe
on the native product target `demo11-native-product-r12`. All 255 translevels
load, 227 entries are playable and no Mario Start stall remains. Eight entries
differ from the reference survey only in death or return timing.

One entry crashes: translevel `094` (level `170`). The demo11 base ROMs load
the same level normally. The product carries the type-3 record `C2`, and the
[level sprite batch](demo11-level-sprites.md) already recorded this failure for
that record. The product needs a descendant without `C2`, or the type-3
constructor work, before a release candidate.

## Product r13 without C2 (2026-10-29)

The [product survey](demo11-product-survey.md) found one crash in the r12
candidate: translevel `094` (level `170`). The `C2` type-3 record is the
cause. `demo11-native-product-r13` removes the record and its pack. The level
loads room `170` in mode `14`, and the full-range survey reports 228
playable entries and no crash. The unit suite passes 344 tests. The correct
`C2` restoration stays open.


## Assisted exit boundaries and course identity (2026-10-29)

The [route inventory](world2-route-inventory.md) now records seven native
primary exit boundaries on product r13 and a fresh Star World control.
The failed earlier probes selected screen 07, where neither source room has
an exit. Correct screens reach the expected primary rooms, including `1D7`
(the high bit was absent from the earlier low-byte-only table). These are
position and pipe-action fixtures, not traversal, clear or save acceptance.
The course labels in the local world catalog conflict with the community
version-specific directory; matching recipient content to course identities
is the next prerequisite for gimmick-specific route work.


## Corrected Forest catalog and two linked saved exits (2026-10-29)

The [Forest identity checkpoint](forest-course-identity.md) corrects the ten
World 2 courses using version-specific names, existing native map nodes and
pinned official-source name/sprite/layout fingerprints. All ten enter their
actual rooms. The first course, room113 Fishing Spree, now has an assisted
real goal-tape clear, natural onward map movement to the bridge node, both
SRAM copies, console-reset File A reload and cleared-course re-entry. No
completion flags or saves are written by the fixture. Full traversal, secret
exit, Dragon Coins and the other eight course clears remain open. The catalog
correction changes no game data or behavior.


## Forest shack real switch, victory and saved exit (2026-10-29)

The [shack checkpoint](forest-shack-route.md) exercises the existing room chain
015 -> 044 -> 046. A real On/Off block hit enables Layer 2 collision; three
original throw-block impacts defeat Big Boo and trigger the actual normal
clear. The route returns to Lost Forest, saves both completion copies, reloads
File A and enters room123. A separate position-assisted pit death loses one
life and re-enters room015. Native and same-image reference checks pass at 19
paired points with all four Map16 buffer regions exact; moving boss positions
permit one pixel. All external mounts remain unused on these two routes, so
the reference result is explicitly limited to this subset. No On/Off, HP,
completion, actor or save writes are used. Complete puzzle traversal remains
open. The existing unit suite passes 344/344. No game code or resource changes.


## Lost Forest eight-color maze and saved normal exit (2026-10-29)

The [Lost Forest checkpoint](forest-lost-route.md) verifies eight actual
color-matched boundary choices in room042, room050's real tape, natural map
return, both saved completion copies, console-reset File A reload and onward
room11F entry. A wrong-color control resets progress after one correct choice
without clearing or losing a life. The fixtures bypass the first log/P-switch
puzzle but never write maze progress, palette, destinations or completion.
Twenty-one native/reference paired samples match asserted semantics, actors,
color state and four Map16 buffer regions exactly. All external mounts are
unused on these limited same-image routes. The already installed sprite08
program matches official cheap_demo; newer official records are placeholders.
All 344 existing tests pass. No game code, ROM or pack changed. Six other
Forest course clears and the full puzzle/collectible/experience gaps stay open.


## Hollow normal save and missing A2 branch (2026-10-29)

The [hollow checkpoint](forest-hollow-route.md) verifies the existing
11F -> 039 -> 043 route, actual goal tape, natural Ghost Forest selection,
both saved completion copies, console-reset File A reload and ordinary room114
entry. Separate position-assisted Up/Down controls reproduce the accessible
room182 branch and its missing custom A2 actor. No completion, actor or
destination writes are used. Seventeen native/reference sample pairs satisfy
the bounded assertions and exact Map16 comparisons; moving room043 Y positions
permit one pixel, explicitly recorded in the report. All mounts are unused on
these limited same-image routes. All 344 existing tests pass.

The older three-source gap census did not establish global donor absence.
Official demoOnly1 has a matching room182 placement and a protected 7,392-byte
A2 candidate. It has not been installed or behavior-qualified; its untouched
reference replay stops in mode12 before entering the course. Modern room182
also has a source-data difference to preserve during review. Five Forest normal
exit/save boundaries are now qualified; five remain. Full traversal, the A2
branch, optional content and broader restoration remain open. No game code,
ROM or resource pack changed in this checkpoint.


## Native product r14: official A2 shop, return and purchase save (2026-10-29)

The [A2 restoration](forest-a2-restoration.md) installs the matching official
demoOnly1 program in native bank `9D`, preserving all recipient room layouts and
46 inherited packs. The new pack restores the hollow's Vivian shop, four menu
selections, insufficient-funds response and one actual 1,111-price purchase
under an explicit 2,222 balance fixture. Ownership changes through the guest
program; duplicate purchase does not charge again. Actual normal clear saves
the remaining currency and ownership in SRAM, and File A reload retains them.

The original return table is empty. A bounded native adaptation adds secondary
`1FF` at the measured incoming pipe position `800/352` and changes only the hollow
variant's selector byte. Actual B return, stable standing and Up re-entry pass.
The other placed A2 in room `104` now matches the source's automatic exit to `180`;
the r13 placeholder control remains in `104`. Thirteen source/native menu and purchase
sample pairs match the asserted functional state and complete 384-byte message
buffers. This is not whole-image parity; source entry uses declared destination
and translevel fixtures. The original source's garbled message glyphs remain.

The r14 hollow normal route is byte-identical to r13 in all 27 complete
WRAM/SRAM/VRAM dump comparisons. All 353 tests pass, including nine admission
tests. The new module's bank must retain the source's low WRAM/IO mirrors; an
earlier D2 prototype crashes and is retained only as ignored diagnostic evidence.
Other mapped programs' bank assumptions need their own audit. The r13 survey's
228 playable entries/no crash is historical and has not been relabelled as an
r14 survey. Other purchases, ability effects, the alternate room104 flag path,
Ghost Forest, full traversal and broader restoration remain open. r14 is the
new working native target, not whole-game acceptance.


## Rejected r15 candidate: low-memory mappings and sprite95 integration (2026-10-29)

The [mapping correction](native-lowmirror-restoration.md) moves ten executable
views from banks without their source programs' low WRAM/I/O mirrors into
compatible native banks. Original program logic and low16 address bits remain.
Fresh r14 controls reproduce a visible-but-stationary actor31 and a parent32
that never generates its child. R15 matches official-source selected actor
identities, motion, velocity and state in16 multi-frame pairs across08B,155,
087 and086. Room087 uses an explicit global-frame phase fixture; the unphased
late-fall difference remains outside full physics/timing acceptance.

R14 also lacked95 in the product despite its earlier independent pilot.
R15 installs the newest official Boss Demo program, verified byte-identical to
7hero for the behavior reference. Its record covers seven rooms; four fresh
room16B held-position samples match the95 actor, while the r14 control lacks
it. The other six rooms and full95 mechanics still need current-target checks.
Room16B's other actor8C differs from the older source; its native coordinates
already match r14, so it remains a separate version/behavior investigation.

All48 mappings and the exact record-only ROM delta are checked. All359 tests
pass. The A2 shop, funded purchase/save and hollow normal route remain byte-
identical to r14 across51 dump points and153 full WRAM/SRAM/VRAM comparisons.
C0/C1 have compatible code addresses, but the initial fixtures did not execute
their callbacks. A subsequent gradual loading probe crashes C0: the recipient
classifies its source shooter ID as a normal actor and executes the ASCII MAIN
label as init code. The mapping report remains component evidence only.
The0A2/15D fixture limits and160/05B trajectory differences are recorded rather
than treated as full actor acceptance. Other Forest routes, complete traversal,
earned endgame victories and music/graphics work remain open. R15 is rejected;
r14 remains the accepted working target. An isolated type3 shooter adapter is
under qualification. No full-game or fresh whole-range survey claim is made.


The isolated [C0/C1 shooter checkpoint](native-type3-shooters-restoration.md)
now fixes that classification through three bounded native hooks, retaining
normal E0 and existing native shooter/generator meanings. Forty-five fresh
source/native live16B samples exercise actual callbacks. C0 generates phase2
95 actors; its motion phase remains open. Twenty C1 generated-actor samples
match selected status/XY/velocity/state after sorting slot differences. Three
r14 regressions cover45 dump points: full SRAM/VRAM match, with explicitly
recorded inactive CPU stack residue excluded from WRAM equality. All359 tests
pass. The experimental target is not promoted: remaining loading windows,
positive current E0 birth, other95 rooms and C2 still need qualification.


## Official C2 shooter descendant (2026-10-29)

The [C2 checkpoint](native-type3-c2-restoration.md) restores the newest official
Boss program in low-mirror bank91 and extends the existing shooter adapter by
three threshold bytes. Ten left/right firing samples match7hero selected actor
and shooter state exactly. Ordinary Y entry through a map/translevel094 fixture
stays live in170 through600 frames and actually generates phase0F custom95.
All six16B shooter placements now load with matching positions and extra flags
across63 live samples; the late-window fixture explicitly bypasses a corridor.
C0 and late-C1 motion phase, positive current E0 birth and other95 rooms remain
open. Two parent regressions retain210 complete byte-identical WRAM/SRAM/VRAM
comparisons;363 tests pass. The experimental target is demo11-native-type3-c2-v2.
Accepted product remains r14; r15 stays rejected. This is no course-clear,
whole-game survey, earned-victory, visible/audio or full timing acceptance.


## Cumulative Seven feature reconciliation (2026-10-29)

The [Seven integration review](native-seven-product-integration.md) finds that
cumulative targets still carried the older7hero controller/resources and an
empty E0 record. The previously qualified newest Boss child/font/ending1up
feature had not survived cumulative integration. A new isolated descendant,
demo11-native-seven-product-v1, carries forward its exact master/resources,
adds the byte-identical official child in low-mirror bank90, and applies seven
bounded, conflict-checked ROM spans. Normal6A and all other programs remain.
Six fresh child actor pairs match19 source fields; real death and font/re-entry
checks pass. Explicit ending-stage fixtures qualify the17B transition, ordinary
pit death and a real hidden green mushroom/life award at source-matched samples
17/28, without proving an earned win. Four parent regressions give327 complete
byte-identical state comparisons;368 tests pass. R14 remains the accepted
product; this experiment is not whole-game acceptance. Other95 rooms, C0/late-
C1 phase, earned Seven/mazo victories/save and music/graphics work remain open.

## Current sprite95 room mechanisms (2026-10-30)

The [six-room checkpoint](native-sprite95-current-rooms.md) now qualifies the
remaining95 rooms in the unchanged experimental Seven product candidate.
Twenty-four completed captures provide86 paired samples:16C generates its
phase06 child,16F actually cycles layer2, and16E loads all six doors. Ordinary
Up enters the five trials at150/16F/170/171/172, with source-matched selected
bits and172 switch preservation. Boss/7hero complete95 programs are identical;
bounded foregrounds and five backgrounds match. The1CC background remains
unqualified, and16E sprite placement order differs while placements match.
These diagnostic entry/position/immunity fixtures do not prove trial clears,
the172 exit,1CC interaction or full-course/visible/audio parity. The candidate
is not promoted. Continue actual trials and earned Seven/mazo wins/save along
with remaining content, route, music and graphics work.

The [fifth-trial mechanism check](native-sprite95-trial5.md) adds59 paired
samples on the same candidate. Real jumps operate the numbered switches,
the protected Koopa crosses the bridge and enters its shell, and actual
stomp/pickup/release follows. After an explicit far-corridor position fixture,
ordinary Up at the actual far door restores switch10 and returns172 to16E,
where the game awards one Dragon Coin. Lives and saved five-coin flags remain
unchanged. Earlier failed timing/loading/lava probes stay separate. Platform
and switch-position fixtures leave ordinary traversal, other trial coins and
five-coin/save acceptance open;1CC interaction also remains unresolved.

The [ordinary fifth-trial platform route](native-sprite95-trial5-route.md)
subsequently removes the far-door teleport and all damage-immunity writes.
Fresh native/7hero runs pass68 paired samples. Following the earlier assisted
switch/stomp/approach setup, ordinary carry/release, upper-passage jump, vine
grab and door Up reach16E and award one Dragon Coin. Initial position fixtures,
the other trials, five-coin/save behavior and full-course acceptance remain.

## Cumulative recovery of omitted25/33/94 programs (2026-10-30)

The [new sprite-product descendant](native-sprite-product-reconciliation.md)
recovers three separately installed programs that never reached the cumulative
table. It selects unchanged newest official Boss code in low-mirror banks
8F/8E/8D, patches only three records and retains all51 prior mappings. Fresh
native/7hero captures match19 actor fields and slots at27 live samples, with
actual25 ascent,33 horizontal/player movement and94 motion/state cycling.
Five existing-feature regressions retain247 unique complete-state comparisons
(741 files), including Seven child/font/re-entry/ending1up, shop saves, C2 and
the ordinary fifth-trial return. The experimental target is now
`demo11-native-sprite-product-v1`; r14 acceptance and r15 rejection are unchanged.
All377 unit tests pass, including nine new integration/census checks.

A native-pack-aware static census also corrects false missing-slot reports:
four room sprite lists reside in external CA-bank data. All512 lists resolve
to164 used custom slots with10 placeholder records. Those remaining records
need official-source/content review; the census does not qualify full rooms,
prove donor absence or close earned Seven/mazo victory/save and asset work.

## C0/C1 shooter phase alignment (2026-10-30)

Dense per-frame captures resolve the open room 16B shooter phase item. The C0
child sequence and shooter countdown match the official 7hero source after a
one-frame shift: 63 of 63 aligned samples. The C1 window matches every moving
child row across 64 frames; one static placed child at X1152 differs by one
pixel. `tools/qualify_native_type3_phase.py` reproduces both checks. The report
is `local/reports/native-type3-phase-v1.json`.

## Room 151 boss extended graphics 0x282 (2026-10-30)

Sprite 9C requests extended graphics `0282` at pack offset `E0A`. The product
pointer is empty and the mazo stream holds 4096 bytes. The candidate
`demo11-native-mazo-gfx282-v1` mounts the official stream at `D2:8000` and
patches the pointer; the ROM delta from r14 is three bytes. The room 151 window
holds sibling sets 027F to 0281 in VRAM but not 0282, so the missing family
member stays open for a runtime frame. See See
[native-mazo-gfx282.md](native-mazo-gfx282.md). Id `027E` stays open.

## Overworld map music World 4 and World 6 (2026-11-02)

The [overworld music correction](demo11-overworld-music.md) fixes the map
themes for World 4 (Cave) and World 6 (Sky). The recipient `OverworldMusic`
table and its `OverworldMusic2` duplicate stored `0x27`, the Special World
theme, at submap 2 (World 4) and `0x22`, the World 4 theme, at submap 1
(World 6). The newest official demo stores `0x22` at submap 2 and `0x23` at
submap 1. The target `demo11-overworld-music` changes four table bytes only.
Reference and native captures show submap 1 -> `0x23` and submap 2 -> `0x22`,
while submaps 3 and 5 keep their values. `tools/qualify_demo11_overworld_music.py`
replays the checks. This proves the song selection only; it is not an audible
match and does not change any song payload.


## Native console performance repair (2026-11-02)

The [console repair](windows-console-performance.md) removes repeated launch
setting queries from the ROM bus path. The isolated r14 Windows candidate drops
from 471.193 ms to 3.320 ms per guest frame in a 60-frame probe; Linux drops
from 25.664 ms to 3.112 ms. Each platform retains 12 exact before/after dump files.
A 3,122-frame Linux room190 diagnostic retains 36 exact files; the repaired
Windows run matches the Linux binary dumps and text after CRLF normalization.
The map/pipe fixture is assisted and does not qualify an earned clear. The
three existing hooks retain their access boundaries and writes; settings now
refresh at content load. All 439 tests pass. Fresh console bundles preserve all
older artifacts and user saves. These r14 packages omit the separate map-music
ROM fix; desktop/audio/full-command and whole-game acceptance remain open.

## Unified product tool and console acceptance (2026-11-02)

The user accepted the delivered r14 console repair after playtesting.
[The product tool](product-tool.md) now unifies configured CMake builds,
headless console/performance verification and Linux/Windows packaging. Releases
require a verification receipt bound to the executable, ROM, product config
and all pack hashes; existing archives and output directories are preserved.
The first shared launchers complete fresh 60-frame checks on both platforms.
Initial CMake configuration and clean toolchain setup remain existing workflows;
Python 3 is required by the generated launchers. These r14 packages still omit
the separate map-music ROM repair. Broader restoration remains open.

## Console teleport table repair (2026-11-02)

The user found low-room teleport 00F could enter 10F. The
[transfer repair](native-console-teleport.md) separates the $19B8 low byte from
the $19D8 high flag and preserves neighboring exit records. Compiled queue tests
cover repeated low/high transfers and fresh Linux/Windows runs confirm 00F/10F
entry into gameplay. Shared product verification passes at 3.085/3.488 ms per
guest frame; new isolated bundles preserve prior artifacts and saves. This is
an assisted transfer-boundary qualification, not a course clear. The broader
restoration and separate map-music integration remain open.

## Console swim restoration (2026-11-02)

The user reported that toggling swim off left swimming active and required
preservation of genuine water behavior. The [frame-scoped repair](native-console-swim.md)
restores the real level-water flag after each simulated frame and lets native
collision update player swimming after disabling the cheat. Actual r14 water
code checks cover dry land, full-water levels, local water and leaving local
water. Eleven targeted tests and both product verifications pass; 12 parent
startup dump files remain exact on each platform. Earlier eight stale-host
full-suite failures are still deferred. Fresh Windows folder and ZIP copies
are hash-verified at the requested `D:/tmp` location. Teleport repair remains;
map-music integration and broader restoration remain open.

## In-level coordinate command (2026-11-02)

The user accepted the swim repair and requested a coordinate teleport available
only inside a course. [The xy command](native-console-xy.md) adds `xy X Y` and
`tp X Y`, with strict decimal/hex parsing, gameplay/action gates, coherent player
position writes and cleared momentum. Twelve targeted tests and both product
verifications pass; startup states remain exact against the swim parent. An
assisted coordinate-write fixture checks subsequent gravity, movement and camera
behavior, separately from compiled-handler tests. Earlier stale-host suite
failures remain deferred. These r14 packages retain teleport/swim fixes;
map-music integration and broader restoration remain open.

## External content packs (2026-11-03)

A LoROM data block must stay inside one 32 KB bank. The free space of the
image is 327,746 bytes in 39,943 ranges, and the largest range is 4,072
bytes, so a 6,144-byte song block has no place to go.

A region provider now replaces a byte range with bytes from a pack file.
It shares the backing map with the sprite-gap runtime, so both providers
write into the same copy of the image.

The first pilot is target `demo11-music-pack`. It moves six song slots that
no level music object requests (26,516 bytes) into one pack. A capture
mounts both providers, and a console-teleport audit reads the moved song
in all nine rooms that request it.

See `docs/native-region-packs.md` for the mechanism and the identities.

## Level music retarget (2026-11-03)

The user reported one wrong music entry for each course and asked to port the
missing songs from the newest version that holds them. The
[music retarget checkpoint](demo11-music-retarget.md) records the analysis.
The level music objects still request legacy-family song numbers, so most
courses play a different Demo 1-1 slot. A scan of every pinned official ROM
finds the legacy four-song upload groups only in `cheap-demo`, so that version
is the donor for the legacy-exclusive songs.

The recipe `demo11-music-retarget` descends from `demo11-overworld-music`. It
changes 208 one-byte music parameters and installs three legacy songs at free
Demo 1-1 slots: `31` to `35`, `49` to `3A` and `51` to `3D`.
ROM SHA-256 is `82741528f9d8c335901157184a6398eb1f05d4ec7395f7ec3c6c72249168e9fa`;
9,258 bytes change. `tools/qualify_demo11_music_retarget.py` checks the
selection sites, the installed payloads, the target slots and the ROM delta.

The song table entry must use the `0x80`-`0xFF` mirror for file banks
`0x7E` and `0x7F`, because a plain pointer there names WRAM and the SPC
upload stalls. Rooms `013` and `0AA` enter gameplay after that fix.

The user reported that the legacy `0x37` track is an older arrangement of slot
`0x30`, so rooms `0AA` and `0AB` request `0x30` and the port is gone.

A console-teleport audit reads `$0DDA` on arrival for the rooms that the
recipe could not identify. Rooms `05D`, `05E`, `0D3` and `102`
are retargeted from that evidence. Seven of those rooms hold no level music object, so they inherit the parent
song. `tools/prepare_music_objects.py` moves the level block into free
space, appends the music object and repoints the level table; a new audit
reads the reviewed song on arrival. Room `107` needed one correction to
the object size table: object `0x28` is three bytes. With that table all
403 level blocks terminate at the end of their RATS payload. Slot `0x1E` is
the legacy silence convention, so rooms `020` and `036` are correct.

The checkpoint proves song selection only. The audible match, the four songs
that use unreviewed commands (`3F`, `43`, `49`, `4F`, `53`), the inherited-music
rooms and the native build stay open.

## Product sprite merge (2026-11-05)

The [sprite merge checkpoint](native-product-sprite-merge.md) moves seven
reviewed custom sprite records onto the product line. Product r20 descends
from r19 and installs slots `25`, `33`, `94`, `97`, `99`, `A1` and `C2`.
The placement census drops from 14 placeholder slots to 7. The other seven
slots hold no official program in any supplied image.

ROM SHA-256 is `f4185fe22f57c66c338b800bbe423dcd915860c87cc2ec395baa7236cad5e567`.
The merge adds 2 record patches, 7 recipes and 1 raw pack. It keeps the 61
inherited patches, the music region pack and every room layout. Native
captures show each new actor in its room and no actor on the parent.
The room 174 fixture needs `BM_SEVEN_RETURN=0`.

The captures use assisted entry fixtures. Boss fights, ordinary routes,
sprite graphics and the `99` position offsets stay open. The doc is
`docs/native-product-sprite-merge.md`. The tests are
`tests/test_product_sprite_merge.py`.

## External sprite graphics provider (2026-11-05)

The [graphics provider checkpoint](native-sprite-graphics-provider.md) moves
custom sprite graphics out of the image. Product r21 descends from r20 and
mounts one reviewed VRAM pack. The provider writes the pack when the game
enters a room that the manifest names.

The r21 ROM SHA-256 equals the r20 ROM SHA-256: the provider is a runtime
feature, not an image change. One pack covers the object character range of
room `175` and rewrites it on every frame of that room. Its qualification
shows 514 applications in that room, none in room `154`, no write outside the
range, and 16 differing bytes inside it against the donor.

The room `175` platforms now render, and the user accepted them on
2026-11-05. The yellow platform pixel count is 570 on the donor, 570 on the
candidate and 38 on the parent. A frame difference of 1,575 pixels remains a
technical observation, not a defect: the platform actors stand at different
object coordinates, which matches the known `99` start-position offset. The
design and the next work are in `docs/native-sprite-content-packs.md`.

## Vanilla SMW music restoration (`demo11-native-product-r41`, 2026-11-08)

The [vanilla SMW audio image checkpoint](vanilla-smw-audio-image.md) and
[low-ID music note](demo11-low-id-music.md) document the restoration of the five
vanilla Super Mario World music tracks into `demo11-native-product-r41`:

- Slot `02` (Overworld, vanilla `$18AA`, `2,321` B payload at `ARAM $5400`) is
  unaliased from Slot `4F` (`468008`) to `4DD008` (`0x26D000`).
- Slot `03` (Water, vanilla `$16C6`, `1,063` B payload at `ARAM $5400`) replaces
  the `r40` *Undersea Palace* substitute at `music-pack.bin` offset `2476352`.
- Slot `05` (Boss, vanilla `$13B0`, `1,150` B payload at `ARAM $5400`) and Slot
  `06` (Underground/Cave, vanilla `$1772`, `447` B payload at `ARAM $5400`)
  replace the placeholder blocks at `music-pack.bin` offsets `2490368` and
  `2530904`.
- Slot `1A` (Bowser Phase 3, vanilla `$1B64`, `924` B payload at `ARAM $5400`)
  replaces the `4DCBF0` (`0x26CBE8`) STAR block.
- `$0F:CF00` (`0x07CF00`) Sample Group entries for the 33 restored song slots
  (`02`, `03`, `05`, `06`, `19`, `1A`, `1E`, `2C`, `2E`, `2F`, `35`, `36`, `3A`–`3F`,
  `42`, `43`, `45`–`47`, `4C`, `4F`, `53`–`57`, `5B`, `5D`, `6D`) are set to `0x02`
  so `SRCN $20..$25` stay populated on direct room entry.
- `tools/adapt_song_base.py` uses the exact AddmusicM command parameter table at
  `ARAM $043E`/`$0F58` (`0xDF: 0`, `0xF0: 0`), fixing a missed `$E9` relocation
  at `0x28019A` in Slot `6D`.

ROM SHA-256 is `220c00cbafab815a9ec194d250c6ba330dd580032c806caa46c06a21144d36d6`
(CRC32 `1a575a2b`); `music-pack.bin` SHA-256 is
`b054d450165eb0f4a32f7a15f2f6c65e41389616da8a336b42bf9ec9bb032c47`. Native
captures with `M1_AUDIO_WAV` on rooms `02E`, `122`, `081`, `062`, `173`, and
`0A2` confirm `mode == 0x14`, `$7E:C112 == 0x02`, exact `ARAM $5400` payload
upload, and non-silent PCM output (`tests/test_vanilla_smw_music.py`).

## Room 0x081 custom sprite 0x0A restoration (`demo11-native-product-r42`, 2026-11-08)

Room `0x081` (Yoshi's Island 2 underground subroom, reached via screen exits from
rooms `0x03C` and `0x06C`) places custom sprite `0x0A` (`extra=2`, raw bytes
`49 91 0a`) at the end of the room (`X=0x0190, Y=0x0140`).

- In `cheap-demo`, custom sprite slot `0x0A` holds record
  `013601062f01196c20fc1340fc130000` (`INIT = $13:FC20`, `MAIN = $13:FC40`,
  885-byte RATS block at `$13:FBC5..$13:FF39`).
- In `demo-1-1`, custom sprite slot `0x0A` at `$31:8312` (`0x188312`) was
  overwritten by an unreachable test room `0x011` (`ザ・ワールド 時よ止まれ`)
  program (`012800003f9bb9c4be8313c283130000`, `INIT = $13:83BE`,
  `MAIN = $13:83C2`). Earlier sprite-coverage passes only checked for slots
  holding the default stub (`0000ffffffffffff218001218001ffff`) and skipped
  slot `0x0A`, leaving room `0x081`'s end-of-room custom sprite inert in `r41`
  (`num=0x28`, zero velocity, drawing four uninitialized `$7F:FFC0` tiles).
- `config/native-content/sprite0a-module.json` maps the `cheap-demo` 885-byte
  RATS block (`$13:FBC5..$13:FF39`, SHA-256
  `cf5559f3eaedcf809aeb0fbbeddbabc50b04f334b5b8d40a1c434d507c90abcf`) to low-mirror
  native bank `$86:FBC5` (`sprite0a-code.bin`, `INIT = $86:FC20`,
  `MAIN = $86:FC40`) with zero internal code edits, and
  `config/restorations/demo11-native-product-r42.json` patches `0x188312` to
  `013601062f01196c20fc8640fc860000`.
- `demo11-native-product-r42` ROM SHA-256 is
  `9f5403a46186d6f7415b98deb7a65646358c05837d77bb6c4d1836032329daa7`.
  Runtime captures (`local/captures/r42-room081-sprite0a-v2` vs
  `local/captures/cheap-demo-room081-sprite0a`) and `tests/test_room081_sprite0a.py`
  confirm that custom sprite `0x0A` initializes with `num=0x36` and
  `($1570 + $1558) & 0xFF == 0xD0`, moves horizontally (`$B6` alternating `0x08` /
  `0xF8`), jumps (`Y < 0x0140`), and spawns child projectile sprite `0xB3`.

## Full 256-slot custom sprite chronology audit and slots 6A/8C upgrade (`demo11-native-product-r43`, 2026-11-10)

Following user confirmation of `demo11-native-product-r42`, a 4-dimensional
automated audit across all 256 custom sprite slots (`0x00..0xFF`) and all 512
rooms (`0x000..0x1FF`) was executed across the official demo chronology
(`cheap-demo -> ow -> mazo -> 7hero -> boss -> demo-only-1 -> demo-1-1`):

1. **RATS Block & 65816 Instruction Integrity Audit**: Using `decode_function`
   seeded with `INIT`, `MAIN`, `JSL $0086DF`, and `JMP ($0000)` tables, all
   active in-ROM (`$10..$3F`) and native-pack (`$80..$BF`) custom sprite blocks
   in `r42` were verified to have zero unrelocated self-bank `JSL`/`JML` calls,
   zero escaped bank-local operands, and zero embedded `STAR` collisions
   (except `sprite7f-module`, which intentionally appends a 128-byte data block).
2. **Base-Address Normalized Equivalence (`is_pure_relocation`)**: Slots `0x09`,
   `0x35`, `0x4E`, and `0x9A` are pure base-address relocations with identical
   instruction streams. Slots `0x58` and `0x78` in `demo-only-1` differ from
   `cheap-demo` only by replacing inlined `JSR SubOffScreen` with `JSL $28:FD6D`
   (saving 115 and 117 bytes of ROM space with identical runtime semantics).
3. **Dynamic Custom Sprite Spawn (`STA $7FAB9E,x`) & Slot-Reuse Audit**:
   - In `demo-1-1`, slot `0x43` (`$32:CFB2` / `$32:D015`, 4,155 bytes)
     intentionally merges `demo-only-1`'s `extra=2` coin-drop controller
     (`$7FAB10,x & 0x04 == 0`, spawned by room `0x08F` boss slot `0x42` at
     `$23:CE38`) with room `0x179`'s `extra=3` world conquest rate screen
     (`$7FAB10,x & 0x04 != 0`).
   - In `Room 0x0FF`, the Seven Koopalings (`seven-code.bin` at `$A2:84D5`, slot
     `0x2A`) dynamically spawns custom sprite `0x6A` with state `$C2,x = 0x15`.
4. **Chronology Precedence Audit (Slots `0x6A` and `0x8C`)**:
   - Across all 256 slots, `Slot 6A` and `Slot 8C` were the only two remaining
     slots where `r42` still carried an older `cheap-demo` program instead of a
     newer official `7hero`/`boss` update:
     - **`Slot 6A`** (placed in rooms `0x0D8`, `0x0E2`, `0x0E3`, `0x0E4` and
       dynamically spawned in `Room 0x0FF` by `Slot 2A`): `r42` held `cheap-demo`'s
       `$20:BEE5` (`3,376` bytes, record `013610003b8b1840f4be203fbf200000`),
       which lacked state `0x15` handling, lacked the `LDA $010B; CMP #$FF` guard,
       lacked `$166E` bit `$20` (`0xAB`), and wrote `$7F:FDF0..$7F:FDF2` instead
       of `$7F:EDF0..$7F:EDF2`. `config/native-content/sprite6a-boss-module.json`
       maps the `7hero`/`boss` program (`$1E:C20E..$1E:CF46`, `3,385` bytes,
       SHA-256 `8301000a2fed1e9c534958f06ef1d82eeb7e62f92cce9ef674b1f369c4fd0dbb`)
       to `$87:C20E` (`INIT = $87:C21D`, `MAIN = $87:C265`, record
       `013610003bab18401dc28765c2870000` at `0x188912`).
     - **`Slot 8C`** (placed in rooms `0x0B0` and `0x16B`): `r42` held
       `cheap-demo`'s `$23:9A96` (`358` bytes, record
       `0136000035031944a79a23c39a230000`), which only checked Map16 tile
       `0x0005` (`LDA $03; CMP #$05`). In room `0x16B`, actor 6 (`cust=0x8C`)
       flew straight through the ceiling into out-of-bounds `Y=0xFEE9` (`C2=0x00`).
       `config/native-content/sprite8c-boss-module.json` maps the `7hero`/`boss`
       program (`$13:AC37..$13:AE07`, `465` bytes, SHA-256
       `cbc93d999faadc4fe56309d6739466c5f57f4ed93352ea94db8619f9b8711463`) to
       `$88:AC37` (`INIT = $88:AC48`, `MAIN = $88:AC62`, record
       `013600003503194448ac8862ac880000` at `0x188B32`).
   - `demo11-native-product-r43` ROM SHA-256 is
     `8400f89dcc552170373548d1f10a6dd147df9e7c7622e1ecf3ceb6f0b8180dbd`.
     Captures `local/captures/r43-room0d8-sprite6a` (`bank=87`
     `executed_page_instructions=102017`), `local/captures/r43-room0e3-sprite6a`
     (`bank=87` `executed_page_instructions=105`),
     `local/captures/r43-room16b-sprite8c` (`bank=88`
     `executed_page_instructions=41399`), and
     `local/captures/r43-room081-sprite0a` (`bank=86`
     `executed_page_instructions=33952`) confirm that in room `0x16B`, actor 6
     (`cust=0x8C`) now stops at ceiling `Y=0x00C9` in state `C2=0x01` (`AA=0x00`),
     matching `local/captures/type3-room16b-7hero-v1` (`tests/test_sprite6a_8c_boss_upgrade.py`).
5. **User Playtest Acceptance & Default Product Head Promotion**:
   - Following initial playtesting without issues, the user approved promoting
     `demo11-native-product-r43` as the default interactive native product head.
   - `tools/launch_native.py`, `tools/play_native_target.py`, and
     `tools/play_native_cheats.py` now default `--target` to
     `demo11-native-product-r43` (`65` mounted `BM_*` content packs in total).
     Historical milestone baselines (`demo11-native-product`, `r14` Windows bundle
     pin in `tools/package_windows_product.py`, `r22`, `r41`, `r42`) remain intact
     for reproducible regression checks.

## ROM-free Public Beta packaging (`demo11-native-product-r43`, 2026-11-10)

To distribute `demo11-native-product-r43` publicly on Linux and Windows without
shipping any Nintendo `Super Mario World` ROM image or extracted asset packs, and
without requiring Python on player machines:

- **`BMPT` v1 Delta Patch Container (`tools/build_smw_delta.py`)**:
  - Encodes `data/rom.sfc` plus all `65` runtime `BM_*` content packs (`50`
    `BM_SEVEN_CODE_PACK*` sprite-gap packs, `BM_NATIVE_CONTENT_PACK` `music-pack.bin`,
    and `14` `BM_SPRITE_GRAPHICS_PACK*` packs = `66` files, `4,503,021` bytes total)
    as a self-verifying binary delta (`patch/brutalmario.bmpatch`, `3,699,352` bytes,
    SHA-256 `1fce1fb0d6664283f2d43ead646cd1c32a2a1ea1bc5c750710ed9e6b55bdca93`)
    against the unmodified US **`Super Mario World (U) [!]`** ROM (`524,288` bytes
    headerless or `524,800` bytes `.smc` with 512-byte copier header, body SHA-256
    `0838e531fe22c077528febe14cb3ff7c492f1f5fa8de354192bdff7137c27f5b`).
  - Copies `738,774` bytes directly from the player's vanilla SMW ROM and RLE-encodes
    `344,260` zero bytes.
- **Zero-Dependency Native C Launcher (`recomp/bm_release_launcher.c`)**:
  - Compiled natively as `bin/bm_launcher` (Linux x86_64, `libc` only) and
    `bin/bm_launcher.exe` (Windows x86_64 `/MT`, UTF-16 Win32 APIs + `MessageBoxW`).
  - On first launch, scans the bundle root (or `--base-rom <path>`) for a `.sfc`/`.smc`
    file matching the US `Super Mario World (U) [!]` SHA-256, synthesizes and
    SHA-256-verifies all `66` runtime files under `data/`, exports the `65` `BM_*`
    environment variables, optionally applies `--unlock special-zone|complete-all`
    (backing up `saves/save.srm` to `saves/save.srm.before-cheat`), and launches
    `bin/BrutalMario[.exe] --config config/config.ini` with `cwd` anchored to the
    bundle root so paths with non-ASCII/CJK characters and spaces work cleanly on
    both OSes.
- **Cross-Platform Build, Qualification & Clean-Room Smoke Verification (`tools/package_public_beta.py`)**:
  - Linux x86_64 binary (`d3b7b6e7890abb0d6667b2615210d6842120d3fee16da9ef6748c4062507f45e`):
    60-frame qualification `guest_mean_ms = 9.139` ms (closed) / `11.652` ms (`help;close`).
  - Windows x86_64 binary (`local/build-windows/demo11-native-product-r43/BrutalMarioDemo11ProductR43SNESRecomp.exe`,
    SHA-256 `bb33edcc9e05e7396833540c49d86573c533803f475f9c01f7dd7aa703576656`, bundled
    with app-local VC143 `msvcp140.dll`, `vcruntime140.dll`, `vcruntime140_1.dll`):
    60-frame qualification `guest_mean_ms = 11.894` ms (closed) / `8.588` ms (`help;close`).
  - Cross-platform 60-frame state & pixel dumps (`wram.bin`, `vram.bin`, `sram.bin`,
    `cgram.bin`, `oam.bin`, `fb.bgrx`, `fb.bmp`) and CRLF-normalized register/APU/PPU
    logs match 100% byte-for-byte between Linux and Windows, both in qualification
    and in clean-room player extraction tests inside directories containing Chinese
    characters and spaces (`tests/test_public_beta_package.py`).
  - Generated ROM-free Public Beta archives (`dist/public-beta-r43/release-receipt.json`):
    - `dist/public-beta-r43/BrutalMario-PublicBeta-r43-Linux.zip` (`2,873,366` B,
      SHA-256 `a3b5a3c2bb2913ac0c93cbfbdebf3d1d629a808ca8f24a8ffcb159e3af0d0f72`)
    - `dist/public-beta-r43/BrutalMario-PublicBeta-r43-Windows.zip` (`4,030,433` B,
      SHA-256 `fd02cbfad75dfb1c171f325727a6bd9da2af118490b11cfaaf52b5b0be7401ce`)
  - Full unassisted human playthrough across every course and boss remains open, so
    these archives are framed as Public Beta builds.

## Room 0x134 ExGFX 0x1B2 restoration (`demo11-native-product-r44`, 2026-11-12)

In Room `0x134` (translevel `0x058`), custom sprite `0x98` already ran identically
in `r43` and `demo-only-1`, but Room `0x134`'s Super GFX Bypass table (`$14:AD08 +
0x134 * 32`) loads ExGFX `0x1B2` into SP4 (`VRAM 0xF000..0xFFFF`).

- In `r43`, the ExGFX `0x1B2` pointer at `$14:821E` (PC `0x0A021E` = `655902`)
  held `38f22f` (`$2F:F238`), an older `cheap-demo` `1,930`-byte LZ2 stream in
  which NT1 tiles `A8..AB`, `AE..AF`, `B8..BB`, `BE..BF`, `CE..CF`, and
  `DE..DF` were zeroed.
- In `demo-only-1`, ExGFX `0x1B2` at `$20:F10C` (`2,175`-byte LZ2 stream, SHA-256
  `c045d50b8c107e807c9c661177940667f47b8c38ae0674203a035d8ee0f22778`; `4,096`-byte
  decoded SP4 image SHA-256
  `23c81a9ae6106d21facd642e54e1a6b9ec338c2f19ca1b03f06548198b14d529`) adds those
  exact 16 tiles from zero (`0` modified, `0` zeroed): sun (`AE,AF,BE,BF`),
  horizon glow (`CE,CF,DE,DF`), and moving snow/ice platform (`A8..AB,B8..BB`).
- `tools/prepare_product_r44.py` extracts the `demo-only-1` stream into
  `local/native-modules/exgfx-1b2-v1/exgfx-1b2.bin`, generates
  `config/restorations/demo11-native-product-r44.json` (with all 50 sprite-gap
  manifests frozen and `BM_EXGFX_1B2_PACK` mounted at `$D2:8000`), and patches
  the 3 bytes at `0x0A021E` from `38f22f` to `0080d2`.
- `demo11-native-product-r44` ROM SHA-256 is
  `8014c789ac9bf9f79d2972f7100ae2c677d7f7489e49c87801dadd4340d4a69b` (`66`
  mounted `BM_*` content packs, `67` encoded files total).
- Runtime captures `local/captures/r44-room134-sun` (vs
  `local/captures/diag-room134-do1-ref`) and `local/captures/r44-room174-exgfx1b2`
  confirm SP4 `VRAM[0xF000:0x10000]` matches `demo-only-1` byte-for-byte,
  `room134_f60.fb.bgrx` renders the sun at `(128, 64)` as `RGB(255, 255, 156)`
  with scanlines spanning `y=49..78, x=113..142` (`724` pixels), and shared
  ExGFX `0x1B2` room `0x174` loads SP4 cleanly (`tests/test_room134_exgfx1b2.py`).
- Default `--target` in `tools/launch_native.py`, `tools/play_native_target.py`,
  `tools/play_native_cheats.py`, `tools/build_smw_delta.py`, and
  `tools/package_public_beta.py` is promoted to `demo11-native-product-r44`
  (preserving `dist/public-beta-r43/` intact).
- Public Beta `r44` bundles (`dist/public-beta-r44/release-receipt.json`,
  `BMPT` v1 delta `3,701,596` B, SHA-256
  `54576443b2696745ff31359dfa571cc80cb7fbf9beabea176cadafe2658dfde8`):
  - `dist/public-beta-r44/BrutalMario-PublicBeta-r44-Linux.zip` (`2,875,015` B,
    SHA-256 `8efc8ff135d7543ba90145b12517f2a7a1c6287768850d01193a5dfea0828299`)
  - `dist/public-beta-r44/BrutalMario-PublicBeta-r44-Windows.zip` (`4,032,142` B,
    SHA-256 `242d1f9cbd10575f62cf8720d87d63d911b79466e22236f4fe026ff6a71da77b`)

## ExGFX 0x257 repair & pure-addition/NULL-pointer batch restoration (demo11-native-product-r45, 2026-11-12)

- **Root cause & scope**:
  - ExGFX `0x257` pointer at `$14:840D` (PC `0x0A040D`, `88cc42` -> `$42:CC88`) was
    corrupted when `r34` merged `boss` music data over bank `0x42`, breaking Wily Capsule
    Phase 2 (`sprite2e` state `8` / `0B` / `0E` / `11` calls to `$85:A997` / `$85:AAE3`).
  - Five additional ExGFX entries in `demo11-native-product-r44` had pure tile additions in
    newer official donors (`boss` for `0x1E3`; `demo-only-1` for `0x163`, `0x18F`, `0x192`,
    `0x1AE`) with zero removed or modified existing tiles (`-0`, `~0`).
  - Two ExGFX slots pointed to NULL `$00:0000` in the `$0F:F600` low table despite active
    room usages: `0x0DA` (PC `0x07F70E`, restored from `boss` `$4A:94A6`) and `0x0BE`
    (PC `0x07F6BA`, restored from `demo-only-1` `$28:DCE8`).
- **Recipe & pack**:
  - `tools/prepare_product_r45.py`, `config/restorations/demo11-native-product-r45.json`
    (descendant of `demo11-native-product-r44`, ROM `4,194,304` B, SHA-256
    `d13003a1e9a7c0a473f97af885a0740cdb40539d2b10b30c4f5fa676de7611e2`, exact 24-byte
    pointer diff across 8 slots).
  - Consolidated non-executable native pack `BM_EXGFX_R45_PACK` at `$D3:8000`
    (`local/native-modules/exgfx-r45-v1/exgfx-r45.bin`, `14,530` B, SHA-256
    `965b85b0ea22473deb44a74eab0e57c0a0f2d38658cbbf16420f8089df22252a`), concatenating in
    exact order:
    1. `0x257` (`boss` `$3C:921A`, `2204` B -> `4096` B): PC `0x0A040D`, `88cc42` ->
       `0080d3` (`$D3:8000`) — restores `sprite2e` Wily Capsule Phase 2 graphics.
    2. `0x1E3` (`boss` `$32:E5D0`, `2551` B -> `4096` B): PC `0x0A02B1`, `49c44c` ->
       `9c88d3` (`$D3:889C`) — pure `+105`-tile upgrade for room `0x0E4` SP4.
    3. `0x163` (`demo-only-1` `$20:C8CA`, `1148` B -> `4096` B): PC `0x0A0131`, `08b24c` ->
       `9392d3` (`$D3:9293`) — pure `+1`-tile upgrade for rooms `0x072, 0x117, 0x125, 0x176`
       SP2.
    4. `0x18F` (`demo-only-1` `$20:D41C`, `1213` B -> `4096` B): PC `0x0A01B5`, `2dbd5c` ->
       `0f97d3` (`$D3:970F`) — pure `+8`-tile upgrade for rooms
       `0x022, 0x097, 0x098, 0x09D, 0x175` SP4.
    5. `0x192` (`demo-only-1` `$20:DBB6`, `917` B -> `4096` B): PC `0x0A01BE`, `f8b65c` ->
       `cc9bd3` (`$D3:9BCC`) — pure `+8`-tile upgrade for rooms `0x022, 0x175` BG3.
    6. `0x1AE` (`demo-only-1` `$20:DF53`, `1548` B -> `4096` B): PC `0x0A0212`, `d8d934` ->
       `619fd3` (`$D3:9F61`) — pure `+5`-tile upgrade for rooms `0x117, 0x176` BG2.
    7. `0x0DA` (`boss` `$4A:94A6`, `2768` B -> `4096` B): PC `0x07F70E`, `000000` ->
       `6da5d3` (`$D3:A56D`) — restores NULL `$0F:F600` pointer for rooms `0x0EE, 0x152` BG3.
    8. `0x0BE` (`demo-only-1` `$28:DCE8`, `2181` B -> `4096` B): PC `0x07F6BA`, `000000` ->
       `3db0d3` (`$D3:B03D`) — restores NULL `$0F:F600` pointer for rooms
       `0x062, 0x06C, 0x0C2` ANM.
- **Verification**:
  - `local/captures/r45-room0e4-exgfx1e3` (`recomp/inputs/seven-child-existing-0e4.script`):
    `bank=D3 resolutions=5102`, `existing_later.vram.bin[0xF000:0x10000]` matches `boss`
    `0x1E3` (`4096` B).
  - `local/captures/r45-room175-exgfx18f-192` (`recomp/inputs/native-modern-175.script`):
    `bank=D3 resolutions=7928`, `f512.vram.bin[0xF000:0x10000]` matches `demo-only-1`
    `0x18F` (`4096` B), `f512.wram.bin[0xAD00:0xBD00]` matches `demo-only-1` `0x192`
    (`4096` B), and `f512.vram.bin[0x3000:0x4000]` matches `0x192` on `126/128` tiles
    including all 8 added tiles (`0x4C..0x4F`, `0x5C..0x5F`).
  - `local/captures/r45-multi-rooms` (`local/probes/r45-exgfx/r45-rooms.script`, labelled
    pipe-transfer + invulnerability fixture): `bank=D3 resolutions=15290`; `r176` exact
    4096B matches for `0x163` (`VRAM[0xE000:0xF000]`), `0x1AE` (`VRAM[0x2000:0x3000]`), and
    `0x1B2` (`VRAM[0xF000:0x10000]`); `r152` exact 4096B match for `0x0DA`
    (`VRAM[0x3000:0x4000]`); `r062` `107/128` static tiles in `VRAM[0xC000:0xD000]` match
    `0x0BE` (remaining 21 are player dynamic DMA slots); `r134` preserves `724` setting sun
    `RGB(255,255,156)` pixels.
  - `local/captures/r45-room15d-wily257`
    (`local/probes/r45-exgfx/r45-room15d-wily257.script`, labelled pipe-transfer +
    invulnerability + P1->P2 state-transition diagnostic fixture): `bank=85
    resolutions=774838 executed_page_instructions=116167`, `bank=D3 resolutions=4408`;
    `p2_wily257` (`room=0x15D`, `$7FFF90=0x0257`) decodes `boss` `0x257` verbatim to
    `WRAM[0x0AD00:0x0BD00]` (`4096` B) and DMAs all 10 `sprite2e` BG3 slices
    (`0x3100..0x3EC0`) into VRAM.
  - `tests/test_exgfx_r45_batch.py`, `tests/test_room134_exgfx1b2.py`, and
    `tests/test_public_beta_package.py` pass.
- **Public Beta promotion (`demo11-native-product-r45`)**:
  - Default `--target` promoted to `demo11-native-product-r45` in `tools/launch_native.py`,
    `tools/play_native_target.py`, `tools/play_native_cheats.py`, `tools/build_smw_delta.py`,
    and `tools/package_public_beta.py` (`67` `BM_*` runtime packs / `68` manifest files,
    `BMPT` v1 delta `3,716,170` B, SHA-256
    `7f2f9702abb2ca87af9341e1318eae025b12682c92c57fe9ae563ffcacd8bb36`):
    - `dist/public-beta-r45/BrutalMario-PublicBeta-r45-Linux.zip` (`2,887,397` B,
      SHA-256 `ad59fe0f4d137ec89f5c91af126d2fbad9d3714d3a23afb9fcb1201406955ba4`)
    - `dist/public-beta-r45/BrutalMario-PublicBeta-r45-Windows.zip` (`4,044,401` B,
      SHA-256 `974e3b524341ccbf1747dae9653701d038a7cf90cefdf7403465ea8f38d5c864`)
    - Linux vs Windows binary parity & clean-room Unicode path ZIP smoke tests pass
      (`Linux guest_mean_ms`: closed `4.458`, console `4.402`; `Windows guest_mean_ms`:
      closed `3.990`, console `3.931`).
- **Deferred ExGFX & non-upgrade notes**:
  - Deferred for visual/layout review (not upgraded in `r45` because existing tiles are
    modified or zeroed):
    - `0x1AF`: `demo-only-1` `$20:E567` (`1629` B) vs `r44` `$34:C6B8` (`1612` B) has `+3`
      added (`4D, 5C, 5D`), `~5` modified (`4C, 4E, 4F, 5E, 5F`), `-0`, `same=106`; used in
      rooms `0x117(s1), 0x164(s1), 0x165(s1), 0x166(s1), 0x176(s1)`.
    - `0x1B0`: `demo-only-1` `$20:EBCC` (`1336` B) vs `r44` `$34:85E8` (`1268` B) has `+6`
      added (`02, 12, 24, 25, 34, 35`), `-2` zeroed (`04, 14`), `~4` modified
      (`05, 06, 15, 16`), `same=68`; used in rooms `0x117(s3), 0x176(s3)`.
  - Non-upgrade rule (`0x400`, `0x401`): `r44` preserves `boss` / `cheap-demo` room `0x13B`
    (`0x400` at `$44:E240`, `2074` B; `0x401` at `$44:EA62`, `2952` B; identical Layer 1 /
    Sprite / `$14:AD08` across official demos through `boss`). `demo-only-1` repurposed
    `0x400`/`0x401` (`$23:BE92` `1913` B, `$23:C613` `2305` B) for its own room `0x168`
    with unrelated artwork (`same=0` tiles). Do not overwrite `r44` `0x400`/`0x401` from
    `demo-only-1`.

## Room `0x1C5` opening story cutscene (`demo11-native-product-r46`)

- **Problem**: `demo11-native-product-r45` inherited `demo-1-1`'s `24`-byte Message 1 stub in
  Room `0x1C5`, disabled Super GFX Bypass, pointed `$00:9EF0` submap `0x00` through
  `$13:EDAF` (`TYA; BEQ` -> `0x0C5` Yoshi's House), and lacked `cheap-demo` ExGFX
  `0x239/0x23A/0x23C` and the Japanese `GFX 0x02A` font tiles needed by custom Sprite `0x00`'s
  opening story sequence (`0x1C5 -> 0x14B -> 0x14C -> 0x14D -> World 1 Overworld`).
- **Recipe & packs**:
  - `tools/prepare_product_r46.py`, `config/restorations/demo11-native-product-r46.json`
    (descendant of `demo11-native-product-r45`, ROM `4,194,304` B, SHA-256
    `142ee768d1d5cd436a17d459719b30a02ba5dafaa79271b9d3c37da4965a0b7e`, exact `56`-byte
    diff across `15` patches).
  - `BM_ROOM1C5_R46_DATA_PACK` at `$D4:8000`
    (`local/native-modules/room1c5-r46-v1/room1c5-r46-data.bin`, `14,181` B, SHA-256
    `754eadae48ceb2376090d2ca43148ff3c47d6af90071c3f8952dd1e72ac36a07`, non-executable):
    1. `$D4:8000` (`3,099` B): `cheap-demo` ExGFX `0x23A` LZ2 (`$45:CF66`), mounted at
       `$14:83B6` (PC `0x0A03B6`).
    2. `$D4:8C1B` (`3,250` B): `cheap-demo` ExGFX `0x239` LZ2 (`$43:EB1E`), mounted at
       `$14:83B3` (PC `0x0A03B3`).
    3. `$D4:98CD` (`2,655` B): `cheap-demo` ExGFX `0x23C` LZ2 (`$45:E484`), mounted at
       `$14:83BC` (PC `0x0A03BC`).
    4. `$D4:A32C` (`514` B): `cheap-demo` Room `0x1C5` Custom Palette (`$57:DA95`),
       mounted at `$0E:FB4F` (PC `0x077B4F`).
    5. `$D4:A52E` (`546` B): `cheap-demo` Room `0x1C5` Layer 1 (`$57:A065`) with music byte
       patched `40 60 44 ff` -> `40 60 5a ff` (modern slot `$59`, *Aboard the Hilda Garde*),
       mounted at `$05:E54F` (PC `0x02E54F`).
    6. `$D4:A750` (`16` B): `cheap-demo` Room `0x1C5` Layer 2 RLE stream (`$57:A28F`),
       mounted at `$05:EB4F` (PC `0x02EB4F`).
    7. `$D4:A760` (`5` B): `cheap-demo` Room `0x1C5` Sprite list (`$57:DC9F`, `00e83000ff`),
       mounted at `$05:EF8A` / `$0E:F2C5` (PC `0x02EF8A` / `0x0772C5`).
    8. `$D4:A765` (`2,048` B): decoded `cheap-demo` Japanese `GFX 0x02A` (SHA-256
       `2f0619a305c515d72c4707dd7f18a792dcc376d3a5ac65adab35e68e75e15e1f`).
    9. `$D4:AF65` (`2,048` B): decoded `r45` / `demo-1-1` English `GFX 0x02A` (SHA-256
       `310facf09c5f280859dcfcf4da215c63089377af4802aabea31e49ce5f09d0fa`).
  - `BM_ROOM1C5_R46_CODE_PACK` at `$89:B000`
    (`local/native-modules/room1c5-r46-v1/room1c5-r46-code.bin`, `123` B, SHA-256
    `33d8328acd5aacf08ee50f332e1a12e3a6e7245e51d6b36fd826ce22f8721398`, executable LoROM
    mirror bank `$89`):
    - `$89:B000` (hooked from `$3F:E296`, `JSL $89B000; NOP`): DMA2 uploads Japanese `GFX 0x02A`
      (`$D4:A765`) to VRAM word `$4800` while preserving full 16-bit `C`, `P`, `X`, `Y`, `DB`,
      `D`, then replays `LDA #$FF; STA $18BD; RTL`.
    - `$89:B040` (hooked from `$3F:E44D`, `JSL $89B040; NOP`): DMA2 restores English `GFX 0x02A`
      (`$D4:AF65`) to VRAM word `$4800` when `0x14D` exits to the Overworld, then replays
      `STZ $18BD; LDA #$A0; RTL`.
  - Supporting patches: Room `0x1C5` secondary headers (`$05:F1C5` `5b`->`83`, `$0E:F4D5`
    `00`->`02`), `32`-byte Super GFX Bypass (`$14:E5A8`), New-Save silence slot `$1E`
    (`$00:9724` `01`->`1e`), and `$13:EDAF` (`98f006`->`eaeaea`) so New Save (`$0100>=$0B`
    and `$0109!=0`) enters `0x1C5` even with World 1 `$1F11==0x00`.
- **Verification**:
  - `local/captures/r46-room1c5-intro` (`recomp/inputs/native-room1c5-intro.script`, `--audio`):
    unassisted Boot -> Title (`0x00C7`, `mode=0x07`, `$0DDA=0x02`, audio `rms=589.09`) ->
    File Select (`mode=0x08`) -> New Save File A -> `0x1C5 -> 0x14B -> 0x14C -> 0x14D`
    (`bank=D4 resolutions=42488 executed=0`, `bank=89 resolutions=1712 executed=260`; `0x239` at
    `VRAM[0x2000:0x3000]`, `0x23A` at `VRAM[0x3000:0x4000]`, `0x23C` matching `116/128` static
    tiles at `VRAM[0x1000:0x2000]`, custom CGRAM matching `cheap-demo` `PAL_1C5` except animated
    word `0x64`, Japanese `GFX 0x02A` at `VRAM[0x9000:0x9800]`, streamed `$39xx` BG3 subtitle
    tiles in `VRAM[0xB200:0xB600]` across all `4` scenes, `$0DDA=0x1E` and `audio.wav` silence
    `rms=0.00` during cutscene) -> natural exit to World 1 Overworld (`mode=0x0E`,
    `submap=0x00`, `$0109=0x00`, English `GFX 0x02A` restored byte-for-byte at
    `VRAM[0x9000:0x9800]`, `"Hey, I am Mario!"` BG3 HUD row 4 intact, Overworld BGM
    `rms=1067.29`) -> Course `1-1` (`0x105`) entry from `(0048, 0198)` -> reset + File A reload
    landing directly on Overworld `(0048, 0198)` without replaying intro.
  - `local/captures/r46-room1c5-skip2` (`recomp/inputs/native-room1c5-skip.script`): `Start`
    pauses (`$13D4=1`) and unpauses (`$13D4=0`), and `A`/`B` skips `0x1C5 -> 0x14B -> 0x14C ->
    0x14D -> Overworld` with English `GFX 0x02A` restored.
  - `local/captures/r46-reg-room175` (`recomp/inputs/native-modern-175.script`): `r45` ExGFX
    `0x18F` / `0x192` and bank `D3` remain intact (`0x18F` exact at `VRAM[0xF000:0x10000]`,
    `0x192` exact at `WRAM[0xAD00:0xBD00]`, `126/128` tiles at `VRAM[0x3000:0x4000]`).
  - `tests/test_room1c5_intro_cutscene.py`, `tests/test_exgfx_r45_batch.py`, and
    `tests/test_public_beta_package.py` pass.
- **Public Beta promotion (`demo11-native-product-r46`)**:
  - Default `--target` promoted to `demo11-native-product-r46` in `tools/launch_native.py`,
    `tools/play_native_target.py`, `tools/play_native_cheats.py`, `tools/build_smw_delta.py`,
    and `tools/package_public_beta.py` (`69` `BM_*` runtime packs / `70` manifest files,
    `BMPT` v1 delta `3,730,473` B, SHA-256
    `ed885d5a874401a780ab3299e3e71a1746036613d9ea5e2323629be8e8c911cc`):
    - `dist/public-beta-r46/BrutalMario-PublicBeta-r46-Linux.zip` (`2,897,966` B, SHA-256
      `9cb5d23e5f9c78e0353d078cbc3d50a52c8b12aa68b17c51888744b4fcddb23f`)
    - `dist/public-beta-r46/BrutalMario-PublicBeta-r46-Windows.zip` (`4,055,052` B, SHA-256
      `e4a63ef437bd5ab18a94118262c503a60572626a34ea14cd371125ae65b09508`)
    - Linux vs Windows binary parity & clean-room Unicode path ZIP smoke tests pass
      (`Linux guest_mean_ms`: closed `4.665`, console `4.640`; `Windows guest_mean_ms`:
      closed `4.001`, console `4.126`).


## Multi-language EN/JA switching (`demo11-native-product-r47`)

- **Problem**: Official Japanese demos through `boss` share Japanese `GFX 0x28`/`0x2A`/`0x2B`
  fonts, `boss` Overworld level names (`96` slots), `boss` message boxes (`144` slots), and
  Mazo `0x191`/`0x192` Japanese messages, whereas `demo6`/`demo7`/`demoOnly1`/`Demo 1-1`
  replaced `GFX 0x2A` (`$4800..$4BFF`) with English tiles while translating only a small subset
  of strings (`10` Overworld names + `4` non-tutorial message boxes), causing untranslated
  Japanese strings in English builds to render as mojibake (`乱码`) and offering no Japanese UI
  option.
- **Data audit & `BMLG` v1 pack**:
  - `tools/audit_localization.py` + `config/native-content/localization-audit-r47.json` audit the
    10 official ROMs (`demo6 -> demo6.5 -> demo7 -> cheap_demo -> ow -> mazo -> 7hero -> boss ->
    demoonly1 -> 1-1`) and deterministically build `lang-r47-data.bin` (`BMLG` v1, `30,814` B,
    SHA-256 `dc88751479e1342c31da4fd292a8c371b4c792179de547439b258ee24f7b819a`):
    - **Japanese payload (`boss` + Mazo)**: `boss` Layer 3 fonts (`GFX 0x28`/`0x2A`/`0x2B`),
      Title stripe image, `96` Japanese Overworld level names (`$15:827F`), `144` Japanese SMW
      message boxes (`$15:89A7`), and Mazo `0x192`/`0x191` Japanese messages (`70` B / `86` B).
    - **English payload + auto-JP fallback**: newest-first official English merge (`Demo 1-1 >
      demoOnly1 > demo7 > demo6`, excluding untouched vanilla US SMW tutorial messages on cleared
      slots) paired with per-slot/per-room `needs_jp_font` tables so untranslated Japanese
      strings and Japanese rooms (`0x0FF`, `0x17B`, `0x191`, `0x192`, `0x1C5..0x14D`) in EN mode
      automatically display with Japanese `GFX 0x2A` instead of garbled glyphs.
- **Recipe, packs & runtime UI**:
  - `tools/prepare_product_r47.py` + `config/restorations/demo11-native-product-r47.json`
    (descendant of `demo11-native-product-r46`, ROM `4,194,304` B, SHA-256
    `2123f5e3415364d3a5def92b8ac3ab1f581ec68f0cf6469ffda12f4a9da80b0a`, `8` code hooks across
    `0005D4`, `003A28`, `01BB20`, `01BB90`, `01BBC9`, `02B11D`, `1FE296`, `1FE44D`):
    - `BM_LANG_R47_DATA_PACK` at `$D5:8000` (`30,814` B, SHA-256 `dc887514...`, non-executable).
    - `BM_LANG_R47_CODE_PACK` at `$90:8000` (`4,096` B, SHA-256
      `ea1c8cef78d1f32b68fa9db0dfdc5767f11d3ad36fa9f94aff9df75555e0deb8`, executable LoROM
      system-mirror bank `$90`), reserving `$90:8FF0..8FFF` (`0`-initialized on disk) with
      `$90:8FF0` carrying host `effective_lang` (`0 = en`, `1 = ja`) and queuing mid-frame-safe
      `GFX 0x2A` VRAM updates through SMW's `$10:D8D0` NMI VBlank scheduler.
  - Runtime & host patches (`patches/runtime/0014..0016` in `config/runtime-patches.json`),
    `recomp/native_seven.c` (`#ifdef BM_LANG_R47_SUPPORT`), and `recomp/bm_release_launcher.c`:
    - `Esc` (single-player idle) / `O` opens the `GAME SETTINGS` modal (`ENGLISH` / `JAPANESE` /
      `AUTO (SYSTEM)`) and `~` console supports `lang [en|ja|jp|auto|toggle]`.
    - Live hot-swap immediately updates `$90:8FF0`, VRAM Layer 3 font tiles (`$4000`, `$4800`,
      `$4C00`), active Overworld 19-tile banner (`$508B..$509D`, resolved via hovered banner
      tiles so stale `$13BF` does not misindex), and any open `8x18` message box without
      touching `save.srm`, persisting `[General] Language = auto|en|ja` in `config.ini`.
    - First-launch `auto` defaults to `ja` strictly on Japanese OS locales (`LANG_JAPANESE` on
      Win32; `LC_ALL` > `LC_MESSAGES` > `LANG` starting with `ja` case-insensitively on POSIX)
      and `en` on all other locales; `--lang en|ja|auto` overrides on `bm_launcher` and
      `tools/launch_native.py` / `tools/play_native_target.py` / `tools/play_native_cheats.py`.
- **Verification**:
  - Headless E2E captures under `local/captures/r47-*` verified EN & JA Title `GFX 0x28/0x2A/0x2B`
    + Title stripe, `0x1C5 -> 0x14D -> Overworld` (`ja_gfx02a` retained on OW in `ja`, `en_gfx02a`
    restored on EN-named OW node in `en`), untranslated JP OW node (`0x28`) & JP message (`0x106`)
    auto-switching `GFX 0x2A` to Japanese in EN mode, Mazo `0x191` (`$1426==2`) & `0x192`
    (`$1426==1`) diagnostic teleport+poke fixtures rendering Japanese text and restoring `en_gfx02a`
    on close, `GAME SETTINGS` overlay dump (`SNESRECOMP_SETTINGS_MENU=1`), live Overworld banner
    + font round-trip hot-swap (`en -> ja -> en`, `$13BF == 0x00` on `0x29`, `save.srm` invariant),
    and `native-room1c5-intro.script` / `native-room1c5-skip.script` / `native-modern-175.script`
    regressions.
  - Full repository unit test suite: `python3 -m unittest discover -s tests -p "test_*.py" -v`
    passed **586/586** (`0` failures, `0` errors, `0` skipped); `local/upstream/snesrecomp` clean.
- **Public Beta promotion (`demo11-native-product-r47`)**:
  - Default `--target` promoted to `demo11-native-product-r47` across launch, delta, and
    packaging tools (`71` `BM_*` runtime packs / `72` manifest files, `BMPT` v1 delta `3,758,610`
    B, SHA-256 `b893d48681a98ecfee7ff3434998cd4ead152343656e03ffea09df0dc0770be0`):
    - `dist/public-beta-r47/BrutalMario-PublicBeta-r47-Linux.zip` (`2,910,207` B, SHA-256
      `d5420e784a6fc211be656cf8257e9004a7a1a194ed3b2a34e06816d8282a917d`)
    - `dist/public-beta-r47/BrutalMario-PublicBeta-r47-Windows.zip` (`4,065,802` B, SHA-256
      `c6c257d92f52f3ba54fa4cccd2d1c3d45e63f45873edf9d04eec6af12a91fbf0`)
    - Linux vs Windows binary parity & clean-room Unicode path ZIP smoke tests pass
      (`Linux guest_mean_ms`: closed `4.858`, console `4.981`; `Windows guest_mean_ms`:
      closed `4.326`, console `4.257`), including clean-room `cheat-complete-all.script`
      (Linux) and `cheat-special-zone.script` (Windows) smoke runs after syncing
      `recomp/inputs/cheat-complete-all.script`, `recomp/inputs/cheat-special-zone.script`, and
      `tools/play_native_cheats.py` (`STARTUP`/`FAST_STARTUP`) to skip all `4` scenes
      (`0x1C5 -> 0x14B -> 0x14C -> 0x14D -> 0x0E`); historical `dist/public-beta-r43..r46/`
      preserved.


## Room 0x116 countdown & Super GFX Bypass SP2 protection (demo11-native-product-r48)

- **Problem & 65816 root cause**:
  - Room `0x116` (`translevel 0x03A`, Skull Coaster / *Ghost Special*) renders custom sprite `0x45`
    (`$34:84A2` via `$31:86CA`, OAM tiles `$80..$89`/`$90..$99`, prop `$22`, `SP2` VRAM word
    `$6800`) using Super GFX Bypass `SP2 = ExGFX 0x12A` (red brush-stroke countdown digits
    `0..9`, `4,096` B LZ2-decompressed), while the vanilla header sprite table (`$00:A8C3`,
    indexed via `$192B = $01`) gives `$06 = $01`.
  - Inside `$00:AA35 -> JSR $AA6B -> JSL $0FF160 -> $0F:F840`, Super GFX Bypass decompresses
    `ExGFX 0x12A` into `$7E:AD00`, then `$0F:F882: PLY` restores stale vanilla `Y = $01`. Back at
    `$00:AA6F: CPY #$01 / BNE $AA80 / LDA $1F01 / BPL $AA80 / LDY #$31 / JSL $00BA28`, whenever
    `$1F01` bit 7 is set (e.g., via the `complete` cheat writing `$1EA2..$1F01 = $9F` or a saved
    `save.srm` from `complete`), SMW overwrites `$7E:AD00..$7E:B4FF` with `2,048`-byte vanilla
    `GFX 0x31` (red berry / white creature).
  - Blast radius across all `512` rooms (`$14:AD08 + room*32` vs `$00:A8C3`, where all `16`
    vanilla sprite sets have `vanilla_sp2 == 0x01`): **127** Super GFX Bypass rooms (`43` in
    `config/demo11-level-index.json`) have `vanilla_sp2 == 0x01` and `super_sp2 != 0x0001`
    (including `0x116` = `0x012A`, `0x007` = `0x012A`, `0x105` = `0x029F`), whereas **385**
    rooms (**235** Super GFX Bypass `super_sp2 == 0x0001`, e.g. `0x101`, plus **150** vanilla
    fallback, e.g. `0x104`) have `effective_sp2 == 0x0001` where Autumn `GFX 0x31` is legitimately
    expected (`$01:9825` / `$01:B9CC` also inspect `$1F01` bit 7).
- **Recipe & 3 ROM patches**:
  - `tools/prepare_product_r48.py` + `config/restorations/demo11-native-product-r48.json`
    (descendant of `demo11-native-product-r47`, ROM `4,194,304` B, SHA-256
    `bbd52ff43fe86e872ee2c55da7adf40ca0eb52e117d529bc5449f3aae5b1bc52`, `71` `BM_*` packs /
    `72` manifest files with `frozen_manifests` preserving all `50` `r47` manifests and `16`
    `extra_packs`, `recomp/targets/demo11-native-product-r48/symbols.toml` preserving all `11`
    `r47_*` `bank = 144, emit = false` entries).
  - `3` ROM patches (`002A6F`: `c001 -> c901`, `07F19B`: `20b7f1 -> 208cf8`, `07F884..07F8A1`:
    `30`-byte `$0F:F840` epilogue update
    `a9016020b7f180f5ffffffffffffffffffffffffffffffffffffffffffff -> a902604c92f8eaea4820b7f168604820b7f168c90100d0e5287afaa90160`)
    return effective GFX indicator `A = $01` from `$0F:F160` iff effective decompressed GFX ID
    `== $0001` (`$02` for other Super GFX Bypass slots), keeping vanilla `Y` and `$0F:F160` entry
    stack depth (`$0F:F160: A3 04`) intact, and test `CMP #$01` at `$00:AA6F` while preserving `Y`
    for `$00:AA8C`/`$00:AA90`.
  - Registered `'demo11-native-product-r48'` (`BrutalMarioDemo11ProductR48SNESRecomp`) in
    `tools/restoration_targets.py`.
- **Verification & Public Beta `r48` promotion**:
  - Captures under `local/captures/r48-*`:
    - `local/captures/r48-repro-r47-room116-complete`: read-only `r47` repro in Room `0x116`
      (`$1F01 = 0x9F`), confirming `VRAM[0x6800*2 : 0x6800*2+2048] == lz2(r47, 0x31)`.
    - `local/captures/r48-verify-room116-normal`: `r48` Room `0x116` (`$1F01 = 0x1F`),
      `VRAM[0x6800*2 : 0x7000*2] == lz2(r48, 0x12A)` (`4,096` B), OAM countdown digits `09`
      (`0x80`/`0x90`, `0x89`/`0x99`, prop `0x22`), `0` `BRK`.
    - `local/captures/r48-verify-room116-complete`: `r48` Room `0x116` post-`complete`
      (`$1F01 = 0x9F`), `VRAM[0x6800*2 : 0x7000*2] == lz2(r48, 0x12A)`, OAM digits `09`
      (`prop=0x22`), `146` red `(247, 8, 8)` pixels in digit bounding box, `0` `BRK`; visual
      verification screenshot `local/reports/r48-room116-complete-after.png` (`4,035` B,
      `256x224` RGBA PNG).
    - `local/captures/r48-verify-room007-complete`: `r48` Room `0x007` (Cave Star, `SP2 = 0x012A`,
      `$1F01 = 0x9F`), `VRAM[0x6800*2 : 0x7000*2] == lz2(r48, 0x12A)`, OAM digits `06`
      (`prop=0x22`), `0` `BRK`.
    - `local/captures/r48-verify-room104-autumn`: `r48` Room `0x104` (Yoshi's House, vanilla
      `SP2 = $01`, `$1F01 = 0x9F`), `VRAM[0x6800*2 : 0x6800*2+2048] == lz2(r48, 0x31)`, `0` `BRK`.
  - `tests/test_room116_countdown_gfx.py` (config/lineage/`symbols.toml`/3 patches/71 packs,
    512-room static audit, headless `0x116` normal & `$1F01=0x9F`, `0x104`/`0x101` positive
    controls, and `0x105` `ExGFX 0x29F` preservation),
    `tests/test_public_beta_package.py::test_r48_delta_patch_roundtrip_and_manifest`, and the
    full repository unit test suite (`python3 -m unittest discover -s tests -p "test_*.py" -v`
    recorded in `local/reports/unit-tests-r48.log`: **591/591** passed in `236.494s`, `0`
    failures, `0` errors, `0` skipped).
  - Default `--target` promoted to `demo11-native-product-r48` across `tools/launch_native.py`,
    `tools/play_native_target.py`, `tools/play_native_cheats.py`, `tools/build_smw_delta.py`,
    and `tools/package_public_beta.py` (`--out-dir` `dist/public-beta-r48`, `--diag-dir`
    `local/diagnostics/public-beta-r48`; `71` `BM_*` runtime packs / `72` manifest files, `BMPT`
    v1 delta `3,758,449` B, SHA-256
    `7feba77824945c8d69d11c0bf41c8e7f07798fb2c7f39262ddcff9c1664bb080`):
    - `dist/public-beta-r48/BrutalMario-PublicBeta-r48-Linux.zip` (`2,909,856` B, SHA-256
      `b479cff7bdea4bdcb3a0ad2f5e33a4f88d20b9a24e8868949837f86087059e17`; `linux_binary_sha256`
      `6f20815c85cc0e582175691972553c74d838c86e556bbd9268b3867cd4b2a0cd`, `linux_launcher_sha256`
      `6a16d1b9f51b4d4a0e332e8f51db4e8f8dd45d9bf313d115ade3fd8236feb11c`)
    - `dist/public-beta-r48/BrutalMario-PublicBeta-r48-Windows.zip` (`4,065,447` B, SHA-256
      `b315413bd0e090d602ba8d5ade4d7cabd5918d6aa20570ad8d4607692809e2a3`; `windows_binary_sha256`
      `e76d62d1b06897562a443bc31da33ba04c6ca35b8e6261bceff6f103015d7d6c`, `windows_launcher_sha256`
      `1fa13043ec6f81cbba98fcfc6e8a37079687534b59d5b80e308d288ef4bd9b8d`)
    - Linux vs Windows 60-frame binary parity & clean-room `cheat-complete-all.script` /
      `cheat-special-zone.script` smoke tests pass (`Linux guest_mean_ms`: closed `12.121`,
      console `11.53`; `Windows guest_mean_ms`: closed `9.823`, console `9.44`); historical
      `r14..r47` targets and `dist/public-beta-r43..r47/` preserved untouched.

