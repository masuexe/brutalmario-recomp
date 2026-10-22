# Manual playtest evidence

Last full-stage manually accepted baseline: [Sky Star / middle-right](star-world-middle-right-restoration.md),
room `$009` with destination `$09B`. The user reports that another agent
completed the work and their playtest found no problems. They also report
that sound is available again and the heard audio is normal. This accepts
the stage and current Sky Star sound; secret completion and all five DK
coins were not itemized and remain unqualified. The user authorizes an
automatic restoration loop, with targeted human checks only when essential.

The upper-inner cave (`$007`) is automatically qualified on top of that
baseline. Both hosts clear it and keep the save. It is not a new manual
acceptance. Middle-left (`$003`) is also automatically qualified: both
hosts touch the goal tape and keep translevel `$03` flagged `$8C` after
File A reload. That is not a new manual acceptance either.

The [lower-inner 100-coin exit](star-world-lower-inner-restoration.md) is now
automatically qualified with real pickups, save and File A reload. Its coin
route uses explicit player/camera shortcuts. All eight surrounding courses
are included in the [cumulative center candidate](star-world-center-restoration.md);
its unfinished Giant Starman ending is an accepted exception, preserved as the
donor left it, so no center clear is claimed.

The user subsequently reported incorrect lower-inner music. The
[music correction](lower-inner-music.md) selects existing course song `$60`
and cap song `$79`, with all three expiry paths returning to `$60`.
The cap song's reachable musical graph matches cheap_demo exactly; the course
song is its existing revised arrangement. On 2026-10-21 the user confirmed that
the corrected music is completely normal, accepting this scoped listening
check. Individual cap variants were not itemized; all three variants have
separate automated pickup/expiry checks, along with exit/save/reset evidence.

On 2026-10-21 the user reported that powered Mario died instead of shrinking
in `star-world-center`. The [recipe regression](center-damage-regression.md)
was reproduced and repaired with real Koopa-contact checks in both hosts.
The user also reported short cannon travel near the second DK coin and
identified cheap_demo under ZSNES 1.51 as their comparison. Controlled legacy
and native checks reproduce the same input distinction: releasing directional
input and retaining B crosses the pit and collects the DK coin. See
[the cannon evidence](center-cannon-flight.md). These are automated findings;
the user has not supplied a subsequent manual acceptance of either report.

Earlier accepted cumulative baseline: [upper-right Star World](star-world-upper-right-restoration.md),
room `$002`. The user confirmed normal entry and working SMB3 bricks, then
explicitly chose to waive a complete manual run because the course takes too
long. They agreed to stage acceptance using those observations plus the
automated actual pipe, normal-goal, five-DK, reset/save/re-entry and death
checks. Record this as bounded stage acceptance, not a full manual playthrough
or sound pass. That earlier checkpoint took place during a silent window.
Sound subsequently returned, as recorded above; individually unconfirmed
tracks remain in the [optional listening queue](audio-acceptance-queue.md).

On 2026-10-19 the user selected the lower-left course in the nine-star hub
for the first restoration. They clarified that it becomes a Warp Star after
clearing and that the course itself is the target, not a World 1 course after
the warp. An isolated [restoration candidate](star-world-1-restoration.md) is
available with automated bounded checks. The user subsequently tested it and
reported behavior broadly matching the original, with some minor issues.
They requested committing and pushing the current checkpoint and deferring
those issues until daytime. The first specific report concerns the
[LOVE ANIMAL corpse / respawn effect](star-world-1-animal.md). A bounded
cheap_demo comparison reproduces the fixed artwork in the native candidate.
After the user clarified that living Koopas reappear and selected fireball
kills, the investigation reproduced that behavior in both versions: an
uncollected enemy-derived coin unloads, clearing the original enemy's load
record. A stomped Koopa does not respawn in the tested route. The user then
reproduced the explained behavior and considers this report resolved without
a gameplay change. This does not close other unspecified issues or qualify
every individual branch, DK persistence or audio. Previous
acceptances below apply to the original targets and earlier runtime checkpoints.

The subsequent [automated save/hub checkpoint](star-hub-survey.md) checks
actual normal-clear SRAM persistence and fixes a native console-reset hook.
No loaded DK placement was found in the first course's examined dependency
path in either version, so a collectible pickup was not fabricated. Nine
uncleared hub entrances were surveyed, and the upper-left vertical cave is
selected for the next restoration. These are automated observations, not a
new user playthrough, listening acceptance or complete second-course recovery.

Date: 2026-10-15. These observations are user-reported, rather than automated
or independently reproduced by the agent.

- The known-working historical environment is ZSNES 1.51.
- Initial native testing found basic controls working, but mosaic transitions
  appeared as vertical stripes and MARIO START flashed vertical stripes.
