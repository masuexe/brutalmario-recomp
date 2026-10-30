# Bowser Keep fifth trial: assisted mechanism and return qualification

The subsequent [ordinary platform/vine route](native-sprite95-trial5-route.md)
removes the far-door teleport and all immunity writes. Its fresh68 paired
samples cover the shell/platform/vine/door segment through real return and
one coin. Earlier switch/stomp/approach position fixtures still remain.

## Result (2026-10-30)

The unchanged `demo11-native-seven-product-v1` candidate now exercises the
fifth trial through actual switch hits, Koopa movement, shell entry, stomp,
pickup/release and the far return door. Two fresh native/official7hero runs
pass59 paired samples. Ordinary Up at the far door returns from172 to16E and
the game awards one Dragon Coin. Player-position fixtures assist these
interactions and bypass the remaining platform traversal. This is not an
unassisted trial clear or five-coin/save acceptance.

The target ROM/executable and official source identities are unchanged from
the [six-room checkpoint](native-sprite95-current-rooms.md). The new evidence
does not promote the candidate or alter historical r14/r15 acceptance.
No ROM, runtime, resource or recipe was modified.

## Exercised sequence

The [community walkthrough](https://brutalmario.fandom.com/wiki/Finish%21_Bowser_Keep)
describes protecting the shellless Koopa with the three numbered switches and
using its shell. Actual local captures establish this trial as room172, entered
by the fifth16E door; numeric IDs are not inferred from the walkthrough.

1. The ordinary hub-door interaction sets bit10 (hex). Room172 initialization
   saves it at `$7FFEAF` and clears `$14AF` for the puzzle.
2. Three ordinary jumps hit the overhead switches. The working byte changes
   `00 -> 01 -> 03 -> 07`. Assisted standing positions place Mario below each
   switch; no switch/actor values are written.
3. Fourteen jumps follow event waits on the live Koopa X position. The Koopa
   crosses the numbered bridge at Y160, with native/source positions, status,
   direction and velocities matching at the asserted samples. The raised
   switch2 barrier near X448 must also open before it reaches the shell.
4. The waiting ID04 shell at X496/Y160 changes from status09 to a walking
   status08 Koopa at X499/Y160; the original shellless actor disappears.
   The walking actor subsequently reaches X531/Y160 in both hosts.
5. An assisted drop produces a real stomp: the actor becomes a stationary
   status09 shell at X537/Y160. A separate assisted side approach and ordinary
   right+Y input sets carrying byte `$1470=1`. The input format inserts an idle
   frame after a press, so the observed shell is already released to status0A
   at that dump. It then moves from X542/Y159 to X602/Y125, and carrying clears.
   No held status0B sample is claimed.
6. An explicit above-roof position/scroll fixture loads the far door while
   bypassing the remaining platform segment. Mario is then positioned on its
   real floor at X976/Y96; the phase10 custom95 door is at X976/Y112.
   Ordinary Up sets pipe action06 and restores working bit10 from `$7FFEAF`.
7. Both hosts return to live16E at X208/Y688. The working byte is10, the saved
   temporary byte is00, and Dragon Coin counters `$1420/$1422` both change
   from0 to1. Lives and the saved five-coin flag array remain unchanged.

The bridge schedule is pinned in `tools/qualify_sprite95_trial5.py`. Its Koopa
X event positions are160,192,224,240,256,272,288,304,324,340,368,400,412,432.
The game performs every switch change, shell transition and coin award.

## Comparison boundaries and failed probes

All59 samples compare room, game mode, action, player coordinates, working and
saved switch bytes, goal timer and coin state. The first nine bridge events
compare17 selected normal-actor fields, omitting animation counter1570 and
animation frame1602. Those animation values differ early in the two entry
histories; for example the first event's counter is181 versus39. The last
five bridge events and six shell samples compare all19 selected fields,
including animation and slots. This does not establish full WRAM, rendering,
audio or whole-course timing parity.

Earlier ignored probes remain intact:

- `sprite95-trial5-bridge-*-v1/v2` used incorrect switch/timing assumptions and
  lost the Koopa in both hosts. Source timing-grid captures established that
  the first inverted bridge needs switch1 cleared; clearing switch2 or3 loses
  the Koopa. The corrected schedule retains the real Koopa through shell entry.
- `sprite95-trial5-bridge-*-v3` omitted the raised switch2 barrier. The Koopa
  turned around and died. V4 opens that barrier and reaches the shell.
- `sprite95-trial5-shell-*-v1` kicked the stomped shell before the attempted
  pickup. V2 adds a separate side approach and records the carrying/release
  boundary. Do not relabel the earlier kick as pickup evidence.
- `sprite95-trial5-return-*-v1` jumped directly to the far coordinate and
  skipped door loading. V2 loaded the door but the assisted path touched lava
  and died in both hosts. Final V3 uses an explicitly labelled above-roof
  fixture. It proves the far-door return boundary, not ordinary traversal.

The earlier beginning-door self-loop is distinct from the successful far door.
Room1CC interaction remains unresolved. No progress, completion, saved flags,
actor, velocity, HP, or collision-state writes were used to manufacture results.

## Reproduction

```
python3 tools/qualify_sprite95_trial5.py --prepare
python3 tools/m1.py native --target demo11-native-seven-product-v1 --script local/probes/sprite95-trial5-v1/native-return-v3.script --capture sprite95-trial5-return-native-v3
SNESREF_CORE_OPTIONS=snes9x_echo_buffer_hack=enabled python3 tools/probe_reference.py --manifest config/7hero-donor.json --rom local/content-versions/7hero/rom.sfc --script local/probes/sprite95-trial5-v1/source-return-v3.script --capture sprite95-trial5-return-source-v3
python3 tools/qualify_sprite95_trial5.py --output local/reports/FRESH.json
```

Keep existing captures/scripts intact. The generator verifies existing script
bytes rather than overwriting them; future command changes require new artifact
and capture identities. Qualification checks actual scripts, source ROM,
native ROM/build/binary/content identities, reference core/options, completed
logs, module A3 execution and explicit behavioral assertions.

Report `local/reports/sprite95-trial5-v2.json` and its byte-identical recheck
have SHA-256 `100c4f2c90d3fbcd6946e655571e3b21d15945d2b4206cb03ee100f989b2129e`.
The new checker compiles. Existing game code and its prior test qualification
are unchanged; no fresh full-suite run is claimed.

Next: replace the position-assisted switch/platform segments with ordinary
inputs, then qualify the other trials' mechanisms, actual returns and coins.
Five-coin award/save, castle traversal, earned Seven/mazo wins and remaining
restoration work remain open.
