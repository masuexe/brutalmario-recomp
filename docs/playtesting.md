# Manual playtest evidence

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