- The user confirmed that the subsequent PPU fixes resolved those symptoms.
- After the timing update, the user played level 1-1 and reported no issues
  found so far. The user then authorized the next development step.

The user also confirmed that audio was enabled and that background music and
action effects sounded normal compared with their memory of ZSNES 1.51.

The user subsequently clarified that Demo 1-1 has only one ordinary level
and no boss. They authorized map edits or exploration of demoOnly1 for boss
testing, identified Athletic Special's end boss, and confirmed its final
rainbow-room door. This corrects the earlier assumption that a custom boss
could be qualified in Demo 1-1; see [boss-entry.md](boss-entry.md).

The user then tested the demoOnly1 boss and reported that boss functionality
worked, but death frequently caused a black screen. This triggered the
[legacy audio-memory fix](death-black-screen.md). Automated death regressions
pass after rebuilding. The user subsequently confirmed that several deaths
all returned to the overworld without a black-screen hang. The manual
death-return checkpoint therefore passes; the exact number of deaths and
whether air swimming remained enabled were not specified.

The user later reported accidentally reaching Star World and difficulty
staying on the boss arena's platforms. They requested air swimming for
practice. The launcher now offers fresh Special/Boss practice sessions with
isolated saves and optional water physics; see [boss-entry.md](boss-entry.md).
The user confirmed that air swimming works and that they could defeat the
boss with it enabled. After victory the screen turned black without showing
"MARIO STAGE CLEAR". The user suspects the original behaves the same way
and explicitly deferred investigation. Original-version parity is unverified;
record this as a known, accepted limitation of the current checkpoint, not
as a confirmed original behavior or a verified post-victory transition.

The current boss-functionality checkpoint passes with air swimming enabled:
the user reports normal boss functionality and a successful defeat. This
does not qualify an unassisted clear, complete post-victory flow, full
demoOnly1 compatibility, or a recorded ZSNES comparison. With repeated
death returns also manually confirmed, this round of basic functionality
validation is complete, subject to the accepted victory-screen limitation.
Exact session duration, controller route, and executable hash were not supplied.

After the [file-menu background / HDMA fix](menu-background.md), the user
manually retested and reported no issues found. This is a further manual
checkpoint for the rebuilt runtime; the exact route and duration were not
specified. Residual cross-core timing differences remain an investigation
item rather than a user-reported gameplay defect.

The later [APU-clock correction](boot-timing.md) has automated boot, gameplay,
audio-capture, and death-return regressions. Later gameplay feedback is
recorded below; a new explicit audio listening comparison after that clock
change has not been reported.

The user subsequently reported a missing item-selection cursor in demoOnly1's
Vivian's Shop, entered through Baby Yoshi Hill's opening pipe. They confirmed
that descriptions still changed with Up/Down. This was reproduced as a missing
scanline palette highlight, independently of the APU-clock setting, and fixed;
see [shop-cursor.md](shop-cursor.md). Automated four-item selection and B-exit
comparisons pass; subsequent manual confirmation is recorded below.

On 2026-10-16, the user retested after the shop palette rebuild and reported
no issues. This completes manual confirmation of the reported shop selection
defect and closes the current basic-functionality and reported-display-defect
checkpoint. The report does not specify a new audio listening comparison,
test duration, or full-version playthrough. Remaining cross-core timing
differences, wider AOT coverage, and the accepted/deferred boss-victory black
screen retain their separately documented status.

See [timing.md](timing.md) for automated timing evidence and remaining issues.

The subsequent [PPU counter-read correction](loading-timing.md) has automated
loading, full-route, shop-selection and three-death regressions, with 21 tests
passing. It removes the compiled frame-838 mismatch; later timing differences
remain. Some shop animation samples advance one guest frame earlier, while
the highlight and exit remain functional. This build has no new user playtest
or explicit listening report yet. The earlier manual checkpoint remains valid
for the earlier build rather than automatically qualifying every later change.

After the counter-read rebuild, the user reported that all tests they tried
were free of issues and authorized the next stage: expanding static
recompilation coverage. This confirms that build's manual checkpoint; no
exact route, duration or separate audio listening comparison was supplied.
Subsequent AOT qualification is recorded in [aot-coverage.md](aot-coverage.md).

After the first AOT expansion, the user reported normal functionality but
perceived slower invincibility-star music relative to the original. Treat this
as a new audio concern. The [star-music probe](star-audio.md) finds no accumulating
lag in generated Demo 1-1 PCM versus Snes9x over the measured passage; it does
not resolve a historical ZSNES or physical-device listening comparison.

The user listened to the native/reference star clips and reported that they
sounded identical, then explicitly deferred further investigation of the
subjective star-music concern. Physical-output and ZSNES parity were not
thereby established.

The subsequent [AOT instruction-timing correction](aot-timing.md) has generated
code/interpreter differential tests, complete-route and transition regressions,
and byte-identical generated audio against the preceding native capture.
Manual confirmation of this 49-variant executable is recorded below.

