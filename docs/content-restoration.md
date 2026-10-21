# Content restoration and regression workflow

The user has accepted the 68-variant Demo 1-1 checkpoint and clarified the
long-term objective: retain Demo 1-1 or demoOnly1 as the engine/baseline and
restore unplayable content from other supplied versions where a complete,
playable donor exists. The user chose to compare the existing local versions
first. Official chronology and a latest complete release are not established.

## Priorities

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
loaded DK placement in the first course's four examined rooms in either
version; pickup is not applicable to that path, rather than a fabricated pass.
Actual normal-clear progress survives saving, native cold restart and console
reset/File A reload. This uncovered and fixed a missing native hardware-reset
callback. The 20 unchanged-entry scene samples remain byte-identical; all 92
tests pass. Nonzero DK persistence is still unqualified by this course.

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
Entry, real upward pipe/normal goal, five DK pickups and reset/save/re-entry,
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
hub, and allows a fresh entry. The two upper DK coins are on opposite sides
of a wall and do not both fit one climb. The secret exit remains open.
The user subsequently tested Sky Star without finding problems and reported
that sound is available again and its audio is normal. The
[middle-right restoration report](star-world-middle-right-restoration.md)
records stage acceptance and the new cumulative baseline. Secret completion
and all-five-DK coverage remain unconfirmed.

The center star (`$00A`, room `$079`) has no reachable victory store. Its
phase-2 boss program never writes the level-end timer, and the donor sprite
block is unchanged. That course stays unqualified. The upper-inner cave
(`$007`, map 6 / `$0178,$0188`) is the next cumulative candidate on the Sky
Star ROM. Its recipe restores the six missing ExGFX streams and custom
sprites `$15`, `$45`, and `$50`. `star-world-upper-inner-goal.script` rides
the coaster, stomps the Koopas, and touches the goal tape. Both hosts return
to the hub in mode `$0E` with `$13CE=1` and translevel `$07` flagged `$81`
in WRAM and both SRAM copies; File A reload keeps `$81`. Two frame-counter
pokes after the map tile poke keep native on the same phase as reference.
Death and DK coverage are not part of this checkpoint. The stage is
automatically qualified. Continue with the remaining hub courses, middle-left
`$003` and lower-inner `$117`. A new manual gate is not required.
