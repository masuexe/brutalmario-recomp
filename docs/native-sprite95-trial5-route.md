# Fifth trial: ordinary shell, upper passage and vine return

## Result (2026-10-30)

The unchanged `demo11-native-seven-product-v1` candidate now completes the
shell/platform/vine/door segment using ordinary controller input. Fresh
native and official7hero captures pass68 paired samples, with damage-immunity
timer1497 and power-up state19 both zero at every checked sample. Actual Up
returns172 to16E and the game collects one Dragon Coin. Earlier hub, switch,
stomp, escape-position and side-approach fixtures remain; this is not an
unassisted whole-trial or five-coin/save qualification.

This extends the [earlier assisted mechanism check](native-sprite95-trial5.md).
The target ROM/executable and source identities remain those of the
[six-room checkpoint](native-sprite95-current-rooms.md). No ROM, runtime,
resource, recipe or gameplay behavior changes were made.

## Ordinary segment and verification

The fixture still protects the Koopa with actual numbered-switch hits,
qualifies real shell entry and stomps the walking Koopa. A player-position
fixture keeps Mario clear while the escaped Koopa moves left; a final
side-approach fixture places Mario at516/144. After that final position write,
the script contains only controller input, waits, dumps and quit:

1. Right+Y150 picks up and carries the shell through the existing layer2
   slope to796/48. The release frame launches the shell. Mario then jumps
   right with Y+B24 into the upper passage and continues right16. The jump
   reaches Y-31 (unsigned65505); this is an ordinary game jump, not the old
   above-roof teleport fixture.
2. Right+Y10, left+Y6 and a16-frame wait brake at924/48. A6-frame right press
   and8-frame wait approach the narrow gap at928/48.
3. The actual released shell hits the existing11A block at944/112. The block
   becomes132 and generates a real ID79 vine. Up+right16 grabs that growing
   vine at938/46, with climb byte74 nonzero. The below-ceiling approach from
   the earlier pilot was too low to reach it.
4. Down34 and right32 use the vine/ledge path and reach969/96 on the far
   door's actual floor. The phase10 custom95 door is loaded at976/112.
5. Ordinary Up2 activates action06 at971/96 and restores working bit10 from
   `$7FFEAF`. After160 frames, both hosts are live in16E at208/688, with
   `$14AF=10`, temporary saved byte00 and Dragon Coin counters1420/1422=1.
   Another160-frame sample preserves that result. Lives and saved five-coin
   flags remain unchanged.

The first nine bridge events compare17 normal-actor fields, excluding the
early-history animation counter1570/frame1602 differences already recorded in
the mechanism check. Later bridge samples, the shell samples and all15 new
route samples compare all19 selected normal-actor fields, including animation
and allocated slots. Functional player/room/switch/coin state and climb/carry
bytes match at all68 samples. Native module A3 executes. Completed logs,
scripts, reference core/options and ROM/build/binary/content identities are
checked; this is a cross-image comparison, not full-engine parity.

## Reproduction and retained limits

```
python3 tools/qualify_sprite95_trial5_route.py --prepare
python3 tools/m1.py native --target demo11-native-seven-product-v1 --script local/probes/sprite95-trial5-route-v2/native.script --capture sprite95-trial5-route-native-v2
SNESREF_CORE_OPTIONS=snes9x_echo_buffer_hack=enabled python3 tools/probe_reference.py --manifest config/7hero-donor.json --rom local/content-versions/7hero/rom.sfc --script local/probes/sprite95-trial5-route-v2/source.script --capture sprite95-trial5-route-source-v2
python3 tools/qualify_sprite95_trial5_route.py --output local/reports/FRESH.json
```

The checker generates immutable ignored scripts and refuses changed existing
bytes. Preserve existing captures; future reruns require fresh identities.
Report `local/reports/sprite95-trial5-route-v2.json` and its byte-identical
recheck have SHA-256
`c7fc56aa5d6820d275226f0c4e40523fc85081761873d212585ed118902232fb`.
The checker compiles. No fresh full game-code test suite is claimed for this
verification-only checkpoint.

Earlier v1 route captures retained persistent immunity and are separate from
these v2 no-immunity runs. Source pilot `sprite95-trial5-upper-source-v6`
established the final input sequence; v4 accidentally truncated at the initial
hub door and is invalid as trial evidence. The other below-ceiling and vine
approach pilots remain failed route attempts, not restoration defects.

Room/pipe entry and player positions still assist the hub, numbered-switch
schedule, initial stomp, escape direction and side approach. No immunity,
actor, velocity, HP, switch, progress, completion or save writes occur in the
final scripts. Remaining work includes ordinary input for those earlier
segments, the other trials/coins, five-coin/save behavior and full castle
traversal. No new audible/visible equality, whole-course or product promotion
claim follows from these samples.