On 2026-10-16, after the instruction-timing rebuild, the user reported no
issues in Demo 1-1's Entry course itself. They also entered the underground
Entry area through its pipe and confirmed that the Baby Yoshi mechanic
worked normally. The user had not obtained the DK coin, so its collection
behavior remains explicitly untested. No exact session duration or new
explicit listening/death-return report was supplied.

Combined with the automated differential and replay checks, this passes the
current AOT instruction-timing regression checkpoint for the covered Entry
and underground Baby Yoshi flows. DK coin collection remains a follow-up
coverage item; it does not block this bounded checkpoint. This report does
not establish a full level clear, complete collectible/persistence coverage,
or whole-port fidelity.

The subsequent [indexed table-read expansion](aot-indexed.md) produces a
50-variant executable with automated differential, full-route, transition and
matched-device audio regression checks.

On 2026-10-16, in response to the requested checks of map movement, level entry,
and the pipe/underground return route, the user reported no issues with the new
build. They also explicitly confirmed that the DK coin could be collected
normally. This passes the 50-variant build's manual regression checkpoint and
closes the previously outstanding DK coin pickup item. The report does not
separately establish collectible persistence after saving/reloading, a full
level clear, or whole-port fidelity; no exact duration or executable hash was
supplied.

The subsequent [WRAM-store expansion](aot-wram.md) produces a 52-variant
executable. Automated differential, replay and matched-device audio checks
are recorded separately. On 2026-10-16, in response to the requested map
movement, Entry loading, pipe/underground and map-return checks, the user
reported no issues. This passes the new build's bounded manual regression
checkpoint. No exact duration, executable hash or new separate DK coin pickup
report was supplied; the previous pickup confirmation remains recorded above.

On 2026-10-16, the user requested arbitrary map-position teleport, specifically
World 1's castle for Larry investigation. The [practice selector](level-select.md)
implements map/pixel coordinates and a castle preset with isolated saves.
Its automated entry/return and launcher-isolation checks pass; user testing
of the new selector and Larry battle is pending. The user also confirmed that
Milky Way Wishes and End of Special Zone hang at MARIO START in original
demoOnly1. These are recorded as original-version unavailable entries, with
matching reference loading observations, rather than native-only regressions.

The user confirmed that arbitrary map teleport works, but identified the old
World 1 castle preset as a World 6 level. They requested a separate all-levels
and DK-coin completion cheat to unlock Warp Stars. Their lower-left castle /
raised-ground / animated-skull landmark was used to correct the preset to map
0, X=$0018, Y=$01B8. The [completion option](completion-cheat.md) has automated
Warp Star, ordinary-level return and isolated-launcher checks; user acceptance
of this new option is pending.

The corrected castle starts loading $010 but stalls at MARIO START in native
and Snes9x reference runs, with and without the cheat. The user explicitly said
they do not know whether the original behaves this way. Original ZSNES 1.51
parity is therefore unknown; do not record this castle as a confirmed original
unavailable level or a qualified Larry encounter. This differs from their
explicit original-version confirmation for Milky Way Wishes and End of Special
Zone. The earlier $101 sample belongs to the misidentified World 6 node.


On 2026-10-18, the user confirmed that the second castle preset (map 0 /
$0018,$01B8) was also wrong. They manually entered the actual intended castle
and reported that the **Lemmy boss worked normally**. This supersedes the
castle-location assumptions in the preceding historical entries: neither
$101 nor $010 is a verified route to that encounter. Their loading observations
remain attached to their sampled nodes, not to the intended castle. The prior
Larry attribution is withdrawn.

The manual Lemmy functionality checkpoint passes within the reported scope.
Correct coordinates and room ID were not recorded; exact duration, clear,
death-return, audio and cheat settings were not separately supplied. The
unverified named shortcut is removed, and `tools/play_demo_only1.py --show-location`
provides a read-only map/room diagnostic for capturing a reproducible route.
The next core work is qualifying PPU register-write timestamps against the
interpreter before promoting the remaining palette/CGRAM hotspots to AOT;
see [aot-wram.md](aot-wram.md).


Later on 2026-10-18, the user supplied the stationary Lemmy castle entrance
reading: frame 3608, mode `$0E`, map 0, X=$00A8, Y=$01A8. This closes the map
coordinate item. The `world1-castle` shortcut is restored at that measured
position. The supplied on-map Room=$1C5 / Translevel=$00 remains prior level
state and does not establish the entered castle room. Both earlier guessed
positions remain withdrawn. The manual Lemmy functionality report remains
accepted within its previously recorded scope.


Native checks of the restored preset reach room $10E / translevel $32 in
active mode $14. Without completion flags, ordinary entry works; with all
completion flags, ordinary entry is ignored even after 600 extra frames,
but L+R shoulder-button re-entry reaches the same room. These are entrance
checks only and do not replace the user's manual Lemmy encounter report.

On 2026-10-18, the user reported thin vertical lines below Mario and at the
far-left screen edge while a background layer obscures the scene in Lemmy's
castle. The supplied screenshot is
`tmp/Snipaste_2026-10-18_21-48-35.png`. Screenshot inspection confirms the
reported visual artifact, but does not identify its cause. Original ZSNES
behavior is unknown; no matched scene has yet been compared with the reference
or the alternate native renderer. The earlier castle entrance captures are
not sufficient to qualify this later scene.

Keep this as an open visual-fidelity item, separate from the accepted manual
boss-functionality checkpoint. Investigate window boundaries, layer rendering
and per-line register/HDMA behavior before changing shared PPU semantics. A
confirmed original-game artifact would require a separate decision about any
optional visual correction rather than being silently classified as a native
regression.


The subsequent [spotlight investigation](lemmy-mask.md) reproduces the scene
in room $08C via the existing screen-5 exit of $10E. Native legacy and optimized
framebuffers match exactly; the Snes9x sample matches every pixel at five-bit
channel precision. Both left-edge and below-circle seams are explained by
actual guest-generated HDMA tables: equal left/right bounds at zero above the
circle, and at center X below it after table termination. This reclassifies
the reported seams as a ROM-driven visual artifact reproduced by the reference,
rather than an identified native-only regression. Historical ZSNES appearance
remains unknown. No visual correction was applied; the earlier functional
Lemmy checkpoint remains accepted. See the linked investigation for the
reproducible input route, ROM byte anchors and local comparison report.


On 2026-10-18, the [restricted palette-port event model](aot-palette.md)
produces a **54-variant Demo 1-1 candidate**. It promotes the $169585 and
$13EFB2 palette loops after exact write-event qualification, retaining the
old timing counterexample as a negative control. All 57 project tests pass.
Full-route, dense-transition, pure-interpreter and generated-audio regression
results are documented in the linked report. **Manual acceptance of this new
executable is pending.** Previous 52-variant user feedback remains historical.
The requested next manual pass covers ordinary map movement, Entry loading
and play, the pipe/underground return route, map return, palette/transition
appearance and ordinary music/effects. No new demoOnly1 manual qualification
is implied by this primary-target AOT expansion.


The user subsequently confirmed launching
`local/build/demo-1-1/BrutalMarioDemo11SNESRecomp` directly and reported no
issues. This response to the requested regression pass accepts the 54-variant
build's bounded manual checkpoint, superseding the pending status above.
The current workspace binary's SHA-256 is
`14218a4054260558b6437889a8f1452c926f0dfcf3446a5c30ffe9e6d21eb231`,
which matches the final automated full-route capture; the user did not supply
an independent hash. Exact duration and individual checklist results were
not separately supplied. This closes the current palette AOT expansion
checkpoint without asserting whole-port fidelity or new demoOnly1 coverage.


The subsequent [indexed coordinate arithmetic expansion](aot-coordinate.md)
produces a **55-variant Demo 1-1 candidate**. It promotes only the $13F1C2
helper's compiled call path after binary/decimal arithmetic, accumulator-width,
flag, full-memory, deadline/continuation and indexed word-boundary checks.
All 60 project tests pass, with an additional final arithmetic-only run after
strengthening intermediate XBA/B-register cases. Full-route, dense-transition,
pure-interpreter and generated-audio regressions pass against the accepted
54-variant baseline. **Manual acceptance of this new executable is pending.**
The requested next pass uses the same direct launch command and checks ordinary
map movement, Entry loading/play, movement/jumping, pipe/underground return,
map return, character/enemy/object positions and graphics, transitions and
ordinary sound. Prior 54-variant feedback does not automatically accept this
new executable; demoOnly1 coverage is unchanged.


The user subsequently reported no issues in response to the requested
55-variant manual regression pass. This accepts the indexed-coordinate-helper
checkpoint and supersedes its pending status above. The workspace executable
at `local/build/demo-1-1/BrutalMarioDemo11SNESRecomp` has SHA-256
`2811b0080b0606058f333a9b83a06677a0176230dcb41de46e44aefa7db10423`, verified against its
build receipt. No independent user hash, exact duration or individual checklist
results were supplied. The 55-variant build becomes the next bounded regression
baseline; no new demoOnly1 or whole-port fidelity claim is made.


The subsequent [nested coordinate caller expansion](aot-caller.md) produces
a **56-variant Demo 1-1 candidate** by qualifying $13F1A7, its nested helper
call and its inline helper continuation. All 62 project tests pass, including
27,604 new caller differential cases. Full-route, dense-transition,
pure-interpreter and generated-audio regressions pass against the accepted
55-variant baseline. **Manual acceptance of this executable is pending.**
The verified regular binary SHA-256 is
`a6a578adf8c17521da45f68ad5b4312cb029ce3d606a9efe5fbba5fd5132a21f`.
The next check uses `local/build/demo-1-1/BrutalMarioDemo11SNESRecomp` for
map movement, Entry loading/play, movement/jumping, object/enemy/player
positions and graphics, pipe/underground return, map return, transitions and
ordinary sound. Previous manual feedback does not automatically accept this
candidate; demoOnly1 qualification is unchanged.


The user subsequently reported no issues in response to the requested
56-variant manual regression pass. This accepts the nested-coordinate-caller
checkpoint and supersedes the pending status above. The workspace executable
was rechecked against its build receipt and checkpoint SHA-256
`a6a578adf8c17521da45f68ad5b4312cb029ce3d606a9efe5fbba5fd5132a21f`.
No independent user hash, exact session duration or individual checklist
results were supplied. The accepted 56-variant build becomes the next bounded
regression baseline; no new demoOnly1 or whole-port fidelity claim is made.


The subsequent [indexed sprite-entry loop expansion](aot-sprite.md) produces
a **57-variant Demo 1-1 candidate** by qualifying $13F06F, its nested
coordinate calls and its bounded output loop. All 63 project tests pass,
including 138,536 new differential cases. Full-route, dense-transition,
pure-interpreter and generated-audio regressions pass against the accepted
56-variant baseline. **Manual acceptance of this executable is pending.**
The verified regular binary SHA-256 is
`376a1ce9e1919093b7866778cf160d7f91493c5b950d8d6914c473f090094f83`.
The next check uses `local/build/demo-1-1/BrutalMarioDemo11SNESRecomp` for
map movement, Entry loading/play, jumping, player/enemy/object positions and
graphics, pipe/underground return, map return, transitions and ordinary sound.
Prior manual feedback does not automatically accept this candidate;
demoOnly1 qualification is unchanged.


The user subsequently reported no issues in response to the requested
57-variant manual regression pass. This accepts the indexed-sprite-loop
checkpoint and supersedes the pending status above. The workspace regular
executable was rechecked against its build receipt, capture receipt and
checkpoint SHA-256
`376a1ce9e1919093b7866778cf160d7f91493c5b950d8d6914c473f090094f83`.
No independent user hash, exact session duration or individual checklist
results were supplied. The accepted 57-variant build becomes the next bounded
regression baseline; no new demoOnly1 or whole-port fidelity claim is made.


The subsequent [sprite append-loop expansion](aot-sprite-y.md) produces
a **58-variant Demo 1-1 candidate** by qualifying $13F13D and its preservation
of Y around nested coordinate calls. All 64 project tests pass, including
498,557 new differential cases and the existing sprite-loop fixture.
Full-route, dense-transition, pure-interpreter and generated-audio regressions
pass against the accepted 57-variant baseline. **Manual acceptance of this
executable is pending.** The verified regular binary SHA-256 is
`8a9f33d3fd6be204f20c1860bc05d77eab0f12b08057f0e5804b20a569c5fce1`.
The next check uses `local/build/demo-1-1/BrutalMarioDemo11SNESRecomp` for
map movement, Entry loading/play, jumping, player/enemy/object positions and
graphics, pipe/underground return, map return, transitions and ordinary sound.
Prior manual feedback does not automatically accept this candidate;
demoOnly1 qualification is unchanged.


The user subsequently reported no issues in response to the requested
58-variant manual regression pass. This accepts the sprite append-loop
checkpoint and supersedes the pending status above. The workspace regular
executable was rechecked against its build receipt, capture receipt and
checkpoint SHA-256
`8a9f33d3fd6be204f20c1860bc05d77eab0f12b08057f0e5804b20a569c5fce1`.
No independent user hash, exact session duration or individual checklist
results were supplied. The accepted 58-variant build becomes the next bounded
regression baseline; no new demoOnly1 or whole-port fidelity claim is made.


The subsequent [bank-15 coordinate expansion](aot-coordinate15.md) produces
a **60-variant Demo 1-1 candidate**, promoting $15A023 and $15A032 together
from the accepted 58-variant build. All 67 project tests pass, including
51,332 new differential cases. Full-route, dense-transition, pure-interpreter
and generated-PCM regressions pass. Dummy output counters vary across runs;
a selective interpreter control also reproduces extra underflows. The linked
report retains all measurements and does not claim exact historical output
parity. **Manual acceptance of this executable is pending.**
The verified regular binary SHA-256 is
`e3e62825d7615aaa589080bf0f715fcfcaf8f39230991f82d4150c4ed648ac63`.
The next check uses `local/build/demo-1-1/BrutalMarioDemo11SNESRecomp` for
map movement, Entry loading/play, jumping, player/enemy/object positions and
graphics, pipe/underground return, map return, transitions and ordinary sound.
Prior manual feedback does not automatically accept this candidate;
demoOnly1 qualification is unchanged.


The user subsequently reported no issues while testing the 60-variant build
in a silent environment. This passes its bounded non-audio manual checkpoint
and supersedes the corresponding pending status above. **Audible music/effects
verification remains pending.** The report does not establish whether audio
was disabled or simply unavailable to hear, and does not resolve the recorded
dummy-output counter variability.
The workspace regular executable was rechecked against its build receipt,
capture receipt and checkpoint SHA-256
`e3e62825d7615aaa589080bf0f715fcfcaf8f39230991f82d4150c4ed648ac63`.
No independent user hash, exact duration or individual checklist results
were supplied. The 60-variant build becomes the bounded non-audio regression
baseline, carrying the pending audible check forward; no new demoOnly1 or
whole-port fidelity claim is made.

The subsequent [pointer and indexed-phase helper batch](aot-helpers.md)
produces a **63-variant Demo 1-1 candidate**, promoting $0DA6B1, $0DA97D and
$15A055 on top of the accepted 60-variant build. All 70 project tests pass,
including 311,172 new differential cases. Full-route, dense-transition,
pure-interpreter and generated-PCM regressions pass, with 64,560 fewer
interpreted instructions on the fixed route. **Manual acceptance of this
executable is pending.**
The verified regular binary SHA-256 is
`334bcdd755914f66b92efc4579979c1d4a19b81c9f7aec7a894f9e1956a633d0`.
The next check uses `local/build/demo-1-1/BrutalMarioDemo11SNESRecomp` for
map movement, Entry loading/play, jumping, player/enemy/object positions and
graphics, pipe/underground return, map return, transitions and ordinary sound.
Prior manual feedback does not automatically accept this candidate; the
audible music/effects check carried forward from the 60-variant build is still
outstanding, and demoOnly1 qualification is unchanged.

The 63-variant candidate's gameplay and graphics passed this check, but the
user reported the previously fixed A/V desync and audio stutter returning.
The session report shows the executable had been launched directly, so it
ran on SDL's WSLg RDP sink instead of the project's Windows-native output
path; the fixes are present in the binary but only engage through the
launcher. `tools/play_demo_1_1.py` now applies that path to demo-1-1.
See [audio synchronization](audio-sync.md) for the measured comparison
(RDP consumption collapse at about 98 s versus a stable four-minute Windows
run) and for the focus-loss analysis, which found no host focus handling at
all. **Gameplay acceptance stands; audio verification on the native path is
pending.** Launch with `python3 tools/play_demo_1_1.py`.


The user subsequently reported that the helper batch and demo-1-1 audio
stutter follow-up were tested without issues. This accepts the 63-variant
build's bounded gameplay/audio checkpoint, superseding its pending native-path
audio status above. The workspace regular binary still matches its build
receipt SHA-256
`334bcdd755914f66b92efc4579979c1d4a19b81c9f7aec7a894f9e1956a633d0`.
No exact duration, individual checklist results or independent user hash were
supplied. Future interactive checks must use `python3 tools/play_demo_1_1.py`
to select the Windows-native output path on this WSL setup. The 63-variant
build is the next bounded regression baseline; no new demoOnly1 or whole-port
fidelity claim is made.


The [word buffer-index expansion](aot-buffer-index.md) produces a **64-variant
Demo 1-1 candidate**, qualifying $15A2FD in M0/X1 after the accepted 63-variant
baseline. All 77 project tests pass, including 291,525 new differential cases.
The full-route and 85 dense-transition samples match the baseline; the
interpreter-only floor is unchanged. The fixed route removes 308,970
interpreted instructions, and generated PCM and selected audio-route
state/clock samples match exactly. **Manual acceptance remains pending.**
The verified regular executable SHA-256 is
`9955ebe282746c00ca41f2b466a706a48bdaec846021d15e7d6edcbd9d669c5d`.
Launch with `python3 tools/play_demo_1_1.py` and check Entry loading,
movement/jumping, tile collision and objects, pipe/underground travel and
return, map return, transitions and ordinary music/effects. Prior acceptance
does not automatically accept this new executable; demoOnly1 is unchanged.


The user subsequently reported no issues in response to the requested
64-variant gameplay/audio check. This accepts the word buffer-index
checkpoint and supersedes its pending manual status above. The workspace
regular executable still matches its build receipt and SHA-256
`9955ebe282746c00ca41f2b466a706a48bdaec846021d15e7d6edcbd9d669c5d`.
No exact duration, itemized outcomes or independent user hash were supplied.
The accepted 64-variant build becomes the next bounded regression baseline;
continue launching with `python3 tools/play_demo_1_1.py`. No new demoOnly1
or whole-port fidelity claim is made.


The [buffer-value expansion](aot-buffer-read.md) produces a **65-variant
Demo 1-1 candidate**, qualifying $15A0E3 after the accepted 64-variant build.
All 80 project tests pass; strengthened boundary probes bring the new
state/write-order/clock/continuation coverage to 740,973 cases. The shared
timed PHX transformation now writes high byte before low byte, matching the
interpreter's stack-write order. Full-route and dense-transition samples,
selected state/clocks, the interpreter-only floor and generated PCM retain
baseline parity. The fixed route removes 89,258 interpreted instructions.
**Manual gameplay/audio acceptance remains pending.**
The verified regular executable SHA-256 is
`3f4ef3817b249e595d66de8197e70a45b9e495255e7780e0554f4bb8629b2cb3`.
Launch with `python3 tools/play_demo_1_1.py` and check Entry loading,
movement/jumping, tile collision and objects, pipe/underground travel and
return, map return, transitions and ordinary music/effects. demoOnly1 is
unchanged; prior acceptance does not automatically accept this candidate.


The user subsequently reported no issues in response to the requested
65-variant gameplay/audio check. This accepts the buffer-value checkpoint
and supersedes its pending manual status above. The workspace regular
executable still matches its build receipt and SHA-256
`3f4ef3817b249e595d66de8197e70a45b9e495255e7780e0554f4bb8629b2cb3`.
No exact duration, itemized outcomes or independent user hash were supplied.
The accepted 65-variant build becomes the next bounded regression baseline;
continue launching with `python3 tools/play_demo_1_1.py`. No new demoOnly1
or whole-port fidelity claim is made.


The [buffer-match flag expansion](aot-buffer-flags.md) produces a **66-variant
Demo 1-1 candidate**, qualifying $15A110 after the accepted 65-variant build.
All 84 project tests pass, including 519,998 new differential cases. A
post-SEP deadline probe exposed a missing X high-byte truncation; the shared
instruction-bus transformation now enforces the interpreter's X/Y truncation
at flag synchronization. Full-route and dense-transition samples, selected
state/clocks, the interpreter-only floor and generated PCM retain baseline
parity. The fixed route removes 401,661 interpreted instructions. Dummy audio
output counters vary and are retained in the linked report.
**Manual gameplay/audio acceptance remains pending.**
The verified regular executable SHA-256 is
`5def7c6769443ca30003500b0a08d5fa29c27a6b67a09256782c8633be794768`.
Launch with `python3 tools/play_demo_1_1.py` and check Entry loading,
movement/jumping, tile collision and objects, pipe/underground travel and
return, map return, transitions and ordinary music/effects. demoOnly1 is
unchanged; prior acceptance does not automatically accept this candidate.


The user subsequently reported one test round without issues and authorized
committing/pushing the 66-variant checkpoint before continuing. This accepts
the buffer-match flag checkpoint and supersedes its pending manual status
above. The workspace regular executable still matches its build receipt and
SHA-256 `5def7c6769443ca30003500b0a08d5fa29c27a6b67a09256782c8633be794768`.
No exact duration, itemized outcomes or independent user hash were supplied.
The accepted 66-variant build becomes the next bounded regression baseline;
continue launching with `python3 tools/play_demo_1_1.py`. No new demoOnly1
or whole-port fidelity claim is made.


The [WRAM record-writer expansion](aot-records.md) produces a **68-variant
Demo 1-1 candidate**, qualifying $15A19F and its $15A25B callee together after
the accepted 66-variant build. There is no separate 67-variant checkpoint.
All 85 project tests pass, including 424,913 new state/write-order/clock and
continuation cases. Word stores, decimal pointer arithmetic, the narrowed-X
terminator and parent/child unwind are qualified against the interpreter.
Full-route and dense-transition samples, selected state/clocks, the
interpreter-only floor and generated PCM retain baseline parity. The fixed
route removes 51,595 interpreted instructions; it does not reach the alternate
callee, whose qualification comes from the differential probe. Dummy output
counter variability is retained in the linked report.
**Manual gameplay/audio acceptance remains pending.**
The verified regular executable SHA-256 is
`3a9c1f5dc3d821d2fc02086785e36628349a96d340e02e5cf4b3c69c05866677`.
Launch with `python3 tools/play_demo_1_1.py` and check Entry loading,
movement/jumping, tile/object appearance and interactions, pipe/underground
travel and return, map return, transitions and ordinary music/effects.
demoOnly1 is unchanged; prior acceptance does not automatically accept this
candidate or imply alternate-branch gameplay coverage.


The user subsequently reported another test round without issues. This
accepts the bounded 68-variant checkpoint and supersedes its pending manual
status above. The regular executable still matches its build receipt and
SHA-256 `3a9c1f5dc3d821d2fc02086785e36628349a96d340e02e5cf4b3c69c05866677`.
No exact duration, itemized outcomes or independent user hash were supplied.
The 68-variant build becomes the next bounded regression baseline. Future
routine AOT changes use automatic qualification and milestone sampling as
described in [content restoration](content-restoration.md); alternate-callee
gameplay and demoOnly1 coverage are not expanded by this report.


## Upper-left Star World cave restoration acceptance

The user tested the [cumulative cave restoration](star-world-upper-left-restoration.md)
and reported that custom sprites load normally and the damaged regions seen
in the original no longer occur. They accepted this stage. This supersedes
the pending manual cave milestone; it does not independently itemize sound,
full ascent, every branch or completion. Existing bounded automated evidence
covers water/platform interactions, five real DK pickups, save/reload,
examined exits and death/re-entry, with 99 project tests passing.

Accepted workspace ROM SHA-256:
`7bffb1c7eb369297cd8dc2f6e84c908e718a5f06a5c445c722512f2e67e7aa37`.
The executable matches its build receipt with SHA-256
`eea9c5bd64e90689b4f047defb8bfc393781fb3d1c2144326dc75bec13eb66b1`.
These are verified workspace identities; no independent user hash was supplied.
Use `star-world-upper-left` as the accepted cumulative restoration baseline.
The original Demo 1-1 and demoOnly1 baselines remain separate.


## Snow Star lower-right candidate awaiting manual acceptance

The [Snow Star cumulative candidate](star-world-lower-right-restoration.md)
restores the missing `$54` song that stalls MARIO START, ExGFX `$1B3` and
ice Ptooie `$57`, retaining the accepted upper-left and lower-left repairs.
All 105 project tests and 191 selected local assertions pass. Actual DK
pickups/save/reload, timed slot/goal and key/keyhole exits, Warp Star,
death/re-entry and sampled enemies pass bounded native/reference checks.
The 36 earlier route samples retain exact full-WRAM/raw-framebuffer matches.
Native song bytes match the adapted payload, and both hosts produce
non-silent captured music; audible fidelity is still a human check.

Candidate ROM SHA-256:
`92cb99a4c48baf9493af7d37f0eddb3305dd6ccf617d2c5d21cf7c15ddc51fd8`.
Launch with `python3 tools/play_demo_only1.py --restoration star-world-lower-right --show-location`.
Request one consolidated course session for unassisted traversal, custom
enemies, music/effects and the final slot interactions. The user has not yet
accepted this candidate. The accepted restoration baseline remains
`star-world-upper-left`; original-version acceptance is unchanged.


## Snow Star gameplay accepted; silent test window

The user subsequently tested both the normal and key exits without issues
and authorized continuing. This accepts the Snow Star gameplay milestone and
supersedes its pending gameplay status above. The accepted workspace ROM is
`92cb99a4c48baf9493af7d37f0eddb3305dd6ccf617d2c5d21cf7c15ddc51fd8`;
the regular executable matches its receipt with SHA-256
`096318c7c040fbafa7c398fa9cb773a47afd65c382d1616f6c6c819f59190708`.
Use `star-world-lower-right` as the cumulative gameplay baseline. No independent
user hash or itemized listening result was supplied.

The silent window is closed: the user reports sound is available again, and on
2026-10-21 they reported that the listening experience is fine when running
`tools/play_demo_only1.py --restoration star-world-center`. That is a general
listening acceptance for the center cumulative candidate, not an itemized pass
and not a retroactive acceptance of the earlier tracks. Remaining itemized
listening stays deferred to the [audio acceptance queue](audio-acceptance-queue.md).

## Lower-inner cap pickup freezes the game (2026-10-21)

The user reported that in the course directly below the star hub, eating a cap
changes the music and then the game freezes. Reproduced and traced: the restored
`hat.asm` requests song `$21` when the cap effects expire, and that id has no
entry in the recipient song table at `$0F:E000`, so the guest hangs waiting for
the music engine. Poking `$1DFB=21` reproduces a hard freeze on the candidate and
does not on `cheap_demo`. See
[the lower-inner report](star-world-lower-inner-restoration.md).

This is a real, user-visible defect in an otherwise qualified course. Until the
songs `$21`, `$1E` and `$22` are restored from the donor, grabbing a cap in this
course is unsafe. The 100-coin exit fixture never grabs caps, which is why the
automated qualification passed.

## Lower-inner cap freeze: fixed and confirmed by the user (2026-10-21)

The reported cap-pickup freeze is mitigated in the shipped candidate and the
user confirmed the result in game: eating a cap switches the music, and when the
cap expires the music returns to the course theme with no freeze.

The underlying song slots are still interim aliases, not the donor tracks. The
proper per-song restoration is now tractable through runtime SPC capture; see
[the lower-inner report](star-world-lower-inner-restoration.md).
